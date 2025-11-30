"""Content Transformer - Core orchestration for Holocron.

The ContentTransformer is the main orchestrator that ties together:
- Domain adapters for concept extraction and assessment generation
- Mastery engine for tracking learner progress
- LLM integration for content transformation
- Scaffolding based on learner mastery levels

This is the primary entry point for transforming learning content
with personalized scaffolding support.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from holocron.core.mastery import MasteryEngine
from holocron.core.models import (
    Assessment,
    BloomLevel,
    Concept,
    ConceptMastery,
    LearnerProfile,
)
from holocron.domains.base import DomainAdapter
from holocron.domains.registry import DomainRegistry


@dataclass
class TransformResult:
    """Result of content transformation.

    Attributes:
        original_content: The original input content
        transformed_content: The scaffolded/transformed content
        concepts_found: Concepts extracted from the content
        assessments: Generated assessments for the concepts
        scaffold_level: The scaffold level used for transformation
        mastery_updates: Any mastery updates from exposure
        metadata: Additional transformation metadata
    """

    original_content: str
    transformed_content: str
    concepts_found: list[Concept]
    assessments: list[Assessment]
    scaffold_level: int
    mastery_updates: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TransformConfig:
    """Configuration for content transformation.

    Attributes:
        include_assessments: Whether to generate assessments
        num_assessments: Number of assessments per concept
        assessment_bloom_levels: Which Bloom levels to assess
        include_inline_support: Whether to add inline definitions/explanations
        max_concepts: Maximum concepts to process (None = unlimited)
        scaffold_level_override: Force a specific scaffold level (None = auto)
        record_exposure: Whether to record this as concept exposure
    """

    include_assessments: bool = True
    num_assessments: int = 1
    assessment_bloom_levels: list[BloomLevel] = field(
        default_factory=lambda: [BloomLevel.KNOWLEDGE, BloomLevel.COMPREHENSION]
    )
    include_inline_support: bool = True
    max_concepts: int | None = None
    scaffold_level_override: int | None = None
    record_exposure: bool = True


class ContentTransformer:
    """Main orchestrator for content transformation with adaptive scaffolding.

    The ContentTransformer coordinates between domain adapters, the mastery
    engine, and LLM integration to provide personalized learning content.

    Example:
        ```python
        transformer = ContentTransformer(
            domain_id="reading-skills",
            learner=learner_profile,
        )

        result = transformer.transform(
            content="Text to learn from...",
            config=TransformConfig(include_assessments=True),
        )

        print(result.transformed_content)
        for assessment in result.assessments:
            print(assessment.question)
        ```
    """

    def __init__(
        self,
        domain_id: str,
        learner: LearnerProfile,
        llm_callback: Callable[[str, str], str] | None = None,
    ) -> None:
        """Initialize the content transformer.

        Args:
            domain_id: The skill domain to use
            learner: The learner profile for personalization
            llm_callback: Optional callback for LLM calls (system_prompt, user_content) -> response
        """
        self.domain_id = domain_id
        self.learner = learner
        self.llm_callback = llm_callback

        # Get domain adapter
        self.adapter: DomainAdapter = DomainRegistry.get(domain_id)

        # Initialize mastery engine
        self.mastery_engine = MasteryEngine(
            domain_config=self.adapter.config,
            learner_profile=learner,
        )

    def transform(
        self,
        content: str,
        config: TransformConfig | None = None,
    ) -> TransformResult:
        """Transform content with adaptive scaffolding.

        Args:
            content: The content to transform
            config: Transformation configuration

        Returns:
            TransformResult with transformed content and metadata
        """
        if config is None:
            config = TransformConfig()

        # Validate content
        if not self.adapter.validate_content(content):
            return TransformResult(
                original_content=content,
                transformed_content=content,
                concepts_found=[],
                assessments=[],
                scaffold_level=3,
                metadata={"error": "Content not suitable for this domain"},
            )

        # Preprocess content
        processed_content = self.adapter.preprocess_content(content)

        # Extract concepts
        all_concepts = self.adapter.extract_concepts(processed_content)

        # Limit concepts if configured
        if config.max_concepts:
            concepts = all_concepts[: config.max_concepts]
        else:
            concepts = all_concepts

        # Get mastery for each concept
        concept_mastery_pairs: list[tuple[Concept, ConceptMastery]] = []
        for concept in concepts:
            mastery = self.learner.get_mastery(self.domain_id, concept.concept_id)
            concept_mastery_pairs.append((concept, mastery))

        # Determine scaffold level
        if config.scaffold_level_override is not None:
            scaffold_level = config.scaffold_level_override
        else:
            scaffold_level = self._calculate_scaffold_level(concept_mastery_pairs)

        # Generate scaffold prompt
        scaffold_prompt = self.adapter.get_scaffold_prompt(
            scaffold_level, concept_mastery_pairs
        )

        # Transform content using LLM (or return processed if no LLM)
        if self.llm_callback and config.include_inline_support:
            transformed_content = self.llm_callback(scaffold_prompt, processed_content)
        else:
            transformed_content = processed_content

        # Postprocess content
        transformed_content = self.adapter.postprocess_content(transformed_content)

        # Record exposures if configured
        mastery_updates = []
        if config.record_exposure:
            for concept, _ in concept_mastery_pairs:
                update = self.mastery_engine.update_from_exposure(concept.concept_id)
                mastery_updates.append({
                    "concept_id": concept.concept_id,
                    "new_mastery": update.new_mastery,
                    "exposure_count": update.new_exposure_count,
                })

        # Generate assessments
        assessments = []
        if config.include_assessments:
            for concept, mastery in concept_mastery_pairs:
                for bloom_level in config.assessment_bloom_levels:
                    for _ in range(config.num_assessments):
                        assessment = self.adapter.generate_assessment(
                            concept=concept,
                            bloom_level=bloom_level,
                            context=self._get_concept_context(concept, processed_content),
                        )
                        assessments.append(assessment)

        return TransformResult(
            original_content=content,
            transformed_content=transformed_content,
            concepts_found=concepts,
            assessments=assessments,
            scaffold_level=scaffold_level,
            mastery_updates=mastery_updates,
            metadata={
                "domain_id": self.domain_id,
                "learner_id": self.learner.learner_id,
                "total_concepts": len(all_concepts),
                "processed_concepts": len(concepts),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    def _calculate_scaffold_level(
        self, concept_mastery_pairs: list[tuple[Concept, ConceptMastery]]
    ) -> int:
        """Calculate overall scaffold level from concept masteries.

        Uses a weighted approach that considers:
        - Average mastery across concepts
        - Number of low-mastery concepts
        - Concept difficulties

        Args:
            concept_mastery_pairs: List of (concept, mastery) tuples

        Returns:
            Scaffold level from 1 (max support) to 5 (min support)
        """
        if not concept_mastery_pairs:
            return 3  # Default to middle level

        # Calculate weighted average considering difficulty
        total_weight = 0.0
        weighted_mastery = 0.0

        for concept, mastery in concept_mastery_pairs:
            # Higher difficulty concepts have more weight
            weight = concept.difficulty_score / 5.0
            weighted_mastery += mastery.overall_mastery * weight
            total_weight += weight

        if total_weight == 0:
            avg_mastery = 50.0
        else:
            avg_mastery = weighted_mastery / total_weight

        # Count low mastery concepts
        low_mastery_count = sum(
            1 for _, m in concept_mastery_pairs if m.overall_mastery < 40
        )
        low_mastery_ratio = low_mastery_count / len(concept_mastery_pairs)

        # Adjust for low mastery prevalence
        if low_mastery_ratio > 0.5:
            avg_mastery *= 0.8  # Increase support

        # Map to scaffold levels
        if avg_mastery < 20:
            return 1
        elif avg_mastery < 40:
            return 2
        elif avg_mastery < 60:
            return 3
        elif avg_mastery < 80:
            return 4
        else:
            return 5

    def _get_concept_context(self, concept: Concept, content: str) -> str:
        """Extract context for a concept from the content.

        Args:
            concept: The concept to find context for
            content: The full content

        Returns:
            A relevant snippet of context
        """
        # For reading domain, use stored contexts
        if "original_contexts" in concept.domain_data:
            contexts = concept.domain_data["original_contexts"]
            if contexts:
                return contexts[0]

        # For programming domain, use examples
        if concept.examples:
            return concept.examples[0]

        # Default: return a portion of content
        return content[:500] if len(content) > 500 else content

    def get_due_concepts(self) -> list[str]:
        """Get concepts due for spaced repetition review.

        Returns:
            List of concept IDs due for review
        """
        return self.mastery_engine.get_concepts_due_for_review()

    def get_recommended_concepts(self, count: int = 5) -> list[Concept]:
        """Get recommended concepts to study based on mastery and readiness.

        Args:
            count: Number of concepts to recommend

        Returns:
            List of recommended Concept objects
        """
        # Get concepts from adapter's concept graph
        # For now, return concepts with lowest mastery
        all_mastery = self.learner.domain_mastery.get(self.domain_id, {})

        # Sort by mastery (lowest first)
        sorted_concepts = sorted(
            all_mastery.items(),
            key=lambda x: x[1].overall_mastery,
        )

        # Return concept IDs (would need to map back to full concepts)
        return [concept_id for concept_id, _ in sorted_concepts[:count]]

    def process_assessment_response(
        self,
        assessment: Assessment,
        response: str,
        is_correct: bool | None = None,
        score: float | None = None,
    ) -> dict[str, Any]:
        """Process a learner's response to an assessment.

        Args:
            assessment: The assessment that was answered
            response: The learner's response
            is_correct: Whether the response was correct (for MC questions)
            score: Score from 0-1 (for graded responses)

        Returns:
            Dictionary with mastery update information
        """
        from holocron.core.models import AssessmentResult

        # Create assessment result
        result = AssessmentResult(
            assessment_id=assessment.assessment_id,
            learner_id=self.learner.learner_id,
            timestamp=datetime.now(timezone.utc),
            response=response,
            is_correct=is_correct if is_correct is not None else (score is not None and score >= 0.7),
            score=score if score is not None else (1.0 if is_correct else 0.0),
        )

        # Update mastery
        update = self.mastery_engine.update_from_assessment(
            concept_id=assessment.concept_id,
            result=result,
            bloom_level=assessment.bloom_level,
        )

        return {
            "concept_id": assessment.concept_id,
            "bloom_level": assessment.bloom_level.value,
            "is_correct": result.is_correct,
            "score": result.score,
            "new_mastery": update.new_mastery,
            "next_review": update.new_next_review.isoformat() if update.new_next_review else None,
        }

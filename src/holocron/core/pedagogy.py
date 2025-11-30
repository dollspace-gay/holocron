"""Pedagogical Transformer with evidence-based learning techniques.

This module implements proven learning science techniques:
- Elaborative Encoding: Creating meaningful connections through analogies
- Dual Coding: Combining verbal and visual representations
- Feynman Technique: Simplifying concepts for deeper understanding
- Interleaving: Mixing related topics for better discrimination
- Retrieval Practice: Testing to strengthen memory
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from holocron.core.models import Concept, ConceptMastery, BloomLevel


class PedagogicalTechnique(str, Enum):
    """Evidence-based pedagogical techniques."""

    ELABORATIVE_ENCODING = "elaborative_encoding"
    DUAL_CODING = "dual_coding"
    FEYNMAN = "feynman"
    INTERLEAVING = "interleaving"
    RETRIEVAL_PRACTICE = "retrieval_practice"
    SPACED_REPETITION = "spaced_repetition"
    SCAFFOLDING = "scaffolding"


@dataclass
class TechniqueResult:
    """Result of applying a pedagogical technique.

    Attributes:
        technique: The technique that was applied
        original_content: The input content
        transformed_content: The content after transformation
        metadata: Additional technique-specific data
    """

    technique: PedagogicalTechnique
    original_content: str
    transformed_content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class TechniqueStrategy(ABC):
    """Abstract base class for pedagogical technique implementations."""

    @property
    @abstractmethod
    def technique(self) -> PedagogicalTechnique:
        """The technique this strategy implements."""
        pass

    @abstractmethod
    def apply(
        self,
        concept: Concept,
        mastery: ConceptMastery,
        context: str = "",
        llm_callback: Callable[[str, str], str] | None = None,
    ) -> TechniqueResult:
        """Apply the technique to transform content.

        Args:
            concept: The concept to enhance
            mastery: The learner's mastery of the concept
            context: Additional context for the transformation
            llm_callback: Optional LLM callback for AI-powered transformations

        Returns:
            TechniqueResult with transformed content
        """
        pass

    def is_appropriate(self, concept: Concept, mastery: ConceptMastery) -> bool:
        """Determine if this technique is appropriate for the current state.

        Args:
            concept: The concept being learned
            mastery: The learner's current mastery

        Returns:
            True if the technique should be applied
        """
        return True


class ElaborativeEncodingStrategy(TechniqueStrategy):
    """Creates meaningful connections through analogies and elaboration.

    Uses analogies to connect new concepts to familiar ideas,
    leveraging existing knowledge structures for better retention.
    """

    @property
    def technique(self) -> PedagogicalTechnique:
        return PedagogicalTechnique.ELABORATIVE_ENCODING

    def apply(
        self,
        concept: Concept,
        mastery: ConceptMastery,
        context: str = "",
        llm_callback: Callable[[str, str], str] | None = None,
    ) -> TechniqueResult:
        # Use existing analogies or generate new ones
        if concept.analogies:
            analogy = concept.analogies[0]
            elaboration = f"\n\n**Think of it this way:** {analogy}\n"
        elif llm_callback:
            prompt = f"""Create a relatable analogy to explain this concept:

Concept: {concept.name}
Description: {concept.description}

Generate a single, clear analogy that connects this concept to everyday experience.
Format: "Think of [concept] like [analogy]..."
Keep it concise (1-2 sentences)."""

            elaboration = "\n\n**Analogy:** " + llm_callback(
                "You are an expert educator creating memorable analogies.",
                prompt
            ) + "\n"
        else:
            # Basic elaboration without LLM
            elaboration = f"\n\n**Key Insight:** {concept.name} - {concept.description}\n"

        content = context if context else concept.description
        transformed = content + elaboration

        return TechniqueResult(
            technique=self.technique,
            original_content=content,
            transformed_content=transformed,
            metadata={"analogy": elaboration},
        )

    def is_appropriate(self, concept: Concept, mastery: ConceptMastery) -> bool:
        # Most useful for new or partially understood concepts
        return mastery.overall_mastery < 70


class DualCodingStrategy(TechniqueStrategy):
    """Combines verbal and visual representations.

    Leverages both verbal and visual memory systems for
    stronger encoding and easier retrieval.
    """

    @property
    def technique(self) -> PedagogicalTechnique:
        return PedagogicalTechnique.DUAL_CODING

    def apply(
        self,
        concept: Concept,
        mastery: ConceptMastery,
        context: str = "",
        llm_callback: Callable[[str, str], str] | None = None,
    ) -> TechniqueResult:
        content = context if context else concept.description

        # Use existing visual description or generate one
        if concept.visual_description:
            visual = concept.visual_description
        elif llm_callback:
            prompt = f"""Create a vivid mental image to represent this concept:

Concept: {concept.name}
Description: {concept.description}

Describe a visual scene or mental picture that captures the essence of this concept.
Use sensory details (colors, shapes, movement).
Keep it to 2-3 sentences."""

            visual = llm_callback(
                "You are an expert at creating memorable mental imagery for learning.",
                prompt
            )
        else:
            # Generate a basic visual suggestion
            visual = f"Visualize {concept.name} as a distinct element in your mental map of {concept.domain_id}."

        transformed = content + f"\n\n**Mental Image:** {visual}\n"

        return TechniqueResult(
            technique=self.technique,
            original_content=content,
            transformed_content=transformed,
            metadata={"visual_description": visual},
        )

    def is_appropriate(self, concept: Concept, mastery: ConceptMastery) -> bool:
        # Useful for initial learning and reinforcement
        return mastery.exposure_count < 5 or mastery.overall_mastery < 60


class FeynmanStrategy(TechniqueStrategy):
    """Simplifies concepts for deeper understanding.

    Named after Richard Feynman's technique of explaining complex
    ideas in simple terms to identify gaps in understanding.
    """

    @property
    def technique(self) -> PedagogicalTechnique:
        return PedagogicalTechnique.FEYNMAN

    def apply(
        self,
        concept: Concept,
        mastery: ConceptMastery,
        context: str = "",
        llm_callback: Callable[[str, str], str] | None = None,
    ) -> TechniqueResult:
        content = context if context else concept.description

        if llm_callback:
            prompt = f"""Explain this concept as if teaching it to someone with no background in the subject:

Concept: {concept.name}
Technical Description: {concept.description}

Requirements:
- Use simple, everyday language
- Avoid jargon (or define it if essential)
- Use concrete examples
- Keep it under 100 words"""

            simple_explanation = llm_callback(
                "You are a patient teacher explaining to a curious beginner.",
                prompt
            )
        else:
            # Simplify using available examples
            if concept.examples:
                simple_explanation = f"In simple terms: {concept.examples[0]}"
            else:
                simple_explanation = f"The key idea: {concept.description}"

        transformed = content + f"\n\n**In Plain English:** {simple_explanation}\n"

        return TechniqueResult(
            technique=self.technique,
            original_content=content,
            transformed_content=transformed,
            metadata={"simplified": simple_explanation},
        )

    def is_appropriate(self, concept: Concept, mastery: ConceptMastery) -> bool:
        # Most useful for difficult concepts or when comprehension is low
        return concept.difficulty_score >= 6 or mastery.comprehension_score < 50


class InterleavingStrategy(TechniqueStrategy):
    """Mixes related topics for better discrimination.

    Alternating between related concepts improves the ability
    to distinguish between them and apply the right approach.
    """

    @property
    def technique(self) -> PedagogicalTechnique:
        return PedagogicalTechnique.INTERLEAVING

    def __init__(self, related_concepts: list[Concept] | None = None):
        """Initialize with optional related concepts.

        Args:
            related_concepts: Concepts to interleave with
        """
        self.related_concepts = related_concepts or []

    def apply(
        self,
        concept: Concept,
        mastery: ConceptMastery,
        context: str = "",
        llm_callback: Callable[[str, str], str] | None = None,
    ) -> TechniqueResult:
        content = context if context else concept.description

        interleave_notes = []

        # Add contrast with related concepts
        if self.related_concepts:
            for related in self.related_concepts[:3]:
                contrast = f"**Compare with {related.name}:** While {concept.name} {concept.description[:50]}..., {related.name} {related.description[:50]}..."
                interleave_notes.append(contrast)
        elif concept.related_concepts:
            for related_id in concept.related_concepts[:3]:
                related_name = related_id.split(".")[-1].replace("_", " ").title()
                interleave_notes.append(f"**Related:** {related_name}")

        if llm_callback and not interleave_notes:
            prompt = f"""Identify 2-3 related concepts that should be learned alongside this one:

Concept: {concept.name}
Domain: {concept.domain_id}
Description: {concept.description}

List related concepts that:
1. Share similarities but have key differences
2. Are commonly confused with this concept
3. Build on or extend this concept

Format as a bullet list."""

            related_info = llm_callback(
                "You are an expert curriculum designer.",
                prompt
            )
            interleave_notes.append(f"**Related Topics to Study:**\n{related_info}")

        if interleave_notes:
            transformed = content + "\n\n" + "\n".join(interleave_notes) + "\n"
        else:
            transformed = content

        return TechniqueResult(
            technique=self.technique,
            original_content=content,
            transformed_content=transformed,
            metadata={"related_concepts": [c.concept_id for c in self.related_concepts]},
        )

    def is_appropriate(self, concept: Concept, mastery: ConceptMastery) -> bool:
        # More useful once basic understanding is achieved
        return mastery.recognition_score >= 50


class RetrievalPracticeStrategy(TechniqueStrategy):
    """Generates retrieval prompts to strengthen memory.

    Testing memory through retrieval is more effective than
    re-reading for long-term retention.
    """

    @property
    def technique(self) -> PedagogicalTechnique:
        return PedagogicalTechnique.RETRIEVAL_PRACTICE

    def apply(
        self,
        concept: Concept,
        mastery: ConceptMastery,
        context: str = "",
        llm_callback: Callable[[str, str], str] | None = None,
    ) -> TechniqueResult:
        content = context if context else concept.description

        prompts = []

        # Generate retrieval prompts based on Bloom levels
        if mastery.overall_mastery < 40:
            # Knowledge level
            prompts.append(f"**Quick Check:** Can you define {concept.name} in one sentence?")
        elif mastery.overall_mastery < 60:
            # Comprehension level
            prompts.append(f"**Think About It:** How would you explain {concept.name} to a friend?")
        elif mastery.overall_mastery < 80:
            # Application level
            prompts.append(f"**Apply It:** When would you use {concept.name}? Give an example.")
        else:
            # Analysis/Synthesis level
            prompts.append(f"**Challenge:** How does {concept.name} relate to other concepts you know?")

        if llm_callback:
            prompt = f"""Generate a thought-provoking question about this concept:

Concept: {concept.name}
Description: {concept.description}
Learner Mastery: {mastery.overall_mastery:.0f}%

Create a question that:
- Requires active recall (not just recognition)
- Is appropriate for the learner's current level
- Encourages deeper thinking

Format: A single question."""

            custom_prompt = llm_callback(
                "You are an expert at creating effective practice questions.",
                prompt
            )
            prompts.append(f"**Recall Challenge:** {custom_prompt}")

        transformed = content + "\n\n" + "\n".join(prompts) + "\n"

        return TechniqueResult(
            technique=self.technique,
            original_content=content,
            transformed_content=transformed,
            metadata={"retrieval_prompts": prompts},
        )


class PedagogicalTransformer:
    """Applies evidence-based pedagogical techniques to learning content.

    Orchestrates multiple learning science techniques to enhance
    content based on the learner's current mastery level.

    Example:
        ```python
        transformer = PedagogicalTransformer()

        result = transformer.transform(
            concept=list_comprehension_concept,
            mastery=learner_mastery,
            techniques=[
                PedagogicalTechnique.ELABORATIVE_ENCODING,
                PedagogicalTechnique.DUAL_CODING,
            ],
        )

        print(result.transformed_content)
        ```
    """

    def __init__(
        self,
        llm_callback: Callable[[str, str], str] | None = None,
        related_concepts: list[Concept] | None = None,
    ):
        """Initialize the pedagogical transformer.

        Args:
            llm_callback: Optional LLM callback for AI-powered techniques
            related_concepts: Related concepts for interleaving
        """
        self.llm_callback = llm_callback
        self.related_concepts = related_concepts or []

        # Initialize technique strategies
        self._strategies: dict[PedagogicalTechnique, TechniqueStrategy] = {
            PedagogicalTechnique.ELABORATIVE_ENCODING: ElaborativeEncodingStrategy(),
            PedagogicalTechnique.DUAL_CODING: DualCodingStrategy(),
            PedagogicalTechnique.FEYNMAN: FeynmanStrategy(),
            PedagogicalTechnique.INTERLEAVING: InterleavingStrategy(related_concepts),
            PedagogicalTechnique.RETRIEVAL_PRACTICE: RetrievalPracticeStrategy(),
        }

    def get_recommended_techniques(
        self,
        concept: Concept,
        mastery: ConceptMastery,
        max_techniques: int = 3,
    ) -> list[PedagogicalTechnique]:
        """Get recommended techniques based on current learning state.

        Args:
            concept: The concept being learned
            mastery: The learner's current mastery
            max_techniques: Maximum number of techniques to recommend

        Returns:
            List of recommended techniques in priority order
        """
        recommended = []

        for technique, strategy in self._strategies.items():
            if strategy.is_appropriate(concept, mastery):
                recommended.append(technique)

        # Prioritize based on mastery level
        def priority(t: PedagogicalTechnique) -> int:
            if mastery.overall_mastery < 30:
                # New learner: focus on encoding
                priorities = {
                    PedagogicalTechnique.ELABORATIVE_ENCODING: 1,
                    PedagogicalTechnique.DUAL_CODING: 2,
                    PedagogicalTechnique.FEYNMAN: 3,
                }
            elif mastery.overall_mastery < 60:
                # Developing: focus on understanding
                priorities = {
                    PedagogicalTechnique.FEYNMAN: 1,
                    PedagogicalTechnique.RETRIEVAL_PRACTICE: 2,
                    PedagogicalTechnique.ELABORATIVE_ENCODING: 3,
                }
            else:
                # Advanced: focus on discrimination and retrieval
                priorities = {
                    PedagogicalTechnique.INTERLEAVING: 1,
                    PedagogicalTechnique.RETRIEVAL_PRACTICE: 2,
                    PedagogicalTechnique.FEYNMAN: 3,
                }
            return priorities.get(t, 10)

        recommended.sort(key=priority)
        return recommended[:max_techniques]

    def transform(
        self,
        concept: Concept,
        mastery: ConceptMastery,
        techniques: list[PedagogicalTechnique] | None = None,
        context: str = "",
    ) -> TechniqueResult:
        """Apply pedagogical techniques to enhance learning content.

        Args:
            concept: The concept to enhance
            mastery: The learner's current mastery
            techniques: Specific techniques to apply (auto-selects if None)
            context: Additional context for transformations

        Returns:
            TechniqueResult with all transformations applied
        """
        if techniques is None:
            techniques = self.get_recommended_techniques(concept, mastery)

        content = context if context else concept.description
        all_metadata: dict[str, Any] = {"techniques_applied": []}

        for technique in techniques:
            if technique not in self._strategies:
                continue

            strategy = self._strategies[technique]
            result = strategy.apply(
                concept=concept,
                mastery=mastery,
                context=content,
                llm_callback=self.llm_callback,
            )

            content = result.transformed_content
            all_metadata["techniques_applied"].append(technique.value)
            all_metadata.update(result.metadata)

        return TechniqueResult(
            technique=techniques[0] if techniques else PedagogicalTechnique.SCAFFOLDING,
            original_content=context if context else concept.description,
            transformed_content=content,
            metadata=all_metadata,
        )

    def apply_single(
        self,
        technique: PedagogicalTechnique,
        concept: Concept,
        mastery: ConceptMastery,
        context: str = "",
    ) -> TechniqueResult:
        """Apply a single pedagogical technique.

        Args:
            technique: The technique to apply
            concept: The concept to enhance
            mastery: The learner's current mastery
            context: Additional context

        Returns:
            TechniqueResult from the technique
        """
        if technique not in self._strategies:
            return TechniqueResult(
                technique=technique,
                original_content=context,
                transformed_content=context,
                metadata={"error": "Technique not implemented"},
            )

        return self._strategies[technique].apply(
            concept=concept,
            mastery=mastery,
            context=context,
            llm_callback=self.llm_callback,
        )

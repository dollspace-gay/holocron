"""Template for creating custom domain adapters.

This module provides a complete template for creating new skill domain
adapters for Holocron. Copy this file and customize for your domain.

Example usage:
    1. Copy this file to your_domain.py
    2. Rename TemplateDomainAdapter to YourDomainAdapter
    3. Implement the abstract methods
    4. Register in __init__.py or at runtime

See the reading.py and programming.py adapters for complete examples.
"""

from dataclasses import field
from typing import Any

from holocron.core.models import (
    Assessment,
    AssessmentOption,
    AssessmentType,
    BloomLevel,
    Concept,
    ConceptMastery,
)
from holocron.domains.base import DomainAdapter, DomainConfig


class TemplateDomainAdapter(DomainAdapter):
    """Template domain adapter - copy and customize for your domain.

    Steps to create a custom domain:
    1. Define your domain configuration (ID, name, file types)
    2. Implement concept extraction from content
    3. Implement assessment generation for concepts
    4. Optionally customize scaffolding prompts

    Example:
        ```python
        class MusicTheoryAdapter(TemplateDomainAdapter):
            @property
            def config(self) -> DomainConfig:
                return DomainConfig(
                    domain_id="music-theory",
                    display_name="Music Theory",
                    description="Learn music theory fundamentals",
                    file_extensions=[".txt", ".abc", ".musicxml"],
                    scaffold_levels=5,
                    mastery_threshold=80,
                )

            def extract_concepts(self, content: str) -> list[Concept]:
                # Extract musical concepts from content
                ...
        ```
    """

    @property
    def config(self) -> DomainConfig:
        """Return domain configuration.

        Customize these values for your domain:
        - domain_id: Unique identifier (e.g., "music-theory")
        - display_name: Human-readable name
        - description: Brief description
        - file_extensions: Supported file types
        - scaffold_levels: Number of scaffold levels (default 5)
        - mastery_threshold: % required for mastery (default 80)
        """
        return DomainConfig(
            domain_id="template-domain",
            display_name="Template Domain",
            description="A template for creating custom domains",
            file_extensions=[".txt", ".md"],
            scaffold_levels=5,
            mastery_threshold=80,
        )

    def validate_content(self, content: str) -> bool:
        """Validate if content is suitable for this domain.

        Override to add domain-specific validation.

        Args:
            content: The raw content to validate

        Returns:
            True if content can be processed by this domain
        """
        # Basic validation - customize for your domain
        if not content or len(content.strip()) < 10:
            return False
        return True

    def preprocess_content(self, content: str) -> str:
        """Preprocess content before concept extraction.

        Override to add domain-specific preprocessing:
        - Clean up formatting
        - Normalize text
        - Extract relevant sections

        Args:
            content: Raw content

        Returns:
            Preprocessed content
        """
        # Example preprocessing
        content = content.strip()
        # Add your preprocessing logic here
        return content

    def extract_concepts(self, content: str) -> list[Concept]:
        """Extract concepts from content.

        This is the core method - implement your extraction logic here.

        Args:
            content: Preprocessed content

        Returns:
            List of Concept objects found in the content
        """
        concepts = []

        # Example: Extract concepts based on patterns
        # Replace with your domain-specific extraction logic

        # Example concept
        example_concept = Concept(
            concept_id=f"{self.config.domain_id}.example_concept",
            domain_id=self.config.domain_id,
            name="Example Concept",
            description="This is an example concept. Replace with real extraction.",
            difficulty_score=5,
            bloom_level=BloomLevel.KNOWLEDGE,
            examples=["Example 1", "Example 2"],
            analogies=["Think of it like..."],
            domain_data={
                "source": "example",
                "category": "general",
            },
        )
        concepts.append(example_concept)

        return concepts

    def generate_assessment(
        self,
        concept: Concept,
        bloom_level: BloomLevel,
        context: str = "",
    ) -> Assessment:
        """Generate an assessment question for a concept.

        Create appropriate questions based on Bloom's Taxonomy level:
        - KNOWLEDGE: Define, recall, list
        - COMPREHENSION: Explain, summarize, paraphrase
        - APPLICATION: Apply, use, demonstrate
        - ANALYSIS: Compare, contrast, differentiate
        - SYNTHESIS: Create, design, construct
        - EVALUATION: Judge, critique, justify

        Args:
            concept: The concept to assess
            bloom_level: Target cognitive level
            context: Optional context for the question

        Returns:
            Assessment object with question and grading info
        """
        # Generate question based on Bloom level
        questions = {
            BloomLevel.KNOWLEDGE: f"Define {concept.name}.",
            BloomLevel.COMPREHENSION: f"Explain {concept.name} in your own words.",
            BloomLevel.APPLICATION: f"Give an example of how {concept.name} is used.",
            BloomLevel.ANALYSIS: f"Compare {concept.name} with a related concept.",
            BloomLevel.SYNTHESIS: f"How would you combine {concept.name} with other ideas?",
            BloomLevel.EVALUATION: f"Evaluate the importance of {concept.name}.",
        }

        question = questions.get(bloom_level, questions[BloomLevel.KNOWLEDGE])

        # Determine assessment type based on level
        if bloom_level in [BloomLevel.KNOWLEDGE, BloomLevel.COMPREHENSION]:
            # Simpler levels can use multiple choice
            return self._create_multiple_choice(concept, bloom_level, question)
        else:
            # Higher levels use free response
            return Assessment(
                assessment_id=f"assess-{concept.concept_id}-{bloom_level.value}",
                concept_id=concept.concept_id,
                bloom_level=bloom_level,
                assessment_type=AssessmentType.FREE_RESPONSE,
                question=question,
                context=context,
                rubric=f"Evaluate understanding of {concept.name} at {bloom_level.value} level",
                sample_answer=concept.description,
                difficulty=self._map_bloom_to_difficulty(bloom_level),
            )

    def _create_multiple_choice(
        self,
        concept: Concept,
        bloom_level: BloomLevel,
        question: str,
    ) -> Assessment:
        """Create a multiple choice assessment.

        Customize this to generate domain-appropriate options.
        """
        # Generate options - customize for your domain
        options = [
            AssessmentOption(
                text=concept.description[:100] if concept.description else "Correct answer",
                is_correct=True,
                explanation="This is the correct definition.",
            ),
            AssessmentOption(
                text="An incorrect but plausible answer",
                is_correct=False,
            ),
            AssessmentOption(
                text="Another incorrect option",
                is_correct=False,
            ),
            AssessmentOption(
                text="A clearly wrong option",
                is_correct=False,
            ),
        ]

        return Assessment(
            assessment_id=f"assess-{concept.concept_id}-{bloom_level.value}",
            concept_id=concept.concept_id,
            bloom_level=bloom_level,
            assessment_type=AssessmentType.MULTIPLE_CHOICE,
            question=question,
            options=options,
            difficulty=self._map_bloom_to_difficulty(bloom_level),
        )

    def _map_bloom_to_difficulty(self, bloom_level: BloomLevel) -> int:
        """Map Bloom level to difficulty score (1-10)."""
        mapping = {
            BloomLevel.KNOWLEDGE: 3,
            BloomLevel.COMPREHENSION: 4,
            BloomLevel.APPLICATION: 6,
            BloomLevel.ANALYSIS: 7,
            BloomLevel.SYNTHESIS: 8,
            BloomLevel.EVALUATION: 9,
        }
        return mapping.get(bloom_level, 5)

    def get_scaffold_prompt(
        self,
        scaffold_level: int,
        concept_mastery_pairs: list[tuple[Concept, ConceptMastery]],
    ) -> str:
        """Generate a scaffolding prompt for content transformation.

        Customize the scaffolding levels for your domain:
        - Level 1: Maximum support (definitions, examples, step-by-step)
        - Level 5: Minimal support (just the content)

        Args:
            scaffold_level: Current scaffold level (1-5)
            concept_mastery_pairs: Concepts and their mastery levels

        Returns:
            System prompt for LLM transformation
        """
        concept_list = ", ".join(c.name for c, _ in concept_mastery_pairs[:5])

        if scaffold_level == 1:
            return f"""Transform this content with maximum learning support.

Target concepts: {concept_list}

Add:
- Clear definitions for all key terms
- Multiple examples for each concept
- Step-by-step explanations
- Real-world analogies
- Visual descriptions
- Prerequisite knowledge review"""

        elif scaffold_level == 2:
            return f"""Transform this content with significant support.

Target concepts: {concept_list}

Add:
- Definitions for difficult terms
- Examples for main concepts
- Clarifying explanations where needed
- Helpful analogies"""

        elif scaffold_level == 3:
            return f"""Transform this content with moderate support.

Target concepts: {concept_list}

Add:
- Brief definitions for technical terms
- One example per main concept
- Clarification of complex points"""

        elif scaffold_level == 4:
            return f"""Lightly enhance this content.

Target concepts: {concept_list}

Add only:
- Minimal definitions for unusual terms
- Brief clarifications where essential"""

        else:  # Level 5
            return f"""Present this content with minimal modification.

Target concepts: {concept_list}

Maintain the original content, making only essential formatting improvements."""

    def postprocess_content(self, content: str) -> str:
        """Postprocess transformed content.

        Override to add domain-specific formatting or cleanup.

        Args:
            content: Transformed content

        Returns:
            Final processed content
        """
        return content


# =============================================================================
# Registration example
# =============================================================================

# To register your adapter, add this in your __init__.py or main module:
#
# from holocron.domains.registry import DomainRegistry
# from your_module import YourDomainAdapter
#
# DomainRegistry.register(YourDomainAdapter())

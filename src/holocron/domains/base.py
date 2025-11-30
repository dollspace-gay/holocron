"""Base classes for skill domain adapters.

This module defines the abstract interface that all domain adapters must implement,
along with the configuration dataclass for domain settings.

Domain adapters are the key abstraction that allows Holocron to support
different skill domains (reading, programming, music, etc.) through a
common interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from holocron.core.models import (
    Assessment,
    BloomLevel,
    Concept,
    ConceptMastery,
)

if TYPE_CHECKING:
    from holocron.core.models import ConceptGraph


@dataclass
class DomainConfig:
    """Configuration for a skill domain.

    Defines the settings and capabilities of a domain adapter.

    Attributes:
        domain_id: Unique identifier (e.g., "python-programming", "reading-skills")
        display_name: Human-readable name
        description: Brief description of the domain
        concept_extractors: List of extraction strategies to use
        mastery_model: How mastery is calculated
        initial_mastery: Starting mastery for new concepts
        mastery_decay_rate: Daily decay rate for spaced repetition
        scaffold_levels: Number of scaffolding levels
        bloom_levels: Bloom taxonomy levels supported
        pedagogical_techniques: Learning techniques to apply
        file_extensions: File types this domain can process
    """

    domain_id: str
    display_name: str
    description: str

    # Concept extraction settings
    concept_extractors: list[str] = field(default_factory=list)

    # Mastery settings
    mastery_model: str = "hybrid"  # "exposure-count", "spaced-repetition", "assessment-based", "hybrid"
    initial_mastery: float = 0.0
    mastery_decay_rate: float = 0.05  # Daily decay for spaced repetition

    # Scaffolding settings
    scaffold_levels: int = 5

    # Assessment settings
    bloom_levels: list[str] = field(
        default_factory=lambda: [
            "knowledge",
            "comprehension",
            "application",
        ]
    )

    # Pedagogical techniques to apply
    pedagogical_techniques: list[str] = field(
        default_factory=lambda: [
            "elaborative-encoding",
            "dual-coding",
            "feynman-technique",
            "interleaving",
            "retrieval-practice",
        ]
    )

    # File handling
    file_extensions: list[str] = field(default_factory=list)


class DomainAdapter(ABC):
    """Abstract base class for domain-specific adapters.

    Each skill domain (reading, programming, music theory, etc.)
    implements this interface to customize:
    - Concept extraction from content
    - Assessment generation
    - Content transformation prompts
    - Pedagogical technique application

    Example:
        ```python
        @DomainRegistry.register("python-programming")
        class PythonAdapter(DomainAdapter):
            @property
            def config(self) -> DomainConfig:
                return DomainConfig(
                    domain_id="python-programming",
                    display_name="Python Programming",
                    ...
                )

            def extract_concepts(self, content: str) -> list[Concept]:
                # Extract Python concepts from code/docs
                ...
        ```
    """

    @property
    @abstractmethod
    def config(self) -> DomainConfig:
        """Return the domain configuration.

        Returns:
            DomainConfig with all settings for this domain
        """
        ...

    @abstractmethod
    def extract_concepts(self, content: str) -> list[Concept]:
        """Extract learnable concepts from content.

        This is the core abstraction that replaces word extraction
        in the reading domain with semantic concept extraction.

        Args:
            content: The text content to analyze

        Returns:
            List of Concept objects found in the content
        """
        ...

    @abstractmethod
    def generate_assessment(
        self,
        concept: Concept,
        bloom_level: BloomLevel,
        context: str = "",
    ) -> Assessment:
        """Generate an assessment for a concept at a given Bloom level.

        Replaces TrapGenerator with domain-aware assessment generation.

        Args:
            concept: The concept to assess
            bloom_level: The cognitive level to test
            context: Optional context from the learning material

        Returns:
            Assessment object ready for the learner
        """
        ...

    @abstractmethod
    def get_scaffold_prompt(
        self,
        level: int,
        concepts: list[tuple[Concept, ConceptMastery]],
    ) -> str:
        """Generate system prompt for content transformation.

        Creates the LLM system prompt that guides how content should
        be transformed based on the learner's mastery levels.

        Args:
            level: Overall scaffold level (1=max support, N=min support)
            concepts: List of (concept, mastery) tuples for context

        Returns:
            System prompt string for the LLM
        """
        ...

    def build_concept_graph(self, concepts: list[Concept]) -> "ConceptGraph":
        """Build a concept graph from extracted concepts.

        Default implementation creates a graph from concept relationships.
        Override for domain-specific graph construction.

        Args:
            concepts: List of concepts to build graph from

        Returns:
            ConceptGraph with concepts and their relationships
        """
        from holocron.core.models import ConceptGraph

        graph = ConceptGraph(domain_id=self.config.domain_id)
        for concept in concepts:
            graph.add_concept(concept)
        return graph

    def get_difficulty_tier(self, concept: Concept) -> str:
        """Categorize concept difficulty into tiers.

        Args:
            concept: The concept to categorize

        Returns:
            Tier name: "easy", "medium", or "challenging"
        """
        score = concept.difficulty_score
        if score <= 3:
            return "easy"
        elif score <= 6:
            return "medium"
        else:
            return "challenging"

    def apply_pedagogical_techniques(
        self,
        content: str,
        concepts: list[Concept],
        techniques: list[str] | None = None,
    ) -> str:
        """Apply pedagogical techniques to content.

        Default implementation returns content unchanged.
        Override for domain-specific technique application.

        Args:
            content: The content to enhance
            concepts: Concepts present in the content
            techniques: Techniques to apply (defaults to config)

        Returns:
            Enhanced content string
        """
        return content

    def validate_content(self, content: str) -> bool:
        """Validate that content is suitable for this domain.

        Args:
            content: The content to validate

        Returns:
            True if content can be processed by this domain
        """
        return len(content.strip()) > 0

    def preprocess_content(self, content: str) -> str:
        """Preprocess content before concept extraction.

        Override for domain-specific preprocessing.

        Args:
            content: Raw content

        Returns:
            Preprocessed content
        """
        return content.strip()

    def postprocess_content(self, content: str) -> str:
        """Postprocess transformed content.

        Override for domain-specific postprocessing.

        Args:
            content: Transformed content

        Returns:
            Final content
        """
        return content

"""Core data models for Holocron skill training platform.

This module defines the fundamental data structures used throughout Holocron:
- Concept: A learnable unit of knowledge within a domain
- ConceptMastery: Tracks a learner's progress on a concept
- Assessment: Questions/exercises to verify understanding
- LearnerProfile: Complete learner state across domains
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class BloomLevel(str, Enum):
    """Bloom's Taxonomy cognitive levels for assessments."""

    KNOWLEDGE = "knowledge"  # Remember: Define, list, recall
    COMPREHENSION = "comprehension"  # Understand: Explain, summarize, paraphrase
    APPLICATION = "application"  # Apply: Use, demonstrate, solve
    ANALYSIS = "analysis"  # Analyze: Compare, contrast, differentiate
    SYNTHESIS = "synthesis"  # Create: Design, construct, develop
    EVALUATION = "evaluation"  # Evaluate: Judge, critique, justify


class AssessmentType(str, Enum):
    """Types of assessment questions."""

    MULTIPLE_CHOICE = "multiple_choice"
    FREE_RESPONSE = "free_response"
    CODE_EXERCISE = "code_exercise"
    MATCHING = "matching"
    FILL_IN_BLANK = "fill_in_blank"
    SCENARIO = "scenario"


@dataclass
class Concept:
    """A learnable concept within a skill domain.

    Generalizes WordEntry from Anchor-Text to represent any learnable
    unit of knowledge, from vocabulary words to programming patterns.

    Attributes:
        concept_id: Unique identifier (e.g., "python.list_comprehension")
        domain_id: Parent domain identifier
        name: Human-readable name
        description: Brief explanation of the concept
        prerequisites: Concept IDs that should be learned first
        related_concepts: Semantically related concepts
        parent_concept: For hierarchical organization
        canonical_definition: The "official" definition
        examples: Concrete examples demonstrating the concept
        analogies: Real-world analogies for elaborative encoding
        visual_description: Description for dual coding
        difficulty_score: Complexity rating (1-10)
        bloom_level: Target cognitive level
        tags: Classification tags
        domain_data: Domain-specific extension data
    """

    concept_id: str
    domain_id: str
    name: str
    description: str

    # Relationships
    prerequisites: list[str] = field(default_factory=list)
    related_concepts: list[str] = field(default_factory=list)
    parent_concept: str | None = None

    # Content for pedagogical techniques
    canonical_definition: str = ""
    examples: list[str] = field(default_factory=list)
    analogies: list[str] = field(default_factory=list)
    visual_description: str = ""

    # Metadata
    difficulty_score: int = 5
    bloom_level: BloomLevel = BloomLevel.KNOWLEDGE
    tags: list[str] = field(default_factory=list)

    # Domain-specific extensions
    domain_data: dict[str, Any] = field(default_factory=dict)


@dataclass
class ConceptMastery:
    """Tracks a learner's mastery of a single concept.

    Evolves from WordExposure: instead of simple exposure counts,
    tracks multi-dimensional mastery with spaced repetition support.

    The mastery model uses three dimensions aligned with Bloom's Taxonomy:
    - Recognition: Can identify and define the concept
    - Comprehension: Can explain in own words
    - Application: Can apply to new situations

    Attributes:
        concept_id: The concept being tracked
        learner_id: The learner this mastery belongs to
        recognition_score: Ability to define (0-100)
        comprehension_score: Ability to explain (0-100)
        application_score: Ability to apply (0-100)
        exposure_count: Total times encountered
        first_exposure: When first seen
        last_exposure: Most recent exposure
        last_assessment: Most recent assessment
        assessment_results: History of assessment attempts
        ease_factor: SM-2 algorithm ease factor
        interval_days: Days until next review
        next_review: Scheduled review date
    """

    concept_id: str
    learner_id: str

    # Multi-dimensional mastery scores (0-100)
    recognition_score: float = 0.0
    comprehension_score: float = 0.0
    application_score: float = 0.0

    # Exposure tracking
    exposure_count: int = 0
    first_exposure: datetime | None = None
    last_exposure: datetime | None = None
    last_assessment: datetime | None = None

    # Assessment history (stored as list of result IDs or inline)
    assessment_results: list["AssessmentResult"] = field(default_factory=list)

    # Spaced repetition (SM-2 algorithm)
    ease_factor: float = 2.5
    interval_days: float = 1.0
    next_review: datetime | None = None

    @property
    def overall_mastery(self) -> float:
        """Calculate weighted average of mastery dimensions.

        Weights application highest as it represents deeper understanding.
        """
        return (
            self.recognition_score * 0.2
            + self.comprehension_score * 0.3
            + self.application_score * 0.5
        )

    def get_scaffold_level(self, num_levels: int = 5) -> int:
        """Determine scaffolding level based on mastery.

        Maps 0-100 mastery to scaffold levels where:
        - Level 1 = MAX support (low mastery)
        - Level N = MIN support (high mastery)

        Args:
            num_levels: Total number of scaffold levels (default 5)

        Returns:
            Scaffold level from 1 (max support) to num_levels (min support)
        """
        mastery = self.overall_mastery

        if mastery < 20:
            return 1  # Full support
        elif mastery < 40:
            return 2
        elif mastery < 60:
            return 3
        elif mastery < 80:
            return 4
        else:
            return num_levels  # Minimal support

    def is_due_for_review(self) -> bool:
        """Check if concept is due for spaced repetition review."""
        if self.next_review is None:
            return True
        return _utc_now() >= self.next_review


@dataclass
class AssessmentOption:
    """An option in a multiple-choice assessment."""

    text: str
    is_correct: bool
    is_lookalike: bool = False  # For decoder traps
    explanation: str = ""


@dataclass
class Assessment:
    """A learning assessment question.

    Generalizes DecoderTrap to support Bloom's Taxonomy levels
    and multiple question types.

    Attributes:
        assessment_id: Unique identifier
        concept_id: The concept being assessed
        bloom_level: Cognitive level being tested
        assessment_type: Type of question
        question: The question text
        context: Optional scenario or passage context
        options: For multiple choice questions
        rubric: Grading criteria for LLM evaluation
        sample_answer: Example correct response
        difficulty: Question difficulty (1-10)
        time_estimate_seconds: Expected time to answer
        explanation: Shown after answering
        hints: Progressive hints if struggling
        follow_up_concepts: Concepts to review if wrong
    """

    assessment_id: str
    concept_id: str
    bloom_level: BloomLevel
    assessment_type: AssessmentType

    question: str
    context: str = ""

    # For multiple choice
    options: list[AssessmentOption] = field(default_factory=list)

    # For free response / code exercises
    rubric: str = ""
    sample_answer: str = ""

    # Metadata
    difficulty: int = 5
    time_estimate_seconds: int = 60
    explanation: str = ""

    # Pedagogical support
    hints: list[str] = field(default_factory=list)
    follow_up_concepts: list[str] = field(default_factory=list)


@dataclass
class AssessmentResult:
    """Result of a learner's assessment attempt."""

    assessment_id: str
    learner_id: str
    timestamp: datetime

    response: str
    is_correct: bool
    score: float  # 0-1 for partial credit

    # For LLM-graded responses
    feedback: str = ""
    grading_rationale: str = ""
    strengths: list[str] = field(default_factory=list)
    areas_for_improvement: list[str] = field(default_factory=list)


@dataclass
class LearningSession:
    """A single learning session."""

    session_id: str
    learner_id: str
    domain_id: str
    started_at: datetime
    ended_at: datetime | None = None

    concepts_studied: list[str] = field(default_factory=list)
    assessments_completed: list[str] = field(default_factory=list)
    duration_minutes: int = 0


@dataclass
class LearnerPreferences:
    """Learner preferences and settings."""

    preferred_scaffold_level: int | None = None
    explanation_style: str = "detailed"  # "detailed", "concise", "visual", "example-heavy"
    theme: str = "system"  # "light", "dark", "system"
    daily_goal_minutes: int = 30
    notification_enabled: bool = True


@dataclass
class LearnerProfile:
    """Complete learner state across all domains.

    Manages cross-session mastery tracking and learner preferences.

    Attributes:
        learner_id: Unique identifier
        name: Display name
        created_at: When profile was created
        preferences: Learner settings
        domain_mastery: Mastery data organized by domain
        sessions: Learning session history
        total_study_time_minutes: Cumulative study time
        concepts_mastered: Count of concepts at 80%+ mastery
        current_streak_days: Consecutive days studied
        last_study_date: Most recent study session
    """

    learner_id: str
    name: str
    created_at: datetime = field(default_factory=_utc_now)

    preferences: LearnerPreferences = field(default_factory=LearnerPreferences)

    # Per-domain mastery: {domain_id: {concept_id: ConceptMastery}}
    domain_mastery: dict[str, dict[str, ConceptMastery]] = field(default_factory=dict)

    # Session history
    sessions: list[LearningSession] = field(default_factory=list)

    # Analytics
    total_study_time_minutes: int = 0
    concepts_mastered: int = 0
    current_streak_days: int = 0
    last_study_date: datetime | None = None

    def get_mastery(self, domain_id: str, concept_id: str) -> ConceptMastery:
        """Get or create mastery record for a concept.

        Args:
            domain_id: The skill domain
            concept_id: The concept within that domain

        Returns:
            ConceptMastery record (creates new if doesn't exist)
        """
        if domain_id not in self.domain_mastery:
            self.domain_mastery[domain_id] = {}

        if concept_id not in self.domain_mastery[domain_id]:
            self.domain_mastery[domain_id][concept_id] = ConceptMastery(
                concept_id=concept_id,
                learner_id=self.learner_id,
            )

        return self.domain_mastery[domain_id][concept_id]

    def get_domain_overall_mastery(self, domain_id: str) -> float:
        """Calculate average mastery across all concepts in a domain.

        Args:
            domain_id: The skill domain

        Returns:
            Average mastery percentage (0-100)
        """
        if domain_id not in self.domain_mastery:
            return 0.0

        masteries = self.domain_mastery[domain_id].values()
        if not masteries:
            return 0.0

        return sum(m.overall_mastery for m in masteries) / len(masteries)

    def get_concepts_due_for_review(self, domain_id: str | None = None) -> list[str]:
        """Get concept IDs due for spaced repetition review.

        Args:
            domain_id: Optional filter by domain

        Returns:
            List of concept_ids due for review
        """
        due = []
        domains = [domain_id] if domain_id else self.domain_mastery.keys()

        for d_id in domains:
            if d_id not in self.domain_mastery:
                continue
            for concept_id, mastery in self.domain_mastery[d_id].items():
                if mastery.is_due_for_review():
                    due.append(concept_id)

        return due


@dataclass
class ConceptGraph:
    """Knowledge graph of concepts and their relationships.

    Provides structure for learning paths and prerequisite tracking.

    Attributes:
        domain_id: The domain this graph represents
        concepts: All concepts indexed by ID
        prerequisite_edges: (from_id, to_id) where from blocks to
        related_edges: Soft connections between concepts
        hierarchy_edges: Parent-child relationships
    """

    domain_id: str
    concepts: dict[str, Concept] = field(default_factory=dict)

    prerequisite_edges: list[tuple[str, str]] = field(default_factory=list)
    related_edges: list[tuple[str, str]] = field(default_factory=list)
    hierarchy_edges: list[tuple[str, str]] = field(default_factory=list)

    def add_concept(self, concept: Concept) -> None:
        """Add a concept to the graph."""
        self.concepts[concept.concept_id] = concept

        # Add prerequisite edges
        for prereq in concept.prerequisites:
            self.prerequisite_edges.append((prereq, concept.concept_id))

        # Add related edges
        for related in concept.related_concepts:
            if (concept.concept_id, related) not in self.related_edges:
                self.related_edges.append((concept.concept_id, related))

        # Add hierarchy edge
        if concept.parent_concept:
            self.hierarchy_edges.append((concept.parent_concept, concept.concept_id))

    def get_prerequisites(self, concept_id: str) -> list[str]:
        """Get all prerequisite concept IDs for a concept."""
        return [from_id for from_id, to_id in self.prerequisite_edges if to_id == concept_id]

    def get_learning_path(self, target_concept: str) -> list[str]:
        """Get topologically sorted list of concepts to learn.

        Returns concepts in order such that all prerequisites
        come before the concepts that depend on them.

        Args:
            target_concept: The concept to build a path to

        Returns:
            Ordered list of concept_ids to learn
        """
        visited: set[str] = set()
        path: list[str] = []

        def dfs(concept_id: str) -> None:
            if concept_id in visited:
                return
            visited.add(concept_id)

            for prereq in self.get_prerequisites(concept_id):
                dfs(prereq)

            path.append(concept_id)

        dfs(target_concept)
        return path

    def get_next_concepts(self, mastered: set[str]) -> list[str]:
        """Get concepts whose prerequisites are all satisfied.

        Args:
            mastered: Set of concept_ids already mastered

        Returns:
            List of concept_ids ready to learn
        """
        ready = []
        for concept_id in self.concepts:
            if concept_id in mastered:
                continue

            prereqs = self.get_prerequisites(concept_id)
            if all(p in mastered for p in prereqs):
                ready.append(concept_id)

        return ready

    def get_related_for_interleaving(
        self, current_concept: str, count: int = 3
    ) -> list[str]:
        """Get related concepts for interleaved practice.

        Args:
            current_concept: The concept currently being studied
            count: Maximum number of related concepts to return

        Returns:
            List of related concept_ids for interleaving
        """
        related = []

        # Get directly related
        for c1, c2 in self.related_edges:
            if c1 == current_concept and c2 not in related:
                related.append(c2)
            elif c2 == current_concept and c1 not in related:
                related.append(c1)

            if len(related) >= count:
                break

        return related[:count]

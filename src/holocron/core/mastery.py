"""Mastery Engine for adaptive scaffolding and spaced repetition.

This module implements the MasteryEngine that tracks learner progress
and manages adaptive scaffolding. It evolves from Anchor-Text's
ScaffoldingContext to support:

- Multi-dimensional mastery tracking (recognition, comprehension, application)
- Spaced repetition using the SM-2 algorithm
- Mastery decay over time
- Adaptive scaffold level calculation
"""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)

from holocron.core.models import (
    AssessmentResult,
    BloomLevel,
    Concept,
    ConceptMastery,
    LearnerProfile,
)

if TYPE_CHECKING:
    from holocron.domains.base import DomainConfig


class MasteryModel(str, Enum):
    """Mastery calculation models."""

    EXPOSURE_COUNT = "exposure-count"  # Original Anchor-Text model
    SPACED_REPETITION = "spaced-repetition"  # SM-2 algorithm
    ASSESSMENT_BASED = "assessment-based"  # Only update on assessment
    HYBRID = "hybrid"  # Combination of exposure and assessment


@dataclass
class MasteryUpdate:
    """Result of a mastery update operation."""

    concept_id: str
    previous_mastery: float
    new_mastery: float
    previous_scaffold_level: int
    new_scaffold_level: int
    mastery_delta: float
    new_exposure_count: int = 0
    new_next_review: datetime | None = None

    @property
    def improved(self) -> bool:
        """Check if mastery improved."""
        return self.mastery_delta > 0

    @property
    def level_changed(self) -> bool:
        """Check if scaffold level changed."""
        return self.previous_scaffold_level != self.new_scaffold_level


class MasteryEngine:
    """Manages learner mastery tracking and adaptive scaffolding.

    Evolves ScaffoldingContext from exposure-counting to multi-dimensional
    mastery with spaced repetition support.

    Example:
        ```python
        engine = MasteryEngine(domain_config, learner_profile)

        # Update from content exposure
        update = engine.update_from_exposure("python.list_comprehension")

        # Update from assessment
        result = AssessmentResult(...)
        update = engine.update_from_assessment(
            "python.list_comprehension",
            result,
            BloomLevel.APPLICATION
        )

        # Get scaffold level for a concept
        level = engine.get_scaffold_level("python.list_comprehension")
        ```
    """

    def __init__(
        self,
        domain_config: "DomainConfig",
        learner_profile: LearnerProfile,
    ) -> None:
        """Initialize the mastery engine.

        Args:
            domain_config: Configuration for the skill domain
            learner_profile: The learner's profile
        """
        self.config = domain_config
        self.profile = learner_profile
        self.mastery_model = MasteryModel(domain_config.mastery_model)

    def update_from_exposure(
        self,
        concept_id: str,
        exposure_quality: float = 1.0,
    ) -> MasteryUpdate:
        """Update mastery after learner is exposed to a concept.

        Recognition improves with exposure using diminishing returns.

        Args:
            concept_id: The concept that was encountered
            exposure_quality: Quality of engagement (0-1)

        Returns:
            MasteryUpdate with before/after mastery values
        """
        mastery = self.profile.get_mastery(self.config.domain_id, concept_id)

        previous_mastery = mastery.overall_mastery
        previous_level = mastery.get_scaffold_level(self.config.scaffold_levels)

        # Update exposure tracking
        mastery.exposure_count += 1
        now = _utc_now()

        if mastery.first_exposure is None:
            mastery.first_exposure = now
        mastery.last_exposure = now

        # Recognition improves with exposure (diminishing returns)
        # Formula: gain = base_gain * quality * (1 - current/max)
        recognition_gain = 15 * exposure_quality * (1 - mastery.recognition_score / 100)
        mastery.recognition_score = min(100, mastery.recognition_score + recognition_gain)

        # Small comprehension gain from exposure
        if self.mastery_model in (MasteryModel.EXPOSURE_COUNT, MasteryModel.HYBRID):
            comprehension_gain = 5 * exposure_quality * (1 - mastery.comprehension_score / 100)
            mastery.comprehension_score = min(100, mastery.comprehension_score + comprehension_gain)

        new_mastery = mastery.overall_mastery
        new_level = mastery.get_scaffold_level(self.config.scaffold_levels)

        return MasteryUpdate(
            concept_id=concept_id,
            previous_mastery=previous_mastery,
            new_mastery=new_mastery,
            previous_scaffold_level=previous_level,
            new_scaffold_level=new_level,
            mastery_delta=new_mastery - previous_mastery,
            new_exposure_count=mastery.exposure_count,
            new_next_review=mastery.next_review,
        )

    def update_from_assessment(
        self,
        concept_id: str,
        result: AssessmentResult,
        bloom_level: BloomLevel,
    ) -> MasteryUpdate:
        """Update mastery after an assessment.

        Different Bloom levels affect different mastery dimensions.

        Args:
            concept_id: The concept that was assessed
            result: The assessment result
            bloom_level: The cognitive level that was tested

        Returns:
            MasteryUpdate with before/after mastery values
        """
        mastery = self.profile.get_mastery(self.config.domain_id, concept_id)

        previous_mastery = mastery.overall_mastery
        previous_level = mastery.get_scaffold_level(self.config.scaffold_levels)

        # Record the assessment
        mastery.assessment_results.append(result)
        mastery.last_assessment = _utc_now()

        # Map Bloom levels to mastery dimensions
        if bloom_level == BloomLevel.KNOWLEDGE:
            dimension = "recognition_score"
        elif bloom_level in (BloomLevel.COMPREHENSION, BloomLevel.ANALYSIS):
            dimension = "comprehension_score"
        else:  # APPLICATION, SYNTHESIS, EVALUATION
            dimension = "application_score"

        current = getattr(mastery, dimension)

        if result.is_correct:
            # Increase mastery (diminishing returns)
            gain = 20 * result.score * (1 - current / 100)
            setattr(mastery, dimension, min(100, current + gain))

            # Update spaced repetition
            self._update_spaced_repetition(mastery, result.score)
        else:
            # Decrease mastery (learning from mistakes)
            loss = 10 * (1 - result.score)
            setattr(mastery, dimension, max(0, current - loss))

            # Reset interval for spaced repetition
            mastery.interval_days = 1.0
            mastery.next_review = _utc_now() + timedelta(days=1)

        new_mastery = mastery.overall_mastery
        new_level = mastery.get_scaffold_level(self.config.scaffold_levels)

        return MasteryUpdate(
            concept_id=concept_id,
            previous_mastery=previous_mastery,
            new_mastery=new_mastery,
            previous_scaffold_level=previous_level,
            new_scaffold_level=new_level,
            mastery_delta=new_mastery - previous_mastery,
        )

    def _update_spaced_repetition(
        self,
        mastery: ConceptMastery,
        quality: float,
    ) -> None:
        """Update spaced repetition parameters using SM-2 algorithm.

        Args:
            mastery: The mastery record to update
            quality: Response quality (0-1)
        """
        # Map quality 0-1 to SM-2's 0-5 scale
        q = int(quality * 5)

        # SM-2 algorithm
        # EF' = EF + (0.1 - (5-q) * (0.08 + (5-q) * 0.02))
        mastery.ease_factor = max(
            1.3,
            mastery.ease_factor + 0.1 - (5 - q) * (0.08 + (5 - q) * 0.02),
        )

        # Update interval
        if q >= 3:  # Correct response
            if mastery.exposure_count <= 1:
                mastery.interval_days = 1
            elif mastery.exposure_count == 2:
                mastery.interval_days = 6
            else:
                mastery.interval_days *= mastery.ease_factor
        else:
            mastery.interval_days = 1

        mastery.next_review = _utc_now() + timedelta(days=mastery.interval_days)

    def get_scaffold_level(self, concept_id: str) -> int:
        """Determine scaffolding level for a concept.

        Args:
            concept_id: The concept to check

        Returns:
            Scaffold level (1=max support, N=min support)
        """
        mastery = self.profile.get_mastery(self.config.domain_id, concept_id)
        return mastery.get_scaffold_level(self.config.scaffold_levels)

    def get_overall_scaffold_level(
        self,
        concepts: list[Concept],
    ) -> int:
        """Calculate overall scaffold level from multiple concepts.

        Uses average mastery to determine the scaffold level.

        Args:
            concepts: List of concepts to consider

        Returns:
            Overall scaffold level
        """
        if not concepts:
            return 1  # Max support for unknown content

        total_mastery = 0.0
        for concept in concepts:
            mastery = self.profile.get_mastery(
                self.config.domain_id, concept.concept_id
            )
            total_mastery += mastery.overall_mastery

        avg_mastery = total_mastery / len(concepts)

        if avg_mastery < 20:
            return 1
        elif avg_mastery < 40:
            return 2
        elif avg_mastery < 60:
            return 3
        elif avg_mastery < 80:
            return 4
        else:
            return self.config.scaffold_levels

    def get_concepts_due_for_review(self) -> list[str]:
        """Get concepts due for spaced repetition review.

        Returns:
            List of concept_ids due for review
        """
        return self.profile.get_concepts_due_for_review(self.config.domain_id)

    def apply_decay(self) -> None:
        """Apply time-based mastery decay for spaced repetition models.

        Only applies if mastery_model uses spaced repetition.
        """
        if self.mastery_model not in (
            MasteryModel.SPACED_REPETITION,
            MasteryModel.HYBRID,
        ):
            return

        now = _utc_now()
        domain_mastery = self.profile.domain_mastery.get(self.config.domain_id, {})

        for mastery in domain_mastery.values():
            if mastery.last_exposure:
                days_since = (now - mastery.last_exposure).days
                decay = self.config.mastery_decay_rate * days_since

                # Apply decay with different rates per dimension
                # Application decays fastest, recognition slowest
                mastery.recognition_score = max(
                    0, mastery.recognition_score - decay * 0.5
                )
                mastery.comprehension_score = max(
                    0, mastery.comprehension_score - decay * 0.7
                )
                mastery.application_score = max(
                    0, mastery.application_score - decay * 1.0
                )

    def get_mastered_concepts(self, threshold: float = 80.0) -> list[str]:
        """Get concepts that have reached mastery threshold.

        Args:
            threshold: Mastery percentage to consider "mastered"

        Returns:
            List of concept_ids at or above threshold
        """
        mastered = []
        domain_mastery = self.profile.domain_mastery.get(self.config.domain_id, {})

        for concept_id, mastery in domain_mastery.items():
            if mastery.overall_mastery >= threshold:
                mastered.append(concept_id)

        return mastered

    def get_struggling_concepts(self, threshold: float = 40.0) -> list[str]:
        """Get concepts the learner is struggling with.

        Args:
            threshold: Mastery percentage below which is "struggling"

        Returns:
            List of concept_ids below threshold with multiple exposures
        """
        struggling = []
        domain_mastery = self.profile.domain_mastery.get(self.config.domain_id, {})

        for concept_id, mastery in domain_mastery.items():
            # Only consider struggling if they've tried multiple times
            if mastery.overall_mastery < threshold and mastery.exposure_count >= 3:
                struggling.append(concept_id)

        return struggling

    def format_exclusion_prompt(self) -> str:
        """Generate prompt text instructing LLM to exclude mastered concepts.

        Similar to Anchor-Text's ScaffoldingContext.format_exclusion_prompt().

        Returns:
            Prompt snippet to append to system prompt, or empty string
        """
        mastered = self.get_mastered_concepts()
        if not mastered:
            return ""

        # Limit to top 50 to avoid overwhelming the prompt
        mastered_limited = mastered[:50]

        return f"""

## MASTERED CONCEPTS (Minimal scaffolding - learner should recall independently):
The learner has demonstrated mastery of these concepts. Use the terms without
extensive re-explanation to reinforce independent recall:
{', '.join(mastered_limited)}
"""

    def get_stats(self) -> dict:
        """Get statistics about current mastery state.

        Returns:
            Dictionary with mastery statistics
        """
        domain_mastery = self.profile.domain_mastery.get(self.config.domain_id, {})

        total_concepts = len(domain_mastery)
        mastered = len(self.get_mastered_concepts())
        struggling = len(self.get_struggling_concepts())
        due_for_review = len(self.get_concepts_due_for_review())

        total_mastery = sum(m.overall_mastery for m in domain_mastery.values())
        avg_mastery = total_mastery / total_concepts if total_concepts > 0 else 0

        return {
            "domain_id": self.config.domain_id,
            "mastery_model": self.mastery_model.value,
            "total_concepts": total_concepts,
            "mastered_concepts": mastered,
            "struggling_concepts": struggling,
            "due_for_review": due_for_review,
            "average_mastery": avg_mastery,
            "mastery_rate": mastered / total_concepts if total_concepts > 0 else 0,
        }

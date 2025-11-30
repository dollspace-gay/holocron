"""Core components for Holocron.

This package contains the fundamental abstractions:
- models: Data structures (Concept, ConceptMastery, Assessment, etc.)
- mastery: MasteryEngine for tracking and adaptive scaffolding
- transformer: ContentTransformer for processing content
- assessment: AssessmentGenerator for creating questions
- grading: LLMGrader for evaluating responses
- pedagogy: PedagogicalTransformer for applying learning techniques
"""

from holocron.core.mastery import MasteryEngine, MasteryModel, MasteryUpdate
from holocron.core.transformer import ContentTransformer, TransformConfig, TransformResult
from holocron.core.grader import AssessmentGrader, GradingResult, grade_response
from holocron.core.pedagogy import (
    PedagogicalTechnique,
    PedagogicalTransformer,
    TechniqueResult,
)
from holocron.core.models import (
    Assessment,
    AssessmentOption,
    AssessmentResult,
    AssessmentType,
    BloomLevel,
    Concept,
    ConceptGraph,
    ConceptMastery,
    LearnerPreferences,
    LearnerProfile,
    LearningSession,
)

__all__ = [
    # Models
    "Concept",
    "ConceptMastery",
    "ConceptGraph",
    "Assessment",
    "AssessmentOption",
    "AssessmentResult",
    "AssessmentType",
    "BloomLevel",
    "LearnerProfile",
    "LearnerPreferences",
    "LearningSession",
    # Mastery
    "MasteryEngine",
    "MasteryModel",
    "MasteryUpdate",
    # Transformer
    "ContentTransformer",
    "TransformConfig",
    "TransformResult",
    # Grader
    "AssessmentGrader",
    "GradingResult",
    "grade_response",
    # Pedagogy
    "PedagogicalTechnique",
    "PedagogicalTransformer",
    "TechniqueResult",
]

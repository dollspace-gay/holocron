"""Holocron: A Generalized Skill Training Platform.

Holocron is an evidence-based learning platform that adapts content
to learner mastery using pedagogical techniques like spaced repetition,
Bloom's Taxonomy assessments, and adaptive scaffolding.

Example:
    ```python
    from holocron import Holocron
    from holocron.domains.registry import DomainRegistry
    from holocron.learner import LearnerProfile

    # Initialize
    holo = Holocron(model="gemini/gemini-2.0-flash")
    learner = LearnerProfile.load_or_create("alice")

    # Transform content with adaptive scaffolding
    result = holo.transform(
        content="def example(): ...",
        domain="python-programming",
        learner=learner,
    )
    ```
"""

__version__ = "0.1.0"

from holocron.config import Settings, get_settings
from holocron.core.models import (
    Assessment,
    AssessmentResult,
    AssessmentType,
    BloomLevel,
    Concept,
    ConceptGraph,
    ConceptMastery,
    LearnerProfile,
)
from holocron.domains.base import DomainAdapter, DomainConfig
from holocron.domains.registry import DomainRegistry

__all__ = [
    # Version
    "__version__",
    # Config
    "Settings",
    "get_settings",
    # Core models
    "Concept",
    "ConceptMastery",
    "ConceptGraph",
    "Assessment",
    "AssessmentResult",
    "AssessmentType",
    "BloomLevel",
    "LearnerProfile",
    # Domain system
    "DomainAdapter",
    "DomainConfig",
    "DomainRegistry",
]

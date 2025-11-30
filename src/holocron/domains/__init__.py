"""Skill domain adapters for Holocron.

This package contains the domain adapter system:
- base: DomainAdapter abstract base class and DomainConfig
- registry: DomainRegistry for registering and retrieving adapters
- reading/: Reading skills domain (Anchor-Text compatibility)
- programming/: Programming skills domain
"""

from holocron.domains.base import DomainAdapter, DomainConfig
from holocron.domains.registry import DomainRegistry

# Import adapters to register them with the registry
from holocron.domains.reading import ReadingSkillsAdapter
from holocron.domains.programming import PythonProgrammingAdapter

__all__ = [
    "DomainAdapter",
    "DomainConfig",
    "DomainRegistry",
    "ReadingSkillsAdapter",
    "PythonProgrammingAdapter",
]

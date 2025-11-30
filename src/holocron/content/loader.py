"""Lesson loader for built-in and custom content.

This module provides the infrastructure for loading and managing lessons.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import json


class LessonCategory(Enum):
    """Categories for organizing lessons."""
    FUNDAMENTALS = "fundamentals"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    PRACTICE = "practice"
    REFERENCE = "reference"


@dataclass
class Lesson:
    """A single lesson with content and metadata."""
    lesson_id: str
    domain_id: str
    title: str
    description: str
    content: str
    category: LessonCategory = LessonCategory.FUNDAMENTALS
    difficulty: int = 1  # 1-10 scale
    estimated_minutes: int = 10
    prerequisites: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "lesson_id": self.lesson_id,
            "domain_id": self.domain_id,
            "title": self.title,
            "description": self.description,
            "content": self.content,
            "category": self.category.value,
            "difficulty": self.difficulty,
            "estimated_minutes": self.estimated_minutes,
            "prerequisites": self.prerequisites,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Lesson":
        """Create from dictionary."""
        return cls(
            lesson_id=data["lesson_id"],
            domain_id=data["domain_id"],
            title=data["title"],
            description=data["description"],
            content=data["content"],
            category=LessonCategory(data.get("category", "fundamentals")),
            difficulty=data.get("difficulty", 1),
            estimated_minutes=data.get("estimated_minutes", 10),
            prerequisites=data.get("prerequisites", []),
            tags=data.get("tags", []),
        )


class LessonLoader:
    """Load and manage lessons from built-in and custom sources."""

    _builtin_lessons: dict[str, list[Lesson]] = {}
    _custom_lessons: dict[str, list[Lesson]] = {}

    @classmethod
    def register_builtin(cls, lesson: Lesson) -> None:
        """Register a built-in lesson."""
        if lesson.domain_id not in cls._builtin_lessons:
            cls._builtin_lessons[lesson.domain_id] = []
        cls._builtin_lessons[lesson.domain_id].append(lesson)

    @classmethod
    def get_lessons(cls, domain_id: str) -> list[Lesson]:
        """Get all lessons for a domain."""
        builtin = cls._builtin_lessons.get(domain_id, [])
        custom = cls._custom_lessons.get(domain_id, [])
        return builtin + custom

    @classmethod
    def get_lesson(cls, domain_id: str, lesson_id: str) -> Optional[Lesson]:
        """Get a specific lesson by ID."""
        for lesson in cls.get_lessons(domain_id):
            if lesson.lesson_id == lesson_id:
                return lesson
        return None

    @classmethod
    def get_lessons_by_category(cls, domain_id: str, category: LessonCategory) -> list[Lesson]:
        """Get lessons filtered by category."""
        return [l for l in cls.get_lessons(domain_id) if l.category == category]

    @classmethod
    def list_domains_with_lessons(cls) -> list[str]:
        """List all domains that have lessons."""
        domains = set(cls._builtin_lessons.keys())
        domains.update(cls._custom_lessons.keys())
        return sorted(domains)

    @classmethod
    def load_from_file(cls, path: Path) -> list[Lesson]:
        """Load lessons from a JSON file."""
        with open(path) as f:
            data = json.load(f)

        lessons = []
        for item in data.get("lessons", []):
            lesson = Lesson.from_dict(item)
            lessons.append(lesson)

            # Add to custom lessons
            if lesson.domain_id not in cls._custom_lessons:
                cls._custom_lessons[lesson.domain_id] = []
            cls._custom_lessons[lesson.domain_id].append(lesson)

        return lessons

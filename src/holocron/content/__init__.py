"""Built-in lesson content for Holocron.

This package provides pre-built lessons organized by domain and difficulty.
"""

from holocron.content.loader import LessonLoader, Lesson, LessonCategory

# Import lesson modules to register built-in lessons
import holocron.content.python_lessons  # noqa: F401
import holocron.content.reading_lessons  # noqa: F401

__all__ = ["LessonLoader", "Lesson", "LessonCategory"]

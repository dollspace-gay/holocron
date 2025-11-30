"""SQLite database backend for Holocron learner persistence.

This module provides async SQLite database operations using aiosqlite,
implementing the persistence layer for learner profiles and mastery data.

The database schema stores:
- Learner profiles with preferences
- Concept mastery records per domain
- Assessment results history
- Learning session logs
"""

import json
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator

import aiosqlite

from holocron.core.models import (
    AssessmentResult,
    ConceptMastery,
    LearnerPreferences,
    LearnerProfile,
    LearningSession,
)


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


# SQL Schema
SCHEMA = """
-- Learner profiles
CREATE TABLE IF NOT EXISTS learners (
    learner_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    preferences TEXT NOT NULL,  -- JSON
    total_study_time_minutes INTEGER DEFAULT 0,
    concepts_mastered INTEGER DEFAULT 0,
    current_streak_days INTEGER DEFAULT 0,
    last_study_date TEXT
);

-- Concept mastery records
CREATE TABLE IF NOT EXISTS concept_mastery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    learner_id TEXT NOT NULL,
    domain_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    recognition_score REAL DEFAULT 0.0,
    comprehension_score REAL DEFAULT 0.0,
    application_score REAL DEFAULT 0.0,
    exposure_count INTEGER DEFAULT 0,
    first_exposure TEXT,
    last_exposure TEXT,
    last_assessment TEXT,
    ease_factor REAL DEFAULT 2.5,
    interval_days REAL DEFAULT 1.0,
    next_review TEXT,
    UNIQUE(learner_id, domain_id, concept_id),
    FOREIGN KEY (learner_id) REFERENCES learners(learner_id) ON DELETE CASCADE
);

-- Assessment results
CREATE TABLE IF NOT EXISTS assessment_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_id TEXT NOT NULL,
    learner_id TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    domain_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    response TEXT NOT NULL,
    is_correct INTEGER NOT NULL,
    score REAL NOT NULL,
    feedback TEXT DEFAULT '',
    grading_rationale TEXT DEFAULT '',
    FOREIGN KEY (learner_id) REFERENCES learners(learner_id) ON DELETE CASCADE
);

-- Learning sessions
CREATE TABLE IF NOT EXISTS learning_sessions (
    session_id TEXT PRIMARY KEY,
    learner_id TEXT NOT NULL,
    domain_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    concepts_studied TEXT NOT NULL,  -- JSON array
    assessments_completed TEXT NOT NULL,  -- JSON array
    duration_minutes INTEGER DEFAULT 0,
    FOREIGN KEY (learner_id) REFERENCES learners(learner_id) ON DELETE CASCADE
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_mastery_learner ON concept_mastery(learner_id);
CREATE INDEX IF NOT EXISTS idx_mastery_domain ON concept_mastery(learner_id, domain_id);
CREATE INDEX IF NOT EXISTS idx_mastery_review ON concept_mastery(next_review);
CREATE INDEX IF NOT EXISTS idx_results_learner ON assessment_results(learner_id);
CREATE INDEX IF NOT EXISTS idx_sessions_learner ON learning_sessions(learner_id);
"""


class Database:
    """Async SQLite database connection manager.

    Provides connection pooling and schema initialization.

    Example:
        ```python
        db = Database("holocron.db")
        await db.initialize()

        async with db.connection() as conn:
            await conn.execute("SELECT * FROM learners")
        ```
    """

    def __init__(self, db_path: str | Path) -> None:
        """Initialize database with path.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database schema.

        Creates tables if they don't exist.
        """
        if self._initialized:
            return

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            await db.executescript(SCHEMA)
            await db.commit()

        self._initialized = True

    @asynccontextmanager
    async def connection(self) -> AsyncGenerator[aiosqlite.Connection, None]:
        """Get a database connection.

        Yields:
            Async SQLite connection
        """
        if not self._initialized:
            await self.initialize()

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            yield db


class LearnerRepository:
    """Repository for learner profile persistence.

    Handles CRUD operations for learner profiles and related data.

    Example:
        ```python
        repo = LearnerRepository(database)

        # Create a new learner
        profile = LearnerProfile(learner_id="user1", name="Alice")
        await repo.save(profile)

        # Load a learner
        profile = await repo.get("user1")

        # List all learners
        learners = await repo.list_all()
        ```
    """

    def __init__(self, database: Database) -> None:
        """Initialize repository with database.

        Args:
            database: Database instance
        """
        self.db = database

    async def save(self, profile: LearnerProfile) -> None:
        """Save or update a learner profile.

        Args:
            profile: LearnerProfile to save
        """
        async with self.db.connection() as conn:
            # Save learner record
            await conn.execute(
                """
                INSERT INTO learners (
                    learner_id, name, created_at, preferences,
                    total_study_time_minutes, concepts_mastered,
                    current_streak_days, last_study_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(learner_id) DO UPDATE SET
                    name = excluded.name,
                    preferences = excluded.preferences,
                    total_study_time_minutes = excluded.total_study_time_minutes,
                    concepts_mastered = excluded.concepts_mastered,
                    current_streak_days = excluded.current_streak_days,
                    last_study_date = excluded.last_study_date
                """,
                (
                    profile.learner_id,
                    profile.name,
                    profile.created_at.isoformat(),
                    json.dumps(self._preferences_to_dict(profile.preferences)),
                    profile.total_study_time_minutes,
                    profile.concepts_mastered,
                    profile.current_streak_days,
                    profile.last_study_date.isoformat() if profile.last_study_date else None,
                ),
            )

            # Save mastery records
            for domain_id, concepts in profile.domain_mastery.items():
                for concept_id, mastery in concepts.items():
                    await self._save_mastery(conn, profile.learner_id, domain_id, mastery)

            await conn.commit()

    async def _save_mastery(
        self,
        conn: aiosqlite.Connection,
        learner_id: str,
        domain_id: str,
        mastery: ConceptMastery,
    ) -> None:
        """Save a concept mastery record."""
        await conn.execute(
            """
            INSERT INTO concept_mastery (
                learner_id, domain_id, concept_id,
                recognition_score, comprehension_score, application_score,
                exposure_count, first_exposure, last_exposure, last_assessment,
                ease_factor, interval_days, next_review
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(learner_id, domain_id, concept_id) DO UPDATE SET
                recognition_score = excluded.recognition_score,
                comprehension_score = excluded.comprehension_score,
                application_score = excluded.application_score,
                exposure_count = excluded.exposure_count,
                first_exposure = excluded.first_exposure,
                last_exposure = excluded.last_exposure,
                last_assessment = excluded.last_assessment,
                ease_factor = excluded.ease_factor,
                interval_days = excluded.interval_days,
                next_review = excluded.next_review
            """,
            (
                learner_id,
                domain_id,
                mastery.concept_id,
                mastery.recognition_score,
                mastery.comprehension_score,
                mastery.application_score,
                mastery.exposure_count,
                mastery.first_exposure.isoformat() if mastery.first_exposure else None,
                mastery.last_exposure.isoformat() if mastery.last_exposure else None,
                mastery.last_assessment.isoformat() if mastery.last_assessment else None,
                mastery.ease_factor,
                mastery.interval_days,
                mastery.next_review.isoformat() if mastery.next_review else None,
            ),
        )

    async def get(self, learner_id: str) -> LearnerProfile | None:
        """Get a learner profile by ID.

        Args:
            learner_id: The learner's unique identifier

        Returns:
            LearnerProfile if found, None otherwise
        """
        async with self.db.connection() as conn:
            # Get learner record
            cursor = await conn.execute(
                "SELECT * FROM learners WHERE learner_id = ?",
                (learner_id,),
            )
            row = await cursor.fetchone()

            if row is None:
                return None

            # Build profile
            profile = self._row_to_profile(row)

            # Load mastery records
            cursor = await conn.execute(
                "SELECT * FROM concept_mastery WHERE learner_id = ?",
                (learner_id,),
            )
            async for mastery_row in cursor:
                domain_id = mastery_row["domain_id"]
                if domain_id not in profile.domain_mastery:
                    profile.domain_mastery[domain_id] = {}

                mastery = self._row_to_mastery(mastery_row)
                profile.domain_mastery[domain_id][mastery.concept_id] = mastery

            return profile

    async def list_all(self) -> list[LearnerProfile]:
        """List all learner profiles.

        Returns:
            List of LearnerProfile objects (without full mastery data)
        """
        profiles = []
        async with self.db.connection() as conn:
            cursor = await conn.execute("SELECT * FROM learners ORDER BY name")
            async for row in cursor:
                profiles.append(self._row_to_profile(row))
        return profiles

    async def delete(self, learner_id: str) -> bool:
        """Delete a learner profile.

        Args:
            learner_id: The learner's unique identifier

        Returns:
            True if deleted, False if not found
        """
        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "DELETE FROM learners WHERE learner_id = ?",
                (learner_id,),
            )
            await conn.commit()
            return cursor.rowcount > 0

    async def exists(self, learner_id: str) -> bool:
        """Check if a learner exists.

        Args:
            learner_id: The learner's unique identifier

        Returns:
            True if exists
        """
        async with self.db.connection() as conn:
            cursor = await conn.execute(
                "SELECT 1 FROM learners WHERE learner_id = ?",
                (learner_id,),
            )
            return await cursor.fetchone() is not None

    async def get_concepts_due_for_review(
        self, learner_id: str, domain_id: str | None = None
    ) -> list[tuple[str, str]]:
        """Get concepts due for spaced repetition review.

        Args:
            learner_id: The learner's ID
            domain_id: Optional domain filter

        Returns:
            List of (domain_id, concept_id) tuples
        """
        now = _utc_now().isoformat()
        async with self.db.connection() as conn:
            if domain_id:
                cursor = await conn.execute(
                    """
                    SELECT domain_id, concept_id FROM concept_mastery
                    WHERE learner_id = ? AND domain_id = ?
                    AND (next_review IS NULL OR next_review <= ?)
                    ORDER BY next_review
                    """,
                    (learner_id, domain_id, now),
                )
            else:
                cursor = await conn.execute(
                    """
                    SELECT domain_id, concept_id FROM concept_mastery
                    WHERE learner_id = ?
                    AND (next_review IS NULL OR next_review <= ?)
                    ORDER BY next_review
                    """,
                    (learner_id, now),
                )

            return [(row["domain_id"], row["concept_id"]) async for row in cursor]

    async def save_assessment_result(
        self,
        learner_id: str,
        domain_id: str,
        result: AssessmentResult,
    ) -> None:
        """Save an assessment result.

        Args:
            learner_id: The learner's ID
            domain_id: The domain of the assessment
            result: The assessment result to save
        """
        async with self.db.connection() as conn:
            await conn.execute(
                """
                INSERT INTO assessment_results (
                    assessment_id, learner_id, concept_id, domain_id,
                    timestamp, response, is_correct, score,
                    feedback, grading_rationale
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.assessment_id,
                    learner_id,
                    result.assessment_id.split("-")[0] if "-" in result.assessment_id else "",
                    domain_id,
                    result.timestamp.isoformat(),
                    result.response,
                    1 if result.is_correct else 0,
                    result.score,
                    result.feedback,
                    result.grading_rationale,
                ),
            )
            await conn.commit()

    async def get_learner_stats(self, learner_id: str) -> dict[str, Any]:
        """Get statistics for a learner.

        Args:
            learner_id: The learner's ID

        Returns:
            Dictionary with learner statistics
        """
        async with self.db.connection() as conn:
            # Basic stats
            cursor = await conn.execute(
                "SELECT * FROM learners WHERE learner_id = ?",
                (learner_id,),
            )
            learner = await cursor.fetchone()
            if not learner:
                return {}

            # Mastery counts by domain
            cursor = await conn.execute(
                """
                SELECT domain_id, COUNT(*) as concept_count,
                       AVG(recognition_score * 0.2 + comprehension_score * 0.3 + application_score * 0.5) as avg_mastery
                FROM concept_mastery
                WHERE learner_id = ?
                GROUP BY domain_id
                """,
                (learner_id,),
            )
            domains = {}
            async for row in cursor:
                domains[row["domain_id"]] = {
                    "concept_count": row["concept_count"],
                    "avg_mastery": round(row["avg_mastery"] or 0, 1),
                }

            # Assessment stats
            cursor = await conn.execute(
                """
                SELECT COUNT(*) as total, SUM(is_correct) as correct
                FROM assessment_results
                WHERE learner_id = ?
                """,
                (learner_id,),
            )
            assessment_row = await cursor.fetchone()

            # Due for review
            due_count = len(await self.get_concepts_due_for_review(learner_id))

            return {
                "learner_id": learner_id,
                "name": learner["name"],
                "total_study_time_minutes": learner["total_study_time_minutes"],
                "concepts_mastered": learner["concepts_mastered"],
                "current_streak_days": learner["current_streak_days"],
                "domains": domains,
                "total_assessments": assessment_row["total"] or 0,
                "correct_assessments": assessment_row["correct"] or 0,
                "accuracy": (
                    round((assessment_row["correct"] or 0) / assessment_row["total"] * 100, 1)
                    if assessment_row["total"]
                    else 0
                ),
                "concepts_due_for_review": due_count,
            }

    def _row_to_profile(self, row: aiosqlite.Row) -> LearnerProfile:
        """Convert a database row to LearnerProfile."""
        preferences_data = json.loads(row["preferences"])

        return LearnerProfile(
            learner_id=row["learner_id"],
            name=row["name"],
            created_at=datetime.fromisoformat(row["created_at"]),
            preferences=LearnerPreferences(
                preferred_scaffold_level=preferences_data.get("preferred_scaffold_level"),
                explanation_style=preferences_data.get("explanation_style", "detailed"),
                theme=preferences_data.get("theme", "system"),
                daily_goal_minutes=preferences_data.get("daily_goal_minutes", 30),
                notification_enabled=preferences_data.get("notification_enabled", True),
            ),
            total_study_time_minutes=row["total_study_time_minutes"],
            concepts_mastered=row["concepts_mastered"],
            current_streak_days=row["current_streak_days"],
            last_study_date=(
                datetime.fromisoformat(row["last_study_date"])
                if row["last_study_date"]
                else None
            ),
        )

    def _row_to_mastery(self, row: aiosqlite.Row) -> ConceptMastery:
        """Convert a database row to ConceptMastery."""
        return ConceptMastery(
            concept_id=row["concept_id"],
            learner_id=row["learner_id"],
            recognition_score=row["recognition_score"],
            comprehension_score=row["comprehension_score"],
            application_score=row["application_score"],
            exposure_count=row["exposure_count"],
            first_exposure=(
                datetime.fromisoformat(row["first_exposure"])
                if row["first_exposure"]
                else None
            ),
            last_exposure=(
                datetime.fromisoformat(row["last_exposure"])
                if row["last_exposure"]
                else None
            ),
            last_assessment=(
                datetime.fromisoformat(row["last_assessment"])
                if row["last_assessment"]
                else None
            ),
            ease_factor=row["ease_factor"],
            interval_days=row["interval_days"],
            next_review=(
                datetime.fromisoformat(row["next_review"])
                if row["next_review"]
                else None
            ),
        )

    def _preferences_to_dict(self, prefs: LearnerPreferences) -> dict[str, Any]:
        """Convert LearnerPreferences to dictionary."""
        return {
            "preferred_scaffold_level": prefs.preferred_scaffold_level,
            "explanation_style": prefs.explanation_style,
            "theme": prefs.theme,
            "daily_goal_minutes": prefs.daily_goal_minutes,
            "notification_enabled": prefs.notification_enabled,
        }


def get_default_db_path() -> Path:
    """Get the default database path.

    Returns:
        Path to the default database file
    """
    # Use user's data directory
    import os

    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    return base / "holocron" / "holocron.db"

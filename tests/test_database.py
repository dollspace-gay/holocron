"""Tests for SQLite database persistence."""

import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from holocron.core.models import (
    ConceptMastery,
    LearnerPreferences,
    LearnerProfile,
)
from holocron.learner.database import Database, LearnerRepository


@pytest.fixture
def temp_db_path():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    yield path
    # Cleanup
    if path.exists():
        path.unlink()


@pytest.fixture
def database(temp_db_path):
    """Create a database instance."""
    return Database(temp_db_path)


@pytest.fixture
def repository(database):
    """Create a repository instance."""
    return LearnerRepository(database)


@pytest.fixture
def sample_profile():
    """Create a sample learner profile."""
    return LearnerProfile(
        learner_id="test-user",
        name="Test User",
        preferences=LearnerPreferences(
            explanation_style="concise",
            daily_goal_minutes=45,
        ),
    )


def run(coro):
    """Run async code in tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class TestDatabase:
    """Tests for Database class."""

    def test_initialize_creates_tables(self, database, temp_db_path):
        """Test that initialization creates database tables."""
        run(database.initialize())

        assert temp_db_path.exists()

    def test_connection_context_manager(self, database):
        """Test database connection context manager."""

        async def test():
            await database.initialize()
            async with database.connection() as conn:
                cursor = await conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] async for row in cursor]
                return tables

        tables = run(test())
        assert "learners" in tables
        assert "concept_mastery" in tables
        assert "assessment_results" in tables


class TestLearnerRepository:
    """Tests for LearnerRepository class."""

    def test_save_and_get_profile(self, repository, sample_profile):
        """Test saving and retrieving a learner profile."""

        async def test():
            await repository.save(sample_profile)
            retrieved = await repository.get(sample_profile.learner_id)
            return retrieved

        retrieved = run(test())

        assert retrieved is not None
        assert retrieved.learner_id == sample_profile.learner_id
        assert retrieved.name == sample_profile.name
        assert retrieved.preferences.explanation_style == "concise"
        assert retrieved.preferences.daily_goal_minutes == 45

    def test_get_nonexistent_profile(self, repository):
        """Test getting a profile that doesn't exist."""

        async def test():
            return await repository.get("nonexistent")

        result = run(test())
        assert result is None

    def test_exists(self, repository, sample_profile):
        """Test checking if a profile exists."""

        async def test():
            # Should not exist initially
            before = await repository.exists(sample_profile.learner_id)
            await repository.save(sample_profile)
            after = await repository.exists(sample_profile.learner_id)
            return before, after

        before, after = run(test())
        assert before is False
        assert after is True

    def test_list_all(self, repository):
        """Test listing all profiles."""

        async def test():
            # Create multiple profiles
            for i in range(3):
                profile = LearnerProfile(
                    learner_id=f"user-{i}",
                    name=f"User {i}",
                )
                await repository.save(profile)

            return await repository.list_all()

        profiles = run(test())
        assert len(profiles) == 3

    def test_delete(self, repository, sample_profile):
        """Test deleting a profile."""

        async def test():
            await repository.save(sample_profile)
            deleted = await repository.delete(sample_profile.learner_id)
            exists = await repository.exists(sample_profile.learner_id)
            return deleted, exists

        deleted, exists = run(test())
        assert deleted is True
        assert exists is False

    def test_delete_nonexistent(self, repository):
        """Test deleting a profile that doesn't exist."""

        async def test():
            return await repository.delete("nonexistent")

        result = run(test())
        assert result is False

    def test_save_with_mastery(self, repository, sample_profile):
        """Test saving profile with mastery data."""

        async def test():
            # Add mastery data
            sample_profile.domain_mastery["python-programming"] = {
                "python.list_comprehension": ConceptMastery(
                    concept_id="python.list_comprehension",
                    learner_id=sample_profile.learner_id,
                    recognition_score=80.0,
                    comprehension_score=60.0,
                    application_score=40.0,
                    exposure_count=5,
                ),
            }

            await repository.save(sample_profile)
            retrieved = await repository.get(sample_profile.learner_id)
            return retrieved

        retrieved = run(test())

        assert "python-programming" in retrieved.domain_mastery
        mastery = retrieved.domain_mastery["python-programming"]["python.list_comprehension"]
        assert mastery.recognition_score == 80.0
        assert mastery.comprehension_score == 60.0
        assert mastery.application_score == 40.0
        assert mastery.exposure_count == 5

    def test_update_profile(self, repository, sample_profile):
        """Test updating an existing profile."""

        async def test():
            await repository.save(sample_profile)

            # Update profile
            sample_profile.name = "Updated Name"
            sample_profile.total_study_time_minutes = 100
            await repository.save(sample_profile)

            return await repository.get(sample_profile.learner_id)

        retrieved = run(test())

        assert retrieved.name == "Updated Name"
        assert retrieved.total_study_time_minutes == 100

    def test_get_concepts_due_for_review(self, repository, sample_profile):
        """Test getting concepts due for review."""

        async def test():
            # Add mastery with past review date
            sample_profile.domain_mastery["python-programming"] = {
                "python.list_comprehension": ConceptMastery(
                    concept_id="python.list_comprehension",
                    learner_id=sample_profile.learner_id,
                    next_review=None,  # Due immediately
                ),
            }

            await repository.save(sample_profile)
            due = await repository.get_concepts_due_for_review(sample_profile.learner_id)
            return due

        due = run(test())

        assert len(due) == 1
        assert due[0] == ("python-programming", "python.list_comprehension")

    def test_get_learner_stats(self, repository, sample_profile):
        """Test getting learner statistics."""

        async def test():
            # Add some mastery data
            sample_profile.domain_mastery["python-programming"] = {
                "python.list_comprehension": ConceptMastery(
                    concept_id="python.list_comprehension",
                    learner_id=sample_profile.learner_id,
                    recognition_score=100.0,
                    comprehension_score=80.0,
                    application_score=60.0,
                ),
            }
            sample_profile.total_study_time_minutes = 120

            await repository.save(sample_profile)
            return await repository.get_learner_stats(sample_profile.learner_id)

        stats = run(test())

        assert stats["learner_id"] == sample_profile.learner_id
        assert stats["name"] == sample_profile.name
        assert stats["total_study_time_minutes"] == 120
        assert "python-programming" in stats["domains"]
        assert stats["domains"]["python-programming"]["concept_count"] == 1

    def test_stats_for_nonexistent_learner(self, repository):
        """Test getting stats for a learner that doesn't exist."""

        async def test():
            return await repository.get_learner_stats("nonexistent")

        stats = run(test())
        assert stats == {}

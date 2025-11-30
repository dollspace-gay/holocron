"""Tests for the REPL session controller."""

import asyncio
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from holocron.core.grader import GradingResult
from holocron.core.models import (
    Assessment,
    AssessmentOption,
    AssessmentType,
    BloomLevel,
    LearnerProfile,
)
from holocron.learner import Database
from holocron.repl import SessionController, SessionState, SessionStats


@pytest.fixture
def temp_db():
    """Create a temporary database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = Path(f.name)
    db = Database(path)
    yield db
    if path.exists():
        path.unlink()


@pytest.fixture
def mock_console():
    """Create a mock console."""
    console = MagicMock(spec=Console)
    console.print = MagicMock()
    console.status = MagicMock(return_value=MagicMock(__enter__=MagicMock(), __exit__=MagicMock()))
    return console


@pytest.fixture
def mock_grader():
    """Create a mock grader."""
    grader = MagicMock()
    grader.grade.return_value = GradingResult(
        score=0.85,
        is_correct=True,
        feedback="Good answer!",
        strengths=["Clear understanding"],
        areas_for_improvement=["Add more detail"],
    )
    return grader


def run(coro):
    """Run async code in tests."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


class TestSessionStats:
    """Tests for SessionStats dataclass."""

    def test_initial_stats(self):
        """Test initial session stats."""
        stats = SessionStats()

        assert stats.concepts_studied == 0
        assert stats.assessments_attempted == 0
        assert stats.assessments_correct == 0
        assert stats.accuracy == 0.0

    def test_accuracy_calculation(self):
        """Test accuracy calculation."""
        stats = SessionStats(
            assessments_attempted=10,
            assessments_correct=7,
        )

        assert stats.accuracy == 70.0

    def test_accuracy_with_no_attempts(self):
        """Test accuracy with zero attempts."""
        stats = SessionStats()
        assert stats.accuracy == 0.0


class TestSessionController:
    """Tests for SessionController class."""

    def test_init(self, temp_db, mock_console, mock_grader):
        """Test controller initialization."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        assert controller.learner_id == "test-learner"
        assert controller.domain_id == "reading-skills"
        assert controller.state == SessionState.IDLE
        assert controller.running is False

    def test_initialize_creates_learner(self, temp_db, mock_console, mock_grader):
        """Test that initialization creates learner profile if needed."""
        controller = SessionController(
            learner_id="new-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        async def test():
            result = await controller.initialize()
            return result, controller.learner

        result, learner = run(test())

        assert result is True
        assert learner is not None
        assert learner.learner_id == "new-learner"

    def test_initialize_loads_existing_learner(self, temp_db, mock_console, mock_grader):
        """Test that initialization loads existing learner profile."""
        async def setup_and_test():
            # Create existing profile
            await temp_db.initialize()
            from holocron.learner import LearnerRepository
            repo = LearnerRepository(temp_db)
            profile = LearnerProfile(
                learner_id="existing-learner",
                name="Existing User",
                total_study_time_minutes=100,
            )
            await repo.save(profile)

            # Initialize controller
            controller = SessionController(
                learner_id="existing-learner",
                domain_id="reading-skills",
                db=temp_db,
                console=mock_console,
                grader=mock_grader,
            )
            await controller.initialize()

            return controller.learner

        learner = run(setup_and_test())

        assert learner.name == "Existing User"
        assert learner.total_study_time_minutes == 100

    def test_commands_registered(self, temp_db, mock_console, mock_grader):
        """Test that commands are properly registered."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        # Check main commands
        assert "help" in controller._commands
        assert "stats" in controller._commands
        assert "progress" in controller._commands
        assert "review" in controller._commands
        assert "load" in controller._commands
        assert "quit" in controller._commands

        # Check aliases
        assert "h" in controller._commands
        assert "?" in controller._commands
        assert "s" in controller._commands
        assert "q" in controller._commands

    def test_get_prompt_by_state(self, temp_db, mock_console, mock_grader):
        """Test prompt changes based on state."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        controller.state = SessionState.IDLE
        assert "holocron" in controller._get_prompt()

        controller.state = SessionState.STUDYING
        assert "studying" in controller._get_prompt()

        controller.state = SessionState.ASSESSMENT
        assert "answer" in controller._get_prompt()

    def test_cmd_help(self, temp_db, mock_console, mock_grader):
        """Test help command displays commands."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        controller._cmd_help([])

        # Should have printed table with commands
        assert mock_console.print.called

    def test_cmd_stats(self, temp_db, mock_console, mock_grader):
        """Test stats command."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        controller.stats.concepts_studied = 5
        controller.stats.assessments_attempted = 3
        controller.stats.assessments_correct = 2

        controller._cmd_stats([])

        assert mock_console.print.called

    def test_cmd_quit(self, temp_db, mock_console, mock_grader):
        """Test quit command sets running to False."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        controller.running = True
        controller._cmd_quit([])

        assert controller.running is False

    def test_cmd_skip_in_assessment(self, temp_db, mock_console, mock_grader):
        """Test skip command during assessment."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        # Set up assessment state
        controller.state = SessionState.ASSESSMENT
        controller.current_assessments = [
            Assessment(
                assessment_id="a1",
                concept_id="test.concept",
                bloom_level=BloomLevel.KNOWLEDGE,
                assessment_type=AssessmentType.FREE_RESPONSE,
                question="Test question 1",
            ),
            Assessment(
                assessment_id="a2",
                concept_id="test.concept",
                bloom_level=BloomLevel.KNOWLEDGE,
                assessment_type=AssessmentType.FREE_RESPONSE,
                question="Test question 2",
            ),
        ]
        controller.current_assessment_index = 0

        controller._cmd_skip([])

        assert controller.current_assessment_index == 1
        assert controller.stats.assessments_attempted == 1

    def test_cmd_skip_not_in_assessment(self, temp_db, mock_console, mock_grader):
        """Test skip command when not in assessment mode."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        controller.state = SessionState.IDLE
        controller._cmd_skip([])

        # Should print warning
        assert mock_console.print.called


class TestAssessmentGrading:
    """Tests for assessment grading in REPL."""

    def test_handle_assessment_response_correct(self, temp_db, mock_console, mock_grader):
        """Test handling a correct assessment response."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        async def test():
            await controller.initialize()

            # Set up assessment
            controller.state = SessionState.ASSESSMENT
            controller.current_assessments = [
                Assessment(
                    assessment_id="a1",
                    concept_id="test.concept",
                    bloom_level=BloomLevel.KNOWLEDGE,
                    assessment_type=AssessmentType.FREE_RESPONSE,
                    question="What is X?",
                ),
            ]
            controller.current_assessment_index = 0

            # Mock grader returns correct
            mock_grader.grade.return_value = GradingResult(
                score=1.0,
                is_correct=True,
                feedback="Perfect!",
            )

            await controller._handle_assessment_response("My answer")

            return controller.stats

        stats = run(test())

        assert stats.assessments_attempted == 1
        assert stats.assessments_correct == 1

    def test_handle_assessment_response_incorrect(self, temp_db, mock_console, mock_grader):
        """Test handling an incorrect assessment response."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        async def test():
            await controller.initialize()

            controller.state = SessionState.ASSESSMENT
            controller.current_assessments = [
                Assessment(
                    assessment_id="a1",
                    concept_id="test.concept",
                    bloom_level=BloomLevel.KNOWLEDGE,
                    assessment_type=AssessmentType.FREE_RESPONSE,
                    question="What is X?",
                ),
            ]
            controller.current_assessment_index = 0

            # Mock grader returns incorrect
            mock_grader.grade.return_value = GradingResult(
                score=0.3,
                is_correct=False,
                feedback="Not quite.",
            )

            await controller._handle_assessment_response("Wrong answer")

            return controller.stats

        stats = run(test())

        assert stats.assessments_attempted == 1
        assert stats.assessments_correct == 0


class TestSessionState:
    """Tests for session state transitions."""

    def test_state_enum_values(self):
        """Test SessionState enum values."""
        assert SessionState.IDLE.value == "idle"
        assert SessionState.STUDYING.value == "studying"
        assert SessionState.ASSESSMENT.value == "assessment"
        assert SessionState.REVIEW.value == "review"
        assert SessionState.PAUSED.value == "paused"

    def test_state_after_study_content(self, temp_db, mock_console, mock_grader):
        """Test state transitions during content study."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        async def test():
            await controller.initialize()

            # Study some content
            test_content = "The mitochondria is the powerhouse of the cell."

            # Patch Confirm to auto-decline assessments
            with patch("holocron.repl.session.Confirm") as mock_confirm:
                mock_confirm.ask.return_value = False
                await controller._study_content(test_content)

            return controller.state

        state = run(test())

        # Should return to IDLE after declining assessments
        assert state == SessionState.IDLE


class TestCommandHandling:
    """Tests for command parsing and handling."""

    def test_handle_unknown_command(self, temp_db, mock_console, mock_grader):
        """Test handling of unknown command."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        async def test():
            await controller._handle_command("unknowncommand")

        run(test())

        # Should print error message
        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Unknown command" in str(c) for c in calls)

    def test_handle_command_with_args(self, temp_db, mock_console, mock_grader):
        """Test command handling with arguments."""
        controller = SessionController(
            learner_id="test-learner",
            domain_id="reading-skills",
            db=temp_db,
            console=mock_console,
            grader=mock_grader,
        )

        # Test load command without args shows usage
        async def test():
            await controller._cmd_load([])

        run(test())

        calls = [str(c) for c in mock_console.print.call_args_list]
        assert any("Usage" in str(c) for c in calls)

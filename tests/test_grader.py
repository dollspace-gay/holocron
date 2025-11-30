"""Tests for assessment grading module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from holocron.core.grader import AssessmentGrader, GradingResult, grade_response
from holocron.core.models import (
    Assessment,
    AssessmentOption,
    AssessmentType,
    BloomLevel,
)


@pytest.fixture
def multiple_choice_assessment():
    """Create a multiple choice assessment."""
    return Assessment(
        assessment_id="mc-001",
        concept_id="python.list_comprehension",
        bloom_level=BloomLevel.KNOWLEDGE,
        assessment_type=AssessmentType.MULTIPLE_CHOICE,
        question="What is a list comprehension in Python?",
        options=[
            AssessmentOption(
                text="A way to create lists using a concise syntax",
                is_correct=True,
                explanation="Correct! List comprehensions provide a concise way to create lists.",
            ),
            AssessmentOption(
                text="A method to sort lists",
                is_correct=False,
            ),
            AssessmentOption(
                text="A type of loop that only works with lists",
                is_correct=False,
            ),
            AssessmentOption(
                text="A debugging tool for lists",
                is_correct=False,
            ),
        ],
    )


@pytest.fixture
def free_response_assessment():
    """Create a free response assessment."""
    return Assessment(
        assessment_id="fr-001",
        concept_id="python.list_comprehension",
        bloom_level=BloomLevel.COMPREHENSION,
        assessment_type=AssessmentType.FREE_RESPONSE,
        question="Explain in your own words what a list comprehension is and when you would use one.",
        rubric="Should mention: concise syntax, creating lists from iterables, optional conditions",
        sample_answer="A list comprehension is a concise way to create a new list by applying an expression to each item in an iterable, optionally filtering items with a condition.",
    )


@pytest.fixture
def application_assessment():
    """Create an application-level assessment."""
    return Assessment(
        assessment_id="app-001",
        concept_id="python.list_comprehension",
        bloom_level=BloomLevel.APPLICATION,
        assessment_type=AssessmentType.CODE_EXERCISE,
        question="Write a list comprehension that squares all even numbers from 1 to 10.",
        sample_answer="[x**2 for x in range(1, 11) if x % 2 == 0]",
        context="You need to create a list containing the squares of even numbers only.",
    )


class TestGradingResult:
    """Tests for GradingResult dataclass."""

    def test_create_result(self):
        """Test creating a grading result."""
        result = GradingResult(
            score=0.85,
            is_correct=True,
            feedback="Good explanation!",
            strengths=["Clear understanding", "Good examples"],
            areas_for_improvement=["Could add more detail"],
        )

        assert result.score == 0.85
        assert result.is_correct is True
        assert len(result.strengths) == 2
        assert len(result.areas_for_improvement) == 1

    def test_result_defaults(self):
        """Test GradingResult with default values."""
        result = GradingResult(
            score=0.5,
            is_correct=False,
            feedback="Needs work",
        )

        assert result.strengths == []
        assert result.areas_for_improvement == []
        assert result.grading_rationale == ""
        assert result.concept_understanding == ""


class TestAssessmentGraderMultipleChoice:
    """Tests for multiple choice grading."""

    def test_grade_correct_answer_by_letter(self, multiple_choice_assessment):
        """Test grading correct answer by letter."""
        grader = AssessmentGrader()
        result = grader.grade(multiple_choice_assessment, "A")

        assert result.score == 1.0
        assert result.is_correct is True
        assert "Correct" in result.feedback

    def test_grade_correct_answer_by_text(self, multiple_choice_assessment):
        """Test grading correct answer by matching text."""
        grader = AssessmentGrader()
        result = grader.grade(
            multiple_choice_assessment,
            "A way to create lists using a concise syntax",
        )

        assert result.score == 1.0
        assert result.is_correct is True

    def test_grade_incorrect_answer(self, multiple_choice_assessment):
        """Test grading incorrect answer."""
        grader = AssessmentGrader()
        result = grader.grade(multiple_choice_assessment, "B")

        assert result.score == 0.0
        assert result.is_correct is False
        assert "Not quite" in result.feedback

    def test_grade_case_insensitive(self, multiple_choice_assessment):
        """Test that grading is case insensitive."""
        grader = AssessmentGrader()
        result = grader.grade(multiple_choice_assessment, "a")

        assert result.score == 1.0
        assert result.is_correct is True


class TestAssessmentGraderFreeResponse:
    """Tests for free response grading with LLM."""

    @patch("holocron.core.grader.LLMClient")
    def test_grade_free_response_success(self, mock_llm_class, free_response_assessment):
        """Test successful free response grading."""
        mock_client = MagicMock()
        mock_client.complete.return_value = MagicMock(
            content="""{
                "score": 0.85,
                "feedback": "Good explanation of list comprehensions.",
                "strengths": ["Clear understanding", "Mentioned key concepts"],
                "areas_for_improvement": ["Could provide an example"],
                "grading_rationale": "Response covers main points",
                "concept_understanding": "Solid comprehension level"
            }"""
        )
        mock_llm_class.return_value = mock_client

        grader = AssessmentGrader()
        result = grader.grade(
            free_response_assessment,
            "A list comprehension is a compact way to generate a new list from an existing sequence. You use it when you want to transform or filter items efficiently.",
        )

        assert result.score == 0.85
        assert result.is_correct is True
        assert "Good explanation" in result.feedback
        assert len(result.strengths) == 2
        assert len(result.areas_for_improvement) == 1

    @patch("holocron.core.grader.LLMClient")
    def test_grade_free_response_partial_credit(self, mock_llm_class, free_response_assessment):
        """Test partial credit grading."""
        mock_client = MagicMock()
        mock_client.complete.return_value = MagicMock(
            content="""{
                "score": 0.5,
                "feedback": "Partial understanding demonstrated.",
                "strengths": ["Basic idea understood"],
                "areas_for_improvement": ["Missing key details", "Needs examples"],
                "grading_rationale": "Incomplete response",
                "concept_understanding": "Basic level"
            }"""
        )
        mock_llm_class.return_value = mock_client

        grader = AssessmentGrader()
        result = grader.grade(
            free_response_assessment,
            "It's a way to make lists shorter.",
        )

        assert result.score == 0.5
        assert result.is_correct is False  # Below 0.7 threshold

    @patch("holocron.core.grader.LLMClient")
    def test_grade_api_error_fallback(self, mock_llm_class, free_response_assessment):
        """Test fallback when LLM API fails."""
        mock_client = MagicMock()
        mock_client.complete.side_effect = Exception("API Error")
        mock_llm_class.return_value = mock_client

        grader = AssessmentGrader()
        result = grader.grade(free_response_assessment, "Some response")

        assert result.score == 0.5
        assert result.is_correct is False
        assert "Unable to grade" in result.feedback

    @patch("holocron.core.grader.LLMClient")
    def test_grade_malformed_json_fallback(self, mock_llm_class, free_response_assessment):
        """Test fallback when LLM returns malformed JSON."""
        mock_client = MagicMock()
        mock_client.complete.return_value = MagicMock(
            content="This is not JSON, but the score is 0.8/1"
        )
        mock_llm_class.return_value = mock_client

        grader = AssessmentGrader()
        result = grader.grade(free_response_assessment, "Some response")

        # Should extract score from text
        assert result.score == 0.8
        assert result.is_correct is True

    @patch("holocron.core.grader.LLMClient")
    def test_grade_clamps_score(self, mock_llm_class, free_response_assessment):
        """Test that scores are clamped to 0-1 range."""
        mock_client = MagicMock()
        mock_client.complete.return_value = MagicMock(
            content='{"score": 1.5, "feedback": "Perfect"}'
        )
        mock_llm_class.return_value = mock_client

        grader = AssessmentGrader()
        result = grader.grade(free_response_assessment, "Some response")

        assert result.score == 1.0  # Clamped from 1.5


class TestAssessmentGraderBloomLevels:
    """Tests for Bloom level-specific grading."""

    def test_bloom_criteria_exist(self):
        """Test that all Bloom levels have criteria."""
        for level in BloomLevel:
            assert level in AssessmentGrader.BLOOM_CRITERIA
            assert "focus" in AssessmentGrader.BLOOM_CRITERIA[level]
            assert "criteria" in AssessmentGrader.BLOOM_CRITERIA[level]
            assert len(AssessmentGrader.BLOOM_CRITERIA[level]["criteria"]) >= 3

    @patch("holocron.core.grader.LLMClient")
    def test_application_level_grading(self, mock_llm_class, application_assessment):
        """Test grading at application level."""
        mock_client = MagicMock()
        mock_client.complete.return_value = MagicMock(
            content="""{
                "score": 0.9,
                "feedback": "Excellent application of concepts.",
                "strengths": ["Correct syntax", "Proper use of filter condition"],
                "areas_for_improvement": [],
                "grading_rationale": "Demonstrates practical understanding",
                "concept_understanding": "Strong application level"
            }"""
        )
        mock_llm_class.return_value = mock_client

        grader = AssessmentGrader()
        result = grader.grade(
            application_assessment,
            "[x**2 for x in range(1, 11) if x % 2 == 0]",
        )

        assert result.score == 0.9
        assert result.is_correct is True

        # Verify the prompt included application-level criteria
        call_args = mock_client.complete.call_args
        system_prompt = call_args.kwargs["system_prompt"]
        assert "Application" in system_prompt
        assert "applying knowledge" in system_prompt.lower()


class TestCreateAssessmentResult:
    """Tests for creating AssessmentResult from grading."""

    def test_create_result_from_grading(self, multiple_choice_assessment):
        """Test creating an AssessmentResult from grading."""
        grader = AssessmentGrader()
        grading_result = GradingResult(
            score=1.0,
            is_correct=True,
            feedback="Correct!",
            strengths=["Good recall"],
            areas_for_improvement=[],
            grading_rationale="Matched correct answer",
        )

        result = grader.create_assessment_result(
            assessment=multiple_choice_assessment,
            response="A",
            learner_id="test-learner",
            grading_result=grading_result,
        )

        assert result.assessment_id == "mc-001"
        assert result.learner_id == "test-learner"
        assert result.response == "A"
        assert result.is_correct is True
        assert result.score == 1.0
        assert result.feedback == "Correct!"
        assert isinstance(result.timestamp, datetime)

    def test_create_result_auto_grade(self, multiple_choice_assessment):
        """Test creating result with automatic grading."""
        grader = AssessmentGrader()

        result = grader.create_assessment_result(
            assessment=multiple_choice_assessment,
            response="B",
            learner_id="test-learner",
        )

        assert result.is_correct is False
        assert result.score == 0.0


class TestGradeResponseFunction:
    """Tests for the convenience function."""

    def test_grade_response_mc(self, multiple_choice_assessment):
        """Test grade_response convenience function with MC."""
        result = grade_response(multiple_choice_assessment, "A")

        assert result.score == 1.0
        assert result.is_correct is True

    @patch("holocron.core.grader.LLMClient")
    def test_grade_response_free(self, mock_llm_class, free_response_assessment):
        """Test grade_response convenience function with free response."""
        mock_client = MagicMock()
        mock_client.complete.return_value = MagicMock(
            content='{"score": 0.75, "feedback": "Good job"}'
        )
        mock_llm_class.return_value = mock_client

        result = grade_response(
            free_response_assessment,
            "A list comprehension creates lists efficiently.",
        )

        assert result.score == 0.75
        assert result.is_correct is True

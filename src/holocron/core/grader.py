"""Assessment grading using LLM evaluation.

This module provides LLM-based grading for free-response assessments,
supporting Bloom's Taxonomy levels and detailed feedback generation.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from holocron.core.models import (
    Assessment,
    AssessmentResult,
    AssessmentType,
    BloomLevel,
)
from holocron.llm import LLMClient


@dataclass
class GradingResult:
    """Result from LLM grading of an assessment response.

    Attributes:
        score: Numeric score from 0.0 to 1.0
        is_correct: Whether the response is considered correct (score >= 0.7)
        feedback: Constructive feedback for the learner
        strengths: What the learner did well
        areas_for_improvement: Where the learner can improve
        grading_rationale: Explanation of how the score was determined
        concept_understanding: Assessment of concept understanding level
    """

    score: float
    is_correct: bool
    feedback: str
    strengths: list[str] = field(default_factory=list)
    areas_for_improvement: list[str] = field(default_factory=list)
    grading_rationale: str = ""
    concept_understanding: str = ""


class AssessmentGrader:
    """LLM-powered assessment grader for free-response questions.

    Uses structured prompts aligned with Bloom's Taxonomy levels
    to evaluate learner responses and provide pedagogically-sound feedback.

    Example:
        ```python
        grader = AssessmentGrader()

        result = grader.grade(
            assessment=comprehension_assessment,
            response="The learner's answer here...",
        )

        print(f"Score: {result.score}")
        print(f"Feedback: {result.feedback}")
        ```
    """

    # Bloom level criteria for grading
    BLOOM_CRITERIA = {
        BloomLevel.KNOWLEDGE: {
            "focus": "recall and recognition",
            "criteria": [
                "Correctly identifies key terms and definitions",
                "Accurately recalls factual information",
                "Demonstrates basic familiarity with the concept",
            ],
        },
        BloomLevel.COMPREHENSION: {
            "focus": "understanding and explanation",
            "criteria": [
                "Explains concepts in their own words",
                "Demonstrates understanding beyond mere recall",
                "Can summarize and paraphrase accurately",
                "Shows grasp of underlying meaning",
            ],
        },
        BloomLevel.APPLICATION: {
            "focus": "applying knowledge to new situations",
            "criteria": [
                "Correctly applies concepts to solve problems",
                "Uses appropriate methods and procedures",
                "Can transfer knowledge to novel contexts",
                "Demonstrates practical understanding",
            ],
        },
        BloomLevel.ANALYSIS: {
            "focus": "breaking down and examining relationships",
            "criteria": [
                "Identifies components and their relationships",
                "Distinguishes between relevant and irrelevant information",
                "Recognizes patterns and underlying structures",
                "Compares and contrasts effectively",
            ],
        },
        BloomLevel.SYNTHESIS: {
            "focus": "creating and combining ideas",
            "criteria": [
                "Combines elements to form new understanding",
                "Proposes creative solutions or approaches",
                "Integrates knowledge from multiple sources",
                "Generates original work or ideas",
            ],
        },
        BloomLevel.EVALUATION: {
            "focus": "making judgments and defending positions",
            "criteria": [
                "Makes well-reasoned judgments",
                "Supports opinions with evidence",
                "Evaluates validity and reliability",
                "Defends conclusions with logical arguments",
            ],
        },
    }

    def __init__(
        self,
        llm_client: LLMClient | None = None,
        model: str | None = None,
    ) -> None:
        """Initialize the grader.

        Args:
            llm_client: Optional LLM client (creates default if not provided)
            model: Optional model override for the LLM client
        """
        self.llm_client = llm_client or LLMClient(model=model)

    def grade(
        self,
        assessment: Assessment,
        response: str,
        learner_id: str = "",
    ) -> GradingResult:
        """Grade a learner's response to an assessment.

        Args:
            assessment: The assessment being answered
            response: The learner's response text
            learner_id: Optional learner identifier for tracking

        Returns:
            GradingResult with score, feedback, and analysis
        """
        # For multiple choice, use simple matching
        if assessment.assessment_type == AssessmentType.MULTIPLE_CHOICE:
            return self._grade_multiple_choice(assessment, response)

        # For free response and others, use LLM
        return self._grade_with_llm(assessment, response)

    def _grade_multiple_choice(
        self, assessment: Assessment, response: str
    ) -> GradingResult:
        """Grade a multiple choice response by matching."""
        response_clean = response.strip().upper()

        # Find correct option
        correct_option = None
        selected_option = None

        for i, option in enumerate(assessment.options):
            # Check if response matches option letter (A, B, C, D) or text
            option_letter = chr(65 + i)  # A, B, C, D...
            if response_clean == option_letter or response_clean == option.text.strip().upper():
                selected_option = option

            if option.is_correct:
                correct_option = option

        is_correct = selected_option is not None and selected_option.is_correct

        if is_correct:
            return GradingResult(
                score=1.0,
                is_correct=True,
                feedback="Correct! " + (correct_option.explanation if correct_option else ""),
                strengths=["Correctly identified the answer"],
            )
        else:
            explanation = ""
            if correct_option and correct_option.explanation:
                explanation = f" {correct_option.explanation}"

            return GradingResult(
                score=0.0,
                is_correct=False,
                feedback=f"Not quite.{explanation}",
                areas_for_improvement=["Review the concept and try again"],
            )

    def _grade_with_llm(
        self, assessment: Assessment, response: str
    ) -> GradingResult:
        """Grade a free-response using LLM evaluation."""
        bloom_info = self.BLOOM_CRITERIA.get(
            assessment.bloom_level,
            self.BLOOM_CRITERIA[BloomLevel.COMPREHENSION]
        )

        system_prompt = self._build_grading_prompt(assessment, bloom_info)
        user_prompt = self._build_user_prompt(assessment, response)

        try:
            llm_response = self.llm_client.complete(
                user_message=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for consistent grading
            )

            return self._parse_grading_response(llm_response.content)
        except Exception as e:
            # Fallback for API errors
            return GradingResult(
                score=0.5,
                is_correct=False,
                feedback=f"Unable to grade response automatically. Please review manually.",
                grading_rationale=f"Grading error: {str(e)}",
            )

    def _build_grading_prompt(
        self, assessment: Assessment, bloom_info: dict
    ) -> str:
        """Build the system prompt for grading."""
        criteria_list = "\n".join(f"- {c}" for c in bloom_info["criteria"])

        rubric_section = ""
        if assessment.rubric:
            rubric_section = f"""
## Rubric
{assessment.rubric}
"""

        sample_section = ""
        if assessment.sample_answer:
            sample_section = f"""
## Sample Correct Answer
{assessment.sample_answer}
"""

        return f"""You are an expert educational assessor evaluating student responses.
Your goal is to provide accurate, constructive feedback that helps learners improve.

## Assessment Context
- Concept Being Assessed: {assessment.concept_id}
- Bloom's Taxonomy Level: {assessment.bloom_level.value.title()}
- Focus: {bloom_info["focus"]}
- Assessment Type: {assessment.assessment_type.value}

## Evaluation Criteria for {assessment.bloom_level.value.title()} Level
{criteria_list}
{rubric_section}{sample_section}
## Grading Instructions
1. Read the question and learner's response carefully
2. Evaluate against the criteria for this Bloom level
3. Assign a score from 0.0 to 1.0:
   - 0.0-0.3: Significant gaps or errors
   - 0.4-0.6: Partial understanding with room for improvement
   - 0.7-0.8: Good understanding with minor issues
   - 0.9-1.0: Excellent, demonstrates mastery

## Response Format
Respond with a JSON object containing:
{{
    "score": <float 0.0-1.0>,
    "feedback": "<constructive feedback for the learner>",
    "strengths": ["<strength 1>", "<strength 2>"],
    "areas_for_improvement": ["<area 1>", "<area 2>"],
    "grading_rationale": "<explanation of how score was determined>",
    "concept_understanding": "<brief assessment of their understanding level>"
}}

Be encouraging but honest. Focus on helping the learner grow."""

    def _build_user_prompt(self, assessment: Assessment, response: str) -> str:
        """Build the user prompt containing question and response."""
        context_section = ""
        if assessment.context:
            context_section = f"""
Context:
{assessment.context}
"""

        return f"""## Question
{assessment.question}
{context_section}
## Learner's Response
{response}

Please evaluate this response and provide your assessment in JSON format."""

    def _parse_grading_response(self, llm_output: str) -> GradingResult:
        """Parse the LLM's grading response into a GradingResult."""
        try:
            # Try to extract JSON from the response
            json_match = re.search(r'\{[\s\S]*\}', llm_output)
            if json_match:
                data = json.loads(json_match.group())

                score = float(data.get("score", 0.5))
                score = max(0.0, min(1.0, score))  # Clamp to valid range

                return GradingResult(
                    score=score,
                    is_correct=score >= 0.7,
                    feedback=data.get("feedback", ""),
                    strengths=data.get("strengths", []),
                    areas_for_improvement=data.get("areas_for_improvement", []),
                    grading_rationale=data.get("grading_rationale", ""),
                    concept_understanding=data.get("concept_understanding", ""),
                )
        except (json.JSONDecodeError, ValueError, KeyError):
            pass

        # Fallback: try to extract a numeric score
        score_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:/\s*1(?:\.0)?|out of 1)', llm_output.lower())
        if score_match:
            score = float(score_match.group(1))
            if score > 1:
                score = score / 100  # Handle percentage format
            score = max(0.0, min(1.0, score))

            return GradingResult(
                score=score,
                is_correct=score >= 0.7,
                feedback=llm_output,
            )

        # Last resort: return the raw output as feedback
        return GradingResult(
            score=0.5,
            is_correct=False,
            feedback=llm_output[:500] if len(llm_output) > 500 else llm_output,
            grading_rationale="Could not parse structured response from LLM",
        )

    def create_assessment_result(
        self,
        assessment: Assessment,
        response: str,
        learner_id: str,
        grading_result: GradingResult | None = None,
    ) -> AssessmentResult:
        """Create an AssessmentResult from a grading.

        Args:
            assessment: The assessment that was answered
            response: The learner's response
            learner_id: The learner's identifier
            grading_result: Optional pre-computed grading result

        Returns:
            AssessmentResult ready for storage
        """
        if grading_result is None:
            grading_result = self.grade(assessment, response, learner_id)

        return AssessmentResult(
            assessment_id=assessment.assessment_id,
            learner_id=learner_id,
            timestamp=datetime.now(timezone.utc),
            response=response,
            is_correct=grading_result.is_correct,
            score=grading_result.score,
            feedback=grading_result.feedback,
            grading_rationale=grading_result.grading_rationale,
            strengths=grading_result.strengths,
            areas_for_improvement=grading_result.areas_for_improvement,
        )


def grade_response(
    assessment: Assessment,
    response: str,
    learner_id: str = "",
) -> GradingResult:
    """Convenience function to grade a response without creating a grader instance.

    Args:
        assessment: The assessment being answered
        response: The learner's response
        learner_id: Optional learner identifier

    Returns:
        GradingResult with score and feedback
    """
    grader = AssessmentGrader()
    return grader.grade(assessment, response, learner_id)

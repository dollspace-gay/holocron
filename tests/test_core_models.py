"""Tests for core data models."""

from datetime import datetime, timedelta, timezone

import pytest

from holocron.core.models import (
    Assessment,
    AssessmentOption,
    AssessmentResult,
    AssessmentType,
    BloomLevel,
    Concept,
    ConceptGraph,
    ConceptMastery,
    LearnerProfile,
)


class TestConcept:
    """Tests for Concept dataclass."""

    def test_concept_creation(self):
        """Test basic concept creation."""
        concept = Concept(
            concept_id="python.list_comprehension",
            domain_id="python-programming",
            name="List Comprehension",
            description="A concise way to create lists",
        )

        assert concept.concept_id == "python.list_comprehension"
        assert concept.domain_id == "python-programming"
        assert concept.name == "List Comprehension"
        assert concept.difficulty_score == 5  # default

    def test_concept_with_relationships(self):
        """Test concept with prerequisites and related concepts."""
        concept = Concept(
            concept_id="python.generator_expression",
            domain_id="python-programming",
            name="Generator Expression",
            description="Memory-efficient iteration",
            prerequisites=["python.list_comprehension", "python.iterators"],
            related_concepts=["python.generators"],
        )

        assert len(concept.prerequisites) == 2
        assert "python.list_comprehension" in concept.prerequisites


class TestConceptMastery:
    """Tests for ConceptMastery dataclass."""

    def test_overall_mastery_calculation(self):
        """Test weighted mastery calculation."""
        mastery = ConceptMastery(
            concept_id="test",
            learner_id="learner1",
            recognition_score=100,  # 0.2 weight
            comprehension_score=100,  # 0.3 weight
            application_score=100,  # 0.5 weight
        )

        assert mastery.overall_mastery == 100.0

    def test_overall_mastery_weights(self):
        """Test that weights are applied correctly."""
        mastery = ConceptMastery(
            concept_id="test",
            learner_id="learner1",
            recognition_score=50,  # contributes 10
            comprehension_score=50,  # contributes 15
            application_score=50,  # contributes 25
        )

        # 50 * 0.2 + 50 * 0.3 + 50 * 0.5 = 10 + 15 + 25 = 50
        assert mastery.overall_mastery == 50.0

    def test_scaffold_level_low_mastery(self):
        """Test scaffold level for low mastery."""
        mastery = ConceptMastery(
            concept_id="test",
            learner_id="learner1",
            recognition_score=10,
            comprehension_score=10,
            application_score=10,
        )

        assert mastery.get_scaffold_level() == 1  # Max support

    def test_scaffold_level_high_mastery(self):
        """Test scaffold level for high mastery."""
        mastery = ConceptMastery(
            concept_id="test",
            learner_id="learner1",
            recognition_score=90,
            comprehension_score=90,
            application_score=90,
        )

        assert mastery.get_scaffold_level() == 5  # Min support

    def test_is_due_for_review_no_date(self):
        """Test due for review when no next_review set."""
        mastery = ConceptMastery(
            concept_id="test",
            learner_id="learner1",
        )

        assert mastery.is_due_for_review() is True

    def test_is_due_for_review_future(self):
        """Test not due for review when next_review is in future."""
        mastery = ConceptMastery(
            concept_id="test",
            learner_id="learner1",
            next_review=datetime.now(timezone.utc) + timedelta(days=1),
        )

        assert mastery.is_due_for_review() is False


class TestLearnerProfile:
    """Tests for LearnerProfile dataclass."""

    def test_get_mastery_creates_new(self):
        """Test that get_mastery creates new mastery if not exists."""
        profile = LearnerProfile(
            learner_id="learner1",
            name="Test Learner",
        )

        mastery = profile.get_mastery("python", "list_comprehension")

        assert mastery.concept_id == "list_comprehension"
        assert mastery.learner_id == "learner1"
        assert "python" in profile.domain_mastery

    def test_get_mastery_returns_existing(self):
        """Test that get_mastery returns existing mastery."""
        profile = LearnerProfile(
            learner_id="learner1",
            name="Test Learner",
        )

        # Get twice
        mastery1 = profile.get_mastery("python", "list_comprehension")
        mastery1.recognition_score = 50
        mastery2 = profile.get_mastery("python", "list_comprehension")

        assert mastery2.recognition_score == 50

    def test_domain_overall_mastery(self):
        """Test domain-wide mastery calculation."""
        profile = LearnerProfile(
            learner_id="learner1",
            name="Test Learner",
        )

        m1 = profile.get_mastery("python", "concept1")
        m1.recognition_score = 100
        m1.comprehension_score = 100
        m1.application_score = 100

        m2 = profile.get_mastery("python", "concept2")
        m2.recognition_score = 0
        m2.comprehension_score = 0
        m2.application_score = 0

        # Average of 100 and 0
        assert profile.get_domain_overall_mastery("python") == 50.0


class TestConceptGraph:
    """Tests for ConceptGraph."""

    def test_add_concept(self):
        """Test adding concepts to graph."""
        graph = ConceptGraph(domain_id="python")

        concept = Concept(
            concept_id="python.basics",
            domain_id="python",
            name="Python Basics",
            description="Basic Python concepts",
        )

        graph.add_concept(concept)

        assert "python.basics" in graph.concepts

    def test_get_prerequisites(self):
        """Test getting prerequisites for a concept."""
        graph = ConceptGraph(domain_id="python")

        basic = Concept(
            concept_id="python.basics",
            domain_id="python",
            name="Basics",
            description="Basic concepts",
        )

        advanced = Concept(
            concept_id="python.advanced",
            domain_id="python",
            name="Advanced",
            description="Advanced concepts",
            prerequisites=["python.basics"],
        )

        graph.add_concept(basic)
        graph.add_concept(advanced)

        prereqs = graph.get_prerequisites("python.advanced")
        assert "python.basics" in prereqs

    def test_get_learning_path(self):
        """Test topological sort for learning path."""
        graph = ConceptGraph(domain_id="python")

        # Create a chain: A <- B <- C
        a = Concept(
            concept_id="a",
            domain_id="python",
            name="A",
            description="Concept A",
        )
        b = Concept(
            concept_id="b",
            domain_id="python",
            name="B",
            description="Concept B",
            prerequisites=["a"],
        )
        c = Concept(
            concept_id="c",
            domain_id="python",
            name="C",
            description="Concept C",
            prerequisites=["b"],
        )

        graph.add_concept(a)
        graph.add_concept(b)
        graph.add_concept(c)

        path = graph.get_learning_path("c")

        # Should be [a, b, c] in order
        assert path == ["a", "b", "c"]

    def test_get_next_concepts(self):
        """Test getting concepts ready to learn."""
        graph = ConceptGraph(domain_id="python")

        a = Concept(
            concept_id="a",
            domain_id="python",
            name="A",
            description="Concept A",
        )
        b = Concept(
            concept_id="b",
            domain_id="python",
            name="B",
            description="Concept B",
            prerequisites=["a"],
        )

        graph.add_concept(a)
        graph.add_concept(b)

        # Nothing mastered - only A is available
        ready = graph.get_next_concepts(set())
        assert "a" in ready
        assert "b" not in ready

        # A mastered - B is now available
        ready = graph.get_next_concepts({"a"})
        assert "b" in ready


class TestAssessment:
    """Tests for Assessment dataclass."""

    def test_multiple_choice_assessment(self):
        """Test creating a multiple choice assessment."""
        assessment = Assessment(
            assessment_id="assess1",
            concept_id="python.list_comprehension",
            bloom_level=BloomLevel.KNOWLEDGE,
            assessment_type=AssessmentType.MULTIPLE_CHOICE,
            question="What is the output of [x*2 for x in [1,2,3]]?",
            options=[
                AssessmentOption(text="[2,4,6]", is_correct=True),
                AssessmentOption(text="[1,2,3]", is_correct=False),
                AssessmentOption(text="[1,4,9]", is_correct=False),
            ],
        )

        assert assessment.bloom_level == BloomLevel.KNOWLEDGE
        assert len(assessment.options) == 3
        assert sum(1 for o in assessment.options if o.is_correct) == 1

    def test_free_response_assessment(self):
        """Test creating a free response assessment."""
        assessment = Assessment(
            assessment_id="assess2",
            concept_id="python.list_comprehension",
            bloom_level=BloomLevel.COMPREHENSION,
            assessment_type=AssessmentType.FREE_RESPONSE,
            question="Explain list comprehension in your own words.",
            rubric="Should mention: concise syntax, iteration, optional filter",
            sample_answer="A list comprehension is a compact way to create lists...",
        )

        assert assessment.assessment_type == AssessmentType.FREE_RESPONSE
        assert assessment.rubric != ""

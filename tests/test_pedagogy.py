"""Tests for the pedagogical transformer module."""

import pytest

from holocron.core.models import BloomLevel, Concept, ConceptMastery
from holocron.core.pedagogy import (
    DualCodingStrategy,
    ElaborativeEncodingStrategy,
    FeynmanStrategy,
    InterleavingStrategy,
    PedagogicalTechnique,
    PedagogicalTransformer,
    RetrievalPracticeStrategy,
    TechniqueResult,
)


@pytest.fixture
def sample_concept():
    """Create a sample concept."""
    return Concept(
        concept_id="python.list_comprehension",
        domain_id="python-programming",
        name="List Comprehension",
        description="A concise way to create lists in Python using a single line of code.",
        examples=["[x**2 for x in range(10)]", "[s.upper() for s in strings]"],
        analogies=["Like a recipe that transforms ingredients into a dish in one step"],
        visual_description="Picture a factory assembly line where items enter one end and exit transformed",
        difficulty_score=5,
    )


@pytest.fixture
def low_mastery():
    """Create low mastery state."""
    return ConceptMastery(
        concept_id="python.list_comprehension",
        learner_id="test-learner",
        recognition_score=20.0,
        comprehension_score=10.0,
        application_score=5.0,
        exposure_count=2,
    )


@pytest.fixture
def medium_mastery():
    """Create medium mastery state."""
    return ConceptMastery(
        concept_id="python.list_comprehension",
        learner_id="test-learner",
        recognition_score=60.0,
        comprehension_score=50.0,
        application_score=40.0,
        exposure_count=10,
    )


@pytest.fixture
def high_mastery():
    """Create high mastery state."""
    return ConceptMastery(
        concept_id="python.list_comprehension",
        learner_id="test-learner",
        recognition_score=90.0,
        comprehension_score=85.0,
        application_score=80.0,
        exposure_count=25,
    )


class TestTechniqueResult:
    """Tests for TechniqueResult dataclass."""

    def test_create_result(self):
        """Test creating a technique result."""
        result = TechniqueResult(
            technique=PedagogicalTechnique.ELABORATIVE_ENCODING,
            original_content="Original",
            transformed_content="Original + Elaboration",
        )

        assert result.technique == PedagogicalTechnique.ELABORATIVE_ENCODING
        assert result.original_content == "Original"
        assert "Elaboration" in result.transformed_content
        assert result.metadata == {}

    def test_result_with_metadata(self):
        """Test result with metadata."""
        result = TechniqueResult(
            technique=PedagogicalTechnique.DUAL_CODING,
            original_content="Text",
            transformed_content="Text with image",
            metadata={"visual": "A picture of..."},
        )

        assert result.metadata["visual"] == "A picture of..."


class TestElaborativeEncodingStrategy:
    """Tests for ElaborativeEncodingStrategy."""

    def test_uses_existing_analogies(self, sample_concept, low_mastery):
        """Test that existing analogies are used."""
        strategy = ElaborativeEncodingStrategy()
        result = strategy.apply(sample_concept, low_mastery)

        assert "recipe" in result.transformed_content.lower()
        assert result.technique == PedagogicalTechnique.ELABORATIVE_ENCODING

    def test_is_appropriate_for_low_mastery(self, sample_concept, low_mastery):
        """Test appropriateness for low mastery."""
        strategy = ElaborativeEncodingStrategy()
        assert strategy.is_appropriate(sample_concept, low_mastery) is True

    def test_not_appropriate_for_high_mastery(self, sample_concept, high_mastery):
        """Test not appropriate for high mastery."""
        strategy = ElaborativeEncodingStrategy()
        assert strategy.is_appropriate(sample_concept, high_mastery) is False


class TestDualCodingStrategy:
    """Tests for DualCodingStrategy."""

    def test_uses_existing_visual(self, sample_concept, low_mastery):
        """Test that existing visual descriptions are used."""
        strategy = DualCodingStrategy()
        result = strategy.apply(sample_concept, low_mastery)

        assert "factory" in result.transformed_content.lower() or "Mental Image" in result.transformed_content
        assert result.technique == PedagogicalTechnique.DUAL_CODING

    def test_is_appropriate_for_new_concepts(self, sample_concept, low_mastery):
        """Test appropriateness for new concepts."""
        strategy = DualCodingStrategy()
        assert strategy.is_appropriate(sample_concept, low_mastery) is True


class TestFeynmanStrategy:
    """Tests for FeynmanStrategy."""

    def test_simplifies_with_examples(self, sample_concept, medium_mastery):
        """Test simplification using examples."""
        strategy = FeynmanStrategy()
        result = strategy.apply(sample_concept, medium_mastery)

        assert "Plain English" in result.transformed_content
        assert result.technique == PedagogicalTechnique.FEYNMAN

    def test_is_appropriate_for_difficult_concepts(self, sample_concept, medium_mastery):
        """Test appropriateness for difficult concepts."""
        strategy = FeynmanStrategy()

        # Lower difficulty - not appropriate
        sample_concept.difficulty_score = 3
        medium_mastery.comprehension_score = 60
        assert strategy.is_appropriate(sample_concept, medium_mastery) is False

        # High difficulty - appropriate
        sample_concept.difficulty_score = 8
        assert strategy.is_appropriate(sample_concept, medium_mastery) is True


class TestInterleavingStrategy:
    """Tests for InterleavingStrategy."""

    def test_with_related_concepts(self, sample_concept, medium_mastery):
        """Test interleaving with related concepts."""
        related = Concept(
            concept_id="python.generator_expression",
            domain_id="python-programming",
            name="Generator Expression",
            description="A memory-efficient way to iterate over large sequences.",
        )

        strategy = InterleavingStrategy(related_concepts=[related])
        result = strategy.apply(sample_concept, medium_mastery)

        assert "Generator Expression" in result.transformed_content or "Compare" in result.transformed_content
        assert result.technique == PedagogicalTechnique.INTERLEAVING

    def test_is_appropriate_after_basic_understanding(self, sample_concept, low_mastery, medium_mastery):
        """Test appropriateness based on recognition level."""
        strategy = InterleavingStrategy()

        # Low recognition - not appropriate
        low_mastery.recognition_score = 30
        assert strategy.is_appropriate(sample_concept, low_mastery) is False

        # Medium recognition - appropriate
        assert strategy.is_appropriate(sample_concept, medium_mastery) is True


class TestRetrievalPracticeStrategy:
    """Tests for RetrievalPracticeStrategy."""

    def test_generates_prompts_for_low_mastery(self, sample_concept, low_mastery):
        """Test prompt generation for low mastery."""
        strategy = RetrievalPracticeStrategy()
        result = strategy.apply(sample_concept, low_mastery)

        assert "Quick Check" in result.transformed_content or "define" in result.transformed_content.lower()
        assert result.technique == PedagogicalTechnique.RETRIEVAL_PRACTICE

    def test_generates_prompts_for_medium_mastery(self, sample_concept, medium_mastery):
        """Test prompt generation for medium mastery."""
        strategy = RetrievalPracticeStrategy()
        result = strategy.apply(sample_concept, medium_mastery)

        assert "Think About It" in result.transformed_content or "explain" in result.transformed_content.lower()

    def test_generates_prompts_for_high_mastery(self, sample_concept, high_mastery):
        """Test prompt generation for high mastery."""
        strategy = RetrievalPracticeStrategy()
        result = strategy.apply(sample_concept, high_mastery)

        assert "Challenge" in result.transformed_content or "relate" in result.transformed_content.lower()


class TestPedagogicalTransformer:
    """Tests for PedagogicalTransformer."""

    def test_init_default_strategies(self):
        """Test default strategy initialization."""
        transformer = PedagogicalTransformer()

        assert PedagogicalTechnique.ELABORATIVE_ENCODING in transformer._strategies
        assert PedagogicalTechnique.DUAL_CODING in transformer._strategies
        assert PedagogicalTechnique.FEYNMAN in transformer._strategies
        assert PedagogicalTechnique.INTERLEAVING in transformer._strategies
        assert PedagogicalTechnique.RETRIEVAL_PRACTICE in transformer._strategies

    def test_get_recommended_for_low_mastery(self, sample_concept, low_mastery):
        """Test recommendations for low mastery learners."""
        transformer = PedagogicalTransformer()
        recommended = transformer.get_recommended_techniques(sample_concept, low_mastery)

        # Should prioritize encoding techniques
        assert PedagogicalTechnique.ELABORATIVE_ENCODING in recommended
        assert len(recommended) <= 3

    def test_get_recommended_for_high_mastery(self, sample_concept, high_mastery):
        """Test recommendations for high mastery learners."""
        transformer = PedagogicalTransformer()
        recommended = transformer.get_recommended_techniques(sample_concept, high_mastery)

        # Should prioritize discrimination and retrieval
        assert PedagogicalTechnique.INTERLEAVING in recommended or PedagogicalTechnique.RETRIEVAL_PRACTICE in recommended

    def test_transform_applies_techniques(self, sample_concept, low_mastery):
        """Test that transform applies techniques."""
        transformer = PedagogicalTransformer()
        result = transformer.transform(sample_concept, low_mastery)

        assert result.transformed_content != sample_concept.description
        assert "techniques_applied" in result.metadata
        assert len(result.metadata["techniques_applied"]) > 0

    def test_transform_with_specific_techniques(self, sample_concept, low_mastery):
        """Test transform with specific techniques requested."""
        transformer = PedagogicalTransformer()
        result = transformer.transform(
            sample_concept,
            low_mastery,
            techniques=[PedagogicalTechnique.ELABORATIVE_ENCODING],
        )

        assert "elaborative_encoding" in result.metadata["techniques_applied"]
        assert len(result.metadata["techniques_applied"]) == 1

    def test_apply_single_technique(self, sample_concept, medium_mastery):
        """Test applying a single technique."""
        transformer = PedagogicalTransformer()
        result = transformer.apply_single(
            PedagogicalTechnique.FEYNMAN,
            sample_concept,
            medium_mastery,
        )

        assert result.technique == PedagogicalTechnique.FEYNMAN
        assert "Plain English" in result.transformed_content

    def test_transform_with_context(self, sample_concept, low_mastery):
        """Test transform with additional context."""
        transformer = PedagogicalTransformer()
        context = "Custom context for transformation."

        result = transformer.transform(
            sample_concept,
            low_mastery,
            context=context,
        )

        assert context in result.original_content or context in result.transformed_content

    def test_transform_with_llm_callback(self, sample_concept, low_mastery):
        """Test transform with LLM callback."""
        def mock_llm(system: str, user: str) -> str:
            return "LLM-generated response"

        transformer = PedagogicalTransformer(llm_callback=mock_llm)
        result = transformer.transform(
            sample_concept,
            low_mastery,
            techniques=[PedagogicalTechnique.RETRIEVAL_PRACTICE],
        )

        # Should include LLM-generated content
        assert "LLM-generated response" in result.transformed_content


class TestPedagogicalTechniqueEnum:
    """Tests for PedagogicalTechnique enum."""

    def test_technique_values(self):
        """Test technique enum values."""
        assert PedagogicalTechnique.ELABORATIVE_ENCODING.value == "elaborative_encoding"
        assert PedagogicalTechnique.DUAL_CODING.value == "dual_coding"
        assert PedagogicalTechnique.FEYNMAN.value == "feynman"
        assert PedagogicalTechnique.INTERLEAVING.value == "interleaving"
        assert PedagogicalTechnique.RETRIEVAL_PRACTICE.value == "retrieval_practice"
        assert PedagogicalTechnique.SPACED_REPETITION.value == "spaced_repetition"
        assert PedagogicalTechnique.SCAFFOLDING.value == "scaffolding"

    def test_all_techniques_listed(self):
        """Test that all expected techniques exist."""
        techniques = list(PedagogicalTechnique)
        assert len(techniques) >= 5  # At least 5 core techniques

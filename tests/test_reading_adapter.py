"""Tests for Reading Skills Domain Adapter."""

import pytest

from holocron.core.models import BloomLevel, ConceptMastery
from holocron.domains.reading.adapter import ReadingSkillsAdapter
from holocron.domains.registry import DomainRegistry


@pytest.fixture
def adapter() -> ReadingSkillsAdapter:
    """Create a fresh reading adapter instance."""
    # Clear registry to avoid conflicts between tests
    DomainRegistry.clear_instances()
    return DomainRegistry.get("reading-skills")


@pytest.fixture
def sample_text() -> str:
    """Sample text for testing concept extraction."""
    return """
    The phenomenon of photosynthesis is fundamental to understanding plant biology.
    Photosynthesis occurs in the chloroplasts of plant cells, where chlorophyll
    absorbs light energy. This energy drives the synthesis of glucose from carbon
    dioxide and water. The process releases oxygen as a byproduct, which is
    essential for aerobic organisms. Understanding photosynthesis helps us
    appreciate the interconnectedness of ecosystems and the carbon cycle.
    Photosynthesis is truly a remarkable biological phenomenon that sustains life.
    """


class TestReadingSkillsAdapter:
    """Tests for ReadingSkillsAdapter."""

    def test_adapter_registration(self):
        """Test that adapter is properly registered."""
        assert DomainRegistry.is_registered("reading-skills")

    def test_adapter_config(self, adapter):
        """Test adapter configuration."""
        config = adapter.config

        assert config.domain_id == "reading-skills"
        assert config.display_name == "Reading Skills"
        assert ".txt" in config.file_extensions
        assert ".pdf" in config.file_extensions
        assert "vocabulary" in config.description.lower() or "reading" in config.description.lower()

    def test_extract_concepts(self, adapter, sample_text):
        """Test concept extraction from text."""
        concepts = adapter.extract_concepts(sample_text)

        # Should extract some concepts
        assert len(concepts) > 0

        # Check concept structure
        for concept in concepts:
            assert concept.concept_id.startswith("reading.vocab.")
            assert concept.domain_id == "reading-skills"
            assert concept.name  # Should have a name
            assert "word" in concept.domain_data

    def test_extract_concepts_filters_common_words(self, adapter, sample_text):
        """Test that common words are filtered out."""
        concepts = adapter.extract_concepts(sample_text)
        words = [c.domain_data["word"] for c in concepts]

        # Common words should not be in results
        assert "the" not in words
        assert "and" not in words
        assert "for" not in words

    def test_extract_concepts_finds_domain_vocabulary(self, adapter, sample_text):
        """Test that domain-specific vocabulary is extracted."""
        concepts = adapter.extract_concepts(sample_text)
        words = [c.domain_data["word"] for c in concepts]

        # Should find key vocabulary
        assert "photosynthesis" in words
        assert "chloroplasts" in words or "chlorophyll" in words

    def test_concept_difficulty_scoring(self, adapter, sample_text):
        """Test that difficulty scores are assigned."""
        concepts = adapter.extract_concepts(sample_text)

        for concept in concepts:
            assert 1 <= concept.difficulty_score <= 10

    def test_concept_contexts(self, adapter, sample_text):
        """Test that contexts are extracted for vocabulary."""
        concepts = adapter.extract_concepts(sample_text)

        # Find photosynthesis concept
        photo_concept = next(
            (c for c in concepts if c.domain_data["word"] == "photosynthesis"),
            None,
        )

        assert photo_concept is not None
        assert "original_contexts" in photo_concept.domain_data
        assert len(photo_concept.domain_data["original_contexts"]) > 0

    def test_generate_knowledge_assessment(self, adapter, sample_text):
        """Test generating knowledge-level assessment."""
        concepts = adapter.extract_concepts(sample_text)
        concept = concepts[0]

        assessment = adapter.generate_assessment(
            concept, BloomLevel.KNOWLEDGE, context="Test context"
        )

        assert assessment.concept_id == concept.concept_id
        assert assessment.bloom_level == BloomLevel.KNOWLEDGE
        assert len(assessment.options) > 0

    def test_generate_comprehension_assessment(self, adapter, sample_text):
        """Test generating comprehension-level assessment."""
        concepts = adapter.extract_concepts(sample_text)
        concept = concepts[0]

        assessment = adapter.generate_assessment(
            concept, BloomLevel.COMPREHENSION
        )

        assert assessment.bloom_level == BloomLevel.COMPREHENSION
        assert assessment.rubric  # Should have grading rubric
        assert "explain" in assessment.question.lower() or "meaning" in assessment.question.lower()

    def test_generate_application_assessment(self, adapter, sample_text):
        """Test generating application-level assessment."""
        concepts = adapter.extract_concepts(sample_text)
        concept = concepts[0]

        assessment = adapter.generate_assessment(
            concept, BloomLevel.APPLICATION
        )

        assert assessment.bloom_level == BloomLevel.APPLICATION
        assert "sentence" in assessment.question.lower() or "write" in assessment.question.lower()

    def test_scaffold_prompt_level_1(self, adapter, sample_text):
        """Test maximum scaffolding prompt generation."""
        concepts = adapter.extract_concepts(sample_text)

        # Create low mastery records
        concept_mastery = [
            (c, ConceptMastery(concept_id=c.concept_id, learner_id="test", recognition_score=10))
            for c in concepts[:5]
        ]

        prompt = adapter.get_scaffold_prompt(1, concept_mastery)

        assert "Maximum Support" in prompt or "maximum" in prompt.lower()
        assert "definition" in prompt.lower()

    def test_scaffold_prompt_level_5(self, adapter, sample_text):
        """Test minimal scaffolding prompt generation."""
        concepts = adapter.extract_concepts(sample_text)

        # Create high mastery records
        concept_mastery = [
            (
                c,
                ConceptMastery(
                    concept_id=c.concept_id,
                    learner_id="test",
                    recognition_score=90,
                    comprehension_score=90,
                    application_score=90,
                ),
            )
            for c in concepts[:5]
        ]

        prompt = adapter.get_scaffold_prompt(5, concept_mastery)

        assert "Minimal Support" in prompt or "minimal" in prompt.lower()

    def test_validate_content_valid(self, adapter, sample_text):
        """Test content validation with valid text."""
        assert adapter.validate_content(sample_text) is True

    def test_validate_content_too_short(self, adapter):
        """Test content validation with too-short text."""
        assert adapter.validate_content("Too short") is False

    def test_validate_content_no_words(self, adapter):
        """Test content validation with no real words."""
        assert adapter.validate_content("123 456 789 " * 50) is False

    def test_preprocess_content(self, adapter):
        """Test content preprocessing."""
        messy_text = "  Page 1   Some text   [1]  with   extra   spaces  Page 2  "
        cleaned = adapter.preprocess_content(messy_text)

        # Should remove page markers and citation markers
        assert "Page 1" not in cleaned
        assert "Page 2" not in cleaned
        assert "[1]" not in cleaned
        # Should normalize whitespace
        assert "   " not in cleaned


class TestDomainRegistryIntegration:
    """Test integration with domain registry."""

    def test_get_reading_adapter(self):
        """Test retrieving reading adapter from registry."""
        DomainRegistry.clear_instances()
        adapter = DomainRegistry.get("reading-skills")

        assert isinstance(adapter, ReadingSkillsAdapter)

    def test_list_domains_includes_reading(self):
        """Test that reading domain is listed."""
        domains = DomainRegistry.list_domains()

        assert "reading-skills" in domains

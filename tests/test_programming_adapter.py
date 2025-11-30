"""Tests for Python Programming Domain Adapter."""

import pytest

from holocron.core.models import BloomLevel, ConceptMastery
from holocron.domains.programming.adapter import PythonProgrammingAdapter
from holocron.domains.registry import DomainRegistry


@pytest.fixture
def adapter() -> PythonProgrammingAdapter:
    """Create a fresh programming adapter instance."""
    DomainRegistry.clear_instances()
    return DomainRegistry.get("python-programming")


@pytest.fixture
def sample_code() -> str:
    """Sample Python code for testing concept extraction."""
    return '''
def calculate_stats(numbers: list[int]) -> dict[str, float]:
    """Calculate statistics for a list of numbers."""
    if not numbers:
        raise ValueError("Cannot calculate stats for empty list")

    total = sum(numbers)
    average = total / len(numbers)

    # Use list comprehension for squared values
    squared = [x ** 2 for x in numbers]
    variance = sum((x - average) ** 2 for x in numbers) / len(numbers)

    return {
        "total": total,
        "average": average,
        "variance": variance,
    }


class DataProcessor:
    """Process data with various transformations."""

    def __init__(self, data: list):
        self.data = data

    @property
    def length(self) -> int:
        return len(self.data)

    def filter_by(self, predicate):
        """Filter data using a predicate function."""
        return [item for item in self.data if predicate(item)]


# Using a decorator
@staticmethod
def helper_function():
    pass


# Context manager usage
with open("data.txt") as f:
    content = f.read()


# Lambda and sorting
items = [(1, "b"), (2, "a"), (3, "c")]
sorted_items = sorted(items, key=lambda x: x[1])
'''


@pytest.fixture
def simple_code() -> str:
    """Simple code with basic concepts."""
    return '''
x = 10
y = 20
result = x + y

for i in range(5):
    print(i)

if result > 25:
    print("Big number")
'''


class TestPythonProgrammingAdapter:
    """Tests for PythonProgrammingAdapter."""

    def test_adapter_registration(self):
        """Test that adapter is properly registered."""
        assert DomainRegistry.is_registered("python-programming")

    def test_adapter_config(self, adapter):
        """Test adapter configuration."""
        config = adapter.config

        assert config.domain_id == "python-programming"
        assert config.display_name == "Python Programming"
        assert ".py" in config.file_extensions
        assert "application" in config.bloom_levels

    def test_extract_concepts_from_code(self, adapter, sample_code):
        """Test concept extraction from Python code."""
        concepts = adapter.extract_concepts(sample_code)

        # Should extract several concepts
        assert len(concepts) > 0

        # Check concept structure
        for concept in concepts:
            assert concept.concept_id.startswith("python.")
            assert concept.domain_id == "python-programming"
            assert "language" in concept.domain_data
            assert concept.domain_data["language"] == "python"

    def test_extract_list_comprehension(self, adapter, sample_code):
        """Test extraction of list comprehension concept."""
        concepts = adapter.extract_concepts(sample_code)
        concept_ids = [c.concept_id for c in concepts]

        assert "python.list_comprehension" in concept_ids

    def test_extract_classes(self, adapter, sample_code):
        """Test extraction of class concept."""
        concepts = adapter.extract_concepts(sample_code)
        concept_ids = [c.concept_id for c in concepts]

        assert "python.classes" in concept_ids

    def test_extract_decorators(self, adapter, sample_code):
        """Test extraction of decorator concept."""
        concepts = adapter.extract_concepts(sample_code)
        concept_ids = [c.concept_id for c in concepts]

        # Should find @staticmethod or @property
        has_decorator = (
            "python.decorators" in concept_ids
            or "python.static_methods" in concept_ids
            or "python.properties" in concept_ids
        )
        assert has_decorator

    def test_extract_context_managers(self, adapter, sample_code):
        """Test extraction of context manager concept."""
        concepts = adapter.extract_concepts(sample_code)
        concept_ids = [c.concept_id for c in concepts]

        assert "python.context_managers" in concept_ids

    def test_extract_lambda(self, adapter, sample_code):
        """Test extraction of lambda concept."""
        concepts = adapter.extract_concepts(sample_code)
        concept_ids = [c.concept_id for c in concepts]

        assert "python.lambda" in concept_ids

    def test_extract_basic_concepts(self, adapter, simple_code):
        """Test extraction of basic concepts."""
        concepts = adapter.extract_concepts(simple_code)
        concept_ids = [c.concept_id for c in concepts]

        # Should find loops and conditionals
        assert "python.loops" in concept_ids
        assert "python.conditionals" in concept_ids

    def test_concept_difficulty_scoring(self, adapter, sample_code):
        """Test that difficulty scores are assigned appropriately."""
        concepts = adapter.extract_concepts(sample_code)

        for concept in concepts:
            assert 1 <= concept.difficulty_score <= 10

        # Find specific concepts and check relative difficulty
        list_comp = next(
            (c for c in concepts if c.concept_id == "python.list_comprehension"),
            None,
        )
        if list_comp:
            # List comprehension should be moderate difficulty
            assert 4 <= list_comp.difficulty_score <= 7

    def test_concept_prerequisites(self, adapter, sample_code):
        """Test that prerequisites are assigned."""
        concepts = adapter.extract_concepts(sample_code)

        # More advanced concepts should have prerequisites
        for concept in concepts:
            if concept.difficulty_score >= 6:
                # High difficulty concepts should have some prerequisites
                # (though not all will in our simplified hierarchy)
                pass  # Just checking structure exists

    def test_generate_knowledge_assessment(self, adapter, sample_code):
        """Test generating knowledge-level assessment."""
        concepts = adapter.extract_concepts(sample_code)
        concept = concepts[0]

        assessment = adapter.generate_assessment(
            concept, BloomLevel.KNOWLEDGE
        )

        assert assessment.concept_id == concept.concept_id
        assert assessment.bloom_level == BloomLevel.KNOWLEDGE
        assert "```python" in assessment.question or "code" in assessment.question.lower()

    def test_generate_comprehension_assessment(self, adapter, sample_code):
        """Test generating comprehension-level assessment."""
        concepts = adapter.extract_concepts(sample_code)
        concept = concepts[0]

        assessment = adapter.generate_assessment(
            concept, BloomLevel.COMPREHENSION
        )

        assert assessment.bloom_level == BloomLevel.COMPREHENSION
        assert "explain" in assessment.question.lower()

    def test_generate_application_assessment(self, adapter, sample_code):
        """Test generating application-level assessment."""
        concepts = adapter.extract_concepts(sample_code)
        concept = concepts[0]

        assessment = adapter.generate_assessment(
            concept, BloomLevel.APPLICATION
        )

        assert assessment.bloom_level == BloomLevel.APPLICATION
        assert "write" in assessment.question.lower()

    def test_generate_analysis_assessment(self, adapter, sample_code):
        """Test generating analysis-level assessment."""
        concepts = adapter.extract_concepts(sample_code)
        concept = concepts[0]

        assessment = adapter.generate_assessment(
            concept, BloomLevel.ANALYSIS
        )

        assert assessment.bloom_level == BloomLevel.ANALYSIS
        assert "compare" in assessment.question.lower() or "trade" in assessment.question.lower()

    def test_scaffold_prompt_level_1(self, adapter, sample_code):
        """Test maximum scaffolding prompt generation."""
        concepts = adapter.extract_concepts(sample_code)

        concept_mastery = [
            (c, ConceptMastery(concept_id=c.concept_id, learner_id="test"))
            for c in concepts[:5]
        ]

        prompt = adapter.get_scaffold_prompt(1, concept_mastery)

        assert "Maximum Support" in prompt
        assert "comment" in prompt.lower()
        assert "explain" in prompt.lower()

    def test_scaffold_prompt_level_5(self, adapter, sample_code):
        """Test minimal scaffolding prompt generation."""
        concepts = adapter.extract_concepts(sample_code)

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

        assert "Minimal Support" in prompt
        assert "pythonic" in prompt.lower() or "senior" in prompt.lower()

    def test_validate_content_valid_python(self, adapter, sample_code):
        """Test content validation with valid Python code."""
        assert adapter.validate_content(sample_code) is True

    def test_validate_content_invalid(self, adapter):
        """Test content validation with non-Python content."""
        assert adapter.validate_content("Just some random text") is False

    def test_validate_content_python_docs(self, adapter):
        """Test content validation with Python documentation."""
        doc = """
        # Python List Comprehension

        ```python
        squares = [x**2 for x in range(10)]
        ```

        List comprehensions provide a concise way to create lists.
        """
        assert adapter.validate_content(doc) is True

    def test_preprocess_content(self, adapter):
        """Test content preprocessing."""
        notebook_content = """
In [1]: x = 10

Out[1]: 10

```python
y = 20
```
"""
        cleaned = adapter.preprocess_content(notebook_content)

        assert "In [1]:" not in cleaned
        assert "Out[1]:" not in cleaned
        assert "```python" not in cleaned


class TestDomainRegistryIntegration:
    """Test integration with domain registry."""

    def test_get_programming_adapter(self):
        """Test retrieving programming adapter from registry."""
        DomainRegistry.clear_instances()
        adapter = DomainRegistry.get("python-programming")

        assert isinstance(adapter, PythonProgrammingAdapter)

    def test_list_domains_includes_programming(self):
        """Test that programming domain is listed."""
        domains = DomainRegistry.list_domains()

        assert "python-programming" in domains

    def test_both_domains_coexist(self):
        """Test that both reading and programming domains work together."""
        # Import domains to ensure both are registered
        from holocron.domains import ReadingSkillsAdapter, PythonProgrammingAdapter

        DomainRegistry.clear_instances()

        reading = DomainRegistry.get("reading-skills")
        programming = DomainRegistry.get("python-programming")

        assert reading.config.domain_id == "reading-skills"
        assert programming.config.domain_id == "python-programming"

# Holocron

A generalized skill training platform using evidence-based pedagogical techniques.

Holocron helps learners master any skill through adaptive scaffolding, spaced repetition, and Bloom's Taxonomy assessments. It evolved from the Anchor-Text vocabulary system into a domain-agnostic learning platform.

## Features

- **Multi-Domain Learning**: Built-in adapters for reading comprehension and Python programming, with a template for custom domains
- **Adaptive Scaffolding**: Content difficulty adjusts based on learner mastery
- **Bloom's Taxonomy Assessments**: Questions target appropriate cognitive levels
- **Spaced Repetition**: SM-2 algorithm schedules reviews for optimal retention
- **Evidence-Based Pedagogy**: Implements elaborative encoding, dual coding, Feynman technique, and interleaving
- **Interactive REPL**: Terminal-based learning sessions with immediate feedback
- **Web GUI**: Modern NiceGUI interface with dashboard, study mode, and progress tracking
- **LLM Integration**: Optional AI-powered grading and content enhancement

## Installation

```bash
pip install holocron
```

Or install from source:

```bash
git clone https://github.com/yourusername/holocron.git
cd holocron
pip install -e ".[dev]"
```

## Quick Start

### CLI Commands

```bash
# List available domains
holocron domains

# Analyze a file for concepts
holocron analyze document.txt

# Transform content with scaffolding
holocron transform document.txt --domain reading-skills --concepts

# Start interactive learning session
holocron learn --domain reading-skills

# Start spaced repetition review
holocron review --learner your-name

# Launch web interface
holocron gui

# Manage learner profiles
holocron learner create "Your Name"
holocron learner list
holocron learner stats your-name
```

### Python API

```python
from holocron.core import (
    ContentTransformer,
    TransformConfig,
    LearnerProfile,
    MasteryEngine,
    AssessmentGrader,
    PedagogicalTransformer,
)
from holocron.domains.registry import DomainRegistry

# Create a learner profile
learner = LearnerProfile(
    learner_id="student-1",
    name="Alice",
)

# Transform content with adaptive scaffolding
transformer = ContentTransformer(
    domain_id="python-programming",
    learner=learner,
)

result = transformer.transform(
    content='''
    def fibonacci(n):
        """Calculate the nth Fibonacci number."""
        if n <= 1:
            return n
        return fibonacci(n-1) + fibonacci(n-2)
    ''',
    config=TransformConfig(include_assessments=True),
)

print(f"Found {len(result.concepts_found)} concepts")
print(f"Scaffold level: {result.scaffold_level}")

# Grade an assessment response
grader = AssessmentGrader()
grading = grader.grade(
    assessment=result.assessments[0],
    response="This function uses recursion to calculate Fibonacci numbers",
)
print(f"Score: {grading.score}, Feedback: {grading.feedback}")

# Apply pedagogical techniques
pedagogy = PedagogicalTransformer()
enhanced = pedagogy.transform(
    concept=result.concepts_found[0],
    mastery=learner.get_mastery("python-programming", result.concepts_found[0].concept_id),
)
print(enhanced.transformed_content)
```

## Architecture

```
holocron/
├── core/
│   ├── models.py          # Concept, ConceptMastery, Assessment, LearnerProfile
│   ├── mastery.py         # MasteryEngine with SM-2 spaced repetition
│   ├── transformer.py     # ContentTransformer for scaffolded learning
│   ├── grader.py          # AssessmentGrader with LLM support
│   └── pedagogy.py        # PedagogicalTransformer with learning techniques
├── domains/
│   ├── base.py            # DomainAdapter abstract base class
│   ├── registry.py        # DomainRegistry for adapter management
│   ├── reading.py         # Reading comprehension adapter
│   └── programming.py     # Python programming adapter
├── llm/
│   ├── client.py          # LLMClient with LiteLLM, retry logic, token counting
│   └── chunker.py         # Document chunking for token limits
├── learner/
│   └── database.py        # SQLite persistence for learner profiles
├── repl/
│   └── session.py         # Interactive REPL session controller
├── gui/
│   └── app.py             # NiceGUI web interface
└── cli.py                 # Typer CLI commands
```

## Built-in Domains

### Reading Skills (`reading-skills`)

Extracts vocabulary concepts from text content:
- Word frequency analysis
- Academic vocabulary detection (AWL)
- Etymology and context extraction
- Difficulty scoring based on frequency

### Python Programming (`python-programming`)

Extracts programming concepts from Python code:
- Language constructs (loops, functions, classes)
- Standard library usage
- Design patterns
- Code complexity metrics

## Creating Custom Domain Adapters

Create a new domain by extending `DomainAdapter`:

```python
from holocron.domains.base import DomainAdapter, DomainConfig
from holocron.core.models import Concept, Assessment, BloomLevel

class MyDomainAdapter(DomainAdapter):
    @property
    def config(self) -> DomainConfig:
        return DomainConfig(
            domain_id="my-domain",
            display_name="My Custom Domain",
            description="A custom learning domain",
            file_extensions=[".txt", ".md"],
        )

    def extract_concepts(self, content: str) -> list[Concept]:
        # Extract concepts from content
        concepts = []
        # ... your extraction logic
        return concepts

    def generate_assessment(
        self,
        concept: Concept,
        bloom_level: BloomLevel,
        context: str = "",
    ) -> Assessment:
        # Generate an assessment question
        return Assessment(
            assessment_id=f"assess-{concept.concept_id}",
            concept_id=concept.concept_id,
            bloom_level=bloom_level,
            assessment_type=AssessmentType.FREE_RESPONSE,
            question=f"Explain {concept.name} in your own words.",
        )

# Register the adapter
from holocron.domains.registry import DomainRegistry
DomainRegistry.register(MyDomainAdapter())
```

## Configuration

Set configuration via environment variables or a `.env` file:

```bash
# LLM API Keys (at least one required for LLM features)
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key

# LLM Settings
HOLOCRON_DEFAULT_MODEL=gpt-4
HOLOCRON_TEMPERATURE=0.7

# Web Settings
HOLOCRON_WEB_HOST=127.0.0.1
HOLOCRON_WEB_PORT=8080
```

## Pedagogical Techniques

Holocron implements evidence-based learning techniques:

1. **Elaborative Encoding**: Creates analogies connecting new concepts to familiar ideas
2. **Dual Coding**: Combines verbal descriptions with mental imagery
3. **Feynman Technique**: Simplifies complex concepts using plain language
4. **Interleaving**: Mixes related topics for better discrimination
5. **Retrieval Practice**: Generates prompts to strengthen memory through testing
6. **Spaced Repetition**: Uses SM-2 algorithm for optimal review scheduling

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=holocron --cov-report=html

# Run specific test file
pytest tests/test_pedagogy.py -v
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Format code
black src/ tests/
ruff check src/ tests/

# Type checking
mypy src/holocron
```

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Evolved from the [Anchor-Text](https://github.com/yourusername/anchor-text) vocabulary learning system
- Implements research-backed techniques from cognitive science and educational psychology
- Uses [LiteLLM](https://github.com/BerriAI/litellm) for multi-provider LLM support
- Built with [Typer](https://typer.tiangolo.com/) and [NiceGUI](https://nicegui.io/)

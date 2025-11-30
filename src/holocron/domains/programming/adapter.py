"""Programming Domain Adapter for Holocron.

This adapter provides skill training for programming concepts,
starting with Python. It extracts programming concepts from code
and documentation, generates Bloom's Taxonomy assessments, and
provides scaffolded learning support.

The programming domain treats language constructs, patterns, and
idioms as concepts, with:
- Recognition = can identify the concept in code
- Comprehension = can explain what the code does
- Application = can write code using the concept
"""

import ast
import re
import uuid
from collections import defaultdict
from typing import Any

from holocron.core.models import (
    Assessment,
    AssessmentOption,
    AssessmentType,
    BloomLevel,
    Concept,
    ConceptMastery,
)
from holocron.domains.base import DomainAdapter, DomainConfig
from holocron.domains.registry import DomainRegistry


# Python concept categories and their relationships
PYTHON_CONCEPT_HIERARCHY = {
    "basics": {
        "parent": None,
        "concepts": ["variables", "data_types", "operators", "expressions"],
    },
    "control_flow": {
        "parent": "basics",
        "concepts": ["conditionals", "loops", "match_case"],
    },
    "data_structures": {
        "parent": "basics",
        "concepts": ["lists", "tuples", "dictionaries", "sets", "strings"],
    },
    "functions": {
        "parent": "control_flow",
        "concepts": [
            "function_definition",
            "parameters",
            "return_values",
            "default_arguments",
            "keyword_arguments",
            "args_kwargs",
            "lambda",
            "closures",
            "decorators",
        ],
    },
    "comprehensions": {
        "parent": "data_structures",
        "concepts": [
            "list_comprehension",
            "dict_comprehension",
            "set_comprehension",
            "generator_expression",
        ],
    },
    "oop": {
        "parent": "functions",
        "concepts": [
            "classes",
            "inheritance",
            "polymorphism",
            "encapsulation",
            "magic_methods",
            "properties",
            "class_methods",
            "static_methods",
            "dataclasses",
        ],
    },
    "error_handling": {
        "parent": "control_flow",
        "concepts": [
            "try_except",
            "raise",
            "custom_exceptions",
            "context_managers",
        ],
    },
    "modules": {
        "parent": "functions",
        "concepts": ["import", "packages", "namespaces", "__init__"],
    },
    "iterators": {
        "parent": "comprehensions",
        "concepts": ["iterators", "generators", "yield", "itertools"],
    },
    "async": {
        "parent": "iterators",
        "concepts": ["async_await", "coroutines", "asyncio", "tasks"],
    },
    "typing": {
        "parent": "functions",
        "concepts": ["type_hints", "generics", "protocols", "typing_module"],
    },
}

# Difficulty scores for concepts (1-10)
CONCEPT_DIFFICULTY = {
    "variables": 1,
    "data_types": 2,
    "operators": 2,
    "expressions": 2,
    "conditionals": 2,
    "loops": 3,
    "lists": 2,
    "tuples": 3,
    "dictionaries": 3,
    "sets": 4,
    "strings": 2,
    "function_definition": 3,
    "parameters": 3,
    "return_values": 3,
    "default_arguments": 4,
    "keyword_arguments": 4,
    "args_kwargs": 5,
    "lambda": 5,
    "closures": 7,
    "decorators": 7,
    "list_comprehension": 5,
    "dict_comprehension": 6,
    "set_comprehension": 6,
    "generator_expression": 6,
    "classes": 5,
    "inheritance": 6,
    "polymorphism": 7,
    "encapsulation": 6,
    "magic_methods": 7,
    "properties": 6,
    "class_methods": 6,
    "static_methods": 5,
    "dataclasses": 5,
    "try_except": 4,
    "raise": 4,
    "custom_exceptions": 5,
    "context_managers": 7,
    "import": 2,
    "packages": 4,
    "namespaces": 5,
    "iterators": 6,
    "generators": 7,
    "yield": 7,
    "itertools": 7,
    "async_await": 8,
    "coroutines": 8,
    "asyncio": 9,
    "tasks": 9,
    "type_hints": 4,
    "generics": 7,
    "protocols": 8,
    "typing_module": 6,
    "match_case": 5,
}


@DomainRegistry.register("python-programming")
class PythonProgrammingAdapter(DomainAdapter):
    """Domain adapter for Python programming skill training.

    Extracts programming concepts from Python code and documentation,
    generates assessments at various Bloom's Taxonomy levels, and
    provides scaffolded learning support.
    """

    def __init__(self) -> None:
        self._config = DomainConfig(
            domain_id="python-programming",
            display_name="Python Programming",
            description="Python programming concepts, patterns, and best practices",
            concept_extractors=["ast", "pattern", "docstring"],
            mastery_model="hybrid",
            initial_mastery=0.0,
            mastery_decay_rate=0.03,  # Slower decay for programming skills
            scaffold_levels=5,
            bloom_levels=[
                "knowledge",
                "comprehension",
                "application",
                "analysis",
                "synthesis",
            ],
            pedagogical_techniques=[
                "elaborative-encoding",
                "dual-coding",
                "feynman-technique",
                "interleaving",
                "retrieval-practice",
                "worked-examples",
            ],
            file_extensions=[".py", ".pyw", ".pyi", ".ipynb"],
        )

    @property
    def config(self) -> DomainConfig:
        """Return the Python programming domain configuration."""
        return self._config

    def extract_concepts(self, content: str) -> list[Concept]:
        """Extract programming concepts from Python code or documentation.

        Uses AST analysis for code and pattern matching for documentation.

        Args:
            content: Python code or documentation text

        Returns:
            List of Concept objects for identified programming concepts
        """
        concepts: dict[str, Concept] = {}

        # Try AST analysis for Python code
        try:
            tree = ast.parse(content)
            self._extract_from_ast(tree, concepts, content)
        except SyntaxError:
            # Not valid Python code, try pattern matching for docs
            pass

        # Also do pattern-based extraction (catches concepts in comments/docs)
        self._extract_from_patterns(content, concepts)

        return list(concepts.values())

    def _extract_from_ast(
        self, tree: ast.AST, concepts: dict[str, Concept], source: str
    ) -> None:
        """Extract concepts from AST nodes."""
        for node in ast.walk(tree):
            concept_info = self._identify_ast_concept(node)
            if concept_info:
                concept_id, name, description = concept_info
                if concept_id not in concepts:
                    concepts[concept_id] = self._create_concept(
                        concept_id, name, description, source, node
                    )
                else:
                    # Increment encounter count
                    concepts[concept_id].domain_data["encounter_count"] += 1

    def _identify_ast_concept(self, node: ast.AST) -> tuple[str, str, str] | None:
        """Identify which concept an AST node represents."""
        if isinstance(node, ast.FunctionDef):
            if any(isinstance(d, ast.Name) for d in node.decorator_list):
                return ("decorators", "Decorators", "Function decorators modify function behavior")
            return ("function_definition", "Function Definition", "Defining functions with def")

        elif isinstance(node, ast.AsyncFunctionDef):
            return ("async_await", "Async/Await", "Asynchronous function definition")

        elif isinstance(node, ast.ClassDef):
            if node.bases:
                return ("inheritance", "Class Inheritance", "Classes inheriting from other classes")
            return ("classes", "Classes", "Defining classes for OOP")

        elif isinstance(node, ast.ListComp):
            return ("list_comprehension", "List Comprehension", "Concise list creation syntax")

        elif isinstance(node, ast.DictComp):
            return ("dict_comprehension", "Dict Comprehension", "Concise dictionary creation")

        elif isinstance(node, ast.SetComp):
            return ("set_comprehension", "Set Comprehension", "Concise set creation")

        elif isinstance(node, ast.GeneratorExp):
            return ("generator_expression", "Generator Expression", "Memory-efficient iteration")

        elif isinstance(node, ast.Lambda):
            return ("lambda", "Lambda Functions", "Anonymous inline functions")

        elif isinstance(node, ast.Try):
            return ("try_except", "Try/Except", "Exception handling blocks")

        elif isinstance(node, ast.Raise):
            return ("raise", "Raise Exceptions", "Raising exceptions explicitly")

        elif isinstance(node, ast.With):
            return ("context_managers", "Context Managers", "Resource management with 'with'")

        elif isinstance(node, ast.AsyncWith):
            return ("async_await", "Async Context Managers", "Async resource management")

        elif isinstance(node, ast.Yield):
            return ("yield", "Yield Statement", "Generator yield expressions")

        elif isinstance(node, ast.YieldFrom):
            return ("generators", "Yield From", "Delegating to subgenerators")

        elif isinstance(node, ast.Match):
            return ("match_case", "Match/Case", "Structural pattern matching")

        elif isinstance(node, ast.For):
            return ("loops", "For Loops", "Iteration over sequences")

        elif isinstance(node, ast.While):
            return ("loops", "While Loops", "Conditional iteration")

        elif isinstance(node, ast.If):
            return ("conditionals", "Conditionals", "If/elif/else statements")

        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            return ("import", "Import Statements", "Importing modules and packages")

        return None

    def _extract_from_patterns(self, content: str, concepts: dict[str, Concept]) -> None:
        """Extract concepts using regex pattern matching."""
        patterns = {
            "list_comprehension": r"\[[^\]]+\s+for\s+\w+\s+in\s+[^\]]+\]",
            "dict_comprehension": r"\{[^}]+:\s*[^}]+\s+for\s+\w+\s+in\s+[^}]+\}",
            "lambda": r"\blambda\s+\w*\s*:",
            "decorators": r"@\w+(\.\w+)*(\([^)]*\))?\s*\n",
            "type_hints": r":\s*(int|str|float|bool|list|dict|tuple|set|None|Any|\w+\[)",
            "f_strings": r'f["\'][^"\']*\{[^}]+\}[^"\']*["\']',
            "args_kwargs": r"\*args|\*\*kwargs",
            "dataclasses": r"@dataclass",
            "properties": r"@property",
            "class_methods": r"@classmethod",
            "static_methods": r"@staticmethod",
            "generators": r"\byield\b",
            "async_await": r"\basync\s+(def|for|with)\b|\bawait\b",
            "context_managers": r"\bwith\s+\w+",
            "try_except": r"\btry\s*:\s*\n|\bexcept\b",
        }

        for concept_key, pattern in patterns.items():
            matches = re.findall(pattern, content, re.MULTILINE)
            if matches:
                if concept_key not in concepts:
                    name = concept_key.replace("_", " ").title()
                    concepts[concept_key] = self._create_concept(
                        concept_key,
                        name,
                        f"Python {name.lower()} concept",
                        content,
                    )
                concepts[concept_key].domain_data["encounter_count"] = len(matches)

    def _create_concept(
        self,
        concept_key: str,
        name: str,
        description: str,
        source: str,
        node: ast.AST | None = None,
    ) -> Concept:
        """Create a Concept object for a programming concept."""
        # Find prerequisites from hierarchy
        prerequisites = []
        for category, info in PYTHON_CONCEPT_HIERARCHY.items():
            if concept_key in info["concepts"]:
                if info["parent"]:
                    # Add concepts from parent category as prerequisites
                    parent_info = PYTHON_CONCEPT_HIERARCHY.get(info["parent"], {})
                    prerequisites.extend(
                        [f"python.{c}" for c in parent_info.get("concepts", [])[:2]]
                    )
                break

        # Get difficulty
        difficulty = CONCEPT_DIFFICULTY.get(concept_key, 5)

        # Extract example from source
        example = self._extract_example(concept_key, source, node)

        return Concept(
            concept_id=f"python.{concept_key}",
            domain_id=self._config.domain_id,
            name=name,
            description=description,
            prerequisites=prerequisites,
            difficulty_score=difficulty,
            bloom_level=BloomLevel.KNOWLEDGE,
            tags=["python", "programming", self._get_category(concept_key)],
            examples=[example] if example else [],
            domain_data={
                "language": "python",
                "concept_key": concept_key,
                "encounter_count": 1,
                "category": self._get_category(concept_key),
            },
        )

    def _get_category(self, concept_key: str) -> str:
        """Get the category for a concept."""
        for category, info in PYTHON_CONCEPT_HIERARCHY.items():
            if concept_key in info["concepts"]:
                return category
        return "other"

    def _extract_example(
        self, concept_key: str, source: str, node: ast.AST | None
    ) -> str:
        """Extract a code example for the concept."""
        if node and hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            lines = source.split("\n")
            start = max(0, node.lineno - 1)
            end = min(len(lines), node.end_lineno if node.end_lineno else start + 1)
            return "\n".join(lines[start:end])
        return ""

    def generate_assessment(
        self,
        concept: Concept,
        bloom_level: BloomLevel,
        context: str = "",
    ) -> Assessment:
        """Generate a programming assessment at the specified Bloom level.

        Args:
            concept: The programming concept to assess
            bloom_level: The cognitive level to test
            context: Optional code context

        Returns:
            Assessment object for the programming concept
        """
        concept_key = concept.domain_data.get("concept_key", concept.name.lower())

        if bloom_level == BloomLevel.KNOWLEDGE:
            return self._generate_recognition_assessment(concept, concept_key, context)
        elif bloom_level == BloomLevel.COMPREHENSION:
            return self._generate_comprehension_assessment(concept, concept_key, context)
        elif bloom_level == BloomLevel.APPLICATION:
            return self._generate_application_assessment(concept, concept_key, context)
        elif bloom_level == BloomLevel.ANALYSIS:
            return self._generate_analysis_assessment(concept, concept_key, context)
        else:  # SYNTHESIS or EVALUATION
            return self._generate_synthesis_assessment(concept, concept_key, context)

    def _generate_recognition_assessment(
        self, concept: Concept, concept_key: str, context: str
    ) -> Assessment:
        """Generate a code recognition assessment."""
        code_example = self._get_code_example(concept_key)

        return Assessment(
            assessment_id=f"assess-{uuid.uuid4().hex[:8]}",
            concept_id=concept.concept_id,
            bloom_level=BloomLevel.KNOWLEDGE,
            assessment_type=AssessmentType.MULTIPLE_CHOICE,
            question=f"Which Python concept is demonstrated in this code?\n\n```python\n{code_example}\n```",
            context=context,
            options=[
                AssessmentOption(text=concept.name, is_correct=True),
                AssessmentOption(text="[Alternative concept 1]", is_correct=False),
                AssessmentOption(text="[Alternative concept 2]", is_correct=False),
                AssessmentOption(text="[Alternative concept 3]", is_correct=False),
            ],
            rubric="Identify the primary Python concept being demonstrated.",
            difficulty=concept.difficulty_score,
            hints=[
                f"Look for {concept.name.lower()} syntax patterns",
                "Consider the structure of the code",
            ],
        )

    def _generate_comprehension_assessment(
        self, concept: Concept, concept_key: str, context: str
    ) -> Assessment:
        """Generate a code comprehension assessment."""
        code_example = self._get_code_example(concept_key)

        return Assessment(
            assessment_id=f"assess-{uuid.uuid4().hex[:8]}",
            concept_id=concept.concept_id,
            bloom_level=BloomLevel.COMPREHENSION,
            assessment_type=AssessmentType.FREE_RESPONSE,
            question=f"Explain what this code does and why {concept.name.lower()} is useful here:\n\n```python\n{code_example}\n```",
            context=context,
            rubric="""
Excellent (90-100%): Clear explanation of functionality, identifies concept benefits, mentions relevant details
Good (70-89%): Adequate explanation, understands main purpose, some details missing
Partial (50-69%): Basic understanding shown, explanation incomplete
Insufficient (0-49%): Misunderstands code functionality or concept purpose
""",
            sample_answer=f"This code uses {concept.name.lower()} to...",
            difficulty=concept.difficulty_score,
            hints=[
                "Start by describing what the code produces",
                f"Think about why you'd use {concept.name.lower()} instead of alternatives",
            ],
        )

    def _generate_application_assessment(
        self, concept: Concept, concept_key: str, context: str
    ) -> Assessment:
        """Generate a coding exercise assessment."""
        task = self._get_coding_task(concept_key)

        return Assessment(
            assessment_id=f"assess-{uuid.uuid4().hex[:8]}",
            concept_id=concept.concept_id,
            bloom_level=BloomLevel.APPLICATION,
            assessment_type=AssessmentType.CODE_EXERCISE,
            question=f"Write Python code that uses {concept.name.lower()} to:\n\n{task}",
            context=context,
            rubric="""
Excellent (90-100%): Correct syntax, efficient solution, follows Python conventions
Good (70-89%): Works correctly, minor style issues
Partial (50-69%): Partially correct, some syntax errors or logic issues
Insufficient (0-49%): Does not demonstrate understanding of the concept
""",
            sample_answer=f"# Example solution using {concept.name.lower()}\n...",
            difficulty=concept.difficulty_score + 1,
            hints=[
                f"Remember the basic syntax for {concept.name.lower()}",
                "Test your code mentally with sample inputs",
            ],
        )

    def _generate_analysis_assessment(
        self, concept: Concept, concept_key: str, context: str
    ) -> Assessment:
        """Generate a code analysis assessment."""
        return Assessment(
            assessment_id=f"assess-{uuid.uuid4().hex[:8]}",
            concept_id=concept.concept_id,
            bloom_level=BloomLevel.ANALYSIS,
            assessment_type=AssessmentType.FREE_RESPONSE,
            question=f"Compare using {concept.name.lower()} versus an alternative approach. When would you choose one over the other? Discuss trade-offs.",
            context=context,
            rubric="""
Excellent (90-100%): Thorough comparison, identifies specific use cases, discusses performance/readability trade-offs
Good (70-89%): Good comparison with some trade-offs mentioned
Partial (50-69%): Basic comparison, limited analysis of trade-offs
Insufficient (0-49%): No meaningful comparison or analysis
""",
            difficulty=concept.difficulty_score + 2,
            hints=[
                "Consider readability, performance, and maintainability",
                "Think about real-world scenarios",
            ],
        )

    def _generate_synthesis_assessment(
        self, concept: Concept, concept_key: str, context: str
    ) -> Assessment:
        """Generate a creative coding assessment."""
        return Assessment(
            assessment_id=f"assess-{uuid.uuid4().hex[:8]}",
            concept_id=concept.concept_id,
            bloom_level=BloomLevel.SYNTHESIS,
            assessment_type=AssessmentType.CODE_EXERCISE,
            question=f"Design and implement a small utility or function that creatively uses {concept.name.lower()} to solve a problem of your choosing. Explain your design decisions.",
            context=context,
            rubric="""
Excellent (90-100%): Creative solution, well-designed, excellent use of concept, clear explanation
Good (70-89%): Good solution, appropriate use of concept, adequate explanation
Partial (50-69%): Basic solution, concept used but not optimally
Insufficient (0-49%): Does not effectively use the concept
""",
            difficulty=concept.difficulty_score + 3,
            hints=[
                "Think of a practical problem you've encountered",
                f"Consider how {concept.name.lower()} can make the solution elegant",
            ],
        )

    def _get_code_example(self, concept_key: str) -> str:
        """Get a representative code example for a concept."""
        examples = {
            "list_comprehension": "squares = [x**2 for x in range(10) if x % 2 == 0]",
            "dict_comprehension": "word_lengths = {word: len(word) for word in words}",
            "lambda": "sorted_items = sorted(items, key=lambda x: x.value)",
            "decorators": "@timer\ndef slow_function():\n    time.sleep(1)",
            "generators": "def countdown(n):\n    while n > 0:\n        yield n\n        n -= 1",
            "context_managers": "with open('file.txt') as f:\n    content = f.read()",
            "classes": "class Dog:\n    def __init__(self, name):\n        self.name = name",
            "inheritance": "class Labrador(Dog):\n    def fetch(self):\n        return 'ball'",
            "try_except": "try:\n    result = risky_operation()\nexcept ValueError as e:\n    handle_error(e)",
            "async_await": "async def fetch_data():\n    result = await api_call()\n    return result",
        }
        return examples.get(concept_key, f"# Example of {concept_key}\n...")

    def _get_coding_task(self, concept_key: str) -> str:
        """Get a coding task description for a concept."""
        tasks = {
            "list_comprehension": "Create a list of all even numbers from 1 to 100, squared.",
            "dict_comprehension": "Create a dictionary mapping numbers 1-10 to their cubes.",
            "lambda": "Sort a list of tuples by their second element using a lambda.",
            "decorators": "Write a decorator that logs function calls with their arguments.",
            "generators": "Write a generator that yields Fibonacci numbers indefinitely.",
            "context_managers": "Create a context manager that times code execution.",
            "classes": "Create a BankAccount class with deposit and withdraw methods.",
            "inheritance": "Extend the BankAccount class to create a SavingsAccount with interest.",
            "try_except": "Write a function that safely converts strings to integers with error handling.",
            "async_await": "Write an async function that fetches data from multiple URLs concurrently.",
        }
        return tasks.get(concept_key, f"Demonstrate your understanding of {concept_key}.")

    def get_scaffold_prompt(
        self,
        level: int,
        concepts: list[tuple[Concept, ConceptMastery]],
    ) -> str:
        """Generate system prompt for programming content transformation.

        Creates scaffolded learning support based on concept mastery levels.

        Args:
            level: Overall scaffold level (1=max support, 5=min support)
            concepts: List of (concept, mastery) tuples

        Returns:
            System prompt for LLM content transformation
        """
        # Categorize concepts by mastery
        low_mastery = []
        medium_mastery = []

        for concept, mastery in concepts:
            name = concept.name
            if mastery.overall_mastery < 40:
                low_mastery.append(name)
            elif mastery.overall_mastery < 70:
                medium_mastery.append(name)

        base_prompt = """You are a Python programming tutor helping a learner understand code.
Transform the provided code according to the learner's needs while preserving functionality."""

        if level == 1:
            return f"""{base_prompt}

SCAFFOLDING LEVEL: Maximum Support

For this learner, provide maximum code support:
1. Add detailed inline comments explaining every significant line
2. Break complex expressions into simpler, intermediate steps
3. Add docstrings explaining function purpose, parameters, and return values
4. Include type hints for all variables and functions
5. Add print statements or comments showing expected values at each step
6. Explain any Python idioms or patterns used

Concepts needing explanation: {', '.join(low_mastery[:10]) if low_mastery else 'general Python concepts'}

Format: Heavily annotated code with explanations."""

        elif level == 2:
            return f"""{base_prompt}

SCAFFOLDING LEVEL: High Support

For this learner:
1. Add comments for complex or non-obvious code sections
2. Include docstrings for functions and classes
3. Add type hints where helpful
4. Explain Python-specific idioms

Focus on explaining: {', '.join(low_mastery[:8]) if low_mastery else 'intermediate concepts'}

Format: Well-commented code with key explanations."""

        elif level == 3:
            return f"""{base_prompt}

SCAFFOLDING LEVEL: Moderate Support

For this learner:
1. Add docstrings for public functions and classes
2. Comment only complex algorithms or non-obvious logic
3. Use clear variable names that serve as documentation

Concepts that may need clarification: {', '.join(low_mastery[:5]) if low_mastery else 'none identified'}

Format: Clean code with strategic comments."""

        elif level == 4:
            return f"""{base_prompt}

SCAFFOLDING LEVEL: Light Support

For this learner:
1. Ensure docstrings exist for public API
2. Comment only truly complex sections
3. Code should be largely self-documenting

Optional explanations for: {', '.join(low_mastery[:3]) if low_mastery else 'none needed'}

Format: Production-quality code with minimal comments."""

        else:  # level == 5
            return f"""{base_prompt}

SCAFFOLDING LEVEL: Minimal Support

This learner has strong Python skills.
1. Present code as a senior developer would write it
2. Use Pythonic idioms and patterns
3. Comments only for non-obvious design decisions

Format: Clean, idiomatic Python code."""

    def validate_content(self, content: str) -> bool:
        """Validate that content is suitable for Python skill training.

        Args:
            content: The content to validate

        Returns:
            True if content appears to be Python code or documentation
        """
        # Check minimum length
        if len(content.strip()) < 20:
            return False

        # Try to parse as Python
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            pass

        # Check for Python-like patterns in documentation
        python_patterns = [
            r"\bdef\s+\w+\s*\(",
            r"\bclass\s+\w+",
            r"\bimport\s+\w+",
            r"\bpython\b",
            r"```python",
        ]

        for pattern in python_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False

    def preprocess_content(self, content: str) -> str:
        """Preprocess Python content before concept extraction.

        Args:
            content: Raw Python code or documentation

        Returns:
            Cleaned content
        """
        # Remove common notebook artifacts
        content = re.sub(r"In\s*\[\d+\]:\s*", "", content)
        content = re.sub(r"Out\s*\[\d+\]:\s*", "", content)

        # Remove markdown code fence markers if present
        content = re.sub(r"```python\s*\n?", "", content)
        content = re.sub(r"```\s*\n?", "", content)

        return content.strip()

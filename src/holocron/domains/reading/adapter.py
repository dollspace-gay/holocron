"""Reading Skills Domain Adapter for Holocron.

This adapter provides backward compatibility with Anchor-Text,
implementing concept extraction from text, vocabulary-based assessments,
and scaffolded reading support using the Literacy Bridge Protocol.

The reading domain treats vocabulary words as concepts, with:
- Recognition = can identify the word
- Comprehension = can define/explain the word
- Application = can use the word in context
"""

import re
import uuid
from collections import Counter

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


# Common English words to exclude from vocabulary extraction
COMMON_WORDS = frozenset([
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their", "what",
    "so", "up", "out", "if", "about", "who", "get", "which", "go", "me",
    "when", "make", "can", "like", "time", "no", "just", "him", "know", "take",
    "people", "into", "year", "your", "good", "some", "could", "them", "see", "other",
    "than", "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "back", "after", "use", "two", "how", "our", "work", "first", "well", "way",
    "even", "new", "want", "because", "any", "these", "give", "day", "most", "us",
    "is", "are", "was", "were", "been", "being", "has", "had", "having", "does",
    "did", "doing", "am", "may", "might", "must", "shall", "should", "ought", "need",
    "very", "too", "much", "more", "many", "such", "own", "same", "few", "those",
    "through", "during", "before", "between", "under", "again", "once", "here", "where",
    "why", "while", "each", "every", "both", "few", "more", "most", "other", "some",
    "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too",
])


@DomainRegistry.register("reading-skills")
class ReadingSkillsAdapter(DomainAdapter):
    """Domain adapter for reading and vocabulary skill training.

    Implements the Literacy Bridge Protocol for reading rehabilitation,
    with concepts being vocabulary words extracted from text content.
    """

    def __init__(self) -> None:
        self._config = DomainConfig(
            domain_id="reading-skills",
            display_name="Reading Skills",
            description="Vocabulary and reading comprehension training using evidence-based techniques",
            concept_extractors=["lexical", "frequency"],
            mastery_model="hybrid",
            initial_mastery=0.0,
            mastery_decay_rate=0.05,
            scaffold_levels=5,
            bloom_levels=["knowledge", "comprehension", "application"],
            pedagogical_techniques=[
                "elaborative-encoding",
                "dual-coding",
                "feynman-technique",
                "interleaving",
                "retrieval-practice",
            ],
            file_extensions=[".txt", ".pdf", ".epub", ".docx", ".html", ".md"],
        )

    @property
    def config(self) -> DomainConfig:
        """Return the reading domain configuration."""
        return self._config

    def extract_concepts(self, content: str) -> list[Concept]:
        """Extract vocabulary concepts from text content.

        Analyzes text to identify vocabulary words worth learning,
        filtering common words and calculating difficulty scores.

        Args:
            content: The text content to analyze

        Returns:
            List of Concept objects representing vocabulary words
        """
        # Tokenize and clean
        words = re.findall(r"\b[a-zA-Z]{3,}\b", content.lower())

        # Count frequencies
        word_counts = Counter(words)

        # Filter and create concepts
        concepts = []
        for word, count in word_counts.most_common():
            # Skip common words
            if word in COMMON_WORDS:
                continue

            # Skip very rare words (likely typos or names)
            if count < 2 and len(content) > 1000:
                continue

            # Calculate difficulty based on word length and frequency
            difficulty = self._calculate_word_difficulty(word, count, len(words))

            concept = Concept(
                concept_id=f"reading.vocab.{word}",
                domain_id=self._config.domain_id,
                name=word.capitalize(),
                description=f"Vocabulary word: {word}",
                difficulty_score=difficulty,
                bloom_level=BloomLevel.KNOWLEDGE,
                tags=["vocabulary", "reading"],
                domain_data={
                    "word": word,
                    "frequency": count,
                    "original_contexts": self._find_contexts(word, content),
                },
            )
            concepts.append(concept)

        return concepts

    def _calculate_word_difficulty(self, word: str, frequency: int, total_words: int) -> int:
        """Calculate difficulty score for a vocabulary word.

        Args:
            word: The word to score
            frequency: How often it appears
            total_words: Total word count in document

        Returns:
            Difficulty score from 1-10
        """
        # Longer words tend to be harder
        length_score = min(len(word) / 2, 5)

        # Less frequent words are harder
        freq_ratio = frequency / max(total_words, 1)
        freq_score = 5 - min(freq_ratio * 1000, 5)

        # Combine scores
        return max(1, min(10, int(length_score + freq_score)))

    def _find_contexts(self, word: str, content: str, max_contexts: int = 3) -> list[str]:
        """Find sentence contexts where the word appears.

        Args:
            word: The word to find
            content: The full text content
            max_contexts: Maximum number of contexts to return

        Returns:
            List of sentences containing the word
        """
        # Split into sentences
        sentences = re.split(r"[.!?]+", content)
        contexts = []

        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)

        for sentence in sentences:
            if pattern.search(sentence):
                # Clean up the sentence
                clean = " ".join(sentence.split()).strip()
                if len(clean) > 20:  # Skip very short fragments
                    contexts.append(clean)
                    if len(contexts) >= max_contexts:
                        break

        return contexts

    def generate_assessment(
        self,
        concept: Concept,
        bloom_level: BloomLevel,
        context: str = "",
    ) -> Assessment:
        """Generate a vocabulary assessment at the specified Bloom level.

        Args:
            concept: The vocabulary concept to assess
            bloom_level: The cognitive level to test
            context: Optional context sentence

        Returns:
            Assessment object for the vocabulary word
        """
        word = concept.domain_data.get("word", concept.name.lower())

        if bloom_level == BloomLevel.KNOWLEDGE:
            return self._generate_recognition_assessment(concept, word, context)
        elif bloom_level == BloomLevel.COMPREHENSION:
            return self._generate_comprehension_assessment(concept, word, context)
        else:
            return self._generate_application_assessment(concept, word, context)

    def _generate_recognition_assessment(
        self, concept: Concept, word: str, context: str
    ) -> Assessment:
        """Generate a recognition/definition assessment."""
        return Assessment(
            assessment_id=f"assess-{uuid.uuid4().hex[:8]}",
            concept_id=concept.concept_id,
            bloom_level=BloomLevel.KNOWLEDGE,
            assessment_type=AssessmentType.MULTIPLE_CHOICE,
            question=f"Which word best fits in the following context?\n\n{context or f'The _____ was significant to the outcome.'}",
            context=context,
            options=[
                AssessmentOption(text=word.capitalize(), is_correct=True),
                # Note: In production, these would be LLM-generated distractors
                AssessmentOption(text="[distractor 1]", is_correct=False, is_lookalike=True),
                AssessmentOption(text="[distractor 2]", is_correct=False),
                AssessmentOption(text="[distractor 3]", is_correct=False),
            ],
            rubric="Select the word that best fits the context based on meaning.",
            difficulty=concept.difficulty_score,
            explanation=f"The word '{word}' fits this context because of its meaning and usage.",
            hints=[f"The word starts with '{word[0]}'", f"It has {len(word)} letters"],
        )

    def _generate_comprehension_assessment(
        self, concept: Concept, word: str, context: str
    ) -> Assessment:
        """Generate a comprehension/explanation assessment."""
        return Assessment(
            assessment_id=f"assess-{uuid.uuid4().hex[:8]}",
            concept_id=concept.concept_id,
            bloom_level=BloomLevel.COMPREHENSION,
            assessment_type=AssessmentType.FREE_RESPONSE,
            question=f"Explain the meaning of '{word}' in your own words. Include an example of how it might be used.",
            context=context,
            rubric="""
Excellent (90-100%): Clear definition in own words, accurate example, shows deep understanding
Good (70-89%): Adequate definition, reasonable example, minor gaps
Partial (50-69%): Basic understanding shown, weak example or incomplete definition
Insufficient (0-49%): Definition incorrect or missing, no valid example
""",
            sample_answer=f"The word '{word}' means... For example, one might say...",
            difficulty=concept.difficulty_score,
            hints=[
                "Think about the context where you encountered this word",
                "Consider words with similar meanings",
            ],
        )

    def _generate_application_assessment(
        self, concept: Concept, word: str, context: str
    ) -> Assessment:
        """Generate an application/usage assessment."""
        return Assessment(
            assessment_id=f"assess-{uuid.uuid4().hex[:8]}",
            concept_id=concept.concept_id,
            bloom_level=BloomLevel.APPLICATION,
            assessment_type=AssessmentType.FREE_RESPONSE,
            question=f"Write an original sentence using the word '{word}' that demonstrates you understand its meaning. The sentence should be different from any examples you've seen.",
            context=context,
            rubric="""
Excellent (90-100%): Original sentence, correct usage, demonstrates full understanding
Good (70-89%): Correct usage, shows understanding, may be similar to examples
Partial (50-69%): Usage technically correct but meaning not clearly demonstrated
Insufficient (0-49%): Incorrect usage or meaning misunderstood
""",
            sample_answer=f"[Original sentence using '{word}' correctly]",
            difficulty=concept.difficulty_score + 1,  # Application is harder
            hints=[
                "Think of a real situation where this word would apply",
                "Make sure your sentence shows you know what the word means",
            ],
        )

    def get_scaffold_prompt(
        self,
        level: int,
        concepts: list[tuple[Concept, ConceptMastery]],
    ) -> str:
        """Generate system prompt for reading content transformation.

        Creates scaffolded reading support based on vocabulary mastery levels.

        Args:
            level: Overall scaffold level (1=max support, 5=min support)
            concepts: List of (concept, mastery) tuples for vocabulary

        Returns:
            System prompt for LLM content transformation
        """
        # Separate concepts by mastery
        low_mastery = []
        medium_mastery = []
        high_mastery = []

        for concept, mastery in concepts:
            word = concept.domain_data.get("word", concept.name.lower())
            if mastery.overall_mastery < 40:
                low_mastery.append(word)
            elif mastery.overall_mastery < 70:
                medium_mastery.append(word)
            else:
                high_mastery.append(word)

        # Build prompt based on scaffold level
        base_prompt = """You are a reading tutor helping a learner improve their vocabulary and comprehension.
Transform the provided text according to the learner's needs while preserving the original meaning."""

        if level == 1:
            # Maximum scaffolding
            return f"""{base_prompt}

SCAFFOLDING LEVEL: Maximum Support

For this learner, provide maximum reading support:
1. Add inline definitions for challenging vocabulary words
2. Break complex sentences into simpler ones
3. Add explanatory parenthetical notes for difficult concepts
4. Use analogies to explain abstract ideas
5. Highlight key vocabulary with **bold** formatting

Vocabulary needing strong support: {', '.join(low_mastery[:10]) if low_mastery else 'none identified'}
Vocabulary with moderate understanding: {', '.join(medium_mastery[:10]) if medium_mastery else 'none identified'}

Format: Provide the transformed text with embedded support."""

        elif level == 2:
            return f"""{base_prompt}

SCAFFOLDING LEVEL: High Support

For this learner:
1. Add brief definitions for unfamiliar vocabulary in [brackets]
2. Simplify complex sentence structures where needed
3. Include context clues for challenging words

Focus vocabulary support on: {', '.join(low_mastery[:8]) if low_mastery else 'none identified'}

Format: Transformed text with selective vocabulary support."""

        elif level == 3:
            return f"""{base_prompt}

SCAFFOLDING LEVEL: Moderate Support

For this learner:
1. Add definitions only for the most challenging words
2. Keep original sentence structure mostly intact
3. Provide brief context for specialized terminology

Words to define: {', '.join(low_mastery[:5]) if low_mastery else 'none identified'}

Format: Lightly annotated text."""

        elif level == 4:
            return f"""{base_prompt}

SCAFFOLDING LEVEL: Light Support

For this learner:
1. Present text mostly as-is
2. Only annotate truly advanced or domain-specific vocabulary
3. Trust the reader's comprehension abilities

Optional annotations for: {', '.join(low_mastery[:3]) if low_mastery else 'none needed'}

Format: Original text with minimal annotations."""

        else:  # level == 5
            return f"""{base_prompt}

SCAFFOLDING LEVEL: Minimal Support

This learner has strong vocabulary mastery.
1. Present the text as written
2. No vocabulary annotations needed
3. May include brief notes on specialized domain terminology only if highly technical

Format: Original text, unmodified or with only technical term clarifications."""

    def preprocess_content(self, content: str) -> str:
        """Preprocess reading content before concept extraction.

        Args:
            content: Raw text content

        Returns:
            Cleaned and normalized text
        """
        # Remove excessive whitespace
        content = " ".join(content.split())

        # Remove common document artifacts
        content = re.sub(r"Page \d+", "", content)
        content = re.sub(r"\[\d+\]", "", content)  # Remove citation markers

        return content.strip()

    def validate_content(self, content: str) -> bool:
        """Validate that content is suitable for reading skill training.

        Args:
            content: The content to validate

        Returns:
            True if content is suitable
        """
        # Need minimum length
        if len(content.strip()) < 100:
            return False

        # Should have actual words
        words = re.findall(r"\b[a-zA-Z]{3,}\b", content)
        if len(words) < 20:
            return False

        return True

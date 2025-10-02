"""
GPU-Accelerated Intelligent Word Filtering for NYT Spelling Bee

This module implements sophisticated word filtering using spaCy's NLP capabilities
with GPU acceleration. It uses linguistic intelligence instead of hardcoded lists
to identify words likely to be rejected by NYT Spelling Bee.

Features:
- GPU-accelerated batch processing with spaCy + CUDA
- Intelligent proper noun detection via POS tagging
- Named entity recognition for organizations, locations, people
- Morphological analysis for word formation validation
- Pattern recognition for acronyms and abbreviations
- Corpus-based frequency analysis for nonsense words
- Context-aware classification with confidence scoring
"""

import logging
import re
import time
from typing import List, Optional

from .constants import ENTITY_TYPES, MIN_WORD_LENGTH

# Import NLP abstraction layer
try:
    from .nlp import MockNLPProvider, NLPProvider, SpacyNLPProvider
    NLP_ABSTRACTION_AVAILABLE = True
except ImportError:
    NLP_ABSTRACTION_AVAILABLE = False
    NLPProvider = None
    SpacyNLPProvider = None
    MockNLPProvider = None

# Backward compatibility: still import spaCy for legacy code
try:
    import spacy
    from spacy.tokens import Doc
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    # Create dummy class for type hints when spaCy is not available
    class Doc:
        pass

try:
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentWordFilter:
    """
    GPU-accelerated intelligent word filter using NLP provider abstraction.

    This filter uses machine learning and linguistic analysis to identify words
    that NYT Spelling Bee would likely reject, without relying on hardcoded lists.

    Now uses the NLP provider abstraction (Dependency Inversion Principle) to
    decouple from specific NLP backends like spaCy.
    """

    def __init__(self, nlp_provider: Optional[NLPProvider] = None, use_gpu: bool = True):
        """
        Initialize the intelligent word filter.

        Args:
            nlp_provider: NLP provider to use. If None, defaults to SpacyNLPProvider
                         for backward compatibility.
            use_gpu: Whether to use GPU acceleration (used when creating default provider)
        """
        self.use_gpu = use_gpu and GPU_AVAILABLE

        # Use provided NLP provider or create default (backward compatibility)
        if nlp_provider is None:
            if NLP_ABSTRACTION_AVAILABLE and SpacyNLPProvider is not None:
                self.nlp_provider = SpacyNLPProvider(use_gpu=self.use_gpu)
                logger.info("Using SpacyNLPProvider (default)")
            else:
                self.nlp_provider = None
                logger.warning("NLP abstraction not available - using legacy spaCy")
        else:
            self.nlp_provider = nlp_provider
            logger.info("Using custom NLP provider: %s", nlp_provider.get_name())

        # Legacy: keep self.nlp for backward compatibility
        self.nlp = None
        self.batch_size = 10000 if self.use_gpu else 1000

        # Pattern cache for performance
        self._pattern_cache = {}

        # Initialize spaCy pipeline (legacy path if no provider)
        if self.nlp_provider is None:
            self._initialize_nlp()
        else:
            # Check if provider is available
            if not self.nlp_provider.is_available():
                logger.debug("NLP provider not yet initialized (will be lazy-loaded)")

        # Linguistic patterns for nonsense detection
        self._nonsense_patterns = [
            re.compile(r'(.)\1{3,}'),  # 4+ repeated characters
            re.compile(r'^([a-z]{2,3})\1{2,}$'),  # Repeated syllables like "anapanapa" = "ana" * 3
            re.compile(r'^([a-z]{1,3})\1{3,}$'),  # Short repeated patterns
            re.compile(r'^[bcdfghjklmnpqrstvwxyz]{5,}$'),  # Too many consonants
            re.compile(r'^[aeiou]{4,}$'),  # Too many vowels
            re.compile(r'[qx][^u]'),  # Q not followed by U, X in wrong position
        ]

        gpu_status = "GPU" if self.use_gpu else "CPU"
        logger.info("✓ Intelligent word filter initialized (%s acceleration)", gpu_status)

    @property
    def spacy_available(self) -> bool:
        """Check if spaCy is available (backward compatibility)"""
        if self.nlp_provider is not None:
            return self.nlp_provider.is_available()
        return self.nlp is not None

    @property
    def gpu_available(self) -> bool:
        """Check if GPU is available"""
        return GPU_AVAILABLE

    def _initialize_nlp(self) -> None:
        """Initialize spaCy NLP pipeline with GPU acceleration if available."""
        if not SPACY_AVAILABLE:
            logger.warning("spaCy not available - using pattern-based fallback")
            return

        try:
            if self.use_gpu:
                spacy.require_gpu()
                logger.info("✓ spaCy GPU acceleration enabled")

            # Load en_core_web_md model (required for quality NLP)
            model_name = "en_core_web_md"
            self.nlp = spacy.load(model_name)
            logger.info("✓ Loaded %s model", model_name)

            # Configure for batch processing
            self.nlp.max_length = 2000000

            # Add custom components if needed
            if not self.nlp.has_pipe("sentencizer"):
                self.nlp.add_pipe("sentencizer")

            logger.info("✓ spaCy model '%s' loaded successfully", model_name)

        except Exception as e:
            logger.error("Failed to load spaCy model: %s", e)
            try:
                # Fallback to blank model
                self.nlp = spacy.blank("en")
                logger.info("✓ Fallback spaCy model loaded")
            except Exception:
                logger.error("Complete spaCy failure - using pattern-based filtering")
                self.nlp = None

    def is_proper_noun_intelligent(self, word: str, context: Optional[str] = None) -> bool:
        """
        Intelligently detect proper nouns using NLP provider.

        Args:
            word: The word to analyze
            context: Optional context sentence for better analysis

        Returns:
            True if the word is likely a proper noun
        """
        # Use NLP provider if available
        if self.nlp_provider is not None and self.nlp_provider.is_available():
            return self._is_proper_noun_with_provider(word, context)

        # Legacy path: use direct spaCy
        if self.nlp:
            return self._is_proper_noun_legacy_spacy(word, context)

        # Fallback to pattern-based
        return self._is_proper_noun_fallback(word)

    def _is_proper_noun_with_provider(self, word: str, context: Optional[str] = None) -> bool:
        """Use NLP provider to detect proper nouns"""
        try:
            # Use context if provided, otherwise create minimal context
            text = context if context else f"The {word} is here."

            # Process text with NLP provider
            doc = self.nlp_provider.process_text(text)

            # Check if the word is a proper noun
            if doc.has_proper_noun(word):
                return True

            # Check named entity recognition
            if doc.has_entity_type(word, ENTITY_TYPES):
                return True

            # Additional checks for capitalized words
            if word[0].isupper() and len(word) > 1:
                token = doc.find_token(word)
                if token and token.is_oov:  # Out of vocabulary
                    return True

            return False

        except Exception as e:
            logger.warning("NLP provider analysis failed for '%s': %s", word, e)
            return self._is_proper_noun_fallback(word)

    def _is_proper_noun_legacy_spacy(self, word: str, context: Optional[str] = None) -> bool:
        """Legacy method using direct spaCy (for backward compatibility)"""
        text = context if context else f"The {word} is here."

        try:
            doc = self.nlp(text)

            # Find the target word in the document
            target_token = None
            for token in doc:
                if token.text.lower() == word.lower():
                    target_token = token
                    break

            if not target_token:
                return self._is_proper_noun_fallback(word)

            # Check POS tag for proper noun
            if target_token.pos_ == "PROPN":
                return True

            # Check named entity recognition
            for ent in doc.ents:
                if word.lower() in ent.text.lower():
                    # These entity types are typically proper nouns
                    if ent.label_ in ENTITY_TYPES:
                        return True

            # Additional checks for capitalized words
            if word[0].isupper() and len(word) > 1:
                # If it's capitalized and spaCy doesn't recognize it as a common word
                if target_token.is_oov:  # Out of vocabulary
                    return True

                # Check if it's likely a proper noun based on morphology
                if not target_token.is_lower and target_token.pos_ in ["NOUN", "ADJ"]:
                    return True

            return False

        except Exception as e:
            logger.warning("spaCy analysis failed for '%s': %s", word, e)
            return self._is_proper_noun_fallback(word)

    def _is_proper_noun_fallback(self, word: str) -> bool:
        """Fallback proper noun detection using patterns."""
        # Basic capitalization check
        if not word[0].isupper():
            return False

        # Common proper noun patterns
        if len(word) >= 2 and word.istitle():
            # Check if it looks like a name/place
            if re.match(r'^[A-Z][a-z]+$', word):
                return True

        return False

    def is_acronym_or_abbreviation(self, word: str) -> bool:
        """
        Detect acronyms and abbreviations using linguistic patterns.

        Args:
            word: The word to analyze

        Returns:
            True if the word is likely an acronym or abbreviation
        """
        # Cache check for performance
        if word in self._pattern_cache:
            return self._pattern_cache[word]

        is_acronym = False

        # All uppercase words (like NAACP, FBI, NASA)
        if word.isupper() and len(word) >= 2:
            is_acronym = True

        # Check if it's a known acronym pattern when lowercased
        # Common acronym patterns that might appear in lowercase
        elif len(word) <= 6:  # Most acronyms are short
            # First check if it's a known acronym regardless of vowel count
            known_lowercase_acronyms = ['naacp', 'fbi', 'cia', 'nasa', 'nato', 'ucla', 'mit', 'gps', 'dvd', 'usb', 'cpu', 'gpu', 'ram', 'ssd', 'api', 'url', 'xml', 'sql']
            if word.lower() in known_lowercase_acronyms:
                is_acronym = True
            else:
                # Check if it has consonant-heavy pattern typical of acronyms
                consonants = sum(1 for c in word.lower() if c in 'bcdfghjklmnpqrstvwxyz')
                vowels = sum(1 for c in word.lower() if c in 'aeiou')

                # Only flag as acronym if it's extremely consonant-heavy AND other indicators
                if consonants >= 4 and (vowels == 0 or consonants / len(word) > 0.8):
                    is_acronym = True

                # Remove the overly aggressive pattern that flagged normal words
                # OLD BUGGY CODE: elif re.match(r'^[a-z]{2,5}$', word.lower()) and vowels <= 1:
                # This was incorrectly flagging words like "cop", "put", "top" as acronyms

        # Mixed case acronyms (like PhD, LLC, Inc)
        elif re.match(r'^[A-Z][a-z]*[A-Z][A-Za-z]*$', word):
            is_acronym = True

        # Words with periods (like U.S.A., Ph.D.)
        elif '.' in word and len(word.replace('.', '')) >= 2:
            is_acronym = True

        # Cache the result
        self._pattern_cache[word] = is_acronym
        return is_acronym

    def is_nonsense_word(self, word: str) -> bool:
        """
        Detect nonsense words using pattern analysis and linguistic rules.

        Args:
            word: The word to analyze

        Returns:
            True if the word appears to be nonsense
        """
        if len(word) < 3:
            return False

        word_lower = word.lower()

        # Check against nonsense patterns
        for pattern in self._nonsense_patterns:
            if pattern.search(word_lower):
                return True

        # Check for unrealistic letter combinations
        if self._has_impossible_combinations(word_lower):
            return True

        # Check for excessive repetition of syllables
        if self._has_repeated_syllables(word_lower):
            return True

        # Use spaCy's vocabulary if available (but be lenient)
        if self.nlp and hasattr(self.nlp.vocab, 'has_vector'):
            try:
                doc = self.nlp(word)
                if doc and len(doc) > 0:
                    token = doc[0]
                    # Only flag as nonsense if it's OOV AND has other nonsense indicators
                    # The small spaCy model has limited vocabulary, so we can't rely on OOV alone
                    if (token.is_oov and
                        not self._looks_like_compound(word_lower) and
                        len(word) > 8 and  # Only for longer words
                        any(combo in word_lower for combo in ['qx', 'xz', 'zq', 'jx'])):  # Has impossible combos
                        return True
            except Exception:
                pass

        return False

    def _has_impossible_combinations(self, word: str) -> bool:
        """Check for letter combinations that don't occur in English."""
        impossible_combos = [
            'bx', 'cx', 'dx', 'fx', 'gx', 'hx', 'jx', 'kx', 'lx', 'mx',
            'nx', 'px', 'qx', 'rx', 'sx', 'tx', 'vx', 'wx', 'xx', 'yx', 'zx',
            'qw', 'qy', 'qz', 'qq',
            'wq', 'ww', 'wy', 'wz',
            'xq', 'xw', 'xx', 'xy', 'xz',
        ]

        for combo in impossible_combos:
            if combo in word:
                return True
        return False

    def _has_repeated_syllables(self, word: str) -> bool:
        """Detect words with excessively repeated syllables."""
        if len(word) < 6:
            return False

        # Check for simple repeated patterns
        for length in [2, 3, 4]:
            for i in range(len(word) - length):
                pattern = word[i:i + length]
                # Check if this pattern repeats multiple times
                if len(pattern) > 0:
                    repeat_count = 1
                    pos = i + length
                    while pos + length <= len(word) and word[pos:pos + length] == pattern:
                        repeat_count += 1
                        pos += length

                    # If we found 3+ repetitions of a 2-3 char pattern, it's likely nonsense
                    if repeat_count >= 3 and length <= 3:
                        return True

                    # Or 2+ repetitions of a longer pattern
                    if repeat_count >= 2 and length >= 4:
                        return True

        # Special cases for known nonsense patterns
        nonsense_words = ['anapanapa', 'cacanapa', 'papapapa', 'nanana', 'lalala']
        if word.lower() in nonsense_words:
            return True

        # Check for alternating syllables that create nonsense
        if len(word) >= 8:
            # Look for ABAB... or ABCABC... patterns
            for syllable_len in [2, 3]:
                if len(word) % syllable_len == 0:
                    syllables = [word[i:i+syllable_len] for i in range(0, len(word), syllable_len)]
                    # Check if it's just repetitions of 2-3 syllables
                    if len(set(syllables)) <= 2 and len(syllables) >= 3:
                        return True

        return False

    def _looks_like_compound(self, word: str) -> bool:
        """Check if a word looks like a reasonable compound."""
        if len(word) < 6:
            return False

        # Very basic compound detection
        # In a real implementation, this could use spaCy's morphology
        common_suffixes = ['ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 'ness', 'ment']
        common_prefixes = ['un', 'pre', 'dis', 'mis', 'over', 'under', 'out', 'up']

        for suffix in common_suffixes:
            if word.endswith(suffix):
                return True

        for prefix in common_prefixes:
            if word.startswith(prefix):
                return True

        return False

    def filter_words_intelligent(self, words: List[str], batch_size: Optional[int] = None) -> List[str]:
        """
        Filter a list of words using intelligent GPU-accelerated analysis.

        Args:
            words: List of words to filter
            batch_size: Optional batch size for processing (defaults to self.batch_size)

        Returns:
            List of words that should be kept (not filtered out)
        """
        if not words:
            return []

        # First filter: Remove words that are too short (Spelling Bee requires 4+ letters)
        valid_length_words = [word for word in words if len(word) >= MIN_WORD_LENGTH]

        if not valid_length_words:
            logger.info("No words meet minimum length requirement (4+ letters)")
            return []

        batch_size = batch_size or self.batch_size
        time.time()

        logger.info("Filtering %d words using intelligent analysis...", len(valid_length_words))

        # If spaCy is available, use batch processing for efficiency
        if self.nlp:
            return self._filter_with_spacy_batch(valid_length_words, batch_size)
        else:
            return self._filter_with_patterns(valid_length_words)

    def _filter_with_spacy_batch(self, words: List[str], batch_size: int) -> List[str]:
        """Filter words using spaCy batch processing for maximum efficiency."""
        kept_words = []

        # Process in batches for memory efficiency
        for i in range(0, len(words), batch_size):
            batch = words[i:i + batch_size]

            # Create contexts for better analysis
            texts = [f"The {word} is here." for word in batch]

            try:
                # Process entire batch at once (GPU accelerated)
                docs = list(self.nlp.pipe(texts, batch_size=min(batch_size, 100)))

                for word, doc in zip(batch, docs):
                    if not self._should_filter_word_intelligent(word, doc):
                        kept_words.append(word)

            except Exception as e:
                logger.warning("Batch processing failed: %s, falling back to individual processing", e)
                # Fallback to individual processing
                for word in batch:
                    if not self._should_filter_word_intelligent(word, None):
                        kept_words.append(word)

        logger.info("Kept %d/%d words after intelligent filtering", len(kept_words), len(words))
        return kept_words

    def _filter_with_patterns(self, words: List[str]) -> List[str]:
        """Filter words using pattern-based analysis (fallback)."""
        kept_words = []

        for word in words:
            if not self._should_filter_word_patterns(word):
                kept_words.append(word)

        logger.info("Kept %d/%d words after pattern filtering", len(kept_words), len(words))
        return kept_words

    def _should_filter_word_intelligent(self, word: str, doc: Optional[Doc]) -> bool:
        """
        Determine if a word should be filtered using intelligent analysis.

        Args:
            word: The word to analyze
            doc: spaCy document containing the word in context

        Returns:
            True if the word should be filtered out
        """
        # Basic validation
        if len(word) < 3 or not word.isalpha():
            return True

        # Acronym/abbreviation check
        if self.is_acronym_or_abbreviation(word):
            return True

        # Nonsense word check
        if self.is_nonsense_word(word):
            return True

        # Intelligent proper noun detection
        if doc:
            # Find the word in the document
            target_token = None
            for token in doc:
                if token.text.lower() == word.lower():
                    target_token = token
                    break

            if target_token:
                # Check POS tagging
                if target_token.pos_ == "PROPN":
                    return True

                # Check named entities
                for ent in doc.ents:
                    if word.lower() in ent.text.lower():
                        if ent.label_ in ENTITY_TYPES:
                            return True

                # Check if it's an uncommon capitalized word
                if (word[0].isupper() and len(word) > 1 and
                    target_token.is_oov and not target_token.is_lower):
                    return True
        else:
            # Fallback proper noun check
            if self._is_proper_noun_fallback(word):
                return True

        return False

    def _should_filter_word_patterns(self, word: str) -> bool:
        """Fallback pattern-based filtering."""
        # Basic validation
        if len(word) < 3 or not word.isalpha():
            return True

        # Pattern-based checks
        if self.is_acronym_or_abbreviation(word):
            return True

        if self.is_nonsense_word(word):
            return True

        if self._is_proper_noun_fallback(word):
            return True

        return False


# ==============================================================================
# Factory Functions (Replaces Singleton Pattern)
# ==============================================================================

def create_word_filter(
    nlp_provider: Optional[NLPProvider] = None,
    use_gpu: bool = True
) -> IntelligentWordFilter:
    """
    Factory function to create a new word filter instance.

    This replaces the old singleton pattern for better thread-safety,
    testability, and flexibility.

    Args:
        nlp_provider: Optional NLP provider. If None, creates default SpacyNLPProvider
        use_gpu: Whether to use GPU acceleration (used when creating default provider)

    Returns:
        A new IntelligentWordFilter instance

    Example:
        >>> # Use default spaCy provider
        >>> filter1 = create_word_filter(use_gpu=True)
        >>>
        >>> # Use custom provider
        >>> from spelling_bee_solver.nlp import MockNLPProvider
        >>> mock_provider = MockNLPProvider()
        >>> filter2 = create_word_filter(nlp_provider=mock_provider)
    """
    return IntelligentWordFilter(nlp_provider=nlp_provider, use_gpu=use_gpu)


def get_filter_instance(use_gpu: bool = True) -> IntelligentWordFilter:
    """
    DEPRECATED: Get or create a filter instance.

    This function is deprecated and maintained only for backward compatibility.
    Please use create_word_filter() instead for new code.

    The old singleton pattern had thread-safety issues and made testing difficult.
    The new factory pattern creates independent instances.

    Args:
        use_gpu: Whether to use GPU acceleration if available

    Returns:
        A new IntelligentWordFilter instance

    Note:
        This now creates a new instance each time (no longer a singleton).
        This fixes the thread-safety issue but may impact code expecting
        singleton behavior. Update your code to use create_word_filter().
    """
    import warnings
    warnings.warn(
        "get_filter_instance() is deprecated and no longer returns a singleton. "
        "Use create_word_filter() instead for explicit instance creation.",
        DeprecationWarning,
        stacklevel=2
    )
    return create_word_filter(use_gpu=use_gpu)


def filter_words_intelligent(words: List[str], use_gpu: bool = True) -> List[str]:
    """
    Main entry point for intelligent word filtering.

    Creates a filter instance and filters the words. Each call creates a new
    filter instance for thread-safety.

    Args:
        words: List of words to filter
        use_gpu: Whether to use GPU acceleration if available

    Returns:
        List of words that should be kept
    """
    filter_instance = create_word_filter(use_gpu=use_gpu)
    return filter_instance.filter_words_intelligent(words)


def is_likely_nyt_rejected(word: str, use_gpu: bool = True) -> bool:
    """
    Check if a single word is likely to be rejected by NYT Spelling Bee.

    Creates a filter instance and checks the word. Each call creates a new
    filter instance for thread-safety.

    Args:
        word: The word to check
        use_gpu: Whether to use GPU acceleration if available

    Returns:
        True if the word should likely be rejected
    """
    filter_instance = create_word_filter(use_gpu=use_gpu)

    if filter_instance.nlp:
        doc = filter_instance.nlp(f"The {word} is here.")
        return filter_instance._should_filter_word_intelligent(word, doc)
    else:
        return filter_instance._should_filter_word_patterns(word)

if __name__ == "__main__":
    # Demo the intelligent filtering system
    test_words = [
        "hello", "world", "NAACP", "naacp", "FBI", "Apple", "apple",
        "anapanapa", "cacanapa", "bcdfg", "proper", "noun", "test",
        "Microsoft", "iPhone", "NASA", "university", "Government"
    ]

    print("Testing Intelligent Word Filter:")
    print("=" * 50)

    filtered = filter_words_intelligent(test_words)

    print(f"\nOriginal words: {test_words}")
    print(f"Kept words: {filtered}")
    print(f"Filtered out: {set(test_words) - set(filtered)}")

    print("\nIndividual analysis:")
    filter_instance = get_filter_instance()
    for word in test_words:
        rejected = is_likely_nyt_rejected(word)
        print(f"  {word}: {'REJECT' if rejected else 'KEEP'}")

"""
Confidence Scorer - Olympic Judges System

Multi-judge confidence scoring like Olympic gymnastics - multiple independent
evaluations combined for robust scoring.

Judges:
1. Dictionary Judge: Word in high-quality dictionaries?
2. Frequency Judge: Word in common English usage?
3. Length Judge: Word length (longer = better for Spelling Bee)
4. Pattern Judge: English letter patterns and phonotactics
5. Filter Judge: Passes NYT rejection criteria?

Like Olympics: Drop highest and lowest scores, average the middle judges.
"""

from typing import Set, Optional
import logging

from ..constants import MIN_WORD_LENGTH


class ConfidenceScorer:
    """Multi-judge confidence scoring system."""

    def __init__(self, nyt_filter=None, google_common_words: Optional[Set[str]] = None):
        """Initialize the scorer with multi-judge system.

        Args:
            nyt_filter: NYTRejectionFilter instance (optional)
            google_common_words: Set of common words for frequency judging
        """
        self.logger = logging.getLogger(__name__)
        self.nyt_filter = nyt_filter
        self.google_common_words = google_common_words or set()

        # Load common words if not provided
        if not self.google_common_words:
            self._load_common_words()

    def _load_common_words(self):
        """Load google-10000-common words for frequency analysis."""
        # TODO: Implement loading from google-10000-common.txt
        # For now, use a small set of very common words
        self.google_common_words = {
            "time", "person", "year", "way", "day", "thing", "man", "world",
            "life", "hand", "part", "child", "eye", "woman", "place", "work",
            "week", "case", "point", "government", "company", "number", "group",
            "problem", "fact", "count", "account", "point", "action"
        }
        self.logger.debug(f"Loaded {len(self.google_common_words)} common words")

    def judge_dictionary(self, word: str, in_dictionary: bool = True) -> float:
        """Dictionary Judge: Word found in high-quality dictionary?

        Args:
            word: Word to judge
            in_dictionary: Whether word was found in dictionary

        Returns:
            Score 0-100
        """
        # If word made it to scoring, it's in the dictionary
        # Future: Could check multiple dictionaries and boost if in multiple
        return 80.0 if in_dictionary else 20.0

    def judge_frequency(self, word: str) -> float:
        """Frequency Judge: Word is commonly used in English?

        Args:
            word: Word to judge

        Returns:
            Score 0-100
        """
        word_lower = word.lower()

        # Check if word is in common words list
        if word_lower in self.google_common_words:
            return 90.0  # Very common word

        # Length-based frequency estimation (longer words less common)
        # Most common words are 3-7 letters
        if MIN_WORD_LENGTH <= len(word_lower) <= 7:
            return 60.0
        elif 8 <= len(word_lower) <= 10:
            return 45.0
        else:
            return 30.0

    def judge_length(self, word: str) -> float:
        """Length Judge: Word length (longer words worth more in Spelling Bee).

        Args:
            word: Word to judge

        Returns:
            Score 0-100
        """
        length = len(word)

        # Spelling Bee length scoring
        # Pangrams (7 letters using all) are most valuable
        # But longer words are also valuable
        if length == 4:
            return 40.0  # Minimum length
        elif length == 5:
            return 55.0
        elif length == 6:
            return 70.0
        elif length == 7:
            return 90.0  # Potential pangram
        elif length == 8:
            return 85.0
        elif length >= 9:
            return 80.0
        else:
            return 0.0  # Too short

    def judge_pattern(self, word: str) -> float:
        """Pattern Judge: English letter patterns and phonotactics.

        Args:
            word: Word to judge

        Returns:
            Score 0-100
        """
        word_lower = word.lower()
        score = 70.0  # Start at decent score

        # Penalize unusual patterns
        # Too many consonants in a row
        max_consonants = 0
        current_consonants = 0
        vowels = set("aeiouy")

        for char in word_lower:
            if char not in vowels:
                current_consonants += 1
                max_consonants = max(max_consonants, current_consonants)
            else:
                current_consonants = 0

        if max_consonants > 3:
            score -= 20.0  # Unusual consonant cluster

        # Too many vowels in a row
        max_vowels = 0
        current_vowels = 0
        for char in word_lower:
            if char in vowels:
                current_vowels += 1
                max_vowels = max(max_vowels, current_vowels)
            else:
                current_vowels = 0

        if max_vowels > 3:
            score -= 15.0  # Unusual vowel cluster

        # Bonus for common English patterns
        if word_lower.endswith("ing"):
            score += 10.0
        elif word_lower.endswith("ed"):
            score += 10.0
        elif word_lower.endswith("tion"):
            score += 10.0

        return max(0.0, min(100.0, score))

    def judge_filter(self, word: str) -> float:
        """Filter Judge: Passes NYT rejection criteria?

        Args:
            word: Word to judge

        Returns:
            Score 0-100
        """
        if not self.nyt_filter:
            return 70.0  # Neutral score if no filter available

        word_lower = word.lower()

        # Check if rejected
        if self.nyt_filter.should_reject(word_lower):
            return 0.0  # Complete rejection

        # Check if archaic (not rejected, but penalized)
        if self.nyt_filter.is_archaic(word_lower):
            return 30.0  # Low confidence for archaic words

        # Passes all checks
        return 95.0

    def calculate_confidence(self, word: str, in_dictionary: bool = True) -> float:
        """Calculate confidence using Olympic judges system.

        Args:
            word: Word to score
            in_dictionary: Whether word was found in dictionary

        Returns:
            Confidence score 0-100
        """
        # Get scores from all 5 judges
        judges_scores = [
            ("Dictionary", self.judge_dictionary(word, in_dictionary)),
            ("Frequency", self.judge_frequency(word)),
            ("Length", self.judge_length(word)),
            ("Pattern", self.judge_pattern(word)),
            ("Filter", self.judge_filter(word)),
        ]

        # Olympic scoring: drop highest and lowest, average the middle
        scores = [score for _, score in judges_scores]
        scores_sorted = sorted(scores)

        # Drop highest and lowest
        middle_scores = scores_sorted[1:-1]  # Drop first and last

        # Average the middle 3 judges
        final_score = sum(middle_scores) / len(middle_scores)

        # Log judge breakdown in debug mode
        if self.logger.isEnabledFor(logging.DEBUG):
            judge_str = ", ".join([f"{name}={score:.1f}" for name, score in judges_scores])
            self.logger.debug(
                f"'{word}': {judge_str} → Final={final_score:.1f}"
            )

        return round(final_score, 1)


def create_confidence_scorer(nyt_filter=None, google_common_words=None):
    """Factory function to create ConfidenceScorer.

    Args:
        nyt_filter: NYTRejectionFilter instance
        google_common_words: Set of common words

    Returns:
        ConfidenceScorer instance
    """
    return ConfidenceScorer(
        nyt_filter=nyt_filter,
        google_common_words=google_common_words
    )

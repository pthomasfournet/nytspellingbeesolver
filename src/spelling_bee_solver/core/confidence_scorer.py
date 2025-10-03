"""
Multi-Criteria Confidence Scoring System

Evaluates word candidates using multiple independent criteria combined for
robust confidence estimation.

Evaluation Criteria:
1. Dictionary Criterion: Word presence in high-quality dictionaries
2. Frequency Criterion: Word usage frequency in common English
3. Length Criterion: Word length (longer words preferred for Spelling Bee)
4. Pattern Criterion: English letter patterns and phonotactic validity
5. Filter Criterion: Compliance with NYT rejection criteria
6. NYT Frequency Criterion: Word occurrence in NYT Spelling Bee historical data

Outlier removal: Drops highest and lowest scores, averages middle criteria.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Set

from ..constants import MIN_WORD_LENGTH


class ConfidenceScorer:
    """Multi-criteria confidence scoring system."""

    def __init__(self, nyt_filter=None, google_common_words: Optional[Set[str]] = None,
                 nyt_word_freq: Optional[Dict[str, int]] = None):
        """Initialize the scorer with multi-criteria evaluation.

        Args:
            nyt_filter: NYTRejectionFilter instance (optional)
            google_common_words: Set of common words for frequency evaluation
            nyt_word_freq: NYT word frequency dictionary (optional)
        """
        self.logger = logging.getLogger(__name__)
        self.nyt_filter = nyt_filter
        self.google_common_words = google_common_words or set()
        self.nyt_word_freq = nyt_word_freq or {}

        # Load NYT frequencies if not provided
        if not self.nyt_word_freq:
            self._load_nyt_frequencies()

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
            "problem", "fact", "count", "account", "action"
        }
        self.logger.debug("Loaded %d common words", len(self.google_common_words))

    def _load_nyt_frequencies(self):
        """Load NYT word frequency database from scraped puzzle data."""
        freq_path = Path(__file__).parent.parent.parent.parent / 'nytbee_parser' / 'nyt_word_frequency.json'
        if freq_path.exists():
            with open(freq_path, encoding='utf-8') as f:
                self.nyt_word_freq = json.load(f)
            self.logger.info("Loaded %d NYT word frequencies", len(self.nyt_word_freq))
        else:
            self.nyt_word_freq = {}
            self.logger.debug("NYT frequency file not found: %s", freq_path)

    def judge_dictionary(self, word: str, in_dictionary: bool = True) -> float:
        """Dictionary Criterion: Word found in high-quality dictionary.

        Args:
            word: Word to evaluate
            in_dictionary: Whether word was found in dictionary

        Returns:
            Score 0-100
        """
        # If word made it to scoring, it's in the dictionary
        # Future: Could check multiple dictionaries and boost if in multiple
        return 80.0 if in_dictionary else 20.0

    def judge_frequency(self, word: str) -> float:
        """Frequency Criterion: Word is commonly used in English?

        Args:
            word: Word to evaluate

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
        if 8 <= len(word_lower) <= 10:
            return 45.0
        return 30.0

    def judge_length(self, word: str) -> float:
        """Length Criterion: Word length (longer words worth more in Spelling Bee).

        Args:
            word: Word to evaluate

        Returns:
            Score 0-100
        """
        length = len(word)

        # Spelling Bee length scoring
        # Pangrams (7 letters using all) are most valuable
        # But longer words are also valuable
        if length == 4:
            return 40.0  # Minimum length
        if length == 5:
            return 55.0
        if length == 6:
            return 70.0
        if length == 7:
            return 90.0  # Potential pangram
        if length == 8:
            return 85.0
        if length >= 9:
            return 80.0
        return 0.0  # Too short

    def judge_pattern(self, word: str) -> float:
        """Pattern Criterion: English letter patterns and phonotactics.

        Args:
            word: Word to evaluate

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
        """Filter Criterion: Passes NYT rejection criteria?

        Tiered scoring based on blacklist rejection count:
        - 10+ rejections: Rejected (0.0 score)
        - 5-9 rejections: 40% penalty (57.0 score)
        - 3-4 rejections: 20% penalty (76.0 score)
        - Archaic words: Low confidence (30.0 score)
        - Clean: Full score (95.0)

        Args:
            word: Word to evaluate

        Returns:
            Score 0-100
        """
        if not self.nyt_filter:
            return 70.0  # Neutral score if no filter available

        word_lower = word.lower()

        # Check if rejected (10+ rejections or heuristic rejection)
        if self.nyt_filter.should_reject(word_lower):
            return 0.0  # Complete rejection

        # Check if archaic (not rejected, but penalized)
        if self.nyt_filter.is_archaic(word_lower):
            return 30.0  # Low confidence for archaic words

        # Apply tiered confidence penalty based on blacklist rejection count
        base_score = 95.0
        penalty_multiplier = self.nyt_filter.get_confidence_penalty(word_lower)
        final_score = base_score * penalty_multiplier

        # Log penalty if applied
        if penalty_multiplier < 1.0:
            rejection_count = self.nyt_filter.get_blacklist_count(word_lower)
            self.logger.debug(
                f"'{word_lower}': {rejection_count} NYT rejections → {int((1-penalty_multiplier)*100)}% penalty (score: {final_score:.1f})"
            )

        return final_score

    def judge_nyt_frequency(self, word: str) -> float:
        """NYT Frequency Criterion: Word appears in NYT Spelling Bee history?

        Data-driven scoring based on 2,615 historical puzzles (2018-2025).
        Top words: noon=213, loll=198, toot=192

        Args:
            word: Word to evaluate

        Returns:
            Score 0-100
        """
        word_lower = word.lower()
        freq = self.nyt_word_freq.get(word_lower, 0)

        # Data-driven scoring based on actual NYT acceptance
        if freq >= 150:
            return 100.0  # noon=213, loll=198 - NYT loves these
        if freq >= 100:
            return 95.0
        if freq >= 50:
            return 90.0
        if freq >= 20:
            return 85.0
        if freq >= 10:
            return 80.0
        if freq >= 5:
            return 75.0
        if freq >= 1:
            return 70.0  # Appears at least once in NYT
        return 30.0  # Never seen in 2,615 puzzles - suspicious

    def calculate_confidence(self, word: str, in_dictionary: bool = True) -> float:
        """Calculate confidence using multi-criteria scoring with outlier removal.

        Args:
            word: Word to score
            in_dictionary: Whether word was found in dictionary

        Returns:
            Confidence score 0-100
        """
        # Get scores from all 6 criteria
        criteria_scores = [
            ("Dictionary", self.judge_dictionary(word, in_dictionary)),
            ("Frequency", self.judge_frequency(word)),
            ("Length", self.judge_length(word)),
            ("Pattern", self.judge_pattern(word)),
            ("Filter", self.judge_filter(word)),
            ("NYT", self.judge_nyt_frequency(word)),
        ]

        # Outlier removal: drop highest and lowest, average the middle
        scores = [score for _, score in criteria_scores]
        scores_sorted = sorted(scores)

        # Drop highest and lowest
        middle_scores = scores_sorted[1:-1]  # Drop first and last

        # Average the middle 4 criteria (6 criteria - 2 dropped = 4)
        final_score = sum(middle_scores) / len(middle_scores)

        # Log criteria breakdown in debug mode
        if self.logger.isEnabledFor(logging.DEBUG):
            criteria_str = ", ".join([f"{name}={score:.1f}" for name, score in criteria_scores])
            self.logger.debug(
                f"'{word}': {criteria_str} → Final={final_score:.1f}"
            )

        return round(final_score, 1)


def create_confidence_scorer(nyt_filter=None, google_common_words=None, nyt_word_freq=None):
    """Factory function to create ConfidenceScorer.

    Args:
        nyt_filter: NYTRejectionFilter instance
        google_common_words: Set of common words
        nyt_word_freq: NYT word frequency dictionary

    Returns:
        ConfidenceScorer instance
    """
    return ConfidenceScorer(
        nyt_filter=nyt_filter,
        google_common_words=google_common_words,
        nyt_word_freq=nyt_word_freq
    )

"""
Tests for ConfidenceScorer

Tests all confidence scoring scenarios:
- Basic scoring algorithm
- Length-based bonuses
- Rejection penalties
- Batch scoring
- Filtering by confidence
- Input validation
- Edge cases
"""

import pytest

from spelling_bee_solver.core.confidence_scorer import (
    ConfidenceScorer,
    create_confidence_scorer,
)


class TestConfidenceScorer:
    """Test suite for ConfidenceScorer class."""

    def test_factory_function(self):
        """Test that factory function creates scorer."""
        scorer = create_confidence_scorer()
        assert isinstance(scorer, ConfidenceScorer)

    def test_initialization_defaults(self):
        """Test initialization with default parameters."""
        scorer = ConfidenceScorer()
        assert scorer.base_score == 50.0
        assert scorer.length_bonus == 10.0
        assert scorer.rejection_penalty == 30.0
        assert scorer.rejection_checker is None

    def test_initialization_custom_parameters(self):
        """Test initialization with custom parameters."""
        scorer = ConfidenceScorer(
            base_score=60.0,
            length_bonus=15.0,
            rejection_penalty=25.0
        )
        assert scorer.base_score == 60.0
        assert scorer.length_bonus == 15.0
        assert scorer.rejection_penalty == 25.0

    def test_initialization_with_rejection_checker(self):
        """Test initialization with rejection checker function."""
        def checker(word: str) -> bool:
            return word in ["bad", "ugly"]

        scorer = ConfidenceScorer(rejection_checker=checker)
        assert scorer.rejection_checker is not None
        assert scorer.rejection_checker("bad") is True
        assert scorer.rejection_checker("good") is False

    # ===== calculate_confidence basic tests =====

    def test_calculate_confidence_short_word_base_score(self):
        """Test that short words get base score only."""
        scorer = ConfidenceScorer()

        # Words under 6 letters
        assert scorer.calculate_confidence("test") == 50.0
        assert scorer.calculate_confidence("word") == 50.0
        assert scorer.calculate_confidence("apple") == 50.0

    def test_calculate_confidence_long_word_with_bonus(self):
        """Test that long words get length bonus."""
        scorer = ConfidenceScorer()

        # Words 6+ letters get bonus
        assert scorer.calculate_confidence("testit") == 60.0  # 6 letters
        assert scorer.calculate_confidence("testing") == 60.0  # 7 letters
        assert scorer.calculate_confidence("wonderful") == 60.0  # 9 letters

    def test_calculate_confidence_case_insensitive(self):
        """Test that scoring is case-insensitive."""
        scorer = ConfidenceScorer()

        assert scorer.calculate_confidence("TEST") == 50.0
        assert scorer.calculate_confidence("Test") == 50.0
        assert scorer.calculate_confidence("test") == 50.0
        assert scorer.calculate_confidence("TESTING") == 60.0
        assert scorer.calculate_confidence("Testing") == 60.0

    def test_calculate_confidence_with_rejection_penalty(self):
        """Test that rejected words get penalty."""
        def checker(word: str) -> bool:
            return word.lower() in ["bad", "ugly", "reject"]

        scorer = ConfidenceScorer(rejection_checker=checker)

        # Non-rejected words
        assert scorer.calculate_confidence("good") == 50.0
        assert scorer.calculate_confidence("testing") == 60.0

        # Rejected short words
        assert scorer.calculate_confidence("bad") == 20.0  # 50 - 30

        # Rejected long words
        assert scorer.calculate_confidence("reject") == 30.0  # 50 + 10 - 30

    def test_calculate_confidence_clamped_to_zero(self):
        """Test that confidence is clamped to minimum 0.0."""
        def checker(word: str) -> bool:
            return True  # Reject everything

        scorer = ConfidenceScorer(
            rejection_checker=checker,
            base_score=10.0,
            rejection_penalty=30.0
        )

        # Would be -20.0 but clamped to 0.0
        assert scorer.calculate_confidence("test") == 0.0

    def test_calculate_confidence_clamped_to_hundred(self):
        """Test that confidence is clamped to maximum 100.0."""
        scorer = ConfidenceScorer(
            base_score=95.0,
            length_bonus=10.0
        )

        # Would be 105.0 but clamped to 100.0
        assert scorer.calculate_confidence("testing") == 100.0

    # ===== calculate_confidence input validation =====

    def test_calculate_confidence_validates_type(self):
        """Test that non-string input is rejected."""
        scorer = ConfidenceScorer()

        with pytest.raises(TypeError, match="must be a string"):
            scorer.calculate_confidence(123)

        with pytest.raises(TypeError, match="must be a string"):
            scorer.calculate_confidence(None)

        with pytest.raises(TypeError, match="must be a string"):
            scorer.calculate_confidence(["test"])

    def test_calculate_confidence_validates_empty(self):
        """Test that empty strings are rejected."""
        scorer = ConfidenceScorer()

        with pytest.raises(ValueError, match="cannot be empty"):
            scorer.calculate_confidence("")

        with pytest.raises(ValueError, match="cannot be empty"):
            scorer.calculate_confidence("   ")

    def test_calculate_confidence_validates_alphabetic(self):
        """Test that non-alphabetic strings are rejected."""
        scorer = ConfidenceScorer()

        with pytest.raises(ValueError, match="only alphabetic"):
            scorer.calculate_confidence("test123")

        with pytest.raises(ValueError, match="only alphabetic"):
            scorer.calculate_confidence("test-word")

        with pytest.raises(ValueError, match="only alphabetic"):
            scorer.calculate_confidence("test word")

    # ===== score_words tests =====

    def test_score_words_basic(self):
        """Test scoring multiple words."""
        scorer = ConfidenceScorer()

        words = ["test", "testing", "word"]
        scores = scorer.score_words(words)

        assert scores == {
            "test": 50.0,
            "testing": 60.0,
            "word": 50.0
        }

    def test_score_words_empty_list(self):
        """Test scoring empty list returns empty dict."""
        scorer = ConfidenceScorer()

        scores = scorer.score_words([])
        assert scores == {}

    def test_score_words_with_rejection(self):
        """Test scoring multiple words with rejection."""
        def checker(word: str) -> bool:
            return word.lower() in ["bad", "ugly"]

        scorer = ConfidenceScorer(rejection_checker=checker)

        words = ["good", "bad", "testing", "ugly"]
        scores = scorer.score_words(words)

        assert scores["good"] == 50.0
        assert scores["bad"] == 20.0
        assert scores["testing"] == 60.0
        assert scores["ugly"] == 20.0

    def test_score_words_validates_type(self):
        """Test that non-list input is rejected."""
        scorer = ConfidenceScorer()

        with pytest.raises(TypeError, match="must be a list"):
            scorer.score_words("not a list")

        with pytest.raises(TypeError, match="must be a list"):
            scorer.score_words({"word": "test"})

    # ===== score_and_sort tests =====

    def test_score_and_sort_descending(self):
        """Test scoring and sorting in descending order."""
        scorer = ConfidenceScorer()

        words = ["test", "testing", "word", "example"]
        sorted_scores = scorer.score_and_sort(words, reverse=True)

        # All long words (60.0) should come first
        assert sorted_scores[0][0] in ["testing", "example"]
        assert sorted_scores[0][1] == 60.0
        assert sorted_scores[1][0] in ["testing", "example"]
        assert sorted_scores[1][1] == 60.0
        # All short words (50.0) should come last
        assert sorted_scores[2][0] in ["test", "word"]
        assert sorted_scores[2][1] == 50.0
        assert sorted_scores[3][0] in ["test", "word"]
        assert sorted_scores[3][1] == 50.0

    def test_score_and_sort_ascending(self):
        """Test scoring and sorting in ascending order."""
        scorer = ConfidenceScorer()

        words = ["test", "testing"]
        sorted_scores = scorer.score_and_sort(words, reverse=False)

        assert sorted_scores[0] == ("test", 50.0)
        assert sorted_scores[1] == ("testing", 60.0)

    def test_score_and_sort_with_rejection(self):
        """Test sorting with rejection penalties."""
        def checker(word: str) -> bool:
            return word.lower() == "bad"

        scorer = ConfidenceScorer(rejection_checker=checker)

        words = ["good", "bad", "testing"]
        sorted_scores = scorer.score_and_sort(words)

        # Order: testing (60), good (50), bad (20)
        assert sorted_scores[0] == ("testing", 60.0)
        assert sorted_scores[1] == ("good", 50.0)
        assert sorted_scores[2] == ("bad", 20.0)

    # ===== filter_by_confidence tests =====

    def test_filter_by_confidence_basic(self):
        """Test filtering words by minimum confidence."""
        scorer = ConfidenceScorer()

        words = ["test", "testing", "word", "example"]
        filtered = scorer.filter_by_confidence(words, min_confidence=55.0)

        # Only words with 60.0 score
        assert set(filtered) == {"testing", "example"}

    def test_filter_by_confidence_all_pass(self):
        """Test filtering with low threshold (all pass)."""
        scorer = ConfidenceScorer()

        words = ["test", "testing", "word"]
        filtered = scorer.filter_by_confidence(words, min_confidence=40.0)

        assert set(filtered) == set(words)

    def test_filter_by_confidence_none_pass(self):
        """Test filtering with high threshold (none pass)."""
        scorer = ConfidenceScorer()

        words = ["test", "word"]
        filtered = scorer.filter_by_confidence(words, min_confidence=70.0)

        assert filtered == []

    def test_filter_by_confidence_exact_threshold(self):
        """Test filtering with exact threshold match."""
        scorer = ConfidenceScorer()

        words = ["test", "testing"]
        filtered = scorer.filter_by_confidence(words, min_confidence=50.0)

        # Both should pass (50.0 >= 50.0, 60.0 >= 50.0)
        assert set(filtered) == set(words)

    def test_filter_by_confidence_validates_type(self):
        """Test that invalid input types are rejected."""
        scorer = ConfidenceScorer()

        with pytest.raises(TypeError, match="must be a list"):
            scorer.filter_by_confidence("not a list", 50.0)

        with pytest.raises(TypeError, match="must be a number"):
            scorer.filter_by_confidence(["test"], "not a number")

    def test_filter_by_confidence_validates_range(self):
        """Test that out-of-range confidence is rejected."""
        scorer = ConfidenceScorer()

        with pytest.raises(ValueError, match="between 0.0 and 100.0"):
            scorer.filter_by_confidence(["test"], -10.0)

        with pytest.raises(ValueError, match="between 0.0 and 100.0"):
            scorer.filter_by_confidence(["test"], 150.0)

    # ===== Constants tests =====

    def test_constants(self):
        """Test that class constants have expected values."""
        assert ConfidenceScorer.CONFIDENCE_BASE == 50.0
        assert ConfidenceScorer.CONFIDENCE_LENGTH_BONUS == 10.0
        assert ConfidenceScorer.CONFIDENCE_REJECTION_PENALTY == 30.0
        assert ConfidenceScorer.LENGTH_BONUS_THRESHOLD == 6

    # ===== Integration tests =====

    def test_full_workflow_no_rejection(self):
        """Test complete workflow without rejection checking."""
        scorer = create_confidence_scorer()

        words = ["test", "word", "testing", "example", "great"]

        # Score all words
        scores = scorer.score_words(words)
        assert len(scores) == 5

        # Sort by confidence
        sorted_words = scorer.score_and_sort(words)
        assert sorted_words[0][1] >= sorted_words[-1][1]

        # Filter high confidence
        high_conf = scorer.filter_by_confidence(words, min_confidence=55.0)
        assert all(len(w) >= 6 for w in high_conf)

    def test_full_workflow_with_rejection(self):
        """Test complete workflow with rejection checking."""
        rejected_words = {"bad", "ugly", "hate"}

        def checker(word: str) -> bool:
            return word.lower() in rejected_words

        scorer = create_confidence_scorer(rejection_checker=checker)

        words = ["good", "bad", "testing", "ugly", "example"]

        # Score with rejection
        scores = scorer.score_words(words)
        assert scores["bad"] < scores["good"]
        assert scores["ugly"] < scores["testing"]

        # Filter removes low confidence rejected words
        filtered = scorer.filter_by_confidence(words, min_confidence=30.0)
        assert "bad" not in filtered  # Would be 20.0
        assert "ugly" not in filtered  # Would be 20.0
        assert "good" in filtered

    def test_real_world_scenario(self):
        """Test with realistic puzzle scenario."""
        # Simulate NYT rejection checker
        nyt_rejected = {"xxx", "zzz", "awkward"}

        def nyt_checker(word: str) -> bool:
            return word.lower() in nyt_rejected

        scorer = create_confidence_scorer(rejection_checker=nyt_checker)

        # Candidate words from a puzzle
        candidates = [
            "test",      # 4 letters, not rejected -> 50.0
            "tests",     # 5 letters, not rejected -> 50.0
            "tested",    # 6 letters, not rejected -> 60.0
            "testing",   # 7 letters, not rejected -> 60.0
            "awkward",   # 7 letters, REJECTED -> 30.0
        ]

        # Get high-confidence words only
        high_conf = scorer.filter_by_confidence(candidates, min_confidence=40.0)

        assert "test" in high_conf
        assert "tests" in high_conf
        assert "tested" in high_conf
        assert "testing" in high_conf
        assert "awkward" not in high_conf  # Rejected, too low confidence

        # Sort by confidence
        sorted_results = scorer.score_and_sort(candidates)

        # Top results should be long, non-rejected words
        assert sorted_results[0][0] in ["tested", "testing"]
        assert sorted_results[0][1] == 60.0

        # Lowest should be rejected word
        assert sorted_results[-1][0] == "awkward"
        assert sorted_results[-1][1] == 30.0

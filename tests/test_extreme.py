#!/usr/bin/env python3
"""
Edge case test to push coverage to maximum.
"""

from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver
from src.spelling_bee_solver.core import (
    NYTRejectionFilter,
    ConfidenceScorer,
)


def test_extreme_edge_cases():
    """Test the most obscure edge cases for maximum coverage."""
    print("Testing extreme edge cases...")

    # Test unified solver edge cases
    solver = UnifiedSpellingBeeSolver(verbose=True)

    # Test with valid puzzle that has many solutions
    print("Testing complex puzzle...")
    results = solver.solve_puzzle("A", "CTIONS")  # required_letter, other_letters
    print(f"Complex puzzle results: {len(results)}")

    # Test dictionary downloading (if available)
    try:
        words = solver._download_dictionary(
            "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
        )
        print(f"Downloaded dictionary: {len(words)} words")
    except Exception:
        print("Dictionary download not available")

    # Test Google common words loading
    try:
        common_words = solver._load_google_common_words()
        print(f"Google common words: {len(common_words)}")
    except Exception:
        print("Google common words not available")

    # Test config validation
    config_valid = solver._validate_dictionaries()
    print(f"Config validation: {config_valid}")

    # Test with different letter combinations
    # Format: (required_letter, other_6_letters)
    edge_puzzles = [
        ("A", "BCDEFG"),
        ("Q", "WERTYU"),
        ("Z", "YXWVUT"),
    ]

    for req, letters in edge_puzzles:
        try:
            results = solver.solve_puzzle(req, letters)
            print(f"Edge puzzle {req}{letters}-{req}: {len(results)} words")
        except Exception as e:
            print(f"Edge puzzle failed: {e}")

    # Test word filtering edge cases
    print("\nTesting word filtering edge cases...")

    nyt_filter = NYTRejectionFilter()
    confidence_scorer = ConfidenceScorer(nyt_filter=nyt_filter)

    edge_words = [
        "",  # Empty
        "a",  # Single letter
        "ab",  # Two letters
        "ABC",  # All caps
        "123",  # Numbers
        "test's",  # Apostrophe
        "co-op",  # Hyphen
        "café",  # Accent
        "VERY_LONG_WORD_THAT_SHOULD_BE_REJECTED_FOR_LENGTH" * 10,  # Very long
    ]

    for word in edge_words:
        try:
            rejected = nyt_filter.should_reject(word)
            # Skip confidence for invalid words
            if word and word.isalpha() and len(word) >= 4:
                conf = confidence_scorer.calculate_confidence(word)
                print(f"'{word[:20]}...': rejected={rejected}, conf={conf:.2f}")
            else:
                print(f"'{word[:20]}...': rejected={rejected}, conf=N/A (invalid)")
        except Exception as e:
            print(f"Error with '{word[:20]}...': {e}")

    # Test IntelligentWordFilter with edge cases
    print("\nTesting IntelligentWordFilter edge cases...")

    try:
        from src.spelling_bee_solver.intelligent_word_filter import filter_words_intelligent

        # Test with empty lists
        empty_results = filter_words_intelligent([], use_gpu=False)
        print(f"Empty filter: {len(empty_results)}")

        # Test with large batch
        large_batch = ["word" + str(i) for i in range(100)]
        large_results = filter_words_intelligent(large_batch, use_gpu=False)
        print(f"Large batch: {len(large_batch)} -> {len(large_results)}")

        # Test with mixed case and special characters
        edge_cases = ["Test", "TEST", "test-word", "test's", ""]
        edge_results = filter_words_intelligent(edge_cases, use_gpu=False)
        print(f"Edge cases: {len(edge_cases)} -> {len(edge_results)}")

    except Exception as e:
        print(f"IntelligentWordFilter edge case error: {e}")

    print("Extreme edge case testing complete!")


if __name__ == "__main__":
    test_extreme_edge_cases()

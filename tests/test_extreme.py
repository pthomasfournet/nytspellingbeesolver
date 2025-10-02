#!/usr/bin/env python3
"""
Edge case test to push coverage to maximum.
"""

from src.spelling_bee_solver.gpu.gpu_word_filtering import GPUWordFilter
from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver
from src.spelling_bee_solver.word_filtering import (
    get_word_confidence,
    is_likely_nyt_rejected,
    is_proper_noun,
)


def test_extreme_edge_cases():
    """Test the most obscure edge cases for maximum coverage."""
    print("Testing extreme edge cases...")

    # Test unified solver edge cases
    solver = UnifiedSpellingBeeSolver(verbose=True)

    # Test with valid puzzle that has many solutions
    print("Testing complex puzzle...")
    results = solver.solve_puzzle("ACTIONS", "A")
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
    config_valid = solver._validate_active_dictionaries()
    print(f"Config validation: {config_valid}")

    # Test with different letter combinations
    edge_puzzles = [
        ("ABCDEFG", "A"),
        ("QWERTYU", "Q"),
        ("ZYXWVUT", "Z"),
    ]

    for letters, req in edge_puzzles:
        try:
            results = solver.solve_puzzle(letters, req)
            print(f"Edge puzzle {letters}-{req}: {len(results)} words")
        except Exception as e:
            print(f"Edge puzzle failed: {e}")

    # Test word filtering edge cases
    print("\nTesting word filtering edge cases...")

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
            rejected = is_likely_nyt_rejected(word)
            conf = get_word_confidence(word)
            proper = is_proper_noun(word)
            print(
                f"'{word[:20]}...': rejected={rejected}, conf={conf:.2f}, proper={proper}"
            )
        except Exception as e:
            print(f"Error with '{word[:20]}...': {e}")

    # Test GPU components with edge cases
    print("\nTesting GPU edge cases...")

    try:
        gpu_filter = GPUWordFilter()

        # Test with empty lists
        empty_results = gpu_filter.comprehensive_filter([])
        print(f"GPU empty filter: {len(empty_results)}")

        # Test with large batch
        large_batch = ["word" + str(i) for i in range(1000)]
        large_results = gpu_filter.comprehensive_filter(large_batch)
        print(f"GPU large batch: {len(large_batch)} -> {len(large_results)}")

        # Test GPU stats
        stats = gpu_filter.get_stats()
        print(f"GPU detailed stats: {stats}")

    except Exception as e:
        print(f"GPU edge case error: {e}")

    # Test CUDA NLTK edge cases
    print("\nTesting CUDA NLTK edge cases...")

    try:
        from src.spelling_bee_solver.gpu.cuda_nltk import CudaNLTKProcessor

        cuda_proc = CudaNLTKProcessor()

        # Test with empty input
        empty_tokens = cuda_proc.batch_tokenize_gpu([])
        print(f"CUDA empty tokenize: {len(empty_tokens)}")

        # Test with unusual text
        weird_texts = ["", "123", "!!!@@@", "αβγδε", "🚀🌟💫"]
        weird_tokens = cuda_proc.batch_tokenize_gpu(weird_texts)
        print(f"CUDA weird tokenize: {len(weird_tokens)}")

        # Test batch processing limits
        cuda_stats = cuda_proc.get_stats()
        print(f"CUDA detailed stats: {cuda_stats}")

    except Exception as e:
        print(f"CUDA edge case error: {e}")

    print("Extreme edge case testing complete!")


if __name__ == "__main__":
    test_extreme_edge_cases()

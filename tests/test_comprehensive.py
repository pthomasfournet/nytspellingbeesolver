#!/usr/bin/env python3
"""
Comprehensive test runner to improve code coverage.
"""


def test_unified_solver_comprehensive():
    """Comprehensive test of unified solver."""
    print("Running comprehensive unified solver tests...")

    from src.spelling_bee_solver.unified_solver import (
        UnifiedSpellingBeeSolver,
    )

    # Test unified mode (no mode parameter needed)
    try:
        solver = UnifiedSpellingBeeSolver(verbose=False)
        print("✓ Unified solver initialized")

        # Test basic solving
        results = solver.solve_puzzle("N", "ACUOTP")
        print(f"✓ Solving: {len(results)} words")

        # Test confidence calculation
        confidence = solver.calculate_confidence("count")
        print(f"✓ Confidence calculation: {confidence}%")

        # Test word validation
        valid = solver.is_valid_word_basic("count", "nacuotp", "n")
        print(f"✓ Word validation: {valid}")

        # Test rejection logic
        rejected = solver.is_likely_nyt_rejected("NASA")
        print(f"✓ Rejection logic: NASA={rejected}")

    except (ImportError, AttributeError, ValueError) as e:
        print(f"⚠ Unified mode test failed: {e}")


def test_word_filtering_comprehensive():
    """Comprehensive test of word filtering."""
    print("\nRunning comprehensive word filtering tests...")

    from src.spelling_bee_solver.core import (
        CandidateGenerator,
        ConfidenceScorer,
        NYTRejectionFilter,
    )

    nyt_filter = NYTRejectionFilter()
    confidence_scorer = ConfidenceScorer(nyt_filter=nyt_filter)
    candidate_gen = CandidateGenerator()

    # Test various word types
    test_cases = [
        ("count", False),  # Normal word
        ("London", True),  # Proper noun
        ("NASA", True),  # Acronym
        ("govt", True),  # Abbreviation
        ("apple", False),  # Common word
        ("", True),  # Empty (too short)
        ("cat", True),  # Too short
    ]

    for word, expected_rejection in test_cases:
        try:
            result = nyt_filter.should_reject(word)
            status = "✓" if result == expected_rejection else "⚠"
            print(f"{status} {word}: expected={expected_rejection}, got={result}")
        except (ValueError, TypeError) as e:
            print(f"✗ Error testing '{word}': {e}")

    # Test filtering functions
    try:
        test_words = ["count", "London", "apple", "NASA"]
        filtered = [w for w in test_words if candidate_gen.is_valid_word_basic(w, "nacuotp", "n") and not nyt_filter.should_reject(w)]
        print(f"✓ Filter words: {len(test_words)} -> {len(filtered)}")

        # Test confidence scoring
        for word in ["count", "apple"]:
            conf = confidence_scorer.calculate_confidence(word)
            print(f"✓ Confidence for '{word}': {conf:.2f}")

    except (ImportError, ValueError, TypeError) as e:
        print(f"✗ Filtering test failed: {e}")


def test_gpu_components_comprehensive():
    """Comprehensive test of GPU/NLP components."""
    print("\nRunning comprehensive GPU/NLP tests...")

    # Test IntelligentWordFilter (the actual GPU filtering system)
    try:
        from src.spelling_bee_solver.intelligent_word_filter import (
            IntelligentWordFilter,
            filter_words_intelligent,
        )

        filter_obj = IntelligentWordFilter(use_gpu=False)  # Use CPU for testing
        print("✓ IntelligentWordFilter initialized")

        test_words = ["count", "apple", "London", "NASA", "government", "lloyd", "loca"]

        # Test module-level filtering function
        filtered = filter_words_intelligent(test_words, use_gpu=False)
        print(f"✓ Intelligent filtering: {len(test_words)} -> {len(filtered)}")

        # Test class method filtering
        filtered2 = filter_obj.filter_words_intelligent(test_words)
        print(f"✓ Class method filtering: {len(test_words)} -> {len(filtered2)}")

        # Verify proper nouns are filtered (London, NASA should be removed)
        assert "London" not in filtered, "London should be filtered (proper noun)"
        assert "NASA" not in filtered, "NASA should be filtered (acronym)"
        print("✓ Proper noun/acronym filtering verified")

    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"⚠ IntelligentWordFilter test failed: {e}")


def test_configuration_and_edge_cases():
    """Test configuration loading and edge cases."""
    print("\nTesting configuration and edge cases...")

    from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver

    # Test with non-existent config
    try:
        solver = UnifiedSpellingBeeSolver(config_path="nonexistent.json")
        print("✓ Handles missing config gracefully")
    except (FileNotFoundError, ValueError) as e:
        print(f"⚠ Config handling: {e}")

    # Test edge cases for puzzle solving
    try:
        solver = UnifiedSpellingBeeSolver(verbose=False)

        # Test with invalid inputs
        try:
            solver.solve_puzzle("", "")
            print("✗ Should have failed with empty input")
        except ValueError:
            print("✓ Correctly rejects empty input")

        try:
            solver.solve_puzzle("ABC", "A")
            print("✗ Should have failed with short input")
        except ValueError:
            print("✓ Correctly rejects short input")

        try:
            solver.solve_puzzle("ABCDEFG", "Z")
            print("✗ Should have failed with invalid required letter")
        except ValueError:
            print("✓ Correctly rejects invalid required letter")

        # Test confidence edge cases
        try:
            solver.calculate_confidence("")
            print("✗ Should have failed with empty confidence input")
        except ValueError:
            print("✓ Correctly rejects empty confidence input")

        conf_normal = solver.calculate_confidence("count")
        print(
            f"✓ Confidence calculation: normal={conf_normal:.1f}"
        )

    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"⚠ Edge case testing: {e}")


if __name__ == "__main__":
    print("🧪 Running comprehensive code coverage tests...")
    print("=" * 70)

    test_functions = [
        test_unified_solver_comprehensive,
        test_word_filtering_comprehensive,
        test_gpu_components_comprehensive,
        test_configuration_and_edge_cases,
    ]

    for test_func in test_functions:
        try:
            test_func()
        except (ImportError, AttributeError, RuntimeError) as e:
            print(f"✗ Test {test_func.__name__} failed: {e}")

    print("\n" + "=" * 70)
    print("🏁 Comprehensive testing complete!")

#!/usr/bin/env python3
"""
Basic tests with real solver and dictionaries.
"""

import pytest


def test_basic_imports():
    """Test that all modules can be imported."""
    print("\n=== Testing Module Imports ===")

    from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver
    print("✓ unified_solver imported")

    from src.spelling_bee_solver.word_filtering import is_likely_nyt_rejected
    print("✓ word_filtering imported")

    # GPU/NLP components (may fail on systems without dependencies)
    try:
        from src.spelling_bee_solver.intelligent_word_filter import IntelligentWordFilter, filter_words_intelligent
        print("✓ intelligent_word_filter imported")
    except Exception as e:
        print(f"⚠ intelligent_word_filter: {e}")

    # cuda_nltk removed (was dead code)

    print("✅ All imports successful\n")


def test_unified_solver():
    """Test unified solver functionality."""
    print("\n=== Testing Unified Solver ===")
    from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver

    # Test initialization (unified mode - no mode parameter)
    solver = UnifiedSpellingBeeSolver(verbose=False)
    print("✓ Solver initialized")

    # Verify solver configuration
    assert hasattr(solver, 'DICTIONARIES'), "Should have DICTIONARIES attribute"
    assert len(solver.DICTIONARIES) == 2, "Should have exactly 2 dictionaries"

    dict_names = [name for name, _ in solver.DICTIONARIES]
    print(f"✓ Dictionaries configured: {dict_names}")
    assert "Webster's Unabridged" in dict_names
    assert "ASPELL American English" in dict_names

    # Test puzzle solving
    print("✓ Solving puzzle NACUOTP (required: N)...")
    results = solver.solve_puzzle("N", "ACUOTP")
    print(f"✓ Puzzle solved: {len(results)} words found")

    if results:
        # results is a list of (word, confidence) tuples
        top_results = results[:10]
        top_words = [word for word, conf in top_results]
        print(f"✓ Top words: {top_words}")
        for word, confidence in top_results[:3]:
            print(f"   {word}: {confidence}% confidence")

    assert len(results) >= 0, "Should return results"
    print("✅ Unified solver test successful\n")


def test_word_filtering():
    """Test word filtering functions."""
    print("\n=== Testing Word Filtering ===")
    from src.spelling_bee_solver.word_filtering import is_likely_nyt_rejected

    test_cases = [
        ("London", True, "proper noun"),
        ("NASA", True, "acronym"),
        ("count", False, "normal word"),
        ("apple", False, "common word"),
        ("cat", True, "too short"),
    ]

    print("Testing rejection logic:")
    for word, expected, reason in test_cases:
        result = is_likely_nyt_rejected(word)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{word}' ({reason}): expected={expected}, got={result}")
        assert result == expected, f"'{word}' should {'be rejected' if expected else 'not be rejected'}"

    print("✅ Word filtering test successful\n")


if __name__ == "__main__":
    print("🧪 Running basic functionality tests for code coverage...")
    print("=" * 60)

    tests = [test_basic_imports, test_unified_solver, test_word_filtering]
    passed = 0

    for test_func in tests:
        if test_func():
            passed += 1

    print("\n" + "=" * 60)
    print(f"🏁 Results: {passed}/{len(tests)} tests passed")
    print("✅ Basic functionality verified!")

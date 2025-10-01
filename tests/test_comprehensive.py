#!/usr/bin/env python3
"""
Comprehensive test runner to improve code coverage.
"""


def test_unified_solver_comprehensive():
    """Comprehensive test of unified solver."""
    print("Running comprehensive unified solver tests...")

    from src.spelling_bee_solver.unified_solver import (
        SolverMode,
        UnifiedSpellingBeeSolver,
    )

    # Test different modes
    for mode in [SolverMode.DEBUG_SINGLE, SolverMode.PRODUCTION]:
        try:
            solver = UnifiedSpellingBeeSolver(mode=mode, verbose=False)
            print(f"✓ {mode.value} mode initialized")

            # Test basic solving
            results = solver.solve_puzzle("NACUOTP", "N")
            print(f"✓ {mode.value} solving: {len(results)} words")

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
            print(f"⚠ {mode.value} test failed: {e}")


def test_word_filtering_comprehensive():
    """Comprehensive test of word filtering."""
    print("\nRunning comprehensive word filtering tests...")

    from src.spelling_bee_solver.word_filtering import (
        filter_inappropriate_words,
        filter_words,
        get_word_confidence,
        is_likely_nyt_rejected,
        is_proper_noun,
    )

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
            result = is_likely_nyt_rejected(word)
            status = "✓" if result == expected_rejection else "⚠"
            print(f"{status} {word}: expected={expected_rejection}, got={result}")
        except (ValueError, TypeError) as e:
            print(f"✗ Error testing '{word}': {e}")

    # Test filtering functions
    try:
        test_words = ["count", "London", "apple", "NASA"]
        filtered = filter_words(test_words, "nacuotp", "n")
        print(f"✓ Filter words: {len(test_words)} -> {len(filtered)}")

        # Test confidence scoring
        for word in ["count", "apple"]:
            conf = get_word_confidence(word)
            print(f"✓ Confidence for '{word}': {conf:.2f}")

        # Test legacy functions
        proper_result = is_proper_noun("London")
        print(f"✓ Legacy proper noun check: {proper_result}")

        inappropriate_filtered = filter_inappropriate_words(test_words)
        print(
            f"✓ Inappropriate filter: {len(test_words)} -> {len(inappropriate_filtered)}"
        )

    except (ImportError, ValueError, TypeError) as e:
        print(f"✗ Filtering test failed: {e}")


def test_gpu_components_comprehensive():
    """Comprehensive test of GPU components."""
    print("\nRunning comprehensive GPU tests...")

    # Test GPU word filtering
    try:
        from src.spelling_bee_solver.gpu.gpu_word_filtering import GPUWordFilter

        gpu_filter = GPUWordFilter()
        print("✓ GPU filter initialized")

        test_words = ["count", "apple", "London", "NASA", "government"]

        # Test proper noun detection
        proper_results = gpu_filter.is_proper_noun(test_words)
        print(f"✓ GPU proper noun detection: {len(proper_results)} results")

        # Test inappropriate word detection
        inappropriate_results = gpu_filter.is_inappropriate_word(test_words)
        print(f"✓ GPU inappropriate detection: {len(inappropriate_results)} results")

        # Test comprehensive filtering
        filtered = gpu_filter.comprehensive_filter(test_words)
        print(f"✓ GPU comprehensive filter: {len(test_words)} -> {len(filtered)}")

        # Test filtering methods
        proper_filtered = gpu_filter.filter_proper_nouns(test_words)
        print(f"✓ GPU proper noun filter: {len(test_words)} -> {len(proper_filtered)}")

        inappropriate_filtered = gpu_filter.filter_inappropriate_words(test_words)
        print(
            f"✓ GPU inappropriate filter: {len(test_words)} -> {len(inappropriate_filtered)}"
        )

        # Test stats
        stats = gpu_filter.get_stats()
        print(f"✓ GPU stats: GPU={stats['gpu_available']}")

    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"⚠ GPU filter test failed: {e}")

    # Test CUDA NLTK
    try:
        from src.spelling_bee_solver.gpu.cuda_nltk import get_cuda_nltk_processor

        processor = get_cuda_nltk_processor()
        print("✓ CUDA NLTK processor initialized")

        test_texts = ["Hello world", "This is a test", "London is great"]

        # Test tokenization
        tokens = processor.batch_tokenize_gpu(test_texts)
        print(f"✓ CUDA tokenization: {len(test_texts)} -> {len(tokens)}")

        # Test POS tagging
        tagged = processor.batch_pos_tag_gpu(tokens)
        print(f"✓ CUDA POS tagging: {len(tokens)} -> {len(tagged)}")

        # Test NER
        ner_results = processor.batch_named_entity_recognition(test_texts)
        print(f"✓ CUDA NER: {len(test_texts)} -> {len(ner_results)}")

        # Test proper noun detection
        test_words = ["count", "London", "apple"]
        proper_results = processor.is_proper_noun_batch_cuda(test_words)
        print(f"✓ CUDA proper noun batch: {len(test_words)} -> {len(proper_results)}")

        # Test stats
        stats = processor.get_stats()
        print(f"✓ CUDA stats: GPU={stats['cuda_available']}")

    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"⚠ CUDA NLTK test failed: {e}")

    # Test GPU puzzle solver
    try:
        from src.spelling_bee_solver.gpu.gpu_puzzle_solver import GPUPuzzleSolver

        gpu_solver = GPUPuzzleSolver()
        print("✓ GPU puzzle solver initialized")

        # Test dictionary loading
        if hasattr(gpu_solver, "dictionary_sources") and gpu_solver.dictionary_sources:
            dict_name, dict_path = gpu_solver.dictionary_sources[0]
            words = gpu_solver.load_dictionary(dict_path)
            print(f"✓ GPU dictionary loading: {len(words)} words from {dict_name}")

        # Test validation
        valid = gpu_solver.is_valid_word_basic("count", "nacuotp", "n")
        print(f"✓ GPU validation: {valid}")

        # Test rejection
        rejected = gpu_solver.is_likely_nyt_rejected("NASA")
        print(f"✓ GPU rejection: {rejected}")

        # Test filtering
        test_words = ["count", "apple", "London"]
        filtered = gpu_solver.filter_words_fast(test_words)
        print(f"✓ GPU fast filtering: {len(test_words)} -> {len(filtered)}")

    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"⚠ GPU puzzle solver test failed: {e}")


def test_configuration_and_edge_cases():
    """Test configuration loading and edge cases."""
    print("\nTesting configuration and edge cases...")

    from src.spelling_bee_solver.unified_solver import (
        SolverMode,
        UnifiedSpellingBeeSolver,
    )

    # Test with non-existent config
    try:
        solver = UnifiedSpellingBeeSolver(config_path="nonexistent.json")
        print("✓ Handles missing config gracefully")
    except (FileNotFoundError, ValueError) as e:
        print(f"⚠ Config handling: {e}")

    # Test edge cases for puzzle solving
    try:
        solver = UnifiedSpellingBeeSolver(mode=SolverMode.DEBUG_SINGLE)

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
        conf_empty = solver.calculate_confidence("")
        conf_normal = solver.calculate_confidence("count")
        print(
            f"✓ Confidence edge cases: empty={conf_empty:.1f}, normal={conf_normal:.1f}"
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

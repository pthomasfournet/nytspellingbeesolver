"""
Tests for Singleton Pattern Fix - Thread Safety and Factory Pattern

This test suite verifies that the refactored word filter implementation:
1. Is thread-safe (no race conditions)
2. Allows multiple independent instances
3. Maintains backward compatibility
4. Shows deprecation warnings appropriately
"""

import threading
import warnings

import pytest

from src.spelling_bee_solver.intelligent_word_filter import (
    IntelligentWordFilter,
    create_word_filter,
    get_filter_instance,
)


def test_create_word_filter_returns_new_instances():
    """Test that create_word_filter() returns independent instances"""
    filter1 = create_word_filter(use_gpu=False)
    filter2 = create_word_filter(use_gpu=False)

    assert filter1 is not filter2, "Should create independent instances"
    assert isinstance(filter1, IntelligentWordFilter)
    assert isinstance(filter2, IntelligentWordFilter)


def test_thread_safety_multiple_instances():
    """Test that multiple threads can create filters safely without race conditions"""
    filters = []
    errors = []

    def create_filter():
        try:
            f = create_word_filter(use_gpu=False)
            filters.append(f)
        except Exception as e:
            errors.append(e)

    # Create 10 threads that all try to create filters simultaneously
    threads = [threading.Thread(target=create_filter) for _ in range(10)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Verify results
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(filters) == 10, f"Expected 10 filters, got {len(filters)}"
    assert all(f is not None for f in filters), "All filters should be valid"
    assert all(isinstance(f, IntelligentWordFilter) for f in filters), "All should be IntelligentWordFilter instances"

    # Verify all instances are independent (not the same object)
    unique_ids = len(set(id(f) for f in filters))
    assert unique_ids == 10, f"Expected 10 unique instances, got {unique_ids}"


def test_get_filter_instance_shows_deprecation_warning():
    """Test that get_filter_instance() shows a deprecation warning"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        filter_instance = get_filter_instance(use_gpu=False)

        # Check that a warning was raised
        assert len(w) >= 1, "Expected deprecation warning"

        # Find the deprecation warning
        deprecation_warnings = [warning for warning in w if issubclass(warning.category, DeprecationWarning)]
        assert len(deprecation_warnings) >= 1, "Expected DeprecationWarning"

        # Check the warning message
        warning_msg = str(deprecation_warnings[0].message)
        assert "deprecated" in warning_msg.lower(), f"Warning should mention deprecation: {warning_msg}"
        assert "create_word_filter" in warning_msg, f"Warning should suggest create_word_filter: {warning_msg}"


def test_get_filter_instance_returns_new_instance():
    """Test that get_filter_instance() now returns new instances (not singleton)"""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # Suppress deprecation warnings for this test

        filter1 = get_filter_instance(use_gpu=False)
        filter2 = get_filter_instance(use_gpu=False)

        # Should NOT be the same instance (no longer a singleton)
        assert filter1 is not filter2, "Should create new instances, not singleton"


def test_multiple_configurations_coexist():
    """Test that different filter configurations can coexist independently"""
    # Note: use_gpu parameter doesn't create truly different configs in current impl,
    # but this tests the pattern
    filter_gpu = create_word_filter(use_gpu=True)
    filter_cpu = create_word_filter(use_gpu=False)

    assert filter_gpu is not filter_cpu, "Different configs should be different instances"
    assert isinstance(filter_gpu, IntelligentWordFilter)
    assert isinstance(filter_cpu, IntelligentWordFilter)


def test_backward_compatibility_filter_works():
    """Test that the refactored filter still works correctly"""
    filter_instance = create_word_filter(use_gpu=False)

    # Test basic filtering
    test_words = ["hello", "world", "NASA", "test"]
    results = filter_instance.filter_words_intelligent(test_words)

    assert isinstance(results, list), "Should return a list"
    assert all(isinstance(w, str) for w in results), "All results should be strings"

    # Basic sanity check - "NASA" should be filtered out as acronym
    assert "NASA" not in results, "Acronym should be filtered"
    assert "hello" in results or "world" in results or "test" in results, "Some common words should pass"


def test_thread_safety_concurrent_filtering():
    """Test that multiple threads can use filter instances concurrently"""
    results_dict = {}
    errors = []

    def filter_words():
        try:
            filter_instance = create_word_filter(use_gpu=False)
            thread_id = threading.current_thread().ident

            test_words = ["hello", "world", "test", "NASA", "apple"]
            filtered = filter_instance.filter_words_intelligent(test_words)

            results_dict[thread_id] = filtered
        except Exception as e:
            errors.append(e)

    # Run filtering in multiple threads
    threads = [threading.Thread(target=filter_words) for _ in range(5)]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    # Verify results
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results_dict) == 5, f"Expected 5 results, got {len(results_dict)}"

    # All threads should get similar results (filtering is deterministic)
    results_list = list(results_dict.values())
    first_result = set(results_list[0])
    for result in results_list[1:]:
        assert set(result) == first_result, "All threads should get consistent filtering results"


if __name__ == "__main__":
    print("Running singleton fix tests...")
    pytest.main([__file__, "-v"])

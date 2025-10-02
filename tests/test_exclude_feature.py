"""
Tests for the exclude known words feature.

Tests the ability to exclude already-found words from solver results.
"""

import tempfile
from pathlib import Path

import pytest

from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver


def test_exclude_words_parameter():
    """Test that exclude_words parameter filters results correctly."""
    solver = UnifiedSpellingBeeSolver(verbose=False)

    # Solve without exclusions
    all_results = solver.solve_puzzle("N", "ACUOTP")
    all_words = {word for word, _ in all_results}

    # Solve with exclusions
    exclude_set = {"count", "upon", "coat"}
    filtered_results = solver.solve_puzzle("N", "ACUOTP", exclude_words=exclude_set)
    filtered_words = {word for word, _ in filtered_results}

    # Verify excluded words are not in results
    assert "count" not in filtered_words
    assert "upon" not in filtered_words
    assert "coat" not in filtered_words

    # Verify excluded words were in original results
    assert "count" in all_words or "upon" in all_words  # At least one should be valid

    # Verify some words are still returned
    assert len(filtered_results) > 0
    assert len(filtered_results) < len(all_results)


def test_exclude_words_stats():
    """Test that exclusion stats are tracked correctly."""
    solver = UnifiedSpellingBeeSolver(verbose=False)

    exclude_set = {"count", "upon"}
    results = solver.solve_puzzle("N", "ACUOTP", exclude_words=exclude_set)

    # Check stats were recorded
    assert "excluded_count" in solver.stats
    assert "excluded_words" in solver.stats

    # Verify stats accuracy
    assert solver.stats["excluded_count"] >= 0
    assert isinstance(solver.stats["excluded_words"], list)


def test_exclude_invalid_words():
    """Test that invalid excluded words are handled gracefully."""
    solver = UnifiedSpellingBeeSolver(verbose=False)

    # Try to exclude words that don't exist
    exclude_set = {"invalidword123", "notarealword", "zzzzzzz"}
    results = solver.solve_puzzle("N", "ACUOTP", exclude_words=exclude_set)

    # Should not crash, just ignore invalid words
    assert len(results) > 0


def test_exclude_all_words():
    """Test excluding all valid words returns empty results."""
    solver = UnifiedSpellingBeeSolver(verbose=False)

    # Get all words first
    all_results = solver.solve_puzzle("N", "ACUOTP")
    all_words = {word for word, _ in all_results}

    # Exclude all of them
    filtered_results = solver.solve_puzzle("N", "ACUOTP", exclude_words=all_words)

    # Should return empty results
    assert len(filtered_results) == 0


def test_exclude_case_insensitive():
    """Test that word exclusion is case-insensitive."""
    solver = UnifiedSpellingBeeSolver(verbose=False)

    # Try excluding with different cases
    exclude_set = {"COUNT", "Upon", "CoAt"}
    results = solver.solve_puzzle("N", "ACUOTP", exclude_words=exclude_set)
    result_words = {word.lower() for word, _ in results}

    # Should exclude regardless of case
    assert "count" not in result_words
    assert "upon" not in result_words
    assert "coat" not in result_words


def test_exclude_with_whitespace():
    """Test that whitespace in excluded words is handled."""
    solver = UnifiedSpellingBeeSolver(verbose=False)

    # Include words with whitespace
    exclude_set = {" count ", "upon\t", "\ncoat"}
    results = solver.solve_puzzle("N", "ACUOTP", exclude_words=exclude_set)
    result_words = {word for word, _ in results}

    # Should still exclude after stripping
    assert "count" not in result_words
    assert "upon" not in result_words
    assert "coat" not in result_words


def test_exclude_empty_set():
    """Test that empty exclude set doesn't affect results."""
    solver = UnifiedSpellingBeeSolver(verbose=False)

    normal_results = solver.solve_puzzle("N", "ACUOTP")
    empty_exclude_results = solver.solve_puzzle("N", "ACUOTP", exclude_words=set())

    # Should be identical
    assert len(normal_results) == len(empty_exclude_results)


def test_exclude_none():
    """Test that None exclude_words works (backward compatibility)."""
    solver = UnifiedSpellingBeeSolver(verbose=False)

    results = solver.solve_puzzle("N", "ACUOTP", exclude_words=None)

    # Should work normally
    assert len(results) > 0
    assert all(isinstance(word, str) and isinstance(conf, (int, float))
               for word, conf in results)


def test_cli_exclude_file(tmp_path):
    """Test CLI --exclude-file option (integration test)."""
    import subprocess
    import sys

    # Create temp file with known words
    exclude_file = tmp_path / "found.txt"
    exclude_file.write_text("count\nupon\ncoat\n")

    # Run solver with exclude file
    result = subprocess.run(
        [sys.executable, "-m", "src.spelling_bee_solver", "N", "ACUOTP",
         "--exclude-file", str(exclude_file)],
        capture_output=True,
        text=True,
        timeout=30
    )

    # Verify it ran successfully
    assert result.returncode == 0
    # Check for exclusion stats (words appear in stats line)
    assert "Excluded:" in result.stdout
    assert "count" in result.stdout and "upon" in result.stdout  # In stats line
    # Verify words list sections don't contain excluded words as separate entries
    lines = result.stdout.split('\n')
    word_lines = [l for l in lines if '(' in l and '%' in l]  # Lines with confidence %
    # "count" and "upon" should not appear as standalone words (allow in "account", "accountant")
    assert not any(line.strip().startswith("count ") or " count " in line for line in word_lines)
    assert not any(line.strip().startswith("upon ") or " upon " in line for line in word_lines)


def test_cli_exclude_comma_separated():
    """Test CLI --exclude with comma-separated words (integration test)."""
    import subprocess
    import sys

    # Run solver with comma-separated exclude
    result = subprocess.run(
        [sys.executable, "-m", "src.spelling_bee_solver", "N", "ACUOTP",
         "--exclude", "count,upon"],
        capture_output=True,
        text=True,
        timeout=30
    )

    # Verify it ran successfully
    assert result.returncode == 0
    # Check exclusion happened
    assert "Excluded: 2 words" in result.stdout
    assert "count, upon" in result.stdout  # In stats line
    # Verify excluded words aren't in the word lists
    lines = result.stdout.split('\n')
    word_lines = [l for l in lines if '(' in l and '%' in l]
    assert not any(line.strip().startswith("count ") or " count " in line for line in word_lines)
    assert not any(line.strip().startswith("upon ") or " upon " in line for line in word_lines)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Comprehensive tests for Wiktionary Layer 4 smart filter system.

Tests cover:
1. WiktionaryMetadata loader unit tests
2. NYTRejectionFilter Layer 4 integration
3. Random puzzle validation
"""

import json
import random
from pathlib import Path

import pytest

from src.spelling_bee_solver.core.nyt_rejection_filter import NYTRejectionFilter
from src.spelling_bee_solver.core.wiktionary_metadata import load_wiktionary_metadata
from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver


class TestWiktionaryMetadata:
    """Unit tests for WiktionaryMetadata loader."""

    def test_loads_successfully(self):
        """Test that Wiktionary metadata loads without errors."""
        metadata = load_wiktionary_metadata()
        assert metadata.loaded is True
        assert len(metadata.obsolete_words) > 0
        assert len(metadata.proper_nouns) > 0

    def test_obsolete_detection(self):
        """Test obsolete word detection."""
        metadata = load_wiktionary_metadata()

        # Should detect obsolete words
        assert metadata.is_obsolete("taglia") is True
        assert metadata.is_obsolete("whilst") is True

        # Should not flag normal words
        assert metadata.is_obsolete("account") is False
        assert metadata.is_obsolete("normal") is False

    def test_archaic_detection(self):
        """Test archaic word detection."""
        metadata = load_wiktionary_metadata()

        # Should detect archaic words
        assert metadata.is_archaic("hath") is True
        assert metadata.is_archaic("doth") is True
        assert metadata.is_archaic("thee") is True

        # Should not flag normal words
        assert metadata.is_archaic("account") is False

    def test_rare_detection(self):
        """Test rare word detection."""
        metadata = load_wiktionary_metadata()

        # Should detect rare words
        assert metadata.is_rare("abstruse") is True

        # Should not flag normal words
        assert metadata.is_rare("account") is False

    def test_proper_noun_detection(self):
        """Test proper noun detection (capitalization handling)."""
        metadata = load_wiktionary_metadata()

        # Should detect proper nouns (checks capitalized version)
        assert metadata.is_proper_noun_wiktionary("atlanta") is True
        assert metadata.is_proper_noun_wiktionary("Tanzania") is True
        assert metadata.is_proper_noun_wiktionary("ATLANTA") is True  # Any case

        # Should not flag normal words
        assert metadata.is_proper_noun_wiktionary("account") is False
        assert metadata.is_proper_noun_wiktionary("normal") is False

    def test_multi_language_detection(self):
        """Test multi-language word detection."""
        metadata = load_wiktionary_metadata()

        # Should detect multi-language words
        assert metadata.is_multi_language("taglia") is True
        assert metadata.is_multi_language("gitana") is True

        # Should have language lists
        assert "Italian" in metadata.get_languages("taglia")
        assert len(metadata.get_languages("atlanta")) > 0

    def test_no_duplicates_in_data(self):
        """Test that there are no duplicate entries in proper nouns."""
        metadata = load_wiktionary_metadata()

        proper_nouns_list = list(metadata.proper_nouns)
        proper_nouns_set = set(metadata.proper_nouns)

        assert len(proper_nouns_list) == len(proper_nouns_set), \
            "Duplicates found in proper_nouns"

    def test_stats_accuracy(self):
        """Test that metadata stats match actual counts."""
        # Load raw JSON to check stats
        metadata_path = Path('src/spelling_bee_solver/data/wiktionary_metadata.json')
        with open(metadata_path, encoding='utf-8') as f:
            data = json.load(f)

        assert data['stats']['obsolete_count'] == len(data['obsolete'])
        assert data['stats']['archaic_count'] == len(data['archaic'])
        assert data['stats']['proper_noun_count'] == len(set(data['proper_nouns']))


class TestNYTRejectionFilterLayer4:
    """Integration tests for Layer 4 in NYTRejectionFilter."""

    def test_layer4_loads_in_filter(self):
        """Test that Layer 4 loads successfully in filter."""
        filter = NYTRejectionFilter(enable_wiktionary=True)

        assert filter.wiktionary is not None
        assert filter.wiktionary.loaded is True

    def test_obsolete_words_rejected(self):
        """Test that obsolete words are rejected via Layer 4."""
        filter = NYTRejectionFilter(enable_wiktionary=True)

        # Obsolete words should be rejected
        assert filter.should_reject("taglia") is True

        # Normal words should pass
        assert filter.should_reject("account") is False

    def test_proper_nouns_rejected_via_wiktionary(self):
        """Test that proper nouns are rejected via Wiktionary Layer 4."""
        filter = NYTRejectionFilter(enable_wiktionary=True)

        # Note: These may also be caught by manual list, but Layer 4 provides redundancy
        assert filter.should_reject("atlanta") is True
        assert filter.should_reject("tanzania") is True

    def test_archaic_flagged_not_rejected(self):
        """Test that archaic words are flagged but NOT rejected."""
        filter = NYTRejectionFilter(enable_wiktionary=True)

        # Archaic words should be flagged
        assert filter.is_archaic("hath") is True

        # But NOT rejected (scored with low confidence instead)
        assert filter.should_reject("hath") is False

    def test_graceful_degradation_when_disabled(self):
        """Test that filter works when Wiktionary disabled."""
        filter = NYTRejectionFilter(enable_wiktionary=False)

        # Should still work, just without Layer 4
        assert filter.wiktionary is None

        # Manual lists should still work
        assert filter.should_reject("lloyd") is True  # In manual list

    def test_redundancy_with_manual_lists(self):
        """Test that Layer 4 provides redundancy for manual lists."""
        filter = NYTRejectionFilter(enable_wiktionary=True)

        # Words in BOTH manual list and Wiktionary
        # (Should be caught by either Layer 1 or Layer 4)
        assert filter.should_reject("atlanta") is True

        # Even if we remove from manual list, Layer 4 catches it
        assert filter.wiktionary.is_proper_noun_wiktionary("atlanta") is True


class TestRandomPuzzles:
    """Test filtering on random puzzles from historical data."""

    @pytest.fixture
    def puzzles_dataset(self):
        """Load historical puzzles dataset."""
        with open('nytbee_parser/nyt_puzzles_dataset.json', encoding='utf-8') as f:
            data = json.load(f)
        # Filter to only valid puzzles (with center and letters)
        return [p for p in data if p['center'] and p['letters']]

    @pytest.fixture
    def random_puzzles(self, puzzles_dataset):
        """Get 5 random puzzles for testing."""
        random.seed(42)
        return random.sample(puzzles_dataset, 5)

    def test_random_puzzles_solver_works(self, random_puzzles):
        """Test that solver works on random puzzles."""
        solver = UnifiedSpellingBeeSolver()

        results_summary = []

        for puzzle in random_puzzles:
            center = puzzle['center']
            all_letters = puzzle['letters']

            # Extract outer letters (remove center from all_letters)
            outer_letters = all_letters.replace(center, '', 1)

            # Run solver (expects: required_letter + 6 outer letters)
            results = solver.solve_puzzle(center, outer_letters)

            results_summary.append({
                'date': puzzle['date'],
                'letters': f"{center}/{outer_letters}",
                'nyt_accepted': len(puzzle['accepted']),
                'nyt_rejected': len(puzzle['rejected']),
                'solver_found': len(results),
            })

        # Print results for analysis
        print("\n" + "="*70)
        print("RANDOM PUZZLE TESTING RESULTS")
        print("="*70)
        for r in results_summary:
            print(f"Date: {r['date']:12} {r['letters']:12} | "
                  f"NYT Accept: {r['nyt_accepted']:3} | "
                  f"NYT Reject: {r['nyt_rejected']:3} | "
                  f"Solver: {r['solver_found']:3}")
        print("="*70)

        # All puzzles should return results
        for r in results_summary:
            assert r['solver_found'] > 0, f"Solver found 0 words for {r['date']}"

    def test_wiktionary_layer4_impact(self, random_puzzles):
        """Test impact of Wiktionary Layer 4 on filtering."""
        # Solver with Wiktionary
        solver_with_layer4 = UnifiedSpellingBeeSolver()

        # This test validates that Layer 4 is active and working
        # by checking that obsolete/proper noun detection is functioning

        filter = solver_with_layer4.nyt_filter

        # Verify Layer 4 is loaded
        assert filter.wiktionary is not None
        assert filter.wiktionary.loaded is True

        # Test on first puzzle
        puzzle = random_puzzles[0]
        center = puzzle['center']
        all_letters = puzzle['letters']

        # Extract outer letters (remove center from all_letters)
        outer_letters = all_letters.replace(center, '', 1)

        results = solver_with_layer4.solve_puzzle(center, outer_letters)

        # Should have filtered some words
        assert len(results) > 0

        print(f"\nLayer 4 active on puzzle {puzzle['date']}: {len(results)} words found")


# Performance benchmarks
def test_wiktionary_load_performance():
    """Benchmark: Wiktionary metadata load time."""
    import time

    start = time.time()
    load_wiktionary_metadata()
    load_time = time.time() - start

    print(f"\nWiktionary load time: {load_time*1000:.1f}ms")

    # Should load in under 100ms
    assert load_time < 0.1, f"Load time too slow: {load_time*1000:.1f}ms"

def test_wiktionary_lookup_performance():
    """Benchmark: Wiktionary lookup speed."""
    import time

    metadata = load_wiktionary_metadata()

    # Test 1000 lookups
    test_words = ["account", "taglia", "atlanta", "hath", "normal"] * 200

    start = time.time()
    for word in test_words:
        metadata.is_obsolete(word)
        metadata.is_proper_noun_wiktionary(word)
        metadata.is_archaic(word)
    lookup_time = time.time() - start

    avg_time_us = (lookup_time / len(test_words)) * 1000000

    print(f"\n1000 lookups: {lookup_time*1000:.1f}ms")
    print(f"Average per lookup: {avg_time_us:.2f}μs")

    # Should be very fast (O(1) hash lookups)
    assert avg_time_us < 10, f"Lookup too slow: {avg_time_us:.2f}μs"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])

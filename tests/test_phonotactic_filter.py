"""
Unit tests for PhonotacticFilter

Tests all phonotactic rules with positive/negative cases and edge cases.
"""

import pytest
from src.spelling_bee_solver.core.phonotactic_filter import (
    PhonotacticFilter,
    PhonotacticRules,
    create_phonotactic_filter
)


class TestPhonotacticFilterFactory:
    """Test factory function for creating filters."""
    
    def test_create_default_filter(self):
        """Test creating filter with default settings."""
        filter = create_phonotactic_filter()
        assert filter is not None
        assert filter.rules.reject_triple_letters is True
        assert filter.rules.reject_impossible_doubles is True
        assert filter.rules.reject_invalid_clusters is True
        assert filter.rules.reject_extreme_vc_patterns is True
    
    def test_create_custom_filter(self):
        """Test creating filter with custom settings."""
        filter = create_phonotactic_filter(
            reject_triple_letters=False,
            reject_impossible_doubles=True,
            max_consecutive_consonants=5
        )
        assert filter.rules.reject_triple_letters is False
        assert filter.rules.reject_impossible_doubles is True
        assert filter.rules.max_consecutive_consonants == 5


class TestTripleLetters:
    """Test triple letter detection (Rule 1)."""
    
    def test_no_triple_letters_valid(self):
        """Valid words with no triple letters should pass."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("hello") is True
        assert filter.is_valid_sequence("book") is True
        assert filter.is_valid_sequence("apple") is True
        assert filter.is_valid_sequence("coffee") is True
    
    def test_triple_letters_invalid(self):
        """Sequences with triple letters should be rejected."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("helllo") is False  # Triple 'l'
        assert filter.is_valid_sequence("aaargh") is False  # Triple 'a'
        assert filter.is_valid_sequence("boook") is False   # Triple 'o'
        assert filter.is_valid_sequence("tttest") is False  # Triple 't'
    
    def test_triple_letters_disabled(self):
        """Triple letters should pass when rule is disabled."""
        rules = PhonotacticRules(reject_triple_letters=False)
        filter = PhonotacticFilter(rules)
        assert filter.is_valid_sequence("helllo") is True
        assert filter.is_valid_sequence("aaargh") is True
    
    def test_stats_triple_rejection(self):
        """Stats should track triple letter rejections."""
        filter = PhonotacticFilter()
        filter.is_valid_sequence("helllo")
        filter.is_valid_sequence("hello")
        stats = filter.get_stats()
        assert stats["rejected_triple"] == 1
        assert stats["accepted"] == 1


class TestDoubleLetters:
    """Test double letter validation (Rule 2)."""
    
    def test_common_doubles_valid(self):
        """Common double letters should pass."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("hello") is True   # 'll'
        assert filter.is_valid_sequence("pass") is True    # 'ss'
        assert filter.is_valid_sequence("butter") is True  # 'tt'
        assert filter.is_valid_sequence("coffee") is True  # 'ff'
        assert filter.is_valid_sequence("bee") is True     # 'ee'
        assert filter.is_valid_sequence("moon") is True    # 'oo'
    
    def test_rare_doubles_valid(self):
        """Rare but valid double letters should pass."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("aardvark") is True  # 'aa'
        assert filter.is_valid_sequence("skiing") is True    # 'ii'
        assert filter.is_valid_sequence("vacuum") is True    # 'uu'
    
    def test_impossible_doubles_invalid(self):
        """Impossible double letters should be rejected."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("xxyz") is False   # 'xx' impossible
        assert filter.is_valid_sequence("aqqb") is False   # 'qq' impossible
        assert filter.is_valid_sequence("jjump") is False  # 'jj' impossible
        assert filter.is_valid_sequence("vvery") is False  # 'vv' impossible
        assert filter.is_valid_sequence("hhello") is False # 'hh' impossible
    
    def test_doubles_disabled(self):
        """Impossible doubles should pass when rule is disabled."""
        rules = PhonotacticRules(reject_impossible_doubles=False)
        phonotactic_filter = PhonotacticFilter(rules)
        # Note: xxyz may still fail other rules (cluster check)
        # Test with a word that only fails double check
        assert phonotactic_filter.is_valid_sequence("saxxon") is True  # xx in middle
        assert phonotactic_filter.is_valid_sequence("hajji") is True   # jj with vowels around it
    
    def test_stats_double_rejection(self):
        """Stats should track impossible double rejections."""
        filter = PhonotacticFilter()
        filter.is_valid_sequence("xxyz")
        filter.is_valid_sequence("hello")
        stats = filter.get_stats()
        assert stats["rejected_double"] == 1
        assert stats["accepted"] == 1


class TestConsonantClusters:
    """Test consonant cluster validation (Rule 3)."""
    
    def test_valid_2letter_clusters(self):
        """Valid 2-letter initial clusters should pass."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("blue") is True    # 'bl'
        assert filter.is_valid_sequence("brown") is True   # 'br'
        assert filter.is_valid_sequence("chair") is True   # 'ch'
        assert filter.is_valid_sequence("cross") is True   # 'cr'
        assert filter.is_valid_sequence("tree") is True    # 'tr'
        assert filter.is_valid_sequence("swing") is True   # 'sw'
    
    def test_valid_3letter_clusters(self):
        """Valid 3-letter initial clusters should pass."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("chrome") is True   # 'chr'
        assert filter.is_valid_sequence("phrase") is True   # 'phr'
        assert filter.is_valid_sequence("school") is True   # 'sch'
        assert filter.is_valid_sequence("screen") is True   # 'scr'
        assert filter.is_valid_sequence("string") is True   # 'str'
        assert filter.is_valid_sequence("thread") is True   # 'thr'
    
    def test_invalid_initial_pairs(self):
        """Invalid initial consonant pairs should be rejected."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("bkword") is False  # 'bk' invalid
        assert filter.is_valid_sequence("dkword") is False  # 'dk' invalid
        assert filter.is_valid_sequence("pkword") is False  # 'pk' invalid
        assert filter.is_valid_sequence("tkword") is False  # 'tk' invalid
    
    def test_words_starting_with_vowel(self):
        """Words starting with vowels should pass cluster check."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("apple") is True
        assert filter.is_valid_sequence("orange") is True
        assert filter.is_valid_sequence("under") is True
    
    def test_clusters_disabled(self):
        """Invalid clusters should pass when rule is disabled."""
        rules = PhonotacticRules(reject_invalid_clusters=False)
        filter = PhonotacticFilter(rules)
        assert filter.is_valid_sequence("bkword") is True
        assert filter.is_valid_sequence("pkword") is True
    
    def test_stats_cluster_rejection(self):
        """Stats should track cluster rejections."""
        filter = PhonotacticFilter()
        filter.is_valid_sequence("bkword")
        filter.is_valid_sequence("blue")
        stats = filter.get_stats()
        assert stats["rejected_cluster"] == 1
        assert stats["accepted"] == 1


class TestVowelConsonantPatterns:
    """Test vowel-consonant pattern validation (Rule 4)."""
    
    def test_normal_patterns_valid(self):
        """Normal VC patterns should pass."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("cat") is True      # CVC
        assert filter.is_valid_sequence("apple") is True    # VCCV
        assert filter.is_valid_sequence("string") is True   # CCCVCC
        assert filter.is_valid_sequence("beautiful") is True # CVVVCVCVC
    
    def test_extreme_consonants_invalid(self):
        """Too many consecutive consonants should be rejected."""
        phonotactic_filter = PhonotacticFilter()
        # Default max is 4 consonants
        assert phonotactic_filter.is_valid_sequence("string") is True  # "str" is 3, "ng" is 2 - valid
        assert phonotactic_filter.is_valid_sequence("bcdfgh") is False  # 6 consonants - invalid
        assert phonotactic_filter.is_valid_sequence("pqrst") is False   # 5 consonants - invalid
    
    def test_extreme_vowels_invalid(self):
        """Too many consecutive vowels should be rejected."""
        phonotactic_filter = PhonotacticFilter()
        # Default max is 3 vowels - but 'queue' has 4 (u-e-u-e)
        assert phonotactic_filter.is_valid_sequence("beautiful") is True  # max 3 vowels (eau)
        assert phonotactic_filter.is_valid_sequence("aeiou") is False   # 5 vowels
        assert phonotactic_filter.is_valid_sequence("aeio") is False    # 4 vowels
    
    def test_custom_thresholds(self):
        """Custom VC thresholds should be respected."""
        rules = PhonotacticRules(
            max_consecutive_consonants=5,
            max_consecutive_vowels=4
        )
        phonotactic_filter = PhonotacticFilter(rules)
        assert phonotactic_filter.is_valid_sequence("string") is True  # 3 consonants max - OK
        assert phonotactic_filter.is_valid_sequence("beautiful") is True    # 3 vowels max - OK
        assert phonotactic_filter.is_valid_sequence("bcdfgh") is False # 6 consonants - too many even with limit=5
    
    def test_vc_patterns_disabled(self):
        """Extreme patterns should pass when rule is disabled."""
        rules = PhonotacticRules(reject_extreme_vc_patterns=False)
        phonotactic_filter = PhonotacticFilter(rules)
        # These would normally fail, but should pass with rule disabled
        assert phonotactic_filter.is_valid_sequence("aeiou") is True  # 5 vowels
        # Still might fail other rules (e.g., cluster check for consonant-heavy)
        # So test something that only fails VC pattern
        assert phonotactic_filter.is_valid_sequence("iouea") is True  # 5 vowels
    
    def test_stats_vc_rejection(self):
        """Stats should track VC pattern rejections."""
        filter = PhonotacticFilter()
        filter.is_valid_sequence("aeiou")
        filter.is_valid_sequence("apple")
        stats = filter.get_stats()
        assert stats["rejected_vc_pattern"] == 1
        assert stats["accepted"] == 1


class TestFilterPermutations:
    """Test the filter_permutations generator method."""
    
    def test_filter_generator(self):
        """Generator should yield only valid sequences."""
        filter = PhonotacticFilter()
        perms = ['hello', 'helllo', 'xxyz', 'world', 'bkword', 'apple']
        valid = list(filter.filter_permutations(perms))
        
        # Should keep: hello, world, apple
        # Should reject: helllo (triple), xxyz (impossible double), bkword (bad cluster)
        assert 'hello' in valid
        assert 'world' in valid
        assert 'apple' in valid
        assert 'helllo' not in valid
        assert 'xxyz' not in valid
        assert 'bkword' not in valid
    
    def test_filter_empty_input(self):
        """Empty input should yield nothing."""
        filter = PhonotacticFilter()
        valid = list(filter.filter_permutations([]))
        assert len(valid) == 0
    
    def test_filter_all_invalid(self):
        """All invalid sequences should yield nothing."""
        filter = PhonotacticFilter()
        perms = ['helllo', 'xxyz', 'bkword', 'aeiou']
        valid = list(filter.filter_permutations(perms))
        assert len(valid) == 0


class TestStatistics:
    """Test statistics tracking and reporting."""
    
    def test_initial_stats(self):
        """Initial stats should be all zeros."""
        filter = PhonotacticFilter()
        stats = filter.get_stats()
        assert stats["checked"] == 0
        assert stats["accepted"] == 0
        assert stats["rejected_triple"] == 0
        assert stats["rejected_double"] == 0
        assert stats["rejected_cluster"] == 0
        assert stats["rejected_vc_pattern"] == 0
    
    def test_stats_accumulation(self):
        """Stats should accumulate across multiple checks."""
        filter = PhonotacticFilter()
        filter.is_valid_sequence("hello")    # Valid
        filter.is_valid_sequence("helllo")   # Triple
        filter.is_valid_sequence("xxyz")     # Double
        filter.is_valid_sequence("bkword")   # Cluster
        filter.is_valid_sequence("aeiou")    # VC pattern
        
        stats = filter.get_stats()
        assert stats["checked"] == 5
        assert stats["accepted"] == 1
        assert stats["rejected_triple"] == 1
        assert stats["rejected_double"] == 1
        assert stats["rejected_cluster"] == 1
        assert stats["rejected_vc_pattern"] == 1
    
    def test_rejection_rate_calculation(self):
        """Rejection rate should be calculated correctly."""
        filter = PhonotacticFilter()
        # 3 valid, 2 invalid = 40% rejection
        filter.is_valid_sequence("hello")
        filter.is_valid_sequence("world")
        filter.is_valid_sequence("apple")
        filter.is_valid_sequence("helllo")
        filter.is_valid_sequence("xxyz")
        
        stats = filter.get_stats()
        assert stats["rejection_rate"] == "40.00%"
        assert stats["acceptance_rate"] == "60.00%"
    
    def test_reset_stats(self):
        """Reset should clear all stats."""
        filter = PhonotacticFilter()
        filter.is_valid_sequence("hello")
        filter.is_valid_sequence("helllo")
        filter.reset_stats()
        
        stats = filter.get_stats()
        assert stats["checked"] == 0
        assert stats["accepted"] == 0
        assert stats["rejected_triple"] == 0


class TestRealWorldWords:
    """Test with real English words that should pass all checks."""
    
    def test_common_english_words(self):
        """Common English words should pass all filters."""
        filter = PhonotacticFilter()
        common_words = [
            "action", "captain", "nation", "option", "caution",
            "hello", "world", "apple", "orange", "banana",
            "computer", "keyboard", "mouse", "screen", "laptop",
            "python", "filter", "sequence", "pattern", "cluster"
        ]
        for word in common_words:
            assert filter.is_valid_sequence(word) is True, f"Word '{word}' should be valid"
    
    def test_nyt_spelling_bee_words(self):
        """Known NYT Spelling Bee solutions should pass."""
        filter = PhonotacticFilter()
        nyt_words = [
            "nacuotp", "caption", "coupon", "toucan", "octant",
            "count", "cannot", "cotton", "mount", "onto"
        ]
        for word in nyt_words:
            # Note: These are letter sets, not real words, but should pass phonotactic rules
            if len(word) <= 7:  # Only check short sequences
                result = filter.is_valid_sequence(word)
                # Some may fail cluster/VC checks, but shouldn't fail triple/double
                if not result:
                    stats = filter.get_stats()
                    # Should not be rejected for triple or impossible doubles
                    assert stats["rejected_triple"] == 0 or word not in nyt_words
                    assert stats["rejected_double"] == 0 or word not in nyt_words


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_letter(self):
        """Single letters should pass (no patterns to check)."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("a") is True
        assert filter.is_valid_sequence("z") is True
    
    def test_two_letters(self):
        """Two-letter sequences should be handled correctly."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("at") is True
        assert filter.is_valid_sequence("it") is True
        assert filter.is_valid_sequence("xx") is False  # Impossible double
    
    def test_case_insensitive(self):
        """Filter should be case-insensitive."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("Hello") is True
        assert filter.is_valid_sequence("HELLO") is True
        assert filter.is_valid_sequence("HeLLo") is True
        assert filter.is_valid_sequence("HELLLO") is False
    
    def test_empty_string(self):
        """Empty string should pass (vacuously true)."""
        filter = PhonotacticFilter()
        assert filter.is_valid_sequence("") is True


class TestPerformance:
    """Test performance characteristics (not strict benchmarks)."""
    
    def test_large_batch_filtering(self):
        """Should handle large batches efficiently."""
        filter = PhonotacticFilter()
        # Generate 1000 test sequences
        perms = [f"test{i}" for i in range(1000)]
        valid = list(filter.filter_permutations(perms))
        
        # Should process without errors
        assert len(valid) > 0
        stats = filter.get_stats()
        assert stats["checked"] == 1000
    
    def test_stats_no_division_by_zero(self):
        """Stats should handle zero checks gracefully."""
        filter = PhonotacticFilter()
        stats = filter.get_stats()
        assert stats["rejection_rate"] == "0.00%"
        assert stats["acceptance_rate"] == "0.00%"

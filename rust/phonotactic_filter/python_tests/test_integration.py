"""
Integration tests for Rust Phonotactic Filter

Compares Rust implementation against Python implementation to ensure identical behavior.
"""

import sys
import pytest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import Rust version
try:
    from phonotactic_filter import PhonotacticFilter as RustFilter
    from phonotactic_filter import PhonotacticRules as RustRules
    from phonotactic_filter import create_phonotactic_filter
    RUST_AVAILABLE = True
except ImportError as e:
    RUST_AVAILABLE = False
    print(f"⚠️  Rust module not available: {e}")
    print("   Build it with: cd rust/phonotactic_filter && maturin develop --release")

# Import Python version for comparison
from src.spelling_bee_solver.core.phonotactic_filter import (
    PhonotacticFilter as PyFilter,
    PhonotacticRules as PyRules,
)


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust module not built")
class TestRustPhonotacticFilter:
    """Test Rust implementation against Python reference"""

    def test_module_imports(self):
        """Verify all classes and functions are available"""
        assert RustFilter is not None
        assert RustRules is not None
        assert create_phonotactic_filter is not None

    def test_rules_creation_default(self):
        """Test PhonotacticRules with default parameters"""
        rust_rules = RustRules()

        assert rust_rules.reject_triple_letters == True
        assert rust_rules.reject_impossible_doubles == True
        assert rust_rules.reject_invalid_clusters == True
        assert rust_rules.reject_extreme_vc_patterns == True
        assert rust_rules.max_consecutive_consonants == 4
        assert rust_rules.max_consecutive_vowels == 3

    def test_rules_creation_custom(self):
        """Test PhonotacticRules with custom parameters"""
        rust_rules = RustRules(
            reject_triple_letters=False,
            reject_impossible_doubles=True,
            max_consecutive_consonants=5,
            max_consecutive_vowels=4
        )

        assert rust_rules.reject_triple_letters == False
        assert rust_rules.reject_impossible_doubles == True
        assert rust_rules.max_consecutive_consonants == 5
        assert rust_rules.max_consecutive_vowels == 4

    def test_filter_creation_default(self):
        """Test filter creation with default rules"""
        rust_filter = RustFilter()
        assert rust_filter is not None

    def test_filter_creation_custom_rules(self):
        """Test filter creation with custom rules"""
        rules = RustRules(reject_triple_letters=False)
        rust_filter = RustFilter(rules)
        assert rust_filter is not None

    def test_factory_function(self):
        """Test create_phonotactic_filter factory function"""
        rust_filter = create_phonotactic_filter(
            reject_triple_letters=True,
            reject_impossible_doubles=True,
            max_consecutive_consonants=5
        )
        assert rust_filter is not None

    def test_valid_common_words(self):
        """Test that common English words are accepted"""
        rust_filter = RustFilter()
        python_filter = PyFilter()

        common_words = [
            "hello", "world", "python", "rust", "programming",
            "computer", "science", "algorithm", "data", "structure",
            "strength", "chrome", "school", "through", "knight",
        ]

        for word in common_words:
            rust_result = rust_filter.is_valid_sequence(word)
            python_result = python_filter.is_valid_sequence(word)

            assert rust_result == python_result, \
                f"Mismatch for '{word}': Rust={rust_result}, Python={python_result}"
            assert rust_result == True, f"Common word '{word}' should be valid"

    def test_triple_letters_rejection(self):
        """Test that triple letters are correctly rejected"""
        rust_filter = RustFilter()
        python_filter = PyFilter()

        triple_words = [
            "aaa", "bbb", "hlllo", "goood", "treee",
        ]

        for word in triple_words:
            rust_result = rust_filter.is_valid_sequence(word)
            python_result = python_filter.is_valid_sequence(word)

            assert rust_result == python_result, \
                f"Mismatch for '{word}': Rust={rust_result}, Python={python_result}"
            assert rust_result == False, f"Word '{word}' with triple letters should be invalid"

    def test_impossible_doubles_rejection(self):
        """Test that impossible doubles are correctly rejected"""
        rust_filter = RustFilter()
        python_filter = PyFilter()

        impossible_double_words = [
            "xxyz", "hajj", "navvy", "vacuuming",  # vv is impossible
        ]

        for word in impossible_double_words:
            rust_result = rust_filter.is_valid_sequence(word)
            python_result = python_filter.is_valid_sequence(word)

            assert rust_result == python_result, \
                f"Mismatch for '{word}': Rust={rust_result}, Python={python_result}"

    def test_valid_consonant_clusters(self):
        """Test that valid consonant clusters are accepted"""
        rust_filter = RustFilter()
        python_filter = PyFilter()

        valid_clusters = [
            "string", "chrome", "school", "sphere", "split",
            "spray", "threshold", "knight", "pneumatic", "psychology",
        ]

        for word in valid_clusters:
            rust_result = rust_filter.is_valid_sequence(word)
            python_result = python_filter.is_valid_sequence(word)

            assert rust_result == python_result, \
                f"Mismatch for '{word}': Rust={rust_result}, Python={python_result}"

    def test_invalid_consonant_clusters(self):
        """Test that invalid consonant clusters are rejected"""
        rust_filter = RustFilter()
        python_filter = PyFilter()

        invalid_clusters = [
            "bktest", "pktest", "tktest", "dmtest",
        ]

        for word in invalid_clusters:
            rust_result = rust_filter.is_valid_sequence(word)
            python_result = python_filter.is_valid_sequence(word)

            assert rust_result == python_result, \
                f"Mismatch for '{word}': Rust={rust_result}, Python={python_result}"
            assert rust_result == False, f"Word '{word}' with invalid cluster should be invalid"

    def test_extreme_vc_patterns(self):
        """Test vowel-consonant pattern validation"""
        rust_filter = RustFilter()
        python_filter = PyFilter()

        test_cases = [
            ("hello", True),       # Normal pattern
            ("strength", True),    # 4 consonants (ngth) - valid
            ("bcdfg", False),      # 5 consonants - invalid
            ("aeiou", False),      # 5 vowels - invalid
            ("queue", True),       # 3 vowels (ueu) - valid
        ]

        for word, expected in test_cases:
            rust_result = rust_filter.is_valid_sequence(word)
            python_result = python_filter.is_valid_sequence(word)

            assert rust_result == python_result, \
                f"Mismatch for '{word}': Rust={rust_result}, Python={python_result}"

    def test_filter_permutations(self):
        """Test batch filtering of permutations"""
        rust_filter = RustFilter()
        python_filter = PyFilter()

        permutations = [
            "hello", "hlllo", "world", "xxyz", "strength",
            "chrome", "bktest", "aeiou", "bcdfg", "python",
        ]

        rust_results = rust_filter.filter_permutations(permutations)
        python_results = list(python_filter.filter_permutations(iter(permutations)))

        assert set(rust_results) == set(python_results), \
            f"Rust and Python filter_permutations differ:\nRust: {rust_results}\nPython: {python_results}"

    def test_statistics_tracking(self):
        """Test that statistics are correctly tracked"""
        rust_filter = RustFilter()

        # Check initial stats
        stats = rust_filter.get_stats()
        assert stats["checked"] == "0"
        assert stats["accepted"] == "0"

        # Process some words
        rust_filter.is_valid_sequence("hello")  # Valid
        rust_filter.is_valid_sequence("hlllo")  # Invalid (triple)
        rust_filter.is_valid_sequence("xxyz")   # Invalid (impossible double)

        # Check updated stats
        stats = rust_filter.get_stats()
        assert stats["checked"] == "3"
        assert stats["accepted"] == "1"
        assert stats["rejected_triple"] == "1"
        assert stats["rejected_double"] == "1"

        # Reset and verify
        rust_filter.reset_stats()
        stats = rust_filter.get_stats()
        assert stats["checked"] == "0"
        assert stats["accepted"] == "0"

    def test_case_insensitivity(self):
        """Test that validation is case-insensitive"""
        rust_filter = RustFilter()

        words = ["HELLO", "Hello", "hello", "HeLLo"]

        for word in words:
            assert rust_filter.is_valid_sequence(word) == True

    def test_comprehensive_word_list(self):
        """Test a comprehensive list of words to ensure Rust matches Python"""
        rust_filter = RustFilter()
        python_filter = PyFilter()

        # Mix of valid and invalid words
        test_words = [
            # Valid words
            "accept", "account", "action", "adult", "ancient",
            "bottle", "butter", "coffee", "copper", "committee",
            "cheese", "choose", "chrome", "church", "school",
            "street", "strong", "structure", "threshold", "through",
            # Invalid patterns
            "aaa", "bbb", "ccc", "hlllo", "goood",
            "xxtest", "qqtest", "vvtest", "hhtest",
            "bktest", "pktest", "tktest",
        ]

        mismatches = []
        for word in test_words:
            rust_result = rust_filter.is_valid_sequence(word)
            python_result = python_filter.is_valid_sequence(word)

            if rust_result != python_result:
                mismatches.append(f"{word}: Rust={rust_result}, Python={python_result}")

        assert len(mismatches) == 0, f"Found mismatches:\n" + "\n".join(mismatches)

    def test_custom_rules_respected(self):
        """Test that custom rules are properly respected"""
        # Create filter that ALLOWS triple letters
        rules = RustRules(reject_triple_letters=False)
        rust_filter = RustFilter(rules)

        # Triple letters should now be allowed
        assert rust_filter.is_valid_sequence("hlllo") == True

        # Create filter that allows extreme VC patterns
        rules2 = RustRules(
            reject_extreme_vc_patterns=False,
            max_consecutive_consonants=10,
            max_consecutive_vowels=10
        )
        rust_filter2 = RustFilter(rules2)

        # Should allow extreme patterns
        assert rust_filter2.is_valid_sequence("bcdfg") == True  # Would normally fail


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust module not built")
def test_example_usage():
    """Test the example from the documentation works"""
    filter_obj = RustFilter()

    assert filter_obj.is_valid_sequence("hello") == True
    assert filter_obj.is_valid_sequence("hlllo") == False  # Triple 'l'
    assert filter_obj.is_valid_sequence("xxyz") == False   # Impossible 'xx'


if __name__ == "__main__":
    if RUST_AVAILABLE:
        print("✅ Rust module is available!")
        print("\nRunning basic tests...\n")

        # Quick smoke test
        rust_filter = RustFilter()
        python_filter = PyFilter()

        test_words = ["hello", "hlllo", "xxyz", "strength", "chrome"]

        print("Word       | Rust  | Python | Match")
        print("-" * 40)
        for word in test_words:
            rust_result = rust_filter.is_valid_sequence(word)
            python_result = python_filter.is_valid_sequence(word)
            match = "✅" if rust_result == python_result else "❌"

            print(f"{word:10} | {str(rust_result):5} | {str(python_result):6} | {match}")

        print("\nRun full tests with: pytest test_integration.py -v")
    else:
        print("❌ Rust module not available")
        print("   Build it with: cd rust/phonotactic_filter && maturin develop --release")

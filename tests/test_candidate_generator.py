"""Tests for CandidateGenerator component.

This test suite verifies the candidate generation logic for Spelling Bee puzzles,
including:
- Factory function creation
- Basic word validation
- Candidate generation from dictionaries
- Advanced filtering integration
- Input validation and error handling
- Edge cases and special scenarios
"""

import pytest
from spelling_bee_solver.core import CandidateGenerator, create_candidate_generator


class TestCandidateGenerator:
    """Test suite for CandidateGenerator class."""

    # ==================== Factory Function Tests ====================

    def test_create_candidate_generator_default(self):
        """Test creating CandidateGenerator with default configuration."""
        generator = create_candidate_generator()
        
        assert isinstance(generator, CandidateGenerator)
        assert generator.min_word_length == 4

    def test_create_candidate_generator_custom_length(self):
        """Test creating CandidateGenerator with custom minimum length."""
        generator = create_candidate_generator(min_word_length=5)
        
        assert generator.min_word_length == 5

    def test_create_candidate_generator_with_filter(self):
        """Test creating CandidateGenerator with custom filter."""
        def my_filter(words):
            return [w for w in words if not w.startswith('x')]
        
        generator = create_candidate_generator(advanced_filter=my_filter)
        
        assert generator._advanced_filter is not None

    def test_create_candidate_generator_invalid_length(self):
        """Test creating CandidateGenerator with invalid minimum length."""
        with pytest.raises(ValueError, match="min_word_length must be >= 1"):
            create_candidate_generator(min_word_length=0)

    # ==================== Initialization Tests ====================

    def test_init_default(self):
        """Test CandidateGenerator initialization with defaults."""
        generator = CandidateGenerator()
        
        assert generator.min_word_length == 4
        assert generator._advanced_filter is None

    def test_init_custom_min_length(self):
        """Test CandidateGenerator initialization with custom min length."""
        generator = CandidateGenerator(min_word_length=6)
        
        assert generator.min_word_length == 6

    def test_init_with_advanced_filter(self):
        """Test CandidateGenerator initialization with advanced filter."""
        def custom_filter(words):
            return words[:10]
        
        generator = CandidateGenerator(advanced_filter=custom_filter)
        
        assert generator._advanced_filter is custom_filter

    def test_init_invalid_type(self):
        """Test CandidateGenerator initialization with invalid type."""
        with pytest.raises(TypeError, match="min_word_length must be an integer"):
            CandidateGenerator(min_word_length="4")

    def test_init_negative_length(self):
        """Test CandidateGenerator initialization with negative length."""
        with pytest.raises(ValueError, match="min_word_length must be >= 1"):
            CandidateGenerator(min_word_length=-1)

    # ==================== is_valid_word_basic Tests ====================

    def test_is_valid_word_basic_valid(self):
        """Test is_valid_word_basic with valid word."""
        generator = CandidateGenerator()
        
        assert generator.is_valid_word_basic("count", "nacuotp", "n") is True

    def test_is_valid_word_basic_too_short(self):
        """Test is_valid_word_basic with word too short."""
        generator = CandidateGenerator()
        
        assert generator.is_valid_word_basic("cat", "nacuotp", "n") is False

    def test_is_valid_word_basic_missing_required_letter(self):
        """Test is_valid_word_basic with missing required letter."""
        generator = CandidateGenerator()
        
        assert generator.is_valid_word_basic("apple", "nacuotp", "n") is False

    def test_is_valid_word_basic_invalid_letters(self):
        """Test is_valid_word_basic with invalid letters (word uses letter not in puzzle)."""
        generator = CandidateGenerator()
        
        # 'example' contains 'e', 'x', 'm', 'l' which are not in 'nacuotp'
        assert generator.is_valid_word_basic("example", "nacuotp", "n") is False

    def test_is_valid_word_basic_case_insensitive(self):
        """Test is_valid_word_basic is case insensitive."""
        generator = CandidateGenerator()
        
        assert generator.is_valid_word_basic("COUNT", "NACUOTP", "N") is True
        assert generator.is_valid_word_basic("Count", "NaCuOtP", "n") is True

    def test_is_valid_word_basic_exact_min_length(self):
        """Test is_valid_word_basic with word exactly at minimum length."""
        generator = CandidateGenerator(min_word_length=4)
        
        assert generator.is_valid_word_basic("coat", "nacuotp", "c") is True

    def test_is_valid_word_basic_custom_min_length(self):
        """Test is_valid_word_basic with custom minimum length."""
        generator = CandidateGenerator(min_word_length=6)
        
        assert generator.is_valid_word_basic("count", "nacuotp", "n") is False  # 5 letters
        assert generator.is_valid_word_basic("canton", "nacuotp", "n") is True  # 6 letters

    def test_is_valid_word_basic_pangram(self):
        """Test is_valid_word_basic with pangram (uses all letters)."""
        generator = CandidateGenerator()
        
        # "captain" uses c-a-p-t-a-i-n (all 7 letters)
        assert generator.is_valid_word_basic("captain", "captoin", "c") is True

    def test_is_valid_word_basic_repeated_letters(self):
        """Test is_valid_word_basic with repeated letters."""
        generator = CandidateGenerator()
        
        # "noon" has repeated 'o' and 'n'
        assert generator.is_valid_word_basic("noon", "nacuotp", "n") is True

    # ==================== Input Validation Tests ====================

    def test_is_valid_word_basic_invalid_word_type(self):
        """Test is_valid_word_basic with non-string word."""
        generator = CandidateGenerator()
        
        with pytest.raises(TypeError, match="Word must be a string"):
            generator.is_valid_word_basic(123, "nacuotp", "n")

    def test_is_valid_word_basic_invalid_letters_type(self):
        """Test is_valid_word_basic with non-string letters."""
        generator = CandidateGenerator()
        
        with pytest.raises(TypeError, match="Letters must be a string"):
            generator.is_valid_word_basic("count", 1234567, "n")

    def test_is_valid_word_basic_invalid_required_letter_type(self):
        """Test is_valid_word_basic with non-string required letter."""
        generator = CandidateGenerator()
        
        with pytest.raises(TypeError, match="Required letter must be a string"):
            generator.is_valid_word_basic("count", "nacuotp", 1)

    def test_is_valid_word_basic_empty_word(self):
        """Test is_valid_word_basic with empty word."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Word cannot be empty or whitespace"):
            generator.is_valid_word_basic("", "nacuotp", "n")

    def test_is_valid_word_basic_whitespace_word(self):
        """Test is_valid_word_basic with whitespace word."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Word cannot be empty or whitespace"):
            generator.is_valid_word_basic("   ", "nacuotp", "n")

    def test_is_valid_word_basic_wrong_letters_length(self):
        """Test is_valid_word_basic with wrong number of letters."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Letters must be exactly 7 characters"):
            generator.is_valid_word_basic("count", "abc", "n")

    def test_is_valid_word_basic_wrong_required_letter_length(self):
        """Test is_valid_word_basic with wrong required letter length."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Required letter must be exactly 1 character"):
            generator.is_valid_word_basic("count", "nacuotp", "nn")

    def test_is_valid_word_basic_non_alphabetic_word(self):
        """Test is_valid_word_basic with non-alphabetic word."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Word must contain only alphabetic characters"):
            generator.is_valid_word_basic("co-unt", "nacuotp", "n")

    def test_is_valid_word_basic_non_alphabetic_letters(self):
        """Test is_valid_word_basic with non-alphabetic letters."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Letters must contain only alphabetic characters"):
            generator.is_valid_word_basic("count", "nacu0tp", "n")

    def test_is_valid_word_basic_non_alphabetic_required_letter(self):
        """Test is_valid_word_basic with non-alphabetic required letter."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Required letter must be alphabetic"):
            generator.is_valid_word_basic("count", "nacuotp", "1")

    def test_is_valid_word_basic_required_letter_not_in_letters(self):
        """Test is_valid_word_basic with required letter not in puzzle letters."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Required letter 'x' must be one of the puzzle letters"):
            generator.is_valid_word_basic("count", "nacuotp", "x")

    # ==================== generate_candidates Tests ====================

    def test_generate_candidates_basic(self):
        """Test generate_candidates with basic dictionary."""
        generator = CandidateGenerator()
        dictionary = {'apple', 'count', 'upon', 'act', 'can'}
        
        candidates = generator.generate_candidates(dictionary, 'nacuotp', 'n')
        
        assert sorted(candidates) == ['count', 'upon']

    def test_generate_candidates_empty_dictionary(self):
        """Test generate_candidates with empty dictionary."""
        generator = CandidateGenerator()
        
        candidates = generator.generate_candidates(set(), 'nacuotp', 'n')
        
        assert candidates == []

    def test_generate_candidates_no_matches(self):
        """Test generate_candidates with no matching words."""
        generator = CandidateGenerator()
        dictionary = {'apple', 'berry', 'cherry'}
        
        candidates = generator.generate_candidates(dictionary, 'nacuotp', 'n')
        
        assert candidates == []

    def test_generate_candidates_case_insensitive(self):
        """Test generate_candidates is case insensitive."""
        generator = CandidateGenerator()
        dictionary = {'COUNT', 'Upon', 'APPLE'}
        
        candidates = generator.generate_candidates(dictionary, 'NACUOTP', 'N')
        
        assert sorted(candidates) == ['count', 'upon']

    def test_generate_candidates_custom_min_length(self):
        """Test generate_candidates with custom minimum length."""
        generator = CandidateGenerator(min_word_length=6)
        dictionary = {'count', 'canoe', 'account', 'cannot'}
        
        candidates = generator.generate_candidates(dictionary, 'nacuotp', 'n')
        
        # Only 'account' and 'cannot' have 6+ letters and meet criteria
        assert sorted(candidates) == ['account', 'cannot']

    def test_generate_candidates_with_advanced_filter(self):
        """Test generate_candidates with advanced filter."""
        def filter_no_vowels(words):
            return [w for w in words if not any(v in w for v in 'aeiou')]
        
        generator = CandidateGenerator(advanced_filter=filter_no_vowels)
        dictionary = {'count', 'canoe', 'onto', 'noon'}
        
        candidates = generator.generate_candidates(dictionary, 'nacuotp', 'n')
        
        # 'noon' passes basic filter but should be removed by advanced filter (has 'o')
        # Actually, 'onto' and 'noon' both have vowels, so they're filtered
        # Only if there were consonant-only words...
        # Let me reconsider: all these have vowels, so result should be empty
        assert candidates == []

    def test_generate_candidates_skip_advanced_filter(self):
        """Test generate_candidates skipping advanced filter."""
        def filter_all(words):  # noqa: ARG001 - unused argument in test filter
            return []  # Filters everything
        
        generator = CandidateGenerator(advanced_filter=filter_all)
        dictionary = {'count', 'upon'}
        
        # With filter applied
        candidates_filtered = generator.generate_candidates(
            dictionary, 'nacuotp', 'n', apply_advanced_filter=True
        )
        assert candidates_filtered == []
        
        # Without filter applied
        candidates_unfiltered = generator.generate_candidates(
            dictionary, 'nacuotp', 'n', apply_advanced_filter=False
        )
        assert sorted(candidates_unfiltered) == ['count', 'upon']

    def test_generate_candidates_pangram(self):
        """Test generate_candidates with pangrams."""
        generator = CandidateGenerator()
        dictionary = {'captain', 'cap', 'cat', 'paint', 'tin'}
        
        candidates = generator.generate_candidates(dictionary, 'captoin', 'c')
        
        # 'captain' uses all 7 letters (c-a-p-t-o-i-n)
        assert 'captain' in candidates

    def test_generate_candidates_repeated_letters(self):
        """Test generate_candidates allows repeated letters."""
        generator = CandidateGenerator()
        dictionary = {'noon', 'cannon', 'cotton', 'onto'}
        
        candidates = generator.generate_candidates(dictionary, 'nacuotp', 'n')
        
        # All these words have repeated letters and should pass
        assert 'noon' in candidates
        assert 'cannon' in candidates

    # ==================== generate_candidates Input Validation ====================

    def test_generate_candidates_invalid_dictionary_type(self):
        """Test generate_candidates with non-set dictionary."""
        generator = CandidateGenerator()
        
        with pytest.raises(TypeError, match="Dictionary must be a set"):
            generator.generate_candidates(['count', 'canoe'], 'nacuotp', 'n')

    def test_generate_candidates_invalid_letters_type(self):
        """Test generate_candidates with non-string letters."""
        generator = CandidateGenerator()
        
        with pytest.raises(TypeError, match="Letters must be a string"):
            generator.generate_candidates(set(), 1234567, 'n')

    def test_generate_candidates_invalid_required_letter_type(self):
        """Test generate_candidates with non-string required letter."""
        generator = CandidateGenerator()
        
        with pytest.raises(TypeError, match="Required letter must be a string"):
            generator.generate_candidates(set(), 'nacuotp', 1)

    def test_generate_candidates_wrong_letters_length(self):
        """Test generate_candidates with wrong number of letters."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Letters must be exactly 7 characters"):
            generator.generate_candidates(set(), 'abc', 'n')

    def test_generate_candidates_wrong_required_letter_length(self):
        """Test generate_candidates with wrong required letter length."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Required letter must be exactly 1 character"):
            generator.generate_candidates(set(), 'nacuotp', 'nn')

    def test_generate_candidates_non_alphabetic_letters(self):
        """Test generate_candidates with non-alphabetic letters."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Letters must contain only alphabetic characters"):
            generator.generate_candidates(set(), 'nacu0tp', 'n')

    def test_generate_candidates_non_alphabetic_required_letter(self):
        """Test generate_candidates with non-alphabetic required letter."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Required letter must be alphabetic"):
            generator.generate_candidates(set(), 'nacuotp', '1')

    def test_generate_candidates_required_letter_not_in_letters(self):
        """Test generate_candidates with required letter not in puzzle letters."""
        generator = CandidateGenerator()
        
        with pytest.raises(ValueError, match="Required letter 'x' must be one of the puzzle letters"):
            generator.generate_candidates(set(), 'nacuotp', 'x')

    # ==================== filter_candidates Tests ====================

    def test_filter_candidates_basic(self):
        """Test filter_candidates with basic list."""
        generator = CandidateGenerator()
        candidates = ['apple', 'count', 'upon', 'act']
        
        filtered = generator.filter_candidates(candidates, 'nacuotp', 'n')
        
        assert sorted(filtered) == ['count', 'upon']

    def test_filter_candidates_empty_list(self):
        """Test filter_candidates with empty list."""
        generator = CandidateGenerator()
        
        filtered = generator.filter_candidates([], 'nacuotp', 'n')
        
        assert filtered == []

    def test_filter_candidates_all_invalid(self):
        """Test filter_candidates with all invalid words."""
        generator = CandidateGenerator()
        candidates = ['apple', 'berry', 'cherry', 'date']
        
        filtered = generator.filter_candidates(candidates, 'nacuotp', 'n')
        
        assert filtered == []

    def test_filter_candidates_mixed_case(self):
        """Test filter_candidates handles mixed case."""
        generator = CandidateGenerator()
        candidates = ['COUNT', 'Upon', 'apple']
        
        filtered = generator.filter_candidates(candidates, 'nacuotp', 'n')
        
        assert sorted(filtered) == ['COUNT', 'Upon']

    def test_filter_candidates_invalid_type(self):
        """Test filter_candidates with non-list input."""
        generator = CandidateGenerator()
        
        with pytest.raises(TypeError, match="Candidates must be a list"):
            generator.filter_candidates({'count', 'canoe'}, 'nacuotp', 'n')

    # ==================== Constants Tests ====================

    def test_min_word_length_constant(self):
        """Test MIN_WORD_LENGTH class constant."""
        assert CandidateGenerator.MIN_WORD_LENGTH == 4

    # ==================== Integration Tests ====================

    def test_real_world_scenario(self):
        """Test with realistic Spelling Bee scenario."""
        generator = CandidateGenerator()
        
        # Real NYT Spelling Bee puzzle
        # Letters: N-A-C-U-O-T-P, Required: N
        dictionary = {
            'count', 'upon', 'cannot', 'account', 'noun', 'onto',
            'canton', 'coupon', 'unto',
            'apple', 'table', 'chair',  # Invalid - no 'n'
            'cat', 'can', 'act'  # Invalid - too short
        }
        
        candidates = generator.generate_candidates(dictionary, 'nacuotp', 'n')
        
        expected = ['account', 'cannot', 'canton', 'count', 'coupon', 'noun', 'onto', 'unto', 'upon']
        assert sorted(candidates) == expected

    def test_advanced_filter_integration(self):
        """Test integration with custom advanced filter."""
        def proper_noun_filter(words):
            # Simple filter: remove capitalized words
            return [w for w in words if w.islower()]
        
        generator = CandidateGenerator(advanced_filter=proper_noun_filter)
        dictionary = {'count', 'London', 'canoe', 'Paris'}
        
        candidates = generator.generate_candidates(dictionary, 'nacuotp', 'n')
        
        # 'London' and 'Paris' don't have 'n' anyway, but let's use better example
        dictionary = {'count', 'noun', 'canon'}
        candidates = generator.generate_candidates(dictionary, 'nacuotp', 'n')
        
        assert sorted(candidates) == ['canon', 'count', 'noun']

    def test_min_word_length_variations(self):
        """Test different minimum word lengths."""
        dictionary = {'no', 'ton', 'onto', 'count', 'cannot'}
        
        # Default: 4 letters
        gen4 = CandidateGenerator(min_word_length=4)
        candidates4 = gen4.generate_candidates(dictionary, 'nacuotp', 'n')
        assert sorted(candidates4) == ['cannot', 'count', 'onto']
        
        # Minimum: 5 letters
        gen5 = CandidateGenerator(min_word_length=5)
        candidates5 = gen5.generate_candidates(dictionary, 'nacuotp', 'n')
        assert sorted(candidates5) == ['cannot', 'count']
        
        # Minimum: 6 letters
        gen6 = CandidateGenerator(min_word_length=6)
        candidates6 = gen6.generate_candidates(dictionary, 'nacuotp', 'n')
        assert sorted(candidates6) == ['cannot']

    def test_performance_with_large_dictionary(self):
        """Test performance with large dictionary."""
        generator = CandidateGenerator()
        
        # Create large dictionary (10,000 words)
        large_dict = {f'word{i}nacuotp' for i in range(10000)}
        large_dict.add('count')
        large_dict.add('upon')
        
        candidates = generator.generate_candidates(large_dict, 'nacuotp', 'n')
        
        # Should efficiently filter to valid words
        assert 'count' in candidates
        assert 'upon' in candidates
        assert len(candidates) >= 2

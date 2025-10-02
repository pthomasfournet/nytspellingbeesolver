"""
Tests for InputValidator

Tests all validation scenarios:
- Valid inputs
- Invalid types
- Invalid formats
- Invalid lengths
- Invalid characters
- Edge cases
"""

import pytest

from spelling_bee_solver.core.input_validator import (
    InputValidator,
    create_input_validator,
)


class TestInputValidator:
    """Test suite for InputValidator class."""

    def test_factory_function(self):
        """Test that factory function creates validator."""
        validator = create_input_validator()
        assert isinstance(validator, InputValidator)

    # ===== validate_letters tests =====

    def test_validate_letters_valid(self):
        """Test validation with valid letters."""
        validator = InputValidator()

        result = validator.validate_letters("ABCDEFG")
        assert result == "abcdefg"

        result = validator.validate_letters("abcdefg")
        assert result == "abcdefg"

        result = validator.validate_letters("AbCdEfG")
        assert result == "abcdefg"

    def test_validate_letters_none(self):
        """Test validation rejects None."""
        validator = InputValidator()

        with pytest.raises(ValueError, match="cannot be None"):
            validator.validate_letters(None)

    def test_validate_letters_wrong_type(self):
        """Test validation rejects non-string types."""
        validator = InputValidator()

        with pytest.raises(TypeError, match="must be a string"):
            validator.validate_letters(1234567)

        with pytest.raises(TypeError, match="must be a string"):
            validator.validate_letters(['A', 'B', 'C', 'D', 'E', 'F', 'G'])

    def test_validate_letters_wrong_length(self):
        """Test validation rejects incorrect length."""
        validator = InputValidator()

        with pytest.raises(ValueError, match="exactly 7 characters"):
            validator.validate_letters("ABC")

        with pytest.raises(ValueError, match="exactly 7 characters"):
            validator.validate_letters("ABCDEFGH")

        with pytest.raises(ValueError, match="exactly 7 characters"):
            validator.validate_letters("")

    def test_validate_letters_non_alphabetic(self):
        """Test validation rejects non-alphabetic characters."""
        validator = InputValidator()

        with pytest.raises(ValueError, match="only alphabetic"):
            validator.validate_letters("ABC123G")

        with pytest.raises(ValueError, match="only alphabetic"):
            validator.validate_letters("ABC-EFG")

        with pytest.raises(ValueError, match="only alphabetic"):
            validator.validate_letters("ABC EFG")

    # ===== validate_required_letter tests =====

    def test_validate_required_letter_valid(self):
        """Test validation with valid required letter."""
        validator = InputValidator()

        result = validator.validate_required_letter("A", "ABCDEFG")
        assert result == "a"

        result = validator.validate_required_letter("g", "abcdefg")
        assert result == "g"

        result = validator.validate_required_letter("D", "AbCdEfG")
        assert result == "d"

    def test_validate_required_letter_none(self):
        """Test validation rejects None."""
        validator = InputValidator()

        with pytest.raises(ValueError, match="cannot be None"):
            validator.validate_required_letter(None, "ABCDEFG")

    def test_validate_required_letter_wrong_type(self):
        """Test validation rejects non-string types."""
        validator = InputValidator()

        with pytest.raises(TypeError, match="must be a string"):
            validator.validate_required_letter(1, "ABCDEFG")

    def test_validate_required_letter_wrong_length(self):
        """Test validation rejects incorrect length."""
        validator = InputValidator()

        with pytest.raises(ValueError, match="exactly 1 character"):
            validator.validate_required_letter("AB", "ABCDEFG")

        with pytest.raises(ValueError, match="exactly 1 character"):
            validator.validate_required_letter("", "ABCDEFG")

    def test_validate_required_letter_non_alphabetic(self):
        """Test validation rejects non-alphabetic characters."""
        validator = InputValidator()

        with pytest.raises(ValueError, match="must be alphabetic"):
            validator.validate_required_letter("1", "ABCDEFG")

        with pytest.raises(ValueError, match="must be alphabetic"):
            validator.validate_required_letter("-", "ABCDEFG")

    def test_validate_required_letter_not_in_puzzle(self):
        """Test validation rejects letter not in puzzle."""
        validator = InputValidator()

        with pytest.raises(ValueError, match="must be one of"):
            validator.validate_required_letter("Z", "ABCDEFG")

        with pytest.raises(ValueError, match="must be one of"):
            validator.validate_required_letter("X", "abcdefg")

    # ===== validate_and_normalize tests =====

    def test_validate_and_normalize_both_provided(self):
        """Test validation when both inputs provided."""
        validator = InputValidator()

        letters_lower, required_lower, letters_set = validator.validate_and_normalize(
            "ABCDEFG", "D"
        )

        assert letters_lower == "abcdefg"
        assert required_lower == "d"
        assert letters_set == {'a', 'b', 'c', 'd', 'e', 'f', 'g'}

    def test_validate_and_normalize_required_defaults_to_first(self):
        """Test that required letter defaults to first puzzle letter."""
        validator = InputValidator()

        letters_lower, required_lower, letters_set = validator.validate_and_normalize(
            "ABCDEFG"
        )

        assert letters_lower == "abcdefg"
        assert required_lower == "a"  # First letter
        assert letters_set == {'a', 'b', 'c', 'd', 'e', 'f', 'g'}

    def test_validate_and_normalize_propagates_errors(self):
        """Test that validation errors are propagated."""
        validator = InputValidator()

        # Invalid letters
        with pytest.raises(ValueError):
            validator.validate_and_normalize("ABC")

        # Invalid required letter
        with pytest.raises(ValueError):
            validator.validate_and_normalize("ABCDEFG", "Z")

    # ===== is_valid_word tests =====

    def test_is_valid_word_valid(self):
        """Test validation with valid words."""
        validator = InputValidator()
        letters_set = {'a', 'b', 'c', 'd', 'e', 'f', 'g'}
        required_letter = 'd'

        # Exactly 4 letters (minimum)
        assert validator.is_valid_word("abcd", letters_set, required_letter)

        # More than 4 letters
        assert validator.is_valid_word("abcdef", letters_set, required_letter)

        # All same letters repeated
        assert validator.is_valid_word("dddd", letters_set, required_letter)

        # Mixed case
        assert validator.is_valid_word("AbCd", letters_set, required_letter)

    def test_is_valid_word_too_short(self):
        """Test validation rejects words < 4 letters."""
        validator = InputValidator()
        letters_set = {'a', 'b', 'c', 'd', 'e', 'f', 'g'}
        required_letter = 'd'

        assert not validator.is_valid_word("d", letters_set, required_letter)
        assert not validator.is_valid_word("ad", letters_set, required_letter)
        assert not validator.is_valid_word("abd", letters_set, required_letter)

    def test_is_valid_word_missing_required_letter(self):
        """Test validation rejects words without required letter."""
        validator = InputValidator()
        letters_set = {'a', 'b', 'c', 'd', 'e', 'f', 'g'}
        required_letter = 'd'

        assert not validator.is_valid_word("abce", letters_set, required_letter)
        assert not validator.is_valid_word("fgab", letters_set, required_letter)

    def test_is_valid_word_uses_invalid_letters(self):
        """Test validation rejects words with letters not in puzzle."""
        validator = InputValidator()
        letters_set = {'a', 'b', 'c', 'd', 'e', 'f', 'g'}
        required_letter = 'd'

        assert not validator.is_valid_word("abcdxyz", letters_set, required_letter)
        assert not validator.is_valid_word("defz", letters_set, required_letter)

    def test_is_valid_word_wrong_type(self):
        """Test validation rejects non-string types."""
        validator = InputValidator()
        letters_set = {'a', 'b', 'c', 'd', 'e', 'f', 'g'}
        required_letter = 'd'

        with pytest.raises(TypeError, match="must be a string"):
            validator.is_valid_word(1234, letters_set, required_letter)

    def test_is_valid_word_empty_or_whitespace(self):
        """Test validation rejects empty/whitespace words."""
        validator = InputValidator()
        letters_set = {'a', 'b', 'c', 'd', 'e', 'f', 'g'}
        required_letter = 'd'

        with pytest.raises(ValueError, match="cannot be empty"):
            validator.is_valid_word("", letters_set, required_letter)

        with pytest.raises(ValueError, match="cannot be empty"):
            validator.is_valid_word("   ", letters_set, required_letter)

    def test_is_valid_word_non_alphabetic(self):
        """Test validation rejects non-alphabetic words."""
        validator = InputValidator()
        letters_set = {'a', 'b', 'c', 'd', 'e', 'f', 'g'}
        required_letter = 'd'

        with pytest.raises(ValueError, match="only alphabetic"):
            validator.is_valid_word("abc123", letters_set, required_letter)

        with pytest.raises(ValueError, match="only alphabetic"):
            validator.is_valid_word("ab-cd", letters_set, required_letter)

    # ===== Constants tests =====

    def test_constants(self):
        """Test that class constants have expected values."""
        validator = InputValidator()

        assert validator.PUZZLE_LETTER_COUNT == 7
        assert validator.REQUIRED_LETTER_COUNT == 1
        assert validator.MIN_WORD_LENGTH == 4

    # ===== Real-world scenarios =====

    def test_real_world_scenario_1(self):
        """Test with actual NYT Spelling Bee puzzle."""
        validator = InputValidator()

        # Real puzzle from NYT: letters BEGLRTU, required G
        letters_lower, required_lower, letters_set = validator.validate_and_normalize(
            "BEGLRTU", "G"
        )

        assert letters_lower == "beglrtu"
        assert required_lower == "g"
        assert letters_set == {'b', 'e', 'g', 'l', 'r', 't', 'u'}

        # Valid words
        assert validator.is_valid_word("glue", letters_set, required_lower)
        assert validator.is_valid_word("gruel", letters_set, required_lower)
        assert validator.is_valid_word("gutter", letters_set, required_lower)

        # Invalid: too short
        assert not validator.is_valid_word("bug", letters_set, required_lower)

        # Invalid: missing required letter
        assert not validator.is_valid_word("blue", letters_set, required_lower)
        assert not validator.is_valid_word("butler", letters_set, required_lower)

        # Invalid: uses letters not in puzzle
        assert not validator.is_valid_word("glaze", letters_set, required_lower)

    def test_real_world_scenario_2(self):
        """Test with another actual puzzle."""
        validator = InputValidator()

        # Puzzle: ACINOPT, required C
        letters_lower, required_lower, letters_set = validator.validate_and_normalize(
            "ACINOPT", "C"
        )

        assert letters_lower == "acinopt"
        assert required_lower == "c"

        # Valid words
        assert validator.is_valid_word("optic", letters_set, required_lower)
        assert validator.is_valid_word("caption", letters_set, required_lower)

        # Invalid: no required letter
        assert not validator.is_valid_word("point", letters_set, required_lower)

    def test_validate_letters_with_duplicates(self):
        """Test validation rejects duplicate letters (NYT Spelling Bee requires 7 UNIQUE letters)."""
        validator = InputValidator()

        # Test 7 letters but with 1 duplicate (A appears twice)
        with pytest.raises(ValueError, match="7 unique characters"):
            validator.validate_letters("ACTIONA")

        # Test 7 letters but with 2 duplicates (A appears 3 times total)
        with pytest.raises(ValueError, match="duplicate"):
            validator.validate_letters("AACTION")

        # Test with consecutive duplicates
        with pytest.raises(ValueError, match="duplicate"):
            validator.validate_letters("AABCDEF")

        # Test valid 7 unique letters (should pass)
        result = validator.validate_letters("CAPTION")
        assert result == "caption"
        assert len(set(result)) == 7  # Verify 7 unique letters

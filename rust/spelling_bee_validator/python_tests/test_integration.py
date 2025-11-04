"""
Integration tests for Rust InputValidator

These tests verify that the Rust implementation provides identical behavior
to the Python implementation.
"""

import pytest
import sys
import os

# Add the Rust build output to path
# After building with `maturin develop`, the module will be available
try:
    from spelling_bee_validator import InputValidator, MIN_WORD_LENGTH, PUZZLE_LETTER_COUNT
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False
    print("⚠️  Rust module not built yet. Run: maturin develop")
    print("   Skipping Rust integration tests")


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust module not built")
class TestInputValidatorRust:
    """Test Rust InputValidator implementation"""

    def test_create_validator(self):
        """Test creating a validator instance"""
        validator = InputValidator()
        assert validator is not None
        assert repr(validator) == "InputValidator()"

    def test_validate_letters_success(self):
        """Test successful letter validation"""
        validator = InputValidator()

        # Test uppercase conversion
        assert validator.validate_letters("NACUOTP") == "nacuotp"

        # Test lowercase passthrough
        assert validator.validate_letters("abcdefg") == "abcdefg"

        # Test mixed case
        assert validator.validate_letters("NaCuOtP") == "nacuotp"

    def test_validate_letters_errors(self):
        """Test letter validation errors"""
        validator = InputValidator()

        # Too short
        with pytest.raises(ValueError, match="exactly 7 characters"):
            validator.validate_letters("ABC")

        # Too long
        with pytest.raises(ValueError, match="exactly 7 characters"):
            validator.validate_letters("ABCDEFGH")

        # Non-alphabetic
        with pytest.raises(ValueError, match="only alphabetic characters"):
            validator.validate_letters("ABC123D")

        # Duplicates
        with pytest.raises(ValueError, match="unique"):
            validator.validate_letters("AABCDEF")

        # Empty string
        with pytest.raises(ValueError):
            validator.validate_letters("")

    def test_validate_required_letter_success(self):
        """Test successful required letter validation"""
        validator = InputValidator()

        assert validator.validate_required_letter("N", "nacuotp") == "n"
        assert validator.validate_required_letter("n", "nacuotp") == "n"
        assert validator.validate_required_letter("A", "nacuotp") == "a"

    def test_validate_required_letter_errors(self):
        """Test required letter validation errors"""
        validator = InputValidator()

        # Too long
        with pytest.raises(ValueError, match="exactly 1 character"):
            validator.validate_required_letter("AB", "nacuotp")

        # Not in letters
        with pytest.raises(ValueError, match="must be one of the puzzle letters"):
            validator.validate_required_letter("Z", "nacuotp")

        # Non-alphabetic
        with pytest.raises(ValueError, match="alphabetic"):
            validator.validate_required_letter("1", "nacuotp")

        # Empty
        with pytest.raises(ValueError):
            validator.validate_required_letter("", "nacuotp")

    def test_validate_and_normalize(self):
        """Test combined validation"""
        validator = InputValidator()

        # With explicit required letter
        letters, required, letters_set = validator.validate_and_normalize(
            "NACUOTP", "N"
        )
        assert letters == "nacuotp"
        assert required == "n"
        assert len(letters_set) == 7
        assert "n" in letters_set

        # With default required letter (first letter)
        letters, required, letters_set = validator.validate_and_normalize("NACUOTP")
        assert letters == "nacuotp"
        assert required == "n"  # First letter becomes required

    def test_validate_puzzle(self):
        """Test puzzle validation (center + 6 others)"""
        validator = InputValidator()

        # Valid puzzle
        all_letters, center, letters_set = validator.validate_puzzle("N", "ACUOTP")
        assert all_letters == "nacuotp"
        assert center == "n"
        assert len(letters_set) == 7

        # Center letter in others (should error)
        with pytest.raises(ValueError, match="must NOT appear in other letters"):
            validator.validate_puzzle("N", "NACUOT")

        # Duplicate in others
        with pytest.raises(ValueError, match="unique"):
            validator.validate_puzzle("N", "AACUOT")

    def test_is_valid_word(self):
        """Test word validation"""
        validator = InputValidator()

        letters_set = ["n", "a", "c", "u", "o", "t", "p"]
        required = "n"

        # Valid words
        assert validator.is_valid_word("noun", letters_set, required) is True
        assert validator.is_valid_word("count", letters_set, required) is True
        assert validator.is_valid_word("anton", letters_set, required) is True

        # Too short
        assert validator.is_valid_word("ant", letters_set, required) is False

        # Missing required letter
        assert validator.is_valid_word("auto", letters_set, required) is False

        # Invalid letter
        assert validator.is_valid_word("noun", letters_set, required) is True
        assert validator.is_valid_word("nouns", letters_set, required) is False  # 's' not in set

        # Non-alphabetic should error
        with pytest.raises(ValueError, match="only alphabetic"):
            validator.is_valid_word("no-un", letters_set, required)

    def test_constants(self):
        """Test that constants match Python version"""
        assert MIN_WORD_LENGTH == 4
        assert PUZZLE_LETTER_COUNT == 7

    def test_version(self):
        """Test version info"""
        validator = InputValidator()
        version = validator.__version__()
        assert version == "0.1.0"


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust module not built")
class TestRustPythonEquivalence:
    """Test that Rust and Python implementations are equivalent"""

    def test_error_messages_match(self):
        """Verify error messages are similar between Rust and Python"""
        from src.spelling_bee_solver.core.input_validator import (
            InputValidator as PythonValidator
        )

        rust_validator = InputValidator()
        python_validator = PythonValidator()

        # Test too short
        try:
            rust_validator.validate_letters("ABC")
            rust_error = None
        except ValueError as e:
            rust_error = str(e)

        try:
            python_validator.validate_letters("ABC")
            python_error = None
        except ValueError as e:
            python_error = str(e)

        assert rust_error is not None
        assert python_error is not None
        # Both should mention "7 characters"
        assert "7" in rust_error and "7" in python_error


if __name__ == "__main__":
    if RUST_AVAILABLE:
        print("✅ Rust module loaded successfully")
        print(f"   MIN_WORD_LENGTH = {MIN_WORD_LENGTH}")
        print(f"   PUZZLE_LETTER_COUNT = {PUZZLE_LETTER_COUNT}")

        # Run a quick test
        validator = InputValidator()
        print(f"\n🧪 Quick test:")
        print(f"   validate_letters('NACUOTP') = {validator.validate_letters('NACUOTP')}")
        print(f"   validate_required_letter('N', 'nacuotp') = {validator.validate_required_letter('N', 'nacuotp')}")

        print("\n🚀 Run full tests with: pytest python_tests/test_integration.py -v")
    else:
        print("❌ Rust module not available")
        print("   Build it with: maturin develop")

"""
Input Validator - Single Responsibility: Validate Puzzle Inputs

This module handles all validation logic for NYT Spelling Bee puzzle inputs,
following the Single Responsibility Principle by separating validation concerns
from solving logic.

Simplified Rules (NYT Spelling Bee Standard):
- Puzzle letters: Exactly 7 UNIQUE characters (a-z only, case-insensitive)
- Center letter: Exactly 1 character (a-z only, must be one of the 7 puzzle letters)
- Words: Minimum 4 letters, must contain center letter, only use puzzle letters

Responsibilities:
- Validate puzzle letters (7 unique alphabetic characters, no duplicates)
- Validate required/center letter (1 alphabetic character in puzzle letters)
- Validate individual words against puzzle rules
- Normalize inputs (lowercase conversion, whitespace handling)
"""

from typing import Set, Tuple

from ..constants import MIN_WORD_LENGTH, PUZZLE_LETTER_COUNT, REQUIRED_LETTER_COUNT


class InputValidator:
    """
    Validates NYT Spelling Bee puzzle inputs.

    This class encapsulates all validation logic for puzzle parameters,
    ensuring consistent error handling and clear error messages.
    """

    def validate_letters(self, letters: str) -> str:
        """
        Validate and normalize puzzle letters.

        Simplified rules (NYT Spelling Bee standard):
        - Must be exactly 7 characters
        - Only a-z letters (case-insensitive)
        - Must be 7 UNIQUE letters (no duplicates)

        Args:
            letters: The 7 puzzle letters

        Returns:
            Normalized letters (lowercase)

        Raises:
            TypeError: If letters is not a string
            ValueError: If letters is invalid (wrong length, non-alphabetic, duplicates)
        """
        # Type validation
        if letters is None:
            raise ValueError("Letters parameter cannot be None")

        if not isinstance(letters, str):
            raise TypeError(f"Letters must be a string, got {type(letters).__name__}")

        # Length validation
        if len(letters) != PUZZLE_LETTER_COUNT:
            raise ValueError(
                f"Letters must be exactly {PUZZLE_LETTER_COUNT} characters, "
                f"got {len(letters)}"
            )

        # Character validation - ONLY a-z allowed
        if not letters.isalpha():
            invalid_chars = [c for c in letters if not c.isalpha()]
            raise ValueError(
                f"Letters must contain only alphabetic characters (a-z), "
                f"found invalid: {invalid_chars}"
            )

        letters_lower = letters.lower()

        # Uniqueness validation - NYT Spelling Bee always has 7 UNIQUE letters
        unique_letters = set(letters_lower)
        if len(unique_letters) != PUZZLE_LETTER_COUNT:
            duplicate_count = len(letters_lower) - len(unique_letters)
            raise ValueError(
                f"Letters must be 7 unique characters (no duplicates), "
                f"found {duplicate_count} duplicate(s) in '{letters}'"
            )

        return letters_lower

    def validate_required_letter(
        self, required_letter: str, letters: str
    ) -> str:
        """
        Validate and normalize required letter (center letter).

        Simplified rules:
        - Must be exactly 1 character
        - Only a-z letters (case-insensitive)
        - Must be one of the 7 puzzle letters

        Args:
            required_letter: The required/center letter
            letters: The puzzle letters (already validated and lowercase)

        Returns:
            Normalized required letter (lowercase)

        Raises:
            TypeError: If required_letter is not a string
            ValueError: If required_letter is invalid
        """
        # Type validation
        if required_letter is None:
            raise ValueError("Required letter parameter cannot be None")

        if not isinstance(required_letter, str):
            raise TypeError(
                f"Required letter must be a string, got {type(required_letter).__name__}"
            )

        # Length validation - must be exactly 1 character
        if len(required_letter) != REQUIRED_LETTER_COUNT:
            raise ValueError(
                f"Required letter must be exactly {REQUIRED_LETTER_COUNT} character, "
                f"got {len(required_letter)}"
            )

        # Character validation - ONLY a-z allowed
        if not required_letter.isalpha():
            raise ValueError(
                f"Required letter must be alphabetic (a-z): '{required_letter}'"
            )

        required_lower = required_letter.lower()
        letters_lower = letters.lower()  # Handle case where letters isn't already lowercase

        # Must be one of the 7 puzzle letters
        if required_lower not in letters_lower:
            raise ValueError(
                f"Required letter '{required_letter}' must be one of the "
                f"puzzle letters: {letters}"
            )

        return required_lower

    def validate_and_normalize(
        self, letters: str, required_letter: str = None
    ) -> Tuple[str, str, Set[str]]:
        """
        Validate and normalize both puzzle inputs.

        Convenience method that validates both inputs and returns normalized values
        plus a set of available letters for efficient lookups.

        Args:
            letters: The 7 puzzle letters
            required_letter: The required letter (defaults to first letter if None)

        Returns:
            Tuple of (letters_lower, required_lower, letters_set)

        Raises:
            TypeError: If inputs are not strings
            ValueError: If inputs are invalid
        """
        # Validate letters first
        letters_lower = self.validate_letters(letters)

        # Default required letter to first puzzle letter
        if required_letter is None:
            required_letter = letters[0]

        # Validate required letter
        required_lower = self.validate_required_letter(required_letter, letters_lower)

        # Create set for efficient lookups
        letters_set = set(letters_lower)

        return letters_lower, required_lower, letters_set

    def validate_puzzle(
        self, center_letter: str, other_letters: str
    ) -> Tuple[str, str, Set[str]]:
        """
        Validate and normalize puzzle using the cleaner API.

        This is the preferred API that matches NYT Spelling Bee design:
        - 1 center letter (required in all words)
        - 6 other letters (surrounding the center)

        This design makes it IMPOSSIBLE to create invalid puzzles where
        the center letter appears multiple times in the 7-letter set.

        Args:
            center_letter: The center/required letter (1 character, a-z)
            other_letters: The 6 surrounding letters (6 unique characters, a-z,
                must NOT contain the center letter)

        Returns:
            Tuple of (all_letters_lower, center_lower, letters_set)
            where all_letters_lower = center + other_letters

        Raises:
            TypeError: If inputs are not strings
            ValueError: If inputs are invalid

        Example:
            >>> validator = InputValidator()
            >>> all_letters, center, letter_set = validator.validate_puzzle('N', 'ACUOTP')
            >>> print(all_letters)  # 'nacuotp'
            >>> print(center)        # 'n'
            >>> print(len(letter_set))  # 7
        """
        # Validate center letter
        if center_letter is None:
            raise ValueError("Center letter parameter cannot be None")

        if not isinstance(center_letter, str):
            raise TypeError(
                f"Center letter must be a string, got {type(center_letter).__name__}"
            )

        if len(center_letter) != 1:
            raise ValueError(
                f"Center letter must be exactly 1 character, got {len(center_letter)}"
            )

        if not center_letter.isalpha():
            raise ValueError(
                f"Center letter must be alphabetic (a-z): '{center_letter}'"
            )

        center_lower = center_letter.lower()

        # Validate other letters
        if other_letters is None:
            raise ValueError("Other letters parameter cannot be None")

        if not isinstance(other_letters, str):
            raise TypeError(
                f"Other letters must be a string, got {type(other_letters).__name__}"
            )

        if len(other_letters) != 6:
            raise ValueError(
                f"Other letters must be exactly 6 characters, got {len(other_letters)}"
            )

        if not other_letters.isalpha():
            raise ValueError(
                f"Other letters must contain only alphabetic characters (a-z), "
                f"found invalid: {[c for c in other_letters if not c.isalpha()]}"
            )

        other_lower = other_letters.lower()

        # Check that other letters are unique (no duplicates)
        if len(set(other_lower)) != 6:
            duplicate_count = 6 - len(set(other_lower))
            raise ValueError(
                f"Other letters must be 6 unique characters (no duplicates), "
                f"found {duplicate_count} duplicate(s) in '{other_letters}'"
            )

        # Check that center letter is NOT in other letters
        if center_lower in other_lower:
            raise ValueError(
                f"Center letter '{center_letter}' must NOT appear in other letters '{other_letters}'. "
                f"The center letter should be separate from the 6 surrounding letters."
            )

        # Combine into full 7-letter set
        all_letters_lower = center_lower + other_lower
        letters_set = set(all_letters_lower)

        return all_letters_lower, center_lower, letters_set

    def is_valid_word(
        self,
        word: str,
        letters_set: Set[str],
        required_letter: str
    ) -> bool:
        """
        Check if a word is valid according to puzzle rules.

        This performs basic validation:
        - Word length >= MIN_WORD_LENGTH
        - Contains required letter
        - All letters from available set

        Args:
            word: The word to validate
            letters_set: Set of available letters (lowercase)
            required_letter: The required letter (lowercase)

        Returns:
            True if word meets basic validation criteria

        Raises:
            TypeError: If word is not a string
            ValueError: If word format is invalid
        """
        # Type validation
        if not isinstance(word, str):
            raise TypeError(f"Word must be a string, got {type(word).__name__}")

        # Content validation
        if not word.strip():
            raise ValueError("Word cannot be empty or whitespace")

        if not word.isalpha():
            raise ValueError(
                f"Word must contain only alphabetic characters: '{word}'"
            )

        word_lower = word.lower()

        # Length check
        if len(word_lower) < MIN_WORD_LENGTH:
            return False

        # Required letter check
        if required_letter not in word_lower:
            return False

        # Available letters check
        if not set(word_lower).issubset(letters_set):
            return False

        return True


def create_input_validator() -> InputValidator:
    """
    Factory function to create an InputValidator.

    Returns:
        A new InputValidator instance
    """
    return InputValidator()

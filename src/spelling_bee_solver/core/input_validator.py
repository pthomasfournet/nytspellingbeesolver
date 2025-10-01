"""
Input Validator - Single Responsibility: Validate Puzzle Inputs

This module handles all validation logic for NYT Spelling Bee puzzle inputs,
following the Single Responsibility Principle by separating validation concerns
from solving logic.

Responsibilities:
- Validate puzzle letters (7 alphabetic characters)
- Validate required letter (1 alphabetic character in puzzle letters)
- Validate individual words against puzzle rules
- Normalize inputs (lowercase conversion, whitespace handling)
"""

from typing import Tuple, Set


class InputValidator:
    """
    Validates NYT Spelling Bee puzzle inputs.
    
    This class encapsulates all validation logic for puzzle parameters,
    ensuring consistent error handling and clear error messages.
    """
    
    # Constants for NYT Spelling Bee rules
    PUZZLE_LETTER_COUNT = 7
    REQUIRED_LETTER_COUNT = 1
    MIN_WORD_LENGTH = 4
    
    def validate_letters(self, letters: str) -> str:
        """
        Validate and normalize puzzle letters.
        
        Args:
            letters: The 7 puzzle letters
            
        Returns:
            Normalized letters (lowercase)
            
        Raises:
            TypeError: If letters is not a string
            ValueError: If letters is invalid (wrong length, non-alphabetic)
        """
        # Type validation
        if letters is None:
            raise ValueError("Letters parameter cannot be None")
        
        if not isinstance(letters, str):
            raise TypeError(f"Letters must be a string, got {type(letters).__name__}")
        
        # Length validation
        if len(letters) != self.PUZZLE_LETTER_COUNT:
            raise ValueError(
                f"Letters must be exactly {self.PUZZLE_LETTER_COUNT} characters, "
                f"got {len(letters)}"
            )
        
        # Character validation
        if not letters.isalpha():
            invalid_chars = [c for c in letters if not c.isalpha()]
            raise ValueError(
                f"Letters must contain only alphabetic characters, "
                f"found invalid: {invalid_chars}"
            )
        
        return letters.lower()
    
    def validate_required_letter(
        self, required_letter: str, letters: str
    ) -> str:
        """
        Validate and normalize required letter.
        
        Args:
            required_letter: The required letter
            letters: The puzzle letters (already validated)
            
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
        
        # Length validation
        if len(required_letter) != self.REQUIRED_LETTER_COUNT:
            raise ValueError(
                f"Required letter must be exactly {self.REQUIRED_LETTER_COUNT} character, "
                f"got {len(required_letter)}"
            )
        
        # Character validation
        if not required_letter.isalpha():
            raise ValueError(
                f"Required letter must be alphabetic: '{required_letter}'"
            )
        
        # Check it's in puzzle letters
        required_lower = required_letter.lower()
        letters_lower = letters.lower()
        
        if required_lower not in letters_lower:
            raise ValueError(
                f"Required letter '{required_letter}' must be one of the "
                f"{self.PUZZLE_LETTER_COUNT} puzzle letters: {letters}"
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
        if len(word_lower) < self.MIN_WORD_LENGTH:
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

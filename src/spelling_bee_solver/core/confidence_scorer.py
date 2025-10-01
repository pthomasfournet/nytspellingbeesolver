"""
Confidence Scorer - Single Responsibility: Score Word Confidence

This module handles confidence scoring for NYT Spelling Bee puzzle solutions,
following the Single Responsibility Principle by separating scoring logic
from solving logic.

Responsibilities:
- Calculate confidence scores for individual words
- Apply length-based bonuses
- Apply rejection penalties
- Score multiple words efficiently
- Normalize scores to 0-100 range
"""

from typing import Dict, List, Tuple, Callable, Optional


class ConfidenceScorer:
    """
    Calculates confidence scores for Spelling Bee words.
    
    This class encapsulates scoring logic, providing consistent and
    configurable confidence assessment for puzzle solutions.
    
    Scoring Algorithm:
        Base Score: 50.0
        + Length Bonus: +10.0 for words >= 6 letters
        - Rejection Penalty: -30.0 for likely rejected words
        = Final Score: clamped to [0.0, 100.0]
    """
    
    # Constants for scoring algorithm
    CONFIDENCE_BASE = 50.0
    CONFIDENCE_LENGTH_BONUS = 10.0
    CONFIDENCE_REJECTION_PENALTY = 30.0
    LENGTH_BONUS_THRESHOLD = 6
    
    def __init__(
        self,
        rejection_checker: Optional[Callable[[str], bool]] = None,
        base_score: float = CONFIDENCE_BASE,
        length_bonus: float = CONFIDENCE_LENGTH_BONUS,
        rejection_penalty: float = CONFIDENCE_REJECTION_PENALTY
    ):
        """
        Initialize the ConfidenceScorer.
        
        Args:
            rejection_checker: Optional callable that returns True if word
                             is likely to be rejected. If None, no rejection
                             penalty is applied.
            base_score: Base confidence score for all words (default: 50.0)
            length_bonus: Bonus for longer words (default: 10.0)
            rejection_penalty: Penalty for rejected words (default: 30.0)
        
        Example:
            # Default scorer (no rejection checking)
            scorer = ConfidenceScorer()
            
            # With rejection checker
            def my_checker(word: str) -> bool:
                return word in REJECTED_WORDS
            scorer = ConfidenceScorer(rejection_checker=my_checker)
            
            # Custom scoring parameters
            scorer = ConfidenceScorer(base_score=60.0, length_bonus=15.0)
        """
        self.rejection_checker = rejection_checker
        self.base_score = base_score
        self.length_bonus = length_bonus
        self.rejection_penalty = rejection_penalty
    
    def calculate_confidence(self, word: str) -> float:
        """
        Calculate confidence score for a word.
        
        The confidence score reflects how likely the word is to be a valid
        Spelling Bee answer based on length and rejection criteria.
        
        Args:
            word: The word to score
            
        Returns:
            Confidence score between 0.0 and 100.0
            
        Raises:
            TypeError: If word is not a string
            ValueError: If word is empty or contains non-alphabetic characters
        
        Example:
            scorer = ConfidenceScorer()
            
            score = scorer.calculate_confidence("test")
            # score == 50.0 (base only)
            
            score = scorer.calculate_confidence("testing")
            # score == 60.0 (base + length bonus)
        """
        # Input validation
        if not isinstance(word, str):
            raise TypeError(f"Word must be a string, got {type(word).__name__}")
        
        if not word.strip():
            raise ValueError("Word cannot be empty or whitespace")
        
        if not word.isalpha():
            raise ValueError(f"Word must contain only alphabetic characters: '{word}'")
        
        word = word.lower()
        confidence = self.base_score
        
        # Length-based confidence
        if len(word) >= self.LENGTH_BONUS_THRESHOLD:
            confidence += self.length_bonus
        
        # Penalize likely rejected words
        if self.rejection_checker and self.rejection_checker(word):
            confidence -= self.rejection_penalty
        
        # Clamp to valid range
        return min(100.0, max(0.0, confidence))
    
    def score_words(self, words: List[str]) -> Dict[str, float]:
        """
        Calculate confidence scores for multiple words.
        
        Args:
            words: List of words to score
            
        Returns:
            Dictionary mapping words to their confidence scores
            
        Raises:
            TypeError: If words is not a list or contains non-strings
            ValueError: If any word is invalid
        
        Example:
            scorer = ConfidenceScorer()
            words = ["test", "testing", "example"]
            scores = scorer.score_words(words)
            # scores == {
            #     "test": 50.0,
            #     "testing": 60.0,
            #     "example": 60.0
            # }
        """
        if not isinstance(words, list):
            raise TypeError(f"Words must be a list, got {type(words).__name__}")
        
        scores = {}
        for word in words:
            scores[word] = self.calculate_confidence(word)
        
        return scores
    
    def score_and_sort(
        self,
        words: List[str],
        reverse: bool = True
    ) -> List[Tuple[str, float]]:
        """
        Score words and return sorted list of (word, score) tuples.
        
        Args:
            words: List of words to score
            reverse: If True, sort highest scores first (default: True)
            
        Returns:
            List of (word, score) tuples sorted by score
            
        Raises:
            TypeError: If words is not a list or contains non-strings
            ValueError: If any word is invalid
        
        Example:
            scorer = ConfidenceScorer()
            words = ["test", "testing", "example"]
            sorted_results = scorer.score_and_sort(words)
            # sorted_results == [
            #     ("testing", 60.0),
            #     ("example", 60.0),
            #     ("test", 50.0)
            # ]
        """
        scores = self.score_words(words)
        return sorted(scores.items(), key=lambda x: x[1], reverse=reverse)
    
    def filter_by_confidence(
        self,
        words: List[str],
        min_confidence: float
    ) -> List[str]:
        """
        Filter words by minimum confidence threshold.
        
        Args:
            words: List of words to filter
            min_confidence: Minimum confidence score (0.0-100.0)
            
        Returns:
            List of words meeting the minimum confidence threshold
            
        Raises:
            TypeError: If words is not a list or min_confidence not a number
            ValueError: If min_confidence is out of range or any word is invalid
        
        Example:
            scorer = ConfidenceScorer()
            words = ["test", "testing", "example"]
            filtered = scorer.filter_by_confidence(words, min_confidence=55.0)
            # filtered == ["testing", "example"]
        """
        if not isinstance(words, list):
            raise TypeError(f"Words must be a list, got {type(words).__name__}")
        
        if not isinstance(min_confidence, (int, float)):
            raise TypeError(
                f"min_confidence must be a number, got {type(min_confidence).__name__}"
            )
        
        if not 0.0 <= min_confidence <= 100.0:
            raise ValueError(
                f"min_confidence must be between 0.0 and 100.0, got {min_confidence}"
            )
        
        scores = self.score_words(words)
        return [word for word, score in scores.items() if score >= min_confidence]


def create_confidence_scorer(
    rejection_checker: Optional[Callable[[str], bool]] = None,
    **kwargs
) -> ConfidenceScorer:
    """
    Factory function to create a ConfidenceScorer.
    
    Args:
        rejection_checker: Optional callable for rejection checking
        **kwargs: Additional parameters passed to ConfidenceScorer
        
    Returns:
        A new ConfidenceScorer instance
    
    Example:
        # Simple scorer
        scorer = create_confidence_scorer()
        
        # With rejection checker
        def check_rejected(word: str) -> bool:
            return word in ["bad", "ugly"]
        scorer = create_confidence_scorer(rejection_checker=check_rejected)
        
        # With custom parameters
        scorer = create_confidence_scorer(base_score=60.0, length_bonus=15.0)
    """
    return ConfidenceScorer(rejection_checker=rejection_checker, **kwargs)

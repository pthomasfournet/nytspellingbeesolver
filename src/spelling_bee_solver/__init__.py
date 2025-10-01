"""
Spelling Bee Solver - A GPU-accelerated word puzzle solver.

This package provides comprehensive tools for solving New York Times Spelling Bee puzzles
with GPU acceleration and advanced word filtering capabilities.
"""

from .unified_solver import UnifiedSpellingBeeSolver, SolverMode
from .word_filtering import (
    is_likely_nyt_rejected,
    filter_words,
    get_word_confidence,
    is_proper_noun,
    filter_inappropriate_words
)

__version__ = "2.0.0"
__author__ = "Tom"
__email__ = "tom@example.com"

__all__ = [
    "UnifiedSpellingBeeSolver",
    "SolverMode", 
    "is_likely_nyt_rejected",
    "filter_words",
    "get_word_confidence",
    "is_proper_noun",
    "filter_inappropriate_words"
]
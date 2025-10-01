"""
Spelling Bee Solver - A GPU-accelerated word puzzle solver.

This package provides comprehensive tools for solving New York Times Spelling Bee puzzles
with GPU acceleration and advanced word filtering capabilities.
"""

from .unified_solver import SolverMode, UnifiedSpellingBeeSolver
from .word_filtering import (
    filter_inappropriate_words,
    filter_words,
    get_word_confidence,
    is_likely_nyt_rejected,
    is_proper_noun,
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
    "filter_inappropriate_words",
]

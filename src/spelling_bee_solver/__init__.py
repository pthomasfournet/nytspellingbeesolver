"""
Spelling Bee Solver - A GPU-accelerated word puzzle solver.

This package provides comprehensive tools for solving New York Times Spelling Bee puzzles
with GPU acceleration and advanced word filtering capabilities.
"""

from .core import (
    CandidateGenerator,
    ConfidenceScorer,
    DictionaryManager,
    InputValidator,
    NYTRejectionFilter,
    PhonotacticFilter,
    ResultFormatter,
)
from .unified_solver import UnifiedSpellingBeeSolver

__version__ = "2.0.0"
__author__ = "Tom"
__email__ = "tom@example.com"

__all__ = [
    "UnifiedSpellingBeeSolver",
    "NYTRejectionFilter",
    "ConfidenceScorer",
    "CandidateGenerator",
    "DictionaryManager",
    "InputValidator",
    "ResultFormatter",
    "PhonotacticFilter",
]

"""
Core Components Package

This package contains extracted, focused components from the unified solver,
following the Single Responsibility Principle.

Each component has a single, well-defined responsibility:
- InputValidator: Validates puzzle inputs
- DictionaryManager: Manages word dictionaries
- (Future) CandidateGenerator: Generates candidate words
- (Future) ConfidenceScorer: Scores word confidence
- (Future) ResultFormatter: Formats output
"""

from .input_validator import InputValidator, create_input_validator
from .dictionary_manager import DictionaryManager, create_dictionary_manager

__all__ = [
    'InputValidator',
    'create_input_validator',
    'DictionaryManager',
    'create_dictionary_manager',
]

"""Core components for Spelling Bee solver.

This package provides the fundamental building blocks for the Spelling Bee solver,
following SOLID principles with clean separation of concerns.
"""

from .input_validator import InputValidator, create_input_validator
from .dictionary_manager import DictionaryManager, create_dictionary_manager
from .confidence_scorer import ConfidenceScorer, create_confidence_scorer
from .candidate_generator import CandidateGenerator, create_candidate_generator
from .result_formatter import ResultFormatter, create_result_formatter, OutputFormat

__all__ = [
    'InputValidator',
    'create_input_validator',
    'DictionaryManager',
    'create_dictionary_manager',
    'ConfidenceScorer',
    'create_confidence_scorer',
    'CandidateGenerator',
    'create_candidate_generator',
    'ResultFormatter',
    'create_result_formatter',
    'OutputFormat',
]

"""
NLP Provider Abstraction Package

This package provides an abstraction layer for NLP (Natural Language Processing)
providers, implementing the Dependency Inversion Principle.

Public API:
- NLPProvider: Abstract base class for NLP providers
- Document, Token, Entity: Abstract data classes
- SpacyNLPProvider: spaCy implementation
- MockNLPProvider: Mock implementation for testing
- Factory functions: create_spacy_provider, create_mock_provider
"""

from .nlp_provider import NLPProvider, Document, Token, Entity
from .spacy_provider import SpacyNLPProvider, create_spacy_provider
from .mock_provider import MockNLPProvider, create_mock_provider

__all__ = [
    # Abstract interfaces
    'NLPProvider',
    'Document',
    'Token',
    'Entity',
    # Concrete implementations
    'SpacyNLPProvider',
    'MockNLPProvider',
    # Factory functions
    'create_spacy_provider',
    'create_mock_provider',
]

"""
NLP Provider Abstraction Layer

This module defines abstract interfaces for NLP (Natural Language Processing) providers,
allowing the word filtering system to work with different NLP backends without tight coupling.

Design Pattern: Dependency Inversion Principle (DIP)
- High-level modules (IntelligentWordFilter) depend on abstractions (NLPProvider)
- Low-level modules (SpacyNLPProvider) depend on abstractions
- Both can vary independently

Benefits:
- Decouple from spaCy: Can swap to other NLP backends (NLTK, Stanza, transformers)
- Easier testing: Can use MockNLPProvider instead of loading real models
- Flexibility: Support multiple backends simultaneously
- Maintainability: Changes to spaCy API don't affect core logic
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Token:
    """
    Abstract representation of a linguistic token.
    
    This is a backend-agnostic representation that any NLP provider can produce.
    """
    text: str
    """The text of the token"""
    
    pos: str
    """Part of speech tag (e.g., 'NOUN', 'VERB', 'PROPN')"""
    
    is_proper_noun: bool
    """Whether this token is a proper noun"""
    
    is_oov: bool
    """Whether this token is out-of-vocabulary (unknown to the model)"""
    
    lemma: Optional[str] = None
    """Base form of the token (optional)"""


@dataclass
class Entity:
    """
    Abstract representation of a named entity.
    
    Named entities are real-world objects like people, organizations, locations.
    """
    text: str
    """The text of the entity"""
    
    label: str
    """Entity type label (e.g., 'PERSON', 'ORG', 'GPE', 'NORP')"""
    
    start: int = 0
    """Start character position in original text"""
    
    end: int = 0
    """End character position in original text"""


class Document(ABC):
    """
    Abstract document representation produced by NLP processing.
    
    This provides a unified interface for accessing linguistic analysis results
    regardless of which NLP backend is used.
    """
    
    @abstractmethod
    def get_tokens(self) -> List[Token]:
        """
        Get list of tokens in the document.
        
        Returns:
            List of Token objects representing the linguistic tokens
        """
        pass
    
    @abstractmethod
    def get_entities(self) -> List[Entity]:
        """
        Get list of named entities in the document.
        
        Returns:
            List of Entity objects representing named entities
        """
        pass
    
    @abstractmethod
    def find_token(self, text: str) -> Optional[Token]:
        """
        Find a specific token by text (case-insensitive).
        
        Args:
            text: The token text to search for
            
        Returns:
            The Token if found, None otherwise
        """
        pass
    
    @abstractmethod
    def has_proper_noun(self, word: str) -> bool:
        """
        Check if a specific word is tagged as a proper noun.
        
        Args:
            word: The word to check
            
        Returns:
            True if the word is a proper noun
        """
        pass
    
    @abstractmethod
    def has_entity_type(self, word: str, entity_types: List[str]) -> bool:
        """
        Check if a word is part of an entity with one of the given types.
        
        Args:
            word: The word to check
            entity_types: List of entity type labels to check (e.g., ['PERSON', 'ORG'])
            
        Returns:
            True if the word is part of a matching entity
        """
        pass


class NLPProvider(ABC):
    """
    Abstract NLP provider interface.
    
    This is the main abstraction that allows swapping between different NLP backends.
    Any NLP backend (spaCy, NLTK, Stanza, transformers, etc.) can implement this interface.
    
    Example:
        >>> provider = SpacyNLPProvider()
        >>> doc = provider.process_text("The Apple is red.")
        >>> tokens = doc.get_tokens()
        >>> for token in tokens:
        ...     print(f"{token.text}: {token.pos}")
    """
    
    @abstractmethod
    def process_text(self, text: str) -> Document:
        """
        Process text and return a document with linguistic analysis.
        
        This is the main entry point for NLP processing. The implementation
        should perform tokenization, POS tagging, and named entity recognition.
        
        Args:
            text: The text to process
            
        Returns:
            A Document object with analysis results
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the NLP backend is available and functional.
        
        This allows graceful fallback when dependencies are missing or
        models aren't installed.
        
        Returns:
            True if the provider is ready to use
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Get the name/description of this NLP provider.
        
        Used for logging and debugging.
        
        Returns:
            A human-readable name for this provider
        """
        pass
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"<{self.__class__.__name__}: {self.get_name()}>"

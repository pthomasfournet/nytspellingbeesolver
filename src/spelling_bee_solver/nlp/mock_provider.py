"""
Mock NLP Provider Implementation

This module provides a mock implementation of the NLP provider interface
for testing purposes. It doesn't require any external dependencies or
model files.

The mock provider is useful for:
- Unit testing without loading heavy NLP models
- Fast test execution
- Deterministic testing behavior
- Testing error handling and edge cases
"""

import logging
from typing import List, Optional, Set

from .nlp_provider import Document, Entity, NLPProvider, Token

logger = logging.getLogger(__name__)


class MockDocument(Document):
    """
    Mock implementation of the Document interface.

    Provides configurable, deterministic responses for testing.
    """

    def __init__(
        self,
        text: str,
        tokens: Optional[List[Token]] = None,
        entities: Optional[List[Entity]] = None
    ):
        """
        Initialize with mock data.

        Args:
            text: The original text
            tokens: List of Token objects (if None, creates simple tokens)
            entities: List of Entity objects (if None, uses empty list)
        """
        self.text = text
        self._tokens = tokens or []
        self._entities = entities or []

    def get_tokens(self) -> List[Token]:
        """Get list of mock tokens"""
        return self._tokens

    def get_entities(self) -> List[Entity]:
        """Get list of mock entities"""
        return self._entities

    def find_token(self, text: str) -> Optional[Token]:
        """Find a specific token by text (case-insensitive)"""
        text_lower = text.lower()
        for token in self._tokens:
            if token.text.lower() == text_lower:
                return token
        return None

    def has_proper_noun(self, word: str) -> bool:
        """Check if a specific word is tagged as a proper noun"""
        token = self.find_token(word)
        return token is not None and token.is_proper_noun

    def has_entity_type(self, word: str, entity_types: List[str]) -> bool:
        """Check if a word is part of an entity with one of the given types"""
        word_lower = word.lower()
        for entity in self._entities:
            if word_lower in entity.text.lower():
                if entity.label in entity_types:
                    return True
        return False


class MockNLPProvider(NLPProvider):
    """
    Mock implementation of the NLP provider for testing.

    This provider doesn't actually perform NLP - it uses configurable
    rules to simulate NLP behavior in a fast, deterministic way.

    Example:
        >>> provider = MockNLPProvider()
        >>> provider.proper_nouns = {"NASA", "London"}
        >>> doc = provider.process_text("NASA is in London")
        >>> assert doc.has_proper_noun("NASA")
        >>> assert doc.has_proper_noun("London")
        >>> assert not doc.has_proper_noun("in")
    """

    def __init__(self):
        """Initialize the mock provider with empty configuration"""
        self.proper_nouns: Set[str] = set()
        """Set of words to treat as proper nouns (case-insensitive)"""

        self.entities: List[tuple] = []
        """List of (text, label) tuples for named entities"""

        self.processed_texts: List[str] = []
        """Track all texts processed (useful for test assertions)"""

        self._available = True
        """Whether this provider is available"""

    def process_text(self, text: str) -> Document:
        """
        Process text using mock rules.

        Creates tokens and entities based on the configured proper_nouns
        and entities sets.

        Args:
            text: The text to process

        Returns:
            A MockDocument with simulated NLP results
        """
        # Track for testing
        self.processed_texts.append(text)

        # Simple word tokenization
        words = text.split()

        # Create tokens
        tokens = [
            Token(
                text=word,
                pos="PROPN" if self._is_proper_noun(word) else "NOUN",
                is_proper_noun=self._is_proper_noun(word),
                is_oov=False,
                lemma=word.lower()
            )
            for word in words
        ]

        # Create entities
        entities = [
            Entity(text=ent_text, label=label)
            for ent_text, label in self.entities
            if ent_text.lower() in text.lower()
        ]

        return MockDocument(text, tokens, entities)

    def _is_proper_noun(self, word: str) -> bool:
        """Check if a word should be treated as a proper noun"""
        # Check against configured proper nouns (case-insensitive)
        return word.lower() in {pn.lower() for pn in self.proper_nouns}

    def is_available(self) -> bool:
        """
        Check if the mock provider is available.

        Always returns True unless explicitly disabled for testing.
        """
        return self._available

    def get_name(self) -> str:
        """Get the name of this provider"""
        return "Mock NLP Provider (for testing)"

    def reset(self):
        """Reset the mock provider state (useful between tests)"""
        self.proper_nouns.clear()
        self.entities.clear()
        self.processed_texts.clear()
        self._available = True

    def add_proper_noun(self, word: str):
        """
        Add a word to be treated as a proper noun.

        Args:
            word: The word to add
        """
        self.proper_nouns.add(word)

    def add_entity(self, text: str, label: str):
        """
        Add a named entity.

        Args:
            text: The entity text
            label: The entity type (e.g., 'PERSON', 'ORG', 'GPE')
        """
        self.entities.append((text, label))

    def set_unavailable(self):
        """Make this provider report as unavailable (for testing error handling)"""
        self._available = False


def create_mock_provider() -> MockNLPProvider:
    """
    Factory function to create a mock NLP provider.

    Returns:
        A new MockNLPProvider instance
    """
    return MockNLPProvider()

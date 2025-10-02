"""
spaCy NLP Provider Implementation

This module provides a concrete implementation of the NLP provider interface
using spaCy as the backend.

spaCy is a fast, production-ready NLP library with excellent support for
named entity recognition, part-of-speech tagging, and GPU acceleration.
"""

import logging
from typing import List, Optional

from .nlp_provider import Document, Entity, NLPProvider, Token

logger = logging.getLogger(__name__)


class SpacyDocument(Document):
    """
    spaCy implementation of the Document interface.

    Wraps a spaCy Doc object and provides the abstract interface.
    """

    def __init__(self, spacy_doc):
        """
        Initialize with a spaCy Doc object.

        Args:
            spacy_doc: A spacy.tokens.Doc object
        """
        self._doc = spacy_doc

    def get_tokens(self) -> List[Token]:
        """Get list of tokens from spaCy doc"""
        return [
            Token(
                text=token.text,
                pos=token.pos_,
                is_proper_noun=(token.pos_ == "PROPN"),
                is_oov=token.is_oov,
                lemma=token.lemma_
            )
            for token in self._doc
        ]

    def get_entities(self) -> List[Entity]:
        """Get list of named entities from spaCy doc"""
        return [
            Entity(
                text=ent.text,
                label=ent.label_,
                start=ent.start_char,
                end=ent.end_char
            )
            for ent in self._doc.ents
        ]

    def find_token(self, text: str) -> Optional[Token]:
        """Find a specific token by text (case-insensitive)"""
        text_lower = text.lower()
        for token in self._doc:
            if token.text.lower() == text_lower:
                return Token(
                    text=token.text,
                    pos=token.pos_,
                    is_proper_noun=(token.pos_ == "PROPN"),
                    is_oov=token.is_oov,
                    lemma=token.lemma_
                )
        return None

    def has_proper_noun(self, word: str) -> bool:
        """Check if a specific word is tagged as a proper noun"""
        token = self.find_token(word)
        return token is not None and token.is_proper_noun

    def has_entity_type(self, word: str, entity_types: List[str]) -> bool:
        """Check if a word is part of an entity with one of the given types"""
        word_lower = word.lower()
        for entity in self.get_entities():
            if word_lower in entity.text.lower():
                if entity.label in entity_types:
                    return True
        return False


class SpacyNLPProvider(NLPProvider):
    """
    spaCy implementation of the NLP provider.

    This provider uses spaCy models for NLP processing. It supports:
    - Multiple spaCy models (sm, md, lg)
    - GPU acceleration via spacy.require_gpu()
    - Lazy loading of models
    - Configurable max text length

    Example:
        >>> provider = SpacyNLPProvider(model_name="en_core_web_md", use_gpu=True)
        >>> doc = provider.process_text("Apple Inc. is in California.")
        >>> entities = doc.get_entities()
        >>> print([(e.text, e.label) for e in entities])
        [('Apple Inc.', 'ORG'), ('California', 'GPE')]
    """

    def __init__(
        self,
        model_name: str = "en_core_web_md",
        use_gpu: bool = True,
        max_length: int = 2_000_000
    ):
        """
        Initialize the spaCy NLP provider.

        Args:
            model_name: Name of the spaCy model to load (e.g., 'en_core_web_md')
            use_gpu: Whether to attempt GPU acceleration
            max_length: Maximum text length to process
        """
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.max_length = max_length
        self._nlp = None
        self._gpu_attempted = False

    def _load_model(self):
        """Lazy load the spaCy model"""
        if self._nlp is not None:
            return

        try:
            import spacy

            # Attempt GPU acceleration if requested
            if self.use_gpu and not self._gpu_attempted:
                try:
                    spacy.require_gpu()
                    logger.info("✓ spaCy GPU acceleration enabled")
                except Exception as e:
                    logger.info("✗ GPU acceleration not available: %s", e)
                finally:
                    self._gpu_attempted = True

            # Load the model
            logger.info("Loading spaCy model: %s", self.model_name)
            self._nlp = spacy.load(self.model_name)
            self._nlp.max_length = self.max_length
            logger.info("✓ Loaded %s model", self.model_name)

        except ImportError:
            logger.debug("spaCy is not installed. Install with: pip install spacy")
            raise
        except OSError:
            logger.error(
                "spaCy model '%s' not found. Install with: python -m spacy download %s",
                self.model_name,
                self.model_name
            )
            raise

    def process_text(self, text: str) -> Document:
        """
        Process text using spaCy and return a Document.

        Args:
            text: The text to process

        Returns:
            A SpacyDocument wrapping the spaCy Doc object
        """
        self._load_model()

        if not text or not text.strip():
            # Handle empty text gracefully
            text = "empty"

        doc = self._nlp(text)
        return SpacyDocument(doc)

    def is_available(self) -> bool:
        """
        Check if spaCy and the model are available.

        Returns:
            True if spaCy can be imported and the model loaded
        """
        try:
            self._load_model()
            return self._nlp is not None
        except Exception:
            return False

    def get_name(self) -> str:
        """Get the name of this provider"""
        gpu_status = " (GPU)" if self.use_gpu else " (CPU)"
        return f"spaCy ({self.model_name}){gpu_status}"


def create_spacy_provider(
    model_name: str = "en_core_web_md",
    use_gpu: bool = True
) -> SpacyNLPProvider:
    """
    Factory function to create a spaCy NLP provider.

    Args:
        model_name: Name of the spaCy model to use
        use_gpu: Whether to attempt GPU acceleration

    Returns:
        A configured SpacyNLPProvider instance
    """
    return SpacyNLPProvider(model_name=model_name, use_gpu=use_gpu)

"""
Wiktionary Metadata Loader

Pre-caches Wiktionary metadata for fast O(1) lookups during word filtering.

Loads metadata extracted from Wiktionary dump including:
- Obsolete/archaic words
- Proper nouns
- Foreign-only words
- Multi-language words

Memory footprint: ~5-10MB (pre-cached sets/dicts)
Lookup time: O(1) hash table lookups
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class WiktionaryMetadata:
    """Pre-cached Wiktionary metadata for fast word classification.

    Loads metadata from JSON database and provides O(1) lookup methods
    for checking word properties.

    Attributes:
        obsolete_words: Set of obsolete English words
        archaic_words: Set of archaic English words
        rare_words: Set of rare English words
        proper_nouns: Set of proper nouns (capitalized)
        foreign_only: Set of words with no English entry
        multi_language: Dict mapping words to list of languages
    """

    def __init__(self, metadata_path: Optional[Path] = None):
        """Initialize Wiktionary metadata loader.

        Args:
            metadata_path: Path to wiktionary_metadata.json
                         If None, uses default path in package data/
        """
        self.obsolete_words: Set[str] = set()
        self.archaic_words: Set[str] = set()
        self.rare_words: Set[str] = set()
        self.proper_nouns: Set[str] = set()
        self.foreign_only: Set[str] = set()
        self.multi_language: Dict[str, List[str]] = {}

        self.loaded = False
        self.metadata_path = metadata_path

        # Auto-load if path provided
        if metadata_path:
            self.load(metadata_path)

    def load(self, metadata_path: Optional[Path] = None):
        """Load Wiktionary metadata from JSON file.

        Args:
            metadata_path: Path to wiktionary_metadata.json
                         If None, uses default path
        """
        if metadata_path is None:
            # Default path: src/spelling_bee_solver/data/wiktionary_metadata.json
            metadata_path = Path(__file__).parent.parent / 'data' / 'wiktionary_metadata.json'

        if not metadata_path.exists():
            logger.warning(f"Wiktionary metadata not found: {metadata_path}")
            logger.warning("Wiktionary Layer 4 filtering disabled")
            logger.warning("Run: python3 wiktionary_parser/create_sample_db.py")
            return False

        try:
            with open(metadata_path, encoding='utf-8') as f:
                data = json.load(f)

            # Convert lists to sets for O(1) lookup
            self.obsolete_words = set(data.get('obsolete', []))
            self.archaic_words = set(data.get('archaic', []))
            self.rare_words = set(data.get('rare', []))
            self.proper_nouns = set(data.get('proper_nouns', []))
            self.foreign_only = set(data.get('foreign_only', []))
            self.multi_language = data.get('multi_language', {})

            self.loaded = True
            self.metadata_path = metadata_path

            # Log stats
            stats = data.get('stats', {})
            logger.info("✓ Loaded Wiktionary metadata from %s", metadata_path)
            logger.debug("  Obsolete: %d", len(self.obsolete_words))
            logger.debug("  Archaic: %d", len(self.archaic_words))
            logger.debug("  Rare: %d", len(self.rare_words))
            logger.debug("  Proper nouns: %d", len(self.proper_nouns))
            logger.debug("  Foreign-only: %d", len(self.foreign_only))
            logger.debug("  Multi-language: %d", len(self.multi_language))

            if 'note' in stats:
                logger.debug("  Note: %s", stats['note'])

            return True

        except Exception as e:
            logger.error(f"Failed to load Wiktionary metadata: {e}")
            return False

    def is_obsolete(self, word: str) -> bool:
        """Check if word is marked as obsolete in Wiktionary.

        Args:
            word: Word to check (will be lowercased)

        Returns:
            True if word is obsolete
        """
        if not self.loaded:
            return False
        return word.lower() in self.obsolete_words

    def is_archaic(self, word: str) -> bool:
        """Check if word is marked as archaic in Wiktionary.

        Args:
            word: Word to check (will be lowercased)

        Returns:
            True if word is archaic
        """
        if not self.loaded:
            return False
        return word.lower() in self.archaic_words

    def is_rare(self, word: str) -> bool:
        """Check if word is marked as rare in Wiktionary.

        Args:
            word: Word to check (will be lowercased)

        Returns:
            True if word is rare
        """
        if not self.loaded:
            return False
        return word.lower() in self.rare_words

    def is_proper_noun_wiktionary(self, word: str) -> bool:
        """Check if word is a proper noun in Wiktionary.

        Checks for capitalized version in proper nouns set.

        Args:
            word: Word to check

        Returns:
            True if capitalized version is in proper nouns
        """
        if not self.loaded:
            return False

        # Check capitalized version (proper nouns are stored capitalized)
        return word.capitalize() in self.proper_nouns

    def is_foreign_only(self, word: str) -> bool:
        """Check if word appears only in foreign language sections.

        Args:
            word: Word to check (will be lowercased)

        Returns:
            True if word has no English entry
        """
        if not self.loaded:
            return False
        return word.lower() in self.foreign_only

    def is_multi_language(self, word: str) -> bool:
        """Check if word appears in multiple languages.

        Args:
            word: Word to check (will be lowercased)

        Returns:
            True if word appears in multiple language sections
        """
        if not self.loaded:
            return False
        return word.lower() in self.multi_language

    def get_languages(self, word: str) -> List[str]:
        """Get list of languages for a multi-language word.

        Args:
            word: Word to check (will be lowercased)

        Returns:
            List of language names, empty if not multi-language
        """
        if not self.loaded:
            return []
        return self.multi_language.get(word.lower(), [])


def load_wiktionary_metadata(metadata_path: Optional[Path] = None) -> WiktionaryMetadata:
    """Factory function to load Wiktionary metadata.

    Args:
        metadata_path: Optional custom path to metadata JSON

    Returns:
        WiktionaryMetadata instance
    """
    metadata = WiktionaryMetadata()
    metadata.load(metadata_path)
    return metadata

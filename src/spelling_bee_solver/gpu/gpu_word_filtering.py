"""
GPU-accelerated word filtering using spaCy and CUDA.

This module replaces the slow NLTK-based filtering with GPU-accelerated batch processing.
Uses persistent caching to avoid reprocessing words.
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

import spacy
import torch

logger = logging.getLogger(__name__)

_GPU_FILTER = None


def get_gpu_filter():
    """Get the singleton GPU filter instance."""
    global _GPU_FILTER
    if _GPU_FILTER is None:
        _GPU_FILTER = GPUWordFilter()
    return _GPU_FILTER


class GPUWordFilter:
    """GPU-accelerated word filter using spaCy with CUDA support."""

    def __init__(self, cache_dir: str = "word_filter_cache"):
        """Initialize the GPU word filter.

        Args:
            cache_dir: Directory to store cached results
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize spaCy with GPU support
        self._init_spacy()

        # Load existing caches
        self.proper_noun_cache = self._load_cache("proper_nouns.pkl")
        self.inappropriate_cache = self._load_cache("inappropriate.pkl")
        self.valid_cache = self._load_cache("valid.pkl")

        # Stats
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "gpu_batches_processed": 0,
            "words_processed": 0,
        }

    def _init_spacy(self):
        """Initialize spaCy with GPU support if available."""
        try:
            # Load the English model
            self.nlp = spacy.load("en_core_web_sm")

            # Try to configure for GPU if available
            # self.gpu_enabled = False  # Unused attribute
            if torch.cuda.is_available():
                try:
                    # Test if CuPy is properly installed and can perform operations
                    import cupy as cp

                    test_array = cp.array([1, 2, 3])
                    _ = test_array * 2  # Simple test operation
                    spacy.require_gpu()
                    # self.gpu_enabled = True  # Unused attribute
                    logger.info(
                        "GPU acceleration enabled: %s", torch.cuda.get_device_name(0)
                    )
                except (ImportError, ValueError, RuntimeError, OSError) as gpu_error:
                    logger.warning(
                        "GPU initialization failed (%s), using optimized CPU processing",
                        gpu_error,
                    )
                    # self.gpu_enabled = False  # Unused attribute
            else:
                logger.warning("CUDA not available, using optimized CPU processing")

        except Exception as e:
            logger.error("Failed to initialize spaCy: %s", e)
            raise

    def _load_cache(self, filename: str) -> Dict[str, bool]:
        """Load cache from JSON file."""
        cache_path = Path(__file__).parent / "cache" / f"{filename}.json"
        try:
            if cache_path.exists():
                with open(cache_path, "r", encoding="utf-8") as f:
                    cache = json.load(f)
                logger.info("Loaded %d entries from %s", len(cache), filename)
                return cache
        except Exception as e:
            logger.warning("Failed to load cache %s: %s", filename, e)
        return {}

    def _save_cache(self, cache: Dict[str, bool], filename: str):
        """Save cache to JSON file."""
        cache_path = Path(__file__).parent / "cache" / f"{filename}.json"
        cache_path.parent.mkdir(exist_ok=True)
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f)
            logger.debug("Saved %d entries to %s", len(cache), filename)
        except Exception as e:
            logger.warning("Failed to save cache %s: %s", filename, e)

    def _batch_process_words(
        self, words: List[str], batch_size: int = 1000
    ) -> List[Any]:
        """Process words in batches using GPU acceleration.

        Args:
            words: List of words to process
            batch_size: Number of words per batch

        Returns:
            List of spaCy Doc objects
        """
        docs = []
        start_time = time.time()

        for i in range(0, len(words), batch_size):
            batch = words[i : i + batch_size]

            # Process batch with spaCy
            batch_docs = list(self.nlp.pipe(batch, batch_size=len(batch)))
            docs.extend(batch_docs)

            self.stats["gpu_batches_processed"] += 1

            # Log progress for large batches
            if len(words) > 1000 and (i + batch_size) % 5000 == 0:
                elapsed = time.time() - start_time
                rate = (i + batch_size) / elapsed
                logger.info(
                    "Processed %d/%d words (%.1f words/sec)",
                    i + batch_size, len(words), rate
                )

        elapsed = time.time() - start_time
        rate = len(words) / elapsed if elapsed > 0 else 0
        logger.info(
            "Batch processing complete: %d words in %.2fs (%.1f words/sec)",
            len(words), elapsed, rate
        )

        return docs

    def is_proper_noun(self, words: List[str]) -> Dict[str, bool]:
        """Check if words are proper nouns using GPU-accelerated processing.

        Args:
            words: List of words to check

        Returns:
            Dictionary mapping word -> is_proper_noun
        """
        # Check cache first
        uncached_words = []
        results = {}

        for word in words:
            if word in self.proper_noun_cache:
                results[word] = self.proper_noun_cache[word]
                self.stats["cache_hits"] += 1
            else:
                uncached_words.append(word)
                self.stats["cache_misses"] += 1

        if not uncached_words:
            return results

        logger.info(
            "Processing %d uncached words for proper noun detection",
            len(uncached_words)
        )

        # Process uncached words in batches
        docs = self._batch_process_words(uncached_words)

        # Analyze results
        for word, doc in zip(uncached_words, docs):
            # Check if any token is a proper noun (PROPN) or named entity
            # But be more selective about what we consider a proper noun
            is_proper = False

            for token in doc:
                # Only consider it a proper noun if:
                # 1. It's tagged as PROPN AND has specific entity types, OR
                # 2. It's a clear personal name or geographic location
                if token.pos_ == "PROPN" and token.ent_type_ in [
                    "PERSON",
                    "GPE",
                    "ORG",
                ]:
                    is_proper = True
                    break
                elif token.ent_type_ in [
                    "PERSON",
                    "GPE",
                ]:  # Person or geographic location
                    is_proper = True
                    break

            # Additional check: if word is all lowercase and common, it's probably not a proper noun
            if word.islower() and len(word) <= 5:
                # These are likely common words that spaCy misidentified
                is_proper = False

            results[word] = is_proper
            self.proper_noun_cache[word] = is_proper
            self.stats["words_processed"] += 1

        # Save updated cache
        self._save_cache(self.proper_noun_cache, "proper_nouns.pkl")

        return results

    def filter_proper_nouns(self, words: List[str]) -> List[str]:
        """Filter out proper nouns from a list of words.

        Args:
            words: List of words to filter

        Returns:
            List of words that are not proper nouns
        """
        proper_noun_results = self.is_proper_noun(words)
        return [word for word in words if not proper_noun_results[word]]

    def is_inappropriate_word(self, words: List[str]) -> Dict[str, bool]:
        """Check if words are inappropriate using linguistic analysis.

        This is a basic implementation that can be extended with more sophisticated
        filtering based on your specific needs.

        Args:
            words: List of words to check

        Returns:
            Dictionary mapping word -> is_inappropriate
        """
        # Check cache first
        uncached_words = []
        results = {}

        for word in words:
            if word in self.inappropriate_cache:
                results[word] = self.inappropriate_cache[word]
                self.stats["cache_hits"] += 1
            else:
                uncached_words.append(word)
                self.stats["cache_misses"] += 1

        if not uncached_words:
            return results

        logger.info(
            "Processing %d uncached words for inappropriate content",
            len(uncached_words)
        )

        # For now, implement basic checks
        # You can extend this with more sophisticated analysis
        for word in uncached_words:
            # Basic checks for obviously inappropriate content
            is_inappropriate = (
                len(word) < 2  # Too short
                or word.isdigit()  # Numbers only
                or not word.isalpha()  # Contains non-alphabetic characters
                or word.isupper()
                and len(word) > 1  # ALL CAPS (likely acronym)
            )

            results[word] = is_inappropriate
            self.inappropriate_cache[word] = is_inappropriate
            self.stats["words_processed"] += 1

        # Save updated cache
        self._save_cache(self.inappropriate_cache, "inappropriate.pkl")

        return results

    def filter_inappropriate_words(self, words: List[str]) -> List[str]:
        """Filter out inappropriate words from a list of words.

        Args:
            words: List of words to filter

        Returns:
            List of words that are appropriate
        """
        inappropriate_results = self.is_inappropriate_word(words)
        return [word for word in words if not inappropriate_results[word]]

    def comprehensive_filter(self, words: List[str]) -> List[str]:
        """Apply comprehensive filtering to remove improper words.

        Args:
            words: List of words to filter

        Returns:
            List of filtered words
        """
        start_time = time.time()
        original_count = len(words)

        logger.info("Starting comprehensive filtering of %d words", original_count)

        # Apply all filters
        words = self.filter_inappropriate_words(words)
        logger.info("After inappropriate filter: %d words remain", len(words))

        words = self.filter_proper_nouns(words)
        logger.info("After proper noun filter: %d words remain", len(words))

        elapsed = time.time() - start_time
        filtered_count = original_count - len(words)

        logger.info(
            "Filtering complete: removed %d/%d words in %.2fs",
            filtered_count, original_count, elapsed
        )

        return words

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        cache_hit_rate = (
            self.stats["cache_hits"] / total_requests if total_requests > 0 else 0
        )

        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "gpu_available": torch.cuda.is_available(),
            "gpu_name": (
                torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
            ),
        }


# Convenience functions for backward compatibility

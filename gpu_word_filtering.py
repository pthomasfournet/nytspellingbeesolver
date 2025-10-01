"""
GPU-accelerated word filtering using spaCy and CUDA.

This module replaces the slow NLTK-based filtering with GPU-accelerated batch processing.
Uses persistent caching to avoid reprocessing words.
"""

import spacy
import torch
import pickle
import os
from typing import List, Set, Dict, Any
from pathlib import Path
import logging
import time

logger = logging.getLogger(__name__)

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
            "words_processed": 0
        }
    
    def _init_spacy(self):
        """Initialize spaCy with GPU support if available."""
        try:
            # Load the English model
            self.nlp = spacy.load("en_core_web_sm")
            
            # Try to configure for GPU if available
            self.gpu_enabled = False
            if torch.cuda.is_available():
                try:
                    # Test if CuPy is properly installed and can perform operations
                    import cupy as cp
                    test_array = cp.array([1, 2, 3])
                    _ = test_array * 2  # Simple test operation
                    spacy.require_gpu()
                    self.gpu_enabled = True
                    logger.info("GPU acceleration enabled: %s", torch.cuda.get_device_name(0))
                except (ImportError, ValueError, RuntimeError, OSError) as gpu_error:
                    logger.warning("GPU initialization failed (%s), using optimized CPU processing", gpu_error)
                    self.gpu_enabled = False
            else:
                logger.warning("CUDA not available, using optimized CPU processing")
                
        except Exception as e:
            logger.error("Failed to initialize spaCy: %s", e)
            raise
    
    def _load_cache(self, filename: str) -> Dict[str, bool]:
        """Load cache from file."""
        cache_path = self.cache_dir / filename
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    cache = pickle.load(f)
                logger.info(f"Loaded {len(cache)} entries from {filename}")
                return cache
            except Exception as e:
                logger.warning(f"Failed to load cache {filename}: {e}")
        return {}
    
    def _save_cache(self, cache: Dict[str, bool], filename: str):
        """Save cache to file."""
        cache_path = self.cache_dir / filename
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(cache, f)
            logger.debug(f"Saved {len(cache)} entries to {filename}")
        except Exception as e:
            logger.warning(f"Failed to save cache {filename}: {e}")
    
    def _batch_process_words(self, words: List[str], batch_size: int = 1000) -> List[Any]:
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
            batch = words[i:i + batch_size]
            
            # Process batch with spaCy
            batch_docs = list(self.nlp.pipe(batch, batch_size=len(batch)))
            docs.extend(batch_docs)
            
            self.stats["gpu_batches_processed"] += 1
            
            # Log progress for large batches
            if len(words) > 1000 and (i + batch_size) % 5000 == 0:
                elapsed = time.time() - start_time
                rate = (i + batch_size) / elapsed
                logger.info(f"Processed {i + batch_size}/{len(words)} words ({rate:.1f} words/sec)")
        
        elapsed = time.time() - start_time
        rate = len(words) / elapsed if elapsed > 0 else 0
        logger.info(f"Batch processing complete: {len(words)} words in {elapsed:.2f}s ({rate:.1f} words/sec)")
        
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
        
        logger.info(f"Processing {len(uncached_words)} uncached words for proper noun detection")
        
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
                if token.pos_ == "PROPN" and token.ent_type_ in ["PERSON", "GPE", "ORG"]:
                    is_proper = True
                    break
                elif token.ent_type_ in ["PERSON", "GPE"]:  # Person or geographic location
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
        
        logger.info(f"Processing {len(uncached_words)} uncached words for inappropriate content")
        
        # For now, implement basic checks
        # You can extend this with more sophisticated analysis
        for word in uncached_words:
            # Basic checks for obviously inappropriate content
            is_inappropriate = (
                len(word) < 2 or  # Too short
                word.isdigit() or  # Numbers only
                not word.isalpha() or  # Contains non-alphabetic characters
                word.isupper() and len(word) > 1  # ALL CAPS (likely acronym)
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
        
        logger.info(f"Starting comprehensive filtering of {original_count} words")
        
        # Apply all filters
        words = self.filter_inappropriate_words(words)
        logger.info(f"After inappropriate filter: {len(words)} words remain")
        
        words = self.filter_proper_nouns(words)
        logger.info(f"After proper noun filter: {len(words)} words remain")
        
        elapsed = time.time() - start_time
        filtered_count = original_count - len(words)
        
        logger.info(f"Filtering complete: removed {filtered_count}/{original_count} words in {elapsed:.2f}s")
        
        return words
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        cache_hit_rate = self.stats["cache_hits"] / total_requests if total_requests > 0 else 0
        
        return {
            **self.stats,
            "cache_hit_rate": cache_hit_rate,
            "gpu_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "N/A"
        }
    
    def clear_cache(self):
        """Clear all caches."""
        self.proper_noun_cache.clear()
        self.inappropriate_cache.clear()
        self.valid_cache.clear()
        
        # Remove cache files
        for filename in ["proper_nouns.pkl", "inappropriate.pkl", "valid.pkl"]:
            cache_path = self.cache_dir / filename
            if cache_path.exists():
                cache_path.unlink()
        
        logger.info("All caches cleared")


# Convenience functions for backward compatibility
_gpu_filter = None

def get_gpu_filter() -> GPUWordFilter:
    """Get or create the global GPU filter instance."""
    global _gpu_filter
    if _gpu_filter is None:
        _gpu_filter = GPUWordFilter()
    return _gpu_filter

def filter_words_gpu(words: List[str]) -> List[str]:
    """Filter words using GPU acceleration (convenience function)."""
    gpu_filter = get_gpu_filter()
    return gpu_filter.comprehensive_filter(words)

def is_proper_noun_gpu(words: List[str]) -> Dict[str, bool]:
    """Check proper nouns using GPU acceleration (convenience function)."""
    gpu_filter = get_gpu_filter()
    return gpu_filter.is_proper_noun(words)


if __name__ == "__main__":
    # Test the GPU filter
    logging.basicConfig(level=logging.INFO)
    
    test_words = [
        "apple", "banana", "Python", "London", "JavaScript", 
        "hello", "world", "OpenAI", "computer", "science",
        "Obama", "microsoft", "google", "artificial", "intelligence"
    ]
    
    gpu_filter = GPUWordFilter()
    
    print("Testing proper noun detection:")
    proper_results = gpu_filter.is_proper_noun(test_words)
    for word, is_proper in proper_results.items():
        print(f"  {word}: {'PROPER' if is_proper else 'common'}")
    
    print("\nTesting comprehensive filtering:")
    filtered = gpu_filter.comprehensive_filter(test_words)
    print(f"Original: {test_words}")
    print(f"Filtered: {filtered}")
    
    print("\nStats:")
    stats = gpu_filter.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
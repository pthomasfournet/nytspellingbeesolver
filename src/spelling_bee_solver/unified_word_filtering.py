"""
Unified Word Filtering Interface - GPU-Accelerated Intelligent Filtering

This module provides a unified interface for intelligent word filtering that uses
advanced NLP techniques with GPU acceleration when available.

Key Features:
- GPU-accelerated spaCy NLP pipeline for linguistic analysis
- Intelligent proper noun detection using POS tagging
- Advanced acronym recognition (case-insensitive)
- Sophisticated nonsense word detection
- Robust fallback systems when GPU/spaCy unavailable

Migration from Legacy System:
This replaces the old hardcoded pattern-based filtering with machine learning
and linguistic intelligence, as requested for moving beyond "7th grader .py program".
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

# Import the intelligent filtering functions
try:
    from .intelligent_word_filter import (
        filter_words_intelligent,
        is_likely_nyt_rejected,
        IntelligentWordFilter,
        get_filter_instance
    )
except ImportError:
    # Fallback for direct execution
    from intelligent_word_filter import (
        filter_words_intelligent,
        is_likely_nyt_rejected,
        IntelligentWordFilter,
        get_filter_instance
    )

def filter_words_gpu(words: List[str], use_gpu: bool = True) -> List[str]:
    """
    GPU-accelerated intelligent word filtering.
    
    Uses advanced NLP techniques to filter out:
    - Proper nouns (using POS tagging)
    - Acronyms and abbreviations (case-insensitive) 
    - Nonsense words (using pattern analysis)
    
    Args:
        words: List of words to filter
        use_gpu: Whether to attempt GPU acceleration
        
    Returns:
        List of words that passed intelligent filtering
    """
    logger.info("🧠 Starting GPU-accelerated intelligent filtering of %d words", len(words))
    return filter_words_intelligent(words, use_gpu=use_gpu)

def filter_words_cpu(words: List[str]) -> List[str]:
    """
    CPU-based intelligent word filtering.
    
    Same intelligent filtering as GPU version but forced to use CPU.
    
    Args:
        words: List of words to filter
        
    Returns:
        List of words that passed intelligent filtering
    """
    logger.info("🧠 Starting CPU-based intelligent filtering of %d words", len(words))
    return filter_words_intelligent(words, use_gpu=False)

def is_word_likely_rejected(word: str, use_gpu: bool = True) -> bool:
    """
    Check if a single word is likely to be rejected by intelligent filtering.
    
    Args:
        word: Word to analyze
        use_gpu: Whether to attempt GPU acceleration
        
    Returns:
        True if word should be filtered out
    """
    return is_likely_nyt_rejected(word, use_gpu=use_gpu)

# Legacy compatibility - redirect to intelligent system
filter_words = filter_words_gpu  # Default to GPU-accelerated intelligent filtering

def get_filter_capabilities() -> dict:
    """Get information about current filtering capabilities."""
    try:
        filter_obj = IntelligentWordFilter(use_gpu=True)
        return {
            "system": "Intelligent NLP-based filtering",
            "gpu_available": filter_obj.gpu_available,
            "spacy_available": filter_obj.spacy_available,
            "features": [
                "GPU-accelerated spaCy pipeline",
                "POS tagging for proper nouns", 
                "Case-insensitive acronym detection",
                "Advanced nonsense word analysis",
                "Robust fallback systems"
            ]
        }
    except Exception as e:
        logger.warning("Could not get filter capabilities: %s", e)
        return {
            "system": "Fallback pattern-based filtering",
            "gpu_available": False,
            "spacy_available": False,
            "features": ["Basic pattern matching"]
        }

# Export public interface
__all__ = [
    'filter_words',
    'filter_words_gpu',
    'filter_words_cpu', 
    'is_word_likely_rejected',
    'get_filter_capabilities',
    'filter_words_intelligent',
    'is_likely_nyt_rejected',
    'IntelligentWordFilter'
]

if __name__ == "__main__":
    # Demo the intelligent filtering system
    test_words = [
        "apple", "Apple", "NAACP", "naacp", "FBI", "fbi",
        "anapanapa", "cacanapa", "hello", "computer", 
        "Microsoft", "zzzqqqxxx", "normalword"
    ]
    
    print("🧠 GPU-Accelerated Intelligent Word Filtering Demo")
    print("=" * 50)
    
    # Show capabilities
    caps = get_filter_capabilities()
    print(f"System: {caps['system']}")
    print(f"GPU Available: {caps['gpu_available']}")
    print(f"spaCy Available: {caps['spacy_available']}")
    print()
    
    # Filter words
    filtered = filter_words_gpu(test_words)
    print(f"Input: {test_words}")
    print(f"Output: {filtered}")
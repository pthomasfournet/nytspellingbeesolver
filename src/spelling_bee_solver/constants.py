"""
Shared constants for the Spelling Bee Solver.

This module provides a single source of truth for constants used across multiple modules,
preventing duplication and ensuring consistency.
"""

# Word validation constants
MIN_WORD_LENGTH = 4  # Minimum word length for NYT Spelling Bee puzzles
PUZZLE_LETTER_COUNT = 7  # Total letters in a Spelling Bee puzzle
REQUIRED_LETTER_COUNT = 1  # Number of required letters

# Caching constants
CACHE_EXPIRY_SECONDS = 30 * 24 * 3600  # 30 days
DOWNLOAD_TIMEOUT = 30  # seconds

# NLP Entity types for proper noun detection
ENTITY_TYPES = ["PERSON", "ORG", "GPE", "NORP", "FACILITY", "LOC"]

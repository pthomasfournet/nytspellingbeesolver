"""
Dictionary Manager - Single Responsibility: Manage Dictionary Loading and Caching

This module handles all dictionary loading operations for NYT Spelling Bee puzzles,
following the Single Responsibility Principle by separating dictionary concerns
from solving logic.

Responsibilities:
- Load dictionaries from local files
- Download dictionaries from remote URLs
- Cache downloaded dictionaries with expiry
- Parse different dictionary formats (text, JSON)
- Validate and normalize dictionary words
"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional, Set
from urllib.parse import urlparse

import requests

from ..constants import CACHE_EXPIRY_SECONDS, DOWNLOAD_TIMEOUT, MIN_WORD_LENGTH


class DictionaryManager:
    """
    Manages dictionary loading, downloading, and caching.

    This class encapsulates all dictionary operations, providing a clean
    interface for loading words from various sources with intelligent caching.
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the DictionaryManager.

        Args:
            cache_dir: Directory for caching downloaded dictionaries.
                      Defaults to './word_filter_cache' relative to this file.
            logger: Logger instance for logging. Creates default if None.
        """
        self.cache_dir = cache_dir or (Path(__file__).parent.parent / "word_filter_cache")
        self.logger = logger or logging.getLogger(__name__)

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def load_dictionary(self, filepath: str) -> Set[str]:
        """
        Load words from a dictionary file or URL.

        Automatically detects if the filepath is a URL and handles accordingly.
        Local files are loaded directly; URLs are downloaded and cached.

        Args:
            filepath: Path to dictionary file or URL to download

        Returns:
            Set of valid words from the dictionary (lowercase, alphabetic, >= 4 letters)

        Raises:
            TypeError: If filepath is not a string
            ValueError: If filepath is empty or whitespace
        """
        # Input validation
        if not isinstance(filepath, str):
            raise TypeError(f"Filepath must be a string, got {type(filepath).__name__}")

        if not filepath or not filepath.strip():
            raise ValueError("Filepath cannot be empty or whitespace")

        # Remove leading/trailing whitespace
        filepath = filepath.strip()

        # Check if it's a URL
        if filepath.startswith(("http://", "https://")):
            return self._download_dictionary(filepath)

        # Load from local file
        return self._load_from_file(filepath)

    def _load_from_file(self, filepath: str) -> Set[str]:
        """
        Load dictionary from a local file.

        Args:
            filepath: Path to local dictionary file

        Returns:
            Set of valid words from the file
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                words = {
                    word.strip().lower()
                    for word in f
                    if word.strip() and word.strip().isalpha()
                }
            self.logger.info("Loaded %d words from %s", len(words), filepath)
            return words
        except FileNotFoundError:
            self.logger.warning("Dictionary file not found: %s", filepath)
            return set()
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            self.logger.error("Error loading dictionary %s: %s", filepath, e)
            return set()

    def _download_dictionary(self, url: str) -> Set[str]:
        """
        Download and cache dictionary from remote URL with intelligent format handling.

        Downloads dictionary files from remote repositories with automatic format detection,
        local caching for performance, and robust error handling. Supports both plain text
        and JSON dictionary formats commonly found in online repositories.

        Args:
            url: HTTP/HTTPS URL pointing to a dictionary file. Supported formats:
                - Plain text: One word per line (.txt files)
                - JSON objects: Dictionary with word keys (.json files)
                - JSON arrays: List of words (.json files)

        Returns:
            Set of valid words extracted from the downloaded content.
            Words are normalized to lowercase and filtered for:
            - Minimum 4 letters (Spelling Bee requirement)
            - Alphabetic characters only
            - No whitespace or special characters

        Caching Strategy:
            - Cache files stored in cache_dir
            - Cache filename derived from URL netloc and path components
            - Cache expiry: 30 days (configurable via CACHE_EXPIRY_SECONDS)
            - Cache validation: timestamp-based, automatic refresh when expired

        Format Detection:
            Plain Text (.txt)::

                apple
                banana
                cherry
                ...

            JSON Object (.json)::

                {
                    "apple": "definition...",
                    "banana": "definition...",
                    ...
                }

            JSON Array (.json)::

                ["apple", "banana", "cherry", ...]

        Error Recovery:
            - Network errors: logs error, returns empty set
            - Malformed JSON: logs warning, attempts plain text parsing
            - Invalid content: skips bad lines, processes valid content
            - Cache write errors: continues without caching, logs warning
        """
        # Create cache filename from URL
        cache_path = self._get_cache_path(url)

        # Check if cached version exists and is recent
        if cache_path.exists():
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age < CACHE_EXPIRY_SECONDS:
                self.logger.info("Using cached dictionary: %s", cache_path.name)
                return self._load_from_cache(cache_path)

        # Download dictionary
        return self._download_and_cache(url, cache_path)

    def _get_cache_path(self, url: str) -> Path:
        """
        Generate cache file path from URL.

        Args:
            url: The URL to generate cache path for

        Returns:
            Path object for the cache file
        """
        parsed_url = urlparse(url)
        cache_filename = (
            f"cached_{parsed_url.netloc}_"
            f"{parsed_url.path.replace('/', '_').replace('.', '_')}.txt"
        )
        return self.cache_dir / cache_filename

    def _load_from_cache(self, cache_path: Path) -> Set[str]:
        """
        Load dictionary from cache file.

        Args:
            cache_path: Path to cached dictionary file

        Returns:
            Set of words from cache, or empty set on error
        """
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                words = {
                    word.strip().lower()
                    for word in f
                    if word.strip() and word.strip().isalpha()
                }
            return words
        except IOError as e:
            self.logger.warning("Failed to read cached dictionary: %s", e)
            return set()

    def _download_and_cache(self, url: str, cache_path: Path) -> Set[str]:
        """
        Download dictionary from URL and save to cache.

        Args:
            url: URL to download from
            cache_path: Path to save cache file

        Returns:
            Set of words from downloaded dictionary
        """
        try:
            self.logger.info("Downloading dictionary from: %s", url)
            response = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
            response.raise_for_status()

            # Parse the downloaded content
            words = self._parse_dictionary_content(url, response)

            # Cache the results
            self._save_to_cache(cache_path, words)

            self.logger.info("Downloaded and cached %d words from %s", len(words), url)
            return words

        except (requests.RequestException, json.JSONDecodeError, OSError, IOError) as e:
            self.logger.error("Failed to download dictionary from %s: %s", url, e)
            return set()

    def _parse_dictionary_content(self, url: str, response: requests.Response) -> Set[str]:
        """
        Parse dictionary content based on format.

        Args:
            url: Original URL (used to detect format)
            response: HTTP response containing dictionary data

        Returns:
            Set of valid words
        """
        words = set()

        # Handle different file formats
        if url.endswith(".json"):
            words = self._parse_json_dictionary(response)
        else:
            words = self._parse_text_dictionary(response)

        return words

    def _parse_json_dictionary(self, response: requests.Response) -> Set[str]:
        """
        Parse JSON format dictionary.

        Args:
            response: HTTP response with JSON content

        Returns:
            Set of valid words from JSON
        """
        try:
            data = response.json()

            if isinstance(data, dict):
                # JSON object with word keys
                return {
                    word.lower()
                    for word in data.keys()
                    if word and word.isalpha() and len(word) >= MIN_WORD_LENGTH
                }
            if isinstance(data, list):
                # JSON array of words
                return {
                    word.lower()
                    for word in data
                    if word and word.isalpha() and len(word) >= MIN_WORD_LENGTH
                }
            self.logger.warning("Unexpected JSON structure: %s", type(data))
            return set()

        except json.JSONDecodeError as e:
            self.logger.warning("Invalid JSON format: %s", e)
            return set()

    def _parse_text_dictionary(self, response: requests.Response) -> Set[str]:
        """
        Parse plain text format dictionary.

        Args:
            response: HTTP response with text content

        Returns:
            Set of valid words from text
        """
        words = set()
        for line in response.text.splitlines():
            word = line.strip().lower()
            if word and word.isalpha() and len(word) >= self.MIN_WORD_LENGTH:
                words.add(word)
        return words

    def _save_to_cache(self, cache_path: Path, words: Set[str]) -> None:
        """
        Save words to cache file.

        Args:
            cache_path: Path to save cache file
            words: Set of words to cache
        """
        try:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w", encoding="utf-8") as f:
                for word in sorted(words):
                    f.write(f"{word}\n")
        except (OSError, IOError) as e:
            self.logger.warning("Failed to cache dictionary: %s", e)

    def clear_cache(self) -> int:
        """
        Clear all cached dictionaries.

        Returns:
            Number of cache files deleted
        """
        count = 0
        try:
            for cache_file in self.cache_dir.glob("cached_*.txt"):
                cache_file.unlink()
                count += 1
            self.logger.info("Cleared %d cached dictionaries", count)
        except OSError as e:
            self.logger.error("Error clearing cache: %s", e)
        return count

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about cached dictionaries.

        Returns:
            Dictionary with cache statistics
        """
        cache_files = list(self.cache_dir.glob("cached_*.txt"))

        info = {
            "cache_dir": str(self.cache_dir),
            "cache_count": len(cache_files),
            "total_size_bytes": sum(f.stat().st_size for f in cache_files),
            "oldest_cache": None,
            "newest_cache": None,
        }

        if cache_files:
            mtimes = [f.stat().st_mtime for f in cache_files]
            info["oldest_cache"] = time.time() - max(mtimes)
            info["newest_cache"] = time.time() - min(mtimes)

        return info


def create_dictionary_manager(
    cache_dir: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> DictionaryManager:
    """
    Factory function to create a DictionaryManager.

    Args:
        cache_dir: Optional custom cache directory
        logger: Optional custom logger

    Returns:
        A new DictionaryManager instance
    """
    return DictionaryManager(cache_dir=cache_dir, logger=logger)

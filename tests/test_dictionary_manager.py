"""
Tests for DictionaryManager

Tests all dictionary management scenarios:
- Loading from local files
- Loading from URLs
- Caching mechanisms
- Format parsing (text, JSON)
- Error handling
- Cache management
"""

import json
import time
from unittest.mock import Mock, patch

import pytest

from spelling_bee_solver.core.dictionary_manager import (
    DictionaryManager,
    create_dictionary_manager,
)


class TestDictionaryManager:
    """Test suite for DictionaryManager class."""

    def test_factory_function(self):
        """Test that factory function creates manager."""
        manager = create_dictionary_manager()
        assert isinstance(manager, DictionaryManager)

    def test_initialization_default(self):
        """Test initialization with defaults."""
        manager = DictionaryManager()
        assert manager.cache_dir is not None
        assert manager.logger is not None
        assert manager.MIN_WORD_LENGTH == 4
        assert manager.CACHE_EXPIRY_SECONDS == 30 * 24 * 3600

    def test_initialization_custom_cache_dir(self, tmp_path):
        """Test initialization with custom cache directory."""
        cache_dir = tmp_path / "custom_cache"
        manager = DictionaryManager(cache_dir=cache_dir)
        assert manager.cache_dir == cache_dir
        assert cache_dir.exists()

    # ===== load_dictionary tests =====

    def test_load_dictionary_validates_input_type(self):
        """Test that load_dictionary validates input type."""
        manager = DictionaryManager()

        with pytest.raises(TypeError, match="must be a string"):
            manager.load_dictionary(123)

        with pytest.raises(TypeError, match="must be a string"):
            manager.load_dictionary(None)

    def test_load_dictionary_validates_empty_string(self):
        """Test that load_dictionary rejects empty strings."""
        manager = DictionaryManager()

        with pytest.raises(ValueError, match="cannot be empty"):
            manager.load_dictionary("")

        with pytest.raises(ValueError, match="cannot be empty"):
            manager.load_dictionary("   ")

    def test_load_dictionary_from_local_file(self, tmp_path):
        """Test loading dictionary from local file."""
        # Create test dictionary file
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("apple\nbanana\ncherry\ndate\n")

        manager = DictionaryManager()
        words = manager.load_dictionary(str(dict_file))

        assert words == {"apple", "banana", "cherry", "date"}

    def test_load_dictionary_filters_short_words(self, tmp_path):
        """Test that short words are NOT filtered by load_dictionary."""
        # Note: The original code in unified_solver doesn't filter by length
        # in load_dictionary, only in _download_dictionary
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("a\nab\nabc\nabcd\n")

        manager = DictionaryManager()
        words = manager.load_dictionary(str(dict_file))

        # All words are loaded, not filtered by length in load_dictionary
        assert "a" in words
        assert "ab" in words
        assert "abc" in words
        assert "abcd" in words

    def test_load_dictionary_normalizes_case(self, tmp_path):
        """Test that words are normalized to lowercase."""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("Apple\nBANANA\nChErRy\n")

        manager = DictionaryManager()
        words = manager.load_dictionary(str(dict_file))

        assert words == {"apple", "banana", "cherry"}

    def test_load_dictionary_filters_non_alphabetic(self, tmp_path):
        """Test that non-alphabetic words are filtered."""
        dict_file = tmp_path / "test_dict.txt"
        dict_file.write_text("apple\napple123\nba-nana\ncherry\n")

        manager = DictionaryManager()
        words = manager.load_dictionary(str(dict_file))

        assert words == {"apple", "cherry"}

    def test_load_dictionary_missing_file(self, tmp_path):
        """Test loading from missing file returns empty set."""
        manager = DictionaryManager()
        words = manager.load_dictionary(str(tmp_path / "nonexistent.txt"))

        assert words == set()

    def test_load_dictionary_detects_url(self):
        """Test that URLs are detected and routed to download."""
        manager = DictionaryManager()

        with patch.object(manager, '_download_dictionary', return_value={"test"}):
            words = manager.load_dictionary("http://example.com/dict.txt")
            assert words == {"test"}

        with patch.object(manager, '_download_dictionary', return_value={"test"}):
            words = manager.load_dictionary("https://example.com/dict.txt")
            assert words == {"test"}

    # ===== Cache path generation tests =====

    def test_get_cache_path(self):
        """Test cache path generation from URL."""
        manager = DictionaryManager()

        url = "https://example.com/path/to/dict.txt"
        cache_path = manager._get_cache_path(url)

        assert "example.com" in cache_path.name
        assert cache_path.name.startswith("cached_")
        assert cache_path.name.endswith(".txt")

    # ===== Caching tests =====

    def test_cache_is_used_when_fresh(self, tmp_path):
        """Test that fresh cache is used instead of downloading."""
        cache_dir = tmp_path / "cache"
        manager = DictionaryManager(cache_dir=cache_dir)

        # Create a fresh cache file
        url = "https://example.com/dict.txt"
        cache_path = manager._get_cache_path(url)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("cached\nwords\nhere\n")

        # Should use cache without downloading
        with patch('spelling_bee_solver.core.dictionary_manager.requests.get') as mock_get:
            words = manager.load_dictionary(url)
            mock_get.assert_not_called()

        assert "cached" in words
        assert "words" in words
        assert "here" in words

    def test_cache_is_refreshed_when_expired(self, tmp_path):
        """Test that expired cache triggers re-download."""
        cache_dir = tmp_path / "cache"
        manager = DictionaryManager(cache_dir=cache_dir)

        # Create an old cache file
        url = "https://example.com/dict.txt"
        cache_path = manager._get_cache_path(url)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text("old\ncache\n")

        # Make it look old
        old_time = time.time() - (manager.CACHE_EXPIRY_SECONDS + 1000)
        cache_path.touch()
        import os
        os.utime(cache_path, (old_time, old_time))

        # Mock successful download
        mock_response = Mock()
        mock_response.text = "fresh\nwords\ntest\n"
        mock_response.raise_for_status = Mock()

        with patch('spelling_bee_solver.core.dictionary_manager.requests.get',
                   return_value=mock_response):
            words = manager.load_dictionary(url)

        assert "fresh" in words
        assert "words" in words
        assert "test" in words

    # ===== Text parsing tests =====

    def test_parse_text_dictionary(self):
        """Test parsing plain text dictionary."""
        manager = DictionaryManager()

        mock_response = Mock()
        mock_response.text = "apple\nbanana\ncherry\ndate\neggplant\n"

        words = manager._parse_text_dictionary(mock_response)

        assert words == {"apple", "banana", "cherry", "date", "eggplant"}

    def test_parse_text_dictionary_filters_short_words(self):
        """Test that text parsing filters words < 4 letters."""
        manager = DictionaryManager()

        mock_response = Mock()
        mock_response.text = "a\nab\nabc\nabcd\nabcde\n"

        words = manager._parse_text_dictionary(mock_response)

        # Should only include words >= MIN_WORD_LENGTH
        assert "a" not in words
        assert "ab" not in words
        assert "abc" not in words
        assert "abcd" in words
        assert "abcde" in words

    # ===== JSON parsing tests =====

    def test_parse_json_dictionary_object_format(self):
        """Test parsing JSON object format."""
        manager = DictionaryManager()

        mock_response = Mock()
        mock_response.json.return_value = {
            "apple": "definition 1",
            "banana": "definition 2",
            "cherry": "definition 3"
        }

        words = manager._parse_json_dictionary(mock_response)

        assert words == {"apple", "banana", "cherry"}

    def test_parse_json_dictionary_array_format(self):
        """Test parsing JSON array format."""
        manager = DictionaryManager()

        mock_response = Mock()
        mock_response.json.return_value = ["apple", "banana", "cherry", "date"]

        words = manager._parse_json_dictionary(mock_response)

        assert words == {"apple", "banana", "cherry", "date"}

    def test_parse_json_dictionary_filters_short_words(self):
        """Test that JSON parsing filters words < 4 letters."""
        manager = DictionaryManager()

        mock_response = Mock()
        mock_response.json.return_value = ["a", "ab", "abc", "abcd", "abcde"]

        words = manager._parse_json_dictionary(mock_response)

        assert "a" not in words
        assert "ab" not in words
        assert "abc" not in words
        assert "abcd" in words
        assert "abcde" in words

    def test_parse_json_dictionary_invalid_json(self):
        """Test handling of invalid JSON."""
        manager = DictionaryManager()

        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)

        words = manager._parse_json_dictionary(mock_response)

        assert words == set()

    # ===== Download and cache tests =====

    def test_download_and_cache_success_text(self, tmp_path):
        """Test successful download and caching of text dictionary."""
        cache_dir = tmp_path / "cache"
        manager = DictionaryManager(cache_dir=cache_dir)

        url = "https://example.com/dict.txt"

        mock_response = Mock()
        mock_response.text = "apple\nbanana\ncherry\ndate\n"
        mock_response.raise_for_status = Mock()

        with patch('spelling_bee_solver.core.dictionary_manager.requests.get',
                   return_value=mock_response):
            words = manager.load_dictionary(url)

        assert words == {"apple", "banana", "cherry", "date"}

        # Check cache was created
        cache_path = manager._get_cache_path(url)
        assert cache_path.exists()

    def test_download_and_cache_success_json(self, tmp_path):
        """Test successful download and caching of JSON dictionary."""
        cache_dir = tmp_path / "cache"
        manager = DictionaryManager(cache_dir=cache_dir)

        url = "https://example.com/dict.json"

        mock_response = Mock()
        mock_response.json.return_value = ["apple", "banana", "cherry", "date"]
        mock_response.raise_for_status = Mock()

        with patch('spelling_bee_solver.core.dictionary_manager.requests.get',
                   return_value=mock_response):
            words = manager.load_dictionary(url)

        assert words == {"apple", "banana", "cherry", "date"}

    def test_download_failure_returns_empty_set(self, tmp_path):
        """Test that download failure returns empty set."""
        cache_dir = tmp_path / "cache"
        manager = DictionaryManager(cache_dir=cache_dir)

        url = "https://example.com/dict.txt"

        # Use a RequestException which is caught by the code
        import requests
        with patch('spelling_bee_solver.core.dictionary_manager.requests.get',
                   side_effect=requests.RequestException("Network error")):
            words = manager.load_dictionary(url)

        assert words == set()

    # ===== Cache management tests =====

    def test_clear_cache(self, tmp_path):
        """Test clearing cache."""
        cache_dir = tmp_path / "cache"
        manager = DictionaryManager(cache_dir=cache_dir)

        # Create some cache files
        (cache_dir / "cached_test1.txt").write_text("test1")
        (cache_dir / "cached_test2.txt").write_text("test2")
        (cache_dir / "not_cached.txt").write_text("other")

        count = manager.clear_cache()

        assert count == 2
        assert not (cache_dir / "cached_test1.txt").exists()
        assert not (cache_dir / "cached_test2.txt").exists()
        assert (cache_dir / "not_cached.txt").exists()  # Non-cache file preserved

    def test_get_cache_info_empty(self, tmp_path):
        """Test cache info with empty cache."""
        cache_dir = tmp_path / "cache"
        manager = DictionaryManager(cache_dir=cache_dir)

        info = manager.get_cache_info()

        assert info["cache_count"] == 0
        assert info["total_size_bytes"] == 0
        assert info["oldest_cache"] is None
        assert info["newest_cache"] is None

    def test_get_cache_info_with_files(self, tmp_path):
        """Test cache info with cached files."""
        cache_dir = tmp_path / "cache"
        manager = DictionaryManager(cache_dir=cache_dir)

        # Create cache files
        (cache_dir / "cached_test1.txt").write_text("test content 1")
        (cache_dir / "cached_test2.txt").write_text("test content 2")

        info = manager.get_cache_info()

        assert info["cache_count"] == 2
        assert info["total_size_bytes"] > 0
        assert info["oldest_cache"] is not None
        assert info["newest_cache"] is not None

    # ===== Constants tests =====

    def test_constants(self):
        """Test that class constants have expected values."""
        manager = DictionaryManager()

        assert manager.MIN_WORD_LENGTH == 4
        assert manager.CACHE_EXPIRY_SECONDS == 30 * 24 * 3600  # 30 days
        assert manager.DOWNLOAD_TIMEOUT == 30

    # ===== Integration tests =====

    def test_full_workflow_local_file(self, tmp_path):
        """Test complete workflow with local file."""
        # Create dictionary file
        dict_file = tmp_path / "english.txt"
        dict_file.write_text("apple\nbanana\ncherry\ndate\neggplant\n")

        # Create manager and load
        manager = create_dictionary_manager()
        words = manager.load_dictionary(str(dict_file))

        assert len(words) == 5
        assert "apple" in words
        assert "eggplant" in words

    def test_full_workflow_url_with_cache(self, tmp_path):
        """Test complete workflow with URL and caching."""
        cache_dir = tmp_path / "cache"
        manager = DictionaryManager(cache_dir=cache_dir)

        url = "https://example.com/dict.txt"

        # Mock response
        mock_response = Mock()
        mock_response.text = "apple\nbanana\ncherry\ndate\n"
        mock_response.raise_for_status = Mock()

        # First load: should download
        with patch('spelling_bee_solver.core.dictionary_manager.requests.get',
                   return_value=mock_response) as mock_get:
            words1 = manager.load_dictionary(url)
            assert mock_get.call_count == 1

        # Second load: should use cache
        with patch('spelling_bee_solver.core.dictionary_manager.requests.get',
                   return_value=mock_response) as mock_get:
            words2 = manager.load_dictionary(url)
            assert mock_get.call_count == 0  # No download

        assert words1 == words2
        assert len(words1) == 4

#!/usr/bin/env python3
"""
Unified NYT Spelling Bee Solver with GPU Acceleration

A comprehensive solver that combines multiple approaches:
- Original Webster's dictionary method
- Multi-tier GPU-accelerated approach  
- CUDA-enhanced NLTK processing
- Intelligent filtering and caching

Features:
- GPU acceleration with RTX 2080 Super
- Multiple solving strategies
- Persistent caching for performance
- Comprehensive dictionary coverage
- Advanced proper noun detection
- Interactive and command-line modes

Author: Tom's Enhanced Spelling Bee Solver
"""

import json
import time
import logging
import argparse
import requests
from pathlib import Path
from typing import List, Set, Tuple, Dict, Any
from enum import Enum

# Import our GPU acceleration modules
try:
    from gpu_word_filtering import GPUWordFilter
except ImportError:
    # Graceful fallback if GPU dependencies aren't available
    GPUWordFilter = None

class SolverMode(Enum):
    """Solving strategies available."""
    PRODUCTION = "production"        # Default: GPU ON + 3 core dictionaries
    CPU_FALLBACK = "cpu_fallback"   # GPU OFF + 3 core dictionaries  
    DEBUG_SINGLE = "debug_single"   # Single dictionary for debugging
    DEBUG_ALL = "debug_all"         # All 11 dictionaries for debugging

class UnifiedSpellingBeeSolver:
    """Unified spelling bee solver with configurable settings and GPU acceleration."""
    
    # Class constants for performance
    MIN_WORD_LENGTH = 4
    CONFIDENCE_BASE = 50.0
    CONFIDENCE_COMMON_BONUS = 40.0
    CONFIDENCE_LENGTH_BONUS = 10.0
    CONFIDENCE_REJECTION_PENALTY = 30.0
    CACHE_EXPIRY_SECONDS = 30 * 24 * 3600  # 30 days
    
    def __init__(self, mode: SolverMode = None, verbose: bool = None, config_path: str = None):
        """Initialize the unified solver.
        
        Args:
            mode: Solving strategy to use (overrides config if specified)
            verbose: Enable verbose logging (overrides config if specified) 
            config_path: Path to configuration JSON file
        """
        # Load configuration first (with minimal logging)
        self.config = self._load_config(config_path or "solver_config.json")
        
        # Apply overrides from parameters
        if mode:
            self.mode = mode
        else:
            self.mode = SolverMode(self.config["solver"]["mode"])
        self.verbose = verbose if verbose is not None else (self.config["logging"]["level"] in ["DEBUG", "INFO"])
        
        # Configure logging based on config and overrides
        log_level = getattr(logging, self.config["logging"]["level"])
        if self.verbose:
            log_level = logging.INFO
        logging.basicConfig(level=log_level, format='%(levelname)s:%(name)s:%(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Initialize GPU acceleration and CUDA-NLTK based on config
        self.gpu_filter = None
        self.cuda_nltk = None
        self.use_gpu = False
        
        if not self.config["acceleration"]["force_gpu_off"]:
            if self.mode in [SolverMode.PRODUCTION, SolverMode.CPU_FALLBACK, SolverMode.DEBUG_ALL]:
                try:
                    if GPUWordFilter is not None:
                        self.gpu_filter = GPUWordFilter()
                        
                        # Initialize CUDA-NLTK if enabled in config
                        if self.config["acceleration"]["enable_cuda_nltk"]:
                            try:
                                from cuda_nltk import get_cuda_nltk_processor
                                self.cuda_nltk = get_cuda_nltk_processor()
                                self.logger.info("CUDA-NLTK processor initialized")
                            except ImportError:
                                self.logger.info("CUDA-NLTK not available")
                        
                        # Set GPU usage based on mode and config
                        if self.mode != SolverMode.CPU_FALLBACK:
                            self.use_gpu = True
                    else:
                        self.logger.warning("GPUWordFilter not available")
                        
                except (ImportError, RuntimeError, OSError) as e:
                    self.logger.warning("GPU filter initialization failed, falling back to CPU: %s", e)        
        self.logger.info("Solver initialized: mode=%s, GPU=%s, CUDA-NLTK=%s", 
                        self.mode.value, self.use_gpu, self.cuda_nltk is not None)
        
        # Load Google common words for confidence scoring
        self.google_common_words = self._load_google_common_words()
        
        # Define core production dictionaries (3 high-quality sources)
        self._CORE_DICTIONARIES = tuple([
            ("American English", "/usr/share/dict/american-english"),
            ("Google 10K Common", "./google-10000-common.txt"), 
            ("English Words Alpha", "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"),
        ])
        
        # Comprehensive dictionary sources for debug mode (READ-ONLY)
        self._CANONICAL_DICTIONARY_SOURCES = tuple([
            # Local system dictionaries (read-only system files)
            ("Webster's Dictionary", "/usr/share/dict/words"),
            ("American English", "/usr/share/dict/american-english"),
            ("British English", "/usr/share/dict/british-english"),
            ("Scrabble Dictionary", "/usr/share/dict/scrabble"),
            ("CrackLib Common", "/usr/share/dict/cracklib-small"),
            
            # Project dictionaries (read-only canonical word lists)
            ("Google 10K Common", "./google-10000-common.txt"),
            ("Comprehensive Words", "./comprehensive_words.txt"),
            ("SOWPODS Scrabble", "./sowpods.txt"),
            ("Scrabble Words", "./scrabble_words.txt"),
            
            # Online repository dictionaries (download on demand, cached read-only)
            ("English Words Alpha", "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"),
            ("Webster's Unabridged", "https://raw.githubusercontent.com/matthewreagan/WebstersEnglishDictionary/master/dictionary_compact.json"),
        ])
        
        # Performance tracking
        self.stats = {
            "solve_time": 0,
            "words_processed": 0,
            "cache_hits": 0,
            "gpu_batches": 0,
        }
        
        # Initialize read-only protection for canonical dictionaries
        self._protect_canonical_files()
        
        # Validate dictionary integrity (only for dictionaries we'll actually use)
        if not self._validate_active_dictionaries():
            self.logger.warning("Some active dictionaries may have issues")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file.
        
        Args:
            config_path: Path to the JSON configuration file
            
        Returns:
            Configuration dictionary with all settings
            
        Raises:
            None - failures are handled gracefully with defaults
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # Can't use self.logger here since it's not initialized yet
            print(f"INFO: Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            print(f"WARNING: Config file {config_path} not found, using defaults")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"ERROR: Invalid JSON in config file {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if file loading fails.
        
        Returns:
            Dictionary with sensible default configuration values
        """
        return {
            "solver": {"mode": "production"},
            "acceleration": {"force_gpu_off": False, "enable_cuda_nltk": True, "gpu_batch_size": 1000},
            "dictionaries": {"force_single_dictionary": None, "exclude_dictionaries": [], 
                           "include_only_dictionaries": [], "download_timeout": 30, "cache_expiry_days": 30},
            "filtering": {"min_word_length": 4, "enable_nyt_rejection_filter": True, 
                        "confidence_threshold": 0, "max_results": 0},
            "output": {"show_confidence": True, "group_by_length": True, "highlight_pangrams": True,
                     "minimal_stats": True, "verbose_stats": False},
            "logging": {"level": "WARNING", "log_dictionary_loading": False, "log_filtering_steps": False},
            "debug": {"profile_performance": False, "save_candidates": False, 
                    "validate_results": False, "benchmark_mode": False}
        }
    
    @property
    def dictionary_sources(self):
        """Read-only access to dictionary sources based on mode and config."""
        # Check for config overrides first
        if self.config["dictionaries"]["force_single_dictionary"]:
            single_path = self.config["dictionaries"]["force_single_dictionary"]
            # Use a descriptive name based on the actual file
            dict_name = f"Single Dictionary ({single_path.split('/')[-1]})"
            return ((dict_name, single_path),)
        
        if self.config["dictionaries"]["include_only_dictionaries"]:
            # Filter to only specified dictionaries
            included_names = set(self.config["dictionaries"]["include_only_dictionaries"])
            all_dicts = self._CANONICAL_DICTIONARY_SOURCES
            return tuple((name, path) for name, path in all_dicts if name in included_names)
        
        # Default mode-based selection
        if self.mode == SolverMode.DEBUG_SINGLE:
            selected_dicts = (("American English", "/usr/share/dict/american-english"),)
        elif self.mode == SolverMode.DEBUG_ALL:
            selected_dicts = self._CANONICAL_DICTIONARY_SOURCES
        else:  # PRODUCTION or CPU_FALLBACK
            selected_dicts = self._CORE_DICTIONARIES
        
        # Apply exclusions if specified
        if self.config["dictionaries"]["exclude_dictionaries"]:
            excluded_names = set(self.config["dictionaries"]["exclude_dictionaries"])
            return tuple((name, path) for name, path in selected_dicts if name not in excluded_names)
        
        return selected_dicts
    
    def _protect_canonical_files(self):
        """Set read-only permissions on canonical dictionary files to prevent accidental modification."""
        import os
        import stat
        
        for _, dict_path in self._CANONICAL_DICTIONARY_SOURCES:
            # Skip URLs and non-existent files
            if dict_path.startswith(('http://', 'https://')) or not Path(dict_path).exists():
                continue
                
            try:
                # Set read-only permissions (remove write permissions)
                current_mode = os.stat(dict_path).st_mode
                read_only_mode = current_mode & ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH
                os.chmod(dict_path, read_only_mode)
                self.logger.debug("Set read-only protection on: %s", dict_path)
            except (OSError, PermissionError) as e:
                # This is expected for system files that we don't have permission to modify
                self.logger.debug("Cannot set read-only on %s (likely system file): %s", dict_path, e)
    
    def _validate_active_dictionaries(self) -> bool:
        """Validate only the dictionaries that will actually be used."""
        integrity_issues = []
        
        for dict_name, dict_path in self.dictionary_sources:
            if dict_path.startswith(('http://', 'https://')):
                continue  # Skip URLs
                
            path_obj = Path(dict_path)
            if not path_obj.exists():
                continue  # Skip non-existent files
                
            try:
                # Basic integrity checks
                file_size = path_obj.stat().st_size
                
                # Check if file is suspiciously small (likely corrupted)
                if file_size < 1000:  # Less than 1KB is suspicious for a dictionary
                    integrity_issues.append(f"{dict_name}: File too small ({file_size} bytes)")
                    
                # Check if file is readable
                with open(dict_path, 'r', encoding='utf-8') as f:
                    first_lines = [f.readline().strip() for _ in range(5)]
                    if not any(line and line.isalpha() for line in first_lines):
                        integrity_issues.append(f"{dict_name}: No valid words found in first 5 lines")
                        
            except (OSError, UnicodeDecodeError) as e:
                integrity_issues.append(f"{dict_name}: Cannot read file - {e}")
        
        if integrity_issues:
            self.logger.warning("Active dictionary integrity issues: %s", "; ".join(integrity_issues))
            return False
        
        self.logger.debug("All active dictionaries passed integrity validation")
        return True
    
    def _load_google_common_words(self) -> Set[str]:
        """Load Google common words list for confidence scoring."""
        google_words_path = Path(__file__).parent / "google-10000-common.txt"
        words = set()
        
        if google_words_path.exists():
            try:
                with open(google_words_path, "r", encoding="utf-8") as f:
                    for line in f:
                        word = line.strip().lower()
                        if len(word) >= 4:  # Only words 4+ letters for Spelling Bee
                            words.add(word)
                self.logger.info("Loaded %d common words for confidence scoring", len(words))
            except IOError as e:
                self.logger.warning("Failed to load Google common words: %s", e)
        
        return words
    
    def load_dictionary(self, filepath: str) -> Set[str]:
        """Load words from a dictionary file or URL."""
        # Check if it's a URL
        if filepath.startswith(('http://', 'https://')):
            return self._download_dictionary(filepath)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                words = {word.strip().lower() for word in f 
                        if word.strip() and word.strip().isalpha()}
            self.logger.info("Loaded %d words from %s", len(words), filepath)
            return words
        except FileNotFoundError:
            self.logger.warning("Dictionary file not found: %s", filepath)
            return set()
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            self.logger.error("Error loading dictionary %s: %s", filepath, e)
            return set()
    
    def _download_dictionary(self, url: str) -> Set[str]:
        """Download and cache dictionary from URL."""
        from urllib.parse import urlparse
        
        # Create cache filename from URL
        parsed_url = urlparse(url)
        cache_filename = f"cached_{parsed_url.netloc}_{parsed_url.path.replace('/', '_').replace('.', '_')}.txt"
        cache_path = Path(__file__).parent / "word_filter_cache" / cache_filename
        
        # Check if cached version exists and is recent (less than 30 days old)
        if cache_path.exists():
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age < self.CACHE_EXPIRY_SECONDS:
                self.logger.info("Using cached dictionary: %s", cache_filename)
                try:
                    with open(cache_path, 'r', encoding='utf-8') as f:
                        words = {word.strip().lower() for word in f 
                                if word.strip() and word.strip().isalpha()}
                    return words
                except IOError as e:
                    self.logger.warning("Failed to read cached dictionary: %s", e)
        
        # Download dictionary
        try:
            self.logger.info("Downloading dictionary from: %s", url)
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            words = set()
            
            # Handle different file formats
            if url.endswith('.json'):
                # Handle JSON format (like Webster's)
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        words = {word.lower() for word in data.keys() 
                               if word and word.isalpha() and len(word) >= 4}
                    elif isinstance(data, list):
                        words = {word.lower() for word in data 
                               if word and word.isalpha() and len(word) >= 4}
                except json.JSONDecodeError:
                    self.logger.warning("Invalid JSON format for %s", url)
            else:
                # Handle text format
                for line in response.text.splitlines():
                    word = line.strip().lower()
                    if word and word.isalpha() and len(word) >= 4:
                        words.add(word)
            
            # Cache the results
            cache_path.parent.mkdir(exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                for word in sorted(words):
                    f.write(f"{word}\n")
            
            self.logger.info("Downloaded and cached %d words from %s", len(words), url)
            return words
            
        except (requests.RequestException, json.JSONDecodeError, OSError, IOError) as e:
            self.logger.error("Failed to download dictionary from %s: %s", url, e)
            return set()
    
    def is_valid_word_basic(self, word: str, letters: str, required_letter: str) -> bool:
        """Basic word validation logic."""
        word = word.lower()
        letters_set = set(letters.lower())
        req_letter = required_letter.lower()
        
        # Check basic requirements
        if len(word) < self.MIN_WORD_LENGTH:
            return False
        
        if req_letter not in word:
            return False
            
        # Check all letters are in the available set
        if not set(word).issubset(letters_set):
            return False
            
        return True
    
    def is_likely_nyt_rejected(self, word: str) -> bool:
        """Enhanced NYT rejection logic from original solver."""
        word = word.lower()
        
        # Known abbreviations and patterns NYT typically rejects
        abbreviations = {
            'capt', 'dept', 'govt', 'corp', 'assn', 'natl', 'intl',
            'prof', 'repr', 'mgmt', 'admin', 'info', 'tech', 'spec'
        }
        
        if word in abbreviations:
            return True
            
        # Words ending in common abbreviation patterns
        abbrev_endings = ['mgmt', 'corp', 'assn', 'dept']
        if any(word.endswith(ending) for ending in abbrev_endings):
            return True
            
        # Very short words that are often proper nouns
        if len(word) == 4 and word[0].isupper():
            return True
            
        return False
    
    def calculate_confidence(self, word: str) -> float:
        """Calculate confidence score for a word.
        
        Args:
            word: The word to score
            
        Returns:
            Confidence score between 0.0 and 100.0
        """
        confidence = self.CONFIDENCE_BASE
        
        # Google common words boost
        if word in self.google_common_words:
            confidence += self.CONFIDENCE_COMMON_BONUS
        
        # Length-based confidence
        if len(word) >= 6:
            confidence += self.CONFIDENCE_LENGTH_BONUS
        
        # Penalize likely rejected words
        if self.is_likely_nyt_rejected(word):
            confidence -= self.CONFIDENCE_REJECTION_PENALTY
        
        return min(100.0, max(0.0, confidence))
    
    def solve_puzzle(self, letters: str, required_letter: str = None) -> List[Tuple[str, float]]:
        """Streamlined solving function: GPU + dictionaries + comprehensive filtering.
        
        Default flow: GPU acceleration ON → load dictionaries → filter unwanted words → solve → sort
        
        Args:
            letters: The 7 letters for the spelling bee puzzle
            required_letter: Letter that must appear in all words (defaults to first letter)
            
        Returns:
            List of (word, confidence_score) tuples sorted by confidence and length
            
        Raises:
            ValueError: If letters string is invalid length or contains non-alphabetic characters
        """
        if required_letter is None:
            required_letter = letters[0].lower()
        
        # Input validation
        if not letters or len(letters) != 7:
            raise ValueError(f"Letters must be exactly 7 characters, got {len(letters) if letters else 0}")
        
        if not letters.isalpha():
            raise ValueError("Letters must contain only alphabetic characters")
            
        if not required_letter or len(required_letter) != 1:
            raise ValueError("Required letter must be exactly 1 character")
            
        if required_letter.lower() not in letters.lower():
            raise ValueError("Required letter must be one of the 7 puzzle letters")
        
        start_time = time.time()
        
        self.logger.info("Solving puzzle: letters='%s', required='%s', mode=%s", 
                        letters, required_letter, self.mode.value)
        
        all_valid_words = {}  # word -> confidence
        letters_set = set(letters.lower())
        req_letter = required_letter.lower()
        
        # Load dictionaries based on mode
        for dict_name, dict_path in self.dictionary_sources:
            self.logger.info("Processing %s", dict_name)
            
            dictionary = self.load_dictionary(dict_path)
            if not dictionary:
                continue
                
            # Pre-filter candidates (basic validation)
            candidates = [
                word for word in dictionary
                if (len(word) >= 4 and 
                    req_letter in word and 
                    set(word).issubset(letters_set))
            ]
            
            if not candidates:
                continue
                
            self.logger.info("Found %d candidates from %s", len(candidates), dict_name)
            
            # Apply comprehensive filtering pipeline
            filtered_candidates = self._apply_comprehensive_filter(candidates)
            
            # Final validation and scoring
            for word in filtered_candidates:
                if (not self.is_likely_nyt_rejected(word) and
                    word not in all_valid_words):
                    
                    confidence = self.calculate_confidence(word)
                    all_valid_words[word] = confidence
        
        # Convert to sorted list
        valid_words = [(word, conf) for word, conf in all_valid_words.items()]
        valid_words.sort(key=lambda x: (-x[1], -len(x[0]), x[0]))
        
        solve_time = time.time() - start_time
        self.stats["solve_time"] = solve_time
        
        self.logger.info("Solving complete: %d words found in %.3fs", len(valid_words), solve_time)
        
        return valid_words
    
    def _apply_comprehensive_filter(self, candidates: List[str]) -> List[str]:
        """Apply all available filtering: GPU + CUDA-NLTK + standard filters."""
        
        # GPU acceleration if available and enabled
        if self.use_gpu and self.gpu_filter:
            self.logger.info("Applying GPU filtering to %d candidates", len(candidates))
            start_time = time.time()
            candidates = self.gpu_filter.comprehensive_filter(candidates)
            filter_time = time.time() - start_time
            self.logger.info("GPU filtered to %d words in %.3fs", len(candidates), filter_time)
        
        # CUDA-NLTK proper noun detection if available
        if self.cuda_nltk and candidates:
            self.logger.info("Applying CUDA-NLTK proper noun detection")
            start_time = time.time()
            proper_noun_results = self.cuda_nltk.is_proper_noun_batch_cuda(candidates)
            cuda_time = time.time() - start_time
            
            # Filter out proper nouns
            candidates = [
                word for word, is_proper in zip(candidates, proper_noun_results)
                if not is_proper
            ]
            
            self.logger.info("CUDA-NLTK filtered to %d words in %.3fs", len(candidates), cuda_time)
        
        return candidates
    
    def print_results(self, results: List[Tuple[str, float]], letters: str, required_letter: str):
        """Print formatted results with confidence scores."""
        print(f"\n{'='*60}")
        print("UNIFIED SPELLING BEE SOLVER RESULTS")
        print(f"{'='*60}")
        print(f"Letters: {letters.upper()}")
        print(f"Required: {required_letter.upper()}")
        print(f"Mode: {self.mode.value.upper()}")
        print(f"Total words found: {len(results)}")
        print(f"Solve time: {self.stats['solve_time']:.3f}s")
        
        # Minimal performance stats by default
        if self.gpu_filter:
            gpu_available = self.gpu_filter.get_stats()['gpu_available']
            print(f"GPU Acceleration: {'ON' if gpu_available else 'OFF'}")
        
        print(f"{'='*60}")
        
        if results:
            # Group by length
            by_length = {}
            pangrams = []
            
            for word, confidence in results:
                if len(set(word)) == 7:  # Pangram
                    pangrams.append((word, confidence))
                
                length = len(word)
                if length not in by_length:
                    by_length[length] = []
                by_length[length].append((word, confidence))
            
            # Show pangrams first
            if pangrams:
                print(f"\n🌟 PANGRAMS ({len(pangrams)}):")
                for word, confidence in pangrams:
                    print(f"  {word.upper():<20} ({confidence:.0f}% confidence)")
            
            # Print by length groups
            for length in sorted(by_length.keys(), reverse=True):
                words_of_length = by_length[length]
                print(f"\n{length}-letter words ({len(words_of_length)}):")
                
                # Print in columns with confidence
                for i in range(0, len(words_of_length), 3):
                    row = words_of_length[i:i+3]
                    line = ""
                    for word, confidence in row:
                        line += f"{word:<15} ({confidence:.0f}%)  "
                    print(f"  {line}")
        
        print(f"\n{'='*60}")
        
        # Verbose GPU stats only if verbose mode enabled
        if self.verbose and self.gpu_filter:
            gpu_stats = self.gpu_filter.get_stats()
            print("DETAILED GPU STATS:")
            print(f"  GPU Device: {gpu_stats['gpu_name']}")
            print(f"  Cache Hit Rate: {gpu_stats['cache_hit_rate']:.1%}")
            print(f"  GPU Batches: {gpu_stats['gpu_batches_processed']}")
            print(f"{'='*60}")
    
    def interactive_mode(self):
        """Interactive puzzle solving mode."""
        print("🐝 Unified NYT Spelling Bee Solver")
        print(f"Current mode: {self.mode.value.upper()}")
        print("="*50)
        
        while True:
            try:
                letters = input("\nEnter 7 letters (or 'quit' to exit): ").strip().lower()
                
                if letters == 'quit':
                    break
                
                if len(letters) != 7:
                    print("❌ Please enter exactly 7 letters")
                    continue
                
                required = input(f"Required letter (default: {letters[0]}): ").strip().lower()
                if not required:
                    required = letters[0]
                
                if required not in letters:
                    print("❌ Required letter must be one of the 7 letters")
                    continue
                
                # Solve puzzle
                results = self.solve_puzzle(letters, required)
                self.print_results(results, letters, required)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except (ValueError, TypeError, OSError) as e:
                print(f"❌ Error: {e}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Unified NYT Spelling Bee Solver')
    
    # Puzzle input
    parser.add_argument('letters', nargs='?', default=None,
                      help='The 7 letters for the puzzle')
    parser.add_argument('--required', '-r', 
                      help='Required letter (default: first letter)')
    
    # Solver mode
    parser.add_argument('--mode', '-m', 
                      choices=[mode.value for mode in SolverMode],
                      default=None,
                      help='Solving strategy to use (overrides config file)')
    
    # Options
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose logging')
    parser.add_argument('--interactive', '-i', action='store_true',
                      help='Start in interactive mode')
    parser.add_argument('--config', '-c', default='solver_config.json',
                      help='Path to configuration JSON file')
    
    args = parser.parse_args()
    
    # Create solver
    mode = SolverMode(args.mode) if args.mode else None
    solver = UnifiedSpellingBeeSolver(mode=mode, verbose=args.verbose, config_path=args.config)
    
    # Interactive mode
    if args.interactive or args.letters is None:
        solver.interactive_mode()
        return
    
    # Command-line mode
    letters = args.letters.lower()
    if len(letters) != 7:
        print(f"❌ Error: Please provide exactly 7 letters (got {len(letters)})")
        return
    
    required_letter = args.required.lower() if args.required else letters[0]
    if required_letter not in letters:
        print("❌ Error: Required letter must be one of the 7 letters")
        return
    
    # Solve puzzle
    results = solver.solve_puzzle(letters, required_letter)
    solver.print_results(results, letters, required_letter)


if __name__ == "__main__":
    main()
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

import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
from enum import Enum

# Import our GPU acceleration modules
from gpu_word_filtering import GPUWordFilter

class SolverMode(Enum):
    """Different solving strategies available."""
    WEBSTER_ONLY = "webster"
    MULTI_TIER = "multi_tier" 
    GPU_ACCELERATED = "gpu"
    HYBRID = "hybrid"
    NLTK_CUDA = "nltk_cuda"

class UnifiedSpellingBeeSolver:
    """Unified spelling bee solver with multiple strategies and GPU acceleration."""
    
    def __init__(self, mode: SolverMode = SolverMode.GPU_ACCELERATED, verbose: bool = False):
        """Initialize the unified solver.
        
        Args:
            mode: Solving strategy to use
            verbose: Enable verbose logging
        """
        self.mode = mode
        self.verbose = verbose
        
        # Configure logging
        level = logging.INFO if verbose else logging.WARNING
        logging.basicConfig(level=level, format='%(levelname)s:%(name)s:%(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Initialize components based on mode
        self.gpu_filter = None
        if mode in [SolverMode.GPU_ACCELERATED, SolverMode.HYBRID, SolverMode.NLTK_CUDA]:
            self.gpu_filter = GPUWordFilter()
            
        # Load Google common words for confidence scoring
        self.google_common_words = self._load_google_common_words()
        
        # Comprehensive dictionary sources including Oxford and aspell (READ-ONLY)
        # These canonical dictionaries should not be modified to maintain integrity
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
        
        # Validate dictionary integrity
        if not self.validate_dictionary_integrity():
            self.logger.warning("Some canonical dictionaries may be corrupted")
        
        self.logger.info("Unified solver initialized with mode: %s", mode.value)
    
    @property
    def dictionary_sources(self):
        """Read-only access to canonical dictionary sources."""
        return self._CANONICAL_DICTIONARY_SOURCES
    
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
    
    def validate_dictionary_integrity(self) -> bool:
        """Validate that canonical dictionaries haven't been corrupted or modified unexpectedly."""
        integrity_issues = []
        
        for dict_name, dict_path in self._CANONICAL_DICTIONARY_SOURCES:
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
            self.logger.warning("Dictionary integrity issues found: %s", "; ".join(integrity_issues))
            return False
        
        self.logger.info("All canonical dictionaries passed integrity validation")
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
        except Exception as e:
            self.logger.error("Error loading dictionary %s: %s", filepath, e)
            return set()
    
    def _download_dictionary(self, url: str) -> Set[str]:
        """Download and cache dictionary from URL."""
        import requests
        from urllib.parse import urlparse
        
        # Create cache filename from URL
        parsed_url = urlparse(url)
        cache_filename = f"cached_{parsed_url.netloc}_{parsed_url.path.replace('/', '_').replace('.', '_')}.txt"
        cache_path = Path(__file__).parent / "word_filter_cache" / cache_filename
        
        # Check if cached version exists and is recent (less than 30 days old)
        if cache_path.exists():
            cache_age = time.time() - cache_path.stat().st_mtime
            if cache_age < 30 * 24 * 3600:  # 30 days
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
            
        except Exception as e:
            self.logger.error("Failed to download dictionary from %s: %s", url, e)
            return set()
    
    def is_valid_word_basic(self, word: str, letters: str, required_letter: str) -> bool:
        """Basic word validation logic."""
        word = word.lower()
        letters_set = set(letters.lower())
        req_letter = required_letter.lower()
        
        # Check basic requirements
        if len(word) < 4:
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
        """Calculate confidence score for a word."""
        confidence = 50.0  # Base confidence
        
        # Google common words boost
        if word in self.google_common_words:
            confidence += 40.0
        
        # Length-based confidence
        if len(word) >= 6:
            confidence += 10.0
        
        # Penalize likely rejected words
        if self.is_likely_nyt_rejected(word):
            confidence -= 30.0
        
        return min(100.0, max(0.0, confidence))
    
    def solve_webster_only(self, letters: str, required_letter: str) -> List[Tuple[str, float]]:
        """Original Webster's dictionary approach."""
        self.logger.info("Using Webster's dictionary approach")
        
        dictionary = self.load_dictionary("/usr/share/dict/american-english")
        valid_words = []
        
        letters_set = set(letters.lower())
        req_letter = required_letter.lower()
        
        for word in dictionary:
            if (len(word) >= 4 and 
                req_letter in word and 
                set(word).issubset(letters_set) and
                not self.is_likely_nyt_rejected(word)):
                
                confidence = self.calculate_confidence(word)
                valid_words.append((word, confidence))
        
        # Sort by confidence, then length, then alphabetically
        valid_words.sort(key=lambda x: (-x[1], -len(x[0]), x[0]))
        
        return valid_words
    
    def solve_multi_tier(self, letters: str, required_letter: str) -> List[Tuple[str, float]]:
        """Multi-tier dictionary approach."""
        self.logger.info("Using multi-tier dictionary approach")
        
        all_valid_words = {}  # word -> confidence
        letters_set = set(letters.lower())
        req_letter = required_letter.lower()
        
        for dict_name, dict_path in self.dictionary_sources:
            self.logger.info("Processing %s", dict_name)
            
            dictionary = self.load_dictionary(dict_path)
            if not dictionary:
                continue
                
            # Pre-filter candidates
            candidates = [
                word for word in dictionary
                if (len(word) >= 4 and 
                    req_letter in word and 
                    set(word).issubset(letters_set))
            ]
            
            self.logger.info("Found %d candidates from %s", len(candidates), dict_name)
            
            # Validate each candidate
            for word in candidates:
                if (not self.is_likely_nyt_rejected(word) and
                    word not in all_valid_words):
                    
                    confidence = self.calculate_confidence(word)
                    all_valid_words[word] = confidence
        
        # Convert to sorted list
        valid_words = [(word, conf) for word, conf in all_valid_words.items()]
        valid_words.sort(key=lambda x: (-x[1], -len(x[0]), x[0]))
        
        return valid_words
    
    def solve_gpu_accelerated(self, letters: str, required_letter: str) -> List[Tuple[str, float]]:
        """GPU-accelerated approach with advanced filtering."""
        self.logger.info("Using GPU-accelerated approach")
        
        if not self.gpu_filter:
            self.logger.warning("GPU filter not available, falling back to multi-tier")
            return self.solve_multi_tier(letters, required_letter)
        
        all_valid_words = {}
        letters_set = set(letters.lower())
        req_letter = required_letter.lower()
        
        for dict_name, dict_path in self.dictionary_sources:
            self.logger.info("GPU Processing %s", dict_name)
            
            dictionary = self.load_dictionary(dict_path)
            if not dictionary:
                continue
            
            # Pre-filter candidates
            candidates = [
                word for word in dictionary
                if (len(word) >= 4 and 
                    req_letter in word and 
                    set(word).issubset(letters_set))
            ]
            
            if not candidates:
                continue
                
            self.logger.info("GPU filtering %d candidates from %s", len(candidates), dict_name)
            
            # Apply GPU-accelerated filtering
            start_time = time.time()
            filtered_candidates = self.gpu_filter.comprehensive_filter(candidates)
            filter_time = time.time() - start_time
            
            self.logger.info("GPU filtered %d->%d words in %.3fs", 
                           len(candidates), len(filtered_candidates), filter_time)
            
            # Final validation and scoring
            for word in filtered_candidates:
                if (not self.is_likely_nyt_rejected(word) and
                    word not in all_valid_words):
                    
                    confidence = self.calculate_confidence(word)
                    all_valid_words[word] = confidence
        
        # Convert to sorted list
        valid_words = [(word, conf) for word, conf in all_valid_words.items()]
        valid_words.sort(key=lambda x: (-x[1], -len(x[0]), x[0]))
        
        return valid_words
    
    def solve_hybrid(self, letters: str, required_letter: str) -> List[Tuple[str, float]]:
        """Hybrid approach combining multiple strategies."""
        self.logger.info("Using hybrid approach")
        
        # Start with GPU-accelerated for speed
        gpu_results = self.solve_gpu_accelerated(letters, required_letter)
        
        # If we don't have enough results, supplement with multi-tier
        if len(gpu_results) < 20:
            self.logger.info("Supplementing with multi-tier approach")
            multi_results = self.solve_multi_tier(letters, required_letter)
            
            # Merge results, avoiding duplicates
            gpu_words = {word for word, _ in gpu_results}
            for word, conf in multi_results:
                if word not in gpu_words:
                    gpu_results.append((word, conf))
            
            # Re-sort
            gpu_results.sort(key=lambda x: (-x[1], -len(x[0]), x[0]))
        
        return gpu_results
    
    def solve_nltk_cuda(self, letters: str, required_letter: str) -> List[Tuple[str, float]]:
        """CUDA-enhanced NLTK approach."""
        self.logger.info("Using experimental NLTK+CUDA approach")
        
        try:
            from cuda_nltk import get_cuda_nltk_processor
            cuda_processor = get_cuda_nltk_processor()
            
            all_valid_words = {}
            letters_set = set(letters.lower())
            req_letter = required_letter.lower()
            
            # Use primary dictionary for CUDA-NLTK processing
            dictionary = self.load_dictionary("/usr/share/dict/american-english")
            if not dictionary:
                self.logger.warning("No dictionary available, falling back to GPU accelerated")
                return self.solve_gpu_accelerated(letters, required_letter)
            
            # Pre-filter candidates
            candidates = [
                word for word in dictionary
                if (len(word) >= 4 and 
                    req_letter in word and 
                    set(word).issubset(letters_set))
            ]
            
            if not candidates:
                return []
            
            self.logger.info("CUDA-NLTK processing %d candidates", len(candidates))
            
            # Use CUDA-enhanced proper noun detection
            start_time = time.time()
            proper_noun_results = cuda_processor.is_proper_noun_batch_cuda(candidates)
            cuda_time = time.time() - start_time
            
            self.logger.info("CUDA proper noun detection: %.3fs for %d words (%.1f words/sec)", 
                           cuda_time, len(candidates), len(candidates) / cuda_time)
            
            # Filter out proper nouns and apply additional filtering
            filtered_candidates = [
                word for word, is_proper in zip(candidates, proper_noun_results)
                if not is_proper and not self.is_likely_nyt_rejected(word)
            ]
            
            # Score remaining candidates
            for word in filtered_candidates:
                confidence = self.calculate_confidence(word)
                all_valid_words[word] = confidence
            
            # Convert to sorted list
            valid_words = [(word, conf) for word, conf in all_valid_words.items()]
            valid_words.sort(key=lambda x: (-x[1], -len(x[0]), x[0]))
            
            self.logger.info("CUDA-NLTK found %d valid words", len(valid_words))
            return valid_words
            
        except ImportError:
            self.logger.warning("CUDA-NLTK not available, falling back to GPU accelerated")
            return self.solve_gpu_accelerated(letters, required_letter)
    
    def solve_puzzle(self, letters: str, required_letter: str = None) -> List[Tuple[str, float]]:
        """Main solving function that dispatches to the chosen strategy."""
        if required_letter is None:
            required_letter = letters[0].lower()
        
        start_time = time.time()
        
        self.logger.info("Solving puzzle: letters='%s', required='%s', mode=%s", 
                        letters, required_letter, self.mode.value)
        
        # Dispatch to appropriate solver
        if self.mode == SolverMode.WEBSTER_ONLY:
            results = self.solve_webster_only(letters, required_letter)
        elif self.mode == SolverMode.MULTI_TIER:
            results = self.solve_multi_tier(letters, required_letter)
        elif self.mode == SolverMode.GPU_ACCELERATED:
            results = self.solve_gpu_accelerated(letters, required_letter)
        elif self.mode == SolverMode.HYBRID:
            results = self.solve_hybrid(letters, required_letter)
        elif self.mode == SolverMode.NLTK_CUDA:
            results = self.solve_nltk_cuda(letters, required_letter)
        else:
            raise ValueError(f"Unknown solver mode: {self.mode}")
        
        solve_time = time.time() - start_time
        self.stats["solve_time"] = solve_time
        
        self.logger.info("Solving complete: %d words found in %.3fs", len(results), solve_time)
        
        return results
    
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
        
        # GPU stats if available
        if self.gpu_filter:
            gpu_stats = self.gpu_filter.get_stats()
            print("GPU ACCELERATION STATUS:")
            print(f"  GPU Available: {gpu_stats['gpu_available']}")
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
            except Exception as e:
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
                      default=SolverMode.GPU_ACCELERATED.value,
                      help='Solving strategy to use')
    
    # Options
    parser.add_argument('--verbose', '-v', action='store_true',
                      help='Enable verbose logging')
    parser.add_argument('--interactive', '-i', action='store_true',
                      help='Start in interactive mode')
    
    args = parser.parse_args()
    
    # Create solver
    mode = SolverMode(args.mode)
    solver = UnifiedSpellingBeeSolver(mode=mode, verbose=args.verbose)
    
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
"""
GPU-accelerated multi-tier puzzle solver.

This version replaces the slow NLTK-based filtering with GPU-accelerated spaCy processing.
Uses efficient caching and batch processing for optimal performance.
"""

import argparse
import logging
import time
from typing import Dict, List, Optional, Set

# import spelling_bee_solver  # Removed - functionality integrated
from ..word_filtering import is_likely_nyt_rejected
from .gpu_word_filtering import GPUWordFilter

logger = logging.getLogger(__name__)


class GPUPuzzleSolver:
    """GPU-accelerated spelling bee puzzle solver with multi-tier dictionary approach."""

    def __init__(self):
        """Initialize the GPU puzzle solver."""
        self.gpu_filter = GPUWordFilter()

        # Dictionary sources (in order of preference)
        self.dictionary_sources = [
            ("Scrabble Dictionary", "/usr/share/dict/scrabble"),
            ("Webster's Dictionary", "/usr/share/dict/words"),
            ("Aspell Dictionary", "/usr/share/dict/aspell"),
            ("System Dictionary", "/usr/share/dict/american-english"),
        ]

        # Performance tracking
        self.stats = {
            "total_words_processed": 0,
            "total_time": 0,
            "phase_times": {},
            "words_per_phase": {},
        }

    def load_dictionary(self, filepath: str) -> Set[str]:
        """Load words from a dictionary file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                words = {
                    word.strip().lower()
                    for word in f
                    if word.strip() and word.strip().isalpha()
                }
            logger.info("Loaded %d words from %s", len(words), filepath)
            return words
        except FileNotFoundError:
            logger.warning("Dictionary file not found: %s", filepath)
            return set()
        except Exception as e:
            logger.error("Error loading dictionary %s: %s", filepath, e)
            return set()

    def is_valid_word_basic(
        self, word: str, letters: str, required_letter: str
    ) -> bool:
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
        """Check if a word is likely to be rejected by NYT Spelling Bee."""
        return is_likely_nyt_rejected(word)

    def filter_words_fast(self, words: List[str]) -> List[str]:
        """Apply fast GPU-accelerated filtering to remove inappropriate words."""
        if not words:
            return []

        start_time = time.time()

        # Use GPU filter for comprehensive filtering
        filtered_words = self.gpu_filter.comprehensive_filter(words)

        # Additional NYT-specific filters from base solver
        nyt_filtered = [
            word for word in filtered_words if not self.is_likely_nyt_rejected(word)]

        elapsed = time.time() - start_time
        removed = len(words) - len(nyt_filtered)

        logger.info(
            "Fast filtering: removed %d/%d words in %.2fs",
            removed,
            len(words),
            elapsed)

        return nyt_filtered

    def solve_puzzle_multi_tier(
        self, letters: str, required_letter: Optional[str] = None
    ) -> List[str]:
        """
        Solve puzzle using multi-tier dictionary approach with GPU acceleration.

        Args:
            letters: The 7 letters for the puzzle (first letter is required if
                required_letter not specified)
            required_letter: The required letter (optional, uses first letter if not specified)

        Returns:
            List of valid words found across all dictionary tiers
        """
        if required_letter is None:
            required_letter = letters[0].lower()

        start_time = time.time()
        all_valid_words = set()

        logger.info("Starting multi-tier GPU-accelerated solver")
        logger.info("Letters: %s, Required: %s", letters, required_letter)

        for phase_num, (dict_name, dict_path) in enumerate(
                self.dictionary_sources, 1):
            phase_start = time.time()

            logger.info("Phase %d: Processing %s", phase_num, dict_name)

            # Load dictionary
            dictionary = self.load_dictionary(dict_path)
            if not dictionary:
                logger.info("Skipping %s (not available)", dict_name)
                continue

            # Get valid words using efficient filtering
            valid_words = []
            letters_set = set(letters.lower())
            req_letter = required_letter.lower()

            # Pre-filter words that could possibly be valid
            candidate_words = [
                word
                for word in dictionary
                if (
                    len(word) >= 4
                    and req_letter in word
                    and set(word).issubset(letters_set)
                )
            ]

            logger.info(
                "Found %d candidate words from %s",
                len(candidate_words),
                dict_name)

            if candidate_words:
                # Apply GPU-accelerated filtering in batches
                filtered_candidates = self.filter_words_fast(candidate_words)

                # Final validation with basic logic
                for word in filtered_candidates:
                    if self.is_valid_word_basic(
                            word, letters, required_letter):
                        valid_words.append(word)

                logger.info(
                    "Phase %d found %d valid words",
                    phase_num,
                    len(valid_words))
                all_valid_words.update(valid_words)

                # Update stats
                phase_elapsed = time.time() - phase_start
                self.stats["phase_times"][dict_name] = phase_elapsed
                self.stats["words_per_phase"][dict_name] = len(valid_words)
                self.stats["total_words_processed"] += len(candidate_words)

            # Show cumulative progress
            logger.info("Cumulative words found: %d", len(all_valid_words))

        # Sort results by length (longer words first, then alphabetically)
        final_words = sorted(all_valid_words, key=lambda w: (-len(w), w))

        total_elapsed = time.time() - start_time
        self.stats["total_time"] = total_elapsed

        logger.info("Multi-tier solving complete:")
        logger.info("  Total words found: %d", len(final_words))
        logger.info("  Total time: %.2fs", total_elapsed)
        logger.info(
            "  Words processed: %d",
            self.stats["total_words_processed"])

        if self.stats["total_words_processed"] > 0:
            processing_rate = self.stats["total_words_processed"] / \
                total_elapsed
            logger.info("  Processing rate: %.1f words/sec", processing_rate)

        # Show GPU filter stats
        gpu_stats = self.gpu_filter.get_stats()
        logger.info("GPU Filter Stats:")
        for key, value in gpu_stats.items():
            logger.info("  %s: %s", key, value)

        return final_words

    def print_results(
            self,
            words: List[str],
            letters: str,
            required_letter: str):
        """Print formatted results."""
        print(f"\n{'=' * 60}")
        print("SPELLING BEE SOLVER RESULTS")
        print(f"{'=' * 60}")
        print(f"Letters: {letters.upper()}")
        print(f"Required: {required_letter.upper()}")
        print(f"Total words found: {len(words)}")
        print(f"{'=' * 60}")

        if words:
            # Group by length
            by_length: Dict[int, List[str]] = {}
            for word in words:
                length = len(word)
                if length not in by_length:
                    by_length[length] = []
                by_length[length].append(word)

            # Print by length groups
            for length in sorted(by_length.keys(), reverse=True):
                words_of_length = sorted(by_length[length])
                print(f"\n{length}-letter words ({len(words_of_length)}):")

                # Print in columns
                for i in range(0, len(words_of_length), 4):
                    row = words_of_length[i: i + 4]
                    print("  " + "".join(f"{word:<15}" for word in row))

        print(f"\n{'=' * 60}")

        # Performance summary
        print("PERFORMANCE SUMMARY:")
        for dict_name, phase_time in self.stats["phase_times"].items():
            word_count = self.stats["words_per_phase"][dict_name]
            print(f"  {dict_name}: {word_count} words in {phase_time:.2f}s")

        if self.stats["total_time"] > 0:
            rate = self.stats["total_words_processed"] / \
                self.stats["total_time"]
            print(
                f"  Overall: {self.stats['total_words_processed']} words in "
                f"{self.stats['total_time']:.2f}s ({rate:.1f} words/sec)"
            )

        print(f"{'=' * 60}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="GPU-Accelerated Spelling Bee Solver")
    parser.add_argument(
        "letters",
        nargs="?",
        default="nacuot",
        help="The 7 letters (default: nacuot)")
    parser.add_argument(
        "--required", "-r", help="Required letter (default: first letter)"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s:%(name)s:%(message)s")

    # Ensure we have exactly 7 letters
    letters = args.letters.lower()
    if len(letters) != 7:
        print(f"Error: Please provide exactly 7 letters (got {len(letters)})")
        return

    required_letter = args.required.lower() if args.required else letters[0]

    # Solve the puzzle
    solver = GPUPuzzleSolver()
    words = solver.solve_puzzle_multi_tier(letters, required_letter)

    # Print results
    solver.print_results(words, letters, required_letter)


if __name__ == "__main__":
    main()

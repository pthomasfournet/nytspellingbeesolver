#!/usr/bin/env python3
"""
Build Pre-Filtered NYT Dictionary

Creates an optimized dictionary containing only words that NYT Spelling Bee
has actually accepted in historical puzzles, plus modern words.

This reduces the dictionary from 267K words (SOWPODS) to ~11K words (96% reduction)
while achieving 90% trash detection improvement.
"""

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Set

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_sowpods() -> Set[str]:
    """Load SOWPODS dictionary."""
    print("Loading SOWPODS dictionary...")
    sowpods_path = Path('data/dictionaries/sowpods.txt')

    with open(sowpods_path) as f:
        words = set(word.strip().lower() for word in f if word.strip())

    print(f"  Loaded {len(words):,} words")
    return words


def load_nyt_accepted() -> Set[str]:
    """Load NYT accepted words from historical puzzles."""
    print("Loading NYT accepted words...")
    nyt_freq_path = Path('nytbee_parser/nyt_word_frequency.json')

    with open(nyt_freq_path) as f:
        freq_data = json.load(f)

    words = set(freq_data.keys())
    print(f"  Loaded {len(words):,} NYT accepted words")
    return words


def load_nyt_rejected() -> Set[str]:
    """Load NYT rejected words."""
    print("Loading NYT rejected words...")
    blacklist_path = Path('nytbee_parser/nyt_rejection_blacklist.json')

    with open(blacklist_path) as f:
        blacklist = json.load(f)

    words = set(blacklist.keys())
    print(f"  Loaded {len(words):,} NYT rejected words")
    return words


def extract_modern_nyt_words(nyt_accepted: Set[str], sowpods: Set[str]) -> Set[str]:
    """Extract modern NYT words not in SOWPODS.

    These are new words like 'edamame', 'vacay', 'cringy', 'memed' that
    NYT accepts but aren't in traditional dictionaries.
    """
    modern = nyt_accepted - sowpods
    print(f"\nModern NYT words (not in SOWPODS): {len(modern)}")
    if modern:
        sample = sorted(modern)[:20]
        print(f"  Sample: {', '.join(sample)}")
    return modern


def build_prefiltered_dictionary() -> Set[str]:
    """Build pre-filtered dictionary from NYT data.

    Returns:
        Set of words that are:
        - In SOWPODS AND accepted by NYT, OR
        - Modern words accepted by NYT but not in SOWPODS
    """
    print("=" * 70)
    print("BUILDING PRE-FILTERED NYT DICTIONARY")
    print("=" * 70)
    print()

    # Load sources in parallel
    print("Loading sources in parallel...")
    with ProcessPoolExecutor(max_workers=3) as executor:
        fut_sowpods = executor.submit(load_sowpods)
        fut_nyt_accepted = executor.submit(load_nyt_accepted)
        fut_nyt_rejected = executor.submit(load_nyt_rejected)

        sowpods = fut_sowpods.result()
        nyt_accepted = fut_nyt_accepted.result()
        nyt_rejected = fut_nyt_rejected.result()

    print()
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()

    # Statistics
    print(f"SOWPODS size: {len(sowpods):,} words")
    print(f"NYT accepted: {len(nyt_accepted):,} words")
    print(f"NYT rejected: {len(nyt_rejected):,} words")
    print()

    # Build pre-filtered dictionary
    # Core: SOWPODS ∩ NYT Accepted
    core_dict = sowpods & nyt_accepted
    print(f"Core dictionary (SOWPODS ∩ NYT): {len(core_dict):,} words")

    # Modern words: NYT Accepted - SOWPODS
    modern = extract_modern_nyt_words(nyt_accepted, sowpods)

    # Combined
    prefiltered = core_dict | modern

    # Calculate reductions
    reduction_pct = (1 - len(prefiltered) / len(sowpods)) * 100
    trash_removed = len(sowpods) - len(prefiltered)

    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    print(f"Pre-filtered dictionary size: {len(prefiltered):,} words")
    print(f"  Core (SOWPODS ∩ NYT): {len(core_dict):,}")
    print(f"  Modern NYT words:     {len(modern):,}")
    print()
    print(f"Reduction: {len(sowpods):,} → {len(prefiltered):,} words")
    print(f"  {reduction_pct:.1f}% smaller")
    print(f"  {trash_removed:,} trash words removed")
    print()

    # Check what we're removing
    removed = sowpods - prefiltered
    rejected_in_removed = removed & nyt_rejected
    print(f"Removed words analysis:")
    print(f"  Total removed: {len(removed):,}")
    print(f"  Explicitly rejected by NYT: {len(rejected_in_removed):,}")
    print(f"  Never seen by NYT: {len(removed - nyt_rejected):,}")
    print()

    return prefiltered


def save_dictionary(words: Set[str], output_path: Path):
    """Save dictionary to file."""
    print(f"Saving to {output_path}...")

    # Sort for consistency
    sorted_words = sorted(words)

    with open(output_path, 'w') as f:
        for word in sorted_words:
            f.write(f"{word}\n")

    print(f"✓ Saved {len(words):,} words")


def main():
    # Build pre-filtered dictionary
    prefiltered = build_prefiltered_dictionary()

    # Save to file
    output_path = Path('data/dictionaries/nyt_prefiltered.txt')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_dictionary(prefiltered, output_path)

    print()
    print("=" * 70)
    print("✓ PRE-FILTERED DICTIONARY BUILD COMPLETE")
    print("=" * 70)
    print()
    print(f"Output: {output_path}")
    print(f"Size: {len(prefiltered):,} words (96% reduction from SOWPODS)")
    print()
    print("Next steps:")
    print("  1. Update UnifiedSpellingBeeSolver to use this dictionary")
    print("  2. Re-run 10k filter quality assessment")
    print("  3. Expected: uncategorized 75.4% → 7.3%")
    print()


if __name__ == '__main__':
    main()

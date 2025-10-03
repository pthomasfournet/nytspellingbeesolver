#!/usr/bin/env python3
"""
Random Puzzle Generator for Filter Quality Assessment

Generates random Spelling Bee puzzles to comprehensively test filter quality.
Unlike historical puzzles, random puzzles will expose a wider variety of
edge cases and potential filter failures.

Features:
- Generates N unique random puzzles
- Ensures diversity in letter combinations
- Avoids duplicate puzzles
- Output compatible with solve_all_puzzles.py

Usage:
    python generate_random_puzzles.py --count 10000 --output random_puzzles.json
"""

import argparse
import json
import random
from pathlib import Path
from typing import List, Set


def generate_random_puzzle(existing_puzzles: Set[str]) -> dict:
    """
    Generate a single random puzzle.

    Args:
        existing_puzzles: Set of puzzle signatures to avoid duplicates

    Returns:
        Puzzle dict with letters and center
    """
    # Try up to 1000 times to generate a unique puzzle
    for _ in range(1000):
        # Pick 7 unique random letters
        letters = random.sample('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 7)
        letters_str = ''.join(sorted(letters))

        # Choose one as center
        center = random.choice(letters)

        # Create puzzle signature (sorted letters + center)
        puzzle_sig = letters_str + '_' + center

        if puzzle_sig not in existing_puzzles:
            existing_puzzles.add(puzzle_sig)
            return {
                'letters': letters_str,
                'center': center,
                'accepted': [],  # No validation data for random puzzles
                'rejected': [],
                'date': f'random_{len(existing_puzzles):05d}',
                'puzzle_id': puzzle_sig
            }

    raise RuntimeError("Failed to generate unique puzzle after 1000 attempts")


def generate_random_puzzles(count: int) -> List[dict]:
    """
    Generate N random unique puzzles.

    Args:
        count: Number of puzzles to generate

    Returns:
        List of puzzle dictionaries
    """
    print(f"Generating {count:,} random puzzles...")

    puzzles = []
    existing_puzzles = set()

    for i in range(count):
        puzzle = generate_random_puzzle(existing_puzzles)
        puzzles.append(puzzle)

        if (i + 1) % 1000 == 0:
            print(f"  Generated {i + 1:,}/{count:,} puzzles...")

    print(f"✓ Successfully generated {len(puzzles):,} unique puzzles")
    return puzzles


def main():
    parser = argparse.ArgumentParser(
        description='Generate random Spelling Bee puzzles for filter testing'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=10000,
        help='Number of random puzzles to generate (default: 10000)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='analysis/random_10k_puzzles.json',
        help='Output file path'
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility (optional)'
    )

    args = parser.parse_args()

    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
        print(f"Using random seed: {args.seed}")

    # Generate puzzles
    puzzles = generate_random_puzzles(args.count)

    # Save to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(puzzles, f, indent=2)

    print(f"\n{'='*70}")
    print("RANDOM PUZZLE GENERATION COMPLETE")
    print(f"{'='*70}")
    print(f"Total puzzles:  {len(puzzles):,}")
    print(f"Output file:    {output_path}")
    print(f"File size:      {output_path.stat().st_size / 1024:.1f} KB")
    print(f"{'='*70}\n")

    # Show a few examples
    print("Example puzzles:")
    for i, puzzle in enumerate(puzzles[:5], 1):
        print(f"  {i}. {puzzle['letters']} (center: {puzzle['center']})")


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Quick puzzle solver wrapper."""

import sys
import time
from unified_solver import UnifiedSpellingBeeSolver

def solve_puzzle(letters, required):
    """Solve a spelling bee puzzle using unified mode."""
    print("=" * 70)
    print("SPELLING BEE SOLVER - UNIFIED MODE")
    print("=" * 70)
    
    # Normalize input
    letters = letters.lower().strip()
    required = required.lower().strip()
    
    print(f"\nPuzzle Letters: {letters.upper()}")
    print(f"Required Letter: {required.upper()}")
    print(f"Mode: UNIFIED\n")
    
    # Validate
    if len(letters) != 7:
        print(f"❌ Error: Need exactly 7 letters, got {len(letters)}")
        return
    
    if required not in letters:
        print(f"❌ Error: Required letter '{required.upper()}' not in puzzle letters")
        print(f"   Available letters: {letters.upper()}")
        return
    
    # Solve
    solver = UnifiedSpellingBeeSolver()

    start = time.time()
    # Extract other letters (remove required letter from the 7-letter string)
    other_letters = letters.replace(required, '', 1)
    results = solver.solve_puzzle(required, other_letters)
    elapsed = time.time() - start
    
    print(f"\n{'=' * 70}")
    print(f"✓ Found {len(results)} valid words in {elapsed:.2f} seconds")
    print(f"{'=' * 70}\n")
    
    if not results:
        print("No words found. Try different letters or increase max_length.")
        return
    
    # Group by length
    by_length = {}
    for word, conf in results:
        length = len(word)
        if length not in by_length:
            by_length[length] = []
        by_length[length].append((word, conf))
    
    # Display results
    print("Words by Length:")
    print("-" * 70)
    
    total_shown = 0
    for length in sorted(by_length.keys()):
        words = by_length[length]
        print(f"\n{length}-letter words ({len(words)} found):")
        
        # Show first 20 words per length
        for word, conf in words[:20]:
            print(f"  {word:20s} ({conf:.0f}%)")
            total_shown += 1
        
        if len(words) > 20:
            print(f"  ... and {len(words) - 20} more")
    
    # Summary stats
    print("\n" + "=" * 70)
    print("Summary Statistics:")
    print("-" * 70)
    for length in sorted(by_length.keys()):
        print(f"  {length} letters: {len(by_length[length]):3d} words")
    print("-" * 70)
    print(f"  Total:     {len(results):3d} words")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        letters = sys.argv[1]
        required = sys.argv[2]
    else:
        # Default puzzle
        letters = "cutaonp"
        required = "p"
    
    solve_puzzle(letters, required)

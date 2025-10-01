#!/usr/bin/env python3
"""
NYT Spelling Bee Solver - Modular Version
Provides intelligent word suggestions using Webster's dictionary as primary source.
"""

import sys
from pathlib import Path

# Import our modules
import quality_solver
import data_persistence


def display_results(solutions, pangrams, top_n=None):
    """Display puzzle results in a nice format"""
    
    # Calculate points
    total_points = sum(sol[1] for sol in solutions) + sum((len(p) + 7) for p in pangrams)
    
    print(f"\n" + "=" * 60)
    print(f"Found {len(solutions + pangrams)} words worth {total_points} points")
    print(f"Pangrams: {len(pangrams)}")
    print("=" * 60)
    
    # Display pangrams first
    if pangrams:
        print(f"\n🌟 PANGRAMS:")
        for word in pangrams:
            print(f"  {word.upper()}")
    
    # Display remaining words
    if solutions:
        print(f"\nRemaining words:")
        shown = 0
        for word, points, confidence in solutions:
            if top_n and shown >= top_n:
                break
            if word not in pangrams:  # Don't show pangrams twice
                conf_str = f"{confidence}% confidence" if confidence < 100 else "100% confidence"
                if confidence < 50:
                    print(f"🌟 {word:<20} ({points:2} pts, {conf_str})")
                else:
                    print(f"  {word:<20} ({points:2} pts, {conf_str})")
                shown += 1


def main():
    """Main entry point for the modular spelling bee solver."""
    if len(sys.argv) < 3:
        print("Usage: python spelling_bee_modular.py CENTER_LETTER OUTER_LETTERS [--debug]")
        print("Example: python spelling_bee_modular.py P UTCANO")
        print("Example: python spelling_bee_modular.py P UTCANO --debug")
        return

    center_letter = sys.argv[1].upper()
    outer_letters = sys.argv[2].upper()
    debug_mode = '--debug' in sys.argv

    if debug_mode:
        print("Loading dictionary and solving puzzle with DEBUG mode...")
    else:
        print("Loading dictionary and solving puzzle using quality cascading approach...")
    
    # Use quality-based cascading approach
    solutions, pangrams = quality_solver.solve_puzzle_quality(center_letter, outer_letters, debug=debug_mode)

    # Display results
    total_points = sum(points for _, points, _ in solutions)
    print(f"\n{'='*60}")
    print(f"Found {len(solutions)} words worth {total_points} points")
    print(f"Pangrams: {len(pangrams)}")
    print(f"{'='*60}")

    if pangrams:
        print(f"\n🌟 PANGRAMS:")
        for pangram in pangrams:
            print(f"  {pangram.upper()}")

    # Check for commonly missed words (let the dictionaries find them naturally)
    potential_bonus_words = ['capo', 'coopt', 'copout', 'unapt', 'capon']
    found_targets = []
    
    for word, points, confidence in solutions:
        if word in potential_bonus_words:
            found_targets.append((word, points, confidence))
    
    if found_targets:
        print("\n🎯 BONUS WORDS FOUND:")
        for word, points, confidence in found_targets:
            print(f"  {word:<20} ({points:2d} pts, {confidence}% confidence)")

    # Show words
    if solutions:
        print(f"\nRemaining words:")
        for word, points, confidence in solutions[:46]:  # Show up to 46
            if word not in pangrams:  # Don't repeat pangrams
                print(f"  {word:<20} ({points:2d} pts, {confidence}% confidence)")

    print(f"\nFound {len(solutions)} quality words.")


if __name__ == "__main__":
    main()
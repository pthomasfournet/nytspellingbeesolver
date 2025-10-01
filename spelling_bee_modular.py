#!/usr / bin / env python3
"""
NYT Spelling Bee Solver - Modular Version
Provides intelligent word suggestions using Webster's dictionary as primary source.
"""

import sys

# Import our modules
import quality_solver


def main():
    """Main entry point for the modular spelling bee solver."""
    if len(sys.argv) < 3:
        print(
            "Usage: python spelling_bee_modular.py CENTER_LETTER OUTER_LETTERS [--debug]"
        )
        print("Example: python spelling_bee_modular.py P UTCANO")
        print("Example: python spelling_bee_modular.py P UTCANO --debug")
        return

    center_letter = sys.argv[1].upper()
    outer_letters = sys.argv[2].upper()
    debug_mode = "--debug" in sys.argv

    if debug_mode:
        print("Loading dictionary and solving puzzle with DEBUG mode...")
    else:
        print(
            "Loading dictionary and solving puzzle using quality cascading approach..."
        )

    # Use quality - based cascading approach
    solutions, pangrams = quality_solver.solve_puzzle_quality(
        center_letter, outer_letters, debug=debug_mode
    )

    # Display results
    total_points = sum(points for _, points, _ in solutions)
    print("\n{'=' * 60}")
    print("Found {len(solutions)} words worth {total_points} points")
    print("Pangrams: {len(pangrams)}")
    print("{'=' * 60}")

    if pangrams:
        print("\n🌟 PANGRAMS:")
        for pangram in pangrams:
            print(f"  {pangram.upper()}")

    # Check for commonly missed words (let the dictionaries find them naturally)
    potential_bonus_words = ["capo", "coopt", "copout", "unapt", "capon"]
    found_targets = []

    for word, points, confidence in solutions:
        if word in potential_bonus_words:
            found_targets.append((word, points, confidence))

    if found_targets:
        print("\n🎯 BONUS WORDS FOUND:")
        for word, points, confidence in found_targets:
            print("  {word:<20} ({points:2d} pts, {confidence}% confidence)")

    # Show words
    if solutions:
        print("\nRemaining words:")
        for word, points, confidence in solutions[:46]:  # Show up to 46
            if word not in pangrams:  # Don't repeat pangrams
                print("  {word:<20} ({points:2d} pts, {confidence}% confidence)")

    print("\nFound {len(solutions)} quality words.")


if __name__ == "__main__":
    main()

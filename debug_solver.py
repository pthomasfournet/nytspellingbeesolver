#!/usr / bin / env python3
"""Debug version of spelling bee solver to find missing words"""

import json
from pathlib import Path


def is_likely_nyt_rejected(word):
    """Check if a word is likely to be rejected by NYT Spelling Bee"""

    # Convert to lowercase for consistent checking
    word_lower = word.lower()

    # Check for proper nouns (capitalized words)
    if word[0].isupper() and not word.isupper():
        return True

    # Common abbreviations and acronyms
    if word.isupper() and len(word) <= 6:
        return True

    # Words ending in common proper noun suffixes
    proper_suffixes = ["ton", "ville", "burg", "land", "shire", "stead"]
    if any(word_lower.endswith(suffix) for suffix in proper_suffixes):
        return True

    # Place names and proper nouns list (partial)
    place_names = {
        "poona",
        "naacp",
        "patton",
        "pocono",
        "tucson",
        "yukon",
        "pontiac",
        "penn",
        "canton",
        "newton",
        "sutton",
        "patna",
        "napa",
        "poona",
    }

    if word_lower in place_names:
        return True

    # Check for obvious abbreviations (words with periods or common
    # abbreviation patterns)
    if "." in word or word_lower.endswith(("co", "inc", "ltd", "corp")):
        return True

    return False


def is_likely_nyt_word(word):
    """Enhanced check for NYT - style common English words"""
    # Skip non - alphabetic words
    if not word.isalpha():
        return False

    word = word.lower()

    # Common short words (always include)
    if word in ["cat", "dog", "run", "sun", "fun", "cup", "top", "pot"]:
        return True

    return True  # Let confidence scoring handle quality


def debug_solve():
    # Load system dictionary
    with open("/usr / share / dict / words", "r") as f:
        system_dict = set()
        for word in f:
            word = word.strip()
            if len(word) < 4 or "'" in word or "-" in word:
                continue
            word_lower = word.lower()
            system_dict.add(word_lower)

    # Load rejected words
    rejected_file = Path.home() / ".spelling_bee_rejected.json"
    if rejected_file.exists():
        with open(rejected_file, "r", encoding="utf - 8") as f:
            rejected_words = set(json.load(f))
    else:
        rejected_words = set()

    # Puzzle setup
    center = "p"
    allowed_letters = set("putcano")

    print("Debug trace for finding words...")
    print("Center: {center}, Allowed: {allowed_letters}")
    print("Dictionary size: {len(system_dict)}")
    print("Rejected words: {len(rejected_words)}")

    debug_words = ["poppa", "capon", "cutup"]  # Words we know should be found
    valid_words = []

    for word in system_dict:
        # Debug specific words
        debug_this = word in debug_words

        if debug_this:
            print("\nDEBUG {word}:")
            print("  In rejected list: {word in rejected_words}")

        # Skip rejected words
        if word in rejected_words:
            if debug_this:
                print("  FILTERED: In rejected list")
            continue

        # Must contain center letter
        if center not in word:
            if debug_this:
                print("  FILTERED: No center letter '{center}'")
            continue

        # Must only use allowed letters
        if not set(word) <= allowed_letters:
            if debug_this:
                print(
                    "  FILTERED: Uses forbidden letters: {set(word) - allowed_letters}"
                )
            continue

        # Length check
        if len(word) < 4:
            if debug_this:
                print("  FILTERED: Too short ({len(word)} chars)")
            continue

        # NYT rejection filter
        if is_likely_nyt_rejected(word):
            if debug_this:
                print("  FILTERED: Likely rejected by NYT")
            continue

        # NYT word filter
        if not is_likely_nyt_word(word):
            if debug_this:
                print("  FILTERED: Not likely NYT word")
            continue

        if debug_this:
            print("  INCLUDED! ✓")
        valid_words.append(word)

    print("\nFound {len(valid_words)} valid words:")
    for word in sorted(valid_words):
        print("  {word}")


if __name__ == "__main__":
    debug_solve()

"""
Quality-based spelling bee solver using cascading high-quality dictionaries.
Uses Oxford/Webster-style authoritative sources rather than hardcoded lists.
"""

import subprocess
import data_persistence
import word_filtering


def load_google_common_words():
    """Load Google's 10,000 most common English words."""
    try:
        with open("google-10000-common.txt", "r", encoding="utf-8") as f:
            words = set()
            for line in f:
                word = line.strip().lower()
                if len(word) >= 4 and word.isalpha():
                    words.add(word)
        return words
    except FileNotFoundError:
        print("Google common words not found")
        return set()


def load_webster_words():
    """Load Webster's/American English dictionary words."""
    try:
        with open("/usr/share/dict/american-english", "r", encoding="utf-8") as f:
            words = set()
            for line in f:
                word = line.strip().lower()
                if len(word) >= 4 and word.isalpha():
                    words.add(word)
        return words
    except FileNotFoundError:
        print("Webster's dictionary not found")
        return set()


def load_aspell_words():
    """Load aspell dictionary words (comprehensive English)."""
    try:
        result = subprocess.run(
            ["aspell", "-d", "en", "dump", "master"],
            capture_output=True,
            text=True,
            check=True,
        )
        words = set()
        for line in result.stdout.strip().split("\n"):
            word = line.strip().lower()
            if len(word) >= 4 and word.isalpha():
                words.add(word)
        return words
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Aspell dictionary not available")
        return set()


def solve_puzzle_quality(center_letter, outer_letters, debug=False):
    """
    Quality-based solver using cascading authoritative dictionaries:
    1. Google Common Words (highest confidence - most frequently used)
    2. Webster's Dictionary (high confidence - authoritative American English)
    3. Aspell Dictionary (good confidence - comprehensive but filtered)

    Each tier adds words not found in higher tiers.
    """
    center = center_letter.lower()
    outer = outer_letters.lower()
    allowed_letters = set(center + outer)

    print(f"Solving puzzle: Center='{center.upper()}' Outer='{outer.upper()}'")
    if debug:
        print("DEBUG MODE: Will show dictionary source for each word")

    # Load all dictionaries
    print("\nLoading authoritative dictionaries...")
    google_words = load_google_common_words()
    webster_words = load_webster_words()
    aspell_words = load_aspell_words()

    print(f"Google Common Words: {len(google_words)} words")
    print(f"Webster's Dictionary: {len(webster_words)} words")
    print(f"Aspell Dictionary: {len(aspell_words)} words")

    # Load rejected words
    rejected_words = data_persistence.load_rejected_words()

    solutions = []
    pangrams = []
    found_words = set()

    if debug:
        print("\n=== DEBUG: Word-by-word analysis ===")

    # Dictionary tiers (base_confidence no longer used - calculated dynamically)
    dictionary_tiers = [
        (google_words, "GOOGLE_COMMON"),
        (webster_words, "WEBSTER"),
        (aspell_words, "ASPELL"),
    ]

    for word_set, source_name in dictionary_tiers:
        tier_found = 0

        for word in word_set:
            # Skip if already found in higher tier
            if word in found_words:
                continue

            # Must contain center letter
            if center not in word:
                if debug and word in ["capo", "capon", "papa", "atop", "upon"]:
                    print(
                        f"  {
                            word:<15} [{source_name}] FILTERED: No center letter '{center}'"
                    )
                continue

            # Must only use allowed letters
            if not set(word) <= allowed_letters:
                if debug and word in ["capo", "capon", "papa", "atop", "upon"]:
                    forbidden = set(word) - allowed_letters
                    print(
                        f"  {
                            word:<15} [{source_name}] FILTERED: Uses forbidden letters {forbidden}"
                    )
                continue

            # Must be long enough
            if len(word) < 4:
                if debug and word in ["capo", "capon", "papa", "atop", "upon"]:
                    print(
                        f"  {
                            word:<15} [{source_name}] FILTERED: Too short ({
                            len(word)} chars)"
                    )
                continue

            # Skip rejected words
            if word in rejected_words:
                if debug:
                    print(
                        f"  {word:<15} [{source_name}] FILTERED: In rejected words list"
                    )
                continue

            # Apply intelligent filtering for obvious non-NYT words
            if word_filtering.is_likely_nyt_rejected(word):
                if debug and word in ["capo", "capon", "papa", "atop", "upon", "napa"]:
                    print(f"  {word:<15} [{source_name}] FILTERED: Likely NYT rejected")
                continue

            # Valid word found!
            word_len = len(word)
            is_pangram = len(set(word)) == 7

            if is_pangram:
                points = word_len + 7
                pangrams.append(word)
            elif word_len == 4:
                points = 1
            else:
                points = word_len

            # Calculate confidence based on dictionary presence
            # Any legitimate dictionary = 100% confidence (it's a real word)
            # Multiple dictionaries = additive confidence (more authoritative sources)
            confidence = 0
            source_list = []

            if word in google_words:
                confidence += 100
                source_list.append("GOOGLE")
            if word in webster_words:
                confidence += 100
                source_list.append("WEBSTER")
            if word in aspell_words:
                confidence += 100
                source_list.append("ASPELL")

            # Should always be at least 100% since we found it in current word_set
            confidence = max(confidence, 100)
            source_display = (
                "+".join(source_list) if len(source_list) > 1 else source_name
            )

            solutions.append((word, points, confidence))
            found_words.add(word)
            tier_found += 1

            if debug:
                pangram_note = " (PANGRAM)" if is_pangram else ""
                print(
                    f"  {
                        word:<15} [{source_display}] ACCEPTED: {points} pts, {confidence}% confidence{pangram_note}"
                )

        print(f"Found {tier_found} new words in {source_name}")

    # Sort by confidence (descending), then by points (descending)
    solutions.sort(key=lambda x: (-x[2], -x[1]))

    print(f"\nTotal: {len(solutions)} valid words, {len(pangrams)} pangrams")

    return solutions, pangrams

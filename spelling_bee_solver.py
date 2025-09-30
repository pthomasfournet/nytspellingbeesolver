#!/usr/bin/env python3
"""
New York Times Spelling Bee Solver

Rules:
- Words must contain at least 4 letters
- Words must include the center letter
- Words can only use letters from the 7 available letters
- Letters can be used more than once
- Each puzzle has at least one "pangram" using all 7 letters
"""

import sys
import json
from pathlib import Path


def is_likely_nyt_word(word):
    """Filter out words unlikely to be in NYT Spelling Bee."""
    # Reject scientific/technical suffixes (minerals, medical terms)
    if len(word) > 6:
        if word.endswith(('itic', 'otic')) and word not in ['biotic', 'otic', 'abiotic']:
            return False
        if word.endswith('ite') and word not in ['bite', 'cite', 'elite', 'finite', 'ignite', 'invite',
                                                   'polite', 'quite', 'site', 'white', 'write', 'lite',
                                                   'kite', 'mite', 'rite', 'smite', 'spite', 'trite', 'unite']:
            # Likely a mineral/scientific term
            return False

    # Reject most -ee suffix variations (except common ones)
    if word.endswith('ee') and len(word) > 5:
        if word not in ['settee', 'trustee', 'devotee', 'coffee', 'toffee', 'refugee',
                        'employee', 'committee', 'emcee']:
            return False

    # Reject most foreign words (French/Irish endings)
    if word.endswith(('oi', 'etoile')) or word in ['ceili', 'boite', 'ciel']:
        return False

    # Very short obscure words (4 letters) - keep only common ones
    if len(word) == 4:
        common_4letter = {'able', 'back', 'best', 'both', 'call', 'come', 'does', 'each',
                         'even', 'find', 'give', 'good', 'hand', 'help', 'here', 'just',
                         'know', 'last', 'life', 'long', 'look', 'made', 'make', 'many',
                         'more', 'most', 'move', 'much', 'must', 'name', 'need', 'next',
                         'only', 'over', 'part', 'same', 'seem', 'some', 'such', 'take',
                         'tell', 'than', 'that', 'them', 'then', 'they', 'this', 'time',
                         'very', 'want', 'well', 'what', 'when', 'will', 'with', 'work',
                         'year', 'your', 'bile', 'bill', 'bite', 'boil', 'cite', 'coil',
                         'lice', 'lilt', 'lite', 'obit', 'tile', 'till', 'tilt', 'toil',
                         'loci', 'olio', 'otic'}
        if word not in common_4letter and not word.isalpha():
            return False

    return True


def load_dictionary(dict_path=None):
    """Load dictionary words from SOWPODS or system dictionary."""
    # Try SOWPODS first (better for word games)
    if dict_path is None:
        sowpods_path = Path.home() / "sowpods.txt"
        if sowpods_path.exists():
            dict_path = str(sowpods_path)
        else:
            dict_path = "/usr/share/dict/words"

    try:
        with open(dict_path, 'r') as f:
            words = set()
            for word in f:
                word = word.strip()
                # Skip short words and words with apostrophes/hyphens
                if len(word) < 4 or "'" in word or "-" in word:
                    continue
                word_lower = word.lower()

                # Apply NYT-specific filters
                if not is_likely_nyt_word(word_lower):
                    continue

                words.add(word_lower)
        return words
    except FileNotFoundError:
        print(f"Dictionary not found at {dict_path}")
        return set()


def load_rejected_words():
    """Load globally rejected words (not in NYT Spelling Bee)."""
    rejected_file = Path.home() / ".spelling_bee_rejected.json"
    if rejected_file.exists():
        try:
            with open(rejected_file, 'r') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_rejected_words(rejected_words):
    """Save globally rejected words."""
    rejected_file = Path.home() / ".spelling_bee_rejected.json"
    with open(rejected_file, 'w') as f:
        json.dump(list(rejected_words), f, indent=2)


def load_found_words(center, outer, date=None):
    """Load previously found words for this puzzle."""
    if date:
        found_file = Path.home() / f".spelling_bee_{date}.json"
    else:
        puzzle_id = f"{center}{''.join(sorted(outer))}".lower()
        found_file = Path.home() / f".spelling_bee_{puzzle_id}.json"

    if found_file.exists():
        try:
            with open(found_file, 'r') as f:
                data = json.load(f)
                # Handle both old format (list) and new format (dict with metadata)
                if isinstance(data, list):
                    return set(data)
                elif isinstance(data, dict):
                    return set(data.get('words', []))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_found_words(center, outer, found_words, date=None):
    """Save found words for this puzzle."""
    if date:
        found_file = Path.home() / f".spelling_bee_{date}.json"
    else:
        puzzle_id = f"{center}{''.join(sorted(outer))}".lower()
        found_file = Path.home() / f".spelling_bee_{puzzle_id}.json"

    # Save with metadata
    data = {
        'date': date,
        'center': center,
        'outer': outer,
        'words': list(found_words)
    }
    with open(found_file, 'w') as f:
        json.dump(data, f, indent=2)


def find_solutions(center_letter, outer_letters, dictionary, exclude_found=None, rejected_words=None):
    """
    Find all valid words for the Spelling Bee puzzle.

    Args:
        center_letter: The required center letter (str)
        outer_letters: The 6 outer letters (str or list)
        dictionary: Set of valid words
        exclude_found: Set of words to exclude from display (already found)
        rejected_words: Set of words to exclude globally (not accepted by NYT)

    Returns:
        dict with 'words', 'pangrams', and 'total_points'
    """
    center = center_letter.lower()
    allowed_letters = set(center + ''.join(outer_letters).lower())
    exclude_found = exclude_found or set()
    rejected_words = rejected_words or set()

    solutions = []
    pangrams = []
    total_points = 0
    total_available = 0

    for word in dictionary:
        # Skip rejected words
        if word in rejected_words:
            continue

        # Must contain center letter
        if center not in word:
            continue

        # Must only use allowed letters
        if not all(letter in allowed_letters for letter in word):
            continue

        # Valid word found
        word_len = len(word)

        # Calculate points (4-letter words = 1 point, longer = length, pangrams = length + 7)
        is_pangram = len(set(word)) == 7

        if is_pangram:
            points = word_len + 7
            pangrams.append(word)
        elif word_len == 4:
            points = 1
        else:
            points = word_len

        total_available += points

        # Only add to display if not already found
        if word not in exclude_found:
            solutions.append((word, points, is_pangram))
            total_points += points

    # Sort by points (descending), then alphabetically
    solutions.sort(key=lambda x: (-x[1], x[0]))

    return {
        'words': solutions,
        'pangrams': pangrams,
        'total_points': total_points,
        'total_available': total_available,
        'found_count': len(exclude_found)
    }


def calculate_word_confidence(word):
    """
    Calculate confidence score (0-100) that NYT will accept this word.
    Higher score = more likely to be accepted.
    """
    score = 50  # Start at neutral

    # Pangrams are always shown
    if len(set(word)) == 7:
        return 100

    # Length bonus - common words are often 4-8 letters
    if 4 <= len(word) <= 6:
        score += 20
    elif 7 <= len(word) <= 8:
        score += 10
    elif len(word) >= 9:
        score -= 15  # Very long words often obscure

    # Common endings (positive signals)
    common_endings = {
        'ing': 20, 'tion': 20, 'able': 15, 'ible': 15, 'ness': 15,
        'less': 15, 'ment': 15, 'ful': 15, 'ous': 15, 'ance': 15,
        'ence': 15, 'ant': 10, 'ent': 10, 'er': 10, 'or': 10,
        'ly': 10, 'ed': 10, 'al': 10, 'ive': 10, 'ate': 10
    }
    for ending, bonus in common_endings.items():
        if word.endswith(ending) and len(word) > len(ending) + 2:
            score += bonus
            break

    # Penalize obscure patterns
    obscure_patterns = [
        ('itic', -30), ('otic', -25), ('olite', -30),
        ('elli', -20), ('obi', -25), ('oboli', -30),
        ('ii', -20), ('uu', -25), ('aa', -20)
    ]
    for pattern, penalty in obscure_patterns:
        if pattern in word:
            score += penalty

    # Penalize 'oo' in middle of word
    if 'oo' in word[1:-1]:
        score -= 10

    # Penalize 'pp' in short words
    if word.count('pp') > 0 and len(word) < 6:
        score -= 15

    # Handle repeated letters - some are common (poop, noon, papa), some aren't
    if len(word) <= 5:
        # Common repeated-letter words get a bonus
        common_repeated = ['poop', 'noon', 'papa', 'mama', 'toot', 'peep', 'noon', 'putt', 'mutt', 'butt']
        if word in common_repeated:
            score += 20
        else:
            # Penalize unusual doubles in short words
            unusual_doubles = ['pp', 'tt', 'oo', 'aa', 'uu']
            for double in unusual_doubles:
                if double in word:
                    score -= 10

    # Penalize foreign-looking words
    foreign_endings = ['ata', 'atta', 'otto', 'etto', 'ooh', 'aah']
    for ending in foreign_endings:
        if word.endswith(ending):
            score -= 15

    # Penalize words ending in -an/-on that might be foreign
    if len(word) >= 6 and word.endswith(('an', 'on')) and word[-3] in 'aeiouy':
        score -= 10

    # Bonus for recognizable common words and compound words
    very_common = [
        'about', 'upon', 'into', 'onto', 'cannot', 'output', 'potato',
        'cotton', 'button', 'coupon', 'caption', 'catnap', 'copout',
        'cutup', 'setup', 'popup', 'letup', 'getup', 'makeup', 'takeout',
        'ayout', 'payout', 'without', 'turnout', 'workout', 'cookout',
        'atop', 'coup', 'pact', 'pant', 'punt', 'pout', 'taco', 'coat',
        'auto', 'unto', 'tattoo', 'cocoa', 'cancan'
    ]
    if word in very_common:
        score += 35

    # Bonus for recognizable compound word patterns
    compound_patterns = [
        ('cat', 'nap'), ('cop', 'out'), ('cut', 'up'), ('put', 'out'),
        ('top', 'coat'), ('out', 'put'), ('un', 'cap')
    ]
    for part1, part2 in compound_patterns:
        if word == part1 + part2:
            score += 25
            break

    # Major penalty for words ending in -an, -on, -un that aren't common
    if len(word) >= 5 and word.endswith(('tan', 'pan', 'ton', 'pon', 'tun', 'pun')) and word not in very_common:
        # Check if it's likely a foreign/technical term
        if word.endswith(('tan', 'pan', 'ton', 'pon')) and word not in ['cotton', 'button', 'coupon', 'canton']:
            score -= 25

    # Penalty for words with unusual letter patterns (likely foreign)
    unusual_sequences = ['aca', 'ata', 'uca', 'uta', 'nta', 'nca', 'oupa', 'patu', 'paua', 'noup', 'caup']
    for seq in unusual_sequences:
        if seq in word:
            score -= 30
            break

    # Heavy penalty for likely obscure words (not in common vocabulary)
    # Comprehensive list of obscure words to reject
    obscure_word_list = [
        # 4-letter obscure
        'atap', 'paca', 'paco', 'caup', 'noup', 'oupa', 'patu', 'paua', 'poco', 'tapa', 'tapu', 'topo', 'upta',
        'capa', 'napa', 'pont', 'puna', 'pupa', 'pupu', 'pott', 'noop', 'poon', 'poot', 'oppo',
        # 5-letter obscure
        'attap', 'apoop', 'napoo', 'nappa', 'poonac', 'pucan', 'poupt', 'putto', 'tappa',
        'capot', 'caput', 'coapt', 'panto', 'punto', 'potoo', 'potto', 'puton',
        # 6+ letter obscure
        'captan', 'pantun', 'panton', 'pataca', 'ponton', 'tupuna', 'autoput', 'catapan',
        'cocopan', 'puccoon', 'taupata', 'caponata', 'optant', 'outtop', 'puncta', 'puncto'
    ]

    obscure_indicators = [
        word in obscure_word_list,
        len(word) == 5 and word.endswith(('ta', 'ca', 'pa', 'to', 'po')) and word not in very_common,
        len(word) >= 6 and word.endswith(('ant', 'pon', 'tan', 'tun', 'cta', 'cto')) and word not in very_common,
    ]
    if any(obscure_indicators):
        score -= 50

    # Cap score between 0 and 100
    return max(0, min(100, score))


def is_common_word(word):
    """Check if a word is common enough to show by default."""
    confidence = calculate_word_confidence(word)
    return confidence >= 40  # Show words with 40+ confidence


def display_results(results, show_all=False, top_n=None):
    """Display the solver results in a formatted way."""
    words = results['words']
    pangrams = results['pangrams']
    total_points = results['total_points']
    total_available = results['total_available']
    found_count = results['found_count']

    # Add confidence scores and sort by points (highest first), then confidence
    words_with_confidence = [(w, p, pan, calculate_word_confidence(w)) for w, p, pan in words]
    words_with_confidence.sort(key=lambda x: (-x[1], -x[3], x[0]))  # Sort by points desc, confidence desc, name asc

    # Filter to common words unless --all
    if not show_all:
        common_words = [(w, p, pan, conf) for w, p, pan, conf in words_with_confidence if conf >= 40]
        obscure_count = len(words_with_confidence) - len(common_words)
        obscure_points = total_points - sum(p for _, p, _, _ in common_words)
        words_with_confidence = common_words
        total_points = sum(p for _, p, _, _ in common_words)

    # Limit to top N if specified
    if top_n:
        words_with_confidence = words_with_confidence[:top_n]

    print(f"\n{'='*60}")
    if found_count > 0:
        points_found = total_available - results['total_points']
        print(f"Progress: {found_count} words found ({points_found} points)")
        print(f"Remaining: {len(words)} words ({total_points} points)")
        if not show_all and obscure_count > 0:
            print(f"Hidden: {obscure_count} obscure words ({obscure_points} points)")
            print("Use --all to show all words")
    else:
        print(f"Found {len(words)} words worth {total_points} points")
        if not show_all and obscure_count > 0:
            print(f"Hidden: {obscure_count} obscure words ({obscure_points} points)")
    print(f"Pangrams: {len(pangrams)}")
    print(f"{'='*60}\n")

    if len(words) == 0:
        if not show_all and obscure_count > 0:
            print(f"All common words found! {obscure_count} obscure words remain.")
            print("Use --all to see them")
        else:
            print("✓ All words found! Congratulations!")
        return

    if pangrams:
        print("🌟 PANGRAMS:")
        for pangram in pangrams:
            print(f"  {pangram.upper()}")
        print()

    print("Remaining words:")
    for word, points, is_pangram, confidence in words_with_confidence:
        marker = "🌟" if is_pangram else " "
        print(f"{marker} {word:20} ({points} pts, {confidence}% confidence)")


def draw_hexagon(center, outer):
    """Draw honeycomb hexagon with letters."""
    letters = list(outer.upper())
    c = center.upper()

    print("\n" + " " * 10 + "     ___")
    print(" " * 10 + f"    /   \\")
    print(" " * 10 + f"   / {letters[0]:^3} \\")
    print(" " * 5 + " ___/___  ___\\___")
    print(" " * 5 + f"/   \\   /   \\   /")
    print(" " * 5 + f"/ {letters[5]:^3} \\ / {c:^3} \\ / {letters[1]:^3} \\")
    print(" " * 5 + "\\___  ___/___  ___/")
    print(" " * 9 + f"\\   /   \\   /")
    print(" " * 9 + f" \\ / {letters[4]:^3} \\ / {letters[2]:^3} \\")
    print(" " * 9 + "  \\___  ___/")
    print(" " * 13 + "\\   /")
    print(" " * 13 + f" \\ / {letters[3]:^3}")
    print(" " * 13 + "  \\___/\n")


def interactive_mode():
    """Interactive mode with hexagon display."""
    print("New York Times Spelling Bee Solver")
    print("=" * 60)

    while True:
        # Get center letter
        center = input("\nEnter CENTER letter: ").strip().lower()
        if len(center) != 1 or not center.isalpha():
            print("❌ Error: Must enter exactly 1 letter")
            continue

        # Get outer letters
        outer = input("Enter 6 OUTER letters: ").strip().lower()
        if len(outer) != 6 or not outer.isalpha():
            print("❌ Error: Must enter exactly 6 letters")
            continue

        # Display hexagon
        draw_hexagon(center, outer)

        # Confirm
        ready = input("Ready to solve? (y/n): ").strip().lower()
        if ready == 'y':
            return center, outer, False, False, False, 46  # Return defaults with top_n=46
        elif ready == 'n':
            change = input("Change letters? (y/n): ").strip().lower()
            if change != 'y':
                print("Exiting...")
                sys.exit(0)
            # Loop continues to re-enter letters
        else:
            print("Please enter 'y' or 'n'")


def main():
    """Main function to run the Spelling Bee solver."""
    # Check for special flags
    auto_solve = "-y" in sys.argv or "--yes" in sys.argv

    # Get puzzle input
    if len(sys.argv) >= 3 and sys.argv[1] not in ['-y', '--yes']:
        # CLI mode with letters provided
        center = sys.argv[1]
        outer = sys.argv[2]
        mark_mode = "--mark" in sys.argv or "-m" in sys.argv
        reset_mode = "--reset" in sys.argv or "-r" in sys.argv
        show_all = "--all" in sys.argv or "-a" in sys.argv

        # Check for --top N flag
        top_n = None
        for i, arg in enumerate(sys.argv):
            if arg == "--top" and i + 1 < len(sys.argv):
                try:
                    top_n = int(sys.argv[i + 1])
                except ValueError:
                    pass

        # Default to top 46 if not specified
        if top_n is None and not mark_mode and not reset_mode:
            top_n = 46
    else:
        # Interactive mode
        center, outer, mark_mode, reset_mode, show_all, top_n = interactive_mode()

    # Validate input
    if len(center) != 1 or len(outer) != 6:
        print("Error: Need 1 center letter and 6 outer letters")
        sys.exit(1)

    if not center.isalpha() or not outer.isalpha():
        print("Error: Only letters allowed")
        sys.exit(1)

    # Handle reset mode
    if reset_mode:
        puzzle_id = f"{center}{''.join(sorted(outer))}".lower()
        found_file = Path.home() / f".spelling_bee_{puzzle_id}.json"
        if found_file.exists():
            found_file.unlink()
            print("\n✓ Reset puzzle. All words unmarked.")
        else:
            print("\nNo saved progress for this puzzle.")
        sys.exit(0)

    # Load dictionary
    print("\nLoading dictionary...")
    dictionary = load_dictionary()

    if not dictionary:
        print("Could not load dictionary. Please check your system dictionary.")
        sys.exit(1)

    print(f"Loaded {len(dictionary)} words")

    # Load previously found words and rejected words
    found_words = load_found_words(center, outer)
    rejected_words = load_rejected_words()

    if rejected_words:
        print(f"Loaded {len(rejected_words)} rejected words")

    # Find solutions
    print(f"\nSolving puzzle: Center='{center.upper()}' Outer='{outer.upper()}'")
    results = find_solutions(center, outer, dictionary, exclude_found=found_words, rejected_words=rejected_words)

    # Display results
    display_results(results, show_all=show_all, top_n=top_n)

    # Interactive marking mode
    if mark_mode:
        print("\nEnter words you've found (one per line, 'q' to quit):")
        print("Prefix with '-' to mark as rejected (e.g., '-bibliotic')")
        while True:
            try:
                word = input("> ").strip().lower()
                if word == 'q':
                    break

                # Check if marking as rejected
                if word.startswith('-'):
                    reject_word = word[1:].strip()
                    if reject_word:
                        rejected_words.add(reject_word)
                        save_rejected_words(rejected_words)
                        print(f"  ✗ Rejected: {reject_word} (will be hidden globally)")
                elif word in found_words:
                    print(f"  Already marked: {word}")
                else:
                    found_words.add(word)
                    save_found_words(center, outer, found_words)
                    print(f"  ✓ Marked: {word}")
            except (EOFError, KeyboardInterrupt):
                break
        print("\nProgress saved!")


if __name__ == "__main__":
    main()

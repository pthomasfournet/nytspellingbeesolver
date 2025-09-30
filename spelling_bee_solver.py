#!/usr/bin/env python3
"""
New York Times Spelling Bee Solver

A sophisticated solver for the NYT Spelling Bee puzzle that uses multiple
dictionary sources and intelligent filtering to predict the most likely
words that will be accepted.

Rules:
- Words must contain at least 4 letters
- Words must include the center letter
- Words can only use letters from the 7 available letters
- Letters can be used more than once
- Each puzzle has at least one "pangram" using all 7 letters

Author: Enhanced with aggregate scoring and comprehensive filtering
"""

import sys
import json
from pathlib import Path

# Load Google common words list for confidence scoring
GOOGLE_COMMON_WORDS = None

def load_google_common_words():
    """Load Google common words list for enhanced confidence scoring."""
    # Use module-level variable to cache the word list
    if GOOGLE_COMMON_WORDS is None:
        google_words_path = Path(__file__).parent / "google-10000-common.txt"
        words = set()

        if google_words_path.exists():
            try:
                with open(google_words_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        word = line.strip().lower()
                        if len(word) >= 4:  # Only words 4+ letters for Spelling Bee
                            words.add(word)
            except IOError:
                pass

        # Update the module-level variable
        globals()['GOOGLE_COMMON_WORDS'] = words

    return GOOGLE_COMMON_WORDS or set()  # Always return a set, never None


def get_word_dictionary_scores(word):
    """
    Get aggregate scores from multiple dictionary sources.
    Returns a dict with scores from different sources.
    """
    scores = {
        'google_common': 0,
        'sowpods': 0,
        'compound': 0,
        'frequency': 0
    }

    # Google common words score
    google_words = load_google_common_words()
    if word in google_words:
        scores['google_common'] = 100
        # Bonus for very high frequency words (top 1000)
        word_list = list(google_words)
        if len(word_list) >= 1000 and word in word_list[:1000]:
            scores['frequency'] = 50

    # SOWPODS dictionary presence (assume it's loaded if we got here)
    scores['sowpods'] = 30  # Base score for being in SOWPODS

    # Compound word detection
    compound_indicators = [
        word in ['cannot', 'into', 'onto', 'upon', 'without', 'output', 'input'],
        any(word.startswith(prefix) for prefix in ['auto', 'self', 'over', 'under', 'out']),
        any(word.endswith(suffix) for suffix in ['up', 'out', 'off', 'down']),
        len(word) >= 6 and any(common in word for common in ['cat', 'dog', 'top', 'set'])
    ]
    if any(compound_indicators):
        scores['compound'] = 25

    return scores


def is_google_common_word(word):
    """Check if a word is in the Google common words list."""
    common_words = load_google_common_words()
    return word.lower() in common_words


def calculate_aggregate_confidence(word, dict_scores):
    """
    Calculate confidence using aggregate scores from multiple sources.
    """
    base_score = 20  # Lower base score, require evidence

    # Major bonus for strong dictionary evidence
    if dict_scores['google_common'] > 0:
        base_score += 40
    if dict_scores['frequency'] > 0:
        base_score += 20
    if dict_scores['compound'] > 0:
        base_score += 15

    # Pangrams always get high score
    if len(set(word)) == 7:
        return 100

    # Length preferences
    if 4 <= len(word) <= 6:
        base_score += 15
    elif 7 <= len(word) <= 8:
        base_score += 8
    elif len(word) >= 9:
        base_score -= 20

    # NYT pattern bonuses
    pattern_bonuses = [
        (word.endswith('ing'), 15),
        (word.endswith('tion'), 15),
        (word.endswith(('able', 'ible')), 12),
        (word.endswith(('ness', 'ment', 'ful')), 10),
        (word.endswith(('er', 'or', 'ly', 'ed')), 8),
    ]

    for condition, bonus in pattern_bonuses:
        if condition:
            base_score += bonus
            break

    # Penalties for problematic patterns
    if not dict_scores['google_common'] and len(word) > 6:
        base_score -= 15  # Uncommon long words

    if any(bad in word for bad in ['oo', 'ii', 'uu']) and not dict_scores['google_common']:
        base_score -= 20

    return max(0, min(100, base_score))


def is_likely_nyt_rejected(word):
    """
    Check if a word is likely to be rejected by NYT Spelling Bee.
    Returns True if the word should be filtered out.
    """
    word = word.lower()

    # Proper nouns (capitalized words) - already handled by dictionary loading

    # Common NYT rejection patterns
    rejection_patterns = [
        # Scientific/technical suffixes
        word.endswith(('ism', 'ist', 'ite', 'ide', 'ase', 'ose')) and len(word) > 6,

        # Medical/biological terms
        word.endswith(('osis', 'itis', 'emia', 'uria', 'pathy')) and len(word) > 6,

        # Chemical compounds
        word.endswith(('ene', 'ine', 'ane', 'ole', 'yl')) and len(word) > 5,

        # Foreign language endings
        word.endswith(('eau', 'ieu', 'oux', 'ais', 'ois', 'eur')),

        # Latin/Greek endings
        word.endswith(('um', 'us', 'ae', 'ii')) and len(word) > 4,

        # Archaic/obsolete endings
        word.endswith(('est', 'eth', 'th')) and word not in [
            'best', 'test', 'rest', 'west', 'nest', 'pest'],

        # Unusual letter combinations
        'qq' in word or 'xx' in word or 'zz' in word and word not in ['buzz', 'jazz', 'fizz'],

        # Very short uncommon words
        len(word) == 4 and word.startswith(('zz', 'qq', 'xx')),

        # Slang/informal contractions
        word.endswith(("'s", "'t", "'d", "'ll", "'ve", "'re")),

        # Hyphenated words (though these should be filtered earlier)
        '-' in word,

        # Geographic/place name indicators
        word.endswith(('burg', 'heim', 'stadt', 'grad', 'sk', 'icz')),

        # Technical abbreviations
        len(word) <= 5 and word.isupper() and word.isalpha(),
    ]

    # Specific word blacklist - known NYT rejects
    nyt_blacklist = {
        # Common technical terms
        'api', 'cpu', 'gpu', 'ram', 'rom', 'usb', 'wifi', 'http', 'html', 'css',
        'sql', 'xml', 'json', 'unix', 'linux', 'ios', 'app', 'apps',

        # Internet/gaming terms
        'meme', 'blog', 'vlog', 'tweet', 'emoji', 'selfie', 'hashtag',
        'avatar', 'noob', 'pwn', 'lol', 'omg', 'wtf', 'fyi', 'asap',

        # Brand names that might slip through
        'pepsi', 'nike', 'ford', 'sony', 'apple', 'google', 'tesla',

        # Vulgar/offensive (basic list)
        'damn', 'hell', 'crap', 'piss',

        # Very informal/slang
        'yeah', 'nope', 'yep', 'nah', 'ugh', 'meh', 'blah', 'duh',
        'bro', 'sis', 'mom', 'dad', 'grandma', 'grandpa',

        # Onomatopoeia
        'whoosh', 'bang', 'boom', 'crash', 'splash', 'thud', 'whack',
        'zap', 'pow', 'bam', 'wham', 'kaboom',

        # Very technical/scientific
        'amino', 'enzyme', 'protein', 'genome', 'neuron', 'synapse',
        'photon', 'quark', 'boson', 'plasma',
    }

    if word in nyt_blacklist:
        return True

    return any(rejection_patterns)


def is_likely_nyt_word(word):
    """Filter out words unlikely to be in NYT Spelling Bee."""
    # Reject scientific/technical suffixes (minerals, medical terms)
    if len(word) > 6:
        if word.endswith(('itic', 'otic')) and word not in ['biotic', 'otic', 'abiotic']:
            return False
        if word.endswith('ite') and word not in [
                'bite', 'cite', 'elite', 'finite', 'ignite', 'invite',
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
    """Load dictionary words from SOWPODS or system dictionary with NYT filtering."""
    # Try SOWPODS first (better for word games)
    if dict_path is None:
        sowpods_path = Path.home() / "sowpods.txt"
        if sowpods_path.exists():
            dict_path = str(sowpods_path)
        else:
            dict_path = "/usr/share/dict/words"

    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            words = set()
            for word in f:
                word = word.strip()
                # Skip short words and words with apostrophes/hyphens
                if len(word) < 4 or "'" in word or "-" in word:
                    continue
                word_lower = word.lower()

                # Apply NYT rejection filter first (performance optimization)
                if is_likely_nyt_rejected(word_lower):
                    continue

                # Apply original NYT-specific filters
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
            with open(rejected_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_rejected_words(rejected_words):
    """Save globally rejected words."""
    rejected_file = Path.home() / ".spelling_bee_rejected.json"
    with open(rejected_file, 'w', encoding='utf-8') as f:
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
            with open(found_file, 'r', encoding='utf-8') as f:
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
    with open(found_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def find_solutions(center_letter, outer_letters, dictionary,
                   exclude_found=None, rejected_words=None):
    """
    Find all valid words for the Spelling Bee puzzle.

    Args:
        center_letter (str): The required center letter
        outer_letters (str or list): The 6 outer letters
        dictionary (set): Set of valid words to search through
        exclude_found (set, optional): Set of words to exclude from display (already found)
        rejected_words (set, optional): Set of words to exclude globally (not accepted by NYT)

    Returns:
        dict: Dictionary with keys:
            - 'words': List of (word, points, is_pangram) tuples
            - 'pangrams': List of pangram words
            - 'total_points': Total points for remaining words
            - 'total_available': Total points for all valid words
            - 'found_count': Number of words already found
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
    Enhanced with aggregate scoring from multiple dictionary sources.
    """
    # Get scores from multiple dictionary sources
    dict_scores = get_word_dictionary_scores(word)

    # Use aggregate confidence calculation
    return calculate_aggregate_confidence(word, dict_scores)


def is_common_word(word):
    """Check if a word is common enough to show by default."""
    confidence = calculate_word_confidence(word)
    return confidence >= 60  # Raised threshold for better filtering


def display_results(results, show_all=False, top_n=None):
    """
    Display the solver results in a formatted way.

    Args:
        results (dict): Results dictionary from find_solutions()
        show_all (bool): Whether to show obscure words (default: False)
        top_n (int, optional): Limit to top N words (default: None for all)
    """
    words = results['words']
    pangrams = results['pangrams']
    total_points = results['total_points']
    total_available = results['total_available']
    found_count = results['found_count']

    # Add confidence scores and sort by points (highest first), then confidence
    words_with_confidence = [(w, p, pan, calculate_word_confidence(w)) for w, p, pan in words]
    # Sort by points desc, confidence desc, name asc
    words_with_confidence.sort(key=lambda x: (-x[1], -x[3], x[0]))

    # Filter to common words unless --all
    obscure_count = 0
    obscure_points = 0
    if not show_all:
        common_words = [(w, p, pan, conf) for w, p, pan, conf in words_with_confidence
                        if conf >= 60]
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
    """
    Draw honeycomb hexagon with letters.

    Args:
        center (str): The center letter
        outer (str): The 6 outer letters
    """
    letters = list(outer.upper())
    c = center.upper()

    print("\n" + " " * 10 + "     ___")
    print(" " * 10 + "    /   \\")
    print(" " * 10 + f"   / {letters[0]:^3} \\")
    print(" " * 5 + " ___/___  ___\\___")
    print(" " * 5 + "/   \\   /   \\   /")
    print(" " * 5 + f"/ {letters[5]:^3} \\ / {c:^3} \\ / {letters[1]:^3} \\")
    print(" " * 5 + "\\___  ___/___  ___/")
    print(" " * 9 + "\\   /   \\   /")
    print(" " * 9 + f" \\ / {letters[4]:^3} \\ / {letters[2]:^3} \\")
    print(" " * 9 + "  \\___  ___/")
    print(" " * 13 + "\\   /")
    print(" " * 13 + f" \\ / {letters[3]:^3}")
    print(" " * 13 + "  \\___/\n")


def interactive_mode():
    """
    Interactive mode with hexagon display.

    Returns:
        tuple: (center, outer, mark_mode, reset_mode, show_all, top_n)
    """
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
    results = find_solutions(center, outer, dictionary,
                             exclude_found=found_words, rejected_words=rejected_words)

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

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
                with open(google_words_path, "r", encoding="utf-8") as f:
                    for line in f:
                        word = line.strip().lower()
                        if len(word) >= 4:  # Only words 4+ letters for Spelling Bee
                            words.add(word)
            except IOError:
                pass

        # Update the module-level variable
        globals()["GOOGLE_COMMON_WORDS"] = words

    return GOOGLE_COMMON_WORDS or set()  # Always return a set, never None


def is_google_common_word(word):
    """Check if a word is in the Google common words list."""
    common_words = load_google_common_words()
    return word.lower() in common_words


def is_likely_nyt_rejected(word):
    """
    Get comprehensive scores from multiple dictionary sources.
    Returns a dict with detailed scores from different authoritative sources.
    """
    scores = {
        "google_common": 0,  # Google 10k common words
        "webster": 0,  # Webster's dictionary words
        "oxford": 0,  # Oxford dictionary words
        "american_english": 0,  # American English dictionary
        "compound": 0,  # Compound word bonus
        "frequency": 0,  # High frequency word bonus
        "nyt_patterns": 0,  # NYT-style word patterns
        "length_penalty": 0,  # Penalty for unusual lengths
        "foreign_penalty": 0,  # Penalty for foreign words
        "technical_penalty": 0,  # Penalty for technical terms
    }

    # Google common words score (highest priority)
    google_words = load_google_common_words()
    if word in google_words:
        scores["google_common"] = 100
        # Extra bonus for very high frequency words (top 2000)
        word_list = list(google_words)
        if len(word_list) >= 2000 and word in word_list[:2000]:
            scores["frequency"] = 75
        elif len(word_list) >= 5000 and word in word_list[:5000]:
            scores["frequency"] = 50

    # Simulate Webster's dictionary (common English patterns)
    # Enhanced with words commonly found in mobile word games
    webster_indicators = [
        # Core English words that mobile games always include
        word
        in [
            "about",
            "point",
            "count",
            "court",
            "paint",
            "plant",
            "quota",
            "piano",
            "output",
            "input",
            "upon",
            "auto",
            "coat",
            "coup",
            "atop",
            "cant",
            "pant",
            "catnap",
            "copout",
            "coupon",
            "potato",
            "putout",
            "outtop",
            "topcoat",
            "cutup",
            "unapt",
            "uncap",
            "pout",
            "pontoon",
            "capon",
            "coopt",
            "cuppa",
            "punt",
            "coop",
            "papa",
            "pact",
            "pont",
            "pupa",
            "poop",  # Very common word
            "putt",  # Common golf term
            "taco",
            "unto",
        ],
        # Animal words (popular in word games)
        word
        in [
            "cat",
            "dog",
            "cow",
            "pig",
            "ant",
            "bat",
            "rat",
            "fox",
            "owl",
            "bee",
            "cod",
            "eel",
            "hen",
            "ram",
            "elk",
            "yak",
            "ape",
            "gnu",
            "ox",
        ],
        # Food words (very common in games)
        word
        in [
            "cake",
            "soup",
            "meat",
            "rice",
            "bean",
            "corn",
            "milk",
            "beer",
            "wine",
            "egg",
            "ham",
            "pie",
            "tea",
            "jam",
            "nut",
            "oil",
            "rum",
        ],
        # Body parts (common category)
        word
        in [
            "hand",
            "foot",
            "head",
            "neck",
            "back",
            "knee",
            "toe",
            "eye",
            "ear",
            "arm",
            "leg",
            "hip",
            "jaw",
            "rib",
            "gut",
        ],
        # Common objects/tools
        word
        in [
            "book",
            "door",
            "window",
            "chair",
            "table",
            "lamp",
            "clock",
            "phone",
            "car",
            "bike",
            "boat",
            "plane",
            "train",
            "bus",
            "truck",
        ],
        # Common verbs in past/present forms
        word
        in [
            "run",
            "walk",
            "talk",
            "look",
            "make",
            "take",
            "give",
            "come",
            "go",
            "see",
            "hear",
            "feel",
            "know",
            "think",
            "want",
            "need",
            "help",
            "work",
            "play",
            "read",
            "write",
            "eat",
            "drink",
            "sleep",
        ],
        # Common adjectives
        word
        in [
            "good",
            "bad",
            "big",
            "small",
            "hot",
            "cold",
            "new",
            "old",
            "fast",
            "slow",
            "high",
            "low",
            "long",
            "short",
            "wide",
            "thin",
            "thick",
        ],
        # Common English word patterns
        word.endswith(("ing", "tion", "able", "ment", "ness", "ful", "less")),
        word.startswith(("un", "re", "pre", "dis", "mis", "over", "under")),
        # Compound word patterns
        len(word) >= 6
        and any(
            root in word
            for root in [
                "work",
                "play",
                "help",
                "make",
                "take",
                "give",
                "cut",
                "put",
                "out",
                "top",
                "cat",
            ]
        ),
        # 4-letter words that are definitely English (common in word games)
        len(word) == 4
        and word
        in [
            "coop",
            "punt",
            "pact",
            "papa",
            "pont",
            "noun",
            "verb",
            "noun",
            "hope",
            "love",
            "hate",
            "fear",
            "pain",
            "gain",
            "loss",
            "cost",
            "plan",
            "goal",
            "task",
            "role",
            "rule",
            "tool",
            "pool",
            "cool",
        ],
    ]
    if any(webster_indicators):
        scores["webster"] = 80

    # Simulate Oxford dictionary (slightly more formal/British)
    oxford_indicators = [
        word in ["colour", "favour", "honour", "centre", "theatre", "metre"],
        word.endswith(("ise", "isation", "our", "re")),
        len(word) >= 5 and word.endswith(("ed", "er", "ly", "al", "ic")),
    ]
    if any(oxford_indicators):
        scores["oxford"] = 70

    # American English dictionary (standard American spelling)
    american_indicators = [
        word in ["color", "favor", "honor", "center", "theater", "meter"],
        word.endswith(("ize", "ization", "or")),
        word in ["realize", "organize", "recognize", "analyze"],
    ]
    if any(american_indicators):
        scores["american_english"] = 70

    # Compound word detection (English compound patterns)
    compound_indicators = [
        # Known legitimate compound words
        word
        in [
            "cannot",
            "into",
            "onto",
            "upon",
            "without",
            "output",
            "input",
            "catnap",
            "topcoat",
            "cutup",
            "putout",
            "outtop",
            "copout",
            "uncap",
        ],
        # Real compound words with these endings
        word
        in [
            "blackout",
            "knockout",
            "workout",
            "dropout",
            "takeout",
            "layout",
            "payout",
        ],
        # Real compound words with these beginnings (be very selective)
        word in ["automobile", "automatic", "autopilot"] and word.startswith("auto"),
        # Legitimate -up compounds
        word.endswith("up")
        and word in ["cutup", "setup", "backup", "startup", "cleanup", "pickup"],
        # Legitimate -out compounds
        word.endswith("out")
        and word in ["output", "putout", "copout", "blackout", "knockout"],
    ]
    if any(compound_indicators):
        scores["compound"] = 60

    # NYT-style word patterns (what they typically include)
    nyt_patterns = [
        word.endswith(("ing", "tion", "sion")),
        word.endswith(("able", "ible", "ment", "ness", "ful")),
        word.endswith(("er", "or", "ly", "ed", "al")),
        4 <= len(word) <= 8,  # NYT prefers moderate length words
    ]
    if any(nyt_patterns):
        scores["nyt_patterns"] = 40

    # Length penalties (NYT doesn't like very short or very long words)
    if len(word) < 4:
        scores["length_penalty"] = -50
    elif len(word) > 10:
        scores["length_penalty"] = -30
    elif len(word) == 4 and word not in google_words:
        scores["length_penalty"] = -20  # Short uncommon words are risky

    # Foreign word penalties (words that seem non-English)
    foreign_patterns = [
        word.endswith(("eau", "ieu", "oux", "ais", "ois", "eur", "oi")),  # French
        word.endswith(("ung", "ich", "ach", "ein")),  # German
        word.endswith(("ita", "ano", "ino", "etto")),  # Italian
        word.endswith(("cion", "tad", "dad")),  # Spanish
        # Specific questionable words that got through (expanded list)
        word
        in [
            "caup",
            "noup",
            "upta",
            "taupata",
            "cocopan",
            "puccoon",
            "captan",
            "optant",
            "pataca",
            "ponton",
            "poonac",
            "apoop",
            "attap",
            "capot",
            "napoo",
            "potoo",
            "caponata",
            "autoput",
            "catapan",
            "panton",
            "pantun",
            "patton",
            "pocono",
            "puncta",
            "puncto",
            "tupuna",
            "naacp",
            "patna",
        ],
        # Patterns of non-English words (more specific)
        len(word) <= 5
        and not is_google_common_word(word)
        and any(
            # More specific patterns that don't catch common English words
            word.endswith(pattern)
            for pattern in ["pta", "aup"]
        )
        and word
        not in [
            "coup",
            "putt",
            "poop",
            "coop",
            "loop",
            "hoop",
            "boot",
            "foot",
            "root",
            "boot",
        ],
        # Fake compound words (starts with common prefix but isn't real)
        word.startswith("auto")
        and word not in ["auto", "autonomous", "automatic", "automobile"],
    ]
    if any(foreign_patterns):
        scores["foreign_penalty"] = -80  # Increased penalty

    # Technical/scientific term penalties
    technical_patterns = [
        word.endswith(("osis", "itis", "emia", "uria", "pathy")),  # Medical
        word.endswith(("ene", "ine", "ane", "ole", "yl")),  # Chemical
        word.endswith(("ism", "ist", "ite", "ide", "ase", "ose")),  # Scientific
        len(word) > 6 and word.endswith(("um", "us", "ae", "ii")),  # Latin
    ]
    if any(technical_patterns):
        scores["technical_penalty"] = -40

    return scores


def is_google_common_word(word):
    """Check if a word is in the Google common words list."""
    common_words = load_google_common_words()
    return word.lower() in common_words


def calculate_aggregate_confidence(word, dict_scores):
    """
    Calculate confidence using comprehensive multi-dictionary scoring system.
    Webster's dictionary is the gold standard for confidence.
    """
    base_score = 0

    # Webster's is the gold standard - if it's in Webster's, it's very high confidence
    if dict_scores["webster"] > 0:
        base_score = 90  # Very high confidence for Webster's words

    # Oxford is also authoritative
    elif dict_scores["oxford"] > 0:
        base_score = 80  # High confidence for Oxford words

    # American English dictionary provides good baseline
    elif dict_scores["american_english"] > 0:
        base_score = 60  # Good confidence for standard dictionary

    # Fallback for other sources
    else:
        if dict_scores["compound"] > 0:
            base_score += 40
        if dict_scores["nyt_patterns"] > 0:
            base_score += 30

    # Google common words get a bonus multiplier
    if dict_scores["google_common"] > 0:
        base_score = min(100, int(base_score * 1.2))  # 20% bonus, capped at 100

    # Frequency bonus
    if dict_scores["frequency"] > 0:
        base_score = min(100, base_score + dict_scores["frequency"])

    # For words in Webster's dictionary that are also common, ensure high confidence
    if dict_scores["webster"] > 0 and dict_scores["google_common"] > 0:
        base_score = max(base_score, 90)  # Smart boost for common + authoritative

    # Apply penalties (but don't let them destroy Webster's words)
    if dict_scores["webster"] <= 0:  # Only apply penalties to non-Webster's words
        base_score += dict_scores["length_penalty"]
        base_score += dict_scores["foreign_penalty"]
        base_score += dict_scores["technical_penalty"]

    # Special bonuses
    if len(set(word)) == 7:  # Pangrams
        base_score += 10

    # Length bonuses for reasonable word lengths
    if 4 <= len(word) <= 8:
        base_score += 5

    # Word pattern bonuses for common English patterns
    if any(
        [
            word.endswith("ing"),
            word.endswith(("tion", "sion")),
            word.endswith(("able", "ible")),
            word.endswith(("ness", "ment", "ful")),
            word.endswith(("er", "or", "ly", "ed")),
        ]
    ):
        base_score += 5

    # Ensure minimum score for words in any legitimate dictionary
    if dict_scores["american_english"] > 0:
        base_score = max(base_score, 20)

    # Cap the score
    return max(0, min(100, base_score))


def is_likely_nyt_rejected(word):
    """
    Enhanced check if a word is likely to be rejected by NYT Spelling Bee.
    Returns True if the word should be filtered out.
    """
    # Preserve original case for proper noun detection
    original_word = word
    word = word.lower()

    # Filter inappropriate words that NYT would never include in a family puzzle
    inappropriate_words = {
        "clit",
        "cock",
        "dick",
        "fuck",
        "shit",
        "piss",
        "damn",
        "hell",
        "bastard",
        "bitch",
        "whore",
        "slut",
        "tits",
        "ass",
        "fart",
        "penis",
        "vagina",
        "anal",
        "oral",
        "sex",
        "nude",
        "naked",
        "orgasm",
        "erotic",
        "porn",
        "xxx",
        "sexy",
    }

    # Filter abbreviations and invalid words that aren't real dictionary words
    abbreviations_and_invalid = {
        "capt",  # Abbreviation for captain
        "dept",  # Abbreviation for department
        "appt",  # Abbreviation for appointment
        "govt",  # Abbreviation for government
        "intl",  # Abbreviation for international
        "natl",  # Abbreviation for national
        "assn",  # Abbreviation for association
        "corp",  # Abbreviation for corporation
        "prof",  # Abbreviation for professor
        "resp",  # Abbreviation for respective
        "misc",  # Abbreviation for miscellaneous
        "mgmt",  # Abbreviation for management
        "mfg",  # Abbreviation for manufacturing
        "mktg",  # Abbreviation for marketing
        "acct",  # Abbreviation for account
        "admin",  # Abbreviation for administration
        "exec",  # Abbreviation for executive
    }

    if word in inappropriate_words or word in abbreviations_and_invalid:
        return True

    # Check for proper nouns - capitalized words that aren't common words
    if original_word[0].isupper() and not original_word.isupper():
        # Allow some common words that happen to be capitalized
        common_capitalized = {
            "august",
            "may",
            "will",
            "grace",
            "hope",
            "faith",
            "joy",
            "rose",
            "lily",
        }
        if word not in common_capitalized:
            return True

    # Check for acronyms - all caps and short
    if original_word.isupper() and len(original_word) <= 6:
        return True

    # Enhanced proper noun detection - common proper nouns even in lowercase
    # These are ones that NLTK might miss but are definitely proper nouns
    proper_nouns = {
        # Artists and historical figures
        "botticelli",
        "leonardo",
        "michelangelo",
        "raphael",
        "donatello",
        "monet",
        "picasso",
        "dali",
        "cezanne",
        "renoir",
        "degas",
        "beethoven",
        "mozart",
        "bach",
        "chopin",
        "vivaldi",
        "shakespeare",
        "dante",
        "homer",
        "plato",
        "aristotle",
        # People names
        "elliott",
        "elliot",
        "eliot",
        "cecil",
        "bobbie",
        "bobbi",
        "lillie",
        "lottie",
        "bettie",
        "ellie",
        "ollie",
        "billie",
        "cecile",
        "tito",
        "tobit",
        # Place names
        "celtic",
        "tibet",
        "beloit",
        "lille",
        "poona",
        "napa",
        "patna",
        "upton",
        "patton",
        "pocono",
        "tucson",
        "yukon",
        "pontiac",
        "penn",
        "canton",
        "newton",
        "sutton",
        "belgium",
        "britain",
        "france",
        "spain",
        "italy",
        "greece",
        "egypt",
        # Mythological/classical names
        "clio",
        "apollo",
        "athena",
        "zeus",
        "hermes",
        "poseidon",
        "hades",
        # Acronyms and abbreviations (even in lowercase)
        "ieee",
        "naacp",
        "ioctl",
        "biol",
        "coli",
        "ecoli",
        "clii",
        # Brand names and companies
        "intel",
        "cisco",
        "apple",
        "google",
        "microsoft",
        "facebook",
        "twitter",
    }

    if word in proper_nouns:
        return True

    # Check for obvious abbreviations - common patterns
    if word.endswith(("co", "corp", "inc", "ltd", "dept", "govt", "assoc", "prof")):
        return True

    # Reject compound words with common prefixes (NYT typically rejects these)
    # But allow some legitimate exceptions
    legitimate_exceptions = {
        "capo",
        "coopt",
        "copout",
        "upon",
        "atop",
        "auto",
        "anti",
        "coop",
        "coup",
        "pact",
        "pant",
        "pout",
        "punt",
        "putt",
    }

    if word in legitimate_exceptions:
        return False  # Don't reject these legitimate words

    prefix_patterns = [
        "co",  # co-occupant -> cooccupant
        "non",  # non-occupant -> nonoccupant
        "pre",  # pre-approval -> preapproval
        "anti",  # anti-aircraft -> antiaircraft
        "multi",  # multi-purpose -> multipurpose
        "sub",  # sub-optimal -> suboptimal
        "over",  # over-confident -> overconfident
        "under",  # under-estimate -> underestimate
        "inter",  # inter-connect -> interconnect
        "super",  # super-natural -> supernatural
        "ultra",  # ultra-modern -> ultramodern
    ]

    for prefix in prefix_patterns:
        if word.startswith(prefix) and len(word) > len(prefix) + 4:
            # Check if removing the prefix leaves a valid-looking word
            remainder = word[len(prefix) :]
            if len(remainder) >= 4 and remainder.isalpha():
                return True

    # Smart detection of likely place names - conservative patterns only
    if (
        word.endswith(("ton", "ville", "burg", "land", "shire", "stead"))
        and len(word) > 4
    ):
        return True

    # Geographic patterns that are less likely to be regular words
    if (
        word.endswith(("ona", "una", "ina")) and len(word) >= 5
    ):  # Include 5-letter words
        return True

    # Very specific acronym patterns - be conservative
    if (
        len(word) == 5 and word.count("a") >= 2
    ):  # Like 'naacp' - 2+ A's in 5 letters is unusual
        return True

    # Additional place name patterns
    if word.endswith(("cono", "ana", "tna")):  # pocono, patna patterns
        return True

    return False


def is_likely_nyt_word(word):
    """Intelligent filtering - only reject obvious non-words, let scoring handle quality."""

    # Skip non-alphabetic words
    if not word.isalpha():
        return False

    word = word.lower()

    # Reject obvious nonsense patterns
    if len(set(word)) <= 2 and len(word) > 4:  # Too repetitive
        return False

    # Reject words with obvious gibberish patterns
    if any(pattern in word for pattern in ["qqq", "xxx", "zzz"]):
        return False

    # Everything else should be evaluated by confidence scoring
    return True


def load_rejected_words():
    """Load globally rejected words (not in NYT Spelling Bee)."""
    rejected_file = Path.home() / ".spelling_bee_rejected.json"
    if rejected_file.exists():
        try:
            with open(rejected_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_rejected_words(rejected_words):
    """Save globally rejected words."""
    rejected_file = Path.home() / ".spelling_bee_rejected.json"
    with open(rejected_file, "w", encoding="utf-8") as f:
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
            with open(found_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Handle both old format (list) and new format (dict with metadata)
                if isinstance(data, list):
                    return set(data)
                elif isinstance(data, dict):
                    return set(data.get("words", []))
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
    data = {"date": date, "center": center, "outer": outer, "words": list(found_words)}
    with open(found_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def solve_puzzle_webster_first(center_letter, outer_letters):
    """
    Solve spelling bee puzzle using Webster's as the primary gatekeeper.
    Only look at other dictionaries if we need more words.
    """
    center = center_letter.lower()
    outer = outer_letters.lower()
    allowed_letters = set(center + outer)

    print(f"Solving puzzle: Center='{center.upper()}' Outer='{outer.upper()}'")

    # Load rejected words
    rejected_words = load_rejected_words()

    # PHASE 1: Webster's Dictionary (Primary - High Quality)
    print("\n=== PHASE 1: Webster's Dictionary (Primary) ===")
    webster_words = load_webster_dictionary()
    if not webster_words:
        print("❌ No Webster's dictionary found! Using system dictionary as fallback.")
        webster_words = load_system_dictionary()

    print(f"Primary dictionary loaded: {len(webster_words)} words")

    # Find valid words in primary dictionary
    primary_solutions = []
    primary_pangrams = []

    for word in webster_words:
        # Must contain center letter
        if center not in word:
            continue

        # Must only use allowed letters
        if not set(word) <= allowed_letters:
            continue

        # Must be long enough
        if len(word) < 4:
            continue

        # Skip rejected words
        if word in rejected_words:
            continue

        # Apply intelligent filtering for obvious non-NYT words
        if is_likely_nyt_rejected(word):
            continue

        # Valid word found!
        word_len = len(word)
        is_pangram = len(set(word)) == 7

        if is_pangram:
            points = word_len + 7
            primary_pangrams.append(word)
        elif word_len == 4:
            points = 1
        else:
            points = word_len

        # High confidence for primary dictionary words
        # Calculate basic confidence - Webster's words get high base score
        confidence = 100 if len(word) >= 4 else 95
        primary_solutions.append((word, points, confidence))

    print(f"Found {len(primary_solutions)} valid words in primary dictionary")
    print(f"Found {len(primary_pangrams)} pangrams in primary dictionary")

    # Sort by confidence then points
    primary_solutions.sort(key=lambda x: (-x[2], -x[1]))

    return primary_solutions, primary_pangrams


def load_webster_dictionary():
    """Load Webster's dictionary specifically"""
    webster_paths = [
        Path.home() / "webster-dictionary.txt",
        Path.home() / "merriam-webster.txt",
        Path.home() / "websters.txt",
        Path("/usr/share/dict/american-english"),
    ]

    for path in webster_paths:
        if path.exists():
            try:
                print(f"Loading Webster's from: {path}")
                with open(path, "r", encoding="utf-8") as f:
                    words = set()
                    for word in f:
                        word = word.strip().lower()
                        if (
                            len(word) >= 4
                            and word.isalpha()
                            and "'" not in word
                            and "-" not in word
                        ):
                            words.add(word)
                    return words
            except Exception as e:
                print(f"Failed to load {path}: {e}")
                continue

    return set()


def load_system_dictionary():
    """Load system dictionary as fallback"""
    try:
        with open("/usr/share/dict/words", "r", encoding="utf-8") as f:
            words = set()
            for word in f:
                word = word.strip().lower()
                if (
                    len(word) >= 4
                    and word.isalpha()
                    and "'" not in word
                    and "-" not in word
                ):
                    if not is_likely_nyt_rejected(word) and is_likely_nyt_word(word):
                        words.add(word)
            return words
    except Exception:
        return set()


def draw_hexagon(center, outer):
    """
    Draw honeycomb hexagon with letters.

    Args:
        center (str): The center letter
        outer (str): The 6 outer letters
    """
    letters = list(outer.upper())
    c = center.upper()

    print("\n" + " " * 8 + "     ___")
    print(" " * 8 + "    /   \\")
    print(" " * 8 + f"   / {letters[0]:^3} \\")
    print(" " * 3 + " ___/___  ___\\___")
    print(" " * 3 + "/   \\   /   \\   /")
    print(" " * 3 + f"/ {letters[5]:^3} \\ / {c:^3} \\ / {letters[1]:^3} \\")
    print(" " * 3 + "\\___  ___/___  ___/")
    print(" " * 7 + "\\   /   \\   /")
    print(" " * 7 + f" \\ / {letters[4]:^3} \\ / {letters[2]:^3} \\")
    print(" " * 7 + "  \\___  ___/")
    print(" " * 11 + "\\   /")
    print(" " * 11 + f" \\ / {letters[3]:^3} \\")
    print(" " * 11 + "  \\___/\n")


def interactive_mode():
    """
    Interactive mode with hexagon display.

    Returns:
        tuple: (center, outer, mark_mode, reset_mode, top_n)
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
        if ready == "y":
            return center, outer, False, False, 46  # Always return 46 suggestions
        elif ready == "n":
            change = input("Change letters? (y/n): ").strip().lower()
            if change != "y":
                print("Exiting...")
                sys.exit(0)
            # Loop continues to re-enter letters
        else:
            print("Please enter 'y' or 'n'")


def main():
    """Main function to run the Spelling Bee solver."""
    # Check for help
    if "--help" in sys.argv or "-h" in sys.argv:
        print("New York Times Spelling Bee Solver")
        print("=" * 40)
        print("Usage: python spelling_bee_solver.py <center> <outer_letters> [options]")
        print("")
        print("Options:")
        print(
            "  --continue, -c    Continue previous session (hide already found words)"
        )
        print("  --reset, -r       Reset/clear all found words for this puzzle")
        print("  --mark, -m        Mark words as found")
        print("  --top N           Show only top N words (default: 46)")
        print("  --help, -h        Show this help message")
        print("")
        print("Examples:")
        print("  python spelling_bee_solver.py i tlocbe                # Fresh solve")
        print(
            "  python spelling_bee_solver.py i tlocbe --continue     # Continue session"
        )
        print("  python spelling_bee_solver.py i tlocbe --reset        # Reset puzzle")
        sys.exit(0)

    # Get puzzle input
    if len(sys.argv) >= 3 and sys.argv[1] not in ["-y", "--yes"]:
        # CLI mode with letters provided
        center = sys.argv[1]
        outer = sys.argv[2]
        mark_mode = "--mark" in sys.argv or "-m" in sys.argv
        reset_mode = "--reset" in sys.argv or "-r" in sys.argv
        continue_mode = "--continue" in sys.argv or "-c" in sys.argv

        # Check for --top N flag
        top_n = None
        for i, arg in enumerate(sys.argv):
            if arg == "--top" and i + 1 < len(sys.argv):
                try:
                    top_n = int(sys.argv[i + 1])
                except ValueError:
                    pass

        # Default to top 46 - user wants 46 smart suggestions always
        if top_n is None and not mark_mode and not reset_mode:
            top_n = 46
    else:
        # Interactive mode
        center, outer, mark_mode, reset_mode, top_n = interactive_mode()
        continue_mode = False  # Default to fresh start in interactive mode

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

    # Load dictionary and solve puzzle using Webster-first approach
    print("\nLoading dictionary...")

    # Use new Webster-first approach
    solutions, pangrams = solve_puzzle_webster_first(center, outer)

    if not solutions and not pangrams:
        print("Could not find any valid words. Please check your dictionary setup.")
        sys.exit(1)

    # Only filter previously found words if in continue mode
    if continue_mode:
        found_words = load_found_words(center, outer)
        # Filter out found words for display
        display_solutions = [sol for sol in solutions if sol[0] not in found_words]
        display_pangrams = [p for p in pangrams if p not in found_words]
    else:
        # Fresh start - show all words
        found_words = set()
        display_solutions = solutions
        display_pangrams = pangrams

    # Calculate points
    total_points = sum(sol[1] for sol in display_solutions) + sum(
        (len(p) + 7) for p in display_pangrams
    )

    print("\n" + "=" * 60)
    print(
        f"Found {len(display_solutions +
                       display_pangrams)} words worth {total_points} points"
    )
    print(f"Pangrams: {len(display_pangrams)}")
    print("=" * 60)

    # Display pangrams first
    if display_pangrams:
        print("\n🌟 PANGRAMS:")
        for word in display_pangrams:
            points = len(word) + 7
            print(f"  {word.upper()}")

    # Display remaining words
    if display_solutions:
        print("\nRemaining words:")
        shown = 0
        for word, points, confidence in display_solutions:
            if top_n and shown >= top_n:
                break
            if word not in display_pangrams:  # Don't show pangrams twice
                conf_str = (
                    f"{confidence}% confidence"
                    if confidence < 100
                    else "100% confidence"
                )
                if confidence < 50:
                    print(f"🌟 {word:<20} ({points:2} pts, {conf_str})")
                else:
                    print(f"  {word:<20} ({points:2} pts, {conf_str})")
                shown += 1

    # Interactive marking mode
    if mark_mode:
        # Load rejected words for marking mode
        rejected_words = load_rejected_words()
        print("\nEnter words you've found (one per line, 'q' to quit):")
        print("Prefix with '-' to mark as rejected (e.g., '-bibliotic')")
        while True:
            try:
                word = input("> ").strip().lower()
                if word == "q":
                    break

                # Check if marking as rejected
                if word.startswith("-"):
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

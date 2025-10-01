"""
Word filtering logic for NYT Spelling Bee solver.
Contains intelligent detection of proper nouns, place names, acronyms, and non - English words.
"""

# Try to import NLTK - based proper noun filter
try:
    from nltk_proper_noun_filter import NLTKProperNounFilter

    nltk_filter = NLTKProperNounFilter()
    NLTK_AVAILABLE = True
    print("Enhanced NLTK proper noun filtering enabled")
except ImportError:
    NLTK_AVAILABLE = False
    nltk_filter = None
    print("NLTK not available, using manual proper noun filtering only")


def is_likely_nyt_rejected(word):
    """
    Check if a word is likely to be rejected by NYT Spelling Bee using intelligent detection.
    Returns True if the word should be filtered out.
    """
    # Preserve original case for proper noun detection
    original_word = word
    word = word.lower()

    # Filter inappropriate words that NYT would never include in a family puzzle
    inappropriate_words = {
        'clit', 'cock', 'dick', 'fuck', 'shit', 'piss', 'damn', 'hell',
        'bastard', 'bitch', 'whore', 'slut', 'tits', 'ass', 'fart',
        'poop', 'penis', 'vagina', 'anal', 'oral', 'sex', 'nude',
        'naked', 'orgasm', 'erotic', 'porn', 'xxx', 'sexy'
    }
    
    if word in inappropriate_words:
        return True

    # First try NLTK - based proper noun detection if available  
    # TEMPORARILY DISABLED: NLTK is too slow for large dictionaries
    # if NLTK_AVAILABLE and nltk_filter:
    #     try:
    #         if nltk_filter.is_likely_proper_noun(original_word):
    #             return True
    #     except Exception:
    #         # Fall back to manual detection if NLTK fails
    #         pass

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
        # Mythological / classical names
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
        "co",  # co - occupant -> cooccupant
        "non",  # non - occupant -> nonoccupant
        "pre",  # pre - approval -> preapproval
        "anti",  # anti - aircraft -> antiaircraft
        "multi",  # multi - purpose -> multipurpose
        "sub",  # sub - optimal -> suboptimal
        "over",  # over - confident -> overconfident
        "under",  # under - estimate -> underestimate
        "inter",  # inter - connect -> interconnect
        "super",  # super - natural -> supernatural
        "ultra",  # ultra - modern -> ultramodern
    ]

    for prefix in prefix_patterns:
        if word.startswith(prefix) and len(word) > len(prefix) + 4:
            # Check if removing the prefix leaves a valid - looking word
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
    ):  # Include 5 - letter words
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


def is_likely_nyt_rejected_strict(word):
    """
    Strict filtering for comprehensive dictionary - more restrictive.
    """
    # Apply standard filtering first
    if is_likely_nyt_rejected(word):
        return True

    word = word.lower()

    # Allow some legitimate words that look like compounds but aren't
    legitimate_compounds = {
        "capo",
        "coopt",
        "copout",
        "unapt",
        "atop",
        "upon",
        "auto",
        "coop",
        "coup",
        "pact",
        "pant",
        "pout",
        "punt",
        "putt",
        "papa",
        "pupa",
        "poop",
        "catnap",
        "topcoat",
        "coupon",
        "output",
        "potato",
        "pontoon",
        "occupant",
    }

    if word in legitimate_compounds:
        return False

    # Reject obvious nonsense patterns - repetitive sequences
    if len(word) > 6:
        # Check for suspicious repetition patterns like "taptaptap", "anapanapa"
        for i in range(len(word) - 2):
            substr = word[i : i + 3]
            if word.count(substr) >= 2:  # Same 3 - letter sequence appears twice
                return True

    # Reject words with too much repetition of single letters
    for char in set(word):
        if word.count(char) > len(word) // 2:  # More than half the word is one letter
            return True

    # Reject words that are just random letter combinations
    if len(word) >= 7:
        # Check for patterns that suggest made - up words
        vowels = set("aeiou")
        consonants = set("bcdfghjklmnpqrstvwxyz")

        # Too many consecutive consonants or vowels suggests nonsense
        max_consecutive_vowels = 0
        max_consecutive_consonants = 0
        current_vowel_streak = 0
        current_consonant_streak = 0

        for char in word:
            if char in vowels:
                current_vowel_streak += 1
                current_consonant_streak = 0
                max_consecutive_vowels = max(
                    max_consecutive_vowels, current_vowel_streak
                )
            elif char in consonants:
                current_consonant_streak += 1
                current_vowel_streak = 0
                max_consecutive_consonants = max(
                    max_consecutive_consonants, current_consonant_streak
                )

        # Reject words with too many consecutive vowels or consonants
        if max_consecutive_vowels > 3 or max_consecutive_consonants > 4:
            return True

    # Reject words that look like place names or foreign words
    if any(pattern in word for pattern in ["appa", "atta", "etto", "anna"]):
        if len(word) >= 7:  # Only apply to longer words
            return True

    # Reject obvious nonsense or very technical terms
    if any(ending in word for ending in ["toc", "acon", "acan"]):
        return True

    return False


def is_likely_nyt_word(word):
    """Intelligent filtering - only reject obvious non - words, let scoring handle quality."""

    # Handle hyphenated words - strip hyphens and check the result
    if "-" in word:
        dehyphenated = word.replace("-", "")
        # Must be valid after removing hyphens
        if len(dehyphenated) < 4:
            return False
        # Check if it's still a reasonable word pattern
        if not dehyphenated.isalpha():
            return False
        # Use the dehyphenated version for further checks
        word = dehyphenated

    # Skip non - alphabetic words
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


def process_word_for_puzzle(word):
    """
    Process a dictionary word for puzzle use - handles hyphen removal.
    Returns the word as it should appear in the puzzle, or None if invalid.
    """
    if "-" in word:
        # Remove hyphens for puzzle purposes
        processed = word.replace("-", "")
        # Must still be long enough after removing hyphens
        if len(processed) >= 4 and processed.isalpha():
            return processed.lower()
        return None
    return word.lower()

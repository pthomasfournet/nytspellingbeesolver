"""
Word filtering logic for NYT Spelling Bee solver.
Contains intelligent detection of proper nouns, place names, acronyms, and non - English words.

DEPRECATED: This module is deprecated. Use core.NYTRejectionFilter instead.
"""

import warnings


def is_likely_nyt_rejected(word):
    """
    Check if a word is likely to be rejected by NYT Spelling Bee using intelligent detection.
    Returns True if the word should be filtered out.

    DEPRECATED: Use core.NYTRejectionFilter.should_reject() instead.
    """
    warnings.warn(
        "is_likely_nyt_rejected() is deprecated. Use core.NYTRejectionFilter.should_reject() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    # Preserve original case for proper noun detection
    original_word = word
    word_lower = word.lower()

    # Basic checks
    if len(word) < 4:
        return True  # Too short

    # Check for obvious proper nouns - if first letter is capitalized
    if original_word[0].isupper() and len(original_word) > 4:
        return True

    # Known abbreviations and patterns NYT typically rejects
    abbreviations = {
        "capt",
        "dept",
        "govt",
        "corp",
        "assn",
        "natl",
        "intl",
        "prof",
        "repr",
        "mgmt",
        "admin",
        "info",
        "tech",
        "spec",
        "univ",
        "inst",
        "assoc",
        "incl",
        "misc",
        "temp",
        "approx",
        "est",
        "max",
        "min",
        "avg",
        "std",
    }

    if word_lower in abbreviations:
        return True

    # Words ending in common abbreviation patterns
    # Whitelist common compound words to avoid false positives
    compound_word_whitelist = {
        "engagement", "arrangement", "management", "assignment",
        "government", "department", "assessment"
    }
    
    if word_lower not in compound_word_whitelist:
        abbrev_endings = ["mgmt", "corp", "assn", "dept", "govt", "natl", "intl"]
        if any(word_lower.endswith(ending) for ending in abbrev_endings):
            return True

    # Common proper noun suffixes
    # Whitelist common compound words that happen to end with these suffixes
    geographic_whitelist = {
        "woodland", "understand", "backfield", "outfield", "midfield",
        "airfield", "minefield", "battlefield", "misunderstand"
    }
    
    if word_lower not in geographic_whitelist:
        proper_suffixes = [
            "burg",
            "ville",
            "town",
            "shire",
            "ford",
            "field",
            "wood",
            "land",
        ]
        if any(word_lower.endswith(suffix)
               for suffix in proper_suffixes) and len(word) > 6:
            return True

    # Words that are likely brand names (all caps in original, or unusual
    # capitalization)
    if len(original_word) > 1 and original_word.isupper():
        return True

    # Check for non-English patterns
    # Words with 'x' followed by consonants (often Latin/Greek)
    if "x" in word_lower and len(word) > 5:
        x_idx = word_lower.find("x")
        if x_idx < len(word) - \
                1 and word_lower[x_idx + 1] in "bcdfghjklmnpqrstvwyz":
            return True

    # Words ending in common Latin suffixes
    # Whitelist common English words with these endings
    latin_suffix_whitelist = {
        # Common -ous words
        "famous", "joyous", "nervous", "anxious", "curious", "generous",
        "dangerous", "zealous", "envious", "glorious", "rigorous", "vigorous",
        # Common -ane words
        "plane", "crane", "humane", "insane", "propane", "membrane", "mundane",
        # Common -ine words
        "fine", "line", "mine", "pine", "wine", "dine", "vine", "shine",
        "marine", "machine", "routine", "doctrine", "medicine", "genuine",
        # Common -ene words
        "scene", "serene", "obscene",
        # Common -ium words (keep scientific ones out)
        "premium", "stadium"
    }
    
    if word_lower not in latin_suffix_whitelist:
        latin_endings = ["ium", "ius", "ous", "eum", "ine", "ene", "ane"]
        if any(word_lower.endswith(ending)
               for ending in latin_endings) and len(word) > 6:
            return True

    # Scientific/technical words (often have specific patterns)
    if (
        word_lower.endswith("ase")
        or word_lower.endswith("ose")
        or word_lower.endswith("ide")
    ):
        return True

    # Check for likely foreign words
    # Double letters uncommon in English (removed "oo" - it's common in English)
    # "aa", "ii", "uu" are truly rare in English words
    uncommon_doubles = ["aa", "ii", "uu"]
    if any(double in word_lower for double in uncommon_doubles):
        return True
    
    # Separate check for unusual "oo" patterns (but not common words)
    # Triple-o or starting with oo are suspicious
    if "ooo" in word_lower or (word_lower.startswith("oo") and len(word) > 4):
        return True

    # Words with 'q' not followed by 'u'
    if "q" in word_lower:
        q_indices = [i for i, char in enumerate(word_lower) if char == "q"]
        for q_idx in q_indices:
            if q_idx == len(word_lower) - 1 or word_lower[q_idx + 1] != "u":
                return True

    return False


def filter_words(words, letters, required_letter):
    """
    Filter a list of words based on Spelling Bee rules and intelligent rejection detection.

    Args:
        words: List of words to filter
        letters: String of available letters
        required_letter: Letter that must be present in all words

    Returns:
        List of filtered words that should be valid for the puzzle

    DEPRECATED: Use core.CandidateGenerator.generate_candidates() instead.
    """
    warnings.warn(
        "filter_words() is deprecated. Use core.CandidateGenerator.generate_candidates() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    filtered = []
    letters_set = set(letters.lower())
    required = required_letter.lower()

    for word in words:
        word_lower = word.lower().strip()

        # Basic Spelling Bee validation
        if len(word_lower) < 4:
            continue

        if required not in word_lower:
            continue

        # Check if word uses only available letters
        if not set(word_lower).issubset(letters_set):
            continue

        # Apply intelligent rejection filtering
        if is_likely_nyt_rejected(word):
            continue

        filtered.append(word_lower)

    return filtered


def get_word_confidence(word, google_common_words=None):
    """
    Calculate a confidence score for how likely a word is to be accepted.

    Args:
        word: The word to score
        google_common_words: Set of common words (optional)

    Returns:
        Float confidence score (0.0 to 1.0)

    DEPRECATED: Use core.ConfidenceScorer.calculate_confidence() instead.
    """
    warnings.warn(
        "get_word_confidence() is deprecated. Use core.ConfidenceScorer.calculate_confidence() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    confidence = 0.5  # Base confidence

    # Length bonus (longer words often more valuable)
    if len(word) >= 6:
        confidence += 0.2
    if len(word) >= 8:
        confidence += 0.1

    # Common word bonus
    if google_common_words and word.lower() in google_common_words:
        confidence += 0.3

    # Penalize likely rejected words
    if is_likely_nyt_rejected(word):
        confidence -= 0.4

    # Bonus for words that look "normal"
    if word.islower() and word.isalpha():
        confidence += 0.1

    return max(0.0, min(1.0, confidence))


# Legacy support functions
def is_proper_noun(word):
    """Legacy function - now handled by is_likely_nyt_rejected.

    DEPRECATED: Use core.NYTRejectionFilter.is_proper_noun() instead.
    """
    warnings.warn(
        "is_proper_noun() is deprecated. Use core.NYTRejectionFilter.should_reject() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return is_likely_nyt_rejected(word)


def filter_inappropriate_words(words):
    """Legacy function for filtering inappropriate content.

    DEPRECATED: Use core.NYTRejectionFilter instead.
    """
    warnings.warn(
        "filter_inappropriate_words() is deprecated. Use core.NYTRejectionFilter instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return [word for word in words if not is_likely_nyt_rejected(word)]

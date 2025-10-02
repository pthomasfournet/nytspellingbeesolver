"""
NYT Spelling Bee rejection filter.

Detects words that NYT Spelling Bee typically rejects:
- Proper nouns (people, places)
- Foreign words
- Archaic/obsolete words (flagged but not rejected - low confidence instead)
- Abbreviations
- Technical/scientific terms
"""

from typing import Optional
import logging

from ..constants import MIN_WORD_LENGTH


class NYTRejectionFilter:
    """Filter for detecting words likely rejected by NYT Spelling Bee."""

    def __init__(self):
        """Initialize the rejection filter with known proper nouns and foreign words."""
        self.logger = logging.getLogger(__name__)

        # Known proper nouns (people names, places) that appear in dictionaries lowercase
        # This catches cases like "lloyd" which is a surname
        self.known_proper_nouns = {
            # Common surnames that appear in dictionaries
            "lloyd", "louis", "martin", "mason", "grant", "banks", "chase",
            "ford", "dean", "frank", "jack", "miles", "scott", "lane",
            # Place names
            "loca", "lima", "java", "cairo", "boston", "austin", "madison",
            "paris", "berlin", "london", "dublin", "orlando", "eugene",
            # Common first names
            "john", "mary", "anna", "emma", "noah", "liam", "sophia",
        }

        # Known foreign words (non-English) that should be rejected
        self.known_foreign_words = {
            # Spanish
            "loca", "loco", "casa", "mesa", "taco", "salsa",
            # French
            "avec", "sans", "tres", "mais", "pour",
            # Italian
            "ciao", "bella", "pasta", "pizza",
            # German
            "uber", "auto",
        }

        # Archaic/obsolete words (low confidence, not rejected)
        # These get flagged for low confidence scoring instead of outright rejection
        self.archaic_words = {
            "hath", "doth", "thee", "thou", "thy", "thine", "ye",
            "whilst", "whence", "whither", "hither", "thither",
            "betwixt", "amongst", "unto", "anon",
        }

        # Abbreviations
        self.abbreviations = {
            "capt", "dept", "govt", "corp", "assn", "natl", "intl",
            "prof", "repr", "mgmt", "admin", "info", "tech", "spec",
            "univ", "inst", "assoc", "incl", "misc", "temp", "approx",
            "est", "max", "min", "avg", "std",
        }

    def is_proper_noun(self, word: str) -> bool:
        """Check if word is a proper noun.

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word is a known proper noun
        """
        word_lower = word.lower().strip()

        # Check known proper nouns list
        if word_lower in self.known_proper_nouns:
            return True

        # Pattern-based detection
        # Words ending in common place suffixes (longer words only)
        if len(word_lower) > 6:
            place_suffixes = ["burg", "ville", "town", "shire", "ford", "field"]
            if any(word_lower.endswith(suffix) for suffix in place_suffixes):
                # Whitelist common words
                if word_lower not in {"woodland", "understand", "battlefield"}:
                    return True

        return False

    def is_foreign_word(self, word: str) -> bool:
        """Check if word is a foreign (non-English) word.

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word is likely foreign
        """
        word_lower = word.lower().strip()

        # Check known foreign words
        if word_lower in self.known_foreign_words:
            return True

        # Pattern-based foreign word detection
        # Double letters rare in English
        uncommon_doubles = ["aa", "ii", "uu"]
        if any(double in word_lower for double in uncommon_doubles):
            return True

        # Words with 'q' not followed by 'u' (Arabic, etc.)
        if "q" in word_lower:
            q_indices = [i for i, char in enumerate(word_lower) if char == "q"]
            for q_idx in q_indices:
                if q_idx == len(word_lower) - 1 or word_lower[q_idx + 1] != "u":
                    return True

        return False

    def is_archaic(self, word: str) -> bool:
        """Check if word is archaic/obsolete.

        Note: Archaic words are NOT rejected, just flagged for low confidence.

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word is archaic
        """
        word_lower = word.lower().strip()
        return word_lower in self.archaic_words

    def is_abbreviation(self, word: str) -> bool:
        """Check if word is an abbreviation.

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word is an abbreviation
        """
        word_lower = word.lower().strip()

        # Direct match
        if word_lower in self.abbreviations:
            return True

        # Words ending in abbreviation patterns
        compound_whitelist = {"engagement", "arrangement", "management", "government"}
        if word_lower not in compound_whitelist:
            abbrev_endings = ["mgmt", "corp", "assn", "dept"]
            if any(word_lower.endswith(ending) for ending in abbrev_endings):
                return True

        return False

    def is_technical_term(self, word: str) -> bool:
        """Check if word is a technical/scientific term.

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word is likely technical
        """
        word_lower = word.lower().strip()

        # Scientific suffixes (enzyme names, chemicals)
        if word_lower.endswith("ase") or word_lower.endswith("ose"):
            return True

        if word_lower.endswith("ide") and len(word_lower) > 5:
            return True

        # Latin scientific endings (but whitelist common words)
        if len(word_lower) > 6:
            latin_whitelist = {"famous", "nervous", "curious", "plane", "humane"}
            if word_lower not in latin_whitelist:
                latin_endings = ["ium", "ius", "ous", "eum"]
                if any(word_lower.endswith(ending) for ending in latin_endings):
                    return True

        return False

    def should_reject(self, word: str) -> bool:
        """Check if word should be rejected (NYT likely won't accept it).

        This is the main entry point for filtering.

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word should be rejected
        """
        word_lower = word.lower().strip()

        # Length check
        if len(word_lower) < MIN_WORD_LENGTH:
            return True

        # Check all rejection criteria
        if self.is_proper_noun(word_lower):
            self.logger.debug(f"Rejecting '{word_lower}': proper noun")
            return True

        if self.is_foreign_word(word_lower):
            self.logger.debug(f"Rejecting '{word_lower}': foreign word")
            return True

        if self.is_abbreviation(word_lower):
            self.logger.debug(f"Rejecting '{word_lower}': abbreviation")
            return True

        if self.is_technical_term(word_lower):
            self.logger.debug(f"Rejecting '{word_lower}': technical term")
            return True

        # Note: Archaic words are NOT rejected here
        # They're flagged by is_archaic() and scored with low confidence instead

        return False

    def get_rejection_reason(self, word: str) -> Optional[str]:
        """Get the reason why a word would be rejected.

        Args:
            word: Word to check

        Returns:
            String describing rejection reason, or None if not rejected
        """
        word_lower = word.lower().strip()

        if len(word_lower) < MIN_WORD_LENGTH:
            return "too_short"

        if self.is_proper_noun(word_lower):
            return "proper_noun"

        if self.is_foreign_word(word_lower):
            return "foreign_word"

        if self.is_abbreviation(word_lower):
            return "abbreviation"

        if self.is_technical_term(word_lower):
            return "technical_term"

        if self.is_archaic(word_lower):
            return "archaic_word"  # Note: not a rejection, just a flag

        return None

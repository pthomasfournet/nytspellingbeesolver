"""
NYT Spelling Bee rejection filter.

Detects words that NYT Spelling Bee typically rejects:
- Proper nouns (people, places)
- Foreign words
- Archaic/obsolete words (flagged but not rejected - low confidence instead)
- Abbreviations
- Technical/scientific terms
- Blacklisted words (data-driven from 2,615 historical puzzles)
- Wiktionary metadata (Layer 4: comprehensive automated detection)
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional

from ..constants import MIN_WORD_LENGTH
from .wiktionary_metadata import load_wiktionary_metadata


class NYTRejectionFilter:
    """Filter for detecting words likely rejected by NYT Spelling Bee."""

    # Rejection thresholds for blacklist (data-driven from 2,615 puzzles)
    INSTANT_REJECT_THRESHOLD = 3   # Words rejected 3+ times = instant reject (5,321 words)
    LOW_CONFIDENCE_THRESHOLD = 2   # Words rejected 2+ times = suspicious (5,892 words)

    def __init__(self, nyt_rejection_blacklist: Optional[Dict[str, int]] = None,
                 enable_wiktionary: bool = True):
        """Initialize the rejection filter with known proper nouns and foreign words.

        Args:
            nyt_rejection_blacklist: Dict of {word: rejection_count} from historical puzzles
            enable_wiktionary: Enable Layer 4 Wiktionary metadata filtering
        """
        self.logger = logging.getLogger(__name__)
        self.nyt_rejection_blacklist = nyt_rejection_blacklist or {}

        # Load NYT rejection blacklist if not provided
        if not self.nyt_rejection_blacklist:
            self._load_nyt_blacklist()

        # Load Wiktionary metadata (Layer 4)
        self.wiktionary = None
        if enable_wiktionary:
            self.wiktionary = load_wiktionary_metadata()
            if not self.wiktionary.loaded:
                self.logger.debug("Wiktionary Layer 4 disabled (metadata not found)")

        # Known proper nouns (people names, places) that appear in dictionaries lowercase
        # Comprehensive list + blacklist (threshold=10) for layered filtering
        self.known_proper_nouns = {
            # Common surnames
            "lloyd", "louis", "martin", "mason", "grant", "banks", "chase",
            "ford", "dean", "frank", "jack", "miles", "scott", "lane",
            "brown", "smith", "johnson", "williams", "jones", "garcia",

            # Countries & Major Regions
            "tanzania", "brazil", "france", "spain", "russia", "japan",
            "china", "india", "egypt", "peru", "chile", "cuba", "haiti",
            "kenya", "libya", "mali", "niger", "somalia", "uganda", "ghana",
            "iraq", "iran", "syria", "yemen", "oman", "jordan", "qatar",
            "nepal", "tibet", "burma", "laos", "vietnam", "korea",
            "panama", "honduras", "nicaragua", "bolivia", "uruguay", "paraguay",
            "algeria", "tunisia", "morocco", "sudan", "zambia", "zimbabwe",
            "angola", "namibia", "botswana", "malawi", "rwanda", "senegal",

            # US States & Territories
            "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
            "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
            "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana",
            "maine", "maryland", "massachusetts", "michigan", "minnesota",
            "mississippi", "missouri", "montana", "nebraska", "nevada",
            "ohio", "oklahoma", "oregon", "pennsylvania", "tennessee", "texas",
            "utah", "vermont", "virginia", "washington", "wisconsin", "wyoming",
            "guam", "samoa", "dakota", "carolina",

            # Major Cities
            "atlanta", "boston", "chicago", "dallas", "denver", "detroit",
            "houston", "miami", "phoenix", "seattle", "portland", "austin",
            "memphis", "nashville", "charlotte", "tampa", "orlando",
            "baltimore", "philadelphia", "pittsburgh", "cleveland", "cincinnati",
            "milwaukee", "minneapolis", "omaha", "wichita", "tulsa", "oakland",
            "mesa", "raleigh", "durham", "lexington", "toledo", "buffalo",

            # World Cities
            "london", "paris", "berlin", "madrid", "rome", "athens", "vienna",
            "prague", "warsaw", "budapest", "bucharest", "sofia", "zagreb",
            "belgrade", "dublin", "edinburgh", "glasgow", "manchester",
            "amsterdam", "brussels", "copenhagen", "stockholm", "oslo", "helsinki",
            "moscow", "kiev", "minsk", "riga", "vilnius", "tallinn", "tbilisi",
            "istanbul", "ankara", "tehran", "baghdad", "damascus", "beirut",
            "jerusalem", "cairo", "tripoli", "tunis", "algiers", "rabat",
            "nairobi", "lagos", "accra", "dakar", "addis", "harare", "lusaka",
            "tokyo", "beijing", "seoul", "taipei", "bangkok", "manila", "jakarta",
            "delhi", "mumbai", "karachi", "dhaka", "colombo", "kathmandu",
            "lima", "bogota", "quito", "caracas", "havana", "santiago",
            "buenos", "aires", "montevideo", "asuncion", "brasilia", "rio",

            # Historical/Mythological Regions
            "galatia", "anatolia", "iberia", "thrace", "macedonia", "illyria",
            "phrygia", "lydia", "cappadocia", "cilicia", "bithynia",
            "mesopotamia", "phoenicia", "judea", "galilee", "samaria",
            "nubia", "carthage", "palmyra", "babylonia", "assyria",
            "altai", "aztlan", "atlantis", "lemuria", "camelot", "shangri",

            # Common First Names
            "john", "mary", "anna", "emma", "noah", "liam", "sophia",
            "natalia", "anita", "tania", "tina", "nita", "maria", "julia",
            "lucia", "elena", "isabel", "rosa", "carmen", "ana", "eva",
            "sara", "laura", "paula", "diana", "monica", "claudia", "andrea",
            "michael", "david", "james", "robert", "william", "richard",
            "joseph", "thomas", "charles", "daniel", "matthew", "anthony",
            "mark", "donald", "steven", "paul", "andrew", "joshua", "brian",
            "ryan", "jason", "justin", "kevin", "eric", "jacob", "aaron",

            # Famous People (often in dictionaries)
            "attila", "caesar", "nero", "brutus", "cicero", "homer", "plato",
            "aristotle", "socrates", "pythagoras", "euclid", "archimedes",
            "ptolemy", "cleopatra", "nefertiti", "ramses", "tutankhamun",
            "atalanta", "athena", "apollo", "zeus", "hera", "artemis",
            "hercules", "achilles", "odysseus", "perseus", "theseus",

            # Constellations & Astronomy
            "antlia", "aquila", "aries", "cygnus", "draco", "hydra", "leo",
            "libra", "lyra", "orion", "phoenix", "pisces", "taurus", "virgo",
            "ursa", "vega", "sirius", "rigel", "betelgeuse", "polaris",

            # Demonyms (nationalities/ethnicities)
            "tanzanian", "brazilian", "french", "spanish", "russian", "japanese",
            "chinese", "indian", "italian", "german", "british", "english",
            "irish", "scottish", "welsh", "dutch", "belgian", "swiss",
            "austrian", "czech", "polish", "romanian", "hungarian", "croatian",
            "serbian", "greek", "turkish", "persian", "arab", "kurdish",
            "egyptian", "moroccan", "algerian", "tunisian", "libyan",
            "kenyan", "nigerian", "ethiopian", "somalian", "ugandan", "ghanaian",
            "korean", "vietnamese", "thai", "filipino", "indonesian", "malaysian",
            "pakistani", "bangladeshi", "afghan", "nepalese", "tibetan",
            "mexican", "cuban", "puerto", "rican", "haitian", "jamaican",
            "colombian", "venezuelan", "peruvian", "chilean", "argentinian",
            "altaian", "galatian", "thracian", "macedonian", "spartan", "athenian",
            "roman", "etruscan", "carthaginian", "phoenician", "babylonian",

            # Brands/Companies (sometimes in dictionaries)
            "alliant", "boeing", "ford", "tesla", "google", "amazon",

            # Place name components (often parts of compound proper nouns)
            "loca", "lima", "java", "cairo", "madison", "eugene",
        }

        # Known foreign words (non-English) that should be rejected
        self.known_foreign_words = {
            # Spanish
            "loca", "loco", "casa", "mesa", "taco", "salsa",
            "gitana",  # gypsy woman
            "tiza",    # chalk
            # French
            "avec", "sans", "tres", "mais", "pour",
            # Italian
            "ciao", "bella", "pasta", "pizza",
            "taglia",  # cut/size
            "intagli", # engravings (plural of intaglio)
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

    def _load_nyt_blacklist(self):
        """Load NYT rejection blacklist from scraped puzzle data.

        Blacklist contains words rejected 3+ times across 2,615 puzzles.
        Top rejected words: titi=206, lall=176, otto=176, caca=171, anna=167
        """
        blacklist_path = Path(__file__).parent.parent.parent.parent / 'nytbee_parser' / 'nyt_rejection_blacklist.json'
        if blacklist_path.exists():
            with open(blacklist_path, encoding='utf-8') as f:
                self.nyt_rejection_blacklist = json.load(f)
            self.logger.info("Loaded %d blacklisted words from NYT data", len(self.nyt_rejection_blacklist))
        else:
            self.nyt_rejection_blacklist = {}
            self.logger.debug("NYT blacklist file not found: %s", blacklist_path)

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
        Checks both manual list and Wiktionary metadata.

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word is archaic
        """
        word_lower = word.lower().strip()

        # Check manual archaic words list
        if word_lower in self.archaic_words:
            return True

        # Check Wiktionary metadata (Layer 4)
        if self.wiktionary and self.wiktionary.loaded:
            if self.wiktionary.is_archaic(word_lower) or self.wiktionary.is_rare(word_lower):
                return True

        return False

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

    def is_blacklisted(self, word: str) -> bool:
        """Check if word is in NYT rejection blacklist.

        Data-driven rejection based on 2,615 historical puzzles.
        Words rejected 50+ times are considered definitively rejected.

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word should be rejected based on blacklist
        """
        word_lower = word.lower().strip()
        rejection_count = self.nyt_rejection_blacklist.get(word_lower, 0)

        # Instant reject if word rejected many times
        if rejection_count >= self.INSTANT_REJECT_THRESHOLD:
            return True

        return False

    def get_blacklist_count(self, word: str) -> int:
        """Get the number of times a word was rejected in NYT history.

        Args:
            word: Word to check

        Returns:
            Rejection count (0 if not in blacklist)
        """
        word_lower = word.lower().strip()
        return self.nyt_rejection_blacklist.get(word_lower, 0)

    def get_confidence_penalty(self, word: str) -> float:
        """Get confidence penalty based on blacklist rejection count.

        Tiered system:
        - 10+ rejections: Word is rejected outright (penalty not used)
        - 5-9 rejections: 40% confidence penalty (suspicious)
        - 3-4 rejections: 20% confidence penalty (questionable)
        - 0-2 rejections: No penalty

        Args:
            word: Word to check

        Returns:
            Confidence penalty multiplier (0.0 to 1.0)
        """
        rejection_count = self.get_blacklist_count(word)

        if rejection_count >= self.INSTANT_REJECT_THRESHOLD:
            return 0.0  # Rejected, but this shouldn't be called
        elif rejection_count >= self.LOW_CONFIDENCE_THRESHOLD:
            return 0.6  # 40% penalty for 5-9 rejections
        elif rejection_count >= 3:
            return 0.8  # 20% penalty for 3-4 rejections
        else:
            return 1.0  # No penalty

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

        # Check NYT blacklist first (data-driven)
        if self.is_blacklisted(word_lower):
            rejection_count = self.get_blacklist_count(word_lower)
            self.logger.debug("Rejecting '%s': NYT blacklist (%d rejections)", word_lower, rejection_count)
            return True

        # Check all heuristic rejection criteria
        if self.is_proper_noun(word_lower):
            self.logger.debug("Rejecting '%s': proper noun", word_lower)
            return True

        if self.is_foreign_word(word_lower):
            self.logger.debug("Rejecting '%s': foreign word", word_lower)
            return True

        if self.is_abbreviation(word_lower):
            self.logger.debug("Rejecting '%s': abbreviation", word_lower)
            return True

        if self.is_technical_term(word_lower):
            self.logger.debug("Rejecting '%s': technical term", word_lower)
            return True

        # Layer 4: Wiktionary metadata (comprehensive automated detection)
        if self.wiktionary and self.wiktionary.loaded:
            # Check proper nouns via Wiktionary
            if self.wiktionary.is_proper_noun_wiktionary(word_lower):
                self.logger.debug("Rejecting '%s': proper noun (Wiktionary)", word_lower)
                return True

            # Check foreign-only words
            if self.wiktionary.is_foreign_only(word_lower):
                self.logger.debug("Rejecting '%s': foreign-only (Wiktionary)", word_lower)
                return True

            # Obsolete words are rejected (not just low confidence)
            if self.wiktionary.is_obsolete(word_lower):
                self.logger.debug("Rejecting '%s': obsolete (Wiktionary)", word_lower)
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

        if self.is_blacklisted(word_lower):
            return "nyt_blacklist"

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

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
from typing import Dict, List, Optional, Set

from ..constants import MIN_WORD_LENGTH
from .wiktionary_metadata import load_wiktionary_metadata

# GPU acceleration support (cuDF for batch string operations)
try:
    import cudf
    import pandas as pd
    GPU_AVAILABLE = True
    GPU_BATCH_SIZE = 10000  # Process 10k words per GPU batch
except ImportError:
    GPU_AVAILABLE = False
    GPU_BATCH_SIZE = 10000  # Still define for code consistency


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

        # Load NYT Pre-Filtered whitelist (words from valid NYT puzzles)
        # This is our ground truth - if word appeared in valid puzzles, accept it
        # regardless of Wiktionary flags (archaic, proper noun, etc.)
        self.nyt_prefiltered_whitelist = self._load_nyt_prefiltered()

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

            # Additional proper nouns (names, etc.)
            "inonu",  # Turkish surname/place name

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
            "indio",   # Indian (Spanish)
            "doni",    # gifts (Italian/Spanish)
            "chicha",  # fermented corn beverage (Andean/South American)
            # French
            "avec", "sans", "tres", "mais", "pour",
            # Italian
            "ciao", "bella", "pasta", "pizza",
            "taglia",  # cut/size
            "intagli", # engravings (plural of intaglio)
            # German
            "uber", "auto",
            # Greek
            "chian",   # from Chios island (proper noun/adjective)
            "achean",  # variant of "Achaean" (Greek proper adjective)
            # Latin
            "omnium",  # of all (Latin genitive plural)
            "unio",    # pearl/union (Latin, also mollusk genus)
        }

        # Archaic/obsolete words (flagged for rejection if not in NYT whitelist)
        # These are obscure words that should be rejected unless proven valid by NYT
        self.archaic_words = {
            # Old English pronouns and verbs
            "hath", "doth", "thee", "thou", "thy", "thine", "ye",
            # Archaic adverbs and prepositions
            "whilst", "whence", "whither", "hither", "thither",
            "betwixt", "amongst", "unto", "anon",
            # Archaic past tenses and participles
            "chidden",  # archaic past participle of "chide"
            "hied",     # archaic past tense of "hie" (to go quickly)
            # Archaic spelling variants
            "enniche",  # archaic variant of "niche"
            "inhance",  # archaic spelling of "enhance"
            # Archaic/dialectal words
            "hanch",    # archaic/dialectal
            "cond",     # archaic/abbreviation for "conduct" or "conduit"
            # Obscure religious/liturgical terms
            "noncommunion",  # obscure religious/liturgical term
            "nondo",    # archaic (not in Wiktionary but NYT rejects it)
        }

        # Offensive words/slurs (ALWAYS rejected, even if in dictionaries)
        # NYT would never include these regardless of alternate meanings
        self.offensive_words = {
            "coon",  # Racial slur (even though also = raccoon)
        }

        # Dialectal/informal words (regional variants, informal speech)
        # These are non-standard English forms that NYT typically avoids
        self.dialectal_words = {
            "haddie",  # dialectal/informal for "haddock" (fish)
            "dich",    # unknown origin, possibly German or dialectal
            "niched",  # questionable verb form of "niche" (modern marketing jargon)
        }

        # Abbreviations (NYT doesn't accept abbreviations)
        self.abbreviations = {
            "capt", "dept", "govt", "corp", "assn", "natl", "intl",
            "prof", "repr", "mgmt", "admin", "info", "tech", "spec",
            "univ", "inst", "assoc", "incl", "misc", "temp", "approx",
            "est", "max", "min", "avg", "std",
            "muni",  # municipal (appears in puzzles but is abbreviation)
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

    def _load_nyt_prefiltered(self):
        """Load NYT Pre-Filtered whitelist from valid puzzle solutions.

        This dictionary contains words that have appeared in valid NYT puzzles.
        Words in this list are ALWAYS accepted, even if Wiktionary marks them
        as archaic, proper nouns, etc.

        This is our ground truth for what NYT considers acceptable.
        """
        prefiltered_path = Path(__file__).parent.parent.parent.parent / 'data' / 'dictionaries' / 'nyt_prefiltered.txt'
        if prefiltered_path.exists():
            with open(prefiltered_path, encoding='utf-8') as f:
                whitelist = {line.strip().lower() for line in f if line.strip()}
            self.logger.info("Loaded %d words from NYT Pre-Filtered whitelist", len(whitelist))
            return whitelist
        else:
            self.logger.debug("NYT Pre-Filtered file not found: %s", prefiltered_path)
            return set()

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

    def is_dialectal(self, word: str) -> bool:
        """Check if word is dialectal or informal.

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word is dialectal/informal
        """
        word_lower = word.lower().strip()

        # Check known dialectal/informal words
        if word_lower in self.dialectal_words:
            return True

        return False

    def is_archaic(self, word: str) -> bool:
        """Check if word is archaic/obsolete.

        Note: Archaic/obsolete words are NOT rejected, just flagged for low confidence.
        Checks both manual list and Wiktionary metadata.

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word is archaic/obsolete/rare
        """
        word_lower = word.lower().strip()

        # Check manual archaic words list
        if word_lower in self.archaic_words:
            return True

        # Check Wiktionary metadata (Layer 4)
        # Include obsolete, archaic, and rare words - all get low confidence
        if self.wiktionary and self.wiktionary.loaded:
            if (self.wiktionary.is_obsolete(word_lower) or
                self.wiktionary.is_archaic(word_lower) or
                self.wiktionary.is_rare(word_lower)):
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

    def is_slang_compound(self, word: str) -> bool:
        """Check if word is a slang compound (e.g., acidhead, pothead).

        Args:
            word: Word to check (should be lowercase)

        Returns:
            True if word is a slang compound
        """
        word_lower = word.lower().strip()

        # Drug-related compound slang: *head (acidhead, pothead, crackhead, etc.)
        # These are 1960s-1980s counterculture slang terms NYT avoids
        if len(word_lower) > 7 and word_lower.endswith("head"):
            # Check if the part before "head" is drug-related or derogatory
            stem = word_lower[:-4]  # Remove "head"
            drug_stems = {
                "acid",     # LSD
                "pot",      # marijuana
                "crack",    # crack cocaine
                "meth",     # methamphetamine
                "coke",     # cocaine
                "speed",    # amphetamines
                "dope",     # various drugs
                "pill",     # pill abuse
            }
            if stem in drug_stems:
                return True
            # Also check for derogatory compound terms
            derogatory_stems = {
                "bone",     # bonehead (stupid person)
                "block",    # blockhead (stupid person)
                "knuckle",  # knucklehead (stupid person)
                "air",      # airhead (stupid person)
                "meat",     # meathead (stupid person)
            }
            if stem in derogatory_stems:
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

        # Chemical alkaloids and proteins ending in -ine (e.g., echidnine, morphine, caffeine)
        # But whitelist common words
        if len(word_lower) > 5 and word_lower.endswith("ine"):
            ine_whitelist = {
                "mine", "line", "fine", "wine", "dine", "pine", "vine", "nine",
                "spine", "shine", "whine", "brine", "swine", "trine",
                "define", "refine", "confine", "genuine", "routine", "machine",
                "feline", "canine", "bovine", "equine",  # common animal terms
            }
            if word_lower not in ine_whitelist:
                return True

        # Chemical alkanes ending in -ane (e.g., methane, propane, hendecane, hecdecane)
        # But whitelist common words
        if len(word_lower) > 5 and word_lower.endswith("ane"):
            ane_whitelist = {
                "lane", "cane", "mane", "pane", "vane", "wane", "bane", "sane",
                "plane", "crane", "humane", "insane", "arcane", "profane",
                "butane", "octane", "propane",  # common fuels that might appear
            }
            if word_lower not in ane_whitelist:
                return True

        # Specific alkane pattern: *decane (11-carbon chain hydrocarbons)
        # These are very technical chemistry terms
        if "decane" in word_lower and len(word_lower) > 6:
            return True

        # Zoological family names ending in -id (e.g., echinid, canid, felid)
        # But whitelist common words
        if len(word_lower) > 5 and word_lower.endswith("id"):
            id_whitelist = {
                "said", "paid", "laid", "maid", "raid", "braid",
                "valid", "solid", "timid", "rapid", "vapid", "acrid",
                "liquid", "stupid", "hybrid", "orchid",
            }
            if word_lower not in id_whitelist:
                return True

        # Chemical acid suffixes (e.g., muconic acid, nonoic acid, cuminic acid, cahincic acid)
        # -oic, -onic, -inic, -oid, -idic, -ic endings typically indicate chemical compounds
        if len(word_lower) > 5:
            # Whitelist common words to avoid false positives
            chemical_whitelist = {
                "heroic", "stoic", "sonic", "tonic", "iconic", "ironic", "chronic",
                "conic", "ionic",  # geometry/physics terms that are common
                "music", "magic", "logic", "comic", "topic", "basic", "toxic",  # common -ic words
                "public", "static", "ethnic", "cosmic", "classic", "plastic",
            }
            if word_lower not in chemical_whitelist:
                chemical_endings = ["oic", "onic", "inic", "oid", "idic"]
                if any(word_lower.endswith(ending) for ending in chemical_endings):
                    return True
                # Standalone -ic for acids (check for unusual consonant clusters)
                if len(word_lower) > 7 and word_lower.endswith("ic"):
                    # Chemical names often have unusual patterns:
                    # 1. Doubled letters (e.g., salicylic)
                    # 2. 3+ consonants in a row (e.g., cahincic has "hinc")
                    # 3. Uncommon letter combinations
                    if any(c1 == c2 for c1, c2 in zip(word_lower, word_lower[1:])):
                        return True
                    # Check for 3+ consecutive consonants (very unusual in English)
                    consonants = set('bcdfghjklmnpqrstvwxyz')
                    consonant_run = 0
                    max_consonant_run = 0
                    for char in word_lower:
                        if char in consonants:
                            consonant_run += 1
                            max_consonant_run = max(max_consonant_run, consonant_run)
                        else:
                            consonant_run = 0
                    if max_consonant_run >= 3:
                        return True

        # Chemical protein/compound names ending in -in (e.g., nucin, indoin, indin)
        # But avoid common words like "min", "din", "in"
        if len(word_lower) > 4 and word_lower.endswith("in"):
            # Whitelist common -in words
            in_whitelist = {"min", "din", "sin", "fin", "kin", "pin", "tin", "win",
                           "cumin", "satin", "robin", "cabin", "basin", "resin",
                           "ruin", "main", "rain", "pain", "gain", "vein", "coin", "join"}
            if word_lower not in in_whitelist:
                return True

        # Latin scientific endings (but whitelist common words)
        if len(word_lower) > 6:
            # Whitelist common words that end in Latin suffixes
            # -ous: famous, nervous, curious, etc.
            # -ium: stadium, premium, medium, condominium, etc.
            latin_whitelist = {
                "famous", "nervous", "curious", "humane",  # -ous/-ane
                "stadium", "premium", "medium", "podium",  # -ium (common)
                "auditorium", "condominium", "delirium",   # -ium (common)
                "equilibrium", "aquarium", "emporium",     # -ium (common)
            }
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

    def filter_batch_gpu(self, words: List[str]) -> Set[str]:
        """GPU-accelerated batch filtering of candidate words.

        Uses cuDF for parallel set membership checks and pattern matching.
        Significantly faster than sequential CPU filtering for large batches.

        Args:
            words: List of words to filter

        Returns:
            Set of words that passed all rejection filters
        """
        if not GPU_AVAILABLE or len(words) < 1000:
            # For small batches, CPU is faster (no GPU transfer overhead)
            return {word for word in words if not self.should_reject(word)}

        accepted_words = set()

        # Process in batches to manage GPU memory
        for i in range(0, len(words), GPU_BATCH_SIZE):
            batch = words[i:i + GPU_BATCH_SIZE]

            # Create cuDF DataFrame on GPU
            df = cudf.DataFrame({'word': batch})
            df['word_lower'] = df['word'].str.lower().str.strip()

            # GPU-accelerated whitelist check (highest priority)
            if self.nyt_prefiltered_whitelist:
                whitelist_series = cudf.Series(list(self.nyt_prefiltered_whitelist))
                df['in_whitelist'] = df['word_lower'].isin(whitelist_series)
            else:
                df['in_whitelist'] = False

            # GPU-accelerated blacklist check
            if self.nyt_rejection_blacklist:
                blacklist_series = cudf.Series(list(self.nyt_rejection_blacklist.keys()))
                df['in_blacklist'] = df['word_lower'].isin(blacklist_series)
            else:
                df['in_blacklist'] = False

            # GPU-accelerated offensive words check
            if self.offensive_words:
                offensive_series = cudf.Series(list(self.offensive_words))
                df['is_offensive'] = df['word_lower'].isin(offensive_series)
            else:
                df['is_offensive'] = False

            # GPU-accelerated proper nouns check
            if self.known_proper_nouns:
                proper_series = cudf.Series(list(self.known_proper_nouns))
                df['is_proper'] = df['word_lower'].isin(proper_series)
            else:
                df['is_proper'] = False

            # GPU-accelerated foreign words check
            if self.known_foreign_words:
                foreign_series = cudf.Series(list(self.known_foreign_words))
                df['is_foreign'] = df['word_lower'].isin(foreign_series)
            else:
                df['is_foreign'] = False

            # Transfer filtered results to CPU for final processing
            # Accept words that:
            # 1. Are in whitelist (highest priority) OR
            # 2. NOT (blacklisted OR offensive OR proper OR foreign)
            df_pandas = df.to_pandas()

            for _, row in df_pandas.iterrows():
                word_lower = row['word_lower']

                # Whitelist has highest priority
                if row['in_whitelist']:
                    accepted_words.add(word_lower)
                    continue

                # Reject if any rejection criteria met
                if (row['is_offensive'] or row['in_blacklist'] or
                    row['is_proper'] or row['is_foreign']):
                    continue

                # For remaining words, do CPU-based detailed checks
                # (pattern matching, technical terms, etc. are complex for GPU)
                if not self.should_reject(word_lower):
                    accepted_words.add(word_lower)

        return accepted_words

    def should_reject(self, word: str) -> bool:
        """Check if word should be rejected (NYT likely won't accept it).

        This is the main entry point for filtering.

        Args:
            word: Word to check (case-insensitive, will be lowercased)

        Returns:
            True if word should be rejected
        """
        word_original = word.strip()
        word_lower = word_original.lower()

        # Length check
        if len(word_lower) < MIN_WORD_LENGTH:
            return True

        # PRIORITY 0: Offensive words/slurs (ABSOLUTE HIGHEST PRIORITY)
        # ALWAYS reject, even if in dictionaries or NYT whitelist
        # This is an ethical/safety requirement
        if word_lower in self.offensive_words:
            self.logger.debug("Rejecting '%s': offensive word/slur", word_lower)
            return True

        # PRIORITY 0.5: Abbreviations (NYT policy: no abbreviations)
        # ALWAYS reject, even if appeared in historical puzzles (whitelist)
        # NYT doesn't accept abbreviations as per their rules
        if self.is_abbreviation(word_lower):
            self.logger.debug("Rejecting '%s': abbreviation", word_lower)
            return True

        # PRIORITY 0.6: Slang compounds (NYT policy: avoid counterculture slang)
        # ALWAYS reject drug slang and derogatory compounds
        if self.is_slang_compound(word_lower):
            self.logger.debug("Rejecting '%s': slang compound", word_lower)
            return True

        # PRIORITY 1: NYT Pre-Filtered Whitelist (HIGHEST PRIORITY)
        # If word appeared in valid NYT puzzles, ALWAYS accept it
        # Whitelist > Blacklist because a word can be rejected in some puzzles but accepted in others
        # Examples: "indium" rejected 4 times but IS valid in some puzzles
        # This overrides blacklist and Wiktionary flags
        if word_lower in self.nyt_prefiltered_whitelist:
            self.logger.debug("Accepting '%s': in NYT Pre-Filtered whitelist", word_lower)
            return False

        # PRIORITY 2: NYT Blacklist (data-driven from 2,615 puzzles)
        # Only reject if NOT in whitelist
        # Words rejected 3+ times are likely invalid (unless whitelist proves otherwise)
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

        if self.is_dialectal(word_lower):
            self.logger.debug("Rejecting '%s': dialectal/informal word", word_lower)
            return True

        if self.is_technical_term(word_lower):
            self.logger.debug("Rejecting '%s': technical term", word_lower)
            return True

        # Check manual archaic words list (with whitelist protection already applied)
        # Words in archaic_words that aren't in NYT whitelist get rejected
        if self.is_archaic(word_lower):
            # Only reject if from manual list, not Wiktionary (Wiktionary checked below)
            if word_lower in self.archaic_words:
                self.logger.debug("Rejecting '%s': archaic/obscure (manual list)", word_lower)
                return True

        # Layer 4: Wiktionary metadata (comprehensive automated detection)
        if self.wiktionary and self.wiktionary.loaded:
            # Check proper nouns (RE-ENABLED with whitelist protection)
            # Safe now because NYT Pre-Filtered whitelist overrides this
            # Examples: "communion" (proper + in whitelist) → accepted (by whitelist)
            #           "dominic" (proper + NOT in whitelist) → rejected here
            if self.wiktionary.is_proper_noun_wiktionary(word_lower):
                self.logger.debug("Rejecting '%s': proper noun (Wiktionary)", word_lower)
                return True

            # Check foreign-only words
            if self.wiktionary.is_foreign_only(word_lower):
                self.logger.debug("Rejecting '%s': foreign-only (Wiktionary)", word_lower)
                return True

            # Check obsolete/archaic/rare words (RE-ENABLED with whitelist protection)
            # Reject if NOT in NYT Pre-Filtered (we already checked whitelist above)
            # This catches truly obsolete words like "mund", "minum", "immund", "unnun"
            # while accepting common words with archaic senses like "mind", "work"
            if (self.wiktionary.is_obsolete(word_lower) or
                self.wiktionary.is_archaic(word_lower) or
                self.wiktionary.is_rare(word_lower)):
                self.logger.debug("Rejecting '%s': obsolete/archaic/rare (Wiktionary)", word_lower)
                return True

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

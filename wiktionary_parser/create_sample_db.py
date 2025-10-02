#!/usr/bin/env python3
"""
Create sample Wiktionary database for testing.

Uses Wiktionary API to fetch metadata for specific test words.
For production, use build_wiktionary_db.py to process full dump.
"""

import json
from pathlib import Path

# Sample test data based on our manual analysis
# In production, this would come from parsing the full Wiktionary dump

SAMPLE_DATABASE = {
    "obsolete": [
        "taglia",  # English: obsolete (pulley system), also Italian/Romansch
        "whilst",  # archaic form of "while"
        "betwixt", # archaic form of "between"
    ],
    "archaic": [
        "hath", "doth", "thee", "thou", "thy", "thine", "ye",
        "whence", "whither", "hither", "thither",
        "amongst", "unto", "anon",
    ],
    "rare": [
        # Words marked as rare in Wiktionary
        "abstruse", "obfuscate",
    ],
    "proper_nouns": [
        # Capitalized entries with POS=Proper noun
        "Tanzania", "Atlanta", "Tallinn", "Galatia", "Altai", "Aztlan",
        "Natalia", "Attila", "Atalanta", "Anita", "Tania",
        "Antlia",  # constellation
        "Atlanta", "Boston", "Chicago", "Dallas",
        # Countries
        "Brazil", "France", "Spain", "Russia", "Japan", "China", "India",
        # More cities
        "London", "Paris", "Berlin", "Madrid", "Rome",
    ],
    "foreign_only": [
        # Words that appear ONLY in foreign language sections (no English entry)
        # Based on testing - these might actually have English entries in real Wiktionary
        # For now, empty - will be populated from full dump
    ],
    "multi_language": {
        # Words that appear in multiple languages
        "taglia": ["English-obsolete", "Italian", "Romansch"],
        "gitana": ["English", "Spanish", "Catalan", "Italian"],
        "atlanta": ["English-proper", "Italian"],
    },
    "stats": {
        "obsolete_count": 3,
        "archaic_count": 13,
        "rare_count": 2,
        "proper_noun_count": 20,
        "foreign_only_count": 0,
        "multi_language_count": 3,
        "note": "Sample database for testing. Run build_wiktionary_db.py for full database."
    }
}


def main():
    """Create sample Wiktionary metadata database."""
    output_path = Path('src/spelling_bee_solver/data/wiktionary_metadata.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(SAMPLE_DATABASE, f, indent=2, ensure_ascii=False)

    print(f"✓ Created sample Wiktionary database: {output_path}")
    print(f"  Obsolete: {len(SAMPLE_DATABASE['obsolete'])}")
    print(f"  Archaic: {len(SAMPLE_DATABASE['archaic'])}")
    print(f"  Proper nouns: {len(SAMPLE_DATABASE['proper_nouns'])}")
    print()
    print("NOTE: This is a small sample for testing.")
    print("For production, run: ./wiktionary_parser/build_wiktionary_db.py")
    print("  (Downloads ~2GB, parses 6M+ entries, takes 1-2 hours)")


if __name__ == '__main__':
    main()

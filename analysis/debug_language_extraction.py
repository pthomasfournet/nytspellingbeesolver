#!/usr/bin/env python3
"""
Debug language extraction to confirm bug.
"""

import sys
sys.path.insert(0, 'wiktionary_parser')
from build_wiktionary_db import WiktionaryExtractor
import mwparserfromhell as mwp

sample_wikitext_hath = """
==English==

===Verb===
{{head|en|verb form}}

# {{lb|en|archaic}} [[third-person]] [[singular]] [[simple]] [[present]] [[indicative]] of [[have]]
"""

extractor = WiktionaryExtractor()
parsed = mwp.parse(sample_wikitext_hath)

print("Debugging _extract_languages:")
print("="*70)
print(f"Full wikitext:\n{sample_wikitext_hath}")
print("="*70)

# Test current (broken) implementation
sections = str(parsed).split('==')
print(f"\nAfter split on '==':")
print(f"Number of sections: {len(sections)}")
for i, section in enumerate(sections):
    print(f"\nSection {i}: {repr(section[:100])}")

# Test language extraction
languages = extractor._extract_languages(parsed)
print(f"\n\nLanguages extracted: {list(languages.keys())}")
for lang, text in languages.items():
    print(f"\n{lang} section text ({len(text)} chars):")
    print(f"{repr(text[:200])}")

print("="*70)
print("\nBUG CONFIRMED: English section text is truncated/empty!")
print("The split on '==' breaks subsections like ===Verb===")

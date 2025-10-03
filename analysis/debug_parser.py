#!/usr/bin/env python3
"""
Debug parser by testing on sample wikitext.
"""

import sys
sys.path.insert(0, 'wiktionary_parser')
from build_wiktionary_db import WiktionaryExtractor

# Sample wikitext for "hath" (from WebFetch)
sample_wikitext_hath = """
==English==

===Verb===
{{head|en|verb form}}

# {{lb|en|archaic}} [[third-person]] [[singular]] [[simple]] [[present]] [[indicative]] of [[have]]
"""

# Sample wikitext for "abaft"
sample_wikitext_abaft = """
==English==

===Adverb===
{{en-adv|-}}

# {{lb|en|nautical}} Behind; toward the [[stern]] relative to some other [[object]] or [[position]]; [[aft]] of.
# {{lb|en|nautical|obsolete}} Backwards.
"""

# Test
extractor = WiktionaryExtractor()

print("Testing parser on sample wikitext:")
print("="*60)

print("\n1. Testing 'hath' (should find 'archaic'):")
extractor.extract_from_page("hath", sample_wikitext_hath)
print(f"   Archaic words: {extractor.archaic_words}")
print(f"   Obsolete words: {extractor.obsolete_words}")

print("\n2. Testing 'abaft' (should find 'obsolete'):")
extractor2 = WiktionaryExtractor()
extractor2.extract_from_page("abaft", sample_wikitext_abaft)
print(f"   Archaic words: {extractor2.archaic_words}")
print(f"   Obsolete words: {extractor2.obsolete_words}")

print("\n3. Checking if English section is being extracted:")
from build_wiktionary_db import WiktionaryExtractor
import mwparserfromhell as mwp
parsed = mwp.parse(sample_wikitext_hath)
extractor3 = WiktionaryExtractor()
languages = extractor3._extract_languages(parsed)
print(f"   Languages found: {list(languages.keys())}")
if 'English' in languages:
    print(f"   English section text: {languages['English'][:100]}...")
    labels = extractor3._extract_usage_labels(languages['English'])
    print(f"   Labels extracted: {labels}")

print("="*60)

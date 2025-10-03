#!/usr/bin/env python3
"""
Quick test to verify parser fix for plain text labels.
Tests the regex pattern matching logic directly.
"""

import re

# Test cases from actual Wiktionary entries
# NOTE: This test only covers PLAIN TEXT labels in parentheses.
# Template-based labels like {{lb|en|obsolete}} are tested separately.
test_cases = [
    # (section_text, expected_labels)
    ("1. (archaic) third-person singular simple present", {'archaic'}),
    ("# {{lb|en|nautical}} Behind", set()),  # Template only, no plain text labels
    ("# {{lb|en|nautical|obsolete}} Backwards", set()),  # Template only (regex won't catch this)
    ("(rare, dated) An old usage", {'rare', 'dated'}),
    ("Some normal definition", set()),
    ("(Archaic) Capitalized version", {'archaic'}),  # Case insensitive
    ("(historical) Old term", {'historical'}),
    ("(uncommon) Rarely used", {'uncommon'}),
    ("(obsolete, archaic) Very old word", {'obsolete', 'archaic'}),  # Multiple labels
]

# Label sets from parser
obsolete_labels = {'obsolete', 'dated'}
archaic_labels = {'archaic', 'historical'}
rare_labels = {'rare', 'uncommon'}
all_labels = obsolete_labels | archaic_labels | rare_labels

def extract_labels(section_text: str) -> set:
    """Extract usage labels using the new regex pattern."""
    labels = set()

    for label in all_labels:
        # Match label in parentheses - can be first or in comma-separated list
        pattern = r'[\(,]\s*' + re.escape(label) + r'\s*[,\)]'
        if re.search(pattern, section_text, re.IGNORECASE):
            labels.add(label)

    return labels

# Run tests
print("Testing parser fix for plain text labels:\n")
all_passed = True

for i, (text, expected) in enumerate(test_cases, 1):
    result = extract_labels(text)
    passed = result == expected
    all_passed = all_passed and passed

    status = "✓" if passed else "✗"
    print(f"{status} Test {i}: {text[:50]}")
    if not passed:
        print(f"  Expected: {expected}")
        print(f"  Got:      {result}")
    print()

if all_passed:
    print("✓ All tests passed! Parser fix is working correctly.")
else:
    print("✗ Some tests failed. Review regex pattern.")

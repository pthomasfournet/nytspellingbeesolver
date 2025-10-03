#!/usr/bin/env python3
"""
Detailed debug of label extraction logic.
"""

import mwparserfromhell as mwp

# Sample English section text from "hath"
section_text = """
===Verb===
{{head|en|verb form}}

# {{lb|en|archaic}} [[third-person]] [[singular]] [[simple]] [[present]] [[indicative]] of [[have]]
"""

print("Debugging label extraction:")
print("="*70)

# Parse the section
parsed = mwp.parse(section_text)
print(f"\n1. Parsed section:\n{parsed}")

# Find all templates
templates = list(parsed.filter_templates())
print(f"\n2. Found {len(templates)} templates:")
for i, template in enumerate(templates):
    print(f"   Template {i}: {template}")
    print(f"     Name: '{template.name}'")
    print(f"     Name (stripped/lower): '{str(template.name).strip().lower()}'")
    print(f"     Params: {list(template.params)}")
    for j, param in enumerate(template.params):
        print(f"       Param {j}: value='{param.value}', stripped/lower='{str(param.value).strip().lower()}'")

# Test label sets
obsolete_labels = {'obsolete', 'dated'}
archaic_labels = {'archaic', 'historical'}
rare_labels = {'rare', 'uncommon'}

print(f"\n3. Label sets:")
print(f"   Obsolete: {obsolete_labels}")
print(f"   Archaic: {archaic_labels}")
print(f"   Rare: {rare_labels}")

# Test extraction logic
labels = set()
for template in parsed.filter_templates():
    name = str(template.name).strip().lower()

    # Check template name
    if name in obsolete_labels | archaic_labels | rare_labels:
        print(f"\n4. Template name '{name}' matches! Adding to labels.")
        labels.add(name)

    # Check for {{label|en|obsolete}} format
    if name in {'label', 'lb', 'context'}:
        print(f"\n5. Found label template '{name}', checking params...")
        for param in template.params:
            param_str = str(param.value).strip().lower()
            print(f"   Checking param: '{param_str}'")
            if param_str in obsolete_labels | archaic_labels | rare_labels:
                print(f"   ✓ MATCH! Adding '{param_str}' to labels.")
                labels.add(param_str)
            else:
                print(f"   ✗ No match")

print(f"\n6. Final labels extracted: {labels}")
print("="*70)

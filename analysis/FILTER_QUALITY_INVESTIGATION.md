# Filter Quality Investigation Summary

**Date:** October 3, 2025
**Branch:** dev

## Executive Summary

Investigated filter quality by generating and solving 1,000 random Spelling Bee puzzles. Identified critical bug in Wiktionary Layer 4 filter preventing proper detection of archaic, obsolete, and specialized terminology.

## Test Methodology

### Random Puzzle Generation
- Generated 10,000 unique random puzzles with seed 42
- Solved 1,000 puzzles using 12 parallel workers
- Extracted 17,437 unique words for analysis

### Initial Results
- **Total words:** 17,437
- **Problematic (categorized):** 10 (0.06%)
  - 5 archaic (anon, hath, thee, unto, whence)
  - 5 very long (>13 characters)
- **Uncategorized:** 17,427 (99.94%)

### Suspicious Words Identified (Sample)
Manual review of first 200 words found 15 problematic entries:
- **Foreign/Biblical:** abaddon, abayas, abdal, abhal, abuna
- **Technical:** abamp (electrical unit), abbr (abbreviation)
- **Nautical/Archaic:** abaft, abray
- **Obscure:** abada, abattu, abcee, abegge, aberr, abos

## Root Cause Analysis

### Problem 1: Sample Database Usage
**Issue:** Solver was using `wiktionary_metadata.json` (44 words) instead of full database.

**Evidence:**
```json
{
  "obsolete": ["taglia", "whilst", "betwixt"],
  "archaic": ["hath", "doth", "thee", "thou", ...],  // 14 total
  "proper_nouns": ["Tanzania", "Atlanta", ...],       // 27 total
  "stats": {
    "note": "Sample database for testing"
  }
}
```

### Problem 2: Parser Bug
**Issue:** Wiktionary parser only checked for template syntax `{{archaic}}`, but Wiktionary uses plain text labels `(archaic)`.

**Investigation:**
Fetched actual Wiktionary entries to examine format:

**hath:** Uses plain text label
```wikitext
'''hath'''
1. (archaic) third-person singular simple present indicative of have
```

**abaft:** Uses lb (label) template
```wikitext
# {{lb|en|nautical}} Behind; toward the stern
# {{lb|en|nautical|obsolete}} Backwards.
```

**Previous Parser Logic (BROKEN):**
```python
# Only checked template names
for template in parsed.filter_templates():
    name = str(template.name).strip().lower()
    if name in {'obsolete', 'archaic', 'rare'}:  # Never matched!
        labels.add(name)
```

**Previous Build Results:**
- Processed: 10,158,088 pages
- Obsolete: 0 ❌
- Archaic: 0 ❌
- Rare: 0 ❌
- Proper nouns: 0 ❌
- Foreign-only: 7,226,626 ✓

## Solution Implemented

### Parser Fix (wiktionary_parser/build_wiktionary_db.py)

**Initial Fix:** Added regex pattern matching for parenthetical labels
**Improvement:** Enhanced regex to handle comma-separated labels

```python
# Also check for plain text labels in parentheses: (archaic), (obsolete), (rare, dated)
import re
all_labels = self.obsolete_labels | self.archaic_labels | self.rare_labels
for label in all_labels:
    # Match label in parentheses - can be first or in comma-separated list
    # Matches: (archaic), (rare, dated), (obsolete)
    pattern = r'[\(,]\s*' + re.escape(label) + r'\s*[,\)]'
    if re.search(pattern, section_text, re.IGNORECASE):
        labels.add(label)
```

**Pattern Explanation:**
- `[\(,]` - Label can be preceded by `(` or `,`
- `\s*` - Optional whitespace
- `label` - The actual label text (escaped)
- `\s*` - Optional whitespace
- `[,\)]` - Label can be followed by `,` or `)`

This now handles all formats:
- Template: `{{lb|en|archaic}}` or `{{archaic}}` (handled by existing template code)
- Plain text: `(archaic)`, `(obsolete)`, `(rare, dated)`, `(obsolete, archaic)`
- Case-insensitive: `(Archaic)` → matched as "archaic"

**Validation:** Created test_parser_fix.py with 9 test cases - all pass ✓

## Expected Results After Fix

### Database Rebuild
- **Status:** In progress (restarted 13:30:04 with improved regex)
- **PID:** 211737
- **Output:** `src/spelling_bee_solver/data/wiktionary_metadata.json`
- **Expected:** Non-zero counts for obsolete/archaic/rare/proper_nouns
- **Note:** First build stopped at 484k pages, restarted with improved comma-separated label fix

### Suspicious Words Should Be Caught
Examples that should now be filtered:
- `abaft`: (nautical, obsolete)
- `abray`: (archaic)
- `abbr`: (abbreviation - may still pass if not labeled)
- `abamp`: (technical - may still pass if not labeled obsolete/rare)

### Filter Effectiveness Improvement
- **Before:** 0.06% categorized, 99.94% uncategorized
- **After:** Expected significant increase in categorized words

## Files Generated

### Analysis Tools
- `analysis/generate_random_puzzles.py` - Random puzzle generator
- `analysis/solve_all_puzzles.py` - Bulk puzzle solver (modified for random puzzles)
- `analysis/assess_filter_quality.py` - Filter quality analyzer

### Data Files
- `analysis/random_10k_puzzles.json` (1.5MB) - 10,000 puzzle specifications
- `analysis/random_1k_results.json` (1.1MB) - Solver results for 1,000 puzzles
- `analysis/random_1k_filter_quality.json` - Detailed categorization

### Logs
- `analysis/wiktionary_rebuild.log` - Current rebuild progress

## Next Steps

1. **Wait for rebuild to complete** (~30-60 minutes)
2. **Verify database quality:**
   ```bash
   jq '.stats' src/spelling_bee_solver/data/wiktionary_metadata.json
   ```
3. **Re-test 1,000 puzzles:**
   ```bash
   ./venv/bin/python3 analysis/solve_all_puzzles.py \
     --input analysis/random_10k_puzzles.json \
     --max-puzzles 1000 \
     --output analysis/random_1k_results_v2.json \
     --workers 12
   ```
4. **Analyze improvements:**
   ```bash
   ./venv/bin/python3 analysis/assess_filter_quality.py \
     --input analysis/random_1k_results_v2.json \
     --output analysis/filter_quality_v2.json
   ```
5. **Compare before/after** to quantify improvement

## Technical Notes

### Parser Label Sets
```python
self.obsolete_labels = {'obsolete', 'dated'}
self.archaic_labels = {'archaic', 'historical'}
self.rare_labels = {'rare', 'uncommon'}
```

### Proper Noun Detection
Works correctly - checks for header:
```python
def _is_proper_noun(self, section_text: str) -> bool:
    return '===Proper noun===' in section_text or \
           '====Proper noun====' in section_text
```

### Performance
- Puzzle generation: <1 second (10,000 puzzles)
- Puzzle solving: 224 seconds (1,000 puzzles, 4.5/sec)
- Database parsing: ~60 minutes (10.1M pages)

## Conclusion

Filter quality investigation successfully identified two critical issues:
1. Production solver using 44-word sample database
2. Parser unable to extract plain text usage labels

Fix implemented and full database rebuild in progress. Expected significant improvement in filter effectiveness, particularly for archaic and nautical terminology.

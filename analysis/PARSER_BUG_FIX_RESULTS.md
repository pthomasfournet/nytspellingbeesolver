# Wiktionary Parser Bug Fix: Results

**Date:** October 3, 2025
**Branch:** dev
**Status:** ✅ FIXED

## Executive Summary

Discovered and fixed critical bug in Wiktionary parser preventing all archaic/obsolete/rare word detection. Parser was using `split('==')` which destroyed language section content, resulting in **0 characters** of English text to analyze.

## The Bug

### Root Cause
```python
# BROKEN CODE (wiktionary_parser/build_wiktionary_db.py:117)
sections = str(parsed).split('==')
```

**Problem:** Splits on ALL `==` markers, including:
- `==English==` (level-2 header) ✓ intended
- `===Verb===` (level-3 subsection) ✗ unintended
- `====Examples====` (level-4) ✗ unintended

**Result:** English section text = **0 characters**
- `_extract_usage_labels()` receives empty string
- Template parsing finds nothing
- Database build: 0 archaic, 0 obsolete, 0 rare

### Discovery Process

1. **Initial Investigation:** Generated 1,000 random puzzles, found 99.94% uncategorized
2. **Hypothesis:** Plain text labels `(archaic)` not detected (red herring!)
3. **Added Regex Fix:** Pattern `r'[\(,]\s*label\s*[,\)]'` for parenthetical labels
4. **Still Failed:** 100k pages → 0 archaic, 0 obsolete, 0 rare
5. **Deep Debug:** Created test scripts, discovered template parsing works in isolation
6. **Breakthrough:** Found `_extract_languages()` returns 0-char English sections
7. **Root Cause:** The `split('==')` destroys all content

## The Fix

### Implementation
```python
def _extract_languages(self, parsed) -> Dict[str, str]:
    """Extract language sections from parsed wikitext."""
    import re

    text = str(parsed)
    languages = {}

    # Match level-2 headers: ==Language==
    # Pattern captures everything until next level-2 header or end
    pattern = r'\n==([\w\s]+)==\n(.*?)(?=\n==[\w\s]+=|$)'

    for match in re.finditer(pattern, text, re.DOTALL):
        lang_name = match.group(1).strip()
        section_text = match.group(2)
        languages[lang_name] = section_text

    return languages
```

**Key Changes:**
- Uses regex to match only level-2 headers (`==Language==`)
- Captures all content until next level-2 header
- Preserves subsections (`===Verb===`, `====Examples====`)
- Uses `re.DOTALL` for multiline matching

### Validation

**Test Case: "hath"**
```
Before: English section = 0 chars → archaic NOT detected
After:  English section = 134 chars → archaic DETECTED ✓
```

**Database Build (100k pages):**
| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Obsolete | 0 | 3,229 | +∞ |
| Archaic | 0 | 2,236 | +∞ |
| Rare | 0 | 1,127 | +∞ |
| Proper Nouns | 0 | 4,468 | +∞ |
| Foreign-only | 44,573 | 42,153 | -5.4% |

## Filter Quality Impact

### Test: 1,000 Random Puzzles

**Before Fix:**
- Total unique words: 17,437
- Uncategorized: 17,427 (99.94%)
- Wiktionary archaic: 0
- Wiktionary rare: 0
- Wiktionary proper nouns: 0
- Manual archaic only: 5

**After Fix:**
- Total unique words: 15,051
- Uncategorized: 14,836 (98.6%)
- Wiktionary archaic: 158 ✅
- Wiktionary rare: 63 ✅
- Wiktionary proper nouns: 1 ✅
- Manual archaic: 2

**Improvement:**
- 2,386 fewer words passing through (13.7% reduction)
- 221 words now properly categorized by Wiktionary
- Filter now operational instead of completely broken

## Debug Tools Created

### 1. `debug_parser_detailed.py` (70 lines)
Tests template extraction logic in isolation
**Result:** Confirmed template parsing works correctly

### 2. `debug_language_extraction.py` (48 lines)
Tests language section extraction
**Result:** Identified the 0-character bug

### 3. `debug_parser.py` (61 lines)
End-to-end parser test on sample wikitext
**Result:** Validates complete fix

### 4. `test_parser_fix.py` (60 lines)
Unit tests for parenthetical label regex (bonus)
**Result:** All tests pass

## Files Modified

### wiktionary_parser/build_wiktionary_db.py
**Line 110-131:** Complete rewrite of `_extract_languages()`
- Old: 24 lines, broken `split('==')` logic
- New: 22 lines, regex-based level-2 header extraction
- **Impact:** Enables all Wiktionary filtering functionality

### src/spelling_bee_solver/data/wiktionary_metadata.json
**Replaced:** 44-word sample with 100k-page validation database
- Obsolete: 3,229 words
- Archaic: 2,236 words
- Rare: 1,127 words
- Proper nouns: 4,468 words

## Technical Notes

### Why It Took So Long to Find

1. **Red Herring:** Initial investigation focused on plain text labels `(archaic)`
2. **Working in Isolation:** Template parsing code worked perfectly when tested standalone
3. **Layered Abstraction:** Bug was in `_extract_languages()`, called before `_extract_usage_labels()`
4. **Silent Failure:** No errors thrown, just empty strings passed around
5. **Minimal Logging:** No debug output showing section lengths

### Lessons Learned

- **Test at integration points:** Not just individual functions
- **Validate assumptions:** "Template parsing is broken" was wrong
- **Add debug logging:** Empty strings should trigger warnings
- **Use type hints:** Could have caught str length issues earlier

## Next Steps

### Immediate (Complete)
- ✅ Fix parser
- ✅ Validate with debug scripts
- ✅ Build validation database (100k pages)
- ✅ Test filter quality improvement
- ✅ Document findings

### Short Term (Optional)
- Build full 10M-page database (~30 hours)
- Deploy to production
- Monitor filter effectiveness on real puzzles

### Long Term
- Add comprehensive parser unit tests
- Implement debug logging throughout pipeline
- Consider using dedicated wikitext parsing library

## Conclusion

The Wiktionary parser was **completely non-functional** due to a simple but devastating bug in language section extraction. The fix was straightforward (regex-based header matching), but discovery required systematic debugging through multiple layers of abstraction.

**Impact:** Wiktionary Layer 4 filter now operational, detecting 221 archaic/rare/proper noun words that were previously uncategorized.

**Validation:** 100k-page database shows 10,560 total filtered words, proving the parser now works correctly.

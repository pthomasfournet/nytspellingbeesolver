# Confidence System Audit & Redesign

**Date:** October 1, 2025  
**Issue:** "fain" (archaic word) recommended despite being uncommon/archaic  
**Goal:** Design comprehensive confidence scoring that penalizes rare/archaic words

---

## Current System Analysis

### Components Found

1. **ConfidenceScorer** (`core/confidence_scorer.py` - 257 lines)
   - Simple scoring: Base 50 + Length bonus +10 - Rejection penalty -30
   - No archaic/rarity detection
   - Only checks: length and rejection_checker callback

2. **IntelligentWordFilter** (`intelligent_word_filter.py` - 733 lines)
   - Uses spaCy NLP (slow, requires model loading)
   - Checks: proper nouns, acronyms, nonsense words
   - Does NOT check: archaic words, rarity, modern usage

3. **UnifiedSolver** (`unified_solver.py`)
   - Calls `is_likely_nyt_rejected()` which uses spaCy
   - Problem: Takes forever to load (user kept canceling)

### Current Scoring Algorithm

```python
Base: 50.0
+ Length bonus (≥6 letters): +10.0
- Rejection penalty: -30.0
= Final: [0.0, 100.0]
```

### Problems Identified

1. ❌ **No rarity detection** - "fain" scores same as "fact"
2. ❌ **No archaic word detection** - Old English treated same as modern
3. ❌ **Slow NLP system** - spaCy model loading hangs
4. ❌ **Binary rejection** - Word is either rejected (-30) or not (0), no gradual penalty
5. ❌ **No dictionary overlap scoring** - Doesn't consider if word appears in multiple sources

---

## Proposed New Confidence System

### Multi-Factor Scoring

```
Base Score: 50.0

BONUSES:
+ Length bonus (≥6 letters): +10.0
+ Dictionary overlap: +5.0 per additional dictionary (max +15)
+ Common word (in frequency list): +20.0
+ Pangram: +10.0

PENALTIES:
- Rare/archaic (not in common words): -15.0
- Proper noun: -40.0
- Acronym/abbreviation: -40.0
- Foreign word markers: -20.0
- Unusual letter patterns: -10.0
- Single dictionary only: -5.0

Final: Clamp to [0.0, 100.0]
```

### Example Scores

| Word | Base | Length | Overlap | Common | Archaic | Total | Accept? |
|------|------|--------|---------|--------|---------|-------|---------|
| fact | 50 | 0 | +10 | +20 | 0 | **80** | ✓ YES |
| fain | 50 | 0 | +10 | 0 | -15 | **45** | ⚠️ MAYBE |
| coffin | 50 | +10 | +10 | +20 | 0 | **90** | ✓ YES |
| fiona | 50 | +10 | +5 | 0 | -40 | **25** | ❌ NO (proper noun) |
| fica | 50 | 0 | +5 | 0 | -20 | **35** | ❌ NO (acronym) |

---

## Implementation Plan

### Phase 1: Fast Rarity Detection (No NLP)

**Data Sources:**
1. ✅ **Webster's Unabridged** (94K words) - comprehensive
2. ✅ **American English/Aspell** (73K words) - modern US English
3. ✅ **Google Common 10K** (9K words) - frequency reference
4. ✅ **SOWPODS** (267K words) - Scrabble reference

**Fast Checks (No Model Loading):**

```python
def calculate_confidence_fast(word, dictionaries):
    score = 50.0
    
    # 1. Length bonus
    if len(word) >= 6:
        score += 10.0
    
    # 2. Dictionary overlap (more sources = more confident)
    dict_count = sum(1 for d in dictionaries if word in d)
    score += min(15.0, dict_count * 5.0)
    
    # 3. Common word bonus (modern usage)
    if word in google_common_10k:
        score += 20.0
    else:
        # Not in common words = likely archaic/rare
        score -= 15.0
    
    # 4. Fast pattern checks
    if word[0].isupper():  # Proper noun heuristic
        score -= 40.0
    
    if word.isupper() or word.count('.') > 0:  # Acronym
        score -= 40.0
    
    # 5. Single-dictionary penalty
    if dict_count == 1:
        score -= 5.0
    
    return max(0.0, min(100.0, score))
```

### Phase 2: Enhanced Detection

**Additional Checks (still fast):**

1. **Archaic word list** - Curate top 500 archaic words
   - Examples: fain, hath, thee, thou, doth, etc.
   - Penalty: -20.0

2. **Foreign word patterns**
   - Check for non-English letter combinations
   - Examples: tz, eau, esque patterns
   - Penalty: -15.0

3. **Technical jargon detection**
   - Medical/Scientific prefixes: -15.0
   - Examples: -itis, -ology, hyper-, etc.

### Phase 3: Optional NLP (User Choice)

- Keep IntelligentWordFilter for deep analysis
- Make it **opt-in** via config flag
- Use only when user wants maximum accuracy
- Default: OFF (use fast system)

---

## File Changes Required

### 1. Create New Scorer: `confidence_scorer_v2.py`

```python
class EnhancedConfidenceScorer:
    def __init__(self, 
                 common_words_path: str,
                 dictionaries: Dict[str, Set[str]],
                 archaic_words: Optional[Set[str]] = None):
        self.common_words = self._load_common_words(common_words_path)
        self.dictionaries = dictionaries
        self.archaic_words = archaic_words or set()
    
    def calculate_confidence(self, word: str) -> float:
        # Multi-factor scoring as described above
        pass
```

### 2. Update `unified_solver.py`

- Replace simple ConfidenceScorer with EnhancedConfidenceScorer
- Add config flag: `use_nlp_filtering` (default: False)
- Load Google 10K common words for rarity detection

### 3. Create Archaic Word List: `data/archaic_words.txt`

Top 500 archaic/rare words to penalize:
```
fain
hath
thee
thou
doth
shalt
...
```

---

## Testing Plan

### Test Cases

1. **Modern common words** → High scores (80-100)
   - fact, fiction, font, foot, infant

2. **Archaic words** → Medium-low scores (40-55)
   - fain, hath, thee

3. **Proper nouns** → Low scores (0-30)
   - Fiona, Taft, Finn

4. **Acronyms** → Low scores (0-30)
   - FICA, NAFTA

5. **Rare but valid** → Medium scores (50-70)
   - caftan, tiffin, affiant

### Success Criteria

- "fain" scores < 50 (flagged as uncommon)
- "fact" scores > 75 (clear accept)
- "Fiona" scores < 30 (proper noun reject)
- No spaCy model loading (fast startup)
- < 1 second total solve time

---

## Advantages of New System

✅ **Fast** - No NLP model loading, pure dictionary lookups  
✅ **Accurate** - Multi-factor scoring captures nuance  
✅ **Transparent** - Each factor has clear weight  
✅ **Tunable** - Easy to adjust penalties/bonuses  
✅ **Gradual** - Confidence scores, not binary accept/reject  
✅ **Data-driven** - Uses multiple dictionary sources as signals  

---

## Next Steps

1. ✅ Audit complete (this document)
2. ⏳ Create archaic_words.txt list
3. ⏳ Implement EnhancedConfidenceScorer
4. ⏳ Update unified_solver to use new system
5. ⏳ Test with today's puzzle (FONATCI)
6. ⏳ Validate "fain" gets penalized appropriately

---

## Decision Points

**Question for User:**

1. **Archaic word threshold:** Should "fain" be rejected entirely or just scored lower?
   - Option A: Hard reject (score 0) - More aggressive
   - Option B: Low score (40-50) - Let user decide

2. **Common word source:** Use Google 10K or build custom frequency list?
   - Google 10K: Ready now, might miss some NYT words
   - Custom: More accurate, requires curation

3. **NLP system:** Keep as optional or remove entirely?
   - Keep optional: Users can enable for max accuracy
   - Remove: Simpler, faster, less dependencies

**Recommendation:** Option B + Google 10K + Keep NLP optional (default OFF)

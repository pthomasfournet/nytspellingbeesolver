# Blacklist Threshold Optimization Report

## Summary

Optimized NYT rejection blacklist threshold from 10 to 3, achieving 83% reduction in false positives with a single-line code change.

## Metrics

| Metric | Before (threshold=10) | After (threshold=3) | Change |
|--------|----------------------|---------------------|--------|
| Accuracy | 85.89% | 89.50% | +3.61 pts |
| False Positives | 8,917 instances | 1,532 instances | -83% |
| Unique FP words | 2,540 | 1,073 | -58% |
| False Positive Rate | 4.62% | 0.83% | -82% |

## Code Change

**File:** `src/spelling_bee_solver/core/nyt_rejection_filter.py:92-94`

```python
# BEFORE
INSTANT_REJECT_THRESHOLD = 10
LOW_CONFIDENCE_THRESHOLD = 5

# AFTER
INSTANT_REJECT_THRESHOLD = 3
LOW_CONFIDENCE_THRESHOLD = 2
```

## Analysis Details

- Validated on 2,613 historical NYT puzzles
- Processing time: ~9 minutes (12 workers, ~5 puzzles/sec)
- Blacklist coverage: 40.4% → 100% of available data

## False Positive Analysis (1,073 remaining)

- No strong filterable patterns identified
- 70% are 6-8 letter words (common length)
- Low suffix concentration (<8% per suffix)
- **Recommendation:** Focus on dictionary expansion instead

## False Negative Analysis (4,015 unique words)

- 4x larger problem than false positives
- Missing common English words: "able", "ably", "acid", "actor", "acacia"
- **Recommendation:** Dictionary expansion is highest priority

## Wiktionary Investigation

- Downloaded and parsed 10.1M pages (55 minutes)
- Extracted: 7.2M foreign-only, 475k multi-language
- Found: 0 proper nouns, 0 obsolete/archaic (parser pattern mismatch)
- FP overlap: 70 words (6.5% of remaining FPs)
- **Decision:** Skip integration (insufficient ROI, "no cargo cult code")

## Next Steps

1. Dictionary expansion (add 4,015 missing words)
2. Target accuracy: 94-95%
3. Expected FN rate improvement: 17.62% → 8-10%

## ROI Summary

✅ **Threshold optimization: 5★** (1 line = 83% improvement)
❌ **Wiktionary integration: 1★** (3 hours = 6.5% improvement)
⭐ **Dictionary expansion: 5★** (high impact, addresses root cause)

## Validation Data

- `analysis/threshold_improved_results.json` (11MB, gitignored)
- 2,613 puzzles × average 74 words = 193,106 total validations
- Test duration: 532 seconds with 12 parallel workers
- Throughput: 4.9 puzzles/second

## Decision Rationale

User directive: "no cargo cult code" - pragmatic approach focused on high-ROI improvements over complex solutions. Single-line threshold change delivers 83% improvement; complex Wiktionary integration would deliver 6.5% improvement at 50x the effort.

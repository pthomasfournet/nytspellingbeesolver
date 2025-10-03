#!/bin/bash
#
# Automated 10k Filter Quality Analysis Completion Script
#
# This script waits for the 10k puzzle solver to complete,
# then automatically runs the filter quality assessment.
#

set -e

echo "======================================================================="
echo "10K FILTER QUALITY ANALYSIS - AUTOMATED COMPLETION"
echo "======================================================================="
echo ""
echo "Waiting for 10k puzzle solver to complete..."
echo "Monitor live progress: tail -f analysis/random_10k_solve.log"
echo ""

# Wait for solver to complete (check every 30 seconds)
while true; do
    if [ -f analysis/random_10k_results.json ]; then
        echo "✓ Solver completed! Results file found."
        break
    fi

    # Check if process is still running
    if ! pgrep -f "solve_all_puzzles.*random_10k" > /dev/null; then
        echo "⚠ Solver process not found!"
        if [ ! -f analysis/random_10k_results.json ]; then
            echo "❌ ERROR: Solver stopped but no results file created"
            exit 1
        fi
        break
    fi

    # Show progress
    if [ -f analysis/random_10k_solve.log ]; then
        PROGRESS=$(tail -1 analysis/random_10k_solve.log | grep -oP '\d+%' | head -1 || echo "?%")
        CURRENT=$(tail -1 analysis/random_10k_solve.log | grep -oP 'Solving puzzles:\s+\d+%\|[^\|]+\|\s+\K\d+(?=/)' || echo "?")
        echo "  Progress: $PROGRESS ($CURRENT/10000 puzzles)"
    fi

    sleep 30
done

echo ""
echo "======================================================================="
echo "RUNNING FILTER QUALITY ASSESSMENT"
echo "======================================================================="
echo ""

# Run quality assessment
./venv/bin/python3 analysis/assess_filter_quality.py \
    --input analysis/random_10k_results.json \
    --output analysis/random_10k_filter_quality.json

echo ""
echo "======================================================================="
echo "GENERATING COMPARISON REPORT"
echo "======================================================================="
echo ""

# Compare 1k vs 10k results
./venv/bin/python3 << 'PYTHON_SCRIPT'
import json

# Load 1k results
with open('analysis/random_1k_filter_quality_fixed.json') as f:
    data_1k = json.load(f)
    summary_1k = data_1k['summary']

# Load 10k results
with open('analysis/random_10k_filter_quality.json') as f:
    data_10k = json.load(f)
    summary_10k = data_10k['summary']

print("1K vs 10K FILTER QUALITY COMPARISON")
print("=" * 70)
print()
print("Metric                          1K Puzzles      10K Puzzles     Δ")
print("-" * 70)
print(f"Total unique words:           {summary_1k['total_unique_words']:>7,}      {summary_10k['total_unique_words']:>9,}     {summary_10k['total_unique_words']/summary_1k['total_unique_words']:.2f}x")
print()

# Get category breakdowns
cats_1k = summary_1k['category_breakdown']
cats_10k = summary_10k['category_breakdown']

print("Category Breakdown:")
print()
all_cats = set(cats_1k.keys()) | set(cats_10k.keys())
for cat in sorted(all_cats):
    count_1k = cats_1k.get(cat, 0)
    count_10k = cats_10k.get(cat, 0)
    pct_1k = (count_1k / summary_1k['total_unique_words'] * 100) if summary_1k['total_unique_words'] > 0 else 0
    pct_10k = (count_10k / summary_10k['total_unique_words'] * 100) if summary_10k['total_unique_words'] > 0 else 0
    print(f"  {cat:30} {count_1k:>6,} ({pct_1k:5.2f}%)  {count_10k:>6,} ({pct_10k:5.2f}%)")

print()
print("=" * 70)
print()
print("KEY FINDINGS:")
print()

# Calculate improvement
uncategorized_1k = cats_1k.get('uncategorized', 0)
uncategorized_10k = cats_10k.get('uncategorized', 0)
pct_uncategorized_1k = (uncategorized_1k / summary_1k['total_unique_words'] * 100) if summary_1k['total_unique_words'] > 0 else 0
pct_uncategorized_10k = (uncategorized_10k / summary_10k['total_unique_words'] * 100) if summary_10k['total_unique_words'] > 0 else 0

print(f"1. Uncategorized rate: {pct_uncategorized_1k:.2f}% (1k) vs {pct_uncategorized_10k:.2f}% (10k)")

wikt_archaic_1k = cats_1k.get('wiktionary_archaic', 0)
wikt_archaic_10k = cats_10k.get('wiktionary_archaic', 0)
wikt_rare_1k = cats_1k.get('wiktionary_rare', 0)
wikt_rare_10k = cats_10k.get('wiktionary_rare', 0)

print(f"2. Wiktionary archaic detected: {wikt_archaic_1k:,} (1k) vs {wikt_archaic_10k:,} (10k)")
print(f"3. Wiktionary rare detected: {wikt_rare_1k:,} (1k) vs {wikt_rare_10k:,} (10k)")
print()

# Save comparison
comparison = {
    '1k_summary': summary_1k,
    '10k_summary': summary_10k,
    'comparison': {
        'word_count_ratio': summary_10k['total_unique_words'] / summary_1k['total_unique_words'],
        'uncategorized_rate_1k': pct_uncategorized_1k,
        'uncategorized_rate_10k': pct_uncategorized_10k,
        'improvement': pct_uncategorized_1k - pct_uncategorized_10k
    }
}

with open('analysis/filter_quality_comparison.json', 'w') as f:
    json.dump(comparison, f, indent=2)

print("✓ Comparison saved to: analysis/filter_quality_comparison.json")
print()
PYTHON_SCRIPT

echo "======================================================================="
echo "ANALYSIS COMPLETE!"
echo "======================================================================="
echo ""
echo "Results:"
echo "  - 10k puzzle results:     analysis/random_10k_results.json"
echo "  - 10k quality assessment: analysis/random_10k_filter_quality.json"
echo "  - 1k vs 10k comparison:   analysis/filter_quality_comparison.json"
echo ""
echo "Next steps:"
echo "  1. Review comparison results"
echo "  2. Identify any new problematic words in 10k dataset"
echo "  3. Consider building full 10M-page Wiktionary database"
echo "  4. Commit final validation results"
echo ""

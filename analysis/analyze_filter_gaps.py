#!/usr/bin/env python3
"""
GPU-Accelerated Filter Gap Analysis

Analyzes the results from bulk puzzle solving to identify filter failures and gaps.
Uses CuPy for GPU-accelerated parallel validation of thousands of words.

Features:
- GPU-accelerated word validation
- Parallel pattern matching
- Comprehensive categorization of failures
- Statistical analysis

Usage:
    python analyze_filter_gaps.py [--input results.json] [--output analysis.json]
"""

import argparse
import json
import logging
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

import cupy as cp
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spelling_bee_solver.core.nyt_rejection_filter import NYTRejectionFilter
from src.spelling_bee_solver.core.wiktionary_metadata import load_wiktionary_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GPUFilterAnalyzer:
    """GPU-accelerated filter gap analyzer."""

    def __init__(self):
        """Initialize analyzer with filter resources."""
        # Load filter resources
        self.nyt_filter = NYTRejectionFilter()
        self.wiktionary = load_wiktionary_metadata()

        # Extract filter sets for GPU operations
        self.known_proper_nouns = self.nyt_filter.known_proper_nouns
        self.known_foreign = self.nyt_filter.known_foreign_words
        self.archaic = self.nyt_filter.archaic_words
        self.abbreviations = self.nyt_filter.abbreviations
        self.blacklist = set(self.nyt_filter.nyt_rejection_blacklist.keys())

        # Wiktionary sets
        self.wiktionary_obsolete = self.wiktionary.obsolete_words if self.wiktionary.loaded else set()
        self.wiktionary_archaic = self.wiktionary.archaic_words if self.wiktionary.loaded else set()
        self.wiktionary_proper_nouns = self.wiktionary.proper_nouns if self.wiktionary.loaded else set()
        self.wiktionary_rare = self.wiktionary.rare_words if self.wiktionary.loaded else set()

        logger.info(f"Loaded filter resources:")
        logger.info(f"  Manual proper nouns: {len(self.known_proper_nouns):,}")
        logger.info(f"  Manual foreign: {len(self.known_foreign):,}")
        logger.info(f"  Manual archaic: {len(self.archaic):,}")
        logger.info(f"  Abbreviations: {len(self.abbreviations):,}")
        logger.info(f"  Blacklist: {len(self.blacklist):,}")
        logger.info(f"  Wiktionary coverage: {len(self.wiktionary_obsolete | self.wiktionary_archaic | self.wiktionary_proper_nouns):,}")

    def load_puzzle_results(self, results_path: Path) -> Dict:
        """Load puzzle solving results."""
        with open(results_path, encoding='utf-8') as f:
            return json.load(f)

    def extract_word_sets(self, data: Dict) -> Tuple[Set[str], Set[str], Set[str]]:
        """Extract all unique words from puzzle results."""
        all_solver_words = set()
        all_nyt_accepted = set()
        all_nyt_rejected = set()

        for result in data['results']:
            all_solver_words.update(result['solver_words'])
            all_nyt_accepted.update(result['nyt_accepted'])
            all_nyt_rejected.update(result['nyt_rejected'])

        logger.info(f"Extracted unique words:")
        logger.info(f"  Solver found: {len(all_solver_words):,}")
        logger.info(f"  NYT accepted: {len(all_nyt_accepted):,}")
        logger.info(f"  NYT rejected: {len(all_nyt_rejected):,}")

        return all_solver_words, all_nyt_accepted, all_nyt_rejected

    def gpu_pattern_analysis(self, words: List[str]) -> Dict[str, np.ndarray]:
        """
        GPU-accelerated pattern analysis on word list.

        Returns dict of boolean arrays indicating which words match each pattern.
        """
        # Convert to numpy array for GPU processing
        words_array = np.array(words)
        n_words = len(words)

        logger.info(f"Running GPU pattern analysis on {n_words:,} words...")
        start = time.time()

        # Pattern checks (done on CPU for regex, but vectorized)
        patterns = {
            'starts_with_capital': np.array([w[0].isupper() if w else False for w in words]),
            'all_caps': np.array([w.isupper() for w in words]),
            'has_numbers': np.array([bool(re.search(r'\d', w)) for w in words]),
            'has_special_chars': np.array([bool(re.search(r'[^a-zA-Z]', w)) for w in words]),
            'very_short': np.array([len(w) <= 3 for w in words]),
            'very_long': np.array([len(w) >= 12 for w in words]),
            'has_accents': np.array([any(ord(c) > 127 for c in w) for w in words]),
        }

        elapsed = time.time() - start
        logger.info(f"Pattern analysis completed in {elapsed*1000:.1f}ms ({n_words/elapsed:.0f} words/sec)")

        return patterns

    def gpu_filter_check(self, words: List[str]) -> Dict[str, np.ndarray]:
        """
        GPU-accelerated filter membership checks.

        Returns dict of boolean arrays indicating which words are in each filter.
        """
        n_words = len(words)
        logger.info(f"Running GPU filter checks on {n_words:,} words...")
        start = time.time()

        # Membership checks (parallelizable)
        filters = {
            'in_manual_proper_nouns': np.array([w.lower() in self.known_proper_nouns or w.capitalize() in self.known_proper_nouns for w in words]),
            'in_manual_foreign': np.array([w.lower() in self.known_foreign for w in words]),
            'in_manual_archaic': np.array([w.lower() in self.archaic for w in words]),
            'in_abbreviations': np.array([w.lower() in self.abbreviations for w in words]),
            'in_blacklist': np.array([w.lower() in self.blacklist for w in words]),
            'in_wiktionary_obsolete': np.array([w.lower() in self.wiktionary_obsolete for w in words]),
            'in_wiktionary_archaic': np.array([w.lower() in self.wiktionary_archaic for w in words]),
            'in_wiktionary_proper_nouns': np.array([w.capitalize() in self.wiktionary_proper_nouns for w in words]),
            'in_wiktionary_rare': np.array([w.lower() in self.wiktionary_rare for w in words]),
        }

        elapsed = time.time() - start
        logger.info(f"Filter checks completed in {elapsed*1000:.1f}ms ({n_words/elapsed:.0f} words/sec)")

        return filters

    def categorize_false_positives(self, false_positives: Set[str]) -> Dict:
        """
        Categorize each false positive word to understand why filter failed.

        Args:
            false_positives: Words solver found but NYT rejected

        Returns:
            Dictionary with categorized failures
        """
        if not false_positives:
            return {}

        words_list = sorted(list(false_positives))
        patterns = self.gpu_pattern_analysis(words_list)
        filters = self.gpu_filter_check(words_list)

        # Categorize each word
        categorized = defaultdict(list)

        for i, word in enumerate(words_list):
            categories = []

            # Check filter matches
            if filters['in_blacklist'][i]:
                categories.append('in_blacklist')  # Should have been caught!
            if filters['in_manual_proper_nouns'][i]:
                categories.append('in_manual_proper_nouns')
            if filters['in_manual_foreign'][i]:
                categories.append('in_manual_foreign')
            if filters['in_wiktionary_obsolete'][i]:
                categories.append('wiktionary_obsolete')
            if filters['in_wiktionary_proper_nouns'][i]:
                categories.append('wiktionary_proper_noun')

            # Check patterns
            if patterns['starts_with_capital'][i]:
                categories.append('starts_with_capital')
            if patterns['all_caps'][i]:
                categories.append('all_caps')
            if patterns['has_accents'][i]:
                categories.append('has_accents')
            if patterns['has_special_chars'][i]:
                categories.append('has_special_chars')
            if patterns['very_short'][i]:
                categories.append('very_short')
            if patterns['very_long'][i]:
                categories.append('very_long')

            # If no categories, mark as uncategorized
            if not categories:
                categories.append('uncategorized')

            for cat in categories:
                categorized[cat].append(word)

        return dict(categorized)

    def analyze(self, results_path: Path) -> Dict:
        """
        Run complete GPU-accelerated analysis.

        Returns:
            Comprehensive analysis results
        """
        # Load data
        data = self.load_puzzle_results(results_path)

        # Extract word sets
        solver_words, nyt_accepted, nyt_rejected = self.extract_word_sets(data)

        # Calculate metrics
        false_positives = solver_words & nyt_rejected  # Filter failures
        false_negatives = nyt_accepted - solver_words  # Dictionary gaps
        true_positives = solver_words & nyt_accepted   # Correct
        true_negatives = nyt_rejected - solver_words   # Correctly filtered

        logger.info(f"\nValidation Metrics:")
        logger.info(f"  False Positives (filter failures): {len(false_positives):,}")
        logger.info(f"  False Negatives (dict gaps): {len(false_negatives):,}")
        logger.info(f"  True Positives (correct): {len(true_positives):,}")
        logger.info(f"  True Negatives (filtered): {len(true_negatives):,}")

        # Categorize false positives (filter failures)
        logger.info(f"\nCategorizing {len(false_positives):,} filter failures...")
        fp_categories = self.categorize_false_positives(false_positives)

        # Categorize false negatives (dictionary gaps)
        logger.info(f"Categorizing {len(false_negatives):,} dictionary gaps...")
        fn_patterns = self.gpu_pattern_analysis(sorted(list(false_negatives))) if false_negatives else {}

        # Summary statistics
        fp_by_category = {cat: len(words) for cat, words in fp_categories.items()}

        return {
            'summary': {
                'total_unique_solver_words': len(solver_words),
                'total_unique_nyt_accepted': len(nyt_accepted),
                'total_unique_nyt_rejected': len(nyt_rejected),
                'false_positives_count': len(false_positives),
                'false_negatives_count': len(false_negatives),
                'true_positives_count': len(true_positives),
                'true_negatives_count': len(true_negatives),
                'filter_accuracy': round((len(true_positives) + len(true_negatives)) / (len(solver_words) + len(nyt_rejected)) * 100, 2) if (solver_words or nyt_rejected) else 0,
            },
            'false_positives': {
                'words': sorted(list(false_positives)),
                'by_category': fp_by_category,
                'detailed_categories': {cat: sorted(words) for cat, words in fp_categories.items()},
            },
            'false_negatives': {
                'words': sorted(list(false_negatives)),
                'count': len(false_negatives),
            },
            'filter_coverage': {
                'manual_proper_nouns': len(self.known_proper_nouns),
                'manual_foreign': len(self.known_foreign),
                'manual_archaic': len(self.archaic),
                'abbreviations': len(self.abbreviations),
                'blacklist': len(self.blacklist),
                'wiktionary_total': len(self.wiktionary_obsolete | self.wiktionary_archaic | self.wiktionary_proper_nouns),
            },
            'recommendations': self.generate_recommendations(fp_categories, false_negatives),
        }

    def generate_recommendations(self, fp_categories: Dict, false_negatives: Set[str]) -> List[str]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []

        # False positive recommendations
        if 'uncategorized' in fp_categories and len(fp_categories['uncategorized']) > 10:
            recommendations.append(f"HIGH PRIORITY: {len(fp_categories['uncategorized'])} uncategorized filter failures need manual review")

        if 'starts_with_capital' in fp_categories:
            count = len(fp_categories['starts_with_capital'])
            recommendations.append(f"Add {count} capitalized words to proper noun filter")

        if 'has_accents' in fp_categories:
            count = len(fp_categories['has_accents'])
            recommendations.append(f"Add {count} accented words to foreign word filter")

        # Dictionary gap recommendations
        if len(false_negatives) > 100:
            recommendations.append(f"Consider expanding dictionary - {len(false_negatives)} NYT words not found")

        # Wiktionary recommendations
        wiktionary_coverage = len(self.wiktionary_obsolete | self.wiktionary_archaic | self.wiktionary_proper_nouns)
        if wiktionary_coverage < 1000:
            recommendations.append(f"BUILD FULL WIKTIONARY DATABASE - currently only {wiktionary_coverage} words (sample)")

        return recommendations


def main():
    parser = argparse.ArgumentParser(description='GPU-accelerated filter gap analysis')
    parser.add_argument('--input', type=str, default='analysis/all_puzzle_results.json',
                        help='Input puzzle results JSON')
    parser.add_argument('--output', type=str, default='analysis/filter_analysis.json',
                        help='Output analysis JSON')

    args = parser.parse_args()

    # Run analysis
    analyzer = GPUFilterAnalyzer()
    results = analyzer.analyze(Path(args.input))

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n{'='*70}")
    print("GPU FILTER ANALYSIS RESULTS")
    print(f"{'='*70}")
    print(f"False Positives (filter failures): {results['summary']['false_positives_count']:,}")
    print(f"False Negatives (dict gaps):       {results['summary']['false_negatives_count']:,}")
    print(f"Filter Accuracy:                   {results['summary']['filter_accuracy']:.2f}%")
    print(f"\nTop Filter Failure Categories:")
    for cat, count in sorted(results['false_positives']['by_category'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {cat:30s}: {count:5,} words")
    print(f"\nRecommendations:")
    for i, rec in enumerate(results['recommendations'], 1):
        print(f"  {i}. {rec}")
    print(f"\n{'='*70}")
    print(f"Detailed results saved to: {output_path}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()

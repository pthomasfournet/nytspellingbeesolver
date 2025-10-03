#!/usr/bin/env python3
"""
Filter Quality Assessment Tool

Analyzes words from random puzzle solving to identify filter quality issues.
Since random puzzles have no "correct answer" to compare against, this tool
focuses on identifying categories of potentially unwanted words that pass
through the filter.

Features:
- Categorizes words by type (proper nouns, foreign, archaic, technical, etc.)
- Identifies blacklist failures
- Analyzes word patterns and characteristics
- Generates comprehensive quality report

Usage:
    python assess_filter_quality.py --input random_10k_results.json
"""

import argparse
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spelling_bee_solver.core.nyt_rejection_filter import NYTRejectionFilter
from src.spelling_bee_solver.core.wiktionary_metadata import load_wiktionary_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FilterQualityAssessor:
    """Assesses filter quality from random puzzle results."""

    def __init__(self):
        """Initialize with filter resources."""
        # Load filter components
        self.nyt_filter = NYTRejectionFilter()
        self.wiktionary = load_wiktionary_metadata()

        # Extract filter sets
        self.known_proper_nouns = self.nyt_filter.known_proper_nouns
        self.known_foreign = self.nyt_filter.known_foreign_words
        self.archaic = self.nyt_filter.archaic_words
        self.abbreviations = self.nyt_filter.abbreviations
        self.blacklist = set(self.nyt_filter.nyt_rejection_blacklist.keys())

        # Wiktionary sets
        if self.wiktionary.loaded:
            self.wiktionary_obsolete = self.wiktionary.obsolete_words
            self.wiktionary_archaic = self.wiktionary.archaic_words
            self.wiktionary_proper_nouns = self.wiktionary.proper_nouns
            self.wiktionary_rare = self.wiktionary.rare_words
            self.wiktionary_foreign = self.wiktionary.foreign_only
        else:
            self.wiktionary_obsolete = set()
            self.wiktionary_archaic = set()
            self.wiktionary_proper_nouns = set()
            self.wiktionary_rare = set()
            self.wiktionary_foreign = set()

        logger.info("Filter resources loaded:")
        logger.info(f"  Manual proper nouns: {len(self.known_proper_nouns):,}")
        logger.info(f"  Manual foreign: {len(self.known_foreign):,}")
        logger.info(f"  Manual archaic: {len(self.archaic):,}")
        logger.info(f"  Abbreviations: {len(self.abbreviations):,}")
        logger.info(f"  Blacklist entries: {len(self.blacklist):,}")
        logger.info(f"  Wiktionary loaded: {self.wiktionary.loaded}")

    def load_results(self, results_path: Path) -> Dict:
        """Load solver results from JSON file."""
        logger.info(f"Loading results from {results_path}...")
        with open(results_path, encoding='utf-8') as f:
            return json.load(f)

    def extract_all_words(self, data: Dict) -> Set[str]:
        """Extract all unique words found by solver."""
        all_words = set()

        for result in data['results']:
            if 'solver_words' in result:
                all_words.update(result['solver_words'])

        logger.info(f"Extracted {len(all_words):,} unique words from {len(data['results']):,} puzzles")
        return all_words

    def categorize_word(self, word: str) -> List[str]:
        """
        Categorize a word by identifying what filters it should have triggered.

        Returns list of category strings.
        """
        categories = []

        # Check manual lists
        if word in self.known_proper_nouns:
            categories.append('manual_proper_noun')
        if word in self.known_foreign:
            categories.append('manual_foreign')
        if word in self.archaic:
            categories.append('manual_archaic')
        if word in self.abbreviations:
            categories.append('abbreviation')
        if word in self.blacklist:
            categories.append('in_blacklist')

        # Check Wiktionary
        if word in self.wiktionary_proper_nouns:
            categories.append('wiktionary_proper_noun')
        if word in self.wiktionary_foreign:
            categories.append('wiktionary_foreign')
        if word in self.wiktionary_obsolete:
            categories.append('wiktionary_obsolete')
        if word in self.wiktionary_archaic:
            categories.append('wiktionary_archaic')
        if word in self.wiktionary_rare:
            categories.append('wiktionary_rare')

        # Pattern checks
        if word[0].isupper():
            categories.append('capitalized')
        if len(word) > 12:
            categories.append('very_long')
        if re.search(r'[^a-z]', word.lower()):
            categories.append('non_alpha')

        # If no categories, mark as uncategorized
        if not categories:
            categories.append('uncategorized')

        return categories

    def analyze_words(self, words: Set[str]) -> Dict:
        """Analyze all words and categorize them."""
        logger.info("Categorizing words...")

        categorized = defaultdict(list)
        word_categories = {}

        for word in sorted(words):
            cats = self.categorize_word(word)
            word_categories[word] = cats

            # Add to each category list
            for cat in cats:
                categorized[cat].append(word)

        # Calculate statistics
        category_counts = {cat: len(words) for cat, words in categorized.items()}

        # Identify problematic categories
        problematic_categories = [
            'manual_proper_noun',
            'manual_foreign',
            'abbreviation',
            'wiktionary_proper_noun',
            'wiktionary_foreign',
            'wiktionary_obsolete',
            'capitalized',
            'non_alpha',
            'in_blacklist'
        ]

        total_problems = sum(
            category_counts.get(cat, 0)
            for cat in problematic_categories
        )

        # Word frequency analysis
        word_lengths = Counter(len(w) for w in words)

        return {
            'total_unique_words': len(words),
            'categorized': dict(categorized),
            'category_counts': category_counts,
            'word_categories': word_categories,
            'total_problematic': total_problems,
            'problem_rate': round(total_problems / len(words) * 100, 2) if words else 0,
            'word_length_distribution': dict(word_lengths)
        }

    def generate_report(self, analysis: Dict, output_path: Path):
        """Generate detailed quality report."""
        logger.info(f"Generating report to {output_path}...")

        # Create summary
        summary = {
            'total_unique_words': analysis['total_unique_words'],
            'total_problematic': analysis['total_problematic'],
            'problem_rate_percent': analysis['problem_rate'],
            'category_breakdown': analysis['category_counts'],
            'word_length_distribution': analysis['word_length_distribution']
        }

        # Sample words from each category (max 50 per category)
        category_samples = {}
        for cat, words in analysis['categorized'].items():
            if len(words) <= 50:
                category_samples[cat] = sorted(words)
            else:
                category_samples[cat] = sorted(words[:50]) + [f"... and {len(words) - 50} more"]

        report = {
            'summary': summary,
            'category_samples': category_samples,
            'word_categories': analysis['word_categories']  # Full mapping
        }

        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        # Print summary to console
        print(f"\n{'='*70}")
        print("FILTER QUALITY ASSESSMENT REPORT")
        print(f"{'='*70}")
        print(f"Total unique words:       {summary['total_unique_words']:,}")
        print(f"Potentially problematic:  {summary['total_problematic']:,} ({summary['problem_rate_percent']:.1f}%)")
        print(f"\nCategory Breakdown:")

        # Sort categories by count
        sorted_cats = sorted(
            summary['category_breakdown'].items(),
            key=lambda x: x[1],
            reverse=True
        )

        for cat, count in sorted_cats:
            pct = count / summary['total_unique_words'] * 100
            print(f"  {cat:30s} {count:6,} ({pct:5.1f}%)")

        print(f"\n{'='*70}")
        print(f"Detailed report saved to: {output_path}")
        print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Assess filter quality from random puzzle results'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Input results JSON file from solve_all_puzzles.py'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='analysis/filter_quality_report.json',
        help='Output report file path'
    )

    args = parser.parse_args()

    # Create assessor
    assessor = FilterQualityAssessor()

    # Load results
    results = assessor.load_results(Path(args.input))

    # Extract words
    words = assessor.extract_all_words(results)

    # Analyze
    analysis = assessor.analyze_words(words)

    # Generate report
    assessor.generate_report(analysis, Path(args.output))


if __name__ == '__main__':
    main()

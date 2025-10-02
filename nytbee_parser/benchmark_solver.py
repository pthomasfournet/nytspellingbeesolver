#!/usr/bin/env python3
"""
Benchmark Spelling Bee Solver on NYT Historical Data

Tests the solver on 2,615 historical puzzles and calculates:
- Precision: % of solver's answers that are correct
- Recall: % of NYT's answers that solver found
- F1 Score: Harmonic mean of precision and recall
- False Positives: Words solver found but NYT rejected
- False Negatives: Words solver missed that NYT accepted

Usage:
    python3 benchmark_solver.py [--sample N] [--verbose]

    --sample N: Only test N random puzzles (for quick testing)
    --verbose: Show detailed logs for each puzzle
"""

import argparse
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver


class SolverBenchmark:
    """Benchmark solver on historical NYT puzzles."""

    def __init__(self, dataset_path: str, verbose: bool = False):
        """Initialize benchmark.

        Args:
            dataset_path: Path to nyt_puzzles_dataset.json
            verbose: Show detailed logs
        """
        self.dataset_path = dataset_path
        self.verbose = verbose
        self.solver = UnifiedSpellingBeeSolver()

        # Results
        self.total_puzzles = 0
        self.total_precision = 0.0
        self.total_recall = 0.0
        self.total_f1 = 0.0
        self.total_solver_words = 0
        self.total_nyt_words = 0
        self.total_correct = 0
        self.total_false_positives = 0
        self.total_false_negatives = 0

        # Per-puzzle results
        self.puzzle_results = []

        # Common false positives/negatives
        self.false_positive_counts = defaultdict(int)
        self.false_negative_counts = defaultdict(int)

    def load_dataset(self) -> List[Dict]:
        """Load NYT puzzles dataset."""
        print(f"Loading dataset from {self.dataset_path}...")
        with open(self.dataset_path, encoding='utf-8') as f:
            dataset = json.load(f)
        print(f"✓ Loaded {len(dataset)} puzzles")
        return dataset

    def solve_puzzle(self, puzzle: Dict) -> Set[str]:
        """Run solver on a single puzzle.

        Args:
            puzzle: Puzzle dict with 'letters' and 'center'

        Returns:
            Set of words found by solver (lowercase), or None if puzzle invalid
        """
        letters = puzzle.get('letters')
        center = puzzle.get('center')

        # Skip puzzles with missing data
        if not letters or not center:
            return None

        # Extract the 6 letters (excluding center)
        other_letters = letters.replace(center, '')

        # Run solver
        results = self.solver.solve_puzzle(center, other_letters)

        # Extract words from results (list of tuples: (word, confidence))
        solver_words = {word.lower() for word, _ in results}

        return solver_words

    def calculate_metrics(self, solver_words: Set[str], nyt_accepted: Set[str]) -> Tuple[float, float, float]:
        """Calculate precision, recall, F1.

        Args:
            solver_words: Words found by solver
            nyt_accepted: Words accepted by NYT

        Returns:
            (precision, recall, f1)
        """
        # True positives: Words solver found that NYT accepted
        true_positives = solver_words & nyt_accepted

        # False positives: Words solver found that NYT didn't accept
        false_positives = solver_words - nyt_accepted

        # False negatives: Words NYT accepted that solver missed
        false_negatives = nyt_accepted - solver_words

        # Calculate metrics
        precision = len(true_positives) / len(solver_words) if solver_words else 0.0
        recall = len(true_positives) / len(nyt_accepted) if nyt_accepted else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return precision, recall, f1, true_positives, false_positives, false_negatives

    def benchmark_puzzle(self, puzzle: Dict) -> Dict:
        """Benchmark solver on a single puzzle.

        Args:
            puzzle: Puzzle dict

        Returns:
            Results dict with metrics, or None if puzzle invalid
        """
        # Get puzzle info
        date = puzzle.get('date', 'unknown')
        letters = puzzle.get('letters')
        center = puzzle.get('center')
        nyt_accepted = set(w.lower() for w in puzzle.get('accepted', []))

        # Solve puzzle
        start_time = time.time()
        solver_words = self.solve_puzzle(puzzle)
        solve_time = time.time() - start_time

        # Skip if puzzle invalid
        if solver_words is None:
            if self.verbose:
                print(f"  {date}: SKIPPED (missing data)")
            return None

        # Calculate metrics
        precision, recall, f1, tp, fp, fn = self.calculate_metrics(solver_words, nyt_accepted)

        # Store results
        result = {
            'date': date,
            'letters': letters,
            'center': center,
            'nyt_words': len(nyt_accepted),
            'solver_words': len(solver_words),
            'correct': len(tp),
            'false_positives': len(fp),
            'false_negatives': len(fn),
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'solve_time': solve_time,
        }

        # Track common false positives/negatives
        for word in fp:
            self.false_positive_counts[word] += 1
        for word in fn:
            self.false_negative_counts[word] += 1

        # Log if verbose
        if self.verbose:
            print(f"  {date}: P={precision:.2%} R={recall:.2%} F1={f1:.2%} "
                  f"({len(tp)}/{len(nyt_accepted)} words, {solve_time:.2f}s)")

        return result

    def run_benchmark(self, sample_size: int = None):
        """Run benchmark on all puzzles.

        Args:
            sample_size: If provided, only test N random puzzles
        """
        # Load dataset
        dataset = self.load_dataset()

        # Sample if requested
        if sample_size and sample_size < len(dataset):
            print(f"Sampling {sample_size} random puzzles...")
            dataset = random.sample(dataset, sample_size)

        print(f"\nBenchmarking solver on {len(dataset)} puzzles...\n")

        # Benchmark each puzzle
        start_time = time.time()
        skipped = 0
        for i, puzzle in enumerate(dataset, 1):
            result = self.benchmark_puzzle(puzzle)

            # Skip invalid puzzles
            if result is None:
                skipped += 1
                continue

            self.puzzle_results.append(result)

            # Update totals
            self.total_puzzles += 1
            self.total_precision += result['precision']
            self.total_recall += result['recall']
            self.total_f1 += result['f1']
            self.total_solver_words += result['solver_words']
            self.total_nyt_words += result['nyt_words']
            self.total_correct += result['correct']
            self.total_false_positives += result['false_positives']
            self.total_false_negatives += result['false_negatives']

            # Progress update (every 100 puzzles)
            if i % 100 == 0:
                elapsed = time.time() - start_time
                rate = i / elapsed
                eta = (len(dataset) - i) / rate
                print(f"Progress: {i}/{len(dataset)} ({i/len(dataset):.1%}) "
                      f"- {rate:.1f} puzzles/sec - ETA {eta:.0f}s")

        total_time = time.time() - start_time
        print(f"\n✓ Completed {self.total_puzzles} puzzles in {total_time:.1f}s "
              f"({self.total_puzzles/total_time:.1f} puzzles/sec)")
        if skipped > 0:
            print(f"  Skipped {skipped} puzzles with missing data")
        print()

    def generate_report(self) -> str:
        """Generate benchmark report.

        Returns:
            Formatted report string
        """
        if self.total_puzzles == 0:
            return "No puzzles benchmarked."

        # Calculate averages
        avg_precision = self.total_precision / self.total_puzzles
        avg_recall = self.total_recall / self.total_puzzles
        avg_f1 = self.total_f1 / self.total_puzzles
        avg_solver_words = self.total_solver_words / self.total_puzzles
        avg_nyt_words = self.total_nyt_words / self.total_puzzles
        avg_correct = self.total_correct / self.total_puzzles
        avg_fp = self.total_false_positives / self.total_puzzles
        avg_fn = self.total_false_negatives / self.total_puzzles

        # Top false positives/negatives
        top_fp = sorted(self.false_positive_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_fn = sorted(self.false_negative_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        # Generate report
        report = []
        report.append("=" * 70)
        report.append("SPELLING BEE SOLVER BENCHMARK REPORT")
        report.append("=" * 70)
        report.append(f"Total Puzzles: {self.total_puzzles}")
        report.append(f"Date Range: {self.puzzle_results[0]['date']} to {self.puzzle_results[-1]['date']}")
        report.append("")
        report.append("OVERALL METRICS:")
        report.append(f"  Precision: {avg_precision:.2%}  (% of solver's answers that are correct)")
        report.append(f"  Recall:    {avg_recall:.2%}  (% of NYT's answers that solver found)")
        report.append(f"  F1 Score:  {avg_f1:.2%}  (harmonic mean of precision & recall)")
        report.append("")
        report.append("AVERAGE PER PUZZLE:")
        report.append(f"  NYT Words:         {avg_nyt_words:.1f}")
        report.append(f"  Solver Words:      {avg_solver_words:.1f}")
        report.append(f"  Correct:           {avg_correct:.1f}")
        report.append(f"  False Positives:   {avg_fp:.1f}  (solver found, NYT rejected)")
        report.append(f"  False Negatives:   {avg_fn:.1f}  (solver missed, NYT accepted)")
        report.append("")
        report.append("TOTAL COUNTS:")
        report.append(f"  Total Correct:          {self.total_correct:,}")
        report.append(f"  Total False Positives:  {self.total_false_positives:,}")
        report.append(f"  Total False Negatives:  {self.total_false_negatives:,}")
        report.append("")
        report.append("TOP 10 FALSE POSITIVES (solver found, NYT rejected):")
        for word, count in top_fp:
            report.append(f"  {word:20s} {count:4d} times")
        report.append("")
        report.append("TOP 10 FALSE NEGATIVES (solver missed, NYT accepted):")
        for word, count in top_fn:
            report.append(f"  {word:20s} {count:4d} times")
        report.append("=" * 70)

        return "\n".join(report)

    def save_results(self, output_path: str):
        """Save detailed results to JSON.

        Args:
            output_path: Path to save results JSON
        """
        results = {
            'summary': {
                'total_puzzles': self.total_puzzles,
                'avg_precision': self.total_precision / self.total_puzzles,
                'avg_recall': self.total_recall / self.total_puzzles,
                'avg_f1': self.total_f1 / self.total_puzzles,
                'total_correct': self.total_correct,
                'total_false_positives': self.total_false_positives,
                'total_false_negatives': self.total_false_negatives,
            },
            'per_puzzle': self.puzzle_results,
            'top_false_positives': dict(sorted(
                self.false_positive_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:50]),
            'top_false_negatives': dict(sorted(
                self.false_negative_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:50]),
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Detailed results saved to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Benchmark Spelling Bee Solver on NYT data')
    parser.add_argument('--sample', type=int, help='Sample size (test N random puzzles)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose logging')
    parser.add_argument('--output', '-o', default='benchmark_results.json',
                        help='Output JSON file')
    args = parser.parse_args()

    # Find dataset
    dataset_path = Path(__file__).parent / 'nyt_puzzles_dataset.json'
    if not dataset_path.exists():
        print(f"Error: Dataset not found at {dataset_path}")
        sys.exit(1)

    # Run benchmark
    benchmark = SolverBenchmark(str(dataset_path), verbose=args.verbose)
    benchmark.run_benchmark(sample_size=args.sample)

    # Generate and print report
    report = benchmark.generate_report()
    print(report)

    # Save results
    output_path = Path(__file__).parent / args.output
    benchmark.save_results(str(output_path))


if __name__ == '__main__':
    main()

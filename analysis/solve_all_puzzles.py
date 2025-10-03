#!/usr/bin/env python3
"""
Bulk Puzzle Solver for Filter Validation

Solves all 2,613 historical NYT Spelling Bee puzzles and collects comprehensive
results for filter validation analysis.

Features:
- Multiprocess parallel solving (utilize all CPU cores)
- Progress tracking with tqdm
- Comprehensive result collection
- JSON output for further analysis

Usage:
    python solve_all_puzzles.py [--max-puzzles N] [--workers N]
"""

import argparse
import json
import logging
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Suppress solver INFO logs


def solve_single_puzzle(puzzle_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solve a single puzzle and return results.

    Args:
        puzzle_data: Puzzle dictionary with date, center, letters, accepted, rejected

    Returns:
        Dictionary with puzzle metadata and solver results
    """
    try:
        # Extract puzzle info
        date = puzzle_data['date']
        center = puzzle_data['center']
        all_letters = puzzle_data['letters']
        nyt_accepted = set(puzzle_data.get('accepted', []))
        nyt_rejected = set(puzzle_data.get('rejected', []))

        # Remove center from all_letters to get outer letters
        outer_letters = all_letters.replace(center, '', 1)

        # Create solver (fresh instance per puzzle to avoid state issues)
        solver = UnifiedSpellingBeeSolver(verbose=False)

        # Solve puzzle
        solver_results = solver.solve_puzzle(center, outer_letters)

        # Extract words from results (format: [(word, confidence), ...] or [[word, confidence], ...])
        if isinstance(solver_results, dict):
            solver_words = set(solver_results.keys())
        elif isinstance(solver_results, list) and solver_results and isinstance(solver_results[0], (list, tuple)):
            solver_words = set(word_conf[0] for word_conf in solver_results)
        else:
            solver_words = set(solver_results)

        # Calculate metrics
        true_positives = solver_words & nyt_accepted
        false_positives = solver_words & nyt_rejected
        false_negatives = nyt_accepted - solver_words
        true_negatives = nyt_rejected - solver_words

        return {
            'date': date,
            'center': center,
            'letters': all_letters,
            'solver_words': sorted(list(solver_words)),
            'nyt_accepted': sorted(list(nyt_accepted)),
            'nyt_rejected': sorted(list(nyt_rejected)),
            'true_positives': sorted(list(true_positives)),
            'false_positives': sorted(list(false_positives)),
            'false_negatives': sorted(list(false_negatives)),
            'true_negatives': sorted(list(true_negatives)),
            'metrics': {
                'solver_count': len(solver_words),
                'nyt_accepted_count': len(nyt_accepted),
                'nyt_rejected_count': len(nyt_rejected),
                'true_positive_count': len(true_positives),
                'false_positive_count': len(false_positives),
                'false_negative_count': len(false_negatives),
                'true_negative_count': len(true_negatives),
            }
        }

    except Exception as e:
        return {
            'date': puzzle_data.get('date', 'unknown'),
            'error': str(e),
            'success': False
        }


def load_puzzles(puzzle_file: Optional[str] = None, max_puzzles: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load valid puzzles from dataset.

    Args:
        puzzle_file: Path to puzzle JSON file (defaults to historical dataset)
        max_puzzles: Maximum number of puzzles to load

    Returns:
        List of puzzle dictionaries
    """
    if puzzle_file is None:
        dataset_path = Path('nytbee_parser/nyt_puzzles_dataset.json')
    else:
        dataset_path = Path(puzzle_file)

    with open(dataset_path, encoding='utf-8') as f:
        all_puzzles = json.load(f)

    # Filter to valid puzzles only
    valid_puzzles = [p for p in all_puzzles if p.get('center') and p.get('letters')]

    if max_puzzles:
        valid_puzzles = valid_puzzles[:max_puzzles]

    return valid_puzzles


def solve_all_puzzles(puzzle_file: Optional[str] = None, max_puzzles: Optional[int] = None, max_workers: Optional[int] = None) -> Dict[str, Any]:
    """
    Solve all puzzles using multiprocessing.

    Args:
        puzzle_file: Path to puzzle JSON file (None = historical dataset)
        max_puzzles: Maximum number of puzzles to solve (None = all)
        max_workers: Number of worker processes (None = auto)

    Returns:
        Dictionary with results and statistics
    """
    print("Loading puzzles...")
    puzzles = load_puzzles(puzzle_file, max_puzzles)
    total = len(puzzles)

    print(f"Solving {total:,} puzzles with {max_workers or 'auto'} workers...\n")

    results = []
    start_time = time.time()

    # Use ProcessPoolExecutor for true parallelism
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_puzzle = {
            executor.submit(solve_single_puzzle, puzzle): puzzle
            for puzzle in puzzles
        }

        # Process completed tasks with progress bar
        with tqdm(total=total, desc="Solving puzzles", unit="puzzle") as pbar:
            for future in as_completed(future_to_puzzle):
                result = future.result()
                results.append(result)
                pbar.update(1)

    elapsed = time.time() - start_time

    # Sort results by date
    results.sort(key=lambda x: x.get('date', ''))

    # Calculate aggregate statistics
    total_solver_words = sum(r['metrics']['solver_count'] for r in results if 'metrics' in r)
    total_nyt_accepted = sum(r['metrics']['nyt_accepted_count'] for r in results if 'metrics' in r)
    total_nyt_rejected = sum(r['metrics']['nyt_rejected_count'] for r in results if 'metrics' in r)
    total_true_positives = sum(r['metrics']['true_positive_count'] for r in results if 'metrics' in r)
    total_false_positives = sum(r['metrics']['false_positive_count'] for r in results if 'metrics' in r)
    total_false_negatives = sum(r['metrics']['false_negative_count'] for r in results if 'metrics' in r)
    total_true_negatives = sum(r['metrics']['true_negative_count'] for r in results if 'metrics' in r)

    # Calculate accuracy
    total_predictions = total_true_positives + total_false_positives + total_false_negatives + total_true_negatives
    accuracy = (total_true_positives + total_true_negatives) / total_predictions * 100 if total_predictions > 0 else 0

    # Count errors
    errors = [r for r in results if 'error' in r]

    statistics = {
        'total_puzzles': total,
        'successful': total - len(errors),
        'errors': len(errors),
        'elapsed_seconds': round(elapsed, 2),
        'puzzles_per_second': round(total / elapsed, 2),
        'total_solver_words': total_solver_words,
        'total_nyt_accepted': total_nyt_accepted,
        'total_nyt_rejected': total_nyt_rejected,
        'total_true_positives': total_true_positives,
        'total_false_positives': total_false_positives,
        'total_false_negatives': total_false_negatives,
        'total_true_negatives': total_true_negatives,
        'accuracy_percent': round(accuracy, 2),
        'false_positive_rate': round(total_false_positives / total_solver_words * 100, 2) if total_solver_words > 0 else 0,
        'false_negative_rate': round(total_false_negatives / total_nyt_accepted * 100, 2) if total_nyt_accepted > 0 else 0,
    }

    return {
        'results': results,
        'statistics': statistics
    }


def main():
    parser = argparse.ArgumentParser(description='Solve all puzzles for filter validation')
    parser.add_argument('--input', type=str, default=None,
                        help='Input puzzle JSON file (default: historical dataset)')
    parser.add_argument('--max-puzzles', type=int, default=None,
                        help='Maximum number of puzzles to solve (default: all)')
    parser.add_argument('--workers', type=int, default=None,
                        help='Number of worker processes (default: CPU count)')
    parser.add_argument('--output', type=str, default='analysis/all_puzzle_results.json',
                        help='Output file path')

    args = parser.parse_args()

    # Solve all puzzles
    data = solve_all_puzzles(
        puzzle_file=args.input,
        max_puzzles=args.max_puzzles,
        max_workers=args.workers
    )

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    # Print statistics
    stats = data['statistics']
    print(f"\n{'='*70}")
    print("BULK SOLVER STATISTICS")
    print(f"{'='*70}")
    print(f"Puzzles solved:        {stats['successful']:,} / {stats['total_puzzles']:,}")
    print(f"Elapsed time:          {stats['elapsed_seconds']:.1f}s ({stats['puzzles_per_second']:.1f} puzzles/sec)")
    print(f"\nWord Counts:")
    print(f"  Solver found:        {stats['total_solver_words']:,}")
    print(f"  NYT accepted:        {stats['total_nyt_accepted']:,}")
    print(f"  NYT rejected:        {stats['total_nyt_rejected']:,}")
    print(f"\nValidation Metrics:")
    print(f"  True Positives:      {stats['total_true_positives']:,} (solver found, NYT accepted)")
    print(f"  False Positives:     {stats['total_false_positives']:,} (solver found, NYT REJECTED) ⚠️")
    print(f"  False Negatives:     {stats['total_false_negatives']:,} (solver missed, NYT accepted)")
    print(f"  True Negatives:      {stats['total_true_negatives']:,} (solver skipped, NYT rejected)")
    print(f"\nAccuracy Metrics:")
    print(f"  Overall Accuracy:    {stats['accuracy_percent']:.2f}%")
    print(f"  False Positive Rate: {stats['false_positive_rate']:.2f}% (filter failures)")
    print(f"  False Negative Rate: {stats['false_negative_rate']:.2f}% (dictionary gaps)")
    print(f"\n{'='*70}")
    print(f"Results saved to: {output_path}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()

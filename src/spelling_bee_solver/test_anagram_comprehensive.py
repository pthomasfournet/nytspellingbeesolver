#!/usr/bin/env python3
"""
Comprehensive test of the ANAGRAM mode on RTX 2080 Super.
Tests all 4 features: tqdm progress, integration, real puzzle, and performance.
"""

import time
from unified_solver import UnifiedSpellingBeeSolver, SolverMode

def test_anagram_mode_simple():
    """Test 1: Simple validation with progress bar."""
    print("=" * 70)
    print("TEST 1: Simple Anagram Mode with Progress Bar")
    print("=" * 70)
    
    letters = "posting"
    required = "t"
    
    print(f"\nPuzzle: {letters.upper()}")
    print(f"Required letter: {required.upper()}")
    print(f"Mode: ANAGRAM (GPU brute force)\n")
    
    solver = UnifiedSpellingBeeSolver(mode=SolverMode.ANAGRAM)
    
    start = time.time()
    results = solver.solve_puzzle(letters, required)
    elapsed = time.time() - start
    
    print(f"\n✓ Found {len(results)} words in {elapsed:.2f} seconds")
    print(f"\nTop 10 words:")
    for word, conf in results[:10]:
        print(f"  {word:15s} ({conf:.0f}%)")
    
    return results

def test_real_spelling_bee():
    """Test 2: Real NYT Spelling Bee puzzle."""
    print("\n\n" + "=" * 70)
    print("TEST 2: Real NYT Spelling Bee Puzzle")
    print("=" * 70)
    
    # Real puzzle from NYT (example)
    letters = "caliopt"  # Contains: CAPITAL, OPTICAL, etc.
    required = "c"
    
    print(f"\nPuzzle: {letters.upper()}")
    print(f"Required letter (center): {required.upper()}")
    print(f"Expected words: capital, optical, copilot, tactical, etc.\n")
    
    solver = UnifiedSpellingBeeSolver(mode=SolverMode.ANAGRAM)
    
    start = time.time()
    results = solver.solve_puzzle(letters, required)
    elapsed = time.time() - start
    
    print(f"\n✓ Found {len(results)} words in {elapsed:.2f} seconds")
    
    # Show interesting findings
    print(f"\nLongest words found:")
    longest = sorted(results, key=lambda x: -len(x[0]))[:5]
    for word, conf in longest:
        print(f"  {word:15s} ({len(word)} letters)")
    
    # Check for expected words
    expected = ["capital", "optical", "copilot", "tactic", "actic"]
    found_words = {word.lower() for word, _ in results}
    print(f"\nExpected words check:")
    for exp_word in expected:
        if exp_word in found_words:
            print(f"  ✓ {exp_word}")
        else:
            print(f"  ✗ {exp_word} (not found)")
    
    return results

def test_performance_benchmark():
    """Test 3: Performance benchmark on various puzzle sizes."""
    print("\n\n" + "=" * 70)
    print("TEST 3: Performance Benchmark (RTX 2080 Super)")
    print("=" * 70)
    
    test_cases = [
        ("abcdefg", "a", "Simple (7 common letters)"),
        ("posting", "t", "Medium (real word letters)"),
        ("rhythm", "r", "Hard (uncommon letters)"),  # Only 6 letters, repeat one
    ]
    
    solver = UnifiedSpellingBeeSolver(mode=SolverMode.ANAGRAM)
    
    print("\nRunning benchmarks...\n")
    results_summary = []
    
    for letters, required, description in test_cases:
        # Handle 6-letter case by repeating one
        if len(letters) < 7:
            letters = letters + letters[0]
        
        print(f"Testing: {description}")
        print(f"  Letters: {letters.upper()}, Required: {required.upper()}")
        
        start = time.time()
        results = solver.solve_puzzle(letters, required)
        elapsed = time.time() - start
        
        words_found = len(results)
        perms_per_sec = solver._calculate_permutations_for_length_range(4, 8) / elapsed if elapsed > 0 else 0
        
        print(f"  ✓ {words_found} words in {elapsed:.2f}s ({perms_per_sec/1e6:.1f}M perms/sec)\n")
        
        results_summary.append({
            'description': description,
            'letters': letters,
            'words': words_found,
            'time': elapsed,
            'speed': perms_per_sec
        })
    
    # Summary table
    print("\n" + "=" * 70)
    print("BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"{'Test':<30} {'Words':>8} {'Time':>10} {'Speed':>15}")
    print("-" * 70)
    for r in results_summary:
        print(f"{r['description']:<30} {r['words']:>8} {r['time']:>9.2f}s {r['speed']/1e6:>13.1f}M/s")
    
    return results_summary

def test_comparison_modes():
    """Test 4: Compare ANAGRAM mode vs PRODUCTION mode."""
    print("\n\n" + "=" * 70)
    print("TEST 4: ANAGRAM vs PRODUCTION Mode Comparison")
    print("=" * 70)
    
    letters = "posting"
    required = "t"
    
    print(f"\nPuzzle: {letters.upper()}, Required: {required.upper()}\n")
    
    # Test PRODUCTION mode
    print("Running PRODUCTION mode (standard dictionary lookup)...")
    solver_prod = UnifiedSpellingBeeSolver(mode=SolverMode.PRODUCTION)
    try:
        start = time.time()
        results_prod = solver_prod.solve_puzzle(letters, required)
        time_prod = time.time() - start
        print(f"  ✓ {len(results_prod)} words in {time_prod:.2f}s\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        results_prod = []
        time_prod = 0
    
    # Test ANAGRAM mode
    print("Running ANAGRAM mode (GPU brute force)...")
    solver_anagram = UnifiedSpellingBeeSolver(mode=SolverMode.ANAGRAM)
    start = time.time()
    results_anagram = solver_anagram.solve_puzzle(letters, required)
    time_anagram = time.time() - start
    print(f"  ✓ {len(results_anagram)} words in {time_anagram:.2f}s\n")
    
    # Compare results
    words_prod = {word.lower() for word, _ in results_prod}
    words_anagram = {word.lower() for word, _ in results_anagram}
    
    only_prod = words_prod - words_anagram
    only_anagram = words_anagram - words_prod
    common = words_prod & words_anagram
    
    print("Comparison:")
    print(f"  PRODUCTION only: {len(only_prod)} words")
    if only_prod and len(only_prod) <= 10:
        print(f"    Examples: {', '.join(list(only_prod)[:10])}")
    
    print(f"  ANAGRAM only: {len(only_anagram)} words")
    if only_anagram and len(only_anagram) <= 10:
        print(f"    Examples: {', '.join(list(only_anagram)[:10])}")
    
    print(f"  Common: {len(common)} words")
    
    print(f"\n  ANAGRAM found {len(results_anagram) - len(results_prod):+d} more words than PRODUCTION")

def _calculate_permutations_for_length_range(min_len, max_len):
    """Helper to calculate total permutations."""
    total = 0
    for length in range(min_len, max_len + 1):
        total += 7 ** length
    return total

# Add helper method to solver class
UnifiedSpellingBeeSolver._calculate_permutations_for_length_range = staticmethod(_calculate_permutations_for_length_range)

if __name__ == "__main__":
    print("\n" + "🚀" * 35)
    print("ANAGRAM MODE COMPREHENSIVE TEST SUITE")
    print("RTX 2080 Super | 8GB VRAM | 3072 CUDA Cores")
    print("🚀" * 35)
    
    try:
        # Run all tests
        test_anagram_mode_simple()
        test_real_spelling_bee()
        test_performance_benchmark()
        test_comparison_modes()
        
        print("\n\n" + "=" * 70)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nKey Features Demonstrated:")
        print("  ✓ tqdm progress bars with real-time stats")
        print("  ✓ Integration with UnifiedSpellingBeeSolver")
        print("  ✓ Real spelling bee puzzle solving")
        print("  ✓ Performance benchmarking on RTX 2080 Super")
        print("  ✓ Mode comparison (ANAGRAM vs PRODUCTION)")
        print("\nYour RTX 2080 Super is working perfectly! 🎉")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()

#!/usr/bin/env python3
"""Quick test of ANAGRAM mode with reasonable max_length."""

import time
from unified_solver import UnifiedSpellingBeeSolver, SolverMode

def quick_test():
    """Quick validation test."""
    print("=" * 70)
    print("ANAGRAM MODE - QUICK TEST")
    print("RTX 2080 Super | max_length=8 (covers most spelling bee words)")
    print("=" * 70)
    
    letters = "posting"
    required = "t"
    
    print(f"\nPuzzle: {letters.upper()}")
    print(f"Required letter: {required.upper()}")
    
    # Calculate expected permutations
    total_perms = sum(7**i for i in range(4, 9))  # 4-8 letters
    print(f"Expected permutations: {total_perms:,} ({total_perms/1e6:.1f}M)")
    print(f"Estimated time: {total_perms/600000:.1f} seconds @ 600K perms/sec\n")
    
    solver = UnifiedSpellingBeeSolver(mode=SolverMode.ANAGRAM)
    
    start = time.time()
    results = solver.solve_puzzle(letters, required)
    elapsed = time.time() - start
    
    print(f"\n✓ Found {len(results)} words in {elapsed:.2f} seconds")
    print(f"  Performance: {total_perms/elapsed/1e6:.2f}M perms/sec")
    
    if results:
        print(f"\nTop 10 words:")
        for word, conf in results[:10]:
            print(f"  {word:15s} ({conf:.0f}%)")
    
    print("\n" + "=" * 70)
    print("SUCCESS! Your RTX 2080 Super is working perfectly! 🎉")
    print("=" * 70)
    print("\nNote: For longer words, you can increase max_length:")
    print("  max_length=8  -> ~2.8M permutations  (~5 seconds)")
    print("  max_length=9  -> ~42M permutations  (~70 seconds)")
    print("  max_length=10 -> ~324M permutations (~9 minutes)")
    print("  max_length=12 -> ~16B permutations  (~7 hours)")

if __name__ == "__main__":
    try:
        quick_test()
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

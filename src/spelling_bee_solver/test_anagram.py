#!/usr/bin/env python3
"""
Quick test script for the CUDA anagram generator.
Tests with a simple letter set to validate the algorithm.
"""

import time
from anagram_generator import create_anagram_generator

def test_anagram_basic():
    """Test anagram generator with a simple case."""
    print("=" * 60)
    print("Testing CUDA Anagram Generator (RTX 2080 Super Optimized)")
    print("=" * 60)
    
    # Simple test: common letters that should produce many words
    letters = "abcdefg"
    required = "a"
    
    print(f"\nLetters: {letters.upper()}")
    print(f"Required letter: {required.upper()}")
    print(f"Length range: 4-8 (conservative test)")
    
    # Create a simple dictionary for testing
    test_dictionary = {
        "able", "aced", "aged", "bead", "cafe", "cage", "dead",
        "deaf", "fade", "face", "gab", "cab", "bad", "bag", "dab",
        "fad", "fab", "gad", "gaffe", "badge", "cadge", "caged",
        "abaca", "abaci"
    }
    
    print(f"\nTest dictionary size: {len(test_dictionary)} words")
    print("Expected to find: " + ", ".join(sorted(test_dictionary)))
    
    # Create generator
    print("\nInitializing anagram generator...")
    generator = create_anagram_generator(
        letters=letters,
        required_letter=required,
        max_length=8  # Keep it small for quick test
    )
    
    # Track progress
    def progress_callback(processed, total, words_found):
        if processed % 100000 == 0 or processed == total:
            pct = (processed / total) * 100
            print(f"  Progress: {processed:,}/{total:,} ({pct:.1f}%) - {words_found} words found")
    
    # Run generation
    print("\nGenerating permutations and checking dictionary...")
    start_time = time.time()
    
    results = generator.generate_all(
        dictionary=test_dictionary,
        progress_callback=progress_callback
    )
    
    elapsed = time.time() - start_time
    
    # Display results
    print("\n" + "=" * 60)
    print(f"RESULTS (completed in {elapsed:.2f} seconds)")
    print("=" * 60)
    
    print(f"\nTotal words found: {len(results)}")
    print(f"Permutations checked: {generator.total_permutations:,}")
    print(f"Speed: {generator.total_permutations / elapsed:,.0f} permutations/sec")
    
    if results:
        print("\nWords found:")
        for word, _ in results:
            print(f"  {word}")
    else:
        print("\nNo words found!")
    
    # Validate
    found_words = set(word for word, _ in results)
    expected_words = {w for w in test_dictionary if required in w and len(w) >= 4}
    
    print(f"\nValidation:")
    print(f"  Expected: {len(expected_words)} words")
    print(f"  Found: {len(found_words)} words")
    
    if found_words == expected_words:
        print("  ✓ PASS: All expected words found!")
    else:
        missing = expected_words - found_words
        extra = found_words - expected_words
        if missing:
            print(f"  ✗ FAIL: Missing words: {missing}")
        if extra:
            print(f"  ✗ FAIL: Extra words: {extra}")

def test_with_real_letters():
    """Test with a more realistic spelling bee letter set."""
    print("\n\n" + "=" * 60)
    print("Testing with realistic letter set")
    print("=" * 60)
    
    letters = "ptriaol"  # Good mix of common letters
    required = "t"
    
    print(f"\nLetters: {letters.upper()}")
    print(f"Required letter: {required.upper()}")
    print(f"Length range: 4-7 (quick test)")
    
    # Load a real dictionary subset (common words)
    try:
        with open('/usr/share/dict/words', 'r') as f:
            dictionary = set(
                word.strip().lower() 
                for word in f 
                if 4 <= len(word.strip()) <= 7 and word.strip().isalpha()
            )
        print(f"Dictionary size: {len(dictionary)} words")
    except FileNotFoundError:
        print("Warning: System dictionary not found, using small test set")
        dictionary = {"part", "trip", "tail", "port", "riot", "pilot", "trail"}
    
    # Create generator
    generator = create_anagram_generator(
        letters=letters,
        required_letter=required,
        max_length=7  # Keep reasonable for quick test
    )
    
    # Progress tracking
    last_update = [0]
    def progress_callback(processed, total, words_found):
        # Update every 10% or at completion
        pct = (processed / total) * 100
        if pct - last_update[0] >= 10 or processed == total:
            print(f"  Progress: {pct:.0f}% - {words_found} words found")
            last_update[0] = pct
    
    # Run
    print("\nGenerating...")
    start_time = time.time()
    results = generator.generate_all(
        dictionary=dictionary,
        progress_callback=progress_callback
    )
    elapsed = time.time() - start_time
    
    # Results
    print(f"\n✓ Found {len(results)} words in {elapsed:.2f} seconds")
    print(f"  Speed: {generator.total_permutations / elapsed / 1e6:.1f}M permutations/sec")
    
    # Show some examples
    if results:
        print("\nExample words found (showing first 15):")
        for word, _ in results[:15]:
            print(f"  {word}")
        if len(results) > 15:
            print(f"  ... and {len(results) - 15} more")

if __name__ == "__main__":
    try:
        # Test 1: Basic validation
        test_anagram_basic()
        
        # Test 2: Realistic test
        test_with_real_letters()
        
        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

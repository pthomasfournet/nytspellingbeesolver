"""
Simple and effective spelling bee solver using just the system dictionary.
Based on the working debug solver approach.
"""

import data_persistence
import word_filtering


def solve_puzzle_simple(center_letter, outer_letters, debug=False):
    """
    Simple solver using system dictionary plus selected words from comprehensive dictionary.
    This approach finds legitimate words while avoiding garbage.
    
    Args:
        center_letter: The center letter that must be in every word
        outer_letters: The outer letters available for use
        debug: If True, shows dictionary source for each word found
    """
    center = center_letter.lower()
    outer = outer_letters.lower()
    allowed_letters = set(center + outer)
    
    print(f"Solving puzzle: Center='{center.upper()}' Outer='{outer.upper()}'")
    if debug:
        print("DEBUG MODE: Will show dictionary source for each word")
    
    # Load system dictionary (primary source)
    system_words = set()
    try:
        with open('/usr/share/dict/words', 'r', encoding='utf-8') as f:
            for word in f:
                word = word.strip()
                if len(word) < 4 or "'" in word or "-" in word:
                    continue
                word_lower = word.lower()
                system_words.add(word_lower)
        print(f"System dictionary loaded: {len(system_words)} words")
    except FileNotFoundError:
        print("System dictionary not found!")
        return [], []
    
    # Add selected legitimate words from comprehensive dictionary
    # These are words we know are legitimate but missing from system dict
    legitimate_additions = {
        'capo',     # Guitar accessory, Mafia boss
        'coopt',    # Variant of co-opt  
        'copout',   # Variant of cop-out
        'unapt',    # Not apt, unsuitable
    }
    
    comprehensive_words = set()
    # Load comprehensive dictionary to get these specific words
    try:
        with open('comprehensive_words.txt', 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word in legitimate_additions:
                    comprehensive_words.add(word)
        print(f"Added {len(comprehensive_words)} legitimate words from comprehensive dictionary")
    except FileNotFoundError:
        print("Comprehensive dictionary not found - using system dictionary only")
    
    # Combine all words with source tracking
    all_words = system_words | comprehensive_words
    
    # Load rejected words
    rejected_words = data_persistence.load_rejected_words()
    
    solutions = []
    pangrams = []
    
    if debug:
        print(f"\n=== DEBUG: Word-by-word analysis ===")
    
    for word in all_words:
        # Determine source for debug output
        if word in system_words and word in comprehensive_words:
            source = "BOTH"
        elif word in system_words:
            source = "SYSTEM"
        elif word in comprehensive_words:
            source = "COMPREHENSIVE"
        else:
            source = "UNKNOWN"
        
        # Must contain center letter
        if center not in word:
            if debug and word in ['capo', 'capon', 'papa', 'atop', 'upon']:  # Debug key words
                print(f"  {word:<15} [{source}] FILTERED: No center letter '{center}'")
            continue
            
        # Must only use allowed letters
        if not set(word) <= allowed_letters:
            if debug and word in ['capo', 'capon', 'papa', 'atop', 'upon']:  # Debug key words
                forbidden = set(word) - allowed_letters
                print(f"  {word:<15} [{source}] FILTERED: Uses forbidden letters {forbidden}")
            continue
            
        # Must be long enough
        if len(word) < 4:
            if debug and word in ['capo', 'capon', 'papa', 'atop', 'upon']:  # Debug key words
                print(f"  {word:<15} [{source}] FILTERED: Too short ({len(word)} chars)")
            continue
            
        # Skip rejected words
        if word in rejected_words:
            if debug:
                print(f"  {word:<15} [{source}] FILTERED: In rejected words list")
            continue
            
        # Apply basic intelligent filtering (but allow capo, etc.)
        if word_filtering.is_likely_nyt_rejected(word):
            if debug:
                print(f"  {word:<15} [{source}] FILTERED: Likely NYT rejected")
            continue
            
        # Manual filter for specific problematic words
        if word in ['napa']:  # Known place names in lowercase
            if debug:
                print(f"  {word:<15} [{source}] FILTERED: Manual blacklist")
            continue
            
        # Valid word found!
        word_len = len(word)
        is_pangram = len(set(word)) == 7
        
        if is_pangram:
            points = word_len + 7
            pangrams.append(word)
        elif word_len == 4:
            points = 1
        else:
            points = word_len
            
        # Higher confidence for system dictionary words, slightly lower for additions
        confidence = 85 if word in system_words else 80
        solutions.append((word, points, confidence))
        
        if debug:
            pangram_note = " (PANGRAM)" if is_pangram else ""
            print(f"  {word:<15} [{source}] ACCEPTED: {points} pts, {confidence}% confidence{pangram_note}")
    
    # Sort by points (descending), then by confidence (descending)
    solutions.sort(key=lambda x: (-x[1], -x[2]))
    
    print(f"Found {len(solutions)} valid words")
    print(f"Found {len(pangrams)} pangrams")
    
    return solutions, pangrams
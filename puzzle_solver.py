"""
Puzzle solving logic for NYT Spelling Bee solver.
"""

import dictionary_loader
import word_filtering
import data_persistence


def solve_puzzle_webster_first(center_letter, outer_letters, target_count=46):
    """
    Solve spelling bee puzzle using professional Scrabble solver approach:
    1. Scrabble Dictionary (highest quality - official word game source)
    2. Webster's Dictionary (high quality - authoritative)  
    3. Aspell Dictionary (good quality - comprehensive)
    4. Comprehensive Dictionary (moderate quality - includes variants)
    """
    center = center_letter.lower()
    outer = outer_letters.lower()
    allowed_letters = set(center + outer)
    
    print(f"Solving puzzle: Center='{center.upper()}' Outer='{outer.upper()}'")
    
    # Load rejected words
    rejected_words = data_persistence.load_rejected_words()
    
    # PHASE 1: Scrabble Dictionary (Official - Highest Quality)
    print("\n=== PHASE 1: Scrabble Dictionary (Official) ===")
    scrabble_words = dictionary_loader.load_scrabble_dictionary()
    
    all_solutions = []
    all_pangrams = []
    found_words = set()
    
    if scrabble_words:
        for word in scrabble_words:
            # Must contain center letter
            if center not in word:
                continue
                
            # Must only use allowed letters
            if not set(word) <= allowed_letters:
                continue
                
            # Must be long enough
            if len(word) < 4:
                continue
                
            # Skip rejected words
            if word in rejected_words:
                continue
                
            # Valid word found!
            word_len = len(word)
            is_pangram = len(set(word)) == 7
            
            if is_pangram:
                points = word_len + 7
                all_pangrams.append(word)
            elif word_len == 4:
                points = 1
            else:
                points = word_len
                
            # Highest confidence for official Scrabble words
            confidence = 100
            all_solutions.append((word, points, confidence))
            found_words.add(word)
        
        print(f"Found {len([s for s in all_solutions if s[2] == 100])} words in Scrabble dictionary")
    
    # PHASE 2: Webster's Dictionary (Authoritative Supplement)
    print("\n=== PHASE 2: Webster's Dictionary (Authoritative) ===")
    webster_words = dictionary_loader.load_webster_dictionary()
    
    if webster_words:
        webster_found = 0
        for word in webster_words:
            # Skip if already found in Scrabble dictionary
            if word in found_words:
                continue
                
            # Must contain center letter
            if center not in word:
                continue
                
            # Must only use allowed letters
            if not set(word) <= allowed_letters:
                continue
                
            # Must be long enough
            if len(word) < 4:
                continue
                
            # Skip rejected words
            if word in rejected_words:
                continue
                
            # Apply intelligent filtering for obvious non-NYT words
            if word_filtering.is_likely_nyt_rejected(word.title()):
                continue
                
            # Valid supplementary word found!
            word_len = len(word)
            is_pangram = len(set(word)) == 7
            
            if is_pangram:
                points = word_len + 7
                all_pangrams.append(word)
            elif word_len == 4:
                points = 1
            else:
                points = word_len
                
            # High confidence for Webster's words
            confidence = 95
            all_solutions.append((word, points, confidence))
            found_words.add(word)
            webster_found += 1
        
        print(f"Found {webster_found} additional words in Webster's dictionary")
    
    # PHASE 3: Aspell Dictionary (Comprehensive Supplement)
    print("\n=== PHASE 3: Aspell Dictionary (Comprehensive) ===")
    aspell_words = dictionary_loader.load_aspell_dictionary()
    
    if aspell_words:
        aspell_found = 0
        for word in aspell_words:
            # Skip if already found in previous dictionaries
            if word in found_words:
                continue
                
            # Must contain center letter
            if center not in word:
                continue
                
            # Must only use allowed letters
            if not set(word) <= allowed_letters:
                continue
                
            # Must be long enough
            if len(word) < 4:
                continue
                
            # Skip rejected words
            if word in rejected_words:
                continue
                
            # Apply intelligent filtering for obvious non-NYT words
            if word_filtering.is_likely_nyt_rejected(word.title()):
                continue
                
            # Valid supplementary word found!
            word_len = len(word)
            is_pangram = len(set(word)) == 7
            
            if is_pangram:
                points = word_len + 7
                all_pangrams.append(word)
            elif word_len == 4:
                points = 1
            else:
                points = word_len
                
            # Good confidence for aspell words
            confidence = 85
            all_solutions.append((word, points, confidence))
            found_words.add(word)
            aspell_found += 1
        
        print(f"Found {aspell_found} additional words in aspell dictionary")
    
    # PHASE 4: Comprehensive Dictionary (Variant Spellings)
    print("\n=== PHASE 4: Comprehensive Dictionary (Variants) ===")
    comprehensive_words = dictionary_loader.load_comprehensive_dictionary()
    
    if comprehensive_words:
        comprehensive_found = 0
        for word in comprehensive_words:
            # Skip if already found in previous dictionaries
            if word in found_words:
                continue
                
            # Must contain center letter
            if center not in word:
                continue
                
            # Must only use allowed letters
            if not set(word) <= allowed_letters:
                continue
                
            # Must be long enough
            if len(word) < 4:
                continue
                
            # Skip rejected words
            if word in rejected_words:
                continue
                
            # Apply stricter filtering for comprehensive dictionary to avoid nonsense words
            if word_filtering.is_likely_nyt_rejected_strict(word.title()):
                continue
                
            # Valid comprehensive word found!
            word_len = len(word)
            is_pangram = len(set(word)) == 7
            
            if is_pangram:
                points = word_len + 7
                all_pangrams.append(word)
            elif word_len == 4:
                points = 1
            else:
                points = word_len
                
            # Moderate confidence for comprehensive words (includes variants)
            confidence = 75
            all_solutions.append((word, points, confidence))
            comprehensive_found += 1
        
        print(f"Found {comprehensive_found} additional words in comprehensive dictionary")
    
    # Sort by confidence then points and remove duplicates
    seen_words = set()
    unique_solutions = []
    for word, points, confidence in sorted(all_solutions, key=lambda x: (-x[2], -x[1])):
        if word not in seen_words:
            unique_solutions.append((word, points, confidence))
            seen_words.add(word)
    
    return unique_solutions, all_pangrams


def find_solutions_legacy(center_letter, outer_letters, dictionary, exclude_found=None, rejected_words=None):
    """
    LEGACY: Find all valid words for the Spelling Bee puzzle.
    Use solve_puzzle_webster_first() for new Webster-first approach.
    """
    center = center_letter.lower()
    allowed_letters = set(center + "".join(outer_letters).lower())
    exclude_found = exclude_found or set()
    rejected_words = rejected_words or set()

    solutions = []
    pangrams = []

    for word in dictionary:
        # Skip rejected words
        if word in rejected_words:
            continue

        # Must contain center letter
        if center not in word:
            continue

        # Must only use allowed letters
        if not all(letter in allowed_letters for letter in word):
            continue

        # Valid word found
        word_len = len(word)
        is_pangram = len(set(word)) == 7

        if is_pangram:
            points = word_len + 7
            pangrams.append(word)
        elif word_len == 4:
            points = 1
        else:
            points = word_len

        # Skip words already found (if we're excluding them)
        if word in exclude_found:
            continue

        # Simple confidence for legacy function
        confidence = 75
        solutions.append((word, points, confidence))

    # Sort by confidence (descending), then by points (descending)
    solutions.sort(key=lambda x: (-x[2], -x[1]))

    return solutions, pangrams
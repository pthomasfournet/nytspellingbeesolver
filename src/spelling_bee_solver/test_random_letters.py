#!/usr/bin/env python3
"""
Test script to run the spelling bee solver with random letters.
"""

import random
import string
from unified_solver import UnifiedSpellingBeeSolver, SolverMode

def generate_random_puzzle():
    """Generate a random spelling bee puzzle with 7 unique letters."""
    # Pick 7 unique letters
    letters = random.sample(string.ascii_lowercase, 7)
    
    # The first letter will be the center/required letter
    center_letter = letters[0]
    other_letters = letters[1:]
    
    return center_letter, other_letters

def main():
    print("Testing Spelling Bee Solver with Random Letters")
    print("=" * 50)
    
    # Generate random puzzle
    center_letter, other_letters = generate_random_puzzle()
    all_letters = [center_letter] + other_letters
    
    print(f"Center letter (required): {center_letter.upper()}")
    print(f"Other letters: {', '.join(letter.upper() for letter in other_letters)}")
    print(f"All letters: {', '.join(letter.upper() for letter in all_letters)}")
    print()
    
    # Create solver instance with CPU fallback to avoid GPU/spaCy issues
    try:
        solver = UnifiedSpellingBeeSolver(mode=SolverMode.CPU_FALLBACK)
        print("Solver initialized successfully!")
        print()
        
        # Solve the puzzle
        print("Solving puzzle...")
        all_letters_str = ''.join(all_letters)
        results = solver.solve_puzzle(all_letters_str, center_letter)
        
        # Display results
        if results:
            print(f"Found {len(results)} words:")
            print("-" * 30)
            
            # Sort by length and then alphabetically
            sorted_results = sorted(results, key=lambda x: (len(x), x))
            
            # Group by length
            current_length = 0
            for word in sorted_results:
                if len(word) != current_length:
                    current_length = len(word)
                    print(f"\n{current_length} letters:")
                print(f"  {word}")
                
        else:
            print("No words found!")
            
    except Exception as e:
        print(f"Error running solver: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
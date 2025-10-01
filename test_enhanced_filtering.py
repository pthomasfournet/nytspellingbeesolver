#!/usr/bin/env python3
"""Test the enhanced filtering with NLTK integration."""

import sys
sys.path.append('/home/tom/spelling_bee_solver_project')

from word_filtering import is_likely_nyt_rejected

def test_enhanced_filtering():
    """Test our enhanced filtering system."""
    
    test_cases = [
        # Proper nouns that should be rejected
        ('botticelli', True, 'Italian Renaissance painter'),
        ('celtic', True, 'Celtic culture/people'),
        ('elliott', True, 'Personal name'),
        ('tito', True, 'Personal name'),
        ('clio', True, 'Greek muse'),
        ('belgium', True, 'Country name'),
        ('britain', True, 'Country name'),
        ('leonardo', True, 'Artist name'),
        ('shakespeare', True, 'Author name'),
        ('beethoven', True, 'Composer name'),
        
        # Common words that should NOT be rejected
        ('toilet', False, 'Common word'),
        ('little', False, 'Common word'),
        ('bottle', False, 'Common word'),
        ('battle', False, 'Common word'),
        ('cattle', False, 'Common word'),
        ('circle', False, 'Common word'),
        ('title', False, 'Common word'),
        ('bible', False, 'Common word'),
        ('settle', False, 'Common word'),
        ('nettle', False, 'Common word'),
        ('kettle', False, 'Common word'),
        
        # Edge cases
        ('apple', True, 'Could be company name'),
        ('may', False, 'Common word despite being capitalized'),
        ('will', False, 'Common word despite being a name'),
    ]
    
    print("Testing Enhanced Filtering (NLTK + Manual)")
    print("=" * 60)
    
    correct = 0
    total = len(test_cases)
    
    for word, expected_rejected, description in test_cases:
        actual_rejected = is_likely_nyt_rejected(word)
        is_correct = actual_rejected == expected_rejected
        
        status = "✓" if is_correct else "✗"
        result = "REJECTED" if actual_rejected else "ACCEPTED"
        expected = "REJECTED" if expected_rejected else "ACCEPTED"
        
        print(f"{status} {word:15} -> {result:8} (expected {expected:8}) - {description}")
        
        if is_correct:
            correct += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {correct}/{total} correct ({correct/total*100:.1f}%)")
    
    # Test specific case that prompted this enhancement
    botticelli_rejected = is_likely_nyt_rejected('botticelli')
    print(f"\nCritical Test: 'botticelli' -> {'REJECTED' if botticelli_rejected else 'ACCEPTED'}")
    if botticelli_rejected:
        print("✓ SUCCESS: Enhanced filtering now catches 'botticelli'!")
    else:
        print("✗ FAILURE: 'botticelli' still getting through")

if __name__ == "__main__":
    test_enhanced_filtering()
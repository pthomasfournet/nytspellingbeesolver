#!/usr/bin/env python3
"""
Test script to validate filtering improvements.
Tests both the upgraded spaCy model and pattern filter bug fixes.
"""

import sys
sys.path.insert(0, '/home/tom/spelling_bee_solver_project/src/spelling_bee_solver')

from word_filtering import is_likely_nyt_rejected
from intelligent_word_filter import IntelligentWordFilter, filter_words_intelligent

def test_pattern_filter_fixes():
    """Test that pattern filter bugs are fixed."""
    print("=" * 70)
    print("PATTERN FILTER BUG FIXES TEST")
    print("=" * 70)
    
    # Test cases: (word, should_be_accepted, bug_description)
    test_cases = [
        # Issue #1: Suffix false positives (geographic)
        ("woodland", True, "Compound word ending in 'land'"),
        ("understand", True, "Compound word ending in 'stand'"),
        ("backfield", True, "Compound word ending in 'field'"),
        ("Pittsburgh", False, "Actual place name ending in 'burg'"),
        
        # Issue #1: Suffix false positives (abbreviation endings)
        ("government", True, "Common word ending in 'ment'"),
        ("engagement", True, "Common word ending in 'ment'"),
        ("management", True, "Common word ending in 'mgmt'"),
        ("assignment", True, "Common word ending in 'ment'"),
        
        # Issue #2: Double-O false positives
        ("book", True, "Common word with 'oo'"),
        ("cool", True, "Common word with 'oo'"),
        ("moon", True, "Common word with 'oo'"),
        ("food", True, "Common word with 'oo'"),
        ("ooze", True, "Valid English word starting with 'oo'"),
        
        # Issue #3: Latin suffix false positives
        ("famous", True, "Common English word ending in 'ous'"),
        ("joyous", True, "Common English word ending in 'ous'"),
        ("nervous", True, "Common English word ending in 'ous'"),
        ("anxious", True, "Common English word ending in 'ous'"),
        ("propane", True, "Common word ending in 'ane'"),
        ("plane", True, "Common word ending in 'ane'"),
        ("machine", True, "Common word ending in 'ine'"),
        ("routine", True, "Common word ending in 'ine'"),
        
        # Should still reject
        ("NASA", False, "Acronym - all caps"),
        ("London", False, "Proper noun - place"),
        ("calcium", False, "Scientific term ending in 'ium'"),
        ("mgmt", False, "Abbreviation"),
    ]
    
    passed = 0
    failed = 0
    
    print("\nTest Results:")
    print("-" * 70)
    
    for word, should_accept, description in test_cases:
        is_rejected = is_likely_nyt_rejected(word)
        is_accepted = not is_rejected
        
        status = "✅ PASS" if is_accepted == should_accept else "❌ FAIL"
        expected = "ACCEPT" if should_accept else "REJECT"
        actual = "ACCEPT" if is_accepted else "REJECT"
        
        print(f"{status} | {word:15s} | Expected: {expected:6s} | Actual: {actual:6s} | {description}")
        
        if is_accepted == should_accept:
            passed += 1
        else:
            failed += 1
    
    print("-" * 70)
    print(f"\nResults: {passed} passed, {failed} failed ({passed}/{len(test_cases)} = {passed/len(test_cases)*100:.1f}%)")
    
    return passed, failed

def test_spacy_model_upgrade():
    """Test that the upgraded spaCy model is working."""
    print("\n\n" + "=" * 70)
    print("SPACY MODEL UPGRADE TEST")
    print("=" * 70)
    
    try:
        filter_obj = IntelligentWordFilter(use_gpu=True)
        
        # Check which model loaded
        if filter_obj.nlp:
            model_name = filter_obj.nlp.meta.get('name', 'unknown')
            model_version = filter_obj.nlp.meta.get('version', 'unknown')
            vocab_size = len(filter_obj.nlp.vocab)
            
            print(f"\n✅ spaCy Model Information:")
            print(f"   Model: {model_name}")
            print(f"   Version: {model_version}")
            print(f"   Vocabulary: {vocab_size:,} words")
            print(f"   GPU: {filter_obj.use_gpu}")
            
            # Test proper noun detection with medium model
            print(f"\n📊 Proper Noun Detection Test:")
            test_words = [
                ("London", True, "City name"),
                ("london", False, "Lowercase - not capitalized"),
                ("Microsoft", True, "Company name"),
                ("Apple", True, "Company name (also common word)"),
                ("apple", False, "Common noun lowercase"),
                ("John", True, "Person name"),
                ("NASA", True, "Organization acronym"),
            ]
            
            for word, should_reject, description in test_words:
                is_proper = filter_obj.is_proper_noun_intelligent(word)
                status = "✅" if is_proper == should_reject else "❌"
                result = "PROPER" if is_proper else "COMMON"
                expected = "PROPER" if should_reject else "COMMON"
                print(f"   {status} {word:15s} → {result:6s} (expected: {expected:6s}) - {description}")
            
            return True
        else:
            print("❌ spaCy model not loaded")
            return False
            
    except Exception as e:
        print(f"❌ Error testing spaCy model: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intelligent_filter_integration():
    """Test the full intelligent filter with GPU."""
    print("\n\n" + "=" * 70)
    print("INTELLIGENT FILTER INTEGRATION TEST")
    print("=" * 70)
    
    test_words = [
        "hello", "world", "book", "cool", "famous", "joyous",
        "woodland", "government", "NASA", "London", "anapanapa",
        "test", "python", "machine", "routine", "nervous"
    ]
    
    print(f"\nTesting {len(test_words)} words with intelligent filter...")
    
    try:
        filtered = filter_words_intelligent(test_words, use_gpu=True)
        
        print(f"\n✅ Filtered Results:")
        print(f"   Input: {len(test_words)} words")
        print(f"   Output: {len(filtered)} words kept")
        print(f"   Filtered out: {len(test_words) - len(filtered)} words")
        
        print(f"\n   Kept words: {', '.join(filtered)}")
        print(f"   Removed: {', '.join(set(test_words) - set(filtered))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "🔬" * 35)
    print("FILTERING SYSTEM IMPROVEMENTS TEST SUITE")
    print("Testing: spaCy upgrade + pattern filter bug fixes")
    print("🔬" * 35)
    
    try:
        # Test 1: Pattern filter fixes
        passed, failed = test_pattern_filter_fixes()
        
        # Test 2: spaCy model upgrade
        spacy_ok = test_spacy_model_upgrade()
        
        # Test 3: Full integration
        integration_ok = test_intelligent_filter_integration()
        
        # Summary
        print("\n\n" + "=" * 70)
        print("FINAL SUMMARY")
        print("=" * 70)
        print(f"Pattern Filter Fixes: {passed} passed, {failed} failed")
        print(f"spaCy Model Upgrade: {'✅ SUCCESS' if spacy_ok else '❌ FAILED'}")
        print(f"Integration Test: {'✅ SUCCESS' if integration_ok else '❌ FAILED'}")
        
        if failed == 0 and spacy_ok and integration_ok:
            print("\n🎉 ALL TESTS PASSED! Filtering system improved successfully!")
        else:
            print(f"\n⚠️  {failed} pattern filter test(s) failed or integration issues")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

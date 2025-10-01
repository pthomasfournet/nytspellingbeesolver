"""
Dictionary loading and management for NYT Spelling Bee solver.
Handles loading words from various high-quality sources with Webster's as primary.
"""

import subprocess
import word_filtering

def load_webster_dictionary():
    """Load words from Webster's dictionary with intelligent filtering."""
    try:
        # Use American English dictionary as primary source
        with open('/usr/share/dict/american-english', 'r', encoding='utf-8') as f:
            words = []
            for line in f:
                original_word = line.strip()
                if not original_word:
                    continue
                
                # Check for proper nouns BEFORE converting to lowercase
                if word_filtering.is_likely_nyt_rejected(original_word):
                    continue
                
                # Convert to lowercase for processing
                word_lower = original_word.lower()
                
                # Process word (handles hyphen removal)
                processed_word = word_filtering.process_word_for_puzzle(word_lower)
                if not processed_word:
                    continue
                    
                # Apply additional filtering to the processed word
                if not word_filtering.is_likely_nyt_word(processed_word):
                    continue
                    
                words.append(processed_word)
                    
            print(f"Primary dictionary loaded: {len(words)} words")
            return words
    except FileNotFoundError:
        print("Webster's dictionary not found, using basic system dictionary")
        return load_system_dictionary()

def load_aspell_dictionary():
    """Load aspell dictionary as comprehensive supplement."""
    try:
        result = subprocess.run(['aspell', '-d', 'en', 'dump', 'master'], 
                              capture_output=True, text=True, check=True)
        words = []
        for line in result.stdout.strip().split('\n'):
            original_word = line.strip()
            if not original_word:
                continue
                
            # Check for proper nouns BEFORE converting to lowercase
            if word_filtering.is_likely_nyt_rejected(original_word):
                continue
            
            # Convert to lowercase for processing
            word_lower = original_word.lower()
            
            # Process word (handles hyphen removal)
            processed_word = word_filtering.process_word_for_puzzle(word_lower)
            if not processed_word:
                continue
                
            # Apply additional filtering to the processed word
            if not word_filtering.is_likely_nyt_word(processed_word):
                continue
                
            words.append(processed_word)
                
        print(f"Aspell dictionary loaded: {len(words)} words")
        return words
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Aspell dictionary not available")
        return []

def load_scrabble_dictionary():
    """Load official Scrabble dictionary - highest quality word source."""
    try:
        with open('scrabble_words.txt', 'r', encoding='utf-8') as f:
            words = []
            for line in f:
                original_word = line.strip()
                if not original_word:
                    continue
                
                # Check for proper nouns BEFORE converting to lowercase
                if word_filtering.is_likely_nyt_rejected(original_word):
                    continue
                
                # Convert to lowercase for processing
                word_lower = original_word.lower()
                
                # Process word (handles hyphen removal)
                processed_word = word_filtering.process_word_for_puzzle(word_lower)
                if not processed_word:
                    continue
                    
                # Apply additional filtering to the processed word
                if not word_filtering.is_likely_nyt_word(processed_word):
                    continue
                    
                words.append(processed_word)
                    
            print(f"Scrabble dictionary loaded: {len(words)} words")
            return words
    except FileNotFoundError:
        print("Scrabble dictionary not found")
        return []


def load_comprehensive_dictionary():
    """Load comprehensive dictionary with hyphenated words."""
    try:
        with open('comprehensive_words.txt', 'r', encoding='utf-8') as f:
            words = []
            for line in f:
                original_word = line.strip()
                if not original_word:
                    continue
                    
                # Apply intelligent filtering to the ORIGINAL word (before processing)
                if word_filtering.is_likely_nyt_rejected(original_word):
                    continue
                
                # Convert to lowercase for processing
                word_lower = original_word.lower()
                
                # Process word (handles hyphen removal)
                processed_word = word_filtering.process_word_for_puzzle(word_lower)
                if not processed_word:
                    continue
                    
                # Only apply basic validity check to processed word, not intelligent filtering
                if not word_filtering.is_likely_nyt_word(processed_word):
                    continue
                    
                words.append(processed_word)
                    
            print(f"Comprehensive dictionary loaded: {len(words)} words")
            return words
    except FileNotFoundError:
        print("Comprehensive dictionary not found")
        return []
#!/usr/bin/env python3
"""
Enhanced proper noun filtering using NLTK for NYT Spelling Bee solver.
Uses NLP techniques to automatically detect proper nouns.
"""

import nltk
from nltk.corpus import names
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
import string
import re

class NLTKProperNounFilter:
    def __init__(self):
        """Initialize the NLTK-based proper noun filter."""
        self.setup_nltk_data()
        self.load_name_sets()
        
    def setup_nltk_data(self):
        """Ensure required NLTK data is downloaded."""
        required_data = [
            'punkt',
            'averaged_perceptron_tagger', 
            'names'
        ]
        
        for data in required_data:
            try:
                nltk.data.find(f'tokenizers/{data}')
            except LookupError:
                try:
                    nltk.data.find(f'taggers/{data}')
                except LookupError:
                    try:
                        nltk.data.find(f'corpora/{data}')
                    except LookupError:
                        print(f"Downloading {data}...")
                        nltk.download(data, quiet=True)
    
    def load_name_sets(self):
        """Load NLTK name corpora."""
        try:
            self.male_names = set(name.lower() for name in names.words('male.txt'))
            self.female_names = set(name.lower() for name in names.words('female.txt'))
            self.all_names = self.male_names | self.female_names
            print(f"Loaded {len(self.all_names)} names from NLTK corpus")
        except Exception as e:
            print(f"Warning: Could not load NLTK names corpus: {e}")
            self.all_names = set()
    
    def is_proper_noun_by_pos(self, word):
        """Check if word is tagged as proper noun by NLTK POS tagger."""
        try:
            # Tokenize and tag the word
            tokens = word_tokenize(word.capitalize())
            if not tokens:
                return False
                
            tags = pos_tag(tokens)
            # NNP = proper noun, singular
            # NNPS = proper noun, plural
            return any(tag in ['NNP', 'NNPS'] for _, tag in tags)
        except Exception:
            return False
    
    def is_name_in_corpus(self, word):
        """Check if word appears in NLTK names corpus."""
        return word.lower() in self.all_names
    
    def is_likely_proper_noun(self, word):
        """
        Enhanced proper noun detection using multiple NLTK techniques.
        
        Args:
            word (str): Word to check
            
        Returns:
            bool: True if likely a proper noun, False otherwise
        """
        if not word or len(word) < 2:
            return False
            
        word_lower = word.lower()
        
        # Skip very common words that might be tagged as proper nouns
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'over', 'after', 'be', 'am', 'is',
            'are', 'was', 'were', 'being', 'been', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can'
        }
        
        if word_lower in common_words:
            return False
        
        # Check if it's in the names corpus
        if self.is_name_in_corpus(word):
            return True
            
        # Use POS tagging to detect proper nouns
        if self.is_proper_noun_by_pos(word):
            return True
            
        # Additional heuristics for proper nouns
        # Check if starts with capital and contains unusual patterns
        if word[0].isupper():
            # Check for typical proper noun patterns
            # Names ending in common suffixes
            name_endings = ['son', 'sen', 'man', 'ton', 'burg', 'ville', 'ford', 'land']
            if any(word_lower.endswith(ending) for ending in name_endings):
                return True
                
            # Check for place name patterns (ends with geographical suffixes)
            place_endings = ['ia', 'an', 'stan', 'land', 'shire', 'berg', 'holm']
            if any(word_lower.endswith(ending) for ending in place_endings):
                return True
        
        return False

def create_enhanced_filter():
    """Create and return an enhanced proper noun filter using NLTK."""
    return NLTKProperNounFilter()

def test_filter():
    """Test the NLTK proper noun filter."""
    filter_obj = create_enhanced_filter()
    
    test_words = [
        # Should be detected as proper nouns
        'elliott', 'celtic', 'botticelli', 'tito', 'clio', 'belgium', 'britain',
        'John', 'Mary', 'London', 'Paris', 'Microsoft', 'Einstein',
        
        # Should NOT be detected as proper nouns  
        'toilet', 'little', 'elite', 'title', 'bible', 'bottle', 'circle',
        'battle', 'cattle', 'settle', 'nettle', 'kettle'
    ]
    
    print("Testing NLTK Proper Noun Filter:")
    print("=" * 50)
    
    for word in test_words:
        is_proper = filter_obj.is_likely_proper_noun(word)
        print(f"{word:15} -> {'PROPER NOUN' if is_proper else 'common word'}")

if __name__ == "__main__":
    test_filter()
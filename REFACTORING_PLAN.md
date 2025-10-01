# HIGH PRIORITY Refactoring Plan

**Date:** October 1, 2025  
**Project:** NYT Spelling Bee Solver  
**Scope:** Address 3 HIGH PRIORITY architectural issues  
**Total Estimated Time:** 1-2 weeks (developer time)

---

## 🎯 Executive Summary

This plan addresses the three HIGH PRIORITY issues identified in BEST_PRACTICES_ANALYSIS.md:

1. **Singleton Pattern Fix** (2-4 hours) - Thread-safety issue
2. **NLP Abstraction Layer** (1-2 days) - Dependency Inversion Principle
3. **Split unified_solver.py** (2-3 days) - Single Responsibility Principle

**Goals:**
- Improve maintainability and testability
- Fix thread-safety issues
- Reduce coupling to external libraries
- Follow SOLID principles
- Maintain 100% backward compatibility
- Keep all 25/25 tests passing

---

## 📋 Overview of Issues

### Issue #1: Singleton Pattern (Thread-Unsafe)

**Current Code:** `unified_word_filtering.py`

```python
_filter_instance = None  # Global singleton

def get_unified_filter():
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = UnifiedFilter()  # Race condition!
    return _filter_instance
```

**Problems:**
- 🔴 Race condition in multi-threaded applications
- 🔴 Difficult to test (global state persists)
- 🔴 Cannot have multiple filter configurations

**Impact:** HIGH (thread-safety bug)

---

### Issue #2: NLP Abstraction Missing (DIP Violation)

**Current Code:** `intelligent_word_filter.py`

```python
class IntelligentWordFilter:
    def __init__(self, use_gpu=True):
        import spacy  # Tightly coupled!
        self.nlp = spacy.load("en_core_web_md")
        
    def analyze(self, text):
        doc = self.nlp(text)  # spaCy-specific API
        for token in doc:
            if token.pos_ == "PROPN":  # spaCy attribute
                return True
```

**Problems:**
- 🔴 Cannot swap NLP backends (locked to spaCy)
- 🔴 Difficult to test (requires spaCy installation)
- 🔴 Coupled to spaCy API changes
- 🟡 No abstraction layer

**Impact:** HIGH (maintainability, testability)

---

### Issue #3: God Object (SRP Violation)

**Current Code:** `unified_solver.py` (1,590 lines)

```python
class UnifiedSpellingBeeSolver:
    # Responsibility 1: Configuration
    def __init__(self, mode, config_file):
        self.config = self._load_config()
    
    # Responsibility 2: Dictionary loading
    def load_dictionary(self, path): ...
    
    # Responsibility 3: Input validation
    def solve_puzzle(self, letters, required_letter):
        # Validates input
    
    # Responsibility 4: Candidate generation
    # Responsibility 5: Filtering orchestration
    # Responsibility 6: Confidence scoring
    # Responsibility 7: Result formatting
    # Responsibility 8: Interactive mode
```

**Problems:**
- 🔴 Too many responsibilities (violates SRP)
- 🔴 1,590 lines in single file
- 🔴 Difficult to test individual components
- 🔴 Changes ripple throughout class

**Impact:** HIGH (maintainability, testability, readability)

---

## 🚀 Refactoring Strategy

### Phase 1: Quick Win - Fix Singleton Pattern

**Estimated Time:** 2-4 hours

**Approach:** Replace with dependency injection

**Files to Modify:**
- `src/spelling_bee_solver/unified_word_filtering.py`
- `src/spelling_bee_solver/unified_solver.py` (injection point)

**Steps:**

1. Remove global singleton
2. Add factory function with configuration support
3. Update unified_solver.py to create/inject filter
4. Ensure backward compatibility with factory function
5. Add thread-safety test

**Testing:**
- All existing tests must pass
- Add new thread-safety test

---

### Phase 2: Add NLP Abstraction Layer

**Estimated Time:** 1-2 days

**Approach:** Create abstract base class for NLP providers

**Files to Create:**
- `src/spelling_bee_solver/nlp/nlp_provider.py` (ABC)
- `src/spelling_bee_solver/nlp/spacy_provider.py` (implementation)
- `src/spelling_bee_solver/nlp/mock_provider.py` (for testing)

**Files to Modify:**
- `src/spelling_bee_solver/intelligent_word_filter.py`

**Steps:**

1. **Create NLPProvider ABC**
   ```python
   class NLPProvider(ABC):
       @abstractmethod
       def process_text(self, text: str) -> Document: ...
   ```

2. **Create Document/Token/Entity abstractions**
   ```python
   class Document(ABC):
       @abstractmethod
       def get_tokens(self) -> List[Token]: ...
       @abstractmethod
       def get_entities(self) -> List[Entity]: ...
   ```

3. **Implement SpacyNLPProvider**
   - Wraps existing spaCy functionality
   - Adapts spaCy API to our abstractions

4. **Implement MockNLPProvider**
   - Simple mock for testing
   - No external dependencies

5. **Update IntelligentWordFilter**
   - Accept NLPProvider in constructor
   - Use abstract API instead of spaCy directly
   - Maintain backward compatibility (default to SpacyNLPProvider)

**Testing:**
- All existing tests must pass
- Add tests using MockNLPProvider
- Verify spaCy still works correctly

---

### Phase 3: Split unified_solver.py

**Estimated Time:** 2-3 days

**Approach:** Extract focused classes, keep orchestrator

**Files to Create:**
- `src/spelling_bee_solver/core/input_validator.py`
- `src/spelling_bee_solver/core/dictionary_manager.py`
- `src/spelling_bee_solver/core/candidate_generator.py`
- `src/spelling_bee_solver/core/confidence_scorer.py`
- `src/spelling_bee_solver/core/result_formatter.py`

**Files to Modify:**
- `src/spelling_bee_solver/unified_solver.py` (orchestrator only)

**Architecture:**

```
┌─────────────────────────────────────────────────────┐
│         UnifiedSpellingBeeSolver                    │
│              (Orchestrator Only)                    │
│                                                     │
│  - Coordinates all components                       │
│  - No business logic                               │
│  - Pure delegation                                 │
└────────────┬────────────────────────────────────────┘
             │
             ├──► InputValidator
             │    - validate_letters()
             │    - validate_required_letter()
             │
             ├──► DictionaryManager
             │    - load_dictionary()
             │    - cache_dictionary()
             │    - download_dictionary()
             │
             ├──► CandidateGenerator
             │    - generate_candidates()
             │    - apply_basic_rules()
             │
             ├──► FilterCoordinator
             │    - apply_comprehensive_filter()
             │    - coordinate_filters()
             │
             ├──► ConfidenceScorer
             │    - calculate_confidence()
             │    - score_all()
             │
             └──► ResultFormatter
                  - print_results()
                  - format_json()
                  - group_by_length()
```

**Steps:**

1. **Extract InputValidator**
   - Move validation logic
   - Keep validation constants
   - Add comprehensive tests

2. **Extract DictionaryManager**
   - Move load_dictionary()
   - Move caching logic
   - Move download logic
   - Keep dictionary_sources

3. **Extract CandidateGenerator**
   - Move candidate generation logic
   - Keep basic filtering rules

4. **Extract ConfidenceScorer**
   - Move calculate_confidence()
   - Move confidence constants
   - Add configuration support

5. **Extract ResultFormatter**
   - Move print_results()
   - Move formatting logic
   - Add alternative formats (JSON, CSV)

6. **Refactor UnifiedSpellingBeeSolver**
   - Accept components via dependency injection
   - Pure orchestration logic
   - Coordinate component calls
   - Maintain solve_puzzle() public API

**Testing:**
- All 25/25 tests must still pass
- Add unit tests for each new class
- Add integration tests
- Test backward compatibility

---

## 📐 Detailed Design

### Phase 1 Design: Singleton Fix

**Before:**

```python
# unified_word_filtering.py
_filter_instance = None

def get_unified_filter():
    global _filter_instance
    if _filter_instance is None:
        _filter_instance = UnifiedFilter()
    return _filter_instance

# Usage in unified_solver.py
filter = get_unified_filter()
```

**After:**

```python
# unified_word_filtering.py
def create_word_filter(use_gpu: bool = True, config: Optional[dict] = None):
    """Factory function to create word filter (NOT singleton)"""
    return UnifiedFilter(use_gpu=use_gpu, config=config)

# Backward compatibility
def get_unified_filter():
    """Deprecated: Use create_word_filter() instead"""
    import warnings
    warnings.warn(
        "get_unified_filter() is deprecated. Use create_word_filter()",
        DeprecationWarning
    )
    return create_word_filter()

# Usage in unified_solver.py
class UnifiedSpellingBeeSolver:
    def __init__(self, ..., word_filter=None):
        # Dependency injection
        self.word_filter = word_filter or create_word_filter(use_gpu=self.use_gpu)
```

**Benefits:**
- ✅ Thread-safe (no global state)
- ✅ Testable (can inject mock)
- ✅ Configurable (per-instance config)
- ✅ Backward compatible (deprecation warning)

---

### Phase 2 Design: NLP Abstraction

**New Files Structure:**

```
src/spelling_bee_solver/nlp/
├── __init__.py
├── nlp_provider.py      # ABC
├── spacy_provider.py    # spaCy implementation
└── mock_provider.py     # Testing implementation
```

**nlp_provider.py:**

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class Token:
    """Abstract token representation"""
    text: str
    pos: str  # Part of speech
    is_proper_noun: bool
    is_oov: bool  # Out of vocabulary

@dataclass
class Entity:
    """Abstract named entity representation"""
    text: str
    label: str  # PERSON, ORG, GPE, etc.

class Document(ABC):
    """Abstract document representation"""
    
    @abstractmethod
    def get_tokens(self) -> List[Token]:
        """Get list of tokens in document"""
        pass
    
    @abstractmethod
    def get_entities(self) -> List[Entity]:
        """Get list of named entities"""
        pass
    
    @abstractmethod
    def find_token(self, text: str) -> Optional[Token]:
        """Find specific token by text"""
        pass

class NLPProvider(ABC):
    """Abstract NLP provider interface"""
    
    @abstractmethod
    def process_text(self, text: str) -> Document:
        """Process text and return document"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if NLP backend is available"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Get provider name for logging"""
        pass
```

**spacy_provider.py:**

```python
import spacy
from .nlp_provider import NLPProvider, Document, Token, Entity

class SpacyDocument(Document):
    """spaCy implementation of Document"""
    
    def __init__(self, spacy_doc):
        self._doc = spacy_doc
    
    def get_tokens(self) -> List[Token]:
        return [
            Token(
                text=token.text,
                pos=token.pos_,
                is_proper_noun=(token.pos_ == "PROPN"),
                is_oov=token.is_oov
            )
            for token in self._doc
        ]
    
    def get_entities(self) -> List[Entity]:
        return [
            Entity(text=ent.text, label=ent.label_)
            for ent in self._doc.ents
        ]
    
    def find_token(self, text: str) -> Optional[Token]:
        for token in self._doc:
            if token.text.lower() == text.lower():
                return Token(
                    text=token.text,
                    pos=token.pos_,
                    is_proper_noun=(token.pos_ == "PROPN"),
                    is_oov=token.is_oov
                )
        return None

class SpacyNLPProvider(NLPProvider):
    """spaCy implementation of NLP provider"""
    
    def __init__(self, model_name: str = "en_core_web_md", use_gpu: bool = True):
        self.model_name = model_name
        self.use_gpu = use_gpu
        self._nlp = None
    
    def _load_model(self):
        """Lazy load spaCy model"""
        if self._nlp is None:
            if self.use_gpu:
                spacy.require_gpu()
            self._nlp = spacy.load(self.model_name)
            self._nlp.max_length = 2_000_000
    
    def process_text(self, text: str) -> Document:
        self._load_model()
        doc = self._nlp(text)
        return SpacyDocument(doc)
    
    def is_available(self) -> bool:
        try:
            import spacy
            return True
        except ImportError:
            return False
    
    def get_name(self) -> str:
        return f"spaCy ({self.model_name})"
```

**mock_provider.py:**

```python
from .nlp_provider import NLPProvider, Document, Token, Entity

class MockDocument(Document):
    """Mock document for testing"""
    
    def __init__(self, text: str, tokens: List[Token] = None, entities: List[Entity] = None):
        self.text = text
        self._tokens = tokens or []
        self._entities = entities or []
    
    def get_tokens(self) -> List[Token]:
        return self._tokens
    
    def get_entities(self) -> List[Entity]:
        return self._entities
    
    def find_token(self, text: str) -> Optional[Token]:
        for token in self._tokens:
            if token.text.lower() == text.lower():
                return token
        return None

class MockNLPProvider(NLPProvider):
    """Mock NLP provider for testing"""
    
    def __init__(self):
        self.processed_texts = []  # Track calls for testing
        self.proper_nouns = set()  # Configurable proper nouns
    
    def process_text(self, text: str) -> Document:
        self.processed_texts.append(text)
        
        # Simple word extraction
        words = text.split()
        tokens = [
            Token(
                text=word,
                pos="PROPN" if word in self.proper_nouns else "NOUN",
                is_proper_noun=(word in self.proper_nouns),
                is_oov=False
            )
            for word in words
        ]
        
        entities = [
            Entity(text=word, label="PERSON")
            for word in words
            if word in self.proper_nouns
        ]
        
        return MockDocument(text, tokens, entities)
    
    def is_available(self) -> bool:
        return True
    
    def get_name(self) -> str:
        return "Mock NLP Provider"
```

**Update intelligent_word_filter.py:**

```python
from .nlp.nlp_provider import NLPProvider
from .nlp.spacy_provider import SpacyNLPProvider

class IntelligentWordFilter:
    def __init__(self, nlp_provider: Optional[NLPProvider] = None, use_gpu: bool = True):
        """
        Initialize intelligent word filter
        
        Args:
            nlp_provider: NLP provider to use. If None, defaults to SpacyNLPProvider
            use_gpu: Whether to use GPU acceleration (for default provider)
        """
        if nlp_provider is None:
            # Default to spaCy for backward compatibility
            nlp_provider = SpacyNLPProvider(use_gpu=use_gpu)
        
        self.nlp_provider = nlp_provider
        self.logger = logging.getLogger(__name__)
    
    def is_proper_noun_intelligent(self, word: str, context: Optional[str] = None) -> bool:
        """Check if word is proper noun using NLP"""
        text = context if context else f"The {word} is here."
        doc = self.nlp_provider.process_text(text)
        
        # Find target word token
        target = doc.find_token(word)
        if target and target.is_proper_noun:
            return True
        
        # Check named entities
        for entity in doc.get_entities():
            if word.lower() in entity.text.lower():
                if entity.label in ["PERSON", "ORG", "GPE", "NORP"]:
                    return True
        
        return False
```

**Benefits:**
- ✅ Can swap NLP backends
- ✅ Easy to test (MockNLPProvider)
- ✅ Not coupled to spaCy API
- ✅ Backward compatible (defaults to spaCy)

---

### Phase 3 Design: Split unified_solver.py

**New Directory Structure:**

```
src/spelling_bee_solver/
├── core/
│   ├── __init__.py
│   ├── input_validator.py
│   ├── dictionary_manager.py
│   ├── candidate_generator.py
│   ├── confidence_scorer.py
│   └── result_formatter.py
├── unified_solver.py (refactored)
└── ... (existing files)
```

**core/input_validator.py:**

```python
from typing import Tuple

class InputValidator:
    """Validates puzzle inputs according to NYT Spelling Bee rules"""
    
    def validate_letters(self, letters: str) -> str:
        """
        Validate puzzle letters
        
        Args:
            letters: The 7 puzzle letters
            
        Returns:
            Normalized letters (lowercase)
            
        Raises:
            TypeError: If letters is not a string
            ValueError: If letters is invalid
        """
        if not isinstance(letters, str):
            raise TypeError(f"Letters must be a string, got {type(letters).__name__}")
        
        if len(letters) != 7:
            raise ValueError(f"Must provide exactly 7 letters, got {len(letters)}")
        
        if not letters.isalpha():
            raise ValueError(f"Letters must be alphabetic, got '{letters}'")
        
        return letters.lower()
    
    def validate_required_letter(self, required_letter: str, letters: str) -> str:
        """
        Validate required letter
        
        Args:
            required_letter: The required letter
            letters: The puzzle letters (already validated)
            
        Returns:
            Normalized required letter (lowercase)
            
        Raises:
            TypeError: If required_letter is not a string
            ValueError: If required_letter is invalid
        """
        if not isinstance(required_letter, str):
            raise TypeError(
                f"Required letter must be a string, got {type(required_letter).__name__}"
            )
        
        if len(required_letter) != 1:
            raise ValueError(
                f"Required letter must be exactly 1 character, got {len(required_letter)}"
            )
        
        if not required_letter.isalpha():
            raise ValueError(
                f"Required letter must be alphabetic, got '{required_letter}'"
            )
        
        required_lower = required_letter.lower()
        if required_lower not in letters.lower():
            raise ValueError(
                f"Required letter '{required_letter}' must be one of the 7 "
                f"puzzle letters: {letters}"
            )
        
        return required_lower
    
    def validate_and_normalize(self, letters: str, required_letter: str) -> Tuple[str, str, set]:
        """
        Validate and normalize both inputs
        
        Returns:
            Tuple of (letters_lower, required_lower, letters_set)
        """
        letters_lower = self.validate_letters(letters)
        required_lower = self.validate_required_letter(required_letter, letters_lower)
        letters_set = set(letters_lower)
        
        return letters_lower, required_lower, letters_set
```

**core/dictionary_manager.py:**

```python
import hashlib
import json
import requests
from pathlib import Path
from typing import Set, Optional
import time

class DictionaryManager:
    """Manages dictionary loading, caching, and downloading"""
    
    def __init__(self, cache_dir: str = ".dictionary_cache", cache_expiry_days: int = 30):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_expiry_seconds = cache_expiry_days * 24 * 3600
        self.logger = logging.getLogger(__name__)
    
    def load_dictionary(self, path: str) -> Set[str]:
        """
        Load dictionary from path (local file or URL)
        
        Args:
            path: Local file path or URL
            
        Returns:
            Set of words (lowercase)
        """
        if path.startswith("http"):
            return self._load_from_url(path)
        else:
            return self._load_from_file(path)
    
    def _load_from_file(self, path: str) -> Set[str]:
        """Load dictionary from local file"""
        file_path = Path(path)
        if not file_path.exists():
            self.logger.warning(f"Dictionary not found: {path}")
            return set()
        
        try:
            if path.endswith('.json'):
                with open(file_path) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return {word.lower() for word in data if isinstance(word, str)}
                    elif isinstance(data, dict):
                        return {word.lower() for word in data.keys()}
            else:
                # Plain text file
                with open(file_path) as f:
                    return {
                        word.strip().lower()
                        for word in f
                        if word.strip()
                    }
        except Exception as e:
            self.logger.error(f"Error loading dictionary {path}: {e}")
            return set()
    
    def _load_from_url(self, url: str) -> Set[str]:
        """Load dictionary from URL with caching"""
        cache_file = self._get_cache_path(url)
        
        # Check cache
        if cache_file.exists():
            cache_age = time.time() - cache_file.stat().st_mtime
            if cache_age < self.cache_expiry_seconds:
                self.logger.info(f"Loading from cache: {cache_file.name}")
                return self._load_from_file(str(cache_file))
        
        # Download
        self.logger.info(f"Downloading dictionary: {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to cache
            with open(cache_file, 'w') as f:
                f.write(response.text)
            
            # Parse
            words = {
                word.strip().lower()
                for word in response.text.split('\n')
                if word.strip()
            }
            
            return words
        
        except Exception as e:
            self.logger.error(f"Error downloading dictionary {url}: {e}")
            
            # Try to use stale cache
            if cache_file.exists():
                self.logger.info("Using stale cache")
                return self._load_from_file(str(cache_file))
            
            return set()
    
    def _get_cache_path(self, url: str) -> Path:
        """Get cache file path for URL"""
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.txt"
```

**core/confidence_scorer.py:**

```python
from typing import Callable, Optional

class ConfidenceScorer:
    """Calculates confidence scores for words"""
    
    # Default constants
    DEFAULT_BASE = 50.0
    DEFAULT_LENGTH_BONUS = 10.0
    DEFAULT_LENGTH_THRESHOLD = 6
    DEFAULT_REJECTION_PENALTY = 30.0
    
    def __init__(
        self,
        rejection_checker: Callable[[str], bool],
        base_score: float = DEFAULT_BASE,
        length_bonus: float = DEFAULT_LENGTH_BONUS,
        length_threshold: int = DEFAULT_LENGTH_THRESHOLD,
        rejection_penalty: float = DEFAULT_REJECTION_PENALTY
    ):
        """
        Initialize confidence scorer
        
        Args:
            rejection_checker: Function that returns True if word should be rejected
            base_score: Starting confidence score
            length_bonus: Bonus for long words
            length_threshold: Minimum length for bonus
            rejection_penalty: Penalty for rejected words
        """
        self.rejection_checker = rejection_checker
        self.base_score = base_score
        self.length_bonus = length_bonus
        self.length_threshold = length_threshold
        self.rejection_penalty = rejection_penalty
    
    def calculate_confidence(self, word: str) -> float:
        """
        Calculate confidence score for a word
        
        Args:
            word: The word to score
            
        Returns:
            Confidence score between 0.0 and 100.0
        """
        # Input validation
        if not isinstance(word, str):
            raise TypeError(f"Word must be a string, got {type(word).__name__}")
        if not word.strip():
            raise ValueError("Word cannot be empty or whitespace")
        if not word.isalpha():
            raise ValueError(f"Word must contain only alphabetic characters: '{word}'")
        
        word = word.lower()
        confidence = self.base_score
        
        # Length-based confidence
        if len(word) >= self.length_threshold:
            confidence += self.length_bonus
        
        # Penalize likely rejected words
        if self.rejection_checker(word):
            confidence -= self.rejection_penalty
        
        return min(100.0, max(0.0, confidence))
    
    def score_all(self, words: List[str]) -> Dict[str, float]:
        """
        Score all words
        
        Returns:
            Dict mapping word -> confidence score
        """
        return {word: self.calculate_confidence(word) for word in words}
```

**Refactored unified_solver.py (Orchestrator):**

```python
class UnifiedSpellingBeeSolver:
    """Main orchestrator for Spelling Bee solving (Pure coordination)"""
    
    def __init__(
        self,
        mode: SolverMode = SolverMode.PRODUCTION,
        config_file: str = "solver_config.json",
        verbose: bool = False,
        # Dependency injection (optional, with defaults)
        input_validator: Optional[InputValidator] = None,
        dictionary_manager: Optional[DictionaryManager] = None,
        candidate_generator: Optional[CandidateGenerator] = None,
        confidence_scorer: Optional[ConfidenceScorer] = None,
        result_formatter: Optional[ResultFormatter] = None,
        word_filter = None
    ):
        """
        Initialize solver with dependency injection
        
        All components optional with sensible defaults for backward compatibility
        """
        self.mode = mode
        self.verbose = verbose
        self.logger = self._setup_logging()
        
        # Initialize or inject components
        self.validator = input_validator or InputValidator()
        self.dict_manager = dictionary_manager or DictionaryManager()
        self.generator = candidate_generator or CandidateGenerator()
        self.scorer = confidence_scorer or self._create_default_scorer()
        self.formatter = result_formatter or ResultFormatter(verbose=verbose)
        self.word_filter = word_filter or create_word_filter(use_gpu=True)
        
        # Load config
        self.config = self._load_config(config_file)
        self.dictionary_sources = self._get_dictionary_sources()
        
        # Statistics
        self.stats = {}
    
    def solve_puzzle(
        self, letters: str, required_letter: Optional[str] = None
    ) -> List[Tuple[str, float]]:
        """
        Solve puzzle (Pure orchestration - delegates to components)
        
        Args:
            letters: 7 puzzle letters
            required_letter: Required letter (defaults to first)
            
        Returns:
            Sorted list of (word, confidence) tuples
        """
        start_time = time.time()
        
        # Step 1: Validate input (delegate to validator)
        letters_lower, required_lower, letters_set = self.validator.validate_and_normalize(
            letters, required_letter or letters[0]
        )
        
        # Step 2: Load dictionaries (delegate to dictionary manager)
        all_valid_words = {}
        for dict_name, dict_path in self.dictionary_sources:
            self.logger.info(f"Processing {dict_name}")
            dictionary = self.dict_manager.load_dictionary(dict_path)
            
            if not dictionary:
                continue
            
            # Step 3: Generate candidates (delegate to generator)
            candidates = self.generator.generate_candidates(
                dictionary, letters_set, required_lower
            )
            
            if not candidates:
                continue
            
            # Step 4: Apply filters (delegate to word filter)
            filtered = self.word_filter.filter_words(candidates)
            
            # Step 5: Score and store (delegate to scorer)
            for word in filtered:
                if word not in all_valid_words:
                    confidence = self.scorer.calculate_confidence(word)
                    all_valid_words[word] = confidence
        
        # Step 6: Sort results
        valid_words = list(all_valid_words.items())
        valid_words.sort(key=lambda x: (-x[1], -len(x[0]), x[0]))
        
        # Step 7: Update stats
        solve_time = time.time() - start_time
        self.stats["solve_time"] = solve_time
        
        self.logger.info(
            f"Solving complete: {len(valid_words)} words found in {solve_time:.3f}s"
        )
        
        return valid_words
    
    def print_results(self, results, letters, required_letter):
        """Print results (delegate to formatter)"""
        self.formatter.print_results(results, letters, required_letter, self.stats)
```

**Benefits:**
- ✅ Each class has ONE responsibility
- ✅ Easy to test in isolation
- ✅ UnifiedSpellingBeeSolver is pure orchestration
- ✅ Backward compatible (default dependencies)
- ✅ Dependency injection allows customization

---

## ✅ Testing Strategy

### Phase 1 Testing: Singleton Fix

**Tests to Add:**

```python
def test_thread_safety():
    """Test that multiple threads can create filters safely"""
    import threading
    
    filters = []
    def create_filter():
        f = create_word_filter()
        filters.append(f)
    
    threads = [threading.Thread(target=create_filter) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(filters) == 10
    assert all(f is not None for f in filters)

def test_multiple_configurations():
    """Test that different configurations can coexist"""
    filter1 = create_word_filter(use_gpu=True)
    filter2 = create_word_filter(use_gpu=False)
    
    # Both should work independently
    assert filter1 is not filter2
```

**Existing Tests:**
- All 25/25 filtering tests must still pass
- No behavioral changes

---

### Phase 2 Testing: NLP Abstraction

**Tests to Add:**

```python
def test_mock_nlp_provider():
    """Test filtering with mock NLP provider"""
    mock_nlp = MockNLPProvider()
    mock_nlp.proper_nouns = {"NASA", "London"}
    
    filter = IntelligentWordFilter(nlp_provider=mock_nlp)
    
    assert filter.is_proper_noun_intelligent("NASA") == True
    assert filter.is_proper_noun_intelligent("hello") == False
    assert len(mock_nlp.processed_texts) == 2  # Verify calls

def test_spacy_provider_wrapper():
    """Test that spaCy provider works correctly"""
    spacy_nlp = SpacyNLPProvider()
    
    doc = spacy_nlp.process_text("London is a city.")
    entities = doc.get_entities()
    
    assert any(e.text == "London" and e.label == "GPE" for e in entities)

def test_backward_compatibility():
    """Test that default behavior hasn't changed"""
    # Old way (should still work)
    filter = IntelligentWordFilter(use_gpu=False)
    result = filter.is_proper_noun_intelligent("NASA")
    assert result == True
```

**Existing Tests:**
- All 25/25 filtering tests must still pass
- 6/7 NER tests must still pass

---

### Phase 3 Testing: Split unified_solver.py

**Tests to Add (per component):**

```python
# test_input_validator.py
def test_validate_letters_valid():
    validator = InputValidator()
    assert validator.validate_letters("ABCDEFG") == "abcdefg"

def test_validate_letters_invalid_length():
    validator = InputValidator()
    with pytest.raises(ValueError, match="exactly 7 letters"):
        validator.validate_letters("ABC")

# test_dictionary_manager.py
def test_load_from_file():
    manager = DictionaryManager()
    words = manager.load_dictionary("test_dict.txt")
    assert len(words) > 0
    assert all(w.islower() for w in words)

def test_cache_expiry():
    manager = DictionaryManager(cache_expiry_days=0)
    # Test that cache expires correctly

# test_candidate_generator.py
def test_generate_candidates_basic():
    generator = CandidateGenerator()
    dictionary = {"hello", "world", "test", "hi"}
    letters_set = {"h", "e", "l", "o", "w"}
    required = "h"
    
    candidates = generator.generate_candidates(dictionary, letters_set, required)
    
    assert "hello" in candidates
    assert "world" not in candidates  # Missing 'r', 'd'
    assert "hi" not in candidates  # Too short

# test_confidence_scorer.py
def test_calculate_confidence_basic():
    scorer = ConfidenceScorer(rejection_checker=lambda w: False)
    
    assert scorer.calculate_confidence("help") == 50.0
    assert scorer.calculate_confidence("helper") == 60.0

def test_calculate_confidence_rejected():
    scorer = ConfidenceScorer(rejection_checker=lambda w: w == "NASA")
    
    assert scorer.calculate_confidence("hello") == 50.0
    assert scorer.calculate_confidence("NASA") == 20.0

# test_unified_solver_refactored.py
def test_backward_compatibility():
    """Test that public API hasn't changed"""
    solver = UnifiedSpellingBeeSolver()
    results = solver.solve_puzzle("ABCDEFG", "A")
    
    assert isinstance(results, list)
    assert all(isinstance(item, tuple) and len(item) == 2 for item in results)

def test_dependency_injection():
    """Test that components can be injected"""
    mock_validator = MockInputValidator()
    solver = UnifiedSpellingBeeSolver(input_validator=mock_validator)
    
    results = solver.solve_puzzle("ABCDEFG", "A")
    assert mock_validator.validate_called == True
```

**Integration Tests:**

```python
def test_end_to_end_solving():
    """Test complete solving pipeline"""
    solver = UnifiedSpellingBeeSolver(mode=SolverMode.DEBUG_SINGLE)
    results = solver.solve_puzzle("ABCDEFG", "A")
    
    assert len(results) > 0
    assert all(0 <= conf <= 100 for word, conf in results)
    assert all(len(word) >= 4 for word, conf in results)
    assert all("A" in word.upper() for word, conf in results)
```

**Existing Tests:**
- **ALL 25/25 filtering tests MUST pass**
- **All integration tests MUST pass**
- No regressions allowed

---

## 📅 Implementation Schedule

### Week 1

**Day 1 (2-4 hours): Phase 1 - Singleton Fix**
- [ ] Remove global singleton
- [ ] Add create_word_filter() factory
- [ ] Update unified_solver.py to inject filter
- [ ] Add backward compatibility shim
- [ ] Add thread-safety tests
- [ ] Verify all 25/25 tests pass

**Day 2-3 (1-2 days): Phase 2 - NLP Abstraction**
- [ ] Create nlp/ directory structure
- [ ] Implement NLPProvider ABC
- [ ] Implement SpacyNLPProvider
- [ ] Implement MockNLPProvider
- [ ] Update IntelligentWordFilter
- [ ] Add unit tests for providers
- [ ] Verify all tests pass

### Week 2

**Day 4-6 (2-3 days): Phase 3 - Split unified_solver.py**
- [ ] Create core/ directory
- [ ] Extract InputValidator
- [ ] Extract DictionaryManager
- [ ] Extract CandidateGenerator
- [ ] Extract ConfidenceScorer
- [ ] Extract ResultFormatter
- [ ] Refactor UnifiedSpellingBeeSolver
- [ ] Add unit tests for each component
- [ ] Add integration tests
- [ ] Verify ALL tests pass

**Day 7: Final Verification**
- [ ] Run complete test suite
- [ ] Performance benchmarking
- [ ] Documentation updates
- [ ] Code review
- [ ] Commit and deploy

---

## 🚨 Risk Management

### Risk 1: Breaking Backward Compatibility

**Mitigation:**
- Keep public API unchanged
- Add deprecation warnings, not immediate removal
- Provide migration guide
- Extensive testing

### Risk 2: Performance Regression

**Mitigation:**
- Benchmark before and after
- Measure solve times for standard puzzles
- Ensure no significant slowdown (< 5%)

### Risk 3: Test Failures

**Mitigation:**
- Run tests after each small change
- Don't proceed if tests fail
- Keep changes small and incremental

### Risk 4: Scope Creep

**Mitigation:**
- Stick to the plan
- No additional features during refactoring
- Focus on structure, not new functionality

---

## ✅ Success Criteria

1. **All tests pass** (25/25 filtering tests)
2. **Backward compatibility maintained** (public API unchanged)
3. **Performance preserved** (< 5% slowdown acceptable)
4. **Code quality improved** (measured by complexity metrics)
5. **Documentation updated** (audit docs reflect new architecture)

---

## 📚 References

- BEST_PRACTICES_ANALYSIS.md - Original analysis
- MASTER_SYSTEM_AUDIT.md - Current architecture
- FILTERING_SYSTEM_AUDIT.md - Filtering details
- POST_PROCESSING_SYSTEM_AUDIT.md - Post-processing details

---

**Plan Created:** October 1, 2025  
**Status:** READY TO IMPLEMENT  
**Next Step:** Begin Phase 1 (Singleton Fix)

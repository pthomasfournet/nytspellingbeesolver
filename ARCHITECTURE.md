# Spelling Bee Solver Architecture

## Overview

The Spelling Bee Solver is built using SOLID principles with clean separation of concerns. **unified_solver.py** is the orchestrator that coordinates specialized components.

## Architecture Pattern: Dependency Injection

```
unified_solver.py (Orchestrator - 1,292 lines)
    ├─ Coordinates all components
    ├─ Manages configuration
    ├─ Provides public API
    └─ Delegates to specialized modules
```

## Core Components (core/)

All core components follow the Single Responsibility Principle:

### 1. **InputValidator** (341 lines)
- **Responsibility:** Validate puzzle inputs
- **What it does:**
  - Validates 7 unique letters
  - Validates required letter is in puzzle
  - Normalizes to lowercase
- **Used by:** unified_solver.solve_puzzle()

### 2. **DictionaryManager** (397 lines)
- **Responsibility:** Load and cache dictionaries
- **What it does:**
  - Downloads Webster's dictionary
  - Loads ASPELL dictionary
  - Caches to disk
- **Used by:** unified_solver.load_dictionary()

### 3. **CandidateGenerator** (454 lines)
- **Responsibility:** Generate candidate words from letters
- **What it does:**
  - Filters by basic rules (length ≥4, has required, uses only available)
  - Uses PhonotacticFilter for English letter patterns
  - Deduplicates across dictionaries
- **Used by:** unified_solver.solve_puzzle()

### 4. **ConfidenceScorer** (247 lines)
- **Responsibility:** Score word confidence using multi-criteria evaluation
- **What it does:**
  - 5 criteria: Dictionary, Frequency, Length, Pattern, Filter
  - Drops highest and lowest scores, averages middle 3
  - Returns score 0-100
- **Used by:** unified_solver.solve_puzzle()

### 5. **NYTRejectionFilter** (254 lines)
- **Responsibility:** Detect words NYT Spelling Bee typically rejects
- **What it does:**
  - Detects proper nouns (people, places)
  - Detects foreign words
  - Detects abbreviations
  - Flags archaic words (low confidence, not rejected)
- **Used by:** unified_solver.solve_puzzle()

### 6. **PhonotacticFilter** (443 lines)
- **Responsibility:** Filter impossible English letter sequences
- **What it does:**
  - Rejects triple letters (ttt, ooo)
  - Rejects impossible doubles (jj, qq, xx)
  - Validates consonant clusters
- **Used by:** CandidateGenerator

### 7. **ResultFormatter** (508 lines)
- **Responsibility:** Format output for display
- **What it does:**
  - Groups words by length
  - Highlights pangrams
  - Formats confidence scores
  - Displays statistics
- **Used by:** unified_solver.print_results()

## GPU/NLP Components

### 1. **IntelligentWordFilter** (intelligent_word_filter.py, 733 lines)
- **Responsibility:** GPU-accelerated intelligent word filtering
- **What it does:**
  - Uses NLP abstraction layer (dependency inversion)
  - spaCy NLP pipeline for linguistic analysis
  - POS tagging for proper noun detection
  - Named entity recognition (organizations, locations, people)
  - Acronym and abbreviation detection
  - Pattern-based nonsense word detection
  - GPU-accelerated when available (via cupy)
  - Graceful CPU fallback
- **Used by:** unified_solver._apply_comprehensive_filter() (when GPU enabled)

### 2. **NLP Abstraction Layer** (nlp/, 643 lines)
- **Responsibility:** Abstract NLP provider interface (Dependency Inversion Principle)
- **What it provides:**
  - NLPProvider: Abstract base class
  - SpacyNLPProvider: spaCy implementation
  - MockNLPProvider: Mock for testing
  - Document, Token, Entity: Abstract data classes
- **Used by:** IntelligentWordFilter
- **Purpose:** Decouples intelligent_word_filter from spaCy implementation, enables testing

## Main Flow: solve_puzzle()

```python
unified_solver.solve_puzzle(required_letter, letters)
    ↓
1. INPUT VALIDATION
   InputValidator.validate_and_normalize()
   └─ Returns: normalized letters, required letter, letters set
    ↓
2. CANDIDATE GENERATION
   _generate_candidates_comprehensive()
   └─ Loads Webster's + ASPELL dictionaries
   └─ CandidateGenerator filters by basic rules
   └─ PhonotacticFilter removes impossible sequences
   └─ Returns: candidate words (typically 100-300)
    ↓
3. GPU FILTERING (Optional)
   IF GPU enabled:
       intelligent_word_filter.filter_words_intelligent()
       └─ spaCy NLP analysis
       └─ Returns: filtered candidates
    ↓
4. NYT REJECTION FILTERING
   FOR EACH candidate:
       NYTRejectionFilter.should_reject(word)
       └─ Rejects proper nouns, foreign words, abbreviations
       └─ IF rejected: skip word
       └─ IF archaic: flag for low confidence
    ↓
5. CONFIDENCE SCORING
   FOR EACH valid candidate:
       ConfidenceScorer.calculate_confidence(word)
       └─ 5 criteria evaluate word
       └─ Drop outliers, average middle 3
       └─ Returns: score 0-100
    ↓
6. SORTING
   Sort by:
   - Confidence (descending)
   - Length (descending)
   - Alphabetical
    ↓
7. RETURN
   List[(word, confidence)]
```

## Public API

### Primary Entry Point
```python
from spelling_bee_solver import UnifiedSpellingBeeSolver

solver = UnifiedSpellingBeeSolver()
results = solver.solve_puzzle("N", "ACUOTP")  # required_letter, other_letters
solver.print_results(results, "NACUOTP", "N")
```

### Core Components (for advanced usage)
```python
from spelling_bee_solver.core import (
    InputValidator,
    DictionaryManager,
    CandidateGenerator,
    ConfidenceScorer,
    NYTRejectionFilter,
    PhonotacticFilter,
    ResultFormatter,
)
```

## Configuration

Configuration loaded from `solver_config.json`:

```json
{
  "dictionaries": {
    "sources": ["websters", "aspell"]
  },
  "acceleration": {
    "force_gpu_off": false,
    "gpu_batch_size": 1000
  },
  "filtering": {
    "enable_nyt_rejection": true,
    "enable_phonotactic": true
  }
}
```

## Dependency Graph

```
UnifiedSpellingBeeSolver (Orchestrator)
├─── InputValidator
├─── DictionaryManager
├─── CandidateGenerator
│    └─── PhonotacticFilter
├─── ConfidenceScorer
│    └─── NYTRejectionFilter
├─── NYTRejectionFilter
├─── ResultFormatter
└─── [Optional] IntelligentWordFilter
     └─── NLP Abstraction Layer
          ├─── SpacyNLPProvider (production)
          └─── MockNLPProvider (testing)
```

## Files and Line Counts

### Core (2,926 lines)
- input_validator.py (341)
- dictionary_manager.py (397)
- candidate_generator.py (454)
- confidence_scorer.py (247)
- nyt_rejection_filter.py (254)
- phonotactic_filter.py (443)
- result_formatter.py (508)
- __init__.py (25)

### GPU/NLP (~1,400 lines)
- intelligent_word_filter.py (733)
- nlp/ (provider abstraction, 643 lines)
  - nlp_provider.py (194) - Abstract base
  - spacy_provider.py (214) - spaCy implementation
  - mock_provider.py (204) - Testing mock
  - __init__.py (31)

### Main (1,292 lines)
- unified_solver.py (1,292)

### Legacy/Deprecated (238 lines)
- word_filtering.py (238) - DEPRECATED, has deprecation warnings

**Total:** ~5,400 lines of production code

## Design Principles

1. **Single Responsibility:** Each component has one clear purpose
2. **Dependency Injection:** Components are injected into UnifiedSpellingBeeSolver
3. **Open/Closed:** Easy to extend without modifying existing code
4. **Interface Segregation:** Factory functions provide clean interfaces
5. **Dependency Inversion:** Depend on abstractions (interfaces), not concretions

## Testing Strategy

```bash
# Run all tests
./venv/bin/pytest tests/ -v

# Test individual components
./venv/bin/pytest tests/test_basic.py -v
```

Tests verify:
- Core component functionality
- Integration between components
- Edge cases (empty input, invalid puzzles)
- GPU fallback behavior

## Performance

Typical solving times:
- **Unified mode:** 2-5 seconds
- **With GPU:** 1-3 seconds
- **CPU-only:** 3-10 seconds

Dictionaries:
- Webster's: ~235,000 words (downloaded on first run)
- ASPELL: System dictionary

## Future Improvements

1. **Anagram Generation:** Phase 5 - generate permutations of letters
2. **Google Common Words:** Load google-10000-common.txt for better frequency judging
3. **Dictionary Expansion:** Add more high-quality dictionaries
4. **GPU Optimization:** Batch processing improvements
5. **Caching:** Cache puzzle results for repeated solves

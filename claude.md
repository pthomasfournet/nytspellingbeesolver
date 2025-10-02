# NYT Spelling Bee Solver - Development Context

This document provides technical context for Claude Code or other AI assistants working on this codebase.

## Project Overview

A Python-based solver for NYT Spelling Bee puzzles, refactored from a complex multi-mode system to a clean unified architecture with intelligent filtering and confidence scoring.

## Current Architecture (Post-Refactoring)

### Core Philosophy

> "we should have webster and aspell and call it a day" - User requirement

- **Single unified mode** (no mode selection)
- **2 dictionaries only** (Webster's Unabridged + ASPELL American English)
- **Heuristic-based filtering** (not ML/training)
- **Olympic judges scoring** (multiple independent evaluations)
- **GPU-first with CPU fallback** (automatic)

### Pipeline Flow

```
Input (7 letters + required letter)
    ↓
Dictionary Scan (Webster's + ASPELL)
    ↓
Candidate Generation (from both dictionaries, deduplicated)
    ↓
Basic Validation (length ≥4, has required letter, uses only puzzle letters)
    ↓
NYT Rejection Filter (proper nouns, foreign words, abbreviations, technical terms)
    ↓
Enhanced Confidence Scorer (Olympic judges: 5 independent scores, drop outliers)
    ↓
Sorted Results (by confidence desc, then length desc, then alphabetically)
    ↓
Formatted Output (grouped by length, with pangrams highlighted)
```

## Key Components

### 1. UnifiedSpellingBeeSolver (`src/spelling_bee_solver/unified_solver.py`)

**Main orchestrator** (1,318 lines)

**Responsibilities:**
- Configuration loading
- Component initialization via dependency injection
- Dictionary management (2 dictionaries)
- Candidate generation (unified, deduplicated)
- Filtering and scoring pipeline
- Result formatting and display
- CLI interface (direct mode + interactive mode)

**Key Methods:**
- `__init__()`: Initialize with no mode parameter (unified by default)
- `solve_puzzle(letters, required_letter)`: Main entry point, returns `List[Tuple[str, float]]`
- `_generate_candidates_comprehensive()`: Unified generation from all dictionaries
- `_apply_comprehensive_filter()`: Multi-stage filtering pipeline
- `print_results()`: Formatted console output
- `interactive_mode()`: REPL for solving multiple puzzles
- `main()`: CLI entry point with argparse

**Configuration:**
- Loads from `solver_config.json` (falls back to defaults if missing)
- No mode configuration (always unified)
- GPU/CUDA settings
- Dictionary download/cache settings
- Filtering options
- Output formatting options

### 2. NYTRejectionFilter (`src/spelling_bee_solver/core/nyt_rejection_filter.py`)

**Detects words NYT Spelling Bee typically rejects**

**Detection Methods:**
- `is_proper_noun()`: Names, places (lloyd, anna, canaan)
- `is_foreign_word()`: Non-English words (detected by patterns + known list)
- `is_abbreviation()`: NASA, NCAA, govt, etc.
- `is_technical_term()`: Scientific/technical words (-ase, -ose, -ide endings)
- `is_archaic()`: Old English words (hath, doth, thee - flagged but not rejected)

**Main Entry Points:**
- `should_reject(word)`: Returns True if word should be filtered out
- `get_rejection_reason(word)`: Returns reason string or None

**Known Lists:**
- `known_proper_nouns`: 30+ common names/places that appear lowercase in dictionaries
- `known_foreign_words`: Common foreign words that slip through
- `archaic_words`: Old English terms (get low confidence, not rejected)
- `abbreviations`: Common abbreviations

**Example Results for NACUOTP:**
- Filters: anna (proper noun), canaan (place), naacp/ncaa (abbreviations)
- 102 candidates → 98 after filtering

### 3. EnhancedConfidenceScorer (`src/spelling_bee_solver/core/enhanced_confidence_scorer.py`)

**Olympic judges scoring system**

**5 Independent Judges:**
1. **Dictionary Judge** (80pts): Word found in high-quality dictionary?
2. **Frequency Judge** (90pts common, 30-60pts rare): Common English usage?
3. **Length Judge** (40-90pts): Optimal Spelling Bee length? (7 letters = 90pts)
4. **Pattern Judge** (70pts base, ±adjustments): Normal English letter patterns?
5. **Filter Judge** (95pts pass, 30pts archaic, 0pts rejected): Passes NYT criteria?

**Olympic Scoring Algorithm:**
```python
scores = [judge1, judge2, judge3, judge4, judge5]
scores_sorted = sorted(scores)
middle_scores = scores_sorted[1:-1]  # Drop highest and lowest
final_score = average(middle_scores)  # Average of middle 3
```

**Benefits:**
- More robust than single-factor scoring
- Automatic outlier removal
- Better discrimination between words
- Archaic words automatically get low scores

**Example Scores:**
- "account": 86.7% (common word, good length)
- "coconut": 80.0% (normal pattern, good length)
- "hath": 56.7% (archaic - flagged by Filter Judge)

### 4. Other Core Components

**CandidateGenerator** (`core/candidate_generator.py`):
- Filters dictionary words by puzzle rules
- Returns words that use only available letters + have required letter

**DictionaryManager** (`core/dictionary_manager.py`):
- Downloads and caches Webster's dictionary
- Loads system ASPELL dictionary
- Handles file I/O and caching

**InputValidator** (`core/input_validator.py`):
- Validates puzzle input (7 letters, required letter in letters)
- Normalizes to lowercase

**ResultFormatter** (`core/result_formatter.py`):
- Groups words by length
- Highlights pangrams
- Formats confidence scores
- Creates clean console output

## Refactoring History (Phases 1-7)

### Phase 1: Dictionary Consolidation ✓
**Goal:** Reduce 11 dictionaries to 2

**Changes:**
- Deleted `_core_dictionaries` and `_canonical_dictionary_sources`
- Created single `DICTIONARIES` tuple with 2 entries
- Removed `force_single_dictionary`, `exclude_dictionaries`, `include_only_dictionaries` config options
- Simplified `_validate_dictionaries()` method

**Result:** 11 → 2 dictionaries (Webster's + ASPELL)

### Phase 2: Solver Mode Elimination ✓
**Goal:** Remove 5 solver modes, create unified mode

**Changes:**
- Deleted `SolverMode` enum (PRODUCTION, CPU_FALLBACK, DEBUG_SINGLE, DEBUG_ALL, ANAGRAM)
- Created `_generate_candidates_comprehensive()` for unified generation
- Refactored `solve_puzzle()` to single filtering pass
- Removed `--mode` CLI argument
- Updated all tests to remove mode parameter

**Result:** 5 modes → 1 unified mode, cleaner architecture

### Phase 3: NYT Rejection Filter ✓
**Goal:** Better detection of proper nouns, foreign words, etc.

**Changes:**
- Created `NYTRejectionFilter` class
- Proper noun detection (even lowercase: lloyd, anna, canaan)
- Foreign word detection (pattern-based + known list)
- Archaic word flagging (not rejected, just low confidence)
- Integrated into `unified_solver.py` (`is_likely_nyt_rejected()` now uses filter)

**Result:** NACUOTP: 102 candidates → 98 words (anna, canaan, naacp, ncaa filtered)

### Phase 4: Olympic Judges Confidence Scoring ✓
**Goal:** Replace simple scoring with multi-judge system

**Changes:**
- Created `EnhancedConfidenceScorer` class
- 5 independent judges with different criteria
- Olympic scoring algorithm (drop outliers, average middle)
- Integrated into `unified_solver.py` (replaces basic `ConfidenceScorer`)

**Result:** Better discrimination, archaic words automatically score low

### Phase 5: Anagram Integration (SKIPPED)
**Rationale:** Optional, GPU-dependent, dictionary-based approach works well

### Phase 6: Cleanup ✓
**Goal:** Remove dead code and temp files

**Changes:**
- Deleted 23 files (test files, temp docs, debug scripts, backups)
- Removed 6,951 lines of code
- Restored `solver_config.json`

**Result:** Cleaner codebase, all tests passing

### Phase 7: Final Cleanup ✓
**Goal:** Fix remaining test issues

**Changes:**
- Fixed last `SolverMode` reference in `test_comprehensive.py`
- All 11 tests now passing

**Result:** Complete test suite working

## Testing

### Test Files (Working)

**`tests/test_basic.py`** (3 tests):
- `test_basic_imports()`: Module imports work
- `test_unified_solver()`: Basic puzzle solving
- `test_word_filtering()`: Rejection logic

**`tests/test_coverage.py`** (4 tests):
- `test_unified_solver()`: Core functionality
- `test_word_filtering()`: Filter functions
- `test_gpu_components()`: GPU features (may skip)
- `test_configuration()`: Config loading

**`tests/test_comprehensive.py`** (4 tests):
- `test_unified_solver_comprehensive()`: Full pipeline
- `test_word_filtering_comprehensive()`: Advanced filtering
- `test_gpu_components_comprehensive()`: GPU tests
- `test_configuration_and_edge_cases()`: Edge cases

**Current Status:** 11/11 tests passing in ~10s

### Running Tests

```bash
# Basic tests (fast)
./venv/bin/pytest tests/test_basic.py -v

# All working tests
./venv/bin/pytest tests/test_basic.py tests/test_coverage.py tests/test_comprehensive.py -v

# With verbose output and print statements
./venv/bin/pytest tests/test_basic.py -v -s
```

## Usage Patterns

### Direct Solve

```bash
./bee NACUOTP -r N
```

### Interactive Mode

```bash
./bee -i
```

### Programmatic Usage

```python
from src.spelling_bee_solver.unified_solver import UnifiedSpellingBeeSolver

solver = UnifiedSpellingBeeSolver(verbose=False)
results = solver.solve_puzzle("NACUOTP", "N")  # Returns List[Tuple[str, float]]

# results = [("account", 86.7), ("annotto", 80.0), ...]
```

## Configuration

### Default Configuration (`solver_config.json`)

```json
{
  "solver": {},
  "acceleration": {
    "force_gpu_off": false,
    "enable_cuda_nltk": true,
    "gpu_batch_size": 1000
  },
  "dictionaries": {
    "download_timeout": 30,
    "cache_expiry_days": 30
  },
  "filtering": {
    "min_word_length": 4,
    "enable_nyt_rejection_filter": true,
    "confidence_threshold": 0,
    "max_results": 0
  },
  "output": {
    "show_confidence": true,
    "group_by_length": true,
    "highlight_pangrams": true,
    "minimal_stats": true,
    "verbose_stats": false
  },
  "logging": {
    "level": "WARNING",
    "log_dictionary_loading": false,
    "log_filtering_steps": false
  },
  "debug": {
    "profile_performance": false,
    "save_candidates": false,
    "validate_results": false,
    "benchmark_mode": false
  }
}
```

## Dependencies

### Required

- Python 3.8+
- `requests` (HTTP downloads for Webster's dictionary)
- Standard library (pathlib, json, logging, argparse, etc.)

### Optional (GPU Acceleration)

- `cupy-cuda12x` (CUDA processing)
- `spacy` (NLP analysis - currently unused)
- `nltk` (Language processing - currently unused)

**Note:** GPU dependencies are completely optional. Solver works fine on CPU.

## Git History (Recent Commits)

1. `32bd176` - Test Improvements: Add Feedback & Fix Result Handling
2. `e649e4d` - Phase 3: NYT Rejection Filter
3. `dfc8550` - Phase 4: Olympic Judges Confidence Scoring
4. `00b8af6` - Phase 6: Cleanup - Remove Dead Code and Temp Files
5. `0333267` - Phase 7: Final Test Fix - Remove SolverMode Reference

## Known Limitations

1. **Dictionary coverage**: Only Webster's + ASPELL (but this is by design)
2. **NYT acceptance**: Heuristic-based, may not match NYT exactly
3. **Anagram mode**: Not integrated (Phase 5 skipped)
4. **GPU acceleration**: Optional, not critical for performance
5. **Archaic words**: Flagged but not always correctly identified

## Common Issues

### Import Errors

**Problem:** `ModuleNotFoundError` when running `unified_solver.py` directly

**Solution:** Always use wrapper or module syntax:
```bash
./bee NACUOTP -r N
# OR
python3 -m src.spelling_bee_solver.unified_solver NACUOTP -r N
```

### Test Failures

**Problem:** Some tests import `SolverMode` (deleted in Phase 2)

**Solution:** Update test to remove `SolverMode` import and `mode=` parameter

### Config Warnings

**Problem:** "Config file solver_config.json not found"

**Solution:** Normal on first run. Solver uses built-in defaults. Restore from `solver_config.json.backup` if needed.

## Future Considerations

1. **Phase 5 Integration**: Anagram generation could be added if GPU performance is needed
2. **Frequency List**: google-10000-common.txt integration for better Frequency Judge
3. **Pattern Improvements**: Enhanced phonotactic filtering (Phase 4A code exists but unused)
4. **ML Training**: Could train model on historical NYT puzzles (but user prefers heuristics)

## Development Workflow

1. Make changes to source files
2. Run tests: `./venv/bin/pytest tests/test_basic.py -v`
3. Test manually: `./bee NACUOTP -r N`
4. Commit with descriptive message
5. Use "🤖 Generated with Claude Code" footer

## For AI Assistants

**Key Points:**
- Always test after making changes
- Never create new solver modes (unified only)
- Don't add more dictionaries (2 is the limit)
- Heuristics over ML/training
- GPU optional, CPU must always work
- Test suite must stay at 11/11 passing

**User Preferences:**
- Concise, direct communication
- Test-driven development
- Commit after each phase
- Real test feedback (no mocks)
- Simple, maintainable code

**Common Patterns:**
- Dependency injection for all components
- Factory functions for component creation
- Logging throughout for debugging
- Defensive programming with validation
- Clean separation of concerns

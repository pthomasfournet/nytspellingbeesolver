# NYT Spelling Bee Solver

A Python-based solver for the New York Times Spelling Bee puzzle with intelligent filtering, multi-judge confidence scoring, and GPU acceleration support.

## Features

- **Exclude Known Words**: Filter out words you've already found to see only remaining words
- **Progress Tracking**: Shows your puzzle completion percentage
- **Unified Architecture**: Single mode that uses all solving methods automatically
- **2 High-Quality Dictionaries**: Webster's Unabridged + ASPELL American English
- **NYT Rejection Filter**: Detects proper nouns, foreign words, abbreviations, technical terms
- **Olympic Judges Scoring**: 6 independent judges (Dictionary, Frequency, Length, Pattern, Filter, NYT History) with outlier removal
- **GPU Acceleration**: Optional CUDA/CuPy support with automatic CPU fallback
- **Clean Output**: Formatted results with confidence percentages and word grouping

## Quick Start

```bash
# Solve a puzzle directly
./bee N ACUOTP

# Interactive mode (prompts for letters)
./bee -i

# Show help
./bee --help
```

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd spelling_bee_solver_project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (optional GPU support)
pip install requests
pip install cupy-cuda12x  # Optional: for GPU acceleration
```

## Usage

### Direct Solving

```bash
# Basic usage
./bee N ACUOTP

# Exclude words you've already found
./bee N ACUOTP --exclude "count,upon,coat"

# Exclude from file (one word per line)
echo -e "count\nupon\ncoat" > found.txt
./bee N ACUOTP --exclude-file found.txt

# Verbose output (shows filtering steps)
./bee N ACUOTP --verbose

# Custom config file
./bee N ACUOTP --config my_config.json
```

### Interactive Mode

```bash
# Start interactive session
./bee -i

# The solver will prompt you for:
# 1. The 7 puzzle letters
# 2. The required letter
# 3. Words you've already found (optional - just press Enter to skip)

# Interactive with verbose logging
./bee -i --verbose
```

### Output Examples

**Without exclusions:**
```
============================================================
SPELLING BEE SOLVER RESULTS
============================================================
Letters: NACUOTP
Required: N
Mode: UNIFIED
Total words found: 89
Solve time: 0.124s
============================================================

🌟 PANGRAMS (1):
  OCCUPANT             (76% confidence)
...
```

**With exclusions (showing progress):**
```
============================================================
SPELLING BEE SOLVER RESULTS
============================================================
Letters: NACUOTP
Required: N
Mode: UNIFIED
✓ Excluded: 3 words (count, upon, coat)
📊 Progress: 3/89 found (3.4%)
🔍 Remaining: 86 words
Solve time: 0.118s
============================================================

🌟 PANGRAMS (1):
  OCCUPANT             (78% confidence)

10-letter words (1):
  accountant      (77%)

7-letter words (14):
  account         (87%)  annotto         (80%)  cantata         (80%)
  coconut         (80%)  contact         (80%)  pontoon         (80%)
  ...
```

## Architecture

### Unified Solver Pipeline

```
Input Letters → Dictionary Scan → Candidate Generation
    ↓
Basic Validation (length, required letter, valid letters)
    ↓
NYT Rejection Filter (proper nouns, foreign words, etc.)
    ↓
Olympic Judges Confidence Scoring
    ↓
Sorted Results (by confidence, then length, then alphabetically)
```

### Components

1. **Dictionary Manager**: Loads Webster's + ASPELL dictionaries (2 sources)
2. **Candidate Generator**: Creates candidate words from dictionaries
3. **NYT Rejection Filter**: Filters inappropriate words
   - Proper nouns (names, places)
   - Foreign words (non-English)
   - Abbreviations (NASA, NCAA, etc.)
   - Technical/scientific terms
   - Archaic words (flagged for low confidence)

4. **Enhanced Confidence Scorer**: Olympic judges system
   - **Dictionary Judge** (80pts): Word in high-quality dictionary?
   - **Frequency Judge** (90pts): Common English word?
   - **Length Judge** (40-90pts): Optimal Spelling Bee length?
   - **Pattern Judge** (70pts): Normal English letter patterns?
   - **Filter Judge** (95pts): Passes NYT criteria?
   - **Olympic Scoring**: Drop highest/lowest, average middle 3 judges

5. **Result Formatter**: Clean console output with grouping

### Dictionary Sources

- **Webster's Unabridged Dictionary**: ~85K words (high-quality, authoritative)
- **ASPELL American English**: System dictionary (/usr/share/dict/american-english)

Dictionaries are automatically downloaded and cached on first use.

## Configuration

Edit `solver_config.json` to customize:

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
    "highlight_pangrams": true
  },
  "logging": {
    "level": "WARNING"
  }
}
```

## Development

### Running Tests

```bash
# Run basic tests
./venv/bin/pytest tests/test_basic.py -v

# Run all working tests
./venv/bin/pytest tests/test_basic.py tests/test_coverage.py tests/test_comprehensive.py -v

# All tests should pass (11/11)
```

### Project Structure

```
spelling_bee_solver_project/
├── bee                          # Wrapper script
├── solver_config.json           # Configuration
├── src/
│   └── spelling_bee_solver/
│       ├── unified_solver.py    # Main solver
│       ├── core/
│       │   ├── nyt_rejection_filter.py
│       │   ├── enhanced_confidence_scorer.py
│       │   ├── candidate_generator.py
│       │   ├── dictionary_manager.py
│       │   └── ...
│       └── gpu/                 # Optional GPU components
└── tests/                       # Test suite
```

## Recent Improvements (Phases 1-7)

### Phase 1-2: Architecture Simplification
- Reduced 11 dictionaries → 2 (Webster's + ASPELL)
- Eliminated 5 solver modes → 1 unified mode
- Single candidate generation with automatic deduplication

### Phase 3: NYT Rejection Filter
- Proper noun detection (names, places)
- Foreign word detection (non-English)
- Archaic word flagging (low confidence, not rejected)
- Example: anna, canaan, naacp, ncaa filtered from N ACUOTP puzzle

### Phase 4: Olympic Judges Scoring
- 5 independent judges with different criteria
- Outlier removal (drop highest/lowest)
- Better discrimination between words
- Example: "account" 86.7%, "coconut" 80.0%, archaic words ~55%

### Phase 6: Cleanup
- Removed 23 temporary files (6,951 lines)
- Restored configuration
- All tests passing (11/11 in 9.78s)

## NYT Spelling Bee Rules

- Words must contain at least 4 letters
- Words must include the center (required) letter
- Letters can be used more than once
- No offensive, obscure, hyphenated, or proper nouns
- 4-letter words = 1 point
- Longer words = 1 point per letter
- Pangrams (use all 7 letters) = word length + 7 bonus points

## Confidence Scores

- **85-90%**: Very common words with good length (account, coconut)
- **75-85%**: Normal words, good patterns (contact, pontoon)
- **65-75%**: Less common but valid English words
- **55-65%**: Archaic or unusual words (may or may not be accepted)
- **Below 55%**: Unlikely to be accepted

## GPU Acceleration (Optional)

If CuPy is installed, GPU acceleration is automatically used for:
- Large dictionary scans
- Batch filtering operations
- Optional anagram generation (future)

CPU fallback is automatic if GPU is unavailable.

## Troubleshooting

### "Config file not found"
Normal on first run. Solver uses built-in defaults.

### "CUDA-NLTK dependencies not available"
Optional warning. GPU features disabled, CPU mode active.

### Tests failing
Run: `./venv/bin/pytest tests/test_basic.py -v`
Expected: 3/3 tests passing

## License

MIT License

## Contributing

See `claude.md` for development context and architecture details.

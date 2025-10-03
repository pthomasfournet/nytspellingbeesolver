# NYT Spelling Bee Solver

A Python-based computational solver for the New York Times Spelling Bee puzzle with intelligent filtering, multi-criteria confidence scoring, and GPU acceleration support.

## Features

### Core Solver
- **Word Exclusion**: Filter previously discovered words to display only remaining candidates
- **Progress Tracking**: Quantitative puzzle completion metrics
- **Unified Architecture**: Single solving mode utilizing all available methods
- **Three High-Quality Dictionaries**: Webster's Unabridged, ASPELL American English, and SOWPODS
- **NYT Rejection Filter**: Detection of proper nouns, foreign words, abbreviations, and technical terms
- **Multi-Criteria Scoring**: Six independent evaluation criteria (Dictionary, Frequency, Length, Pattern, Filter, NYT History) with outlier removal
- **GPU Acceleration**: Optional CUDA/CuPy support with automatic CPU fallback
- **Formatted Output**: Structured results with confidence percentages and word grouping

### Web Application
- **Progressive Web App**: Installable on mobile and desktop platforms with offline capability
- **Mobile-First Design**: Responsive interface inspired by NYT Spelling Bee styling
- **Auto-Save**: Persistent puzzle and word state storage
- **Copy Functionality**: Single-word and bulk export capabilities
- **Real-time Solving**: Immediate result generation with progress tracking
- **RESTful API**: JSON API for third-party integrations

## Quick Start

### Web Application (Recommended)
```bash
# Start the web server (automatically manages existing instances)
./start_web.sh

# Or manually:
python3 -m uvicorn web_server:app --host 0.0.0.0 --port 8000

# Access via browser: http://localhost:8000
# Access via mobile (same network): http://<your-ip>:8000
```

### Command Line Interface
```bash
# Direct puzzle solving
./bee N ACUOTP

# Interactive mode (prompts for input)
./bee -i

# Display help
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

# Install production dependencies
pip install -r requirements.txt

# For development (includes testing and linting tools)
pip install -r requirements-dev.txt

# Optional: GPU acceleration
pip install cupy-cuda12x
```

## Usage

### Web Application

1. **Server initialization:**
   ```bash
   # Recommended (automatic single-instance management)
   ./start_web.sh

   # Manual startup
   python3 -m uvicorn web_server:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Browser access:**
   - Desktop: http://localhost:8000
   - Mobile (same network): http://<your-computer-ip>:8000
   - API Documentation: http://localhost:8000/api/docs

3. **Interface operation:**
   - Enter center letter and six additional letters
   - Optionally input previously discovered words
   - Select "Solve Puzzle" to generate remaining candidates
   - Click individual words to copy
   - Use "Copy All" or "Copy List" for bulk export

4. **Progressive Web App features:**
   - Install to home screen via mobile browser
   - Offline functionality after initial visit
   - Automatic puzzle state persistence

### Command Line Interface - Direct Solving

```bash
# Basic usage
./bee N ACUOTP

# Exclude previously discovered words
./bee N ACUOTP --exclude "count,upon,coat"

# Exclude from file (one word per line)
echo -e "count\nupon\ncoat" > found.txt
./bee N ACUOTP --exclude-file found.txt

# Verbose output (displays filtering steps)
./bee N ACUOTP --verbose

# Custom configuration file
./bee N ACUOTP --config my_config.json
```

### Interactive Mode

```bash
# Start interactive session
./bee -i

# The solver prompts for:
# 1. The seven puzzle letters
# 2. The required letter
# 3. Previously discovered words (optional - press Enter to skip)

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

PANGRAMS (1):
  OCCUPANT             (76% confidence)
...
```

**With exclusions (progress tracking):**
```
============================================================
SPELLING BEE SOLVER RESULTS
============================================================
Letters: NACUOTP
Required: N
Mode: UNIFIED
Excluded: 3 words (count, upon, coat)
Progress: 3/89 found (3.4%)
Remaining: 86 words
Solve time: 0.118s
============================================================

PANGRAMS (1):
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
Multi-Criteria Confidence Scoring
    ↓
Sorted Results (by confidence, then length, then alphabetically)
```

### Components

1. **Dictionary Manager**: Loads Webster's, ASPELL, and SOWPODS dictionaries (three sources)
2. **Candidate Generator**: Generates candidate words from dictionaries
3. **NYT Rejection Filter**: Filters inappropriate words
   - Proper nouns (names, places)
   - Foreign words (non-English)
   - Abbreviations (NASA, NCAA, etc.)
   - Technical/scientific terms
   - Archaic words (flagged for reduced confidence, not rejected)

4. **Enhanced Confidence Scorer**: Multi-criteria evaluation system
   - **Dictionary Judge** (80pts): Presence in high-quality dictionary
   - **Frequency Judge** (90pts): Common English word frequency
   - **Length Judge** (40-90pts): Optimal Spelling Bee length distribution
   - **Pattern Judge** (70pts): Standard English letter patterns
   - **Filter Judge** (95pts): Compliance with NYT criteria
   - **Scoring Method**: Drop highest and lowest scores, average middle three criteria

5. **Result Formatter**: Console output with structured grouping

### Web Application Stack

**Backend (FastAPI):**
- `web_server.py`: RESTful API with `/api/solve` and `/api/health` endpoints
- Pydantic models for request/response validation
- Singleton solver pattern for performance optimization
- CORS enabled for cross-origin requests

**Frontend (Vanilla JavaScript):**
- `index.html`: Mobile-first semantic HTML5
- `styles.css`: NYT Spelling Bee-inspired design with CSS variables
- `app.js`: Vanilla JavaScript implementation (framework-independent)
- LocalStorage for state persistence
- Service Worker for offline PWA support

**PWA Features:**
- `manifest.json`: Application metadata for installation
- `service-worker.js`: Cache-first static assets, network-first API
- Installable on iOS, Android, and desktop platforms
- Offline functionality after initial visit

### Dictionary Sources

- **Webster's Unabridged Dictionary**: Approximately 85,000 words (high-quality, authoritative)
- **ASPELL American English**: System dictionary (/usr/share/dict/american-english)
- **SOWPODS**: Official Scrabble word list (267,751 words)

Dictionaries are automatically downloaded and cached on first use.

## Configuration

Edit `solver_config.json` to customize solver behavior:

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

### Testing

```bash
# Run basic solver tests
./venv/bin/pytest tests/test_basic.py -v

# Run all solver tests
./venv/bin/pytest tests/test_basic.py tests/test_coverage.py tests/test_comprehensive.py -v

# Run exclude feature tests
./venv/bin/pytest tests/test_exclude_feature.py -v

# Run web API tests
./venv/bin/pytest tests/test_web_api.py -v

# Run all tests
./venv/bin/pytest tests/ -v
```

### Project Structure

```
spelling_bee_solver_project/
├── bee                          # CLI wrapper script
├── web_server.py                # FastAPI web server
├── solver_config.json           # Configuration
├── static/                      # PWA frontend
│   ├── index.html              # Main HTML
│   ├── styles.css              # Styling
│   ├── app.js                  # JavaScript logic
│   ├── manifest.json           # PWA manifest
│   ├── service-worker.js       # Offline support
│   └── ICONS_README.md         # Icon instructions
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
    ├── test_basic.py           # Core solver tests
    ├── test_exclude_feature.py # Exclude words tests
    └── test_web_api.py         # Web API tests
```

## Development History

### Phase 1-2: Architecture Simplification
- Reduced dictionary sources from 11 to 3 (Webster's, ASPELL, SOWPODS)
- Consolidated 5 solver modes into 1 unified mode
- Implemented single candidate generation with automatic deduplication

### Phase 3: NYT Rejection Filter
- Proper noun detection (names, places)
- Foreign word detection (non-English)
- Archaic word flagging (reduced confidence scoring)
- Example: anna, canaan, naacp, ncaa filtered from N ACUOTP puzzle

### Phase 4: Multi-Criteria Scoring
- Six independent evaluation criteria
- Outlier removal (drop highest and lowest scores)
- Improved discrimination between candidates
- Example: "account" 86.7%, "coconut" 80.0%, archaic words approximately 55%

### Phase 6: Code Cleanup
- Removed 23 temporary files (6,951 lines)
- Restored configuration
- All tests passing (11/11 in 9.78s)

### Phase 7: Word Exclusion Feature
- Added `--exclude` and `--exclude-file` CLI options
- Interactive mode prompts for previously discovered words
- Progress tracking (X/Y found, Z% complete)
- Statistics display in results
- 13/13 tests passing

### Phase 8: Progressive Web Application
- **FastAPI Backend**: RESTful `/api/solve` endpoint with Pydantic validation
- **Mobile-First UI**: NYT Spelling Bee-inspired design
- **LocalStorage Persistence**: Automatic puzzle state save with 7-day expiry
- **PWA Features**: Installable, offline-capable, service worker caching
- **Export Functionality**: Copy words as comma-separated or newline-separated list
- **User Experience Enhancements**: Click-to-copy words, empty states, keyboard shortcuts
- 26/26 tests passing (16 web API + 10 exclude feature)

## NYT Spelling Bee Rules

- Words must contain at least 4 letters
- Words must include the center (required) letter
- Letters can be used more than once
- Excludes offensive, obscure, hyphenated, or proper nouns
- 4-letter words = 1 point
- Longer words = 1 point per letter
- Pangrams (use all 7 letters) = word length + 7 bonus points

## Confidence Scores

- **85-90%**: Very common words with optimal length (account, coconut)
- **75-85%**: Standard words with normal patterns (contact, pontoon)
- **65-75%**: Less common but valid English words
- **55-65%**: Archaic or unusual words (may or may not be accepted)
- **Below 55%**: Unlikely to be accepted

## GPU Acceleration (Optional)

If CuPy is installed, GPU acceleration is automatically utilized for:
- Large dictionary scans
- Batch filtering operations
- Optional anagram generation (planned feature)

CPU fallback is automatic if GPU hardware is unavailable.

## Troubleshooting

### "Config file not found"
Normal on first run. Solver uses built-in defaults.

### "CUDA-NLTK dependencies not available"
Optional warning. GPU features disabled, CPU mode active.

### Tests failing
Run: `./venv/bin/pytest tests/test_basic.py -v`
Expected: All tests passing

## License

MIT License

## Contributing

See `CONTRIBUTING.md` for development workflow and contribution guidelines.

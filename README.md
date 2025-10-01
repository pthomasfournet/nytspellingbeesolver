# Spelling Bee Solver 🐝# NYT Spelling Bee Solver



A high-performance, GPU-accelerated word puzzle solver for New York Times Spelling Bee puzzles with comprehensive word filtering and analysis capabilities.A Python-based solver for the New York Times Spelling Bee puzzle with intelligent word filtering, aggregate scoring from multiple dictionaries, and enhanced confidence prediction.



[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)## Features

[![Code Coverage](https://img.shields.io/badge/coverage-61%25-yellow.svg)](reports/coverage/htmlcov/index.html)

[![Code Quality](https://img.shields.io/badge/quality-production-green.svg)](docs/COVERAGE_ANALYSIS.md)- **Enhanced Filtering**: Pre-filters dictionary to remove 16,500+ inappropriate words (proper nouns, technical terms, foreign words)

- **Aggregate Scoring**: Combines evidence from SOWPODS dictionary, Google common words, and pattern analysis

## 🚀 Features- **Smart Confidence Scoring**: Ranks words by likelihood of NYT acceptance (60-100% for display)

- **Global Reject List**: Filters out 76+ obscure words learned from previous puzzles

- **GPU Acceleration**: CUDA-enabled NLTK processing and spaCy filtering- **Performance Optimized**: Loads 248,056 high-quality words (vs 264,581 original)

- **Multi-Tier Solving**: Production and debug modes with configurable dictionary sources- **Puzzle Tracking**: Saves progress per puzzle by date

- **Advanced Filtering**: NYT-style rejection patterns, proper noun detection, inappropriate word filtering- **Interactive Mode**: Beautiful hexagon display and marking system

- **Comprehensive Testing**: 61% code coverage with extensive test suite

- **Clean Architecture**: Organized package structure with proper separation of concerns## Usage

- **Configuration Management**: Flexible JSON-based configuration system

### Quick Start

## 📁 Project Structure

```bash

```# Interactive mode (shows hexagon, prompts for letters)

spelling_bee_solver_project/./bee

├── src/spelling_bee_solver/     # Main package

│   ├── unified_solver.py        # Main solver engine# Quick solve with letters (shows top 46 most likely words)

│   ├── word_filtering.py        # Core filtering logic./bee P NOUCAT

│   └── gpu/                     # GPU acceleration modules

│       ├── cuda_nltk.py         # GPU-accelerated NLTK# Show specific number of top predictions

│       ├── gpu_word_filtering.py # GPU word filtering./bee P NOUCAT --top 20

│       └── gpu_puzzle_solver.py # Multi-tier GPU solver

├── tests/                       # Comprehensive test suite# Show all words including obscure ones

├── data/                        # Dictionaries and puzzle data./bee I BELCOT --all

├── config/                      # Configuration files

├── docs/                        # Documentation# Interactive mode to mark found words

├── scripts/                     # Utility scripts./bee I BELCOT --mark

└── reports/                     # Coverage and analysis reports

```# Reset puzzle progress

./bee I BELCOT --reset

## 🔧 Installation

# Show help

### Prerequisites./bee --help

```

- Python 3.13+

- CUDA-compatible GPU (optional, for acceleration)### Alternative Usage

- Virtual environment (recommended)

You can also use `python spelling_bee_solver.py` instead of `./bee`

### Setup

## Command Line Options

1. **Clone the repository:**

   ```bash- `--top N` - Show top N most confident words (default: 46)

   git clone <repository-url>- `--all, -a` - Show all words including obscure ones (confidence < 60%)

   cd spelling_bee_solver_project- `--mark, -m` - Interactive mode to mark found words

   ```- `--reset, -r` - Reset saved progress for this puzzle

- `--help, -h` - Show help message

2. **Create and activate virtual environment:**

   ```bash## Files

   python -m venv venv

   source venv/bin/activate  # On Windows: venv\Scripts\activate- `spelling_bee_solver.py` - Main solver script with enhanced algorithms

   ```- `bee` - Command wrapper for easier usage

- `sowpods.txt` - SOWPODS Scrabble dictionary (filtered to 248K quality words)

3. **Install dependencies:**- `google-10000-common.txt` - Google common words list for confidence scoring

   ```bash- `puzzles/` - Saved puzzle solutions by date

   pip install -r requirements.txt  - `.spelling_bee_2025-09-30.json` - Tuesday Sept 30 (46 words, 204 pts)

   ```  - `.spelling_bee_2025-09-29.json` - Monday Sept 29 (in progress)

  - `.spelling_bee_rejected.json` - Global reject list (76+ words)

4. **Setup dictionaries:**

   ```bash## Algorithm Improvements

   chmod +x scripts/setup_dictionaries.sh

   ./scripts/setup_dictionaries.sh### Enhanced Dictionary Filtering

   ```

- **Scientific Terms**: Removes -ism, -ite, -osis, -emia endings

## 🎯 Usage- **Foreign Words**: Filters -eau, -ieux, -um, -us endings  

- **Modern Terms**: Blocks internet slang, brand names, technical jargon

### Command Line Interface- **Geographic**: Removes place-name indicators (-burg, -heim, -stadt)

- **Performance**: 6% dictionary size reduction with no valid word loss

#### Basic Usage

```bash### Aggregate Confidence Scoring

# Run from project root

python -m src.spelling_bee_solver.unified_solver IBELCOT --required I- **Google Common Words**: +40 points for high-frequency vocabulary

- **Frequency Bonus**: +20 points for top 1000 most common words

# Or use the wrapper script- **Compound Detection**: +15 points for recognizable compound words

./scripts/bee IBELCOT I- **Pattern Analysis**: Bonuses for NYT-friendly endings (-ing, -tion, etc.)

```- **Smart Filtering**: Only shows words with 60%+ confidence by default



#### Interactive Mode### Results Quality

```bash

python -m src.spelling_bee_solver.unified_solver --interactive- **P/NOUCAT**: 5 high-confidence words (occupant, potato, output, coupon, upon)

```- **T/HAILER**: 20+ realistic suggestions with 7 pangrams

- **Better Accuracy**: Focuses on words actually likely to be in NYT puzzles

#### Advanced Options

```bash## NYT Spelling Bee Rules

python -m src.spelling_bee_solver.unified_solver PNOUCAT \

    --required P \- Words must contain at least 4 letters

    --mode debug_single \- Words must include the center letter

    --verbose \- Letters can be used more than once

    --config config/debug_config.json- No offensive, obscure, hyphenated, or proper nouns

```- 4-letter words = 1 point

- Longer words = 1 point per letter

### Python API- Pangrams (use all 7 letters) = word length + 7 bonus points



```python## Confidence Scoring

from src.spelling_bee_solver import UnifiedSpellingBeeSolver, SolverMode

The solver assigns each word a confidence score (60-100% displayed):

# Initialize solver

solver = UnifiedSpellingBeeSolver(mode=SolverMode.PRODUCTION)- **100%**: Very common words (occupant, potato, upon)

- **80-90%**: Recognizable words, common compounds (retailer, heather)

# Solve puzzle- **70%**: Less common but standard English words (coupon, theatre)

results = solver.solve_puzzle("IBELCOT", "I")- **60-69%**: Words that might be accepted but less certain

- **<60%**: Filtered out by default (use --all to see them)

# Display results

solver.print_results(results, "IBELCOT", "I")## Examples

```

### Tuesday September 30, 2025

### Configuration

- Center: **I**, Outer: **BELCOT**

The solver supports flexible configuration via JSON files:- **46 words, 204 points**

- Pangram: **COLLECTIBLE**

```json

{### Monday September 29, 2025

  "mode": "production",

  "gpu_acceleration": true,- Center: **P**, Outer: **NOUCAT**

  "dictionary_override": ["comprehensive_words.txt"],- Top words: occupant (pangram), potato, output, coupon, upon

  "max_results": 1000,

  "confidence_threshold": 0.5## Development

}

```Run code quality checks:



## 🧪 Testing```bash

ruff check spelling_bee_solver.py    # All checks should pass

### Run Tests```

```bash

# Basic functionality testThe codebase maintains 100% code quality rating with proper encoding, error handling, and clean Python patterns.

python tests/test_basic.py

# Comprehensive test suite
python tests/test_comprehensive.py

# Using pytest
python -m pytest tests/ -v
```

### Code Coverage
```bash
# Generate coverage report
coverage run -m pytest tests/
coverage report
coverage html  # Generate HTML report in reports/coverage/
```

## 📊 Performance

- **Coverage**: 61% overall code coverage
- **GPU Acceleration**: Up to 10x faster filtering with CUDA
- **Dictionary Sources**: 3 core dictionaries (480K+ words)
- **Filtering Pipeline**: Multi-stage rejection with 90%+ accuracy

### Module Coverage Breakdown
| Module | Coverage | Status |
|--------|----------|--------|
| cuda_nltk.py | 72% | ✅ Good |
| word_filtering.py | 74% | ✅ Good |
| gpu_word_filtering.py | 56% | ⚠️ Moderate |
| unified_solver.py | 56% | ⚠️ Moderate |
| gpu_puzzle_solver.py | 29% | ❌ Needs Work |

## 🔍 Development

### VS Code Integration

The project includes comprehensive VS Code configuration:

- **Debug Configurations**: Launch puzzle solving with different modes
- **Tasks**: Run tests, coverage, linting with single commands
- **Settings**: Optimized for Python development

### Code Quality

- **Ruff**: Fast Python linting and formatting
- **Type Hints**: Comprehensive type annotations
- **Error Handling**: Robust exception handling throughout
- **Documentation**: Extensive docstrings and comments

### Contributing

1. Run tests: `python -m pytest tests/`
2. Check coverage: `coverage run -m pytest tests/ && coverage report`
3. Lint code: `ruff check src/ tests/`
4. Fix issues: `ruff check --fix src/ tests/`

## 📚 Documentation

- [Development Guide](docs/DEVELOPMENT.md) - Development setup and guidelines
- [Coverage Analysis](docs/COVERAGE_ANALYSIS.md) - Detailed code coverage report
- [API Reference](docs/API_REFERENCE.md) - Comprehensive API documentation

## 🤝 Architecture

### Core Components

1. **UnifiedSpellingBeeSolver**: Main solver engine with mode-based configuration
2. **GPU Acceleration Suite**: CUDA-enabled processing for enhanced performance
3. **Word Filtering Pipeline**: Multi-stage filtering with NYT rejection patterns
4. **Configuration System**: Flexible JSON-based configuration management

### Design Principles

- **Separation of Concerns**: Clear module boundaries and responsibilities
- **Performance First**: GPU acceleration where beneficial
- **Configurability**: Flexible configuration without code changes
- **Testability**: Comprehensive test coverage with clear APIs

## 📈 Roadmap

- [ ] Improve gpu_puzzle_solver.py coverage to 50%+
- [ ] Add integration tests for full workflows
- [ ] Implement caching for dictionary operations
- [ ] Add performance benchmarking suite
- [ ] CI/CD pipeline integration

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- New York Times for the Spelling Bee puzzle format
- NLTK and spaCy teams for natural language processing tools
- CUDA and PyTorch teams for GPU acceleration capabilities

---

**Note**: This solver is for educational and personal use. Respect the New York Times' intellectual property and terms of service.
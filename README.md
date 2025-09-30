# NYT Spelling Bee Solver

A Python-based solver for the New York Times Spelling Bee puzzle with intelligent word filtering and confidence scoring.

## Features

- **Smart Confidence Scoring**: Ranks words by likelihood of NYT acceptance (0-100%)
- **Global Reject List**: Filters out 76+ obscure words learned from previous puzzles
- **Pattern-Based Filtering**: Automatically rejects scientific terms, foreign words, proper nouns
- **Puzzle Tracking**: Saves progress per puzzle by date
- **SOWPODS Dictionary**: 264K+ words from Scrabble dictionary

## Usage

```bash
# Basic usage
python spelling_bee_solver.py <center_letter> <outer_letters>

# Example: Tuesday Sept 30, 2025 (center: I, outer: BELCOT)
python spelling_bee_solver.py I BELCOT

# Show top N most confident predictions
python spelling_bee_solver.py P NOUCAT --top 50

# Show all words including obscure ones
python spelling_bee_solver.py I BELCOT --all

# Interactive mode to mark found words
python spelling_bee_solver.py I BELCOT --mark
# Enter words you found, or prefix with '-' to reject (e.g., -obscureword)

# Reset puzzle progress
python spelling_bee_solver.py I BELCOT --reset
```

## Files

- `spelling_bee_solver.py` - Main solver script
- `sowpods.txt` - SOWPODS Scrabble dictionary (264K words)
- `puzzles/` - Saved puzzle solutions by date
  - `.spelling_bee_2025-09-30.json` - Tuesday Sept 30 (46 words, 204 pts)
  - `.spelling_bee_2025-09-29.json` - Monday Sept 29 (in progress)
  - `.spelling_bee_rejected.json` - Global reject list (76 words)

## NYT Spelling Bee Rules

- Words must contain at least 4 letters
- Words must include the center letter
- Letters can be used more than once
- No offensive, obscure, hyphenated, or proper nouns
- 4-letter words = 1 point
- Longer words = 1 point per letter
- Pangrams (use all 7 letters) = word length + 7 bonus points

## Confidence Scoring

The solver assigns each word a confidence score (0-100%):
- **100%**: Very common words (occupant, potato, upon)
- **80-90%**: Recognizable words, common compounds (catnap, copout)
- **70%**: Less common but standard English words
- **<40%**: Obscure words, filtered out by default

## Examples

### Tuesday September 30, 2025
- Center: **I**, Outer: **BELCOT**
- **46 words, 204 points**
- Pangram: **COLLECTIBLE**

### Monday September 29, 2025
- Center: **P**, Outer: **NOUCAT**
- In progress...

## Development

Run code quality checks:
```bash
ruff check spelling_bee_solver.py
```

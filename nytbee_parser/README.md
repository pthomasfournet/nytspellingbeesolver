# NYT Spelling Bee Parser and Dataset

Multi-core HTML parser for NYT Spelling Bee historical data.

Parsed 2,615 puzzles in 0.21s (12,321 puzzles/second) using multiprocessing.

## Files

### Parser
- `parse_nyt_puzzles.py` - Multi-core HTML parser utilizing all available CPU cores

### Datasets
- **`nyt_puzzles_dataset.json`** (3.6MB) - Complete dataset of 2,615 puzzles
- **`nyt_word_frequency.json`** (166KB) - Word frequency distribution (10,759 unique words)
- **`nyt_rejection_blacklist.json`** (93KB) - Rejection blacklist (6,095 words rejected 3+ times)

## Dataset Statistics

| Metric | Value |
|--------|-------|
| **Total Puzzles** | 2,615 |
| **Date Range** | 2018-08-01 to 2025-10-01 |
| **Unique Accepted Words** | 10,759 |
| **Unique Rejected Words** | 8,917 |
| **Total Pangrams** | 3,593 |
| **Blacklist Words** | 6,095 (rejected 3+ times) |

## Frequently Accepted Words

**Most Common Accepted Words:**
```
noon     213 appearances
loll     198 appearances
toot     192 appearances
naan     180 appearances
nana     180 appearances
lilt     142 appearances
till     142 appearances
tilt     142 appearances
nene     137 appearances
mama     136 appearances
```

**Most Frequently Rejected Words:**
```
titi     206 rejections
lall     176 rejections
otto     176 rejections
caca     171 rejections
anna     167 rejections
nanna    167 rejections
ictic    144 rejections
coco     144 rejections
coocoo   144 rejections
haha     132 rejections
```

## Dataset Format

### `nyt_puzzles_dataset.json`
```json
[
  {
    "date": "20251001",
    "center": "f",
    "letters": "acfinot",
    "accepted": ["affiant", "afoot", "antifa", ...],
    "rejected": ["antifat", "caff", "caitiff", ...],
    "pangrams": ["citification", "faction", ...],
    "stats": {
      "num_accepted": 30,
      "num_rejected": 32,
      "num_pangrams": 5
    }
  },
  ...
]
```

### `nyt_word_frequency.json`
```json
{
  "noon": 213,
  "loll": 198,
  "toot": 192,
  ...
}
```

### `nyt_rejection_blacklist.json`
```json
{
  "titi": 206,
  "lall": 176,
  "otto": 176,
  ...
}
```

## Usage

### Re-parse All Puzzles
```bash
python3 parse_nyt_puzzles.py
```

Parses all 2,618 HTML files in ../nytbee_data/

### Python Integration
```python
import json

# Load full dataset
with open('nyt_puzzles_dataset.json') as f:
    puzzles = json.load(f)

# Load word frequencies
with open('nyt_word_frequency.json') as f:
    word_freq = json.load(f)

# Check if word is common in NYT
if word_freq.get('noon', 0) > 100:
    print("Very common word")

# Load rejection blacklist
with open('nyt_rejection_blacklist.json') as f:
    blacklist = json.load(f)

# Check if word is commonly rejected
if word in blacklist:
    print(f"Rejected {blacklist[word]} times")
```

## Data Analysis Insights

### NYT Word Selection Patterns
- Short repeated-letter words: noon, loll, toot, naan
- Common 4-letter words: mama, papa, nana
- Rejects proper nouns: anna, otto (even lowercase)
- Rejects obscure/foreign words: titi, caca, coco

### Statistical Patterns
- **10,759 unique accepted words** across 2,615 puzzles
- **Average ~41 words per puzzle** (10,759 unique / 2,615 puzzles)
- **3,593 pangrams** = ~1.37 pangrams per puzzle on average
- **6,095 blacklisted words** = high-confidence rejection list

## Performance Metrics

**Parser Performance:**
- **Speed**: 12,321 puzzles/second
- **Cores Used**: 12 (all available)
- **Total Time**: 0.33s for complete parsing
- **Method**: Python multiprocessing.Pool

**Performance Factors:**
- Multiprocessing for parallel parsing across all cores
- Regex-based parsing (more efficient than BeautifulSoup)
- Minimal I/O operations (single file read)
- CPU-bound regex processing (no GPU required)

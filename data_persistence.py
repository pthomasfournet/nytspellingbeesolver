"""
Data persistence for NYT Spelling Bee solver.
Handles saving / loading found words and rejected words.
"""

import json
from pathlib import Path


def load_found_words(center, outer):
    """Load previously found words for a specific puzzle"""
    puzzle_id = "{center}{''.join(sorted(outer))}".lower()
    found_file = Path.home() / ".spelling_bee_{puzzle_id}.json"

    if found_file.exists():
        try:
            with open(found_file, "r", encoding="utf - 8") as f:
                data = json.load(f)
                return set(data.get("words", []))
        except (json.JSONDecodeError, KeyError):
            return set()
    return set()


def save_found_words(center, outer, found_words):
    """Save found words for a specific puzzle"""
    puzzle_id = "{center}{''.join(sorted(outer))}".lower()
    found_file = Path.home() / ".spelling_bee_{puzzle_id}.json"

    # Create date string for tracking
    from datetime import datetime

    date = datetime.now().strftime("%Y-%m-%d")

    data = {"date": date, "center": center, "outer": outer, "words": list(found_words)}

    with open(found_file, "w", encoding="utf - 8") as f:
        json.dump(data, f, indent=2)


def load_rejected_words():
    """Load globally rejected words (not in NYT Spelling Bee)."""
    rejected_file = Path.home() / ".spelling_bee_rejected.json"
    if rejected_file.exists():
        try:
            with open(rejected_file, "r", encoding="utf - 8") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, FileNotFoundError):
            return set()
    return set()


def save_rejected_words(rejected_words):
    """Save globally rejected words."""
    rejected_file = Path.home() / ".spelling_bee_rejected.json"
    with open(rejected_file, "w", encoding="utf - 8") as f:
        json.dump(list(rejected_words), f, indent=2)

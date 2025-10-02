#!/usr/bin/env python3
"""
Ultra-fast HTML parser for NYT Spelling Bee data.

Uses multiprocessing for lightning-fast parallel parsing of 2,618 puzzles.
"""

import json
import re
import time
from multiprocessing import Pool, cpu_count
from pathlib import Path
from typing import Dict


def parse_single_puzzle(html_path: Path) -> Dict:
    """
    Parse a single NYT Bee HTML file.

    Extracts:
    - Date
    - Accepted words
    - Rejected words (valid but not in official answers)
    - Pangrams
    - Center letter (inferred from first letters chart)
    - All letters (inferred from words)
    """
    try:
        with open(html_path, encoding='utf-8') as f:
            content = f.read()

        # Extract date from filename
        date_match = re.search(r'(\d{8})', html_path.name)
        date = date_match.group(1) if date_match else None

        # Extract accepted words from Bokeh JSON
        words_match = re.search(r'"words":\[\[(.*?)\]\]', content)
        if not words_match:
            return None

        # Parse nested word arrays by length
        words_str = '[' + words_match.group(1) + ']'
        inner_arrays = re.findall(r'\[(.*?)\]', words_str)

        accepted_words = []
        for arr in inner_arrays:
            if arr.strip():
                words = re.findall(r'"([^"]+)"', arr)
                # Strip leading spaces from words
                accepted_words.extend([w.strip() for w in words])

        # Extract pangrams (marked with <mark><strong>)
        pangrams = re.findall(r'<mark><strong>([a-z]+)</strong></mark>', content)

        # Extract rejected words from "Valid dictionary words not in today's official answers"
        rejected_section = re.search(
            r'Valid dictionary words not in today.*?<ul class="column-list">(.*?)</ul>',
            content,
            re.DOTALL
        )
        rejected_words = []
        if rejected_section:
            rejected_words = re.findall(r'<li>([a-z]+)</li>', rejected_section.group(1))

        # Extract first letter chart to find center letter (marked with firebrick color)
        first_letter_json = re.search(
            r'"Words by First Letter".*?"plotX":\[(.*?)\].*?"color":\[(.*?)\]',
            content,
            re.DOTALL
        )

        center_letter = None
        all_letters = set()

        if first_letter_json:
            letters_str = first_letter_json.group(1)
            colors_str = first_letter_json.group(2)

            letters = re.findall(r'"([A-Z])"', letters_str)
            colors = re.findall(r'"([^"]+)"', colors_str)

            # Center letter is marked with 'firebrick' color
            for letter, color in zip(letters, colors):
                all_letters.add(letter.lower())
                if color == 'firebrick':
                    center_letter = letter.lower()

        # If we couldn't find center letter, infer from pangram
        if not center_letter and pangrams:
            pangram_letters = set(pangrams[0])
            # The center letter appears in ALL words
            # Find letter that appears in most accepted words
            letter_freq = {}
            for letter in pangram_letters:
                count = sum(1 for word in accepted_words if letter in word)
                letter_freq[letter] = count
            if letter_freq:
                center_letter = max(letter_freq, key=letter_freq.get)

        # If all_letters not found, get from pangram
        if not all_letters and pangrams:
            all_letters = set(pangrams[0])

        return {
            'date': date,
            'center': center_letter,
            'letters': ''.join(sorted(all_letters)),
            'accepted': sorted(set(accepted_words)),  # deduplicate
            'rejected': sorted(set(rejected_words)),
            'pangrams': pangrams,
            'stats': {
                'num_accepted': len(set(accepted_words)),
                'num_rejected': len(set(rejected_words)),
                'num_pangrams': len(pangrams)
            }
        }

    except Exception as e:
        print(f"Error parsing {html_path.name}: {e}")
        return None


def main():
    """Parse all NYT Bee puzzles using multiprocessing for speed."""

    print("🐝 NYT Spelling Bee Ultra-Fast Parser 🐝")
    print("=" * 60)

    # Find all HTML files
    html_dir = Path('nytbee_data')
    html_files = sorted(html_dir.glob('Bee_*.html'))

    print(f"Found {len(html_files)} puzzle files")
    print(f"Using {cpu_count()} CPU cores for parallel processing")
    print()

    start_time = time.time()

    # Parse in parallel using all CPU cores
    with Pool(cpu_count()) as pool:
        results = pool.map(parse_single_puzzle, html_files)

    # Filter out None results
    puzzles = [r for r in results if r is not None]

    parse_time = time.time() - start_time

    print(f"✅ Parsed {len(puzzles)} puzzles in {parse_time:.2f}s")
    print(f"⚡ Speed: {len(puzzles) / parse_time:.1f} puzzles/second")
    print()

    # Save full dataset
    output_file = Path('nyt_puzzles_dataset.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(puzzles, f, indent=2)
    print(f"💾 Saved dataset to {output_file}")
    print()

    # Build frequency database
    print("📊 Building NYT word frequency database...")
    word_freq = {}
    for puzzle in puzzles:
        for word in puzzle['accepted']:
            word_freq[word] = word_freq.get(word, 0) + 1

    # Sort by frequency descending
    sorted_freq = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

    freq_output = Path('nyt_word_frequency.json')
    with open(freq_output, 'w', encoding='utf-8') as f:
        json.dump(dict(sorted_freq), f, indent=2)

    print(f"💾 Saved frequency database to {freq_output}")
    print("   Top 10 most common words:")
    for word, count in sorted_freq[:10]:
        print(f"     {word:15} {count:3} appearances")
    print()

    # Build rejection blacklist
    print("🚫 Building NYT rejection blacklist...")
    rejection_freq = {}
    for puzzle in puzzles:
        for word in puzzle['rejected']:
            rejection_freq[word] = rejection_freq.get(word, 0) + 1

    # Words rejected in 3+ puzzles are strong candidates for blacklist
    blacklist = {word: count for word, count in rejection_freq.items() if count >= 3}
    sorted_blacklist = sorted(blacklist.items(), key=lambda x: x[1], reverse=True)

    blacklist_output = Path('nyt_rejection_blacklist.json')
    with open(blacklist_output, 'w', encoding='utf-8') as f:
        json.dump(dict(sorted_blacklist), f, indent=2)

    print(f"💾 Saved blacklist to {blacklist_output}")
    print(f"   {len(blacklist)} words rejected 3+ times")
    print("   Top 10 most rejected words:")
    for word, count in sorted_blacklist[:10]:
        print(f"     {word:15} {count:3} rejections")
    print()

    # Summary statistics
    print("📈 Dataset Summary:")
    print(f"   Total puzzles: {len(puzzles)}")
    print(f"   Date range: {puzzles[0]['date']} to {puzzles[-1]['date']}")
    print(f"   Unique accepted words: {len(word_freq)}")
    print(f"   Unique rejected words: {len(rejection_freq)}")
    print(f"   Total pangrams: {sum(p['stats']['num_pangrams'] for p in puzzles)}")
    print()

    total_time = time.time() - start_time
    print(f"🏁 Total time: {total_time:.2f}s")
    print("=" * 60)


if __name__ == '__main__':
    main()

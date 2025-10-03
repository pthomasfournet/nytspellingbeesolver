#!/usr/bin/env python3
"""
Wiktionary Database Builder

Downloads and parses Wiktionary XML dumps to extract metadata for word filtering.

Extracts:
- Obsolete/archaic words
- Proper nouns
- Foreign-only words (no English entry)
- Multi-language words

Output: wiktionary_metadata.json (5-10MB)
"""

import argparse
import bz2
import json
import logging
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Set, Tuple

import requests

# Try to import parsing library
try:
    import mwparserfromhell as mwp
except ImportError:
    print("ERROR: mwparserfromhell not installed")
    print("Run: pip install -r wiktionary_parser/requirements.txt")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Wiktionary dump URL (latest English Wiktionary)
WIKTIONARY_DUMP_URL = "https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles.xml.bz2"


# Label sets (module level for multiprocessing)
OBSOLETE_LABELS = {'obsolete', 'dated'}
ARCHAIC_LABELS = {'archaic', 'historical'}
RARE_LABELS = {'rare', 'uncommon'}


def extract_page_metadata(title: str, text: str) -> Tuple[str, Dict[str, Set[str]]]:
    """Extract metadata from a single page (module-level for multiprocessing).

    Args:
        title: Page title (word)
        text: Wikitext content

    Returns:
        Tuple of (title, metadata_dict) where metadata_dict contains:
            - 'obsolete': set of obsolete words
            - 'archaic': set of archaic words
            - 'rare': set of rare words
            - 'proper_nouns': set of proper nouns
            - 'foreign_only': set of foreign-only words
            - 'multi_language': dict of multi-language words
    """
    result = {
        'obsolete': set(),
        'archaic': set(),
        'rare': set(),
        'proper_nouns': set(),
        'foreign_only': set(),
        'multi_language': {}
    }

    # Skip non-main namespace pages
    if ':' in title:
        return title, result

    # Parse wikitext
    try:
        parsed = mwp.parse(text)
    except Exception:
        return title, result

    # Extract language sections
    languages = _extract_languages_static(parsed)

    # Check if word has English entry
    has_english = 'English' in languages

    # If no English entry but has foreign entries → foreign-only
    if not has_english and languages:
        result['foreign_only'].add(title.lower())
        return title, result

    # Process English section
    if has_english:
        english_section = languages['English']

        # Check for usage labels
        usage_labels = _extract_usage_labels_static(english_section)

        if any(label in OBSOLETE_LABELS for label in usage_labels):
            result['obsolete'].add(title.lower())

        if any(label in ARCHAIC_LABELS for label in usage_labels):
            result['archaic'].add(title.lower())

        if any(label in RARE_LABELS for label in usage_labels):
            result['rare'].add(title.lower())

        # Check for proper noun
        if _is_proper_noun_static(english_section):
            result['proper_nouns'].add(title)  # Keep capitalization

        # Track multi-language words
        if len(languages) > 1:
            result['multi_language'][title.lower()] = list(languages.keys())

    return title, result


def _extract_languages_static(parsed) -> Dict[str, str]:
    """Extract language sections (static version for multiprocessing)."""
    import re

    text = str(parsed)
    languages = {}

    pattern = r'\n==([\w\s]+)==\n(.*?)(?=\n==[\w\s]+=|$)'

    for match in re.finditer(pattern, text, re.DOTALL):
        lang_name = match.group(1).strip()
        section_text = match.group(2)
        languages[lang_name] = section_text

    return languages


def _extract_usage_labels_static(section_text: str) -> Set[str]:
    """Extract usage labels (static version for multiprocessing)."""
    labels = set()

    try:
        parsed = mwp.parse(section_text)
    except Exception:
        return labels

    # Find templates
    for template in parsed.filter_templates():
        name = str(template.name).strip().lower()

        if name in OBSOLETE_LABELS | ARCHAIC_LABELS | RARE_LABELS:
            labels.add(name)

        if name in {'label', 'lb', 'context'}:
            for param in template.params:
                param_str = str(param.value).strip().lower()
                if param_str in OBSOLETE_LABELS | ARCHAIC_LABELS | RARE_LABELS:
                    labels.add(param_str)

    # Check for plain text labels
    import re
    all_labels = OBSOLETE_LABELS | ARCHAIC_LABELS | RARE_LABELS
    for label in all_labels:
        pattern = r'[\(,]\s*' + re.escape(label) + r'\s*[,\)]'
        if re.search(pattern, section_text, re.IGNORECASE):
            labels.add(label)

    return labels


def _is_proper_noun_static(section_text: str) -> bool:
    """Check if word is a proper noun (static version for multiprocessing)."""
    return '===Proper noun===' in section_text or '====Proper noun====' in section_text


class WiktionaryExtractor:
    """Extract metadata from Wiktionary XML dump."""

    def __init__(self):
        self.obsolete_words = set()
        self.archaic_words = set()
        self.rare_words = set()
        self.proper_nouns = set()
        self.foreign_only = set()
        self.multi_language = {}

        # Usage label patterns to detect
        self.obsolete_labels = {'obsolete', 'dated'}
        self.archaic_labels = {'archaic', 'historical'}
        self.rare_labels = {'rare', 'uncommon'}

    def merge_results(self, results: Dict[str, Set[str]]):
        """Merge results from parallel processing.

        Args:
            results: Dict with sets of words for each category
        """
        self.obsolete_words.update(results.get('obsolete', set()))
        self.archaic_words.update(results.get('archaic', set()))
        self.rare_words.update(results.get('rare', set()))
        self.proper_nouns.update(results.get('proper_nouns', set()))
        self.foreign_only.update(results.get('foreign_only', set()))
        self.multi_language.update(results.get('multi_language', {}))

    def extract_from_page(self, title: str, text: str):
        """Extract metadata from a single Wiktionary page.

        Args:
            title: Page title (word)
            text: Wikitext content
        """
        # Skip non-main namespace pages
        if ':' in title:
            return

        # Parse wikitext
        try:
            parsed = mwp.parse(text)
        except Exception as e:
            logger.debug(f"Failed to parse '{title}': {e}")
            return

        # Extract language sections
        languages = self._extract_languages(parsed)

        # Check if word has English entry
        has_english = 'English' in languages

        # If no English entry but has foreign entries → foreign-only
        if not has_english and languages:
            self.foreign_only.add(title.lower())
            return

        # Process English section
        if has_english:
            english_section = languages['English']

            # Check for usage labels
            usage_labels = self._extract_usage_labels(english_section)

            if any(label in self.obsolete_labels for label in usage_labels):
                self.obsolete_words.add(title.lower())

            if any(label in self.archaic_labels for label in usage_labels):
                self.archaic_words.add(title.lower())

            if any(label in self.rare_labels for label in usage_labels):
                self.rare_words.add(title.lower())

            # Check for proper noun
            if self._is_proper_noun(english_section):
                self.proper_nouns.add(title)  # Keep capitalization for proper nouns

            # Track multi-language words
            if len(languages) > 1:
                self.multi_language[title.lower()] = list(languages.keys())

    def _extract_languages(self, parsed) -> Dict[str, str]:
        """Extract language sections from parsed wikitext.

        Returns:
            Dict mapping language name to section text
        """
        import re

        text = str(parsed)
        languages = {}

        # Match level-2 headers: ==Language==
        # Pattern matches: newline, ==, language name (no =), ==
        # Uses lookahead to capture everything until next level-2 header or end
        pattern = r'\n==([\w\s]+)==\n(.*?)(?=\n==[\w\s]+=|$)'

        for match in re.finditer(pattern, text, re.DOTALL):
            lang_name = match.group(1).strip()
            section_text = match.group(2)
            languages[lang_name] = section_text

        return languages

    def _extract_usage_labels(self, section_text: str) -> Set[str]:
        """Extract usage labels like {{obsolete}}, {{archaic}}, or (archaic).

        Returns:
            Set of usage labels found
        """
        labels = set()

        # Parse section
        try:
            parsed = mwp.parse(section_text)
        except Exception:
            return labels

        # Find templates
        for template in parsed.filter_templates():
            name = str(template.name).strip().lower()

            # Common usage label templates
            if name in self.obsolete_labels | self.archaic_labels | self.rare_labels:
                labels.add(name)

            # Also check for {{label|en|obsolete}} format
            if name in {'label', 'lb', 'context'}:
                for param in template.params:
                    param_str = str(param.value).strip().lower()
                    if param_str in self.obsolete_labels | self.archaic_labels | self.rare_labels:
                        labels.add(param_str)

        # Also check for plain text labels in parentheses: (archaic), (obsolete), (rare, dated)
        import re
        all_labels = self.obsolete_labels | self.archaic_labels | self.rare_labels
        for label in all_labels:
            # Match label in parentheses - can be first or in comma-separated list
            # Matches: (archaic), (rare, dated), (obsolete)
            pattern = r'[\(,]\s*' + re.escape(label) + r'\s*[,\)]'
            if re.search(pattern, section_text, re.IGNORECASE):
                labels.add(label)

        return labels

    def _is_proper_noun(self, section_text: str) -> bool:
        """Check if word is a proper noun.

        Returns:
            True if proper noun header found
        """
        # Look for ===Proper noun=== header
        return '===Proper noun===' in section_text or '====Proper noun====' in section_text

    def save_to_json(self, output_path: Path):
        """Save extracted metadata to JSON file.

        Args:
            output_path: Path to output JSON file
        """
        metadata = {
            'obsolete': sorted(list(self.obsolete_words)),
            'archaic': sorted(list(self.archaic_words)),
            'rare': sorted(list(self.rare_words)),
            'proper_nouns': sorted(list(self.proper_nouns)),
            'foreign_only': sorted(list(self.foreign_only)),
            'multi_language': self.multi_language,
            'stats': {
                'obsolete_count': len(self.obsolete_words),
                'archaic_count': len(self.archaic_words),
                'rare_count': len(self.rare_words),
                'proper_noun_count': len(self.proper_nouns),
                'foreign_only_count': len(self.foreign_only),
                'multi_language_count': len(self.multi_language),
            }
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"✓ Saved metadata to {output_path}")
        logger.info(f"  Obsolete: {len(self.obsolete_words):,}")
        logger.info(f"  Archaic: {len(self.archaic_words):,}")
        logger.info(f"  Rare: {len(self.rare_words):,}")
        logger.info(f"  Proper nouns: {len(self.proper_nouns):,}")
        logger.info(f"  Foreign-only: {len(self.foreign_only):,}")
        logger.info(f"  Multi-language: {len(self.multi_language):,}")


def download_wiktionary_dump(output_path: Path, force: bool = False):
    """Download Wiktionary XML dump.

    Args:
        output_path: Path to save dump file
        force: Force re-download even if file exists
    """
    if output_path.exists() and not force:
        logger.info(f"✓ Dump already exists: {output_path}")
        return

    logger.info(f"Downloading Wiktionary dump from {WIKTIONARY_DUMP_URL}")
    logger.info("(This may take 10-30 minutes, file is ~1-2GB compressed)")

    response = requests.get(WIKTIONARY_DUMP_URL, stream=True)
    response.raise_for_status()

    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)

            # Progress indicator
            if total_size > 0:
                progress = (downloaded / total_size) * 100
                logger.info(f"  Progress: {progress:.1f}% ({downloaded:,} / {total_size:,} bytes)")

    logger.info(f"✓ Downloaded to {output_path}")


def parse_wiktionary_dump(dump_path: Path, max_pages: int = None, max_workers: int = 10) -> WiktionaryExtractor:
    """Parse Wiktionary XML dump and extract metadata using multiprocessing.

    Args:
        dump_path: Path to .xml.bz2 dump file
        max_pages: Maximum pages to process (for testing, None = all)
        max_workers: Number of worker processes (default: 10)

    Returns:
        WiktionaryExtractor with extracted metadata
    """
    logger.info(f"Parsing Wiktionary dump: {dump_path}")
    logger.info(f"Using {max_workers} worker processes")

    extractor = WiktionaryExtractor()
    pages_processed = 0
    batch = []
    batch_size = 1000  # Process 1000 pages per batch

    # Open bz2 compressed file
    with bz2.open(dump_path, 'rt', encoding='utf-8') as f:
        current_title = None
        current_text = []
        in_text = False

        for line in f:
            # Extract page title
            if '<title>' in line:
                current_title = line.split('<title>')[1].split('</title>')[0]

            # Extract page text
            elif '<text' in line:
                in_text = True
                # Handle single-line text
                if '</text>' in line:
                    text_content = line.split('<text')[1].split('>')[1].split('</text>')[0]
                    if current_title:
                        batch.append((current_title, text_content))
                        pages_processed += 1

                        # Process batch when full
                        if len(batch) >= batch_size:
                            _process_batch(extractor, batch, max_workers)
                            batch = []
                            logger.info(f"  Processed {pages_processed:,} pages...")

                        if max_pages and pages_processed >= max_pages:
                            break

                    in_text = False
                    current_title = None
                    current_text = []
                else:
                    # Multi-line text
                    text_start = line.split('<text')[1].split('>', 1)[1]
                    current_text.append(text_start)

            elif in_text:
                if '</text>' in line:
                    # End of text
                    text_end = line.split('</text>')[0]
                    current_text.append(text_end)

                    if current_title:
                        full_text = ''.join(current_text)
                        batch.append((current_title, full_text))
                        pages_processed += 1

                        # Process batch when full
                        if len(batch) >= batch_size:
                            _process_batch(extractor, batch, max_workers)
                            batch = []
                            logger.info(f"  Processed {pages_processed:,} pages...")

                        if max_pages and pages_processed >= max_pages:
                            break

                    in_text = False
                    current_title = None
                    current_text = []
                else:
                    current_text.append(line)

    # Process remaining batch
    if batch:
        _process_batch(extractor, batch, max_workers)

    logger.info(f"✓ Processed {pages_processed:,} pages total")
    return extractor


def _process_batch(extractor: WiktionaryExtractor, batch: list, max_workers: int):
    """Process a batch of pages in parallel.

    Args:
        extractor: WiktionaryExtractor to merge results into
        batch: List of (title, text) tuples
        max_workers: Number of worker processes
    """
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all pages in batch
        futures = [executor.submit(extract_page_metadata, title, text) for title, text in batch]

        # Collect results
        for future in as_completed(futures):
            title, results = future.result()
            extractor.merge_results(results)


def main():
    parser = argparse.ArgumentParser(description='Build Wiktionary metadata database')
    parser.add_argument('--download-only', action='store_true', help='Only download dump, don\'t parse')
    parser.add_argument('--parse-only', action='store_true', help='Only parse existing dump')
    parser.add_argument('--force-download', action='store_true', help='Force re-download even if dump exists')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to process (for testing)')
    parser.add_argument('--workers', type=int, default=10, help='Number of worker processes (default: 10)')
    parser.add_argument('--dump-file', type=str, default='wiktionary_parser/enwiktionary-latest.xml.bz2',
                       help='Path to dump file')
    parser.add_argument('--output', type=str, default='src/spelling_bee_solver/data/wiktionary_metadata.json',
                       help='Output JSON path')

    args = parser.parse_args()

    dump_path = Path(args.dump_file)
    output_path = Path(args.output)

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Download phase
    if not args.parse_only:
        download_wiktionary_dump(dump_path, force=args.force_download)

    if args.download_only:
        return

    # Parse phase
    extractor = parse_wiktionary_dump(dump_path, max_pages=args.max_pages, max_workers=args.workers)

    # Save results
    extractor.save_to_json(output_path)

    logger.info("✓ Wiktionary database build complete!")


if __name__ == '__main__':
    main()

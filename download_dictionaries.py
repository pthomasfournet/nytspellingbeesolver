#!/usr/bin/env python3
"""
Dictionary Downloader for Spelling Bee Solver

This script helps download high-quality dictionaries optimized for word games.
Run this to improve the quality of word suggestions.
"""

import requests
from pathlib import Path


def download_file(url, filename, description):
    """Download a file with progress indication."""
    try:
        print(f"Downloading {description}...")
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        filepath = Path.home() / filename
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✓ Downloaded {description} to {filepath}")
        return True
    except (requests.RequestException, IOError, OSError) as e:
        print(f"✗ Failed to download {description}: {e}")
        return False


def main():
    """Download popular word game dictionaries."""
    print("🎯 Word Game Dictionary Downloader")
    print("=" * 50)
    print("This will download high-quality dictionaries for better word suggestions.\n")
    
    # Dictionary sources (you would need to find actual URLs)
    dictionaries = [
        {
            'url': 'https://raw.githubusercontent.com/tabatkins/wordle-list/main/words',
            'filename': 'wordle-words.txt',
            'description': 'Wordle Official Word List (5-letter words)',
        },
        # Note: For real implementation, you'd need to find actual sources for:
        # - Tournament Word List (TWL06/TWL98)
        # - Official Scrabble Players Dictionary
        # - Mobile game dictionaries
        # - Collins Scrabble Words (CSW)
    ]
    
    print("Available dictionaries:")
    for i, dict_info in enumerate(dictionaries, 1):
        print(f"{i}. {dict_info['description']}")
    
    print(f"{len(dictionaries) + 1}. Download all")
    print("0. Exit")
    
    try:
        choice = input("\nEnter your choice (0-{}): ".format(len(dictionaries) + 1))
        choice = int(choice)
        
        if choice == 0:
            print("Exiting...")
            return
        elif choice == len(dictionaries) + 1:
            # Download all
            success_count = 0
            for dict_info in dictionaries:
                if download_file(dict_info['url'], dict_info['filename'], dict_info['description']):
                    success_count += 1
            print(f"\n✓ Downloaded {success_count}/{len(dictionaries)} dictionaries")
        elif 1 <= choice <= len(dictionaries):
            # Download specific dictionary
            dict_info = dictionaries[choice - 1]
            download_file(dict_info['url'], dict_info['filename'], dict_info['description'])
        else:
            print("Invalid choice")
            
    except (ValueError, KeyboardInterrupt):
        print("\nOperation cancelled")
    
    print("\n📝 Note: For best results, try to obtain:")
    print("  • Tournament Word List (TWL06) - Best for American word games")
    print("  • Collins Scrabble Words (CSW) - International Scrabble")
    print("  • Official Scrabble Players Dictionary (OSPD)")
    print("  • Mobile game word lists (Wordscapes, Word Cookies, etc.)")
    print("\nThese can often be found on word game websites or GitHub repositories.")


if __name__ == "__main__":
    main()
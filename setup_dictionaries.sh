#!/bin/bash
# Dictionary Setup Helper for Spelling Bee Solver
# This helps you find and set up better word game dictionaries

echo "🎯 Spelling Bee Solver - Dictionary Setup"
echo "========================================"
echo

# Check current dictionary status
echo "📊 Current Dictionary Status:"
echo

if [ -f "$HOME/twl06.txt" ]; then
    lines=$(wc -l < "$HOME/twl06.txt")
    echo "✓ Tournament Word List (TWL06): $lines words"
elif [ -f "$HOME/twl98.txt" ]; then
    lines=$(wc -l < "$HOME/twl98.txt")
    echo "✓ Tournament Word List (TWL98): $lines words"
else
    echo "❌ No Tournament Word List found"
fi

if [ -f "$HOME/ospd.txt" ]; then
    lines=$(wc -l < "$HOME/ospd.txt")
    echo "✓ Official Scrabble Players Dictionary: $lines words"
else
    echo "❌ No OSPD found"
fi

if [ -f "$HOME/wordle-words.txt" ]; then
    lines=$(wc -l < "$HOME/wordle-words.txt")
    echo "✓ Wordle Word List: $lines words"
else
    echo "❌ No Wordle word list found"
fi

if [ -f "$HOME/sowpods.txt" ]; then
    lines=$(wc -l < "$HOME/sowpods.txt")
    echo "✓ SOWPODS: $lines words"
else
    echo "❌ No SOWPODS found"
fi

echo
echo "💡 To improve word quality, you can:"
echo
echo "1. Download TWL06 (Tournament Word List) - Best for American word games"
echo "   - Search online for 'TWL06 word list download'"
echo "   - Save as: ~/twl06.txt"
echo
echo "2. Download Wordle official word list"
echo "   - Available on GitHub: https://github.com/tabatkins/wordle-list"
echo "   - Save as: ~/wordle-words.txt"
echo
echo "3. Download OSPD (Official Scrabble Players Dictionary)"
echo "   - Search for 'OSPD word list'"
echo "   - Save as: ~/ospd.txt"
echo
echo "4. Mobile game dictionaries:"
echo "   - Wordscapes, Word Cookies, etc. often have GitHub repositories"
echo "   - Save as: ~/wordscapes-dict.txt, ~/word-cookies-dict.txt"
echo
echo "📂 All dictionaries should be saved in your home directory (~)"
echo "🔄 Run './bee P CUAOTN' again after adding dictionaries to see improved results"
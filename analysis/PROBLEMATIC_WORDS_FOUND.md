# Problematic Words Found in 10k Validation

**Date:** October 3, 2025
**Finding:** ~50% of "uncategorized" words are actually trash

## Manual Review Results

### Sample: 100 random words analyzed
**53 problematic words identified (53%)**

### Categories of Problems:

**Archaic/Obsolete (11 words):**
- aedile, apery, frib, guesten, gesses, lumme, misate, strow, vetust, inconcinne, gaingivings

**Scottish/Dialectal (8 words):**
- cuddin, dreul, drooked, gadgie, jannie, shules, suant, whaup

**Foreign Words (12 words):**
- buffi (Italian), camisa (Spanish), cassones (Italian), cerote (Spanish)
- mondains (French), pareiras (Portuguese), serenata (Italian), themata (Greek)
- taiahas (Maori), zufolo (Italian), warragal (Aboriginal), melamdim (Hebrew)

**Proper Nouns (7 words):**
- glenn, everette, mysore, patti, rowett, woolf, wollongong

**Extremely Obscure (12 words):**
- arietate, chronon, colobid, hoka, mahoohoo, pykar, quomodos, siseraries, troilist, tussuck, indenes, myceles

**Potentially Offensive (3 words):**
- mestee, arsier, cerote

### Additional 50-word sample found:

**More Foreign:**
- abrazo (Spanish), farinha (Portuguese), krewe (Louisiana French), karaka (Maori)

**More Proper Nouns:**
- kelsey, leonel, osceola, parsi, sikh

**More Archaic:**
- olent, pheere, tinnen, usuresses, wadd

**More Dialectal:**
- boohai (NZ), skellies (British), sook (Australian)

## Root Cause

**SOWPODS dictionary is too permissive** - includes Scrabble-legal words from:
- Historical texts (archaic)
- Foreign languages commonly used in English
- Regional dialects (Scottish, Irish, Australian, NZ)
- Proper nouns that became words
- Obscure technical/scientific terms

## Current Filter Limitations

1. **Wiktionary database only 100k pages** (10% of full 10M)
   - Missing most archaic/dialectal words

2. **Manual lists incomplete**
   - Only 16 archaic words listed
   - Missing Scottish, foreign, obscure terms

3. **Pattern matching too basic**
   - Can't detect foreign language patterns
   - Can't identify dialectal variations

## Solution: Full 10M Wiktionary Rebuild

Building complete Wiktionary database with FIXED parser (previous 10M build used broken parser).

Expected improvement: +10-20% better filtering of trash words.

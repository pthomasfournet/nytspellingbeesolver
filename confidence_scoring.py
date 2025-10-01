"""
Confidence scoring system for NYT Spelling Bee solver.
Evaluates word quality based on multiple dictionaries and linguistic patterns.
"""


def calculate_dictionary_scores(word):
    """Calculate scores from different dictionary sources"""
    scores = {
        "webster": 0,
        "american_english": 0,
        "google_common": 0,
        "frequency": 0,
        "length_penalty": 0,
        "foreign_penalty": 0,
        "technical_penalty": 0
    }
    
    # Basic scoring logic - simplified for now
    # In a full implementation, this would check multiple dictionary sources
    
    # For now, assume all words get some base scores
    scores["american_english"] = 50  # Base score for being in any dictionary
    
    # Length penalty for very long words
    if len(word) > 10:
        scores["length_penalty"] = -20
    elif len(word) > 8:
        scores["length_penalty"] = -10
    
    # Simple pattern-based scoring
    if any(word.endswith(suffix) for suffix in ['ing', 'ed', 'er', 's']):
        scores["frequency"] = 10  # Common word endings
    
    return scores


def calculate_aggregate_confidence(word, dict_scores=None):
    """
    Calculate aggregate confidence score for a word using multiple signals.
    
    Args:
        word (str): The word to score
        dict_scores (dict, optional): Pre-calculated dictionary scores
        
    Returns:
        int: Confidence score from 0-100
    """
    if dict_scores is None:
        dict_scores = calculate_dictionary_scores(word)
    
    # Start with base score from American English dictionary
    base_score = dict_scores["american_english"]
    
    # Google Common Words bonus (indicates very common usage)
    if dict_scores["google_common"] > 0:
        base_score = min(100, int(base_score * 1.2))  # 20% bonus, capped at 100

    # Frequency bonus
    if dict_scores["frequency"] > 0:
        base_score = min(100, base_score + dict_scores["frequency"])

    # For words in Webster's dictionary that are also common, ensure high confidence
    if dict_scores["webster"] > 0 and dict_scores["google_common"] > 0:
        base_score = max(base_score, 90)  # Smart boost for common + authoritative

    # Apply penalties (but don't let them destroy Webster's words)
    if dict_scores["webster"] <= 0:  # Only apply penalties to non-Webster's words
        base_score += dict_scores["length_penalty"]
        base_score += dict_scores["foreign_penalty"]
        base_score += dict_scores["technical_penalty"]

    # Special bonuses
    if len(set(word)) == 7:  # Pangrams
        base_score += 10

    # Length bonuses for reasonable word lengths
    if 4 <= len(word) <= 8:
        base_score += 5

    # Word pattern bonuses for common English patterns
    if any([
        word.endswith("ing"),
        word.endswith(("tion", "sion")),
        word.endswith(("able", "ible")),
        word.endswith(("ness", "ment", "ful")),
        word.endswith(("er", "or", "ly", "ed"))
    ]):
        base_score += 5

    # Ensure minimum score for words in any legitimate dictionary
    if dict_scores["american_english"] > 0:
        base_score = max(base_score, 20)

    # Cap the score
    return max(0, min(100, base_score))
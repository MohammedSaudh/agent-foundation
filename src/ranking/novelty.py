from src.ranking.simple import text_similarity

def novelty_score(new_text: str, past_texts: list[str]) -> float:
    """
    Returns a novelty score between 0 and 1.
    Higher = more new (less similar to what we saw before )
    """

    if not past_texts:
        return 1.0
    
    best_similarity = 0.0
    for t in past_texts:
        s = text_similarity(new_text, t)
        if s > best_similarity:
            best_similarity = s

    return 1.0 - best_similarity
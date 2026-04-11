from __future__ import annotations                                                     # Allows using type hints without needing classes/functions to be defined beforehand

from src.ranking.simple import text_similarity                                         # Import the lexical similarity helper used by the baseline novelty scorer.

def novelty_score(new_text:str, past_texts:list[str]) ->  float:                       # Compute baseline lexical novelty for one text against a history list.
    if not past_texts:
        return 1.0
    
    best_similarity = max(text_similarity(new_text, historical_text) for historical_text in past_texts) # Find the highest lexical similarity against the history corpus.
    return 1.0 - best_similarity


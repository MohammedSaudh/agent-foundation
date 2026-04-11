from __future__ import annotations                                                     # Allows using type hints without needing classes/functions to be defined beforehand



def text_similarity(a: str, b: str) -> float:                                         # Compute a lightweight token-overlap similarity between two strings.
    """Compute a simple token-overlap similarity bounded to [0, 1]."""   
    tokens_a = set(a.lower().split())                                                 # Lowercase and split the first text into unique tokens.
    tokens_b = set(b.lower().split())                                                 # Lowercase and split the second text into unique token
    if not tokens_a or not tokens_b:                                                  #Return zero similarity if either side has no tokens.
        return 0.0

    return len(tokens_a & tokens_b) / max(len(tokens_a), len(tokens_b))               #Return normalized overlap size using the larger token count as denominator.
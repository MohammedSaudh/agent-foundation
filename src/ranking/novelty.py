from __future__ import annotations                              # Enable postponed evaluation of type hints

import numpy as np                                              # Numerical operations for similarity calculations
from src.ranking.embedding import embed_texts                   # Reuse embedding helper for semantic text vectors


def novelty_score(new_text: str, past_texts: list[str]) -> float:
    """
    Return a novelty score between 0 and 1.
    Higher = more new (less similar to past articles)
    """

    if not past_texts:                                          # No history means the article is fully novel
        return 1.0

    history_embeddings = embed_texts(past_texts)                # Convert all past texts into normalized embeddings

    if history_embeddings.size == 0:                            # Handle empty embedding matrix safely
        return 1.0

    current_embedding = embed_texts([new_text])[0]              # Convert current article into one normalized embedding

    similarities = history_embeddings @ current_embedding       # Cosine similarity via dot product on normalized vectors

    max_similarity = float(np.max(similarities))                # Find the most similar past article

    return max(0.0, min(1.0, 1.0 - max_similarity))             # Convert similarity to novelty and clamp to valid range
from __future__ import annotations                              # Enable postponed evaluation of type hints

import numpy as np                                              # Numerical operations for vectors
from sentence_transformers import SentenceTransformer           # Pretrained sentence embedding model

EMBEDDING_DIM = 384                                             # all-MiniLM-L6-v2 returns 384-dimensional vectors

_MODEL: SentenceTransformer | None = None                       # Cache model globally so it loads only once


def get_model() -> SentenceTransformer:
    global _MODEL                                               # Allow updating the cached global model

    if _MODEL is None:                                          # Load the model only on first use
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")        # Lightweight semantic embedding model

    return _MODEL                                               # Reuse the same loaded model


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:                                               # Return an empty matrix with correct embedding width
        return np.empty((0, EMBEDDING_DIM), dtype=np.float32)

    return get_model().encode(                                  # Convert text list into normalized embedding vectors
        texts,
        convert_to_numpy=True,                                  # Return numpy arrays instead of tensors
        normalize_embeddings=True                               # Normalize vectors so dot product = cosine similarity
    )


def embedding_novelty_score(
    text: str,
    history_texts: list[str],
    history_embeddings: np.ndarray | None = None,
) -> float:
    if history_embeddings is None:                              # Compute history embeddings only if caller did not pass them
        if not history_texts:                                   # No history means the article is fully novel
            return 1.0
        history_embeddings = embed_texts(history_texts)         # Embed past articles once

    elif history_embeddings.size == 0:                          # Empty history embedding matrix also means fully novel
        return 1.0

    current_embedding = embed_texts([text])[0]                  # Embed current article into one normalized vector

    similarities = history_embeddings @ current_embedding       # Dot product of normalized vectors = cosine similarity

    max_similarity = float(np.max(similarities))                # Keep only the most similar past article

    return max(0.0, min(1.0, 1.0 - max_similarity))             # Convert similarity into novelty and clamp to valid range
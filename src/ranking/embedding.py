from sentence_transformers import SentenceTransformer, util
import numpy as np

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")

    return _model


def embed_texts(texts:list[str]) -> np.ndarray:
    """
    Returns normalized embeddings for a list of texts
    """

    model = get_model()
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    return embeddings


def embedding_novelty_score(
        text: str,
        history_texts: list[str],
        history_embeddings: np.ndarray | None = None,

) -> float:
    """
    Novelty = 1 - max cosine similarity vs history
    Output : 0..1 (higher = more novel)
    """
    if not history_texts:
        return 1.0
    
    model = get_model()

    # Embed current article
    emb= model.encode(
        [text],
        convert_to_numpy = True,
        normalize_embeddings = True
    )[0]


    #Embed history if not precomputed
    if history_embeddings is None:
        history_embeddings = embed_texts(history_texts)


    #Cosine similarity = Dot product(already normalized)

    sims = history_embeddings @ emb

    max_sim = float(np.max(sims))

    novelty = 1.0 - max_sim

    # Clamp Safety
    return max(0.0, min(1.0, novelty))

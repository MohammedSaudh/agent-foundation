from __future__ import annotations                              #Enable postponed annotation evaluation fro cleaner type hints.
import numpy as np                                              # for vector operations and array handling.
from sentence_transformers import SentenceTransformer           #Sentence transformer wrapper for text embeddings.
_MODEL : SentenceTransformer |  None = None                     # Cache the embedding model at module scope so it loads only once per process.
def get_model() -> SentenceTransformer:                         #Lazily construct and return the sentence-transformer model
    global _MODEL                                               #Allow assignment to the module- level cache variable
    if _MODEL is None:                                          #Load the model only first time  
        _MODEL = SentenceTransformer("all-MiniLM-L6-v2")        
    return _MODEL                                               #return the cached model instance.

def embed_texts(texts: list[str]) -> np.ndarray:                #Embed a batach of texts into normalized vectors.
    if not texts:
        return np.empty((0, 0), dtype = np.float32)
    
    return get_model().encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings= True
    )
def embedding_novelty_score(text:str,history_texts: list[str],history_embeddings: np.ndarray | None = None,)->float:   #Score one text by how novel it is relative to a history corpus
    if history_embeddings is None:                                                                                     #Compute history embeddings on demand when they were not precomputed
        if not history_texts :                                                                                         #Return full novelty when there no history at all 
            return 1.0                        
        history_embeddings = embed_texts(history_texts)                                                                #Embed the history texts once
    elif history_embeddings.size == 0:                                                                                 #Handle the case where the caller explicitly passed an empty embedding matrix 
        return 1.0
    current_embeddings = embed_texts([text])[0]                                                                        #Embed the current text into one normalized vector

    max_similarity = float(np.max(history_embeddings @ current_embeddings))                                            #Compute the most similar historical article using a dot product on normalized embeddings

    return max(0.0, min(1.0,1.0 - max_similarity))                                                                     #Convert similarity to to novelty and clamp minor floating point drift into valid range.





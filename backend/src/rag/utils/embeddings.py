# Embedding model for retrieval is set here. To change, set EMBEDDING_MODEL_NAME below or via environment variable.
# Answer generation model is set in llm_mistral.py (llm_mistral).

import os
from sentence_transformers import SentenceTransformer
from typing import Union, List
import numpy as np

# Lazy loading to ensure environment variables are loaded first
_embed_model = None

def get_embed_model():
    """Get the SentenceTransformer model, loading it only when needed."""
    global _embed_model
    if _embed_model is None:
        # TEMPORARILY HARDCODED to bypass environment variable issues
        EMBEDDING_MODEL_NAME = "all-mpnet-base-v2"
        print(f"Loading SentenceTransformer model: {EMBEDDING_MODEL_NAME}")
        _embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("Model loaded successfully.")
    return _embed_model

def embed_texts(texts: Union[str, List[str]]) -> np.ndarray:
    """
    Embed a single string or a list of strings using the global model.

    Args:
        texts: str or list of str to embed.

    Returns:
        Numpy array of embeddings.
    """
    if isinstance(texts, str):
        texts = [texts]
    embed_model = get_embed_model()  # Lazy load the model
    return embed_model.encode(texts, convert_to_numpy=True)
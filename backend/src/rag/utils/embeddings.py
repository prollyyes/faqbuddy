from sentence_transformers import SentenceTransformer
from typing import Union, List
import numpy as np

# Initialize model once
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

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
    return embed_model.encode(texts, convert_to_numpy=True)
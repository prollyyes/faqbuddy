from sentence_transformers import SentenceTransformer
import numpy as np
import os

# Use the same embedding model as the RAG system
# Using all-mpnet-base-v2 instead of all-MiniLM-L12-v2 due to model card issues
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-mpnet-base-v2")

# Lazy loading to avoid conflicts with RAG system
_model = None

def get_model():
    """Get the SentenceTransformer model, loading it only when needed."""
    global _model
    if _model is None:
        print(f"Loading SentenceTransformer model: {EMBEDDING_MODEL_NAME}")
        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        print("Model loaded successfully.")
    return _model

def extract_hand_features(question):
    connectives = [" e ", " oppure", "se ", "quando", "come", "perché", "quali", "quale", "posso", "strategia", "passi"]
    modal_verbs = ["posso", "devo", "vorrei", "potrei", "dovrei", "suggerisci", "consigli", "preferirei"]
    q = question.lower()
    words = q.split()
    return [
        len(words),
        sum(1 for c in connectives if c in q),
        q.count("?"),
        int(any(word in q for word in ["come", "perché", "quali", "quale", "posso"])),
        len(q),
        sum(1 for v in modal_verbs if v in q),
        int("," in q or ";" in q),
        int(" e " in q or " oppure " in q),
        int(any(q.startswith(w) for w in ["come", "quali", "quale", "perché"])),
    ]

def extract_features(question):
    hand = extract_hand_features(question)
    model = get_model()  # Lazy load the model
    semantic = model.encode(question)
    return np.concatenate([hand, semantic])

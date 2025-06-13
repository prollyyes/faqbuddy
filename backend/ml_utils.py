from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

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
    semantic = model.encode(question)
    return np.concatenate([hand, semantic])
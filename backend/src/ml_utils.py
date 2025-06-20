from sentence_transformers import SentenceTransformer
import numpy as np
import requests

# inizialize model once
print("Loading SentenceTransformer model...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Model loaded successfully.")

""" OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:4b"  # o modello caricato """

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


""" def query_ollama(prompt: str) -> str:
    response = requests.post(OLLAMA_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    })
    return response.json().get("response", "").strip()

def classify_question(question: str) -> str:
    prompt = (
        "Classifica la seguente domanda SOLO come 'simple' o 'complex'. "
        "Rispondi esclusivamente con una di queste due parole, senza spiegazioni, motivazioni o testo aggiuntivo.\n\n"
        "Esempi:\n"
        "Domanda: Quanti crediti vale il corso di informatica?\nRisposta: simple\n"
        "Domanda: Come posso organizzare il piano di studi per laurearmi in 3 anni?\nRisposta: complex\n"
        f"Domanda: {question}\nRisposta:"
    )
    result = query_ollama(prompt)
    # Cerca la parola chiave nella risposta
    return result.lower() """
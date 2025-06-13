########################################################
########## Versione supervecchia da buttare,    
########## usavo ancora delle euristiche invece di un modello ML
########################################################

from fastapi import FastAPI
from pydantic import BaseModel
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:4b"  # o modello caricato

app = FastAPI()

class QueryRequest(BaseModel):
    question: str

def query_ollama(prompt: str) -> str:
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
    return result.lower()



def classify_heuristic(question: str) -> str:
    complex_connectives = [
        " e ", " oppure", "se ", "quando", "come", "perché", "quali", "quale", "posso", "strategia", "passi",
        "conciliare", "organizzare", "devo", "vorrei", "potrei", "consigli", "suggerisci", "gestire", "pianificare",
        "evitare", "insieme", "differenza", "vantaggi", "svantaggi", "problemi", "soluzioni"
    ]
    min_complex_length = 10

    q = question.lower()
    word_count = len(q.split())
    connectives_found = sum(1 for c in complex_connectives if c in q)
    multiple_questions = q.count("?") > 1

    if word_count > min_complex_length or connectives_found > 0 or multiple_questions:
        return "complex"
    else:
        return "simple"

@app.post("/ask")
async def ask_question(payload: QueryRequest):
    tipo = classify_question(payload.question)
    return {"type": tipo}


if __name__ == "__main__":
    import time
    import random
    test_questions = [
        # Simple
        "Quanti crediti vale il corso di informatica?",
        "Quando si tiene l'esame di matematica 2?",
        "Qual è l'aula della lezione di diritto?",
        "Chi è il docente di economia politica?",
        "Qual è la durata della prova scritta?",
        "Qual è il codice del corso di statistica?",
        "Quanti appelli ci sono a luglio?",
        "Quando inizia il semestre primaverile?",
        "Qual è il voto minimo per superare l'esame?",
        "Dove si trova la segreteria studenti?",
        # Complex
        "Come posso organizzare il piano di studi per laurearmi in 3 anni?",
        "Quali esami posso sostenere in parallelo senza problemi di sovrapposizioni?",
        "Se salto l'esame di statistica a giugno, quando posso riprovare e quali sono le conseguenze?",
        "Posso laurearmi in 3 anni?",
        "Posso superare il test di economia studiando solo 2 ore? E 3? E 4?",
        "Come posso recuperare un esame non superato senza ritardare la laurea?",
        "Quali strategie posso adottare per migliorare la media voti?",
        "Come posso conciliare lavoro e studio durante il semestre?",
        "Quali sono i passi per cambiare corso di laurea senza perdere crediti?",
        "Come posso pianificare gli esami per evitare sovrapposizioni e ritardi?",
    ]

    random.shuffle(test_questions)

    # Benchmark for model
    start_model = time.time()
    model_results = [classify_question(q) for q in test_questions]
    elapsed_model = time.time() - start_model

    # Benchmark for heuristic
    start_heur = time.time()
    heuristic_results = [classify_heuristic(q) for q in test_questions]
    elapsed_heur = time.time() - start_heur

    # Accuracy benchmark (taking gemma3:4b as ground truth)
    correct = 0
    for i in range(len(test_questions)):
        if model_results[i].strip() == heuristic_results[i].strip():
            correct += 1

    accuracy = correct / len(test_questions) * 100

    # Print results
    for i, q in enumerate(test_questions):
        print(f"Question: {q}\nModel (gemma3:4b): {model_results[i]}\tHeuristic: {heuristic_results[i]}\n")
    print(f"Total time for model: {elapsed_model:.2f} seconds")
    print(f"Total time for heuristic: {elapsed_heur:.4f} seconds")
    print(f"{len(test_questions)} questions processed.")
    print(f"Heuristic accuracy vs model: {accuracy:.2f}%")
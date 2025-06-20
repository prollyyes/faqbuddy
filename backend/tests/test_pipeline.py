import time
from src.ml_utils import extract_features
from src.local_llm import classify_question
from src.text_2_SQL.converter import TextToSQLConverter
from src.text_2_SQL.db_utils import get_db_connection, get_database_schema
from src.rag.rag_core import RAGSystem

# Carica il modello ML già addestrato
import os
import joblib
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'ml_model.joblib'))
clf = joblib.load(model_path)


# Domande di test
test_questions = [
    "Elenca tutti i professori",
    "Mostra tutti i libri",
    "Quali esami ci sono nel 2024?",
    "Elenca tutti i libri",
    "Quanti libri ci sono in tutto?",
    "Quanti professori insegnano nella stanza C305?",
    "Come posso organizzare il piano di studi per laurearmi in 3 anni?",
    "Quali esami posso sostenere in parallelo senza problemi di sovrapposizioni??",
]

# Setup T2SQL
conn = get_db_connection()
schema = get_database_schema(conn)
converter = TextToSQLConverter()

# Setup RAG
rag = RAGSystem()

print("\n--- Benchmark: Switcher ML + fallback LLM + T2SQL ---")
correct_sql = 0
correct_rag = 0
times = []

for q in test_questions:
    print(f"\nDomanda: {q}")
    start = time.time()

    features = [extract_features(q)]
    ml_pred = clf.predict(features)[0]
    proba = max(clf.predict_proba(features)[0])
    print(f"ML: {ml_pred} (confidenza: {proba:.2f})")

    threshold = 0.7
    if proba < threshold:
        llm_pred = classify_question(q)
        print(f"LLM: {llm_pred}")
        final_pred = llm_pred.strip().lower()
    else:
        final_pred = ml_pred.strip().lower()

    if final_pred == "simple":
        prompt = converter.create_prompt(q, schema)
        raw_response = converter.query_llm(prompt)
        sql_query = converter.clean_sql_response(raw_response)
        print(f"SQL: {sql_query}")
        if sql_query != "INVALID_QUERY":
            correct_sql += 1
    else:
        print("Risposta: RAG di default")
        rag_result = rag.generate_response(q)
        print("RAG response:", rag_result["response"])
        correct_rag += 1

    times.append(time.time() - start)

print("\n--- RISULTATI BENCHMARK ---")
print(f"Domande processate: {len(test_questions)}")
print(f"Risposte SQL valide: {correct_sql}")
print(f"Risposte RAG di default: {correct_rag}")
print(f"Tempo medio risposta: {sum(times)/len(times):.2f} s")
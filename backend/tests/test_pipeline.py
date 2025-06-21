import time
import pytest
import os
import joblib
from src.switcher.ml_utils import extract_features
from src.utils.utils_llm import classify_question
from src.text_2_SQL.converter import TextToSQLConverter
from src.text_2_SQL.db_utils import get_db_connection, get_database_schema
from src.rag.rag_core import RAGSystem

# Caricamento modello ML
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'ml_model.joblib'))
clf = joblib.load(model_path)

# Setup SQL e RAG
conn = get_db_connection()
schema = get_database_schema(conn)
converter = TextToSQLConverter()
rag = RAGSystem()

# Domande di test parametrizzate
@pytest.mark.parametrize("question", [
    # Domande "simple"
    "Mostra tutti i corsi del primo semestre",
    "Mostra tutti i materiali didattici per il corso Fondamenti di Informatica",
    "Quali sono i corsi con frequenza obbligatoria?",
    # Domande "complex"
    "Come posso organizzare il mio piano di studi per laurearmi in 3 anni?",
    "Quali sono le procedure per il riconoscimento di esami sostenuti all’estero?",
])
def test_question_pipeline(question):
    print(f"\nDomanda: {question}")
    start = time.time()

    features = [extract_features(question)]
    ml_pred = clf.predict(features)[0]
    proba = max(clf.predict_proba(features)[0])
    print(f"ML: {ml_pred} (confidenza: {proba:.2f})")

    threshold = 0.7
    if proba < threshold:
        llm_pred = classify_question(question)
        print(f"LLM: {llm_pred}")
        final_pred = llm_pred.strip().lower()
    else:
        final_pred = ml_pred.strip().lower()

    if final_pred == "simple":
        prompt = converter.create_prompt(question, schema)
        raw_response = converter.query_llm(prompt)
        sql_query = converter.clean_sql_response(raw_response)
        print(f"SQL: {sql_query}")
        assert sql_query != "INVALID_QUERY", "La query SQL è invalida"

        try:
            cur = conn.cursor()
            cur.execute(sql_query)
            rows = cur.fetchall()
            assert rows is not None, "La query non ha restituito righe"
            if cur.description is not None:
                columns = [desc[0] for desc in cur.description]
                results = [dict(zip(columns, row)) for row in rows]
                print("Risultato query:", results)

                natural_response = converter.from_sql_to_text(question, results)
                print("Risposta naturale:", natural_response)
            else:
                print("La query non restituisce colonne.")
            cur.close()
        except Exception as e:
            conn.rollback()
            pytest.fail(f"Errore nell'esecuzione della query: {e}")
    else:
        rag_result = rag.generate_response(question)
        print("RAG response:", rag_result["response"])
        assert rag_result["response"], "RAG non ha prodotto risposta"

    print(f"Tempo di risposta: {time.time() - start:.2f}s")

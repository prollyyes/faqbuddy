import time
import pytest
from ..src.switcher.MLmodel import MLModel
from ..src.text_2_SQL.converter import TextToSQLConverter
from ..src.utils.db_utils import get_connection, MODE
from ..src.utils.db_handler import DBHandler
from ..src.utils.llm_gemma import classify_question

# ##########################################
## DEPRECATED IMPORT RAGSystem, to be UPDATED
from src.rag.rag_core import RAGSystem

# Inizializza risorse condivise
ml_model = MLModel()
converter = TextToSQLConverter()
rag = RAGSystem()

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

    # Nuova connessione per ogni test
    db = DBHandler(get_connection(mode=MODE))
    schema = db.get_schema()

    ml_pred, proba = ml_model.inference(question)
    print(f"ML: {ml_pred} (confidenza: {proba:.2f})")

    threshold = 0.7
    if proba < threshold:
        # come nel main.py, setto a "complex" di default se scendo sotto la soglia
        # llm_pred = classify_question(question)
        # print(f"LLM: {llm_pred}")
        # final_pred = llm_pred.strip().lower()
        final_pred = "complex"
    else:
        final_pred = ml_pred.strip().lower()

    if final_pred == "simple":
        max_attempts = 2
        attempt = 0
        while attempt < max_attempts:
            prompt = converter.create_prompt(question, schema)
            raw_response = converter.query_llm(prompt)
            sql_query = converter.clean_sql_response(raw_response)
            print(f"SQL: {sql_query}")
            if not converter.is_sql_safe(sql_query) or sql_query == "INVALID_QUERY":
                print(f"Attempt {attempt+1}: Invalid SQL query, retrying...")
                attempt += 1
                continue
            try:
                rows, columns = db.run_query(sql_query, fetch=True, columns=True)
                results = [dict(zip(columns, row)) for row in rows]
                if results:
                    print("Risultato query:", results)
                    natural_response = converter.from_sql_to_text(question, results)
                    print("Risposta naturale:", natural_response)
                    db.close_connection()
                    break
                else:
                    print(f"Attempt {attempt+1}: Query returned no results, retrying...")
                    attempt += 1
            except Exception as e:
                db.connection_rollback()
                print(f"Attempt {attempt+1}: Errore nell'esecuzione della query: {e}")
                attempt += 1
        else:
            # Dopo 2 tentativi falliti, fallback RAG
            print("Fallback to RAG after 2 failed attempts.")
            rag_result = rag.generate_response(question)
            print("RAG response:", rag_result["response"])
            db.close_connection()
            assert rag_result["response"], "RAG non ha prodotto risposta"
    else:
        rag_result = rag.generate_response(question)
        print("RAG response:", rag_result["response"])
        db.close_connection()
        assert rag_result["response"], "RAG non ha prodotto risposta"

    print(f"Tempo di risposta: {time.time() - start:.2f}s")
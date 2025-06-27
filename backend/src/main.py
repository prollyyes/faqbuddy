from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.text_2_SQL.converter import TextToSQLConverter
from src.text_2_SQL.db_utils import get_db_connection, get_database_schema, is_sql_safe
from src.switcher.ml_utils import extract_features
from src.local_llm import classify_question
from src.rag.rag_adapter import RAGSystem
import os
import joblib

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class T2SQLRequest(BaseModel):
    question: str

# Carica il modello ML una sola volta
model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'ml_model.joblib'))
clf = joblib.load(model_path)
converter = TextToSQLConverter()
rag = RAGSystem()  # Usa la tua classe già pronta

@app.post("/t2sql")
def t2sql_endpoint(req: T2SQLRequest):
    conn = get_db_connection()
    schema = get_database_schema(conn)
    question = req.question

    # 1. Switcher ML
    features = [extract_features(question)]
    ml_pred = clf.predict(features)[0]
    proba = max(clf.predict_proba(features)[0])

    # 2. Fallback LLM se confidenza bassa
    threshold = 0.7
    fallback = False
    if proba < threshold:
        llm_pred = classify_question(question)
        final_pred = llm_pred.strip().lower()
        fallback = True
    else:
        final_pred = ml_pred.strip().lower()

    # 3. Routing finale
    if final_pred == "simple":
        prompt = converter.create_prompt(question, schema)
        raw_response = converter.query_llm(prompt)
        print("RISPOSTA GREZZA MISTRAL:", repr(raw_response))
        sql_query = converter.clean_sql_response(raw_response)
        print("QUERY SQL GENERATA:\n", sql_query)
        if not is_sql_safe(sql_query):
            return {
                "chosen": "INVALID_QUERY",
                "ml_model": ml_pred,
                "ml_confidence": proba,
                "mistral7B": sql_query
            }
        try:
            cur = conn.cursor()
            cur.execute(sql_query)
            rows = cur.fetchall()
            if cur.description is not None:
                columns = [desc[0] for desc in cur.description]
                result = [dict(zip(columns, row)) for row in rows]
            else:
                columns = []
                result = []
            cur.close()
            conn.close()
            return {
                "result": result,
                "query": sql_query,
                "chosen": "T2SQL",
                "ml_model": ml_pred,
                "ml_confidence": proba,
                "fallback_gemma": fallback
            }
        except Exception as e:
            return {
                "result": str(e),
                "query": sql_query,
                "chosen": "T2SQL",
                "ml_model": ml_pred,
                "ml_confidence": proba,
                "fallback_gemma": fallback
            }
    else:
        # Fallback RAG
        rag_result = rag.generate_response(question)
        return {
            "result": rag_result["response"],
            "chosen": "RAG",
            "ml_model": ml_pred,
            "ml_confidence": proba,
            "retrieval_time": rag_result["retrieval_time"],
            "generation_time": rag_result["generation_time"],
            "total_time": rag_result["total_time"],
            "context_used": rag_result["context_used"]
        }
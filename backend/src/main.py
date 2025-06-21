from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.text_2_SQL.converter import TextToSQLConverter
from src.utils.db_utils import get_db_connection
from src.utils.utils_llm import classify_question
from src.rag.rag_core import RAGSystem
from src.utils.db_handler import DBHandler
from src.switcher.MLmodel import MLModel

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

# Inizializza modello ML
ml_model = MLModel()

# Inizializza converter Text-to-SQL
converter = TextToSQLConverter()

# Inizializza RAG
rag = RAGSystem()



@app.post("/t2sql")
def t2sql_endpoint(req: T2SQLRequest):
    question = req.question

    # Inizializza DBHandler
    db = DBHandler(get_db_connection())
    schema = db.get_schema()

     # 1. Switcher ML
    ml_pred, proba = ml_model.inference(question)

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
        max_attempts = 3
        attempt = 0
        while attempt < max_attempts:
            prompt = converter.create_prompt(question, schema)
            raw_response = converter.query_llm(prompt)
            sql_query = converter.clean_sql_response(raw_response)
            print(f"SQL Query: {sql_query}")
            if not converter.is_sql_safe(sql_query) or sql_query == "INVALID_QUERY":
                print(f"Attempt {attempt+1}: Invalid SQL query, retrying...")
                attempt += 1
                continue
            try:
                rows, columns = db.run_query(sql_query, fetch=True, columns=True)
                result = [dict(zip(columns, row)) for row in rows]
                if result:
                    natural_response = converter.from_sql_to_text(question, result)
                    db.close_connection()
                    print("T2SQL")
                    return {
                        "result": result,
                        "query": sql_query,
                        "natural_response": natural_response,
                        "chosen": "T2SQL",
                        "ml_model": ml_pred,
                        "ml_confidence": proba
                    }
                else:
                    print(f"Attempt {attempt+1}: Query returned no results, retrying...")
                    attempt += 1
            except Exception as e:
                db.connection_rollback()
                print(f"Attempt {attempt+1}: Error executing SQL query, retrying... {e}")
                attempt += 1

        # Dopo 3 tentativi falliti, fallback RAG
        print("Fallback to RAG after 3 failed attempts.")
        rag_result = rag.generate_response(question)
        db.close_connection()
        return {
            "result": rag_result["response"],
            "chosen": "RAG",
            "ml_model": ml_pred,
            "ml_confidence": proba,
            "fallback_gemma": fallback,
            "llm_pred": final_pred if fallback else "",
            "retrieval_time": rag_result["retrieval_time"],
            "generation_time": rag_result["generation_time"],
            "total_time": rag_result["total_time"],
            "context_used": rag_result["context_used"]
        }
    else:
        print("falling back to RAG for complex question prediction.")
        rag_result = rag.generate_response(question)
        db.close_connection()
        return {
            "result": rag_result["response"],
            "chosen": "RAG",
            "ml_model": ml_pred,
            "ml_confidence": proba,
            "fallback_gemma": fallback,
            "llm_pred": final_pred if fallback else "",
            "retrieval_time": rag_result["retrieval_time"],
            "generation_time": rag_result["generation_time"],
            "total_time": rag_result["total_time"],
            "context_used": rag_result["context_used"]
        }
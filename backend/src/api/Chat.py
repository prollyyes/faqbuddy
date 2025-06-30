from src.api.BaseModel import *
from src.api.utils import *
from src.utils.db_handler import DBHandler
from src.switcher.MLmodel import MLModel
from src.text_2_SQL import TextToSQLConverter
from src.rag.rag_adapter import RAGSystem
from src.utils.db_utils import get_connection, MODE
from fastapi import APIRouter


# Initialize router
router = APIRouter()

# Lazy loading variables
_ml_model = None
_converter = None
_rag = None

def get_ml_model():
    """Lazy load ML model."""
    global _ml_model
    if _ml_model is None:
        _ml_model = MLModel()
    return _ml_model

def get_converter():
    """Lazy load Text-to-SQL converter."""
    global _converter
    if _converter is None:
        _converter = TextToSQLConverter()
    return _converter

def get_rag():
    """Lazy load RAG system."""
    global _rag
    if _rag is None:
        _rag = RAGSystem()
    return _rag


@router.post("/t2sql")
def t2sql_endpoint(req: T2SQLRequest):
    question = req.question

    # Initialize DBHandler
    db = DBHandler(get_connection(mode=MODE))
    schema = db.get_schema()

    # 1. Switcher ML
    ml_model = get_ml_model()
    ml_pred, proba = ml_model.inference(question)

    # 2. Fallback LLM se confidenza bassa
    threshold = 0.7
    fallback = False
    if proba < threshold:
        # no Fallback LLM, but we consider the question complex
        final_pred = "complex"
        fallback = True
    else:
        final_pred = ml_pred.strip().lower()

    # 3. Routing finale
    if final_pred == "simple":
        # se entro 2 tentativi non riesco a generare una query SQL valida, faccio il fallback a RAG
        max_attempts = 2
        attempt = 0
        converter = get_converter()
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

        # Dopo 2 tentativi falliti, fallback RAG
        print("Fallback to RAG after 2 failed attempts.")
        rag = get_rag()
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
        rag = get_rag()
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

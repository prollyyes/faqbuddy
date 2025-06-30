from .BaseModel import *
from .utils import *
from ..utils.db_handler import DBHandler
from ..switcher.MLmodel import MLModel
from ..text_2_SQL import TextToSQLConverter
from ..rag.rag_adapter import RAGSystem
from ..utils.db_utils import get_connection, MODE
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import json
from typing import Generator, Optional, Dict, Any


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

def call_rag_system(question: str, streaming: bool = False, include_metadata: bool = False) -> Any:
    """
    Unified function to call the RAG system.
    This is the single point of entry for all RAG operations.
    """
    rag = get_rag()
    
    if streaming:
        if include_metadata:
            return rag.generate_response_streaming_with_metadata(question)
        else:
            return rag.generate_response_streaming(question)
    else:
        return rag.generate_response(question)

def handle_rag_fallback(question: str, ml_pred: str, proba: float, fallback: bool, final_pred: str, db) -> Dict[str, Any]:
    """
    Unified function to handle RAG fallback scenarios.
    This ensures there's only ONE call to the RAG system for any fallback.
    """
    print("Falling back to RAG system.")
    try:
        rag_result = call_rag_system(question, streaming=False, include_metadata=False)
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
    except Exception as e:
        db.close_connection()
        return {
            "error": str(e),
            "chosen": "RAG",
            "ml_model": ml_pred,
            "ml_confidence": proba,
            "fallback_gemma": fallback,
            "llm_pred": final_pred if fallback else "",
            "result": "Si è verificato un errore durante la generazione della risposta."
        }

def handle_t2sql_logic(question: str) -> Dict[str, Any]:
    """
    Handle the T2SQL logic (SQL generation and execution).
    Returns T2SQL result or raises exception for fallback.
    """
    print(f"🎯 Starting T2SQL logic for question: {question}")
    
    # Initialize DBHandler
    db = DBHandler(get_connection(mode=MODE))
    schema = db.get_schema()
    print("📊 Database schema loaded")

    # 1. Switcher ML
    ml_model = get_ml_model()
    ml_pred, proba = ml_model.inference(question)
    print(f"🤖 ML prediction: {ml_pred}, confidence: {proba}")

    # 2. Fallback LLM se confidenza bassa
    threshold = 0.7
    fallback = False
    if proba < threshold:
        final_pred = "complex"
        fallback = True
        print(f"⚠️ Low confidence ({proba} < {threshold}), marking as complex")
    else:
        final_pred = ml_pred.strip().lower()
        print(f"✅ High confidence ({proba} >= {threshold}), final prediction: {final_pred}")

    # 3. Routing finale
    if final_pred == "simple":
        print("📝 Question classified as simple, attempting SQL generation...")
        # se entro 2 tentativi non riesco a generare una query SQL valida, faccio il fallback a RAG
        max_attempts = 2
        attempt = 0
        converter = get_converter()
        while attempt < max_attempts:
            print(f"🔄 SQL generation attempt {attempt + 1}")
            prompt = converter.create_prompt(question, schema)
            raw_response = converter.query_llm(prompt)
            sql_query = converter.clean_sql_response(raw_response)
            print(f"💾 Generated SQL Query: {sql_query}")
            if not converter.is_sql_safe(sql_query) or sql_query == "INVALID_QUERY":
                print(f"❌ Attempt {attempt+1}: Invalid SQL query, retrying...")
                attempt += 1
                continue
            try:
                rows, columns = db.run_query(sql_query, fetch=True, columns=True)
                result = [dict(zip(columns, row)) for row in rows]
                if result:
                    natural_response = converter.from_sql_to_text(question, result)
                    db.close_connection()
                    print("✅ SQL execution successful, returning T2SQL result")
                    return {
                        "result": result,
                        "query": sql_query,
                        "natural_response": natural_response,
                        "chosen": "T2SQL",
                        "ml_model": ml_pred,
                        "ml_confidence": proba
                    }
                else:
                    print(f"⚠️ Attempt {attempt+1}: Query returned no results, retrying...")
                    attempt += 1
            except Exception as e:
                db.connection_rollback()
                print(f"❌ Attempt {attempt+1}: Error executing SQL query, retrying... {e}")
                attempt += 1

        # Dopo 2 tentativi falliti, fallback RAG
        print("🔄 All SQL attempts failed, falling back to RAG")
        return handle_rag_fallback(question, ml_pred, proba, fallback, final_pred, db)
    else:
        print(f"🔄 Question classified as complex ({final_pred}), falling back to RAG")
        return handle_rag_fallback(question, ml_pred, proba, fallback, final_pred, db)

@router.post("/chat")
def unified_chat_endpoint(
    req: ChatRequest,
    streaming: Optional[bool] = Query(False, description="Enable streaming response"),
    include_metadata: Optional[bool] = Query(False, description="Include metadata in response (only works with streaming)")
):
    """
    Unified chat endpoint that handles all types of requests automatically:
    - Tries T2SQL first for simple questions
    - Falls back to RAG for complex questions or SQL failures
    - Supports streaming and metadata options
    
    The system automatically chooses the best approach based on the question complexity.
    """
    question = req.question
    print(f"\n🔍 Processing question: {question}")
    
    # Validate parameters
    if include_metadata and not streaming:
        return {
            "error": "Metadata can only be included with streaming responses",
            "chosen": "CHAT"
        }
    
    try:
        # Handle streaming responses
        if streaming:
            def generate_stream() -> Generator[str, None, None]:
                """Generate streaming response."""
                try:
                    print("📊 Streaming mode - trying T2SQL first...")
                    # For streaming, try T2SQL first, then fallback to RAG
                    try:
                        # Try T2SQL first (non-streaming)
                        t2sql_result = handle_t2sql_logic(question)
                        print(f"✅ T2SQL succeeded: {t2sql_result['chosen']}")
                        
                        # Convert T2SQL result to streaming format
                        response_text = t2sql_result.get('natural_response') or str(t2sql_result.get('result', ''))
                        
                        # Stream the response token by token
                        words = response_text.split()
                        for word in words:
                            yield f"data: {json.dumps({'token': word + ' ', 'type': 'token'})}\n\n"
                        
                        # Send completion signal
                        yield f"data: {json.dumps({'type': 'complete', 'chosen': 'T2SQL'})}\n\n"
                        return
                        
                    except Exception as t2sql_error:
                        print(f"⚠️ T2SQL failed for streaming, falling back to RAG: {t2sql_error}")
                        # Fallback to RAG streaming
                        rag_result = call_rag_system(question, streaming=True, include_metadata=include_metadata)
                        
                        if include_metadata:
                            # Streaming with metadata
                            for chunk in rag_result:
                                yield f"data: {json.dumps(chunk)}\n\n"
                        else:
                            # Simple streaming
                            for token in rag_result:
                                yield f"data: {json.dumps({'token': token, 'type': 'token'})}\n\n"
                            
                            # Send completion signal for simple streaming
                            yield f"data: {json.dumps({'type': 'complete', 'chosen': 'RAG'})}\n\n"
                        
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream",
                }
            )
        
        # Handle standard response - try T2SQL first, fallback to RAG
        else:
            print("📊 Non-streaming mode - trying T2SQL first...")
            try:
                # Try T2SQL first
                result = handle_t2sql_logic(question)
                print(f"✅ T2SQL succeeded: {result['chosen']}")
                return result
            except Exception as e:
                # If T2SQL fails completely, fallback to RAG
                print(f"⚠️ T2SQL failed, falling back to RAG: {e}")
                rag_result = call_rag_system(question, streaming=False, include_metadata=False)
                return {
                    "result": rag_result["response"],
                    "chosen": "RAG",
                    "fallback_reason": "T2SQL failure",
                    "retrieval_time": rag_result["retrieval_time"],
                    "generation_time": rag_result["generation_time"],
                    "total_time": rag_result["total_time"],
                    "context_used": rag_result["context_used"]
                }
            
    except Exception as e:
        print(f"❌ General error: {e}")
        if streaming:
            # For streaming, we need to return a streaming error response
            def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
            return StreamingResponse(
                error_stream(),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Content-Type": "text/event-stream",
                }
            )
        else:
            return {
                "error": str(e),
                "chosen": "CHAT",
                "result": "Si è verificato un errore durante la generazione della risposta."
            }

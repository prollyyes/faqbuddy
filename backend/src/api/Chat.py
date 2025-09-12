from .BaseModel import *
from .utils import *
from .conversation_memory import conversation_memory
from .response_cache import response_cache
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

def call_rag_system(question: str, streaming: bool = False, include_metadata: bool = False, conversation_context: str = "") -> Any:
    """
    Unified function to call the RAG system.
    This is the single point of entry for all RAG operations.
    """
    # Check cache first (only for non-streaming responses)
    if not streaming:
        cached_response = response_cache.get_response(question, conversation_context)
        if cached_response:
            print("🚀 Cache hit! Returning cached response")
            return cached_response
    
    rag = get_rag()
    
    # Add conversation context to the question if provided
    if conversation_context:
        enhanced_question = f"{conversation_context}{question}"
    else:
        enhanced_question = question
    
    if streaming:
        if include_metadata:
            return rag.generate_response_streaming_with_metadata(enhanced_question)
        else:
            return rag.generate_response_streaming(enhanced_question)
    else:
        result = rag.generate_response(enhanced_question)
        # Cache the result
        response_cache.set_response(question, result, conversation_context)
        return result

def decide_route(question: str) -> Dict[str, Any]:
    """
    Decide whether to use T2SQL or RAG based on the ML switcher only.
    Returns a dict with: route ("T2SQL"|"RAG"), ml_model, ml_confidence, final_pred.
    """
    ml_model = get_ml_model()
    ml_pred, proba = ml_model.inference(question)
    print(f"🤖 ML prediction: {ml_pred}, confidence: {proba}")
    threshold = 0.7
    route = "T2SQL" if (proba >= threshold and ml_pred.strip().lower() == "simple") else "RAG"
    print(f"🧭 Route decision: {route}")
    return {"route": route, "ml_model": ml_pred, "ml_confidence": proba, "final_pred": ml_pred.strip().lower()}

def run_t2sql(question: str) -> Dict[str, Any]:
    """
    Execute the T2SQL generation+execution path. Raises on failure.
    """
    print(f"🎯 Running T2SQL for question: {question}")
    db = DBHandler(get_connection(mode=MODE))
    schema = db.get_schema()
    print("📊 Database schema loaded")
    converter = get_converter()
    max_attempts = 2
    attempt = 0
    last_error = None
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
                    "natural_response": natural_response
                }
            else:
                print(f"⚠️ Attempt {attempt+1}: Query returned no results, retrying...")
                attempt += 1
        except Exception as e:
            db.connection_rollback()
            last_error = e
            print(f"❌ Attempt {attempt+1}: Error executing SQL query, retrying... {e}")
            attempt += 1
    db.close_connection()
    raise RuntimeError(f"T2SQL failed after {max_attempts} attempts: {last_error}")

def handle_rag_fallback(question: str, ml_pred: str, proba: float, fallback: bool, final_pred: str, db) -> Dict[str, Any]:
    """
    Unified function to handle RAG fallback scenarios.
    This ensures there's only one call to the RAG system for any fallback.
    """
    print("Falling back to RAG system.")
    try:
        rag_result = call_rag_system(question, streaming=False, include_metadata=False)
        db.close_connection()
        return {
            "result": rag_result["response"],
            "thinking": rag_result.get("thinking", ""),
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

def handle_t2sql_logic(question: str, streaming_hint: bool = False) -> Dict[str, Any]:
    """
    Handle the T2SQL logic (legacy). Prefer using decide_route + run_t2sql in new flows.
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

        # Dopo 2 tentativi falliti
        print("🔄 All SQL attempts failed")
        if streaming_hint:
            # In streaming mode, do NOT trigger a RAG generation here.
            db.close_connection()
            return {
                "chosen": "RAG",
                "ml_model": ml_pred,
                "ml_confidence": proba
            }
        print("🔄 Falling back to RAG (non-streaming path)")
        return handle_rag_fallback(question, ml_pred, proba, fallback, final_pred, db)
    else:
        print(f"🔄 Question classified as complex ({final_pred})")
        if streaming_hint:
            # In streaming mode, do NOT trigger a RAG generation here.
            db.close_connection()
            return {
                "chosen": "RAG",
                "ml_model": ml_pred,
                "ml_confidence": proba
            }
        print("🔄 Falling back to RAG (non-streaming path)")
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
    - Maintains conversation context and resolves pronouns/ellipsis
    
    The system automatically chooses the best approach based on the question complexity.
    """
    # Handle conversation memory
    conversation_id = req.conversation_id
    if not conversation_id:
        conversation_id = conversation_memory.create_conversation()
        print(f"🆕 Created new conversation: {conversation_id}")
    else:
        print(f"🔄 Continuing conversation: {conversation_id}")
    
    # Resolve pronouns and ellipsis using conversation context
    original_question = req.question
    resolved_question = conversation_memory.resolve_query(conversation_id, original_question)
    
    if resolved_question != original_question:
        print(f"🔄 Query resolved: '{original_question}' -> '{resolved_question}'")
    
    question = resolved_question
    print(f"\n🔍 Processing question: {question}")
    
    # Get conversation context for the prompt
    conversation_context = conversation_memory.get_conversation_context(conversation_id)
    
    # Validate parameters
    if include_metadata and not streaming:
        return {
            "error": "Metadata can only be included with streaming responses",
            "chosen": "CHAT",
            "conversation_id": conversation_id
        }
    
    try:
        # Handle streaming responses
        if streaming:
            def generate_stream() -> Generator[str, None, None]:
                """Generate streaming response following a single-route policy."""
                collected_response = ""
                chosen_method = "RAG"
                try:
                    decision = decide_route(question)
                    if decision["route"] == "T2SQL":
                        try:
                            t2 = run_t2sql(question)
                            import re as _re
                            response_text = t2.get("natural_response") or str(t2.get("result", ""))
                            collected_response = response_text
                            chosen_method = "T2SQL"
                            for token in _re.findall(r'\S+|\s+', response_text):
                                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                            yield f"data: {json.dumps({'type': 'complete', 'chosen': 'T2SQL', 'conversation_id': conversation_id})}\n\n"
                            
                            # Update conversation memory
                            conversation_memory.add_turn(conversation_id, original_question, response_text)
                            return
                        except Exception as e:
                            print(f"⚠️ T2SQL failed, switching to RAG: {e}")
                    # RAG path (with metadata)
                    rag_stream = call_rag_system(question, streaming=True, include_metadata=True, conversation_context=conversation_context)
                    for chunk in rag_stream:
                        if chunk.get('type') == 'token':
                            collected_response += chunk.get('token', '')
                        yield f"data: {json.dumps(chunk)}\n\n"
                    
                    # Update conversation memory after RAG streaming completes
                    if collected_response:
                        conversation_memory.add_turn(conversation_id, original_question, collected_response)
                        
                except Exception as e:
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        
        # Handle standard response - try T2SQL first, fallback to RAG
        else:
            print("📊 Non-streaming mode - single-route policy")
            decision = decide_route(question)
            if decision["route"] == "T2SQL":
                try:
                    t2 = run_t2sql(question)
                    response = {
                        "result": t2["result"],
                        "query": t2["query"],
                        "natural_response": t2["natural_response"],
                        "chosen": "T2SQL",
                        "ml_model": decision["ml_model"],
                        "ml_confidence": decision["ml_confidence"],
                        "conversation_id": conversation_id
                    }
                    
                    # Update conversation memory
                    conversation_memory.add_turn(conversation_id, original_question, t2["natural_response"])
                    return response
                except Exception as e:
                    print(f"⚠️ T2SQL failed, using RAG instead: {e}")
            rag_result = call_rag_system(question, streaming=False, include_metadata=False, conversation_context=conversation_context)
            response = {
                "result": rag_result["response"],
                "thinking": rag_result.get("thinking", ""),
                "chosen": "RAG",
                "retrieval_time": rag_result["retrieval_time"],
                "generation_time": rag_result["generation_time"],
                "total_time": rag_result["total_time"],
                "context_used": rag_result["context_used"],
                "conversation_id": conversation_id
            }
            
            # Update conversation memory
            conversation_memory.add_turn(conversation_id, original_question, rag_result["response"])
            return response
            
    except Exception as e:
        print(f"❌ General error: {e}")
        if streaming:
            # For streaming, we need to return a streaming error response
            def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
            return StreamingResponse(
                error_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        else:
            return {
                "error": str(e),
                "chosen": "CHAT",
                "result": "Si è verificato un errore durante la generazione della risposta."
            }

from .BaseModel import *
from .utils import *
from utils.db_handler import DBHandler
from switcher.MLmodel import MLModel
from text_2_SQL import TextToSQLConverter
from rag.rag_adapter import RAGSystem
from utils.db_utils import get_connection, MODE
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
import json
import os
import uuid
from typing import Generator, Optional, Dict, Any
from .model_manager import model_manager


# Initialize router
router = APIRouter()

# Chat configuration
CHAT_ENABLED = os.getenv("CHAT_ENABLED", "true").lower() == "true"

# Import cancellation utilities
from utils.cancellation import register_request, cancel_request, is_request_cancelled, cleanup_request, has_active_requests

# Import model switching utilities - DEPRECATED
# from utils.model_switcher import ensure_gemma_loaded, ensure_mistral_loaded, get_current_model

# Import direct model loading functions (fallback only)
# from utils.llm_mistral import ensure_mistral_loaded
# from utils.llm_gemma import ensure_gemma_loaded

# Global processing state
_processing_request = False

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

def register_request_with_processing(request_id: str) -> None:
    """Register an active request and set processing flag."""
    global _processing_request
    register_request(request_id)
    _processing_request = True
    print(f"========= Processing flag set to True for request {request_id}")

def cancel_request_with_processing(request_id: str) -> bool:
    """Cancel a specific request and reset processing flag."""
    global _processing_request
    success = cancel_request(request_id)
    if success:
        _processing_request = False
        print(f"========= Processing flag set to False due to cancellation for request {request_id}")
        # Add a small delay to allow GPU memory to be freed naturally
        import time
        time.sleep(1)
    return success

def cleanup_request_with_processing(request_id: str) -> None:
    """Clean up a request and reset processing flag if no active requests."""
    global _processing_request
    cleanup_request(request_id)
    # Check if there are any active requests left
    if not has_active_requests():  # No more active requests
        # Add a small delay to ensure proper cleanup
        import time
        time.sleep(0.1)
        _processing_request = False
        print(f"========= Processing flag set to False - no more active requests")
    else:
        print(f"========= Processing flag remains True - still has active requests")


def call_rag_system(question: str, streaming: bool = False, include_metadata: bool = False, request_id: str = None) -> Any:
    """
    Unified function to call the RAG system.
    This is the single point of entry for all RAG operations.
    """
    # Ensure Mistral model is loaded for RAG operations
    print(f"🔄 Ensuring Mistral model is loaded for RAG (streaming={streaming}, request_id={request_id})...")
    try:
        model_loaded = model_manager.load_mistral()
        print(f"🔄 Mistral model loading result: {model_loaded}")
        if not model_loaded:
            print("❌ Failed to load Mistral model for RAG")
    except Exception as model_error:
        print(f"❌ Exception during Mistral model loading: {model_error}")
        model_loaded = False
    
    if not model_loaded:
        if streaming:
            # Return a streaming error response
            def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'message': 'Model loading failed'})}\n\n"
            return error_stream()
        else:
            return {
                "response": "Si è verificato un errore durante il caricamento del modello per la generazione della risposta.",
                "thinking": "",
                "error": "Model loading failed"
            }
    
    rag = get_rag()
    
    if streaming:
        if include_metadata:
            return rag.generate_response_streaming_with_metadata(question, request_id)
        else:
            return rag.generate_response_streaming(question, request_id)
    else:
        result = rag.generate_response(question)
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
        print(f"⚠️ Low confidence ({proba} < {threshold}), using Gemma fallback classification...")
        try:
            from utils.llm_gemma import classify_question
            final_pred = classify_question(question)
            fallback = True
            print(f"🔄 Gemma fallback prediction: {final_pred}")
        except Exception as e:
            print(f"❌ Gemma fallback failed: {e}, defaulting to complex")
            final_pred = "complex"
            fallback = True
    else:
        final_pred = ml_pred.strip().lower()
        print(f"✅ High confidence ({proba} >= {threshold}), final prediction: {final_pred}")

    # 3. Routing finale
    if final_pred == "simple":
        print("📝 Question classified as simple, attempting SQL generation...")
        
        # Switch to Gemma model for T2SQL operations
        print("🔄 Switching to Gemma model for T2SQL...")
        if not model_manager.load_gemma():
            print("❌ Failed to load Gemma model, falling back to RAG")
            return handle_rag_fallback(question, streaming_hint)
        
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
        
        # Switch to Mistral model for RAG operations
        print("🔄 Switching to Mistral model for RAG...")
        if not model_manager.load_mistral():
            print("❌ Failed to load Mistral model, returning error")
            db.close_connection()
            return {
                "result": "Si è verificato un errore durante il caricamento del modello.",
                "chosen": "ERROR"
            }
        
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
    
    The system automatically chooses the best approach based on the question complexity.
    """
    # Check if chat is enabled
    if not CHAT_ENABLED:
        if streaming:
            # For streaming requests, return a streaming error response
            def disabled_stream():
                yield f"data: {json.dumps({'type': 'error', 'message': 'Chat functionality is disabled in production. Please use the local RAG pipeline for testing.'})}\n\n"
                yield f"data: {json.dumps({'type': 'complete', 'chosen': 'DISABLED'})}\n\n"
            
            return StreamingResponse(
                disabled_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Accept",
                }
            )
        else:
            return {
                "error": "Chat functionality is disabled in production. Please use the local RAG pipeline for testing.",
                "chosen": "DISABLED"
            }
    
    # Check if another request is already being processed
    if _processing_request:
        print(f"========= REJECTING REQUEST: Processing flag is True, rejecting new request")
        print(f"========= Active requests: {has_active_requests()}")
        
        if streaming:
            # For streaming requests, return a streaming error response
            def busy_stream():
                yield f"data: {json.dumps({'type': 'error', 'message': 'Another request is currently being processed. Please wait or stop the current generation.'})}\n\n"
                yield f"data: {json.dumps({'type': 'complete', 'chosen': 'BUSY'})}\n\n"
            
            return StreamingResponse(
                busy_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Accept",
                }
            )
        else:
            return {
                "error": "Another request is currently being processed. Please wait or stop the current generation.",
                "chosen": "BUSY"
            }
    
    # Process the question directly without conversation context
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
            # Generate unique request ID for cancellation tracking
            request_id = str(uuid.uuid4())
            print(f"========= REGISTERING NEW REQUEST: {request_id}")
            register_request_with_processing(request_id)
            
            def generate_stream() -> Generator[str, None, None]:
                """Generate streaming response following a single-route policy."""
                collected_response = ""
                chosen_method = "RAG"
                try:
                    print(f"========= GENERATE_STREAM: Starting for request {request_id}")
                    
                    # Send request ID to frontend for potential cancellation
                    print(f"========= GENERATE_STREAM: Sending request_id")
                    yield f"data: {json.dumps({'type': 'request_id', 'request_id': request_id})}\n\n"
                    
                    print(f"========= GENERATE_STREAM: Making route decision")
                    decision = decide_route(question)
                    print(f"========= GENERATE_STREAM: Route decision: {decision['route']}")
                    if decision["route"] == "T2SQL":
                        try:
                            t2 = run_t2sql(question)
                            import re as _re
                            response_text = t2.get("natural_response") or str(t2.get("result", ""))
                            collected_response = response_text
                            chosen_method = "T2SQL"
                            
                            # Stream with cancellation checks
                            for token in _re.findall(r'\S+|\s+', response_text):
                                # Check for cancellation before each token
                                if is_request_cancelled(request_id):
                                    yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Generation stopped by user'})}\n\n"
                                    return
                                
                                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"
                            
                            # Check for cancellation before completion
                            if is_request_cancelled(request_id):
                                yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Generation stopped by user'})}\n\n"
                                return
                            
                            yield f"data: {json.dumps({'type': 'complete', 'chosen': 'T2SQL'})}\n\n"
                            return
                        except Exception as e:
                            print(f"❌ T2SQL FAILED, switching to RAG: {e}")
                            print(f"❌ T2SQL Exception type: {type(e).__name__}")
                            print(f"❌ T2SQL Exception details: {str(e)}")
                            import traceback
                            print(f"❌ T2SQL Full traceback: {traceback.format_exc()}")
                            # Send error information to frontend before falling back
                            # Safely escape the error message to prevent JSON parsing issues
                            error_msg = str(e).replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
                            safe_error_data = {
                                'type': 'error', 
                                'message': f'T2SQL failed, switching to RAG: {error_msg}',
                                'severity': 'warning',  # Mark as warning since we have fallback
                                'fallback': 'RAG'
                            }
                            try:
                                yield f"data: {json.dumps(safe_error_data)}\n\n"
                            except Exception as json_err:
                                print(f"❌ Failed to serialize T2SQL error: {json_err}")
                                # Send a simple fallback message if JSON serialization fails
                                yield f"data: {json.dumps({'type': 'error', 'message': 'T2SQL failed, switching to RAG'})}\n\n"
                    # RAG path (with metadata)
                    print(f"========= SWITCHING TO RAG with request_id: {request_id}")
                    try:
                        rag_stream = call_rag_system(question, streaming=True, include_metadata=True, request_id=request_id)
                        print(f"========= RAG stream obtained successfully")
                    except Exception as rag_init_error:
                        print(f"❌ Error initializing RAG stream: {rag_init_error}")
                        yield f"data: {json.dumps({'type': 'error', 'message': f'RAG initialization failed: {str(rag_init_error)}'})}\n\n"
                        return
                    
                    chunk_count = 0
                    collected_response = ""
                    stream_completed = False
                    
                    for chunk in rag_stream:
                        chunk_count += 1
                        print(f"========= STREAMING: Chunk {chunk_count}: {chunk}")
                        
                        # Check for cancellation before each chunk
                        if is_request_cancelled(request_id):
                            yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Generation stopped by user'})}\n\n"
                            return
                        
                        if chunk.get('type') == 'token':
                            collected_response += chunk.get('token', '')
                        
                        # Check if RAG pipeline sent completion signal
                        if chunk.get('type') == 'metadata' and chunk.get('finished'):
                            print(f"========= RAG pipeline sent completion metadata - stream finished")
                            stream_completed = True
                        
                        # Ensure all chunk data is JSON serializable
                        try:
                            json_chunk = json.dumps(chunk)
                            yield f"data: {json_chunk}\n\n"
                        except (TypeError, ValueError) as e:
                            print(f"❌ JSON serialization error: {e}")
                            print(f"❌ Problematic chunk: {chunk}")
                            # Send a simplified version
                            safe_chunk = {
                                "type": chunk.get("type", "unknown"),
                                "message": f"Serialization error: {str(e)}"
                            }
                            if chunk.get("type") == "token":
                                safe_chunk["token"] = str(chunk.get("token", ""))
                            yield f"data: {json.dumps(safe_chunk)}\n\n"
                    
                    print(f"========= STREAMING: Total chunks sent: {chunk_count}")
                    
                    # Check for cancellation before completion
                    if is_request_cancelled(request_id):
                        yield f"data: {json.dumps({'type': 'cancelled', 'message': 'Generation stopped by user'})}\n\n"
                        return
                    
                    # Only send completion signal if RAG pipeline didn't already send one
                    if not stream_completed:
                        print(f"========= RAG pipeline did not send completion - sending Chat.py completion signal")
                        yield f"data: {json.dumps({'type': 'complete', 'chosen': 'RAG'})}\n\n"
                    else:
                        print(f"========= RAG pipeline already sent completion - skipping duplicate signal")
                        
                except Exception as e:
                    print(f"❌ Exception in generate_stream: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
            # Create a wrapper that ensures cleanup
            def stream_with_cleanup():
                chunk_count = 0
                try:
                    for chunk in generate_stream():
                        chunk_count += 1
                        yield chunk
                except Exception as e:
                    print(f"❌ Exception in stream_with_cleanup: {e}")
                    yield f"data: {json.dumps({'type': 'error', 'message': f'Stream error: {str(e)}'})}\n\n"
                finally:
                    # ALWAYS clean up the request, regardless of success or failure
                    print(f"========= FORCED CLEANUP REQUEST: {request_id} (chunks: {chunk_count})")
                    cleanup_request_with_processing(request_id)
                    
                    # Extra safety: reset processing flag if still True
                    global _processing_request
                    if _processing_request:
                        print(f"🚨 EMERGENCY: Forcing processing flag to False for request {request_id}")
                        _processing_request = False
            
            return StreamingResponse(
                stream_with_cleanup(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Accept",
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
                        "ml_confidence": decision["ml_confidence"]
                    }
                    return response
                except Exception as e:
                    print(f"⚠️ T2SQL failed, using RAG instead: {e}")
                    print(f"========= SWITCHING TO RAG with request_id: {request_id}")
            
            # RAG fallback (either from T2SQL failure or direct RAG route)
            print(f"========= CHAT: Calling RAG system for question: {question}")
            rag_result = call_rag_system(question, streaming=False, include_metadata=False)
            print(f"========= CHAT: RAG result keys: {list(rag_result.keys()) if isinstance(rag_result, dict) else 'Not a dict'}")
            print(f"========= CHAT: RAG result type: {type(rag_result)}")
            response = {
                "result": rag_result["response"],
                "thinking": rag_result.get("thinking", ""),
                "chosen": "RAG",
                "retrieval_time": rag_result["retrieval_time"],
                "generation_time": rag_result["generation_time"],
                "total_time": rag_result["total_time"],
                "context_used": rag_result["context_used"]
            }
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

@router.get("/chat/test-stream")
def test_stream():
    """
    Simple test endpoint to verify streaming works.
    """
    def test_generator():
        import time
        for i in range(5):
            yield f"data: {json.dumps({'type': 'test', 'number': i, 'message': f'Test message {i}'})}\n\n"
            time.sleep(0.5)
        yield f"data: {json.dumps({'type': 'complete', 'message': 'Test completed'})}\n\n"
    
    return StreamingResponse(
        test_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Accept",
        }
    )

@router.post("/chat/reset")
def emergency_reset():
    """
    Emergency endpoint to reset stuck processing flags and clear resources.
    Use this if the system gets stuck with "Processing flag is True".
    """
    global _processing_request
    try:
        print("🚨 EMERGENCY RESET: Clearing all processing flags and active requests")
        
        # Force clear processing flag
        _processing_request = False
        
        # Clear all active requests
        from utils.cancellation import cleanup_all_requests
        cleanup_all_requests()
        
        print("✅ Emergency reset completed")
        return {
            "success": True,
            "message": "Processing flags and active requests cleared"
        }
    except Exception as e:
        print(f"❌ Error during emergency reset: {e}")
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/chat/stop")
def stop_generation(request: dict):
    """
    Stop an active generation request.
    
    Args:
        request: JSON body containing request_id
        
    Returns:
        Success/failure status
    """
    if not CHAT_ENABLED:
        return {"error": "Chat is disabled", "success": False}
    
    try:
        # Extract request_id from the request body
        request_id = request.get("request_id")
        if not request_id:
            return {"success": False, "error": "No request_id provided"}
        
        success = cancel_request_with_processing(request_id)
        if success:
            print(f"🛑 Request {request_id} cancelled successfully")
            return {"success": True, "message": "Generation stopped successfully"}
        else:
            print(f"⚠️ Request {request_id} not found or already completed")
            return {"success": False, "message": "Request not found or already completed"}
    except Exception as e:
        print(f"❌ Error cancelling request: {e}")
        return {"success": False, "error": str(e)}

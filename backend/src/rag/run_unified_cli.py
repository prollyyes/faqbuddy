#!/usr/bin/env python3
"""
Unified CLI with Switcher Logic
===============================

This CLI includes the switcher logic that decides between T2SQL and RAG
based on question complexity analysis.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from switcher.MLmodel import MLModel
from text_2_SQL.converter import TextToSQLConverter
from utils.db_utils import get_connection, MODE
from utils.db_handler import DBHandler
from rag.advanced_rag_pipeline import AdvancedRAGPipeline

def print_banner():
    print("""
>>> Unified FAQBuddy CLI - Smart Question Routing
================================================
[BRAIN] ML-Based Question Classification
[DATA] Text-to-SQL for Simple Questions  
[SEARCH] Advanced RAG for Complex Questions
[OK] Automatic Fallback & Error Handling
[TARGET] Thesis-Level Research Quality

Optimized for: University FAQ System (La Sapienza)
""")

def print_help():
    """Print help information."""
    print("""
📋 Available Commands:
--------------------
• Ask any question about courses, professors, procedures, etc.
• 'stats' - Show system statistics
• 'test' - Run comprehensive test suite
• 'help' - Show this help message
• 'quit' or 'exit' - Exit the program

Example Queries:
------------------
• "Mostra tutti i corsi del primo semestre" (→ T2SQL)
• "Chi insegna il corso di Programmazione?" (→ T2SQL)
• "Come posso organizzare il mio piano di studi?" (→ RAG)
• "Spiega cos'è un sistema operativo" (→ RAG)

Smart Routing Features:
-------------------------
• ML-based question classification (simple vs complex)
• Automatic T2SQL for database queries
• Advanced RAG for complex reasoning
• Confidence-based fallback system
• Error handling and retry logic
""")

def handle_t2sql_logic(question: str) -> dict:
    """
    Handle the T2SQL logic (SQL generation and execution).
    Returns T2SQL result or raises exception for fallback.
    """
    print(f"-> Starting T2SQL logic for question: {question}")
    
    # Initialize DBHandler
    db = DBHandler(get_connection(mode=MODE))
    schema = db.get_schema()
    print("->Database schema loaded")

    # Initialize converter
    converter = TextToSQLConverter()
    print("->Text-to-SQL converter initialized")
    
    # Try SQL generation
    max_attempts = 2
    attempt = 0
    while attempt < max_attempts:
        print(f"======= SQL generation attempt {attempt + 1}")
        prompt = converter.create_prompt(question, schema)
        raw_response = converter.query_llm(prompt)
        sql_query = converter.clean_sql_response(raw_response)
        print(f"[SAVE] Generated SQL Query: {sql_query}")
        
        if not converter.is_sql_safe(sql_query) or sql_query == "INVALID_QUERY":
            print(f"====== Attempt {attempt+1}: Invalid SQL query, retrying...")
            attempt += 1
            continue
        
        try:
            rows, columns = db.run_query(sql_query, fetch=True, columns=True)
            result = [dict(zip(columns, row)) for row in rows]
            if result:
                natural_response = converter.from_sql_to_text(question, result)
                db.close_connection()
                print("[OK] SQL execution successful!")
                return {
                    "result": result,
                    "query": sql_query,
                    "natural_response": natural_response,
                    "chosen": "T2SQL",
                    "success": True
                }
            else:
                print(f"====== Attempt {attempt+1}: Query returned no results, retrying...")
                attempt += 1
        except Exception as e:
            db.connection_rollback()
            print(f"====== Attempt {attempt+1}: Error executing SQL query: {e}")
            attempt += 1

    # If we get here, T2SQL failed
    print("====== All SQL attempts failed, falling back to RAG")
    db.close_connection()
    raise Exception("T2SQL failed after all attempts")

def handle_rag_logic(question: str) -> dict:
    """
    Handle the RAG logic using Advanced RAG Pipeline.
    """
    print("-> Starting Advanced RAG processing...")
    
    # Initialize Advanced RAG Pipeline
    pipeline = AdvancedRAGPipeline()
    
    # Process the query
    result = pipeline.answer(question)
    
    return {
        "result": result.answer,
        "chosen": "RAG",
        "success": True,
        "confidence": result.confidence_score,
        "verified": getattr(result.verification_result, "is_verified", False),
        "query_analysis": result.query_analysis
    }

def process_question_with_switcher(question: str) -> dict:
    """
    Process a question using the switcher logic.
    """
    print(f"\n ======== Processing question: {question}")
    print("-" * 60)
    
    try:
        # 1. Initialize ML model
        ml_model = MLModel()
        print("[OK] ML Model loaded successfully")
        
        # 2. ML Prediction
        ml_pred, proba = ml_model.inference(question)
        print(f"===> ML prediction: '{ml_pred}' (confidence: {proba:.3f})")
        
        # 3. Threshold check
        threshold = 0.7
        if proba < threshold:
            final_pred = "complex"
            fallback = True
            print(f"[WARN] Low confidence ({proba:.3f} < {threshold}), marking as complex")
        else:
            final_pred = ml_pred.strip().lower()
            fallback = False
            print(f"[OK] High confidence ({proba:.3f} >= {threshold}), final tprediction: '{final_pred}'")
        
        # 4. Routing decision
        if final_pred == "simple":
            print("======== DECISION: Using T2SQL for simple question")
            try:
                result = handle_t2sql_logic(question)
                result.update({
                    "ml_model": ml_pred,
                    "ml_confidence": proba,
                    "fallback_used": fallback
                })
                return result
            except Exception as e:
                print(f"======= T2SQL failed: {e}")
                print("======= Falling back to RAG...")
                
                # Preload Mistral model immediately upon T2SQL failure for better performance
                print(f"[LOAD] Preloading Mistral model for RAG fallback...")
                try:
                    from utils.llm_mistral import ensure_mistral_loaded
                    model_loaded = ensure_mistral_loaded()
                    if model_loaded:
                        print(f"[OK] Mistral model preloaded successfully for RAG")
                    else:
                        print(f"[WARN] Mistral model preload failed, will load on-demand")
                except Exception as preload_error:
                    print(f"[WARN] Mistral preload error: {preload_error}, will load on-demand")
                
                result = handle_rag_logic(question)
                result.update({
                    "ml_model": ml_pred,
                    "ml_confidence": proba,
                    "fallback_used": fallback,
                    "fallback_reason": "T2SQL failure"
                })
                return result
        else:
            print(f"======== DECISION: Using RAG for complex question ({final_pred})")
            result = handle_rag_logic(question)
            result.update({
                "ml_model": ml_pred,
                "ml_confidence": proba,
                "fallback_used": fallback
            })
            return result
            
    except Exception as e:
        print(f"======= Error in switcher logic: {e}")
        print("======= Emergency fallback to RAG...")
        
        # Preload Mistral model for emergency fallback
        print(f"[LOAD] Preloading Mistral model for emergency RAG fallback...")
        try:
            from utils.llm_mistral import ensure_mistral_loaded
            model_loaded = ensure_mistral_loaded()
            if model_loaded:
                print(f"[OK] Mistral model preloaded successfully for emergency RAG")
            else:
                print(f"[WARN] Mistral model preload failed, will load on-demand")
        except Exception as preload_error:
            print(f"[WARN] Mistral preload error: {preload_error}, will load on-demand")
        
        result = handle_rag_logic(question)
        result.update({
            "ml_model": "error",
            "ml_confidence": 0.0,
            "fallback_used": True,
            "fallback_reason": "Switcher error"
        })
        return result

def main():
    """Main CLI function."""
    print_banner()
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    if not os.getenv("PINECONE_API_KEY"):
        print("[ERROR] PINECONE_API_KEY environment variable is required")
        sys.exit(1)
    
    print_help()
    
    # Main interaction loop
    while True:
        try:
            user_input = input("\n🤔 Your question: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                break
            
            elif user_input.lower() == 'help':
                print_help()
                continue
            
            # Process the query with switcher logic
            start_time = time.time()
            result = process_question_with_switcher(user_input)
            processing_time = time.time() - start_time
            
            # Display results
            print(f"\n ======= Answer:")
            if result['chosen'] == 'T2SQL' and 'natural_response' in result:
                print(f"{result['natural_response']}")
            else:
                print(f"{result['result']}")
            
            print(f"\n ======= Analysis:")
            print(f"   Method: {result['chosen']}")
            print(f"   ML Prediction: {result.get('ml_model', 'N/A')}")
            print(f"   ML Confidence: {result.get('ml_confidence', 0):.3f}")
            print(f"   Processing Time: {processing_time:.2f}s")
            
            if result['chosen'] == 'RAG':
                print(f"   RAG Confidence: {result.get('confidence', 0):.3f}")
                print(f"   Verified: {'[OK] YES' if result.get('verified', False) else '[ERROR] NO'}")
            
            if result.get('fallback_reason'):
                print(f"   Fallback Reason: {result['fallback_reason']}")
            
            if result['chosen'] == 'T2SQL' and 'query' in result:
                print(f"\n[SAVE] SQL Query Used:")
                print(f"{result['query']}")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"[ERROR] Error: {e}")

if __name__ == "__main__":
    main()

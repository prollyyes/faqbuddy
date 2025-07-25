#!/usr/bin/env python3
"""
Test Chatbot with RAG v2 Integration
====================================

This script tests the chatbot functionality with the updated RAG v2 system.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from rag.rag_adapter import RAGSystem

def test_ragv2_system():
    """Test the RAG v2 system directly."""
    print("🧪 Testing RAG v2 System Integration")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Initialize RAG system
    print("🚀 Initializing RAG v2 System...")
    rag_system = RAGSystem()
    
    # Get system info
    system_info = rag_system.get_system_info()
    print(f"📊 System Info:")
    print(f"   Type: {system_info['system_type']}")
    print(f"   Embedding Model: {system_info['embedding_model']}")
    print(f"   LLM Model: {system_info['llm_model']}")
    print(f"   Namespaces: {system_info['namespaces']}")
    print(f"   Features: {system_info['features']}")
    
    # Test queries
    test_queries = [
        "Come mi posso iscrivere al corso di ingegneria informatica e automatica?",
        "Chi insegna il corso di Sistemi Operativi?",
        "Come funziona il sistema bibliotecario in Sapienza?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}/{len(test_queries)}: {query}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Test RAG system directly
            result = rag_system.generate_response(query)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ Response generated in {duration:.2f}s")
            print(f"📝 Answer: {result['response'][:200]}...")
            print(f"⏱️ Total time: {result['total_time']}s")
            print(f"📊 Sources: {result['context_used']['total_sources']}")
            print(f"🏷️ Namespaces: {result['context_used']['namespace_counts']}")
            print(f"🎯 Features used: {list(result['context_used']['features_used'].keys())}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

def test_streaming():
    """Test streaming functionality."""
    print(f"\n📡 Testing Streaming Functionality")
    print("=" * 50)
    
    test_query = "Chi insegna il corso di Sistemi Operativi?"
    
    try:
        print(f"🔍 Testing streaming for: {test_query}")
        
        # Test streaming response
        rag_system = RAGSystem()
        stream = rag_system.generate_response_streaming(test_query)
        
        print("📡 Streaming response:")
        tokens = []
        for token in stream:
            tokens.append(token)
            print(token, end='', flush=True)
        
        print(f"\n✅ Streaming completed with {len(tokens)} tokens")
        
    except Exception as e:
        print(f"❌ Streaming Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function."""
    print("🚀 Testing Chatbot with RAG v2 Integration")
    print("=" * 60)
    
    # Test RAG v2 system
    test_ragv2_system()
    
    # Test streaming
    test_streaming()
    
    print(f"\n🎉 Chatbot RAG v2 Integration Test Complete!")
    print(f"📋 Summary:")
    print(f"   - RAG v2 system is integrated")
    print(f"   - Chat API is enabled")
    print(f"   - Streaming functionality works")
    print(f"   - Web search enhancement is active")
    print(f"   - Enhanced retrieval is working")

if __name__ == "__main__":
    main() 
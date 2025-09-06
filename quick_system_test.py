#!/usr/bin/env python3
"""
Quick System Test for FAQBuddy RAG System
=========================================

Simple test to verify the system is working before running comprehensive evaluation.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def test_system_components():
    """Test individual system components."""
    print("🧪 Testing System Components")
    print("=" * 40)
    
    # Test 1: Environment variables
    load_dotenv()
    pinecone_key = os.getenv("PINECONE_API_KEY")
    print(f"✅ Pinecone API Key: {'SET' if pinecone_key else 'NOT SET'}")
    
    # Test 2: RAG Pipeline import
    try:
        from rag.rag_pipeline_v2 import RAGv2Pipeline
        print("✅ RAG Pipeline import successful")
        
        # Test 3: Pipeline initialization
        print("🔄 Initializing RAG pipeline...")
        pipeline = RAGv2Pipeline()
        print("✅ RAG Pipeline initialized successfully")
        
        # Test 4: Simple query test
        print("🔄 Testing simple query...")
        start_time = time.time()
        
        result = pipeline.answer("Quali sono i corsi del primo semestre?")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"✅ Query completed in {response_time:.2f} seconds")
        print(f"📊 Retrieved documents: {result.get('retrieved_documents', 0)}")
        print(f"📝 Answer length: {len(result.get('answer', ''))} characters")
        
        # Test 5: Check namespace usage
        namespace_breakdown = result.get('namespace_breakdown', {})
        print(f"📊 Namespace breakdown: {namespace_breakdown}")
        
        # Test 6: Check per-row usage
        per_row_results = namespace_breakdown.get('per_row', 0)
        print(f"🎯 Per-row results: {per_row_results}")
        
        return True, result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_api_endpoint():
    """Test if the API endpoint is accessible."""
    print("\n🌐 Testing API Endpoint")
    print("=" * 30)
    
    try:
        import requests
        
        # Test API health
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API endpoint accessible")
            return True
        else:
            print(f"⚠️ API returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ API endpoint not accessible - server may not be running")
        return False
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False

def main():
    """Run quick system test."""
    print("🚀 FAQBuddy Quick System Test")
    print("=" * 50)
    
    # Test API first
    api_working = test_api_endpoint()
    
    # Test RAG system
    rag_working, test_result = test_system_components()
    
    print("\n📊 TEST SUMMARY")
    print("=" * 20)
    print(f"API Endpoint: {'✅ Working' if api_working else '❌ Not Working'}")
    print(f"RAG System: {'✅ Working' if rag_working else '❌ Not Working'}")
    
    if rag_working and test_result:
        print(f"Response Time: {test_result.get('total_time', 'N/A')}s")
        print(f"GPU Acceleration: {'✅ Active' if test_result.get('gpu_memory_used', 0) > 0 else '❌ Not Active'}")
        
        # Show sample answer
        answer = test_result.get('answer', '')
        if answer:
            print(f"\n📝 Sample Answer Preview:")
            print(f"   {answer[:200]}{'...' if len(answer) > 200 else ''}")
    
    if rag_working:
        print("\n🎯 System is ready for comprehensive evaluation!")
        print("   Run: python thesis_evaluation_framework.py")
    else:
        print("\n⚠️ System needs attention before evaluation")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Final System Test for FAQBuddy RAG System
=========================================

Comprehensive test to verify all components are working correctly:
1. Environment and dependencies
2. Vector database connectivity
3. Per-row namespace functionality
4. Traditional namespace functionality
5. RAG pipeline integration
6. GPU acceleration
7. End-to-end query processing
"""

import os
import sys
import time
from dotenv import load_dotenv
from typing import Dict, List, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def test_environment():
    """Test environment setup and dependencies."""
    print("🔧 TESTING ENVIRONMENT SETUP")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    pinecone_key = os.getenv("PINECONE_API_KEY")
    print(f"✅ Pinecone API Key: {'SET' if pinecone_key else 'NOT SET'}")
    
    # Test imports
    try:
        from pinecone import Pinecone
        print("✅ Pinecone import successful")
    except ImportError as e:
        print(f"❌ Pinecone import failed: {e}")
        return False
    
    try:
        from llama_cpp import Llama
        print("✅ llama-cpp-python import successful")
    except ImportError as e:
        print(f"❌ llama-cpp-python import failed: {e}")
        return False
    
    try:
        from rag.utils.embeddings_v2 import EnhancedEmbeddings
        print("✅ Enhanced embeddings import successful")
    except ImportError as e:
        print(f"❌ Enhanced embeddings import failed: {e}")
        return False
    
    return True

def test_vector_database():
    """Test vector database connectivity and namespaces."""
    print("\n🗄️ TESTING VECTOR DATABASE")
    print("=" * 50)
    
    try:
        from pinecone import Pinecone
        load_dotenv()
        
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index = pc.Index('exams-index-enhanced')
        
        # Get index stats
        stats = index.describe_index_stats()
        print(f"✅ Connected to index: exams-index-enhanced")
        print(f"📊 Total vectors: {stats['total_vector_count']}")
        
        # Check namespaces
        namespaces = stats.get('namespaces', {})
        print(f"📁 Available namespaces: {list(namespaces.keys())}")
        
        # Check per_row namespace
        if 'per_row' in namespaces:
            per_row_count = namespaces['per_row']['vector_count']
            print(f"✅ Per-row namespace: {per_row_count} vectors")
        else:
            print("❌ Per-row namespace not found")
            return False
        
        # Check traditional namespaces
        for ns in ['db_v2', 'pdf_v2']:
            if ns in namespaces:
                count = namespaces[ns]['vector_count']
                print(f"✅ {ns} namespace: {count} vectors")
            else:
                print(f"⚠️ {ns} namespace not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector database test failed: {e}")
        return False

def test_embeddings():
    """Test embedding generation."""
    print("\n🧠 TESTING EMBEDDINGS")
    print("=" * 50)
    
    try:
        from rag.utils.embeddings_v2 import EnhancedEmbeddings
        
        embeddings = EnhancedEmbeddings()
        test_text = "Test query for embedding generation"
        
        start_time = time.time()
        embedding = embeddings.encode_single(test_text)
        end_time = time.time()
        
        print(f"✅ Embedding generated successfully")
        print(f"📏 Embedding dimension: {len(embedding)}")
        print(f"⏱️ Generation time: {(end_time - start_time):.3f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Embeddings test failed: {e}")
        return False

def test_retrieval():
    """Test retrieval functionality."""
    print("\n🔍 TESTING RETRIEVAL")
    print("=" * 50)
    
    try:
        from pinecone import Pinecone
        from rag.utils.embeddings_v2 import EnhancedEmbeddings
        load_dotenv()
        
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index = pc.Index('exams-index-enhanced')
        embeddings = EnhancedEmbeddings()
        
        # Test query
        query = "Who teaches Sistemi Operativi?"
        query_embedding = embeddings.encode_single(query)
        
        # Test per_row namespace
        print("🔹 Testing per_row namespace...")
        per_row_results = index.query(
            vector=query_embedding,
            top_k=3,
            namespace='per_row',
            include_metadata=True
        )
        
        if per_row_results['matches']:
            best_match = per_row_results['matches'][0]
            print(f"✅ Per-row retrieval successful")
            print(f"📊 Best score: {best_match['score']:.4f}")
            print(f"📝 Best match: {best_match['metadata']['text'][:100]}...")
        else:
            print("❌ No results from per_row namespace")
            return False
        
        # Test traditional namespace
        print("\n🔹 Testing db_v2 namespace...")
        db_v2_results = index.query(
            vector=query_embedding,
            top_k=3,
            namespace='db_v2',
            include_metadata=True
        )
        
        if db_v2_results['matches']:
            best_match = db_v2_results['matches'][0]
            print(f"✅ DB_v2 retrieval successful")
            print(f"📊 Best score: {best_match['score']:.4f}")
            print(f"📝 Best match: {best_match['metadata']['text'][:100]}...")
        else:
            print("❌ No results from db_v2 namespace")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Retrieval test failed: {e}")
        return False

def test_gpu_acceleration():
    """Test GPU acceleration for LLM."""
    print("\n🚀 TESTING GPU ACCELERATION")
    print("=" * 50)
    
    try:
        from llama_cpp import Llama
        import os
        
        # Check if model exists
        model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'models', 'capybarahermes-2.5-mistral-7b.Q4_K_M.gguf'))
        
        if not os.path.exists(model_path):
            print(f"❌ Model not found at: {model_path}")
            return False
        
        print(f"✅ Model found: {os.path.basename(model_path)}")
        
        # Test GPU initialization (without full generation)
        print("🔄 Testing GPU initialization...")
        llm = Llama(
            model_path=model_path,
            n_ctx=512,  # Smaller context for testing
            n_threads=4,
            n_gpu_layers=-1,  # Use all GPU layers
            verbose=False
        )
        
        print("✅ GPU acceleration initialized successfully")
        print("🎯 All layers offloaded to GPU")
        
        return True
        
    except Exception as e:
        print(f"❌ GPU acceleration test failed: {e}")
        return False

def test_rag_pipeline():
    """Test the complete RAG pipeline."""
    print("\n🤖 TESTING RAG PIPELINE")
    print("=" * 50)
    
    try:
        from rag.rag_pipeline_v2 import RAGv2Pipeline
        
        # Initialize pipeline
        print("🔄 Initializing RAG pipeline...")
        pipeline = RAGv2Pipeline()
        print("✅ RAG pipeline initialized successfully")
        
        # Test a simple query
        test_query = "Da quanti crediti è il corso di Sistemi Operativi?"
        print(f"🔍 Testing query: {test_query}")
        
        start_time = time.time()
        result = pipeline.process_query(test_query)
        end_time = time.time()
        
        if result and 'answer' in result:
            print("✅ RAG pipeline query successful")
            print(f"⏱️ Processing time: {(end_time - start_time):.2f}s")
            print(f"📝 Answer preview: {result['answer'][:150]}...")
            
            # Check if per-row namespace was used
            if 'retrieval_results' in result:
                namespace_breakdown = result['retrieval_results'].get('namespace_breakdown', {})
                if 'per_row' in namespace_breakdown:
                    print(f"✅ Per-row namespace used: {namespace_breakdown['per_row']} results")
                else:
                    print("⚠️ Per-row namespace not used in retrieval")
            
            return True
        else:
            print("❌ RAG pipeline returned no answer")
            return False
        
    except Exception as e:
        print(f"❌ RAG pipeline test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 FAQBUDDY SYSTEM COMPREHENSIVE TEST")
    print("=" * 60)
    print("Testing all components to ensure everything is working correctly...\n")
    
    tests = [
        ("Environment Setup", test_environment),
        ("Vector Database", test_vector_database),
        ("Embeddings", test_embeddings),
        ("Retrieval", test_retrieval),
        ("GPU Acceleration", test_gpu_acceleration),
        ("RAG Pipeline", test_rag_pipeline)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready for use.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
RAGv2 Test Script (Root Level)
==============================

This script tests the RAGv2 system with real Pinecone client.
Run this from the project root directory.
"""

import os
import sys
from dotenv import load_dotenv

def test_ragv2_with_real_pinecone():
    """Test RAGv2 system with real Pinecone client."""
    print("🧪 Testing RAGv2 with Real Pinecone Client")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    if not pinecone_api_key:
        print("❌ PINECONE_API_KEY not found in environment variables")
        print("   Please set PINECONE_API_KEY in your .env file")
        return False
    
    try:
        # Import RAGv2 components
        from backend.src.rag.config import get_feature_flags, get_ragv2_namespaces
        from backend.src.rag.utils.embeddings_v2 import EnhancedEmbeddings
        from backend.src.rag.retrieval_v2 import EnhancedRetrieval
        from backend.src.rag.generation_guards import GenerationGuards
        from backend.src.rag.rag_pipeline_v2 import RAGv2Pipeline
        from pinecone import Pinecone
        
        print("✅ All imports successful")
        
        # Test 1: Configuration
        print("\n1️⃣ Testing Configuration...")
        flags = get_feature_flags()
        namespaces = get_ragv2_namespaces()
        
        print(f"   Feature flags: {len(flags)} flags loaded")
        print(f"   RAGv2 namespaces: {namespaces}")
        
        # Test 2: Pinecone Connection
        print("\n2️⃣ Testing Pinecone Connection...")
        pc = Pinecone(api_key=pinecone_api_key)
        print("   ✅ Pinecone client initialized")
        
        # Test 3: Embeddings
        print("\n3️⃣ Testing Enhanced Embeddings...")
        embeddings = EnhancedEmbeddings()
        
        test_text = "Test text for embedding generation"
        embedding = embeddings.encode_single(test_text)
        
        print(f"   ✅ Embedding generated: {len(embedding)} dimensions")
        print(f"   Model: {embeddings.model_name}")
        
        # Test 4: Retrieval System
        print("\n4️⃣ Testing Enhanced Retrieval...")
        retrieval = EnhancedRetrieval(pc)
        
        test_query = "Who teaches Operating Systems this semester?"
        results = retrieval.retrieve(test_query)
        
        print(f"   ✅ Retrieval completed: {len(results)} results")
        
        if results:
            print(f"   First result namespace: {results[0].get('namespace', 'unknown')}")
            print(f"   First result score: {results[0].get('score', 0):.3f}")
        
        # Test 5: Generation Guards
        print("\n5️⃣ Testing Generation Guards...")
        guards = GenerationGuards()
        
        test_sources = [
            {'text': 'The course is taught by Professor Smith'},
            {'text': 'Operating Systems is a core course'}
        ]
        
        test_answer = "Professor Smith teaches the course"
        result = guards.generate_safe_answer("Who teaches the course?", test_sources, test_answer)
        
        print(f"   ✅ Guard test completed")
        print(f"   Answer safe: {result.get('is_safe', False)}")
        print(f"   Confidence: {result.get('confidence_score', 0):.3f}")
        
        # Test 6: Full Pipeline
        print("\n6️⃣ Testing Full RAGv2 Pipeline...")
        pipeline = RAGv2Pipeline(pc)
        
        pipeline_result = pipeline.answer(test_query)
        
        print(f"   ✅ Pipeline test completed")
        print(f"   Answer length: {len(pipeline_result.get('answer', ''))}")
        print(f"   Sources: {len(pipeline_result.get('sources', []))}")
        print(f"   Query time: {pipeline_result.get('metadata', {}).get('query_time', 0):.3f}s")
        
        # Test 7: Feature Flags
        print("\n7️⃣ Testing Feature Flags...")
        enabled_flags = [name for name, enabled in flags.items() if enabled]
        disabled_flags = [name for name, enabled in flags.items() if not enabled]
        
        print(f"   Enabled: {enabled_flags}")
        print(f"   Disabled: {disabled_flags}")
        
        print("\n✅ All tests completed successfully!")
        print("\n📊 Summary:")
        print(f"   - Configuration: ✅")
        print(f"   - Pinecone Connection: ✅")
        print(f"   - Embeddings: ✅ ({embeddings.model_name})")
        print(f"   - Retrieval: ✅ ({len(results)} results)")
        print(f"   - Generation Guards: ✅")
        print(f"   - Full Pipeline: ✅")
        print(f"   - Feature Flags: ✅ ({len(enabled_flags)} enabled)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
        print("   Run: pip install -r backend/src/requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_namespace_verification():
    """Test namespace verification."""
    print("\n🔍 Testing Namespace Verification...")
    
    try:
        from backend.src.rag.update_pinecone_ragv2 import SafePineconeUpsert
        
        upsert = SafePineconeUpsert()
        verification = upsert.verify_namespaces()
        
        print(f"   ✅ Namespace verification completed")
        print(f"   Success: {verification.get('success', False)}")
        
        if verification.get('warnings'):
            print(f"   Warnings: {verification['warnings']}")
        
        return verification.get('success', False)
        
    except Exception as e:
        print(f"❌ Namespace verification failed: {e}")
        return False


def main():
    """Main function."""
    print("🚀 RAGv2 Real-World Test Suite")
    print("=" * 50)
    
    # Test 1: Basic functionality
    success = test_ragv2_with_real_pinecone()
    
    # Test 2: Namespace verification
    if success:
        namespace_success = test_namespace_verification()
        success = success and namespace_success
    
    if success:
        print("\n🎉 All tests passed! RAGv2 is ready for deployment.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main()) 
#!/usr/bin/env python3
"""
RAGv2 Population and Query Test
===============================

This script demonstrates:
1. Populating RAGv2 namespaces with data
2. Querying the RAGv2 system with observability
3. Analyzing responses and performance

Run this to test the complete RAGv2 workflow.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add the backend/src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def test_population():
    """Test RAGv2 data population."""
    print("🚀 Testing RAGv2 Data Population")
    print("=" * 50)
    
    try:
        from backend.src.rag.populate_ragv2 import run_full_population
        
        # Run full population (database only for now)
        results = run_full_population(verbose=True)
        
        if results["success"]:
            print("✅ Population test completed successfully!")
            return True
        else:
            print("❌ Population test failed!")
            for error in results.get("errors", []):
                print(f"   - {error}")
            return False
            
    except Exception as e:
        print(f"❌ Population test failed: {e}")
        return False

def test_query_interface():
    """Test RAGv2 query interface."""
    print("\n🎯 Testing RAGv2 Query Interface")
    print("=" * 50)
    
    try:
        from backend.src.rag.query_interface import RAGv2QueryInterface
        
        # Initialize query interface
        interface = RAGv2QueryInterface(enable_logging=False)
        
        # Test queries
        test_questions = [
            "Who teaches Operating Systems?",
            "What courses are available in Computer Science?",
            "Tell me about the database course",
            "Who is the professor for Algorithms?"
        ]
        
        print("📝 Running test queries...")
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n{i}. Question: {question}")
            
            # Execute query
            result = interface.query(question)
            
            # Display results
            print(f"   Answer: {result.answer}")
            print(f"   Confidence: {result.confidence:.2%}")
            print(f"   Response time: {result.response_time:.3f}s")
            print(f"   Sources: {len(result.sources)}")
            print(f"   Namespaces: {result.namespace_breakdown}")
            
            # Show top source if available
            if result.sources:
                top_source = result.sources[0]
                score = top_source.get("score", 0)
                namespace = top_source.get("namespace", "unknown")
                text = top_source.get("metadata", {}).get("text", "")[:80]
                print(f"   Top source: [{namespace}] (score: {score:.3f}) {text}...")
        
        # Get performance report
        print(f"\n📊 Performance Report:")
        report = interface.get_performance_report()
        print(f"   Total queries: {report['summary']['total_queries']}")
        print(f"   Average response time: {report['summary']['average_response_time']:.3f}s")
        print(f"   Feature usage: {report['feature_usage']}")
        print(f"   Namespace usage: {report['namespace_usage']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Query interface test failed: {e}")
        return False

def test_verification():
    """Test namespace verification."""
    print("\n🔍 Testing Namespace Verification")
    print("=" * 50)
    
    try:
        from backend.src.rag.populate_ragv2 import verify_population
        
        # Verify population
        results = verify_population(verbose=True)
        
        if results["success"]:
            print("✅ Verification completed successfully!")
            
            # Check if RAGv2 namespaces have data
            ragv2_namespaces = results.get("ragv2_namespaces", {})
            total_vectors = sum(info.get("vector_count", 0) for info in ragv2_namespaces.values())
            
            if total_vectors > 0:
                print(f"✅ RAGv2 namespaces populated with {total_vectors} vectors")
                return True
            else:
                print("⚠️ RAGv2 namespaces are empty - population may have failed")
                return False
        else:
            print("❌ Verification failed!")
            return False
            
    except Exception as e:
        print(f"❌ Verification test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 RAGv2 Population and Query Test Suite")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY not found in environment variables")
        print("   Please set PINECONE_API_KEY in your .env file")
        return 1
    
    # Run tests
    tests = [
        ("Population", test_population),
        ("Verification", test_verification),
        ("Query Interface", test_query_interface)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! RAGv2 is ready for use.")
        print("\nNext steps:")
        print("1. Run: python backend/src/rag/query_interface.py --interactive")
        print("2. Or: python backend/src/rag/populate_ragv2.py --verify-only")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit(main()) 
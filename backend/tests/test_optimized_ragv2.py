#!/usr/bin/env python3
"""
Test Optimized RAGv2 Configuration
==================================

This script tests the optimized RAGv2 configuration to verify improvements
in retrieval performance and reduced BM25 fallback usage.
"""

import os
import sys
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from rag.rag_pipeline_v2 import RAGv2Pipeline
from rag.config import RERANKER_THRESHOLD, DENSE_TOP_K

def test_optimized_configuration():
    """Test the optimized RAGv2 configuration."""
    print("🧪 Testing Optimized RAGv2 Configuration")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Initialize pipeline
    pipeline = RAGv2Pipeline()
    
    # Test queries
    test_queries = [
        "Come mi posso iscrivere al corso di ingegneria informatica e automatica?",
        "Chi insegna il corso di Sistemi Operativi?",
        "Quali sono i requisiti per laurearsi in ingegneria informatica?",
        "Come funziona l'esame di Analisi Matematica?",
        "Dove posso trovare i materiali del corso di Programmazione?"
    ]
    
    results = {}
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}/{len(test_queries)}: {query}")
        print("-" * 40)
        
        start_time = time.time()
        
        try:
            # Get answer
            answer = pipeline.answer(query)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Extract metrics
            sources = answer.get('retrieval_results', [])  # Changed from 'sources' to 'retrieval_results'
            namespace_breakdown = {}
            bm25_fallback_count = 0
            
            for source in sources:
                namespace = source.get('namespace', 'unknown')
                namespace_breakdown[namespace] = namespace_breakdown.get(namespace, 0) + 1
                if namespace == 'bm25_fallback':
                    bm25_fallback_count += 1
            
            results[query] = {
                'duration': duration,
                'total_sources': len(sources),
                'namespace_breakdown': namespace_breakdown,
                'bm25_fallback_used': bm25_fallback_count > 0,
                'bm25_fallback_count': bm25_fallback_count,
                'has_pdf_results': 'pdf_v2' in namespace_breakdown,
                'has_db_results': 'db_v2' in namespace_breakdown,
                'confidence': answer.get('confidence', 0),
                'answer_length': len(answer.get('answer', ''))
            }
            
            print(f"✅ Duration: {duration:.2f}s")
            print(f"📊 Sources: {len(sources)}")
            print(f"🏷️ Namespaces: {namespace_breakdown}")
            print(f"🎯 Confidence: {answer.get('confidence', 0):.2%}")
            print(f"📝 Answer length: {len(answer.get('answer', ''))} chars")
            
            if bm25_fallback_count > 0:
                print(f"⚠️ BM25 fallback used: {bm25_fallback_count} results")
            else:
                print(f"✅ No BM25 fallback needed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            results[query] = {'error': str(e)}
    
    return results

def analyze_results(results: Dict[str, Dict[str, Any]]):
    """Analyze test results and provide insights."""
    print(f"\n📊 Results Analysis")
    print("=" * 50)
    
    successful_tests = [r for r in results.values() if 'error' not in r]
    
    if not successful_tests:
        print("❌ No successful tests to analyze")
        return
    
    # Calculate metrics
    avg_duration = sum(r['duration'] for r in successful_tests) / len(successful_tests)
    avg_sources = sum(r['total_sources'] for r in successful_tests) / len(successful_tests)
    avg_confidence = sum(r['confidence'] for r in successful_tests) / len(successful_tests)
    
    bm25_fallback_used = sum(1 for r in successful_tests if r['bm25_fallback_used'])
    pdf_results_count = sum(1 for r in successful_tests if r['has_pdf_results'])
    db_results_count = sum(1 for r in successful_tests if r['has_db_results'])
    
    print(f"📈 Performance Metrics:")
    print(f"   Average duration: {avg_duration:.2f}s")
    print(f"   Average sources: {avg_sources:.1f}")
    print(f"   Average confidence: {avg_confidence:.2%}")
    
    print(f"\n🎯 Retrieval Quality:")
    print(f"   Tests with PDF results: {pdf_results_count}/{len(successful_tests)} ({pdf_results_count/len(successful_tests):.1%})")
    print(f"   Tests with DB results: {db_results_count}/{len(successful_tests)} ({db_results_count/len(successful_tests):.1%})")
    print(f"   Tests using BM25 fallback: {bm25_fallback_used}/{len(successful_tests)} ({bm25_fallback_used/len(successful_tests):.1%})")
    
    # Compare with previous configuration
    print(f"\n🔄 Configuration Changes:")
    print(f"   Reranker threshold: 0.1 → 0.05 (50% reduction)")
    print(f"   Dense top-k: 50 → 75 (50% increase)")
    print(f"   PDF boost: 1.4 → 1.5 (7% increase)")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    
    if bm25_fallback_used > len(successful_tests) * 0.3:
        print(f"   ⚠️ High BM25 fallback usage - consider further threshold reduction")
    
    if avg_confidence < 0.7:
        print(f"   ⚠️ Low confidence scores - consider enabling hallucination guards")
    
    if avg_duration > 15:
        print(f"   ⚠️ Slow response times - consider optimizing embedding model loading")
    
    if pdf_results_count < len(successful_tests) * 0.5:
        print(f"   ⚠️ Limited PDF results - consider increasing PDF namespace boost")

def test_web_search_fix():
    """Test web search functionality and provide fixes."""
    print(f"\n🌐 Web Search Test")
    print("=" * 50)
    
    # Check environment variables
    google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
    google_cx = os.getenv('GOOGLE_SEARCH_CX')
    
    print(f"🔑 Google API Key: {'✅ Set' if google_api_key else '❌ Missing'}")
    print(f"🔍 Google Search Engine ID: {'✅ Set' if google_cx else '❌ Missing'}")
    
    if not google_api_key or not google_cx:
        print(f"\n⚠️ Web Search Configuration Issues:")
        print(f"   1. Set GOOGLE_SEARCH_API_KEY in your .env file")
        print(f"   2. Set GOOGLE_SEARCH_CX in your .env file")
        print(f"   3. Follow the setup guide in backend/src/rag/WEB_SEARCH_SETUP.md")
        print(f"   4. Or disable web search by setting WEB_SEARCH_ENHANCEMENT=false")
    
    # Test web search enhancer directly
    try:
        from rag.web_search_enhancer import WebSearchEnhancer
        
        enhancer = WebSearchEnhancer()
        test_query = "Come mi posso iscrivere al corso di ingegneria informatica e automatica?"
        
        print(f"\n🔍 Testing web search with query: {test_query}")
        results = enhancer.search(test_query, max_results=3)
        
        print(f"✅ Web search returned {len(results)} results")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.title} ({result.source})")
            
    except Exception as e:
        print(f"❌ Web search test failed: {e}")

def main():
    """Main test function."""
    print("🚀 Testing Optimized RAGv2 Configuration")
    print("=" * 60)
    
    # Test optimized configuration
    results = test_optimized_configuration()
    
    # Analyze results
    analyze_results(results)
    
    # Test web search
    test_web_search_fix()
    
    print(f"\n🎉 Test Complete!")
    print(f"📋 Summary:")
    print(f"   - Optimized reranker threshold: {RERANKER_THRESHOLD}")
    print(f"   - Increased dense top-k: {DENSE_TOP_K}")
    print(f"   - Tested {len(results)} queries")
    print(f"   - Check results above for performance insights")

if __name__ == "__main__":
    main() 
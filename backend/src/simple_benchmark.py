#!/usr/bin/env python3
"""
Simple RAG Benchmark Suite
==========================

Quick benchmark comparing key RAG approaches.
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Import RAG systems
from rag.advanced_rag_pipeline import AdvancedRAGPipeline
from rag.utils.embeddings_v2 import EnhancedEmbeddings
from pinecone import Pinecone

def test_advanced_rag(query: str):
    """Test Advanced RAG pipeline."""
    print(f"  🔹 Testing Advanced RAG...")
    start_time = time.time()
    
    try:
        advanced_rag = AdvancedRAGPipeline()
        result = advanced_rag.answer(query)
        
        processing_time = time.time() - start_time
        
        return {
            "approach": "Advanced RAG",
            "query": query,
            "answer": result.answer,
            "confidence": result.confidence_score,
            "verified": result.verification_result.is_verified if result.verification_result else False,
            "processing_time": processing_time,
            "contexts_count": len(result.retrieval_results),
            "error": None
        }
    except Exception as e:
        return {
            "approach": "Advanced RAG",
            "query": query,
            "answer": "",
            "confidence": 0.0,
            "verified": False,
            "processing_time": time.time() - start_time,
            "contexts_count": 0,
            "error": str(e)
        }

def test_per_row_retrieval(query: str):
    """Test per-row retrieval."""
    print(f"  🔹 Testing Per-Row Retrieval...")
    start_time = time.time()
    
    try:
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index = pc.Index('exams-index-enhanced')
        embeddings = EnhancedEmbeddings()
        
        query_embedding = embeddings.encode_single(query)
        
        results = index.query(
            vector=query_embedding,
            top_k=5,
            namespace='per_row',
            include_metadata=True
        )
        
        processing_time = time.time() - start_time
        best_score = results['matches'][0]['score'] if results['matches'] else 0.0
        
        return {
            "approach": "Per-Row Retrieval",
            "query": query,
            "answer": f"Retrieved {len(results['matches'])} results",
            "confidence": best_score,
            "verified": False,
            "processing_time": processing_time,
            "contexts_count": len(results['matches']),
            "error": None
        }
    except Exception as e:
        return {
            "approach": "Per-Row Retrieval",
            "query": query,
            "answer": "",
            "confidence": 0.0,
            "verified": False,
            "processing_time": time.time() - start_time,
            "contexts_count": 0,
            "error": str(e)
        }

def test_traditional_retrieval(query: str):
    """Test traditional db_v2 retrieval."""
    print(f"  🔹 Testing Traditional Retrieval...")
    start_time = time.time()
    
    try:
        pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
        index = pc.Index('exams-index-enhanced')
        embeddings = EnhancedEmbeddings()
        
        query_embedding = embeddings.encode_single(query)
        
        results = index.query(
            vector=query_embedding,
            top_k=5,
            namespace='db_v2',
            include_metadata=True
        )
        
        processing_time = time.time() - start_time
        best_score = results['matches'][0]['score'] if results['matches'] else 0.0
        
        return {
            "approach": "Traditional Retrieval",
            "query": query,
            "answer": f"Retrieved {len(results['matches'])} results",
            "confidence": best_score,
            "verified": False,
            "processing_time": processing_time,
            "contexts_count": len(results['matches']),
            "error": None
        }
    except Exception as e:
        return {
            "approach": "Traditional Retrieval",
            "query": query,
            "answer": "",
            "confidence": 0.0,
            "verified": False,
            "processing_time": time.time() - start_time,
            "contexts_count": 0,
            "error": str(e)
        }

def main():
    """Run simple benchmark."""
    load_dotenv()
    
    print("🚀 Simple RAG Benchmark Suite")
    print("=" * 50)
    
    # Test queries
    test_queries = [
        "Quali corsi insegna il prof Lenzerini?",
        "Come si chiama di nome il prof Lenzerini?", 
        "Quali sono i corsi insegnati da Ottolino?",
        "Chi è il professore che insegna Sistemi Operativi?",
        "Cosa insegna Gabriele Proietti Mattia?"
    ]
    
    results = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 QUERY {i}/{len(test_queries)}: {query}")
        print("-" * 50)
        
        # Test all approaches
        approaches = [
            test_advanced_rag,
            test_per_row_retrieval,
            test_traditional_retrieval
        ]
        
        for test_func in approaches:
            result = test_func(query)
            results.append(result)
            
            if result["error"]:
                print(f"    ❌ {result['approach']}: {result['error']}")
            else:
                print(f"    ✅ {result['approach']}: {result['confidence']:.3f} confidence, {result['processing_time']:.2f}s")
    
    # Analyze results
    print(f"\n📊 ANALYSIS")
    print("=" * 30)
    
    by_approach = {}
    for result in results:
        approach = result["approach"]
        if approach not in by_approach:
            by_approach[approach] = []
        by_approach[approach].append(result)
    
    for approach, approach_results in by_approach.items():
        successful = [r for r in approach_results if r["error"] is None]
        if successful:
            avg_confidence = sum(r["confidence"] for r in successful) / len(successful)
            avg_time = sum(r["processing_time"] for r in successful) / len(successful)
            success_rate = len(successful) / len(approach_results)
            
            print(f"\n{approach}:")
            print(f"  Success Rate: {success_rate:.1%}")
            print(f"  Avg Confidence: {avg_confidence:.3f}")
            print(f"  Avg Time: {avg_time:.2f}s")
            
            if approach == "Advanced RAG":
                verified_count = sum(1 for r in successful if r["verified"])
                print(f"  Verified Answers: {verified_count}/{len(successful)}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"../../simple_benchmark_results_{timestamp}.json"
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "timestamp": timestamp,
            "test_queries": test_queries,
            "results": results,
            "analysis": by_approach
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {results_file}")
    print("🎉 Benchmark completed!")

if __name__ == "__main__":
    main()

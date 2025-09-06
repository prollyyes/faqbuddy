#!/usr/bin/env python3
"""
Compare Per-Row vs Traditional Chunking Approaches
=================================================

This script compares the performance of the per-row approach vs traditional chunking
for specific queries to demonstrate the improvement.
"""

import os
import sys
import time
from dotenv import load_dotenv
from typing import List, Dict, Any

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from pinecone import Pinecone
from rag.utils.embeddings_v2 import EnhancedEmbeddings

def test_query_retrieval(query: str, namespace: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Test query retrieval in a specific namespace."""
    load_dotenv()
    
    pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
    index = pc.Index('exams-index-enhanced')
    embeddings = EnhancedEmbeddings()
    
    query_embedding = embeddings.encode_single(query)
    
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        namespace=namespace,
        include_metadata=True
    )
    
    return results['matches']

def compare_approaches():
    """Compare per-row vs traditional approaches."""
    print("🔬 COMPARING PER-ROW VS TRADITIONAL CHUNKING APPROACHES")
    print("=" * 70)
    
    # Test queries
    test_queries = [
        "Who teaches Sistemi Operativi?",
        "Da quanti crediti è il corso di Sistemi Operativi?",
        "Chi insegna Sistemi di Calcolo?",
        "Qual è il docente del corso di Programmazione?",
        "Conosci il professor Lenzerini?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 TEST {i}: {query}")
        print("-" * 50)
        
        # Test per-row namespace
        print("🔹 PER-ROW NAMESPACE:")
        per_row_results = test_query_retrieval(query, 'per_row', 3)
        for j, match in enumerate(per_row_results, 1):
            score = match['score']
            text = match['metadata']['text'][:100] + "..." if len(match['metadata']['text']) > 100 else match['metadata']['text']
            print(f"  {j}. Score: {score:.4f} | {text}")
        
        # Test traditional db_v2 namespace
        print("\n🔹 TRADITIONAL DB_V2 NAMESPACE:")
        db_v2_results = test_query_retrieval(query, 'db_v2', 3)
        for j, match in enumerate(db_v2_results, 1):
            score = match['score']
            text = match['metadata']['text'][:100] + "..." if len(match['metadata']['text']) > 100 else match['metadata']['text']
            print(f"  {j}. Score: {score:.4f} | {text}")
        
        # Analysis
        per_row_best = per_row_results[0]['score'] if per_row_results else 0
        db_v2_best = db_v2_results[0]['score'] if db_v2_results else 0
        
        if per_row_best > db_v2_best:
            improvement = ((per_row_best - db_v2_best) / db_v2_best) * 100 if db_v2_best > 0 else 0
            print(f"\n✅ PER-ROW WINS: {improvement:.1f}% better score")
        elif db_v2_best > per_row_best:
            decline = ((db_v2_best - per_row_best) / per_row_best) * 100 if per_row_best > 0 else 0
            print(f"\n❌ TRADITIONAL WINS: {decline:.1f}% better score")
        else:
            print(f"\n🤝 TIE: Same best score")

if __name__ == "__main__":
    compare_approaches()

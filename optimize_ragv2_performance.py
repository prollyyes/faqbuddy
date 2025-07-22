#!/usr/bin/env python3
"""
RAGv2 Performance Optimization Script
====================================

This script analyzes the current RAGv2 performance and suggests optimizations
based on the test results showing BM25 fallback and web search failures.
"""

import os
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from rag.config import (
    RERANKER_THRESHOLD, DENSE_TOP_K, MAX_CONTEXT_TOKENS,
    get_feature_flags, get_ragv2_namespaces
)
from rag.retrieval_v2_enhanced import EnhancedRetrievalV2
from rag.utils.embeddings_v2 import EnhancedEmbeddings
from pinecone import Pinecone

def analyze_current_performance():
    """Analyze current RAGv2 performance issues."""
    print("🔍 Analyzing Current RAGv2 Performance Issues")
    print("=" * 50)
    
    # Current configuration
    print(f"📊 Current Configuration:")
    print(f"   Reranker threshold: {RERANKER_THRESHOLD}")
    print(f"   Dense top-k: {DENSE_TOP_K}")
    print(f"   Max context tokens: {MAX_CONTEXT_TOKENS}")
    
    # Feature flags
    flags = get_feature_flags()
    print(f"\n🚩 Active Features:")
    for flag, enabled in flags.items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {flag}")
    
    # Issues identified
    print(f"\n⚠️ Issues Identified:")
    print(f"   1. Reranker threshold ({RERANKER_THRESHOLD}) too high - only 2/50 results passed")
    print(f"   2. Web search failing with 400 error")
    print(f"   3. BM25 fallback being used instead of dense retrieval")
    print(f"   4. Limited PDF results making it through cross-encoder")

def test_threshold_optimization():
    """Test different reranker thresholds to find optimal value."""
    print(f"\n🧪 Testing Reranker Threshold Optimization")
    print("=" * 50)
    
    # Test query from the output
    test_query = "Come mi posso iscrivere al corso di ingegneria informatica e automatica?"
    
    # Load environment
    load_dotenv()
    
    # Initialize components
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    retrieval = EnhancedRetrievalV2(pc)
    
    # Test different thresholds
    thresholds = [0.05, 0.075, 0.1, 0.125, 0.15, 0.2]
    results = {}
    
    for threshold in thresholds:
        print(f"\n🔍 Testing threshold: {threshold}")
        
        # Temporarily modify the threshold
        import rag.config
        original_threshold = rag.config.RERANKER_THRESHOLD
        rag.config.RERANKER_THRESHOLD = threshold
        
        try:
            # Perform retrieval
            retrieval_results = retrieval.retrieve(test_query)
            
            # Count results by namespace
            namespace_counts = {}
            for result in retrieval_results:
                namespace = result.get('namespace', 'unknown')
                namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
            
            results[threshold] = {
                'total_results': len(retrieval_results),
                'namespace_breakdown': namespace_counts,
                'has_pdf_results': 'pdf_v2' in namespace_counts,
                'has_db_results': 'db_v2' in namespace_counts,
                'has_bm25_fallback': 'bm25_fallback' in namespace_counts
            }
            
            print(f"   Results: {len(retrieval_results)} total")
            print(f"   Namespaces: {namespace_counts}")
            
        except Exception as e:
            print(f"   Error: {e}")
            results[threshold] = {'error': str(e)}
        
        finally:
            # Restore original threshold
            rag.config.RERANKER_THRESHOLD = original_threshold
    
    return results

def suggest_optimizations(threshold_results: Dict[float, Dict[str, Any]]):
    """Suggest optimizations based on test results."""
    print(f"\n💡 Optimization Suggestions")
    print("=" * 50)
    
    # Find best threshold
    best_threshold = None
    best_score = -1
    
    for threshold, result in threshold_results.items():
        if 'error' in result:
            continue
            
        score = 0
        if result['has_pdf_results']:
            score += 2
        if result['has_db_results']:
            score += 1
        if not result['has_bm25_fallback']:
            score += 3
        if result['total_results'] >= 5:
            score += 1
        
        if score > best_score:
            best_score = score
            best_threshold = threshold
    
    print(f"🎯 Recommended Reranker Threshold: {best_threshold}")
    print(f"   Score: {best_score}")
    
    # Web search fixes
    print(f"\n🌐 Web Search Fixes:")
    print(f"   1. Check GOOGLE_SEARCH_API_KEY environment variable")
    print(f"   2. Verify GOOGLE_SEARCH_CX (Custom Search Engine ID)")
    print(f"   3. Ensure Google Custom Search API is enabled")
    print(f"   4. Check API quotas and billing")
    
    # Additional optimizations
    print(f"\n⚡ Additional Optimizations:")
    print(f"   1. Increase DENSE_TOP_K from {DENSE_TOP_K} to 75-100")
    print(f"   2. Adjust namespace boosts for better PDF retrieval")
    print(f"   3. Consider enabling hallucination guards for better quality")
    print(f"   4. Monitor cross-encoder performance for Italian text")

def create_optimized_config():
    """Create an optimized configuration file."""
    print(f"\n📝 Creating Optimized Configuration")
    print("=" * 50)
    
    optimized_config = {
        "reranker_threshold": 0.075,  # Lowered from 0.1
        "dense_top_k": 75,  # Increased from 50
        "max_context_tokens": 4000,  # Keep current
        "namespace_boosts": {
            "pdf_v2": 1.4,  # Increased PDF boost
            "documents_v2": 1.2,
            "db_v2": 1.0
        },
        "web_search_fixes": {
            "check_api_key": True,
            "verify_cx": True,
            "enable_api": True
        }
    }
    
    # Save to file
    with open('optimized_ragv2_config.json', 'w') as f:
        json.dump(optimized_config, f, indent=2)
    
    print(f"✅ Optimized configuration saved to optimized_ragv2_config.json")
    return optimized_config

def main():
    """Main optimization function."""
    print("🚀 RAGv2 Performance Optimization")
    print("=" * 60)
    
    # Analyze current issues
    analyze_current_performance()
    
    # Test threshold optimization
    threshold_results = test_threshold_optimization()
    
    # Suggest optimizations
    suggest_optimizations(threshold_results)
    
    # Create optimized config
    optimized_config = create_optimized_config()
    
    print(f"\n🎉 Optimization Complete!")
    print(f"📋 Next Steps:")
    print(f"   1. Apply the optimized reranker threshold")
    print(f"   2. Fix web search API configuration")
    print(f"   3. Test with the new settings")
    print(f"   4. Monitor performance improvements")

if __name__ == "__main__":
    main() 
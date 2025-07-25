#!/usr/bin/env python3
"""
Test Web Search Integration with RAG v2
=======================================

This script tests the integration of web search enhancement with the RAG v2 system.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from rag.web_search_enhancer import WebSearchEnhancer
from rag.config import get_feature_flags

def test_web_search_integration():
    """Test the web search integration."""
    print("🧪 Testing Web Search Integration...")
    
    # Check feature flags
    flags = get_feature_flags()
    print(f"📋 Feature flags: {flags}")
    
    # Test web search enhancer
    enhancer = WebSearchEnhancer()
    
    # Test query enhancement
    test_queries = [
        "Chi insegna il corso di Sistemi Operativi?",
        "Come si richiede l'iscrizione?",
        "Quali sono i requisiti per l'ammissione?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing query enhancement: {query}")
        print(f"{'='*60}")
        
        enhanced = enhancer._enhance_query_for_sapienza(query)
        print(f"Original: {query}")
        print(f"Enhanced: {enhanced}")
        
        # Test web search (without API keys, will use DuckDuckGo)
        print(f"\n🔍 Testing web search...")
        try:
            results = enhancer.search(query, max_results=2)
            print(f"Found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                print(f"  {i}. [{result.source}] {result.title}")
                print(f"     Score: {result.relevance_score:.3f}")
                print(f"     Type: {result.content_type}")
                print(f"     URL: {result.url}")
                print()
                
        except Exception as e:
            print(f"⚠️ Web search failed: {e}")
    
    # Test RAG integration format
    print(f"\n{'='*60}")
    print("Testing RAG integration format")
    print(f"{'='*60}")
    
    # Mock results for testing
    from rag.web_search_enhancer import WebSearchResult
    
    mock_results = [
        WebSearchResult(
            title="Sapienza - Corso di Sistemi Operativi",
            url="https://www.uniroma1.it/sistemi-operativi",
            snippet="Il corso di Sistemi Operativi è tenuto dal Prof. Paolo Ottolino...",
            source="sapienza",
            relevance_score=0.9,
            content_type="official"
        )
    ]
    
    formatted = enhancer.format_results_for_rag(mock_results)
    print(f"Formatted {len(formatted)} results for RAG integration")
    
    for result in formatted:
        print(f"  ID: {result['id']}")
        print(f"  Score: {result['score']}")
        print(f"  Namespace: {result['namespace']}")
        print(f"  Source: {result['metadata']['source']}")
        print(f"  Text preview: {result['text'][:100]}...")
        print()
    
    print("✅ Web search integration test completed!")
    return True

if __name__ == "__main__":
    test_web_search_integration() 
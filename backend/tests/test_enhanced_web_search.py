#!/usr/bin/env python3
"""
Test Enhanced Web Search with Essential Keyword Extraction
=========================================================

This script demonstrates how the web search now extracts essential keywords
instead of using the full user query.
"""

import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from rag.web_search_enhancer import WebSearchEnhancer

def test_keyword_extraction():
    """Test the essential keyword extraction functionality."""
    print("🔍 Testing Enhanced Web Search with Essential Keywords")
    print("=" * 60)
    
    # Load environment
    load_dotenv()
    
    # Initialize web search enhancer
    enhancer = WebSearchEnhancer()
    
    # Test queries
    test_queries = [
        "Mi spieghi come funziona il sistema bibliotecario in Sapienza?",
        "Chi insegna il corso di Sistemi Operativi?",
        "Come mi posso iscrivere al corso di ingegneria informatica e automatica?",
        "Quali sono i requisiti per laurearsi in ingegneria informatica?",
        "Dove posso trovare i materiali del corso di Programmazione?",
        "Potresti dirmi come funziona l'esame di Analisi Matematica?",
        "Vorrei sapere quando sono le scadenze per l'iscrizione ai corsi"
    ]
    
    print("📝 Original Query → Essential Keywords → Enhanced Search Query")
    print("-" * 80)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Original: {query}")
        
        # Extract essential keywords
        essential = enhancer._extract_essential_keywords(query)
        print(f"   Essential: {essential}")
        
        # Enhance for Sapienza
        enhanced = enhancer._enhance_query_for_sapienza(query)
        print(f"   Enhanced: {enhanced}")
        
        print("-" * 80)
    
    # Test actual web search with one example
    print(f"\n🌐 Testing Actual Web Search")
    print("=" * 40)
    
    test_query = "Mi spieghi come funziona il sistema bibliotecario in Sapienza?"
    print(f"Original query: {test_query}")
    
    # Show the transformation
    essential = enhancer._extract_essential_keywords(test_query)
    enhanced = enhancer._enhance_query_for_sapienza(test_query)
    
    print(f"Essential keywords: {essential}")
    print(f"Enhanced search: {enhanced}")
    
    # Perform actual search
    print(f"\n🔍 Performing web search...")
    results = enhancer.search(test_query, max_results=3)
    
    print(f"✅ Found {len(results)} results")
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result.title}")
        print(f"      URL: {result.url}")
        print(f"      Source: {result.source} ({result.content_type})")
        print(f"      Score: {result.relevance_score:.2f}")
        print()

def main():
    """Main test function."""
    test_keyword_extraction()
    
    print("🎉 Enhanced Web Search Test Complete!")
    print("\n💡 Benefits of Essential Keyword Extraction:")
    print("   - More focused and relevant search results")
    print("   - Removes noise from question words and common terms")
    print("   - Better matches with search engine algorithms")
    print("   - Maintains Sapienza context for academic relevance")

if __name__ == "__main__":
    main() 
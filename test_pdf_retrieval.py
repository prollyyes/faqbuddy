#!/usr/bin/env python3
"""
PDF Retrieval Test for RAG v2
=============================

This script tests whether the RAG v2 system is correctly retrieving information
from PDF files stored in the Pinecone namespace for PDF.
"""

import os
import sys
import time
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add backend/src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from backend.src.rag.config import (
    get_ragv2_namespaces, 
    get_existing_namespaces,
    INDEX_NAME,
    RAGV2_PDF_NAMESPACE
)
from backend.src.rag.retrieval_v2 import EnhancedRetrieval
from backend.src.rag.utils.embeddings_v2 import EnhancedEmbeddings
from pinecone import Pinecone

def test_pdf_namespace_configuration():
    """Test 1: Verify PDF namespace configuration."""
    print("🔍 Test 1: PDF Namespace Configuration")
    print("=" * 50)
    
    # Get namespace configuration
    ragv2_namespaces = get_ragv2_namespaces()
    existing_namespaces = get_existing_namespaces()
    
    print(f"RAGv2 namespaces: {ragv2_namespaces}")
    print(f"Existing namespaces: {existing_namespaces}")
    print(f"PDF namespace: {RAGV2_PDF_NAMESPACE}")
    
    # Verify PDF namespace is configured
    if RAGV2_PDF_NAMESPACE in ragv2_namespaces.values():
        print("✅ PDF namespace is properly configured")
        return True
    else:
        print("❌ PDF namespace is missing from configuration")
        return False

def test_pinecone_connection():
    """Test 2: Verify Pinecone connection and index access."""
    print("\n🔍 Test 2: Pinecone Connection")
    print("=" * 50)
    
    try:
        load_dotenv()
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Check if index exists
        if INDEX_NAME not in pc.list_indexes().names():
            print(f"❌ Index '{INDEX_NAME}' not found")
            return False
        
        # Get index stats
        index = pc.Index(INDEX_NAME)
        stats = index.describe_index_stats()
        
        print(f"✅ Connected to Pinecone index: {INDEX_NAME}")
        print(f"   Total vectors: {stats.get('total_vector_count', 0)}")
        print(f"   Dimension: {stats.get('dimension', 'unknown')}")
        print(f"   Metric: {stats.get('metric', 'unknown')}")
        
        # Check namespaces
        namespaces = stats.get('namespaces', {})
        print(f"   Available namespaces: {list(namespaces.keys())}")
        
        # Check PDF namespace specifically
        if RAGV2_PDF_NAMESPACE in namespaces:
            pdf_stats = namespaces[RAGV2_PDF_NAMESPACE]
            print(f"✅ PDF namespace '{RAGV2_PDF_NAMESPACE}' found")
            print(f"   PDF vectors: {pdf_stats.get('vector_count', 0)}")
            return True
        else:
            print(f"❌ PDF namespace '{RAGV2_PDF_NAMESPACE}' not found")
            print(f"   Available namespaces: {list(namespaces.keys())}")
            return False
            
    except Exception as e:
        print(f"❌ Pinecone connection failed: {e}")
        return False

def test_embeddings_generation():
    """Test 3: Verify embeddings generation for PDF content."""
    print("\n🔍 Test 3: Embeddings Generation")
    print("=" * 50)
    
    try:
        embeddings = EnhancedEmbeddings()
        
        # Test with sample PDF-like text
        test_texts = [
            "Il corso di Sistemi Operativi è tenuto dal professor Paolo Ottolino.",
            "Gli esami si svolgono in modalità scritta e orale.",
            "Il programma del corso include processi, thread e gestione della memoria."
        ]
        
        print("Generating embeddings for test texts...")
        start_time = time.time()
        embeddings_list = embeddings.encode(test_texts)
        end_time = time.time()
        
        print(f"✅ Generated {len(embeddings_list)} embeddings in {end_time - start_time:.2f}s")
        print(f"   Embedding dimension: {len(embeddings_list[0])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embeddings generation failed: {e}")
        return False

def test_pdf_retrieval():
    """Test 4: Test actual PDF retrieval from Pinecone."""
    print("\n🔍 Test 4: PDF Retrieval Test")
    print("=" * 50)
    
    try:
        # Initialize retrieval system
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        retrieval = EnhancedRetrieval(pc)
        
        # Test queries that should retrieve PDF content
        test_queries = [
            "Chi insegna il corso di Sistemi Operativi?",
            "Come si svolge l'esame?",
            "Quali sono i requisiti per l'iscrizione?",
            "Come funziona il sistema di crediti?",
            "Quali sono le modalità di tirocinio?"
        ]
        
        pdf_results_count = 0
        total_results = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\nQuery {i}: {query}")
            
            # Perform retrieval
            start_time = time.time()
            results = retrieval.retrieve(query)
            end_time = time.time()
            
            print(f"   Retrieval time: {end_time - start_time:.2f}s")
            print(f"   Total results: {len(results)}")
            
            # Check for PDF results
            pdf_results = [r for r in results if r.get('namespace') == RAGV2_PDF_NAMESPACE]
            print(f"   PDF results: {len(pdf_results)}")
            
            if pdf_results:
                print("   PDF sources found:")
                for j, result in enumerate(pdf_results[:3], 1):  # Show first 3
                    metadata = result.get('metadata', {})
                    source = metadata.get('source', 'Unknown')
                    text_preview = result.get('text', '')[:100] + "..." if len(result.get('text', '')) > 100 else result.get('text', '')
                    print(f"     {j}. {source}: {text_preview}")
            
            pdf_results_count += len(pdf_results)
            total_results += len(results)
        
        # Summary
        print(f"\n📊 Retrieval Summary:")
        print(f"   Total queries: {len(test_queries)}")
        print(f"   Total results: {total_results}")
        print(f"   PDF results: {pdf_results_count}")
        print(f"   PDF coverage: {pdf_results_count/total_results*100:.1f}%" if total_results > 0 else "   PDF coverage: 0%")
        
        if pdf_results_count > 0:
            print("✅ PDF retrieval is working correctly")
            return True
        else:
            print("❌ No PDF results found - PDF namespace may be empty or not properly indexed")
            return False
            
    except Exception as e:
        print(f"❌ PDF retrieval test failed: {e}")
        return False

def test_namespace_comparison():
    """Test 5: Compare results across different namespaces."""
    print("\n🔍 Test 5: Namespace Comparison")
    print("=" * 50)
    
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(INDEX_NAME)
        
        # Test query
        query = "Chi insegna il corso di Sistemi Operativi?"
        
        # Get embeddings
        embeddings = EnhancedEmbeddings()
        query_embedding = embeddings.encode_single(query)
        
        # Search different namespaces
        namespaces_to_test = [
            ("PDF (RAGv2)", RAGV2_PDF_NAMESPACE),
            ("Documents (RAGv2)", "documents_v2"),
            ("Database (RAGv2)", "db_v2"),
            ("Documents (Original)", "documents"),
            ("Database (Original)", "db")
        ]
        
        for namespace_name, namespace in namespaces_to_test:
            try:
                results = index.query(
                    vector=query_embedding,
                    top_k=5,
                    namespace=namespace,
                    include_metadata=True
                )
                
                print(f"{namespace_name}: {len(results.get('matches', []))} results")
                
                # Show first result if available
                if results.get('matches'):
                    first_match = results['matches'][0]
                    score = first_match.get('score', 0)
                    metadata = first_match.get('metadata', {})
                    source = metadata.get('source', 'Unknown')
                    print(f"   Top result: {source} (score: {score:.3f})")
                else:
                    print("   No results found")
                    
            except Exception as e:
                print(f"{namespace_name}: Error - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Namespace comparison failed: {e}")
        return False

def main():
    """Run all PDF retrieval tests."""
    print("🧪 PDF Retrieval Test Suite for RAG v2")
    print("=" * 60)
    
    tests = [
        ("Namespace Configuration", test_pdf_namespace_configuration),
        ("Pinecone Connection", test_pinecone_connection),
        ("Embeddings Generation", test_embeddings_generation),
        ("PDF Retrieval", test_pdf_retrieval),
        ("Namespace Comparison", test_namespace_comparison)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! PDF retrieval is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        
        # Provide recommendations
        print("\n🔧 Recommendations:")
        if not any(name == "PDF Retrieval" and result for name, result in results):
            print("   - PDF namespace may be empty. Run populate_ragv2.py to index PDF files")
        if not any(name == "Pinecone Connection" and result for name, result in results):
            print("   - Check PINECONE_API_KEY environment variable")
        if not any(name == "Embeddings Generation" and result for name, result in results):
            print("   - Check model dependencies and internet connection")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test Per-Row Query
==================

Simple test to verify that the per-row approach is working correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend/src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from pinecone import Pinecone
from rag.config import INDEX_NAME, get_per_row_namespace
from rag.utils.embeddings_v2 import EnhancedEmbeddings

def test_per_row_query():
    """Test a query that should find results in the per_row namespace."""
    print("🧪 Testing Per-Row Query")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(INDEX_NAME)
    embeddings = EnhancedEmbeddings()
    per_row_namespace = get_per_row_namespace()
    
    # Test query that should find course information
    query = "Corso di Sistemi Operativi"
    print(f"🔍 Query: '{query}'")
    print("-" * 40)
    
    try:
        # Generate query embedding
        query_embedding = embeddings.encode_single(query)
        
        # Search in per_row namespace
        results = index.query(
            vector=query_embedding,
            top_k=5,
            namespace=per_row_namespace,
            include_metadata=True
        )
        
        matches = results.get('matches', [])
        
        if matches:
            print(f"✅ Found {len(matches)} results in per_row namespace:")
            for i, match in enumerate(matches, 1):
                score = match.get('score', 0)
                metadata = match.get('metadata', {})
                node_type = metadata.get('node_type', 'unknown')
                table_name = metadata.get('table_name', 'unknown')
                text = metadata.get('text', 'No text available')
                
                print(f"   {i}. Score: {score:.3f} | Type: {node_type} | Table: {table_name}")
                print(f"      Text: {text[:100]}{'...' if len(text) > 100 else ''}")
                
            # Check if we found course-related results
            course_results = [m for m in matches if m['metadata'].get('node_type') == 'course']
            if course_results:
                print(f"\n✅ Success! Found {len(course_results)} course results in per_row namespace")
                return True
            else:
                print(f"\n⚠️ Found results but no course-specific matches")
                return False
        else:
            print("❌ No results found in per_row namespace")
            return False
            
    except Exception as e:
        print(f"❌ Error searching: {e}")
        return False

def test_namespace_comparison():
    """Compare results between per_row and db_v2 namespaces."""
    print("\n🧪 Testing Namespace Comparison")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Initialize components
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(INDEX_NAME)
    embeddings = EnhancedEmbeddings()
    
    # Test query
    query = "Corso di Sistemi Operativi"
    query_embedding = embeddings.encode_single(query)
    
    print(f"🔍 Query: '{query}'")
    print("-" * 40)
    
    # Search in different namespaces
    namespaces = ["per_row", "db_v2"]
    
    for namespace in namespaces:
        try:
            print(f"\n📊 Searching in namespace: {namespace}")
            
            results = index.query(
                vector=query_embedding,
                top_k=3,
                namespace=namespace,
                include_metadata=True
            )
            
            matches = results.get('matches', [])
            
            if matches:
                print(f"✅ Found {len(matches)} results:")
                for i, match in enumerate(matches, 1):
                    score = match.get('score', 0)
                    metadata = match.get('metadata', {})
                    node_type = metadata.get('node_type', 'unknown')
                    table_name = metadata.get('table_name', 'unknown')
                    
                    print(f"   {i}. Score: {score:.3f} | Type: {node_type} | Table: {table_name}")
            else:
                print("❌ No results found")
                
        except Exception as e:
            print(f"❌ Error searching in {namespace}: {e}")

def main():
    """Run all tests."""
    print("🚀 Starting Per-Row Query Tests")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    
    # Check if database connection is available
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY environment variable is required")
        sys.exit(1)
    
    # Run tests
    success = test_per_row_query()
    test_namespace_comparison()
    
    if success:
        print(f"\n🎉 Per-row approach is working correctly!")
    else:
        print(f"\n⚠️ Per-row approach may have issues")
    
    print(f"\n✅ All tests completed!")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
RAGv2 Demo Script
=================

This script demonstrates the RAGv2 pipeline with different feature flag combinations.
It shows how to enable/disable features and compare performance.
"""

import os
import time
from typing import Dict, Any

def demo_feature_flags():
    """Demonstrate different feature flag combinations."""
    print("🚀 RAGv2 Feature Flag Demo")
    print("=" * 50)
    
    # Import after setting environment variables
    from .config import get_feature_flags, is_feature_enabled
    
    # Demo 1: All features disabled (baseline)
    print("\n📋 Demo 1: Baseline (All features disabled)")
    print("-" * 40)
    
    # Set environment variables for baseline
    os.environ.update({
        'SCHEMA_AWARE_CHUNKING': 'false',
        'INSTRUCTOR_XL_EMBEDDINGS': 'false',
        'RERANKER_ENABLED': 'false',
        'HALLUCINATION_GUARDS': 'false',
        'OBSERVABILITY_ENABLED': 'false'
    })
    
    flags = get_feature_flags()
    for flag, enabled in flags.items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {flag}")
    
    # Demo 2: Schema-aware chunking only
    print("\n📋 Demo 2: Schema-aware chunking enabled")
    print("-" * 40)
    
    os.environ['SCHEMA_AWARE_CHUNKING'] = 'true'
    flags = get_feature_flags()
    for flag, enabled in flags.items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {flag}")
    
    # Demo 3: Enhanced embeddings
    print("\n📋 Demo 3: Enhanced embeddings enabled")
    print("-" * 40)
    
    os.environ['INSTRUCTOR_XL_EMBEDDINGS'] = 'true'
    flags = get_feature_flags()
    for flag, enabled in flags.items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {flag}")
    
    # Demo 4: Retrieval improvements
    print("\n📋 Demo 4: Retrieval improvements enabled")
    print("-" * 40)
    
    os.environ['RERANKER_ENABLED'] = 'true'
    flags = get_feature_flags()
    for flag, enabled in flags.items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {flag}")
    
    # Demo 5: Generation guards
    print("\n📋 Demo 5: Generation guards enabled")
    print("-" * 40)
    
    os.environ['HALLUCINATION_GUARDS'] = 'true'
    flags = get_feature_flags()
    for flag, enabled in flags.items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {flag}")
    
    # Demo 6: Full RAGv2 (all features)
    print("\n📋 Demo 6: Full RAGv2 (all features enabled)")
    print("-" * 40)
    
    os.environ['OBSERVABILITY_ENABLED'] = 'true'
    flags = get_feature_flags()
    for flag, enabled in flags.items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {flag}")


def demo_pipeline_performance():
    """Demonstrate pipeline performance with different configurations."""
    print("\n🏃 RAGv2 Pipeline Performance Demo")
    print("=" * 50)
    
    # Test questions
    test_questions = [
        "Who teaches Operating Systems this semester?",
        "What are the prerequisites for Database Systems?",
        "How many CFU does the Machine Learning course have?",
        "What is the exam modality for Computer Networks?",
        "Who is the president of the Computer Science faculty?"
    ]
    
    # Import pipeline
    from .rag_pipeline_v2 import RAGv2Pipeline
    
    # Test with different configurations
    configurations = [
        ("Baseline", {
            'SCHEMA_AWARE_CHUNKING': 'false',
            'INSTRUCTOR_XL_EMBEDDINGS': 'false',
            'RERANKER_ENABLED': 'false',
            'HALLUCINATION_GUARDS': 'false',
            'OBSERVABILITY_ENABLED': 'false'
        }),
        ("Schema-aware chunking", {
            'SCHEMA_AWARE_CHUNKING': 'true',
            'INSTRUCTOR_XL_EMBEDDINGS': 'false',
            'RERANKER_ENABLED': 'false',
            'HALLUCINATION_GUARDS': 'false',
            'OBSERVABILITY_ENABLED': 'false'
        }),
        ("Enhanced embeddings", {
            'SCHEMA_AWARE_CHUNKING': 'true',
            'INSTRUCTOR_XL_EMBEDDINGS': 'true',
            'RERANKER_ENABLED': 'false',
            'HALLUCINATION_GUARDS': 'false',
            'OBSERVABILITY_ENABLED': 'false'
        }),
        ("Full RAGv2", {
            'SCHEMA_AWARE_CHUNKING': 'true',
            'INSTRUCTOR_XL_EMBEDDINGS': 'true',
            'RERANKER_ENABLED': 'true',
            'HALLUCINATION_GUARDS': 'true',
            'OBSERVABILITY_ENABLED': 'true'
        })
    ]
    
    for config_name, env_vars in configurations:
        print(f"\n🔧 Testing: {config_name}")
        print("-" * 30)
        
        # Set environment variables
        os.environ.update(env_vars)
        
        # Initialize pipeline
        start_time = time.time()
        pipeline = RAGv2Pipeline()
        init_time = time.time() - start_time
        
        print(f"   Initialization time: {init_time:.3f}s")
        
        # Test with first question
        question = test_questions[0]
        print(f"   Testing question: {question}")
        
        start_time = time.time()
        result = pipeline.answer(question)
        query_time = time.time() - start_time
        
        print(f"   Query time: {query_time:.3f}s")
        print(f"   Retrieved documents: {result.get('retrieved_documents', 0)}")
        print(f"   Answer length: {len(result.get('answer', ''))} characters")
        
        # Show features used
        features_used = result.get('features_used', {})
        active_features = [f for f, used in features_used.items() if used]
        if active_features:
            print(f"   Active features: {', '.join(active_features)}")
        else:
            print(f"   Active features: none")


def demo_component_tests():
    """Run individual component tests."""
    print("\n🧪 RAGv2 Component Tests")
    print("=" * 50)
    
    # Test schema-aware chunking
    print("\n📝 Testing Schema-aware Chunking...")
    try:
        from .utils.schema_aware_chunker import test_schema_aware_chunking
        result = test_schema_aware_chunking()
        print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
    except Exception as e:
        print(f"   Result: ❌ ERROR - {e}")
    
    # Test enhanced embeddings
    print("\n🔤 Testing Enhanced Embeddings...")
    try:
        from .utils.embeddings_v2 import test_embedding_upgrade
        result = test_embedding_upgrade()
        print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
    except Exception as e:
        print(f"   Result: ❌ ERROR - {e}")
    
    # Test enhanced retrieval
    print("\n🔍 Testing Enhanced Retrieval...")
    try:
        from .retrieval_v2 import test_enhanced_retrieval
        result = test_enhanced_retrieval()
        print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
    except Exception as e:
        print(f"   Result: ❌ ERROR - {e}")
    
    # Test generation guards
    print("\n🛡️ Testing Generation Guards...")
    try:
        from .generation_guards import test_generation_guards
        result = test_generation_guards()
        print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
    except Exception as e:
        print(f"   Result: ❌ ERROR - {e}")
    
    # Test full pipeline
    print("\n🚀 Testing Full RAGv2 Pipeline...")
    try:
        from .rag_pipeline_v2 import test_ragv2_pipeline
        result = test_ragv2_pipeline()
        print(f"   Result: {'✅ PASS' if result else '❌ FAIL'}")
    except Exception as e:
        print(f"   Result: ❌ ERROR - {e}")


def demo_usage_examples():
    """Show usage examples for different components."""
    print("\n📚 RAGv2 Usage Examples")
    print("=" * 50)
    
    print("\n1️⃣ Schema-aware Chunking:")
    print("""
from rag.utils.schema_aware_chunker import SchemaAwareChunker

chunker = SchemaAwareChunker()
chunks = chunker.get_course_edition_chunks()

for chunk in chunks[:3]:  # Show first 3 chunks
    print(f"ID: {chunk['id']}")
    print(f"Text: {chunk['text'][:100]}...")
    print(f"Node type: {chunk['metadata']['node_type']}")
    print()
""")
    
    print("\n2️⃣ Enhanced Embeddings:")
    print("""
from rag.utils.embeddings_v2 import EnhancedEmbeddings

embeddings = EnhancedEmbeddings()
vector = embeddings.encode_single("Sample text for embedding")

print(f"Embedding dimension: {len(vector)}")
print(f"Average latency: {embeddings.get_average_latency():.2f}ms")
""")
    
    print("\n3️⃣ Enhanced Retrieval:")
    print("""
from rag.retrieval_v2 import EnhancedRetrieval
from pinecone import Pinecone

pc = Pinecone(api_key="your-api-key")
retrieval = EnhancedRetrieval(pc)

results = retrieval.retrieve("Who teaches Operating Systems?")
print(f"Retrieved {len(results)} documents")
""")
    
    print("\n4️⃣ Generation Guards:")
    print("""
from rag.generation_guards import GenerationGuards

guards = GenerationGuards()
result = guards.generate_safe_answer(context, question)

print(f"Answer: {result['answer']}")
print(f"Verified: {result['is_verified']}")
print(f"Score: {result['verification_score']:.3f}")
""")
    
    print("\n5️⃣ Full RAGv2 Pipeline:")
    print("""
from rag.rag_pipeline_v2 import RAGv2Pipeline

# Set feature flags
os.environ['SCHEMA_AWARE_CHUNKING'] = 'true'
os.environ['INSTRUCTOR_XL_EMBEDDINGS'] = 'true'
os.environ['RERANKER_ENABLED'] = 'true'
os.environ['HALLUCINATION_GUARDS'] = 'true'

pipeline = RAGv2Pipeline()
result = pipeline.answer("Who teaches Operating Systems this semester?")

print(f"Answer: {result['answer']}")
print(f"Features used: {result['features_used']}")
print(f"Retrieved documents: {result['retrieved_documents']}")
""")


def main():
    """Run the complete RAGv2 demo."""
    print("🎯 RAGv2 Complete Demo")
    print("=" * 60)
    print("This demo shows the RAGv2 upgrade features and capabilities.")
    print("Make sure you have the required environment variables set.")
    print()
    
    try:
        # Demo 1: Feature flags
        demo_feature_flags()
        
        # Demo 2: Component tests
        demo_component_tests()
        
        # Demo 3: Usage examples
        demo_usage_examples()
        
        # Demo 4: Performance (optional - requires database connection)
        print("\n" + "=" * 60)
        print("Performance demo requires database connection.")
        print("To run performance demo, ensure:")
        print("  - Database is accessible")
        print("  - Pinecone API key is set")
        print("  - Required models are downloaded")
        print()
        
        response = input("Run performance demo? (y/N): ").lower().strip()
        if response == 'y':
            demo_pipeline_performance()
        
        print("\n✅ RAGv2 demo completed successfully!")
        print("\n📖 For more information, see docs/RAG_UPGRADE.md")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("Check that all dependencies are installed and environment is configured.")


if __name__ == "__main__":
    main() 
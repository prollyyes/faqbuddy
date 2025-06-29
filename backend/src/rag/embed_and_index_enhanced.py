# Enhanced Indexing Script for FAQBuddy
# This script creates enhanced chunks with academic knowledge and uploads them to Pinecone

import os
import sys
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec, CreateIndexSpec
import time
from src.rag.rag_core_enhanced import EnhancedRAGSystem

def create_enhanced_index():
    """
    Create enhanced Pinecone index with academic knowledge base.
    """
    load_dotenv()
    
    # Initialize Pinecone and ensure index exists BEFORE EnhancedRAGSystem
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index_name = "exams-index-enhanced"
    namespace = "v9"
    if index_name not in pc.list_indexes().names():
        print(f"🔨 Creating new Pinecone index: {index_name}")
        pc.create_index(
            name=index_name,
            spec=CreateIndexSpec(
                dimension=768,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",  # or "gcp" if you use Google Cloud
                    region="us-east-1"  # or your preferred region
                )
            )
        )
        time.sleep(10)  # Wait for index to be ready
    
    # Now it's safe to instantiate EnhancedRAGSystem
    print("🚀 Initializing Enhanced RAG System...")
    rag_system = EnhancedRAGSystem()
    
    # Create enhanced chunks
    print("📝 Creating enhanced chunks...")
    chunks = rag_system.create_enhanced_chunks()
    
    print(f"✅ Created {len(chunks)} enhanced chunks")
    
    # Prepare vectors for upload
    print("🔧 Preparing vectors for upload...")
    vectors_to_upsert = []
    
    for chunk in chunks:
        # Generate embedding
        text = chunk['text']
        embedding = rag_system.embedding_model.encode(text)
        
        # Prepare vector data
        vector_data = {
            'id': chunk['id'],
            'values': embedding.tolist(),
            'metadata': {
                'text': text,
                **chunk['metadata']
            }
        }
        vectors_to_upsert.append(vector_data)
    
    # Upload in batches
    batch_size = 100
    total_vectors = len(vectors_to_upsert)
    
    print(f"📤 Uploading {total_vectors} vectors to Pinecone...")
    
    for i in range(0, total_vectors, batch_size):
        batch = vectors_to_upsert[i:i + batch_size]
        print(f"Uploading batch {i//batch_size + 1}/{(total_vectors + batch_size - 1)//batch_size}")
        
        try:
            index = pc.Index(index_name)
            index.upsert(vectors=batch, namespace=namespace)
            print(f"✅ Batch {i//batch_size + 1} uploaded successfully")
        except Exception as e:
            print(f"❌ Error uploading batch {i//batch_size + 1}: {e}")
    
    print(f"🎉 Enhanced indexing completed!")
    print(f"📊 Total vectors uploaded: {total_vectors}")
    print(f"📁 Index: {index_name}")
    print(f"🏷️  Namespace: {namespace}")
    
    # Print statistics
    factual_count = sum(1 for chunk in chunks if chunk['metadata'].get('knowledge_type') == 'factual')
    procedural_count = sum(1 for chunk in chunks if chunk['metadata'].get('knowledge_type') == 'procedural')
    strategic_count = sum(1 for chunk in chunks if chunk['metadata'].get('knowledge_type') == 'strategic')
    
    print(f"\n📈 Knowledge Distribution:")
    print(f"   Factual: {factual_count}")
    print(f"   Procedural: {procedural_count}")
    print(f"   Strategic: {strategic_count}")

def test_enhanced_index():
    """
    Test the enhanced index with sample queries.
    """
    print("\n🧪 Testing Enhanced Index...")
    
    rag_system = EnhancedRAGSystem()
    
    test_queries = [
        "Come posso pianificare il mio percorso di studi?",
        "Conosci Marco Shaerf?",
        "Quali strategie per migliorare la media?",
        "Documenti necessari per laurea",
        "Come conciliare lavoro e studio?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print(f"{'='*50}")
        
        try:
            result = rag_system.generate_response(query)
            print(f"Intent: {result['detected_intent']}")
            print(f"Response: {result['response'][:200]}...")
            print(f"Time: {result['total_time']:.2f}s")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎯 Enhanced FAQBuddy Indexing Script")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_enhanced_index()
    else:
        create_enhanced_index()
        print("\n" + "=" * 50)
        print("✅ Enhanced indexing completed! Run with 'test' argument to test.") 
#!/usr/bin/env python3
"""
Restore Document Chunks Script
This script restores document chunks to the Pinecone index using the same embedding model
as the database chunks (all-mpnet-base-v2, 768 dimensions).
"""

import os
import sys
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec

# Import the PDF chunker
sys.path.append('backend/src/rag/utils')
from pdf_chunker import chunk_pdf

# Configuration
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend/data'))
INDEX_NAME = "exams-index-enhanced"
NAMESPACE = "documents"
EMBEDDING_MODEL = "all-mpnet-base-v2"  # Same as database chunks
CHUNK_WINDOW = 200
CHUNK_OVERLAP = 50

def get_pdf_files(data_dir):
    """Get all PDF files from the data directory."""
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return []
    
    pdf_files = [os.path.join(data_dir, f) for f in os.listdir(data_dir)
                if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(data_dir, f))]
    return pdf_files

def main():
    """Main execution function."""
    load_dotenv()
    
    print("🚀 Restoring Document Chunks to Pinecone")
    print("=" * 50)
    
    # Check environment
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY not found in environment")
        sys.exit(1)
    
    # Scan for PDF files
    print(f"🔍 Scanning {DATA_DIR} for PDF files...")
    pdf_files = get_pdf_files(DATA_DIR)
    print(f"Found {len(pdf_files)} PDF files.")
    
    if not pdf_files:
        print("No PDF files found. Exiting.")
        return
    
    # Load embedding model
    print(f"🤖 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL, device='mps')
    
    # Initialize Pinecone
    print(f"🔑 Initializing Pinecone...")
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    
    if INDEX_NAME not in pc.list_indexes().names():
        print(f"❌ Index {INDEX_NAME} not found. Please run the database setup first.")
        return
    
    index = pc.Index(INDEX_NAME)
    
    # Generate chunks from all PDFs
    all_chunks = []
    for pdf_path in pdf_files:
        print(f"\n📄 Chunking: {os.path.basename(pdf_path)}")
        try:
            chunks = chunk_pdf(pdf_path, ocr=False, window_tokens=CHUNK_WINDOW, overlap_tokens=CHUNK_OVERLAP)
            print(f"  → {len(chunks)} chunks generated.")
            
            # Add unique IDs and metadata
            for i, chunk in enumerate(chunks):
                chunk['id'] = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_chunk_{i+1}"
                chunk['metadata']['chunk_type'] = 'pdf'
                chunk['metadata']['source'] = 'document'
                chunk['metadata']['file_name'] = os.path.basename(pdf_path)
            
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"  ❌ Error chunking {pdf_path}: {e}")
    
    print(f"\n🧮 Total chunks to index: {len(all_chunks)}")
    if not all_chunks:
        print("No chunks to index. Exiting.")
        return
    
    # Create embeddings
    print(f"🔗 Generating embeddings...")
    texts = [chunk['text'] for chunk in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    
    # Prepare vectors for Pinecone
    vectors = []
    for chunk, embedding in zip(all_chunks, embeddings):
        vector_data = {
            'id': chunk['id'],
            'values': embedding.tolist(),
            'metadata': chunk['metadata']
        }
        vectors.append(vector_data)
    
    # Upload in batches
    batch_size = 100
    total_vectors = len(vectors)
    print(f"\n📤 Uploading {total_vectors} vectors to Pinecone (namespace: {NAMESPACE})...")
    
    uploaded = 0
    for i in range(0, total_vectors, batch_size):
        batch = vectors[i:i + batch_size]
        batch_num = i // batch_size + 1
        total_batches = (total_vectors + batch_size - 1) // batch_size
        
        print(f"📦 Uploading batch {batch_num}/{total_batches} ({len(batch)} vectors)...")
        try:
            index.upsert(vectors=batch, namespace=NAMESPACE)
            uploaded += len(batch)
            print(f"✅ Batch {batch_num} uploaded successfully")
        except Exception as e:
            print(f"❌ Error uploading batch {batch_num}: {e}")
            sys.exit(1)
    
    print(f"\n🎉 Document chunk restoration completed!")
    print(f"📁 Index: {INDEX_NAME}")
    print(f"🏷️  Namespace: {NAMESPACE}")
    print(f"📊 Total vectors uploaded: {uploaded}")
    print(f"📄 PDF files processed: {len(pdf_files)}")
    
    # Verify upload
    print("\n🔍 Verifying upload...")
    try:
        stats = index.describe_index_stats()
        if NAMESPACE in stats.namespaces:
            namespace_stats = stats.namespaces[NAMESPACE]
            vector_count = namespace_stats.vector_count
            print(f"✅ Namespace '{NAMESPACE}' contains {vector_count} vectors")
        else:
            print(f"⚠️  Namespace '{NAMESPACE}' not found in index stats")
        
        print("\n📊 Index Statistics:")
        for namespace, stats in stats.namespaces.items():
            print(f"  - {namespace}: {stats.vector_count} vectors")
    except Exception as e:
        print(f"⚠️  Warning: Could not verify upload: {e}")

if __name__ == "__main__":
    main() 
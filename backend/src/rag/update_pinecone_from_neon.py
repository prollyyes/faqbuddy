#!/usr/bin/env python3
"""
Update Pinecone Database from Neon Database
This script updates Pinecone with fresh database chunks from the Neon database.
It performs a delete and reindex operation for the 'db' namespace.
"""

import os
import sys
import time
import json
import datetime
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from .utils.generate_chunks import ChunkGenerator

# Load environment variables
load_dotenv()

# Configuration
INDEX_NAME = "exams-index-enhanced"
DB_NAMESPACE = "db"  # Dedicated namespace for database chunks
EMBEDDING_MODEL = "all-mpnet-base-v2"
BATCH_SIZE = 100

def log_debug(step, message, data=None):
    """Log debug information to file and console."""
    log_entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "step": step,
        "message": message,
    }
    if data is not None:
        log_entry["data"] = data
    
    # Write to debug file
    try:
        with open("debugging_pinecone.json", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        print(f"[DEBUG LOGGING ERROR] {e}")
    
    # Also print to console for immediate feedback
    print(f"[{step}] {message}")

def check_environment():
    """Check if all required environment variables are set."""
    step = "check_environment"
    log_debug(step, "Checking environment variables...")
    
    required_vars = [
        "PINECONE_API_KEY", 
        "DB_NAME", 
        "DB_USER", 
        "DB_PASSWORD", 
        "DB_HOST", 
        "DB_PORT"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        log_debug(step, f"Missing environment variables: {missing_vars}")
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please check your .env file")
        sys.exit(1)
    
    log_debug(step, "Environment variables loaded successfully.")
    print("✅ Environment variables loaded")

def initialize_pinecone():
    """Initialize Pinecone client and ensure index exists with correct configuration."""
    step = "initialize_pinecone"
    log_debug(step, "Initializing Pinecone...")
    
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        log_debug(step, "Pinecone client created.")
        
        # Check if index exists
        if INDEX_NAME not in pc.list_indexes().names():
            log_debug(step, f"Creating new Pinecone index: {INDEX_NAME}")
            pc.create_index(
                name=INDEX_NAME,
                dimension=768,  # all-mpnet-base-v2 dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            log_debug(step, "Waiting for index to be ready...")
            time.sleep(10)
            print(f"✅ Created new index: {INDEX_NAME}")
        else:
            log_debug(step, f"Index {INDEX_NAME} already exists.")
            print(f"✅ Index {INDEX_NAME} already exists")
            
            # Check if the existing index has the correct dimension
            try:
                index = pc.Index(INDEX_NAME)
                stats = index.describe_index_stats()
                log_debug(step, f"Existing index dimension: {stats.dimension}")
                
                if stats.dimension != 768:
                    log_debug(step, f"Dimension mismatch: index has {stats.dimension}, need 768. Deleting and recreating index.")
                    print(f"⚠️  Dimension mismatch detected. Deleting and recreating index...")
                    pc.delete_index(INDEX_NAME)
                    time.sleep(5)  # Wait for deletion
                    
                    pc.create_index(
                        name=INDEX_NAME,
                        dimension=768,
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region="us-east-1"
                        )
                    )
                    log_debug(step, "New index created with correct dimension.")
                    time.sleep(10)  # Wait for index to be ready
                    print("✅ Index recreated with correct dimension")
            except Exception as e:
                log_debug(step, f"Error checking index dimension: {e}")
                print(f"⚠️  Could not verify index dimension: {e}")
        
        log_debug(step, "Returning Pinecone index object.")
        return pc.Index(INDEX_NAME)
        
    except Exception as e:
        log_debug(step, f"Error initializing Pinecone: {e}")
        print(f"❌ Error initializing Pinecone: {e}")
        sys.exit(1)

def clear_db_namespace(index):
    """Clear all vectors from the 'db' namespace."""
    step = "clear_db_namespace"
    log_debug(step, f"Clearing namespace '{DB_NAMESPACE}'...")
    
    try:
        # Get current stats to show what we're clearing
        stats = index.describe_index_stats()
        if DB_NAMESPACE in stats.namespaces:
            vector_count = stats.namespaces[DB_NAMESPACE].vector_count
            log_debug(step, f"Found {vector_count} vectors in namespace '{DB_NAMESPACE}'")
            print(f"🗑️  Clearing {vector_count} vectors from namespace '{DB_NAMESPACE}'...")
        else:
            log_debug(step, f"No vectors found in namespace '{DB_NAMESPACE}'")
            print(f"🗑️  No vectors found in namespace '{DB_NAMESPACE}'")
        
        index.delete(namespace=DB_NAMESPACE, delete_all=True)
        log_debug(step, f"Cleared namespace '{DB_NAMESPACE}'")
        print(f"✅ Cleared namespace '{DB_NAMESPACE}'")
        
    except Exception as e:
        log_debug(step, f"Could not clear namespace: {e}")
        print(f"⚠️  Warning: Could not clear namespace: {e}")
        print("Continuing anyway...")

def generate_db_chunks():
    """Generate chunks from the Neon database."""
    step = "generate_db_chunks"
    log_debug(step, "Generating database chunks from Neon...")
    
    try:
        generator = ChunkGenerator()
        log_debug(step, "ChunkGenerator instantiated.")
        chunks = generator.get_chunks()
        log_debug(step, f"Generated {len(chunks)} database chunks.", data={"num_chunks": len(chunks)})
        print(f"✅ Generated {len(chunks)} database chunks from Neon")
        return chunks
        
    except Exception as e:
        log_debug(step, f"Error generating chunks: {e}")
        print(f"❌ Error generating chunks: {e}")
        sys.exit(1)

def create_embeddings(chunks, model):
    """Create embeddings for the chunks using the specified model."""
    step = "create_embeddings"
    log_debug(step, f"Creating embeddings for {len(chunks)} chunks...")
    
    try:
        texts = [chunk['text'] for chunk in chunks]
        log_debug(step, "Encoding texts with model.")
        
        # Show progress
        print(f"🤖 Creating embeddings with {EMBEDDING_MODEL}...")
        embeddings = model.encode(texts, show_progress_bar=True)
        log_debug(step, "Embeddings created.")
        
        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            vector_data = {
                'id': chunk['id'],
                'values': embedding.tolist(),
                'metadata': {
                    'text': chunk['text'],
                    'source': 'database',
                    **chunk['metadata']
                }
            }
            vectors.append(vector_data)
        
        log_debug(step, f"Prepared {len(vectors)} vectors for Pinecone upload.")
        print(f"✅ Created {len(vectors)} embeddings")
        return vectors
        
    except Exception as e:
        log_debug(step, f"Error creating embeddings: {e}")
        print(f"❌ Error creating embeddings: {e}")
        sys.exit(1)

def upload_to_pinecone(vectors, index):
    """Upload vectors to Pinecone in batches."""
    step = "upload_to_pinecone"
    log_debug(step, f"Uploading {len(vectors)} vectors to namespace '{DB_NAMESPACE}'...")
    
    total_vectors = len(vectors)
    uploaded = 0
    
    for i in range(0, total_vectors, BATCH_SIZE):
        batch = vectors[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        total_batches = (total_vectors + BATCH_SIZE - 1) // BATCH_SIZE
        
        log_debug(step, f"Uploading batch {batch_num}/{total_batches} ({len(batch)} vectors)...")
        
        try:
            index.upsert(vectors=batch, namespace=DB_NAMESPACE)
            uploaded += len(batch)
            log_debug(step, f"Batch {batch_num} uploaded successfully.")
            print(f"✅ Batch {batch_num}/{total_batches} uploaded ({uploaded}/{total_vectors} vectors)")
            
        except Exception as e:
            log_debug(step, f"Error uploading batch {batch_num}: {e}")
            print(f"❌ Error uploading batch {batch_num}: {e}")
            sys.exit(1)
    
    log_debug(step, f"Successfully uploaded {uploaded} vectors to namespace '{DB_NAMESPACE}'")
    print(f"🎉 Successfully uploaded {uploaded} vectors to namespace '{DB_NAMESPACE}'")

def verify_upload(index):
    """Verify the upload by checking index statistics."""
    step = "verify_upload"
    log_debug(step, "Verifying upload...")
    
    try:
        stats = index.describe_index_stats()
        log_debug(step, f"Index stats: {stats}")
        
        if DB_NAMESPACE in stats.namespaces:
            namespace_stats = stats.namespaces[DB_NAMESPACE]
            vector_count = namespace_stats.vector_count
            log_debug(step, f"Namespace '{DB_NAMESPACE}' contains {vector_count} vectors.")
            print(f"✅ Namespace '{DB_NAMESPACE}' contains {vector_count} vectors")
        else:
            log_debug(step, f"Namespace '{DB_NAMESPACE}' not found in index stats.")
            print(f"⚠️  Namespace '{DB_NAMESPACE}' not found in index stats")
        
        print("\n📊 Index Statistics:")
        for namespace, stats in stats.namespaces.items():
            print(f"  - {namespace}: {stats.vector_count} vectors")
            
    except Exception as e:
        log_debug(step, f"Could not verify upload: {e}")
        print(f"⚠️  Warning: Could not verify upload: {e}")

def main():
    """Main function to orchestrate the Pinecone update process."""
    log_debug("main", "Starting Pinecone Database Update from Neon")
    print("🚀 Starting Pinecone Database Update from Neon")
    print("=" * 60)
    
    # Step 1: Check environment
    check_environment()
    log_debug("main", "Environment checked.")
    
    # Step 2: Initialize Pinecone
    index = initialize_pinecone()
    log_debug("main", "Pinecone initialized.")
    
    # Step 3: Clear existing database namespace
    clear_db_namespace(index)
    log_debug("main", "Namespace cleared.")
    
    # Step 4: Generate chunks from Neon database
    chunks = generate_db_chunks()
    log_debug("main", f"Generated {len(chunks)} chunks.")
    
    if not chunks:
        log_debug("main", "No chunks generated. Exiting.")
        print("⚠️  No chunks generated. Exiting.")
        return
    
    # Step 5: Load embedding model
    print(f"🤖 Loading embedding model: {EMBEDDING_MODEL}")
    log_debug("main", f"Loading embedding model: {EMBEDDING_MODEL}")
    
    try:
        model = SentenceTransformer(EMBEDDING_MODEL, device='mps')
        log_debug("main", "Embedding model loaded.")
    except Exception as e:
        print(f"⚠️  Could not use MPS device, falling back to CPU: {e}")
        model = SentenceTransformer(EMBEDDING_MODEL)
        log_debug("main", "Embedding model loaded on CPU.")
    
    # Step 6: Create embeddings
    vectors = create_embeddings(chunks, model)
    log_debug("main", f"Created {len(vectors)} vectors.")
    
    # Step 7: Upload to Pinecone
    upload_to_pinecone(vectors, index)
    log_debug("main", "Vectors uploaded to Pinecone.")
    
    # Step 8: Verify upload
    verify_upload(index)
    log_debug("main", "Upload verified.")
    
    print("=" * 60)
    print("🎉 Pinecone database update completed successfully!")
    print(f"📊 Database chunks uploaded to namespace: '{DB_NAMESPACE}'")
    print("💡 Your RAG system is now ready with fresh database data from Neon!")
    log_debug("main", "Pinecone database update completed successfully!")

if __name__ == "__main__":
    main() 
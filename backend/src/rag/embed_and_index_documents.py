import os
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from .utils.pdf_chunker import chunk_pdf

# Config
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
INDEX_NAME = "exams-index-enhanced"
NAMESPACE = "documents"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_WINDOW = 200
CHUNK_OVERLAP = 50
PINECONE_ENV = "us-east-1" 


def get_pdf_files(data_dir):
    return [os.path.join(data_dir, f) for f in os.listdir(data_dir)
            if f.lower().endswith('.pdf') and os.path.isfile(os.path.join(data_dir, f))]

def main():
    load_dotenv()
    print(f"🔍 Scanning {DATA_DIR} for PDF files...")
    pdf_files = get_pdf_files(DATA_DIR)
    print(f"Found {len(pdf_files)} PDF files.")
    if not pdf_files:
        print("No PDF files found. Exiting.")
        return

    print(f"🚀 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"🔑 Initializing Pinecone...")
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    if INDEX_NAME not in pc.list_indexes().names():
        print(f"🔨 Creating new Pinecone index: {INDEX_NAME}")
        pc.create_index(
            name=INDEX_NAME,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        time.sleep(10)
    index = pc.Index(INDEX_NAME)

    all_chunks = []
    for pdf_path in pdf_files:
        print(f"\n📄 Chunking: {os.path.basename(pdf_path)}")
        try:
            chunks = chunk_pdf(pdf_path, ocr=False, window_tokens=CHUNK_WINDOW, overlap_tokens=CHUNK_OVERLAP)
            print(f"  → {len(chunks)} chunks generated.")
            # Add unique IDs and chunk_type
            for i, chunk in enumerate(chunks):
                chunk['id'] = f"{os.path.splitext(os.path.basename(pdf_path))[0]}_chunk_{i+1}"
                chunk['metadata']['chunk_type'] = 'pdf'
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"  ❌ Error chunking {pdf_path}: {e}")

    print(f"\n🧮 Total chunks to index: {len(all_chunks)}")
    if not all_chunks:
        print("No chunks to index. Exiting.")
        return

    # Prepare vectors as tuples (id, values, metadata)
    print(f"🔗 Generating embeddings...")
    texts = [chunk['text'] for chunk in all_chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    vectors_to_upsert = [
        (chunk['id'], embedding.tolist(), chunk['metadata'])
        for chunk, embedding in zip(all_chunks, embeddings)
    ]

    # Upload in batches
    batch_size = 100
    total_vectors = len(vectors_to_upsert)
    print(f"\n📤 Uploading {total_vectors} vectors to Pinecone (namespace: {NAMESPACE})...")
    for i in range(0, total_vectors, batch_size):
        batch = vectors_to_upsert[i:i + batch_size]
        print(f"Uploading batch {i//batch_size + 1}/{(total_vectors + batch_size - 1)//batch_size}")
        try:
            index.upsert(vectors=batch, namespace=NAMESPACE)
            print(f"✅ Batch {i//batch_size + 1} uploaded successfully")
        except Exception as e:
            print(f"❌ Error uploading batch {i//batch_size + 1}: {e}")
    print(f"\n🎉 Document chunk indexing completed!")
    print(f"📁 Index: {INDEX_NAME}")
    print(f"🏷️  Namespace: {NAMESPACE}")
    print(f"📊 Total vectors uploaded: {total_vectors}")

if __name__ == "__main__":
    main() 
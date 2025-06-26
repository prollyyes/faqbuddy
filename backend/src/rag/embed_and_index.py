import os
from dotenv import load_dotenv
from src.rag.utils.embeddings import embed_texts
from src.rag.utils.vector_db import upsert_vectors, NAMESPACE
from src.rag.utils.generate_chunks import get_chunks

load_dotenv()

def embed_and_index():
    chunks = get_chunks()
    print(f"✅ Loaded {len(chunks)} chunks from DB.")

    embeddings = embed_texts(chunks)
    print("✅ Embeddings generated.")

    items_to_upsert = [
        {
            "id": f"chunk-{i}",
            "values": vec.tolist(),
            "metadata": {"text": text}
        }
        for i, (vec, text) in enumerate(zip(embeddings, chunks))
    ]

    upsert_vectors(items_to_upsert, namespace=NAMESPACE)
    print(f"✅ Chunks indexed in Pinecone (namespace='{NAMESPACE}').")

if __name__ == "__main__":
    embed_and_index()
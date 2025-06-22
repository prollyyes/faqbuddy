import os
from dotenv import load_dotenv
from src.rag.utils.embeddings import embed_texts
from src.rag.utils.vector_db import upsert_vectors
from src.rag.utils.generate_chunks import get_chunks

load_dotenv()

def embed_and_index():
    # Returns a list of dictionaries, where each dict has 'id', 'text', and 'metadata'
    documents = get_chunks()
    print(f"✅ Loaded {len(documents)} structured documents from the database.")

    # Extract the text from each document to be embedded
    texts_to_embed = [doc['text'] for doc in documents]
    
    # Generate embeddings for the texts
    embeddings = embed_texts(texts_to_embed)
    print("✅ Embeddings generated.")

    # Prepare documents for upserting, now with rich metadata
    items_to_upsert = []
    for doc, vec in zip(documents, embeddings):
        item = {
            "id": doc['id'],
            "values": vec.tolist(),
            "metadata": {
                "text": doc['text'],
                **doc['metadata']  # Adds table_name and primary_key
            }
        }
        items_to_upsert.append(item)

    # Upsert the structured data into Pinecone
    upsert_vectors(items_to_upsert, namespace="v6")
    print("✅ Documents indexed in Pinecone with structured metadata (namespace='v6').")

if __name__ == "__main__":
    embed_and_index()
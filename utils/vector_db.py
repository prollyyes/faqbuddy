# utils/vector_db.py

from pinecone import Pinecone
from utils.embeddings import embed_texts
from typing import List
from dotenv import load_dotenv
import os
# Constants for Pinecone index
INDEX_NAME = "exams-index"
NAMESPACE = "v2"

load_dotenv()  # Load environment variables from .env file  


# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(INDEX_NAME)

def query_vector_db(query: str, top_k: int = 5) -> List[dict]:
    """
    Queries Pinecone using the embedding of a given string.

    Args:
        query: The query string to embed and search.
        top_k: Number of top results to return.

    Returns:
        List of Pinecone match dictionaries.
    """
    print(f"🔍 Querying Pinecone with: {query}")
    embedding = embed_texts([query])[0].tolist()
    response = index.query(
        namespace=NAMESPACE,
        vector=embedding,
        top_k=top_k,
        include_metadata=True
    )
    print(f"✅ Matches: {len(response.matches)}")
    return [match.metadata.get("text", "") for match in response.matches]


# Upsert function for Pinecone vectors
def upsert_vectors(vectors: List[dict], namespace: str = NAMESPACE):
    """
    Upserts a list of vectors into the Pinecone index.

    Args:
        vectors: List of dictionaries with 'id', 'values', and optional 'metadata'.
        namespace: Namespace in Pinecone where the vectors will be stored.
    """
    print(f"📦 Upserting {len(vectors)} vectors to namespace '{namespace}'")
    index.upsert(vectors=vectors, namespace=namespace)
    print("✅ Upsert complete.")
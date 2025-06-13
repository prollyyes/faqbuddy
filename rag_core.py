import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import torch
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
import numpy as np
from utils.local_llm import generate_answer
import time

class RAGSystem:
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 index_name: str = "exams-index",
                 namespace: str = "v2",
                 dimension: int = 384):
        """
        Initialize the RAG system with embedding model and vector store.
        
        Args:
            model_name: Name of the sentence transformer model to use
            index_name: Name of the Pinecone index
            namespace: Namespace in Pinecone where vectors are stored
            dimension: Dimension of the embeddings
        """
        load_dotenv()
        
        # Initialize embedding model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=self.device)
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(index_name)
        self.namespace = namespace
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for a single text."""
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        return self.model.encode(texts).tolist()
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of dicts with 'id', 'text', and optional 'metadata'
        """
        vectors = []
        for doc in documents:
            vector = {
                "id": doc["id"],
                "values": self.embed_text(doc["text"]),
                "metadata": {"text": doc["text"], **doc.get("metadata", {})}
            }
            vectors.append(vector)
        
        # Upsert in batches of 100
        for i in range(0, len(vectors), 100):
            batch = vectors[i:i + 100]
            self.index.upsert(vectors=batch, namespace=self.namespace)
    
    def query(self, 
             query_text: str, 
             top_k: int = 5,
             filter: Dict = None) -> List[Dict[str, Any]]:
        """
        Query the vector store for similar documents.
        
        Args:
            query_text: The query text
            top_k: Number of results to return
            filter: Optional metadata filter
            
        Returns:
            List of dictionaries containing matched documents and their metadata
        """
        query_vector = self.embed_text(query_text)
        results = self.index.query(
            namespace=self.namespace,
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        
        return results.matches

    def generate_response(self, 
                         query: str, 
                         top_k: int = 5,
                         filter: Dict = None) -> Dict[str, Any]:
        """
        Generate a response using the RAG pipeline.
        
        Args:
            query: The user's question
            top_k: Number of relevant documents to retrieve
            filter: Optional metadata filter
            
        Returns:
            Dictionary containing the response and timing information
        """
        start_time = time.time()
        
        # Step 1: Retrieve relevant documents
        retrieval_start = time.time()
        matches = self.query(query, top_k=top_k, filter=filter)
        retrieval_time = time.time() - retrieval_start
        
        if not matches:
            return {
                "response": "I couldn't find any relevant information to answer your question.",
                "retrieval_time": retrieval_time,
                "generation_time": 0,
                "total_time": time.time() - start_time,
                "context_used": []
            }
        
        # Step 2: Prepare context
        context = "\n\n".join([match.metadata.get("text", "") for match in matches])
        
        # Step 3: Generate response
        generation_start = time.time()
        response = generate_answer(context, query)
        generation_time = time.time() - generation_start
        
        return {
            "response": response,
            "retrieval_time": retrieval_time,
            "generation_time": generation_time,
            "total_time": time.time() - start_time,
            "context_used": [match.metadata.get("text", "") for match in matches]
        }

def main():
    """Example usage of the RAG system."""
    # Initialize RAG system
    rag = RAGSystem()
    
    # Example query
    query = "What exams were given by Professor Smith in 2023?"
    result = rag.generate_response(query)
    
    print(f"\nQuery: {query}")
    print(f"\nResponse: {result['response']}")
    print(f"\nTiming:")
    print(f"Retrieval time: {result['retrieval_time']:.2f}s")
    print(f"Generation time: {result['generation_time']:.2f}s")
    print(f"Total time: {result['total_time']:.2f}s")
    
    print("\nContext used:")
    for i, context in enumerate(result['context_used'], 1):
        print(f"\n{i}. {context}")

if __name__ == "__main__":
    main() 
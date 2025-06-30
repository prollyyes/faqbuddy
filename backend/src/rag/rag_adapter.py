"""
RAG Adapter for FAQBuddy Main API
This adapter wraps the RAGPipeline to provide the interface expected by main.py
"""

import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .rag_pipeline import RAGPipeline
from .hybrid_retrieval import determine_namespace_boost
from typing import Generator, Dict, Any

class RAGSystem:
    """
    Adapter class that wraps RAGPipeline to provide the interface expected by main.py
    """
    
    def __init__(self):
        """Initialize the RAG system with the pipeline."""
        self.pipeline = RAGPipeline()
        print("[RAGSystem] Initialized with RAGPipeline adapter")
    
    def generate_response(self, question: str) -> dict:
        """
        Generate a response using the RAG pipeline.
        Returns a dictionary with timing information and response details.
        """
        start_time = time.time()
        
        # Track retrieval time
        retrieval_start = time.time()
        
        # Get namespace boost information for context
        docs_boost, db_boost = determine_namespace_boost(question)
        
        # Generate the answer using the pipeline
        answer = self.pipeline.answer(question)
        
        retrieval_time = time.time() - retrieval_start
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Estimate generation time as the remaining time
        generation_time = total_time - retrieval_time
        
        # Create detailed context information
        context_info = {
            "namespace_boosts": {
                "documents": docs_boost,
                "database": db_boost
            },
            "pipeline_used": "hybrid_retrieval",
            "model": "mistral",
            "retrieval_method": "hybrid_dense_sparse",
            "reranking": "cross_encoder",
            "namespaces_searched": ["documents", "db"]
        }
        
        return {
            "response": answer,
            "retrieval_time": round(retrieval_time, 3),
            "generation_time": round(generation_time, 3),
            "total_time": round(total_time, 3),
            "context_used": context_info
        }

    def generate_response_streaming(self, question: str) -> Generator[str, None, None]:
        """
        Generate a streaming response using the RAG pipeline.
        Yields tokens as they are generated for reduced perceived latency.
        """
        # Get namespace boost information for context
        docs_boost, db_boost = determine_namespace_boost(question)
        
        # Generate the streaming answer using the pipeline
        for token in self.pipeline.answer_streaming(question):
            yield token

    def generate_response_streaming_with_metadata(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generate a streaming response with metadata using the RAG pipeline.
        Yields dictionaries with tokens and metadata for enhanced client experience.
        """
        # Get namespace boost information for context
        docs_boost, db_boost = determine_namespace_boost(question)
        
        # Generate the streaming answer with metadata using the pipeline
        for chunk in self.pipeline.answer_streaming_with_metadata(question):
            # Add adapter-specific metadata
            if chunk["type"] == "metadata":
                chunk.update({
                    "namespace_boosts": {
                        "documents": docs_boost,
                        "database": db_boost
                    },
                    "pipeline_used": "hybrid_retrieval",
                    "model": "mistral",
                    "retrieval_method": "hybrid_dense_sparse",
                    "reranking": "cross_encoder",
                    "namespaces_searched": ["documents", "db"]
                })
            yield chunk
    
    def get_system_info(self) -> dict:
        """Get information about the RAG system configuration."""
        return {
            "system_type": "hybrid_rag",
            "embedding_model": "all-mpnet-base-v2",
            "llm_model": "mistral",
            "namespaces": ["documents", "db"],
            "features": [
                "namespace_aware_retrieval",
                "hybrid_search",
                "cross_encoder_reranking",
                "dynamic_boost_calculation",
                "streaming_response"
            ]
        } 
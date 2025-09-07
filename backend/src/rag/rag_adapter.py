"""
RAG Adapter for FAQBuddy Main API
This adapter wraps the RAGv2Pipeline to provide the interface expected by main.py
"""

import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .rag_pipeline_v2 import RAGv2Pipeline
from .advanced_rag_pipeline import AdvancedRAGPipeline # new pipeline introduced in RAGv3
from typing import Generator, Dict, Any

class RAGSystem:
    """
    Adapter class that wraps RAGv2Pipeline to provide the interface expected by main.py
    """
    
    def __init__(self):
        """Initialize the RAG system with the Advanced RAG pipeline."""
        self.pipeline = AdvancedRAGPipeline()
        print("[RAGSystem] Initialized with AdvancedRAGPipeline adapter")
    
    def generate_response(self, question: str) -> dict:
        """
        Generate a response using the Advanced RAG pipeline.
        Returns a dictionary with timing information and response details.
        """
        start_time = time.time()
        
        # Generate the answer using the Advanced RAG pipeline
        result = self.pipeline.answer(question)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Extract information from Advanced RAG result
        answer = result.answer
        sources = result.retrieval_results  # AdvancedRAGResult uses retrieval_results instead of sources
        confidence = result.confidence_score
        
        # Count sources by namespace
        namespace_counts = {}
        for source in sources:
            namespace = source.get('namespace', 'unknown')
            namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
        
        # Create detailed context information
        context_info = {
            "pipeline_used": "advanced_rag",
            "model": "mistral",
            "retrieval_method": "enhanced_retrieval_v2",
            "reranking": "cross_encoder",
            "namespaces_searched": list(namespace_counts.keys()),
            "namespace_counts": namespace_counts,
            "total_sources": len(sources),
            "features_used": result.features_used,
            "confidence_score": confidence,
            "query_analysis": result.query_analysis.__dict__ if hasattr(result, 'query_analysis') else {}
        }
        
        return {
            "response": answer,
            "retrieval_time": round(total_time * 0.6, 3),  # Estimate 60% for retrieval
            "generation_time": round(total_time * 0.4, 3),  # Estimate 40% for generation
            "total_time": round(total_time, 3),
            "context_used": context_info,
            "sources": sources,
            "confidence_score": confidence
        }

    def generate_response_streaming(self, question: str) -> Generator[str, None, None]:
        """
        Generate a streaming response using the RAGv2 pipeline.
        Yields tokens as they are generated for reduced perceived latency.
        """
        # Generate the streaming answer using the RAGv2 pipeline
        for token in self.pipeline.answer_streaming(question):
            yield token

    def generate_response_streaming_with_metadata(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generate a streaming response with metadata using the RAGv2 pipeline.
        Yields dictionaries with tokens and metadata for enhanced client experience.
        """
        # Generate the streaming answer with metadata using the RAGv2 pipeline
        for chunk in self.pipeline.answer_streaming_with_metadata(question):
            # Add adapter-specific metadata for RAGv2
            if chunk.get("type") == "metadata":
                chunk.update({
                    "pipeline_used": "ragv2_enhanced",
                    "model": "mistral",
                    "retrieval_method": "enhanced_retrieval_v2",
                    "reranking": "cross_encoder",
                    "features_used": {
                        "schema_aware_chunking": True,
                        "instructor_xl_embeddings": True,
                        "reranker_enabled": True,
                        "web_search_enhancement": True
                    }
                })
            yield chunk
    
    def get_system_info(self) -> dict:
        """Get information about the Advanced RAG system configuration."""
        return {
            "system_type": "advanced_rag",
            "embedding_model": "all-mpnet-base-v2",
            "llm_model": "mistral",
            "namespaces": ["pdf_v2", "per_row", "web_search"],
            "features": [
                "query_understanding",
                "advanced_prompt_engineering",
                "chain_of_thought_reasoning",
                "self_verification",
                "source_attribution",
                "enhanced_retrieval_v2",
                "cross_encoder_reranking",
                "web_search_enhancement",
                "answer_verification",
                "hallucination_detection",
                "confidence_scoring"
            ]
        } 
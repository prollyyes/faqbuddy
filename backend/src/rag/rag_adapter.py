"""
Enhanced RAG Adapter for FAQBuddy Main API
==========================================

This adapter wraps the enhanced RAGPipeline to provide the interface expected by main.py
with improved performance monitoring and configuration management.
"""

import time
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.rag.rag_pipeline import RAGPipeline
from src.rag.rag_config import get_config, update_config
from src.rag.hybrid_retrieval import determine_namespace_boost, get_retrieval_stats
from src.utils.llm_mistral import get_llm_stats, test_llm_connection
from typing import Generator, Dict, Any, Optional

class RAGSystem:
    """
    Enhanced adapter class that wraps RAGPipeline to provide the interface expected by main.py
    with improved performance monitoring and configuration management.
    """
    
    def __init__(self, profile: str = "balanced", custom_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the RAG system with the pipeline.
        
        Args:
            profile: Configuration profile ("speed", "balanced", "quality")
            custom_config: Optional custom configuration overrides
        """
        # Get configuration
        if custom_config:
            self.config = update_config(custom_config, profile)
        else:
            self.config = get_config(profile)
        
        # Initialize pipeline with configuration
        self.pipeline = RAGPipeline(
            top_k=self.config["performance"]["top_k"]
        )
        
        self.profile = profile
        print(f"[RAGSystem] Initialized with {profile.upper()} profile")
        print(f"[RAGSystem] Configuration: top_k={self.config['performance']['top_k']}, alpha={self.config['retrieval']['alpha']}")
    
    def generate_response(self, question: str) -> dict:
        """
        Generate a response using the enhanced RAG pipeline.
        Returns a dictionary with timing information and response details.
        """
        start_time = time.time()
        
        try:
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
                "pipeline_used": "enhanced_hybrid_retrieval",
                "model": "mistral_optimized",
                "retrieval_method": "hybrid_dense_sparse",
                "reranking": "cross_encoder" if self.config["performance"]["use_cross_encoder"] else "none",
                "namespaces_searched": ["documents", "db"],
                "profile": self.profile,
                "config": {
                    "top_k": self.config["performance"]["top_k"],
                    "alpha": self.config["retrieval"]["alpha"],
                    "max_chunks": self.config["performance"]["max_chunks"],
                    "use_cross_encoder": self.config["performance"]["use_cross_encoder"]
                }
            }
            
            return {
                "response": answer,
                "retrieval_time": round(retrieval_time, 3),
                "generation_time": round(generation_time, 3),
                "total_time": round(total_time, 3),
                "context_used": context_info,
                "success": True
            }
            
        except Exception as e:
            total_time = time.time() - start_time
            return {
                "response": f"Mi dispiace, si è verificato un errore durante l'elaborazione della tua domanda. Errore: {str(e)}",
                "retrieval_time": 0,
                "generation_time": 0,
                "total_time": round(total_time, 3),
                "context_used": {"error": str(e)},
                "success": False
            }

    def generate_response_streaming(self, question: str) -> Generator[str, None, None]:
        """
        Generate a streaming response using the enhanced RAG pipeline.
        Yields tokens as they are generated for reduced perceived latency.
        """
        try:
            # Get namespace boost information for context
            docs_boost, db_boost = determine_namespace_boost(question)
            
            # Generate the streaming answer using the pipeline
            for token in self.pipeline.answer_streaming(question):
                yield token
                
        except Exception as e:
            yield f"Mi dispiace, si è verificato un errore durante l'elaborazione della tua domanda. Errore: {str(e)}"

    def generate_response_streaming_with_metadata(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generate a streaming response with metadata using the enhanced RAG pipeline.
        Yields dictionaries with tokens and metadata for enhanced client experience.
        """
        try:
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
                        "pipeline_used": "enhanced_hybrid_retrieval",
                        "model": "mistral_optimized",
                        "retrieval_method": "hybrid_dense_sparse",
                        "reranking": "cross_encoder" if self.config["performance"]["use_cross_encoder"] else "none",
                        "namespaces_searched": ["documents", "db"],
                        "profile": self.profile,
                        "config": {
                            "top_k": self.config["performance"]["top_k"],
                            "alpha": self.config["retrieval"]["alpha"],
                            "max_chunks": self.config["performance"]["max_chunks"],
                            "use_cross_encoder": self.config["performance"]["use_cross_encoder"]
                        }
                    })
                yield chunk
                
        except Exception as e:
            yield {
                "type": "error",
                "content": f"Mi dispiace, si è verificato un errore durante l'elaborazione della tua domanda. Errore: {str(e)}",
                "error": str(e)
            }
    
    def get_system_info(self) -> dict:
        """Get comprehensive information about the RAG system configuration."""
        # Get component stats
        pipeline_stats = self.pipeline.get_stats()
        retrieval_stats = get_retrieval_stats()
        llm_stats = get_llm_stats()
        llm_test = test_llm_connection()
        
        return {
            "system_type": "enhanced_hybrid_rag",
            "profile": self.profile,
            "embedding_model": self.config["retrieval"]["embedding_model"],
            "llm_model": "mistral_optimized",
            "namespaces": ["documents", "db"],
            "features": [
                "namespace_aware_retrieval",
                "enhanced_hybrid_search",
                "cross_encoder_reranking" if self.config["performance"]["use_cross_encoder"] else "basic_reranking",
                "dynamic_boost_calculation",
                "streaming_response",
                "performance_monitoring",
                "configuration_profiles"
            ],
            "configuration": {
                "top_k": self.config["performance"]["top_k"],
                "alpha": self.config["retrieval"]["alpha"],
                "max_chunks": self.config["performance"]["max_chunks"],
                "use_cross_encoder": self.config["performance"]["use_cross_encoder"],
                "cache_size": self.config["performance"]["cache_size"]
            },
            "performance": pipeline_stats,
            "retrieval_system": retrieval_stats,
            "llm_system": {
                "stats": llm_stats,
                "connection_test": llm_test
            }
        }
    
    def test_retrieval(self, question: str) -> Dict[str, Any]:
        """
        Test retrieval components without generation for debugging.
        """
        try:
            retrieval_test = self.pipeline.test_retrieval(question)
            
            # Add configuration information
            retrieval_test.update({
                "profile": self.profile,
                "config": {
                    "top_k": self.config["performance"]["top_k"],
                    "alpha": self.config["retrieval"]["alpha"],
                    "use_cross_encoder": self.config["performance"]["use_cross_encoder"]
                }
            })
            
            return retrieval_test
            
        except Exception as e:
            return {
                "error": str(e),
                "profile": self.profile,
                "config": self.config["performance"]
            }
    
    def switch_profile(self, new_profile: str) -> Dict[str, Any]:
        """
        Switch to a different performance profile.
        
        Args:
            new_profile: New profile ("speed", "balanced", "quality")
        
        Returns:
            Dictionary with new configuration
        """
        try:
            # Get new configuration
            new_config = get_config(new_profile)
            
            # Update current configuration
            self.config = new_config
            self.profile = new_profile
            
            # Reinitialize pipeline with new settings
            self.pipeline = RAGPipeline(
                top_k=self.config["performance"]["top_k"]
            )
            
            return {
                "success": True,
                "new_profile": new_profile,
                "configuration": {
                    "top_k": self.config["performance"]["top_k"],
                    "alpha": self.config["retrieval"]["alpha"],
                    "max_chunks": self.config["performance"]["max_chunks"],
                    "use_cross_encoder": self.config["performance"]["use_cross_encoder"]
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "current_profile": self.profile
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.
        """
        pipeline_stats = self.pipeline.get_stats()
        retrieval_stats = get_retrieval_stats()
        
        return {
            "pipeline_stats": pipeline_stats,
            "retrieval_stats": retrieval_stats,
            "profile": self.profile,
            "configuration": {
                "top_k": self.config["performance"]["top_k"],
                "alpha": self.config["retrieval"]["alpha"],
                "max_chunks": self.config["performance"]["max_chunks"],
                "use_cross_encoder": self.config["performance"]["use_cross_encoder"]
            }
        }

def main():
    """Test the enhanced RAG adapter."""
    print("=== Testing Enhanced RAG Adapter ===")
    
    # Test different profiles
    for profile in ["speed", "balanced", "quality"]:
        print(f"\n--- Testing {profile.upper()} Profile ---")
        
        # Initialize adapter
        adapter = RAGSystem(profile=profile)
        
        # Test system info
        system_info = adapter.get_system_info()
        print(f"System Type: {system_info['system_type']}")
        print(f"Profile: {system_info['profile']}")
        print(f"Top K: {system_info['configuration']['top_k']}")
        print(f"Alpha: {system_info['configuration']['alpha']}")
        
        # Test retrieval
        test_question = "Quanti CFU ha il corso di Informatica?"
        retrieval_test = adapter.test_retrieval(test_question)
        print(f"Retrieval Test - Intent: {retrieval_test.get('intent', 'unknown')}")
        print(f"Retrieval Test - Results: {retrieval_test.get('merged_results_count', 0)}")
        
        # Test response generation
        response = adapter.generate_response(test_question)
        print(f"Response Time: {response['total_time']:.3f}s")
        print(f"Success: {response['success']}")
        
        # Test profile switching
        if profile == "balanced":
            switch_result = adapter.switch_profile("speed")
            print(f"Profile Switch: {switch_result['success']}")

if __name__ == "__main__":
    main() 
"""
RAGv2 Pipeline - Enhanced RAG System
====================================

This module implements the main RAGv2 pipeline that integrates all the new components:
- Task 1: Schema-aware chunking
- Task 2: Enhanced embeddings (instructor-xl)
- Task 3: Improved retrieval pipeline
- Task 4: Generation guard-rails
- Task 5: Observability

All features are controlled by feature flags for independent deployment.
"""

import time
import logging
from typing import Dict, Any, List, Optional, Generator
from pinecone import Pinecone
from dotenv import load_dotenv

from .config import (
    get_feature_flags, 
    is_feature_enabled,
    OBSERVABILITY_ENABLED
)
from .utils.schema_aware_chunker import SchemaAwareChunker
from .utils.embeddings_v2 import EnhancedEmbeddings
from .retrieval_v2 import EnhancedRetrieval
from .generation_guards import GenerationGuards
from .utils.generate_chunks import ChunkGenerator  # Legacy chunker for fallback

# Setup logging for observability
if OBSERVABILITY_ENABLED:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

class RAGv2Pipeline:
    """
    Enhanced RAG pipeline with all RAGv2 improvements.
    
    Features:
    - Schema-aware chunking (Task 1)
    - Enhanced embeddings with instructor-xl (Task 2)
    - Improved retrieval with cross-encoder reranking (Task 3)
    - Generation guard-rails (Task 5)
    - Comprehensive observability (Task 8)
    """
    
    def __init__(self, data_dir: str = None, top_k: int = 5):
        """
        Initialize the RAGv2 pipeline.
        
        Args:
            data_dir: Directory containing data files
            top_k: Number of top results to retrieve
        """
        load_dotenv()
        
        self.data_dir = data_dir
        self.top_k = top_k
        self.feature_flags = get_feature_flags()
        
        # Initialize components based on feature flags
        self._initialize_components()
        
        # Observability
        self.pipeline_stats = {
            "total_queries": 0,
            "total_time": 0,
            "average_time": 0,
            "feature_usage": {flag: 0 for flag in self.feature_flags.keys()}
        }
        
        print("🚀 RAGv2 Pipeline Initialized")
        print("📋 Active Features:")
        for flag, enabled in self.feature_flags.items():
            status = "✅" if enabled else "❌"
            print(f"   {status} {flag}")
    
    def _initialize_components(self):
        """Initialize pipeline components based on feature flags."""
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Initialize chunkers
        if is_feature_enabled("schema_aware_chunking"):
            self.schema_chunker = SchemaAwareChunker()
            print("✅ Schema-aware chunker initialized")
        else:
            self.schema_chunker = None
            print("❌ Schema-aware chunking disabled")
        
        # Initialize legacy chunker for fallback
        self.legacy_chunker = ChunkGenerator()
        
        # Initialize embeddings
        if is_feature_enabled("instructor_xl_embeddings"):
            self.embeddings = EnhancedEmbeddings()
            print("✅ Enhanced embeddings initialized")
        else:
            self.embeddings = None
            print("❌ Enhanced embeddings disabled")
        
        # Initialize retrieval
        self.retrieval = EnhancedRetrieval(self.pc)
        print("✅ Enhanced retrieval initialized")
        
        # Initialize generation guards
        if is_feature_enabled("hallucination_guards"):
            self.generation_guards = GenerationGuards()
            print("✅ Generation guards initialized")
        else:
            self.generation_guards = None
            print("❌ Generation guards disabled")
    
    def _get_chunks(self) -> List[Dict[str, Any]]:
        """Get chunks using appropriate chunker based on feature flags."""
        if is_feature_enabled("schema_aware_chunking") and self.schema_chunker:
            chunks = self.schema_chunker.get_all_chunks()
            if chunks:
                self.pipeline_stats["feature_usage"]["schema_aware_chunking"] += 1
                return chunks
        
        # Fallback to legacy chunker
        print("🔄 Using legacy chunker as fallback")
        chunks = self.legacy_chunker.get_chunks()
        return chunks
    
    def _log_query_start(self, question: str) -> Dict[str, Any]:
        """Log query start for observability."""
        query_id = f"query_{int(time.time() * 1000)}"
        
        if OBSERVABILITY_ENABLED:
            logger.info(f"Query started: {query_id} - {question}")
        
        return {
            "query_id": query_id,
            "question": question,
            "start_time": time.time(),
            "feature_flags": self.feature_flags.copy()
        }
    
    def _log_query_end(self, query_info: Dict[str, Any], result: Dict[str, Any]):
        """Log query completion for observability."""
        end_time = time.time()
        duration = end_time - query_info["start_time"]
        
        # Update pipeline stats
        self.pipeline_stats["total_queries"] += 1
        self.pipeline_stats["total_time"] += duration
        self.pipeline_stats["average_time"] = (
            self.pipeline_stats["total_time"] / self.pipeline_stats["total_queries"]
        )
        
        # Log feature usage
        for feature, used in result.get("features_used", {}).items():
            if used:
                self.pipeline_stats["feature_usage"][feature] += 1
        
        if OBSERVABILITY_ENABLED:
            logger.info(
                f"Query completed: {query_info['query_id']} - "
                f"Duration: {duration:.3f}s - "
                f"Features: {result.get('features_used', {})}"
            )
    
    def answer(self, question: str) -> Dict[str, Any]:
        """
        Generate answer using the enhanced RAG pipeline.
        
        Args:
            question: User question
            
        Returns:
            Dictionary containing answer and metadata
        """
        # Start query logging
        query_info = self._log_query_start(question)
        
        try:
            # Step 1: Get chunks
            chunks = self._get_chunks()
            
            # Step 2: Retrieve relevant documents
            retrieval_results = self.retrieval.retrieve(question, chunks)
            
            # Step 3: Generate answer with guards
            if is_feature_enabled("hallucination_guards") and self.generation_guards:
                generation_result = self.generation_guards.generate_safe_answer(
                    retrieval_results, question
                )
                answer = generation_result["answer"]
                verification_info = {
                    "verification_score": generation_result.get("verification_score"),
                    "is_verified": generation_result.get("is_verified"),
                    "refusal_reason": generation_result.get("refusal_reason")
                }
            else:
                # Fallback to simple generation
                from .build_prompt import build_prompt
                from ..utils.llm_mistral import generate_answer
                
                prompt = build_prompt(retrieval_results, question)
                answer = generate_answer(prompt, question)
                verification_info = {"guards_disabled": True}
            
            # Prepare result
            result = {
                "answer": answer,
                "retrieved_documents": len(retrieval_results),
                "retrieval_stats": self.retrieval.get_retrieval_stats(),
                "verification_info": verification_info,
                "features_used": {
                    "schema_aware_chunking": is_feature_enabled("schema_aware_chunking"),
                    "instructor_xl_embeddings": is_feature_enabled("instructor_xl_embeddings"),
                    "reranker_enabled": is_feature_enabled("reranker_enabled"),
                    "hallucination_guards": is_feature_enabled("hallucination_guards")
                },
                "query_id": query_info["query_id"]
            }
            
            # Log completion
            self._log_query_end(query_info, result)
            
            return result
            
        except Exception as e:
            error_msg = f"Error in RAGv2 pipeline: {str(e)}"
            if OBSERVABILITY_ENABLED:
                logger.error(error_msg, exc_info=True)
            
            # Log completion with error
            self._log_query_end(query_info, {"error": error_msg})
            
            return {
                "answer": "I encountered an error while processing your question. Please try again.",
                "error": error_msg,
                "query_id": query_info["query_id"]
            }
    
    def answer_streaming(self, question: str) -> Generator[str, None, None]:
        """
        Generate streaming answer (simplified version for now).
        
        Args:
            question: User question
            
        Yields:
            Answer tokens
        """
        result = self.answer(question)
        answer = result.get("answer", "")
        
        # Simple token streaming
        words = answer.split()
        for word in words:
            yield word + " "
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics."""
        stats = self.pipeline_stats.copy()
        
        # Add component-specific stats
        if self.retrieval:
            stats["retrieval_stats"] = self.retrieval.get_retrieval_stats()
        
        if self.generation_guards:
            stats["guard_stats"] = self.generation_guards.get_guard_stats()
        
        if self.embeddings:
            stats["embedding_stats"] = self.embeddings.get_model_info()
        
        return stats


def test_ragv2_pipeline():
    """Test the RAGv2 pipeline functionality."""
    print("🧪 Testing RAGv2 Pipeline...")
    
    # Initialize pipeline
    pipeline = RAGv2Pipeline()
    
    # Test question
    question = "Who teaches Operating Systems this semester?"
    
    # Generate answer
    result = pipeline.answer(question)
    
    print(f"✅ RAGv2 pipeline test completed")
    print(f"📊 Result: {result}")
    
    # Check required fields
    required_fields = ["answer", "retrieved_documents", "features_used", "query_id"]
    for field in required_fields:
        if field not in result:
            print(f"❌ Missing field: {field}")
            return False
    
    print("✅ All required fields present")
    
    # Check pipeline stats
    stats = pipeline.get_pipeline_stats()
    print(f"📈 Pipeline stats: {stats}")
    
    return True


if __name__ == "__main__":
    import os
    test_ragv2_pipeline() 
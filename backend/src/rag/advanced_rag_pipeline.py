"""
Advanced RAG Pipeline for State-of-the-Art Performance
=====================================================

This module implements a state-of-the-art RAG pipeline that integrates:
- Advanced query understanding
- Enhanced retrieval with query expansion
- Advanced prompt engineering
- Comprehensive answer verification
- Hallucination prevention
"""

import time
import sys
import os
from typing import Generator
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from .query_understanding import AdvancedQueryUnderstanding, QueryAnalysis
from .advanced_prompt_engineering import AdvancedPromptEngineer, PromptConfig
from .answer_verification import AdvancedAnswerVerification, VerificationResult
from .retrieval_v2_enhanced import EnhancedRetrievalV2
from .config import *
from utils.llm_mistral import generate_answer

@dataclass
class AdvancedRAGResult:
    """Result from the advanced RAG pipeline."""
    answer: str
    query_analysis: QueryAnalysis
    verification_result: VerificationResult
    retrieval_results: List[Dict[str, Any]]
    processing_time: float
    confidence_score: float
    features_used: Dict[str, bool]

class AdvancedRAGPipeline:
    """
    State-of-the-art RAG pipeline with advanced components.
    
    Features:
    - Query understanding and intent classification
    - Advanced retrieval with query expansion
    - Chain-of-thought prompt engineering
    - Comprehensive answer verification
    - Hallucination prevention
    """
    
    def __init__(self):
        """Initialize the advanced RAG pipeline."""
        print("🚀 Initializing Advanced RAG Pipeline")
        
        # Initialize components
        self.query_understanding = AdvancedQueryUnderstanding()
        self.prompt_engineer = AdvancedPromptEngineer(
            PromptConfig(
                use_chain_of_thought=True,
                use_self_verification=True,
                use_source_attribution=True,
                max_context_tokens=3000,
                max_sources=8
            )
        )
        self.answer_verifier = AdvancedAnswerVerification()
        
        # Initialize retrieval system
        from pinecone import Pinecone
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.retrieval = EnhancedRetrievalV2(pc, INDEX_NAME)
        
        # Pipeline statistics
        self.pipeline_stats = {
            "total_queries": 0,
            "verified_answers": 0,
            "average_confidence": 0.0,
            "average_processing_time": 0.0,
            "query_types": {},
            "complexity_levels": {}
        }
        
        print("✅ Advanced RAG Pipeline initialized")
        print(f"   Query understanding: ✅")
        print(f"   Advanced prompt engineering: ✅")
        print(f"   Answer verification: ✅")
        print(f"   Enhanced retrieval: ✅")
    
    def answer(self, question: str) -> AdvancedRAGResult:
        """
        Generate an answer using the advanced RAG pipeline.
        
        Args:
            question: User question
            
        Returns:
            AdvancedRAGResult with comprehensive analysis
        """
        start_time = time.time()
        
        print(f"\n🧠 Processing query: {question}")
        
        # Step 1: Query Understanding
        print("🔍 Step 1: Analyzing query...")
        query_analysis = self.query_understanding.analyze_query(question)
        
        print(f"   Intent: {query_analysis.intent.value}")
        print(f"   Complexity: {query_analysis.complexity.value}")
        print(f"   Entities: {query_analysis.entities}")
        print(f"   Requires reasoning: {query_analysis.requires_reasoning}")
        print(f"   Confidence: {query_analysis.confidence:.2f}")
        
        # Step 2: Advanced Retrieval
        print("🔍 Step 2: Advanced retrieval...")
        retrieval_strategy = self.query_understanding.get_retrieval_strategy(query_analysis)
        
        # Use query expansion if needed
        queries_to_try = [question]
        if retrieval_strategy.get("query_expansion", False):
            queries_to_try.extend(query_analysis.expanded_queries[:2])  # Try top 2 expansions
        
        best_results = []
        for query_variant in queries_to_try:
            print(f"   Trying query: {query_variant}")
            results = self.retrieval.retrieve(query_variant)
            if len(results) > len(best_results):
                best_results = results
        
        print(f"   Retrieved {len(best_results)} documents")
        
        # Step 3: Advanced Prompt Engineering
        print("🔍 Step 3: Building advanced prompt...")
        query_type = query_analysis.intent.value
        prompt = self.prompt_engineer.build_advanced_prompt(
            best_results, question, query_type
        )
        
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Query type: {query_type}")
        
        # Step 4: Answer Generation
        print("🔍 Step 4: Generating answer...")
        answer = generate_answer(prompt, question)
        
        print(f"   Answer length: {len(answer)} characters")
        
        # Step 5: Answer Verification
        print("🔍 Step 5: Verifying answer...")
        verification_result = self.answer_verifier.verify_answer(
            answer, best_results, question
        )
        
        print(f"   Verification: {'✅ VERIFIED' if verification_result.is_verified else '❌ NOT VERIFIED'}")
        print(f"   Confidence: {verification_result.confidence_score:.3f}")
        print(f"   Fact-check: {verification_result.fact_check_score:.3f}")
        print(f"   Hallucination risk: {verification_result.hallucination_risk:.3f}")
        
        # Step 6: Post-processing
        processing_time = time.time() - start_time
        
        # Update statistics
        self._update_stats(query_analysis, verification_result, processing_time)
        
        # Prepare result
        result = AdvancedRAGResult(
            answer=answer,
            query_analysis=query_analysis,
            verification_result=verification_result,
            retrieval_results=best_results,
            processing_time=processing_time,
            confidence_score=verification_result.confidence_score,
            features_used={
                "query_understanding": True,
                "advanced_prompt_engineering": True,
                "answer_verification": True,
                "query_expansion": retrieval_strategy.get("query_expansion", False),
                "chain_of_thought": True,
                "hallucination_prevention": True
            }
        )
        
        print(f"✅ Advanced RAG pipeline completed in {processing_time:.2f}s")
        print(f"   Final confidence: {result.confidence_score:.3f}")
        
        return result
    
    def _update_stats(self, 
                     query_analysis: QueryAnalysis, 
                     verification_result: VerificationResult, 
                     processing_time: float):
        """Update pipeline statistics."""
        self.pipeline_stats["total_queries"] += 1
        
        if verification_result.is_verified:
            self.pipeline_stats["verified_answers"] += 1
        
        # Update query type statistics
        intent = query_analysis.intent.value
        self.pipeline_stats["query_types"][intent] = self.pipeline_stats["query_types"].get(intent, 0) + 1
        
        # Update complexity statistics
        complexity = query_analysis.complexity.value
        self.pipeline_stats["complexity_levels"][complexity] = self.pipeline_stats["complexity_levels"].get(complexity, 0) + 1
        
        # Update average confidence
        total = self.pipeline_stats["total_queries"]
        current_avg = self.pipeline_stats["average_confidence"]
        self.pipeline_stats["average_confidence"] = (
            (current_avg * (total - 1) + verification_result.confidence_score) / total
        )
        
        # Update average processing time
        current_avg_time = self.pipeline_stats["average_processing_time"]
        self.pipeline_stats["average_processing_time"] = (
            (current_avg_time * (total - 1) + processing_time) / total
        )
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics."""
        stats = self.pipeline_stats.copy()
        
        if stats["total_queries"] > 0:
            stats["verification_rate"] = stats["verified_answers"] / stats["total_queries"]
        else:
            stats["verification_rate"] = 0.0
        
        # Add component statistics
        stats["query_understanding_stats"] = {
            "total_queries": stats["total_queries"],
            "query_types": stats["query_types"],
            "complexity_levels": stats["complexity_levels"]
        }
        
        stats["verification_stats"] = self.answer_verifier.get_verification_stats()
        
        return stats
    
    def answer_streaming(self, question: str) -> Generator[str, None, None]:
        """
        Generate a streaming answer using the advanced RAG pipeline.
        
        Args:
            question: User question
            
        Yields:
            Answer tokens as they are generated
        """
        # For now, we'll generate the full answer and then stream it
        # In a real implementation, this would stream from the LLM directly
        result = self.answer(question)
        answer = result.answer
        
        # Parse the response to separate thinking from main answer
        # Simple parsing to avoid circular imports
        import re
        
        # Look for the thinking section
        thinking_pattern = r'\*\*🤔\s*Thinking\*\*(.*?)(?=\n\n\*\*Risposta\*\*)'
        thinking_match = re.search(thinking_pattern, answer, re.DOTALL | re.IGNORECASE)
        
        if thinking_match:
            thinking_content = thinking_match.group(1).strip()
            # Remove the thinking section from the main answer
            main_answer = re.sub(thinking_pattern, '', answer, flags=re.DOTALL | re.IGNORECASE).strip()
        else:
            main_answer = answer
        
        # Clean up the main answer
        main_answer = re.sub(r'^\*\*Risposta\*\*\s*', '', main_answer, flags=re.IGNORECASE)
        main_answer = re.sub(r'^Risposta:\s*', '', main_answer, flags=re.IGNORECASE)
        main_answer = main_answer.strip()
        
        # Stream while preserving whitespace and newlines
        import re as _re
        tokens = _re.findall(r'\S+|\s+', main_answer)
        print(f"🔄 Streaming {len(tokens)} tokens (whitespace-preserving)...")
        for i, token in enumerate(tokens):
            yield token
        print(f"🔄 Finished streaming {len(tokens)} tokens")
    
    def answer_streaming_with_metadata(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generate a streaming answer with metadata using the advanced RAG pipeline.
        
        Args:
            question: User question
            
        Yields:
            Dictionaries with tokens and metadata
        """
        # Generate the full answer first
        result = self.answer(question)
        
        # Parse the response
        import re
        
        # Look for the thinking section
        thinking_pattern = r'\*\*🤔\s*Thinking\*\*(.*?)(?=\n\n\*\*Risposta\*\*)'
        thinking_match = re.search(thinking_pattern, result.answer, re.DOTALL | re.IGNORECASE)
        
        if thinking_match:
            thinking = thinking_match.group(1).strip()
            # Remove the thinking section from the main answer
            main_answer = re.sub(thinking_pattern, '', result.answer, flags=re.DOTALL | re.IGNORECASE).strip()
        else:
            thinking = ""
            main_answer = result.answer
        
        # Clean up the main answer
        main_answer = re.sub(r'^\*\*Risposta\*\*\s*', '', main_answer, flags=re.IGNORECASE)
        main_answer = re.sub(r'^Risposta:\s*', '', main_answer, flags=re.IGNORECASE)
        main_answer = main_answer.strip()
        
        # Stream the main answer with metadata
        import re as _re
        tokens = _re.findall(r'\S+|\s+', main_answer)
        for token in tokens:
            yield {
                "type": "token",
                "token": token,
                "confidence": result.confidence_score,
                "verified": result.verification_result.is_verified
            }
        
        # Send final metadata
        yield {
            "type": "metadata",
            "thinking": thinking,
            "confidence": result.confidence_score,
            "verified": result.verification_result.is_verified,
            "processing_time": result.processing_time,
            "features_used": result.features_used
        }
    
    def test_pipeline(self, test_queries: List[str]) -> Dict[str, Any]:
        """Test the pipeline with a set of queries."""
        print(f"🧪 Testing Advanced RAG Pipeline with {len(test_queries)} queries")
        
        results = []
        for i, query in enumerate(test_queries, 1):
            print(f"\n--- Test {i}/{len(test_queries)} ---")
            try:
                result = self.answer(query)
                results.append({
                    "query": query,
                    "success": True,
                    "confidence": result.confidence_score,
                    "verified": result.verification_result.is_verified,
                    "processing_time": result.processing_time,
                    "answer_length": len(result.answer)
                })
            except Exception as e:
                print(f"❌ Error processing query: {e}")
                results.append({
                    "query": query,
                    "success": False,
                    "error": str(e)
                })
        
        # Calculate test statistics
        successful_results = [r for r in results if r["success"]]
        test_stats = {
            "total_queries": len(test_queries),
            "successful_queries": len(successful_results),
            "success_rate": len(successful_results) / len(test_queries),
            "average_confidence": sum(r["confidence"] for r in successful_results) / len(successful_results) if successful_results else 0,
            "average_processing_time": sum(r["processing_time"] for r in successful_results) / len(successful_results) if successful_results else 0,
            "verified_answers": sum(1 for r in successful_results if r["verified"]),
            "verification_rate": sum(1 for r in successful_results if r["verified"]) / len(successful_results) if successful_results else 0
        }
        
        print(f"\n📊 Test Results:")
        print(f"   Success rate: {test_stats['success_rate']:.1%}")
        print(f"   Average confidence: {test_stats['average_confidence']:.3f}")
        print(f"   Verification rate: {test_stats['verification_rate']:.1%}")
        print(f"   Average processing time: {test_stats['average_processing_time']:.2f}s")
        
        return {
            "test_stats": test_stats,
            "detailed_results": results,
            "pipeline_stats": self.get_pipeline_stats()
        }

def test_advanced_rag_pipeline():
    """Test the advanced RAG pipeline."""
    print("🧪 Testing Advanced RAG Pipeline")
    
    # Initialize pipeline
    pipeline = AdvancedRAGPipeline()
    
    # Test queries
    test_queries = [
        "Da quanti crediti è il corso di Sistemi Operativi?",
        "Chi insegna il corso di Programmazione?",
        "Come posso iscrivermi al corso di Algoritmi?",
        "Qual è la differenza tra Sistemi Operativi e Reti di Calcolatori?",
        "Spiega cos'è un sistema operativo"
    ]
    
    # Run tests
    test_results = pipeline.test_pipeline(test_queries)
    
    print(f"\n🎯 Final Test Results:")
    print(f"   Overall success rate: {test_results['test_stats']['success_rate']:.1%}")
    print(f"   Average confidence: {test_results['test_stats']['average_confidence']:.3f}")
    print(f"   Verification rate: {test_results['test_stats']['verification_rate']:.1%}")
    
    return test_results

if __name__ == "__main__":
    test_advanced_rag_pipeline()

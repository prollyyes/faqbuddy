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
from .web_search_enhancer import WebSearchEnhancer
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
        
        # Initialize chunker for BM25 hybrid retrieval
        self.chunker = None
        try:
            from .utils.schema_aware_chunker import SchemaAwareChunker
            from .utils.generate_chunks import ChunkGenerator
            from .config import is_feature_enabled, BM25_FALLBACK
            
            if BM25_FALLBACK:  # Only initialize if BM25 is enabled
                if is_feature_enabled("schema_aware_chunking"):
                    print("🔄 Initializing schema-aware chunker for BM25 hybrid retrieval...")
                    self.chunker = SchemaAwareChunker()
                else:
                    print("🔄 Initializing chunk generator for BM25 hybrid retrieval...")
                    self.chunker = ChunkGenerator()
            else:
                print("📚 BM25 hybrid retrieval disabled")
        except ImportError as e:
            print(f"⚠️ Could not initialize chunker for BM25 hybrid retrieval: {e}")
            self.chunker = None
        
        # Initialize web search enhancer (if enabled)
        self.web_search = None
        if WEB_SEARCH_ENHANCEMENT:
            try:
                self.web_search = WebSearchEnhancer()
                print("   Web search enhancement: OK")
            except Exception as e:
                print(f"   Web search enhancement: FAILED (Error: {e})")
                self.web_search = None
        else:
            print("   Web search enhancement: FAILED (Disabled)")
        
        # Pipeline statistics
        self.pipeline_stats = {
            "total_queries": 0,
            "verified_answers": 0,
            "average_confidence": 0.0,
            "average_processing_time": 0.0,
            "query_types": {},
            "complexity_levels": {}
        }
        
        # Preload Mistral model to prevent generation delays
        print("🔄 Preloading Mistral model...")
        try:
            from utils.llm_mistral import ensure_mistral_loaded
            model_loaded = ensure_mistral_loaded()
            if model_loaded:
                print("   Mistral model: ✅ (preloaded)")
            else:
                print("   Mistral model: ⚠️ (failed to preload, will load on-demand)")
        except Exception as e:
            print(f"   Mistral model: ⚠️ (preload error: {e}, will load on-demand)")
        
        print("✅ Advanced RAG Pipeline initialized")
        print(f"   Query understanding: ✅")
        print(f"   Advanced prompt engineering: ✅")
        print(f"   Answer verification: ✅")
        print(f"   Enhanced retrieval: ✅")
        print(f"   BM25 hybrid retrieval: {'✅' if self.chunker else '❌'}")

    def _get_chunks_for_hybrid_search(self) -> List[Dict[str, Any]]:
        """Get chunks for BM25 hybrid retrieval."""
        if not self.chunker:
            return []
        
        try:
            if hasattr(self.chunker, 'get_all_chunks'):
                return self.chunker.get_all_chunks()
            elif hasattr(self.chunker, 'get_chunks'):
                return self.chunker.get_chunks()
            else:
                print("⚠️ Chunker doesn't have expected methods")
                return []
        except Exception as e:
            print(f"⚠️ Error getting chunks for BM25 hybrid search: {e}")
            return []
    
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
        
        # Get chunks for BM25 hybrid retrieval (if enabled)
        chunks_for_hybrid = self._get_chunks_for_hybrid_search()
        if chunks_for_hybrid:
            print(f"   📚 Loaded {len(chunks_for_hybrid)} chunks for BM25 hybrid retrieval")
        
        # Use query expansion if needed
        queries_to_try = [question]
        if retrieval_strategy.get("query_expansion", False):
            queries_to_try.extend(query_analysis.expanded_queries[:2])  # Try top 2 expansions
        
        best_results = []
        for query_variant in queries_to_try:
            print(f"   Trying query: {query_variant}")
            results = self.retrieval.retrieve(query_variant, chunks_for_hybrid)
            if len(results) > len(best_results):
                best_results = results
        
        print(f"   Retrieved {len(best_results)} documents")
        
        # Step 2.5: Web Search Enhancement (if enabled)
        if self.web_search:
            print("======= Step 2.5: Web search enhancement...")
            try:
                web_results = self.web_search.search(question, max_results=3)
                web_formatted = self.web_search.format_results_for_rag(web_results)
                
                # Combine with retrieval results
                best_results.extend(web_formatted)
                
                # Re-sort by score
                best_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                
                print(f"   Combined results: {len(best_results)} (local: {len(best_results) - len(web_formatted)}, web: {len(web_formatted)})")
            except Exception as e:
                print(f"   Web search failed: {e}")
                print("   Continuing with local results only...")
        
        # Step 3: Advanced Prompt Engineering
        print("======= Step 3: Building advanced prompt...")
        query_type = query_analysis.intent.value
        prompt = self.prompt_engineer.build_advanced_prompt(
            best_results, question, query_type, query_analysis
        )
        
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Query type: {query_type}")
        
        # Step 4: Answer Generation using modular prompt
        print("======= Step 4: Generating answer...")
        from utils.llm_mistral import ensure_mistral_loaded, clean_response, extract_answer_section
        
        # Ensure model is loaded
        if not ensure_mistral_loaded():
            answer = "⚠️ LLM generation is not available. Please install llama-cpp-python and ensure the Mistral model is available."
        else:
            # Re-import to get the updated global variable after loading
            from utils.llm_mistral import llm_mistral
            
            if llm_mistral is None:
                answer = "⚠️ Model loading failed after ensure_mistral_loaded"
            else:
                try:
                    # The prompt is already complete from modular system, use it directly
                    print(f"🔍 Using modular prompt directly (length: {len(prompt)})")
                    output = llm_mistral(prompt, max_tokens=2048, stop=["</s>", "[/INST]"], temperature=0.7, top_p=0.9)
                    
                    if isinstance(output, dict) and "choices" in output and len(output["choices"]) > 0:
                        raw_response = output["choices"][0]["text"].strip()
                        cleaned_response = clean_response(raw_response)
                        answer = extract_answer_section(cleaned_response)
                        
                        if not answer.strip():
                            answer = cleaned_response if cleaned_response.strip() else "⚠️ LLM generated empty response"
                    else:
                        answer = "⚠️ LLM output format error"
                except Exception as e:
                    answer = f"⚠️ LLM generation error: {str(e)}"
        
        print(f"   Answer length: {len(answer)} characters")
        
        # Step 5: Answer Verification
        print("======= Step 5: Verifying answer...")
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
                "web_search_enhancement": self.web_search is not None,
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
    
    def answer_streaming(self, question: str, request_id: str = None) -> Generator[str, None, None]:
        """
        Generate a streaming answer using the advanced RAG pipeline.
        
        Args:
            question: User question
            request_id: Request ID for cancellation tracking
            
        Yields:
            Answer tokens as they are generated
        """
        start_time = time.time()
        
        print(f"\n🧠 Processing query (streaming): {question}")
        
        # Import cancellation check function
        from utils.cancellation import is_request_cancelled
        
        # Check for cancellation before starting
        if request_id and is_request_cancelled(request_id):
            print(f"🛑 Request cancelled before processing: {request_id}")
            return
        
        # Step 1: Query Understanding
        print("🔍 Step 1: Analyzing query...")
        query_analysis = self.query_understanding.analyze_query(question)
        
        # Check for cancellation after query analysis
        if request_id and is_request_cancelled(request_id):
            print(f"🛑 Request cancelled after query analysis: {request_id}")
            return
        
        print(f"   Intent: {query_analysis.intent.value}")
        print(f"   Complexity: {query_analysis.complexity.value}")
        print(f"   Entities: {query_analysis.entities}")
        print(f"   Requires reasoning: {query_analysis.requires_reasoning}")
        print(f"   Confidence: {query_analysis.confidence:.2f}")
        
        # Step 2: Advanced Retrieval
        print("🔍 Step 2: Advanced retrieval...")
        retrieval_strategy = self.query_understanding.get_retrieval_strategy(query_analysis)
        
        # Get chunks for BM25 hybrid retrieval (if enabled)
        chunks_for_hybrid = self._get_chunks_for_hybrid_search()
        if chunks_for_hybrid:
            print(f"   📚 Loaded {len(chunks_for_hybrid)} chunks for BM25 hybrid retrieval")
        
        # Use query expansion if needed
        queries_to_try = [question]
        if retrieval_strategy.get("query_expansion", False):
            queries_to_try.extend(query_analysis.expanded_queries[:2])  # Try top 2 expansions
        
        best_results = []
        for query_variant in queries_to_try:
            print(f"   Trying query: {query_variant}")
            results = self.retrieval.retrieve(query_variant, chunks_for_hybrid)
            if len(results) > len(best_results):
                best_results = results
        
        print(f"   Retrieved {len(best_results)} documents")
        
        # Check for cancellation after retrieval
        if request_id and is_request_cancelled(request_id):
            print(f"🛑 Request cancelled after retrieval: {request_id}")
            return
        
        # Step 2.5: Web Search Enhancement (if enabled)
        if self.web_search:
            print("======= Step 2.5: Web search enhancement...")
            try:
                web_results = self.web_search.search(question, max_results=3)
                web_formatted = self.web_search.format_results_for_rag(web_results)
                
                # Combine with retrieval results
                best_results.extend(web_formatted)
                
                # Re-sort by score
                best_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                
                print(f"   Combined results: {len(best_results)} (local: {len(best_results) - len(web_formatted)}, web: {len(web_formatted)})")
            except Exception as e:
                print(f"   Web search failed: {e}")
                print("   Continuing with local results only...")
        
        # Check for cancellation after web search
        if request_id and is_request_cancelled(request_id):
            print(f"🛑 Request cancelled after web search: {request_id}")
            return
        
        # Step 3: Advanced Prompt Engineering
        print("======= Step 3: Building advanced prompt...")
        query_type = query_analysis.intent.value
        prompt = self.prompt_engineer.build_advanced_prompt(
            best_results, question, query_type, query_analysis
        )
        
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Query type: {query_type}")
        
        # Check for cancellation before LLM generation
        if request_id and is_request_cancelled(request_id):
            print(f"🛑 Request cancelled before LLM generation: {request_id}")
            return
        
        # Step 4: Streaming Answer Generation
        print("======= Step 4: Generating streaming answer...")
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Question: {question}")
        print(f"   Request ID: {request_id}")
        
        # Use the advanced streaming LLM function that can handle complex prompts
        from utils.llm_mistral import generate_answer_streaming_advanced
        
        print("   Starting LLM streaming...")
        token_count = 0
        # Stream the answer directly from the LLM using the advanced prompt
        for token in generate_answer_streaming_advanced(prompt, request_id):
            token_count += 1
            print(f"   Token {token_count}: {repr(token[:50])}...")
            # Check for cancellation before yielding each token
            if request_id and is_request_cancelled(request_id):
                print(f"🛑 Request cancelled during streaming: {request_id}")
                return
            yield token
        
        print(f"🔄 Finished streaming answer ({token_count} tokens)")
    
    def answer_streaming_with_metadata(self, question: str, request_id: str = None) -> Generator[Dict[str, Any], None, None]:
        """
        Generate a streaming answer with metadata using the advanced RAG pipeline.
        
        Args:
            question: User question
            request_id: Request ID for cancellation tracking
            
        Yields:
            Dictionaries with tokens and metadata
        """
        start_time = time.time()
        
        print(f"\n🧠 Processing query (streaming with metadata): {question}")
        print(f"========= PIPELINE: Starting with request_id: {request_id}")
        
        # Import cancellation check function
        from utils.cancellation import is_request_cancelled
        
        # Check for cancellation before starting
        if request_id and is_request_cancelled(request_id):
            print(f"🛑 Request cancelled before processing: {request_id}")
            return
        
        # Step 1: Query Understanding
        print("🔍 Step 1: Analyzing query...")
        query_analysis = self.query_understanding.analyze_query(question)
        
        # Check for cancellation after query analysis
        if request_id and is_request_cancelled(request_id):
            print(f"🛑 Request cancelled after query analysis: {request_id}")
            return
        
        print(f"   Intent: {query_analysis.intent.value}")
        print(f"   Complexity: {query_analysis.complexity.value}")
        print(f"   Entities: {query_analysis.entities}")
        print(f"   Requires reasoning: {query_analysis.requires_reasoning}")
        print(f"   Confidence: {query_analysis.confidence:.2f}")
        
        # Step 2: Advanced Retrieval
        print("🔍 Step 2: Advanced retrieval...")
        retrieval_strategy = self.query_understanding.get_retrieval_strategy(query_analysis)
        
        # Get chunks for BM25 hybrid retrieval (if enabled)
        chunks_for_hybrid = self._get_chunks_for_hybrid_search()
        if chunks_for_hybrid:
            print(f"   📚 Loaded {len(chunks_for_hybrid)} chunks for BM25 hybrid retrieval")
        
        # Use query expansion if needed
        queries_to_try = [question]
        if retrieval_strategy.get("query_expansion", False):
            queries_to_try.extend(query_analysis.expanded_queries[:2])  # Try top 2 expansions
        
        best_results = []
        for query_variant in queries_to_try:
            print(f"   Trying query: {query_variant}")
            results = self.retrieval.retrieve(query_variant, chunks_for_hybrid)
            if len(results) > len(best_results):
                best_results = results
        
        print(f"   Retrieved {len(best_results)} documents")
        
        # Check for cancellation after retrieval
        if request_id and is_request_cancelled(request_id):
            print(f"🛑 Request cancelled after retrieval: {request_id}")
            return
        
        # Step 2.5: Web Search Enhancement (if enabled)
        if self.web_search:
            print("======= Step 2.5: Web search enhancement...")
            try:
                web_results = self.web_search.search(question, max_results=3)
                web_formatted = self.web_search.format_results_for_rag(web_results)
                
                # Combine with retrieval results
                best_results.extend(web_formatted)
                
                # Re-sort by score
                best_results.sort(key=lambda x: x.get('score', 0), reverse=True)
                
                print(f"   Combined results: {len(best_results)} (local: {len(best_results) - len(web_formatted)}, web: {len(web_formatted)})")
            except Exception as e:
                print(f"   Web search failed: {e}")
                print("   Continuing with local results only...")
        
        # Check for cancellation after web search
        if request_id and is_request_cancelled(request_id):
            print(f"🛑 Request cancelled after web search: {request_id}")
            return
        
        # Step 3: Advanced Prompt Engineering
        print("======= Step 3: Building advanced prompt...")
        query_type = query_analysis.intent.value
        prompt = self.prompt_engineer.build_advanced_prompt(
            best_results, question, query_type, query_analysis
        )
        
        print(f"   Prompt length: {len(prompt)} characters")
        print(f"   Query type: {query_type}")
        
        # Check for cancellation before LLM generation
        if request_id and is_request_cancelled(request_id):
            print(f"🛑 Request cancelled before LLM generation: {request_id}")
            return
        
        # Step 4: Streaming Answer Generation with Metadata using modular prompt
        print("======= Step 4: Generating streaming answer with metadata...")
        
        # Ensure Mistral model is loaded and use it directly with the modular prompt
        from utils.llm_mistral import ensure_mistral_loaded, clean_response_streaming, extract_answer_section
        
        if not ensure_mistral_loaded():
            yield {
                "type": "error",
                "message": "⚠️ LLM generation is not available. Please install llama-cpp-python and ensure the Mistral model is available."
            }
            return
        
        # Re-import to get the updated global variable after loading
        from utils.llm_mistral import llm_mistral
        
        if llm_mistral is None:
            yield {
                "type": "error", 
                "message": "⚠️ Model loading failed after ensure_mistral_loaded"
            }
            return
        
        # Stream directly from the modular prompt (same as CLI approach)
        token_count = 0
        accumulated_text = ""
        yielded_meaningful = False
        try:
            print(f"🔍 Starting modular streaming with prompt length: {len(prompt)}")
            
            # First test the model with a simple non-streaming call (like CLI does)
            print(f"🔍 DEBUG: Testing model with simple prompt before streaming...")
            test_output = llm_mistral("[INST] Saluta brevemente [/INST]", max_tokens=50, stop=["</s>"], temperature=0.7)
            test_response = test_output["choices"][0]["text"] if "choices" in test_output and len(test_output["choices"]) > 0 else ""
            print(f"🔍 DEBUG: Test response: {repr(test_response[:100])}")
            
            if not test_response.strip():
                print("❌ DEBUG: Model fails even simple test - returning error")
                yield {
                    "type": "error",
                    "message": "⚠️ LLM model non è in grado di generare testo. Verificare configurazione model."
                }
                return
            
            # Now try streaming with the modular prompt
            print(f"🔍 DEBUG: Model test passed, starting streaming...")
            
            # EXPERIMENT: Test with simple prompt first to isolate the issue
            print(f"🔍 DEBUG: Testing simple prompt in streaming mode...")
            simple_test_prompt = "[INST] Rispondi brevemente: Come contattare la segreteria studenti? [/INST]"
            
            try:
                # Test 1: Simple prompt streaming
                test_stream = llm_mistral(simple_test_prompt, max_tokens=100, stop=["</s>", "[/INST]"], stream=True, temperature=0.7, top_p=0.9)
                print(f"🔍 DEBUG: Simple test stream created: {type(test_stream)}")
                
                test_chunk_count = 0
                for test_chunk in test_stream:
                    test_chunk_count += 1
                    print(f"🔍 DEBUG: Simple test chunk {test_chunk_count}: {test_chunk}")
                    if test_chunk_count >= 3:  # Just test first few chunks
                        break
                
                print(f"🔍 DEBUG: Simple test produced {test_chunk_count} chunks")
                
                # Test 2: Create streaming-compatible prompt (simpler format)
                print(f"🔍 DEBUG: Creating streaming-compatible prompt...")
                
                # Extract key info from modular prompt but use simpler format
                context_chunks = best_results[:5]  # Limit to top 5 for simplicity
                context_text = "\n\n".join([
                    f"Documento {i+1}: {chunk.get('text', '')[:300]}..."
                    for i, chunk in enumerate(context_chunks)
                ])
                
                streaming_prompt = f"""[INST] Sei FAQBuddy dell'Università La Sapienza di Roma. Rispondi in italiano usando le informazioni fornite.

CONTESTO:
{context_text}

DOMANDA: {question}

Rispondi in modo chiaro e professionale, citando i documenti come [Documento X]. [/INST]"""
                
                print(f"🔍 DEBUG: Streaming prompt length: {len(streaming_prompt)}")
                stream = llm_mistral(streaming_prompt, max_tokens=2048, stop=["</s>", "[/INST]"], stream=True, temperature=0.7, top_p=0.9)
                print(f"🔍 DEBUG: Streaming-compatible prompt stream created: {type(stream)}")
                
            except Exception as stream_error:
                print(f"❌ DEBUG: Failed to create stream: {stream_error}")
                yield {
                    "type": "error",
                    "message": f"Failed to create streaming response: {str(stream_error)}"
                }
                return
            
            chunk_counter = 0
            print(f"🔍 DEBUG: About to enter stream iteration loop...")
            
            for chunk in stream:
                chunk_counter += 1
                print(f"🔍 DEBUG: Processing chunk {chunk_counter}: {chunk}")
                
                # Check for cancellation before processing each chunk
                if request_id and is_request_cancelled(request_id):
                    print(f"🛑 Request cancelled during streaming: {request_id}")
                    return
                
                try:
                    choice = chunk.get("choices", [{}])[0]
                    text_content = ""
                    
                    if isinstance(choice, dict):
                        if "delta" in choice and isinstance(choice["delta"], dict):
                            text_content = choice["delta"].get("content", "")
                        elif "text" in choice:
                            text_content = choice.get("text", "")
                        elif "content" in choice:
                            text_content = choice.get("content", "")
                    
                    if text_content:
                        print(f"🔍 Raw token received: {repr(text_content)}")
                        
                        # Clean the token using streaming-safe cleaning (preserves whitespace)
                        cleaned_token = clean_response_streaming(text_content)
                        print(f"🧹 After clean_response_streaming: {repr(cleaned_token)}")
                        
                        # Strip leading "Risposta:" prefix (case-insensitive) if it appears at the very beginning
                        if cleaned_token and not yielded_meaningful:
                            import re as _re
                            original_token = cleaned_token
                            cleaned_token = _re.sub(r'^\s*(risposta\s*:?)\s*', '', cleaned_token, flags=_re.IGNORECASE)
                            if cleaned_token != original_token:
                                print(f"🧹 Stripped 'Risposta:' prefix: {repr(original_token)} -> {repr(cleaned_token)}")
                        
                        # Apply answer extraction to remove thinking if present
                        if accumulated_text == "":  # First token, check for thinking format
                            accumulated_text += cleaned_token
                            final_token = extract_answer_section(accumulated_text)
                            if final_token != accumulated_text:  # Thinking was removed
                                accumulated_text = final_token
                                cleaned_token = final_token
                                print(f"🎯 Extracted answer section from first streaming chunk: {repr(cleaned_token)}")
                        else:
                            accumulated_text += cleaned_token
                        
                        print(f"🎯 Final cleaned token: {repr(cleaned_token)}")
                        
                        # Yield ALL tokens, even if just whitespace (let frontend handle display)
                        if cleaned_token:  # Only check if not empty string, allow whitespace
                            token_count += 1
                            yielded_meaningful = True
                            print(f"✅ Yielding token {token_count}: {repr(cleaned_token)}")
                            yield {
                                "type": "token",
                                "token": cleaned_token,
                                "token_count": token_count,
                                "confidence": 0.85,
                                "query_analysis": {
                                    "intent": str(query_analysis.intent.value),
                                    "complexity": str(query_analysis.complexity.value),
                                    "requires_reasoning": bool(query_analysis.requires_reasoning)
                                },
                                "retrieval_info": {
                                    "sources_count": len(best_results),
                                    "query_type": str(query_type)
                                }
                            }
                        else:
                            print(f"❌ Skipping empty token after cleaning")
                except Exception as chunk_error:
                    print(f"⚠️ Error processing chunk: {chunk_error}")
                    continue
                    
        except Exception as e:
            print(f"❌ Error in modular streaming: {e}")
            yield {
                "type": "error",
                "message": f"Modular streaming failed: {str(e)}"
            }
            return
        
        print(f"========= LLM streaming completed with {token_count} tokens")
        
        # Check for premature termination (only 1 token usually means failure)
        if token_count <= 1:
            print(f"⚠️ WARNING: Only {token_count} token(s) generated - likely premature termination")
            yield {
                "type": "error", 
                "message": f"Stream terminated prematurely after {token_count} token(s)"
            }
            # Still send completion metadata even for errors to properly close the stream
            yield {
                "type": "metadata",
                "token_count": token_count,
                "finished": True,
                "confidence": 0.1,  # Low confidence for failed streams
                "error": True
            }
            return
        
        # Always send final metadata, even if no tokens were generated
        if token_count == 0:
            print("⚠️ No tokens were generated - sending error metadata")
            yield {
                "type": "error",
                "message": "No tokens generated by LLM"
            }
            # Send completion metadata for zero-token case too
            yield {
                "type": "metadata",
                "token_count": 0,
                "finished": True,
                "confidence": 0.0,
                "error": True
            }
            return
        
        # Send final metadata
        yield {
            "type": "metadata",
            "token_count": token_count,
            "finished": True,
            "confidence": 0.85,
            "query_analysis": {
                "intent": str(query_analysis.intent.value),
                "complexity": str(query_analysis.complexity.value),
                "requires_reasoning": bool(query_analysis.requires_reasoning)
            },
            "retrieval_info": {
                "sources_count": len(best_results),
                "query_type": str(query_type)
            }
        }
        
        print(f"========= Finished streaming answer with metadata ({token_count} tokens)")
    
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

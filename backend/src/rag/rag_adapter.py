"""
RAG Adapter for FAQBuddy Main API
This adapter wraps the RAGv2Pipeline to provide the interface expected by main.py
"""

import time
import sys
import os
import re
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
        
        # Parse the response to separate thinking from main answer
        print(f"========= RAG ADAPTER: Raw answer length: {len(answer)}")
        print(f"========= RAG ADAPTER: Raw answer preview: {answer[:200]}...")
        parsed_response = self._parse_chatgpt_response(answer)
        print(f"========= RAG ADAPTER: Parsed response: {parsed_response}")
        
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
            "response": parsed_response["main_answer"],
            "thinking": parsed_response["thinking"],
            "retrieval_time": round(total_time * 0.6, 3),  # Estimate 60% for retrieval
            "generation_time": round(total_time * 0.4, 3),  # Estimate 40% for generation
            "total_time": round(total_time, 3),
            "context_used": context_info,
            "sources": sources,
            "confidence_score": confidence
        }

    def generate_response_streaming(self, question: str, request_id: str = None) -> Generator[str, None, None]:
        """
        Generate a streaming response using the RAGv2 pipeline.
        Yields tokens as they are generated for reduced perceived latency.
        """
        # Generate the streaming answer using the RAGv2 pipeline
        for token in self.pipeline.answer_streaming(question, request_id):
            yield token

    def generate_response_streaming_with_metadata(self, question: str, request_id: str = None) -> Generator[Dict[str, Any], None, None]:
        """
        Generate a streaming response with metadata using the RAGv2 pipeline.
        Yields dictionaries with tokens and metadata for enhanced client experience.
        """
        print(f"========= RAG ADAPTER: Starting streaming with request_id: {request_id}")
        # Generate the streaming answer with metadata using the RAGv2 pipeline
        for chunk in self.pipeline.answer_streaming_with_metadata(question, request_id):
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
    
    def _parse_chatgpt_response(self, answer: str) -> Dict[str, str]:
        """
        Parse the ChatGPT-style response to separate thinking from main answer.
        
        Args:
            answer: The full response from the LLM
            
        Returns:
            Dictionary with 'thinking' and 'main_answer' keys
        """
        # First, clean up any unwanted tags
        answer = re.sub(r'\[INST\].*?\[/INST\]', '', answer, flags=re.DOTALL | re.IGNORECASE)
        answer = re.sub(r'\[/INST\]', '', answer, flags=re.IGNORECASE)
        answer = re.sub(r'\[INST\]', '', answer, flags=re.IGNORECASE)
        answer = re.sub(r'\[CITAZIONE\]', '', answer, flags=re.IGNORECASE)
        answer = re.sub(r'\[/CITAZIONE\]', '', answer, flags=re.IGNORECASE)
        answer = re.sub(r'\[FINE\]', '', answer, flags=re.IGNORECASE)
        
        # Look for the thinking section with multiple patterns
        thinking_patterns = [
            r'🤔\s*\*\*Thinking\*\*(.*?)(?=\n\n\*\*Risposta\*\*)',
            r'🤔\s*Thinking(.*?)(?=\n\n\*\*Risposta\*\*)',
            r'\*\*🤔\s*Thinking\*\*(.*?)(?=\n\n\*\*Risposta\*\*)',
            r'THINKING.*?(?=\n\n\*\*Risposta\*\*)',
            r'RAGIONAMENTO.*?(?=\n\n\*\*Risposta\*\*)',
            # Also look for *** separator
            r'🤔\s*\*\*Thinking\*\*(.*?)(?=\n\n\*\*\*\n\n\*\*Risposta\*\*)',
            r'🤔\s*Thinking(.*?)(?=\n\n\*\*\*\n\n\*\*Risposta\*\*)',
            r'\*\*🤔\s*Thinking\*\*(.*?)(?=\n\n\*\*\*\n\n\*\*Risposta\*\*)'
        ]
        
        thinking_content = ""
        main_answer = answer
        
        for pattern in thinking_patterns:
            thinking_match = re.search(pattern, answer, re.DOTALL | re.IGNORECASE)
            if thinking_match:
                thinking_content = thinking_match.group(1).strip()
                # Remove the thinking section from the main answer
                main_answer = re.sub(pattern, '', answer, flags=re.DOTALL | re.IGNORECASE).strip()
                break
        
        # If no thinking section found, try to extract from the beginning
        if not thinking_content:
            lines = answer.split('\n')
            thinking_lines = []
            main_lines = []
            in_thinking = False
            
            for line in lines:
                if re.search(r'🤔|THINKING|RAGIONAMENTO', line, re.IGNORECASE):
                    in_thinking = True
                    thinking_lines.append(line)
                elif in_thinking and re.search(r'\*\*Risposta\*\*|\*\*Answer\*\*', line, re.IGNORECASE):
                    in_thinking = False
                    main_lines.append(line)
                elif in_thinking:
                    thinking_lines.append(line)
                else:
                    main_lines.append(line)
            
            if thinking_lines:
                thinking_content = '\n'.join(thinking_lines).strip()
                main_answer = '\n'.join(main_lines).strip()
        
        # Clean up the main answer
        main_answer = re.sub(r'^\s*\n+', '', main_answer)  # Remove leading newlines
        main_answer = re.sub(r'\n+\s*$', '', main_answer)  # Remove trailing newlines
        main_answer = re.sub(r'^Risposta:\s*', '', main_answer, flags=re.IGNORECASE)  # Remove "Risposta:" prefix
        
        # Remove any remaining reasoning indicators from the main answer
        # but preserve the thinking content in the thinking section
        reasoning_indicators = [
            r'🔍.*?(?=\n|$)',
            r'🔗.*?(?=\n|$)',
            r'📋.*?(?=\n|$)',
            r'Analisi della domanda.*?(?=\n|$)',
            r'Ricerca nei frammenti.*?(?=\n|$)',
            r'Collegamento delle informazioni.*?(?=\n|$)',
            r'Sintesi della risposta.*?(?=\n|$)',
            r'Cita la risposta.*?(?=\n|$)'
        ]
        
        for indicator in reasoning_indicators:
            main_answer = re.sub(indicator, '', main_answer, flags=re.IGNORECASE)
        
        # Remove any remaining bracket tags that shouldn't be in the final answer
        main_answer = re.sub(r'\[FRAGMENTO\s*\d+\]', '', main_answer, flags=re.IGNORECASE)
        main_answer = re.sub(r'\[Frammento\s*\d+\]', '', main_answer, flags=re.IGNORECASE)
        main_answer = re.sub(r'\[DOCUMENTO\s*\d+\]', '', main_answer, flags=re.IGNORECASE)
        main_answer = re.sub(r'\[Documento\s*\d+\]', '', main_answer, flags=re.IGNORECASE)
        
        # Clean up extra whitespace
        main_answer = re.sub(r'\n\s*\n', '\n\n', main_answer)  # Normalize paragraph breaks
        main_answer = main_answer.strip()
        
        return {
            "thinking": thinking_content,
            "main_answer": main_answer
        } 
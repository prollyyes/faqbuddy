import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from .hybrid_retrieval import (
    load_all_chunks, bm25_search, pinecone_search, fuse_and_rerank, cross_encoder_rerank, ALPHA, TOP_K, EMBEDDING_MODEL
)
from .query_router import classify_intent, structured_retrieval, unstructured_retrieval, merge_results
from .build_prompt import build_prompt
from ..utils.llm_mistral import generate_answer, generate_answer_streaming, generate_answer_streaming_with_metadata
from dotenv import load_dotenv
from typing import Generator, Dict, Any

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))

class RAGPipeline:
    def __init__(self, data_dir=DATA_DIR, top_k=5):
        load_dotenv()
        self.data_dir = data_dir
        self.top_k = top_k
        self._model = None  # Lazy load SentenceTransformer
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.all_chunks = load_all_chunks(self.data_dir)
        print("[RAGPipeline] Initialized. Models will be loaded on first use.")

    @property
    def model(self):
        """Lazy load SentenceTransformer model."""
        if self._model is None:
            print("[RAGPipeline] Loading SentenceTransformer model...")
            self._model = SentenceTransformer(EMBEDDING_MODEL, device='mps')
            print("[RAGPipeline] SentenceTransformer model loaded successfully.")
        return self._model

    def answer(self, question: str) -> str:
        print(f"\n🔍 Processing question: {question}")
        
        # Step 1: Intent classification (structured/unstructured)
        intent = classify_intent(question)
        print(f"🎯 Detected intent: {intent}")
        
        # Step 2: Retrieval
        if intent == 'structured':
            print("📊 Using structured retrieval...")
            structured_results = structured_retrieval(question)
            unstructured_results = []
        elif intent == 'unstructured':
            print("📊 Using unstructured (hybrid) retrieval...")
            structured_results = []
            unstructured_results = unstructured_retrieval(question, self.model, self.pc, self.all_chunks)
        else:
            print("📊 Using both structured and unstructured retrieval...")
            structured_results = structured_retrieval(question)
            unstructured_results = unstructured_retrieval(question, self.model, self.pc, self.all_chunks)
        
        # Show namespace distribution in results
        if unstructured_results:
            docs_count = sum(1 for res in unstructured_results if res.get('namespace') == 'documents')
            db_count = sum(1 for res in unstructured_results if res.get('namespace') == 'db')
            print(f"📈 Namespace distribution: {docs_count} documents, {db_count} database")
        
        merged = merge_results(structured_results, unstructured_results, top_k=self.top_k)
        prompt = build_prompt(merged, question)
        
        # Step 3: Generate answer with Mistral
        print("[RAGPipeline] Generating answer with Mistral...")
        answer = generate_answer(prompt, question)
        return answer

    def answer_streaming(self, question: str) -> Generator[str, None, None]:
        """
        Generate answer using streaming for reduced perceived latency.
        Yields tokens as they are generated.
        """
        print(f"\n🔍 Processing question: {question}")
        
        # Step 1: Intent classification (structured/unstructured)
        intent = classify_intent(question)
        print(f"🎯 Detected intent: {intent}")
        
        # Step 2: Retrieval
        if intent == 'structured':
            print("📊 Using structured retrieval...")
            structured_results = structured_retrieval(question)
            unstructured_results = []
        elif intent == 'unstructured':
            print("📊 Using unstructured (hybrid) retrieval...")
            structured_results = []
            unstructured_results = unstructured_retrieval(question, self.model, self.pc, self.all_chunks)
        else:
            print("📊 Using both structured and unstructured retrieval...")
            structured_results = structured_retrieval(question)
            unstructured_results = unstructured_retrieval(question, self.model, self.pc, self.all_chunks)
        
        # Show namespace distribution in results
        if unstructured_results:
            docs_count = sum(1 for res in unstructured_results if res.get('namespace') == 'documents')
            db_count = sum(1 for res in unstructured_results if res.get('namespace') == 'db')
            print(f"📈 Namespace distribution: {docs_count} documents, {db_count} database")
        
        merged = merge_results(structured_results, unstructured_results, top_k=self.top_k)
        prompt = build_prompt(merged, question)
        
        # Step 3: Generate answer with Mistral using streaming
        print("[RAGPipeline] Generating streaming answer with Mistral...")
        for token in generate_answer_streaming(prompt, question):
            yield token

    def answer_streaming_with_metadata(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generate answer using streaming with metadata for enhanced client experience.
        Yields dictionaries with tokens and metadata.
        """
        print(f"\n🔍 Processing question: {question}")
        
        # Step 1: Intent classification (structured/unstructured)
        intent = classify_intent(question)
        print(f"🎯 Detected intent: {intent}")
        
        # Step 2: Retrieval
        if intent == 'structured':
            print("📊 Using structured retrieval...")
            structured_results = structured_retrieval(question)
            unstructured_results = []
        elif intent == 'unstructured':
            print("📊 Using unstructured (hybrid) retrieval...")
            structured_results = []
            unstructured_results = unstructured_retrieval(question, self.model, self.pc, self.all_chunks)
        else:
            print("📊 Using both structured and unstructured retrieval...")
            structured_results = structured_retrieval(question)
            unstructured_results = unstructured_retrieval(question, self.model, self.pc, self.all_chunks)
        
        # Show namespace distribution in results
        if unstructured_results:
            docs_count = sum(1 for res in unstructured_results if res.get('namespace') == 'documents')
            db_count = sum(1 for res in unstructured_results if res.get('namespace') == 'db')
            print(f"📈 Namespace distribution: {docs_count} documents, {db_count} database")
        
        merged = merge_results(structured_results, unstructured_results, top_k=self.top_k)
        prompt = build_prompt(merged, question)
        
        # Step 3: Generate answer with Mistral using streaming with metadata
        print("[RAGPipeline] Generating streaming answer with metadata...")
        for chunk in generate_answer_streaming_with_metadata(prompt, question):
            # Add RAG-specific metadata
            if chunk["type"] == "metadata":
                chunk.update({
                    "intent": intent,
                    "retrieval_method": "hybrid" if intent == "both" else intent,
                    "context_sources": len(merged),
                    "namespace_distribution": {
                        "documents": docs_count if unstructured_results else 0,
                        "database": db_count if unstructured_results else 0
                    }
                })
            yield chunk 
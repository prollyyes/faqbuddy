import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from src.rag.hybrid_retrieval import (
    load_all_chunks, bm25_search, pinecone_search, fuse_and_rerank, cross_encoder_rerank, 
    ALPHA, TOP_K, EMBEDDING_MODEL, get_retrieval_stats
)
from src.rag.query_router import classify_intent, structured_retrieval, unstructured_retrieval, merge_results
from src.rag.build_prompt import build_prompt, build_prompt_fast
from src.utils.llm_mistral import generate_answer, generate_answer_streaming, generate_answer_streaming_with_metadata
from dotenv import load_dotenv
from typing import Generator, Dict, Any, Optional
import traceback

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))

class RAGPipeline:
    def __init__(self, data_dir=DATA_DIR, top_k=TOP_K):
        load_dotenv()
        self.data_dir = data_dir
        self.top_k = top_k
        self._model = None  # Lazy load SentenceTransformer
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.all_chunks = load_all_chunks(self.data_dir)
        
        # Performance tracking
        self.stats = {
            "total_queries": 0,
            "avg_retrieval_time": 0,
            "avg_generation_time": 0,
            "avg_total_time": 0,
            "successful_queries": 0,
            "failed_queries": 0
        }
        
        print("[RAGPipeline] Initialized with enhanced performance tracking. Models will be loaded on first use.")

    @property
    def model(self):
        """Lazy load SentenceTransformer model."""
        if self._model is None:
            print("[RAGPipeline] Loading SentenceTransformer model...")
            self._model = SentenceTransformer(EMBEDDING_MODEL, device='mps')
            print("[RAGPipeline] SentenceTransformer model loaded successfully.")
        return self._model

    def _update_stats(self, retrieval_time: float, generation_time: float, total_time: float, success: bool = True):
        """Update performance statistics."""
        self.stats["total_queries"] += 1
        
        if success:
            self.stats["successful_queries"] += 1
        else:
            self.stats["failed_queries"] += 1
        
        # Update running averages
        n = self.stats["successful_queries"]
        if n > 0:
            self.stats["avg_retrieval_time"] = (
                (self.stats["avg_retrieval_time"] * (n-1) + retrieval_time) / n
            )
            self.stats["avg_generation_time"] = (
                (self.stats["avg_generation_time"] * (n-1) + generation_time) / n
            )
            self.stats["avg_total_time"] = (
                (self.stats["avg_total_time"] * (n-1) + total_time) / n
            )

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        retrieval_stats = get_retrieval_stats()
        return {
            **self.stats,
            "retrieval_system": retrieval_stats,
            "system_info": {
                "embedding_model": EMBEDDING_MODEL,
                "top_k": self.top_k,
                "alpha": ALPHA,
                "data_dir": self.data_dir
            }
        }

    def answer(self, question: str) -> str:
        """Generate answer with enhanced error handling and performance tracking."""
        start_time = time.time()
        
        try:
            print(f"\n🔍 Processing question: {question}")
            
            # Step 1: Intent classification
            intent_start = time.time()
            intent = classify_intent(question)
            intent_time = time.time() - intent_start
            print(f"🎯 Detected intent: {intent} (took {intent_time:.3f}s)")
            
            # Step 2: Retrieval
            retrieval_start = time.time()
            
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
            
            retrieval_time = time.time() - retrieval_start
            
            # Show namespace distribution in results
            if unstructured_results:
                docs_count = sum(1 for res in unstructured_results if res.get('namespace') == 'documents')
                db_count = sum(1 for res in unstructured_results if res.get('namespace') == 'db')
                print(f"📈 Namespace distribution: {docs_count} documents, {db_count} database")
            
            # Step 3: Merge and build prompt
            prompt_start = time.time()
            merged = merge_results(structured_results, unstructured_results, top_k=self.top_k)
            prompt, prompt_metadata = build_prompt(merged, question)
            prompt_time = time.time() - prompt_start
            
            # Log detailed token breakdown
            total_prompt_tokens = len(prompt.split()) + len([c for c in prompt if c in ',.!?;:'])
            print(f"📝 Prompt built in {prompt_time:.3f}s")
            print(f"   - Context tokens: {prompt_metadata['total_tokens']}")
            print(f"   - Total prompt tokens: {total_prompt_tokens}")
            print(f"   - LLM max_tokens: 800")
            print(f"   - Total estimated: {total_prompt_tokens + 800}")
            print(f"   - Context window limit: 2048")
            
            if total_prompt_tokens + 800 > 2048:
                print(f"⚠️ WARNING: Total tokens ({total_prompt_tokens + 800}) exceed context window (2048)!")
            
            # Step 4: Generate answer
            generation_start = time.time()
            print("[RAGPipeline] Generating answer with Mistral...")
            answer = generate_answer(prompt, question)
            generation_time = time.time() - generation_start
            
            # Calculate total time
            total_time = time.time() - start_time
            
            # Update statistics
            self._update_stats(retrieval_time, generation_time, total_time, success=True)
            
            print(f"✅ Answer generated in {generation_time:.3f}s (total: {total_time:.3f}s)")
            
            return answer
            
        except Exception as e:
            print(f"❌ Error in RAG pipeline: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Update statistics for failed query
            total_time = time.time() - start_time
            self._update_stats(0, 0, total_time, success=False)
            
            return f"Mi dispiace, si è verificato un errore durante l'elaborazione della tua domanda. Errore: {str(e)}"

    def answer_streaming(self, question: str) -> Generator[str, None, None]:
        """
        Generate answer using streaming for reduced perceived latency.
        Yields tokens as they are generated.
        """
        start_time = time.time()
        
        try:
            print(f"\n🔍 Processing question: {question}")
            
            # Step 1: Intent classification
            intent = classify_intent(question)
            print(f"🎯 Detected intent: {intent}")
            
            # Step 2: Retrieval
            retrieval_start = time.time()
            
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
            
            retrieval_time = time.time() - retrieval_start
            
            # Show namespace distribution in results
            if unstructured_results:
                docs_count = sum(1 for res in unstructured_results if res.get('namespace') == 'documents')
                db_count = sum(1 for res in unstructured_results if res.get('namespace') == 'db')
                print(f"📈 Namespace distribution: {docs_count} documents, {db_count} database")
            
            # Step 3: Merge and build prompt (fast version for streaming)
            merged = merge_results(structured_results, unstructured_results, top_k=self.top_k)
            prompt = build_prompt_fast(merged, question)
            
            # Step 4: Generate streaming answer
            generation_start = time.time()
            print("[RAGPipeline] Generating streaming answer with Mistral...")
            
            for token in generate_answer_streaming(prompt, question):
                yield token
            
            generation_time = time.time() - generation_start
            total_time = time.time() - start_time
            
            # Update statistics
            self._update_stats(retrieval_time, generation_time, total_time, success=True)
            
            print(f"✅ Streaming answer completed in {generation_time:.3f}s (total: {total_time:.3f}s)")
            
        except Exception as e:
            print(f"❌ Error in streaming RAG pipeline: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Update statistics for failed query
            total_time = time.time() - start_time
            self._update_stats(0, 0, total_time, success=False)
            
            # For streaming, I need to raise the error so it can be handled properly by the backend
            raise e

    def answer_streaming_with_metadata(self, question: str) -> Generator[Dict[str, Any], None, None]:
        """
        Generate answer using streaming with metadata for enhanced client experience.
        Yields dictionaries with tokens and metadata.
        """
        start_time = time.time()
        
        try:
            print(f"\n🔍 Processing question: {question}")
            
            # Step 1: Intent classification
            intent = classify_intent(question)
            print(f"🎯 Detected intent: {intent}")
            
            # Step 2: Retrieval
            retrieval_start = time.time()
            
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
            
            retrieval_time = time.time() - retrieval_start
            
            # Show namespace distribution in results
            if unstructured_results:
                docs_count = sum(1 for res in unstructured_results if res.get('namespace') == 'documents')
                db_count = sum(1 for res in unstructured_results if res.get('namespace') == 'db')
                print(f"📈 Namespace distribution: {docs_count} documents, {db_count} database")
            
            # Step 3: Merge and build prompt
            merged = merge_results(structured_results, unstructured_results, top_k=self.top_k)
            prompt, prompt_metadata = build_prompt(merged, question)
            
            # Step 4: Generate streaming answer with metadata
            generation_start = time.time()
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
                        },
                        "prompt_metadata": prompt_metadata,
                        "retrieval_time": retrieval_time,
                        "generation_time": time.time() - generation_start,
                        "total_time": time.time() - start_time
                    })
                yield chunk
            
            generation_time = time.time() - generation_start
            total_time = time.time() - start_time
            
            # Update statistics
            self._update_stats(retrieval_time, generation_time, total_time, success=True)
            
            print(f"✅ Streaming answer with metadata completed in {generation_time:.3f}s (total: {total_time:.3f}s)")
            
        except Exception as e:
            print(f"❌ Error in streaming RAG pipeline with metadata: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            
            # Update statistics for failed query
            total_time = time.time() - start_time
            self._update_stats(0, 0, total_time, success=False)
            
            yield {
                "type": "error",
                "content": f"Mi dispiace, si è verificato un errore durante l'elaborazione della tua domanda. Errore: {str(e)}",
                "error": str(e)
            }

    def test_retrieval(self, question: str) -> Dict[str, Any]:
        """
        Test retrieval components without generation for debugging.
        """
        print(f"\n🧪 Testing retrieval for: {question}")
        
        start_time = time.time()
        
        # Test intent classification
        intent = classify_intent(question)
        
        # Test retrieval
        if intent == 'structured':
            structured_results = structured_retrieval(question)
            unstructured_results = []
        elif intent == 'unstructured':
            structured_results = []
            unstructured_results = unstructured_retrieval(question, self.model, self.pc, self.all_chunks)
        else:
            structured_results = structured_retrieval(question)
            unstructured_results = unstructured_retrieval(question, self.model, self.pc, self.all_chunks)
        
        # Merge results
        merged = merge_results(structured_results, unstructured_results, top_k=self.top_k)
        
        # Build prompt to test prompt building
        prompt, prompt_metadata = build_prompt(merged, question)
        
        total_time = time.time() - start_time
        
        return {
            "intent": intent,
            "structured_results_count": len(structured_results),
            "unstructured_results_count": len(unstructured_results),
            "merged_results_count": len(merged),
            "prompt_metadata": prompt_metadata,
            "total_time": total_time,
            "retrieval_stats": get_retrieval_stats()
        }

def main():
    """Test the enhanced RAG pipeline."""
    pipeline = RAGPipeline()
    
    # Test query
    question = input("Enter a test question: ")
    
    print("\n=== Testing Enhanced RAG Pipeline ===")
    
    # Test retrieval first
    retrieval_test = pipeline.test_retrieval(question)
    print(f"\nRetrieval test results:")
    for key, value in retrieval_test.items():
        print(f"  {key}: {value}")
    
    # Test full pipeline
    print(f"\n=== Full Pipeline Test ===")
    answer = pipeline.answer(question)
    print(f"\nAnswer: {answer}")
    
    # Show final statistics
    print(f"\n=== Pipeline Statistics ===")
    stats = pipeline.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main() 
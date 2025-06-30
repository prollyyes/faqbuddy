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
from ..utils.llm_mistral import generate_answer
from dotenv import load_dotenv

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))

class RAGPipeline:
    def __init__(self, data_dir=DATA_DIR, top_k=5):
        load_dotenv()
        self.data_dir = data_dir
        self.top_k = top_k
        self.model = SentenceTransformer(EMBEDDING_MODEL, device='mps')
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.all_chunks = load_all_chunks(self.data_dir)
        print("[RAGPipeline] Initialized with Mistral for generation. Only Mistral is loaded.")

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
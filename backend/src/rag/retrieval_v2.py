"""
Enhanced Retrieval Pipeline for RAGv2
=====================================

This module implements Task 3: Retrieval pipeline improvements.
Features:
- Dense top-50 → cross-encoder reranker (bge-reranker-large)
- Keep any chunk score ≥ 0.2 until total context ≤ 4k tokens
- Remove BM25 from hot path (leave behind feature flag BM25_FALLBACK)
- Uses RAGv2 namespaces (documents_v2, db_v2, pdf_v2) for safe deployment
"""

import time
from typing import List, Dict, Any, Tuple, Optional
from sentence_transformers import CrossEncoder
from pinecone import Pinecone
from rank_bm25 import BM25Okapi
from .config import (
    RERANKER_ENABLED, 
    BM25_FALLBACK, 
    DENSE_TOP_K, 
    RERANKER_THRESHOLD, 
    MAX_CONTEXT_TOKENS,
    CROSS_ENCODER_MODEL,
    get_ragv2_namespaces,
    get_existing_namespaces,
    INDEX_NAME
)
from .utils.embeddings_v2 import EnhancedEmbeddings
import os

class EnhancedRetrieval:
    """
    Enhanced retrieval system with improved reranking and context management.
    
    Features:
    - Dense retrieval with increased top-k
    - Cross-encoder reranking with threshold filtering
    - Context token management
    - BM25 fallback option
    - Uses RAGv2 namespaces for safe deployment
    """
    
    def __init__(self, pinecone_client: Pinecone, index_name: str = INDEX_NAME):
        """
        Initialize the enhanced retrieval system.
        
        Args:
            pinecone_client: Pinecone client instance
            index_name: Name of the Pinecone index
        """
        self.pc = pinecone_client
        self.index_name = index_name
        self.embeddings = EnhancedEmbeddings()
        self._cross_encoder = None
        self.retrieval_stats = {
            "dense_retrieval_time": 0,
            "reranking_time": 0,
            "bm25_time": 0,
            "total_time": 0
        }
        
        # Get namespace configuration
        self.ragv2_namespaces = get_ragv2_namespaces()
        self.existing_namespaces = get_existing_namespaces()
        
        print("🚀 Initializing Enhanced Retrieval System")
        print(f"   Index: {index_name}")
        print(f"   RAGv2 namespaces: {self.ragv2_namespaces}")
        print(f"   Dense top-k: {DENSE_TOP_K}")
        print(f"   Reranker enabled: {RERANKER_ENABLED}")
        print(f"   BM25 fallback: {BM25_FALLBACK}")
        print(f"   Reranker threshold: {RERANKER_THRESHOLD}")
        print(f"   Max context tokens: {MAX_CONTEXT_TOKENS}")
    
    @property
    def cross_encoder(self) -> Optional[CrossEncoder]:
        """Lazy load cross-encoder model."""
        if self._cross_encoder is None and RERANKER_ENABLED:
            try:
                print(f"🔄 Loading cross-encoder: {CROSS_ENCODER_MODEL}")
                self._cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
                print("✅ Cross-encoder loaded successfully")
            except Exception as e:
                print(f"❌ Failed to load cross-encoder: {e}")
                self._cross_encoder = None
        
        return self._cross_encoder
    
    def _count_tokens(self, text: str) -> int:
        """Simple token counting approximation."""
        return len(text.split())
    
    def dense_retrieval(self, query: str, top_k: int = DENSE_TOP_K) -> List[Dict[str, Any]]:
        """
        Perform dense retrieval using Pinecone with RAGv2 namespaces.
        
        Args:
            query: Search query
            top_k: Number of results to retrieve
            
        Returns:
            List of retrieval results with metadata
        """
        start_time = time.time()
        
        # Encode query
        query_embedding = self.embeddings.encode_single(query)
        
        # Search Pinecone using RAGv2 namespaces
        index = self.pc.Index(self.index_name)
        
        # Search RAGv2 namespaces
        docs_results = index.query(
            vector=query_embedding, 
            top_k=top_k, 
            namespace=self.ragv2_namespaces["docs"], 
            include_metadata=True
        )
        db_results = index.query(
            vector=query_embedding, 
            top_k=top_k, 
            namespace=self.ragv2_namespaces["db"], 
            include_metadata=True
        )
        pdf_results = index.query(
            vector=query_embedding, 
            top_k=top_k, 
            namespace=self.ragv2_namespaces["pdf"], 
            include_metadata=True
        )
        
        # Combine results
        all_results = []
        
        for match in docs_results.get('matches', []):
            all_results.append({
                'id': match['id'],
                'score': match['score'],
                'metadata': match['metadata'],
                'namespace': self.ragv2_namespaces["docs"]
            })
        
        for match in db_results.get('matches', []):
            all_results.append({
                'id': match['id'],
                'score': match['score'],
                'metadata': match['metadata'],
                'namespace': self.ragv2_namespaces["db"]
            })
        
        for match in pdf_results.get('matches', []):
            all_results.append({
                'id': match['id'],
                'score': match['score'],
                'metadata': match['metadata'],
                'namespace': self.ragv2_namespaces["pdf"]
            })
        
        # Sort by score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Take top_k overall
        all_results = all_results[:top_k]
        
        self.retrieval_stats["dense_retrieval_time"] = time.time() - start_time
        
        print(f"🔍 Dense retrieval: {len(all_results)} results in {self.retrieval_stats['dense_retrieval_time']:.3f}s")
        print(f"   Namespace breakdown: {self._get_namespace_breakdown(all_results)}")
        
        return all_results
    
    def _get_namespace_breakdown(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of results by namespace."""
        breakdown = {}
        for result in results:
            namespace = result.get('namespace', 'unknown')
            breakdown[namespace] = breakdown.get(namespace, 0) + 1
        return breakdown
    
    def cross_encoder_rerank(self, query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rerank candidates using cross-encoder.
        
        Args:
            query: Search query
            candidates: List of candidate results
            
        Returns:
            Reranked results with cross-encoder scores
        """
        if not RERANKER_ENABLED or not self.cross_encoder:
            print("⚠️ Cross-encoder reranking disabled")
            return candidates
        
        start_time = time.time()
        
        # Prepare pairs for cross-encoder
        pairs = []
        for candidate in candidates:
            text = candidate['metadata'].get('text', '')
            pairs.append([query, text])
        
        # Get cross-encoder scores
        scores = self.cross_encoder.predict(pairs)
        
        # Add scores to candidates
        for i, candidate in enumerate(candidates):
            candidate['cross_score'] = float(scores[i])
        
        # Filter by threshold and sort
        filtered_candidates = [
            c for c in candidates 
            if c.get('cross_score', 0) >= RERANKER_THRESHOLD
        ]
        
        # Sort by cross-encoder score
        filtered_candidates.sort(key=lambda x: x.get('cross_score', 0), reverse=True)
        
        self.retrieval_stats["reranking_time"] = time.time() - start_time
        
        print(f"🎯 Cross-encoder reranking: {len(filtered_candidates)}/{len(candidates)} candidates above threshold in {self.retrieval_stats['reranking_time']:.3f}s")
        
        return filtered_candidates
    
    def bm25_fallback(self, query: str, all_chunks: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        BM25 fallback retrieval (when enabled).
        
        Args:
            query: Search query
            all_chunks: All available chunks
            top_k: Number of results to retrieve
            
        Returns:
            BM25 retrieval results
        """
        if not BM25_FALLBACK:
            return []
        
        start_time = time.time()
        
        # Prepare texts for BM25
        texts = [chunk['text'] for chunk in all_chunks]
        tokenized_corpus = [text.split() for text in texts]
        
        # Create BM25 index
        bm25 = BM25Okapi(tokenized_corpus)
        
        # Search
        tokenized_query = query.split()
        scores = bm25.get_scores(tokenized_query)
        
        # Get top results
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for i in top_indices:
            results.append({
                'id': all_chunks[i]['id'],
                'score': float(scores[i]),
                'metadata': all_chunks[i]['metadata'],
                'namespace': 'bm25_fallback'
            })
        
        self.retrieval_stats["bm25_time"] = time.time() - start_time
        
        print(f"📚 BM25 fallback: {len(results)} results in {self.retrieval_stats['bm25_time']:.3f}s")
        
        return results
    
    def manage_context_tokens(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Manage context tokens to stay within limits.
        
        Args:
            results: List of retrieval results
            
        Returns:
            Filtered results within token limits
        """
        total_tokens = 0
        filtered_results = []
        
        for result in results:
            text = result['metadata'].get('text', '')
            tokens = self._count_tokens(text)
            
            if total_tokens + tokens <= MAX_CONTEXT_TOKENS:
                filtered_results.append(result)
                total_tokens += tokens
            else:
                break
        
        print(f"📏 Context management: {len(filtered_results)}/{len(results)} results, {total_tokens}/{MAX_CONTEXT_TOKENS} tokens")
        
        return filtered_results
    
    def retrieve(self, query: str, all_chunks: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Main retrieval method combining all components.
        
        Args:
            query: Search query
            all_chunks: All available chunks (for BM25 fallback)
            
        Returns:
            Final retrieval results
        """
        start_time = time.time()
        
        # Step 1: Dense retrieval from RAGv2 namespaces
        dense_results = self.dense_retrieval(query)
        
        # Step 2: Cross-encoder reranking
        if RERANKER_ENABLED:
            reranked_results = self.cross_encoder_rerank(query, dense_results)
        else:
            reranked_results = dense_results
        
        # Step 3: BM25 fallback (if enabled and no good results)
        if BM25_FALLBACK and all_chunks and len(reranked_results) < 3:
            print("🔄 Few results from dense retrieval, trying BM25 fallback...")
            bm25_results = self.bm25_fallback(query, all_chunks)
            reranked_results.extend(bm25_results)
        
        # Step 4: Context token management
        final_results = self.manage_context_tokens(reranked_results)
        
        self.retrieval_stats["total_time"] = time.time() - start_time
        
        print(f"✅ Enhanced retrieval completed in {self.retrieval_stats['total_time']:.3f}s")
        print(f"📊 Final results: {len(final_results)}")
        print(f"   Final namespace breakdown: {self._get_namespace_breakdown(final_results)}")
        
        return final_results
    
    def get_retrieval_stats(self) -> Dict[str, float]:
        """Get retrieval performance statistics."""
        return self.retrieval_stats.copy()


def test_enhanced_retrieval():
    """Test the enhanced retrieval system with real Pinecone client."""
    print("🧪 Testing Enhanced Retrieval with Real Pinecone...")
    
    try:
        # Initialize real Pinecone client
        from dotenv import load_dotenv
        load_dotenv()
        
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Initialize retrieval system
        retrieval = EnhancedRetrieval(pc)
        
        # Test retrieval
        query = "Who teaches Operating Systems this semester?"
        results = retrieval.retrieve(query)
        
        print(f"✅ Retrieval test completed")
        print(f"📊 Results: {len(results)}")
        
        # Check results
        if results:
            first_result = results[0]
            required_fields = ['id', 'score', 'metadata', 'namespace']
            for field in required_fields:
                if field not in first_result:
                    print(f"❌ Missing field: {field}")
                    return False
            
            print("✅ All required fields present")
            
            # Check namespace
            namespace = first_result.get('namespace', '')
            if namespace.startswith('documents_v2') or namespace.startswith('db_v2') or namespace.startswith('pdf_v2'):
                print(f"✅ Using RAGv2 namespace: {namespace}")
            else:
                print(f"⚠️ Using non-RAGv2 namespace: {namespace}")
        
        # Check stats
        stats = retrieval.get_retrieval_stats()
        print(f"📈 Retrieval stats: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Retrieval test failed: {e}")
        print("Make sure PINECONE_API_KEY is set and index exists")
        return False


if __name__ == "__main__":
    test_enhanced_retrieval() 
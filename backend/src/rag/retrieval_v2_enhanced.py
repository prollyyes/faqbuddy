#!/usr/bin/env python3
"""
Enhanced Retrieval v2 with Namespace-Aware Selection
===================================================

This module enhances the RAG v2 retrieval system with proper namespace-aware
selection and boosting, similar to the original RAG system.
"""

import os
import time
from typing import Dict, List, Any, Optional, Tuple
from pinecone import Pinecone
from sentence_transformers import CrossEncoder

from .config import (
    INDEX_NAME, DENSE_TOP_K, RERANKER_ENABLED, CROSS_ENCODER_MODEL,
    RERANKER_THRESHOLD, BM25_FALLBACK, MAX_CONTEXT_TOKENS,
    get_ragv2_namespaces, get_existing_namespaces
)
from .utils.embeddings_v2 import EnhancedEmbeddings

# Namespace boost configuration (from original RAG system)
DEFAULT_DOCS_BOOST = 1.1  # 10% boost for documents namespace
DEFAULT_DB_BOOST = 1.0    # No boost for database namespace
DEFAULT_PDF_BOOST = 1.2   # 20% boost for PDF namespace (regulatory content)

# Strong boost when document keywords are detected
STRONG_DOCS_BOOST = 1.3   # 30% boost for documents
STRONG_PDF_BOOST = 1.5    # 50% boost for PDF (increased from 1.4)
STRONG_DB_BOOST = 1.0     # No boost for database

# Keywords that suggest PDF/document content (regulations, procedures, etc.)
PDF_DOCUMENT_KEYWORDS = [
    'regolamento', 'norme', 'procedure', 'requisiti', 'criteri', 'modalità',
    'scadenze', 'termini', 'documentazione', 'certificati', 'attestati',
    'esami', 'lauree', 'tesi', 'stage', 'tirocinio', 'erasmus', 'borsa',
    'contributo', 'tassa', 'pagamento', 'iscrizione', 'immatricolazione',
    'graduatoria', 'concorso', 'ammissione', 'trasferimento', 'rinuncia',
    'sospensione', 'riattivazione', 'cambio', 'opzione', 'curriculum',
    'come', 'quando', 'dove', 'perché', 'quanto', 'quale', 'chi'  # Procedural questions
]

# Keywords that suggest database/structured content (lists, contacts, etc.)
DATABASE_KEYWORDS = [
    'quali', 'elenca', 'mostra', 'lista', 'tutti', 'corsi', 'professori',
    'studenti', 'anno', 'matricola', 'insegnante', 'corso', 'email',
    'contatti', 'dipartimento', 'facoltà', 'review', 'recensioni',
    'materiale', 'edizione', 'orario', 'aula', 'sede', 'telefono',
    'indirizzo', 'sito', 'web', 'pagina', 'link', 'numero', 'codice'
]

# Minimum number of keyword matches to trigger strong boost
MIN_KEYWORD_MATCHES = 1

class EnhancedRetrievalV2:
    """
    Enhanced retrieval system with namespace-aware selection and boosting.
    
    Features:
    - Dense retrieval with namespace-aware boosting
    - Cross-encoder reranking with threshold filtering
    - Context token management
    - BM25 fallback option
    - Uses RAGv2 namespaces for safe deployment
    - Proper namespace selection based on query content
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
        
        print("🚀 Initializing Enhanced Retrieval V2 with Namespace-Aware Selection")
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
    
    def _determine_namespace_boosts(self, query: str) -> Dict[str, float]:
        """
        Determine namespace boosts based on query content.
        
        Args:
            query: Search query
            
        Returns:
            Dictionary of namespace boosts
        """
        query_lower = query.lower()
        
        # Count keyword matches
        pdf_matches = sum(1 for kw in PDF_DOCUMENT_KEYWORDS if kw in query_lower)
        db_matches = sum(1 for kw in DATABASE_KEYWORDS if kw in query_lower)
        
        print(f"🔍 Keyword analysis: {pdf_matches} PDF keywords, {db_matches} database keywords")
        
        # Determine boosts based on keyword analysis
        if pdf_matches >= MIN_KEYWORD_MATCHES and pdf_matches > db_matches:
            # Strong PDF boost for regulatory/procedural questions
            boosts = {
                'pdf_v2': STRONG_PDF_BOOST,
                'documents_v2': STRONG_DOCS_BOOST,
                'db_v2': DEFAULT_DB_BOOST
            }
            print(f"📄 Boosting PDF/Documents namespaces (strong) - PDF: {STRONG_PDF_BOOST}, Docs: {STRONG_DOCS_BOOST}")
        elif db_matches >= MIN_KEYWORD_MATCHES and db_matches > pdf_matches:
            # Strong database boost for factual/list questions
            boosts = {
                'pdf_v2': DEFAULT_PDF_BOOST,
                'documents_v2': DEFAULT_DOCS_BOOST,
                'db_v2': STRONG_DB_BOOST
            }
            print(f"🗄️ Boosting database namespace (strong) - DB: {STRONG_DB_BOOST}")
        else:
            # Default boosts
            boosts = {
                'pdf_v2': DEFAULT_PDF_BOOST,
                'documents_v2': DEFAULT_DOCS_BOOST,
                'db_v2': DEFAULT_DB_BOOST
            }
            print(f"⚖️ Using default namespace boosts")
        
        return boosts
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """Normalize scores to 0-1 range."""
        if not scores:
            return []
        min_score = min(scores)
        max_score = max(scores)
        if max_score == min_score:
            return [1.0 for _ in scores]
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    def dense_retrieval_with_boosting(self, query: str, top_k: int = DENSE_TOP_K) -> List[Dict[str, Any]]:
        """
        Perform dense retrieval with namespace-aware boosting.
        
        Args:
            query: Search query
            top_k: Number of results to retrieve
            
        Returns:
            List of retrieval results with metadata
        """
        start_time = time.time()
        
        # Encode query
        query_embedding = self.embeddings.encode_single(query)
        
        # Determine namespace boosts
        namespace_boosts = self._determine_namespace_boosts(query)
        
        # Search Pinecone using RAGv2 namespaces
        index = self.pc.Index(self.index_name)
        
        # Search each namespace separately
        namespace_results = {}
        for namespace_name, namespace in self.ragv2_namespaces.items():
            try:
                results = index.query(
                    vector=query_embedding, 
                    top_k=top_k, 
                    namespace=namespace, 
                    include_metadata=True
                )
                namespace_results[namespace] = results.get('matches', [])
                print(f"🔍 {namespace_name} namespace: {len(namespace_results[namespace])} results")
            except Exception as e:
                print(f"⚠️ Error searching {namespace}: {e}")
                namespace_results[namespace] = []
        
        # Apply boosts and combine results
        all_results = []
        
        for namespace, matches in namespace_results.items():
            if not matches:
                continue
                
            # Get boost for this namespace
            boost = namespace_boosts.get(namespace, 1.0)
            
            # Normalize scores within this namespace
            scores = [match['score'] for match in matches]
            normalized_scores = self._normalize_scores(scores)
            
            # Apply boost and add to results
            for i, match in enumerate(matches):
                boosted_score = normalized_scores[i] * boost
                all_results.append({
                    'id': match['id'],
                    'score': boosted_score,
                    'original_score': match['score'],
                    'metadata': match['metadata'],
                    'namespace': namespace,
                    'text': match['metadata'].get('text', ''),
                    'boost_applied': boost
                })
        
        # Sort by boosted score
        all_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Take top_k overall
        all_results = all_results[:top_k]
        
        self.retrieval_stats["dense_retrieval_time"] = time.time() - start_time
        
        print(f"🔍 Dense retrieval with boosting: {len(all_results)} results in {self.retrieval_stats['dense_retrieval_time']:.3f}s")
        print(f"   Namespace breakdown: {self._get_namespace_breakdown(all_results)}")
        
        return all_results
    
    def _get_namespace_breakdown(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get breakdown of results by namespace."""
        breakdown = {}
        for result in results:
            namespace = result.get('namespace', 'unknown')
            breakdown[namespace] = breakdown.get(namespace, 0) + 1
        return breakdown
    
    def cross_encoder_rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rerank results using cross-encoder.
        
        Args:
            query: Search query
            results: List of retrieval results
            
        Returns:
            Reranked results
        """
        if not self.cross_encoder or not results:
            return results
        
        start_time = time.time()
        
        # Prepare pairs for cross-encoder
        pairs = []
        for result in results:
            text = result.get('text', '')
            if text.strip():
                pairs.append([query, text])
        
        if not pairs:
            return results
        
        # Get cross-encoder scores
        scores = self.cross_encoder.predict(pairs)
        scores = [float(s) for s in scores]
        
        # Apply scores to results
        for i, result in enumerate(results):
            if i < len(scores):
                result['cross_encoder_score'] = scores[i]
                result['final_score'] = scores[i]  # Use cross-encoder score as final score
        
        # Filter by threshold and sort
        filtered_results = [
            result for result in results 
            if result.get('cross_encoder_score', 0) >= RERANKER_THRESHOLD
        ]
        
        # Sort by cross-encoder score
        filtered_results.sort(key=lambda x: x.get('cross_encoder_score', 0), reverse=True)
        
        self.retrieval_stats["reranking_time"] = time.time() - start_time
        
        print(f"🎯 Cross-encoder reranking: {len(filtered_results)}/{len(results)} candidates above threshold in {self.retrieval_stats['reranking_time']:.3f}s")
        
        return filtered_results
    
    def bm25_fallback(self, query: str, all_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        BM25 fallback for when dense retrieval fails.
        
        Args:
            query: Search query
            all_chunks: All available chunks
            
        Returns:
            BM25 results
        """
        if not all_chunks:
            return []
        
        start_time = time.time()
        
        try:
            from rank_bm25 import BM25Okapi
            
            # Prepare documents for BM25
            documents = []
            for chunk in all_chunks:
                text = chunk.get('text', '')
                if text.strip():
                    documents.append(text)
            
            if not documents:
                return []
            
            # Create BM25 model
            tokenized_docs = [doc.split() for doc in documents]
            bm25 = BM25Okapi(tokenized_docs)
            
            # Search
            tokenized_query = query.split()
            scores = bm25.get_scores(tokenized_query)
            
            # Get top results
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:10]
            
            # Convert to result format
            bm25_results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    chunk = all_chunks[idx]
                    bm25_results.append({
                        'id': chunk.get('id', f'bm25_{idx}'),
                        'score': scores[idx],
                        'metadata': chunk.get('metadata', {}),
                        'namespace': 'bm25_fallback',
                        'text': chunk.get('text', ''),
                        'retrieval_method': 'bm25'
                    })
            
            self.retrieval_stats["bm25_time"] = time.time() - start_time
            
            print(f"📚 BM25 fallback: {len(bm25_results)} results in {self.retrieval_stats['bm25_time']:.3f}s")
            
            return bm25_results
            
        except Exception as e:
            print(f"❌ BM25 fallback failed: {e}")
            return []
    
    def manage_context_tokens(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Manage context tokens to stay within limits.
        
        Args:
            results: List of retrieval results
            
        Returns:
            Results within token limits
        """
        total_tokens = 0
        selected_results = []
        
        for result in results:
            text = result.get('text', '')
            tokens = len(text.split())  # Simple token estimation
            
            if total_tokens + tokens <= MAX_CONTEXT_TOKENS:
                selected_results.append(result)
                total_tokens += tokens
            else:
                break
        
        print(f"📏 Context management: {len(selected_results)}/{len(results)} results, {total_tokens}/{MAX_CONTEXT_TOKENS} tokens")
        
        return selected_results
    
    def retrieve(self, query: str, all_chunks: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Main retrieval method with namespace-aware selection.
        
        Args:
            query: Search query
            all_chunks: All available chunks (for BM25 fallback)
            
        Returns:
            Final retrieval results
        """
        start_time = time.time()
        
        # Step 1: Dense retrieval with namespace-aware boosting
        dense_results = self.dense_retrieval_with_boosting(query)
        
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
        
        print(f"✅ Enhanced retrieval V2 completed in {self.retrieval_stats['total_time']:.3f}s")
        print(f"📊 Final results: {len(final_results)}")
        print(f"   Final namespace breakdown: {self._get_namespace_breakdown(final_results)}")
        
        return final_results
    
    def get_retrieval_stats(self) -> Dict[str, float]:
        """Get retrieval performance statistics."""
        return self.retrieval_stats.copy()


def test_enhanced_retrieval():
    """Test the enhanced retrieval system."""
    print("🧪 Testing Enhanced Retrieval V2...")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    retrieval = EnhancedRetrievalV2(pc)
    
    # Test queries
    test_queries = [
        "Chi insegna il corso di Sistemi Operativi?",  # Should prefer database
        "Come si richiede l'iscrizione al corso di laurea?",  # Should prefer PDF
        "Quali sono i requisiti per l'ammissione?",  # Should prefer PDF
        "Elenca tutti i corsi del primo anno"  # Should prefer database
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Testing: {query}")
        print(f"{'='*60}")
        
        results = retrieval.retrieve(query)
        
        print(f"\nResults: {len(results)}")
        for i, result in enumerate(results[:3], 1):
            namespace = result.get('namespace', 'unknown')
            score = result.get('score', 0)
            boost = result.get('boost_applied', 1.0)
            text = result.get('text', '')[:100] + "..." if len(result.get('text', '')) > 100 else result.get('text', '')
            print(f"  {i}. [{namespace}] Score: {score:.3f} (boost: {boost:.2f})")
            print(f"     Text: {text}")
    
    return True


if __name__ == "__main__":
    test_enhanced_retrieval() 
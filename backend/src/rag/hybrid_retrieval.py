import os
import json
import time
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder
from pinecone import Pinecone
from rank_bm25 import BM25Okapi
from src.rag.utils.pdf_chunker import chunk_pdf
import numpy as np
from typing import List, Dict, Tuple, Any

# Enhanced Configuration
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
INDEX_NAME = "exams-index-enhanced"
DOCS_NAMESPACE = "documents"
DB_NAMESPACE = "db"
EMBEDDING_MODEL = "all-mpnet-base-v2"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CHUNK_WINDOW = 200
CHUNK_OVERLAP = 50
TOP_K = 4  # Reduced for faster processing
ALPHA = 0.7  # Increased weight for dense search (better semantic understanding)
DOCS_NAMESPACE_BOOST = 1.1

# Performance optimizations
CACHE_SIZE = 1000  # LRU cache size for embeddings
BATCH_SIZE = 32  # Batch size for embedding generation
USE_CROSS_ENCODER = True  # Enable/disable cross-encoder for speed

# Enhanced namespace configuration
NAMESPACE_CONFIG = {
    'documents': {
        'boost': 1.1,
        'keywords': [
            'regolamento', 'norme', 'procedure', 'requisiti', 'criteri', 'modalità',
            'scadenze', 'termini', 'documentazione', 'certificati', 'attestati',
            'esami', 'lauree', 'tesi', 'stage', 'tirocinio', 'erasmus', 'borsa',
            'contributo', 'tassa', 'pagamento', 'iscrizione', 'immatricolazione'
        ]
    },
    'db': {
        'boost': 1.0,
        'keywords': [
            'quali', 'elenca', 'mostra', 'lista', 'tutti', 'corsi', 'professori',
            'studenti', 'anno', 'matricola', 'insegnante', 'corso', 'email',
            'contatti', 'dipartimento', 'facoltà', 'review', 'recensioni',
            'materiale', 'edizione', 'orario', 'aula', 'sede'
        ]
    }
}

# Simple LRU cache for embeddings
_embedding_cache = {}
_cache_hits = 0
_cache_misses = 0

def get_cached_embedding(text: str, model) -> List[float]:
    """Get embedding from cache or compute it."""
    global _cache_hits, _cache_misses
    
    # Simple hash for caching
    text_hash = hash(text[:100])  # Use first 100 chars as key
    
    if text_hash in _embedding_cache:
        _cache_hits += 1
        return _embedding_cache[text_hash]
    
    _cache_misses += 1
    embedding = model.encode([text])[0].tolist()
    
    # Simple LRU: remove oldest if cache is full
    if len(_embedding_cache) >= CACHE_SIZE:
        oldest_key = next(iter(_embedding_cache))
        del _embedding_cache[oldest_key]
    
    _embedding_cache[text_hash] = embedding
    return embedding

def get_cache_stats() -> Dict[str, int]:
    """Get embedding cache statistics."""
    return {
        'cache_size': len(_embedding_cache),
        'cache_hits': _cache_hits,
        'cache_misses': _cache_misses,
        'hit_rate': _cache_hits / (_cache_hits + _cache_misses) if (_cache_hits + _cache_misses) > 0 else 0
    }

def clear_embedding_cache():
    """Clear the embedding cache and reset statistics."""
    global _embedding_cache, _cache_hits, _cache_misses
    _embedding_cache.clear()
    _cache_hits = 0
    _cache_misses = 0
    print("🧹 Embedding cache cleared")

# Utility to load all chunks (for BM25)
def load_all_chunks(data_dir):
    all_chunks = []
    for fname in os.listdir(data_dir):
        if fname.lower().endswith('.pdf'):
            pdf_path = os.path.join(data_dir, fname)
            chunks = chunk_pdf(pdf_path, ocr=False, window_tokens=CHUNK_WINDOW, overlap_tokens=CHUNK_OVERLAP)
            for i, chunk in enumerate(chunks):
                chunk['id'] = f"{os.path.splitext(fname)[0]}_chunk_{i+1}"
                chunk['metadata']['chunk_type'] = 'pdf'
            all_chunks.extend(chunks)
    return all_chunks

def bm25_search(query: str, chunks: List[Dict], top_k: int = TOP_K) -> List[Tuple[Dict, float]]:
    """Enhanced BM25 search with better text preprocessing."""
    if not chunks:
        return []
    
    # Preprocess texts for better matching
    texts = []
    for chunk in chunks:
        text = chunk.get('text', '')
        # Clean and normalize text
        text = ' '.join(text.split())  # Normalize whitespace
        texts.append(text)
    
    # Tokenize corpus
    tokenized_corpus = [text.lower().split() for text in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    
    # Tokenize query
    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)
    
    # Get top results
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [(chunks[i], scores[i]) for i in top_indices if scores[i] > 0]

def pinecone_search(query: str, model, pc, top_k: int = TOP_K) -> List[Tuple[Dict, float, str, str]]:
    """Enhanced Pinecone search with better namespace handling and caching."""
    start_time = time.time()
    
    # Get cached embedding
    query_emb = get_cached_embedding(query, model)
    index = pc.Index(INDEX_NAME)
    
    # Determine dynamic namespace boosts
    docs_boost, db_boost = determine_namespace_boost(query)
    print(f"🎯 Dynamic boosts - Documents: {docs_boost:.2f}, Database: {db_boost:.2f}")
    
    # Search both namespaces with optimized parameters
    search_kwargs = {
        'top_k': top_k,
        'include_metadata': True,
        'include_values': False  # Don't return vectors for speed
    }
    
    docs_results = index.query(vector=query_emb, namespace=DOCS_NAMESPACE, **search_kwargs)
    db_results = index.query(vector=query_emb, namespace=DB_NAMESPACE, **search_kwargs)
    
    # Debug output
    print(f"🔍 Documents namespace: {len(docs_results['matches'])} results")
    print(f"🔍 Database namespace: {len(db_results['matches'])} results")
    
    # Normalize and combine results
    all_results = []
    
    # Process document results
    if docs_results['matches']:
        docs_scores = [match['score'] for match in docs_results['matches']]
        norm_docs_scores = min_max_normalize(docs_scores)
        
        for i, match in enumerate(docs_results['matches']):
            boosted_score = norm_docs_scores[i] * docs_boost
            all_results.append((match['metadata'], boosted_score, match['id'], 'documents'))
    
    # Process database results
    if db_results['matches']:
        db_scores = [match['score'] for match in db_results['matches']]
        norm_db_scores = min_max_normalize(db_scores)
        
        for i, match in enumerate(db_results['matches']):
            boosted_score = norm_db_scores[i] * db_boost
            all_results.append((match['metadata'], boosted_score, match['id'], 'db'))
    
    # Sort by score and return top_k
    all_results.sort(key=lambda x: x[1], reverse=True)
    
    # Debug: Show final namespace distribution
    docs_count = sum(1 for _, _, _, ns in all_results[:top_k] if ns == 'documents')
    db_count = sum(1 for _, _, _, ns in all_results[:top_k] if ns == 'db')
    print(f"📊 Final top {top_k} results: {docs_count} from documents, {db_count} from database")
    print(f"⏱️  Pinecone search time: {time.time() - start_time:.3f}s")
    
    return all_results[:top_k]

def min_max_normalize(scores: List[float]) -> List[float]:
    """Enhanced normalization with better handling of edge cases."""
    if not scores:
        return []
    
    min_score = min(scores)
    max_score = max(scores)
    
    if max_score == min_score:
        return [1.0 for _ in scores]
    
    # Use sigmoid-like normalization for better distribution
    normalized = []
    for score in scores:
        norm_score = (score - min_score) / (max_score - min_score)
        # Apply sigmoid transformation for better distribution
        norm_score = 1 / (1 + np.exp(-5 * (norm_score - 0.5)))
        normalized.append(norm_score)
    
    return normalized

def fuse_and_rerank(dense_results: List[Tuple], sparse_results: List[Tuple], alpha: float = ALPHA, top_k: int = TOP_K) -> List[Dict]:
    """Enhanced fusion with better score combination and reranking."""
    if not dense_results and not sparse_results:
        return []
    
    # Build lookup dictionaries
    dense_dict = {}
    for meta, score, id_, namespace in dense_results:
        dense_dict[id_] = {'meta': meta, 'dense': score, 'namespace': namespace}
    
    sparse_dict = {}
    for chunk, score in sparse_results:
        sparse_dict[chunk['id']] = {'meta': chunk['metadata'], 'sparse': score}
    
    # Collect all unique ids
    all_ids = set(dense_dict.keys()) | set(sparse_dict.keys())
    
    # Normalize scores
    dense_scores = [dense_dict.get(i, {}).get('dense', 0) for i in all_ids]
    sparse_scores = [sparse_dict.get(i, {}).get('sparse', 0) for i in all_ids]
    
    norm_dense = min_max_normalize(dense_scores)
    norm_sparse = min_max_normalize(sparse_scores)
    
    # Enhanced fusion with weighted combination
    fused = []
    for idx, id_ in enumerate(all_ids):
        meta = dense_dict.get(id_, sparse_dict.get(id_, {})).get('meta', {})
        namespace = dense_dict.get(id_, {}).get('namespace', 'unknown')
        
        score_dense = norm_dense[idx]
        score_sparse = norm_sparse[idx]
        
        # Enhanced fusion formula with namespace weighting
        namespace_weight = 1.1 if namespace == 'documents' else 1.0
        combined = (alpha * score_dense + (1 - alpha) * score_sparse) * namespace_weight
        
        fused.append({
            'id': id_, 
            'meta': meta, 
            'namespace': namespace,
            'score_dense': score_dense, 
            'score_sparse': score_sparse, 
            'score_combined': combined,
            'text': meta.get('text', '')
        })
    
    # Sort by combined score
    fused.sort(key=lambda x: x['score_combined'], reverse=True)
    return fused[:top_k]

def cross_encoder_rerank(query: str, fused_results: List[Dict], model_name: str = CROSS_ENCODER_MODEL) -> List[Dict]:
    """Enhanced cross-encoder reranking with better error handling and performance."""
    if not USE_CROSS_ENCODER or not fused_results:
        return fused_results
    
    try:
        # Lazy load cross-encoder
        if not hasattr(cross_encoder_rerank, '_cross_encoder'):
            print(f"🔄 Loading cross-encoder model: {model_name}")
            cross_encoder_rerank._cross_encoder = CrossEncoder(model_name)
            print("✅ Cross-encoder loaded successfully")
        
        cross_encoder = cross_encoder_rerank._cross_encoder
        
        # Prepare pairs for cross-encoder
        pairs = []
        for res in fused_results:
            text = res['meta'].get('text', '')
            if text:
                pairs.append((query, text))
            else:
                pairs.append((query, "No content available"))
        
        # Get cross-encoder scores
        scores = cross_encoder.predict(pairs)
        
        # Add scores to results
        for res, score in zip(fused_results, scores):
            res['cross_score'] = float(score)
        
        # Rerank by cross-encoder score
        reranked = sorted(fused_results, key=lambda x: x.get('cross_score', 0), reverse=True)
        
        print(f"🎯 Cross-encoder reranking completed for {len(reranked)} results")
        return reranked
        
    except Exception as e:
        print(f"⚠️  Cross-encoder reranking failed: {e}")
        print("   Falling back to fused results without reranking")
        return fused_results

def determine_namespace_boost(query: str) -> Tuple[float, float]:
    """
    Enhanced namespace boost determination with better keyword matching.
    """
    query_lower = query.lower()
    
    # Count keyword matches for each namespace
    docs_matches = sum(1 for kw in NAMESPACE_CONFIG['documents']['keywords'] if kw in query_lower)
    db_matches = sum(1 for kw in NAMESPACE_CONFIG['db']['keywords'] if kw in query_lower)
    
    print(f"🔍 Keyword analysis: {docs_matches} document keywords, {db_matches} database keywords")
    
    # Calculate boosts based on keyword matches
    docs_boost = NAMESPACE_CONFIG['documents']['boost']
    db_boost = NAMESPACE_CONFIG['db']['boost']
    
    # Apply dynamic boosts based on keyword matches
    if docs_matches > db_matches:
        docs_boost *= 1.2
        db_boost *= 0.9
    elif db_matches > docs_matches:
        docs_boost *= 0.9
        db_boost *= 1.2
    
    # Ensure minimum boost values
    docs_boost = max(docs_boost, 0.8)
    db_boost = max(db_boost, 0.8)
    
    return docs_boost, db_boost

def get_retrieval_stats() -> Dict[str, Any]:
    """Get retrieval system statistics."""
    cache_stats = get_cache_stats()
    return {
        'cache_stats': cache_stats,
        'config': {
            'top_k': TOP_K,
            'alpha': ALPHA,
            'embedding_model': EMBEDDING_MODEL,
            'cross_encoder_model': CROSS_ENCODER_MODEL,
            'use_cross_encoder': USE_CROSS_ENCODER
        }
    }

def main():
    """Enhanced test function with performance monitoring."""
    load_dotenv()
    print(f"\n🔍 Loading all document chunks for BM25...")
    all_chunks = load_all_chunks(DATA_DIR)
    print(f"Loaded {len(all_chunks)} chunks.")

    print(f"\n🚀 Loading embedding model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL, device='mps')

    print(f"\n🔑 Connecting to Pinecone...")
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))

    # Sample query
    query = input("\nEnter your test query: ")

    print(f"\n=== Enhanced Retrieval Pipeline ===")
    
    # Test Pinecone search
    print(f"\n=== Pinecone (Dense) Results ===")
    dense_results = pinecone_search(query, model, pc, top_k=TOP_K)
    for i, (meta, score, id_, namespace) in enumerate(dense_results, 1):
        print(f"{i}. [Score: {score:.4f} | Namespace: {namespace}] Section: {meta.get('section_title', '')} | Page: {meta.get('page', '')}")
        print(f"   ...{meta.get('text', '')[:200]}...")

    # Test BM25 search
    print(f"\n=== BM25 (Sparse) Results ===")
    sparse_results = bm25_search(query, all_chunks, top_k=TOP_K)
    for i, (chunk, score) in enumerate(sparse_results, 1):
        print(f"{i}. [Score: {score:.4f}] Section: {chunk['metadata'].get('section_title', '')} | Page: {chunk['metadata'].get('page', '')}")
        print(f"   ...{chunk['text'][:200]}...")

    # Test fusion and reranking
    print(f"\n=== Enhanced Fusion & Reranking (ALPHA={ALPHA}) ===")
    fused_results = fuse_and_rerank(dense_results, sparse_results, alpha=ALPHA, top_k=TOP_K)
    for i, res in enumerate(fused_results, 1):
        print(f"{i}. [Combined: {res['score_combined']:.4f} | Dense: {res['score_dense']:.4f} | Sparse: {res['score_sparse']:.4f} | Namespace: {res.get('namespace', 'unknown')}] Section: {res['meta'].get('section_title', '')} | Page: {res['meta'].get('page', '')}")
        print(f"   ...{res['meta'].get('text', '')[:200]}...")

    # Test cross-encoder reranking
    if USE_CROSS_ENCODER:
        print(f"\n=== Cross-Encoder Reranked Results ===")
        reranked_results = cross_encoder_rerank(query, fused_results)
        for i, res in enumerate(reranked_results, 1):
            print(f"{i}. [Cross-Score: {res.get('cross_score', 0):.4f} | Combined: {res['score_combined']:.4f} | Namespace: {res.get('namespace', 'unknown')}] Section: {res['meta'].get('section_title', '')} | Page: {res['meta'].get('page', '')}")
            print(f"   ...{res['meta'].get('text', '')[:200]}...")

    # Print statistics
    print(f"\n=== System Statistics ===")
    stats = get_retrieval_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main() 
import os
import json
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer, CrossEncoder
from pinecone import Pinecone
from rank_bm25 import BM25Okapi
from .utils.pdf_chunker import chunk_pdf

# Config
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
INDEX_NAME = "exams-index-enhanced"
DOCS_NAMESPACE = "documents"
DB_NAMESPACE = "db"
EMBEDDING_MODEL = "all-mpnet-base-v2"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
CHUNK_WINDOW = 200
CHUNK_OVERLAP = 50
TOP_K = 5
ALPHA = 0.6  # Weight for dense (Pinecone) score in fusion
DOCS_NAMESPACE_BOOST = 1.1  # Boost factor for documents namespace (1.0 = no boost)

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

def bm25_search(query, chunks, top_k=TOP_K):
    texts = [chunk['text'] for chunk in chunks]
    tokenized_corpus = [text.split() for text in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.split()
    scores = bm25.get_scores(tokenized_query)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [(chunks[i], scores[i]) for i in top_indices]

def pinecone_search(query, model, pc, top_k=TOP_K):
    # Embed the query
    query_emb = model.encode([query])[0].tolist()
    index = pc.Index(INDEX_NAME)
    
    # Determine dynamic namespace boosts
    docs_boost, db_boost = determine_namespace_boost(query)
    print(f"🎯 Dynamic boosts - Documents: {docs_boost:.2f}, Database: {db_boost:.2f}")
    
    # Search both namespaces separately
    docs_results = index.query(vector=query_emb, top_k=top_k, namespace=DOCS_NAMESPACE, include_metadata=True)
    db_results = index.query(vector=query_emb, top_k=top_k, namespace=DB_NAMESPACE, include_metadata=True)
    
    # Debug output
    print(f"🔍 Documents namespace: {len(docs_results['matches'])} results")
    print(f"🔍 Database namespace: {len(db_results['matches'])} results")
    
    # Normalize scores within each namespace first
    docs_scores = [match['score'] for match in docs_results['matches']] if docs_results['matches'] else []
    db_scores = [match['score'] for match in db_results['matches']] if db_results['matches'] else []
    
    # Normalize scores to 0-1 range within each namespace
    def normalize_scores(scores):
        if not scores:
            return []
        min_score = min(scores)
        max_score = max(scores)
        if max_score == min_score:
            return [1.0 for _ in scores]
        return [(s - min_score) / (max_score - min_score) for s in scores]
    
    norm_docs_scores = normalize_scores(docs_scores)
    norm_db_scores = normalize_scores(db_scores)
    
    # Combine results with namespace-aware scoring
    all_results = []
    
    # Add document results with dynamic boost
    for i, match in enumerate(docs_results['matches']):
        boosted_score = norm_docs_scores[i] * docs_boost
        all_results.append((match['metadata'], boosted_score, match['id'], 'documents'))
    
    # Add database results with dynamic boost
    for i, match in enumerate(db_results['matches']):
        boosted_score = norm_db_scores[i] * db_boost
        all_results.append((match['metadata'], boosted_score, match['id'], 'db'))
    
    # Sort by normalized score and return top_k
    all_results.sort(key=lambda x: x[1], reverse=True)
    
    # Debug: Show final namespace distribution
    docs_count = sum(1 for _, _, _, ns in all_results[:top_k] if ns == 'documents')
    db_count = sum(1 for _, _, _, ns in all_results[:top_k] if ns == 'db')
    print(f"📊 Final top {top_k} results: {docs_count} from documents, {db_count} from database")
    
    return all_results[:top_k]

def min_max_normalize(scores):
    if not scores:
        return []
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0 for _ in scores]
    return [(s - min_score) / (max_score - min_score) for s in scores]

def fuse_and_rerank(dense_results, sparse_results, alpha=ALPHA, top_k=TOP_K):
    # Build dicts for fast lookup - handle new tuple format with namespace
    dense_dict = {}
    for meta, score, id_, namespace in dense_results:
        dense_dict[id_] = {'meta': meta, 'dense': score, 'namespace': namespace}
    
    sparse_dict = {chunk['id']: {'meta': chunk['metadata'], 'sparse': score} for chunk, score in sparse_results}
    
    # Collect all unique ids
    all_ids = set(dense_dict.keys()) | set(sparse_dict.keys())
    
    # Normalize scores
    dense_scores = [dense_dict.get(i, {}).get('dense', 0) for i in all_ids]
    sparse_scores = [sparse_dict.get(i, {}).get('sparse', 0) for i in all_ids]
    norm_dense = min_max_normalize(dense_scores)
    norm_sparse = min_max_normalize(sparse_scores)
    
    # Fuse
    fused = []
    for idx, id_ in enumerate(all_ids):
        meta = dense_dict.get(id_, sparse_dict.get(id_, {})).get('meta', {})
        namespace = dense_dict.get(id_, {}).get('namespace', 'unknown')
        score_dense = norm_dense[idx]
        score_sparse = norm_sparse[idx]
        combined = alpha * score_dense + (1 - alpha) * score_sparse
        fused.append({
            'id': id_, 
            'meta': meta, 
            'namespace': namespace,
            'score_dense': score_dense, 
            'score_sparse': score_sparse, 
            'score_combined': combined
        })
    
    # Sort by combined score
    fused.sort(key=lambda x: x['score_combined'], reverse=True)
    return fused[:top_k]

def cross_encoder_rerank(query, fused_results, model_name=CROSS_ENCODER_MODEL):
    try:
        cross_encoder = CrossEncoder(model_name)
    except Exception as e:
        print(f"⚠️  Could not load cross-encoder model '{model_name}': {e}")
        return fused_results  # fallback: return as is
    pairs = [(query, res['meta'].get('text', '')) for res in fused_results]
    scores = cross_encoder.predict(pairs)
    reranked = [dict(res, cross_score=s) for res, s in zip(fused_results, scores)]
    reranked.sort(key=lambda x: x['cross_score'], reverse=True)
    return reranked

def determine_namespace_boost(query):
    """
    Dynamically determine namespace boost based on query content.
    Returns (docs_boost, db_boost) tuple.
    """
    try:
        from namespace_config import (
            DEFAULT_DOCS_BOOST, DEFAULT_DB_BOOST,
            STRONG_DOCS_BOOST, STRONG_DB_BOOST_WHEN_DB,
            STRONG_DOCS_BOOST_WHEN_DB, STRONG_DB_BOOST_WHEN_DB,
            DOCUMENT_KEYWORDS, DATABASE_KEYWORDS,
            MIN_KEYWORD_MATCHES, DEBUG_MODE
        )
    except ImportError:
        # Fallback to hardcoded values if config file not found
        DOCUMENT_KEYWORDS = [
            'regolamento', 'norme', 'procedure', 'requisiti', 'criteri', 'modalità',
            'scadenze', 'termini', 'documentazione', 'certificati', 'attestati',
            'esami', 'lauree', 'tesi', 'stage', 'tirocinio', 'erasmus', 'borsa',
            'contributo', 'tassa', 'pagamento', 'iscrizione', 'immatricolazione'
        ]
        DATABASE_KEYWORDS = [
            'quali', 'elenca', 'mostra', 'lista', 'tutti', 'corsi', 'professori',
            'studenti', 'anno', 'matricola', 'insegnante', 'corso', 'email',
            'contatti', 'dipartimento', 'facoltà', 'review', 'recensioni',
            'materiale', 'edizione', 'orario', 'aula', 'sede'
        ]
        DEFAULT_DOCS_BOOST = 1.1
        DEFAULT_DB_BOOST = 1.0
        STRONG_DOCS_BOOST = 1.2
        STRONG_DB_BOOST_WHEN_DB = 1.1
        STRONG_DOCS_BOOST_WHEN_DB = 1.0
        MIN_KEYWORD_MATCHES = 1
        DEBUG_MODE = True
    
    query_lower = query.lower()
    
    doc_matches = sum(1 for kw in DOCUMENT_KEYWORDS if kw in query_lower)
    db_matches = sum(1 for kw in DATABASE_KEYWORDS if kw in query_lower)
    
    if DEBUG_MODE:
        print(f"🔍 Keyword analysis: {doc_matches} document keywords, {db_matches} database keywords")
    
    # Calculate boosts
    if doc_matches >= MIN_KEYWORD_MATCHES and doc_matches > db_matches:
        docs_boost = STRONG_DOCS_BOOST
        db_boost = DEFAULT_DB_BOOST  # Use default when boosting documents
        if DEBUG_MODE:
            print(f"📄 Boosting documents namespace (strong)")
    elif db_matches >= MIN_KEYWORD_MATCHES and db_matches > doc_matches:
        docs_boost = STRONG_DOCS_BOOST_WHEN_DB
        db_boost = STRONG_DB_BOOST_WHEN_DB
        if DEBUG_MODE:
            print(f"🗄️ Boosting database namespace (strong)")
    else:
        docs_boost = DEFAULT_DOCS_BOOST
        db_boost = DEFAULT_DB_BOOST
        if DEBUG_MODE:
            print(f"⚖️ Using default namespace boosts")
    
    return docs_boost, db_boost

def main():
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

    print(f"\n=== Pinecone (Dense) Results ===")
    dense_results = pinecone_search(query, model, pc, top_k=TOP_K)
    for i, (meta, score, id_, namespace) in enumerate(dense_results, 1):
        print(f"{i}. [Score: {score:.4f} | Namespace: {namespace}] Section: {meta.get('section_title', '')} | Page: {meta.get('page', '')}")
        print(f"   ...{meta.get('text', '')[:200]}...")

    print(f"\n=== BM25 (Sparse) Results ===")
    sparse_results = bm25_search(query, all_chunks, top_k=TOP_K)
    for i, (chunk, score) in enumerate(sparse_results, 1):
        print(f"{i}. [Score: {score:.4f}] Section: {chunk['metadata'].get('section_title', '')} | Page: {chunk['metadata'].get('page', '')}")
        print(f"   ...{chunk['text'][:200]}...")

    print(f"\n=== Fused & Reranked Results (ALPHA={ALPHA}) ===")
    fused_results = fuse_and_rerank(dense_results, sparse_results, alpha=ALPHA, top_k=TOP_K)
    for i, res in enumerate(fused_results, 1):
        print(f"{i}. [Combined: {res['score_combined']:.4f} | Dense: {res['score_dense']:.4f} | Sparse: {res['score_sparse']:.4f} | Namespace: {res.get('namespace', 'unknown')}] Section: {res['meta'].get('section_title', '')} | Page: {res['meta'].get('page', '')}")
        print(f"   ...{res['meta'].get('text', '')[:200]}...")

    print(f"\n=== Cross-Encoder Reranked Results ===")
    reranked_results = cross_encoder_rerank(query, fused_results)
    for i, res in enumerate(reranked_results, 1):
        print(f"{i}. [Cross-Score: {res.get('cross_score', 0):.4f} | Combined: {res['score_combined']:.4f} | Namespace: {res.get('namespace', 'unknown')}] Section: {res['meta'].get('section_title', '')} | Page: {res['meta'].get('page', '')}")
        print(f"   ...{res['meta'].get('text', '')[:200]}...")

if __name__ == "__main__":
    main() 
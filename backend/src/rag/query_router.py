import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from utils.pdf_chunker import chunk_pdf
from hybrid_retrieval import (
    load_all_chunks, bm25_search, pinecone_search, fuse_and_rerank, cross_encoder_rerank, ALPHA, TOP_K, EMBEDDING_MODEL, INDEX_NAME, DOCS_NAMESPACE, DB_NAMESPACE
)
# For structured queries, import your DB chunking logic
from utils.generate_chunks import ChunkGenerator

# Simple rule-based intent classifier
def classify_intent(query):
    structured_keywords = [
        'quali', 'elenca', 'mostra', 'lista', 'tutti', 'corsi', 'professori', 'studenti', 'anno', 'matricola', 'insegnante', 'corso', 'email', 'contatti', 'dipartimento', 'facoltà', 'review', 'recensioni', 'materiale', 'edizione'
    ]
    query_lower = query.lower()
    for kw in structured_keywords:
        if kw in query_lower:
            return 'structured'
    return 'unstructured'

def structured_retrieval(query, top_k=TOP_K):
    # For demo: BM25 over structured tuples
    generator = ChunkGenerator()
    chunks = generator.get_chunks()
    texts = [chunk['text'] for chunk in chunks]
    from rank_bm25 import BM25Okapi
    tokenized_corpus = [text.split() for text in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.split()
    scores = bm25.get_scores(tokenized_query)
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [(chunks[i], scores[i]) for i in top_indices]

def unstructured_retrieval(query, model, pc, all_chunks):
    dense_results = pinecone_search(query, model, pc, top_k=TOP_K)
    sparse_results = bm25_search(query, all_chunks, top_k=TOP_K)
    fused_results = fuse_and_rerank(dense_results, sparse_results, alpha=ALPHA, top_k=TOP_K)
    reranked_results = cross_encoder_rerank(query, fused_results)
    return reranked_results

def merge_results(structured, unstructured, top_k=TOP_K):
    # Merge by unique text, prefer higher score if duplicate
    seen = {}
    for chunk, score in structured:
        seen[chunk['text']] = {'source': 'structured', 'score': score, 'meta': chunk['metadata'], 'text': chunk['text']}
    for res in unstructured:
        text = res['meta'].get('text', '')
        if text in seen:
            if res.get('cross_score', 0) > seen[text]['score']:
                seen[text] = {'source': 'unstructured', 'score': res.get('cross_score', 0), 'meta': res['meta'], 'text': text}
        else:
            seen[text] = {'source': 'unstructured', 'score': res.get('cross_score', 0), 'meta': res['meta'], 'text': text}
    merged = list(seen.values())
    merged.sort(key=lambda x: x['score'], reverse=True)
    return merged[:top_k]

def main():
    load_dotenv()
    print("\n=== Query Router ===")
    query = input("Enter your query: ")
    intent = classify_intent(query)
    print(f"Detected intent: {intent}")

    model = SentenceTransformer(EMBEDDING_MODEL)
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    all_chunks = load_all_chunks(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data')))

    structured_results = []
    unstructured_results = []

    if intent == 'structured':
        print("\nRunning structured retrieval...")
        structured_results = structured_retrieval(query)
    elif intent == 'unstructured':
        print("\nRunning unstructured (hybrid) retrieval...")
        unstructured_results = unstructured_retrieval(query, model, pc, all_chunks)
    else:
        print("\nRunning both retrieval pipelines...")
        structured_results = structured_retrieval(query)
        unstructured_results = unstructured_retrieval(query, model, pc, all_chunks)

    # Merge if both have results
    if structured_results and unstructured_results:
        print("\nMerging structured and unstructured results...")
        merged = merge_results(structured_results, unstructured_results)
    elif structured_results:
        merged = [
            {'source': 'structured', 'score': score, 'meta': chunk['metadata'], 'text': chunk['text']} 
            for chunk, score in structured_results
        ]
    else:
        merged = [
            {'source': 'unstructured', 'score': res.get('cross_score', 0), 'meta': res['meta'], 'text': res['meta'].get('text', '')}
            for res in unstructured_results
        ]

    print("\n=== Final Merged Results ===")
    for i, res in enumerate(merged, 1):
        print(f"{i}. [Source: {res['source']} | Score: {res['score']:.4f}] Section: {res['meta'].get('section_title', '')} | Page: {res['meta'].get('page', '')}")
        print(f"   ...{res['text'][:200]}...")

if __name__ == "__main__":
    main() 
import os
from typing import List, Dict, Any
from dotenv import load_dotenv
import torch
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from rank_bm25 import BM25Okapi
import numpy as np
from src.local_llm import generate_answer, generate_answer_streaming
from src.text_2_SQL.db_utils import get_db_connection
import time

class RAGSystem:
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 index_name: str = "exams-index",
                 namespace: str = "v6",
                 dimension: int = 384):
        """
        Initialize the RAG system with embedding model and vector store.
        
        Args:
            model_name: Name of the sentence transformer model to use
            index_name: Name of the Pinecone index
            namespace: Namespace in Pinecone where vectors are stored
            dimension: Dimension of the embeddings
        """
        load_dotenv()
        
        # Initialize embedding model, Pinecone, and DB connection
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = SentenceTransformer(model_name, device=self.device)
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(index_name)
        self.namespace = namespace
        self.db_conn = get_db_connection()
    
    def __del__(self):
        if self.db_conn:
            self.db_conn.close()

    def _get_rich_context_from_db(self, table_name: str, primary_key: str) -> str:
        """
        Fetches a rich, human-readable context for a given entity from the database
        by performing targeted JOINs and formatting the result into a paragraph.
        """
        with self.db_conn.cursor() as cur:
            # All table names are lowercase as per previous fixes
            if table_name == 'dipartimento':
                cur.execute("SELECT nome FROM dipartimento WHERE id = %s;", (primary_key,))
                row = cur.fetchone()
                return f"Il dipartimento di '{row[0]}'." if row else ""

            elif table_name == 'facolta':
                query = """
                    SELECT f.nome, f.presidente, f.contatti, d.nome as dept_name 
                    FROM facolta f
                    JOIN dipartimento d ON f.dipartimento_id = d.id
                    WHERE f.id = %s;
                """
                cur.execute(query, (primary_key,))
                row = cur.fetchone()
                if not row: return ""
                nome, presidente, contatti, dept_name = row
                return f"La facoltà di '{nome}', parte del dipartimento di '{dept_name}'. Il presidente è {presidente} e i contatti sono: {contatti}."

            elif table_name == 'corso_di_laurea':
                query = """
                    SELECT c.nome, c.descrizione, c.classe, c.tipologia, f.nome as faculty_name
                    FROM corso_di_laurea c
                    JOIN facolta f ON c.id_facolta = f.id
                    WHERE c.id = %s;
                """
                cur.execute(query, (primary_key,))
                row = cur.fetchone()
                if not row: return ""
                nome, desc, classe, tipo, faculty_name = row
                return f"Il corso di laurea in '{nome}' ({classe}, {tipo}) è offerto dalla facoltà di '{faculty_name}'. Descrizione: {desc or 'N/A'}."

            elif table_name == 'corso':
                query = """
                    SELECT c.nome, c.cfu, c.prerequisiti, c.frequenza_obbligatoria, cdl.nome as degree_name
                    FROM corso c
                    JOIN corso_di_laurea cdl ON c.id_corso = cdl.id
                    WHERE c.id = %s;
                """
                cur.execute(query, (primary_key,))
                row = cur.fetchone()
                if not row: return ""
                nome, cfu, prerequisiti, freq, degree_name = row
                return f"Il corso '{nome}' fa parte del corso di laurea in '{degree_name}'. Ha {cfu} CFU, i suoi prerequisiti sono '{prerequisiti or 'nessuno'}', e la frequenza è '{freq or 'non specificata'}'."

            elif table_name == 'edizionecorso':
                query = """
                    SELECT c.nome as course_name, u.nome as prof_nome, u.cognome as prof_cognome,
                           ec.data, ec.mod_esame
                    FROM edizionecorso ec
                    JOIN corso c ON ec.id = c.id
                    JOIN insegnanti i ON ec.insegnante = i.id
                    JOIN utente u ON i.id = u.id
                    WHERE ec.id = %s;
                """
                cur.execute(query, (primary_key,))
                row = cur.fetchone()
                if not row: return ""
                course_name, prof_nome, prof_cognome, data, mod_esame = row
                return f"Il corso di '{course_name}' è tenuto dal professore {prof_nome} {prof_cognome} nel periodo '{data}'. La modalità d'esame è: {mod_esame}."

            elif table_name == 'materiale_didattico':
                query = """
                    SELECT m.tipo, m.verificato, c.nome as course_name, u.nome as uploader_nome, u.cognome as uploader_cognome
                    FROM materiale_didattico m
                    JOIN corso c ON m.course_id = c.id
                    JOIN utente u ON m.utente_id = u.id
                    WHERE m.id = %s;
                """
                cur.execute(query, (primary_key,))
                row = cur.fetchone()
                if not row: return ""
                tipo, verificato, course_name, uploader_nome, uploader_cognome = row
                return f"Un file di tipo '{tipo}' per il corso di '{course_name}' è stato caricato da {uploader_nome} {uploader_cognome}. Stato di verifica: {'verificato' if verificato else 'non verificato'}."

            elif table_name == 'review':
                query = """
                    SELECT r.descrizione, r.voto, c.nome as course_name, u.nome as student_nome, u.cognome as student_cognome
                    FROM review r
                    JOIN edizionecorso ec ON r.edition_id = ec.id
                    JOIN corso c ON ec.id = c.id
                    JOIN studenti s ON r.student_id = s.id
                    JOIN utente u ON s.id = u.id
                    WHERE r.id = %s;
                """
                cur.execute(query, (primary_key,))
                row = cur.fetchone()
                if not row: return ""
                desc, voto, course_name, student_nome, student_cognome = row
                return f"Recensione di {student_nome} {student_cognome} per il corso di '{course_name}': '{desc or 'Nessun commento'}'. Voto: {voto}/5."

            else:
                # No fallback for primary entities
                return ""

    def _rerank_with_bm25(self, query: str, documents: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Reranks a list of documents based on BM25 scores.
        Now works with a list of document dictionaries.
        """
        texts = [doc['metadata']['text'] for doc in documents]
        tokenized_corpus = [doc.split(" ") for doc in texts]
        bm25 = BM25Okapi(tokenized_corpus)
        tokenized_query = query.split(" ")
        doc_scores = bm25.get_scores(tokenized_query)
        
        # Get the top N indices
        top_n_indices = np.argsort(doc_scores)[::-1][:top_n]
        
        # Return the top N documents
        return [documents[i] for i in top_n_indices]

    def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for a single text."""
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        return self.model.encode(texts).tolist()
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of dicts with 'id', 'text', and optional 'metadata'
        """
        vectors = []
        for doc in documents:
            vector = {
                "id": doc["id"],
                "values": self.embed_text(doc["text"]),
                "metadata": {"text": doc["text"], **doc.get("metadata", {})}
            }
            vectors.append(vector)
        
        # Upsert in batches of 100
        for i in range(0, len(vectors), 100):
            batch = vectors[i:i + 100]
            self.index.upsert(vectors=batch, namespace=self.namespace)
    
    def query(self, 
             query_text: str, 
             top_k: int = 20,
             rerank_top_k: int = 5,
             filter: Dict = None) -> List[Dict[str, Any]]:
        """
        Query the vector store for similar documents, then rerank with BM25.
        
        Args:
            query_text: The query text
            top_k: Number of results to return from vector store
            rerank_top_k: Number of results to return after BM25 reranking
            filter: Optional metadata filter
            
        Returns:
            List of dictionaries containing matched documents and their metadata
        """
        # Step 1: Semantic search in Pinecone
        query_vector = self.embed_text(query_text)
        results = self.index.query(
            namespace=self.namespace,
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        
        matches = results.matches
        
        if not matches:
            return []

        # Step 2: Rerank with BM25
        reranked_matches = self._rerank_with_bm25(
            query_text, matches, top_n=rerank_top_k
        )
        
        # Step 3: Fetch rich context from RDBMS for the top results
        final_context_list = []
        for match in reranked_matches:
            metadata = match.metadata
            table = metadata.get("table_name")
            pk = metadata.get("primary_key")
            
            if table and pk is not None:
                # This is where the "join" happens
                rich_context = self._get_rich_context_from_db(table, pk)
                final_context_list.append(rich_context)
            else:
                # Fallback for old data or malformed metadata
                final_context_list.append(metadata.get("text", ""))

        # The 'matches' are now strings of rich context
        return final_context_list

    def generate_response_streaming(self, 
                                  query: str, 
                                  top_k: int = 20,
                                  rerank_top_k: int = 5,
                                  filter: Dict = None) -> Dict[str, Any]:
        """
        Generate a streaming response using the RAG pipeline.
        
        Args:
            query: The user's question
            top_k: Number of relevant documents to retrieve
            rerank_top_k: Number of results to return after BM25 reranking
            filter: Optional metadata filter
            
        Returns:
            Dictionary containing the response stream and timing information
        """
        start_time = time.time()
        
        # Step 1: Retrieve and build rich context
        retrieval_start = time.time()
        # The query method now returns a list of context strings
        context_list = self.query(query, top_k=top_k, rerank_top_k=rerank_top_k, filter=filter)
        retrieval_time = time.time() - retrieval_start
        
        if not context_list:
            return {
                "response_stream": ["I couldn't find any relevant information to answer your question."],
                "retrieval_time": retrieval_time,
                "generation_time": 0,
                "total_time": time.time() - start_time,
                "context_used": []
            }
        
        # Step 2: Prepare context
        context = "\n\n---\n\n".join(context_list)
        
        # Step 3: Generate streaming response
        generation_start = time.time()
        response_stream = generate_answer_streaming(context, query)
        generation_time = time.time() - generation_start
        
        return {
            "response_stream": response_stream,
            "retrieval_time": retrieval_time,
            "generation_time": generation_time,
            "total_time": time.time() - start_time,
            "context_used": context_list
        }

    def generate_response(self, 
                         query: str, 
                         top_k: int = 20,
                         rerank_top_k: int = 5,
                         filter: Dict = None) -> Dict[str, Any]:
        """
        Generate a response using the RAG pipeline.
        
        Args:
            query: The user's question
            top_k: Number of relevant documents to retrieve
            rerank_top_k: Number of results to return after BM25 reranking
            filter: Optional metadata filter
            
        Returns:
            Dictionary containing the response and timing information
        """
        start_time = time.time()
        
        # Step 1: Retrieve and build rich context
        retrieval_start = time.time()
        context_list = self.query(query, top_k=top_k, rerank_top_k=rerank_top_k, filter=filter)
        retrieval_time = time.time() - retrieval_start
        
        if not context_list:
            return {
                "response": "I couldn't find any relevant information to answer your question.",
                "retrieval_time": retrieval_time,
                "generation_time": 0,
                "total_time": time.time() - start_time,
                "context_used": []
            }
        
        # Step 2: Prepare context
        context = "\n\n---\n\n".join(context_list)
        
        # Step 3: Generate response
        generation_start = time.time()
        response = generate_answer(context, query)
        generation_time = time.time() - generation_start
        
        return {
            "response": response,
            "retrieval_time": retrieval_time,
            "generation_time": generation_time,
            "total_time": time.time() - start_time,
            "context_used": context_list
        }

def main():
    """Example usage of the RAG system."""
    # Initialize RAG system
    rag = RAGSystem()
    
    # Example query
    query = "What exams were given by Professor Smith in 2023?"
    result = rag.generate_response(query)
    
    print(f"\nQuery: {query}")
    print(f"\nResponse: {result['response']}")
    print(f"\nTiming:")
    print(f"Retrieval time: {result['retrieval_time']:.2f}s")
    print(f"Generation time: {result['generation_time']:.2f}s")
    print(f"Total time: {result['total_time']:.2f}s")
    
    print("\nContext used:")
    for i, context in enumerate(result['context_used'], 1):
        print(f"\n{i}. {context}")

if __name__ == "__main__":
    main() 
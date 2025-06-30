import os
import pytest
from dotenv import load_dotenv
from src.rag.rag_core import RAGSystem
from ..src.rag.utils.vector_db import NAMESPACE

@pytest.fixture(scope="module")
def rag_system():
    load_dotenv()
    pinecone_key = os.getenv("PINECONE_API_KEY")
    assert pinecone_key, "PINECONE_API_KEY not found in .env file"
    rag = RAGSystem(
        model_name="all-MiniLM-L6-v2",
        index_name="exams-index",
        namespace=NAMESPACE
    )
    return rag

# Le query da testare (puoi aggiungerne altre)
QUERIES = [
    # "What exams were given by Professor Smith in 2023?",
    "Which textbooks were used in the Database Systems course?",
    # "List all exams held in room A101",
    # "What courses were taught by Professor Johnson?",
    "Show me all exams from 2022 that used Machine Learning textbooks"
]

@pytest.mark.parametrize("query", QUERIES)
def test_rag_benchmark(rag_system, query):
    # Esegui 3 run per ogni query e controlla che la risposta sia non vuota
    num_runs = 3
    responses = []
    retrieval_times = []
    generation_times = []
    total_times = []

    for _ in range(num_runs):
        result = rag_system.generate_response(query)
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0
        assert "retrieval_time" in result
        assert "generation_time" in result
        assert "total_time" in result
        responses.append(result["response"])
        retrieval_times.append(result["retrieval_time"])
        generation_times.append(result["generation_time"])
        total_times.append(result["total_time"])

    # Stampa i risultati medi (opzionale, utile per debug)
    avg_retrieval = sum(retrieval_times) / num_runs
    avg_generation = sum(generation_times) / num_runs
    avg_total = sum(total_times) / num_runs
    print(f"\nQuery: {query}")
    print(f"Average Retrieval Time: {avg_retrieval:.3f}s")
    print(f"Average Generation Time: {avg_generation:.3f}s")
    print(f"Average Total Time: {avg_total:.3f}s")
    print(f"Sample Response: {responses[0]}")
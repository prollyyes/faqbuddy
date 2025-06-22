from src.rag.rag_core import RAGSystem
import os
from dotenv import load_dotenv
import sys
import json
from datetime import datetime

def run_benchmark(rag, queries, num_runs=3):
    """
    Run benchmark tests on the RAG system.
    
    Args:
        rag: RAGSystem instance
        queries: List of test queries
        num_runs: Number of runs per query for averaging
    
    Returns:
        Dictionary containing benchmark results
    """
    results = {
        "timestamp": datetime.now().isoformat(),
        "queries": {},
        "averages": {
            "retrieval_time": 0,
            "generation_time": 0,
            "total_time": 0
        }
    }
    
    total_retrieval = 0
    total_generation = 0
    total_time = 0
    
    for query in queries:
        print(f"\n📝 Testing query: {query}")
        query_results = []
        
        for run in range(num_runs):
            print(f"  Run {run + 1}/{num_runs}...")
            result = rag.generate_response(query)
            query_results.append({
                "retrieval_time": result["retrieval_time"],
                "generation_time": result["generation_time"],
                "total_time": result["total_time"],
                "response": result["response"]
            })
            
            total_retrieval += result["retrieval_time"]
            total_generation += result["generation_time"]
            total_time += result["total_time"]
        
        # Calculate averages for this query
        avg_retrieval = sum(r["retrieval_time"] for r in query_results) / num_runs
        avg_generation = sum(r["generation_time"] for r in query_results) / num_runs
        avg_total = sum(r["total_time"] for r in query_results) / num_runs
        
        results["queries"][query] = {
            "runs": query_results,
            "averages": {
                "retrieval_time": avg_retrieval,
                "generation_time": avg_generation,
                "total_time": avg_total
            }
        }
    
    # Calculate overall averages
    num_queries = len(queries)
    results["averages"] = {
        "retrieval_time": total_retrieval / (num_queries * num_runs),
        "generation_time": total_generation / (num_queries * num_runs),
        "total_time": total_time / (num_queries * num_runs)
    }
    
    return results

def print_benchmark_results(results):
    """Print benchmark results in a readable format."""
    print("\n📊 Benchmark Results")
    print("=" * 50)
    print(f"Timestamp: {results['timestamp']}")
    print("\nPer Query Results:")
    print("-" * 50)
    
    for query, data in results["queries"].items():
        print(f"\nQuery: {query}")
        print(f"Average Retrieval Time: {data['averages']['retrieval_time']:.3f}s")
        print(f"Average Generation Time: {data['averages']['generation_time']:.3f}s")
        print(f"Average Total Time: {data['averages']['total_time']:.3f}s")
        print("\nSample Response:")
        print(data['runs'][0]['response'])
        print("-" * 50)
    
    print("\nOverall Averages:")
    print(f"Average Retrieval Time: {results['averages']['retrieval_time']:.3f}s")
    print(f"Average Generation Time: {results['averages']['generation_time']:.3f}s")
    print(f"Average Total Time: {results['averages']['total_time']:.3f}s")

def save_benchmark_results(results, filename=None):
    """Save benchmark results to a JSON file."""
    if filename is None:
        filename = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved to {filename}")

def test_rag():
    # Load environment variables
    load_dotenv()
    
    # Check for Pinecone API key
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ Error: PINECONE_API_KEY not found in .env file")
        print("Please create a .env file with your Pinecone API key:")
        print("PINECONE_API_KEY=your_api_key_here")
        sys.exit(1)
    
    try:
        # Initialize RAG system
        print("🔄 Initializing RAG system...")
        rag = RAGSystem(
            model_name="all-MiniLM-L6-v2",
            index_name="exams-index",
            namespace="v6"
        )
        print("✅ RAG system initialized successfully")
        
        # Test queries
        queries = [
            "What exams were given by Professor Smith in 2023?",
            "Which textbooks were used in the Database Systems course?",
            "List all exams held in room A101",
            "What courses were taught by Professor Johnson?",
            "Show me all exams from 2022 that used Machine Learning textbooks"
        ]
        
        # Run benchmark
        print("\n🔍 Starting benchmark tests...")
        results = run_benchmark(rag, queries, num_runs=3)
        
        # Print results
        print_benchmark_results(results)
        
        # Save results
        # save_benchmark_results(results)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    test_rag()
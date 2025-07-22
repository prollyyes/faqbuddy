#!/usr/bin/env python3
"""
Simple test script for the RAG benchmark tool
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from benchmark_rag_comparison import RAGBenchmark

def test_benchmark():
    """Test the benchmark with a few queries."""
    print("🧪 Testing RAG Benchmark Tool...")
    
    # Initialize benchmark
    benchmark = RAGBenchmark()
    
    # Test with just 3 queries for quick testing
    test_queries = [
        "Chi insegna il corso di Sistemi Operativi?",
        "Quali sono i requisiti per l'iscrizione?",
        "Come funziona il sistema di crediti?",
        "Chi insegna il corso di Basi di Dati?"
    ]
    
    try:
        # Run benchmark
        print(f"\n🏁 Running test benchmark with {len(test_queries)} queries...")
        results = benchmark.run_benchmark(test_queries)
        
        # Calculate metrics
        metrics = benchmark.calculate_performance_metrics()
        
        # Print summary
        print("\n📊 TEST RESULTS SUMMARY:")
        print(f"   Total queries: {metrics.total_queries}")
        print(f"   RAG v1 avg time: {metrics.avg_response_time_v1:.2f}s")
        print(f"   RAG v2 avg time: {metrics.avg_response_time_v2:.2f}s")
        print(f"   RAG v2 avg sources: {metrics.avg_sources_v2:.1f}")
        print(f"   RAG v2 avg confidence: {metrics.avg_confidence_v2:.1%}")
        
        # Export results
        benchmark.export_to_csv("test_benchmark_results.csv")
        benchmark.export_to_json("test_benchmark_results.json")
        
        print("\n✅ Test completed successfully!")
        print("   Check test_benchmark_results.csv and test_benchmark_results.json for details")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_benchmark() 
#!/usr/bin/env python3
"""
RAG Benchmark Comparison Tool
=============================

This script provides a comprehensive comparison between the original RAG implementation
and the new RAG v2 system, allowing you to evaluate performance, accuracy, and features.

Usage:
    python benchmark_rag_comparison.py --help
    python benchmark_rag_comparison.py --compare-all
    python benchmark_rag_comparison.py --test-queries queries.txt
    python benchmark_rag_comparison.py --performance-only
"""

import os
import sys
import time
import json
import argparse
import statistics
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import pandas as pd
from pathlib import Path

# Add backend/src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

# Import both RAG implementations
from backend.src.rag.rag_pipeline import RAGPipeline
from backend.src.rag.rag_pipeline_v2 import RAGv2Pipeline

@dataclass
class BenchmarkResult:
    """Structured result for benchmark comparisons."""
    query: str
    rag_v1_answer: str
    rag_v2_answer: str
    rag_v1_time: float
    rag_v2_time: float
    rag_v1_sources: int
    rag_v2_sources: int
    rag_v1_confidence: float
    rag_v2_confidence: float
    rag_v1_features: Dict[str, bool]
    rag_v2_features: Dict[str, bool]
    timestamp: str

@dataclass
class PerformanceMetrics:
    """Performance metrics for comparison."""
    avg_response_time_v1: float
    avg_response_time_v2: float
    avg_sources_v1: float
    avg_sources_v2: float
    avg_confidence_v1: float
    avg_confidence_v2: float
    total_queries: int
    v2_improvement_time: float  # Percentage improvement
    v2_improvement_sources: float
    v2_improvement_confidence: float

class RAGBenchmark:
    """Comprehensive benchmark tool for RAG comparison."""
    
    def __init__(self):
        """Initialize the benchmark tool."""
        self.results: List[BenchmarkResult] = []
        self.performance_metrics: PerformanceMetrics = None
        
        # Default test queries
        self.default_queries = [
            "Chi insegna il corso di Sistemi Operativi?",
            "Quali sono i requisiti per l'iscrizione al corso di laurea?",
            "Come si svolge l'esame di Analisi Matematica?",
            "Quali sono le modalità di tirocinio?",
            "Come funziona il sistema di crediti?",
            "Quali sono i corsi obbligatori del primo anno?",
            "Come si richiede la laurea?",
            "Quali sono le scadenze per gli esami?",
            "Come funziona il sistema di valutazione?",
            "Quali sono i contatti del dipartimento?"
        ]
        
        print("🚀 Initializing RAG Benchmark Tool...")
        print("   This will load both RAG implementations for comparison")
        
    def load_models(self) -> Tuple[RAGPipeline, RAGv2Pipeline]:
        """Load both RAG models."""
        print("\n📦 Loading RAG Models...")
        
        # Load RAG v1 (Original)
        print("   Loading RAG v1 (Original)...")
        try:
            rag_v1 = RAGPipeline()
            print("   ✅ RAG v1 loaded successfully")
        except Exception as e:
            print(f"   ❌ Failed to load RAG v1: {e}")
            raise
        
        # Load RAG v2 (Enhanced)
        print("   Loading RAG v2 (Enhanced)...")
        try:
            rag_v2 = RAGv2Pipeline()
            print("   ✅ RAG v2 loaded successfully")
        except Exception as e:
            print(f"   ❌ Failed to load RAG v2: {e}")
            raise
        
        return rag_v1, rag_v2
    
    def run_single_comparison(self, query: str, rag_v1: RAGPipeline, rag_v2: RAGv2Pipeline) -> BenchmarkResult:
        """Run a single query comparison between RAG v1 and v2."""
        print(f"\n🔍 Testing Query: {query}")
        
        # Test RAG v1
        print("   Testing RAG v1...")
        start_time = time.time()
        try:
            v1_result = rag_v1.answer(query)
            v1_time = time.time() - start_time
            v1_answer = v1_result
            v1_sources = 0  # RAG v1 doesn't provide source count
            v1_confidence = 0.0  # RAG v1 doesn't provide confidence
            v1_features = {"basic_rag": True}
        except Exception as e:
            print(f"   ❌ RAG v1 failed: {e}")
            v1_time = time.time() - start_time
            v1_answer = f"Error: {str(e)}"
            v1_sources = 0
            v1_confidence = 0.0
            v1_features = {"basic_rag": True}
        
        # Test RAG v2
        print("   Testing RAG v2...")
        start_time = time.time()
        try:
            v2_result = rag_v2.answer(query)
            v2_time = time.time() - start_time
            v2_answer = v2_result.get("answer", "No answer generated")
            v2_sources = v2_result.get("retrieved_documents", 0)
            v2_confidence = v2_result.get("confidence", 0.0)
            v2_features = v2_result.get("features_used", {})
        except Exception as e:
            print(f"   ❌ RAG v2 failed: {e}")
            v2_time = time.time() - start_time
            v2_answer = f"Error: {str(e)}"
            v2_sources = 0
            v2_confidence = 0.0
            v2_features = {}
        
        # Create result
        result = BenchmarkResult(
            query=query,
            rag_v1_answer=v1_answer,
            rag_v2_answer=v2_answer,
            rag_v1_time=v1_time,
            rag_v2_time=v2_time,
            rag_v1_sources=v1_sources,
            rag_v2_sources=v2_sources,
            rag_v1_confidence=v1_confidence,
            rag_v2_confidence=v2_confidence,
            rag_v1_features=v1_features,
            rag_v2_features=v2_features,
            timestamp=datetime.now().isoformat()
        )
        
        print(f"   ✅ Comparison completed")
        print(f"      RAG v1: {v1_time:.2f}s, {v1_sources} sources")
        print(f"      RAG v2: {v2_time:.2f}s, {v2_sources} sources, {v2_confidence:.1%} confidence")
        
        return result
    
    def run_benchmark(self, queries: List[str] = None) -> List[BenchmarkResult]:
        """Run comprehensive benchmark on provided queries."""
        if queries is None:
            queries = self.default_queries
        
        print(f"\n🏁 Starting Benchmark with {len(queries)} queries...")
        
        # Load models
        rag_v1, rag_v2 = self.load_models()
        
        # Run comparisons
        results = []
        for i, query in enumerate(queries, 1):
            print(f"\n📊 Progress: {i}/{len(queries)}")
            result = self.run_single_comparison(query, rag_v1, rag_v2)
            results.append(result)
        
        self.results = results
        return results
    
    def calculate_performance_metrics(self) -> PerformanceMetrics:
        """Calculate performance metrics from benchmark results."""
        if not self.results:
            raise ValueError("No benchmark results available. Run benchmark first.")
        
        # Extract metrics
        v1_times = [r.rag_v1_time for r in self.results]
        v2_times = [r.rag_v2_time for r in self.results]
        v1_sources = [r.rag_v1_sources for r in self.results]
        v2_sources = [r.rag_v2_sources for r in self.results]
        v1_confidence = [r.rag_v1_confidence for r in self.results]
        v2_confidence = [r.rag_v2_confidence for r in self.results]
        
        # Calculate averages
        avg_time_v1 = statistics.mean(v1_times)
        avg_time_v2 = statistics.mean(v2_times)
        avg_sources_v1 = statistics.mean(v1_sources)
        avg_sources_v2 = statistics.mean(v2_sources)
        avg_confidence_v1 = statistics.mean(v1_confidence)
        avg_confidence_v2 = statistics.mean(v2_confidence)
        
        # Calculate improvements
        time_improvement = ((avg_time_v1 - avg_time_v2) / avg_time_v1) * 100 if avg_time_v1 > 0 else 0
        sources_improvement = ((avg_sources_v2 - avg_sources_v1) / avg_sources_v1) * 100 if avg_sources_v1 > 0 else 0
        confidence_improvement = ((avg_confidence_v2 - avg_confidence_v1) / avg_confidence_v1) * 100 if avg_confidence_v1 > 0 else 0
        
        self.performance_metrics = PerformanceMetrics(
            avg_response_time_v1=avg_time_v1,
            avg_response_time_v2=avg_time_v2,
            avg_sources_v1=avg_sources_v1,
            avg_sources_v2=avg_sources_v2,
            avg_confidence_v1=avg_confidence_v1,
            avg_confidence_v2=avg_confidence_v2,
            total_queries=len(self.results),
            v2_improvement_time=time_improvement,
            v2_improvement_sources=sources_improvement,
            v2_improvement_confidence=confidence_improvement
        )
        
        return self.performance_metrics
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate a comprehensive benchmark report."""
        if not self.results:
            raise ValueError("No benchmark results available. Run benchmark first.")
        
        if not self.performance_metrics:
            self.calculate_performance_metrics()
        
        # Create report
        report = []
        report.append("=" * 80)
        report.append("RAG BENCHMARK COMPARISON REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Queries: {self.performance_metrics.total_queries}")
        report.append("")
        
        # Performance Summary
        report.append("📊 PERFORMANCE SUMMARY")
        report.append("-" * 40)
        report.append(f"Average Response Time:")
        report.append(f"  RAG v1: {self.performance_metrics.avg_response_time_v1:.2f}s")
        report.append(f"  RAG v2: {self.performance_metrics.avg_response_time_v2:.2f}s")
        report.append(f"  Improvement: {self.performance_metrics.v2_improvement_time:+.1f}%")
        report.append("")
        
        report.append(f"Average Sources Retrieved:")
        report.append(f"  RAG v1: {self.performance_metrics.avg_sources_v1:.1f}")
        report.append(f"  RAG v2: {self.performance_metrics.avg_sources_v2:.1f}")
        report.append(f"  Improvement: {self.performance_metrics.v2_improvement_sources:+.1f}%")
        report.append("")
        
        report.append(f"Average Confidence Score:")
        report.append(f"  RAG v1: {self.performance_metrics.avg_confidence_v1:.1%}")
        report.append(f"  RAG v2: {self.performance_metrics.avg_confidence_v2:.1%}")
        report.append(f"  Improvement: {self.performance_metrics.v2_improvement_confidence:+.1f}%")
        report.append("")
        
        # Feature Comparison
        report.append("🚀 FEATURE COMPARISON")
        report.append("-" * 40)
        report.append("RAG v1 Features:")
        report.append("  ✅ Basic retrieval")
        report.append("  ✅ Simple answer generation")
        report.append("  ❌ No confidence scoring")
        report.append("  ❌ No source attribution")
        report.append("  ❌ No advanced features")
        report.append("")
        
        report.append("RAG v2 Features:")
        report.append("  ✅ Schema-aware chunking")
        report.append("  ✅ Instructor-XL embeddings")
        report.append("  ✅ Cross-encoder reranking")
        report.append("  ✅ BM25 fallback")
        report.append("  ✅ Graph-RAG integration")
        report.append("  ✅ CDC incremental sync")
        report.append("  ✅ PDF boost")
        report.append("  ✅ Observability & metrics")
        report.append("  ✅ Confidence scoring")
        report.append("  ✅ Source attribution")
        report.append("")
        
        # Detailed Results
        report.append("📋 DETAILED RESULTS")
        report.append("-" * 40)
        for i, result in enumerate(self.results, 1):
            report.append(f"Query {i}: {result.query}")
            report.append(f"  RAG v1: {result.rag_v1_time:.2f}s | {result.rag_v1_sources} sources")
            report.append(f"  RAG v2: {result.rag_v2_time:.2f}s | {result.rag_v2_sources} sources | {result.rag_v2_confidence:.1%} confidence")
            report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 40)
        if self.performance_metrics.v2_improvement_time > 0:
            report.append("✅ RAG v2 shows performance improvements")
        else:
            report.append("⚠️  RAG v2 may be slower but offers more features")
        
        if self.performance_metrics.v2_improvement_sources > 0:
            report.append("✅ RAG v2 retrieves more relevant sources")
        
        if self.performance_metrics.v2_improvement_confidence > 0:
            report.append("✅ RAG v2 provides better confidence scoring")
        
        report.append("✅ RAG v2 offers significantly more features and capabilities")
        report.append("✅ RAG v2 provides better observability and debugging")
        
        report_text = "\n".join(report)
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"📄 Report saved to: {output_file}")
        
        return report_text
    
    def export_to_csv(self, output_file: str = "benchmark_results.csv"):
        """Export benchmark results to CSV format."""
        if not self.results:
            raise ValueError("No benchmark results available. Run benchmark first.")
        
        # Convert results to DataFrame
        data = []
        for result in self.results:
            data.append({
                'query': result.query,
                'rag_v1_answer': result.rag_v1_answer,
                'rag_v2_answer': result.rag_v2_answer,
                'rag_v1_time': result.rag_v1_time,
                'rag_v2_time': result.rag_v2_time,
                'rag_v1_sources': result.rag_v1_sources,
                'rag_v2_sources': result.rag_v2_sources,
                'rag_v1_confidence': result.rag_v1_confidence,
                'rag_v2_confidence': result.rag_v2_confidence,
                'timestamp': result.timestamp
            })
        
        df = pd.DataFrame(data)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"📊 Results exported to CSV: {output_file}")
        
        return output_file
    
    def export_to_json(self, output_file: str = "benchmark_results.json"):
        """Export benchmark results to JSON format."""
        if not self.results:
            raise ValueError("No benchmark results available. Run benchmark first.")
        
        # Prepare data
        data = {
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'total_queries': len(self.results),
                'benchmark_version': '1.0'
            },
            'performance_metrics': asdict(self.performance_metrics) if self.performance_metrics else None,
            'results': [asdict(result) for result in self.results]
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Results exported to JSON: {output_file}")
        return output_file

def load_queries_from_file(file_path: str) -> List[str]:
    """Load queries from a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        return queries
    except FileNotFoundError:
        print(f"❌ Query file not found: {file_path}")
        return []

def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description="RAG Benchmark Comparison Tool")
    parser.add_argument("--compare-all", action="store_true", 
                       help="Run full benchmark with default queries")
    parser.add_argument("--test-queries", type=str, metavar="FILE",
                       help="Load queries from file and run benchmark")
    parser.add_argument("--performance-only", action="store_true",
                       help="Run performance-only benchmark (faster)")
    parser.add_argument("--output-report", type=str, metavar="FILE",
                       help="Save detailed report to file")
    parser.add_argument("--export-csv", type=str, metavar="FILE",
                       help="Export results to CSV file")
    parser.add_argument("--export-json", type=str, metavar="FILE",
                       help="Export results to JSON file")
    parser.add_argument("--interactive", action="store_true",
                       help="Run interactive benchmark mode")
    
    args = parser.parse_args()
    
    # Initialize benchmark
    benchmark = RAGBenchmark()
    
    try:
        if args.interactive:
            print("🎯 Interactive Benchmark Mode")
            print("Enter queries one by one (type 'done' to finish):")
            queries = []
            while True:
                query = input("\nEnter query: ").strip()
                if query.lower() == 'done':
                    break
                if query:
                    queries.append(query)
            
            if queries:
                benchmark.run_benchmark(queries)
            else:
                print("No queries provided.")
                return
        
        elif args.test_queries:
            queries = load_queries_from_file(args.test_queries)
            if queries:
                benchmark.run_benchmark(queries)
            else:
                print("No valid queries found in file.")
                return
        
        elif args.compare_all or args.performance_only:
            benchmark.run_benchmark()
        
        else:
            parser.print_help()
            return
        
        # Generate outputs
        if args.output_report:
            report = benchmark.generate_report(args.output_report)
        else:
            report = benchmark.generate_report()
            print("\n" + report)
        
        if args.export_csv:
            benchmark.export_to_csv(args.export_csv)
        elif args.export_json:
            benchmark.export_to_json(args.export_json)
        else:
            # Default exports
            benchmark.export_to_csv()
            benchmark.export_to_json()
        
        print("\n✅ Benchmark completed successfully!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
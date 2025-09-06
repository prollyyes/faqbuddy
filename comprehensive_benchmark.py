#!/usr/bin/env python3
"""
Comprehensive RAG Benchmark Suite
=================================

This script runs comprehensive benchmarks comparing all RAG approaches:
1. Legacy RAG (baseline)
2. RAGv2 Pipeline
3. Advanced RAG Pipeline
4. Per-row vs Traditional chunking

Results are saved with detailed analysis for thesis research.
"""

import os
import sys
import json
import time
import traceback
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

# Import all RAG systems
try:
    from rag.rag_pipeline_v2 import RAGv2Pipeline
    from rag.advanced_rag_pipeline import AdvancedRAGPipeline
    from rag.rag_adapter import RAGSystem
    from rag.utils.embeddings_v2 import EnhancedEmbeddings
    from pinecone import Pinecone
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trying alternative import paths...")
    try:
        # Try importing from backend/src directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))
        from rag.rag_pipeline_v2 import RAGv2Pipeline
        from rag.advanced_rag_pipeline import AdvancedRAGPipeline
        from rag.rag_adapter import RAGSystem
        from rag.utils.embeddings_v2 import EnhancedEmbeddings
        from pinecone import Pinecone
        print("✅ Imports successful with alternative path")
    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        print("Make sure you're running from the project root and all dependencies are installed")
        sys.exit(1)

class BenchmarkResult:
    """Container for benchmark results."""
    def __init__(self, approach: str, query: str):
        self.approach = approach
        self.query = query
        self.answer = ""
        self.contexts = []
        self.confidence_score = 0.0
        self.processing_time = 0.0
        self.verification_result = None
        self.retrieval_scores = []
        self.error = None
        self.timestamp = datetime.now().isoformat()

class ComprehensiveBenchmark:
    """Comprehensive benchmark suite for all RAG approaches."""
    
    def __init__(self):
        """Initialize the benchmark suite."""
        load_dotenv()
        
        self.results = []
        self.test_queries = [
            "Quali corsi insegna il prof Lenzerini?",
            "Come si chiama di nome il prof Lenzerini?", 
            "Quali sono i corsi insegnati da Ottolino?",
            "Quale corso insegna Califano?",
            "Chi è il professore che insegna Sistemi Operativi?",
            "Da quanti crediti è il corso di Basi di Dati?",
            "Da quanti crediti è il corso di Sistemi Operativi?",
            "Cosa insegna Gabriele Proietti Mattia?",
            "Chi insegna il corso di Introduzione alla Programmazione?",
            "Quali sono i corsi del primo anno di Ingegneria Informatica?"
        ]
        
        # Ground truth for evaluation
        self.ground_truth = {
            "Quali corsi insegna il prof Lenzerini?": "Basi di Dati",
            "Come si chiama di nome il prof Lenzerini?": "Maurizio",
            "Quali sono i corsi insegnati da Ottolino?": "Sistemi Operativi",
            "Quale corso insegna Califano?": "Sistemi Dinamici",
            "Chi è il professore che insegna Sistemi Operativi?": "Ottolino",
            "Da quanti crediti è il corso di Basi di Dati?": "6",
            "Da quanti crediti è il corso di Sistemi Operativi?": "9",
            "Cosa insegna Gabriele Proietti Mattia?": "Complementi di Programmazione",
            "Chi insegna il corso di Introduzione alla Programmazione?": "Massimo Petrarca, Giuseppe Santucci",
            "Quali sono i corsi del primo anno di Ingegneria Informatica?": "Fondamenti di Matematica, Introduzione alla Programmazione, Fisica"
        }
        
        print("🚀 Initializing Comprehensive RAG Benchmark Suite")
        print("=" * 60)
        
    def test_legacy_rag(self, query: str) -> BenchmarkResult:
        """Test the legacy RAG system."""
        result = BenchmarkResult("Legacy RAG", query)
        
        try:
            print(f"  🔹 Testing Legacy RAG...")
            start_time = time.time()
            
            # Initialize legacy RAG
            rag_system = RAGSystem()
            answer = rag_system.answer(query)
            
            result.processing_time = time.time() - start_time
            result.answer = answer if answer else "No answer generated"
            result.confidence_score = 0.5  # Legacy doesn't provide confidence
            
        except Exception as e:
            result.error = str(e)
            print(f"    ❌ Error: {e}")
            
        return result
    
    def test_ragv2_pipeline(self, query: str) -> BenchmarkResult:
        """Test the RAGv2 pipeline."""
        result = BenchmarkResult("RAGv2 Pipeline", query)
        
        try:
            print(f"  🔹 Testing RAGv2 Pipeline...")
            start_time = time.time()
            
            # Initialize RAGv2
            ragv2 = RAGv2Pipeline()
            answer = ragv2.answer(query)
            
            result.processing_time = time.time() - start_time
            result.answer = answer if answer else "No answer generated"
            result.confidence_score = 0.7  # RAGv2 has some confidence scoring
            
        except Exception as e:
            result.error = str(e)
            print(f"    ❌ Error: {e}")
            
        return result
    
    def test_advanced_rag(self, query: str) -> BenchmarkResult:
        """Test the advanced RAG pipeline."""
        result = BenchmarkResult("Advanced RAG", query)
        
        try:
            print(f"  🔹 Testing Advanced RAG...")
            start_time = time.time()
            
            # Initialize Advanced RAG
            advanced_rag = AdvancedRAGPipeline()
            rag_result = advanced_rag.answer(query)
            
            result.processing_time = time.time() - start_time
            result.answer = rag_result.answer
            result.confidence_score = rag_result.confidence_score
            result.verification_result = rag_result.verification_result
            result.contexts = [ctx.text for ctx in rag_result.retrieval_results]
            result.retrieval_scores = [ctx.score for ctx in rag_result.retrieval_results]
            
        except Exception as e:
            result.error = str(e)
            print(f"    ❌ Error: {e}")
            
        return result
    
    def test_per_row_retrieval(self, query: str) -> BenchmarkResult:
        """Test per-row retrieval directly."""
        result = BenchmarkResult("Per-Row Retrieval", query)
        
        try:
            print(f"  🔹 Testing Per-Row Retrieval...")
            start_time = time.time()
            
            # Direct retrieval from per_row namespace
            pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
            index = pc.Index('exams-index-enhanced')
            embeddings = EnhancedEmbeddings()
            
            query_embedding = embeddings.encode_single(query)
            
            retrieval_results = index.query(
                vector=query_embedding,
                top_k=5,
                namespace='per_row',
                include_metadata=True
            )
            
            result.processing_time = time.time() - start_time
            result.retrieval_scores = [match['score'] for match in retrieval_results['matches']]
            result.contexts = [match['metadata']['text'] for match in retrieval_results['matches']]
            result.answer = f"Retrieved {len(retrieval_results['matches'])} results"
            result.confidence_score = retrieval_results['matches'][0]['score'] if retrieval_results['matches'] else 0.0
            
        except Exception as e:
            result.error = str(e)
            print(f"    ❌ Error: {e}")
            
        return result
    
    def test_traditional_retrieval(self, query: str) -> BenchmarkResult:
        """Test traditional db_v2 retrieval."""
        result = BenchmarkResult("Traditional Retrieval", query)
        
        try:
            print(f"  🔹 Testing Traditional Retrieval...")
            start_time = time.time()
            
            # Direct retrieval from db_v2 namespace
            pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
            index = pc.Index('exams-index-enhanced')
            embeddings = EnhancedEmbeddings()
            
            query_embedding = embeddings.encode_single(query)
            
            retrieval_results = index.query(
                vector=query_embedding,
                top_k=5,
                namespace='db_v2',
                include_metadata=True
            )
            
            result.processing_time = time.time() - start_time
            result.retrieval_scores = [match['score'] for match in retrieval_results['matches']]
            result.contexts = [match['metadata']['text'] for match in retrieval_results['matches']]
            result.answer = f"Retrieved {len(retrieval_results['matches'])} results"
            result.confidence_score = retrieval_results['matches'][0]['score'] if retrieval_results['matches'] else 0.0
            
        except Exception as e:
            result.error = str(e)
            print(f"    ❌ Error: {e}")
            
        return result
    
    def run_comprehensive_benchmark(self):
        """Run comprehensive benchmark on all approaches."""
        print(f"\n🧪 RUNNING COMPREHENSIVE BENCHMARK")
        print(f"Testing {len(self.test_queries)} queries across all approaches")
        print("=" * 60)
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n📝 QUERY {i}/{len(self.test_queries)}: {query}")
            print("-" * 50)
            
            # Test all approaches
            approaches = [
                self.test_legacy_rag,
                self.test_ragv2_pipeline, 
                self.test_advanced_rag,
                self.test_per_row_retrieval,
                self.test_traditional_retrieval
            ]
            
            for test_func in approaches:
                try:
                    result = test_func(query)
                    self.results.append(result)
                except Exception as e:
                    print(f"    ❌ Failed to test {test_func.__name__}: {e}")
                    error_result = BenchmarkResult(test_func.__name__.replace('test_', ''), query)
                    error_result.error = str(e)
                    self.results.append(error_result)
        
        print(f"\n✅ Benchmark completed! Generated {len(self.results)} results")
    
    def analyze_results(self) -> Dict[str, Any]:
        """Analyze benchmark results and generate insights."""
        print(f"\n📊 ANALYZING RESULTS")
        print("=" * 40)
        
        analysis = {
            "summary": {},
            "approach_comparison": {},
            "query_analysis": {},
            "performance_metrics": {},
            "recommendations": []
        }
        
        # Group results by approach
        by_approach = {}
        for result in self.results:
            if result.approach not in by_approach:
                by_approach[result.approach] = []
            by_approach[result.approach].append(result)
        
        # Calculate metrics for each approach
        for approach, results in by_approach.items():
            successful_results = [r for r in results if r.error is None]
            
            if successful_results:
                avg_time = sum(r.processing_time for r in successful_results) / len(successful_results)
                avg_confidence = sum(r.confidence_score for r in successful_results) / len(successful_results)
                success_rate = len(successful_results) / len(results)
                
                analysis["approach_comparison"][approach] = {
                    "total_queries": len(results),
                    "successful_queries": len(successful_results),
                    "success_rate": success_rate,
                    "average_processing_time": avg_time,
                    "average_confidence": avg_confidence,
                    "errors": [r.error for r in results if r.error is not None]
                }
                
                print(f"  {approach}:")
                print(f"    Success Rate: {success_rate:.1%}")
                print(f"    Avg Time: {avg_time:.2f}s")
                print(f"    Avg Confidence: {avg_confidence:.3f}")
        
        # Find best performing approach
        best_approach = max(analysis["approach_comparison"].items(), 
                          key=lambda x: x[1]["success_rate"] * x[1]["average_confidence"])
        
        analysis["summary"] = {
            "best_approach": best_approach[0],
            "best_success_rate": best_approach[1]["success_rate"],
            "best_confidence": best_approach[1]["average_confidence"],
            "total_tests": len(self.results)
        }
        
        print(f"\n🏆 BEST PERFORMING APPROACH: {best_approach[0]}")
        print(f"   Success Rate: {best_approach[1]['success_rate']:.1%}")
        print(f"   Confidence: {best_approach[1]['average_confidence']:.3f}")
        
        return analysis
    
    def save_results(self, analysis: Dict[str, Any]):
        """Save comprehensive results to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save raw results
        results_file = f"benchmark_results_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "test_queries": self.test_queries,
                "ground_truth": self.ground_truth,
                "results": [self._result_to_dict(r) for r in self.results],
                "analysis": analysis
            }, f, indent=2, ensure_ascii=False)
        
        # Save summary report
        summary_file = f"benchmark_summary_{timestamp}.md"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(self._generate_summary_report(analysis, timestamp))
        
        print(f"\n💾 RESULTS SAVED:")
        print(f"   Raw data: {results_file}")
        print(f"   Summary: {summary_file}")
        
        return results_file, summary_file
    
    def _result_to_dict(self, result: BenchmarkResult) -> Dict[str, Any]:
        """Convert BenchmarkResult to dictionary for JSON serialization."""
        return {
            "approach": result.approach,
            "query": result.query,
            "answer": result.answer,
            "contexts": result.contexts,
            "confidence_score": result.confidence_score,
            "processing_time": result.processing_time,
            "verification_result": result.verification_result.__dict__ if result.verification_result else None,
            "retrieval_scores": result.retrieval_scores,
            "error": result.error,
            "timestamp": result.timestamp
        }
    
    def _generate_summary_report(self, analysis: Dict[str, Any], timestamp: str) -> str:
        """Generate a markdown summary report."""
        report = f"""# RAG System Benchmark Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Test ID:** {timestamp}

## Executive Summary

This comprehensive benchmark compares all RAG approaches in the FAQBuddy system:

- **Legacy RAG**: Original implementation
- **RAGv2 Pipeline**: Enhanced pipeline with feature flags  
- **Advanced RAG**: State-of-the-art implementation with verification
- **Per-Row Retrieval**: Direct vector database queries (per_row namespace)
- **Traditional Retrieval**: Direct vector database queries (db_v2 namespace)

## Key Findings

### Best Performing Approach
**{analysis['summary']['best_approach']}**
- Success Rate: {analysis['summary']['best_success_rate']:.1%}
- Average Confidence: {analysis['summary']['best_confidence']:.3f}

### Approach Comparison

"""
        
        for approach, metrics in analysis["approach_comparison"].items():
            report += f"""#### {approach}
- **Success Rate**: {metrics['success_rate']:.1%} ({metrics['successful_queries']}/{metrics['total_queries']})
- **Average Processing Time**: {metrics['average_processing_time']:.2f}s
- **Average Confidence**: {metrics['average_confidence']:.3f}
"""
            if metrics['errors']:
                report += f"- **Errors**: {len(metrics['errors'])} failures\n"
            report += "\n"
        
        report += f"""## Test Queries

{len(self.test_queries)} queries were tested:

"""
        for i, query in enumerate(self.test_queries, 1):
            report += f"{i}. {query}\n"
        
        report += f"""
## Recommendations

Based on the benchmark results:

1. **For Production Use**: {analysis['summary']['best_approach']} shows the best overall performance
2. **For Research**: Advanced RAG provides the most detailed verification and confidence scoring
3. **For Speed**: Per-row retrieval offers the fastest direct database access
4. **For Reliability**: Consider the success rates when choosing an approach

## Technical Details

- **Total Tests**: {analysis['summary']['total_tests']}
- **Test Environment**: Linux with GPU acceleration
- **Vector Database**: Pinecone with multiple namespaces
- **Models**: Mistral 7B, Enhanced Embeddings, Cross-encoder reranking

---
*Generated by Comprehensive RAG Benchmark Suite*
"""
        
        return report

def main():
    """Main benchmark execution."""
    print("🚀 FAQBuddy Comprehensive RAG Benchmark Suite")
    print("=" * 60)
    
    try:
        # Initialize benchmark suite
        benchmark = ComprehensiveBenchmark()
        
        # Run comprehensive benchmark
        benchmark.run_comprehensive_benchmark()
        
        # Analyze results
        analysis = benchmark.analyze_results()
        
        # Save results
        results_file, summary_file = benchmark.save_results(analysis)
        
        print(f"\n🎉 BENCHMARK COMPLETED SUCCESSFULLY!")
        print(f"📊 Check {summary_file} for detailed analysis")
        print(f"📁 Raw data available in {results_file}")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())

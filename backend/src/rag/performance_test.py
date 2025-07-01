"""
Performance Testing for Enhanced RAG System
==========================================

This script benchmarks the RAG system performance with different configurations
and provides detailed analysis of speed and accuracy improvements.
"""

import time
import json
import statistics
from typing import List, Dict, Any, Tuple
from src.rag.rag_pipeline import RAGPipeline
from src.rag.rag_config import get_config, get_optimization_tips
from src.rag.build_prompt import build_prompt
from src.rag.hybrid_retrieval import get_retrieval_stats
from src.utils.llm_mistral import get_llm_stats, test_llm_connection

# Test queries for benchmarking
TEST_QUERIES = [
    "Quanti CFU ha il corso di Informatica?",
    "Quali sono i professori del dipartimento di Informatica?",
    "Come funziona l'iscrizione ai corsi?",
    "Quando sono le scadenze per gli esami?",
    "Quali materiali didattici sono disponibili?",
    "Come posso contattare la segreteria?",
    "Quali sono i requisiti per la laurea?",
    "Come funziona il sistema di valutazione?",
    "Dove si trova l'aula magna?",
    "Quali sono le modalità d'esame?"
]

# Performance profiles to test
PROFILES = ["speed", "balanced", "quality"]

class RAGPerformanceTester:
    """Comprehensive performance testing for RAG system."""
    
    def __init__(self):
        self.results = {}
        self.pipeline = None
    
    def test_configuration(self, profile: str) -> Dict[str, Any]:
        """Test a specific configuration profile."""
        print(f"\n🧪 Testing {profile.upper()} profile...")
        
        # Get configuration
        config = get_config(profile)
        
        # Initialize pipeline with profile settings
        self.pipeline = RAGPipeline(
            top_k=config["performance"]["top_k"]
        )
        
        # Test queries
        query_results = []
        total_time = 0
        successful_queries = 0
        
        for i, query in enumerate(TEST_QUERIES, 1):
            print(f"  Query {i}/{len(TEST_QUERIES)}: {query[:50]}...")
            
            try:
                start_time = time.time()
                answer = self.pipeline.answer(query)
                query_time = time.time() - start_time
                
                query_results.append({
                    "query": query,
                    "answer": answer,
                    "time": query_time,
                    "success": True
                })
                
                total_time += query_time
                successful_queries += 1
                
                print(f"    ✅ {query_time:.3f}s")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
                query_results.append({
                    "query": query,
                    "answer": f"Error: {e}",
                    "time": 0,
                    "success": False
                })
        
        # Calculate statistics
        successful_times = [r["time"] for r in query_results if r["success"]]
        
        stats = {
            "profile": profile,
            "total_queries": len(TEST_QUERIES),
            "successful_queries": successful_queries,
            "success_rate": successful_queries / len(TEST_QUERIES),
            "total_time": total_time,
            "avg_time": statistics.mean(successful_times) if successful_times else 0,
            "median_time": statistics.median(successful_times) if successful_times else 0,
            "min_time": min(successful_times) if successful_times else 0,
            "max_time": max(successful_times) if successful_times else 0,
            "std_time": statistics.stdev(successful_times) if len(successful_times) > 1 else 0,
            "queries_per_minute": (successful_queries / total_time * 60) if total_time > 0 else 0,
            "config": config,
            "detailed_results": query_results
        }
        
        return stats
    
    def test_retrieval_components(self) -> Dict[str, Any]:
        """Test individual retrieval components."""
        print("\n🔍 Testing retrieval components...")
        
        if not self.pipeline:
            self.pipeline = RAGPipeline()
        
        retrieval_stats = []
        
        for query in TEST_QUERIES[:3]:  # Test first 3 queries
            print(f"  Testing retrieval for: {query[:50]}...")
            
            try:
                start_time = time.time()
                retrieval_test = self.pipeline.test_retrieval(query)
                retrieval_time = time.time() - start_time
                
                retrieval_stats.append({
                    "query": query,
                    "retrieval_time": retrieval_time,
                    "intent": retrieval_test["intent"],
                    "results_count": retrieval_test["merged_results_count"],
                    "prompt_tokens": retrieval_test["prompt_metadata"]["total_tokens"]
                })
                
                print(f"    ✅ {retrieval_time:.3f}s, {retrieval_test['merged_results_count']} results")
                
            except Exception as e:
                print(f"    ❌ Error: {e}")
        
        return {
            "retrieval_stats": retrieval_stats,
            "avg_retrieval_time": statistics.mean([r["retrieval_time"] for r in retrieval_stats]),
            "avg_results_count": statistics.mean([r["results_count"] for r in retrieval_stats]),
            "avg_prompt_tokens": statistics.mean([r["prompt_tokens"] for r in retrieval_stats])
        }
    
    def test_system_components(self) -> Dict[str, Any]:
        """Test individual system components."""
        print("\n⚙️ Testing system components...")
        
        # Test LLM
        llm_test = test_llm_connection()
        llm_stats = get_llm_stats()
        
        # Test retrieval system
        retrieval_stats = get_retrieval_stats()
        
        # Test pipeline stats
        pipeline_stats = self.pipeline.get_stats() if self.pipeline else {}
        
        return {
            "llm": {
                "connection_test": llm_test,
                "stats": llm_stats
            },
            "retrieval": retrieval_stats,
            "pipeline": pipeline_stats
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive performance test across all profiles."""
        print("🚀 Starting Comprehensive RAG Performance Test")
        print("=" * 60)
        
        results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "profiles": {},
            "component_tests": {},
            "system_tests": {},
            "summary": {}
        }
        
        # Test each profile
        for profile in PROFILES:
            results["profiles"][profile] = self.test_configuration(profile)
        
        # Test retrieval components
        results["component_tests"] = self.test_retrieval_components()
        
        # Test system components
        results["system_tests"] = self.test_system_components()
        
        # Generate summary
        results["summary"] = self.generate_summary(results)
        
        return results
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate performance summary and recommendations."""
        profiles = results["profiles"]
        
        # Find best performing profile
        best_speed = min(profiles.values(), key=lambda x: x["avg_time"])
        best_accuracy = max(profiles.values(), key=lambda x: x["success_rate"])
        
        # Calculate improvements
        speed_profile = profiles["speed"]
        balanced_profile = profiles["balanced"]
        quality_profile = profiles["quality"]
        
        speed_improvement = ((balanced_profile["avg_time"] - speed_profile["avg_time"]) / balanced_profile["avg_time"]) * 100
        quality_improvement = ((quality_profile["success_rate"] - balanced_profile["success_rate"]) / balanced_profile["success_rate"]) * 100
        
        summary = {
            "best_speed_profile": best_speed["profile"],
            "best_accuracy_profile": best_accuracy["profile"],
            "speed_improvement_percent": speed_improvement,
            "quality_improvement_percent": quality_improvement,
            "recommendations": self.generate_recommendations(results),
            "optimization_tips": get_optimization_tips()
        }
        
        return summary
    
    def generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate performance recommendations."""
        recommendations = []
        profiles = results["profiles"]
        
        # Analyze performance patterns
        avg_times = {name: data["avg_time"] for name, data in profiles.items()}
        success_rates = {name: data["success_rate"] for name, data in profiles.items()}
        
        # Speed recommendations
        if avg_times["speed"] < avg_times["balanced"] * 0.8:
            recommendations.append("Speed profile shows significant performance improvement - consider using for high-traffic scenarios")
        
        if avg_times["quality"] > avg_times["balanced"] * 1.5:
            recommendations.append("Quality profile is significantly slower - consider optimizing cross-encoder usage")
        
        # Accuracy recommendations
        if success_rates["quality"] > success_rates["balanced"] * 1.1:
            recommendations.append("Quality profile shows better accuracy - consider using for critical queries")
        
        # System recommendations
        component_tests = results["component_tests"]
        if component_tests.get("avg_retrieval_time", 0) > 3.0:
            recommendations.append("Retrieval time is high - consider reducing top_k or disabling cross-encoder")
        
        if component_tests.get("avg_prompt_tokens", 0) > 800:
            recommendations.append("Prompt tokens are high - consider reducing max_chunks or max_tokens")
        
        return recommendations
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results."""
        print("\n" + "=" * 60)
        print("📊 RAG PERFORMANCE TEST RESULTS")
        print("=" * 60)
        
        # Profile comparison
        print("\n🏃 PROFILE COMPARISON:")
        print(f"{'Profile':<12} {'Avg Time':<10} {'Success Rate':<12} {'QPM':<8}")
        print("-" * 45)
        
        for profile_name, profile_data in results["profiles"].items():
            print(f"{profile_name:<12} {profile_data['avg_time']:<10.3f} {profile_data['success_rate']:<12.1%} {profile_data['queries_per_minute']:<8.1f}")
        
        # Component analysis
        print("\n🔧 COMPONENT ANALYSIS:")
        component_tests = results["component_tests"]
        print(f"Average retrieval time: {component_tests.get('avg_retrieval_time', 0):.3f}s")
        print(f"Average results per query: {component_tests.get('avg_results_count', 0):.1f}")
        print(f"Average prompt tokens: {component_tests.get('avg_prompt_tokens', 0):.0f}")
        
        # System status
        print("\n⚙️ SYSTEM STATUS:")
        system_tests = results["system_tests"]
        llm_status = system_tests["llm"]["connection_test"]["status"]
        print(f"LLM Status: {'✅ Available' if llm_status == 'success' else '❌ Unavailable'}")
        
        # Summary and recommendations
        print("\n📈 SUMMARY:")
        summary = results["summary"]
        print(f"Best speed profile: {summary['best_speed_profile']}")
        print(f"Best accuracy profile: {summary['best_accuracy_profile']}")
        print(f"Speed improvement: {summary['speed_improvement_percent']:.1f}%")
        print(f"Quality improvement: {summary['quality_improvement_percent']:.1f}%")
        
        print("\n💡 RECOMMENDATIONS:")
        for rec in summary["recommendations"]:
            print(f"  - {rec}")
        
        print("\n🔧 OPTIMIZATION TIPS:")
        for tip in summary["optimization_tips"]:
            print(f"  - {tip}")
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save test results to file."""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"rag_performance_test_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")

def main():
    """Run the performance test."""
    tester = RAGPerformanceTester()
    
    try:
        # Run comprehensive test
        results = tester.run_comprehensive_test()
        
        # Print results
        tester.print_results(results)
        
        # Save results
        tester.save_results(results)
        
    except Exception as e:
        print(f"❌ Error during performance test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
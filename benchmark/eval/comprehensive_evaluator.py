#!/usr/bin/env python3
"""
Comprehensive RAG Evaluation Framework
=====================================

This module provides a unified evaluation framework that combines:
- Custom retrieval metrics (Recall@k, MRR, nDCG@k)
- Table-aware evaluation metrics
- Coverage and diversity metrics  
- False-positive rate analysis
- RAGAS evaluation (faithfulness, answer relevancy)
- Ablation study analysis
- Comparative performance reporting
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd

# Import custom evaluation modules
from enhanced_metrics import AdvancedEvaluator, RetrievalMetrics, run_comprehensive_evaluation
from enhanced_trace_generator import EnhancedTraceGenerator

# Import RAGAS components
try:
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
    RAGAS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ RAGAS not available: {e}")
    RAGAS_AVAILABLE = False

@dataclass
class ComprehensiveResults:
    """Comprehensive evaluation results combining all metrics."""
    # Basic info
    config_name: str
    timestamp: str
    total_queries: int
    successful_queries: int
    
    # Custom retrieval metrics
    retrieval_metrics: Dict[str, Any]
    
    # RAGAS metrics
    ragas_metrics: Dict[str, float]
    
    # Performance metrics
    avg_processing_time: float
    avg_confidence_score: float
    
    # Feature analysis
    features_used: Dict[str, bool]
    namespace_performance: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

class ComprehensiveEvaluator:
    """Unified evaluator combining all evaluation approaches."""
    
    def __init__(self, 
                 ground_truth_file: str = None,
                 enable_ragas: bool = True,
                 k_values: List[int] = None):
        """
        Initialize the comprehensive evaluator.
        
        Args:
            ground_truth_file: Path to ground truth mappings
            enable_ragas: Whether to run RAGAS evaluation
            k_values: List of k values for retrieval metrics
        """
        self.ground_truth_file = ground_truth_file
        self.enable_ragas = enable_ragas and RAGAS_AVAILABLE
        self.k_values = k_values or [1, 3, 5, 10]
        
        # Initialize advanced evaluator
        self.advanced_evaluator = AdvancedEvaluator(
            ground_truth_file=ground_truth_file,
            k_values=self.k_values
        )
        
        if not self.enable_ragas:
            print("⚠️ RAGAS evaluation disabled")
    
    def evaluate_configuration(self, 
                             traces_file: str,
                             config_name: str = None) -> ComprehensiveResults:
        """
        Run comprehensive evaluation on a trace file.
        
        Args:
            traces_file: Path to enhanced traces JSONL file
            config_name: Name of the configuration being evaluated
            
        Returns:
            ComprehensiveResults object with all metrics
        """
        if config_name is None:
            config_name = Path(traces_file).stem
        
        print(f"🔍 Evaluating configuration: {config_name}")
        print(f"📁 Traces file: {traces_file}")
        
        # Load traces
        traces = self._load_traces(traces_file)
        print(f"📊 Loaded {len(traces)} traces")
        
        # Run custom retrieval metrics
        print("🎯 Computing custom retrieval metrics...")
        retrieval_metrics = self.advanced_evaluator.evaluate_retrieval_results(traces)
        
        # Run RAGAS evaluation
        ragas_metrics = {}
        if self.enable_ragas:
            print("📈 Running RAGAS evaluation...")
            ragas_metrics = self._run_ragas_evaluation(traces)
        
        # Compute performance metrics
        performance_metrics = self._compute_performance_metrics(traces)
        
        # Analyze features and namespaces
        feature_analysis = self._analyze_features(traces)
        namespace_analysis = self._analyze_namespaces(traces)
        
        # Create comprehensive result
        result = ComprehensiveResults(
            config_name=config_name,
            timestamp=datetime.now().isoformat(),
            total_queries=len(traces),
            successful_queries=len([t for t in traces if "error" not in t]),
            retrieval_metrics=retrieval_metrics.to_dict(),
            ragas_metrics=ragas_metrics,
            avg_processing_time=performance_metrics["avg_processing_time"],
            avg_confidence_score=performance_metrics["avg_confidence_score"],
            features_used=feature_analysis,
            namespace_performance=namespace_analysis
        )
        
        print(f"✅ Evaluation complete for {config_name}")
        return result
    
    def run_ablation_study(self, 
                         ablation_traces_dir: str = "benchmark/logs",
                         output_file: str = None) -> Dict[str, ComprehensiveResults]:
        """
        Run comprehensive ablation study analysis.
        
        Args:
            ablation_traces_dir: Directory containing ablation traces
            output_file: Path to save ablation results
            
        Returns:
            Dictionary mapping configuration names to results
        """
        print("🧪 Running comprehensive ablation study...")
        
        # Find all ablation trace files
        traces_dir = Path(ablation_traces_dir)
        ablation_files = []
        
        # Look for ablation traces
        patterns = ["ablation_*.jsonl", "baseline_*.jsonl", "full_*.jsonl"]
        for pattern in patterns:
            ablation_files.extend(traces_dir.glob(pattern))
        
        if not ablation_files:
            print("❌ No ablation trace files found")
            return {}
        
        print(f"📁 Found {len(ablation_files)} ablation configurations")
        
        # Evaluate each configuration
        results = {}
        for trace_file in ablation_files:
            config_name = trace_file.stem
            print(f"\n📊 Evaluating: {config_name}")
            
            try:
                result = self.evaluate_configuration(str(trace_file), config_name)
                results[config_name] = result
            except Exception as e:
                print(f"❌ Error evaluating {config_name}: {e}")
        
        # Generate ablation analysis
        if results:
            self._generate_ablation_analysis(results, output_file)
        
        return results
    
    def compare_configurations(self, 
                             results: Dict[str, ComprehensiveResults],
                             output_file: str = None) -> Dict[str, Any]:
        """
        Generate detailed comparison of multiple configurations.
        
        Args:
            results: Dictionary mapping config names to results
            output_file: Path to save comparison report
            
        Returns:
            Comparison analysis
        """
        print("📊 Generating configuration comparison...")
        
        if len(results) < 2:
            print("⚠️ Need at least 2 configurations for comparison")
            return {}
        
        # Create comparison analysis
        comparison = {
            "timestamp": datetime.now().isoformat(),
            "configurations": list(results.keys()),
            "metrics_comparison": {},
            "feature_impact": {},
            "performance_comparison": {},
            "ranking": {}
        }
        
        # Compare retrieval metrics
        retrieval_comparison = self._compare_retrieval_metrics(results)
        comparison["metrics_comparison"]["retrieval"] = retrieval_comparison
        
        # Compare RAGAS metrics
        if self.enable_ragas:
            ragas_comparison = self._compare_ragas_metrics(results)
            comparison["metrics_comparison"]["ragas"] = ragas_comparison
        
        # Analyze feature impact
        feature_impact = self._analyze_feature_impact(results)
        comparison["feature_impact"] = feature_impact
        
        # Performance comparison
        performance_comparison = self._compare_performance(results)
        comparison["performance_comparison"] = performance_comparison
        
        # Overall ranking
        ranking = self._rank_configurations(results)
        comparison["ranking"] = ranking
        
        # Save comparison report
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, indent=2, ensure_ascii=False)
            print(f"💾 Comparison report saved to {output_file}")
        
        # Print summary
        self._print_comparison_summary(comparison)
        
        return comparison
    
    def _load_traces(self, traces_file: str) -> List[Dict[str, Any]]:
        """Load traces from JSONL file."""
        traces = []
        with open(traces_file, 'r', encoding='utf-8') as f:
            for line in f:
                traces.append(json.loads(line))
        return traces
    
    def _run_ragas_evaluation(self, traces: List[Dict[str, Any]]) -> Dict[str, float]:
        """Run RAGAS evaluation on traces."""
        if not RAGAS_AVAILABLE:
            return {}
        
        try:
            # Prepare dataset for RAGAS
            ragas_data = []
            for trace in traces:
                if "error" not in trace and trace.get("contexts"):
                    ragas_data.append({
                        "question": trace["question"],
                        "answer": trace.get("answer", ""),
                        "contexts": trace["contexts"],
                        "ground_truth": trace.get("ground_truth", "")
                    })
            
            if not ragas_data:
                return {}
            
            # Create dataset
            dataset = Dataset.from_list(ragas_data)
            
            # Define metrics
            metrics = [faithfulness, answer_relevancy]
            if ragas_data[0].get("ground_truth"):
                metrics.extend([context_recall, context_precision])
            
            # Run evaluation
            result = evaluate(dataset, metrics=metrics)
            
            # Extract scores
            ragas_scores = {}
            for k, v in result.__dict__.items():
                if isinstance(v, (float, int)):
                    ragas_scores[k] = float(v)
            
            return ragas_scores
            
        except Exception as e:
            print(f"❌ RAGAS evaluation failed: {e}")
            return {}
    
    def _compute_performance_metrics(self, traces: List[Dict[str, Any]]) -> Dict[str, float]:
        """Compute performance metrics from traces."""
        processing_times = []
        confidence_scores = []
        
        for trace in traces:
            if "error" not in trace:
                if "processing_time" in trace:
                    processing_times.append(trace["processing_time"])
                if "confidence_score" in trace:
                    confidence_scores.append(trace["confidence_score"])
        
        return {
            "avg_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0.0,
            "avg_confidence_score": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
            "total_processing_time": sum(processing_times)
        }
    
    def _analyze_features(self, traces: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Analyze which features were used in traces."""
        if not traces or "features_used" not in traces[0]:
            return {}
        
        # Get features from first successful trace
        for trace in traces:
            if "error" not in trace and "features_used" in trace:
                return trace["features_used"]
        
        return {}
    
    def _analyze_namespaces(self, traces: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze namespace performance from traces."""
        namespace_stats = {}
        
        for trace in traces:
            if "error" in trace or "namespace_breakdown" not in trace:
                continue
            
            breakdown = trace["namespace_breakdown"]
            for namespace, data in breakdown.items():
                if namespace not in namespace_stats:
                    namespace_stats[namespace] = {
                        "total_retrievals": 0,
                        "avg_score": 0.0,
                        "avg_rank": 0.0,
                        "usage_frequency": 0
                    }
                
                namespace_stats[namespace]["total_retrievals"] += data.get("count", 0)
                namespace_stats[namespace]["usage_frequency"] += 1
        
        # Compute averages
        total_traces = len([t for t in traces if "error" not in t])
        for namespace, stats in namespace_stats.items():
            stats["usage_rate"] = stats["usage_frequency"] / total_traces if total_traces > 0 else 0
        
        return namespace_stats
    
    def _compare_retrieval_metrics(self, results: Dict[str, ComprehensiveResults]) -> Dict[str, Any]:
        """Compare retrieval metrics across configurations."""
        comparison = {}
        
        # Compare Recall@k
        recall_comparison = {}
        for k in self.k_values:
            recall_comparison[f"recall_at_{k}"] = {}
            for config_name, result in results.items():
                recall_score = result.retrieval_metrics["recall_at_k"].get(str(k), 0.0)
                recall_comparison[f"recall_at_{k}"][config_name] = recall_score
        
        comparison["recall"] = recall_comparison
        
        # Compare MRR
        mrr_comparison = {}
        for config_name, result in results.items():
            mrr_comparison[config_name] = result.retrieval_metrics["mrr"]
        comparison["mrr"] = mrr_comparison
        
        # Compare nDCG@k
        ndcg_comparison = {}
        for k in self.k_values:
            ndcg_comparison[f"ndcg_at_{k}"] = {}
            for config_name, result in results.items():
                ndcg_score = result.retrieval_metrics["ndcg_at_k"].get(str(k), 0.0)
                ndcg_comparison[f"ndcg_at_{k}"][config_name] = ndcg_score
        
        comparison["ndcg"] = ndcg_comparison
        
        return comparison
    
    def _compare_ragas_metrics(self, results: Dict[str, ComprehensiveResults]) -> Dict[str, Any]:
        """Compare RAGAS metrics across configurations."""
        ragas_comparison = {}
        
        # Get all RAGAS metric names
        all_metrics = set()
        for result in results.values():
            all_metrics.update(result.ragas_metrics.keys())
        
        # Compare each metric
        for metric in all_metrics:
            ragas_comparison[metric] = {}
            for config_name, result in results.items():
                ragas_comparison[metric][config_name] = result.ragas_metrics.get(metric, 0.0)
        
        return ragas_comparison
    
    def _analyze_feature_impact(self, results: Dict[str, ComprehensiveResults]) -> Dict[str, Any]:
        """Analyze the impact of different features."""
        feature_impact = {}
        
        # Group configurations by features
        feature_groups = {}
        for config_name, result in results.items():
            feature_key = tuple(sorted(
                (k, v) for k, v in result.features_used.items()
            ))
            if feature_key not in feature_groups:
                feature_groups[feature_key] = []
            feature_groups[feature_key].append((config_name, result))
        
        # Analyze impact of each feature
        all_features = set()
        for result in results.values():
            all_features.update(result.features_used.keys())
        
        for feature in all_features:
            with_feature = []
            without_feature = []
            
            for config_name, result in results.items():
                if result.features_used.get(feature, False):
                    with_feature.append(result)
                else:
                    without_feature.append(result)
            
            if with_feature and without_feature:
                # Compute average performance difference
                with_avg_mrr = sum(r.retrieval_metrics["mrr"] for r in with_feature) / len(with_feature)
                without_avg_mrr = sum(r.retrieval_metrics["mrr"] for r in without_feature) / len(without_feature)
                
                feature_impact[feature] = {
                    "mrr_improvement": with_avg_mrr - without_avg_mrr,
                    "configurations_with": len(with_feature),
                    "configurations_without": len(without_feature)
                }
        
        return feature_impact
    
    def _compare_performance(self, results: Dict[str, ComprehensiveResults]) -> Dict[str, Any]:
        """Compare performance metrics across configurations."""
        performance_comparison = {
            "processing_time": {},
            "confidence_score": {}
        }
        
        for config_name, result in results.items():
            performance_comparison["processing_time"][config_name] = result.avg_processing_time
            performance_comparison["confidence_score"][config_name] = result.avg_confidence_score
        
        return performance_comparison
    
    def _rank_configurations(self, results: Dict[str, ComprehensiveResults]) -> Dict[str, Any]:
        """Rank configurations by overall performance."""
        # Create composite score based on multiple metrics
        scores = {}
        
        for config_name, result in results.items():
            # Weighted composite score
            composite_score = (
                result.retrieval_metrics["mrr"] * 0.3 +
                result.retrieval_metrics["recall_at_k"].get("5", 0.0) * 0.25 +
                result.retrieval_metrics["ndcg_at_k"].get("5", 0.0) * 0.25 +
                result.ragas_metrics.get("faithfulness", 0.0) * 0.1 +
                result.ragas_metrics.get("answer_relevancy", 0.0) * 0.1
            )
            
            scores[config_name] = {
                "composite_score": composite_score,
                "mrr": result.retrieval_metrics["mrr"],
                "recall_at_5": result.retrieval_metrics["recall_at_k"].get("5", 0.0),
                "ndcg_at_5": result.retrieval_metrics["ndcg_at_k"].get("5", 0.0),
                "faithfulness": result.ragas_metrics.get("faithfulness", 0.0),
                "answer_relevancy": result.ragas_metrics.get("answer_relevancy", 0.0)
            }
        
        # Sort by composite score
        ranked = sorted(scores.items(), key=lambda x: x[1]["composite_score"], reverse=True)
        
        return {
            "ranking": [{"rank": i+1, "config": config, **metrics} 
                       for i, (config, metrics) in enumerate(ranked)],
            "best_config": ranked[0][0] if ranked else None,
            "worst_config": ranked[-1][0] if ranked else None
        }
    
    def _generate_ablation_analysis(self, 
                                  results: Dict[str, ComprehensiveResults],
                                  output_file: str = None):
        """Generate detailed ablation study analysis."""
        print("\n🔬 Generating ablation study analysis...")
        
        # Run comprehensive comparison
        comparison = self.compare_configurations(results, output_file)
        
        # Print ablation-specific insights
        print("\n" + "="*80)
        print("🧪 ABLATION STUDY INSIGHTS")
        print("="*80)
        
        if comparison.get("feature_impact"):
            print("\n📊 Feature Impact Analysis:")
            for feature, impact in comparison["feature_impact"].items():
                improvement = impact["mrr_improvement"]
                print(f"   {feature}: {improvement:+.3f} MRR improvement")
        
        if comparison.get("ranking"):
            print(f"\n🏆 Best Configuration: {comparison['ranking']['best_config']}")
            print(f"💩 Worst Configuration: {comparison['ranking']['worst_config']}")
    
    def _print_comparison_summary(self, comparison: Dict[str, Any]):
        """Print a summary of the comparison results."""
        print("\n" + "="*80)
        print("📊 CONFIGURATION COMPARISON SUMMARY")
        print("="*80)
        
        configs = comparison["configurations"]
        print(f"Configurations compared: {len(configs)}")
        
        # Print ranking
        if comparison.get("ranking", {}).get("ranking"):
            print(f"\n🏆 Overall Ranking:")
            for entry in comparison["ranking"]["ranking"][:3]:  # Top 3
                print(f"   {entry['rank']}. {entry['config']} (score: {entry['composite_score']:.3f})")
        
        # Print best metrics
        if comparison.get("metrics_comparison", {}).get("ragas"):
            ragas_metrics = comparison["metrics_comparison"]["ragas"]
            print(f"\n📈 Best RAGAS Scores:")
            for metric, scores in ragas_metrics.items():
                best_config = max(scores.items(), key=lambda x: x[1])
                print(f"   {metric}: {best_config[1]:.3f} ({best_config[0]})")

def run_full_evaluation_suite(traces_dir: str = "benchmark/logs",
                            ground_truth_file: str = None,
                            output_dir: str = "benchmark/eval_results") -> Dict[str, Any]:
    """
    Run the complete evaluation suite on all available traces.
    
    Args:
        traces_dir: Directory containing trace files
        ground_truth_file: Path to ground truth file (optional)
        output_dir: Directory to save results
        
    Returns:
        Complete evaluation results
    """
    print("🚀 Running comprehensive evaluation suite...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Initialize evaluator
    evaluator = ComprehensiveEvaluator(ground_truth_file=ground_truth_file)
    
    # Find all trace files
    traces_path = Path(traces_dir)
    trace_files = list(traces_path.glob("*.jsonl"))
    
    if not trace_files:
        print(f"❌ No trace files found in {traces_dir}")
        return {}
    
    print(f"📁 Found {len(trace_files)} trace files")
    
    # Evaluate all configurations
    all_results = {}
    for trace_file in trace_files:
        config_name = trace_file.stem
        print(f"\n🔍 Evaluating: {config_name}")
        
        try:
            result = evaluator.evaluate_configuration(str(trace_file), config_name)
            all_results[config_name] = result
            
            # Save individual result
            individual_output = output_path / f"{config_name}_results.json"
            with open(individual_output, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"❌ Error evaluating {config_name}: {e}")
    
    # Generate comparison report
    if len(all_results) > 1:
        comparison_output = output_path / "comparison_report.json"
        comparison = evaluator.compare_configurations(all_results, str(comparison_output))
        
        # Generate summary report
        summary_output = output_path / "evaluation_summary.json"
        summary = {
            "timestamp": datetime.now().isoformat(),
            "total_configurations": len(all_results),
            "configurations": list(all_results.keys()),
            "comparison": comparison,
            "individual_results": {name: result.to_dict() for name, result in all_results.items()}
        }
        
        with open(summary_output, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Complete evaluation results saved to {output_dir}")
        return summary
    
    return all_results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive RAG evaluation")
    parser.add_argument("--traces-dir", default="benchmark/logs",
                       help="Directory containing trace files")
    parser.add_argument("--ground-truth", help="Path to ground truth file")
    parser.add_argument("--output-dir", default="benchmark/eval_results",
                       help="Output directory for results")
    parser.add_argument("--single-file", help="Evaluate single trace file")
    parser.add_argument("--ablation-only", action="store_true",
                       help="Run only ablation study")
    
    args = parser.parse_args()
    
    if args.single_file:
        # Evaluate single configuration
        evaluator = ComprehensiveEvaluator(ground_truth_file=args.ground_truth)
        result = evaluator.evaluate_configuration(args.single_file)
        
        print("\n" + "="*80)
        print(f"📊 EVALUATION RESULTS: {result.config_name}")
        print("="*80)
        print(f"Total queries: {result.total_queries}")
        print(f"Successful queries: {result.successful_queries}")
        print(f"MRR: {result.retrieval_metrics['mrr']:.3f}")
        print(f"Recall@5: {result.retrieval_metrics['recall_at_k'].get('5', 0):.3f}")
        
    elif args.ablation_only:
        # Run ablation study
        evaluator = ComprehensiveEvaluator(ground_truth_file=args.ground_truth)
        results = evaluator.run_ablation_study(args.traces_dir)
        
    else:
        # Run full evaluation suite
        results = run_full_evaluation_suite(
            args.traces_dir,
            args.ground_truth,
            args.output_dir
        )
    
    print("\n✅ Comprehensive evaluation completed!")

"""
Comprehensive RAG Evaluation Script
==================================

This script runs Ragas evaluation on all generated test traces and creates
a comprehensive comparison report of all RAG pipeline configurations.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from datetime import datetime

def run_ragas_evaluation(traces_file, output_name):
    """Run Ragas evaluation on a traces file."""
    print(f"🔍 Running Ragas evaluation on {traces_file.name}...")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([
            sys.executable, "eval/run_ragas.py",
            "--records", str(traces_file),
            "--out", f"eval_results_{output_name}.json"
        ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ Ragas evaluation completed in {duration:.2f}s")
            return True
        else:
            print(f"❌ Ragas evaluation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running Ragas evaluation: {e}")
        return False

def load_evaluation_results(results_dir):
    """Load all evaluation results."""
    results = {}
    
    for result_file in results_dir.glob("eval_results_*.json"):
        try:
            with result_file.open("r") as f:
                data = json.load(f)
                # Extract config name from filename
                config_name = result_file.stem.replace("eval_results_", "")
                results[config_name] = data
        except Exception as e:
            print(f"❌ Error loading {result_file}: {e}")
    
    return results

def create_comparison_report(results, output_file):
    """Create a comprehensive comparison report."""
    print(f"📊 Creating comparison report...")
    
    # Define metrics to compare
    metrics = ["faithfulness", "answer_relevancy"]
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_configurations": len(results),
        "metrics_compared": metrics,
        "configurations": {},
        "summary": {}
    }
    
    # Process each configuration
    for config_name, data in results.items():
        report["configurations"][config_name] = {
            "metrics": {metric: data.get(metric, 0) for metric in metrics},
            "raw_data": data
        }
    
    # Calculate summary statistics
    for metric in metrics:
        values = [data.get(metric, 0) for data in results.values()]
        if values:
            report["summary"][metric] = {
                "best": max(values),
                "worst": min(values),
                "average": sum(values) / len(values),
                "best_config": max(results.keys(), key=lambda k: results[k].get(metric, 0))
            }
    
    # Save report
    with output_file.open("w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return report

def print_summary_report(report):
    """Print a human-readable summary report."""
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE RAG EVALUATION RESULTS")
    print(f"{'='*80}")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total configurations tested: {report['total_configurations']}")
    print(f"Metrics compared: {', '.join(report['metrics_compared'])}")
    
    print(f"\n📈 METRIC SUMMARY:")
    for metric, stats in report['summary'].items():
        print(f"\n{metric.upper()}:")
        print(f"   Best: {stats['best']:.3f} ({stats['best_config']})")
        print(f"   Worst: {stats['worst']:.3f}")
        print(f"   Average: {stats['average']:.3f}")
    
    print(f"\n📋 DETAILED RESULTS:")
    print(f"{'Configuration':<25} {'Faithfulness':<12} {'Answer Relevancy':<15}")
    print(f"{'-'*25} {'-'*12} {'-'*15}")
    
    # Sort by faithfulness score
    sorted_configs = sorted(
        report['configurations'].items(),
        key=lambda x: x[1]['metrics'].get('faithfulness', 0),
        reverse=True
    )
    
    for config_name, config_data in sorted_configs:
        metrics = config_data['metrics']
        faithfulness = metrics.get('faithfulness', 0)
        answer_relevancy = metrics.get('answer_relevancy', 0)
        print(f"{config_name:<25} {faithfulness:<12.3f} {answer_relevancy:<15.3f}")
    
    print(f"\n🏆 TOP PERFORMING CONFIGURATIONS:")
    for metric in report['metrics_compared']:
        best_config = report['summary'][metric]['best_config']
        best_score = report['summary'][metric]['best']
        print(f"   {metric.title()}: {best_config} ({best_score:.3f})")

def main():
    """Run comprehensive evaluation of all RAG configurations."""
    print("🧪 Comprehensive RAG Pipeline Evaluation")
    print("=" * 60)
    
    # Check if we're in the right directory
    benchmark_dir = Path("benchmark")
    if not benchmark_dir.exists():
        print("❌ Error: benchmark directory not found. Please run from project root.")
        return 1
    
    logs_dir = benchmark_dir / "logs"
    if not logs_dir.exists():
        print("❌ Error: benchmark/logs directory not found. Run the test generation scripts first.")
        return 1
    
    # Find all trace files
    trace_files = list(logs_dir.glob("*.jsonl"))
    if not trace_files:
        print("❌ Error: No trace files found. Run the test generation scripts first.")
        return 1
    
    print(f"📁 Found {len(trace_files)} trace files to evaluate")
    
    # Run Ragas evaluation on each trace file
    evaluation_results = {}
    successful_evaluations = 0
    
    for trace_file in trace_files:
        config_name = trace_file.stem
        print(f"\n🔍 Evaluating {config_name}...")
        
        if run_ragas_evaluation(trace_file, config_name):
            successful_evaluations += 1
        else:
            print(f"❌ Failed to evaluate {config_name}")
    
    print(f"\n📊 Evaluation Summary:")
    print(f"   Total trace files: {len(trace_files)}")
    print(f"   Successful evaluations: {successful_evaluations}")
    print(f"   Failed evaluations: {len(trace_files) - successful_evaluations}")
    
    if successful_evaluations == 0:
        print("❌ No successful evaluations. Cannot create comparison report.")
        return 1
    
    # Load all evaluation results
    results_dir = benchmark_dir / "eval"
    results = load_evaluation_results(results_dir)
    
    if not results:
        print("❌ No evaluation results found.")
        return 1
    
    # Create comprehensive comparison report
    report_file = results_dir / f"comprehensive_evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report = create_comparison_report(results, report_file)
    
    # Print summary
    print_summary_report(report)
    
    print(f"\n✅ Comprehensive evaluation completed!")
    print(f"📄 Detailed report saved to: {report_file}")
    print(f"📊 Individual results in: {results_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

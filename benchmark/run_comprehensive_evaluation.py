#!/usr/bin/env python3
"""
Master Comprehensive RAG Evaluation Script
==========================================

This is the main entry point for running comprehensive RAG evaluation including:
- Recall@k, MRR, nDCG@k metrics
- Table-aware evaluation
- Coverage and diversity metrics
- False-positive rate analysis  
- RAGAS evaluation
- Ablation study
- Comparative analysis

Usage Examples:
  # Run full evaluation suite
  python run_comprehensive_evaluation.py --mode full

  # Generate enhanced traces and evaluate
  python run_comprehensive_evaluation.py --mode generate-and-evaluate

  # Run ablation study
  python run_comprehensive_evaluation.py --mode ablation

  # Evaluate single configuration
  python run_comprehensive_evaluation.py --mode single --trace-file logs/baseline.jsonl

  # Create ground truth template
  python run_comprehensive_evaluation.py --mode ground-truth --create-template
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add eval directory to path
sys.path.insert(0, str(Path(__file__).parent / "eval"))

from enhanced_trace_generator import (
    EnhancedTraceGenerator, 
    generate_baseline_enhanced_traces,
    generate_full_enhanced_traces, 
    generate_ablation_traces
)
from comprehensive_evaluator import (
    ComprehensiveEvaluator,
    run_full_evaluation_suite
)
from ground_truth_creator import (
    GroundTruthCreator,
    create_basic_ground_truth
)

class MasterEvaluator:
    """Master coordinator for comprehensive RAG evaluation."""
    
    def __init__(self, 
                 traces_dir: str = "benchmark/logs",
                 results_dir: str = "benchmark/eval_results",
                 data_dir: str = "benchmark/data"):
        """
        Initialize the master evaluator.
        
        Args:
            traces_dir: Directory containing trace files
            results_dir: Directory to save evaluation results
            data_dir: Directory containing test data
        """
        self.traces_dir = Path(traces_dir)
        self.results_dir = Path(results_dir)
        self.data_dir = Path(data_dir)
        
        # Create directories
        self.traces_dir.mkdir(exist_ok=True)
        self.results_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        self.testset_file = self.data_dir / "testset.jsonl"
        self.ground_truth_file = self.data_dir / "ground_truth.json"
        
        print(f"========== Master Evaluator initialized ==========")
        print(f"   Traces dir: {self.traces_dir}")
        print(f"   Results dir: {self.results_dir}")
        print(f"   Data dir: {self.data_dir}")
    
    def run_full_pipeline(self, 
                         generate_traces: bool = True,
                         create_ground_truth: bool = True,
                         run_evaluation: bool = True) -> Dict[str, Any]:
        """
        Run the complete evaluation pipeline.
        
        Args:
            generate_traces: Whether to generate new traces
            create_ground_truth: Whether to create/update ground truth
            run_evaluation: Whether to run evaluation
            
        Returns:
            Complete pipeline results
        """
        print("=========@ Running Complete RAG Evaluation Pipeline ")
        print("#" * 80)
        
        start_time = time.time()
        pipeline_results = {
            "timestamp": datetime.now().isoformat(),
            "pipeline_config": {
                "generate_traces": generate_traces,
                "create_ground_truth": create_ground_truth,
                "run_evaluation": run_evaluation
            },
            "results": {}
        }
        
        try:
            # Step 1: Create/update ground truth
            if create_ground_truth:
                print("\n========== Step 1: Creating ground truth data ==========")
                self._ensure_ground_truth()
            
            # Step 2: Generate enhanced traces
            if generate_traces:
                print("\n========== Step 2: Generating enhanced traces...")
                trace_results = self._generate_comprehensive_traces()
                pipeline_results["results"]["trace_generation"] = trace_results
            
            # Step 3: Run comprehensive evaluation
            if run_evaluation:
                print("\n========== Step 3: Running comprehensive evaluation...")
                eval_results = self._run_comprehensive_evaluation()
                pipeline_results["results"]["evaluation"] = eval_results
            
            # Step 4: Generate summary report
            print("\n========== Step 4: Generating summary report...")
            summary = self._generate_summary_report(pipeline_results)
            pipeline_results["summary"] = summary
            
            total_time = time.time() - start_time
            pipeline_results["total_execution_time"] = total_time
            
            print(f"\n========== Complete pipeline finished in {total_time:.2f}s ==========")
            return pipeline_results
            
        except Exception as e:
            print(f"========== Pipeline failed: {e} ==========")
            pipeline_results["error"] = str(e)
            return pipeline_results
    
    def generate_traces_only(self, 
                           configurations: List[str] = None) -> Dict[str, Any]:
        """
        Generate only enhanced traces for specified configurations.
        
        Args:
            configurations: List of configurations to generate
                          ["baseline", "full", "ablation"] or None for all
                          
        Returns:
            Trace generation results
        """
        print("========== Generating Enhanced Traces Only ==========")
        print("=" * 50)
        
        if configurations is None:
            configurations = ["baseline", "full", "ablation"]
        
        results = {}
        
        for config in configurations:
            print(f"\n========== Generating {config} traces... ==========")
            
            try:
                if config == "baseline":
                    result = generate_baseline_enhanced_traces()
                elif config == "full":
                    result = generate_full_enhanced_traces()
                elif config == "ablation":
                    result = generate_ablation_traces()
                else:
                    print(f"========== Unknown configuration: {config} ==========")
                    continue
                
                results[config] = result
                print(f"========== {config} traces generated successfully ==========")
                
            except Exception as e:
                print(f"========== Failed to generate {config} traces: {e} ==========")
                results[config] = {"error": str(e)}
        
        return results
    
    def evaluate_traces_only(self, 
                           trace_files: List[str] = None) -> Dict[str, Any]:
        """
        Evaluate existing trace files.
        
        Args:
            trace_files: List of trace files to evaluate (None for all)
            
        Returns:
            Evaluation results
        """
        print("========== Evaluating Existing Traces ==========")
        print("#" * 40)
        
        ground_truth_path = str(self.ground_truth_file) if self.ground_truth_file.exists() else None
        
        if trace_files is None:
            # Find all trace files
            trace_files = list(self.traces_dir.glob("*.jsonl"))
            trace_files = [str(f) for f in trace_files]
        
        if not trace_files:
            print("========== No trace files found to evaluate ==========")
            return {}
        
        print(f"========== Found {len(trace_files)} trace files to evaluate ==========")
        
        # Run evaluation
        results = run_full_evaluation_suite(
            str(self.traces_dir),
            ground_truth_path,
            str(self.results_dir)
        )
        
        return results
    
    def run_ablation_study(self) -> Dict[str, Any]:
        """
        Run comprehensive ablation study.
        
        Returns:
            Ablation study results
        """
        print("========== Running Comprehensive Ablation Study ==========")
        print("=" * 50)
        
        # Step 1: Generate ablation traces if needed
        ablation_files = list(self.traces_dir.glob("ablation_*.jsonl"))
        if not ablation_files:
            print("========== Generating ablation traces... ==========")
            trace_results = generate_ablation_traces()
        else:
            print(f"========== Found {len(ablation_files)} existing ablation traces")
        
        # Step 2: Run ablation evaluation
        print("========== Running ablation evaluation... ==========")
        
        ground_truth_path = str(self.ground_truth_file) if self.ground_truth_file.exists() else None
        evaluator = ComprehensiveEvaluator(ground_truth_file=ground_truth_path)
        
        ablation_results = evaluator.run_ablation_study(
            str(self.traces_dir),
            str(self.results_dir / "ablation_report.json")
        )
        
        return ablation_results
    
    def create_ground_truth_template(self, 
                                   trace_file: str = None,
                                   include_suggestions: bool = True) -> str:
        """
        Create ground truth annotation template.
        
        Args:
            trace_file: Specific trace file to use (None for testset)
            include_suggestions: Whether to include AI suggestions
            
        Returns:
            Path to created template
        """
        print("========== Creating Ground Truth Template ==========")
        print("=" * 40)
        
        creator = GroundTruthCreator()
        
        if trace_file:
            # Create from trace file
            template_path = self.data_dir / f"{Path(trace_file).stem}_template.json"
            creator.create_annotation_template(
                trace_file,
                str(template_path),
                include_suggestions
            )
        else:
            # Create basic template from testset
            template_path = self.data_dir / "ground_truth_template.json"
            create_basic_ground_truth(str(self.testset_file), str(template_path))
        
        print(f"✅ Template created: {template_path}")
        return str(template_path)
    
    def validate_ground_truth(self) -> Dict[str, Any]:
        """
        Validate existing ground truth data.
        
        Returns:
            Validation report
        """
        if not self.ground_truth_file.exists():
            print("========== No ground truth file found ==========")
            return {}
        
        print("========== Validating Ground Truth Data ==========")
        print("=" * 40)
        
        creator = GroundTruthCreator()
        report = creator.validate_ground_truth(str(self.ground_truth_file))
        
        # Save validation report
        report_path = self.results_dir / "ground_truth_validation.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"========== Validation report saved: {report_path} ==========")
        return report
    
    def _ensure_ground_truth(self):
        """Ensure ground truth data exists."""
        if not self.ground_truth_file.exists():
            print("========== Creating basic ground truth from testset... ==========")
            create_basic_ground_truth(str(self.testset_file), str(self.ground_truth_file))
        else:
            print("========== Ground truth file exists ==========")
    
    def _generate_comprehensive_traces(self) -> Dict[str, Any]:
        """Generate all trace configurations."""
        return self.generate_traces_only()
    
    def _run_comprehensive_evaluation(self) -> Dict[str, Any]:
        """Run comprehensive evaluation on all traces."""
        return self.evaluate_traces_only()
    
    def _generate_summary_report(self, pipeline_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate final summary report."""
        summary = {
            "pipeline_execution": {
                "timestamp": pipeline_results["timestamp"],
                "total_time": pipeline_results.get("total_execution_time", 0),
                "success": "error" not in pipeline_results
            },
            "trace_generation": {},
            "evaluation_results": {},
            "recommendations": []
        }
        
        # Summarize trace generation
        if "trace_generation" in pipeline_results.get("results", {}):
            trace_results = pipeline_results["results"]["trace_generation"]
            summary["trace_generation"] = {
                "configurations_generated": len(trace_results),
                "successful_configs": len([r for r in trace_results.values() if "error" not in r]),
                "total_traces": sum(r.get("total_questions", 0) for r in trace_results.values() if "error" not in r)
            }
        
        # Summarize evaluation results
        if "evaluation" in pipeline_results.get("results", {}):
            eval_results = pipeline_results["results"]["evaluation"]
            if isinstance(eval_results, dict) and "individual_results" in eval_results:
                summary["evaluation_results"] = {
                    "configurations_evaluated": len(eval_results["individual_results"]),
                    "best_configuration": eval_results.get("comparison", {}).get("ranking", {}).get("best_config"),
                    "evaluation_metrics": list(eval_results.get("comparison", {}).get("metrics_comparison", {}).keys())
                }
        
        # Generate recommendations
        summary["recommendations"] = [
            "Review evaluation results in the results directory",
            "Check ground truth validation if available",
            "Consider ablation study insights for feature optimization",
            "Update configurations based on performance analysis"
        ]
        
        # Save summary
        summary_path = self.results_dir / "pipeline_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"========== Pipeline summary saved: {summary_path} ==========")
        return summary

def main():
    """Main entry point for comprehensive evaluation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Comprehensive RAG Evaluation Master Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("--mode", 
                       choices=["full", "generate-only", "evaluate-only", "ablation", 
                               "single", "ground-truth", "validate-gt"],
                       default="full",
                       help="Evaluation mode")
    
    parser.add_argument("--traces-dir", default="benchmark/logs",
                       help="Directory containing trace files")
    parser.add_argument("--results-dir", default="benchmark/eval_results", 
                       help="Directory to save results")
    parser.add_argument("--data-dir", default="benchmark/data",
                       help="Directory containing test data")
    
    # Specific mode options
    parser.add_argument("--trace-file", help="Specific trace file for single evaluation")
    parser.add_argument("--configurations", nargs="+", 
                       choices=["baseline", "full", "ablation"],
                       help="Specific configurations to generate")
    parser.add_argument("--create-template", action="store_true",
                       help="Create ground truth annotation template")
    parser.add_argument("--include-suggestions", action="store_true", default=True,
                       help="Include AI suggestions in ground truth template")
    
    # Pipeline options  
    parser.add_argument("--skip-traces", action="store_true",
                       help="Skip trace generation in full mode")
    parser.add_argument("--skip-evaluation", action="store_true", 
                       help="Skip evaluation in full mode")
    parser.add_argument("--skip-ground-truth", action="store_true",
                       help="Skip ground truth creation in full mode")
    
    args = parser.parse_args()
    
    # Initialize master evaluator
    evaluator = MasterEvaluator(
        traces_dir=args.traces_dir,
        results_dir=args.results_dir,
        data_dir=args.data_dir
    )
    
    # Execute based on mode
    start_time = time.time()
    
    try:
        if args.mode == "full":
            # Run complete pipeline
            results = evaluator.run_full_pipeline(
                generate_traces=not args.skip_traces,
                create_ground_truth=not args.skip_ground_truth,
                run_evaluation=not args.skip_evaluation
            )
            
        elif args.mode == "generate-only":
            # Generate traces only
            results = evaluator.generate_traces_only(args.configurations)
            
        elif args.mode == "evaluate-only":
            # Evaluate existing traces
            results = evaluator.evaluate_traces_only()
            
        elif args.mode == "ablation":
            # Run ablation study
            results = evaluator.run_ablation_study()
            
        elif args.mode == "single":
            # Evaluate single trace file
            if not args.trace_file:
                print("========== --trace-file required for single mode ==========")
                return 1
            
            ground_truth_path = str(evaluator.ground_truth_file) if evaluator.ground_truth_file.exists() else None
            comp_evaluator = ComprehensiveEvaluator(ground_truth_file=ground_truth_path)
            result = comp_evaluator.evaluate_configuration(args.trace_file)
            
            print(f"\n========== Single Configuration Results: ==========")
            print(f"   Config: {result.config_name}")
            print(f"   MRR: {result.retrieval_metrics['mrr']:.3f}")
            print(f"   Recall@5: {result.retrieval_metrics['recall_at_k'].get('5', 0):.3f}")
            
            results = {"single_evaluation": result.to_dict()}
            
        elif args.mode == "ground-truth":
            # Ground truth operations
            if args.create_template:
                template_path = evaluator.create_ground_truth_template(
                    args.trace_file,
                    args.include_suggestions
                )
                results = {"template_created": template_path}
            else:
                print("========== Specify --create-template for ground-truth mode ==========")
                return 1
                
        elif args.mode == "validate-gt":
            # Validate ground truth
            results = evaluator.validate_ground_truth()
        
        total_time = time.time() - start_time
        
        print(f"\n========== Evaluation completed successfully in {total_time:.2f}s ==========")
        print(f"========== Results saved in: {evaluator.results_dir} ==========")
        
        return 0
        
    except Exception as e:
        print(f"\n========== Evaluation failed: {e} ==========")
        return 1

if __name__ == "__main__":
    exit(main())

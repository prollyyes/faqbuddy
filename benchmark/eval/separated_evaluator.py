#!/usr/bin/env python3
"""
Separated T2SQL + RAG Evaluator
===============================

Simple approach: Evaluate T2SQL and RAG questions with completely different metrics.
No mixing, no complex hybrid scoring - just clean separation.
"""

import json
import numpy as np
from typing import Dict, List, Any
from pathlib import Path
from dataclasses import dataclass

@dataclass
class T2SQLResults:
    """Results for T2SQL questions only."""
    questions_count: int
    answer_correctness: float
    sql_success_rate: float
    avg_response_time: float
    routing_accuracy: float

@dataclass 
class RAGResults:
    """Results for RAG questions only."""
    questions_count: int
    answer_correctness: float
    contexts_available: float  # % of questions with contexts
    avg_contexts_per_question: float
    avg_response_time: float

@dataclass
class SeparatedResults:
    """Combined results keeping T2SQL and RAG separate."""
    config_name: str
    t2sql: T2SQLResults
    rag: RAGResults

class SeparatedEvaluator:
    """Simple evaluator that keeps T2SQL and RAG completely separate."""
    
    def __init__(self, ground_truth_file: str):
        """Initialize with ground truth."""
        self.ground_truth = self._load_ground_truth(ground_truth_file)
    
    def _load_ground_truth(self, ground_truth_file: str) -> Dict[str, Any]:
        """Load ground truth data."""
        with open(ground_truth_file, 'r') as f:
            data = json.load(f)
        
        gt_dict = {}
        for item in data:
            gt_dict[item["question"]] = {
                "answer": item["ground_truth_answer"],
                "is_table_query": item.get("is_table_query", False)
            }
        
        return gt_dict
    
    def evaluate_trace_file(self, trace_file: str) -> SeparatedResults:
        """Evaluate a trace file with separated metrics."""
        with open(trace_file, 'r') as f:
            traces = [json.loads(line) for line in f]
        
        config_name = Path(trace_file).stem
        
        # Separate traces by question type
        t2sql_traces = []
        rag_traces = []
        
        for trace in traces:
            question = trace["question"]
            gt_info = self.ground_truth.get(question, {})
            
            # Classify based on ground truth table query flag
            if gt_info.get("is_table_query", False):
                t2sql_traces.append(trace)
            else:
                rag_traces.append(trace)
        
        # Evaluate each type separately
        t2sql_results = self._evaluate_t2sql(t2sql_traces)
        rag_results = self._evaluate_rag(rag_traces)
        
        return SeparatedResults(
            config_name=config_name,
            t2sql=t2sql_results,
            rag=rag_results
        )
    
    def _evaluate_t2sql(self, traces: List[Dict[str, Any]]) -> T2SQLResults:
        """Evaluate T2SQL questions with T2SQL-specific metrics."""
        if not traces:
            return T2SQLResults(0, 0.0, 0.0, 0.0, 0.0)
        
        answer_scores = []
        sql_success = []
        response_times = []
        routing_correct = []
        
        for trace in traces:
            question = trace["question"]
            answer = trace.get("answer", "")
            sql_query = trace.get("sql_query", "")
            route_used = trace.get("route_used", "")
            
            # 1. Answer Correctness (simple word overlap)
            gt_info = self.ground_truth.get(question, {})
            if gt_info:
                score = self._compute_word_overlap(answer, gt_info["answer"])
                answer_scores.append(score)
            
            # 2. SQL Success Rate (has valid SQL)
            has_sql = sql_query and len(sql_query.strip()) > 10 and "SELECT" in sql_query.upper()
            sql_success.append(1.0 if has_sql else 0.0)
            
            # 3. Response Time
            response_times.append(trace.get("processing_time", 0))
            
            # 4. Routing Accuracy (did it use T2SQL?)
            used_t2sql = route_used.startswith("T2SQL") or "T2SQL" in route_used
            routing_correct.append(1.0 if used_t2sql else 0.0)
        
        return T2SQLResults(
            questions_count=len(traces),
            answer_correctness=np.mean(answer_scores) if answer_scores else 0.0,
            sql_success_rate=np.mean(sql_success),
            avg_response_time=np.mean(response_times),
            routing_accuracy=np.mean(routing_correct)
        )
    
    def _evaluate_rag(self, traces: List[Dict[str, Any]]) -> RAGResults:
        """Evaluate RAG questions with RAG-specific metrics."""
        if not traces:
            return RAGResults(0, 0.0, 0.0, 0.0, 0.0)
        
        answer_scores = []
        has_contexts = []
        context_counts = []
        response_times = []
        
        for trace in traces:
            question = trace["question"]
            answer = trace.get("answer", "")
            contexts = trace.get("contexts", [])
            
            # 1. Answer Correctness
            gt_info = self.ground_truth.get(question, {})
            if gt_info:
                score = self._compute_word_overlap(answer, gt_info["answer"])
                answer_scores.append(score)
            
            # 2. Context Availability
            has_contexts.append(1.0 if contexts else 0.0)
            
            # 3. Context Count
            context_counts.append(len(contexts))
            
            # 4. Response Time
            response_times.append(trace.get("processing_time", 0))
        
        return RAGResults(
            questions_count=len(traces),
            answer_correctness=np.mean(answer_scores) if answer_scores else 0.0,
            contexts_available=np.mean(has_contexts),
            avg_contexts_per_question=np.mean(context_counts),
            avg_response_time=np.mean(response_times)
        )
    
    def _compute_word_overlap(self, answer: str, ground_truth: str) -> float:
        """Simple word overlap similarity."""
        if not answer or not ground_truth:
            return 0.0
        
        # Clean and normalize
        answer_clean = answer.lower().replace("**", "").strip()
        gt_clean = ground_truth.lower().replace("**", "").strip()
        
        answer_words = set(answer_clean.split())
        gt_words = set(gt_clean.split())
        
        if not gt_words:
            return 0.0
        
        intersection = len(answer_words & gt_words)
        return intersection / len(gt_words)  # Recall-based scoring
    
    def print_results(self, results: SeparatedResults):
        """Print results in a nice format."""
        print(f"\n📊 EVALUATION RESULTS: {results.config_name.upper()}")
        print("=" * 60)
        
        # T2SQL Results
        print(f"\n🔢 T2SQL QUESTIONS ({results.t2sql.questions_count} questions):")
        print(f"   Answer Correctness: {results.t2sql.answer_correctness:.3f}")
        print(f"   SQL Success Rate: {results.t2sql.sql_success_rate:.3f}")
        print(f"   Routing Accuracy: {results.t2sql.routing_accuracy:.3f}")
        print(f"   Avg Response Time: {results.t2sql.avg_response_time:.2f}s")
        
        # RAG Results
        print(f"\n📄 RAG QUESTIONS ({results.rag.questions_count} questions):")
        print(f"   Answer Correctness: {results.rag.answer_correctness:.3f}")
        print(f"   Contexts Available: {results.rag.contexts_available:.3f}")
        print(f"   Avg Contexts/Question: {results.rag.avg_contexts_per_question:.1f}")
        print(f"   Avg Response Time: {results.rag.avg_response_time:.2f}s")

def main():
    """Main evaluation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Separated T2SQL + RAG Evaluator")
    parser.add_argument("--traces", nargs="+", required=True, help="Trace files to evaluate")
    parser.add_argument("--ground-truth", required=True, help="Ground truth JSON file")
    parser.add_argument("--output", help="Optional JSON output file")
    
    args = parser.parse_args()
    
    evaluator = SeparatedEvaluator(args.ground_truth)
    
    all_results = []
    
    for trace_file in args.traces:
        if Path(trace_file).exists():
            results = evaluator.evaluate_trace_file(trace_file)
            evaluator.print_results(results)
            all_results.append(results)
        else:
            print(f"❌ File not found: {trace_file}")
    
    # Save results if requested
    if args.output:
        output_data = {
            "timestamp": "2025-09-21",
            "results": [
                {
                    "config_name": r.config_name,
                    "t2sql": r.t2sql.__dict__,
                    "rag": r.rag.__dict__
                }
                for r in all_results
            ]
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"\n💾 Results saved to: {args.output}")
    
    # Quick comparison
    if len(all_results) > 1:
        print(f"\n🏆 QUICK COMPARISON:")
        print("-" * 40)
        
        # Best T2SQL performance
        best_t2sql = max(all_results, key=lambda r: r.t2sql.answer_correctness)
        print(f"Best T2SQL Answer Correctness: {best_t2sql.config_name} ({best_t2sql.t2sql.answer_correctness:.3f})")
        
        # Best RAG performance
        best_rag = max(all_results, key=lambda r: r.rag.answer_correctness)
        print(f"Best RAG Answer Correctness: {best_rag.config_name} ({best_rag.rag.answer_correctness:.3f})")
        
        # Best routing
        best_routing = max(all_results, key=lambda r: r.t2sql.routing_accuracy)
        print(f"Best T2SQL Routing: {best_routing.config_name} ({best_routing.t2sql.routing_accuracy:.3f})")

if __name__ == "__main__":
    main()

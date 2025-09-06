#!/usr/bin/env python3
"""
Thesis Evaluation Framework for FAQBuddy RAG System
==================================================

Comprehensive evaluation framework for measuring the performance improvements
of the per-row vector database approach vs traditional chunking methods.

Research Focus:
- Retrieval Quality Metrics
- Response Time Analysis  
- GPU Acceleration Impact
- Per-Row vs Traditional Chunking Comparison
- System Scalability Assessment

Author: [Your Name]
Thesis: [Thesis Title]
Date: 2025
"""

import os
import sys
import time
import json
import asyncio
import statistics
from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, asdict
import pandas as pd
import numpy as np

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from dotenv import load_dotenv
load_dotenv()

@dataclass
class EvaluationMetrics:
    """Comprehensive metrics for RAG system evaluation."""
    
    # Performance Metrics
    total_response_time: float
    retrieval_time: float
    generation_time: float
    embedding_time: float
    reranking_time: float
    
    # Quality Metrics
    retrieved_documents: int
    relevant_documents: int
    precision_at_k: float
    recall_at_k: float
    f1_score: float
    
    # System Metrics
    gpu_memory_used: float
    cpu_usage: float
    tokens_generated: int
    tokens_per_second: float
    
    # Content Metrics
    answer_length: int
    answer_quality_score: float
    factual_accuracy: float
    coherence_score: float
    
    # Namespace Analysis
    namespace_breakdown: Dict[str, int]
    per_row_results: int
    traditional_results: int

@dataclass
class TestQuery:
    """Test query structure for evaluation."""
    query_id: str
    question: str
    expected_answer_type: str
    difficulty_level: str  # easy, medium, hard
    domain: str  # course_info, professor_info, material_info, etc.
    expected_entities: List[str]

class ThesisEvaluator:
    """
    Professional evaluation framework for thesis research.
    
    Implements systematic testing methodology for RAG system improvements.
    """
    
    def __init__(self):
        """Initialize the evaluation framework."""
        self.results = []
        self.test_queries = self._load_test_queries()
        self.evaluation_start_time = datetime.now()
        
        # Initialize RAG pipeline
        try:
            from rag.rag_pipeline_v2 import RAGv2Pipeline
            self.rag_pipeline = RAGv2Pipeline()
            print("✅ RAG Pipeline initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize RAG pipeline: {e}")
            self.rag_pipeline = None
    
    def _load_test_queries(self) -> List[TestQuery]:
        """Load comprehensive test queries for evaluation."""
        return [
            # Course Information Queries
            TestQuery("C001", "Quali sono i corsi del primo semestre?", "list", "easy", "course_info", ["corso", "semestre"]),
            TestQuery("C002", "Chi è il docente del corso di Sistemi Operativi?", "specific", "medium", "professor_info", ["docente", "Sistemi Operativi"]),
            TestQuery("C003", "Quali sono i prerequisiti per il corso di Basi di Dati?", "specific", "medium", "course_info", ["prerequisiti", "Basi di Dati"]),
            
            # Professor Information Queries  
            TestQuery("P001", "Elenca tutti i professori del dipartimento di Informatica", "list", "easy", "professor_info", ["professori", "dipartimento", "Informatica"]),
            TestQuery("P002", "Quali corsi tiene il professor Maurizio Lenzerini?", "list", "medium", "course_info", ["Maurizio Lenzerini", "corsi"]),
            TestQuery("P003", "Quali sono gli orari di ricevimento del professor Giuseppe Oriolo?", "specific", "hard", "professor_info", ["orari", "ricevimento", "Giuseppe Oriolo"]),
            
            # Material Information Queries
            TestQuery("M001", "Dove posso trovare i materiali per il corso di Programmazione?", "specific", "medium", "material_info", ["materiali", "Programmazione"]),
            TestQuery("M002", "Quali piattaforme vengono utilizzate per i corsi online?", "list", "easy", "platform_info", ["piattaforme", "online"]),
            
            # Complex Queries
            TestQuery("X001", "Quali sono i corsi di laurea disponibili e i loro requisiti di ammissione?", "complex", "hard", "degree_info", ["corsi di laurea", "requisiti", "ammissione"]),
            TestQuery("X002", "Come posso iscrivermi a un corso e quali sono le scadenze?", "procedural", "hard", "enrollment_info", ["iscrizione", "corso", "scadenze"]),
        ]
    
    async def evaluate_single_query(self, query: TestQuery) -> EvaluationMetrics:
        """Evaluate a single query and return comprehensive metrics."""
        print(f"\n🔍 Evaluating Query {query.query_id}: {query.question}")
        
        start_time = time.time()
        
        try:
            # Execute query through RAG pipeline
            result = self.rag_pipeline.answer(query.question)
            
            total_time = time.time() - start_time
            
            # Extract metrics from result
            metrics = EvaluationMetrics(
                # Performance Metrics
                total_response_time=total_time,
                retrieval_time=result.get('retrieval_time', 0),
                generation_time=result.get('generation_time', 0),
                embedding_time=result.get('embedding_time', 0),
                reranking_time=result.get('reranking_time', 0),
                
                # Quality Metrics
                retrieved_documents=result.get('retrieved_documents', 0),
                relevant_documents=self._count_relevant_documents(result, query),
                precision_at_k=self._calculate_precision_at_k(result, query),
                recall_at_k=self._calculate_recall_at_k(result, query),
                f1_score=0.0,  # Will be calculated
                
                # System Metrics
                gpu_memory_used=result.get('gpu_memory_used', 0),
                cpu_usage=result.get('cpu_usage', 0),
                tokens_generated=result.get('tokens_generated', 0),
                tokens_per_second=result.get('tokens_per_second', 0),
                
                # Content Metrics
                answer_length=len(result.get('answer', '')),
                answer_quality_score=self._evaluate_answer_quality(result, query),
                factual_accuracy=self._evaluate_factual_accuracy(result, query),
                coherence_score=self._evaluate_coherence(result),
                
                # Namespace Analysis
                namespace_breakdown=result.get('namespace_breakdown', {}),
                per_row_results=result.get('namespace_breakdown', {}).get('per_row', 0),
                traditional_results=sum(v for k, v in result.get('namespace_breakdown', {}).items() if k != 'per_row')
            )
            
            # Calculate F1 score
            if metrics.precision_at_k > 0 and metrics.recall_at_k > 0:
                metrics.f1_score = 2 * (metrics.precision_at_k * metrics.recall_at_k) / (metrics.precision_at_k + metrics.recall_at_k)
            
            print(f"✅ Query {query.query_id} completed in {total_time:.2f}s")
            return metrics
            
        except Exception as e:
            print(f"❌ Error evaluating query {query.query_id}: {e}")
            return None
    
    def _count_relevant_documents(self, result: Dict, query: TestQuery) -> int:
        """Count relevant documents in the result."""
        # This would need domain-specific logic
        # For now, return a placeholder
        return min(result.get('retrieved_documents', 0), 3)
    
    def _calculate_precision_at_k(self, result: Dict, query: TestQuery) -> float:
        """Calculate precision at k for the retrieved documents."""
        retrieved = result.get('retrieved_documents', 0)
        relevant = self._count_relevant_documents(result, query)
        return relevant / retrieved if retrieved > 0 else 0.0
    
    def _calculate_recall_at_k(self, result: Dict, query: TestQuery) -> float:
        """Calculate recall at k for the retrieved documents."""
        # This would need ground truth data
        # For now, return a placeholder
        return min(1.0, result.get('retrieved_documents', 0) / 5.0)
    
    def _evaluate_answer_quality(self, result: Dict, query: TestQuery) -> float:
        """Evaluate the quality of the generated answer."""
        answer = result.get('answer', '')
        if not answer:
            return 0.0
        
        # Simple heuristics for answer quality
        score = 0.0
        
        # Length appropriateness
        if 50 <= len(answer) <= 500:
            score += 0.3
        elif len(answer) > 500:
            score += 0.2
        
        # Contains expected entities
        for entity in query.expected_entities:
            if entity.lower() in answer.lower():
                score += 0.2
        
        # Answer completeness
        if any(word in answer.lower() for word in ['corso', 'professore', 'dipartimento', 'materiale']):
            score += 0.3
        
        return min(1.0, score)
    
    def _evaluate_factual_accuracy(self, result: Dict, query: TestQuery) -> float:
        """Evaluate factual accuracy of the answer."""
        # This would need domain expert evaluation
        # For now, return a placeholder based on retrieved documents
        retrieved = result.get('retrieved_documents', 0)
        return min(1.0, retrieved / 5.0)
    
    def _evaluate_coherence(self, result: Dict) -> float:
        """Evaluate coherence of the generated answer."""
        answer = result.get('answer', '')
        if not answer:
            return 0.0
        
        # Simple coherence heuristics
        sentences = answer.split('.')
        if len(sentences) >= 2:
            return 0.8
        elif len(sentences) == 1 and len(answer) > 50:
            return 0.6
        else:
            return 0.4
    
    async def run_comprehensive_evaluation(self) -> Dict[str, Any]:
        """Run comprehensive evaluation across all test queries."""
        print("🚀 Starting Comprehensive Thesis Evaluation")
        print("=" * 60)
        
        if not self.rag_pipeline:
            print("❌ RAG pipeline not available")
            return {}
        
        results = []
        
        for query in self.test_queries:
            metrics = await self.evaluate_single_query(query)
            if metrics:
                results.append({
                    'query_id': query.query_id,
                    'query': query.question,
                    'domain': query.domain,
                    'difficulty': query.difficulty_level,
                    'metrics': asdict(metrics)
                })
        
        # Calculate aggregate statistics
        aggregate_stats = self._calculate_aggregate_statistics(results)
        
        # Generate evaluation report
        evaluation_report = {
            'evaluation_metadata': {
                'timestamp': self.evaluation_start_time.isoformat(),
                'total_queries': len(self.test_queries),
                'successful_queries': len(results),
                'evaluation_duration': (datetime.now() - self.evaluation_start_time).total_seconds()
            },
            'individual_results': results,
            'aggregate_statistics': aggregate_stats,
            'performance_analysis': self._analyze_performance(results),
            'quality_analysis': self._analyze_quality(results),
            'namespace_analysis': self._analyze_namespace_usage(results)
        }
        
        return evaluation_report
    
    def _calculate_aggregate_statistics(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate aggregate statistics across all queries."""
        if not results:
            return {}
        
        metrics_list = [r['metrics'] for r in results]
        
        return {
            'response_times': {
                'mean': statistics.mean([m['total_response_time'] for m in metrics_list]),
                'median': statistics.median([m['total_response_time'] for m in metrics_list]),
                'std_dev': statistics.stdev([m['total_response_time'] for m in metrics_list]) if len(metrics_list) > 1 else 0,
                'min': min([m['total_response_time'] for m in metrics_list]),
                'max': max([m['total_response_time'] for m in metrics_list])
            },
            'quality_scores': {
                'mean_precision': statistics.mean([m['precision_at_k'] for m in metrics_list]),
                'mean_recall': statistics.mean([m['recall_at_k'] for m in metrics_list]),
                'mean_f1': statistics.mean([m['f1_score'] for m in metrics_list]),
                'mean_quality': statistics.mean([m['answer_quality_score'] for m in metrics_list])
            },
            'retrieval_metrics': {
                'mean_documents_retrieved': statistics.mean([m['retrieved_documents'] for m in metrics_list]),
                'mean_per_row_usage': statistics.mean([m['per_row_results'] for m in metrics_list]),
                'mean_traditional_usage': statistics.mean([m['traditional_results'] for m in metrics_list])
            }
        }
    
    def _analyze_performance(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze performance characteristics."""
        metrics_list = [r['metrics'] for r in results]
        
        return {
            'gpu_acceleration_impact': {
                'avg_generation_speed': statistics.mean([m['tokens_per_second'] for m in metrics_list if m['tokens_per_second'] > 0]),
                'gpu_memory_efficiency': statistics.mean([m['gpu_memory_used'] for m in metrics_list if m['gpu_memory_used'] > 0])
            },
            'component_breakdown': {
                'avg_retrieval_time': statistics.mean([m['retrieval_time'] for m in metrics_list]),
                'avg_generation_time': statistics.mean([m['generation_time'] for m in metrics_list]),
                'avg_embedding_time': statistics.mean([m['embedding_time'] for m in metrics_list]),
                'avg_reranking_time': statistics.mean([m['reranking_time'] for m in metrics_list])
            }
        }
    
    def _analyze_quality(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze answer quality characteristics."""
        metrics_list = [r['metrics'] for r in results]
        
        return {
            'answer_characteristics': {
                'avg_length': statistics.mean([m['answer_length'] for m in metrics_list]),
                'avg_quality_score': statistics.mean([m['answer_quality_score'] for m in metrics_list]),
                'avg_factual_accuracy': statistics.mean([m['factual_accuracy'] for m in metrics_list]),
                'avg_coherence': statistics.mean([m['coherence_score'] for m in metrics_list])
            },
            'domain_performance': self._analyze_domain_performance(results)
        }
    
    def _analyze_domain_performance(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze performance by domain."""
        domain_stats = {}
        
        for result in results:
            domain = result['domain']
            if domain not in domain_stats:
                domain_stats[domain] = []
            domain_stats[domain].append(result['metrics'])
        
        domain_analysis = {}
        for domain, metrics_list in domain_stats.items():
            domain_analysis[domain] = {
                'avg_response_time': statistics.mean([m['total_response_time'] for m in metrics_list]),
                'avg_quality_score': statistics.mean([m['answer_quality_score'] for m in metrics_list]),
                'avg_precision': statistics.mean([m['precision_at_k'] for m in metrics_list]),
                'query_count': len(metrics_list)
            }
        
        return domain_analysis
    
    def _analyze_namespace_usage(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze namespace usage patterns."""
        metrics_list = [r['metrics'] for r in results]
        
        return {
            'per_row_effectiveness': {
                'queries_using_per_row': sum(1 for m in metrics_list if m['per_row_results'] > 0),
                'avg_per_row_results': statistics.mean([m['per_row_results'] for m in metrics_list]),
                'per_row_contribution': statistics.mean([m['per_row_results'] / max(1, m['retrieved_documents']) for m in metrics_list])
            },
            'namespace_distribution': {
                'avg_db_v2_usage': statistics.mean([m['namespace_breakdown'].get('db_v2', 0) for m in metrics_list]),
                'avg_pdf_v2_usage': statistics.mean([m['namespace_breakdown'].get('pdf_v2', 0) for m in metrics_list]),
                'avg_documents_v2_usage': statistics.mean([m['namespace_breakdown'].get('documents_v2', 0) for m in metrics_list])
            }
        }
    
    def save_evaluation_report(self, report: Dict[str, Any], filename: str = None):
        """Save evaluation report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"thesis_evaluation_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Evaluation report saved to: {filename}")
        
        # Also save as CSV for easy analysis
        csv_filename = filename.replace('.json', '.csv')
        self._save_results_csv(report, csv_filename)
    
    def _save_results_csv(self, report: Dict[str, Any], filename: str):
        """Save results as CSV for statistical analysis."""
        if 'individual_results' not in report:
            return
        
        rows = []
        for result in report['individual_results']:
            row = {
                'query_id': result['query_id'],
                'domain': result['domain'],
                'difficulty': result['difficulty'],
                **result['metrics']
            }
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df.to_csv(filename, index=False)
        print(f"📈 Results CSV saved to: {filename}")

async def main():
    """Main evaluation function."""
    print("🎓 FAQBuddy Thesis Evaluation Framework")
    print("=" * 50)
    
    evaluator = ThesisEvaluator()
    
    if not evaluator.rag_pipeline:
        print("❌ Cannot proceed without RAG pipeline")
        return
    
    # Run comprehensive evaluation
    report = await evaluator.run_comprehensive_evaluation()
    
    if report:
        # Save results
        evaluator.save_evaluation_report(report)
        
        # Print summary
        print("\n📊 EVALUATION SUMMARY")
        print("=" * 30)
        print(f"Total Queries: {report['evaluation_metadata']['total_queries']}")
        print(f"Successful Queries: {report['evaluation_metadata']['successful_queries']}")
        print(f"Average Response Time: {report['aggregate_statistics']['response_times']['mean']:.2f}s")
        print(f"Average Quality Score: {report['aggregate_statistics']['quality_scores']['mean_quality']:.2f}")
        print(f"Average F1 Score: {report['aggregate_statistics']['quality_scores']['mean_f1']:.2f}")
        
        print("\n🎯 RESEARCH INSIGHTS")
        print("=" * 20)
        print(f"Per-row namespace usage: {report['namespace_analysis']['per_row_effectiveness']['queries_using_per_row']} queries")
        print(f"Average per-row contribution: {report['namespace_analysis']['per_row_effectiveness']['per_row_contribution']:.2%}")
        
    else:
        print("❌ Evaluation failed")

if __name__ == "__main__":
    asyncio.run(main())

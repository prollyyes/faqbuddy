#!/usr/bin/env python3
"""
Enhanced Evaluation Metrics for RAG Systems
==========================================

This module implements comprehensive evaluation metrics including:
- Recall@k, MRR, nDCG@k for retrieval quality
- Table-aware Recall@k for structured data queries
- Coverage metrics for section diversity
- False-positive rate for near-duplicate confusion
- Integration with RAGAS for comprehensive evaluation
"""

import json
import math
import numpy as np
from typing import Dict, List, Any, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import defaultdict
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import re

# Load embedding model for similarity calculations
EMBEDDING_MODEL = None

def get_embedding_model():
    """Lazy load the embedding model."""
    global EMBEDDING_MODEL
    if EMBEDDING_MODEL is None:
        EMBEDDING_MODEL = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return EMBEDDING_MODEL

@dataclass
class RetrievalMetrics:
    """Comprehensive retrieval evaluation metrics."""
    # Basic metrics
    recall_at_k: Dict[int, float]  # k -> recall score
    mrr: float  # Mean Reciprocal Rank
    ndcg_at_k: Dict[int, float]  # k -> nDCG score
    
    # Table-aware metrics
    table_recall_at_k: Dict[int, float]  # Recall for table/structured queries
    table_query_count: int  # Number of table-related queries
    
    # Coverage metrics
    heading_coverage_at_k: Dict[int, float]  # Unique headings in top-k
    section_diversity_at_k: Dict[int, float]  # Section diversity score
    
    # False positive metrics
    false_positive_rate_at_k: Dict[int, float]  # Near-duplicate confusion rate
    cosine_threshold: float  # Threshold used for FP detection
    
    # Overall metrics
    total_queries: int
    successful_queries: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

@dataclass
class GroundTruthInfo:
    """Ground truth information for a query."""
    query_id: str
    question: str
    ground_truth_answer: str
    relevant_chunk_ids: List[str]  # IDs of chunks that should be retrieved
    relevant_sections: List[str]  # Section paths that are relevant
    is_table_query: bool  # Whether this query requires table data
    query_type: str  # Classification of query type

class AdvancedEvaluator:
    """Advanced evaluator for RAG systems."""
    
    def __init__(self, 
                 ground_truth_file: str = None,
                 cosine_threshold: float = 0.9,
                 k_values: List[int] = None):
        """
        Initialize the evaluator.
        
        Args:
            ground_truth_file: Path to ground truth mappings
            cosine_threshold: Threshold for near-duplicate detection
            k_values: List of k values to evaluate (default: [1, 3, 5, 10])
        """
        self.cosine_threshold = cosine_threshold
        self.k_values = k_values or [1, 3, 5, 10]
        self.ground_truth = {}
        
        if ground_truth_file and Path(ground_truth_file).exists():
            self._load_ground_truth(ground_truth_file)
    
    def _load_ground_truth(self, ground_truth_file: str):
        """Load ground truth mappings from file."""
        try:
            with open(ground_truth_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    gt_info = GroundTruthInfo(**item)
                    self.ground_truth[gt_info.question] = gt_info
            print(f"✅ Loaded {len(self.ground_truth)} ground truth mappings")
        except Exception as e:
            print(f"⚠️ Could not load ground truth file: {e}")
    
    def evaluate_retrieval_results(self, 
                                 test_records: List[Dict[str, Any]]) -> RetrievalMetrics:
        """
        Evaluate retrieval results with comprehensive metrics.
        
        Args:
            test_records: List of test records with retrieval results
            
        Returns:
            RetrievalMetrics object with all computed metrics
        """
        print("🔍 Computing comprehensive retrieval metrics...")
        
        # Initialize metric accumulators
        recall_scores = {k: [] for k in self.k_values}
        mrr_scores = []
        ndcg_scores = {k: [] for k in self.k_values}
        table_recall_scores = {k: [] for k in self.k_values}
        heading_coverage_scores = {k: [] for k in self.k_values}
        section_diversity_scores = {k: [] for k in self.k_values}
        false_positive_scores = {k: [] for k in self.k_values}
        
        table_query_count = 0
        total_queries = len(test_records)
        successful_queries = 0
        
        for record in test_records:
            if self._is_valid_record(record):
                successful_queries += 1
                question = record['question']
                contexts = record.get('contexts', [])
                
                # Get ground truth for this question
                gt_info = self.ground_truth.get(question)
                
                if gt_info:
                    # Compute basic retrieval metrics
                    self._compute_recall_metrics(question, contexts, gt_info, recall_scores)
                    self._compute_mrr_metric(question, contexts, gt_info, mrr_scores)
                    self._compute_ndcg_metrics(question, contexts, gt_info, ndcg_scores)
                    
                    # Table-aware metrics
                    if gt_info.is_table_query:
                        table_query_count += 1
                        self._compute_table_recall_metrics(question, contexts, gt_info, table_recall_scores)
                    
                    # Coverage and diversity metrics
                    self._compute_coverage_metrics(contexts, heading_coverage_scores, section_diversity_scores)
                
                # False positive metrics (can be computed without ground truth)
                self._compute_false_positive_metrics(contexts, false_positive_scores)
        
        # Average all metrics
        return RetrievalMetrics(
            recall_at_k={k: np.mean(scores) if scores else 0.0 for k, scores in recall_scores.items()},
            mrr=np.mean(mrr_scores) if mrr_scores else 0.0,
            ndcg_at_k={k: np.mean(scores) if scores else 0.0 for k, scores in ndcg_scores.items()},
            table_recall_at_k={k: np.mean(scores) if scores else 0.0 for k, scores in table_recall_scores.items()},
            table_query_count=table_query_count,
            heading_coverage_at_k={k: np.mean(scores) if scores else 0.0 for k, scores in heading_coverage_scores.items()},
            section_diversity_at_k={k: np.mean(scores) if scores else 0.0 for k, scores in section_diversity_scores.items()},
            false_positive_rate_at_k={k: np.mean(scores) if scores else 0.0 for k, scores in false_positive_scores.items()},
            cosine_threshold=self.cosine_threshold,
            total_queries=total_queries,
            successful_queries=successful_queries
        )
    
    def _is_valid_record(self, record: Dict[str, Any]) -> bool:
        """Check if a record is valid for evaluation."""
        return (
            'question' in record and 
            'contexts' in record and 
            isinstance(record['contexts'], list)
        )
    
    def _compute_recall_metrics(self, 
                              question: str, 
                              contexts: List[str], 
                              gt_info: GroundTruthInfo, 
                              recall_scores: Dict[int, List[float]]):
        """Compute Recall@k metrics."""
        for k in self.k_values:
            top_k_contexts = contexts[:k]
            
            # Simple text-based matching for now
            # In practice, you'd want to match chunk IDs or use semantic similarity
            relevant_found = 0
            for context in top_k_contexts:
                if self._is_relevant_context(context, gt_info):
                    relevant_found += 1
            
            recall = relevant_found / max(len(gt_info.relevant_sections), 1)
            recall_scores[k].append(min(recall, 1.0))  # Cap at 1.0
    
    def _compute_mrr_metric(self, 
                          question: str, 
                          contexts: List[str], 
                          gt_info: GroundTruthInfo, 
                          mrr_scores: List[float]):
        """Compute Mean Reciprocal Rank."""
        for i, context in enumerate(contexts):
            if self._is_relevant_context(context, gt_info):
                mrr_scores.append(1.0 / (i + 1))
                return
        
        # No relevant document found
        mrr_scores.append(0.0)
    
    def _compute_ndcg_metrics(self, 
                            question: str, 
                            contexts: List[str], 
                            gt_info: GroundTruthInfo, 
                            ndcg_scores: Dict[int, List[float]]):
        """Compute nDCG@k metrics."""
        # Create relevance scores (binary for now, could be graded)
        relevance_scores = []
        for context in contexts:
            if self._is_relevant_context(context, gt_info):
                relevance_scores.append(1)
            else:
                relevance_scores.append(0)
        
        for k in self.k_values:
            ndcg_score = self._calculate_ndcg(relevance_scores[:k])
            ndcg_scores[k].append(ndcg_score)
    
    def _compute_table_recall_metrics(self, 
                                    question: str, 
                                    contexts: List[str], 
                                    gt_info: GroundTruthInfo, 
                                    table_recall_scores: Dict[int, List[float]]):
        """Compute table-aware Recall@k metrics."""
        # Similar to regular recall, but specifically for table queries
        for k in self.k_values:
            top_k_contexts = contexts[:k]
            
            # Check if any top-k context contains structured/table data
            table_relevant_found = 0
            for context in top_k_contexts:
                if self._contains_table_data(context) and self._is_relevant_context(context, gt_info):
                    table_relevant_found += 1
            
            recall = table_relevant_found / max(len(gt_info.relevant_sections), 1)
            table_recall_scores[k].append(min(recall, 1.0))
    
    def _compute_coverage_metrics(self, 
                                contexts: List[str], 
                                heading_coverage_scores: Dict[int, List[float]],
                                section_diversity_scores: Dict[int, List[float]]):
        """Compute coverage and diversity metrics."""
        for k in self.k_values:
            top_k_contexts = contexts[:k]
            
            # Extract heading information from contexts
            unique_headings = set()
            unique_sections = set()
            
            for context in top_k_contexts:
                headings = self._extract_headings(context)
                sections = self._extract_sections(context)
                unique_headings.update(headings)
                unique_sections.update(sections)
            
            # Coverage: proportion of unique headings/sections
            heading_coverage = len(unique_headings) / max(k, 1)
            section_diversity = len(unique_sections) / max(k, 1)
            
            heading_coverage_scores[k].append(heading_coverage)
            section_diversity_scores[k].append(section_diversity)
    
    def _compute_false_positive_metrics(self, 
                                      contexts: List[str], 
                                      false_positive_scores: Dict[int, List[float]]):
        """Compute false positive rate metrics for near-duplicate confusion."""
        if len(contexts) < 2:
            for k in self.k_values:
                false_positive_scores[k].append(0.0)
            return
        
        model = get_embedding_model()
        
        for k in self.k_values:
            top_k_contexts = contexts[:k]
            if len(top_k_contexts) < 2:
                false_positive_scores[k].append(0.0)
                continue
            
            # Compute embeddings for all contexts
            embeddings = model.encode(top_k_contexts)
            
            # Compute pairwise similarities
            similarities = cosine_similarity(embeddings)
            
            # Count near-duplicates (high cosine similarity)
            near_duplicates = 0
            total_pairs = 0
            
            for i in range(len(top_k_contexts)):
                for j in range(i + 1, len(top_k_contexts)):
                    total_pairs += 1
                    if similarities[i][j] >= self.cosine_threshold:
                        near_duplicates += 1
            
            fp_rate = near_duplicates / max(total_pairs, 1)
            false_positive_scores[k].append(fp_rate)
    
    def _is_relevant_context(self, context: str, gt_info: GroundTruthInfo) -> bool:
        """Check if a context is relevant to the ground truth."""
        # Simple keyword-based matching
        # In practice, you'd want more sophisticated matching
        context_lower = context.lower()
        gt_lower = gt_info.ground_truth_answer.lower()
        
        # Check for key terms from ground truth in context
        gt_words = set(re.findall(r'\b\w+\b', gt_lower))
        context_words = set(re.findall(r'\b\w+\b', context_lower))
        
        # Simple overlap-based relevance
        overlap = len(gt_words.intersection(context_words))
        return overlap >= min(3, len(gt_words) // 2)
    
    def _contains_table_data(self, context: str) -> bool:
        """Check if context contains structured/table data."""
        # Look for patterns that suggest structured data
        table_indicators = [
            'docente:', 'corso:', 'crediti:', 'modalità:', 'periodo:',
            'edizione del corso', 'matricola', 'email:', 'anno:',
            '\t', '|', 'nome\s+cognome', 'codice\s+corso'
        ]
        
        context_lower = context.lower()
        return any(re.search(pattern, context_lower) for pattern in table_indicators)
    
    def _extract_headings(self, context: str) -> List[str]:
        """Extract heading information from context."""
        # Look for common heading patterns
        headings = []
        
        # Match markdown-style headings
        heading_matches = re.findall(r'^#+\s+(.+)$', context, re.MULTILINE)
        headings.extend(heading_matches)
        
        # Match title-case lines (potential headings)
        title_matches = re.findall(r'^([A-Z][a-z\s]+[A-Z][a-z\s]*):?\s*$', context, re.MULTILINE)
        headings.extend(title_matches)
        
        return headings
    
    def _extract_sections(self, context: str) -> List[str]:
        """Extract section information from context."""
        # Look for section indicators
        sections = []
        
        # Look for "Sezione:", "Capitolo:", etc.
        section_matches = re.findall(r'(?:sezione|capitolo|parte):\s*([^\n]+)', context, re.IGNORECASE)
        sections.extend(section_matches)
        
        # Extract from metadata if available
        if 'sezione:' in context.lower():
            metadata_sections = re.findall(r'sezione:\s*([^\n,]+)', context, re.IGNORECASE)
            sections.extend(metadata_sections)
        
        return sections
    
    def _calculate_ndcg(self, relevance_scores: List[int]) -> float:
        """Calculate nDCG for a list of relevance scores."""
        if not relevance_scores:
            return 0.0
        
        # Calculate DCG
        dcg = 0.0
        for i, rel in enumerate(relevance_scores):
            dcg += rel / math.log2(i + 2)  # +2 because log2(1) = 0
        
        # Calculate IDCG (ideal DCG)
        ideal_relevance = sorted(relevance_scores, reverse=True)
        idcg = 0.0
        for i, rel in enumerate(ideal_relevance):
            idcg += rel / math.log2(i + 2)
        
        # Return nDCG
        return dcg / idcg if idcg > 0 else 0.0

def create_ground_truth_template(test_records: List[Dict[str, Any]], output_file: str):
    """Create a template ground truth file for manual annotation."""
    template = []
    
    for i, record in enumerate(test_records):
        if 'question' in record:
            template.append({
                "query_id": f"q_{i+1}",
                "question": record['question'],
                "ground_truth_answer": record.get('ground_truth', ''),
                "relevant_chunk_ids": [],  # To be filled manually
                "relevant_sections": [],   # To be filled manually
                "is_table_query": False,   # To be marked manually
                "query_type": "unknown"    # To be classified manually
            })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Created ground truth template: {output_file}")
    print(f"   Contains {len(template)} queries to annotate")

def run_comprehensive_evaluation(test_file: str, 
                               ground_truth_file: str = None,
                               output_file: str = None) -> RetrievalMetrics:
    """
    Run comprehensive evaluation on test results.
    
    Args:
        test_file: Path to test results JSONL file
        ground_truth_file: Path to ground truth mappings (optional)
        output_file: Path to save detailed results (optional)
        
    Returns:
        RetrievalMetrics object with all computed metrics
    """
    print(f"🧪 Running comprehensive evaluation on {test_file}")
    
    # Load test records
    test_records = []
    with open(test_file, 'r', encoding='utf-8') as f:
        for line in f:
            test_records.append(json.loads(line))
    
    print(f"📊 Loaded {len(test_records)} test records")
    
    # Initialize evaluator
    evaluator = AdvancedEvaluator(ground_truth_file=ground_truth_file)
    
    # Run evaluation
    metrics = evaluator.evaluate_retrieval_results(test_records)
    
    # Save results if requested
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"💾 Saved detailed metrics to {output_file}")
    
    return metrics

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive RAG evaluation")
    parser.add_argument("--test-file", required=True, help="Path to test results JSONL file")
    parser.add_argument("--ground-truth", help="Path to ground truth mappings JSON file")
    parser.add_argument("--output", help="Path to save detailed results")
    parser.add_argument("--create-template", action="store_true", 
                       help="Create ground truth template for annotation")
    
    args = parser.parse_args()
    
    if args.create_template:
        # Create ground truth template
        test_records = []
        with open(args.test_file, 'r', encoding='utf-8') as f:
            for line in f:
                test_records.append(json.loads(line))
        
        template_file = args.test_file.replace('.jsonl', '_ground_truth_template.json')
        create_ground_truth_template(test_records, template_file)
    else:
        # Run evaluation
        metrics = run_comprehensive_evaluation(
            args.test_file, 
            args.ground_truth, 
            args.output
        )
        
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE EVALUATION RESULTS")
        print("="*80)
        print(f"Total queries: {metrics.total_queries}")
        print(f"Successful queries: {metrics.successful_queries}")
        print(f"Table queries: {metrics.table_query_count}")
        
        print(f"\n📈 RECALL@K:")
        for k, score in metrics.recall_at_k.items():
            print(f"   Recall@{k}: {score:.3f}")
        
        print(f"\n🔄 MRR: {metrics.mrr:.3f}")
        
        print(f"\n📊 nDCG@K:")
        for k, score in metrics.ndcg_at_k.items():
            print(f"   nDCG@{k}: {score:.3f}")
        
        if metrics.table_query_count > 0:
            print(f"\n📋 TABLE-AWARE RECALL@K:")
            for k, score in metrics.table_recall_at_k.items():
                print(f"   Table-Recall@{k}: {score:.3f}")
        
        print(f"\n🎯 COVERAGE@K:")
        for k, score in metrics.heading_coverage_at_k.items():
            print(f"   Heading-Coverage@{k}: {score:.3f}")
        
        print(f"\n❌ FALSE POSITIVE RATE@K (threshold={metrics.cosine_threshold}):")
        for k, score in metrics.false_positive_rate_at_k.items():
            print(f"   FP-Rate@{k}: {score:.3f}")

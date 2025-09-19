# Comprehensive RAG Evaluation Framework

This directory contains a comprehensive evaluation framework for RAG systems that implements advanced metrics, ablation studies, and integrates with RAGAS for thorough evaluation.

## Features

### Advanced Metrics
- **Recall@k**: Gold chunk in top-k retrieval results
- **MRR (Mean Reciprocal Rank)**: Position of first relevant result
- **nDCG@k**: Normalized Discounted Cumulative Gain
- **Table-aware Recall@k**: Specialized metrics for structured data queries
- **Coverage Metrics**: Unique heading path diversity in top-k results
- **False-positive Rate**: Near-duplicate confusion detection (cosine ≥ 0.9)

### RAGAS Integration
- **Faithfulness**: How well answers are grounded in context
- **Answer Relevancy**: Relevance of answers to questions
- **Context Recall**: How well relevant context is retrieved
- **Context Precision**: Precision of retrieved context

### Ablation Study Support
- **Feature Impact Analysis**: Effect of individual features
- **Configuration Comparison**: Side-by-side performance analysis
- **Performance Ranking**: Overall configuration ranking

## Directory Structure

```
benchmark/
├── data/
│   ├── testset.jsonl              # Test questions
│   ├── ground_truth.json          # Ground truth mappings
│   └── ground_truth_template.json # Annotation template
├── eval/
│   ├── enhanced_metrics.py        # Custom evaluation metrics
│   ├── enhanced_trace_generator.py # Enhanced trace generation
│   ├── comprehensive_evaluator.py # Unified evaluator
│   ├── ground_truth_creator.py    # Ground truth management
│   └── run_ragas.py               # Original RAGAS runner
├── logs/
│   ├── baseline_enhanced.jsonl    # Baseline configuration traces
│   ├── full_enhanced.jsonl        # Full feature traces
│   ├── ablation_*.jsonl          # Ablation study traces
│   └── *.jsonl                    # Other configuration traces
├── eval_results/
│   ├── *_results.json            # Individual configuration results
│   ├── comparison_report.json     # Cross-configuration comparison
│   ├── ablation_report.json      # Ablation study analysis
│   └── evaluation_summary.json   # Complete evaluation summary
└── run_comprehensive_evaluation.py # Master evaluation script
```

## Quick Start

### 1. Run Complete Evaluation Pipeline

```bash
# Full pipeline: generate traces + create ground truth + evaluate
python run_comprehensive_evaluation.py --mode full

# Pipeline with existing traces (skip generation)
python run_comprehensive_evaluation.py --mode full --skip-traces

# Pipeline without ground truth creation
python run_comprehensive_evaluation.py --mode full --skip-ground-truth
```

### 2. Generate Enhanced Traces Only

```bash
# Generate all configuration traces
python run_comprehensive_evaluation.py --mode generate-only

# Generate specific configurations
python run_comprehensive_evaluation.py --mode generate-only --configurations baseline full

# Generate ablation study traces
python run_comprehensive_evaluation.py --mode ablation
```

### 3. Evaluate Existing Traces

```bash
# Evaluate all traces in logs directory
python run_comprehensive_evaluation.py --mode evaluate-only

# Evaluate single configuration
python run_comprehensive_evaluation.py --mode single --trace-file logs/baseline_enhanced.jsonl
```

### 4. Ground Truth Management

```bash
# Create annotation template
python run_comprehensive_evaluation.py --mode ground-truth --create-template

# Validate ground truth
python run_comprehensive_evaluation.py --mode validate-gt

# Create template from specific trace file
python run_comprehensive_evaluation.py --mode ground-truth --create-template --trace-file logs/full_enhanced.jsonl
```

## Evaluation Metrics

### Core Retrieval Metrics

```python
# Recall@k: Proportion of relevant items in top-k
recall_at_k = relevant_in_topk / total_relevant

# MRR: Mean reciprocal rank of first relevant item
mrr = 1/rank_of_first_relevant

# nDCG@k: Normalized discounted cumulative gain
ndcg = dcg / idcg
```

### Table-Aware Metrics

```python
# Table Recall@k: Recall specifically for table/structured queries
table_recall = table_relevant_in_topk / total_table_relevant
```

### Coverage Metrics

```python
# Heading Coverage: Unique headings in top-k
heading_coverage = unique_headings / k

# Section Diversity: Unique sections in top-k  
section_diversity = unique_sections / k
```

### False Positive Metrics

```python
# FP Rate: Near-duplicate confusion
fp_rate = near_duplicate_pairs / total_pairs
# where near_duplicate = cosine_similarity >= 0.9
```

## Ablation Study

The framework supports comprehensive ablation studies to understand feature impact:

### Supported Ablation Configurations

1. **`ablation_no_rerank`**: Enhanced retrieval without cross-encoder reranking
2. **`ablation_no_verification`**: No response verification
3. **`ablation_no_enhancement`**: No retrieval enhancement (basic Pinecone)
4. **`ablation_only_web`**: Only web search enhancement

### Feature Impact Analysis

```python
# Automatic feature impact calculation
feature_impact = {
    "cross_encoder_reranking": {
        "mrr_improvement": +0.045,
        "configurations_with": 5,
        "configurations_without": 3
    }
}
```

## Enhanced Trace Format

Enhanced traces capture detailed metadata for comprehensive evaluation:

```json
{
  "question": "Quali corsi insegna il prof Lenzerini?",
  "ground_truth": "Basi di Dati", 
  "answer": "Il prof Maurizio Lenzerini insegna...",
  "contexts": ["Edizione del corso di Basi di Dati..."],
  
  "query_id": "q_1",
  "config": "full_enhanced",
  "confidence_score": 0.87,
  "processing_time": 2.34,
  "features_used": {
    "enhanced_retrieval": true,
    "cross_encoder_reranking": true,
    "response_verification": true
  },
  
  "retrieval_results": [
    {
      "rank": 1,
      "chunk_id": "doc_123_chunk_5",
      "score": 0.89,
      "original_score": 0.82,
      "text": "Edizione del corso di Basi di Dati...",
      "namespace": "ragv2_pdf",
      "source_file": "courses.pdf",
      "page_number": 15,
      "section_hierarchy": ["Offerta Formativa", "Corsi"],
      "boost_applied": 1.2,
      "was_reranked": true
    }
  ],
  
  "namespace_breakdown": {
    "ragv2_pdf": {"count": 3, "avg_score": 0.85},
    "ragv2_docs": {"count": 2, "avg_score": 0.71}
  },
  
  "section_analysis": {
    "unique_sections_count": 2,
    "section_diversity": 0.4,
    "unique_sections": ["Offerta Formativa", "Docenti"]
  },
  
  "query_analysis": {
    "intent": "factual_lookup",
    "complexity": "simple",
    "entities": ["Lenzerini"],
    "requires_reasoning": false
  },
  
  "verification_result": {
    "is_verified": true,
    "confidence_score": 0.92,
    "fact_check_score": 0.88
  }
}
```

## Results Analysis

### Individual Configuration Results

```json
{
  "config_name": "full_enhanced",
  "retrieval_metrics": {
    "recall_at_k": {"1": 0.45, "3": 0.72, "5": 0.83, "10": 0.91},
    "mrr": 0.67,
    "ndcg_at_k": {"1": 0.45, "3": 0.63, "5": 0.71, "10": 0.78},
    "table_recall_at_k": {"1": 0.38, "5": 0.75},
    "heading_coverage_at_k": {"5": 0.68, "10": 0.74},
    "false_positive_rate_at_k": {"5": 0.12, "10": 0.18}
  },
  "ragas_metrics": {
    "faithfulness": 0.84,
    "answer_relevancy": 0.79,
    "context_recall": 0.71,
    "context_precision": 0.68
  }
}
```

### Comparison Report

```json
{
  "ranking": [
    {"rank": 1, "config": "full_enhanced", "composite_score": 0.723},
    {"rank": 2, "config": "ablation_no_verification", "composite_score": 0.689},
    {"rank": 3, "config": "baseline_enhanced", "composite_score": 0.612}
  ],
  "feature_impact": {
    "cross_encoder_reranking": {"mrr_improvement": 0.045},
    "response_verification": {"mrr_improvement": 0.023}
  }
}
```

## Ground Truth Management

### Creating Ground Truth

```bash
# Create basic ground truth from testset
python eval/ground_truth_creator.py --mode basic --testset data/testset.jsonl --output data/ground_truth.json

# Create annotation template
python eval/ground_truth_creator.py --mode template --input logs/full_enhanced.jsonl --output data/annotation_template.json --include-suggestions

# Validate ground truth
python eval/ground_truth_creator.py --mode validate --input data/ground_truth.json
```

### Ground Truth Format

```json
{
  "query_id": "q_1",
  "question": "Quali corsi insegna il prof Lenzerini?",
  "ground_truth_answer": "Basi di Dati",
  "relevant_chunk_ids": ["doc_123_chunk_5", "doc_124_chunk_2"], 
  "relevant_sections": ["Offerta Formativa", "Docenti"],
  "is_table_query": true,
  "query_type": "factual",
  "confidence": 0.9
}
```

## Configuration Options

### Enhanced Trace Generator

```python
generator = EnhancedTraceGenerator("my_config")
generator.setup_pipeline(
    enhanced_retrieval=True,
    cross_encoder_reranking=True,
    web_search_enhancement=False,
    response_verification=True
)
```

### Comprehensive Evaluator

```python
evaluator = ComprehensiveEvaluator(
    ground_truth_file="data/ground_truth.json",
    enable_ragas=True,
    k_values=[1, 3, 5, 10]
)
```

## Usage Examples

### Example 1: Quick Evaluation

```bash
# Generate traces and evaluate with defaults
python run_comprehensive_evaluation.py --mode full
```

### Example 2: Ablation Study

```bash
# Run comprehensive ablation study
python run_comprehensive_evaluation.py --mode ablation
```

### Example 3: Custom Configuration

```bash
# Generate specific configurations only
python run_comprehensive_evaluation.py --mode generate-only --configurations baseline full

# Then evaluate them
python run_comprehensive_evaluation.py --mode evaluate-only
```

### Example 4: Ground Truth Workflow

```bash
# 1. Create annotation template
python run_comprehensive_evaluation.py --mode ground-truth --create-template

# 2. Manually annotate the template (edit data/ground_truth_template.json)

# 3. Validate the annotations  
python run_comprehensive_evaluation.py --mode validate-gt

# 4. Run evaluation with ground truth
python run_comprehensive_evaluation.py --mode full
```

## Best Practices

### 1. Ground Truth Quality
- Manually review AI-generated ground truth suggestions
- Ensure balanced representation of query types
- Include edge cases and challenging queries

### 2. Evaluation Methodology
- Run multiple evaluation rounds for statistical significance
- Use consistent test sets across configurations
- Document configuration changes for reproducibility

### 3. Ablation Study Design
- Test one feature at a time for clear attribution
- Include baseline and full-feature configurations
- Analyze feature interactions

### 4. Result Interpretation
- Consider multiple metrics, not just single scores
- Analyze failure cases for insights
- Use confidence intervals where applicable

## Troubleshooting

### Common Issues

**1. Missing Dependencies**
```bash
pip install sentence-transformers datasets ragas scikit-learn
```

**2. RAGAS Import Errors**
```bash
# Install specific RAGAS version
pip install ragas==0.1.0
```

**3. Memory Issues with Large Models**
```python
# Use smaller embedding model
EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
```

**4. Ground Truth File Not Found**
```bash
# Create basic ground truth first
python run_comprehensive_evaluation.py --mode ground-truth --create-template
```

### Performance Optimization

- Use smaller embedding models for faster evaluation
- Process traces in batches for large datasets
- Cache embedding computations when possible
- Run evaluation on GPU if available

## References

- [RAGAS Documentation](https://docs.ragas.io/)
- [Information Retrieval Metrics](https://en.wikipedia.org/wiki/Evaluation_measures_(information_retrieval))
- [nDCG Explanation](https://en.wikipedia.org/wiki/Discounted_cumulative_gain)
- [Mean Reciprocal Rank](https://en.wikipedia.org/wiki/Mean_reciprocal_rank)

---

For questions or issues, check the troubleshooting section or create an issue in the project repository.

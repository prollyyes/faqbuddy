# RAG Pipeline Comprehensive Testing Suite

This directory contains a comprehensive testing suite for evaluating different configurations of your RAG pipeline using Ragas metrics.

## Overview

The testing suite evaluates the following RAG pipeline configurations:

1. **Baseline RAG** - No enhancements (just Pinecone + generation)
2. **RAG + Re-ranking** - Baseline with cross-encoder re-ranking
3. **RAG + Web Enhancement** - Baseline with web search enhancement
4. **Full Advanced RAG** - All features enabled (AdvancedRAGPipeline)
5. **Top-K Variations** - 12 combinations of top-k (10,20,50,75) and MAX_CHUNKS (3,5,7)

## Test Scripts

### Individual Test Generators

- `generate_baseline_rag_traces.py` - Baseline RAG configuration
- `generate_rag_reranking_traces.py` - RAG with re-ranking
- `generate_rag_web_traces.py` - RAG with web enhancement
- `generate_full_advanced_traces.py` - Full advanced pipeline
- `generate_topk_variations_traces.py` - Top-k and chunk variations

### Master Scripts

- `run_all_rag_tests.py` - Runs all test configurations
- `run_comprehensive_evaluation.py` - Evaluates all traces with Ragas and creates comparison report

## Usage

### Quick Start - Run All Tests

```bash
# From the project root
cd benchmark
python eval/run_all_rag_tests.py
```

This will:
1. Generate traces for all 5 main configurations
2. Generate 12 additional top-k variation traces
3. Save all results to `logs/` directory

### Run Individual Tests

```bash
# Run specific configuration
python eval/generate_baseline_rag_traces.py
python eval/generate_rag_reranking_traces.py
python eval/generate_rag_web_traces.py
python eval/generate_full_advanced_traces.py
python eval/generate_topk_variations_traces.py
```

### Evaluate Results with Ragas

```bash
# Evaluate all traces and create comparison report
python eval/run_comprehensive_evaluation.py
```

Or evaluate individual traces:

```bash
# Evaluate specific configuration
python eval/run_ragas.py --records logs/baseline_rag.jsonl --out baseline_results.json
python eval/run_ragas.py --records logs/rag_reranking.jsonl --out reranking_results.json
python eval/run_ragas.py --records logs/full_advanced.jsonl --out advanced_results.json
```

## Output Files

### Trace Files (in `logs/` directory)

- `baseline_rag.jsonl` - Baseline RAG traces
- `rag_reranking.jsonl` - RAG + re-ranking traces
- `rag_web.jsonl` - RAG + web enhancement traces
- `full_advanced.jsonl` - Full advanced RAG traces
- `topk_10_chunks_3.jsonl` - Top-k=10, MAX_CHUNKS=3
- `topk_10_chunks_5.jsonl` - Top-k=10, MAX_CHUNKS=5
- `topk_10_chunks_7.jsonl` - Top-k=10, MAX_CHUNKS=7
- `topk_20_chunks_3.jsonl` - Top-k=20, MAX_CHUNKS=3
- `topk_20_chunks_5.jsonl` - Top-k=20, MAX_CHUNKS=5
- `topk_20_chunks_7.jsonl` - Top-k=20, MAX_CHUNKS=7
- `topk_50_chunks_3.jsonl` - Top-k=50, MAX_CHUNKS=3
- `topk_50_chunks_5.jsonl` - Top-k=50, MAX_CHUNKS=5
- `topk_50_chunks_7.jsonl` - Top-k=50, MAX_CHUNKS=7
- `topk_75_chunks_3.jsonl` - Top-k=75, MAX_CHUNKS=3
- `topk_75_chunks_5.jsonl` - Top-k=75, MAX_CHUNKS=5
- `topk_75_chunks_7.jsonl` - Top-k=75, MAX_CHUNKS=7
- `topk_variations_summary.json` - Summary of all top-k variations

### Evaluation Results (in `eval/` directory)

- `eval_results_[config_name].json` - Individual Ragas evaluation results
- `comprehensive_evaluation_report_[timestamp].json` - Complete comparison report

## Configuration Details

### Feature Flags Used

Each test script sets specific environment variables to control feature flags:

```python
# Baseline RAG
os.environ["RERANKER_ENABLED"] = "false"
os.environ["WEB_SEARCH_ENHANCEMENT"] = "false"
os.environ["HALLUCINATION_GUARDS"] = "false"

# RAG + Re-ranking
os.environ["RERANKER_ENABLED"] = "true"
os.environ["WEB_SEARCH_ENHANCEMENT"] = "false"
os.environ["HALLUCINATION_GUARDS"] = "false"

# RAG + Web
os.environ["RERANKER_ENABLED"] = "false"
os.environ["WEB_SEARCH_ENHANCEMENT"] = "true"
os.environ["HALLUCINATION_GUARDS"] = "false"

# Full Advanced
os.environ["RERANKER_ENABLED"] = "true"
os.environ["WEB_SEARCH_ENHANCEMENT"] = "true"
os.environ["HALLUCINATION_GUARDS"] = "true"
os.environ["SCHEMA_AWARE_CHUNKING"] = "true"
os.environ["INSTRUCTOR_XL_EMBEDDINGS"] = "true"
```

### Top-K Variations

The top-k variations test different combinations of:
- **Top-K values**: 10, 20, 50, 75
- **MAX_CHUNKS values**: 3, 5, 7
- **MAX_CONTEXT_TOKENS**: Calculated as `max_chunks * 400` (approximate)

## Metrics Evaluated

The Ragas evaluation uses the following metrics:
- **Faithfulness** - How well the answer is grounded in the provided context
- **Answer Relevancy** - How relevant the answer is to the question

## Expected Results

Based on typical RAG performance patterns, you should expect:

1. **Baseline RAG** - Lowest scores, serves as baseline
2. **RAG + Re-ranking** - Improved faithfulness due to better document ranking
3. **RAG + Web** - Potentially improved relevancy for questions requiring external knowledge
4. **Full Advanced** - Best overall performance with all enhancements
5. **Top-K Variations** - Performance may vary based on optimal chunk count and retrieval size

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from the project root and all dependencies are installed
2. **Environment Variables**: Make sure your `.env` file is properly configured
3. **Pinecone Connection**: Verify your Pinecone API key and index are accessible
4. **Memory Issues**: The full advanced pipeline may require more memory; consider running individual tests

### Performance Tips

1. **Run tests sequentially** to avoid memory issues
2. **Monitor GPU memory** if using local models
3. **Check logs** for detailed error information
4. **Start with baseline** to ensure basic functionality

## Analysis

After running all tests, use the comprehensive evaluation report to:

1. **Compare configurations** - See which features provide the most improvement
2. **Identify optimal parameters** - Find the best top-k and chunk settings
3. **Analyze trade-offs** - Balance performance vs. computational cost
4. **Guide future improvements** - Focus on areas with lowest scores

The comparison report includes:
- Best/worst/average scores for each metric
- Top-performing configurations
- Detailed breakdown by configuration
- Timestamped results for tracking improvements over time

# RAGv2 Upgrade Documentation

## Overview

This document describes the RAGv2 upgrade for FAQBuddy, which addresses key pain points in the current RAG system:
- Context drift and hallucinations
- Slow full re-indexing
- Weak PDF coverage
- Missing "one-hop" reasoning

## Architecture Changes

### Current RAG Stack
```
PostgreSQL JOIN → all-mpnet-base-v2 embeddings → Pinecone (cosine, top 20)
        ↘                               ↘
         large concatenated chunks        Elastic BM25 top 4
                                             ↘
                                           Mistral-7B-Instruct
```

### RAGv2 Stack
```
Schema-aware chunks → instructor-xl embeddings → Pinecone (cosine, top 50)
        ↘                                    ↘
         node_type metadata                   Cross-encoder reranker (bge-reranker-large)
        ↘                                    ↘
         natural language only               Context token management (≤ 4k tokens)
        ↘                                    ↘
         IDs in metadata only                Generation guard-rails
```

## Feature Flags

All RAGv2 features are controlled by environment variables for independent deployment:

### Core Features

| Feature Flag | Environment Variable | Default | Description |
|--------------|---------------------|---------|-------------|
| Schema-aware chunking | `SCHEMA_AWARE_CHUNKING` | `true` | Task 1: JSON objects per row with natural language |
| Instructor-XL embeddings | `INSTRUCTOR_XL_EMBEDDINGS` | `false` | Task 2: Replace all-mpnet-base-v2 |
| Cross-encoder reranker | `RERANKER_ENABLED` | `false` | Task 3: bge-reranker-large for improved retrieval |
| BM25 fallback | `BM25_FALLBACK` | `true` | Task 3: Keep BM25 as fallback option |
| Hallucination guards | `HALLUCINATION_GUARDS` | `false` | Task 5: Self-check prompts and answer verification |
| Graph-RAG | `GRAPH_RAG` | `false` | Task 4: Neo4j/Apache AGE integration |
| CDC incremental sync | `CDC_ENABLED` | `false` | Task 6: Real-time DB → vector-DB sync |
| PDF boost | `PDF_BOOST` | `false` | Task 7: Enhanced PDF ingestion |
| Observability | `OBSERVABILITY_ENABLED` | `false` | Task 8: Comprehensive logging and metrics |

### Advanced Configuration

| Configuration | Environment Variable | Default | Description |
|---------------|---------------------|---------|-------------|
| Graph database type | `GRAPH_DB_TYPE` | `neo4j` | `neo4j` or `age` |
| CDC queue type | `CDC_QUEUE_TYPE` | `memory` | `memory`, `redis`, or `kafka` |
| Log level | `LOG_LEVEL` | `INFO` | Logging verbosity |
| Metrics enabled | `METRICS_ENABLED` | `true` | Enable performance metrics |

## Implementation Tasks

### Task 1: Schema-aware Extraction & Chunking ✅

**Objective**: Emit one JSON object per row (≤ 400 tokens) with natural-language labels only.

**Implementation**:
- `backend/src/rag/utils/schema_aware_chunker.py`
- Natural language templates for each table type
- IDs stored only in Pinecone metadata
- `node_type` tag added to metadata

**Done-When**: Unit test passes for sample course_edition row → valid chunk

**Usage**:
```python
from rag.utils.schema_aware_chunker import SchemaAwareChunker

chunker = SchemaAwareChunker()
chunks = chunker.get_course_edition_chunks()
```

### Task 2: Embedding Upgrade ✅

**Objective**: Replace all-mpnet-base-v2 with instructor-xl and prepend instruction prefix.

**Implementation**:
- `backend/src/rag/utils/embeddings_v2.py`
- Automatic model selection based on feature flags
- Instruction prefix: "Represent an education QA passage for retrieval: "
- Latency monitoring and fallback support

**Done-When**: Backfill job completes; embedding latency ≤ 120 ms/row

**Usage**:
```python
from rag.utils.embeddings_v2 import EnhancedEmbeddings

embeddings = EnhancedEmbeddings()
vector = embeddings.encode_single("Sample text")
```

### Task 3: Retrieval Pipeline ✅

**Objective**: Dense top-50 → cross-encoder reranker, keep chunks ≥ 0.2 until context ≤ 4k tokens.

**Implementation**:
- `backend/src/rag/retrieval_v2.py`
- Enhanced retrieval with cross-encoder reranking
- Context token management
- BM25 fallback option

**Done-When**: Recall@5 on regression set ≥ +15% vs baseline

**Usage**:
```python
from rag.retrieval_v2 import EnhancedRetrieval

retrieval = EnhancedRetrieval(pinecone_client)
results = retrieval.retrieve("Who teaches Operating Systems?")
```

### Task 4: Graph-RAG (Planned)

**Objective**: Build property graph with tiny heuristic classifier for graph-friendly queries.

**Implementation**:
- Neo4j or Apache AGE integration
- Query routing to graph vs vector search
- Sub-graph verbalization

**Done-When**: Query "Who teaches Operating Systems this semester?" returns correct teacher via graph path

### Task 5: Generation Guard-rails ✅

**Objective**: Self-check prompts and answer verification to prevent hallucinations.

**Implementation**:
- `backend/src/rag/generation_guards.py`
- Self-check prompt: "Using only the sources above, answer. If unsure, say you don't know."
- Cross-encoder verification with threshold filtering
- Hallucination detection and refusal

**Done-When**: Synthetic hallucination test: refusal ≥ 95%

**Usage**:
```python
from rag.generation_guards import GenerationGuards

guards = GenerationGuards()
result = guards.generate_safe_answer(context, question)
```

### Task 6: CDC-based Incremental Embeddings (Planned)

**Objective**: Real-time database → vector database synchronization.

**Implementation**:
- Airbyte or Debezium for change detection
- Queue system (Redis/Kafka) for event processing
- Incremental embedding generation and Pinecone updates

**Done-When**: 10k row burst appears in Pinecone ≤ 2 min

### Task 7: PDF Ingestion (Planned)

**Objective**: Enhanced PDF processing with 512-token chunks and metadata.

**Implementation**:
- PDF chunking with page numbers
- Metadata: source_type="pdf", PDF path, page numbers
- Feature flag for reranker weight boost

**Done-When**: Queries known to live only in PDFs recall ≥ 90%

### Task 8: Observability ✅

**Objective**: Comprehensive logging and metrics for retrieval quality and latency.

**Implementation**:
- Per-query logging: router decision, retrieved_ids, source types, answer, hallucination flag, p95 latency
- Pipeline statistics and performance metrics
- Feature usage tracking

**Done-When**: Dashboards online and update nightly

## Deployment Guide

### Phase 1: Schema-aware Chunking (Safe to Deploy)

1. **Enable feature flag**:
   ```bash
   export SCHEMA_AWARE_CHUNKING=true
   ```

2. **Test the implementation**:
   ```bash
   cd backend/src/rag
   python -m utils.schema_aware_chunker
   ```

3. **Monitor performance** and verify chunks are generated correctly.

### Phase 2: Enhanced Embeddings (Requires Model Download)

1. **Enable feature flag**:
   ```bash
   export INSTRUCTOR_XL_EMBEDDINGS=true
   ```

2. **Download instructor-xl model** (will happen automatically on first use).

3. **Run backfill job** to update existing embeddings:
   ```bash
   python update_pinecone_from_neon.py --use-instructor-xl
   ```

4. **Monitor latency** to ensure ≤ 120ms per row.

### Phase 3: Retrieval Pipeline (Performance Critical)

1. **Enable feature flags**:
   ```bash
   export RERANKER_ENABLED=true
   export BM25_FALLBACK=true
   ```

2. **Download cross-encoder model** (will happen automatically).

3. **Test with regression set** to verify Recall@5 improvement.

4. **Monitor retrieval performance** and adjust thresholds if needed.

### Phase 4: Generation Guards (Quality Improvement)

1. **Enable feature flag**:
   ```bash
   export HALLUCINATION_GUARDS=true
   ```

2. **Test with synthetic hallucination dataset**.

3. **Monitor refusal rate** to ensure it stays reasonable.

### Phase 5: Observability (Monitoring)

1. **Enable feature flag**:
   ```bash
   export OBSERVABILITY_ENABLED=true
   ```

2. **Set up logging infrastructure** (ELK stack, etc.).

3. **Create dashboards** for monitoring.

## Rollback Procedures

### Emergency Rollback

To quickly disable all RAGv2 features:

```bash
export SCHEMA_AWARE_CHUNKING=false
export INSTRUCTOR_XL_EMBEDDINGS=false
export RERANKER_ENABLED=false
export HALLUCINATION_GUARDS=false
export OBSERVABILITY_ENABLED=false
```

### Selective Rollback

To rollback specific features:

```bash
# Rollback embeddings only
export INSTRUCTOR_XL_EMBEDDINGS=false

# Rollback reranker only
export RERANKER_ENABLED=false

# Rollback generation guards only
export HALLUCINATION_GUARDS=false
```

### Database Rollback

If schema-aware chunking causes issues:

1. **Disable feature flag**:
   ```bash
   export SCHEMA_AWARE_CHUNKING=false
   ```

2. **System will automatically fallback** to legacy chunker.

### Embedding Rollback

If instructor-xl causes performance issues:

1. **Disable feature flag**:
   ```bash
   export INSTRUCTOR_XL_EMBEDDINGS=false
   ```

2. **System will automatically fallback** to all-mpnet-base-v2.

## Testing

### Unit Tests

Run individual component tests:

```bash
# Test schema-aware chunking
python -m rag.utils.schema_aware_chunker

# Test enhanced embeddings
python -m rag.utils.embeddings_v2

# Test enhanced retrieval
python -m rag.retrieval_v2

# Test generation guards
python -m rag.generation_guards

# Test full pipeline
python -m rag.rag_pipeline_v2
```

### Integration Tests

Test the complete RAGv2 pipeline:

```bash
cd backend/tests
python test_ragv2_integration.py
```

### Performance Tests

Benchmark performance improvements:

```bash
cd backend/tests
python test_ragv2_performance.py
```

## Monitoring and Alerts

### Key Metrics

- **Retrieval latency**: Should remain < 500ms
- **Generation latency**: Should remain < 3s
- **Hallucination rate**: Should be < 5%
- **Refusal rate**: Should be < 20%
- **Feature usage**: Track which features are being used

### Alerts

Set up alerts for:
- High latency (> 1s for retrieval, > 5s for generation)
- High error rate (> 5%)
- High hallucination rate (> 10%)
- Feature flag conflicts

## Troubleshooting

### Common Issues

1. **Model loading failures**: Check internet connection and disk space
2. **High latency**: Monitor resource usage and consider model optimization
3. **Low recall**: Adjust reranker threshold or increase dense top-k
4. **High refusal rate**: Lower verification threshold or improve retrieval

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
export OBSERVABILITY_ENABLED=true
```

### Performance Tuning

- **Embedding batch size**: Adjust based on available memory
- **Cross-encoder threshold**: Lower for higher recall, higher for precision
- **Context token limit**: Adjust based on model context window

## Future Enhancements

### Planned Features

1. **Graph-RAG integration** (Task 4)
2. **CDC-based incremental sync** (Task 6)
3. **Enhanced PDF processing** (Task 7)
4. **Advanced observability dashboards** (Task 8)

### Research Areas

1. **Multi-modal retrieval** (images, tables)
2. **Conversational memory**
3. **Personalized retrieval**
4. **Federated search** across multiple knowledge bases

## Support

For issues or questions about the RAGv2 upgrade:

1. Check the troubleshooting section above
2. Review the logs with `OBSERVABILITY_ENABLED=true`
3. Run the unit tests to isolate the issue
4. Contact the development team with specific error messages and logs 
# RAGv2 Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the RAGv2 upgrade safely without affecting the existing system.

## Prerequisites

1. **Environment Setup**
   ```bash
   # Ensure you're on the RAGv2 branch
   git checkout feature/RAGv2
   
   # Install new dependencies
   pip install -r backend/src/requirements.txt
   ```

2. **Environment Variables**
   Create or update your `.env` file:
   ```bash
   # Required
   PINECONE_API_KEY=your_pinecone_api_key
   
   # Database (if using schema-aware chunking)
   DATABASE_URL=your_database_url
   
   # Optional: Enable specific features
   SCHEMA_AWARE_CHUNKING=true
   INSTRUCTOR_XL_EMBEDDINGS=false  # Start with false for testing
   RERANKER_ENABLED=false          # Start with false for testing
   HALLUCINATION_GUARDS=false      # Start with false for testing
   ```

## Phase 1: Validation (Safe)

### Step 1: Test Configuration
```bash
cd backend/src/rag
python test_ragv2_real.py
```

This will:
- ✅ Test all imports
- ✅ Validate Pinecone connection
- ✅ Test embeddings generation
- ✅ Test retrieval system
- ✅ Test generation guards
- ✅ Test full pipeline
- ✅ Verify namespace configuration

### Step 2: Verify Namespaces
```bash
python update_pinecone_ragv2.py --verify-only
```

This will:
- ✅ Check existing namespaces (should be untouched)
- ✅ Check RAGv2 namespaces (may not exist yet)
- ✅ Validate index configuration

## Phase 2: Safe Upsert (Non-Destructive)

### Step 3: Upsert to RAGv2 Namespaces
```bash
# Upsert database chunks to RAGv2 namespace
python update_pinecone_ragv2.py --batch-size 100

# Optional: Upsert PDF chunks
python update_pinecone_ragv2.py --pdf-dir /path/to/pdfs --batch-size 100
```

This will:
- ✅ Use new namespaces (`documents_v2`, `db_v2`, `pdf_v2`)
- ✅ Keep existing namespaces untouched
- ✅ Process chunks with enhanced embeddings
- ✅ Provide progress tracking and error handling

## Phase 3: Feature Rollout (Gradual)

### Step 4: Enable Features One by One

**Start with Schema-Aware Chunking:**
```bash
export SCHEMA_AWARE_CHUNKING=true
python test_ragv2_real.py
```

**Then Enhanced Embeddings:**
```bash
export INSTRUCTOR_XL_EMBEDDINGS=true
python test_ragv2_real.py
```

**Then Cross-Encoder Reranking:**
```bash
export RERANKER_ENABLED=true
python test_ragv2_real.py
```

**Finally Generation Guards:**
```bash
export HALLUCINATION_GUARDS=true
python test_ragv2_real.py
```

## Phase 4: Integration Testing

### Step 5: Test with Real Queries
```bash
cd backend/src/rag
python demo_ragv2.py
```

This will:
- ✅ Test different feature flag combinations
- ✅ Run performance benchmarks
- ✅ Show usage examples
- ✅ Validate end-to-end functionality

### Step 6: Performance Validation
```bash
# Test embedding performance (should be ≤ 120ms/row)
python -c "
from rag.utils.embeddings_v2 import EnhancedEmbeddings
embeddings = EnhancedEmbeddings()
results = embeddings.benchmark_embedding_performance()
print(f'Average latency: {results[\"average_latency\"]:.2f}ms')
assert results['average_latency'] <= 120, 'Latency too high'
"
```

## Phase 5: Production Deployment

### Step 7: Update Application Configuration
Update your main application to use RAGv2:

```python
# In your main application
from rag.rag_pipeline_v2 import RAGv2Pipeline
from pinecone import Pinecone

# Initialize RAGv2 pipeline
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
ragv2_pipeline = RAGv2Pipeline(pc)

# Use for complex queries
result = ragv2_pipeline.answer("Who teaches Operating Systems this semester?")
```

### Step 8: Monitor and Validate
```bash
# Check pipeline statistics
python -c "
from rag.rag_pipeline_v2 import RAGv2Pipeline
from pinecone import Pinecone
pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
pipeline = RAGv2Pipeline(pc)
stats = pipeline.get_pipeline_stats()
print('Pipeline stats:', stats)
"
```

## Rollback Plan

If issues arise, you can easily rollback:

### Option 1: Disable Features
```bash
# Disable all RAGv2 features
export SCHEMA_AWARE_CHUNKING=false
export INSTRUCTOR_XL_EMBEDDINGS=false
export RERANKER_ENABLED=false
export HALLUCINATION_GUARDS=false
```

### Option 2: Switch Back to Original Pipeline
```python
# Use original RAG pipeline instead of RAGv2
from rag.rag_pipeline import RAGPipeline  # Original pipeline
```

### Option 3: Use Existing Namespaces
```python
# Modify config to use existing namespaces
# (This would require code changes)
```

## Monitoring

### Key Metrics to Watch
1. **Embedding Latency**: Should be ≤ 120ms/row
2. **Retrieval Quality**: Check recall@5 improvements
3. **Hallucination Rate**: Should be < 5% with guards enabled
4. **Response Time**: Should be reasonable (< 5s for complex queries)

### Logs to Monitor
- Query processing times
- Feature flag usage
- Error rates
- Namespace usage patterns

## Troubleshooting

### Common Issues

**1. Import Errors**
```bash
# Ensure all dependencies are installed
pip install -r backend/src/requirements.txt
```

**2. Pinecone Connection Issues**
```bash
# Verify API key
echo $PINECONE_API_KEY
```

**3. Database Connection Issues**
```bash
# Check database URL
echo $DATABASE_URL
```

**4. High Latency**
```bash
# Check embedding model
python -c "
from rag.utils.embeddings_v2 import EnhancedEmbeddings
embeddings = EnhancedEmbeddings()
print(f'Model: {embeddings.model_name}')
"
```

### Getting Help

1. Check the logs for detailed error messages
2. Run the test script: `python test_ragv2_real.py`
3. Verify namespace configuration: `python update_pinecone_ragv2.py --verify-only`
4. Review the `docs/RAG_UPGRADE.md` for detailed technical information

## Success Criteria

✅ **Phase 1**: All tests pass with real Pinecone  
✅ **Phase 2**: Safe upsert to RAGv2 namespaces completed  
✅ **Phase 3**: Features can be enabled/disabled independently  
✅ **Phase 4**: Integration tests pass  
✅ **Phase 5**: Production deployment successful  

## Next Steps

After successful deployment:

1. **Monitor Performance**: Watch for any performance regressions
2. **Gather Feedback**: Collect user feedback on answer quality
3. **Optimize**: Fine-tune parameters based on real usage
4. **Scale**: Consider enabling additional features (Graph-RAG, CDC, etc.)

---

**Remember**: The RAGv2 system is designed to be safe and non-destructive. The existing system remains untouched, and you can rollback at any time by disabling feature flags. 
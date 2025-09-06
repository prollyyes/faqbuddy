# FAQBuddy Maintenance Guide

## Overview

FAQBuddy is a university FAQ system with multiple RAG (Retrieval-Augmented Generation) implementations. The system has evolved through several iterations, resulting in multiple pipelines and approaches.

## System Architecture

### Core Components

1. **Backend API** (`backend/src/api/`)
   - `Chat.py` - Main chat endpoint (current implementation)
   - `API.py` - Legacy API router
   - `AuthAPI.py` - Authentication endpoints
   - `Profile.py` - User profile management
   - `Search.py` - Search functionality

2. **RAG Systems** (`backend/src/rag/`)
   - **Legacy RAG** - Original implementation
   - **RAGv2** - Enhanced pipeline with feature flags
   - **Advanced RAG** - State-of-the-art implementation with verification

3. **Database Systems**
   - **PostgreSQL** (Neon) - Structured university data
   - **Pinecone** - Vector database for semantic search
   - **Multiple namespaces** - documents_v2, per_row, pdf_v2

4. **Models**
   - **Mistral 7B** - Main language model (capybarahermes-2.5-mistral-7b.Q4_K_M.gguf)
   - **Gemma 3B** - Secondary model for classification
   - **Embedding models** - all-mpnet-base-v2, hkunlp/instructor-xl

## Current Active Systems

### 1. Advanced RAG Pipeline (Recommended)

**Location**: `backend/src/rag/advanced_rag_pipeline.py`

**Features**:
- Query understanding and intent classification
- Advanced retrieval with query expansion
- Chain-of-thought prompt engineering
- Comprehensive answer verification
- Hallucination prevention

**CLI Interface**: `backend/src/rag/run_advanced_rag_cli.py`

**Usage**:
```bash
cd backend/src
python rag/run_advanced_rag_cli.py
```

### 2. RAGv2 Pipeline (Legacy)

**Location**: `backend/src/rag/rag_pipeline_v2.py`

**Features**:
- Feature flag controlled components
- Schema-aware chunking
- Enhanced embeddings
- Cross-encoder reranking
- Web search enhancement

**CLI Interface**: `backend/src/rag/run_rag_v2_cli.py`

### 3. Per-Row Vector Database

**Location**: `backend/src/rag/utils/per_row_chunker.py`

**Purpose**: Stores one vector per database row instead of chunked text

**Namespace**: `per_row` in Pinecone

**Population Script**: `populate_per_row.py`

## Configuration Management

### Feature Flags

**Location**: `backend/src/rag/config.py`

Key settings:
- `HALLUCINATION_GUARDS` - Enable answer verification
- `SCHEMA_AWARE_CHUNKING` - Use schema-aware chunking
- `INSTRUCTOR_XL_EMBEDDINGS` - Use advanced embeddings
- `RERANKER_ENABLED` - Enable cross-encoder reranking
- `WEB_SEARCH_ENHANCEMENT` - Enable web search

### Environment Variables

Required in `.env`:
- `PINECONE_API_KEY` - Pinecone vector database access
- `DATABASE_URL` - PostgreSQL connection string
- `OPENAI_API_KEY` - For web search enhancement

## Data Management

### Vector Database Namespaces

1. **per_row** - One vector per database row (current approach)
2. **documents_v2** - Document-based chunks
3. **pdf_v2** - PDF document chunks

### Database Population

**Per-row approach**:
```bash
python populate_per_row.py
```

**Legacy approach**:
```bash
python populate_ragv2.py
```

### Data Sources

- **Database**: PostgreSQL with university data (courses, professors, students)
- **PDFs**: University documents in `backend/data/`
- **Web**: Real-time search enhancement

## Testing and Evaluation

### Test Scripts

1. **Quick System Test**: `quick_system_test.py`
2. **Comprehensive Test**: `final_system_test.py`
3. **Approach Comparison**: `compare_approaches.py`
4. **Thesis Evaluation**: `thesis_evaluation_framework.py`

### Benchmarking

**Location**: `benchmark/`
- RAGAS evaluation framework
- Performance metrics
- Quality assessment

## Common Issues and Solutions

### 1. Empty Answers

**Problem**: System returns empty responses
**Cause**: LLM generation issues or prompt complexity
**Solution**: 
- Check GPU memory usage
- Simplify prompts
- Verify model loading

### 2. Low Retrieval Quality

**Problem**: Poor source retrieval
**Cause**: Cross-encoder threshold too high
**Solution**: Adjust `RERANKER_THRESHOLD` in config.py

### 3. Hallucination Issues

**Problem**: Incorrect information in answers
**Cause**: Verification system disabled or misconfigured
**Solution**: Enable `HALLUCINATION_GUARDS` and verify thresholds

### 4. Import Errors

**Problem**: Module not found errors
**Cause**: Python path issues
**Solution**: Run from `backend/src/` directory or adjust sys.path

## Maintenance Tasks

### Daily

1. Check system logs for errors
2. Monitor GPU memory usage
3. Verify database connections

### Weekly

1. Update vector database with new data
2. Run comprehensive tests
3. Review performance metrics

### Monthly

1. Evaluate system performance
2. Update models if needed
3. Review and clean up old data

## Development Workflow

### Adding New Features

1. Create feature branch
2. Implement with feature flags
3. Add tests
4. Update documentation
5. Deploy with flags disabled
6. Enable gradually

### Debugging

1. Use CLI interfaces for testing
2. Check logs in `backend/src/ragv2_queries.log`
3. Verify data in Pinecone console
4. Test individual components

### Performance Optimization

1. Monitor retrieval times
2. Optimize embedding models
3. Adjust cross-encoder thresholds
4. Balance accuracy vs speed

## File Organization

### Critical Files

- `backend/src/rag/config.py` - All configuration
- `backend/src/rag/advanced_rag_pipeline.py` - Main system
- `backend/src/api/Chat.py` - API endpoint
- `populate_per_row.py` - Data population

### Test Files

- `quick_system_test.py` - Basic functionality
- `final_system_test.py` - Comprehensive testing
- `compare_approaches.py` - Performance comparison

### Documentation

- `README.md` - Project overview
- `docs/RAG_UPGRADE.md` - RAG system details
- `UBUNTU_SETUP.md` - Setup instructions

## Quick Commands

### Start System
```bash
cd backend/src
python rag/run_advanced_rag_cli.py
```

### Test System
```bash
python quick_system_test.py
```

### Populate Data
```bash
python populate_per_row.py
```

### Compare Approaches
```bash
python compare_approaches.py
```

## Troubleshooting Checklist

1. **Environment**: Verify conda environment is activated
2. **Dependencies**: Check all packages are installed
3. **API Keys**: Verify Pinecone and other API keys
4. **GPU**: Ensure CUDA is working for models
5. **Database**: Check Neon connection
6. **Vector DB**: Verify Pinecone index exists
7. **Models**: Ensure model files are present
8. **Logs**: Check for error messages in logs

## Support

For issues:
1. Check this maintenance guide
2. Review error logs
3. Test with simple queries
4. Verify configuration settings
5. Check system resources (GPU, memory)

Remember: The Advanced RAG Pipeline is the current recommended system for production use.

# RAG System for FAQBuddy

## Overview

This RAG (Retrieval-Augmented Generation) system is designed for university FAQ management, combining document-based knowledge with structured database information. The system uses hybrid retrieval with namespace-aware balancing to provide accurate and contextually relevant responses.

## Architecture

### Core Components

1. **Hybrid Retrieval System** (`hybrid_retrieval.py`)
   - Combines dense vector search (Pinecone) with sparse keyword search (BM25)
   - Implements namespace-aware scoring for balanced retrieval
   - Uses cross-encoder reranking for improved result quality

2. **Query Router** (`query_router.py`)
   - Classifies queries as structured (database) or unstructured (documents)
   - Routes queries to appropriate retrieval methods
   - Merges results from different sources

3. **RAG Pipeline** (`rag_pipeline.py`)
   - Orchestrates the complete retrieval and generation process
   - Integrates with local LLM for answer generation
   - Provides debugging output for namespace distribution

4. **Namespace Configuration** (`namespace_config.py`)
   - Centralized configuration for namespace balancing
   - Keyword-based boost determination
   - Adjustable parameters for fine-tuning

## Automated Setup

The system includes automated setup scripts that handle all initialization:

### Option 1: Database-Only Setup
For systems with existing database infrastructure:

```bash
cd backend/src/rag
python update_pinecone_db.py
```

This script:
- Connects to Pinecone and creates/updates the vector index
- Generates embeddings for database content
- Uploads vectors to the "db" namespace
- Preserves existing document chunks in the "documents" namespace
- Handles dimension mismatches and index recreation
- Provides detailed logging and error handling

### Option 2: Complete Docker Setup
For fresh installations or development environments:

```bash
python setup_docker_database.py
```

This comprehensive script:
- Checks Docker availability and requirements
- Stops existing database containers (if any)
- Starts a fresh PostgreSQL database using Docker Compose
- Applies the complete database schema
- Verifies database setup and connectivity
- Populates the database with sample data
- Updates environment configuration files
- Runs the Pinecone update script automatically
- Provides step-by-step progress tracking

The Docker setup creates a complete development environment with:
- PostgreSQL database running on port 5433
- Pre-configured database schema
- Sample data for testing
- Updated Pinecone index with database chunks
- Proper environment variable configuration

### Setup Verification

After running either setup script, verify the installation:

```bash
# Test the RAG system
cd backend/src/rag
python run_rag_cli.py

# Test namespace balancing
python test_namespace_fix.py
```

## Namespace Balancing

The system uses two distinct namespaces in Pinecone:

### Documents Namespace
- Contains chunked PDF documents (regulations, procedures, guidelines)
- Optimized for procedural and regulatory queries
- Boosted for queries containing keywords like: "regolamento", "procedure", "requisiti", "scadenze"

### Database Namespace  
- Contains structured database information (courses, professors, contacts)
- Optimized for factual and list-based queries
- Boosted for queries containing keywords like: "elenca", "mostra", "lista", "contatti"

### Dynamic Boost Calculation

The system dynamically determines namespace boosts based on query content:

```python
# Default boosts (when no specific keywords detected)
DEFAULT_DOCS_BOOST = 1.1  # 10% boost for documents
DEFAULT_DB_BOOST = 1.0    # No boost for database

# Strong boosts when specific keywords are detected
STRONG_DOCS_BOOST = 1.2   # 20% boost for documents
STRONG_DB_BOOST_WHEN_DB = 1.1  # 10% boost for database
```

The boost determination algorithm:
1. Analyzes query for document-specific keywords (regulations, procedures, etc.)
2. Analyzes query for database-specific keywords (lists, contacts, etc.)
3. Applies appropriate boost based on keyword matches
4. Normalizes scores within each namespace before combining

## Retrieval Process

### 1. Query Analysis
- Intent classification (structured vs unstructured)
- Keyword extraction for namespace boost determination
- Entity recognition for enhanced matching

### 2. Hybrid Retrieval
- **Dense Retrieval**: Semantic search using sentence transformers
- **Sparse Retrieval**: Keyword-based search using BM25
- **Namespace-Aware Scoring**: Dynamic boost application
- **Score Normalization**: Ensures fair comparison between namespaces

### 3. Result Fusion
- Combines dense and sparse results using weighted fusion
- Default fusion weight: 60% dense, 40% sparse (configurable via ALPHA parameter)
- Maintains namespace information throughout the process

### 4. Cross-Encoder Reranking
- Uses cross-encoder model for final result ordering
- Improves relevance by considering query-document pairs
- Falls back gracefully if cross-encoder is unavailable

## Configuration

### Namespace Configuration (`namespace_config.py`)

```python
# Boost values
DEFAULT_DOCS_BOOST = 1.1
STRONG_DOCS_BOOST = 1.2
STRONG_DB_BOOST_WHEN_DB = 1.1

# Keywords for boost determination
DOCUMENT_KEYWORDS = [
    'regolamento', 'norme', 'procedure', 'requisiti', 'criteri',
    'scadenze', 'termini', 'documentazione', 'certificati',
    'esami', 'lauree', 'tesi', 'stage', 'tirocinio'
]

DATABASE_KEYWORDS = [
    'quali', 'elenca', 'mostra', 'lista', 'tutti', 'corsi',
    'professori', 'studenti', 'contatti', 'orari', 'aula'
]

# Debug mode for detailed logging
DEBUG_MODE = True
```

### Retrieval Configuration (`hybrid_retrieval.py`)

```python
# Core parameters
TOP_K = 5                    # Number of results to retrieve
ALPHA = 0.6                  # Weight for dense vs sparse fusion
EMBEDDING_MODEL = "all-mpnet-base-v2"
CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Chunking parameters
CHUNK_WINDOW = 200           # Tokens per chunk
CHUNK_OVERLAP = 50           # Overlap between chunks
```

## Usage

### Command Line Interface

```bash
cd backend/src/rag
python run_rag_cli.py
```

### Programmatic Usage

```python
from rag_pipeline import RAGPipeline

# Initialize the pipeline
rag = RAGPipeline()

# Process a query
answer = rag.answer("Come funziona l'iscrizione al corso di laurea?")
print(answer)
```

### Testing Namespace Balancing

```bash
cd backend/src/rag
python test_namespace_fix.py
```

This script tests the namespace balancing with various query types and shows boost calculations.

### Docker Management

If using the Docker setup, manage the database container:

```bash
# Start the database
docker-compose up -d

# Stop the database
docker-compose down

# View database logs
docker-compose logs

# Access database directly
docker exec -it faqbuddy_postgres_db psql -U db_user -d faqbuddy_db
```

## Performance Optimization

### Score Normalization
- Prevents one namespace from dominating due to different score distributions
- Ensures fair comparison between document and database results
- Uses min-max normalization within each namespace

### Batch Processing
- Vector uploads are processed in batches of 100
- Reduces API calls and improves reliability
- Includes error handling and retry logic

### Caching
- Embedding model is loaded once and reused
- Pinecone connection is maintained throughout the session
- Document chunks are cached for BM25 search

## Error Handling

The system includes comprehensive error handling:

- **Index Dimension Mismatches**: Automatically detects and recreates index with correct dimensions
- **Missing Namespaces**: Gracefully handles missing namespaces and provides fallback
- **Model Loading Failures**: Falls back to alternative models or continues without advanced features
- **API Rate Limits**: Implements batch processing to avoid rate limiting
- **Database Connection Issues**: Provides detailed error messages and recovery suggestions

## Monitoring and Debugging

### Debug Output
When DEBUG_MODE is enabled, the system provides detailed information:
- Keyword analysis results
- Namespace boost calculations
- Final result distribution
- Retrieval timing information

### Logging
- Detailed logs are written to `debugging_pinecone.json`
- Includes timestamps, steps, and error information
- Useful for troubleshooting and performance analysis

## Dependencies

### Core Dependencies
- `sentence-transformers`: For text embeddings
- `pinecone-client`: For vector database operations
- `rank-bm25`: For sparse retrieval
- `python-dotenv`: For environment variable management

### Optional Dependencies
- `torch`: For GPU acceleration (if available)
- `transformers`: For cross-encoder reranking

## Environment Variables

Required environment variables:

### For Existing Database Setup
```env
PINECONE_API_KEY=your_pinecone_api_key
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=your_database_host
DB_PORT=your_database_port
```

### For Docker Setup
The Docker setup script automatically configures these values:
```env
# Database Configuration (Docker)
DB_NAME=faqbuddy_db
DB_USER=db_user
DB_PASSWORD=pwd
DB_HOST=localhost
DB_PORT=5433

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_api_key_here
```

**Note**: The Docker setup script will prompt you to enter your Pinecone API key during the setup process and automatically create the `.env` file with the correct configuration.

## File Structure

```
backend/src/rag/
├── hybrid_retrieval.py      # Main retrieval system
├── rag_pipeline.py          # Complete RAG pipeline
├── query_router.py          # Query classification and routing
├── build_prompt.py          # Prompt construction
├── namespace_config.py      # Namespace balancing configuration
├── update_pinecone_db.py    # Automated setup script
├── run_rag_cli.py           # Command line interface
├── utils/                   # Utility functions
│   ├── embeddings.py        # Embedding utilities
│   ├── generate_chunks.py   # Database chunk generation
│   ├── pdf_chunker.py       # PDF processing
│   └── vector_db.py         # Vector database utilities
└── README.md               # This file
```

## Best Practices

1. **Regular Index Updates**: Run the setup script periodically to keep database chunks current
2. **Monitor Namespace Distribution**: Use debug output to ensure balanced retrieval
3. **Adjust Boost Values**: Fine-tune namespace boosts based on your specific use case
4. **Test with Various Queries**: Ensure the system handles both document and database queries effectively
5. **Monitor Performance**: Use the logging system to track retrieval times and success rates

## Troubleshooting

### Common Issues

1. **Dimension Mismatch**: The setup script automatically handles this by recreating the index
2. **Missing Namespaces**: Ensure both "documents" and "db" namespaces exist in your Pinecone index
3. **Low Retrieval Quality**: Adjust boost values or add relevant keywords to the configuration
4. **Slow Performance**: Consider using GPU acceleration or reducing batch sizes

### Performance Tuning

- Increase TOP_K for broader retrieval
- Adjust ALPHA for different dense/sparse balance
- Modify boost values based on query patterns
- Use GPU acceleration for embedding generation 
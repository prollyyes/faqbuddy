# FAQBuddy - Intelligent University Assistant

FAQBuddy is an intelligent question-answering system designed for university environments. It combines RAG (Retrieval-Augmented Generation) technology with Text-to-SQL conversion and ML-based question classification to provide accurate answers about courses, professors, materials, and university-related information.

## Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 18+**
- **Neon PostgreSQL Database** (cloud database)
- **Pinecone API Key** (for vector database)

### 1. Setup (One-time)

#### Option A: GUI Setup Wizard (Recommended)
Run the modern GUI setup wizard:

```bash
python setup_faqbuddy_gui.py
```

The GUI wizard provides:
- Modern, intuitive interface with Apple design language
- Secure password fields for sensitive data
- Real-time progress tracking with background processing
- Comprehensive validation and error checking
- Role-based setup (Admin/User) with different privileges

#### Option B: Command Line Setup
For advanced users or headless environments:

```bash
python setup_faqbuddy.py
```

Both setup methods will:
- Check Python version compatibility
- Configure environment variables (.env file)
- Test database connection to Neon
- Download required AI models (Mistral 7B, Gemma 3B)
- Set up Pinecone vector database with database namespace
- Install Python and Node.js dependencies

### 2. Launch

Start both servers with a single command:

```bash
python launch_servers.py
```

Or start them separately:

**Backend Server:**
```bash
cd backend
python -m uvicorn src.api.API:app --reload --host 0.0.0.0 --port 8000
```

**Frontend Server:**
```bash
cd frontend
npm run dev
```

### 3. Access

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Architecture

### Core System Components

**Question Classification System:**
- ML-based classifier using scikit-learn
- Routes questions to appropriate processing method
- Confidence-based fallback to RAG system

**Text-to-SQL Conversion:**
- Converts natural language to SQL queries
- Uses Mistral 7B for query generation
- Safety validation and query cleaning
- Fallback to RAG if SQL generation fails

**RAG System:**
- Hybrid retrieval combining dense embeddings with BM25 search
- Multi-namespace approach (documents vs database content)
- Cross-encoder reranking for improved relevance
- Intent classification for query routing

**Vector Database:**
- Pinecone for semantic search
- Separate namespaces for different content types
- Automatic chunking and embedding generation

### Models

- **Mistral 7B Instruct**: Main language model for answer generation and SQL conversion
- **Gemma 3B**: Secondary model for question classification
- **all-mpnet-base-v2**: Embedding model for semantic search
- **Cross-encoder**: For result reranking

### Database Architecture

- **Neon PostgreSQL**: Cloud database for structured university data
- **Pinecone**: Vector database for semantic search
- **Hybrid Approach**: Combines structured SQL queries with semantic search

## Project Structure

```
faqbuddy/
├── setup_faqbuddy_gui.py          # GUI setup wizard (recommended)
├── setup_faqbuddy.py              # Command-line setup
├── launch_servers.py              # Server launcher
├── requirements.txt               # Python dependencies
├── .env                          # Environment variables
├── backend/
│   ├── src/
│   │   ├── api/                  # API endpoints
│   │   │   ├── API.py           # Main API router
│   │   │   ├── Chat.py          # Chat endpoint (replaces main.py)
│   │   │   ├── AuthAPI.py       # Authentication endpoints
│   │   │   ├── Profile.py       # User profile management
│   │   │   ├── Search.py        # Search functionality
│   │   │   ├── BaseModel.py     # Pydantic models
│   │   │   ├── utils.py         # API utilities
│   │   │   └── drive_utils.py   # Google Drive integration
│   │   ├── auth/                # Authentication system
│   │   │   ├── dependencies.py  # Auth dependencies
│   │   │   └── jwt_handler.py   # JWT token management
│   │   ├── rag/                 # RAG system
│   │   │   ├── rag_adapter.py   # RAG system interface
│   │   │   ├── rag_pipeline.py  # Main RAG pipeline
│   │   │   ├── hybrid_retrieval.py # Hybrid search implementation
│   │   │   ├── query_router.py  # Query routing logic
│   │   │   ├── build_prompt.py  # Prompt engineering
│   │   │   ├── namespace_config.py # Namespace configuration
│   │   │   ├── update_pinecone_from_neon.py # Database vector update
│   │   │   └── utils/           # RAG utilities
│   │   │       ├── embeddings.py # Embedding generation
│   │   │       ├── generate_chunks.py # Database chunking
│   │   │       ├── pdf_chunker.py # PDF processing
│   │   │       └── vector_db.py # Vector database operations
│   │   ├── switcher/            # ML question classification
│   │   │   ├── MLmodel.py       # ML model interface
│   │   │   ├── create_MLmodel.py # Model creation script
│   │   │   └── dataset_domande.csv # Training dataset
│   │   ├── text_2_SQL/          # Text-to-SQL conversion
│   │   │   ├── converter.py     # Main converter
│   │   │   ├── db_utils.py      # Database utilities
│   │   │   └── __init__.py      # Package initialization
│   │   ├── utils/               # Core utilities
│   │   │   ├── db_utils.py      # Database connection management
│   │   │   ├── db_handler.py    # Database operations handler
│   │   │   ├── llm_mistral.py   # Mistral LLM integration
│   │   │   └── llm_gemma.py     # Gemma LLM integration
│   │   └── requirements.txt     # Backend dependencies
│   ├── models/                  # AI models storage
│   ├── data/                    # Data files
│   └── tests/                   # Test files
│       ├── test_pipeline.py     # Integration tests
│       ├── test_rag.py          # RAG system tests
│       ├── test_t2sql.py        # Text-to-SQL tests
│       └── test_ml.py           # ML model tests
├── db/                          # Database setup
│   ├── schema.sql              # Database schema
│   ├── create_db.py            # Database creation
│   ├── setup_data.py           # Data insertion
│   └── utils.py                # Database utilities
├── frontend/                    # Next.js frontend
│   ├── src/
│   │   ├── app/                # App router
│   │   │   ├── (protected)/    # Protected routes
│   │   │   │   ├── homepage/   # Main application
│   │   │   │   │   ├── chat/   # Chat interface
│   │   │   │   │   ├── materials/ # Material management
│   │   │   │   │   └── upload/ # File upload
│   │   │   │   └── profile/    # User profile
│   │   │   ├── auth/           # Authentication pages
│   │   │   └── layout.js       # Root layout
│   │   └── components/         # React components
│   │       ├── pages/          # Page components
│   │       ├── utils/          # Utility components
│   │       └── context/        # React context
│   ├── public/                 # Static assets
│   └── package.json            # Frontend dependencies
└── docker-compose.yml          # Docker configuration
```

## Configuration

### Environment Variables (.env)
## *THIS IS FOR PROD ONLY, TO BE DELETED!!*

The setup wizard will securely prompt for these credentials:

```env
# Neon Database Configuration
DB_NEON_NAME=your_database_name
DB_NEON_USER=your_username
DB_NEON_PASSWORD=your_password
DB_NEON_HOST=your_host
DB_NEON_PORT=5432

# Local Database (fallback)
DB_NAME=faqbuddy_db
DB_USER=db_user
DB_PASSWORD=pwd
DB_HOST=localhost
DB_PORT=5433

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key

# Email Configuration
EMAIL_FROM=your_email@gmail.com
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
```

### Required Models

The setup automatically downloads:
- `mistral-7b-instruct-v0.2.Q4_K_M.gguf` (4.1GB) - Main LLM for answer generation and SQL conversion
- `gemma-3-4b-it-Q4_1.gguf` (1.5GB) - Secondary model for question classification

## Features

### Intelligent Question Answering

**Question Classification:**
- ML-based routing using scikit-learn
- Confidence-based decision making
- Automatic fallback to RAG system

**Text-to-SQL Conversion:**
- Natural language to SQL query conversion
- Safety validation and query cleaning
- Automatic fallback on SQL generation failure
- Structured result formatting

**RAG System:**
- Hybrid retrieval (dense + sparse search)
- Multi-namespace content organization
- Cross-encoder reranking
- Context-aware answer generation

### User Interface

**Authentication System:**
- JWT-based authentication
- Role-based access control (Admin/User)
- Secure password handling
- Email verification system

**Chat Interface:**
- Real-time question-answering
- Message history and persistence
- Response time tracking
- Context preservation

**Material Management:**
- Document upload and organization
- File type validation
- User-specific material storage
- Rating and review system

**User Profiles:**
- Personal information management
- Course enrollment tracking
- Academic statistics
- Progress monitoring

### Technical Features

**Backend:**
- FastAPI for high-performance API
- Async/await for concurrent operations
- Comprehensive error handling
- Request/response validation

**Frontend:**
- Next.js 14 with App Router
- React components with TypeScript
- Responsive design
- Real-time updates

**Database:**
- PostgreSQL for structured data
- Vector database for semantic search
- Connection pooling
- Transaction management

## Development

### Adding New Features

**Backend Development:**
1. Add new endpoints in `backend/src/api/`
2. Create Pydantic models in `BaseModel.py`
3. Implement business logic in appropriate modules
4. Add tests in `backend/tests/`

**Frontend Development:**
1. Create new pages in `frontend/src/app/`
2. Add components in `frontend/src/components/`
3. Update routing in `layout.js`
4. Add styling and interactions

**RAG System Extension:**
1. Modify retrieval logic in `backend/src/rag/`
2. Update chunking in `utils/generate_chunks.py`
3. Adjust prompts in `build_prompt.py`
4. Test with `run_rag_cli.py`

### Testing

```bash
# Backend tests
cd backend
python -m pytest tests/

# Specific test files
python -m pytest -s tests/test_pipeline.py
python -m pytest -s tests/test_rag.py
python -m pytest -s tests/test_t2sql.py
python tests/test_ml.py

# Frontend tests
cd frontend
npm test
```

### Database Management

```bash
# Create database
python db/create_db.py

# Reset database
python db/reset_database.py

# Setup with sample data
python db/setup_data.py

# Update vector database
python backend/src/rag/update_pinecone_from_neon.py
```

## Performance

**Response Times:**
- Simple queries: < 1 second
- Complex RAG queries: < 8 seconds
- SQL queries: < 500ms
- Model loading: ~30 seconds (first time)

**Accuracy Metrics:**
- Question classification: ~85% accuracy
- SQL generation: ~70% success rate
- RAG retrieval: High relevance through hybrid search
- Answer quality: Context-aware and domain-specific

**Scalability:**
- Cloud-based infrastructure
- Connection pooling
- Async processing
- Caching mechanisms

## Troubleshooting

### Common Issues

**Setup Problems:**
- Ensure Python 3.8+ and Node.js 18+
- Check all environment variables are set
- Verify database connection credentials
- Ensure sufficient disk space for models

**Runtime Issues:**
- Check API documentation at http://localhost:8000/docs
- Review backend logs for error messages
- Verify model files are downloaded correctly
- Test database connectivity

**Performance Issues:**
- Monitor memory usage during model loading
- Check Pinecone index status
- Verify database query performance
- Review network connectivity

### Debugging

**Backend Debugging:**
```bash
# Run with debug logging
cd backend
python -m uvicorn src.api.API:app --reload --log-level debug

# Test specific components
python backend/src/rag/run_rag_cli.py
python backend/tests/test_pipeline.py
```

**Frontend Debugging:**
```bash
# Run in development mode
cd frontend
npm run dev

# Check for build errors
npm run build
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the API documentation at http://localhost:8000/docs
2. Review the setup logs for configuration issues
3. Ensure all environment variables are properly set
4. Test individual components using the provided test files

---

**Note**: This is a research project for university environments. The system is designed to handle academic queries and university-related information efficiently through a combination of structured database queries and semantic search capabilities. 
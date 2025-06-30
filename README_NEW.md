# FAQBuddy - Intelligent University Assistant

FAQBuddy is an intelligent question-answering system designed for university environments. It combines RAG (Retrieval-Augmented Generation) technology with a hybrid retrieval system to provide accurate answers about courses, professors, materials, and university-related information.

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **Node.js 18+**
- **Neon PostgreSQL Database** (cloud database)
- **Pinecone API Key** (for vector database)

### 1. Setup (One-time)

#### Option A: GUI Setup Wizard (Recommended)
Run the beautiful GUI setup wizard:

```bash
python setup_faqbuddy_gui.py
```

The GUI wizard provides:
- 🎨 **Beautiful Interface**: Modern, intuitive design
- 🔒 **Secure Input**: Password fields for sensitive data
- 📊 **Progress Tracking**: Real-time progress indicators
- ⚡ **Background Processing**: Non-blocking operations
- ✅ **Validation**: Comprehensive error checking

#### Option B: Command Line Setup
For advanced users or headless environments:

```bash
python setup_faqbuddy.py
```

Both setup methods will:
- ✅ Check Python version compatibility
- ✅ Configure environment variables (.env file)
- ✅ Test database connection
- ✅ Download required AI models (Mistral 7B)
- ✅ Set up Pinecone vector database
- ✅ Install all dependencies

### 2. Launch

Start both servers with a single command:

```bash
python launch_servers.py
```

Or start them separately:

**Backend Server:**
```bash
cd backend
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
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

## 🏗️ Architecture

### RAG System
- **Hybrid Retrieval**: Combines dense embeddings with sparse BM25 search
- **Multi-namespace**: Separate namespaces for documents and database content
- **Cross-encoder Reranking**: Improves result relevance
- **Intent Classification**: Routes queries to appropriate retrieval methods

### Models
- **Mistral 7B Instruct**: Main language model for answer generation
- **all-mpnet-base-v2**: Embedding model for semantic search
- **Cross-encoder**: For result reranking

### Database
- **Neon PostgreSQL**: Cloud database for structured data
- **Pinecone**: Vector database for semantic search
- **Hybrid Approach**: Combines structured SQL queries with semantic search

## 📁 Project Structure

```
faqbuddy/
├── setup_faqbuddy_gui.py      # GUI setup wizard (recommended)
├── setup_faqbuddy.py          # Command-line setup
├── launch_servers.py          # Server launcher
├── backend/
│   ├── src/
│   │   ├── main.py           # FastAPI application
│   │   ├── rag/              # RAG system
│   │   │   ├── rag_pipeline.py
│   │   │   ├── hybrid_retrieval.py
│   │   │   ├── query_router.py
│   │   │   └── utils/
│   │   ├── api/              # API endpoints
│   │   ├── auth/             # Authentication
│   │   └── utils/            # Utilities
│   ├── models/               # AI models
│   └── data/                 # Data files
└── frontend/                 # Next.js frontend
    ├── src/
    │   ├── app/              # App router
    │   └── components/       # React components
    └── public/               # Static assets
```

## 🔧 Configuration

### Environment Variables (.env)

The setup wizard will securely prompt for these credentials:

```env
# Database Configuration
DB_NEON_NAME=your_database_name
DB_NEON_USER=your_username
DB_NEON_PASSWORD=your_password
DB_NEON_HOST=your_host
DB_NEON_PORT=5432

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key
```

### Required Models

The setup automatically downloads:
- `mistral-7b-instruct-v0.2.Q4_K_M.gguf` (4.1GB) - Main LLM

## 🎯 Features

### Intelligent Question Answering
- **Hybrid Retrieval**: Combines semantic and keyword search
- **Context-Aware**: Understands university domain
- **Multi-language**: Supports Italian and English
- **Structured Data**: Handles database queries efficiently

### User Interface
- **Modern UI**: Clean, responsive design
- **Real-time Chat**: Interactive question-answering
- **Authentication**: Secure user management
- **Material Management**: Upload and organize documents

### Technical Features
- **FastAPI Backend**: High-performance API
- **Next.js Frontend**: Modern React framework
- **Vector Search**: Semantic document retrieval
- **Database Integration**: Structured data access

## 🛠️ Development

### Adding New Features

1. **Backend**: Add endpoints in `backend/src/api/`
2. **Frontend**: Create components in `frontend/src/components/`
3. **RAG**: Extend retrieval in `backend/src/rag/`

### Testing

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
npm test
```

## 📊 Performance

- **Response Time**: < 3 seconds for most queries
- **Accuracy**: High relevance through hybrid retrieval
- **Scalability**: Cloud-based infrastructure
- **Reliability**: Robust error handling and fallbacks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the API documentation at http://localhost:8000/docs
2. Review the setup logs for configuration issues
3. Ensure all environment variables are properly set

---

**Note**: This is a research project for university environments. The system is designed to handle academic queries and university-related information efficiently. 
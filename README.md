# RAG System with Local LLM

A streamlined Retrieval-Augmented Generation (RAG) system that combines vector search with a local Mistral-7B model for natural language responses.

# ⚠️ IMPORTANT
[Download the model](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF?show_file_info=mistral-7b-instruct-v0.2.Q4_K_M.gguf) first, it should go inside `./models/`

## 🚀 Features

- **Vector Database Integration**: Uses Pinecone for efficient semantic search
- **Local LLM**: Leverages Mistral-7B for response generation
- **Structured Data**: PostgreSQL database with exam, professor, and textbook information
- **Benchmarking**: Built-in performance testing and timing analysis
- **Modular Design**: Easy to extend and modify

## 📁 Project Structure

```
.
├── models/                      # Local LLM model directory
│   └── mistral-7b-instruct-v0.2.Q4_K_M.gguf
├── utils/                      # Utility modules
│   ├── embeddings.py           # Text embedding functionality
│   ├── generate_chunks.py      # Database to text conversion
│   ├── local_llm.py           # Local LLM integration
│   └── vector_db.py           # Pinecone vector database operations
├── rag_core.py                # Core RAG system implementation
├── setup_database.py          # Database setup and population
├── embed_and_index.py        # Embedding generation and vector storage
├── test_rag.py               # Benchmarking and testing
└── requirements.txt          # Project dependencies
```

## 🛠️ Setup

1. **Environment Setup**
   Create a `.env` file with:
   ```bash
   # Database Configuration
   DB_NAME=exams_db
   DB_USER=simple_user
   DB_PASSWORD=secretpwd
   DB_HOST=localhost
   DB_PORT=5432

   # Pinecone Configuration
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_HOST=your_host
   PINECONE_INDEX=your_index
   ```
2. **Create the DB user**
   ```bash
   -- as postgres superuser:
   CREATE DATABASE thesis_db;
   CREATE USER simple_user WITH PASSWORD 'admin';
   GRANT ALL PRIVILEGES ON DATABASE thesis_db TO simple_user;
   GRANT ALL ON SCHEMA public TO simple_user;
   ALTER SCHEMA public OWNER TO simple_user;
   ```
   To login as superuser: `psql -U postgre`.

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Setup**
   ```bash
   python setup_database.py
   ```

4. **Generate Embeddings and Index**
   ```bash
   python embed_and_index.py
   ```
   This step is crucial as it:
   - Converts database records into text chunks
   - Generates embeddings for each chunk
   - Stores vectors in Pinecone for semantic search
   - Must be run before testing the RAG system

## 🚀 Usage

**To run the test UI, run `./run.sh`**

1. **Run Benchmark Tests**
   ```bash
   python test_rag.py
   ```
   This will:
   - Test multiple queries
   - Measure retrieval and generation times
   - Save benchmark results to JSON
   - Display performance metrics

2. **Example Queries**
   - "What exams were given by Professor Smith in 2023?"
   - "Which textbooks were used in the Database Systems course?"
   - "List all exams held in room A101"
   - "What courses were taught by Professor Johnson?"
   - "Show me all exams from 2022 that used Machine Learning textbooks"

## 📊 Database Schema

```sql
-- Textbook table
CREATE TABLE textbook (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    resources TEXT NOT NULL
);

-- Professor table
CREATE TABLE professor (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    lastname VARCHAR(100) NOT NULL,
    room VARCHAR(20) NOT NULL
);

-- Exam table
CREATE TABLE exam (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    professor_id INTEGER NOT NULL,
    textbook_id INTEGER NOT NULL,
    FOREIGN KEY (professor_id) REFERENCES professor(id),
    FOREIGN KEY (textbook_id) REFERENCES textbook(id)
);
```

## 🔧 Configuration

- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Vector Database**: Pinecone with namespace "v2"
- **Local LLM**: Mistral-7B-Instruct (GGUF format)
- **Benchmark Runs**: 3 runs per query by default

## 📈 Performance

The system provides detailed timing information for:
- Vector retrieval time
- LLM generation time
- Total response time

Results are saved in JSON format for analysis.

## 🔄 Workflow

1. Database records are converted to text chunks
2. Chunks are embedded and stored in Pinecone
3. User query is received
4. Query is embedded using sentence transformers
5. Similar documents are retrieved from Pinecone
6. Retrieved context is sent to local LLM
7. LLM generates a natural language response
8. Performance metrics are recorded

## 📝 Notes

- The system uses a local Mistral-7B model for generation
- Vector search is performed using Pinecone
- Database is PostgreSQL with a simple three-table schema
- All timing information is automatically collected and saved
- Embeddings must be generated before running queries

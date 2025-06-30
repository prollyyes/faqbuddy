## Setup rapido
~Nota: per un setup veloce, `./setup.sh` contiene tutti i passi necessari preparare l'avvio dell'applicazione.
Se ci sono problemi di permessi, basta garantire permessi di esecuzione al file: `chmod +x setup.sh`~


## Quick Launch (Recommended)

For the fastest setup, use the unified launch script:

```bash
python launch_faqbuddy.py
```

This script will:
- Detect your database configuration (Neon or Docker)
- Set up the database if needed
- Start both backend and frontend servers
- Provide a unified interface

## Database Setup Options

### Option 1: Neon Database (Cloud - Recommended)
```bash
python setup_neon_database.py
```

**Required environment variables:**
```env
DB_NEON_NAME=your_neon_database_name
DB_NEON_USER=your_neon_username
DB_NEON_PASSWORD=your_neon_password
DB_NEON_HOST=your_neon_host
DB_NEON_PORT=5432
PINECONE_API_KEY=your_pinecone_api_key
```

**Note:** This script connects to an existing Neon database that is already functional and populated. It only configures your local environment to connect to it.

**Optional:** To update the Pinecone vector database with fresh data:
```bash
python setup_neon_database.py --update-vec-db
```

### Option 2: Docker Database (Local)
```bash
python setup_docker_database.py
```

**Required environment variables:**
```env
PINECONE_API_KEY=your_pinecone_api_key
```

**Note:** The setup script will ask if you want to update Pinecone. It's recommended to skip this unless you've made significant database changes.

## Updating Pinecone Vector Database

When you update your Neon database with new data, you'll want to refresh the Pinecone vector database to ensure your RAG system has the latest information.

### Quick Update (Recommended)
```bash
python update_pinecone_db.py
```

This script will:
- Connect to your Neon database
- Generate fresh chunks from all tables
- Clear the existing 'db' namespace in Pinecone
- Upload the new vectors with embeddings
- Verify the upload

### Test Chunk Generation First
Before running the full update, you can test that chunk generation works correctly:

```bash
python test_chunk_generation.py
```

This will show you:
- How many chunks are generated from each table
- Sample chunks to verify the content
- Any connection or query errors

### Manual Update (Advanced)
If you need more control, you can run the update script directly:

```bash
cd backend/src/rag
python update_pinecone_from_neon.py
```

### What Gets Updated
The update process includes chunks from all major tables:
- **Academic Structure**: Departments, Faculties, Degree Courses, Courses
- **Teaching**: Course Editions, Teachers (both registered and unregistered)
- **Students**: Student records, Course enrollments
- **Materials**: Educational materials, Reviews, Ratings
- **Platforms**: Course platforms and codes
- **Theses**: Thesis information

### Environment Variables Required
Make sure your `.env` file contains:
```env
PINECONE_API_KEY=your_pinecone_api_key
DB_NAME=your_neon_db_name
DB_USER=your_neon_username
DB_PASSWORD=your_neon_password
DB_HOST=your_neon_host
DB_PORT=5432
```

## Manual Setup (Legacy)

### 1. Crea e attiva l'ambiente virtuale

```sh
python3.9 -m venv venv
source venv/bin/activate
cd backend
pip install -r src/requirements.txt
```

---

### 2. Scarica i modelli LLM

Crea la cartella per i modelli:

```sh
mkdir models
```

Scarica e inserisci i file `.gguf` nella cartella `models`:

- [Gemma 3:4B (italiano)](https://huggingface.co/unsloth/gemma-3-4b-it-GGUF?show_file_info=gemma-3-4b-it-Q4_1.gguf)
- [Mistral 7B Instruct](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF?show_file_info=mistral-7b-instruct-v0.2.Q4_K_M.gguf)

---

### 3. Configura le variabili d'ambiente

Crea un file `.env` nella root del progetto con questo contenuto:

```env
PINECONE_API_KEY=pcsk_6FLreq_PQ9dENviDRu7WwTHg5BF27PWBmFoVMPqJNzrJcNQSWywSns973idr5vqgTixqF2
PINECONE_HOST=exams-index-y83qnfa.svc.aped-4627-b74a.pinecone.io
PINECONE_INDEX=exams-index
DB_USER=db_user
DB_PASSWORD=pwd
DB_NAME=faqbuddy_db
DB_HOST=localhost
DB_PORT=5433
```

### 4. imposta il `PYTHONPATH` per puntare a `backend/src` se necessario.
```sh
cd backend/src
export PYTHONPATH=$(pwd)
```
Io sinceramente preferisco inserirlo direttamente dentro `~/.zshrc`, ma fate voi

---

### 5. Setup del database

Consulta la cartella `/db` e leggi il relativo `README.md` per le istruzioni su come creare e popolare il database.

---

### 6. Prepara i modelli ML e RAG

```sh
cd backend/src
python switcher/create_MLmodel.py
python rag/embed_and_index.py
```

---

### 7. Esegui i test

```sh
cd ..
python tests/test_ml.py
python -m pytest -s tests/test_pipeline.py
python src/rag/test_rag.py
```

---

### 8. Avvia il backend e la UI

**Backend (FastAPI):**
```sh
cd backend/src
uvicorn main:app --reload
```

**Frontend (Next.js):**
```sh
cd frontend
npm install
npm run dev
```

## 🎯 Launch Options Summary

| Method | Command | Description |
|--------|---------|-------------|
| **Unified Launch** | `python launch_faqbuddy.py` | Automatic setup and launch |
| **Neon Setup** | `python setup_neon_database.py` | Cloud database setup |
| **Docker Setup** | `python setup_docker_database.py` | Local database setup |
| **Manual Launch** | `uvicorn src.main:app --reload` | Manual backend launch |

### Dev test sul RAG

Per testare solo le funzionalita' del RAG, potete eseguire il file `interactive_test.py`, trovato in `/backend/src/rag/`.
Il resto delle operazioni deve essere fatto, e' semplicemente un basico modo per interagire da CL con il modello e testare velocemente le funzionalita'.

---

## Esempi di domande complex gestite dal RAG

Queste domande richiedono ragionamento, spiegazioni o informazioni non strutturate e **non possono essere risolte con una semplice query SQL**:

- **Come posso pianificare il mio percorso di studi per laurearmi nei tempi previsti?**
- **Quali strategie posso adottare per migliorare la mia media degli esami universitari?**
- **Cosa succede se non supero un esame obbligatorio entro la scadenza prevista dal regolamento?**
- **Quali sono i vantaggi e le opportunità offerte da un curriculum internazionale?**
- **Come posso conciliare efficacemente lavoro e studio durante il mio percorso universitario?**
- **Quali sono le procedure dettagliate per ottenere il riconoscimento di esami sostenuti all'estero?**
- **Quali passi devo seguire se desidero cambiare corso di laurea?**
- **Come posso evitare sovrapposizioni tra esami obbligatori nel mio piano di studi?**
- **Quali documenti sono necessari per presentare la domanda di laurea e dove posso reperirli?**
- **Quali risorse online o materiali sono consigliati per prepararsi al meglio agli esami di informatica?**

---

Buon divertimento con FAQBuddy!

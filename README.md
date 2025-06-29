## Setup rapido

**Per un setup piu' rapido possibile, esegui ./setup.sh dalla root**

### 1. Crea e attiva l’ambiente virtuale

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

### 3. Configura le variabili d’ambiente

### just foR PRODUCTION, IN RELEASE LEVIAMO TUTTO SENNO è LA FINE, sto pushando anche il .env.local ma quello andrà nel gitignore
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

DB_NEON_NAME=neondb
DB_NEON_USER=neondb_owner
DB_NEON_PASSWORD=npg_81IXpKWZQxEa
DB_NEON_HOST=ep-super-credit-a9zsuu7x-pooler.gwc.azure.neon.tech
DB_NEON_PORT=5432

EMAIL_FROM=tutordimatematica.ing@gmail.com
EMAIL_PASS=ohxrysinakqpryrb
EMAIL_USER=tutordimatematica.ing@gmail.com
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

### 7. Esegui i test, o con python o con pytest

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
uvicorn api.API:app --reload
```

**Frontend (Next.js):**
```sh
cd frontend
npm i
npm run dev
```

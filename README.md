## Setup rapido

### 1. Crea e attiva l’ambiente virtuale

```sh
python3.9 -m venv venv
source venv/bin/activate
cd backend
pip install -r requirements.txt
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

> **Nota:** imposta il `PYTHONPATH` per puntare a `backend/src` se necessario.

---

### 4. Setup del database

Consulta la cartella `/db` e leggi il relativo `README.md` per le istruzioni su come creare e popolare il database.

---

### 5. Prepara i modelli ML e RAG

```sh
cd backend/src
python create_MLmodel.py
python rag/embed_and_index.py
```

---

### 6. Esegui i test

```sh
cd ..
python tests/test_ml.py
python tests/test_pipeline.py
python src/rag/test_rag.py
```

---

### 7. Avvia il backend e la UI

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

---

## 💡 Esempi di domande complex gestite dal RAG

Queste domande richiedono ragionamento, spiegazioni o informazioni non strutturate e **non possono essere risolte con una semplice query SQL**:

- **Come posso pianificare il mio percorso di studi per laurearmi nei tempi previsti?**
- **Quali strategie posso adottare per migliorare la mia media degli esami universitari?**
- **Cosa succede se non supero un esame obbligatorio entro la scadenza prevista dal regolamento?**
- **Quali sono i vantaggi e le opportunità offerte da un curriculum internazionale?**
- **Come posso conciliare efficacemente lavoro e studio durante il mio percorso universitario?**
- **Quali sono le procedure dettagliate per ottenere il riconoscimento di esami sostenuti all’estero?**
- **Quali passi devo seguire se desidero cambiare corso di laurea?**
- **Come posso evitare sovrapposizioni tra esami obbligatori nel mio piano di studi?**
- **Quali documenti sono necessari per presentare la domanda di laurea e dove posso reperirli?**
- **Quali risorse online o materiali sono consigliati per prepararsi al meglio agli esami di informatica?**

---

Buon divertimento con FAQBuddy!
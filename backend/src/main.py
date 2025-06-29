from fastapi import FastAPI, Query
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.text_2_SQL.converter import TextToSQLConverter
from src.switcher.MLmodel import MLModel
from src.utils.db_utils import get_connection, MODE
from src.utils.db_handler import DBHandler
from src.rag.rag_adapter import RAGSystem
from src.api.AuthAPI import router as auth_router
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth routes
app.include_router(auth_router)

class T2SQLRequest(BaseModel):
    question: str

# Inizializza modello ML
ml_model = MLModel()

# Inizializza converter Text-to-SQL
converter = TextToSQLConverter()

# Inizializza RAG
rag = RAGSystem()


@app.post("/t2sql")
def t2sql_endpoint(req: T2SQLRequest):
    question = req.question

    # Inizializza DBHandler
    db = DBHandler(get_connection(mode=MODE))
    schema = db.get_schema()

    # 1. Switcher ML
    ml_pred, proba = ml_model.inference(question)

    # 2. Fallback LLM se confidenza bassa
    threshold = 0.7
    fallback = False
    if proba < threshold:
        final_pred = "complex"
        final_pred = "complex"
        fallback = True
    
    else:
        final_pred = ml_pred.strip().lower()

    # 3. Routing finale
    if final_pred == "simple":
        # se entro 2 tentativi non riesco a generare una query SQL valida, faccio il fallback a RAG
        max_attempts = 2
        attempt = 0
        while attempt < max_attempts:
            prompt = converter.create_prompt(question, schema)
            raw_response = converter.query_llm(prompt)
            sql_query = converter.clean_sql_response(raw_response)
            print(f"SQL Query: {sql_query}")
            if not converter.is_sql_safe(sql_query) or sql_query == "INVALID_QUERY":
                print(f"Attempt {attempt+1}: Invalid SQL query, retrying...")
                attempt += 1
                continue
            try:
                rows, columns = db.run_query(sql_query, fetch=True, columns=True)
                result = [dict(zip(columns, row)) for row in rows]
                if result:
                    natural_response = converter.from_sql_to_text(question, result)
                    db.close_connection()
                    print("T2SQL")
                    return {
                        "result": result,
                        "query": sql_query,
                        "natural_response": natural_response,
                        "chosen": "T2SQL",
                        "ml_model": ml_pred,
                        "ml_confidence": proba
                    }
                else:
                    print(f"Attempt {attempt+1}: Query returned no results, retrying...")
                    attempt += 1
            except Exception as e:
                db.connection_rollback()
                print(f"Attempt {attempt+1}: Error executing SQL query, retrying... {e}")
                attempt += 1

        # Dopo 2 tentativi falliti, fallback RAG
        print("Fallback to RAG after 2 failed attempts.")
        rag_result = rag.generate_response(question)
        db.close_connection()
        return {
            "result": rag_result["response"],
            "chosen": "RAG",
            "ml_model": ml_pred,
            "ml_confidence": proba,
            "fallback_gemma": fallback,
            "llm_pred": final_pred if fallback else "",
            "retrieval_time": rag_result["retrieval_time"],
            "generation_time": rag_result["generation_time"],
            "total_time": rag_result["total_time"],
            "context_used": rag_result["context_used"]
        }
    else:
        print("falling back to RAG for complex question prediction.")
        rag_result = rag.generate_response(question)
        db.close_connection()
        return {
            "result": rag_result["response"],
            "chosen": "RAG",
            "ml_model": ml_pred,
            "ml_confidence": proba,
            "fallback_gemma": fallback,
            "llm_pred": final_pred if fallback else "",
            "retrieval_time": rag_result["retrieval_time"],
            "generation_time": rag_result["generation_time"],
            "total_time": rag_result["total_time"],
            "context_used": rag_result["context_used"]
        }


######################################################################################################
# Non sono troppo convinto di questo approccio, fatemi sapere guys
TEMPLATES = [
    "Mostra tutti i corsi del primo semestre",
    "Elenca tutti i corsi di {corso_laurea}",
    "Chi è il docente di {nome_corso}?",
    "Mostra i materiali didattici per il corso {nome_corso}",
    "Quali sono gli orari di ricevimento dei professori?",
    "Quali corsi prevedono la frequenza obbligatoria?",
    "Mostra tutte le informazioni sul corso {nome_corso}",
    "Elenca i professori che ricevono il {giorno_settimana}",
    "Quali sono le tesi disponibili nel dipartimento di {nome_dipartimento}?",
    "Mostra tutti i corsi tenuti dal professor {nome_professore}",
    "Elenca gli studenti iscritti al corso di laurea in {corso_laurea}",
    "Elenca i corsi che utilizzano la piattaforma {nome_piattaforma}",
]

def expand_templates(templates, db):
    # Ottieni i valori dinamici dal DB
    corsi_laurea = [row[0] for row in db.run_query("SELECT nome FROM Corso_di_Laurea", fetch=True)]
    nomi_corso = [row[0] for row in db.run_query("SELECT nome FROM Corso", fetch=True)]
    nomi_prof = [row[0] for row in db.run_query("SELECT nome FROM Utente WHERE id IN (SELECT id FROM Insegnanti)", fetch=True)]
    piattaforme = [row[0] for row in db.run_query("SELECT Nome FROM Piattaforme", fetch=True)]
    dipartimenti = [row[0] for row in db.run_query("SELECT nome FROM Dipartimento", fetch=True)]
    giorni = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì"]

    expanded = []
    for t in templates:
        if "{corso_laurea}" in t:
            expanded += [t.replace("{corso_laurea}", cl) for cl in corsi_laurea]
        elif "{nome_corso}" in t:
            expanded += [t.replace("{nome_corso}", nc) for nc in nomi_corso]
        elif "{nome_professore}" in t:
            expanded += [t.replace("{nome_professore}", np) for np in nomi_prof]
        elif "{nome_piattaforma}" in t:
            expanded += [t.replace("{nome_piattaforma}", p) for p in piattaforme]
        elif "{nome_dipartimento}" in t:
            expanded += [t.replace("{nome_dipartimento}", d) for d in dipartimenti]
        elif "{giorno_settimana}" in t:
            expanded += [t.replace("{giorno_settimana}", g) for g in giorni]
        else:
            expanded.append(t)
    return expanded

@app.get("/autocomplete")
def autocomplete_suggestions(q: str = Query(..., min_length=1)):
    db = DBHandler(get_connection(mode=MODE))
    templates_expanded = expand_templates(TEMPLATES, db)
    db.close_connection()
    q_lower = q.lower()
    suggestions = [t for t in templates_expanded if t.lower().startswith(q_lower) or q_lower in t.lower()]
    return {"suggestions": suggestions[:5]}
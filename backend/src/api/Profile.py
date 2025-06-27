from fastapi import APIRouter, Depends, HTTPException, status, Request
from src.api.BaseModel import (
    UserProfileResponse, UserProfileUpdate, 
    CourseInfo, StatsResponse, ExamInsertRequest
)
from typing import List
from src.utils.db_utils import get_connection, MODE
from src.utils.db_handler import DBHandler
from src.auth.jwt_handler import decode_access_token
from src.api.utils import *
from src.api.drive_utils import *

router = APIRouter()

# Inizializza db_handler
conn = get_connection(mode=MODE)
db_handler = DBHandler(conn)

# Funzione per ottenere l'utente corrente dal JWT
def get_current_user(request: Request):
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token mancante")
    token = auth_header.split(" ")[1]
    try:
        payload = decode_access_token(token)
        return {"user_id": payload["user_id"]}
    except Exception:
        raise HTTPException(status_code=401, detail="Token non valido")

# --- Endpoint: Ottieni info profilo utente ---
@router.get("/profile/me", response_model=UserProfileResponse)
def get_profile(current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]

    query = """
        SELECT 
            u.nome, u.cognome, u.email,
            s.matricola, cdl.nome as corso_laurea,
            i.infoMail, i.sitoWeb, i.cv, i.ricevimento,
            CASE 
                WHEN s.id IS NOT NULL THEN 'studente'
                WHEN i.id IS NOT NULL THEN 'insegnante'
                ELSE NULL
            END as ruolo
        FROM Utente u
        LEFT JOIN Studenti s ON u.id = s.id
        LEFT JOIN Corso_di_Laurea cdl ON s.corso_laurea_id = cdl.id
        LEFT JOIN Insegnanti i ON u.id = i.id
        WHERE u.id = %s
    """
    result = db_handler.run_query(query, params=(user_id,), fetch=True)
    if not result:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    (
        nome, cognome, email,
        matricola, corso_laurea,
        infoMail, sitoWeb, cv, ricevimento,
        ruolo
    ) = result[0]

    rating = None
    livello = None
    percentuale = None

    return UserProfileResponse(
        nome=nome,
        cognome=cognome,
        email=email,
        matricola=matricola,
        corso_laurea=corso_laurea,
        infoMail=infoMail,
        sitoWeb=sitoWeb,
        cv=cv,
        ricevimento=ricevimento,
        ruolo=ruolo,
        rating=rating,
        livello=livello,
        percentuale=percentuale
    )

# # --- Endpoint: Modifica info profilo utente ---
@router.put("/profile/me", response_model=UserProfileResponse)
def update_profile(data: UserProfileUpdate, current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]

    # Aggiorna Utente
    db_handler.execute_sql_insertion(
        "UPDATE Utente SET nome=%s, cognome=%s, email=%s WHERE id=%s",
        (data.nome, data.cognome, data.email, user_id)
    )

    # Aggiorna Studente
    if data.ruolo == "studente":
        db_handler.execute_sql_insertion(
            "UPDATE Studenti SET matricola=%s WHERE id=%s",
            (data.matricola, user_id)
        )
    # Aggiorna Insegnante
    elif data.ruolo == "insegnante":
        db_handler.execute_sql_insertion(
            "UPDATE Insegnanti SET infoMail=%s, sitoWeb=%s, ricevimento=%s, cv=%s WHERE id=%s",
            (data.infoMail, data.sitoWeb, data.ricevimento, data.cv, user_id)
        )

    # Ritorna il nuovo profilo aggiornato
    return get_profile(current_user)

# Endpoint riutilizzabile per l'eliminazione di file
@router.delete("/files/delete/{file_id}")
def delete_file(file_id: str):
    try:
        delete_drive_file(file_id)
        return {"detail": "CV eliminato"}
    except Exception as e:
        print("Errore eliminazione CV:", e)  # <--- AGGIUNGI QUESTO
        raise HTTPException(status_code=500, detail=str(e))


# # --- Endpoint: Corsi frequentati ---
# @router.get("/profile/courses/current", response_model=List[CourseInfo])
# def get_current_courses(current_user=Depends(...)):
#     # Da implementare: restituisci corsi attivi
#     pass

# # --- Endpoint: Corsi completati ---
# @router.get("/profile/courses/completed", response_model=List[CourseInfo])
# def get_completed_courses(current_user=Depends(...)):
#     # Da implementare: restituisci corsi completati
#     pass

# # --- Endpoint: Statistiche ---
# @router.get("/profile/stats", response_model=StatsResponse)
# def get_stats(current_user=Depends(...)):
#     # Da implementare: restituisci statistiche utente
#     pass

# # --- Endpoint: Aggiungi esame ---
# @router.post("/profile/exams")
# def add_exam(data: ExamInsertRequest, current_user=Depends(...)):
#     # Da implementare: inserisci nuovo esame sostenuto
#     pass
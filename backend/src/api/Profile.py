from fastapi import APIRouter, Depends, HTTPException, status, Request
from src.api.BaseModel import *
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








# --- Endpoint: Corsi Disponibili per un determinato studente ---
@router.get("/courses/available", response_model=List[CourseBase])
def get_available_courses(current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]
    # Recupera il corso di laurea dello studente
    query_cdl = "SELECT corso_laurea_id FROM Studenti WHERE id = %s"
    result = db_handler.run_query(query_cdl, params=(user_id,), fetch=True)
    if not result:
        raise HTTPException(status_code=404, detail="Studente non trovato")
    corso_laurea_id = result[0][0]
    # Filtra i corsi per corso di laurea, escludendo quelli già seguiti o completati
    query = """
        SELECT id, nome, cfu
        FROM Corso
        WHERE id_corso = %s
        AND id NOT IN (
            SELECT c.id
            FROM Corsi_seguiti cs
            JOIN EdizioneCorso e ON cs.edition_id = e.id
            JOIN Corso c ON e.id = c.id
            WHERE cs.student_id = %s
        )
    """
    results = db_handler.run_query(query, params=(corso_laurea_id, user_id), fetch=True)
    return [CourseBase(id=row[0], nome=row[1], cfu=row[2]) for row in results]


# --- Endpoint: EdizioneCorsi Disponibili per un determinato corso ---
@router.get("/courses/{corso_id}/editions", response_model=List[CourseEditionResponse])
def get_editions_for_course(corso_id: uuid.UUID):
    query = """
        SELECT e.id, e.data, u.nome as docente
        FROM EdizioneCorso e
        JOIN Insegnanti i ON e.insegnante = i.id
        JOIN Utente u ON i.id = u.id
        WHERE e.id = %s
    """
    results = db_handler.run_query(query, params=(str(corso_id),), fetch=True)
    return [
        CourseEditionResponse(id=row[0], data=row[1], docente=row[2])
        for row in results
    ]


# --- Endpoint: Corsi frequentati dallo studente che è loggato---
@router.get("/profile/courses/current", response_model=list[CourseResponse])
def get_current_courses(current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]
    query = """
        SELECT c.id, c.nome, c.cfu, u.nome as docente_nome, u.cognome as docente_cognome, e.id as edition_id, e.data as edition_data, cs.stato
        FROM Corsi_seguiti cs
        JOIN EdizioneCorso e ON cs.edition_id = e.id AND cs.edition_data = e.data
        JOIN Corso c ON e.id = c.id
        LEFT JOIN Insegnanti i ON e.insegnante = i.id
        LEFT JOIN Utente u ON i.id = u.id
        WHERE cs.student_id = %s
    """
    results = db_handler.run_query(query, params=(user_id,), fetch=True)
    return [
        CourseResponse(
            id=row[0],
            nome=row[1],
            cfu=row[2],
            docente_nome=row[3],
            docente_cognome=row[4],
            edition_id=row[5],
            edition_data=row[6],
            stato=row[7],
        )
        for row in results
    ]

# --- Endpoint: Corsi completati dallo studente che è loggato---
@router.get("/profile/courses/completed", response_model=list[CourseResponse])
def get_completed_courses(current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]
    query = """
        SELECT c.id, c.nome, c.cfu, u.nome as docente_nome, u.cognome as docente_cognome, e.id as edition_id, e.data as edition_data, cs.stato, cs.voto
        FROM Corsi_seguiti cs
        JOIN EdizioneCorso e ON cs.edition_id = e.id AND cs.edition_data = e.data
        JOIN Corso c ON e.id = c.id
        LEFT JOIN Insegnanti i ON e.insegnante = i.id
        LEFT JOIN Utente u ON i.id = u.id
        WHERE cs.student_id = %s AND cs.stato = 'completato'
    """
    results = db_handler.run_query(query, params=(user_id,), fetch=True)
    return [
        CourseResponse(
            id=row[0],
            nome=row[1],
            cfu=row[2],
            docente_nome=row[3],
            docente_cognome=row[4],
            edition_id=row[5],
            edition_data=row[6],
            stato=row[7],
            voto=row[8]
        )
        for row in results
    ]

# --- Endpoint: per completare un edizione del corso allo studente che è loggato ---
@router.put("/profile/courses/{edition_id}/complete")
def complete_course(
    edition_id: str,
    data: CompleteCourseRequest,
    current_user=Depends(get_current_user)
):
    user_id = current_user["user_id"]
    query = """
        UPDATE Corsi_seguiti
        SET stato = 'completato', voto = %s
        WHERE student_id = %s AND edition_id = %s AND edition_data = %s
    """
    db_handler.run_query(query, params=(data.voto, user_id, edition_id, data.edition_data))
    return {"detail": "Corso completato"}
    
    

# --- Endpoint: per iscrivere uno studente ad una determinata EdizioneCorso ---
@router.post("/courses/{corso_id}/editions/{edition_id}/enroll")
def enroll_in_edition(
    corso_id: str,
    edition_id: str,
    stato: str = "attivo",
    current_user=Depends(get_current_user)
):
    user_id = current_user["user_id"]
    # Recupera la data dell'edizione
    data_query = "SELECT data FROM EdizioneCorso WHERE id = %s"
    data_result = db_handler.run_query(data_query, params=(edition_id,), fetch=True)
    if not data_result:
        raise HTTPException(status_code=404, detail="Edizione non trovata")
    edition_data = data_result[0][0]
    # Iscrivi lo studente
    query = """
        INSERT INTO Corsi_seguiti (student_id, edition_id, edition_data, stato)
        VALUES (%s, %s, %s, %s)
    """
    db_handler.run_query(query, params=(user_id, edition_id, edition_data, stato))
    return {"detail": "Iscritto all'edizione"}



# --- Endpoint: per trovare l'id Insegnanti a partire dal Nome e Cognome ---
# Non serve più, la lascio qui magari in futuro può servire
# @router.get("/teachers/search")
# def search_teacher(nome: str, cognome: str):
#     query = """
#         SELECT i.id, u.nome, u.cognome
#         FROM Insegnanti i
#         JOIN Utente u ON i.id = u.id
#         WHERE LOWER(u.nome) = LOWER(%s) AND LOWER(u.cognome) = LOWER(%s)
#         LIMIT 1
#     """
#     result = db_handler.run_query(query, params=(nome, cognome), fetch=True)
#     if not result:
#         raise HTTPException(status_code=404, detail="Insegnante non trovato")
#     return {"id": result[0][0], "nome": result[0][1], "cognome": result[0][2]}


# --- Endpoint: per ottenere tutti gli insegnanti ---
@router.get("/teachers")
def get_teachers():
    query = """
        SELECT i.id, u.nome, u.cognome
        FROM Insegnanti i
        JOIN Utente u ON i.id = u.id
    """
    results = db_handler.run_query(query, fetch=True)
    return [{"id": row[0], "nome": row[1], "cognome": row[2]} for row in results]



# --- Endpoint: Aggiungi edizioneCorso e iscrivi studente a quell'EdizioneCorso ---
@router.post("/courses/{corso_id}/editions/add")
def add_edizione_and_enroll(
    corso_id: str,
    edizione: EdizioneCorsoCreate,
    current_user=Depends(get_current_user)
):
    # 1. Crea la nuova EdizioneCorso
    query = """
        INSERT INTO EdizioneCorso (id, insegnante, data, orario, esonero, mod_Esame)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    db_handler.run_query(query, params=(
        corso_id,
        edizione.insegnante,
        edizione.data,
        edizione.orario,
        edizione.esonero,
        edizione.mod_Esame
    ))

    # 2. Iscrivi lo studente a questa edizione con lo stato scelto
    user_id = current_user["user_id"]
    query2 = """
        INSERT INTO Corsi_seguiti (student_id, edition_id, edition_data, stato)
        VALUES (%s, %s, %s, %s)
    """
    db_handler.run_query(query2, params=(user_id, corso_id, edizione.data, edizione.stato))

    return {"detail": "EdizioneCorso creata e studente iscritto"}










# --- Endpoint: Recensioni dello studente ---
@router.get("/profile/reviews", response_model=list[ReviewResponse])
def get_student_reviews(current_user=Depends(get_current_user)):
    user_id = current_user["user_id"]
    query = """
        SELECT id, student_id, edition_id, edition_data, descrizione, voto
        FROM Review
        WHERE student_id = %s
    """
    results = db_handler.run_query(query, params=(user_id,), fetch=True)
    return [
        ReviewResponse(
            id=row[0],
            student_id=row[1],
            edition_id=row[2],
            edition_data=row[3],
            descrizione=row[4],
            voto=row[5]
        )
        for row in results
    ]

# --- Endpoint: Aggiungi recensione ---
@router.post("/profile/reviews", response_model=ReviewResponse)
def add_review(
    data: ReviewCreate,
    current_user=Depends(get_current_user)
):
    user_id = current_user["user_id"]
    # Verifica se già esiste una recensione per questa edizione
    query = """
        SELECT id FROM Review
        WHERE student_id = %s AND edition_id = %s AND edition_data = %s
    """
    exists = db_handler.run_query(query, params=(user_id, str(data.edition_id), data.edition_data), fetch=True)
    if exists:
        raise HTTPException(status_code=400, detail="Recensione già presente per questo corso")
    # Inserisci la recensione
    insert_query = """
        INSERT INTO Review (student_id, edition_id, edition_data, descrizione, voto)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """
    new_id = db_handler.run_query(
        insert_query,
        params=(user_id, str(data.edition_id), data.edition_data, data.descrizione, data.voto),
        fetch=True
    )[0][0]
    return ReviewResponse(
        id=new_id,
        student_id=user_id,
        edition_id=data.edition_id,
        edition_data=data.edition_data,
        descrizione=data.descrizione,
        voto=data.voto
    )

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
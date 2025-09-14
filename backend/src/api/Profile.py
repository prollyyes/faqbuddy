from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from .BaseModel import *
from typing import List
from ..utils.db_utils import get_connection, MODE
from ..utils.db_handler import DBHandler
from ..auth.jwt_handler import decode_access_token
from .utils import *
from .drive_utils import *

router = APIRouter()

# Database connection dependency for Render
def get_db_handler():
    conn = get_connection(mode=MODE)
    db_handler = DBHandler(conn)
    try:
        yield db_handler
    finally:
        db_handler.close_connection()

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

# --- Endpoint: Ottieni tutti i corsi ---
@router.get("/courses/all")
def get_all_courses(db_handler: DBHandler = Depends(get_db_handler)):
    query = "SELECT id, nome FROM Corso ORDER BY nome"
    results = db_handler.run_query(query, fetch=True)
    return [{"id": row[0], "nome": row[1]} for row in results]


# --- Endpoint: Ottieni info profilo utente ---
@router.get("/profile/me", response_model=UserProfileResponse)
def get_profile(current_user=Depends(get_current_user), db_handler: DBHandler = Depends(get_db_handler)):
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
        LEFT JOIN Insegnanti_Registrati i ON u.id = i.id
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
def update_profile(data: UserProfileUpdate, current_user=Depends(get_current_user), db_handler: DBHandler = Depends(get_db_handler)):
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
            "UPDATE Insegnanti_Registrati SET infoMail=%s, sitoWeb=%s, ricevimento=%s, cv=%s WHERE id=%s",
            (data.infoMail, data.sitoWeb, data.ricevimento, data.cv, user_id)
        )

    # Ritorna il nuovo profilo aggiornato
    return get_profile(current_user, db_handler)


@router.post("/profile/change-password")
def change_password(
    data: dict,
    current_user=Depends(get_current_user),
    db_handler: DBHandler = Depends(get_db_handler)
):
    from passlib.hash import bcrypt
    user_id = current_user["user_id"]
    old_password = data.get("old_password")
    new_password = data.get("new_password")
    if not old_password or not new_password:
        raise HTTPException(status_code=400, detail="Dati mancanti")

    # Recupera la password attuale hashata
    query = "SELECT pwd_hash FROM Utente WHERE id = %s"
    result = db_handler.run_query(query, params=(user_id,), fetch=True)
    if not result:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    hashed = result[0][0]

    # Verifica la vecchia password
    if not bcrypt.verify(old_password, hashed):
        raise HTTPException(status_code=401, detail="Vecchia password errata")

    # Aggiorna la password
    new_hashed = bcrypt.hash(new_password)
    db_handler.execute_sql_insertion(
        "UPDATE Utente SET pwd_hash = %s WHERE id = %s",
        (new_hashed, user_id)
    )
    return {"detail": "Password aggiornata"}

# Endpoint riutilizzabile per l'eliminazione di file
@router.delete("/files/delete/{file_id}")
def delete_file(file_id: str, db_handler: DBHandler = Depends(get_db_handler)):
    try:
        delete_drive_file(file_id)
        return {"detail": "CV eliminato"}
    except Exception as e:
        print("Errore eliminazione CV:", e)  # <--- AGGIUNGI QUESTO
        raise HTTPException(status_code=500, detail=str(e))




#### SEZIONE CORSI STUDENTE ####


# --- Endpoint: Corsi Disponibili per un determinato studente ---
@router.get("/courses/available", response_model=List[CourseBase])
def get_available_courses(current_user=Depends(get_current_user), db_handler: DBHandler = Depends(get_db_handler)):
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
def get_editions_for_course(corso_id: uuid.UUID, db_handler: DBHandler = Depends(get_db_handler)):
    query = """
        SELECT e.id, e.data, ia.nome, ia.cognome
        FROM EdizioneCorso e
        JOIN Insegnanti_Anagrafici ia ON e.insegnante_anagrafico = ia.id
        WHERE e.id = %s
          AND e.stato = 'attivo'
        ORDER BY e.data DESC
    """
    results = db_handler.run_query(query, params=(str(corso_id),), fetch=True)
    return [
        CourseEditionResponse(
            id=row[0],
            data=row[1],
            docente=f"{row[2]} {row[3]}".strip()
        )
        for row in results
    ]


# --- Endpoint: Dettagli di un EdizioneCorso specifico per uno studente ---
@router.get("/courses/editions/{edition_id}/{edition_data:path}")
def get_edition_detail(edition_id: str, edition_data: str, current_user=Depends(get_current_user), db_handler: DBHandler = Depends(get_db_handler)):
    user_id = current_user["user_id"]
    query = """
        SELECT e.id, e.data, e.orario, e.esonero, e.mod_Esame, cs.stato, c.nome, c.cfu,
               ia.nome as docente_nome, ia.cognome as docente_cognome, cs.voto
        FROM EdizioneCorso e
        JOIN Corso c ON e.id = c.id
        LEFT JOIN Insegnanti_Anagrafici ia ON e.insegnante_anagrafico = ia.id
        LEFT JOIN Corsi_seguiti cs ON cs.edition_id = e.id AND cs.edition_data = e.data AND cs.student_id = %s
        WHERE e.id = %s AND e.data = %s
    """
    result = db_handler.run_query(query, params=(user_id, edition_id, edition_data), fetch=True)
    if not result:
        raise HTTPException(status_code=404, detail="Edizione non trovata")
    row = result[0]
    return {
        "edition_id": row[0],
        "edition_data": row[1],
        "orario": row[2],
        "esonero": row[3],
        "mod_Esame": row[4],
        "stato": row[5],
        "nome": row[6],
        "cfu": row[7],
        "docente_nome": row[8],
        "docente_cognome": row[9],
        "voto": row[10],  # può essere None se non ancora assegnato
    }


# --- Endpoint: Corsi seguiti dallo studente che è loggato ---
@router.get("/profile/courses/current", response_model=list[CourseResponse])
def get_current_courses(current_user=Depends(get_current_user), db_handler: DBHandler = Depends(get_db_handler)):
    user_id = current_user["user_id"]
    query = """
        SELECT c.id, c.nome, c.cfu, ia.nome as docente_nome, ia.cognome as docente_cognome, 
               e.id as edition_id, e.data as edition_data, cs.stato
        FROM Corsi_seguiti cs
        JOIN EdizioneCorso e ON cs.edition_id = e.id AND cs.edition_data = e.data
        JOIN Corso c ON e.id = c.id
        LEFT JOIN Insegnanti_Anagrafici ia ON e.insegnante_anagrafico = ia.id
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
def get_completed_courses(current_user=Depends(get_current_user), db_handler: DBHandler = Depends(get_db_handler)):
    user_id = current_user["user_id"]
    query = """
        SELECT c.id, c.nome, c.cfu, ia.nome as docente_nome, ia.cognome as docente_cognome, 
               e.id as edition_id, e.data as edition_data, cs.stato, cs.voto
        FROM Corsi_seguiti cs
        JOIN EdizioneCorso e ON cs.edition_id = e.id AND cs.edition_data = e.data
        JOIN Corso c ON e.id = c.id
        LEFT JOIN Insegnanti_Anagrafici ia ON e.insegnante_anagrafico = ia.id
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
    
# --- Endpoint: per rimuovere un edizione del corso allo studente che è loggato ---
@router.delete("/courses/editions/{edition_id}/unenroll")
def unenroll_from_edition(
    edition_id: str,
    data: UnenrollRequest,
    current_user=Depends(get_current_user),
    db_handler: DBHandler = Depends(get_db_handler)
):
    user_id = current_user["user_id"]
    edition_data = data.edition_data
    delete_query = """
        DELETE FROM Corsi_seguiti
        WHERE student_id = %s AND edition_id = %s AND edition_data = %s
    """
    db_handler.run_query(delete_query, params=(user_id, edition_id, edition_data), fetch=False)
    return {"detail": "Disiscrizione avvenuta con successo"}


# --- Endpoint: per completare un edizione del corso allo studente che è loggato ---
@router.put("/profile/courses/{edition_id}/complete")
def complete_course(
    edition_id: str,
    data: CompleteCourseRequest,
    current_user=Depends(get_current_user),
    db_handler: DBHandler = Depends(get_db_handler)
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
    current_user=Depends(get_current_user),
    db_handler: DBHandler = Depends(get_db_handler)
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


# --- Endpoint: per spostare un corso da completato -> seguito ---
@router.put("/profile/courses/{edition_id}/restore")
def restore_course(
    edition_id: str,
    data: dict = Body(...),
    current_user=Depends(get_current_user),
    db_handler: DBHandler = Depends(get_db_handler)
):
    user_id = current_user["user_id"]
    edition_data = data["edition_data"]

    # 1. Elimina la recensione associata (se esiste)
    delete_review_query = """
        DELETE FROM Review
        WHERE student_id = %s AND edition_id = %s AND edition_data = %s
    """
    db_handler.run_query(delete_review_query, params=(user_id, edition_id, edition_data), fetch=False)

    # 2. Aggiorna lo stato e azzera il voto in Corsi_seguiti
    update_course_query = """
        UPDATE Corsi_seguiti
        SET stato = 'attivo', voto = NULL
        WHERE student_id = %s AND edition_id = %s AND edition_data = %s
    """
    db_handler.run_query(update_course_query, params=(user_id, edition_id, edition_data), fetch=False)

    return {"detail": "Corso ripristinato tra quelli attivi, recensione e voto eliminati"}


# --- Endpoint: per ottenere tutti gli insegnanti ---
@router.get("/teachers")
def get_teachers(db_handler: DBHandler = Depends(get_db_handler)):
    query = """
        SELECT ia.id, ia.nome, ia.cognome
        FROM Insegnanti_Anagrafici ia
    """
    results = db_handler.run_query(query, fetch=True)
    return [{"id": row[0], "nome": row[1], "cognome": row[2]} for row in results]



# --- Endpoint: Aggiungi edizioneCorso e iscrivi studente a quell'EdizioneCorso ---
@router.post("/courses/{corso_id}/editions/add")
def add_edizione_and_enroll(
    corso_id: str,
    edizione: EdizioneCorsoCreate,
    current_user=Depends(get_current_user),
    db_handler: DBHandler = Depends(get_db_handler)
):
    # 1. Crea la nuova EdizioneCorso
    query = """
        INSERT INTO EdizioneCorso (id, insegnante_anagrafico, data, orario, esonero, mod_Esame)
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



###### INSEGNANTE ########


# --- Endpoint: per ottenere i corsi dell'insegnante che è loggato ---
@router.get("/teacher/courses/full")
def get_teacher_courses_full(current_user=Depends(get_current_user), db_handler: DBHandler = Depends(get_db_handler)):
    user_id = current_user["user_id"]
    query = """
        SELECT c.id, c.nome, c.cfu, 
               e.id as edition_id, e.data as edition_data, e.mod_Esame, e.orario, e.esonero, e.stato
        FROM EdizioneCorso e
        JOIN Corso c ON e.id = c.id
        WHERE e.insegnante_anagrafico = %s
        ORDER BY c.nome, e.data DESC
    """
    results = db_handler.run_query(query, params=(user_id,), fetch=True, rollback=True)
    corsi = {}
    for row in results:
        corso_id = row[0]
        if corso_id not in corsi:
            corsi[corso_id] = {
                "id": row[0],
                "nome": row[1],
                "cfu": row[2],
                "edizioni": []
            }
        corsi[corso_id]["edizioni"].append({
            "edition_id": row[3],
            "edition_data": row[4],
            "mod_esame": row[5],
            "orario": row[6],
            "esonero": row[7],
            "stato": row[8]
        })
    return list(corsi.values())



# --- Endpoint: per aggiornare lo stato di un'edizione del corso dell'insegnante che è loggato ---
@router.patch("/teacher/editions/{edition_id}")
def update_edition(
    edition_id: str,
    payload: dict = Body(...),
    current_user=Depends(get_current_user),
    db_handler: DBHandler = Depends(get_db_handler)
):
    user_id = current_user["user_id"]
    # Cambia "insegnante" in "insegnante_anagrafico"
    query_check = "SELECT data FROM EdizioneCorso WHERE id = %s AND insegnante_anagrafico = %s"
    old_data_result = db_handler.run_query(query_check, params=(edition_id, user_id), fetch=True, rollback=True)
    if not old_data_result:
        raise HTTPException(status_code=403, detail="Non autorizzato")
    old_data = old_data_result[0][0]

    allowed_fields = ["data", "mod_Esame", "orario", "esonero", "stato"]
    set_clauses = []
    values = []
    for field in allowed_fields:
        if field in payload:
            set_clauses.append(f"{field} = %s")
            values.append(payload[field])
    if not set_clauses:
        raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")

    # Aggiorna direttamente EdizioneCorso, il CASCADE aggiorna Corsi_seguiti
    query = f"UPDATE EdizioneCorso SET {', '.join(set_clauses)} WHERE id = %s AND data = %s"
    values.extend([edition_id, old_data])
    db_handler.run_query(query, params=tuple(values), rollback=True)
    return {"detail": "Edizione aggiornata"}


# --- Endpoint: Aggiungi una nuova EdizioneCorso come insegnante (vedo anche lo stato)---
@router.post("/teacher/courses/{corso_id}/editions/add")
def add_edition_teacher(
    corso_id: str,
    edizione: EdizioneCorsoCreate,
    current_user=Depends(get_current_user),
    db_handler: DBHandler = Depends(get_db_handler)
):
    user_id = current_user["user_id"]
    # Inserisci la nuova EdizioneCorso
    query = """
        INSERT INTO EdizioneCorso (id, insegnante_anagrafico, data, orario, esonero, mod_Esame, stato)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    db_handler.run_query(query, params=(
        corso_id,
        user_id,
        edizione.data,
        edizione.orario,
        edizione.esonero,
        edizione.mod_Esame,
        getattr(edizione, "stato", "attivo")
    ))
    return {"detail": "EdizioneCorso creata"}








####### STATISTICHE ########


# --- Endpoint: Statistiche dello studente, voti conseguiti, media, cose del genere ---
@router.get("/profile/stats", response_model=StatsResponse)
def get_stats(current_user=Depends(get_current_user), db_handler: DBHandler = Depends(get_db_handler)):
    user_id = current_user["user_id"]
    # Prendi tutti i corsi completati, aggiungi c.id
    query = """
        SELECT c.nome, cs.voto, c.cfu, c.id
        FROM Corsi_seguiti cs
        JOIN EdizioneCorso e ON cs.edition_id = e.id AND cs.edition_data = e.data
        JOIN Corso c ON e.id = c.id
        WHERE cs.student_id = %s AND cs.stato = 'completato' AND cs.voto >= 18
    """
    results = db_handler.run_query(query, params=(user_id,), fetch=True)
    esami = [row[0] for row in results]
    voti = [row[1] for row in results]
    cfu = [row[2] for row in results]
    esami_id = [row[3] for row in results]  # <--- aggiungi questa riga
    
    # Prendi i CFU totali del corso di laurea dello studente
    query_cfu_totali = """
        SELECT cfu_totali
        from corso_di_laurea
        JOIN studenti s ON corso_di_laurea.id = s.corso_laurea_id
        WHERE s.id = %s
    """
    results_cfu_totali = db_handler.run_query(query_cfu_totali, params=(user_id,), fetch=True)
    cfu_totali = results_cfu_totali[0][0] if results_cfu_totali else 0
    
    cfu_completati = sum(cfu)  # tutti quelli trovati sono completati
    media_aritmetica = round(sum(voti) / len(voti), 2) if voti else 0
    media_ponderata = round(sum(v * c for v, c in zip(voti, cfu)) / sum(cfu), 2) if cfu else 0
    return StatsResponse(
        esami=esami,
        voti=voti,
        cfu=cfu,
        esami_id=esami_id,  # <--- aggiungi questo campo
        media_aritmetica=media_aritmetica,
        media_ponderata=media_ponderata,
        cfu_totali=cfu_totali,
        cfu_completati=cfu_completati
    )


# --- Endpoint: Corsi del corso di laurea non ancora completati dallo studente che è loggato ---
# --- Serve per simualre gli esami ---
@router.get("/courses/not-completed", response_model=List[CourseBase])
def get_not_completed_courses(
        current_user=Depends(get_current_user), 
        db_handler: DBHandler = Depends(get_db_handler)):
    
    user_id = current_user["user_id"]
    # Recupera il corso di laurea dello studente
    query_cdl = "SELECT corso_laurea_id FROM Studenti WHERE id = %s"
    result = db_handler.run_query(query_cdl, params=(user_id,), fetch=True)
    if not result:
        raise HTTPException(status_code=404, detail="Studente non trovato")
    corso_laurea_id = result[0][0]
    # Prendi tutti i corsi del corso di laurea che NON sono stati completati
    query = """
        SELECT c.id, c.nome, c.cfu
        FROM Corso c
        WHERE c.id_corso = %s
        AND c.id NOT IN (
            SELECT c2.id
            FROM Corsi_seguiti cs
            JOIN EdizioneCorso e ON cs.edition_id = e.id AND cs.edition_data = e.data
            JOIN Corso c2 ON e.id = c2.id
            WHERE cs.student_id = %s AND cs.stato = 'completato'
        )
        ORDER BY c.nome
    """
    results = db_handler.run_query(query, params=(corso_laurea_id, user_id), fetch=True)
    return [CourseBase(id=row[0], nome=row[1], cfu=row[2]) for row in results]








####### RECENSIONI ########


# --- Endpoint: Recensioni dello studente ---
@router.get("/profile/reviews", response_model=list[ReviewResponse])
def get_student_reviews(current_user=Depends(get_current_user), db_handler: DBHandler = Depends(get_db_handler)):
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
    current_user=Depends(get_current_user),
    db_handler: DBHandler = Depends(get_db_handler)
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

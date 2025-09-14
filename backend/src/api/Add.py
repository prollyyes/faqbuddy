from ..utils.db_utils import get_connection, MODE
from ..utils.db_handler import DBHandler
from fastapi import APIRouter, HTTPException, UploadFile, Form, File, Depends
from ..api.BaseModel import *
from psycopg2 import errors
from ..api.drive_utils import *

# Database connection dependency for Render
def get_db_handler():
    conn = get_connection(mode=MODE)
    db_handler = DBHandler(conn)
    try:
        yield db_handler
    finally:
	    db_handler.close_connection()

router = APIRouter()

@router.post("/addEdizioneCorso")
def addEdizioneCorso(edizioneCorso: AddEdizioneCorso, db_handler: DBHandler = Depends(get_db_handler)):
    """
    Aggiunge una nuova edizione di un corso.

    Parametri:
    - edizioneCorso: dati dell'edizione del corso da aggiungere, inclusi nome corso di laurea, insegnante, semestre, orario, esonero e modalità d'esame.

    Ritorna:
    - messaggio di successo se l'edizione del corso è stata aggiunta correttamente.
    """
    corsiDL = db_handler.execute_query("SELECT DISTINCT nome FROM Corso_di_Laurea")
    if not any(edizioneCorso.nomeCDL in row for row in corsiDL):
        raise HTTPException(status_code=400, detail="Il Corso di Laurea non è stato trovato.")
    
    insegnanti = db_handler.execute_query("SELECT u.id, u.nome, u.cognome FROM Insegnanti_Anagrafici u")
    insegnante_id = None
    for id_, nome, cognome in insegnanti:
        if edizioneCorso.nomeInsegnante == nome and edizioneCorso.cognomeInsegnante == cognome:
            insegnante_id = id_
            break

    if insegnante_id is None:
        raise HTTPException(status_code=400, detail="L'insegnante non è stato trovato.")
    
    corsi = db_handler.execute_query("SELECT id, nome FROM Corso")
    corso_id = None
    for id_, nome in corsi:
        if edizioneCorso.nomeCorso == nome:
            corso_id = id_
            break
    
    if corso_id is None:
        #TODO crea corso
        raise HTTPException(status_code=400, detail="Corso inesistente.")
        

    db_handler.execute_sql_insertion("""
                INSERT INTO EdizioneCorso (id, insegnante_anagrafico, data, orario, esonero, mod_esame) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """, params=(corso_id, insegnante_id, edizioneCorso.semestre.value, 
                             edizioneCorso.orario, edizioneCorso.esonero, 
                             edizioneCorso.mod_Esame))
    
    return {"message": "Edizione Corso aggiunta con successo"}



@router.post("/addCorso")
def addCorso(corso: AddCorso, db_handler: DBHandler = Depends(get_db_handler)):
    """
    Aggiunge un nuovo corso associato a un corso di laurea.

    Parametri:
    - corso: dati del corso da aggiungere, inclusi nome corso, CFU, idoneità, prerequisiti e frequenza obbligatoria.

    Ritorna:
    - messaggio di successo se il corso è stato aggiunto correttamente.
    """
    cdl = db_handler.execute_query("SELECT id, nome FROM Corso_di_Laurea")
    cdl_id = None
    for id_, nome in cdl:
        if corso.nomeCorsoLaurea == nome:
            cdl_id = id_
            break
    
    if cdl_id is None:
        raise HTTPException(status_code=400, detail="Corso di Laurea non trovato.")
    
    db_handler.execute_sql_insertion("""
        INSERT INTO Corso (id_corso, nome, cfu, idoneità, prerequisiti, frequenza_obbligatoria)
        VALUES (%s, %s, %s, %s, %s, %s)
        """, params=(cdl_id, corso.nomeCorso, corso.cfu, corso.idoneita, 
                     corso.prerequisiti, corso.frequenza_obbligatoria))
    
    return {"message": "Corso aggiunto con successo"}

@router.post("/addCorsoSeguito")
def addCorsoSeguito(seguito: AddCorsoSeguito, db_handler: DBHandler = Depends(get_db_handler)): 
    """
    Aggiunge un corso seguito da uno studente.

    Parametri:
    - seguito: dati del corso seguito, inclusi matricola studente, nome corso, semestre, stato e voto.

    Ritorna:
    - messaggio di successo se il corso seguito è stato aggiunto correttamente.
    """
    student_info = db_handler.run_query("""SELECT id, corso_laurea_id FROM Studenti
                                        WHERE matricola = %s""", 
                                        params=(seguito.matricolaStudente,), fetch=True)
    if not student_info:
        raise HTTPException(status_code=400, detail="Matricola dello studente non trovata.")
    student_id = student_info[0][0]
    student_cdl_id = student_info[0][1]

    corso_info = db_handler.run_query("""SELECT id, id_corso
                                         FROM Corso
                                         WHERE nome = %s
                                      """, params=(seguito.nomeCorso,), fetch=True)
    
    if not corso_info:
        raise HTTPException(status_code=400, detail="Corso non trovato.")
    corso_id = corso_info[0][0]
    corso_cdl_id = corso_info[0][1]

    if corso_cdl_id != student_cdl_id:
        raise HTTPException(status_code=400, detail="Non è consentito aggiungere un Corso Seguito che non sia parte del Corso di Laurea dello studente.")

    edizione_data = db_handler.run_query("SELECT data FROM EdizioneCorso WHERE id = %s AND data = %s", params=(corso_id, seguito.semestre.value), fetch=True)
    if not edizione_data:
        raise HTTPException(status_code=400, detail="Edizione del Corso non trovata.")
    edizione_data = edizione_data[0][0]
    db_handler.execute_sql_insertion("""
                                    INSERT INTO Corsi_seguiti (student_id, edition_id, edition_data, stato, voto)
                                    VALUES (%s, %s, %s, %s, %s)
                                     """, params=(student_id, corso_id, edizione_data, seguito.stato, seguito.voto))
    
    return {"message": "Corso Seguito aggiunto con successo"}


@router.post("/addPiattaforma")
def addPiattaforma(piattaforma: AddPiattaforma, db_handler: DBHandler = Depends(get_db_handler)):
    """
    Aggiunge una nuova piattaforma.

    Parametri:
    - piattaforma: dati della piattaforma da aggiungere, principalmente il nome.

    Ritorna:
    - messaggio di successo se la piattaforma è stata aggiunta correttamente.
    """
    if not piattaforma.nome:
        raise HTTPException(status_code=400, detail="Nome della piattaforma invalido.")
    
    db_handler.execute_sql_insertion("""
                        INSERT INTO Piattaforme (nome)
                        VALUES (%s)
                        """, params=(piattaforma.nome,))
    
    return {"message": "Piattaforma aggiunta con successo"}

@router.post("/addEdizioneCorsoPiattaforma")
def addEdizioneCorso_Piattaforma(data: AddEdizioneCorsoPiattaforma, db_handler: DBHandler = Depends(get_db_handler)):
    """
    Associa una piattaforma a una specifica edizione di un corso.

    Parametri:
    - data: dati dell'associazione, inclusi nome corso, semestre, nome piattaforma e codice.

    Ritorna:
    - messaggio di successo se l'associazione è stata aggiunta correttamente.
    - errore 409 se la piattaforma è già associata a questa edizione.
    """
    edizione_corso_info = db_handler.run_query("""
                    SELECT e.id, e.data
                    FROM Corso c JOIN EdizioneCorso e on c.id = e.id
                    WHERE c.nome = %s AND e.data = %s
                                               """,
                    params=(data.nomeCorso, data.semestre.value),fetch=True)
    
    if not edizione_corso_info:
        raise HTTPException(status_code=400, detail="Edizione del Corso non trovata.")
    
    edizione_id = edizione_corso_info[0][0]
    edizione_data = edizione_corso_info[0][1]

    try:
        db_handler.execute_sql_insertion("""
            INSERT INTO EdizioneCorso_Piattaforme (edizione_id, edizione_data, piattaforma_nome, codice)
            VALUES (%s, %s, %s, %s)
        """, params=(edizione_id, edizione_data, data.nomePiattaforma, data.codice))
    except errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="Questa piattaforma è già associata a questa edizione di corso.")
    
    return {"message": "Piattaforma per l'Edzione del Corso aggiunta con successo"}

@router.post("/addTesi")
async def addTesi(
    matricola: str = Form(...),
    parent_folder: str = Form("FAQBuddy"),
    child_folder: str = Form("Tesi"),
    file: UploadFile = File(...),
    db_handler: DBHandler = Depends(get_db_handler)
    ):
    """
    Carica e aggiunge la tesi di uno studente.

    Parametri:
    - matricola: matricola dello studente.
    - parent_folder: cartella principale su Google Drive (default: "FAQBuddy").
    - child_folder: sottocartella su Google Drive (default: "Tesi").
    - file: file della tesi da caricare.

    Ritorna:
    - messaggio di successo se la tesi è stata aggiunta correttamente.
    """
    tesi_info = db_handler.run_query("""
        SELECT s.id, s.corso_laurea_id, u.nome, u.cognome
        FROM Studenti s JOIN Utente u ON s.id = u.id
        WHERE matricola = %s""", params=(matricola,), fetch=True)
    if not tesi_info:
        raise HTTPException(status_code=400, detail="Studente non trovato.")
    
    student_id = tesi_info[0][0]
    cdl_id = tesi_info[0][1]
    nome = tesi_info[0][2]
    cognome = tesi_info[0][3]

    data = await upload_file(file, parent_folder, child_folder, nome, cognome)
    tesi_id = data["file_id"]
    db_handler.execute_sql_insertion("""
                INSERT INTO Tesi (student_id, corso_laurea_id, file)
                VALUES (%s, %s, %s)
                """, params=(student_id, cdl_id, tesi_id))
    
    return {"message": "Tesi aggiunta con successo"}
    

@router.post("/addMaterialeDidattico")
async def addMaterialeDidattico(
        email : str = Form(...),
        nomeCorso : str = Form(...),
        tipo : str = Form(...),
        verificato : bool = Form(False),
        parent_folder: str = Form("FAQBuddy"),
        child_folder: str = Form("Materiale_Didattico"),
        file: UploadFile = File(...),
        db_handler: DBHandler = Depends(get_db_handler)
    ):
    """
    Carica e aggiunge materiale didattico associato a un utente e corso.

    Parametri:
    - email: email dell'utente che carica il materiale.
    - nomeCorso: nome del corso a cui il materiale è associato.
    - tipo: tipo di materiale didattico.
    - verificato: flag di verifica del materiale (default False).
    - parent_folder: cartella principale su Google Drive (default: "FAQBuddy").
    - child_folder: sottocartella su Google Drive (default: "Materiale_Didattico").
    - file: file del materiale didattico da caricare.

    Ritorna:
    - messaggio di successo se il materiale didattico è stato aggiunto correttamente.
    """
    user_info = db_handler.run_query("SELECT id, nome, cognome FROM Utente u WHERE LOWER(u.email) = LOWER(%s)", params=(email,), fetch=True)
    if not user_info:
        raise HTTPException(status_code=400, detail="Utente non trovato.")
    user_id = user_info[0][0]
    nome = user_info[0][1]
    cognome = user_info[0][2]

    course_info = db_handler.run_query("SELECT id FROM Corso WHERE nome = %s", params=(nomeCorso,), fetch=True)
    if not course_info:
        raise HTTPException(status_code=400, detail="Corso non trovato.")
    course_id = course_info[0][0]

    data = await upload_file(file, parent_folder, child_folder, nome, cognome)
    file_id = data["file_id"]
    db_handler.execute_sql_insertion("""
                INSERT INTO Materiale_Didattico (
                            Utente_id,
                            course_id,
                            path_file,
                            tipo,
                            verificato
                            )
                VALUES (%s, %s, %s, %s, %s)""",
                params=(user_id, course_id, file_id, tipo, verificato))
    
    return {"message": "Materiale Didattico Aggiunto con successo."}

@router.post("/addValutazione")
def addValutazione(valutazione: AddValutazione, db_handler: DBHandler = Depends(get_db_handler)):
    """
    Aggiunge una valutazione a un materiale didattico da parte di uno studente.

    Parametri:
    - valutazione: dati della valutazione, inclusi matricola studente, path file del materiale, voto e commento.

    Ritorna:
    - messaggio di successo se la valutazione è stata aggiunta correttamente.
    """
    student_info = db_handler.run_query("SELECT id FROM Studenti WHERE matricola = %s", params=(valutazione.matricola,), fetch=True)
    if not student_info:
        raise HTTPException(status_code=400, detail="Studente non trovato.")
    student_id = student_info[0][0]

    material_info = db_handler.run_query("SELECT id FROM Materiale_Didattico m WHERE m.path_file = %s", params=(valutazione.path_file,),fetch=True)
    if not material_info:
        raise HTTPException(status_code=400, detail="Materiale Didattico non trovato.")
    id_materiale = material_info[0][0]

    db_handler.execute_sql_insertion("""
        INSERT INTO Valutazione (
                                student_id,
                                id_materiale,
                                voto,
                                commento)
        VALUES (%s, %s, %s, %s)""",
        params=(student_id, id_materiale, valutazione.voto, valutazione.commento))
    
    return {"message" : "Valutazione aggiunta con successo."}

async def upload_file(
    file: UploadFile = File(...),
    parent_folder: str = Form(...), # FAQBuddy
    child_folder: str = Form(...), # CV, Materiale_Didattico, Tesi
    nome: str = Form(...),
    cognome: str = Form(...),
    db_handler: DBHandler = Depends(get_db_handler)
):
    """
    Carica un file su Google Drive in una cartella specifica.
    """
    try:
        service = get_drive_service()
        folder_id = get_folder_id(service, parent_folder, child_folder)
        filename = f"{nome}_{cognome}_{file.filename}"
        file_metadata = {'name': filename, 'parents': [folder_id]}
        contents = await file.read()
        with open(filename, "wb") as f:
            f.write(contents)
        from googleapiclient.http import MediaFileUpload
        media = MediaFileUpload(filename, resumable=True)
        uploaded = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        os.remove(filename)
        return {"file_id": uploaded.get('id'), "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
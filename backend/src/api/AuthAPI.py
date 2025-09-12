from uuid import uuid4
from ..utils.db_utils import get_connection, MODE
from ..utils.db_handler import DBHandler
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form, Depends
from .BaseModel import LoginRequest, SignupRequest
from .utils import *
from .drive_utils import *
from dotenv import load_dotenv
from fastapi.responses import JSONResponse


load_dotenv()
# Database connection dependency for Render
def get_db_handler():
    conn = get_connection(mode=MODE)
    db_handler = DBHandler(conn)
    try:
        yield db_handler
    finally:
        db_handler.close_connection()


# conn = get_connection(mode=MODE)

# db_handler = DBHandler(conn)

router = APIRouter()

@router.post("/signup")
def signup(data: SignupRequest, db_handler: DBHandler = Depends(get_db_handler)):
    existing = db_handler.run_query(
        "SELECT id FROM Utente WHERE email = %s",
        params=(data.email,),
        fetch=True
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email già registrata"
        )

    # --- CONTROLLI CAMPI OBBLIGATORI ---
    if not data.nome or not data.cognome or not data.email or not data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tutti i campi obbligatori devono essere compilati"
        )
    # if hasattr(data, "ruolo") and data.ruolo == "insegnante":
    #     if not getattr(data, "infoMail", None) or not getattr(data, "sitoWeb", None) or not getattr(data, "ricevimento", None):
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="Tutti i campi insegnante sono obbligatori"
    #         )
    if hasattr(data, "ruolo") and data.ruolo == "insegnante":
        # non è obbligatorio avere infoMail, sitoWeb, cv, ricevimento
        pass
    else:
        if not getattr(data, "corsoDiLaurea", None) or not getattr(data, "numeroDiMatricola", None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tutti i campi studente sono obbligatori"
            )
        # --- QUI: controllo corso di laurea PRIMA di creare l'utente ---
        corso = db_handler.run_query(
                "SELECT id FROM Corso_di_Laurea WHERE id = %s",
                params=(data.corsoDiLaurea,),
                fetch=True
            )
        if not corso:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corso di laurea non trovato"
            )
        corso_laurea_id = corso[0][0]

    # --- SOLO ORA crea l'utente ---
    user_id = str(uuid4())
    hashed_pwd = hash_password(data.password)
    db_handler.execute_sql_insertion(
        "INSERT INTO Utente (id, email, pwd_hash, nome, cognome, email_verificata) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, data.email, hashed_pwd, data.nome, data.cognome, False) # di default email non verificata per Production
    )

    if hasattr(data, "ruolo") and data.ruolo == "insegnante":
        # Inserisci o aggiorna in Insegnanti_Anagrafici
        db_handler.execute_sql_insertion(
            """
            INSERT INTO Insegnanti_Anagrafici (id, nome, cognome, email, utente_id)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                nome = EXCLUDED.nome,
                cognome = EXCLUDED.cognome,
                email = EXCLUDED.email,
                utente_id = EXCLUDED.utente_id
            """,
            (
                user_id,
                data.nome,
                data.cognome,
                data.email,
                user_id
            )
        )
        db_handler.execute_sql_insertion(
            "INSERT INTO Insegnanti_Registrati (id, anagrafico_id, infoMail, sitoWeb, cv, ricevimento) VALUES (%s, %s, %s, %s, %s, %s)",
            (
                user_id,
                user_id,
                getattr(data, "infoMail", None),
                getattr(data, "sitoWeb", None),
                getattr(data, "cv", None),
                getattr(data, "ricevimento", None)
            )
        )
    else:
        db_handler.execute_sql_insertion(
            "INSERT INTO Studenti (id, corso_laurea_id, matricola) VALUES (%s, %s, %s)",
            (
                user_id,
                corso_laurea_id,
                int(data.numeroDiMatricola)
            )
        )

    # Genera token di verifica (puoi usare anche JWT)
    verification_token = str(uuid4())
    db_handler.execute_sql_insertion(
        "INSERT INTO EmailVerification (user_id, token) VALUES (%s, %s)",
        (user_id, verification_token)
    )
    send_verification_email(data.email, verification_token)
    return {
        "message": "Utente registrato con successo. Controlla la tua email per la verifica.",
        "success": True,
        "user_id": user_id
    }

# -- endpoint per ottenere tutti i corsi di laurea --
@router.get("/corsi-di-laurea")
def get_corsi_di_laurea(db_handler: DBHandler = Depends(get_db_handler)):
    """
    Restituisce la lista dei corsi di laurea disponibili.
    """
    try:
        result = db_handler.run_query(
            "SELECT id, nome FROM Corso_di_Laurea",
            fetch=True
        )
        if not result:
            raise HTTPException(status_code=404, detail="Nessun corso di laurea trovato.")
        return [
            {"id": row[0], "nome": row[1]}
            for row in result
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint riutilizzabile per caricare file su Google Drive
@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    parent_folder: str = Form(...), # FAQBuddy
    child_folder: str = Form(...), # CV, Materiale_Didattico, Tesi
    nome: str = Form(...),
    cognome: str = Form(...)
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
        return JSONResponse({"file_id": uploaded.get('id'), "filename": filename})
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/verify-email")
def verify_email(token: str, db_handler: DBHandler = Depends(get_db_handler)):
    # Cerca il token nella tabella EmailVerification
    result = db_handler.run_query(
        "SELECT user_id FROM EmailVerification WHERE token = %s",
        params=(token,),
        fetch=True
    )
    if not result:
        raise HTTPException(status_code=400, detail="Token non valido o già usato.")
    user_id = result[0][0]
    db_handler.execute_sql_insertion(
        "UPDATE Utente SET email_verificata = TRUE WHERE id = %s",
        (user_id,)
    )
    db_handler.execute_sql_insertion(
        "DELETE FROM EmailVerification WHERE token = %s",
        (token,)
    )
    return {"message": "Email verificata con successo!"}

@router.post("/login")
def login(data: LoginRequest, db_handler: DBHandler = Depends(get_db_handler)):
    user = db_handler.run_query(
        "SELECT id, pwd_hash, email_verificata FROM Utente WHERE email = %s",
        params=(data.email,),
        fetch=True
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utente non valido"
        )
    user_id, pwd_hash, email_verificata = user[0]
    if not verify_password(data.password, pwd_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password non valida"
        )
    if not email_verificata:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Devi prima verificare la tua email"
        )
    from ..auth.jwt_handler import create_access_token
    access_token = create_access_token({"user_id": user_id})
    return {"access_token": access_token}
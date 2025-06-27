from uuid import uuid4
from src.utils.db_utils import get_connection, MODE
from src.utils.db_handler import DBHandler
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from src.api.BaseModel import LoginRequest, SignupRequest
from src.api.utils import *
from src.api.drive_utils import *
from dotenv import load_dotenv
from fastapi.responses import JSONResponse


load_dotenv()

conn = get_connection(mode=MODE)

db_handler = DBHandler(conn)

router = APIRouter()

@router.post("/signup")
def signup(data: SignupRequest):
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
    user_id = str(uuid4())
    hashed_pwd = hash_password(data.password)
    db_handler.execute_sql_insertion(
        "INSERT INTO Utente (id, email, pwd_hash, nome, cognome, email_verificata) VALUES (%s, %s, %s, %s, %s, %s)",
        (user_id, data.email, hashed_pwd, data.nome, data.cognome, True) # metto True solo per comodità, nella realtà è False
    )

    if hasattr(data, "ruolo") and data.ruolo == "insegnante":
        db_handler.execute_sql_insertion(
            "INSERT INTO Insegnanti (id, infoMail, sitoWeb, cv, ricevimento) VALUES (%s, %s, %s, %s, %s)",
            (
                user_id,
                getattr(data, "infoMail", None),
                getattr(data, "sitoWeb", None),
                getattr(data, "cv", None),  # qui puoi salvare l'id file drive o il nome file se vuoi
                getattr(data, "ricevimento", None)
            )
        )
    else:
        # Conversione nome corso di laurea -> id
        if not data.corsoDiLaurea or not data.numeroDiMatricola:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Dati studente mancanti"
            )
        corso = db_handler.run_query(
            "SELECT id FROM Corso_di_Laurea WHERE nome = %s",
            params=(data.corsoDiLaurea,),
            fetch=True
        )
        if not corso:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Corso di laurea non trovato"
            )
        corso_laurea_id = corso[0][0]
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
def verify_email(token: str):
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
def login(data: LoginRequest):
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
    from src.auth.jwt_handler import create_access_token
    access_token = create_access_token({"user_id": user_id})
    return {"access_token": access_token}
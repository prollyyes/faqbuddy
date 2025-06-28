from uuid import uuid4
from src.utils.db_utils import get_db_connection
from src.utils.db_handler import DBHandler
from fastapi import APIRouter, HTTPException, status, UploadFile, File, Form
from src.api.BaseModel import LoginRequest, SignupRequest
from src.api.drive_utils import *
from dotenv import load_dotenv
from fastapi.responses import JSONResponse
import bcrypt
from src.auth.jwt_handler import create_access_token


conn = get_db_connection()

db_handler = DBHandler(conn)

router = APIRouter()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


@router.post("/login")
def login(data: LoginRequest):
    user = db_handler.run_query(
        "SELECT id, pwd_hash FROM Utente WHERE email = %s",
        params=(data.email,),
        fetch=True
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utente non valido"
        )
    user_id, pwd_hash = user[0]
    if not verify_password(data.password, pwd_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password non valida"
        )
    access_token = create_access_token({"user_id": user_id})
    return {"access_token": access_token}

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
        "INSERT INTO Utente (id, email, pwd_hash, nome, cognome) VALUES (%s, %s, %s, %s, %s)",
        (user_id, data.email, hashed_pwd, data.nome, data.cognome)
    )
    return {
        "message": "Utente registrato con successo",
        "success": True,
        "user_id": user_id
    }

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
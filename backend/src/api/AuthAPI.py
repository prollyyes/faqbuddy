from uuid import uuid4
import bcrypt
from src.utils.db_utils import get_connection
from src.utils.db_handler import DBHandler

from src.auth.jwt_handler import create_access_token
from fastapi import APIRouter, HTTPException, status
from src.api.BaseModel import LoginRequest, SignupRequest


conn = get_connection(mode="local")

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

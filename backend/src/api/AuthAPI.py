from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from uuid import uuid4
import bcrypt
from src.utils.db_utils import get_db_connection
from src.utils.db_handler import DBHandler
from fastapi.middleware.cors import CORSMiddleware
from src.auth.jwt_handler import create_access_token


conn = get_db_connection()

db_handler = DBHandler(conn)

app = FastAPI(title="api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    nome: str
    cognome: str

@app.post("/login")
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

@app.post("/signup")
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

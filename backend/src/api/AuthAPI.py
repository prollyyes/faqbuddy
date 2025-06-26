from uuid import uuid4
import bcrypt
from src.utils.db_utils import get_connection, MODE
from src.utils.db_handler import DBHandler
from fastapi import APIRouter, HTTPException, status, Request
from src.api.BaseModel import LoginRequest, SignupRequest
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv

load_dotenv()

conn = get_connection(mode=MODE)
db_handler = DBHandler(conn)
router = APIRouter()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def send_verification_email(email, token):
    msg = EmailMessage()
    msg["Subject"] = "Verifica la tua email"
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = email
    link = f"http://localhost:8000/verify-email?token={token}"
    msg.set_content(f"Clicca qui per verificare la tua email: {link}")
    # Configura il server SMTP (qui esempio con Gmail)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        smtp.send_message(msg)

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
        (user_id, data.email, hashed_pwd, data.nome, data.cognome, False)
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
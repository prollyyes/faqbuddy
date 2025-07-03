import bcrypt
import smtplib
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import os


load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000") # read from .env file, or default to localhost for development

############# Login && Signup####################################################

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def send_verification_email(email, token):
    msg = EmailMessage()
    msg["Subject"] = "Verifica la tua email"
    msg["From"] = os.getenv("EMAIL_FROM")
    msg["To"] = email
    link = f"{API_BASE_URL}/verify-email?token={token}"
    msg.set_content(f"Clicca qui per verificare la tua email: {link}")
    # Configura il server SMTP (qui esempio con Gmail)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(os.getenv("EMAIL_USER"), os.getenv("EMAIL_PASS"))
        smtp.send_message(msg)

##############################################################################

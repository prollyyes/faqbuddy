from pydantic import BaseModel, EmailStr
from typing import List, Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    nome: str
    cognome: str
    ruolo: Optional[str] = "studente"
    corsoDiLaurea: Optional[str] = None
    numeroDiMatricola: Optional[int] = None
    infoMail: Optional[str] = None
    sitoWeb: Optional[str] = None
    cv: Optional[str] = None
    ricevimento: Optional[str] = None

class SearchCorsi(BaseModel):
    nomeCorso : str

# --- PROFILO ---
class UserProfileResponse(BaseModel):
    nome: str
    cognome: str
    email: EmailStr
    matricola: Optional[int] = None
    corso_laurea: Optional[str] = None
    infoMail: Optional[str] = None
    sitoWeb: Optional[str] = None
    cv: Optional[str] = None
    ricevimento: Optional[str] = None
    ruolo: Optional[str] = None
    rating: Optional[float] = None
    livello: Optional[int] = None
    percentuale: Optional[float] = None

class UserProfileUpdate(BaseModel):
    nome: Optional[str]
    cognome: Optional[str]
    email: Optional[EmailStr]
    ruolo: Optional[str]
    # Campi studente
    matricola: Optional[int]
    corso_laurea: Optional[str]
    # Campi insegnante
    infoMail: Optional[str]
    sitoWeb: Optional[str]
    ricevimento: Optional[str]
    cv: Optional[str]

# --- CORSI ---
class CourseInfo(BaseModel):
    nome: str
    docente: Optional[str]
    stato: str  # "attivo" o "completato"
    cfu: Optional[int]

# --- STATISTICHE ---
class StatsResponse(BaseModel):
    esami: List[str]
    voti: List[int]
    media_aritmetica: float
    media_ponderata: float
    cfu_totali: int
    cfu_completati: int

# --- INSERIMENTO ESAME ---
class ExamInsertRequest(BaseModel):
    corso: str
    voto: int
    data: Optional[str]
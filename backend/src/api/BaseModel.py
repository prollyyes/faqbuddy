from pydantic import BaseModel, EmailStr
from typing import List, Optional
import uuid

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
    cfu: List[int]
    esami_id: List[uuid.UUID]
    media_aritmetica: float
    media_ponderata: float
    cfu_totali: int
    cfu_completati: int

# --- INSERIMENTO ESAME ---
class ExamInsertRequest(BaseModel):
    corso: str
    voto: int
    data: Optional[str]

# --- Recensioni Corso ---
class ReviewBase(BaseModel):
    student_id: Optional[uuid.UUID]
    edition_id: uuid.UUID
    edition_data: str
    descrizione: Optional[str]
    voto: int

class ReviewCreate(BaseModel):
    edition_id: uuid.UUID
    edition_data: str
    descrizione: Optional[str]
    voto: int

class ReviewResponse(ReviewBase):
    id: uuid.UUID
    class Config:
        orm_mode = True

class CourseBase(BaseModel):
    id: uuid.UUID
    nome: str
    cfu: int
    docente: Optional[str] = None
    edition_id: Optional[uuid.UUID] = None
    edition_data: Optional[str] = None

class CourseResponse(BaseModel):
    id: str
    nome: str
    cfu: int
    docente_nome: Optional[str]
    docente_cognome: Optional[str]
    edition_id: str
    edition_data: str
    stato: str
    voto: Optional[int] = None

# --- Edizione Corso (per visualizzare le edizioni disponibili di un corso) ---
class CourseEditionResponse(BaseModel):
    id: uuid.UUID
    data: str
    docente: Optional[str]

# --- Richiesta per aggiungere un corso/edizione ai corsi seguiti ---
class AddCourseRequest(BaseModel):
    edition_id: uuid.UUID
    edition_data: str

class EdizioneCorsoCreate(BaseModel):
    insegnante: str  # UUID
    data: str        # semestre, es: 'S1/2024'
    orario: Optional[str] = None
    esonero: bool
    mod_Esame: str
    stato: str = 'Attivo' # "attivo" o "completato"
    
class CompleteCourseRequest(BaseModel):
    edition_data: str
    voto: int
    
    
# Chat.py
class T2SQLRequest(BaseModel):
    question: str
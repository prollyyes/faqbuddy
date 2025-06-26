from pydantic import BaseModel, EmailStr, Field
from uuid import uuid4

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    nome: str
    cognome: str

class SearchCorsi(BaseModel):
    nomeCorso : str

class Semestre(BaseModel):
    value: str = Field(pattern=r"^S[12]/[0-9]{4}$")

class AddEdizioneCorso(BaseModel):
    nomeCDL : str
    nomeCorso : str
    nomeInsegnante : str
    cognomeInsegnante : str
    data : Semestre
    orario : str
    esonero : bool
    mod_Esame : str

class AddCorso(BaseModel):
    nomeCorsoLaurea : str
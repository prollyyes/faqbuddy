from typing import Optional
from pydantic import BaseModel, EmailStr

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

class SearchEdizione(BaseModel):
    nomeCorso: str

class SearchMaterials(BaseModel):
    """
    • edizioneCorso: 'all'  oppure UUID dell'edizione (string)
    • nomeCorso:     richiesto solo se edizioneCorso == 'all'
    • dataEdizione:  richiesto solo se edizioneCorso != 'all'
    """
    edizioneCorso: str
    nomeCorso: Optional[str] = None
    dataEdizione: Optional[str] = None
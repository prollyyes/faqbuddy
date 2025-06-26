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
    edizioneCorso: str
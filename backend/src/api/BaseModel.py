from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional, Annotated

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
    semestre : Semestre
    orario : Optional[str]
    esonero : bool
    mod_Esame : str

class AddCorso(BaseModel):
    nomeCorsoLaurea : str
    nomeCorso : str
    cfu : int
    idoneita : bool
    prerequisiti : Optional[str]
    fequenza_obbligatoria : Optional[str]

class AttendStatus(str, Enum):
    attivo = "attivo"
    completato = "completato"
    abbandonato = "abbandonato"

class AddCorsoSeguito(BaseModel):
    nomeCorso : str
    semestre : Semestre
    matricolaStudente : int
    stato: AttendStatus
    voto: Optional[Annotated[int, Field(ge=18, le=31)]] = None

class AddPiattaforma(BaseModel):
    nome : str

class AddEdizioneCorsoPiattaforma(BaseModel):
    nomeCorso : str
    semestre : Semestre
    nomePiattaforma : str
    codice : Optional[str]

class AddValutazione(BaseModel):
    matricola : str
    path_file : str
    voto : int = Field(ge=1, le=5)
    commento : Optional[str]
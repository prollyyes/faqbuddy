from typing import Optional
from fastapi import HTTPException

def normalize_nome_corso(nome: str) -> str:
    """
    Normalizza il nome del corso: rimuove spazi extra e capitalizza ogni parola.
    Esempio: 'basi di dati' -> 'Basi Di Dati'
    """
    return " ".join(nome.strip().title().split())

def normalize_email(email: str) -> str:
    """
    Normalizza l'email in lowercase e senza spazi.
    """
    return email.strip().lower()

def normalize_nome(nome: str) -> str:
    """
    Capitalizza il nome.
    """
    return nome.strip().capitalize()

def normalize_cognome(cognome: str) -> str:
    """
    Capitalizza il cognome.
    """
    return cognome.strip().capitalize()

def validate_voto_materiale(voto: int):
    """
    Valida il voto dei materiali (1-5).
    """
    if not (1 <= voto <= 5):
        raise HTTPException(status_code=400, detail="Il voto deve essere compreso tra 1 e 5.")
    return voto

def validate_voto_esame(voto: Optional[int]):
    """
    Valida il voto di un esame (18-31) se presente.
    """
    if voto is not None and not (18 <= voto <= 31):
        raise HTTPException(status_code=400, detail="Il voto deve essere compreso tra 18 e 31.")
    return voto

def validate_semestre(semestre: str):
    """
    Valida che il semestre rispetti il pattern.
    """
    import re
    if not re.match(r"^S[12]/[0-9]{4}$", semestre):
        raise HTTPException(status_code=400, detail="Il semestre deve avere il formato S1/AAAA o S2/AAAA.")
    return semestre

def validate_non_empty(value: str, field_name: str):
    """
    Generica: valida che il campo non sia vuoto.
    """
    if not value or not value.strip():
        raise HTTPException(status_code=400, detail=f"{field_name} non può essere vuoto.")
    return value.strip()
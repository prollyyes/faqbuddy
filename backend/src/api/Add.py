from src.utils.db_utils import get_db_connection
from src.utils.db_handler import DBHandler
from fastapi import APIRouter, HTTPException
from src.api.BaseModel import *

conn = get_db_connection()

db_handler = DBHandler(conn)

router = APIRouter()

@router.post("/addEdizioneCorso")
def addEdizioneCorso(edizioneCorso: AddEdizioneCorso):
    corsiDL = db_handler.execute_query("SELECT DISTINCT nome FROM Corso_di_Laurea")
    if not any(edizioneCorso.nomeCDL in row for row in corsiDL):
        raise HTTPException(status_code=400, detail="Il Corso di Laurea non è stato trovato.")
    
    insegnanti = db_handler.execute_query("SELECT u.id, u.nome, u.cognome FROM Utente u JOIN Insegnanti i ON u.id = i.id")
    insegnante_id = None
    for id_, nome, cognome in insegnanti:
        if edizioneCorso.nomeInsegnante == nome and edizioneCorso.cognomeInsegnante == cognome:
            insegnante_id = id_
            break

    if insegnante_id is None:
        raise HTTPException(status_code=400, detail="L'insegnante non è stato trovato.")
    
    corsi = db_handler.execute_query("SELECT id, nome FROM Corso")
    corso_id = None
    for id_, nome in corsi:
        if edizioneCorso.nomeCorso == nome:
            corso_id = id_
            break
    
    if corso_id is None:
        #TODO crea corso
        raise HTTPException(status_code=400, detail="Corso inesistente.")
        

    db_handler.execute_sql_insertion("""
                INSERT INTO EdizioneCorso (id, insegnante, data, orario, esonero, mod_esame) 
                VALUES (%s, %s, %s, %s, %s, %s)
                """, params=(corso_id, insegnante_id, edizioneCorso.data.value, 
                             edizioneCorso.orario, edizioneCorso.esonero, 
                             edizioneCorso.mod_Esame))
    
    return {"message": "Edizione Corso aggiunta con successo"}



@router.post("/addCorso")
def addCorso(corso: AddCorso):
    return
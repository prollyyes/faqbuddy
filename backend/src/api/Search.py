from uuid import uuid4
import bcrypt
from src.utils.db_utils import get_connection
from src.utils.db_handler import DBHandler
from fastapi import APIRouter, HTTPException, status
from fastapi import Depends
from src.api.BaseModel import SearchCorsi, SearchEdizione, SearchMaterials


conn = get_connection(mode="local")

db_handler = DBHandler(conn)

router = APIRouter()


@router.get("/getCorsoLaurea")
def getCorsoLaurea():
    message = "Lista nomi corsi Laurea"
    corsiLaurea = db_handler.run_query(
        "SELECT DISTINCT nome FROM Corso_di_Laurea",
        fetch=True
    )
    if not corsiLaurea:
        message = "Nessun corso di Laurea trovato"

    return{
        "message" : message,
        "nomi" : corsiLaurea
    }

@router.post("/getCorso")
def getCorso(data: SearchCorsi):
    message = "Lista nomi Corsi"
    corsi = db_handler.run_query(
        """
        SELECT DISTINCT c.nome
        FROM Corso AS c 
        JOIN Corso_di_Laurea AS cdl ON c.id_corso = cdl.id
        WHERE cdl.nome = %s
        """,
        params=(data.nomeCorso,),
        fetch=True
    )
    if not corsi:
        message = "nessuno corso trovato"
    return {
        "message": message,
        "nomi": corsi
    }

@router.post("/getEdizione")
def getEdizione(data: SearchEdizione):
    message = "Lista edizione corsi"
    edizioniCorsi = db_handler.run_query(
        """
        SELECT DISTINCT c.nome, e.data, e.id
        FROM Corso c JOIN EdizioneCorso e ON c.id = e.id
        WHERE c.nome = %s
        """,
        params=(data.nomeCorso,),
        fetch=True
    )
    if not edizioniCorsi:
        message = "nessuna edizione del corso trovata"
    return {
        "message" : message,
        "edizioni" : edizioniCorsi
    }

@router.post("/getMaterials")
async def get_materials(data: SearchMaterials):
    try:
        # Validazione logica dei parametri
        if data.edizioneCorso == 'all':
            if not data.nomeCorso:
                raise HTTPException(
                    status_code=422,
                    detail="nomeCorso è obbligatorio quando edizioneCorso='all'"
                )
        else:
            if not data.dataEdizione:
                raise HTTPException(
                    status_code=422,
                    detail="dataEdizione è obbligatorio per edizione specifica"
                )
        if data.edizioneCorso == 'all':
            materiali = db_handler.run_query(
                """
                SELECT md.path_file, md.tipo, md.verificato, md.rating_medio
                FROM Materiale_Didattico md
                JOIN EdizioneCorso ed ON md.course_id = ed.id AND md.data = ed.data
                JOIN Corso c ON c.id = ed.id
                WHERE c.nome = %s
                """,
                params=(data.nomeCorso,),
                fetch=True
            )
        else:
            materiali = db_handler.run_query(
                """
                SELECT md.path_file, md.tipo, md.verificato, md.rating_medio
                FROM Materiale_Didattico md
                WHERE md.course_id = %s AND md.data = %s
                """,
                params=(data.edizioneCorso, data.dataEdizione),
                fetch=True
            )
        return {"materiale": materiali}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/getInfoCorso")
def getInfoCorso(data: SearchMaterials):
    try:
        # Validazione logica dei parametri
        if data.edizioneCorso == 'all':
            if not data.nomeCorso:
                raise HTTPException(
                    status_code=422,
                    detail="nomeCorso è obbligatorio quando edizioneCorso='all'"
                )
        else:
            if not data.dataEdizione:
                raise HTTPException(
                    status_code=422,
                    detail="dataEdizione è obbligatorio per edizione specifica"
                )
        if data.edizioneCorso == 'all':
            info = db_handler.run_query(
                """
                SELECT u.nome,u.cognome,i.infoMail,i.sitoWeb, ed.data, ed.orario, ed.esonero, ed.mod_Esame
                FROM EdizioneCorso ed
                JOIN Corso c ON c.id = ed.id
                JOIN Insegnanti i ON ed.insegnante = i.id
                JOIN Utente u ON i.id = u.id
                WHERE c.nome = %s
                """,
                params=(data.nomeCorso,),
                fetch=True
            )
        else:
            info = db_handler.run_query(
                """
                SELECT u.nome,u.cognome,i.infoMail,i.sitoWeb, ed.data, ed.orario, ed.esonero, ed.mod_Esame
                FROM EdizioneCorso ed
                JOIN Insegnanti i ON ed.insegnante = i.id
                JOIN Utente u ON i.id = u.id
                WHERE ed.id = %s AND ed.data = %s
                """,
                params=(data.edizioneCorso, data.dataEdizione),
                fetch=True
            )
        return {"materiale": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
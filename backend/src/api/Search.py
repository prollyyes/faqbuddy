from src.utils.db_utils import get_db_connection
from src.utils.db_handler import DBHandler
from fastapi import APIRouter, HTTPException, status
from src.api.BaseModel import SearchCorsi, SearchEdizione, SearchMaterials


conn = get_db_connection()

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
def getMaterials(data: SearchMaterials):
    message = "Lista dei materiali didattici"
    materiali = db_handler.run_query(
        """
        SELECT path_file, tipo, verificato, rating_medio
        FROM Materiale_Didattico md 
        JOIN EdizioneCorso ed ON md.course_id = ed.id
        WHERE ed.id = %s
        """,
        params=(data.edizioneCorso,),
        fetch=True
    )
    if not materiali:
        message = "Nessun materiale trovato"
    return {
        "message": message,
        "materiale": materiali
    }

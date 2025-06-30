from uuid import uuid4
from ..utils.db_utils import get_connection, MODE
from ..utils.db_handler import DBHandler
from fastapi import APIRouter, HTTPException, status
from .BaseModel import SearchCorsi


conn = get_connection(mode=MODE)

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

""" @router.post("/getCorso")
def getCorso(data : SearchCorsi):
     """

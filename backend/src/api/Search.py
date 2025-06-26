from uuid import uuid4
import bcrypt
from src.utils.db_utils import get_db_connection
from src.utils.db_handler import DBHandler
from fastapi import APIRouter, HTTPException, status
from src.api.BaseModel import SearchCorsi


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

""" @router.post("/getCorso")
def getCorso(data : SearchCorsi):
     """

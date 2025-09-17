import inspect
from fastapi import HTTPException
from psycopg2 import errors
from functools import wraps


def handle_db_errors(func):
    """
    Decoratore per la gestione degli errori sollevati dal DB.
    """
    if inspect.iscoroutinefunction(func):  # async def
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException as http_exc:
                raise http_exc
            except errors.UniqueViolation:
                raise HTTPException(status_code=409, detail="Elemento già presente nel database.")
            except errors.ForeignKeyViolation:
                raise HTTPException(status_code=400, detail="Violazione di vincolo esterno.")
            except errors.CheckViolation:
                raise HTTPException(status_code=400, detail="Violazione di vincolo CHECK.")
            except errors.NotNullViolation:
                raise HTTPException(status_code=400, detail="Campo richiesto non valorizzato.")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Errore generico: {str(e)}")
        return async_wrapper
    else:  # def
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException as http_exc:
                raise http_exc
            except errors.UniqueViolation:
                raise HTTPException(status_code=409, detail="Elemento già presente nel database.")
            except errors.ForeignKeyViolation:
                raise HTTPException(status_code=400, detail="Violazione di vincolo esterno.")
            except errors.CheckViolation:
                raise HTTPException(status_code=400, detail="Violazione di vincolo di dominio.")
            except errors.NotNullViolation:
                raise HTTPException(status_code=400, detail="Campo richiesto non valorizzato.")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Errore generico: {str(e)}")
        return sync_wrapper
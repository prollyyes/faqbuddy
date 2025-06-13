from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .converter import TextToSQLConverter
from .db_utils import get_db_connection, get_database_schema, is_sql_safe

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class T2SQLRequest(BaseModel):
    question: str

@app.post("/t2sql")
def t2sql_endpoint(req: T2SQLRequest):
    conn = get_db_connection()
    converter = TextToSQLConverter()
    schema = get_database_schema(conn)
    print("SCHEMA PER IL PROMPT:\n", schema)
    prompt = converter.create_prompt(req.question, schema)
    # Chiamata a Ollama e print della risposta grezza
    raw_response = converter.query_ollama(prompt)
    print("RISPOSTA GREZZA OLLAMA:", repr(raw_response))
    sql_query = converter.clean_sql_response(raw_response)
    print("QUERY SQL GENERATA:\n", sql_query)
    if not is_sql_safe(sql_query):
        return {"chosen": "INVALID_QUERY", "ml_model": "T2SQL", "ml_confidence": 0.0, "gemma3_4b": sql_query}
    try:
        cur = conn.cursor()
        cur.execute(sql_query)
        rows = cur.fetchall()
        if cur.description is not None:
            columns = [desc[0] for desc in cur.description]
            result = [dict(zip(columns, row)) for row in rows]
        else:
            columns = []
            result = []
        cur.close()
        conn.close()
        return {
            "chosen": result,
            "ml_model": "T2SQL",
            "ml_confidence": 1.0,
            "gemma3_4b": sql_query
        }
    except Exception as e:
        return {
            "chosen": str(e),
            "ml_model": "T2SQL",
            "ml_confidence": 0.0,
            "gemma3_4b": sql_query
        }
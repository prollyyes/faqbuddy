import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

MODE="local" # cosi usiamo solo MODE per le connessioni, ed è più facile da cambiare

def get_connection(mode="local"):
    if mode == "local":
        prefix = "DB_"
        ssl = False
    elif mode == "neon":
        prefix = "DB_NEON_"
        ssl = True
    else:
        raise ValueError("mode deve essere 'local' o 'neon'")

    dbname = os.getenv(f"{prefix}NAME")
    user = os.getenv(f"{prefix}USER")
    password = os.getenv(f"{prefix}PASSWORD")
    host = os.getenv(f"{prefix}HOST")
    port = os.getenv(f"{prefix}PORT")

    conn_args = dict(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    if ssl:
        conn_args["sslmode"] = "require"

    return psycopg2.connect(**conn_args)

def get_database_schema(conn) -> str:
    # Ottieni lo schema delle tabelle e colonne
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position
    """)
    rows = cur.fetchall()
    schema = {}
    for table, col, dtype in rows:
        schema.setdefault(table, []).append(f"{col} ({dtype})")
    schema_str = ""
    for table, cols in schema.items():
        schema_str += f"Table: {table}\n  " + ", ".join(cols) + "\n"
    cur.close()
    return schema_str

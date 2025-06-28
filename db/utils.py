import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

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
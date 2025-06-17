import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()  # Carica le variabili d'ambiente dal file .env

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME", "faqbuddy_db"),
    user=os.getenv("DB_USER", "db_user"),
    password=os.getenv("DB_PASSWORD", "pwd"),
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5433")
)

print("✅ Connessione a PostgreSQL riuscita!")
conn.close()
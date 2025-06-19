import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()


def get_connection():
    # take the credentials from the .env file
    dbname = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")

    return psycopg2.connect(
        # use the credentials here
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
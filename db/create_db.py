import os
import psycopg2
from dotenv import load_dotenv
import subprocess
import sys

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def drop_and_create_db():
    print(f"Dropping database {DB_NAME} (if exists)...")
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    conn.autocommit = True
    cur = conn.cursor()
    # Termina connessioni attive
    cur.execute(f"""
        SELECT pg_terminate_backend(pid) FROM pg_stat_activity
        WHERE datname = '{DB_NAME}' AND pid <> pg_backend_pid();
    """)
    cur.execute(f"DROP DATABASE IF EXISTS {DB_NAME};")
    print(f"Creating database {DB_NAME}...")
    cur.execute(f"CREATE DATABASE {DB_NAME};")
    cur.close()
    conn.close()
    print("✅ Database dropped and created.")

def run_schema_sql():
    print("Running schema.sql...")
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    cmd = [
        "psql",
        "-h", DB_HOST,
        "-p", str(DB_PORT),
        "-U", DB_USER,
        "-d", DB_NAME,
        "-f", schema_path
    ]
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASSWORD
    result = subprocess.run(cmd, env=env)
    if result.returncode != 0:
        print("❌ Error running schema.sql")
        sys.exit(1)
    print("✅ schema.sql executed.")

def run_setup_data():
    print("Running setup_data.py...")
    setup_data_path = os.path.join(os.path.dirname(__file__), "setup_data.py")
    result = subprocess.run([sys.executable, setup_data_path])
    if result.returncode != 0:
        print("❌ Error running setup_data.py")
        sys.exit(1)
    print("✅ setup_data.py executed.")

if __name__ == "__main__":
    drop_and_create_db()
    run_schema_sql()
    run_setup_data()
    print("🎉 Database setup completo!")
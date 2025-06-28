import os
import psycopg2
from dotenv import load_dotenv
import subprocess
import sys

load_dotenv()

if len(sys.argv) < 2 or sys.argv[1] not in ("local", "neon"):
    print("❌ Devi specificare l'ambiente: python create_db.py local  oppure  neon")
    sys.exit(1)
env = sys.argv[1].lower()

# Prendi i parametri dal connection util
def get_db_params(mode):
    if mode == "neon":
        prefix = "DB_NEON_"
    else:
        prefix = "DB_"
    return {
        "DB_NAME": os.getenv(f"{prefix}NAME"),
        "DB_USER": os.getenv(f"{prefix}USER"),
        "DB_PASSWORD": os.getenv(f"{prefix}PASSWORD"),
        "DB_HOST": os.getenv(f"{prefix}HOST"),
        "DB_PORT": os.getenv(f"{prefix}PORT"),
        "SSL_MODE": "require" if mode == "neon" else None
    }

params = get_db_params(env)
DB_NAME = params["DB_NAME"]
DB_USER = params["DB_USER"]
DB_PASSWORD = params["DB_PASSWORD"]
DB_HOST = params["DB_HOST"]
DB_PORT = params["DB_PORT"]
SSL_MODE = params["SSL_MODE"]

def drop_and_create_db():
    print(f"Dropping database {DB_NAME} (if exists)...")
    conn = psycopg2.connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=int(DB_PORT),
        sslmode=SSL_MODE if SSL_MODE else None
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
    if SSL_MODE:
        cmd.extend(["--set", f"sslmode={SSL_MODE}"])
    env_vars = os.environ.copy()
    env_vars["PGPASSWORD"] = DB_PASSWORD
    result = subprocess.run(cmd, env=env_vars)
    if result.returncode != 0:
        print("❌ Error running schema.sql")
        sys.exit(1)
    print("✅ schema.sql executed.")

def run_setup_data(env):
    print("Running setup_data.py...")
    setup_data_path = os.path.join(os.path.dirname(__file__), "setup_data.py")
    result = subprocess.run([sys.executable, setup_data_path, "--env", env])
    if result.returncode != 0:
        print("❌ Error running setup_data.py")
        sys.exit(1)
    print("✅ setup_data.py executed.")

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("local", "neon"):
        print("❌ Devi specificare l'ambiente: python create_db.py local  oppure  neon")
        sys.exit(1)
    env = sys.argv[1].lower()
    if env == "neon":
        print("⚠️  FACENDO COSI DISTRUGGERAI E RICREERAI IL DB REMOTO SU NEON, NE SEI SICURO? [SI per confermare]")
        risposta = input().strip().lower()
        if risposta != "si":
            print("Operazione annullata.")
            sys.exit(0)
    drop_and_create_db()
    run_schema_sql()
    run_setup_data(env)
    print("🎉 Database setup completo!")
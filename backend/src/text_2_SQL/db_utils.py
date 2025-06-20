import psycopg2
import os

def get_db_connection():
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "faqbuddy_db"),
        user=os.getenv("DB_USER", "db_user"),
        password=os.getenv("DB_PASSWORD", "pwd"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433")
    )

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

def is_sql_safe(sql_query: str) -> bool:
    sql = sql_query.strip().upper()
    return sql.startswith("SELECT") or sql.startswith("WITH")
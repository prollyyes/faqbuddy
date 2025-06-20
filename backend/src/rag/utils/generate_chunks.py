import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_chunks():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "faqbuddy_db"),
        user=os.getenv("DB_USER", "db_user"),
        password=os.getenv("DB_PASSWORD", "pwd"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5433")
    )
    cur = conn.cursor()

    # Query to get all exam information with related professor and textbook details
    cur.execute("""
        SELECT 
            e.id as exam_id,
            e.year,
            p.name as prof_name,
            p.lastname as prof_lastname,
            p.room as prof_room,
            t.title as textbook_title,
            t.resources as textbook_resources
        FROM exam e
        JOIN professor p ON e.professor_id = p.id
        JOIN textbook t ON e.textbook_id = t.id
        ORDER BY e.year DESC, p.lastname, p.name
    """)

    rows = cur.fetchall()
    
    def format_row(row):
        exam_id, year, prof_name, prof_lastname, prof_room, textbook_title, textbook_resources = row
        return (
            f"Exam Information:\n"
            f"ID: {exam_id}\n"
            f"Year: {year}\n"
            f"Professor: {prof_name} {prof_lastname} (Room: {prof_room})\n"
            f"Textbook: {textbook_title}\n"
            f"Resources: {textbook_resources}"
        )

    chunks = [format_row(row) for row in rows]

    cur.close()
    conn.close()

    return chunks
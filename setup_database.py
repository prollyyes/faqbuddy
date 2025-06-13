import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def create_database():
    # Connect to default postgres database to create new database
    conn = psycopg2.connect(
        dbname="postgres",
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432")
    )
    conn.autocommit = True
    cur = conn.cursor()
    
    # Create database if it doesn't exist
    try:
        cur.execute(sql.SQL("CREATE DATABASE {}").format(
            sql.Identifier(os.getenv("DB_NAME", "thesis_db"))
        ))
        print("✅ Database created successfully")
    except psycopg2.Error as e:
        print(f"Note: {e}")
    
    cur.close()
    conn.close()

def setup_tables():
    # Connect to our database
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME", "exams_db"),
        user=os.getenv("DB_USER", "simple_user"),
        password=os.getenv("DB_PASSWORD", "secretpwd"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432")
    )
    cur = conn.cursor()
    
    # Create tables
    cur.execute("""
        -- Create Textbook table
        CREATE TABLE IF NOT EXISTS textbook (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            resources TEXT NOT NULL
        );

        -- Create Professor table
        CREATE TABLE IF NOT EXISTS professor (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            lastname VARCHAR(100) NOT NULL,
            room VARCHAR(20) NOT NULL
        );

        -- Create Exam table with foreign keys
        CREATE TABLE IF NOT EXISTS exam (
            id SERIAL PRIMARY KEY,
            year INTEGER NOT NULL,
            professor_id INTEGER NOT NULL,
            textbook_id INTEGER NOT NULL,
            FOREIGN KEY (professor_id) REFERENCES professor(id),
            FOREIGN KEY (textbook_id) REFERENCES textbook(id)
        );
    """)
    
    # Sample data for textbooks
    textbooks = [
        ("Introduction to Computer Science", "LINK HERE"),
        ("Data Structures and Algorithms", "LINK HERE"),
        ("Database Systems", "LINK HERE"),
        ("Machine Learning Fundamentals", "LINK HERE"),
        ("Software Engineering Principles", "LINK HERE"),
        ("Operating Systems", "LINK HERE"),
        ("Computer Networks", "LINK HERE"),
        ("Artificial Intelligence", "LINK HERE")
    ]
    
    # Sample data for professors
    professors = [
        ("John", "Smith", "A101"),
        ("Maria", "Johnson", "B203"),
        ("Robert", "Williams", "C305"),
        ("Sarah", "Brown", "D407"),
        ("Michael", "Davis", "E509"),
        ("Emma", "Wilson", "F611"),
        ("David", "Taylor", "G713"),
        ("Lisa", "Anderson", "H815")
    ]
    
    # Insert sample data
    print("Inserting textbooks...")
    for title, resources in textbooks:
        cur.execute("""
            INSERT INTO textbook (title, resources)
            VALUES (%s, %s)
        """, (title, resources))
    
    print("Inserting professors...")
    for name, lastname, room in professors:
        cur.execute("""
            INSERT INTO professor (name, lastname, room)
            VALUES (%s, %s, %s)
        """, (name, lastname, room))
    
    # Generate exams (connecting professors and textbooks)
    print("Generating exams...")
    current_year = datetime.now().year
    for year in range(current_year - 3, current_year + 1):
        for prof_id in range(1, len(professors) + 1):
            for textbook_id in range(1, len(textbooks) + 1):
                # Create some variety in the relationships
                if (prof_id + textbook_id) % 3 == 0:  # This creates a pattern of relationships
                    cur.execute("""
                        INSERT INTO exam (year, professor_id, textbook_id)
                        VALUES (%s, %s, %s)
                    """, (year, prof_id, textbook_id))
    
    conn.commit()
    print("✅ Tables created and populated with sample data")
    
    # Print some statistics
    cur.execute("SELECT COUNT(*) FROM textbook")
    textbook_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM professor")
    professor_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM exam")
    exam_count = cur.fetchone()[0]
    
    print(f"\nDatabase Statistics:")
    print(f"Textbooks: {textbook_count}")
    print(f"Professors: {professor_count}")
    print(f"Exams: {exam_count}")
    
    cur.close()
    conn.close()

def main():
    print("🔄 Setting up database...")
    create_database()
    setup_tables()
    print("✅ Database setup complete!")

if __name__ == "__main__":
    main() 
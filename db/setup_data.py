from utils import get_connection
from dotenv import load_dotenv
from uuid import uuid4
from datetime import date
import bcrypt

load_dotenv()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def insert_departments(cur):
    departments = [
        "Ingegneria informatica, automatica e gestionale Antonio Ruberti",
        "Ingegneria civile, edile e ambientale",
        "Ingegneria strutturale e geotecnica",
        "Scienze di base e applicate per l'ingegneria",
        "Ingegneria chimica, materiali e ambiente",
        "Ingegneria meccanica e aerospaziale"
    ]
    
    dept_ids = {}
    for dept in departments:
        dept_id = str(uuid4())
        cur.execute(
            "INSERT INTO Dipartimento (id, nome) VALUES (%s, %s) RETURNING id",
            (dept_id, dept)
        )
        dept_ids[dept] = dept_id
    
    print(f"✅ Inserted {len(departments)} departments")
    return dept_ids

def insert_faculties(cur, dept_ids):
    faculties = [
        {
            "nome": "Ingegneria dell'Informazione, Informatica e Statistica",
            "dipartimento": "Ingegneria informatica, automatica e gestionale Antonio Ruberti",
            "presidente": "Prof. Marco Schaerf",
            "contatti": "presidenza-i3s@uniroma1.it"
        },
        # for now, one entry only... To be expanded later.
        
    ]
    
    faculty_ids = {}
    for faculty in faculties:
        faculty_id = str(uuid4())
        cur.execute(
            "INSERT INTO Facolta (id, dipartimento_id, presidente, nome, contatti) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (faculty_id, dept_ids[faculty["dipartimento"]], faculty["presidente"], faculty["nome"], faculty["contatti"])
        )
        faculty_ids[faculty["nome"]] = faculty_id
    
    print(f"✅ Inserted {len(faculties)} faculties")
    return faculty_ids

def insert_degree_courses(cur, faculty_ids):
    courses = [
        {
            "nome": "Ingegneria Informatica e Automatica",
            "facolta": "Ingegneria dell'Informazione, Informatica e Statistica",
            "descrizione": "Corso di laurea triennale in Ingegneria Informatica e Automatica",
            "classe": "L-8",
            "tipologia": "triennale",
            "mail_segreteria": "segreteria-i3s@uniroma1.it",
            "test": True
        },
        # Add more degree courses
    ]
    
    course_ids = {}
    for course in courses:
        course_id = str(uuid4())
        cur.execute(
            """
            INSERT INTO Corso_di_Laurea 
            (id, id_facolta, nome, descrizione, classe, tipologia, mail_segreteria, test) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (
                course_id, 
                faculty_ids[course["facolta"]], 
                course["nome"],
                course["descrizione"],
                course["classe"],
                course["tipologia"],
                course["mail_segreteria"],
                course["test"]
            )
        )
        course_ids[course["nome"]] = course_id
    
    print(f"✅ Inserted {len(courses)} degree courses")
    return course_ids

def insert_users_and_roles(cur, degree_course_ids):
    professors = [
        {
            "nome": "Roberto",
            "cognome": "Baldoni",
            "email": "roberto.baldoni@uniroma1.it",
            "infoMail": "roberto.baldoni@uniroma1.it",
            "sitoWeb": "http://www.dis.uniroma1.it/~baldoni/",
            "ricevimento": "Martedì 14:00-16:00"
        },
        # Add more professors
    ]
    
    professor_ids = {}
    for prof in professors:
        user_id = str(uuid4())
        # Insert base user
        cur.execute(
            """
            INSERT INTO Utente (id, email, pwd_hash, nome, cognome)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, prof["email"], hash_password("temp123"), prof["nome"], prof["cognome"])
        )
        
        # Insert professor details
        cur.execute(
            """
            INSERT INTO Insegnanti (id, infoMail, sitoWeb, ricevimento)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, prof["infoMail"], prof["sitoWeb"], prof["ricevimento"])
        )
        
        professor_ids[f"{prof['nome']} {prof['cognome']}"] = user_id
    
    print(f"✅ Inserted {len(professors)} professors")
    
    # Insert some students
    students = [
        {
            "nome": "Mario",
            "cognome": "Rossi",
            "email": "mario.rossi@studenti.uniroma1.it",
            "matricola": 1234567,
            "corso": "Ingegneria Informatica e Automatica"
        },
        # Add more students
    ]
    
    student_ids = {}
    for student in students:
        user_id = str(uuid4())
        # Insert base user
        cur.execute(
            """
            INSERT INTO Utente (id, email, pwd_hash, nome, cognome)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, student["email"], hash_password("temp123"), student["nome"], student["cognome"])
        )
        
        # Insert student details
        cur.execute(
            """
            INSERT INTO Studenti (id, corso_laurea_id, matricola)
            VALUES (%s, %s, %s)
            """,
            (user_id, degree_course_ids[student["corso"]], student["matricola"])
        )
        
        student_ids[f"{student['nome']} {student['cognome']}"] = user_id
    
    print(f"✅ Inserted {len(students)} students")
    return professor_ids, student_ids

def insert_courses(cur, degree_course_ids):
    courses = [
        {
            "nome": "Fondamenti di Informatica",
            "corso_laurea": "Ingegneria Informatica e Automatica",
            "cfu": 12,
            "idoneità": False,
            "prerequisiti": "Nessuno",
            "frequenza_obbligatoria": "No"
        },
        # Add more courses
    ]
    
    course_ids = {}
    for course in courses:
        course_id = str(uuid4())
        cur.execute(
            """
            INSERT INTO Corso 
            (id, id_corso, nome, cfu, idoneità, prerequisiti, frequenza_obbligatoria)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                course_id,
                degree_course_ids[course["corso_laurea"]],
                course["nome"],
                course["cfu"],
                course["idoneità"],
                course["prerequisiti"],
                course["frequenza_obbligatoria"]
            )
        )
        course_ids[course["nome"]] = course_id
    
    print(f"✅ Inserted {len(courses)} courses")
    return course_ids

def insert_course_editions(cur, course_ids, professor_ids):
    editions = [
        {
            "corso": "Fondamenti di Informatica",
            "professore": "Roberto Baldoni",
            "aa": "S1/2023",
            "orario": "Lunedì 14:00-16:00, Mercoledì 14:00-16:00",
            "esonero": True,
            "mod_Esame": "Scritto + Orale"
        },
    ]
    
    edition_ids = {}
    for edition in editions:
        edition_id = course_ids[edition["corso"]]  # Using same ID as course
        cur.execute(
            """
            INSERT INTO EdizioneCorso
            (id, insegnante, data, orario, esonero, mod_Esame)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                edition_id,
                professor_ids[edition["professore"]],
                edition["aa"],
                edition["orario"],
                edition["esonero"],
                edition["mod_Esame"]
            )
        )
        edition_ids[f"{edition['corso']}_{edition['aa']}"] = edition_id
    
    print(f"✅ Inserted {len(editions)} course editions")
    return edition_ids

def main():
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Insert data in the correct order to maintain referential integrity
        dept_ids = insert_departments(cur)
        faculty_ids = insert_faculties(cur, dept_ids)
        degree_course_ids = insert_degree_courses(cur, faculty_ids)
        professor_ids, student_ids = insert_users_and_roles(cur, degree_course_ids)
        course_ids = insert_courses(cur, degree_course_ids)
        edition_ids = insert_course_editions(cur, course_ids, professor_ids)
        
        # Commit all changes
        conn.commit()
        print("✅ All data inserted successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {str(e)}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main() 
from utils import get_connection
from dotenv import load_dotenv
from uuid import uuid4
import bcrypt

load_dotenv()


def run_sql_file(cur, filename):
    with open(filename, "r", encoding="utf-8") as f:
        sql = f.read()
    # Divide le query per ';' e rimuove eventuali spazi vuoti
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    for stmt in statements:
        cur.execute(stmt)

# def normalize_text(val):
#     val = val.strip()
#     return val.capitalize() if val else val

# def hash_password(password: str) -> str:
#     return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# def insert_departments(cur):
#     departments = [
#         "Ingegneria informatica, automatica e gestionale Antonio Ruberti",
#         "Ingegneria civile, edile e ambientale",
#         "Ingegneria strutturale e geotecnica",
#         "Scienze di base e applicate per l'ingegneria",
#         "Ingegneria chimica, materiali e ambiente",
#         "Ingegneria meccanica e aerospaziale"
#     ]
#     dept_ids = {}
#     for dept in departments:
#         dept_id = str(uuid4())
#         cur.execute(
#             "INSERT INTO Dipartimento (id, nome) VALUES (%s, %s) RETURNING id",
#             (dept_id, normalize_text(dept))
#         )
#         dept_ids[dept] = dept_id
#     print(f"✅ Inserted {len(departments)} departments")
#     return dept_ids

# def insert_faculties(cur, dept_ids):
#     faculties = [
#         {
#             "nome": "Ingegneria dell'informazione, informatica e statistica",
#             "dipartimento": "Ingegneria informatica, automatica e gestionale Antonio Ruberti",
#             "presidente": "Prof. Marco Schaerf",
#             "contatti": "presidenza-i3s@uniroma1.it"
#         },
#     ]
#     faculty_ids = {}
#     for faculty in faculties:
#         faculty_id = str(uuid4())
#         cur.execute(
#             "INSERT INTO Facolta (id, dipartimento_id, presidente, nome, contatti) VALUES (%s, %s, %s, %s, %s) RETURNING id",
#             (faculty_id, dept_ids[faculty["dipartimento"]], normalize_text(faculty["presidente"]), normalize_text(faculty["nome"]), faculty["contatti"])
#         )
#         faculty_ids[faculty["nome"]] = faculty_id
#     print(f"✅ Inserted {len(faculties)} faculties")
#     return faculty_ids

# def insert_degree_courses(cur, faculty_ids):
#     courses = [
#         {
#             "nome": "Ingegneria Informatica e Automatica",
#             "facolta": "Ingegneria dell'informazione, informatica e statistica",
#             "descrizione": "Corso di laurea triennale in Ingegneria Informatica e Automatica",
#             "classe": "L-8",
#             "tipologia": "Triennale",
#             "mail_segreteria": "segreteria-i3s@uniroma1.it",
#             "test": True
#         },
#     ]
#     course_ids = {}
#     for course in courses:
#         course_id = str(uuid4())
#         cur.execute(
#             """
#             INSERT INTO Corso_di_Laurea 
#             (id, id_facolta, nome, descrizione, classe, tipologia, mail_segreteria, test) 
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
#             """,
#             (
#                 course_id, 
#                 faculty_ids[course["facolta"]],
#                 normalize_text(course["nome"]),
#                 course["descrizione"].capitalize(),
#                 course["classe"],
#                 normalize_text(course["tipologia"]),
#                 course["mail_segreteria"],
#                 course["test"]
#             )
#         )
#         course_ids[course["nome"]] = course_id
#     print(f"✅ Inserted {len(courses)} degree courses")
#     return course_ids

# def insert_users_and_roles(cur, degree_course_ids):
#     professors = [
#         {
#             "nome": "Roberto",
#             "cognome": "Baldoni",
#             "email": "roberto.baldoni@uniroma1.it",
#             "infoMail": "roberto.baldoni@uniroma1.it",
#             "sitoWeb": "http://www.dis.uniroma1.it/~baldoni/",
#             "ricevimento": "Martedì 14:00-16:00"
#         },
#     ]
#     professor_ids = {}
#     for prof in professors:
#         user_id = str(uuid4())
#         anagrafico_id = str(uuid4())
#         # Utente
#         cur.execute(
#             """
#             INSERT INTO Utente (id, email, pwd_hash, nome, cognome, email_verificata)
#             VALUES (%s, %s, %s, %s, %s, %s)
#             """,
#             (user_id, prof["email"], hash_password("roberto"), normalize_text(prof["nome"]), normalize_text(prof["cognome"]), True)
#         )
#         # Insegnanti_Anagrafici
#         cur.execute(
#             """
#             INSERT INTO Insegnanti_Anagrafici (id, nome, cognome, email, utente_id)
#             VALUES (%s, %s, %s, %s, %s)
#             """,
#             (anagrafico_id, normalize_text(prof["nome"]), normalize_text(prof["cognome"]), prof["email"], user_id)
#         )
#         # Insegnanti_Registrati
#         cur.execute(
#             """
#             INSERT INTO Insegnanti_Registrati (id, anagrafico_id, infoMail, sitoWeb, ricevimento)
#             VALUES (%s, %s, %s, %s, %s)
#             """,
#             (user_id, anagrafico_id, prof["infoMail"], prof["sitoWeb"], prof["ricevimento"])
#         )
#         professor_ids[f"{prof['nome']} {prof['cognome']}"] = anagrafico_id
#     print(f"✅ Inserted {len(professors)} professors")
#     students = [
#         {
#             "nome": "super",
#             "cognome": "user",
#             "email": "superuser@superuser.it",
#             "matricola": 1234567,
#             "corso": "Ingegneria Informatica e Automatica"
#         },
#     ]
#     student_ids = {}
#     for student in students:
#         user_id = str(uuid4())
#         cur.execute(
#             """
#             INSERT INTO Utente (id, email, pwd_hash, nome, cognome, email_verificata)
#             VALUES (%s, %s, %s, %s, %s, %s)
#             """,
#             (user_id, student["email"], hash_password("superuser"), normalize_text(student["nome"]), normalize_text(student["cognome"]), True)
#         )
#         cur.execute(
#             """
#             INSERT INTO Studenti (id, corso_laurea_id, matricola)
#             VALUES (%s, %s, %s)
#             """,
#             (user_id, degree_course_ids[student["corso"]], student["matricola"])
#         )
#         student_ids[f"{student['nome']} {student['cognome']}"] = user_id
#     print(f"✅ Inserted {len(students)} students")
#     return professor_ids, student_ids

# def insert_courses(cur, degree_course_ids):
#     courses = [
#         {
#             "nome": "Fondamenti di comunicazioni e internet",
#             "corso_laurea": "Ingegneria Informatica e Automatica",
#             "cfu": 9,
#             "idoneità": False,
#             "prerequisiti": "Nessuno",
#             "frequenza_obbligatoria": "No"
#         },
#     ]
#     course_ids = {}
#     for course in courses:
#         course_id = str(uuid4())
#         cur.execute(
#             """
#             INSERT INTO Corso 
#             (id, id_corso, nome, cfu, idoneità, prerequisiti, frequenza_obbligatoria)
#             VALUES (%s, %s, %s, %s, %s, %s, %s)
#             """,
#             (
#                 course_id,
#                 degree_course_ids[course["corso_laurea"]],
#                 normalize_text(course["nome"]),
#                 course["cfu"],
#                 course["idoneità"],
#                 course["prerequisiti"].capitalize(),
#                 normalize_text(course["frequenza_obbligatoria"])
#             )
#         )
#         course_ids[course["nome"]] = course_id
#     print(f"✅ Inserted {len(courses)} courses")
#     return course_ids

# def insert_platforms(cur, platforms):
#     for nome in platforms:
#         cur.execute(
#             "INSERT INTO Piattaforme (Nome) VALUES (%s) ON CONFLICT DO NOTHING",
#             (normalize_text(nome),)
#         )
#     print(f"✅ Inserted {len(platforms)} platforms")

# def insert_course_editions(cur, course_ids, professor_ids):
#     editions = [
#         {
#             "corso": "Fondamenti di comunicazioni e internet",
#             "professore": "Marco Polverini",
#             "aa": "S1/2024",
#             "orario": "",
#             "esonero": True,
#             "mod_Esame": "Scritto",
#             "piattaforme": [
#                 {"nome": "Moodle", "codice": ""}
#             ]
#         },
#     ]
#     piattaforme_set = set()
#     for edition in editions:
#         for p in edition["piattaforme"]:
#             piattaforme_set.add(p["nome"])
#     insert_platforms(cur, list(piattaforme_set))

#     edition_ids = {}
#     for edition in editions:
#         edition_id = course_ids[edition["corso"]]
#         cur.execute(
#             """
#             INSERT INTO EdizioneCorso
#             (id, insegnante_anagrafico, data, orario, esonero, mod_Esame)
#             VALUES (%s, %s, %s, %s, %s, %s)
#             """,
#             (
#                 edition_id,
#                 professor_ids[edition["professore"]],
#                 edition["aa"],
#                 edition["orario"],
#                 edition["esonero"],
#                 normalize_text(edition["mod_Esame"])
#             )
#         )
#         edition_ids[f"{edition['corso']}_{edition['aa']}"] = (edition_id, edition["aa"])
#         for p in edition["piattaforme"]:
#             cur.execute(
#                 """
#                 INSERT INTO EdizioneCorso_Piattaforme
#                 (edizione_id, edizione_data, piattaforma_nome, codice)
#                 VALUES (%s, %s, %s, %s)
#                 """,
#                 (edition_id, edition["aa"], normalize_text(p["nome"]), p["codice"])
#             )

#     print(f"✅ Inserted {len(editions)} course editions and platforms")
#     return edition_ids

# def insert_anagrafici_extra(cur):
#     """
#     Inserisce insegnanti anagrafici che NON sono utenti registrati.
#     Ritorna un dizionario { "Nome Cognome": anagrafico_id }
#     """
#     extra = [
#         {
#             "nome": "Marco",
#             "cognome": "Polverini",
#             "email": "marco.polverini@uniroma1.it"
#         },
#         # aggiungi altri se vuoi
#     ]
#     extra_ids = {}
#     for prof in extra:
#         anagrafico_id = str(uuid4())
#         cur.execute(
#             """
#             INSERT INTO Insegnanti_Anagrafici (id, nome, cognome, email, utente_id)
#             VALUES (%s, %s, %s, %s, %s)
#             """,
#             (anagrafico_id, normalize_text(prof["nome"]), normalize_text(prof["cognome"]), prof["email"], None)
#         )
#         extra_ids[f"{prof['nome']} {prof['cognome']}"] = anagrafico_id
#     print(f"✅ Inserted {len(extra)} extra anagrafici")
#     return extra_ids


def main(env):
    conn = get_connection(mode=env)
    cur = conn.cursor()
    try:
        run_sql_file(cur, "insert_data.sql")



        # --- AGGIUNGO QUI IL SUPERUSER ---
        # Aggiungo un superuser per i test o per mettere materiali o cose #
        import bcrypt
        from uuid import uuid4

        # Parametri superuser
        user_id = str(uuid4())
        email = "superuser@superuser.it"
        pwd_hash = bcrypt.hashpw("superpassword".encode(), bcrypt.gensalt()).decode()
        nome = "Super"
        cognome = "User"
        matricola = 1234567

        # Trova un corso di laurea valido (prendi il primo)
        cur.execute("SELECT id FROM Corso_di_Laurea LIMIT 1")
        row = cur.fetchone()
        if not row:
            raise Exception("Nessun corso di laurea trovato per assegnare lo studente superuser!")
        corso_laurea_id = row[0]

        # Inserisci l'utente
        cur.execute(
            "INSERT INTO Utente (id, email, pwd_hash, nome, cognome, email_verificata) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, email, pwd_hash, nome, cognome, True)
        )
        # Inserisci come studente
        cur.execute(
            "INSERT INTO Studenti (id, corso_laurea_id, matricola) VALUES (%s, %s, %s)",
            (user_id, corso_laurea_id, matricola)
        )
        # --- FINE SUPERUSER ---



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
    import sys
    if len(sys.argv) < 2 or sys.argv[1] != "--env" or len(sys.argv) < 3:
        print("❌ Devi specificare l'ambiente: python setup_data.py --env local  oppure  --env neon")
        sys.exit(1)
    env = sys.argv[2].lower()
    main(env)
#!/usr/bin/env python3
"""
Docker-compatible setup_data.py
This script populates the database with sample data and can be run inside Docker.
"""

import os
import psycopg2
import uuid
from datetime import datetime

# Database connection for Docker
DB_CONFIG = {
    'dbname': 'faqbuddy_db',
    'user': 'db_user', 
    'password': 'pwd',
    'host': 'localhost',
    'port': '5433'  # Docker mapped port
}

def get_connection():
    """Get database connection."""
    return psycopg2.connect(**DB_CONFIG)

def insert_sample_data():
    """Insert sample data into the database."""
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        print("📊 Inserting sample data...")
        
        # 1. Insert Dipartimenti
        print("  - Inserting departments...")
        dipartimenti = [
            (str(uuid.uuid4()), "Ingegneria Informatica, Automatica e Gestionale"),
            (str(uuid.uuid4()), "Ingegneria Civile e Ingegneria Informatica")
        ]
        cur.executemany("INSERT INTO dipartimento (id, nome) VALUES (%s, %s)", dipartimenti)
        
        # Get department IDs
        cur.execute("SELECT id FROM dipartimento")
        dept_ids = [row[0] for row in cur.fetchall()]
        
        # 2. Insert Facoltà
        print("  - Inserting faculties...")
        facolta = [
            (str(uuid.uuid4()), dept_ids[0], "Prof. Mario Rossi", "Ingegneria Informatica", "info@ing.uniroma1.it"),
            (str(uuid.uuid4()), dept_ids[1], "Prof. Anna Bianchi", "Ingegneria Civile", "civile@ing.uniroma1.it")
        ]
        cur.executemany("INSERT INTO facolta (id, dipartimento_id, presidente, nome, contatti) VALUES (%s, %s, %s, %s, %s)", facolta)
        
        # Get faculty IDs
        cur.execute("SELECT id FROM facolta")
        faculty_ids = [row[0] for row in cur.fetchall()]
        
        # 3. Insert Corsi di Laurea
        print("  - Inserting degree programs...")
        corsi_laurea = [
            (str(uuid.uuid4()), faculty_ids[0], "Ingegneria Informatica", "Corso di laurea in Ingegneria Informatica", "L-8", "triennale", "segreteria.info@ing.uniroma1.it", "Domanda di laurea online", False),
            (str(uuid.uuid4()), faculty_ids[0], "Ingegneria Informatica e Automatica", "Corso di laurea magistrale in Ingegneria Informatica e Automatica", "LM-32", "magistrale", "segreteria.info@ing.uniroma1.it", "Domanda di laurea online", False)
        ]
        cur.executemany("""
            INSERT INTO corso_di_laurea (id, id_facolta, nome, descrizione, classe, tipologia, mail_segreteria, domanda_laurea, test) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, corsi_laurea)
        
        # Get degree program IDs
        cur.execute("SELECT id FROM corso_di_laurea")
        degree_ids = [row[0] for row in cur.fetchall()]
        
        # 4. Insert Utenti (Professors and Students)
        print("  - Inserting users...")
        utenti = [
            (str(uuid.uuid4()), "prof1@uniroma1.it", "hash123", "Mario", "Rossi"),
            (str(uuid.uuid4()), "prof2@uniroma1.it", "hash456", "Anna", "Bianchi"),
            (str(uuid.uuid4()), "student1@uniroma1.it", "hash789", "Luca", "Verdi"),
            (str(uuid.uuid4()), "student2@uniroma1.it", "hash012", "Sofia", "Neri")
        ]
        cur.executemany("INSERT INTO utente (id, email, pwd_hash, nome, cognome) VALUES (%s, %s, %s, %s, %s)", utenti)
        
        # Get user IDs
        cur.execute("SELECT id FROM utente")
        user_ids = [row[0] for row in cur.fetchall()]
        
        # 5. Insert Insegnanti
        print("  - Inserting professors...")
        insegnanti = [
            (user_ids[0], "prof1@uniroma1.it", "https://www.uniroma1.it/prof1", "PhD in Computer Science", "Martedì 14:00-16:00"),
            (user_ids[1], "prof2@uniroma1.it", "https://www.uniroma1.it/prof2", "PhD in Engineering", "Giovedì 10:00-12:00")
        ]
        cur.executemany("INSERT INTO insegnanti (id, infoMail, sitoWeb, cv, ricevimento) VALUES (%s, %s, %s, %s, %s)", insegnanti)
        
        # 6. Insert Studenti
        print("  - Inserting students...")
        studenti = [
            (user_ids[2], degree_ids[0], 12345),
            (user_ids[3], degree_ids[0], 12346)
        ]
        cur.executemany("INSERT INTO studenti (id, corso_laurea_id, matricola) VALUES (%s, %s, %s)", studenti)
        
        # 7. Insert Corsi
        print("  - Inserting courses...")
        corsi = [
            (str(uuid.uuid4()), degree_ids[0], "Programmazione I", 9, True, "Nessuno", "Obbligatoria"),
            (str(uuid.uuid4()), degree_ids[0], "Algoritmi e Strutture Dati", 9, True, "Programmazione I", "Obbligatoria"),
            (str(uuid.uuid4()), degree_ids[0], "Basi di Dati", 6, True, "Programmazione I", "Obbligatoria")
        ]
        cur.executemany("""
            INSERT INTO corso (id, id_corso, nome, cfu, idoneità, prerequisiti, frequenza_obbligatoria) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, corsi)
        
        # Get course IDs
        cur.execute("SELECT id FROM corso")
        course_ids = [row[0] for row in cur.fetchall()]
        
        # 8. Insert Piattaforme
        print("  - Inserting platforms...")
        piattaforme = [
            ("Teams", "TEAMS001"),
            ("Zoom", "ZOOM001"),
            ("Google Meet", "GMEET001")
        ]
        cur.executemany("INSERT INTO piattaforme (Nome, Codice) VALUES (%s, %s)", piattaforme)
        
        # 9. Insert EdizioneCorso
        print("  - Inserting course editions...")
        edizioni = [
            (course_ids[0], user_ids[0], "Teams", "S1/2024", "Lunedì 9:00-11:00", False, "Scritto + Orale"),
            (course_ids[1], user_ids[0], "Zoom", "S1/2024", "Martedì 14:00-16:00", False, "Scritto"),
            (course_ids[2], user_ids[1], "Google Meet", "S2/2024", "Giovedì 10:00-12:00", True, "Progetto + Orale")
        ]
        cur.executemany("""
            INSERT INTO edizionecorso (id, insegnante, piattaforma, data, orario, esonero, mod_Esame) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, edizioni)
        
        # Get edition IDs
        cur.execute("SELECT id FROM edizionecorso")
        edition_ids = [row[0] for row in cur.fetchall()]
        
        # 10. Insert Corsi_seguiti
        print("  - Inserting course enrollments...")
        corsi_seguiti = [
            (user_ids[2], edition_ids[0], "attivo", None),
            (user_ids[2], edition_ids[1], "completato", 28),
            (user_ids[3], edition_ids[0], "attivo", None),
            (user_ids[3], edition_ids[2], "attivo", None)
        ]
        cur.executemany("""
            INSERT INTO corsi_seguiti (student_id, edition_id, stato, voto) 
            VALUES (%s, %s, %s, %s)
        """, corsi_seguiti)
        
        # 11. Insert Materiale_Didattico
        print("  - Inserting teaching materials...")
        materiali = [
            (str(uuid.uuid4()), user_ids[0], course_ids[0], "/materials/prog1_slides.pdf", "slides", True, "01/01/2024", 4.5, 10),
            (str(uuid.uuid4()), user_ids[0], course_ids[1], "/materials/algo_exercises.pdf", "exercises", True, "15/01/2024", 4.2, 8),
            (str(uuid.uuid4()), user_ids[1], course_ids[2], "/materials/db_notes.pdf", "notes", False, "01/02/2024", None, 0)
        ]
        cur.executemany("""
            INSERT INTO materiale_didattico (id, Utente_id, course_id, path_file, tipo, verificato, data_caricamento, rating_medio, numero_voti) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, materiali)
        
        # Get material IDs
        cur.execute("SELECT id FROM materiale_didattico")
        material_ids = [row[0] for row in cur.fetchall()]
        
        # 12. Insert Valutazione
        print("  - Inserting material ratings...")
        valutazioni = [
            (user_ids[2], material_ids[0], 5, "Ottimo materiale!", "15/01/2024"),
            (user_ids[3], material_ids[0], 4, "Molto utile", "16/01/2024"),
            (user_ids[2], material_ids[1], 4, "Esercizi interessanti", "20/01/2024")
        ]
        cur.executemany("""
            INSERT INTO valutazione (student_id, id_materiale, voto, commento, data) 
            VALUES (%s, %s, %s, %s, %s)
        """, valutazioni)
        
        # 13. Insert Review
        print("  - Inserting course reviews...")
        reviews = [
            (str(uuid.uuid4()), user_ids[2], edition_ids[0], "Corso molto interessante e ben strutturato", 5),
            (str(uuid.uuid4()), user_ids[3], edition_ids[0], "Docente molto preparato", 4),
            (str(uuid.uuid4()), user_ids[2], edition_ids[1], "Corso impegnativo ma formativo", 4)
        ]
        cur.executemany("""
            INSERT INTO review (id, student_id, edition_id, descrizione, voto) 
            VALUES (%s, %s, %s, %s, %s)
        """, reviews)
        
        # 14. Insert Tesi
        print("  - Inserting theses...")
        tesi = [
            (str(uuid.uuid4()), user_ids[2], degree_ids[0], "Sviluppo di un sistema RAG per FAQ universitarie", "/theses/tesi_luca_verdi.pdf"),
            (str(uuid.uuid4()), user_ids[3], degree_ids[0], "Analisi di algoritmi di machine learning", "/theses/tesi_sofia_neri.pdf")
        ]
        cur.executemany("""
            INSERT INTO tesi (id, student_id, corso_laurea_id, titolo, file) 
            VALUES (%s, %s, %s, %s, %s)
        """, tesi)
        
        # Commit all changes
        conn.commit()
        print("✅ Sample data inserted successfully!")
        
        # Print summary
        print("\n📊 Data Summary:")
        cur.execute("SELECT COUNT(*) FROM utente")
        print(f"  - Users: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM dipartimento")
        print(f"  - Departments: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM facolta")
        print(f"  - Faculties: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM corso_di_laurea")
        print(f"  - Degree Programs: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM corso")
        print(f"  - Courses: {cur.fetchone()[0]}")
        cur.execute("SELECT COUNT(*) FROM materiale_didattico")
        print(f"  - Teaching Materials: {cur.fetchone()[0]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting sample data: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    insert_sample_data() 
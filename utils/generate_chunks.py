from utils.db import get_connection
import os
from dotenv import load_dotenv
from typing import List, Dict
from uuid import UUID
import json

load_dotenv()

class ChunkGenerator:
    def __init__(self):
        self.conn = get_connection()
        self.cur = self.conn.cursor()
        self._cache = {}

    def __del__(self):
        self.cur.close()
        self.conn.close()

    def _cache_query(self, key: str, query: str) -> List[tuple]:
        """Cache query results for reuse"""
        if key not in self._cache:
            self.cur.execute(query)
            self._cache[key] = self.cur.fetchall()
        return self._cache[key]

    def get_department_chunks(self) -> List[str]:
        rows = self._cache_query('departments', "SELECT id, nome FROM Dipartimento")
        return [
            f"Dipartimento: {nome}\nID: {id}"
            for id, nome in rows
        ]

    def get_faculty_chunks(self) -> List[str]:
        query = """
            SELECT f.id, f.nome, f.presidente, f.contatti, d.nome as dept_name 
            FROM Facolta f
            JOIN Dipartimento d ON f.dipartimento_id = d.id
        """
        rows = self._cache_query('faculties', query)
        return [
            f"Facoltà: {nome}\nDipartimento: {dept_name}\nPresidente: {presidente}\nContatti: {contatti}\nID: {id}"
            for id, nome, presidente, contatti, dept_name in rows
        ]

    def get_degree_course_chunks(self) -> List[str]:
        query = """
            SELECT c.id, c.nome, c.descrizione, c.classe, c.tipologia, 
                   c.mail_segreteria, f.nome as faculty_name
            FROM Corso_di_Laurea c
            JOIN Facolta f ON c.id_facolta = f.id
        """
        rows = self._cache_query('degree_courses', query)
        return [
            f"Corso di Laurea: {nome}\nFacoltà: {faculty_name}\nClasse: {classe}\n"
            f"Tipologia: {tipologia}\nDescrizione: {descrizione or 'N/A'}\n"
            f"Mail Segreteria: {mail_segreteria or 'N/A'}\nID: {id}"
            for id, nome, descrizione, classe, tipologia, mail_segreteria, faculty_name in rows
        ]

    def get_course_chunks(self) -> List[str]:
        query = """
            SELECT c.id, c.nome, c.cfu, c.idoneità, c.prerequisiti, 
                   c.frequenza_obbligatoria, cdl.nome as degree_name
            FROM Corso c
            JOIN Corso_di_Laurea cdl ON c.id_corso = cdl.id
        """
        rows = self._cache_query('courses', query)
        return [
            f"Corso: {nome}\nCorso di Laurea: {degree_name}\nCFU: {cfu}\n"
            f"Idoneità: {'Sì' if idoneita else 'No'}\n"
            f"Prerequisiti: {prerequisiti or 'Nessuno'}\n"
            f"Frequenza Obbligatoria: {freq_obb or 'Non specificata'}\nID: {id}"
            for id, nome, cfu, idoneita, prerequisiti, freq_obb, degree_name in rows
        ]

    def get_course_edition_chunks(self) -> List[str]:
        query = """
            SELECT ec.id, ec.aa, ec.orario, ec.esonero, ec.mod_Esame,
                   c.nome as course_name, u.nome as prof_nome, u.cognome as prof_cognome
            FROM EdizioneCorso ec
            JOIN Corso c ON ec.id = c.id
            JOIN Insegnanti i ON ec.insegnante = i.id
            JOIN Utente u ON i.id = u.id
        """
        rows = self._cache_query('course_editions', query)
        return [
            f"Edizione Corso: {course_name}\nProfessore: {prof_nome} {prof_cognome}\n"
            f"Anno Accademico: {aa}\nOrario: {orario or 'Non specificato'}\n"
            f"Esonero: {'Sì' if esonero else 'No'}\nModalità Esame: {mod_esame}\nID: {id}"
            for id, aa, orario, esonero, mod_esame, course_name, prof_nome, prof_cognome in rows
        ]

    def get_material_chunks(self) -> List[str]:
        query = """
            SELECT m.id, m.path_file, m.tipo, m.verificato, m.data_caricamento,
                   m.rating_medio, m.numero_voti, c.nome as course_name,
                   u.nome as uploader_nome, u.cognome as uploader_cognome
            FROM Materiale_Didattico m
            JOIN Corso c ON m.course_id = c.id
            JOIN Utente u ON m.Utente_id = u.id
        """
        rows = self._cache_query('materials', query)
        return [
            f"Materiale Didattico per: {course_name}\n"
            f"Caricato da: {uploader_nome} {uploader_cognome}\n"
            f"Tipo: {tipo or 'Non specificato'}\nVerificato: {'Sì' if verificato else 'No'}\n"
            f"Data: {data_caricamento}\nRating: {rating_medio or 'N/A'} ({numero_voti or 0} voti)\n"
            f"File: {path_file}\nID: {id}"
            for id, path_file, tipo, verificato, data_caricamento, rating_medio, numero_voti, 
                course_name, uploader_nome, uploader_cognome in rows
        ]

    def get_review_chunks(self) -> List[str]:
        query = """
            SELECT r.id, r.descrizione, r.voto, c.nome as course_name,
                   u.nome as student_nome, u.cognome as student_cognome
            FROM Review r
            JOIN EdizioneCorso ec ON r.edition_id = ec.id
            JOIN Corso c ON ec.id = c.id
            JOIN Studenti s ON r.student_id = s.id
            JOIN Utente u ON s.id = u.id
        """
        rows = self._cache_query('reviews', query)
        return [
            f"Review per: {course_name}\nStudente: {student_nome} {student_cognome}\n"
            f"Voto: {voto}/5\nDescrizione: {descrizione or 'Nessuna descrizione'}\nID: {id}"
            for id, descrizione, voto, course_name, student_nome, student_cognome in rows
        ]

def get_chunks() -> List[str]:
    """Main function to get all chunks with efficient caching"""
    generator = ChunkGenerator()
    all_chunks = []
    
    # Get chunks from all entities
    all_chunks.extend(generator.get_department_chunks())
    all_chunks.extend(generator.get_faculty_chunks())
    all_chunks.extend(generator.get_degree_course_chunks())
    all_chunks.extend(generator.get_course_chunks())
    all_chunks.extend(generator.get_course_edition_chunks())
    all_chunks.extend(generator.get_material_chunks())
    all_chunks.extend(generator.get_review_chunks())
    
    return all_chunks
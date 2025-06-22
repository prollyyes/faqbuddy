from src.text_2_SQL.db_utils import get_db_connection
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class ChunkGenerator:
    def __init__(self):
        self.conn = get_db_connection()
        self.cur = self.conn.cursor()

    def __del__(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def _execute_query(self, query: str) -> List[tuple]:
        """Execute a query and fetch all results."""
        self.cur.execute(query)
        return self.cur.fetchall()

    def get_department_chunks(self) -> List[Dict[str, Any]]:
        rows = self._execute_query("SELECT id, nome FROM dipartimento")
        return [
            {
                "id": f"dipartimento_{id}",
                "text": f"Dipartimento: {nome}",
                "metadata": {"table_name": "dipartimento", "primary_key": id}
            }
            for id, nome in rows
        ]

    def get_faculty_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT f.id, f.nome, f.presidente, f.contatti, d.nome as dept_name 
            FROM facolta f
            JOIN dipartimento d ON f.dipartimento_id = d.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"facolta_{id}",
                "text": f"Facoltà: {nome}, afferente al Dipartimento di {dept_name}. Presidente: {presidente}, Contatti: {contatti}.",
                "metadata": {"table_name": "facolta", "primary_key": id}
            }
            for id, nome, presidente, contatti, dept_name in rows
        ]

    def get_degree_course_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT c.id, c.nome, c.descrizione, c.classe, c.tipologia, 
                   c.mail_segreteria, f.nome as faculty_name
            FROM corso_di_laurea c
            JOIN facolta f ON c.id_facolta = f.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"corso_di_laurea_{id}",
                "text": f"Corso di Laurea in {nome} (Classe {classe}, {tipologia}), offerto dalla Facoltà di {faculty_name}. "
                        f"Descrizione: {descrizione or 'Non disponibile'}. Email segreteria: {mail_segreteria or 'Non disponibile'}.",
                "metadata": {"table_name": "corso_di_laurea", "primary_key": id}
            }
            for id, nome, descrizione, classe, tipologia, mail_segreteria, faculty_name in rows
        ]
    
    def get_course_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT c.id, c.nome, c.cfu, c.idoneità, c.prerequisiti, 
                   c.frequenza_obbligatoria, cdl.nome as degree_name
            FROM corso c
            JOIN corso_di_laurea cdl ON c.id_corso = cdl.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"corso_{id}",
                "text": f"Corso: {nome}, parte del Corso di Laurea in {degree_name}. "
                        f"CFU: {cfu}. Prerequisiti: {prerequisiti or 'Nessuno'}. "
                        f"Frequenza Obbligatoria: {frequenza_obbligatoria or 'Non specificato'}.",
                "metadata": {"table_name": "corso", "primary_key": id}
            }
            for id, nome, cfu, idoneita, prerequisiti, frequenza_obbligatoria, degree_name in rows
        ]

    def get_course_edition_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT ec.id, ec.data, ec.mod_esame, c.nome as course_name, 
                   u.nome as prof_nome, u.cognome as prof_cognome
            FROM edizionecorso ec
            JOIN corso c ON ec.id = c.id
            JOIN insegnanti i ON ec.insegnante = i.id
            JOIN utente u ON i.id = u.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"edizione_corso_{id}",
                "text": f"Edizione del corso di {course_name} per il periodo '{data}'. "
                        f"Docente: {prof_nome} {prof_cognome}. Modalità d'esame: {mod_esame}.",
                "metadata": {"table_name": "edizionecorso", "primary_key": id}
            }
            for id, data, mod_esame, course_name, prof_nome, prof_cognome in rows
        ]

    def get_material_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT m.id, m.path_file, m.tipo, m.verificato, m.data_caricamento,
                   c.nome as course_name, u.nome as uploader_nome, u.cognome as uploader_cognome
            FROM materiale_didattico m
            JOIN corso c ON m.course_id = c.id
            JOIN utente u ON m.utente_id = u.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"materiale_didattico_{id}",
                "text": f"Materiale didattico per il corso di {course_name} (tipo: {tipo}), caricato da {uploader_nome} {uploader_cognome} "
                        f"in data {data_caricamento}. Il file si trova in {path_file}. Verificato: {'Sì' if verificato else 'No'}",
                "metadata": {"table_name": "materiale_didattico", "primary_key": id}
            }
            for id, path_file, tipo, verificato, data_caricamento, course_name, uploader_nome, uploader_cognome in rows
        ]

    def get_review_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT r.id, r.descrizione, r.voto, c.nome as course_name,
                   u.nome as student_nome, u.cognome as student_cognome
            FROM review r
            JOIN edizionecorso ec ON r.edition_id = ec.id
            JOIN corso c ON ec.id = c.id
            JOIN studenti s ON r.student_id = s.id
            JOIN utente u ON s.id = u.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"review_{id}",
                "text": f"Recensione di {student_nome} {student_cognome} per il corso di {course_name}. "
                        f"Voto: {voto}/5. Commento: {descrizione or 'Nessun commento'}.",
                "metadata": {"table_name": "review", "primary_key": id}
            }
            for id, descrizione, voto, course_name, student_nome, student_cognome in rows
        ]

def get_chunks() -> List[Dict[str, Any]]:
    generator = ChunkGenerator()
    all_chunks = []
    
    all_chunks.extend(generator.get_department_chunks())
    all_chunks.extend(generator.get_faculty_chunks())
    all_chunks.extend(generator.get_degree_course_chunks())
    all_chunks.extend(generator.get_course_chunks())
    all_chunks.extend(generator.get_course_edition_chunks())
    all_chunks.extend(generator.get_material_chunks())
    all_chunks.extend(generator.get_review_chunks())
    
    return all_chunks
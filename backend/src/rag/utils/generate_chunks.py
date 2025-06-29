from src.utils.db_utils import get_connection, MODE
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class ChunkGenerator:
    def __init__(self):
        self.conn = get_connection(mode=MODE)
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
                        f"Frequenza Obbligatoria: {frequenza_obbligatoria or 'Non specificato'}."
                        f"Idoneità: {idoneita or 'Non specificato'}.",
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
                   c.nome as course_name
            FROM materiale_didattico m
            JOIN corso c ON m.course_id = c.id
    
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"materiale_didattico_{id}",
                "text": f"Materiale didattico per il corso di {course_name} (tipo: {tipo}), caricato da un utente, per privacy non viene mostrato il nome e cognome."
                        f"in data {data_caricamento}. Il file si trova in {path_file}. Verificato: {'Sì' if verificato else 'No'}",
                "metadata": {"table_name": "materiale_didattico", "primary_key": id}
            }
            for id, path_file, tipo, verificato, data_caricamento, course_name in rows
        ]

    def get_review_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT r.id, r.descrizione, r.voto, c.nome as course_name
            FROM review r
            JOIN edizionecorso ec ON r.edition_id = ec.id AND r.edition_data = ec.data
            JOIN corso c ON ec.id = c.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"review_{id}",
                "text": f"Recensione di uno studente per il corso di {course_name}. "
                        f"Voto: {voto}/5. Commento: {descrizione or 'Nessun commento'}.",
                "metadata": {"table_name": "review", "primary_key": id}
            }
            for id, descrizione, voto, course_name in rows
        ]
    
    def get_valutazione_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT v.voto, v.commento, v.data, s.id as student_id, m.id as materiale_id
            FROM valutazione v JOIN materiale_didattico m ON v.id_materiale = m.id
            JOIN studenti s ON s.id = v.student_id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"review_{student_id}_{materiale_id}",
                "text": f"Valutazione di uno studente per il materiale didattico {materiale_id}."
                        f"Voto: {voto}/5. Commento: {commento or 'Nessun commento'}."
                        f"fatta in data: {data}.",
                "metadata": {
                    "table_name": "review",
                    "primary_key": [student_id, materiale_id]
                }
            }
            for voto, commento, data, student_id, materiale_id in rows
        ]
    def get_piattaforma_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT p.nome, ecp.codice, ecp.edizione_id
            FROM piattaforme p 
            LEFT JOIN edizionecorso_piattaforme ecp ON p.nome = ecp.piattaforma_nome
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"piattaforma_{nome}",
                "text": f"Piattaforma: {nome}, con codice: {codice or 'Nessun codice disponibile'}. "
                        f"Edizione: {edizione_id or 'Non associata'}.",
                "metadata": {"table_name": "piattaforme", "primary_key": nome}
            }
            for nome, codice, edizione_id in rows
        ]
    
    def get_insegnante_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT i.id, i.infoMail as email, u.nome, u.cognome, i.sitoweb, i.cv, i.ricevimento
            FROM insegnanti i JOIN utente u ON i.id = u.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"insegnante_{id}",
                "text": f"Insegnante: {nome} {cognome}, raggiungibile all'email: {email}"
                        f"Ha il seguente CV: {cv} e ricevimento: {ricevimento}. Il sito web dell'insegnante è: {sitoweb}.",
                "metadata": {"table_name": "insegnanti", "primary_key": id}
            }
            for id, email, nome, cognome, sitoweb, cv, ricevimento in rows
        ]
    
    def get_thesis_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT t.id, cdl.nome as corso_laurea_nome, s.matricola as studente_matricola, t.file
            FROM tesi t JOIN corso_di_laurea cdl ON t.corso_laurea_id = cdl.id JOIN studenti s ON t.student_id = s.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"tesi_{id}",
                "text": f"Tesi, dello studente {studente_matricola} del corso di laurea {corso_laurea_nome}."
                        f"Il file si trova in {file}.",
                "metadata": {"table_name": "tesi", "primary_key": id}
            }
            for id, corso_laurea_nome, studente_matricola, file in rows
        ]
    
    def get_chunks(self) -> List[Dict[str, Any]]:
        all_chunks = []
        
        all_chunks.extend(self.get_department_chunks())
        all_chunks.extend(self.get_faculty_chunks())
        all_chunks.extend(self.get_degree_course_chunks())
        all_chunks.extend(self.get_course_chunks())
        all_chunks.extend(self.get_course_edition_chunks())
        all_chunks.extend(self.get_material_chunks())
        all_chunks.extend(self.get_review_chunks())
        all_chunks.extend(self.get_valutazione_chunks())
        all_chunks.extend(self.get_piattaforma_chunks())
        all_chunks.extend(self.get_insegnante_chunks())
        all_chunks.extend(self.get_thesis_chunks()) 
        return all_chunks
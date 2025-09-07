from utils.db_utils import get_connection, MODE
from dotenv import load_dotenv
from typing import List, Dict, Any

load_dotenv()

class ChunkGenerator:
    def __init__(self):
        self.conn = get_connection(MODE)  # Use the main app's database connection
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
        rows = self._execute_query("SELECT id, nome FROM Dipartimento")
        return [
            {
                "id": f"dipartimento_{id}",
                "text": f"Dipartimento: {nome}",
                "metadata": {"table_name": "Dipartimento", "primary_key": id}
            }
            for id, nome in rows
        ]

    def get_faculty_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT f.id, f.nome, f.presidente, f.contatti, d.nome as dept_name 
            FROM Facolta f
            JOIN Dipartimento d ON f.dipartimento_id = d.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"facolta_{id}",
                "text": f"Facoltà: {nome}, afferente al Dipartimento di {dept_name}. Presidente: {presidente}, Contatti: {contatti}.",
                "metadata": {"table_name": "Facolta", "primary_key": id}
            }
            for id, nome, presidente, contatti, dept_name in rows
        ]

    def get_degree_course_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT c.id, c.nome, c.descrizione, c.classe, c.tipologia, 
                   c.mail_segreteria, f.nome as faculty_name
            FROM Corso_di_Laurea c
            JOIN Facolta f ON c.id_facolta = f.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"corso_di_laurea_{id}",
                "text": f"Corso di Laurea in {nome} (Classe {classe}, {tipologia}), offerto dalla Facoltà di {faculty_name}. "
                        f"Descrizione: {descrizione or 'Non disponibile'}. Email segreteria: {mail_segreteria or 'Non disponibile'}.",
                "metadata": {"table_name": "Corso_di_Laurea", "primary_key": id}
            }
            for id, nome, descrizione, classe, tipologia, mail_segreteria, faculty_name in rows
        ]
    
    def get_course_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT c.id, c.nome, c.cfu, c.idoneità, c.prerequisiti, 
                   c.frequenza_obbligatoria, cdl.nome as degree_name
            FROM Corso c
            JOIN Corso_di_Laurea cdl ON c.id_corso = cdl.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"corso_{id}",
                "text": f"Corso: {nome}, parte del Corso di Laurea in {degree_name}. "
                        f"CFU: {cfu}. Prerequisiti: {prerequisiti or 'Nessuno'}. "
                        f"Frequenza Obbligatoria: {frequenza_obbligatoria or 'Non specificato'}."
                        f"Idoneità: {idoneita or 'Non specificato'}.",
                "metadata": {"table_name": "Corso", "primary_key": id}
            }
            for id, nome, cfu, idoneita, prerequisiti, frequenza_obbligatoria, degree_name in rows
        ]

    def get_course_edition_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT ec.id, ec.data, ec.mod_Esame, c.nome as course_name, 
                   ia.nome as prof_nome, ia.cognome as prof_cognome, p.Nome as piattaforma
            FROM EdizioneCorso ec
            JOIN Corso c ON ec.id = c.id
            JOIN Insegnanti_Anagrafici ia ON ec.insegnante_anagrafico = ia.id
            LEFT JOIN EdizioneCorso_Piattaforme ecp ON ec.id = ecp.edizione_id AND ec.data = ecp.edizione_data
            LEFT JOIN Piattaforme p ON ecp.piattaforma_nome = p.Nome
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"edizione_corso_{id}",
                "text": f"Edizione del corso di {course_name} per il periodo '{data}'. "
                        f"Docente: {prof_nome} {prof_cognome}. Modalità d'esame: {mod_Esame}. "
                        f"Piattaforma: {piattaforma or 'Non specificata'}.",
                "metadata": {"table_name": "EdizioneCorso", "primary_key": id}
            }
            for id, data, mod_Esame, course_name, prof_nome, prof_cognome, piattaforma in rows
        ]

    def get_material_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT m.id, m.path_file, m.tipo, m.verificato, m.data_caricamento,
                   c.nome as course_name
            FROM Materiale_Didattico m
            JOIN Corso c ON m.edition_id = c.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"materiale_didattico_{id}",
                "text": f"Materiale didattico per il corso di {course_name} (tipo: {tipo}), caricato da un utente, per privacy non viene mostrato il nome e cognome."
                        f"in data {data_caricamento}. Il file si trova in {path_file}. Verificato: {'Sì' if verificato else 'No'}",
                "metadata": {"table_name": "Materiale_Didattico", "primary_key": id}
            }
            for id, path_file, tipo, verificato, data_caricamento, course_name in rows
        ]

    def get_review_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT r.id, r.descrizione, r.voto, c.nome as course_name
            FROM Review r
            JOIN EdizioneCorso ec ON r.edition_id = ec.id AND r.edition_data = ec.data
            JOIN Corso c ON ec.id = c.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"review_{id}",
                "text": f"Recensione di uno studente per il corso di {course_name}. "
                        f"Voto: {voto}/5. Commento: {descrizione or 'Nessun commento'}.",
                "metadata": {"table_name": "Review", "primary_key": id}
            }
            for id, descrizione, voto, course_name in rows
        ]
    
    def get_valutazione_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT v.voto, v.commento, v.data, s.id as student_id, m.id as materiale_id
            FROM Valutazione v 
            JOIN Materiale_Didattico m ON v.id_materiale = m.id
            JOIN Studenti s ON s.id = v.student_id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"valutazione_{student_id}_{materiale_id}",
                "text": f"Valutazione di uno studente per il materiale didattico {materiale_id}."
                        f"Voto: {voto}/5. Commento: {commento or 'Nessun commento'}."
                        f"fatta in data: {data}.",
                "metadata": {
                    "table_name": "Valutazione",
                    "primary_key": [student_id, materiale_id]
                }
            }
            for voto, commento, data, student_id, materiale_id in rows
        ]
    
    def get_piattaforma_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT p.Nome, ecp.codice, ecp.edizione_id
            FROM Piattaforme p 
            JOIN EdizioneCorso_Piattaforme ecp ON p.Nome = ecp.piattaforma_nome
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"piattaforma_{nome}",
                "text": f"Piattaforma: {nome}, con codice: {codice or 'Nessun codice disponibile'}. "
                        f"Edizione: {edizione_id}.",
                "metadata": {"table_name": "Piattaforme", "primary_key": nome}
            }
            for nome, codice, edizione_id in rows
        ]
    
    def get_insegnante_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT ia.id, ia.email, ia.nome, ia.cognome, ir.sitoWeb, ir.cv, ir.ricevimento
            FROM Insegnanti_Anagrafici ia
            LEFT JOIN Insegnanti_Registrati ir ON ia.utente_id = ir.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"insegnante_{id}",
                "text": f"Insegnante: {nome} {cognome}, raggiungibile all'email: {email or 'Non disponibile'}"
                        f"Ha il seguente CV: {cv or 'Non disponibile'} e ricevimento: {ricevimento or 'Non specificato'}. "
                        f"Il sito web dell'insegnante è: {sitoWeb or 'Non disponibile'}.",
                "metadata": {"table_name": "Insegnanti_Anagrafici", "primary_key": id}
            }
            for id, email, nome, cognome, sitoWeb, cv, ricevimento in rows
        ]
    
    def get_thesis_chunks(self) -> List[Dict[str, Any]]:
        query = """
            SELECT t.id, t.titolo, cdl.nome as corso_laurea_nome, s.matricola as studente_matricola, t.file
            FROM Tesi t
            JOIN Corso_di_Laurea cdl ON t.corso_laurea_id = cdl.id
            JOIN Studenti s ON t.student_id = s.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": f"tesi_{id}",
                "text": f"Tesi di laurea: {titolo}, del Corso di Laurea in {corso_laurea_nome}. "
                        f"Studente con matricola: {studente_matricola}. File: {file}.",
                "metadata": {"table_name": "Tesi", "primary_key": id}
            }
            for id, titolo, corso_laurea_nome, studente_matricola, file in rows
        ]

    def get_chunks(self) -> List[Dict[str, Any]]:
        """Generate all chunks from the database."""
        chunks = []
        
        try:
            chunks.extend(self.get_department_chunks())
            chunks.extend(self.get_faculty_chunks())
            chunks.extend(self.get_degree_course_chunks())
            chunks.extend(self.get_course_chunks())
            chunks.extend(self.get_course_edition_chunks())
            chunks.extend(self.get_material_chunks())
            chunks.extend(self.get_review_chunks())
            chunks.extend(self.get_valutazione_chunks())
            chunks.extend(self.get_piattaforma_chunks())
            chunks.extend(self.get_insegnante_chunks())
            chunks.extend(self.get_thesis_chunks())
            
            print(f"✅ Generated {len(chunks)} chunks from database")
            return chunks
            
        except Exception as e:
            print(f"❌ Error generating chunks: {e}")
            return []
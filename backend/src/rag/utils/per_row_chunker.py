"""
Per-Row Chunker for Vector Database
===================================

This module implements the new approach of upserting one vector per semantic row,
keeping only a node-ID (and optional coarse filters) as metadata, and letting an
automatically-generated graph hold every relationship.

Features:
- One vector per database row
- Minimal metadata (node-ID + optional filters)
- Natural language representation of each row
- Prepared for graph-based relationship handling
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from ...utils.db_utils import get_connection, MODE
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import uuid

load_dotenv()

class PerRowChunker:
    """
    Chunker that creates one vector per database row with minimal metadata.
    
    Each row is represented as a natural language description with only
    the essential metadata needed for graph relationships.
    """
    
    def __init__(self):
        self.conn = get_connection(MODE)
        self.cur = self.conn.cursor()
        
        # Node type prefixes for graph relationships
        self.node_types = {
            'Dipartimento': 'dept',
            'Facolta': 'faculty', 
            'Corso_di_Laurea': 'degree',
            'Corso': 'course',
            'EdizioneCorso': 'edition',
            'Insegnanti_Anagrafici': 'professor',
            'Insegnanti_Registrati': 'professor_reg',
            'Materiale_Didattico': 'material',
            'Review': 'review',
            'Valutazione': 'rating',
            'Piattaforme': 'platform',
            'Tesi': 'thesis',
            'Studenti': 'student',
            'Utente': 'user'
        }

    def __del__(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()

    def _execute_query(self, query: str) -> List[tuple]:
        """Execute a query and fetch all results."""
        self.cur.execute(query)
        return self.cur.fetchall()

    def _get_column_names(self, cursor) -> List[str]:
        """Get column names from cursor description."""
        return [desc[0] for desc in cursor.description]

    def _create_node_id(self, table_name: str, primary_key: str) -> str:
        """Create a unique node ID for graph relationships."""
        node_type = self.node_types.get(table_name, table_name.lower())
        return f"{node_type}_{primary_key}"

    def _create_natural_language_text(self, table_name: str, row_data: Dict[str, Any]) -> str:
        """Create natural language representation of a row."""
        
        if table_name == 'Dipartimento':
            return f"Dipartimento di {row_data['nome']}"
            
        elif table_name == 'Facolta':
            return f"Facoltà di {row_data['nome']}, presieduta da {row_data['presidente']}. Contatti: {row_data['contatti']}"
            
        elif table_name == 'Corso_di_Laurea':
            return f"Corso di Laurea in {row_data['nome']} (Classe {row_data['classe']}, {row_data['tipologia']}). {row_data.get('descrizione', '')}"
            
        elif table_name == 'Corso':
            return f"Corso di {row_data['nome']} ({row_data['cfu']} CFU). Prerequisiti: {row_data.get('prerequisiti', 'Nessuno')}. Frequenza: {row_data.get('frequenza_obbligatoria', 'Non specificato')}"
            
        elif table_name == 'EdizioneCorso':
            return f"Edizione del corso di {row_data['course_name']} per il periodo {row_data['data']}. Docente: {row_data['prof_nome']} {row_data['prof_cognome']}. Modalità d'esame: {row_data['mod_Esame']}"
            
        elif table_name == 'Insegnanti_Anagrafici':
            return f"Docente {row_data['nome']} {row_data['cognome']}, contattabile all'email {row_data.get('email', 'Non disponibile')}"
            
        elif table_name == 'Insegnanti_Registrati':
            return f"Sito web: {row_data.get('sitoWeb', 'Non disponibile')}. CV: {row_data.get('cv', 'Non disponibile')}. Ricevimento: {row_data.get('ricevimento', 'Non specificato')}"
            
        elif table_name == 'Materiale_Didattico':
            return f"Materiale didattico di tipo {row_data.get('tipo', 'Non specificato')}, caricato il {row_data['data_caricamento']}. Verificato: {'Sì' if row_data['verificato'] else 'No'}"
            
        elif table_name == 'Review':
            return f"Recensione con voto {row_data['voto']}/5: {row_data.get('descrizione', 'Nessun commento')}"
            
        elif table_name == 'Valutazione':
            return f"Valutazione con voto {row_data['voto']}/5. Commento: {row_data.get('commento', 'Nessun commento')}. Data: {row_data['data']}"
            
        elif table_name == 'Piattaforme':
            return f"Piattaforma {row_data['Nome']}"
            
        elif table_name == 'Tesi':
            return f"Tesi dal titolo '{row_data['titolo']}'"
            
        elif table_name == 'Studenti':
            return f"Studente con matricola {row_data['matricola']}"
            
        elif table_name == 'Utente':
            return f"Utente {row_data['nome']} {row_data['cognome']} ({row_data['email']})"
            
        else:
            # Fallback: create a generic description
            return f"Record da {table_name}: {', '.join([f'{k}={v}' for k, v in row_data.items() if v is not None])}"

    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean metadata by removing null values and ensuring all values are valid for Pinecone."""
        cleaned = {}
        for key, value in metadata.items():
            if value is not None:
                # Convert to string if it's not a basic type
                if isinstance(value, (str, int, float, bool)):
                    cleaned[key] = value
                else:
                    cleaned[key] = str(value)
        return cleaned

    def get_department_rows(self) -> List[Dict[str, Any]]:
        """Get all department rows as individual vectors."""
        rows = self._execute_query("SELECT id, nome FROM Dipartimento")
        return [
            {
                "id": self._create_node_id("Dipartimento", id),
                "text": self._create_natural_language_text("Dipartimento", {"nome": nome}),
                "metadata": self._clean_metadata({
                    "node_id": self._create_node_id("Dipartimento", id),
                    "table_name": "Dipartimento",
                    "primary_key": id,
                    "node_type": "dept"
                })
            }
            for id, nome in rows
        ]

    def get_faculty_rows(self) -> List[Dict[str, Any]]:
        """Get all faculty rows as individual vectors."""
        query = """
            SELECT f.id, f.nome, f.presidente, f.contatti, d.id as dept_id, d.nome as dept_name 
            FROM Facolta f
            JOIN Dipartimento d ON f.dipartimento_id = d.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Facolta", id),
                "text": self._create_natural_language_text("Facolta", {
                    "nome": nome, 
                    "presidente": presidente, 
                    "contatti": contatti
                }),
                "metadata": self._clean_metadata({
                    "node_id": self._create_node_id("Facolta", id),
                    "table_name": "Facolta",
                    "primary_key": id,
                    "node_type": "faculty",
                    "dept_id": dept_id  # For graph relationships
                })
            }
            for id, nome, presidente, contatti, dept_id, dept_name in rows
        ]

    def get_degree_course_rows(self) -> List[Dict[str, Any]]:
        """Get all degree course rows as individual vectors."""
        query = """
            SELECT c.id, c.nome, c.descrizione, c.classe, c.tipologia, 
                   c.mail_segreteria, f.id as faculty_id, f.nome as faculty_name
            FROM Corso_di_Laurea c
            JOIN Facolta f ON c.id_facolta = f.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Corso_di_Laurea", id),
                "text": self._create_natural_language_text("Corso_di_Laurea", {
                    "nome": nome,
                    "descrizione": descrizione,
                    "classe": classe,
                    "tipologia": tipologia
                }),
                "metadata": {
                    "node_id": self._create_node_id("Corso_di_Laurea", id),
                    "table_name": "Corso_di_Laurea",
                    "primary_key": id,
                    "node_type": "degree",
                    "faculty_id": faculty_id  # For graph relationships
                }
            }
            for id, nome, descrizione, classe, tipologia, mail_segreteria, faculty_id, faculty_name in rows
        ]

    def get_course_rows(self) -> List[Dict[str, Any]]:
        """Get all course rows as individual vectors."""
        query = """
            SELECT c.id, c.nome, c.cfu, c.idoneità, c.prerequisiti, 
                   c.frequenza_obbligatoria, cdl.id as degree_id, cdl.nome as degree_name
            FROM Corso c
            JOIN Corso_di_Laurea cdl ON c.id_corso = cdl.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Corso", id),
                "text": self._create_natural_language_text("Corso", {
                    "nome": nome,
                    "cfu": cfu,
                    "prerequisiti": prerequisiti,
                    "frequenza_obbligatoria": frequenza_obbligatoria
                }),
                "metadata": {
                    "node_id": self._create_node_id("Corso", id),
                    "table_name": "Corso",
                    "primary_key": id,
                    "node_type": "course",
                    "degree_id": degree_id  # For graph relationships
                }
            }
            for id, nome, cfu, idoneita, prerequisiti, frequenza_obbligatoria, degree_id, degree_name in rows
        ]

    def get_course_edition_rows(self) -> List[Dict[str, Any]]:
        """Get all course edition rows as individual vectors."""
        query = """
            SELECT ec.id, ec.data, ec.mod_Esame, ec.orario, ec.esonero, ec.stato,
                   c.id as course_id, c.nome as course_name,
                   ia.id as prof_id, ia.nome as prof_nome, ia.cognome as prof_cognome
            FROM EdizioneCorso ec
            JOIN Corso c ON ec.id = c.id
            JOIN Insegnanti_Anagrafici ia ON ec.insegnante_anagrafico = ia.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("EdizioneCorso", f"{id}_{data}"),
                "text": self._create_natural_language_text("EdizioneCorso", {
                    "data": data,
                    "mod_Esame": mod_Esame,
                    "course_name": course_name,
                    "prof_nome": prof_nome,
                    "prof_cognome": prof_cognome
                }),
                "metadata": {
                    "node_id": self._create_node_id("EdizioneCorso", f"{id}_{data}"),
                    "table_name": "EdizioneCorso",
                    "primary_key": f"{id}_{data}",
                    "node_type": "edition",
                    "course_id": course_id,  # For graph relationships
                    "prof_id": prof_id,      # For graph relationships
                    "semester": data         # Coarse filter
                }
            }
            for id, data, mod_Esame, orario, esonero, stato, course_id, course_name, prof_id, prof_nome, prof_cognome in rows
        ]

    def get_professor_rows(self) -> List[Dict[str, Any]]:
        """Get all professor rows as individual vectors."""
        query = """
            SELECT ia.id, ia.email, ia.nome, ia.cognome, ia.utente_id,
                   ir.sitoWeb, ir.cv, ir.ricevimento
            FROM Insegnanti_Anagrafici ia
            LEFT JOIN Insegnanti_Registrati ir ON ia.utente_id = ir.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Insegnanti_Anagrafici", id),
                "text": self._create_natural_language_text("Insegnanti_Anagrafici", {
                    "nome": nome,
                    "cognome": cognome,
                    "email": email
                }),
                "metadata": {
                    "node_id": self._create_node_id("Insegnanti_Anagrafici", id),
                    "table_name": "Insegnanti_Anagrafici",
                    "primary_key": id,
                    "node_type": "professor",
                    "user_id": utente_id  # For graph relationships
                }
            }
            for id, email, nome, cognome, utente_id, sitoWeb, cv, ricevimento in rows
        ]

    def get_material_rows(self) -> List[Dict[str, Any]]:
        """Get all material rows as individual vectors."""
        query = """
            SELECT m.id, m.path_file, m.tipo, m.verificato, m.data_caricamento,
                   m.edition_id, m.edition_data, c.id as course_id, c.nome as course_name
            FROM Materiale_Didattico m
            JOIN Corso c ON m.edition_id = c.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Materiale_Didattico", id),
                "text": self._create_natural_language_text("Materiale_Didattico", {
                    "tipo": tipo,
                    "data_caricamento": data_caricamento,
                    "verificato": verificato
                }),
                "metadata": {
                    "node_id": self._create_node_id("Materiale_Didattico", id),
                    "table_name": "Materiale_Didattico",
                    "primary_key": id,
                    "node_type": "material",
                    "course_id": course_id,      # For graph relationships
                    "edition_id": edition_id,    # For graph relationships
                    "semester": edition_data,    # Coarse filter
                    "material_type": tipo        # Coarse filter
                }
            }
            for id, path_file, tipo, verificato, data_caricamento, edition_id, edition_data, course_id, course_name in rows
        ]

    def get_review_rows(self) -> List[Dict[str, Any]]:
        """Get all review rows as individual vectors."""
        query = """
            SELECT r.id, r.descrizione, r.voto, r.edition_id, r.edition_data,
                   c.id as course_id, c.nome as course_name
            FROM Review r
            JOIN EdizioneCorso ec ON r.edition_id = ec.id AND r.edition_data = ec.data
            JOIN Corso c ON ec.id = c.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Review", id),
                "text": self._create_natural_language_text("Review", {
                    "voto": voto,
                    "descrizione": descrizione
                }),
                "metadata": {
                    "node_id": self._create_node_id("Review", id),
                    "table_name": "Review",
                    "primary_key": id,
                    "node_type": "review",
                    "course_id": course_id,      # For graph relationships
                    "edition_id": edition_id,    # For graph relationships
                    "semester": edition_data,    # Coarse filter
                    "rating": voto               # Coarse filter
                }
            }
            for id, descrizione, voto, edition_id, edition_data, course_id, course_name in rows
        ]

    def get_rating_rows(self) -> List[Dict[str, Any]]:
        """Get all rating rows as individual vectors."""
        query = """
            SELECT v.voto, v.commento, v.data, v.student_id, v.id_materiale,
                   m.id as material_id, s.matricola as student_matricola
            FROM Valutazione v 
            JOIN Materiale_Didattico m ON v.id_materiale = m.id
            JOIN Studenti s ON s.id = v.student_id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Valutazione", f"{student_id}_{id_materiale}"),
                "text": self._create_natural_language_text("Valutazione", {
                    "voto": voto,
                    "commento": commento,
                    "data": data
                }),
                "metadata": {
                    "node_id": self._create_node_id("Valutazione", f"{student_id}_{id_materiale}"),
                    "table_name": "Valutazione",
                    "primary_key": f"{student_id}_{id_materiale}",
                    "node_type": "rating",
                    "student_id": student_id,        # For graph relationships
                    "material_id": id_materiale,     # For graph relationships
                    "rating": voto                   # Coarse filter
                }
            }
            for voto, commento, data, student_id, id_materiale, material_id, student_matricola in rows
        ]

    def get_platform_rows(self) -> List[Dict[str, Any]]:
        """Get all platform rows as individual vectors."""
        query = """
            SELECT p.Nome, ecp.codice, ecp.edizione_id, ecp.edizione_data
            FROM Piattaforme p 
            JOIN EdizioneCorso_Piattaforme ecp ON p.Nome = ecp.piattaforma_nome
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Piattaforme", f"{Nome}_{edizione_id}_{edizione_data}"),
                "text": self._create_natural_language_text("Piattaforme", {
                    "Nome": Nome
                }),
                "metadata": {
                    "node_id": self._create_node_id("Piattaforme", f"{Nome}_{edizione_id}_{edizione_data}"),
                    "table_name": "Piattaforme",
                    "primary_key": f"{Nome}_{edizione_id}_{edizione_data}",
                    "node_type": "platform",
                    "edition_id": edizione_id,      # For graph relationships
                    "semester": edizione_data,      # Coarse filter
                    "platform_name": Nome           # Coarse filter
                }
            }
            for Nome, codice, edizione_id, edizione_data in rows
        ]

    def get_thesis_rows(self) -> List[Dict[str, Any]]:
        """Get all thesis rows as individual vectors."""
        query = """
            SELECT t.id, t.titolo, t.file, t.corso_laurea_id, t.student_id,
                   cdl.nome as corso_laurea_nome, s.matricola as student_matricola
            FROM Tesi t
            JOIN Corso_di_Laurea cdl ON t.corso_laurea_id = cdl.id
            JOIN Studenti s ON t.student_id = s.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Tesi", id),
                "text": self._create_natural_language_text("Tesi", {
                    "titolo": titolo
                }),
                "metadata": {
                    "node_id": self._create_node_id("Tesi", id),
                    "table_name": "Tesi",
                    "primary_key": id,
                    "node_type": "thesis",
                    "degree_id": corso_laurea_id,   # For graph relationships
                    "student_id": student_id        # For graph relationships
                }
            }
            for id, titolo, file, corso_laurea_id, student_id, corso_laurea_nome, student_matricola in rows
        ]

    def get_student_rows(self) -> List[Dict[str, Any]]:
        """Get all student rows as individual vectors."""
        query = """
            SELECT s.id, s.matricola, s.corso_laurea_id, u.nome, u.cognome, u.email,
                   cdl.nome as corso_laurea_nome
            FROM Studenti s
            JOIN Utente u ON s.id = u.id
            JOIN Corso_di_Laurea cdl ON s.corso_laurea_id = cdl.id
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Studenti", id),
                "text": self._create_natural_language_text("Studenti", {
                    "matricola": matricola
                }),
                "metadata": {
                    "node_id": self._create_node_id("Studenti", id),
                    "table_name": "Studenti",
                    "primary_key": id,
                    "node_type": "student",
                    "degree_id": corso_laurea_id,   # For graph relationships
                    "user_id": id                   # For graph relationships
                }
            }
            for id, matricola, corso_laurea_id, nome, cognome, email, corso_laurea_nome in rows
        ]

    def get_user_rows(self) -> List[Dict[str, Any]]:
        """Get all user rows as individual vectors."""
        query = """
            SELECT id, nome, cognome, email, email_verificata
            FROM Utente
        """
        rows = self._execute_query(query)
        return [
            {
                "id": self._create_node_id("Utente", id),
                "text": self._create_natural_language_text("Utente", {
                    "nome": nome,
                    "cognome": cognome,
                    "email": email
                }),
                "metadata": {
                    "node_id": self._create_node_id("Utente", id),
                    "table_name": "Utente",
                    "primary_key": id,
                    "node_type": "user"
                }
            }
            for id, nome, cognome, email, email_verificata in rows
        ]

    def get_all_rows(self) -> List[Dict[str, Any]]:
        """Generate all row vectors from the database."""
        rows = []
        
        try:
            print("🔄 Generating per-row vectors...")
            
            rows.extend(self.get_department_rows())
            print(f"   ✅ Departments: {len(rows)} rows")
            
            rows.extend(self.get_faculty_rows())
            print(f"   ✅ Faculties: {len(rows)} rows")
            
            rows.extend(self.get_degree_course_rows())
            print(f"   ✅ Degree courses: {len(rows)} rows")
            
            rows.extend(self.get_course_rows())
            print(f"   ✅ Courses: {len(rows)} rows")
            
            rows.extend(self.get_course_edition_rows())
            print(f"   ✅ Course editions: {len(rows)} rows")
            
            rows.extend(self.get_professor_rows())
            print(f"   ✅ Professors: {len(rows)} rows")
            
            rows.extend(self.get_material_rows())
            print(f"   ✅ Materials: {len(rows)} rows")
            
            rows.extend(self.get_review_rows())
            print(f"   ✅ Reviews: {len(rows)} rows")
            
            rows.extend(self.get_rating_rows())
            print(f"   ✅ Ratings: {len(rows)} rows")
            
            rows.extend(self.get_platform_rows())
            print(f"   ✅ Platforms: {len(rows)} rows")
            
            rows.extend(self.get_thesis_rows())
            print(f"   ✅ Theses: {len(rows)} rows")
            
            rows.extend(self.get_student_rows())
            print(f"   ✅ Students: {len(rows)} rows")
            
            rows.extend(self.get_user_rows())
            print(f"   ✅ Users: {len(rows)} rows")
            
            print(f"✅ Generated {len(rows)} per-row vectors from database")
            return rows
            
        except Exception as e:
            print(f"❌ Error generating per-row vectors: {e}")
            return []

    def get_table_stats(self) -> Dict[str, int]:
        """Get statistics about the number of rows per table."""
        stats = {}
        
        try:
            tables = [
                'Dipartimento', 'Facolta', 'Corso_di_Laurea', 'Corso', 
                'EdizioneCorso', 'Insegnanti_Anagrafici', 'Materiale_Didattico',
                'Review', 'Valutazione', 'Piattaforme', 'Tesi', 'Studenti', 'Utente'
            ]
            
            for table in tables:
                self.cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cur.fetchone()[0]
                stats[table] = count
                
        except Exception as e:
            print(f"❌ Error getting table stats: {e}")
            
        return stats 
"""
Schema-aware Chunking for RAGv2
===============================

This module implements schema-aware extraction and chunking.
It emits one JSON object per row (≤ 400 tokens) with natural-language labels only.
IDs are stored only in Pinecone metadata (edition_id, etc.) and adds "node_type": "<TableName>" tag.
"""

import json
import re
from typing import List, Dict, Any, Optional
from src.utils.db_utils import get_connection, MODE
from ..config import SCHEMA_AWARE_CHUNKING, MAX_CHUNK_TOKENS, NODE_TYPE_PREFIX

class SchemaAwareChunker:
    """
    Schema-aware chunker that creates natural language representations of database rows.
    
    Features:
    - One JSON object per row (≤ 400 tokens)
    - Natural-language labels only; IDs stored in metadata
    - "node_type": "<TableName>" tag
    - Schema-aware field mapping
    """
    
    def __init__(self):
        self.conn = get_connection(MODE)
        self.cur = self.conn.cursor()
        
        # Schema-aware field mappings for natural language generation
        self.field_mappings = {
            'Dipartimento': {
                'id': 'ID',
                'nome': 'nome del dipartimento'
            },
            'Facolta': {
                'id': 'ID',
                'nome': 'nome della facoltà',
                'presidente': 'presidente',
                'contatti': 'contatti',
                'dipartimento_id': 'ID del dipartimento di afferenza'
            },
            'Corso_di_Laurea': {
                'id': 'ID',
                'nome': 'nome del corso di laurea',
                'descrizione': 'descrizione',
                'classe': 'classe di laurea',
                'tipologia': 'tipologia',
                'mail_segreteria': 'email della segreteria',
                'id_facolta': 'ID della facoltà'
            },
            'Corso': {
                'id': 'ID',
                'nome': 'nome del corso',
                'cfu': 'crediti formativi universitari',
                'idoneità': 'idoneità',
                'prerequisiti': 'prerequisiti',
                'frequenza_obbligatoria': 'frequenza obbligatoria',
                'id_corso': 'ID del corso di laurea'
            },
            'EdizioneCorso': {
                'id': 'ID',
                'data': 'periodo didattico',
                'mod_Esame': 'modalità d\'esame',
                'insegnante_anagrafico': 'ID dell\'insegnante'
            },
            'Insegnanti_Anagrafici': {
                'id': 'ID',
                'nome': 'nome',
                'cognome': 'cognome',
                'email': 'email',
                'utente_id': 'ID utente'
            },
            'Insegnanti_Registrati': {
                'id': 'ID',
                'sitoWeb': 'sito web',
                'cv': 'curriculum vitae',
                'ricevimento': 'orario di ricevimento',
                'anagrafico_id': 'ID anagrafico'
            },
            'Materiale_Didattico': {
                'id': 'ID',
                'path_file': 'percorso del file',
                'tipo': 'tipo di materiale',
                'verificato': 'verificato',
                'data_caricamento': 'data di caricamento',
                'edition_id': 'ID dell\'edizione'
            },
            'Review': {
                'id': 'ID',
                'descrizione': 'descrizione della recensione',
                'voto': 'voto',
                'edition_id': 'ID dell\'edizione',
                'edition_data': 'data dell\'edizione'
            },
            'Valutazione': {
                'voto': 'voto',
                'commento': 'commento',
                'data': 'data',
                'student_id': 'ID dello studente',
                'id_materiale': 'ID del materiale'
            },
            'Piattaforme': {
                'Nome': 'nome della piattaforma',
                'codice': 'codice',
                'edizione_id': 'ID dell\'edizione'
            },
            'Tesi': {
                'id': 'ID',
                'titolo': 'titolo della tesi',
                'corso_laurea_id': 'ID del corso di laurea',
                'student_id': 'ID dello studente',
                'file': 'file della tesi'
            }
        }
        
        # Natural language templates for different table types
        self.templates = {
            'Dipartimento': "Dipartimento di {nome}",
            'Facolta': "Facoltà di {nome}, presieduta da {presidente}. Contatti: {contatti}",
            'Corso_di_Laurea': "Corso di Laurea in {nome} (Classe {classe}, {tipologia}). {descrizione}",
            'Corso': "Corso di {nome} ({cfu} CFU). Prerequisiti: {prerequisiti}. Frequenza: {frequenza_obbligatoria}",
            'EdizioneCorso': "Edizione del corso per il periodo {data}. Modalità d'esame: {mod_Esame}",
            'Insegnanti_Anagrafici': "Docente {nome} {cognome}, contattabile all'email {email}",
            'Insegnanti_Registrati': "Sito web: {sitoWeb}. CV: {cv}. Ricevimento: {ricevimento}",
            'Materiale_Didattico': "Materiale didattico di tipo {tipo}, caricato il {data_caricamento}. Verificato: {verificato}",
            'Review': "Recensione con voto {voto}/5: {descrizione}",
            'Valutazione': "Valutazione con voto {voto}/5. Commento: {commento}. Data: {data}",
            'Piattaforme': "Piattaforma {Nome} con codice {codice}",
            'Tesi': "Tesi dal titolo '{titolo}'"
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

    def _count_tokens(self, text: str) -> int:
        """Simple token counting (words + punctuation)."""
        # Simple approximation: split on whitespace and count
        return len(text.split())

    def _create_natural_text(self, table_name: str, row_data: Dict[str, Any]) -> str:
        """Create natural language text from row data using templates."""
        template = self.templates.get(table_name, "")
        
        # Replace placeholders with actual values
        text = template
        for field, value in row_data.items():
            if value is not None:
                # Handle boolean values
                if isinstance(value, bool):
                    value = "Sì" if value else "No"
                # Handle None values
                elif value is None:
                    value = "Non specificato"
                else:
                    value = str(value)
                
                text = text.replace(f"{{{field}}}", value)
        
        # Clean up any remaining placeholders
        text = re.sub(r'\{[^}]+\}', 'Non specificato', text)
        
        return text

    def _extract_metadata(self, table_name: str, row_data: Dict[str, Any], row_id: str) -> Dict[str, Any]:
        """Extract metadata for Pinecone storage."""
        metadata = {
            "table_name": table_name,
            "node_type": table_name,
            "row_id": row_id,
            "source_type": "database"
        }
        
        # Add all IDs as metadata (not in text)
        for field, value in row_data.items():
            if field.lower().endswith('_id') or field.lower() == 'id':
                metadata[f"{field}"] = str(value)
        
        return metadata

    def get_department_chunks(self) -> List[Dict[str, Any]]:
        """Generate chunks for Dipartimento table."""
        if not SCHEMA_AWARE_CHUNKING:
            return []
            
        rows = self._execute_query("SELECT id, nome FROM Dipartimento")
        chunks = []
        
        for id_val, nome in rows:
            row_data = {"id": id_val, "nome": nome}
            text = self._create_natural_text("Dipartimento", row_data)
            
            # Check token limit
            if self._count_tokens(text) > MAX_CHUNK_TOKENS:
                continue
                
            chunk = {
                "id": f"dipartimento_{id_val}",
                "text": text,
                "metadata": self._extract_metadata("Dipartimento", row_data, str(id_val))
            }
            chunks.append(chunk)
            
        return chunks

    def get_faculty_chunks(self) -> List[Dict[str, Any]]:
        """Generate chunks for Facolta table."""
        if not SCHEMA_AWARE_CHUNKING:
            return []
            
        query = """
            SELECT f.id, f.nome, f.presidente, f.contatti, d.nome as dept_name 
            FROM Facolta f
            JOIN Dipartimento d ON f.dipartimento_id = d.id
        """
        rows = self._execute_query(query)
        chunks = []
        
        for id_val, nome, presidente, contatti, dept_name in rows:
            row_data = {
                "id": id_val, 
                "nome": nome, 
                "presidente": presidente, 
                "contatti": contatti,
                "dept_name": dept_name
            }
            text = self._create_natural_text("Facolta", row_data)
            
            # Check token limit
            if self._count_tokens(text) > MAX_CHUNK_TOKENS:
                continue
                
            chunk = {
                "id": f"facolta_{id_val}",
                "text": text,
                "metadata": self._extract_metadata("Facolta", row_data, str(id_val))
            }
            chunks.append(chunk)
            
        return chunks

    def get_course_edition_chunks(self) -> List[Dict[str, Any]]:
        """Generate chunks for EdizioneCorso table."""
        if not SCHEMA_AWARE_CHUNKING:
            return []
            
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
        chunks = []
        
        for id_val, data, mod_Esame, course_name, prof_nome, prof_cognome, piattaforma in rows:
            row_data = {
                "id": id_val,
                "data": data,
                "mod_Esame": mod_Esame,
                "course_name": course_name,
                "prof_nome": prof_nome,
                "prof_cognome": prof_cognome,
                "piattaforma": piattaforma
            }
            
            # Create natural language text
            text = f"Edizione del corso di {course_name} per il periodo '{data}'. "
            text += f"Docente: {prof_nome} {prof_cognome}. "
            text += f"Modalità d'esame: {mod_Esame}. "
            if piattaforma:
                text += f"Piattaforma utilizzata: {piattaforma}."
            
            # Check token limit
            if self._count_tokens(text) > MAX_CHUNK_TOKENS:
                continue
                
            chunk = {
                "id": f"edizione_corso_{id_val}",
                "text": text,
                "metadata": self._extract_metadata("EdizioneCorso", row_data, str(id_val))
            }
            chunks.append(chunk)
            
        return chunks

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Generate all chunks using schema-aware chunking."""
        if not SCHEMA_AWARE_CHUNKING:
            print("⚠️ Schema-aware chunking is disabled")
            return []
            
        chunks = []
        
        try:
            print("🔄 Generating schema-aware chunks...")
            chunks.extend(self.get_department_chunks())
            chunks.extend(self.get_faculty_chunks())
            chunks.extend(self.get_course_edition_chunks())
            # Add other table chunks as needed...
            
            print(f"✅ Generated {len(chunks)} schema-aware chunks")
            return chunks
            
        except Exception as e:
            print(f"❌ Error generating schema-aware chunks: {e}")
            return []


def test_schema_aware_chunking():
    """Unit test for schema-aware chunking (Task 1 Done-When)."""
    chunker = SchemaAwareChunker()
    chunks = chunker.get_course_edition_chunks()
    
    if not chunks:
        print("❌ No chunks generated")
        return False
    
    # Test first chunk
    chunk = chunks[0]
    
    # Check required fields
    required_fields = ["id", "text", "metadata"]
    for field in required_fields:
        if field not in chunk:
            print(f"❌ Missing required field: {field}")
            return False
    
    # Check metadata requirements
    metadata = chunk["metadata"]
    if "node_type" not in metadata:
        print("❌ Missing node_type in metadata")
        return False
    
    if "table_name" not in metadata:
        print("❌ Missing table_name in metadata")
        return False
    
    # Check that IDs are in metadata, not text
    text = chunk["text"]
    if "edizione_corso_" in text:
        print("❌ IDs should not be in text, only in metadata")
        return False
    
    # Check token limit
    token_count = len(text.split())
    if token_count > MAX_CHUNK_TOKENS:
        print(f"❌ Chunk exceeds token limit: {token_count} > {MAX_CHUNK_TOKENS}")
        return False
    
    print("✅ Schema-aware chunking test passed")
    return True


if __name__ == "__main__":
    test_schema_aware_chunking() 
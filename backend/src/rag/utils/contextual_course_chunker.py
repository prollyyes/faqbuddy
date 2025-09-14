#!/usr/bin/env python3
"""
Contextual Course Chunker - Rich, Human-Readable Course Profiles
===============================================================

This chunker creates comprehensive, contextual profiles that give the RAG pipeline
the complete picture when answering questions about courses, professors, and programs.

Key Features:
- No UUIDs in user-facing content
- Rich contextual joins across multiple tables
- Natural language focus for human consumption
- Hierarchical information from general to specific
"""

import os
import sys
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add src to path for absolute-style imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.utils.db_utils import get_connection, MODE
from src.utils.llm_mistral import generate_answer

load_dotenv()


class ContextualCourseChunker:
    """
    Creates rich, contextual course profiles with complete information hierarchy.
    """
    
    def __init__(self):
        self.conn = get_connection(mode=MODE)
        print("🚀 Initializing Contextual Course Chunker")
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute a query and return results."""
        cur = self.conn.cursor()
        try:
            cur.execute(query, params)
            return cur.fetchall()
        finally:
            cur.close()
    
    def _generate_summary(self, content: str, entity_type: str) -> str:
        """Generate a concise summary using the LLM."""
        try:
            context = f"Contenuto:\n{content}"
            question = f"Riassumi in massimo 3 frasi le informazioni principali su {entity_type}, mantenendo solo i dettagli essenziali per uno studente universitario."
            
            summary = generate_answer(context, question)
            # Clean up any prompt artifacts
            summary = summary.replace("[INST]", "").replace("[/INST]", "").strip()
            return summary
        except Exception as e:
            print(f"⚠️ Error generating summary for {entity_type}: {e}")
            # Fallback: return first few lines
            lines = content.split('\n')[:3]
            return ' '.join(lines)
    
    def get_course_profiles(self) -> List[Dict[str, Any]]:
        """
        Create comprehensive course profiles with all related information.
        """
        print("📚 Generating comprehensive course profiles...")
        
        # Complex query to get all course information in one go
        query = """
        SELECT DISTINCT
            c.id as course_id,
            c.nome as course_name,
            c.cfu,
            c.idoneità,
            c.prerequisiti,
            c.frequenza_obbligatoria,
            
            -- Degree Program Info
            cd.id as degree_id,
            cd.nome as degree_name,
            cd.descrizione as degree_description,
            cd.classe,
            cd.tipologia as degree_type,
            cd.mail_segreteria,
            cd.domanda_laurea,
            cd.test,
            cd.cfu_totali,
            
            -- Faculty & Department Info
            f.id as faculty_id,
            f.nome as faculty_name,
            f.presidente,
            f.contatti as faculty_contacts,
            d.id as dept_id,
            d.nome as department_name,
            
            -- Current Edition Info
            ec.data as edition_semester,
            ec.orario as schedule,
            ec.esonero as attendance_optional,
            ec.mod_Esame as exam_format,
            ec.stato as edition_status,
            
            -- Professor Info
            ia.id as prof_id,
            ia.nome as prof_name,
            ia.cognome as prof_surname,
            ia.email as prof_email,
            ir.infoMail as prof_info_mail,
            ir.sitoWeb as prof_website,
            ir.cv as prof_cv,
            ir.ricevimento as prof_office_hours
            
        FROM Corso c
        JOIN Corso_di_Laurea cd ON c.id_corso = cd.id
        JOIN Facolta f ON cd.id_facolta = f.id
        JOIN Dipartimento d ON f.dipartimento_id = d.id
        LEFT JOIN EdizioneCorso ec ON c.id = ec.id AND ec.stato = 'attivo'
        LEFT JOIN Insegnanti_Anagrafici ia ON ec.insegnante_anagrafico = ia.id
        LEFT JOIN Insegnanti_Registrati ir ON ia.utente_id = ir.id
        ORDER BY c.nome, ec.data DESC
        """
        
        rows = self._execute_query(query)
        profiles = []
        
        for row in rows:
            (
                course_id, course_name, cfu, idoneita, prerequisiti, frequenza_obbligatoria,
                degree_id, degree_name, degree_description, classe, degree_type, mail_segreteria, 
                domanda_laurea, test, cfu_totali,
                faculty_id, faculty_name, presidente, faculty_contacts, dept_id, department_name,
                edition_semester, schedule, attendance_optional, exam_format, edition_status,
                prof_id, prof_name, prof_surname, prof_email, prof_info_mail, prof_website, prof_cv, prof_office_hours
            ) = row
            
            # Build comprehensive course profile
            profile_text = self._build_course_profile(
                course_name, cfu, idoneita, prerequisiti, frequenza_obbligatoria,
                degree_name, degree_description, classe, degree_type, mail_segreteria, 
                domanda_laurea, test, cfu_totali,
                faculty_name, presidente, faculty_contacts, department_name,
                edition_semester, schedule, attendance_optional, exam_format, edition_status,
                prof_name, prof_surname, prof_email, prof_info_mail, prof_website, prof_cv, prof_office_hours
            )
            
            # Get additional information
            platform_codes = self._get_platform_codes(course_id, edition_semester)
            recent_reviews = self._get_recent_reviews(course_id, edition_semester)
            course_materials = self._get_course_materials(course_id, edition_semester)
            
            if platform_codes:
                profile_text += f"\n\n**Codici Piattaforme:**\n{platform_codes}"
            
            if recent_reviews:
                profile_text += f"\n\n**Recensioni Studenti:**\n{recent_reviews}"
            
            if course_materials:
                profile_text += f"\n\n**Materiali Didattici:**\n{course_materials}"
            
            # Generate AI summary
            summary = self._generate_summary(profile_text, f"il corso {course_name}")
            
            profiles.append({
                "id": f"course_profile_{course_id}_{edition_semester or 'general'}",
                "text": f"**Riepilogo:** {summary}\n\n**Informazioni Complete:**\n{profile_text}",
                "metadata": {
                    "chunk_type": "course_profile",
                    "course_name": course_name,
                    "degree_program": degree_name,
                    "faculty": faculty_name,
                    "department": department_name,
                    "professor": f"{prof_name} {prof_surname}" if prof_name and prof_surname else None,
                    "semester": edition_semester,
                    "cfu": cfu,
                    "primary_key": str(course_id)
                }
            })
        
        print(f"✅ Generated {len(profiles)} comprehensive course profiles")
        return profiles
    
    def _build_course_profile(self, course_name, cfu, idoneita, prerequisiti, frequenza_obbligatoria,
                             degree_name, degree_description, classe, degree_type, mail_segreteria, 
                             domanda_laurea, test, cfu_totali,
                             faculty_name, presidente, faculty_contacts, department_name,
                             edition_semester, schedule, attendance_optional, exam_format, edition_status,
                             prof_name, prof_surname, prof_email, prof_info_mail, prof_website, prof_cv, prof_office_hours) -> str:
        """Build the main course profile text."""
        
        profile = f"**Corso: {course_name}**\n"
        profile += f"**CFU:** {cfu}\n"
        
        if prerequisiti and prerequisiti.strip() and prerequisiti.strip() != "Nessuno":
            profile += f"**Prerequisiti:** {prerequisiti}\n"
        
        if frequenza_obbligatoria and frequenza_obbligatoria.strip() and frequenza_obbligatoria.strip() != "No":
            profile += f"**Frequenza:** {frequenza_obbligatoria}\n"
        
        profile += f"**Idoneità:** {'Sì' if idoneita else 'No'}\n\n"
        
        # Degree Program Information
        profile += f"**Corso di Laurea:** {degree_name}\n"
        if degree_description:
            profile += f"**Descrizione:** {degree_description}\n"
        profile += f"**Classe:** {classe}\n"
        profile += f"**Tipologia:** {degree_type}\n"
        profile += f"**CFU Totali:** {cfu_totali}\n"
        
        if test:
            profile += f"**Test di Ammissione:** Sì\n"
        
        if mail_segreteria:
            profile += f"**Email Segreteria:** {mail_segreteria}\n"
        
        if domanda_laurea:
            profile += f"**Domanda di Laurea:** {domanda_laurea}\n"
        
        profile += "\n"
        
        # Faculty and Department Information
        profile += f"**Facoltà:** {faculty_name}\n"
        profile += f"**Dipartimento:** {department_name}\n"
        if presidente:
            profile += f"**Preside:** {presidente}\n"
        if faculty_contacts:
            profile += f"**Contatti Facoltà:** {faculty_contacts}\n"
        profile += "\n"
        
        # Current Edition Information
        if edition_semester:
            profile += f"**Edizione Attuale:** {edition_semester}\n"
            profile += f"**Stato:** {edition_status}\n"
            
            if prof_name and prof_surname:
                profile += f"**Docente:** {prof_name} {prof_surname}\n"
                
                if prof_email:
                    profile += f"**Email Docente:** {prof_email}\n"
                elif prof_info_mail:
                    profile += f"**Email Docente:** {prof_info_mail}\n"
                
                if prof_office_hours:
                    profile += f"**Ricevimento:** {prof_office_hours}\n"
                
                if prof_website:
                    profile += f"**Sito Web:** {prof_website}\n"
            
            if schedule:
                profile += f"**Orario:** {schedule}\n"
            
            profile += f"**Esonero:** {'Sì' if attendance_optional else 'No'}\n"
            profile += f"**Modalità Esame:** {exam_format}\n"
        
        return profile
    
    def _get_platform_codes(self, course_id: str, semester: Optional[str]) -> str:
        """Get platform codes for the course edition."""
        if not semester:
            return ""
        
        query = """
        SELECT p.Nome, ecp.codice
        FROM EdizioneCorso_Piattaforme ecp
        JOIN Piattaforme p ON ecp.piattaforma_nome = p.Nome
        WHERE ecp.edizione_id = %s AND ecp.edizione_data = %s
        """
        
        rows = self._execute_query(query, (course_id, semester))
        if not rows:
            return ""
        
        codes = []
        for platform_name, code in rows:
            if code:
                codes.append(f"• {platform_name}: {code}")
        
        return "\n".join(codes) if codes else ""
    
    def _get_recent_reviews(self, course_id: str, semester: Optional[str]) -> str:
        """Get recent student reviews for the course."""
        if not semester:
            return ""
        
        query = """
        SELECT r.descrizione, r.voto, s.matricola
        FROM Review r
        JOIN Corsi_seguiti cs ON r.student_id = cs.student_id AND r.edition_id = cs.edition_id AND r.edition_data = cs.edition_data
        JOIN Studenti s ON cs.student_id = s.id
        WHERE r.edition_id = %s AND r.edition_data = %s
        ORDER BY r.voto DESC
        LIMIT 3
        """
        
        rows = self._execute_query(query, (course_id, semester))
        if not rows:
            return ""
        
        reviews = []
        for descrizione, voto, matricola in rows:
            if descrizione:
                reviews.append(f"• Voto: {voto}/5 - {descrizione[:100]}{'...' if len(descrizione) > 100 else ''}")
        
        return "\n".join(reviews) if reviews else ""
    
    def _get_course_materials(self, course_id: str, semester: Optional[str]) -> str:
        """Get available course materials."""
        if not semester:
            return ""
        
        query = """
        SELECT md.tipo, md.rating_medio, md.numero_voti, md.data_caricamento
        FROM Materiale_Didattico md
        WHERE md.edition_id = %s AND md.edition_data = %s AND md.verificato = true
        ORDER BY md.rating_medio DESC NULLS LAST, md.data_caricamento DESC
        LIMIT 5
        """
        
        rows = self._execute_query(query, (course_id, semester))
        if not rows:
            return ""
        
        materials = []
        for tipo, rating, votes, date in rows:
            material_info = f"• {tipo or 'Materiale'}"
            if rating:
                material_info += f" (Rating: {rating:.1f}/5, {votes} voti)"
            material_info += f" - Caricato: {date}"
            materials.append(material_info)
        
        return "\n".join(materials) if materials else ""
    
    def get_professor_profiles(self) -> List[Dict[str, Any]]:
        """
        Create professor profiles with all their courses and student feedback.
        """
        print("👨‍🏫 Generating professor profiles...")
        
        query = """
        SELECT DISTINCT
            ia.id as prof_id,
            ia.nome as prof_name,
            ia.cognome as prof_surname,
            ia.email as prof_email,
            ir.infoMail as prof_info_mail,
            ir.sitoWeb as prof_website,
            ir.cv as prof_cv,
            ir.ricevimento as prof_office_hours,
            
            -- Count of courses taught
            COUNT(DISTINCT ec.id) as courses_count,
            
            -- Recent courses
            STRING_AGG(DISTINCT c.nome, ', ') as recent_courses
            
        FROM Insegnanti_Anagrafici ia
        LEFT JOIN Insegnanti_Registrati ir ON ia.utente_id = ir.id
        LEFT JOIN EdizioneCorso ec ON ia.id = ec.insegnante_anagrafico AND ec.stato = 'attivo'
        LEFT JOIN Corso c ON ec.id = c.id
        GROUP BY ia.id, ia.nome, ia.cognome, ia.email, ir.infoMail, ir.sitoWeb, ir.cv, ir.ricevimento
        HAVING COUNT(DISTINCT ec.id) > 0
        ORDER BY ia.cognome, ia.nome
        """
        
        rows = self._execute_query(query)
        profiles = []
        
        for row in rows:
            (prof_id, prof_name, prof_surname, prof_email, prof_info_mail, 
             prof_website, prof_cv, prof_office_hours, courses_count, recent_courses) = row
            
            # Build professor profile
            profile_text = f"**Docente: {prof_name} {prof_surname}**\n"
            
            if prof_email:
                profile_text += f"**Email:** {prof_email}\n"
            elif prof_info_mail:
                profile_text += f"**Email:** {prof_info_mail}\n"
            
            if prof_office_hours:
                profile_text += f"**Ricevimento:** {prof_office_hours}\n"
            
            if prof_website:
                profile_text += f"**Sito Web:** {prof_website}\n"
            
            profile_text += f"**Corsi Attivi:** {courses_count}\n"
            if recent_courses:
                profile_text += f"**Corsi Insegnati:** {recent_courses}\n"
            
            # Get student feedback
            feedback = self._get_professor_feedback(prof_id)
            if feedback:
                profile_text += f"\n**Feedback Studenti:**\n{feedback}"
            
            # Generate AI summary
            summary = self._generate_summary(profile_text, f"il docente {prof_name} {prof_surname}")
            
            profiles.append({
                "id": f"professor_profile_{prof_id}",
                "text": f"**Riepilogo:** {summary}\n\n**Informazioni Complete:**\n{profile_text}",
                "metadata": {
                    "chunk_type": "professor_profile",
                    "professor_name": f"{prof_name} {prof_surname}",
                    "courses_count": courses_count,
                    "primary_key": str(prof_id)
                }
            })
        
        print(f"✅ Generated {len(profiles)} professor profiles")
        return profiles
    
    def _get_professor_feedback(self, prof_id: str) -> str:
        """Get student feedback for a professor."""
        query = """
        SELECT r.descrizione, r.voto, c.nome as course_name
        FROM Review r
        JOIN Corsi_seguiti cs ON r.student_id = cs.student_id AND r.edition_id = cs.edition_id AND r.edition_data = cs.edition_data
        JOIN EdizioneCorso ec ON cs.edition_id = ec.id AND cs.edition_data = ec.data
        JOIN Corso c ON ec.id = c.id
        WHERE ec.insegnante_anagrafico = %s
        ORDER BY r.voto DESC
        """
        
        rows = self._execute_query(query, (prof_id,))
        if not rows:
            return ""
        
        feedback = []
        for descrizione, voto, course_name in rows:
            if descrizione:
                feedback.append(f"• {course_name}: {voto}/5 - {descrizione[:80]}{'...' if len(descrizione) > 80 else ''}")
        
        return "\n".join(feedback) if feedback else ""
    
    def get_degree_program_overviews(self) -> List[Dict[str, Any]]:
        """
        Create degree program overviews with all courses and structure.
        """
        print("🎓 Generating degree program overviews...")
        
        query = """
        SELECT 
            cd.id as degree_id,
            cd.nome as degree_name,
            cd.descrizione as degree_description,
            cd.classe,
            cd.tipologia as degree_type,
            cd.mail_segreteria,
            cd.domanda_laurea,
            cd.test,
            cd.cfu_totali,
            f.nome as faculty_name,
            d.nome as department_name,
            COUNT(DISTINCT c.id) as total_courses
        FROM Corso_di_Laurea cd
        JOIN Facolta f ON cd.id_facolta = f.id
        JOIN Dipartimento d ON f.dipartimento_id = d.id
        LEFT JOIN Corso c ON cd.id = c.id_corso
        GROUP BY cd.id, cd.nome, cd.descrizione, cd.classe, cd.tipologia, 
                 cd.mail_segreteria, cd.domanda_laurea, cd.test, cd.cfu_totali,
                 f.nome, d.nome
        ORDER BY cd.nome
        """
        
        rows = self._execute_query(query)
        profiles = []
        
        for row in rows:
            (degree_id, degree_name, degree_description, classe, degree_type,
             mail_segreteria, domanda_laurea, test, cfu_totali, faculty_name, 
             department_name, total_courses) = row
            
            # Build degree program overview
            profile_text = f"**Corso di Laurea: {degree_name}**\n"
            
            if degree_description:
                profile_text += f"**Descrizione:** {degree_description}\n"
            
            profile_text += f"**Classe:** {classe}\n"
            profile_text += f"**Tipologia:** {degree_type}\n"
            profile_text += f"**CFU Totali:** {cfu_totali}\n"
            profile_text += f"**Numero Corsi:** {total_courses}\n"
            
            if test:
                profile_text += f"**Test di Ammissione:** Sì\n"
            
            profile_text += f"**Facoltà:** {faculty_name}\n"
            profile_text += f"**Dipartimento:** {department_name}\n"
            
            if mail_segreteria:
                profile_text += f"**Email Segreteria:** {mail_segreteria}\n"
            
            if domanda_laurea:
                profile_text += f"**Domanda di Laurea:** {domanda_laurea}\n"
            
            # Get course structure
            course_structure = self._get_course_structure(degree_id)
            if course_structure:
                profile_text += f"\n**Struttura Corsi:**\n{course_structure}"
            
            # Generate AI summary
            summary = self._generate_summary(profile_text, f"il corso di laurea {degree_name}")
            
            profiles.append({
                "id": f"degree_overview_{degree_id}",
                "text": f"**Riepilogo:** {summary}\n\n**Informazioni Complete:**\n{profile_text}",
                "metadata": {
                    "chunk_type": "degree_overview",
                    "degree_name": degree_name,
                    "faculty": faculty_name,
                    "department": department_name,
                    "degree_type": degree_type,
                    "total_courses": total_courses,
                    "primary_key": str(degree_id)
                }
            })
        
        print(f"✅ Generated {len(profiles)} degree program overviews")
        return profiles
    
    def _get_course_structure(self, degree_id: str) -> str:
        """Get the course structure for a degree program."""
        query = """
        SELECT c.nome, c.cfu, c.prerequisiti
        FROM Corso c
        WHERE c.id_corso = %s
        ORDER BY c.nome
        """
        
        rows = self._execute_query(query, (degree_id,))
        if not rows:
            return ""
        
        courses = []
        for nome, cfu, prerequisiti in rows:
            course_info = f"• {nome} ({cfu} CFU)"
            if prerequisiti and prerequisiti.strip() and prerequisiti.strip() != "Nessuno":
                course_info += f" - Prerequisiti: {prerequisiti}"
            courses.append(course_info)
        
        return "\n".join(courses) if courses else ""
    
    def get_all_contextual_chunks(self) -> List[Dict[str, Any]]:
        """
        Generate all contextual chunks.
        """
        print("🚀 Generating all contextual course chunks...")
        
        all_chunks = []
        
        # Primary: Course profiles (most important)
        all_chunks.extend(self.get_course_profiles())
        
        # Secondary: Professor profiles
        all_chunks.extend(self.get_professor_profiles())
        
        # Tertiary: Degree program overviews
        all_chunks.extend(self.get_degree_program_overviews())
        
        print(f"✅ Generated {len(all_chunks)} total contextual chunks")
        return all_chunks
    
    def __del__(self):
        """Clean up database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()


def test_contextual_chunker():
    """Test the contextual chunker."""
    print("🧪 Testing Contextual Course Chunker...")
    
    chunker = ContextualCourseChunker()
    chunks = chunker.get_all_contextual_chunks()
    
    print(f"\n📊 Results:")
    print(f"   Total chunks: {len(chunks)}")
    
    # Show sample chunk
    if chunks:
        sample = chunks[0]
        print(f"\n📝 Sample chunk:")
        print(f"   ID: {sample['id']}")
        print(f"   Type: {sample['metadata']['chunk_type']}")
        print(f"   Text preview: {sample['text'][:200]}...")
    
    return chunks


if __name__ == "__main__":
    test_contextual_chunker()

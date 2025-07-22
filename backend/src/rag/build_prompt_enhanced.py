#!/usr/bin/env python3
"""
Enhanced Prompt Builder for RAG v2
==================================

This module provides enhanced source attribution and clear distinction
between PDF-based and database-based answers in the RAG v2 system.
"""

import sys
import re
from typing import List, Dict, Any
from dataclasses import dataclass

# Configuration
MAX_CHUNKS = 5
MAX_TOKENS = 1200
MAX_TOKENS_PER_CHUNK = 300

@dataclass
class SourceInfo:
    """Structured source information."""
    source_type: str  # 'pdf', 'database', 'document'
    namespace: str    # 'pdf_v2', 'db_v2', 'documents_v2'
    source_name: str  # filename or table name
    page: str = "N/A"
    section: str = "N/A"
    row_id: str = "N/A"
    confidence: float = 1.0

class EnhancedPromptBuilder:
    """
    Enhanced prompt builder with improved source attribution.
    """
    
    def __init__(self):
        self.system_prompt = self._get_enhanced_system_prompt()
    
    def _get_enhanced_system_prompt(self) -> str:
        """Get enhanced system prompt with clear source attribution instructions."""
        return (
            "Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, "
            "i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere.\n\n"
            
            "📋 ISTRUZIONI IMPORTANTI:\n"
            "1. Usa SOLO il contesto fornito per rispondere\n"
            "2. Cita SEMPRE le fonti inline usando i metadati forniti\n"
            "3. Distingui chiaramente tra informazioni da PDF e da database\n"
            "4. Se non conosci la risposta, dillo onestamente\n"
            "5. Non inventare informazioni\n"
            "6. Rispondi SEMPRE in italiano\n"
            "7. Mantieni un tono professionale ma amichevole\n"
            "8. Usa il formato Markdown per una migliore leggibilità\n\n"
            
            "📚 TIPI DI FONTI:\n"
            "- 📄 PDF: Documenti ufficiali, regolamenti, procedure (es. 'secondo il PDF...')\n"
            "- 🗄️ Database: Informazioni strutturate, liste, contatti (es. 'dal database risulta...')\n"
            "- 📝 Documenti: Altri documenti ufficiali\n\n"
            
            "🔍 FORMATO RISPOSTA:\n"
            "1. Risposta principale\n"
            "2. Citazioni delle fonti utilizzate\n"
            "3. Distinzione tra tipi di informazioni (PDF vs Database)\n"
        )
    
    def _extract_source_info(self, chunk: Dict[str, Any]) -> SourceInfo:
        """Extract structured source information from chunk."""
        metadata = chunk.get('metadata', {})
        namespace = chunk.get('namespace', 'unknown')
        
        # Determine source type from namespace
        if 'pdf' in namespace:
            source_type = 'pdf'
        elif 'db' in namespace:
            source_type = 'database'
        else:
            source_type = 'document'
        
        return SourceInfo(
            source_type=source_type,
            namespace=namespace,
            source_name=metadata.get('source', metadata.get('table_name', 'Unknown')),
            page=metadata.get('page', 'N/A'),
            section=metadata.get('section_title', metadata.get('section', 'N/A')),
            row_id=metadata.get('row_id', 'N/A'),
            confidence=chunk.get('score', 1.0)
        )
    
    def _format_source_citation(self, source_info: SourceInfo, chunk_idx: int) -> str:
        """Format source citation with clear type distinction."""
        if source_info.source_type == 'pdf':
            return (
                f"📄 **Fonte PDF {chunk_idx}**: {source_info.source_name}\n"
                f"   📍 Pagina: {source_info.page} | Sezione: {source_info.section}\n"
                f"   🎯 Confidenza: {source_info.confidence:.3f}\n"
            )
        elif source_info.source_type == 'database':
            return (
                f"🗄️ **Fonte Database {chunk_idx}**: Tabella {source_info.source_name}\n"
                f"   📍 Riga: {source_info.row_id} | Sezione: {source_info.section}\n"
                f"   🎯 Confidenza: {source_info.confidence:.3f}\n"
            )
        else:
            return (
                f"📝 **Fonte Documento {chunk_idx}**: {source_info.source_name}\n"
                f"   📍 Sezione: {source_info.section}\n"
                f"   🎯 Confidenza: {source_info.confidence:.3f}\n"
            )
    
    def _format_chunk_content(self, chunk: Dict[str, Any], chunk_idx: int) -> str:
        """Format chunk content with enhanced source attribution."""
        source_info = self._extract_source_info(chunk)
        text = chunk.get('text', '')
        
        # Truncate if too long
        if len(text) > MAX_TOKENS_PER_CHUNK * 4:  # Rough character estimation
            text = text[:MAX_TOKENS_PER_CHUNK * 4] + "..."
        
        citation = self._format_source_citation(source_info, chunk_idx)
        
        return f"{citation}```\n{text}\n```\n"
    
    def _get_source_summary(self, chunks: List[Dict[str, Any]]) -> str:
        """Generate a summary of sources used."""
        source_counts = {'pdf': 0, 'database': 0, 'document': 0}
        sources_used = []
        
        for chunk in chunks:
            source_info = self._extract_source_info(chunk)
            source_counts[source_info.source_type] += 1
            
            if source_info.source_name not in sources_used:
                sources_used.append(source_info.source_name)
        
        summary = "📊 **Riepilogo Fonti Utilizzate:**\n"
        if source_counts['pdf'] > 0:
            summary += f"   📄 PDF: {source_counts['pdf']} frammenti\n"
        if source_counts['database'] > 0:
            summary += f"   🗄️ Database: {source_counts['database']} frammenti\n"
        if source_counts['document'] > 0:
            summary += f"   📝 Documenti: {source_counts['document']} frammenti\n"
        
        summary += f"   📚 Fonti totali: {', '.join(sources_used[:3])}"
        if len(sources_used) > 3:
            summary += f" e altre {len(sources_used) - 3}"
        
        return summary
    
    def build_enhanced_prompt(self, retrieval_results: List[Dict[str, Any]], question: str) -> str:
        """
        Build enhanced prompt with clear source attribution.
        
        Args:
            retrieval_results: List of retrieval results with metadata
            question: User question
            
        Returns:
            Enhanced prompt string
        """
        # Deduplicate and select top chunks
        deduped = self._deduplicate_chunks(retrieval_results)
        selected = self._select_chunks(deduped)
        
        # Format context with enhanced source attribution
        context_parts = []
        for i, chunk in enumerate(selected, 1):
            context_parts.append(self._format_chunk_content(chunk, i))
        
        context = "\n".join(context_parts)
        source_summary = self._get_source_summary(selected)
        
        # Build final prompt
        prompt = (
            f"{self.system_prompt}\n\n"
            f"❓ **Domanda dell'utente**: {question}\n\n"
            f"{source_summary}\n\n"
            f"📖 **Contesto fornito**:\n{context}\n\n"
            f"💬 **Risposta**:"
        )
        
        return prompt
    
    def _deduplicate_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate chunks based on normalized text."""
        seen = set()
        deduped = []
        
        for chunk in chunks:
            # Normalize text for deduplication
            text = chunk.get('text', '')
            norm = re.sub(r'\W+', '', text.lower())
            
            if norm not in seen and len(norm) > 10:  # Minimum length threshold
                seen.add(norm)
                deduped.append(chunk)
        
        return deduped
    
    def _select_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select top chunks fitting token limit."""
        selected = []
        total_tokens = 0
        
        for chunk in chunks:
            chunk_tokens = len(chunk.get('text', '').split())
            
            if len(selected) < MAX_CHUNKS and total_tokens + chunk_tokens <= MAX_TOKENS:
                selected.append(chunk)
                total_tokens += chunk_tokens
            
            if total_tokens >= MAX_TOKENS:
                break
        
        return selected


def build_prompt(merged_results: List[Dict], user_question: str) -> str:
    """
    Enhanced build_prompt function for backward compatibility.
    
    Args:
        merged_results: List of retrieval results
        user_question: User question
        
    Returns:
        Enhanced prompt string
    """
    builder = EnhancedPromptBuilder()
    return builder.build_enhanced_prompt(merged_results, user_question)


def test_enhanced_prompt():
    """Test the enhanced prompt builder."""
    print("🧪 Testing Enhanced Prompt Builder...")
    
    # Sample retrieval results
    sample_results = [
        {
            'text': 'Il corso di Sistemi Operativi è tenuto dal Prof. Paolo Ottolino nel semestre S1/2025.',
            'metadata': {
                'source': 'iscrizione_ingegneria.pdf',
                'page': 17,
                'section_title': 'Corsi del Primo Anno'
            },
            'namespace': 'pdf_v2',
            'score': 0.95
        },
        {
            'text': 'Paolo Ottolino, email: paolo.ottolino@uniroma1.it, ufficio: Aula 3.2',
            'metadata': {
                'table_name': 'professors',
                'row_id': '123',
                'section': 'Contatti Docenti'
            },
            'namespace': 'db_v2',
            'score': 0.88
        }
    ]
    
    question = "Chi insegna il corso di Sistemi Operativi?"
    
    # Build enhanced prompt
    builder = EnhancedPromptBuilder()
    prompt = builder.build_enhanced_prompt(sample_results, question)
    
    print("✅ Enhanced prompt generated successfully!")
    print("\n" + "="*50)
    print("SAMPLE ENHANCED PROMPT:")
    print("="*50)
    print(prompt)
    
    return prompt


if __name__ == "__main__":
    test_enhanced_prompt() 
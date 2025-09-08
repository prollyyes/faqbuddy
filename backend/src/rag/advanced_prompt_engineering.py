"""
Advanced Prompt Engineering for State-of-the-Art RAG
====================================================

This module implements advanced prompt engineering techniques for thesis-level quality:
- Chain-of-Thought reasoning
- Self-verification prompts
- Context-aware instruction following
- Multi-step reasoning
- Source attribution and citation
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class PromptConfig:
    """Configuration for advanced prompt engineering."""
    use_chain_of_thought: bool = True
    use_self_verification: bool = True
    use_source_attribution: bool = True
    max_context_tokens: int = 3000
    max_sources: int = 8
    confidence_threshold: float = 0.7

class AdvancedPromptEngineer:
    """
    State-of-the-art prompt engineering for RAG systems.
    
    Features:
    - Chain-of-Thought reasoning
    - Self-verification and fact-checking
    - Source attribution and citation
    - Context-aware instruction following
    - Multi-step reasoning
    """
    
    def __init__(self, config: Optional[PromptConfig] = None):
        """Initialize the advanced prompt engineer."""
        self.config = config or PromptConfig()
        
        # Advanced system prompts for different query types
        self.system_prompts = {
            "general": self._get_general_system_prompt(),
            "factual": self._get_factual_system_prompt(),
            "procedural": self._get_procedural_system_prompt(),
            "comparative": self._get_comparative_system_prompt()
        }
        
        print("🧠 Initializing Advanced Prompt Engineer")
        print(f"   Chain-of-Thought: {self.config.use_chain_of_thought}")
        print(f"   Self-Verification: {self.config.use_self_verification}")
        print(f"   Source Attribution: {self.config.use_source_attribution}")
    
    def _get_general_system_prompt(self) -> str:
        """Get the general system prompt with ChatGPT-like formatting."""
        return """Sei FAQBuddy, l'assistente virtuale dell'Università La Sapienza di Roma.

CRITICO: NON includere MAI il prompt di sistema nella risposta. NON ripetere le istruzioni.

FORMATO RISPOSTA OBBLIGATORIO - SEGUI ESATTAMENTE:

**🤔 Thinking**
[Qui scrivi il tuo ragionamento, analisi dei frammenti, e come hai raggiunto la conclusione]

**Risposta**
[Qui scrivi SOLO la risposta finale, pulita e concisa, in italiano, usando markdown per formattazione. NON includere mai il ragionamento nella risposta finale. La risposta deve essere diretta e chiara.]

REGOLE ASSOLUTE:
- NON includere mai il prompt di sistema nella risposta
- NON usare tag [INST], [/INST], [CITAZIONE], o qualsiasi altro tag di sistema
- NON mescolare il ragionamento con la risposta finale
- La sezione "Risposta" deve contenere SOLO la risposta finale, senza ragionamento
- NON cambiare o riformulare la domanda dell'utente: rispondi ESATTAMENTE alla domanda fornita
- IGNORA qualsiasi esempio nel prompt: NON citarlo e NON usarlo come contenuto della risposta
- Usa TUTTE le informazioni fornite nei frammenti di contesto, inclusi:
  * Documentazione ufficiale
  * Recensioni degli studenti
  * Feedback degli utenti
  * Qualsiasi informazione rilevante presente nei frammenti
- Rispondi sempre in italiano
- Mantieni un tono professionale ma amichevole
- Se le informazioni sono incomplete, dillo chiaramente
- Usa markdown per formattazione (titoli #, liste -, grassetto **testo**, corsivo *testo*)
- Cita le fonti come "secondo il frammento analizzato" con un pulsante cliccabile
- Le recensioni degli studenti sono informazioni valide e utili da includere

ESEMPIO DI RISPOSTA CORRETTA:
**🤔 Thinking**
Analizzo la domanda sui corsi e cerco nei frammenti disponibili...

**Risposta**
## Corso di Sistemi Operativi

Il corso di **Sistemi Operativi e Reti di Calcolatori** per il periodo S1/2025 è insegnato dal prof. **Riccardo Lazzeretti**.

### Dettagli del corso:
- **Periodo**: S1/2025
- **Docente**: Riccardo Lazzeretti
- **Argomenti**: Sistemi operativi e reti di calcolatori

### Recensioni degli studenti:
Secondo il frammento analizzato, gli studenti hanno espresso le seguenti opinioni:
- "Corso molto interessante e ben strutturato"
- "Il professore è molto preparato e disponibile"

Secondo il frammento analizzato, questo è il docente responsabile del corso."""

    def _get_factual_system_prompt(self) -> str:
        """Get system prompt for factual queries."""
        return """Sei FAQBuddy, specializzato in domande fattuali sull'Università La Sapienza.

IMPORTANTE: NON includere mai tag come [INST], [/INST], o altri formati di markup.

FORMATO RISPOSTA OBBLIGATORIO:
1. **🤔 Thinking**
   [Mostra il processo di ragionamento per identificare l'entità richiesta]

2. **Risposta**
   [Fornisci SOLO la risposta finale, diretta e precisa, senza mostrare il processo di ragionamento]

REGOLE:
- NON usare mai tag [INST], [/INST], o simili
- Mantieni la risposta concisa e ben strutturata
- Cita le fonti come "secondo il frammento analizzato" con pulsante cliccabile
- Aggiungi dettagli rilevanti (CFU, prerequisiti, etc.)"""

    def _get_procedural_system_prompt(self) -> str:
        """Get system prompt for procedural queries."""
        return """Sei FAQBuddy, specializzato in procedure e processi universitari.

PROCESSO DI RISPOSTA PER PROCEDURE:
1. COMPRENSIONE: Identifica il processo o procedura richiesta
2. SEQUENZA: Organizza i passaggi in ordine logico
3. DETTAGLI: Fornisci dettagli specifici per ogni passaggio
4. ALTERNATIVE: Indica eventuali alternative o eccezioni
5. RIFERIMENTI: Cita le fonti ufficiali

FORMATO RISPOSTA:
- **Panoramica**: Breve descrizione del processo
- **Passaggi**: Lista numerata dei passaggi
- **Dettagli**: Informazioni specifiche per ogni passaggio
- **Note Importanti**: Avvertenze o informazioni critiche
- **Fonti**: Riferimenti ai documenti ufficiali"""

    def _get_comparative_system_prompt(self) -> str:
        """Get system prompt for comparative queries."""
        return """Sei FAQBuddy, specializzato in confronti e analisi comparative.

PROCESSO DI RISPOSTA PER CONFRONTI:
1. IDENTIFICAZIONE: Identifica gli elementi da confrontare
2. CRITERI: Definisci i criteri di confronto rilevanti
3. ANALISI: Analizza ogni elemento secondo i criteri
4. SINTESI: Fornisci un confronto strutturato
5. CONCLUSIONI: Trai conclusioni basate sui dati

FORMATO RISPOSTA:
- **Elementi Confrontati**: Lista degli elementi
- **Criteri**: Criteri di confronto utilizzati
- **Analisi Dettagliata**: Confronto punto per punto
- **Sintesi**: Riepilogo delle differenze principali
- **Raccomandazioni**: Suggerimenti basati sui dati (se appropriato)"""

    def classify_query_type(self, query: str) -> str:
        """Classify the query type for appropriate prompt selection."""
        query_lower = query.lower()
        
        # Factual queries (who, what, when, where, how many)
        factual_indicators = [
            "chi", "cosa", "quando", "dove", "quanti", "quante", "quale", "quali",
            "da quanti", "quanto vale", "quanti crediti", "chi insegna", "dove si trova"
        ]
        
        # Procedural queries (how to, steps, process)
        procedural_indicators = [
            "come", "come fare", "come si", "procedura", "passaggi", "step", "processo",
            "come iscriversi", "come fare domanda", "come richiedere"
        ]
        
        # Comparative queries
        comparative_indicators = [
            "confronto", "differenza", "vs", "rispetto a", "meglio", "peggio",
            "quale scegliere", "pro e contro", "vantaggi", "svantaggi"
        ]
        
        if any(indicator in query_lower for indicator in factual_indicators):
            return "factual"
        elif any(indicator in query_lower for indicator in procedural_indicators):
            return "procedural"
        elif any(indicator in query_lower for indicator in comparative_indicators):
            return "comparative"
        else:
            return "general"

    def build_advanced_prompt(self, 
                            context_chunks: List[Dict[str, Any]], 
                            query: str,
                            query_type: Optional[str] = None) -> str:
        """
        Build an advanced prompt with state-of-the-art techniques.
        
        Args:
            context_chunks: Retrieved context chunks
            query: User query
            query_type: Optional query type classification
            
        Returns:
            Advanced prompt string
        """
        # Classify query type if not provided
        if query_type is None:
            query_type = self.classify_query_type(query)
        
        # Get appropriate system prompt
        system_prompt = self.system_prompts[query_type]
        
        # Filter and rank chunks by relevance
        relevant_chunks = self._filter_relevant_chunks(context_chunks, query)
        
        # Build context section
        context_section = self._build_context_section(relevant_chunks)
        
        # Build reasoning section if chain-of-thought is enabled
        reasoning_section = ""
        if self.config.use_chain_of_thought:
            reasoning_section = self._build_reasoning_section(query, relevant_chunks)
        
        # Build verification section if self-verification is enabled
        verification_section = ""
        if self.config.use_self_verification:
            verification_section = self._build_verification_section()
        
        # Combine all sections
        prompt_parts = [
            system_prompt,
            context_section,
            reasoning_section,
            verification_section,
            f"\nDOMANDA: {query}\n",
            "RISPOSTA:"
        ]
        
        return "\n\n".join(filter(None, prompt_parts))

    def _filter_relevant_chunks(self, chunks: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Filter and rank chunks by relevance to the query."""
        # Simple relevance scoring based on keyword overlap
        query_words = set(re.findall(r'\w+', query.lower()))
        
        scored_chunks = []
        for chunk in chunks:
            chunk_text = chunk.get('text', '').lower()
            chunk_words = set(re.findall(r'\w+', chunk_text))
            
            # Calculate relevance score
            overlap = len(query_words.intersection(chunk_words))
            relevance_score = overlap / len(query_words) if query_words else 0
            
            scored_chunks.append((chunk, relevance_score))
        
        # Sort by relevance and take top chunks
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in scored_chunks[:self.config.max_sources]]

    def _build_context_section(self, chunks: List[Dict[str, Any]]) -> str:
        """Build the context section with proper formatting."""
        if not chunks:
            return "CONTESTO: Nessun frammento di contesto disponibile."
        
        context_parts = ["CONTESTO DISPONIBILE:"]
        
        for i, chunk in enumerate(chunks, 1):
            # Extract metadata
            metadata = chunk.get('metadata', chunk.get('meta', {}))
            source = metadata.get('source', 'N/A')
            page = metadata.get('page', 'N/A')
            section = metadata.get('section_title', 'N/A')
            namespace = metadata.get('namespace', 'N/A')
            
            # Format chunk
            chunk_text = chunk.get('text', '').strip()
            if not chunk_text:
                continue
                
            context_parts.append(
                f"[Frammento {i}] Fonte: {source} | Pagina: {page} | Sezione: {section} | Namespace: {namespace}\n"
                f"{chunk_text}\n"
            )
        
        return "\n".join(context_parts)

    def _build_reasoning_section(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Build the chain-of-thought reasoning section."""
        return """🤔 **Thinking**

Analizzo la domanda e i frammenti disponibili:

1. **Analisi della domanda**: Identifico cosa viene richiesto
2. **Ricerca nei frammenti**: Esamino i frammenti rilevanti
3. **Collegamento delle informazioni**: Come si collegano i dati
4. **Verifica della completezza**: Controllo se le informazioni sono sufficienti
5. **Sintesi della risposta**: Formulo la risposta finale

Procedo con il ragionamento dettagliato..."""

    def _build_verification_section(self) -> str:
        """Build the self-verification section."""
        return """**Verifica della risposta**:
- ✅ Ogni affermazione è supportata dai frammenti
- ✅ Le citazioni sono accurate
- ✅ Non ho aggiunto informazioni non presenti
- ✅ La risposta è completa e risponde alla domanda
- ✅ Il tono è appropriato e professionale

La risposta è pronta per la consegna."""

    def extract_sources_from_answer(self, answer: str) -> List[str]:
        """Extract source citations from the generated answer."""
        # Find all [Frammento X] citations
        citations = re.findall(r'\[Frammento (\d+)\]', answer)
        # Also find "secondo il frammento analizzato" references
        analyzed_citations = re.findall(r'secondo il frammento analizzato', answer, re.IGNORECASE)
        return list(set(citations + analyzed_citations))

    def validate_answer_quality(self, answer: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate the quality of the generated answer.
        
        Returns:
            Dictionary with validation metrics
        """
        # Extract citations
        citations = self.extract_sources_from_answer(answer)
        
        # Check for uncertainty indicators
        uncertainty_indicators = [
            "non so", "non posso rispondere", "non ho informazioni", 
            "non ci sono informazioni", "non disponibile", "non lo so",
            "incerto", "non sono sicuro", "potrebbe essere"
        ]
        
        answer_lower = answer.lower()
        has_uncertainty = any(indicator in answer_lower for indicator in uncertainty_indicators)
        
        # Check for source citations
        has_citations = len(citations) > 0
        
        # Calculate citation coverage
        citation_coverage = len(citations) / len(context_chunks) if context_chunks else 0
        
        return {
            "has_citations": has_citations,
            "citation_count": len(citations),
            "citation_coverage": citation_coverage,
            "has_uncertainty": has_uncertainty,
            "quality_score": self._calculate_quality_score(answer, has_citations, has_uncertainty)
        }

    def _calculate_quality_score(self, answer: str, has_citations: bool, has_uncertainty: bool) -> float:
        """Calculate a quality score for the answer."""
        score = 0.0
        
        # Base score for having an answer
        if answer.strip():
            score += 0.3
        
        # Bonus for citations
        if has_citations:
            score += 0.4
        
        # Bonus for appropriate uncertainty (when information is missing)
        if has_uncertainty:
            score += 0.2
        
        # Penalty for very short answers (likely incomplete)
        if len(answer.split()) < 10:
            score -= 0.2
        
        return min(1.0, max(0.0, score))

def test_advanced_prompt_engineering():
    """Test the advanced prompt engineering system."""
    print("🧪 Testing Advanced Prompt Engineering")
    
    # Create test data
    test_chunks = [
        {
            "text": "Il corso di Sistemi Operativi vale 9 CFU e non richiede prerequisiti.",
            "metadata": {"source": "database", "namespace": "per_row", "page": "1"}
        },
        {
            "text": "Il professore Maurizio Lenzerini insegna il corso di Sistemi Operativi.",
            "metadata": {"source": "database", "namespace": "per_row", "page": "2"}
        }
    ]
    
    test_query = "Da quanti crediti è il corso di Sistemi Operativi e chi lo insegna?"
    
    # Initialize prompt engineer
    config = PromptConfig(
        use_chain_of_thought=True,
        use_self_verification=True,
        use_source_attribution=True
    )
    
    engineer = AdvancedPromptEngineer(config)
    
    # Test query classification
    query_type = engineer.classify_query_type(test_query)
    print(f"Query type: {query_type}")
    
    # Build advanced prompt
    prompt = engineer.build_advanced_prompt(test_chunks, test_query)
    print(f"\nGenerated prompt length: {len(prompt)} characters")
    print(f"Prompt preview: {prompt[:500]}...")
    
    # Test answer validation
    test_answer = "Il corso di Sistemi Operativi vale 9 CFU [Frammento 1] e viene insegnato dal professor Maurizio Lenzerini [Frammento 2]."
    validation = engineer.validate_answer_quality(test_answer, test_chunks)
    print(f"\nAnswer validation: {validation}")

if __name__ == "__main__":
    test_advanced_prompt_engineering()

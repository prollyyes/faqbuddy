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
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .query_understanding import QueryAnalysis

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
        from utils.unified_system_prompt import get_unified_system_prompt
        return get_unified_system_prompt()

    def _get_factual_system_prompt(self) -> str:
        """Get system prompt for factual queries."""
        from utils.unified_system_prompt import get_unified_system_prompt
        return get_unified_system_prompt()

    def _get_procedural_system_prompt(self) -> str:
        """Get system prompt for procedural queries."""
        from utils.unified_system_prompt import get_unified_system_prompt
        return get_unified_system_prompt()

    def _get_comparative_system_prompt(self) -> str:
        """Get system prompt for comparative queries."""
        from utils.unified_system_prompt import get_unified_system_prompt
        return get_unified_system_prompt()

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
                            query_type: Optional[str] = None,
                            query_analysis: Optional['QueryAnalysis'] = None) -> str:
        """
        Build an advanced prompt with state-of-the-art techniques.
        
        Args:
            context_chunks: Retrieved context chunks
            query: User query
            query_type: Optional query type classification
            query_analysis: Optional QueryAnalysis object for conditional CoT
            
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
        
        # Build reasoning section with conditional CoT usage
        reasoning_section = ""
        should_use_cot = self.config.use_chain_of_thought
        
        # If query analysis is provided, use conditional CoT based on requires_reasoning
        if query_analysis is not None:
            should_use_cot = self.config.use_chain_of_thought and query_analysis.requires_reasoning
            print(f"🧠 Conditional CoT: {'ENABLED' if should_use_cot else 'DISABLED'} (requires_reasoning: {query_analysis.requires_reasoning})")
        
        if should_use_cot:
            reasoning_section = self._build_reasoning_section(query, relevant_chunks)
        
        # Build verification section if self-verification is enabled
        verification_section = ""
        if self.config.use_self_verification:
            verification_section = self._build_verification_section()
        
        # Combine all sections
        # Build the instruction content (everything except the question)
        instruction_content = [
            system_prompt,
            context_section,
            reasoning_section,
            verification_section
        ]
        
        # Use proper Mistral instruction format
        instruction = "\n\n".join(filter(None, instruction_content))
        prompt = f"[INST] {instruction}\n\nDomanda:\n{query} [/INST]"
        
        return prompt

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
            
            # Create clean source reference without brackets --> no more [FRAMMENTO X]
            source_info = f"Fonte: {source}"
            if page != 'N/A':
                source_info += f", Pagina: {page}"
            if section != 'N/A':
                source_info += f", Sezione: {section}"
                
            context_parts.append(
                f"**Documento {i}** ({source_info}):\n{chunk_text}\n"
            )
        
        return "\n".join(context_parts)

    def _build_reasoning_section(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Build the chain-of-thought reasoning section."""
        return """🤔 **Thinking**

Analizzo la domanda e i documenti disponibili:

1. **Comprensione della domanda**: Identifico cosa viene richiesto
2. **Ricerca nei documenti**: Esamino i documenti rilevanti
3. **Collegamento delle informazioni**: Come si collegano i dati trovati
4. **Verifica della completezza**: Controllo se le informazioni sono sufficienti
5. **Sintesi della risposta**: Formulo la risposta finale

Procedo con l'analisi dettagliata..."""

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

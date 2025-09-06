"""
Advanced Query Understanding for State-of-the-Art RAG
====================================================

This module implements advanced query understanding techniques:
- Intent classification
- Query expansion and reformulation
- Entity extraction
- Query complexity analysis
- Multi-turn conversation handling
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class QueryIntent(Enum):
    """Query intent classification."""
    FACTUAL = "factual"           # Who, what, when, where, how many
    PROCEDURAL = "procedural"     # How to, steps, process
    COMPARATIVE = "comparative"   # Compare, vs, better/worse
    EXPLANATORY = "explanatory"   # Why, explain, describe
    CONVERSATIONAL = "conversational"  # Greetings, small talk
    CLARIFICATION = "clarification"    # Follow-up questions

class QueryComplexity(Enum):
    """Query complexity levels."""
    SIMPLE = "simple"        # Single fact or entity
    MODERATE = "moderate"    # Multiple facts or simple reasoning
    COMPLEX = "complex"      # Multi-step reasoning or comparison
    EXPERT = "expert"        # Advanced domain knowledge required

@dataclass
class QueryAnalysis:
    """Result of query analysis."""
    intent: QueryIntent
    complexity: QueryComplexity
    entities: List[str]
    keywords: List[str]
    expanded_queries: List[str]
    confidence: float
    requires_reasoning: bool
    expected_answer_type: str

class AdvancedQueryUnderstanding:
    """
    Advanced query understanding system for RAG.
    
    Features:
    - Intent classification
    - Entity extraction
    - Query expansion
    - Complexity analysis
    - Multi-turn conversation handling
    """
    
    def __init__(self):
        """Initialize the query understanding system."""
        
        # Intent classification patterns
        self.intent_patterns = {
            QueryIntent.FACTUAL: [
                r'\b(chi|cosa|quando|dove|quanti|quante|quale|quali)\b',
                r'\b(da quanti|quanto vale|quanti crediti|chi insegna|dove si trova)\b',
                r'\b(quale professore|quale corso|quale dipartimento)\b',
                r'\b(quando inizia|quando finisce|quando è)\b'
            ],
            QueryIntent.PROCEDURAL: [
                r'\b(come|come fare|come si|procedura|passaggi|step|processo)\b',
                r'\b(come iscriversi|come fare domanda|come richiedere)\b',
                r'\b(come funziona|come procedere|come ottenere)\b',
                r'\b(quali sono i passaggi|cosa devo fare)\b'
            ],
            QueryIntent.COMPARATIVE: [
                r'\b(confronto|differenza|vs|rispetto a|meglio|peggio)\b',
                r'\b(quale scegliere|pro e contro|vantaggi|svantaggi)\b',
                r'\b(più facile|più difficile|più conveniente)\b',
                r'\b(confronta|paragona|differenze tra)\b'
            ],
            QueryIntent.EXPLANATORY: [
                r'\b(perché|perchè|spiega|descrivi|cos\'è|cosa significa)\b',
                r'\b(come mai|in che modo|per quale motivo)\b',
                r'\b(definizione|significato|concetto)\b',
                r'\b(aiutami a capire|puoi spiegarmi)\b'
            ],
            QueryIntent.CONVERSATIONAL: [
                r'\b(ciao|salve|buongiorno|buonasera|grazie|prego)\b',
                r'\b(come stai|tutto bene|come va)\b',
                r'\b(aiuto|aiutami|puoi aiutarmi)\b'
            ],
            QueryIntent.CLARIFICATION: [
                r'\b(non ho capito|puoi ripetere|puoi spiegare meglio)\b',
                r'\b(cosa intendi|non è chiaro|più dettagli)\b',
                r'\b(esempio|esempi|caso specifico)\b'
            ]
        }
        
        # Entity extraction patterns
        self.entity_patterns = {
            'course': [
                r'\b(sistemi operativi|programmazione|algoritmi|basi di dati)\b',
                r'\b(ingegneria|informatica|matematica|fisica)\b',
                r'\b(corso di [a-z\s]+|materia [a-z\s]+)\b'
            ],
            'professor': [
                r'\b(professor|prof\.|professoressa|prof\.ssa)\s+([A-Z][a-z]+)\b',
                r'\b(docente|insegnante)\s+([A-Z][a-z]+)\b',
                r'\b([A-Z][a-z]+)\s+(insegna|è docente|è professore)\b'
            ],
            'department': [
                r'\b(dipartimento|facoltà|scuola)\s+([A-Z][a-z\s]+)\b',
                r'\b(ingegneria informatica|informatica e automatica)\b'
            ],
            'credits': [
                r'\b(\d+)\s*(cfu|crediti|crediti formativi)\b',
                r'\b(da quanti|quanti)\s*(cfu|crediti)\b'
            ],
            'semester': [
                r'\b(semestre|trimestre|quadrimestre)\s*(\d+)\b',
                r'\b(s1|s2|primo semestre|secondo semestre)\b'
            ]
        }
        
        # Query expansion patterns
        self.expansion_patterns = {
            'course_related': {
                'sistemi operativi': ['sistemi operativi e reti', 'so', 'operating systems'],
                'programmazione': ['introduzione alla programmazione', 'programming', 'codice'],
                'algoritmi': ['algoritmi e strutture dati', 'algorithms', 'data structures']
            },
            'professor_related': {
                'lenzerini': ['maurizio lenzerini', 'prof. lenzerini'],
                'petrarca': ['massimo petrarca', 'prof. petrarca']
            }
        }
        
        print("🧠 Initializing Advanced Query Understanding")
        print(f"   Intent patterns: {len(self.intent_patterns)}")
        print(f"   Entity patterns: {len(self.entity_patterns)}")
        print(f"   Expansion patterns: {len(self.expansion_patterns)}")

    def analyze_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> QueryAnalysis:
        """
        Perform comprehensive query analysis.
        
        Args:
            query: User query
            context: Optional conversation context
            
        Returns:
            QueryAnalysis object with all analysis results
        """
        query_lower = query.lower().strip()
        
        # Classify intent
        intent = self._classify_intent(query_lower)
        
        # Extract entities
        entities = self._extract_entities(query_lower)
        
        # Extract keywords
        keywords = self._extract_keywords(query_lower)
        
        # Expand query
        expanded_queries = self._expand_query(query_lower, entities, keywords)
        
        # Analyze complexity
        complexity = self._analyze_complexity(query_lower, entities, intent)
        
        # Determine if reasoning is required
        requires_reasoning = self._requires_reasoning(intent, complexity, entities)
        
        # Determine expected answer type
        expected_answer_type = self._get_expected_answer_type(intent, entities)
        
        # Calculate confidence
        confidence = self._calculate_confidence(intent, entities, keywords)
        
        return QueryAnalysis(
            intent=intent,
            complexity=complexity,
            entities=entities,
            keywords=keywords,
            expanded_queries=expanded_queries,
            confidence=confidence,
            requires_reasoning=requires_reasoning,
            expected_answer_type=expected_answer_type
        )

    def _classify_intent(self, query: str) -> QueryIntent:
        """Classify the intent of the query."""
        scores = {}
        
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                score += len(matches)
            scores[intent] = score
        
        # Return intent with highest score, default to factual
        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        return QueryIntent.FACTUAL

    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities from the query."""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, query, re.IGNORECASE)
                for match in matches:
                    if isinstance(match, tuple):
                        entities.extend([m for m in match if m.strip()])
                    else:
                        entities.append(match.strip())
        
        return list(set(entities))  # Remove duplicates

    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from the query."""
        # Remove common stop words
        stop_words = {
            'il', 'la', 'lo', 'gli', 'le', 'di', 'da', 'in', 'con', 'su', 'per', 'tra', 'fra',
            'un', 'una', 'uno', 'del', 'della', 'dei', 'delle', 'al', 'alla', 'ai', 'alle',
            'che', 'chi', 'cui', 'quale', 'quali', 'quanto', 'quanta', 'quanti', 'quante',
            'è', 'sono', 'ha', 'hanno', 'fa', 'fanno', 'va', 'vanno', 'sta', 'stanno',
            'e', 'o', 'ma', 'però', 'quindi', 'allora', 'così', 'anche', 'pure', 'solo'
        }
        
        # Extract words
        words = re.findall(r'\b[a-z]+\b', query.lower())
        
        # Filter out stop words and short words
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return list(set(keywords))

    def _expand_query(self, query: str, entities: List[str], keywords: List[str]) -> List[str]:
        """Expand the query with related terms and synonyms."""
        expanded_queries = [query]  # Start with original query
        
        # Expand based on entities
        for entity in entities:
            for category, expansions in self.expansion_patterns.items():
                for key, synonyms in expansions.items():
                    if key.lower() in entity.lower():
                        for synonym in synonyms:
                            expanded_query = query.replace(key, synonym)
                            if expanded_query != query:
                                expanded_queries.append(expanded_query)
        
        # Expand based on keywords
        for keyword in keywords:
            for category, expansions in self.expansion_patterns.items():
                if keyword in expansions:
                    for synonym in expansions[keyword]:
                        expanded_query = query.replace(keyword, synonym)
                        if expanded_query != query:
                            expanded_queries.append(expanded_query)
        
        return list(set(expanded_queries))  # Remove duplicates

    def _analyze_complexity(self, query: str, entities: List[str], intent: QueryIntent) -> QueryComplexity:
        """Analyze the complexity of the query."""
        complexity_score = 0
        
        # Base complexity by intent
        intent_complexity = {
            QueryIntent.FACTUAL: 1,
            QueryIntent.PROCEDURAL: 2,
            QueryIntent.COMPARATIVE: 3,
            QueryIntent.EXPLANATORY: 3,
            QueryIntent.CONVERSATIONAL: 1,
            QueryIntent.CLARIFICATION: 2
        }
        complexity_score += intent_complexity.get(intent, 1)
        
        # Add complexity for multiple entities
        complexity_score += min(len(entities), 3)
        
        # Add complexity for long queries
        if len(query.split()) > 10:
            complexity_score += 1
        
        # Add complexity for multiple question words
        question_words = re.findall(r'\b(chi|cosa|quando|dove|come|perché|perchè|quale|quali|quanto|quanti)\b', query)
        if len(question_words) > 1:
            complexity_score += 1
        
        # Determine complexity level
        if complexity_score <= 2:
            return QueryComplexity.SIMPLE
        elif complexity_score <= 4:
            return QueryComplexity.MODERATE
        elif complexity_score <= 6:
            return QueryComplexity.COMPLEX
        else:
            return QueryComplexity.EXPERT

    def _requires_reasoning(self, intent: QueryIntent, complexity: QueryComplexity, entities: List[str]) -> bool:
        """Determine if the query requires multi-step reasoning."""
        # High complexity queries require reasoning
        if complexity in [QueryComplexity.COMPLEX, QueryComplexity.EXPERT]:
            return True
        
        # Comparative and explanatory queries require reasoning
        if intent in [QueryIntent.COMPARATIVE, QueryIntent.EXPLANATORY]:
            return True
        
        # Multiple entities often require reasoning
        if len(entities) > 2:
            return True
        
        return False

    def _get_expected_answer_type(self, intent: QueryIntent, entities: List[str]) -> str:
        """Determine the expected type of answer."""
        if intent == QueryIntent.FACTUAL:
            if any('cfu' in entity.lower() or 'crediti' in entity.lower() for entity in entities):
                return "numerical"
            elif any('professor' in entity.lower() or 'docente' in entity.lower() for entity in entities):
                return "person"
            else:
                return "factual"
        elif intent == QueryIntent.PROCEDURAL:
            return "step_by_step"
        elif intent == QueryIntent.COMPARATIVE:
            return "comparison"
        elif intent == QueryIntent.EXPLANATORY:
            return "explanation"
        else:
            return "general"

    def _calculate_confidence(self, intent: QueryIntent, entities: List[str], keywords: List[str]) -> float:
        """Calculate confidence in the query analysis."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for clear intent patterns
        if intent != QueryIntent.FACTUAL:  # Non-default intent
            confidence += 0.2
        
        # Increase confidence for entity extraction
        if entities:
            confidence += 0.2
        
        # Increase confidence for relevant keywords
        if len(keywords) >= 2:
            confidence += 0.1
        
        return min(1.0, confidence)

    def get_retrieval_strategy(self, analysis: QueryAnalysis) -> Dict[str, Any]:
        """Get retrieval strategy based on query analysis."""
        strategy = {
            "top_k": 50,  # Default
            "reranker_threshold": 0.1,  # Default
            "use_hybrid_search": False,
            "boost_namespaces": {},
            "query_expansion": False
        }
        
        # Adjust strategy based on complexity
        if analysis.complexity == QueryComplexity.SIMPLE:
            strategy["top_k"] = 30
            strategy["reranker_threshold"] = 0.2
        elif analysis.complexity == QueryComplexity.MODERATE:
            strategy["top_k"] = 50
            strategy["reranker_threshold"] = 0.1
        elif analysis.complexity == QueryComplexity.COMPLEX:
            strategy["top_k"] = 75
            strategy["reranker_threshold"] = 0.05
            strategy["use_hybrid_search"] = True
        else:  # EXPERT
            strategy["top_k"] = 100
            strategy["reranker_threshold"] = 0.01
            strategy["use_hybrid_search"] = True
            strategy["query_expansion"] = True
        
        # Adjust strategy based on intent
        if analysis.intent == QueryIntent.FACTUAL:
            strategy["boost_namespaces"]["per_row"] = 1.5
        elif analysis.intent == QueryIntent.PROCEDURAL:
            strategy["boost_namespaces"]["documents_v2"] = 1.3
        elif analysis.intent == QueryIntent.COMPARATIVE:
            strategy["use_hybrid_search"] = True
            strategy["query_expansion"] = True
        
        return strategy

def test_query_understanding():
    """Test the query understanding system."""
    print("🧪 Testing Advanced Query Understanding")
    
    # Initialize system
    qa_system = AdvancedQueryUnderstanding()
    
    # Test queries
    test_queries = [
        "Da quanti crediti è il corso di Sistemi Operativi?",
        "Chi insegna il corso di Programmazione?",
        "Come posso iscrivermi al corso di Algoritmi?",
        "Qual è la differenza tra Sistemi Operativi e Reti di Calcolatori?",
        "Spiega cos'è un sistema operativo",
        "Ciao, puoi aiutarmi?"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        analysis = qa_system.analyze_query(query)
        
        print(f"   Intent: {analysis.intent.value}")
        print(f"   Complexity: {analysis.complexity.value}")
        print(f"   Entities: {analysis.entities}")
        print(f"   Keywords: {analysis.keywords}")
        print(f"   Requires reasoning: {analysis.requires_reasoning}")
        print(f"   Expected answer type: {analysis.expected_answer_type}")
        print(f"   Confidence: {analysis.confidence:.2f}")
        
        strategy = qa_system.get_retrieval_strategy(analysis)
        print(f"   Retrieval strategy: {strategy}")

if __name__ == "__main__":
    test_query_understanding()

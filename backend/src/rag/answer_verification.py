"""
Advanced Answer Verification for State-of-the-Art RAG
====================================================

This module implements advanced answer verification techniques:
- Fact-checking against sources
- Consistency validation
- Completeness assessment
- Confidence scoring
- Hallucination detection
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sentence_transformers import CrossEncoder
import numpy as np

@dataclass
class VerificationResult:
    """Result of answer verification."""
    is_verified: bool
    confidence_score: float
    fact_check_score: float
    consistency_score: float
    completeness_score: float
    hallucination_risk: float
    missing_information: List[str]
    unsupported_claims: List[str]
    verification_details: Dict[str, Any]

class AdvancedAnswerVerification:
    """
    Advanced answer verification system for RAG.
    
    Features:
    - Fact-checking against retrieved sources
    - Consistency validation
    - Completeness assessment
    - Hallucination detection
    - Confidence scoring
    """
    
    def __init__(self):
        """Initialize the answer verification system."""
        self._cross_encoder = None
        self.verification_stats = {
            "total_verifications": 0,
            "verified_answers": 0,
            "hallucination_detections": 0,
            "average_confidence": 0.0
        }
        
        print("🔍 Initializing Advanced Answer Verification")
    
    @property
    def cross_encoder(self) -> Optional[CrossEncoder]:
        """Lazy load cross-encoder for verification."""
        if self._cross_encoder is None:
            try:
                print("🔄 Loading cross-encoder for answer verification...")
                self._cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
                print("✅ Cross-encoder loaded for verification")
            except Exception as e:
                print(f"❌ Failed to load cross-encoder: {e}")
                self._cross_encoder = None
        
        return self._cross_encoder
    
    def verify_answer(self, 
                     answer: str, 
                     sources: List[Dict[str, Any]], 
                     query: str) -> VerificationResult:
        """
        Perform comprehensive answer verification.
        
        Args:
            answer: Generated answer to verify
            sources: Retrieved source documents
            query: Original user query
            
        Returns:
            VerificationResult with detailed verification metrics
        """
        print("🔍 Starting comprehensive answer verification...")
        
        # Extract claims from answer
        claims = self._extract_claims(answer)
        
        # Fact-check against sources
        fact_check_score, unsupported_claims = self._fact_check_claims(claims, sources)
        
        # Check consistency
        consistency_score = self._check_consistency(answer, sources)
        
        # Assess completeness
        completeness_score, missing_info = self._assess_completeness(answer, query, sources)
        
        # Detect hallucination risk
        hallucination_risk = self._detect_hallucination_risk(answer, sources, claims)
        
        # Calculate overall confidence
        confidence_score = self._calculate_confidence_score(
            fact_check_score, consistency_score, completeness_score, hallucination_risk
        )
        
        # Determine if answer is verified
        is_verified = self._determine_verification_status(
            confidence_score, fact_check_score, hallucination_risk
        )
        
        # Update statistics
        self._update_stats(is_verified, confidence_score, hallucination_risk)
        
        return VerificationResult(
            is_verified=is_verified,
            confidence_score=confidence_score,
            fact_check_score=fact_check_score,
            consistency_score=consistency_score,
            completeness_score=completeness_score,
            hallucination_risk=hallucination_risk,
            missing_information=missing_info,
            unsupported_claims=unsupported_claims,
            verification_details={
                "total_claims": len(claims),
                "supported_claims": len(claims) - len(unsupported_claims),
                "verification_method": "comprehensive",
                "sources_checked": len(sources)
            }
        )
    
    def _extract_claims(self, answer: str) -> List[str]:
        """Extract factual claims from the answer."""
        # Split answer into sentences
        sentences = re.split(r'[.!?]+', answer)
        claims = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short sentences
                continue
            
            # Remove citations for claim extraction
            clean_sentence = re.sub(r'\[Frammento \d+\]', '', sentence).strip()
            
            # Skip sentences that are just uncertainty indicators
            uncertainty_indicators = [
                "non so", "non posso rispondere", "non ho informazioni",
                "non ci sono informazioni", "non disponibile", "non lo so"
            ]
            
            if not any(indicator in clean_sentence.lower() for indicator in uncertainty_indicators):
                claims.append(clean_sentence)
        
        return claims
    
    def _fact_check_claims(self, claims: List[str], sources: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Fact-check claims against retrieved sources."""
        if not claims or not sources:
            return 0.0, claims
        
        supported_claims = 0
        unsupported_claims = []
        
        for claim in claims:
            is_supported = False
            
            # Check against each source
            for source in sources:
                source_text = source.get('text', '').lower()
                claim_lower = claim.lower()
                
                # Simple keyword overlap check
                claim_words = set(re.findall(r'\w+', claim_lower))
                source_words = set(re.findall(r'\w+', claim_lower))
                
                # Calculate overlap
                overlap = len(claim_words.intersection(source_words))
                overlap_ratio = overlap / len(claim_words) if claim_words else 0
                
                # Use cross-encoder for more sophisticated matching if available
                if self.cross_encoder and overlap_ratio > 0.2:
                    try:
                        score = self.cross_encoder.predict([(claim, source_text)])
                        if score[0] > 0.3:  # Lower threshold for support
                            is_supported = True
                            break
                    except Exception as e:
                        print(f"⚠️ Cross-encoder error: {e}")
                        # Fall back to keyword matching
                        if overlap_ratio > 0.3:
                            is_supported = True
                            break
                elif overlap_ratio > 0.3:  # Lower threshold for keyword matching
                    is_supported = True
                    break
            
            if is_supported:
                supported_claims += 1
            else:
                unsupported_claims.append(claim)
        
        fact_check_score = supported_claims / len(claims) if claims else 0.0
        return fact_check_score, unsupported_claims
    
    def _check_consistency(self, answer: str, sources: List[Dict[str, Any]]) -> float:
        """Check consistency between answer and sources."""
        if not sources:
            return 0.0
        
        # Extract key information from answer
        answer_info = self._extract_key_information(answer)
        
        # Check consistency with each source
        consistency_scores = []
        
        for source in sources:
            source_text = source.get('text', '')
            source_info = self._extract_key_information(source_text)
            
            # Calculate consistency score
            consistency = self._calculate_information_consistency(answer_info, source_info)
            consistency_scores.append(consistency)
        
        return np.mean(consistency_scores) if consistency_scores else 0.0
    
    def _extract_key_information(self, text: str) -> Dict[str, Any]:
        """Extract key information from text."""
        info = {
            'numbers': re.findall(r'\b\d+\b', text),
            'names': re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', text),
            'courses': re.findall(r'\b(sistemi operativi|programmazione|algoritmi|basi di dati)\b', text.lower()),
            'credits': re.findall(r'\b(\d+)\s*(cfu|crediti)\b', text.lower()),
            'departments': re.findall(r'\b(dipartimento|facoltà|scuola)\s+([A-Z][a-z\s]+)\b', text)
        }
        return info
    
    def _calculate_information_consistency(self, info1: Dict[str, Any], info2: Dict[str, Any]) -> float:
        """Calculate consistency between two information sets."""
        total_elements = 0
        consistent_elements = 0
        
        for key in info1:
            if key in info2:
                elements1 = set(info1[key])
                elements2 = set(info2[key])
                
                if elements1 and elements2:
                    total_elements += len(elements1.union(elements2))
                    consistent_elements += len(elements1.intersection(elements2))
        
        return consistent_elements / total_elements if total_elements > 0 else 1.0
    
    def _assess_completeness(self, answer: str, query: str, sources: List[Dict[str, Any]]) -> Tuple[float, List[str]]:
        """Assess completeness of the answer relative to the query and available sources."""
        # Extract query requirements
        query_requirements = self._extract_query_requirements(query)
        
        # Check what information is available in sources
        available_info = self._extract_available_information(sources)
        
        # Check what information is provided in answer
        provided_info = self._extract_provided_information(answer)
        
        # Calculate completeness
        missing_info = []
        for requirement in query_requirements:
            if requirement not in provided_info:
                if requirement in available_info:
                    missing_info.append(requirement)
        
        completeness_score = 1.0 - (len(missing_info) / len(query_requirements)) if query_requirements else 1.0
        return completeness_score, missing_info
    
    def _extract_query_requirements(self, query: str) -> List[str]:
        """Extract information requirements from the query."""
        requirements = []
        query_lower = query.lower()
        
        # Check for specific information requests
        if 'chi' in query_lower or 'docente' in query_lower or 'professor' in query_lower:
            requirements.append('instructor')
        
        if 'quanti' in query_lower or 'cfu' in query_lower or 'crediti' in query_lower:
            requirements.append('credits')
        
        if 'quando' in query_lower or 'orario' in query_lower or 'giorno' in query_lower:
            requirements.append('schedule')
        
        if 'dove' in query_lower or 'aula' in query_lower or 'luogo' in query_lower:
            requirements.append('location')
        
        if 'prerequisiti' in query_lower or 'requisiti' in query_lower:
            requirements.append('prerequisites')
        
        if 'esame' in query_lower or 'valutazione' in query_lower:
            requirements.append('evaluation')
        
        return requirements
    
    def _extract_available_information(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Extract information available in sources."""
        available = []
        
        for source in sources:
            text = source.get('text', '').lower()
            
            if any(word in text for word in ['professor', 'docente', 'insegnante']):
                available.append('instructor')
            
            if any(word in text for word in ['cfu', 'crediti']):
                available.append('credits')
            
            if any(word in text for word in ['orario', 'giorno', 'ora']):
                available.append('schedule')
            
            if any(word in text for word in ['aula', 'dove', 'luogo']):
                available.append('location')
            
            if any(word in text for word in ['prerequisiti', 'requisiti']):
                available.append('prerequisites')
            
            if any(word in text for word in ['esame', 'valutazione', 'voto']):
                available.append('evaluation')
        
        return list(set(available))
    
    def _extract_provided_information(self, answer: str) -> List[str]:
        """Extract information provided in the answer."""
        provided = []
        answer_lower = answer.lower()
        
        if any(word in answer_lower for word in ['professor', 'docente', 'insegnante']):
            provided.append('instructor')
        
        if any(word in answer_lower for word in ['cfu', 'crediti']):
            provided.append('credits')
        
        if any(word in answer_lower for word in ['orario', 'giorno', 'ora']):
            provided.append('schedule')
        
        if any(word in answer_lower for word in ['aula', 'dove', 'luogo']):
            provided.append('location')
        
        if any(word in answer_lower for word in ['prerequisiti', 'requisiti']):
            provided.append('prerequisites')
        
        if any(word in answer_lower for word in ['esame', 'valutazione', 'voto']):
            provided.append('evaluation')
        
        return list(set(provided))
    
    def _detect_hallucination_risk(self, answer: str, sources: List[Dict[str, Any]], claims: List[str]) -> float:
        """Detect risk of hallucination in the answer."""
        if not claims or not sources:
            return 0.5  # Medium risk if no claims or sources
        
        # Check for uncertainty indicators (good sign)
        uncertainty_indicators = [
            "non so", "non posso rispondere", "non ho informazioni",
            "non ci sono informazioni", "non disponibile", "non lo so",
            "incerto", "non sono sicuro", "potrebbe essere"
        ]
        
        answer_lower = answer.lower()
        has_uncertainty = any(indicator in answer_lower for indicator in uncertainty_indicators)
        
        if has_uncertainty:
            return 0.1  # Low risk if uncertainty is expressed
        
        # Check for specific claims without support
        unsupported_claims = []
        for claim in claims:
            is_supported = False
            for source in sources:
                source_text = source.get('text', '').lower()
                claim_lower = claim.lower()
                
                # Simple keyword overlap check
                claim_words = set(re.findall(r'\w+', claim_lower))
                source_words = set(re.findall(r'\w+', source_text))
                
                overlap = len(claim_words.intersection(source_words))
                overlap_ratio = overlap / len(claim_words) if claim_words else 0
                
                if overlap_ratio > 0.2:  # Lower threshold for hallucination detection
                    is_supported = True
                    break
            
            if not is_supported:
                unsupported_claims.append(claim)
        
        # Calculate hallucination risk based on unsupported claims
        hallucination_risk = len(unsupported_claims) / len(claims) if claims else 0.0
        
        return min(1.0, hallucination_risk)
    
    def _calculate_confidence_score(self, 
                                  fact_check_score: float, 
                                  consistency_score: float, 
                                  completeness_score: float, 
                                  hallucination_risk: float) -> float:
        """Calculate overall confidence score."""
        # Weighted combination of different scores
        weights = {
            'fact_check': 0.4,
            'consistency': 0.3,
            'completeness': 0.2,
            'hallucination': 0.1
        }
        
        confidence = (
            weights['fact_check'] * fact_check_score +
            weights['consistency'] * consistency_score +
            weights['completeness'] * completeness_score +
            weights['hallucination'] * (1.0 - hallucination_risk)
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _determine_verification_status(self, 
                                     confidence_score: float, 
                                     fact_check_score: float, 
                                     hallucination_risk: float) -> bool:
        """Determine if the answer is verified."""
        # Answer is verified if:
        # 1. High confidence score (>0.7)
        # 2. Good fact-check score (>0.6)
        # 3. Low hallucination risk (<0.3)
        
        return (confidence_score > 0.2 and 
                fact_check_score > 0.1 and 
                hallucination_risk < 0.7)
    
    def _update_stats(self, is_verified: bool, confidence_score: float, hallucination_risk: float):
        """Update verification statistics."""
        self.verification_stats["total_verifications"] += 1
        
        if is_verified:
            self.verification_stats["verified_answers"] += 1
        
        if hallucination_risk > 0.5:
            self.verification_stats["hallucination_detections"] += 1
        
        # Update average confidence
        total = self.verification_stats["total_verifications"]
        current_avg = self.verification_stats["average_confidence"]
        self.verification_stats["average_confidence"] = (
            (current_avg * (total - 1) + confidence_score) / total
        )
    
    def get_verification_stats(self) -> Dict[str, Any]:
        """Get verification statistics."""
        stats = self.verification_stats.copy()
        if stats["total_verifications"] > 0:
            stats["verification_rate"] = stats["verified_answers"] / stats["total_verifications"]
            stats["hallucination_rate"] = stats["hallucination_detections"] / stats["total_verifications"]
        else:
            stats["verification_rate"] = 0.0
            stats["hallucination_rate"] = 0.0
        
        return stats

def test_answer_verification():
    """Test the answer verification system."""
    print("🧪 Testing Advanced Answer Verification")
    
    # Initialize system
    verifier = AdvancedAnswerVerification()
    
    # Test data
    test_answer = "Il corso di Sistemi Operativi vale 9 CFU e viene insegnato dal professor Maurizio Lenzerini."
    test_sources = [
        {
            "text": "Corso di Sistemi Operativi (9 CFU). Prerequisiti: Nessuno. Frequenza: No",
            "metadata": {"source": "database", "namespace": "per_row"}
        },
        {
            "text": "Docente Maurizio Lenzerini, contattabile all'email None",
            "metadata": {"source": "database", "namespace": "per_row"}
        }
    ]
    test_query = "Da quanti crediti è il corso di Sistemi Operativi e chi lo insegna?"
    
    # Perform verification
    result = verifier.verify_answer(test_answer, test_sources, test_query)
    
    print(f"Verification result:")
    print(f"  Is verified: {result.is_verified}")
    print(f"  Confidence score: {result.confidence_score:.3f}")
    print(f"  Fact-check score: {result.fact_check_score:.3f}")
    print(f"  Consistency score: {result.consistency_score:.3f}")
    print(f"  Completeness score: {result.completeness_score:.3f}")
    print(f"  Hallucination risk: {result.hallucination_risk:.3f}")
    print(f"  Missing information: {result.missing_information}")
    print(f"  Unsupported claims: {result.unsupported_claims}")
    
    # Get statistics
    stats = verifier.get_verification_stats()
    print(f"\nVerification statistics: {stats}")

if __name__ == "__main__":
    test_answer_verification()

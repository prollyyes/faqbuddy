"""
Generation Guard-rails for RAGv2
================================

This module implements the next task: Generation guard-rails.
Features:
- Self-check prompt: "Using only the sources above, answer. If unsure, say you don't know."
- Answer verification using reranker scores
- Hallucination detection and refusal
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from sentence_transformers import CrossEncoder
from .config import HALLUCINATION_GUARDS, RERANKER_THRESHOLD, CROSS_ENCODER_MODEL
from ..utils.llm_mistral import generate_answer

class GenerationGuards:
    """
    Generation guard-rails to prevent hallucinations and ensure answer quality.
    
    Features:
    - Self-check prompts for answer generation
    - Answer verification using cross-encoder
    - Hallucination detection and refusal
    """
    
    def __init__(self):
        """Initialize the generation guards system."""
        self._cross_encoder = None
        self.guard_stats = {
            "hallucination_checks": 0,
            "refusals": 0,
            "verification_time": 0
        }
        
        print("🛡️ Initializing Generation Guards")
        print(f"   Hallucination guards enabled: {HALLUCINATION_GUARDS}")
        print(f"   Verification threshold: {RERANKER_THRESHOLD}")
    
    @property
    def cross_encoder(self) -> Optional[CrossEncoder]:
        """Lazy load cross-encoder for answer verification."""
        if self._cross_encoder is None and HALLUCINATION_GUARDS:
            try:
                print(f"🔄 Loading cross-encoder for answer verification: {CROSS_ENCODER_MODEL}")
                self._cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
                print("✅ Cross-encoder loaded for verification")
            except Exception as e:
                print(f"❌ Failed to load cross-encoder for verification: {e}")
                self._cross_encoder = None
        
        return self._cross_encoder
    
    def create_self_check_prompt(self, context: List[Dict[str, Any]], question: str) -> str:
        """
        Create a prompt with self-check instructions.
        
        Args:
            context: Retrieved context documents
            question: User question
            
        Returns:
            Prompt with self-check instructions
        """
        # Build context text
        context_text = ""
        for i, doc in enumerate(context, 1):
            # Try to get text from different possible locations
            text = ""
            if 'text' in doc:
                text = doc['text']
            elif 'metadata' in doc and 'text' in doc['metadata']:
                text = doc['metadata']['text']
            
            if text.strip():
                context_text += f"Document {i}: {text}\n\n"
        
        # Create self-check prompt
        prompt = f"""Sei un assistente utile. Rispondi alla seguente domanda usando SOLO le informazioni fornite nei documenti qui sotto.

IMPORTANTE: Se la risposta non può essere trovata nei documenti forniti, di' "Non lo so" o "In base alle informazioni disponibili, non posso rispondere a questa domanda." Non inventare informazioni.

Documenti:
{context_text}

Domanda: {question}

Rispondi usando solo le fonti sopra indicate:"""
        
        return prompt
    
    def verify_answer_against_sources(self, answer: str, sources: List[Dict[str, Any]]) -> Tuple[float, bool]:
        """
        Verify answer against source documents using cross-encoder.
        
        Args:
            answer: Generated answer
            sources: Source documents used for generation
            
        Returns:
            Tuple of (mean_score, is_acceptable)
        """
        if not HALLUCINATION_GUARDS or not self.cross_encoder:
            return 1.0, True  # Skip verification if disabled
        
        start_time = time.time()
        
        # Prepare pairs for cross-encoder
        pairs = []
        for source in sources:
            # Try to get text from different possible locations
            source_text = ""
            if 'text' in source:
                source_text = source['text']
            elif 'metadata' in source and 'text' in source['metadata']:
                source_text = source['metadata']['text']
            
            # Only add non-empty source texts
            if source_text.strip():
                pairs.append([answer, source_text])
        
        if not pairs:
            return 0.0, False
        
        # Get cross-encoder scores
        scores = self.cross_encoder.predict(pairs)
        scores = [float(s) for s in scores]
        
        # Calculate mean score
        mean_score = sum(scores) / len(scores)
        
        # Determine if answer is acceptable
        is_acceptable = mean_score >= RERANKER_THRESHOLD
        
        self.guard_stats["verification_time"] += time.time() - start_time
        self.guard_stats["hallucination_checks"] += 1
        
        if not is_acceptable:
            self.guard_stats["refusals"] += 1
        
        print(f"🔍 Answer verification: mean_score={mean_score:.3f}, acceptable={is_acceptable}")
        
        return mean_score, is_acceptable
    
    def generate_safe_answer(self, context: List[Dict[str, Any]], question: str) -> Dict[str, Any]:
        """
        Generate an answer with hallucination protection.
        
        Args:
            context: Retrieved context documents
            question: User question
            
        Returns:
            Dictionary with answer and verification info
        """
        if not HALLUCINATION_GUARDS:
            # Generate answer without guards
            prompt = self.create_self_check_prompt(context, question)
            answer = generate_answer(prompt, question)
            return {
                "answer": answer,
                "verification_score": 1.0,
                "is_verified": True,
                "guards_enabled": False
            }
        
        # Generate answer with self-check prompt
        prompt = self.create_self_check_prompt(context, question)
        answer = generate_answer(prompt, question)
        
        # Check for explicit uncertainty indicators (Italian first, then English)
        uncertainty_indicators = [
            "non so", "non posso rispondere", "non ho informazioni", 
            "non ci sono informazioni", "non disponibile", "non lo so",
            "i don't know", "i cannot answer"
        ]
        
        answer_lower = answer.lower()
        has_uncertainty = any(indicator in answer_lower for indicator in uncertainty_indicators)
        
        if has_uncertainty:
            print("🛡️ Answer indicates uncertainty, accepting without verification")
            return {
                "answer": answer,
                "verification_score": 1.0,
                "is_verified": True,
                "guards_enabled": True,
                "uncertainty_detected": True
            }
        
        # Verify answer against sources
        verification_score, is_acceptable = self.verify_answer_against_sources(answer, context)
        
        if not is_acceptable:
            # Generate refusal message
            refusal_answer = "Non sono sicuro dell'informazione disponibile. Per favore, riprova a formulare la domanda in modo diverso o contatta il dipartimento appropriato per informazioni più specifiche."
            print("🛡️ Answer verification failed, returning refusal")
            
            return {
                "answer": refusal_answer,
                "verification_score": verification_score,
                "is_verified": False,
                "guards_enabled": True,
                "refusal_reason": "low_verification_score"
            }
        
        return {
            "answer": answer,
            "verification_score": verification_score,
            "is_verified": True,
            "guards_enabled": True
        }
    
    def get_guard_stats(self) -> Dict[str, Any]:
        """Get generation guard statistics."""
        stats = self.guard_stats.copy()
        
        if stats["hallucination_checks"] > 0:
            stats["refusal_rate"] = stats["refusals"] / stats["hallucination_checks"]
            stats["average_verification_time"] = stats["verification_time"] / stats["hallucination_checks"]
        else:
            stats["refusal_rate"] = 0.0
            stats["average_verification_time"] = 0.0
        
        return stats


def test_generation_guards():
    """Test the generation guards functionality."""
    print("🧪 Testing Generation Guards...")
    
    guards = GenerationGuards()
    
    # Test context and question
    context = [
        {
            "metadata": {
                "text": "The Operating Systems course is taught by Professor Mario Rossi in the first semester. The course covers process management, memory management, and file systems."
            }
        },
        {
            "metadata": {
                "text": "Professor Mario Rossi has been teaching at the university for 10 years. His office is located in Building A, Room 205."
            }
        }
    ]
    
    question = "Who teaches Operating Systems this semester?"
    
    # Test answer generation
    result = guards.generate_safe_answer(context, question)
    
    print(f"✅ Generation guards test completed")
    print(f"📊 Result: {result}")
    
    # Check required fields
    required_fields = ["answer", "verification_score", "is_verified", "guards_enabled"]
    for field in required_fields:
        if field not in result:
            print(f"❌ Missing field: {field}")
            return False
    
    print("✅ All required fields present")
    
    # Check stats
    stats = guards.get_guard_stats()
    print(f"📈 Guard stats: {stats}")
    
    return True


def test_hallucination_detection():
    """Test hallucination detection with synthetic data."""
    print("🧪 Testing Hallucination Detection...")
    
    guards = GenerationGuards()
    
    # Test with conflicting information
    context = [
        {
            "metadata": {
                "text": "The course is taught by Professor Rossi."
            }
        }
    ]
    
    # Simulate a hallucinated answer
    hallucinated_answer = "The course is taught by Professor Bianchi, who has won multiple teaching awards and has published 50 papers in top journals."
    
    # Verify the hallucinated answer
    score, is_acceptable = guards.verify_answer_against_sources(hallucinated_answer, context)
    
    print(f"🔍 Hallucination test:")
    print(f"   Answer: {hallucinated_answer}")
    print(f"   Verification score: {score:.3f}")
    print(f"   Is acceptable: {is_acceptable}")
    
    # Check if hallucination was detected
    if not is_acceptable:
        print("✅ Hallucination detection working correctly")
        return True
    else:
        print("❌ Hallucination detection failed")
        return False


if __name__ == "__main__":
    test_generation_guards()
    test_hallucination_detection() 
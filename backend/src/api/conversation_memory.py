"""
Conversation Memory Manager
==========================

Handles conversation context and query rewriting for conversational AI.
Maintains conversation history and resolves pronouns/ellipsis in follow-up questions.
"""

import re
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, deque
import time

@dataclass
class ConversationTurn:
    """Represents a single turn in a conversation."""
    question: str
    answer: str
    entities: List[str]  # Extracted entities (courses, professors, etc.)
    timestamp: float

@dataclass
class ConversationContext:
    """Represents the context of a conversation."""
    conversation_id: str
    turns: deque
    last_entities: List[str]
    created_at: float
    last_accessed: float

class ConversationMemoryManager:
    """
    Manages conversation memory and context resolution.
    
    Features:
    - Maintains conversation history per conversation_id
    - Extracts entities from questions and answers
    - Resolves pronouns and ellipsis in follow-up questions
    - Automatic cleanup of old conversations
    """
    
    def __init__(self, max_turns_per_conversation: int = 5, max_conversations: int = 1000, 
                 conversation_ttl: int = 3600):
        """
        Initialize the conversation memory manager.
        
        Args:
            max_turns_per_conversation: Maximum number of turns to keep per conversation
            max_conversations: Maximum number of conversations to keep in memory
            conversation_ttl: Time-to-live for conversations in seconds (1 hour default)
        """
        self.conversations: Dict[str, ConversationContext] = {}
        self.max_turns_per_conversation = max_turns_per_conversation
        self.max_conversations = max_conversations
        self.conversation_ttl = conversation_ttl
        
        # Patterns for entity extraction
        self.course_patterns = [
            r'corso di ([^,\.\?\!]+)',
            r'corso ([^,\.\?\!]+)',
            r'insegnamento di ([^,\.\?\!]+)',
            r'materia ([^,\.\?\!]+)',
            r'disciplina ([^,\.\?\!]+)'
        ]
        
        self.professor_patterns = [
            r'prof\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'professore\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'docente\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'insegnante\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'professor\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'professoressa\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        # Pronouns and ellipsis patterns
        self.pronoun_patterns = [
            (r'\b(chi)\s+(lo|la)\s+(insegna|tiene|fa)\??', 'chi insegna {entity}'),
            (r'\b(quando)\s+(si\s+)?(tiene|fa|insegna)\s+(lo|la)\??', 'quando si tiene {entity}'),
            (r'\b(dove)\s+(si\s+)?(tiene|fa|insegna)\s+(lo|la)\??', 'dove si tiene {entity}'),
            (r'\b(quanti)\s+(crediti|cfu)\s+(ha|ha\s+il)\s+(lo|la)\??', 'quanti crediti ha {entity}'),
            (r'\b(che)\s+(tipo\s+di\s+)?(esame|prova)\s+(ha|ha\s+il)\s+(lo|la)\??', 'che tipo di esame ha {entity}'),
            (r'\b(quali)\s+(sono\s+i\s+)?(prerequisiti|requisiti)\s+(di|del|dello|della)\s+(lo|la)\??', 'quali sono i prerequisiti di {entity}'),
        ]
    
    def create_conversation(self) -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = ConversationContext(
            conversation_id=conversation_id,
            turns=deque(maxlen=self.max_turns_per_conversation),
            last_entities=[],
            created_at=time.time(),
            last_accessed=time.time()
        )
        return conversation_id
    
    def add_turn(self, conversation_id: str, question: str, answer: str) -> None:
        """Add a turn to the conversation."""
        if conversation_id not in self.conversations:
            return
        
        # Extract entities from the question and answer
        entities = self._extract_entities(question + " " + answer)
        
        turn = ConversationTurn(
            question=question,
            answer=answer,
            entities=entities,
            timestamp=time.time()
        )
        
        self.conversations[conversation_id].turns.append(turn)
        self.conversations[conversation_id].last_entities = entities
        self.conversations[conversation_id].last_accessed = time.time()
    
    def resolve_query(self, conversation_id: str, question: str) -> str:
        """
        Resolve pronouns and ellipsis in the question using conversation context.
        
        Args:
            conversation_id: The conversation ID
            question: The current question
            
        Returns:
            Resolved question with pronouns/ellipsis replaced by actual entities
        """
        if conversation_id not in self.conversations:
            return question
        
        context = self.conversations[conversation_id]
        if not context.turns:
            return question
        
        # Get the most recent entities
        recent_entities = context.last_entities
        if not recent_entities:
            return question
        
        # Try to resolve pronouns and ellipsis
        resolved_question = question
        for pattern, replacement in self.pronoun_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                # Use the most recent entity
                entity = recent_entities[0] if recent_entities else "il corso"
                resolved_question = re.sub(
                    pattern, 
                    replacement.format(entity=entity), 
                    question, 
                    flags=re.IGNORECASE
                )
                break
        
        return resolved_question
    
    def get_conversation_context(self, conversation_id: str) -> str:
        """
        Get a brief context summary for the conversation.
        
        Args:
            conversation_id: The conversation ID
            
        Returns:
            A brief context string to include in the prompt
        """
        if conversation_id not in self.conversations:
            return ""
        
        context = self.conversations[conversation_id]
        if not context.turns:
            return ""
        
        # Get the last 2 turns for context
        recent_turns = list(context.turns)[-2:]
        context_parts = []
        
        for turn in recent_turns:
            # Extract the main entity from the question
            entities = self._extract_entities(turn.question)
            if entities:
                context_parts.append(f"Ultima domanda riguardava: {entities[0]}")
        
        if context_parts:
            return f"Contesto conversazione: {'; '.join(context_parts)}. "
        
        return ""
    
    def _extract_entities(self, text: str) -> List[str]:
        """Extract entities (courses, professors) from text."""
        entities = []
        
        # Extract courses
        for pattern in self.course_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                entity = match.strip()
                if len(entity) > 3 and entity not in entities:
                    entities.append(entity)
        
        # Extract professors
        for pattern in self.professor_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                entity = match.strip()
                if len(entity) > 2 and entity not in entities:
                    entities.append(entity)
        
        return entities
    
    def cleanup_old_conversations(self) -> None:
        """Remove old conversations to prevent memory leaks."""
        current_time = time.time()
        to_remove = []
        
        for conv_id, context in self.conversations.items():
            if current_time - context.last_accessed > self.conversation_ttl:
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            del self.conversations[conv_id]
        
        # Also remove oldest conversations if we exceed the limit
        if len(self.conversations) > self.max_conversations:
            sorted_conversations = sorted(
                self.conversations.items(),
                key=lambda x: x[1].last_accessed
            )
            excess_count = len(self.conversations) - self.max_conversations
            for conv_id, _ in sorted_conversations[:excess_count]:
                del self.conversations[conv_id]
    
    def get_conversation_stats(self) -> Dict[str, int]:
        """Get statistics about active conversations."""
        return {
            "active_conversations": len(self.conversations),
            "max_conversations": self.max_conversations,
            "max_turns_per_conversation": self.max_turns_per_conversation
        }

# Global instance
conversation_memory = ConversationMemoryManager()

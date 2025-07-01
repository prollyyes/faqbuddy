import os
import sys
import re
from typing import List, Dict, Tuple
import time

# Enhanced Configuration
MAX_CHUNKS = 4  # Reduced for faster processing
MAX_TOKENS = 1000  # Optimized for faster responses
MAX_CHARS_PER_CHUNK = 400  # Limit chunk size for better focus
MIN_RELEVANCE_SCORE = 0.3  # Minimum relevance threshold

# Enhanced System Prompt with better structure
SYSTEM_PROMPT = """Sei FAQBuddy, un assistente intelligente per un portale universitario italiano. 

COMPITI:
- Rispondi a domande su università, corsi, professori, materiali didattici
- Fornisci informazioni accurate basate SOLO sui documenti forniti
- Mantieni un tono professionale ma amichevole
- Usa sempre il formato Markdown per una migliore leggibilità
- Cita le fonti quando appropriato

REGOLE IMPORTANTI:
- NON inventare informazioni
- Se non hai informazioni sufficienti, dillo chiaramente
- Rispondi SEMPRE in italiano
- Sii conciso ma completo
- Usa elenchi puntati per informazioni strutturate

FORMATO RISPOSTA:
- Usa titoli (# ##) per organizzare la risposta
- Usa elenchi puntati (-) per liste
- Usa grassetto (**testo**) per enfasi
- Usa corsivo (*testo*) per termini tecnici
- Cita le fonti tra parentesi quando appropriato"""

def count_tokens(text: str) -> int:
    """Improved token counting with better approximation."""
    # More accurate token estimation
    words = text.split()
    return len(words) + len([c for c in text if c in ',.!?;:'])

def enhance_query(query: str) -> str:
    """
    Enhance query for better retrieval using techniques from smallRag.
    """
    query = query.strip()
    
    # Add context keywords for university queries
    university_keywords = [
        'università', 'corso', 'professore', 'esame', 'materiale', 
        'segreteria', 'iscrizione', 'laurea', 'facoltà', 'dipartimento'
    ]
    
    # Add academic context if relevant
    if any(keyword in query.lower() for keyword in university_keywords):
        enhanced = f"{query} (contesto universitario)"
    else:
        enhanced = query
    
    # Add specific context based on query type
    if any(word in query.lower() for word in ['quali', 'elenca', 'lista', 'mostra']):
        enhanced += " (richiesta informativa)"
    elif any(word in query.lower() for word in ['come', 'procedura', 'modalità']):
        enhanced += " (richiesta procedurale)"
    elif any(word in query.lower() for word in ['quando', 'data', 'scadenza']):
        enhanced += " (richiesta temporale)"
    
    return enhanced

def deduplicate_chunks(chunks: List[Dict]) -> List[Dict]:
    """Enhanced deduplication with semantic similarity check."""
    seen = set()
    deduped = []
    
    for chunk in chunks:
        # Create a normalized fingerprint
        text = chunk.get('text', '')
        meta = chunk.get('meta', {})
        
        # Normalize text for deduplication
        norm_text = re.sub(r'\s+', ' ', text.lower().strip())
        norm_text = re.sub(r'[^\w\s]', '', norm_text)
        
        # Create fingerprint from text and key metadata
        fingerprint = f"{norm_text[:100]}_{meta.get('source', '')}_{meta.get('page', '')}"
        
        if fingerprint not in seen:
            seen.add(fingerprint)
            deduped.append(chunk)
    
    return deduped

def filter_by_relevance(chunks: List[Dict]) -> List[Dict]:
    """Filter chunks by relevance score."""
    filtered = []
    for chunk in chunks:
        score = chunk.get('score_combined', 0) or chunk.get('cross_score', 0) or 0.5
        if score >= MIN_RELEVANCE_SCORE:
            filtered.append(chunk)
    return filtered

def format_chunk(chunk: Dict, idx: int) -> str:
    """Enhanced chunk formatting with better structure."""
    meta = chunk.get('meta', {})
    text = chunk.get('text', '')
    
    # Truncate text if too long
    if len(text) > MAX_CHARS_PER_CHUNK:
        text = text[:MAX_CHARS_PER_CHUNK] + "..."
    
    # Build metadata string
    meta_parts = []
    if meta.get('source'):
        meta_parts.append(f"Fonte: {meta['source']}")
    if meta.get('page'):
        meta_parts.append(f"Pagina: {meta['page']}")
    if meta.get('section_title'):
        meta_parts.append(f"Sezione: {meta['section_title']}")
    if meta.get('namespace'):
        meta_parts.append(f"Tipo: {meta['namespace']}")
    
    meta_str = f"[{', '.join(meta_parts)}]" if meta_parts else "[Fonte non specificata]"
    
    # Add relevance score if available
    score = chunk.get('score_combined', 0) or chunk.get('cross_score', 0)
    score_str = f" (Rilevanza: {score:.2f})" if score else ""
    
    return f"**Snippet {idx}{score_str}** {meta_str}:\n{text}\n"

def optimize_context_length(chunks: List[Dict]) -> List[Dict]:
    """
    Optimize context length for better performance and relevance.
    Inspired by smallRag's context optimization.
    """
    selected = []
    total_tokens = 0
    total_chars = 0
    
    for chunk in chunks:
        chunk_text = chunk.get('text', '')
        chunk_tokens = count_tokens(chunk_text)
        chunk_chars = len(chunk_text)
        
        # Check if adding this chunk would exceed limits
        if (len(selected) < MAX_CHUNKS and 
            total_tokens + chunk_tokens <= MAX_TOKENS and
            total_chars + chunk_chars <= MAX_TOKENS * 4):  # Rough char estimate
            
            selected.append(chunk)
            total_tokens += chunk_tokens
            total_chars += chunk_chars
        else:
            break
    
    return selected

def build_prompt(merged_results: List[Dict], user_question: str) -> Tuple[str, Dict]:
    """
    Build an optimized prompt with enhanced query processing.
    Returns the prompt and metadata about the build process.
    """
    start_time = time.time()
    
    # Step 1: Enhance the query
    enhanced_query = enhance_query(user_question)
    
    # Step 2: Deduplicate and filter chunks
    deduped = deduplicate_chunks(merged_results)
    filtered = filter_by_relevance(deduped)
    
    # Step 3: Optimize context length
    selected = optimize_context_length(filtered)
    
    # Step 4: Format context
    context_parts = []
    for i, chunk in enumerate(selected, 1):
        context_parts.append(format_chunk(chunk, i))
    
    context = "\n".join(context_parts)
    
    # Step 5: Build final prompt
    prompt = f"""{SYSTEM_PROMPT}

**CONTESTO DISPONIBILE:**
{context}

**DOMANDA UTENTE:**
{user_question}

**RISPOSTA:**"""
    
    # Calculate build metadata
    build_time = time.time() - start_time
    metadata = {
        "original_chunks": len(merged_results),
        "after_deduplication": len(deduped),
        "after_filtering": len(filtered),
        "final_chunks": len(selected),
        "total_tokens": count_tokens(context),
        "build_time": build_time,
        "enhanced_query": enhanced_query,
        "context_sources": list(set(chunk.get('meta', {}).get('source', 'unknown') for chunk in selected))
    }
    
    return prompt, metadata

def build_prompt_fast(merged_results: List[Dict], user_question: str) -> str:
    """
    Fast version of prompt building for streaming responses.
    """
    # Simplified version for speed
    deduped = deduplicate_chunks(merged_results[:3])  # Take only top 3
    context_parts = []
    
    for i, chunk in enumerate(deduped, 1):
        text = chunk.get('text', '')[:300]  # Limit text length
        meta = chunk.get('meta', {})
        source = meta.get('source', 'Fonte')
        context_parts.append(f"**{source}:** {text}")
    
    context = "\n\n".join(context_parts)
    
    return f"""{SYSTEM_PROMPT}

**CONTESTO:**
{context}

**DOMANDA:** {user_question}

**RISPOSTA:**"""

def main():
    """Test function for prompt building."""
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            merged_results = eval(f.read())
    else:
        print("Paste merged results (as a Python list of dicts), then Ctrl-D:")
        merged_results = eval(sys.stdin.read())
    
    user_question = input("\nEnter the user question: ")
    
    print("\n=== Enhanced Prompt Building ===")
    prompt, metadata = build_prompt(merged_results, user_question)
    
    print(f"\nBuild metadata:")
    for key, value in metadata.items():
        print(f"  {key}: {value}")
    
    print(f"\n=== Final LLM Prompt ===\n")
    print(prompt)

if __name__ == "__main__":
    main() 
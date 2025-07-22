import sys
import re
from typing import List, Dict

# Config
MAX_CHUNKS = 5
MAX_TOKENS = 1200  # Adjust for your LLM context window (e.g., 4096 for GPT-3.5, but leave room for question/answer)
SYSTEM_PROMPT = (
    "Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. "
    "Ti verranno forniti una domanda dell'utente e un insieme di frammenti di contesto da varie fonti (PDF, database, ecc.). "
    "Ogni frammento include metadati (fonte, pagina, sezione, ecc.). "
    "Usa SOLO il contesto fornito per rispondere e cita le fonti inline usando i metadati. "
    "Se non conosci la risposta, dillo onestamente. "
    "Non inventare informazioni, non fare allucinazioni. "
    "IMPORTANTE: Rispondi SEMPRE in italiano, a meno che l'utente non chieda esplicitamente in inglese. "
    "Mantieni un tono professionale ma amichevole. "
    "Usa sempre il formato Markdown per una migliore leggibilità."
)

# Simple token count (approximate, by whitespace)
def count_tokens(text):
    return len(text.split())

def deduplicate_chunks(chunks: List[Dict]) -> List[Dict]:
    seen = set()
    deduped = []
    for chunk in chunks:
        # Use normalized text for deduplication
        norm = re.sub(r'\W+', '', chunk['text'].lower())
        if norm not in seen:
            seen.add(norm)
            deduped.append(chunk)
    return deduped

def format_chunk(chunk: Dict, idx: int) -> str:
    # Handle both 'meta' and 'metadata' keys for compatibility
    meta = chunk.get('meta', chunk.get('metadata', {}))
    meta_str = f"[Fonte: {meta.get('source', 'N/A')}, Pagina: {meta.get('page', 'N/A')}, Sezione: {meta.get('section_title', 'N/A')}]"
    return f"Frammento {idx} {meta_str}:\n{chunk['text']}\n"

def build_prompt(merged_results: List[Dict], user_question: str) -> str:
    # Deduplicate
    deduped = deduplicate_chunks(merged_results)
    # Select top N chunks fitting token limit
    selected = []
    total_tokens = 0
    for chunk in deduped:
        chunk_tokens = count_tokens(chunk['text'])
        if len(selected) < MAX_CHUNKS and total_tokens + chunk_tokens <= MAX_TOKENS:
            selected.append(chunk)
            total_tokens += chunk_tokens
        if total_tokens >= MAX_TOKENS:
            break
    # Build prompt
    context = "\n".join([format_chunk(chunk, i+1) for i, chunk in enumerate(selected)])
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Domanda dell'utente: {user_question}\n\n"
        f"Frammenti di contesto:\n{context}\n\n"
        f"Risposta:"
    )
    return prompt

def main():
    # For demo: load merged results from a JSON file or stdin
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            merged_results = eval(f.read())  # Accepts a Python list/dict or JSON
    else:
        print("Paste merged results (as a Python list of dicts), then Ctrl-D:")
        merged_results = eval(sys.stdin.read())
    user_question = input("\nEnter the user question: ")
    prompt = build_prompt(merged_results, user_question)
    print("\n=== Final LLM Prompt ===\n")
    print(prompt)

if __name__ == "__main__":
    main() 
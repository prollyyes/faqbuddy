import sys
import re
from typing import List, Dict

# Config
MAX_CHUNKS = 5
MAX_TOKENS = 1200  # Adjust for your LLM context window (e.g., 4096 for GPT-3.5, but leave room for question/answer)
SYSTEM_PROMPT = (
    "You are FAQBuddy, a helpful university FAQ assistant. "
    "You will be given a user question and a set of context snippets from various sources (PDFs, database, etc). "
    "Each snippet includes metadata (source, page, section, etc). "
    "Use only the provided context to answer, and cite sources inline using the metadata. "
    "If you don't know the answer, say so honestly."
    "Don't hallucinate, don't make up information."
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
    meta = chunk['meta']
    meta_str = f"[Source: {meta.get('source', 'N/A')}, Page: {meta.get('page', 'N/A')}, Section: {meta.get('section_title', 'N/A')}]"
    return f"Snippet {idx} {meta_str}:\n{chunk['text']}\n"

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
        f"User question: {user_question}\n\n"
        f"Context snippets:\n{context}\n\n"
        f"Answer:"
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
import os, json, requests
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from typing import Generator, Iterator

# Seed the detector for consistent results
DetectorFactory.seed = 0

# Remote (preferred)
REMOTE_BASE  = os.getenv("REMOTE_LLM_BASE")            # e.g. https://abc123.trycloudflare.com
REMOTE_MODEL = os.getenv("REMOTE_LLM_MODEL", "mistral:7b-instruct")
REMOTE_KEY   = os.getenv("REMOTE_LLM_API_KEY", "")

# Local fallback (only used if REMOTE_LLM_BASE is not set)
llm_mistral = None
if not REMOTE_BASE:
    try:
        from llama_cpp import Llama
        mistral_model_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'capybarahermes-2.5-mistral-7b.Q4_K_M.gguf')
        )
        if os.path.exists(mistral_model_path):
            llm_mistral = Llama(
                model_path=mistral_model_path,
                n_ctx=4096,
                n_threads=6,
                n_gpu_layers=-1,
                verbose=False
            )
    except Exception:
        llm_mistral = None

def clean_response(response: str) -> str:
    """Clean system tokens and unwanted prefixes from LLM response."""
    import re
    
    # Remove system tokens
    response = re.sub(r'<\|im_start\|>.*?<\|im_end\|>', '', response, flags=re.DOTALL)
    response = re.sub(r'<\|im_start\|>', '', response)
    response = re.sub(r'<\|im_end\|>', '', response)
    response = re.sub(r'\[/INST\]', '', response)
    response = re.sub(r'\[INST\]', '', response)
    
    # Remove custom response tokens
    response = re.sub(r'\[/risposta\]', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\[risposta\]', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\[/answer\]', '', response, flags=re.IGNORECASE)
    response = re.sub(r'\[answer\]', '', response, flags=re.IGNORECASE)
    
    # Remove common unwanted prefixes
    response = re.sub(r'^Risposta:\s*', '', response, flags=re.IGNORECASE)
    response = re.sub(r'^Assistant:\s*', '', response, flags=re.IGNORECASE)
    
    return response.strip()

def get_language_instruction(question: str) -> str:
    try:
        lang = detect(question)
        if lang == "en":
            return "IMPORTANT: Rispondi in italiano (traduci se necessario)."
        else:
            return "IMPORTANTE: Rispondi SEMPRE in italiano. Non usare mai l'inglese."
    except LangDetectException:
        return "IMPORTANTE: Rispondi SEMPRE in italiano. Non usare mai l'inglese."

def _build_prompt(context: str, question: str) -> str:
    li = get_language_instruction(question)
    return (
        f"[INST] Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. Anche i professori usano la piattaforma, quindi mantieni un tono professionale ma amichevole. Non rispondere a domande generali non legate all'università. {li} \n\nIMPORTANTE: \n- Rispondi SEMPRE in formato Markdown pulito\n- Usa titoli (# ##), elenchi puntati (-), grassetto (**testo**), corsivo (*testo*) e link quando appropriato\n- NON includere MAI token di sistema come <|im_start|>, <|im_end|>, [/INST], o simili\n- Inizia direttamente con la risposta, senza prefissi o tag\n- Termina con la risposta completa senza token aggiuntivi\n\nContesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    )

def _generate_remote(context: str, question: str) -> str:
    url = REMOTE_BASE.rstrip("/") + "/api/generate"
    headers = {"Content-Type": "application/json"}
    if REMOTE_KEY:
        headers["Authorization"] = f"Bearer {REMOTE_KEY}"
    
    li = get_language_instruction(question)
    system_message = (
        f"Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. Anche i professori usano la piattaforma, quindi mantieni un tono professionale ma amichevole. Non rispondere a domande generali non legate all'università. {li} "
        f"IMPORTANTE: Rispondi SEMPRE in formato Markdown pulito. Usa titoli (# ##), elenchi puntati (-), grassetto (**testo**), corsivo (*testo*) e link quando appropriato. NON includere MAI token di sistema come <|im_start|>, <|im_end|>, [/INST], o simili. Inizia direttamente con la risposta, senza prefissi o tag. Termina con la risposta completa senza token aggiuntivi. Usa solo il contesto fornito; se manca, dillo chiaramente."
    )
    
    # Build the prompt in Ollama format
    prompt = f"[INST] {system_message}\n\nContesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    
    payload = {
        "model": REMOTE_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_ctx": 4096
        }
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["response"].strip()

def generate_answer(context: str, question: str) -> str:
    if REMOTE_BASE:
        return _generate_remote(context, question)
    if llm_mistral is None:
        return "⚠️ LLM non disponibile. Imposta REMOTE_LLM_BASE per usare il modello locale via tunnel."
    out = llm_mistral(_build_prompt(context, question), max_tokens=700, temperature=0.2)
    return out["choices"][0].get("text", "").strip()

def generate_answer_streaming(context: str, question: str) -> Generator[str, None, None]:
    """
    Generate an answer token by token using streaming.
    Returns a generator that yields tokens as they are generated.
    """
    if REMOTE_BASE:
        # For remote LLM, we'll get the full response and yield it as a single chunk
        # since streaming over HTTP is more complex and may not be supported by all remote services
        response = _generate_remote(context, question)
        yield response
        return
    
    if llm_mistral is None:
        yield "⚠️ LLM generation is not available. Please install llama-cpp-python and ensure the Mistral model is available."
        return
    
    prompt = _build_prompt(context, question)
    
    # Use the streaming API
    stream = llm_mistral(prompt, max_tokens=700, temperature=0.2, stream=True)
    
    for chunk in stream:
        # Check if the chunk has the expected structure
        if "choices" in chunk and len(chunk["choices"]) > 0:
            choice = chunk["choices"][0]
            
            # Check if the response is finished
            if choice.get("finish_reason") is not None:
                break
            
            # Extract the text content - try different possible structures
            text_content = ""
            if "delta" in choice and "content" in choice["delta"]:
                text_content = choice["delta"]["content"]
            elif "text" in choice:
                text_content = choice["text"]
            elif "content" in choice:
                text_content = choice["content"]
            
            if text_content:
                # Clean system tokens from streaming content
                cleaned_content = clean_response(text_content)
                if cleaned_content:  # Only yield if there's content after cleaning
                    yield cleaned_content

def generate_answer_streaming_with_metadata(context: str, question: str) -> Generator[dict, None, None]:
    """
    Generate an answer token by token using streaming with metadata.
    Returns a generator that yields dictionaries with token and metadata.
    """
    if REMOTE_BASE:
        # For remote LLM, we'll get the full response and yield it as a single chunk
        response = _generate_remote(context, question)
        yield {
            "type": "token",
            "content": response,
            "token_count": 1
        }
        yield {
            "type": "metadata",
            "token_count": 1,
            "finished": True
        }
        return
    
    if llm_mistral is None:
        yield {
            "type": "token",
            "content": "⚠️ LLM generation is not available. Please install llama-cpp-python and ensure the Mistral model is available."
        }
        yield {
            "type": "metadata",
            "token_count": 0,
            "finished": True
        }
        return
    
    prompt = _build_prompt(context, question)
    
    # Use the streaming API
    stream = llm_mistral(prompt, max_tokens=700, temperature=0.2, stream=True)
    
    token_count = 0
    for chunk in stream:
        # Check if the chunk has the expected structure
        if "choices" in chunk and len(chunk["choices"]) > 0:
            choice = chunk["choices"][0]
            
            # Check if the response is finished
            if choice.get("finish_reason") is not None:
                # Send final metadata
                yield {
                    "type": "metadata",
                    "token_count": token_count,
                    "finished": True
                }
                break
            
            # Extract the text content - try different possible structures
            text_content = ""
            if "delta" in choice and "content" in choice["delta"]:
                text_content = choice["delta"]["content"]
            elif "text" in choice:
                text_content = choice["text"]
            elif "content" in choice:
                text_content = choice["content"]
            
            if text_content:
                # Clean system tokens from streaming content
                cleaned_content = clean_response(text_content)
                if cleaned_content:  # Only yield if there's content after cleaning
                    token_count += 1
                    yield {
                        "type": "token",
                        "content": cleaned_content,
                        "token_count": token_count
                    }
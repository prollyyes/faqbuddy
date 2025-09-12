import os, json, requests
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Seed the detector for consistent results
DetectorFactory.seed = 0

# Remote (preferred)
REMOTE_BASE  = os.getenv("REMOTE_LLM_BASE")            # e.g. https://abc123.trycloudflare.com
REMOTE_MODEL = os.getenv("REMOTE_LLM_MODEL", "mistral:7b-instruct")
REMOTE_KEY   = os.getenv("REMOTE_LLM_API_KEY", "")

# Local fallback (only used if REMOTE_LLM_BASE is not set)
llm_gemma = None
if not REMOTE_BASE:
    try:
        from llama_cpp import Llama
        gemma_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'gemma-3-4b-it-Q4_1.gguf'))
        
        if os.path.exists(gemma_model_path):
            llm_gemma = Llama(
                model_path=gemma_model_path,
                n_ctx=2048,
                n_threads=6,
                n_gpu_layers=-1,
                verbose=False
            )
    except Exception:
        llm_gemma = None

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
        f"[INST] Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. Anche i professori usano la piattaforma, quindi mantieni un tono professionale ma amichevole. Non rispondere a domande generali non legate all'università. {li} IMPORTANTE: Rispondi sempre in formato Markdown per una migliore leggibilità. Usa titoli (# ##), elenchi puntati (-), grassetto (**testo**), corsivo (*testo*) e link quando appropriato. Contesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    )

def _generate_remote(context: str, question: str) -> str:
    url = REMOTE_BASE.rstrip("/") + "/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    if REMOTE_KEY:
        headers["Authorization"] = f"Bearer {REMOTE_KEY}"
    
    li = get_language_instruction(question)
    system_message = (
        f"Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. Anche i professori usano la piattaforma, quindi mantieni un tono professionale ma amichevole. Non rispondere a domande generali non legate all'università. {li} "
        f"IMPORTANTE: Rispondi sempre in formato Markdown per una migliore leggibilità. Usa titoli (# ##), elenchi puntati (-), grassetto (**testo**), corsivo (*testo*) e link quando appropriato. Usa solo il contesto fornito; se manca, dillo chiaramente."
    )
    
    payload = {
        "model": REMOTE_MODEL,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Contesto:\n{context}\n\nDomanda:\n{question}"}
        ]
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=120)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()

def classify_question(question: str) -> str:
    if REMOTE_BASE:
        # For remote LLM, use a simple classification
        url = REMOTE_BASE.rstrip("/") + "/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        if REMOTE_KEY:
            headers["Authorization"] = f"Bearer {REMOTE_KEY}"
        payload = {
            "model": REMOTE_MODEL,
            "temperature": 0.1,
            "max_tokens": 2,
            "messages": [
                {"role": "system", "content": "Classifica la domanda come 'simple' o 'complex'. Rispondi solo con una parola."},
                {"role": "user", "content": f"Domanda: {question}\nRisposta:"}
            ]
        }
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
            r.raise_for_status()
            data = r.json()
            text = data["choices"][0]["message"]["content"].strip().lower()
            if not text:
                return "simple"
            return text.split()[0]
        except Exception:
            return "simple"
    
    if llm_gemma is None:
        return "simple"
    
    prompt = (
        "Classifica la seguente domanda SOLO come 'simple' o 'complex'. "
        "Rispondi esclusivamente con una di queste due parole, senza spiegazioni, motivazioni o testo aggiuntivo.\n\n"
        "Esempi:\n"
        "Domanda: Quanti crediti vale il corso di informatica?\nRisposta: simple\n"
        "Domanda: Come posso organizzare il piano di studi per laurearmi in 3 anni?\nRisposta: complex\n"
        f"Domanda: {question}\nRisposta:"
    )
    result = llm_gemma(prompt, max_tokens=2)
    text = result["choices"][0].get("text", "").strip().lower()
    if not text:
        return "simple"
    return text.split()[0]

def generate_answer(context: str, question: str) -> str:
    if REMOTE_BASE:
        return _generate_remote(context, question)
    if llm_gemma is None:
        return "⚠️ LLM non disponibile. Imposta REMOTE_LLM_BASE per usare il modello locale via tunnel."
    out = llm_gemma(_build_prompt(context, question), max_tokens=700, temperature=0.2)
    return out["choices"][0].get("text", "").strip()

def generate_answer_streaming(context: str, question: str) -> list:
    """Generate an answer token by token."""
    if REMOTE_BASE:
        # For remote LLM, we'll get the full response and return it as a single token
        response = _generate_remote(context, question)
        return [response]
    
    if llm_gemma is None:
        return ["⚠️ LLM non disponibile. Imposta REMOTE_LLM_BASE per usare il modello locale via tunnel."]
    
    prompt = _build_prompt(context, question)
    
    # Use the streaming API
    stream = llm_gemma(prompt, max_tokens=700, temperature=0.2, stream=True)
    
    tokens = []
    for chunk in stream:
        if chunk["choices"][0]["finish_reason"] is not None:
            break
        token = chunk["choices"][0]["delta"].get("content", "")
        if token:
            tokens.append(token)
    
    return tokens

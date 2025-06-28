import os
from llama_cpp import Llama
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Seed the detector for consistent results
DetectorFactory.seed = 0

mistral_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'mistral-7b-instruct-v0.2.Q4_K_M.gguf'))

llm_mistral = Llama(
    model_path=mistral_model_path,
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=-1,
    verbose=True
)

def get_language_instruction(question: str) -> str:
    """Detects the language of the question and returns a strong instruction for the LLM."""
    try:
        lang = detect(question)
        if lang == 'it':
            return "IMPORTANTE: Rispondi SEMPRE in italiano. Non usare mai l'inglese. Mantieni la conversazione in italiano."
        elif lang == 'en':
            return "IMPORTANT: Always answer in English. Never use Italian. Keep the conversation in English."
        else:
            # Default to Italian for FAQBuddy since it's an Italian university system
            return "IMPORTANTE: Rispondi SEMPRE in italiano. Non usare mai l'inglese. Mantieni la conversazione in italiano."
    except LangDetectException:
        # Default to Italian for FAQBuddy
        return "IMPORTANTE: Rispondi SEMPRE in italiano. Non usare mai l'inglese. Mantieni la conversazione in italiano."

def generate_answer(context: str, question: str) -> str:
    language_instruction = get_language_instruction(question)
    prompt = (
        f"[INST] Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. Anche i professori usano la piattaforma, quindi mantieni un tono professionale ma amichevole. Non rispondere a domande generali non legate all'università. {language_instruction} Contesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    )
    output = llm_mistral(prompt, max_tokens=512, stop=["</s>"])
    return output["choices"][0]["text"].strip()

def generate_answer_streaming(context: str, question: str) -> list:
    """Generate an answer token by token."""
    language_instruction = get_language_instruction(question)
    prompt = f"[INST] Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. Anche i professori usano la piattaforma, quindi mantieni un tono professionale ma amichevole. Non rispondere a domande generali non legate all'università. {language_instruction} Contesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    
    # Use the streaming API
    stream = llm_mistral(prompt, max_tokens=512, stop=["</s>"], stream=True)
    
    tokens = []
    for chunk in stream:
        if chunk["choices"][0]["finish_reason"] is not None:
            break
        token = chunk["choices"][0]["delta"].get("content", "")
        if token:
            tokens.append(token)
    
    return tokens
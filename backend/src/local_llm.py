import os
from llama_cpp import Llama
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Seed the detector for consistent results
DetectorFactory.seed = 0

mistral_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'mistral-7b-instruct-v0.2.Q4_K_M.gguf'))
gemma_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'gemma-3-4b-it-Q4_1.gguf'))
qwen_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'Qwen2.5-7B-Instruct.Q4_K_M.gguf'))

llm_mistral = Llama(
    model_path=mistral_model_path,
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=8,  # Use only 8 GPU layers to prevent kernel panic
    n_batch=512,     # Reduce batch size to lower memory usage
    verbose=True
)

llm_gemma = Llama(
    model_path=gemma_model_path,
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=8,  # Use only 8 GPU layers to prevent kernel panic
    n_batch=512,     # Reduce batch size to lower memory usage
    verbose=True
)

'''
llm_qwen = Llama(
    model_path=qwen_model_path,
    n_ctx=1024,
    n_threads=6,
    n_gpu_layers=-0,
    verbose=True
)
'''

# Set the model to use for answer generation (RAG and T2SQL)
# Options: llm_mistral, llm_qwen
llm_answer = llm_mistral  # <--- Now using Mistral for answer generation

def classify_question(question: str) -> str:
    prompt = (
        "Classifica la seguente domanda SOLO come 'simple' o 'complex'. "
        "Rispondi esclusivamente con una di queste due parole, senza spiegazioni, motivazioni o testo aggiuntivo.\n\n"
        "Esempi:\n"
        "Domanda: Quanti crediti vale il corso di informatica?\nRisposta: simple\n"
        "Domanda: Come posso organizzare il piano di studi per laurearmi in 3 anni?\nRisposta: complex\n"
        f"Domanda: {question}\nRisposta:"
    )
    result = llm_gemma(prompt, max_tokens=2)
    risposta = result["choices"][0]["text"].strip().lower().split()[0] # why error?
    return risposta


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
    output = llm_answer(prompt, max_tokens=512, stop=["</s>"])
    return output["choices"][0]["text"].strip()

def generate_answer_streaming(context: str, question: str) -> list:
    """Generate an answer token by token."""
    language_instruction = get_language_instruction(question)
    prompt = f"[INST] Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. Anche i professori usano la piattaforma, quindi mantieni un tono professionale ma amichevole. Non rispondere a domande generali non legate all'università. {language_instruction} Contesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    
    # Use the streaming API
    stream = llm_answer(prompt, max_tokens=512, stop=["</s>"], stream=True)
    
    tokens = []
    for chunk in stream:
        if chunk["choices"][0]["finish_reason"] is not None:
            break
        token = chunk["choices"][0]["delta"].get("content", "")
        if token:
            tokens.append(token)
    
    return tokens
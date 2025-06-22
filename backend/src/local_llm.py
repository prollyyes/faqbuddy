import os
from llama_cpp import Llama
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Seed the detector for consistent results
DetectorFactory.seed = 0

mistral_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'mistral-7b-instruct-v0.2.Q4_K_M.gguf'))
gemma_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'gemma-3-4b-it-Q4_1.gguf'))

llm_mistral = Llama(
    model_path=mistral_model_path,
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=-1,
    verbose=True
)

llm_gemma = Llama(
    model_path=gemma_model_path,
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=-1,
    verbose=True
)


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
    """Detects the language of the question and returns an instruction for the LLM."""
    try:
        lang = detect(question)
        if lang == 'it':
            return "Answer in Italian."
        # Add other languages as needed
        # elif lang == 'es':
        #     return "Answer in Spanish."
        else:
            return "Answer in English."
    except LangDetectException:
        # Default to English if detection fails
        return "Answer in English."


def generate_answer(context: str, question: str) -> str:
    language_instruction = get_language_instruction(question)
    prompt = f"[INST] You are FAQBuddy, a helpful assistant for a university portal that answers questions about the university, their courses, professors, materials and any problem a student can have. Teachers are also using the platform, so keep a professional but friendly tone. Refrain from answering general questions. {language_instruction} Context:\n{context}\n\nQuestion:\n{question} [/INST]"
    output = llm_mistral(prompt, max_tokens=512, stop=["</s>"])
    return output["choices"][0]["text"].strip()

def generate_answer_streaming(context: str, question: str) -> list:
    """Generate an answer token by token."""
    language_instruction = get_language_instruction(question)
    prompt = f"[INST] You are FAQBuddy, a helpful assistant for a university portal that answers questions about the university, their courses, professors, materials and any problem a student can have. Teachers are also using the platform, so keep a professional but friendly tone. Refrain from answering general questions. {language_instruction} Context:\n{context}\n\nQuestion:\n{question} [/INST]"
    
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
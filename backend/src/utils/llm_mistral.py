import os

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from typing import Generator, Iterator

# Seed the detector for consistent results
DetectorFactory.seed = 0

# Conditional import for llama_cpp
llm_mistral = None
try:
    from llama_cpp import Llama
    mistral_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'capybarahermes-2.5-mistral-7b.Q4_K_M.gguf'))
    
    if os.path.exists(mistral_model_path):
        llm_mistral = Llama(
            model_path=mistral_model_path,
            n_ctx=2048,
            n_threads=6,
            n_gpu_layers=-1,
            verbose=True
        )
    else:
        print(f"⚠️ Warning: Mistral model not found at {mistral_model_path}")
        llm_mistral = None
except ImportError:
    print("⚠️ Warning: llama_cpp not available, LLM generation will be disabled")
    llm_mistral = None

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
    if llm_mistral is None:
        return "⚠️ LLM generation is not available. Please install llama-cpp-python and ensure the Mistral model is available."
    
    language_instruction = get_language_instruction(question)
    prompt = (
        f"[INST] Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. Anche i professori usano la piattaforma, quindi mantieni un tono professionale ma amichevole. Non rispondere a domande generali non legate all'università. {language_instruction} IMPORTANTE: Rispondi sempre in formato Markdown per una migliore leggibilità. Usa titoli (# ##), elenchi puntati (-), grassetto (**testo**), corsivo (*testo*) e link quando appropriato. Contesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    )
    output = llm_mistral(prompt, max_tokens=1024, stop=["</s>"])
    return output["choices"][0]["text"].strip()

def generate_answer_streaming(context: str, question: str) -> Generator[str, None, None]:
    """
    Generate an answer token by token using streaming.
    Returns a generator that yields tokens as they are generated.
    """
    if llm_mistral is None:
        yield "⚠️ LLM generation is not available. Please install llama-cpp-python and ensure the Mistral model is available."
        return
    
    language_instruction = get_language_instruction(question)
    prompt = f"[INST] Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. Anche i professori usano la piattaforma, quindi mantieni un tono professionale ma amichevole. Non rispondere a domande generali non legate all'università. {language_instruction} IMPORTANTE: Rispondi sempre in formato Markdown per una migliore leggibilità. Usa titoli (# ##), elenchi puntati (-), grassetto (**testo**), corsivo (*testo*) e link quando appropriato. Contesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    
    # Use the streaming API
    stream = llm_mistral(prompt, max_tokens=1024, stop=["</s>"], stream=True)
    
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
                yield text_content

def generate_answer_streaming_with_metadata(context: str, question: str) -> Generator[dict, None, None]:
    """
    Generate an answer token by token using streaming with metadata.
    Returns a generator that yields dictionaries with token and metadata.
    """
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
    
    language_instruction = get_language_instruction(question)
    prompt = f"[INST] Sei FAQBuddy, un assistente per un portale universitario che risponde a domande sull'università, i corsi, i professori, i materiali e qualsiasi problema che uno studente può avere. Anche i professori usano la piattaforma, quindi mantieni un tono professionale ma amichevole. Non rispondere a domande generali non legate all'università. {language_instruction} IMPORTANTE: Rispondi sempre in formato Markdown per una migliore leggibilità. Usa titoli (# ##), elenchi puntati (-), grassetto (**testo**), corsivo (*testo*) e link quando appropriato. Contesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    
    # Use the streaming API
    stream = llm_mistral(prompt, max_tokens=1024, stop=["</s>"], stream=True)
    
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
                token_count += 1
                yield {
                    "type": "token",
                    "content": text_content,
                    "token_count": token_count
                }
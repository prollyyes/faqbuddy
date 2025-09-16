import os
import atexit
import gc
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Seed the detector for consistent results
DetectorFactory.seed = 0

# Initialize model variable - will be loaded on-demand
llm_gemma = None

def load_gemma_model():
    """Load the Gemma model if not already loaded."""
    global llm_gemma
    if llm_gemma is not None:
        print("✅ Gemma model already loaded")
        return True
    
    try:
        from llama_cpp import Llama
        gemma_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'gemma-3-4b-it-Q4_1.gguf'))
        
        if os.path.exists(gemma_model_path):
            print("🔄 Loading Gemma model...")
            
            # Optimized settings for RTX 2060S
            PHYSICAL_CORES = max(1, os.cpu_count() // 2)
            
            llm_gemma = Llama(
                model_path=gemma_model_path,
                n_ctx=2048,                      # Smaller context for T2SQL tasks
                n_batch=512,                     # Smaller batch for Gemma
                n_threads=PHYSICAL_CORES,        # Physical cores, not logical
                n_gpu_layers=20,                 # Use all GPU layers for Gemma
                f16_kv=True,                     # Better quality
                verbose=False
            )
            print("✅ Gemma model loaded successfully")
            return True
        else:
            print(f"❌ Gemma model not found at {gemma_model_path}")
            return False
    except Exception as e:
        print(f"❌ Failed to load Gemma model: {e}")
        return False

def unload_gemma_model():
    """Unload the Gemma model to free GPU memory."""
    global llm_gemma
    if llm_gemma is None:
        print("ℹ️ Gemma model not loaded, nothing to unload")
        return True
    
    try:
        print("🔄 Unloading Gemma model...")
        del llm_gemma
        llm_gemma = None
        print("✅ Gemma model unloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to unload Gemma model: {e}")
        return False

def ensure_gemma_loaded():
    """Ensure Gemma model is loaded, load it if not."""
    if llm_gemma is not None:
        return True
    return load_gemma_model()

def cleanup_gemma_resources():
    """Clean up Gemma model resources to prevent semaphore leaks."""
    global llm_gemma
    if llm_gemma is not None:
        try:
            print("🧹 Cleaning up Gemma model resources...")
            del llm_gemma
            llm_gemma = None
            gc.collect()
            print("✅ Gemma model resources cleaned up")
        except Exception as e:
            print(f"⚠️ Error during Gemma cleanup: {e}")

# Register cleanup function with graceful shutdown system
# from utils.graceful_shutdown import register_cleanup_function  # DISABLED
# register_cleanup_function(cleanup_gemma_resources)  # DISABLED

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

def classify_question(question: str) -> str:
    if llm_gemma is None:
        if not ensure_gemma_loaded():
            return "simple"  # Default fallback
    
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


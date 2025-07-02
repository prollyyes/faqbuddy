import os
import time
from llama_cpp import Llama
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from typing import Generator, Iterator, Dict, Any, Optional
import traceback

# Seed the detector for consistent results
DetectorFactory.seed = 0

# Model configuration
mistral_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'mistral-7b-instruct-v0.2.Q4_K_M.gguf'))

# Performance optimizations
LLM_CONFIG = {
    "n_ctx": 2048,  # Reduced context for faster processing
    "n_threads": 8,  # Optimized for M2 Pro
    "n_gpu_layers": -1,  # Use all available GPU layers
    "verbose": False,  # Reduce logging for better performance
    "n_batch": 128,  # Optimized batch size
    "use_mlock": True,  # Keep model in memory
    "use_mmap": True,  # Use memory mapping
    "f16_kv": True,  # Use half precision for key/value cache
    "logits_all": False,  # Don't compute logits for all tokens
    "metal": True,  # Use Metal on Apple Silicon
    "low_vram": False,  # We have sufficient RAM
    "seed": -1,  # Random seed for consistency
    "rope_scaling_type": 0,  # Disable RoPE scaling for speed
    "repeat_penalty": 1.1,  # Light repetition penalty
    "last_n_tokens_size": 64,  # Smaller context for penalty calculation
}

# Initialize LLM with optimized settings
try:
    llm_mistral = Llama(
        model_path=mistral_model_path,
        **LLM_CONFIG
    )
    print("✅ Mistral LLM initialized with optimized settings")
except Exception as e:
    print(f"⚠️ Warning: Could not initialize Mistral LLM: {e}")
    print("   LLM functionality will be limited")
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

def optimize_prompt(context: str, question: str) -> str:
    """
    Optimize prompt for better response quality and markdown formatting.
    Enhanced with better structure and formatting instructions.
    """
    # Get language-specific instruction
    language_instruction = get_language_instruction(question)
    
    # Enhanced prompt structure with better markdown instructions
    optimized_prompt = f"""[INST] Sei FAQBuddy, un assistente universitario intelligente e professionale.

## COMPITI
- Rispondi a domande su università, corsi, professori, materiali didattici
- Fornisci informazioni accurate basate SOLO sui documenti forniti
- Mantieni un tono professionale ma amichevole
- Usa SEMPRE il formato Markdown per strutturare le risposte

## REGOLE DI FORMATTAZIONE
- **Titoli**: Usa `##` per sezioni principali, `###` per sottosezioni
- **Elenchi**: Usa `-` per elenchi puntati, `1.` per elenchi numerati
- **Enfasi**: Usa `**grassetto**` per termini importanti
- **Termini tecnici**: Usa `*corsivo*` per termini tecnici
- **Citazioni**: Usa `> ` per citazioni dirette
- **Codice**: Usa `` `codice` `` per comandi o termini specifici

## STRUTTURA RISPOSTA
Organizza sempre la risposta con:
1. **Titolo principale** con `##`
2. **Contenuto strutturato** con sottosezioni
3. **Elenchi** per informazioni multiple
4. **Enfasi** su informazioni importanti

{language_instruction}

### CONTESTO DISPONIBILE:
{context}

### DOMANDA UTENTE:
{question}

### RISPOSTA FORMATTATA IN MARKDOWN:
[/INST]"""
    
    return optimized_prompt

def generate_answer(context: str, question: str) -> str:
    """
    Generate answer with enhanced error handling and performance optimization.
    """
    if llm_mistral is None:
        return "⚠️ Errore: Modello LLM non disponibile. Controlla che il file del modello sia presente nella cartella models/."
    
    try:
        start_time = time.time()
        
        # Optimize prompt
        prompt = optimize_prompt(context, question)
        
        # Generate response with optimized parameters
        output = llm_mistral(
            prompt, 
            max_tokens=1500,  # Increased for better markdown formatting
            stop=["</s>", "[INST]", "[/INST]"],  # Better stop tokens
            temperature=0.2,  # Slightly higher for more creative formatting
            top_p=0.9,  # Nucleus sampling for better quality
            repeat_penalty=1.1,  # Light repetition penalty
            echo=False  # Don't echo the prompt
        )
        
        generation_time = time.time() - start_time
        
        # Extract and clean the response
        response = output["choices"][0]["text"].strip()
        
        # Remove any remaining prompt artifacts
        if response.startswith("RISPOSTA:"):
            response = response[9:].strip()
        
        print(f"⏱️ LLM generation time: {generation_time:.3f}s")
        
        return response
        
    except Exception as e:
        print(f"❌ Error in LLM generation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return f"Mi dispiace, si è verificato un errore durante la generazione della risposta. Errore: {str(e)}"

def generate_answer_streaming(context: str, question: str) -> Generator[str, None, None]:
    """
    Generate answer using streaming for reduced perceived latency.
    Enhanced with better error handling and performance monitoring.
    """
    if llm_mistral is None:
        yield "⚠️ Errore: Modello LLM non disponibile. Controlla che il file del modello sia presente nella cartella models/."
        return
    
    try:
        start_time = time.time()
        
        # Optimize prompt for streaming
        prompt = optimize_prompt(context, question)
        
        # Use the streaming API with optimized parameters
        stream = llm_mistral(
            prompt, 
            max_tokens=1500,  # Increased for better markdown formatting
            stop=["</s>", "[INST]", "[/INST]"],
            temperature=0.2,  # Slightly higher for more creative formatting
            top_p=0.9,
            repeat_penalty=1.1,
            echo=False,
            stream=True
        )
        
        token_count = 0
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
                    token_count += 1
                    yield text_content
        
        generation_time = time.time() - start_time
        print(f"⏱️ Streaming LLM generation time: {generation_time:.3f}s ({token_count} tokens)")
        
    except Exception as e:
        print(f"❌ Error in streaming LLM generation: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        # For streaming, we need to raise the error so it can be handled properly by the backend
        raise e

def generate_answer_streaming_with_metadata(context: str, question: str) -> Generator[Dict[str, Any], None, None]:
    """
    Generate answer using streaming with metadata for enhanced client experience.
    Enhanced with better error handling and performance monitoring.
    """
    if llm_mistral is None:
        yield {
            "type": "error",
            "content": "⚠️ Errore: Modello LLM non disponibile. Controlla che il file del modello sia presente nella cartella models/.",
            "error": "LLM not available"
        }
        return
    
    try:
        start_time = time.time()
        
        # Optimize prompt for streaming
        prompt = optimize_prompt(context, question)
        
        # Use the streaming API with optimized parameters
        stream = llm_mistral(
            prompt, 
            max_tokens=1500,  # Increased for better markdown formatting
            stop=["</s>", "[INST]", "[/INST]"],
            temperature=0.2,  # Slightly higher for more creative formatting
            top_p=0.9,
            repeat_penalty=1.1,
            echo=False,
            stream=True
        )
        
        token_count = 0
        for chunk in stream:
            # Check if the chunk has the expected structure
            if "choices" in chunk and len(chunk["choices"]) > 0:
                choice = chunk["choices"][0]
                
                # Check if the response is finished
                if choice.get("finish_reason") is not None:
                    # Send final metadata
                    generation_time = time.time() - start_time
                    yield {
                        "type": "metadata",
                        "token_count": token_count,
                        "generation_time": generation_time,
                        "finished": True,
                        "llm_config": LLM_CONFIG
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
                        "token_count": token_count,
                        "timestamp": time.time()
                    }
        
    except Exception as e:
        print(f"❌ Error in streaming LLM generation with metadata: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        yield {
            "type": "error",
            "content": f"Mi dispiace, si è verificato un errore durante la generazione della risposta. Errore: {str(e)}",
            "error": str(e),
            "timestamp": time.time()
        }

def get_llm_stats() -> Dict[str, Any]:
    """Get LLM system statistics and configuration."""
    return {
        "model_path": mistral_model_path,
        "model_available": llm_mistral is not None,
        "config": LLM_CONFIG,
        "system_info": {
            "context_window": LLM_CONFIG["n_ctx"],
            "threads": LLM_CONFIG["n_threads"],
            "gpu_layers": LLM_CONFIG["n_gpu_layers"],
            "metal_enabled": LLM_CONFIG.get("metal", False)
        }
    }

def test_llm_connection() -> Dict[str, Any]:
    """Test LLM connection and basic functionality."""
    if llm_mistral is None:
        return {
            "status": "error",
            "message": "LLM not available",
            "model_path": mistral_model_path,
            "model_exists": os.path.exists(mistral_model_path)
        }
    
    try:
        # Simple test prompt
        test_prompt = "[INST] Rispondi solo con 'OK' se funzioni correttamente. [/INST]"
        start_time = time.time()
        
        output = llm_mistral(test_prompt, max_tokens=10, temperature=0.1)
        response = output["choices"][0]["text"].strip()
        generation_time = time.time() - start_time
        
        return {
            "status": "success",
            "response": response,
            "generation_time": generation_time,
            "model_path": mistral_model_path,
            "config": LLM_CONFIG
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "model_path": mistral_model_path,
            "config": LLM_CONFIG
        }

def main():
    """Test the enhanced LLM integration."""
    print("=== Testing Enhanced LLM Integration ===")
    
    # Test LLM connection
    print("\n1. Testing LLM connection...")
    connection_test = test_llm_connection()
    print(f"Connection test: {connection_test}")
    
    # Test basic generation
    print("\n2. Testing basic generation...")
    test_context = "Il corso di Informatica ha 180 CFU e dura 3 anni."
    test_question = "Quanti CFU ha il corso di Informatica?"
    
    answer = generate_answer(test_context, test_question)
    print(f"Question: {test_question}")
    print(f"Answer: {answer}")
    
    # Test streaming
    print("\n3. Testing streaming generation...")
    print("Streaming response:")
    for token in generate_answer_streaming(test_context, test_question):
        print(token, end="", flush=True)
    print()
    
    # Show LLM stats
    print("\n4. LLM Statistics:")
    stats = get_llm_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
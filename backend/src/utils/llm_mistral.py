import os
import atexit
import gc

from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from typing import Generator, Iterator

# Seed the detector for consistent results
DetectorFactory.seed = 0

# Initialize model variable - will be loaded on-demand
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

def extract_answer_section(response: str) -> str:
    """
    Extract only the answer section from responses that include thinking.
    If the response has both thinking and answer sections, return only the answer.
    """
    import re
    
    # Look for the "📌 Risposta" section and extract everything after it
    answer_match = re.search(r'📌\s*Risposta\s*\n(.*)', response, re.DOTALL | re.IGNORECASE)
    if answer_match:
        answer_section = answer_match.group(1).strip()
        print(f"🎯 Extracted answer section from thinking format")
        return answer_section
    
    # Look for "Risposta" without emoji
    answer_match = re.search(r'(?:^|\n)\s*Risposta\s*\n(.*)', response, re.DOTALL | re.IGNORECASE)
    if answer_match:
        answer_section = answer_match.group(1).strip()
        print(f"🎯 Extracted answer section (no emoji)")
        return answer_section
    
    # If no thinking format is detected, return the whole response
    print(f"🎯 No thinking format detected, returning full response")
    return response

def clean_response_streaming(response: str) -> str:
    """Clean system tokens from streaming response while preserving whitespace."""
    import re
    
    # Remove system tokens but preserve whitespace
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
    
    # Don't strip whitespace for streaming - preserve original spacing
    return response


def generate_answer(context: str, question: str) -> str:
    if llm_mistral is None:
        if not ensure_mistral_loaded():
            return "⚠️ LLM generation is not available. Please install llama-cpp-python and ensure the Mistral model is available."
    
    # Use simple system prompt for direct generation (context is already processed)
    from utils.unified_system_prompt import get_simple_system_prompt
    system_prompt = get_simple_system_prompt()
    prompt = f"[INST] {system_prompt}\n\nContesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    
    print(f"🔍 DEBUG: Calling LLM with prompt length: {len(prompt)}")
    print(f"🔍 DEBUG: Context length: {len(context)}, Question: {question[:100]}...")
    
    # Check if prompt is too long - if so, try with shorter context
    if len(prompt) > 10000:
        print(f"⚠️ DEBUG: Prompt very long ({len(prompt)} chars), trying with reduced context...")
        # Try with just the first 3000 chars of context
        short_context = context[:3000] + "\n\n[...contesto ridotto per limitazioni di lunghezza...]"
        short_prompt = f"[INST] {system_prompt}\n\nContesto:\n{short_context}\n\nDomanda:\n{question} [/INST]"
        print(f"🔍 DEBUG: Reduced prompt length: {len(short_prompt)}")
        prompt = short_prompt
    
    try:
        print(f"🔍 DEBUG: Model status - loaded: {llm_mistral is not None}")
        if llm_mistral is None:
            print("❌ DEBUG: Model is None!")
            return "⚠️ Model not loaded"
            
        # First try a simple test generation to check if the model works
        print(f"🔍 DEBUG: Testing model with simple prompt...")
        test_output = llm_mistral("[INST] Saluta brevemente [/INST]", max_tokens=50, stop=["</s>"], temperature=0.7)
        test_response = test_output["choices"][0]["text"] if "choices" in test_output else ""
        print(f"🔍 DEBUG: Test response: {repr(test_response[:100])}")
        
        if not test_response.strip():
            print("❌ DEBUG: Model fails even simple test - returning error")
            return "⚠️ LLM model non è in grado di generare testo. Verificare configurazione model."
        
        # Now try the actual prompt
        output = llm_mistral(prompt, max_tokens=2048, stop=["</s>", "[/INST]", "[INST]"], temperature=0.7, top_p=0.9)
        print(f"🔍 DEBUG: LLM call completed successfully")
        print(f"🔍 DEBUG: LLM output structure: {type(output)}, keys: {output.keys() if isinstance(output, dict) else 'not dict'}")
        
        if isinstance(output, dict) and "choices" in output and len(output["choices"]) > 0:
            raw_response = output["choices"][0]["text"].strip()
            print(f"🔍 DEBUG: Raw response length: {len(raw_response)}")
            print(f"🔍 DEBUG: Raw response preview: {repr(raw_response[:200])}")
            
            cleaned_response = clean_response(raw_response)
            print(f"🔍 DEBUG: Cleaned response length: {len(cleaned_response)}")
            print(f"🔍 DEBUG: Cleaned response preview: {repr(cleaned_response[:200])}")
            
            # Extract only the "Risposta" section if thinking format is detected
            final_response = extract_answer_section(cleaned_response)
            print(f"🔍 DEBUG: Final response length: {len(final_response)}")
            print(f"🔍 DEBUG: Final response preview: {repr(final_response[:200])}")
            
            if not final_response.strip():
                print("⚠️ DEBUG: Response is empty after final processing!")
                print(f"⚠️ DEBUG: Original raw response was: {repr(raw_response)}")
                # Return cleaned response if final processing made it empty
                return cleaned_response if cleaned_response.strip() else "⚠️ LLM generated empty response"
            
            return final_response
        else:
            print(f"❌ DEBUG: Unexpected output format: {output}")
            return "⚠️ LLM output format error"
            
    except Exception as e:
        print(f"❌ DEBUG: LLM generation failed: {e}")
        return f"⚠️ LLM generation error: {str(e)}"

def load_mistral_model():
    """Load the Mistral model if not already loaded."""
    global llm_mistral
    if llm_mistral is not None:
        print("✅ Mistral model already loaded")
        return True
    
    # Force garbage collection and unload Gemma if loaded to free GPU memory
    print("🧹 Cleaning GPU memory before loading Mistral...")
    
    # Try to unload Gemma model if it's loaded
    try:
        from utils.llm_gemma import unload_gemma_model
        unload_gemma_model()
        print("   Unloaded Gemma model to free GPU memory")
    except Exception as e:
        print(f"   Could not unload Gemma: {e}")
    
    gc.collect()
    import time
    time.sleep(2)  # Give more time for GPU memory to be freed
    
    try:
        from llama_cpp import Llama
        mistral_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'capybarahermes-2.5-mistral-7b.Q4_K_M.gguf'))
        
        if os.path.exists(mistral_model_path):
            print("🔄 Loading Mistral model...")
            
            # Optimized settings for RTX 2060S
            PHYSICAL_CORES = max(1, os.cpu_count() // 2)
            
            llm_mistral = Llama(
                model_path=mistral_model_path,   
                n_ctx=4096,                      # Reasonable context for 7B model (reduced from 32768)
                n_batch=512,                     # Conservative batch size for stability
                n_threads=PHYSICAL_CORES,        # Physical cores, not logical
                n_gpu_layers=12,                 # Reduced to prevent GPU memory conflicts with Gemma
                f16_kv=True,                     # Better quality
                verbose=False,
                use_mmap=True,                   # Enable memory mapping for better memory efficiency
                use_mlock=False                  # Disable memory locking to save RAM
            )
            print("✅ Mistral model loaded successfully")
            return True
        else:
            print(f"❌ Mistral model not found at {mistral_model_path}")
            return False
    except Exception as e:
        print(f"❌ Failed to load Mistral model: {e}")
        return False

def unload_mistral_model():
    """Unload the Mistral model to free GPU memory."""
    global llm_mistral
    if llm_mistral is None:
        print("ℹ️ Mistral model not loaded, nothing to unload")
        return True
    
    try:
        print("🔄 Unloading Mistral model...")
        del llm_mistral
        llm_mistral = None
        print("✅ Mistral model unloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to unload Mistral model: {e}")
        return False

def ensure_mistral_loaded():
    """Ensure Mistral model is loaded, load it if not."""
    # Basic check first
    if llm_mistral is None:
        return load_mistral_model()
    
    # Validate that the model is actually functional
    try:
        if not hasattr(llm_mistral, 'model_path') or not hasattr(llm_mistral, '__call__'):
            print("⚠️ Mistral model exists but is invalid, reloading...")
            return load_mistral_model()
        return True
    except Exception as e:
        print(f"⚠️ Mistral model validation failed: {e}, reloading...")
        return load_mistral_model()

def cleanup_mistral_resources():
    """Clean up Mistral model resources to prevent semaphore leaks."""
    global llm_mistral
    if llm_mistral is not None:
        try:
            print("🧹 Cleaning up Mistral model resources...")
            del llm_mistral
            llm_mistral = None
            gc.collect()
            print("✅ Mistral model resources cleaned up")
        except Exception as e:
            print(f"⚠️ Error during Mistral cleanup: {e}")

# Register cleanup function with graceful shutdown system
# from utils.graceful_shutdown import register_cleanup_function  # DISABLED
# register_cleanup_function(cleanup_mistral_resources)  # DISABLED

def generate_answer_streaming(context: str, question: str, request_id: str = None) -> Generator[str, None, None]:
    """
    Generate an answer token by token using streaming.
    Returns a generator that yields tokens as they are generated.
    """
    print(f"🔄 LLM streaming called with context length: {len(context)}, question: {question[:50]}...")
    
    if llm_mistral is None:
        if not ensure_mistral_loaded():
            print("❌ LLM model is None, cannot generate")
            yield "⚠️ LLM generation is not available. Please install llama-cpp-python and ensure the Mistral model is available."
            return
    
    from utils.unified_system_prompt import get_simple_system_prompt
    system_prompt = get_simple_system_prompt()
    prompt = f"[INST] {system_prompt}\n\nContesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    
    # Use the streaming API
    print(f"🔄 Starting LLM stream with prompt length: {len(prompt)}")
    try:
        stream = llm_mistral(prompt, max_tokens=2048, stop=["</s>", "[/INST]", "[INST]"], stream=True, temperature=0.7, top_p=0.9)
    except Exception as e:
        print(f"❌ Failed to start LLM streaming: {e}")
        yield f"⚠️ Failed to start text generation: {str(e)}"
        return
    
    chunk_count = 0
    try:
        for chunk in stream:
            chunk_count += 1
            print(f"   Chunk {chunk_count}: {chunk}")
            print(f"   Chunk type: {type(chunk)}")
            print(f"   Chunk keys: {list(chunk.keys()) if isinstance(chunk, dict) else 'Not a dict'}")
            # Check for cancellation before processing each chunk
            if request_id:
                try:
                    from utils.cancellation import is_request_cancelled
                    if is_request_cancelled(request_id):
                        print(f"======== LLM streaming cancelled for request {request_id}")
                        return
                except ImportError:
                    pass  # If we can't import, continue without cancellation check
            
            # Check if the chunk has the expected structure
            if "choices" in chunk and len(chunk["choices"]) > 0:
                choice = chunk["choices"][0]
                print(f"   Choice structure: {choice}")
                
                # Check if the response is finished
                if choice.get("finish_reason") is not None:
                    print(f"   Response finished: {choice.get('finish_reason')}")
                    break
                
                # Extract the text content - try different possible structures
                text_content = ""
                if "delta" in choice and "content" in choice["delta"]:
                    text_content = choice["delta"]["content"]
                    print(f"   Found content in delta: {repr(text_content)}")
                elif "text" in choice:
                    text_content = choice["text"]
                    print(f"   Found content in text: {repr(text_content)}")
                elif "content" in choice:
                    text_content = choice["content"]
                    print(f"   Found content in content: {repr(text_content)}")
                else:
                    print(f"   No text content found in choice: {choice}")
                
                # Process all text content - don't filter out characters unnecessarily
                if text_content:
                    # Clean system tokens from streaming content while preserving whitespace
                    cleaned_content = clean_response_streaming(text_content)
                    print(f"   Cleaned content: {repr(cleaned_content)}")
                    # Yield all content, even if it's just whitespace or single characters
                    print(f"   ✅ Yielding content: {repr(cleaned_content)}")
                    yield cleaned_content
                else:
                    print(f"   ❌ No text content to yield")
            else:
                # Try alternative chunk structures (llama-cpp-python might use different format)
                print(f"   Metadata Chunk doesn't have choices, trying alternative structure: {chunk}")
                
                # Check if chunk has direct text content
                if "text" in chunk:
                    text_content = chunk["text"]
                    print(f"   Found direct text content: {repr(text_content)}")
                    if text_content:
                        cleaned_content = clean_response(text_content)
                        yield cleaned_content
                else:
                    print(f"   No recognizable text content in chunk: {chunk}")
    except Exception as e:
        print(f"❌ Error during LLM streaming: {e}")
        yield f"⚠️ Streaming error: {str(e)}"

def generate_answer_streaming_advanced(prompt: str, request_id: str = None) -> Generator[str, None, None]:
    """Minimal advanced streaming: initialize llama-cpp stream and yield cleaned text only."""
    if llm_mistral is None:
        if not ensure_mistral_loaded():
            yield "⚠️ LLM generation is not available. Please install llama-cpp-python and ensure the Mistral model is available."
            return
    try:
        stream = llm_mistral(
            prompt,
            max_tokens=2048,
            stop=["</s>", "[/INST]"],
            stream=True,
            temperature=0.7,
            top_p=0.9
        )
    except Exception as e:
        yield f"⚠️ Stream initialization failed: {str(e)}"
        return

    import re as _re
    for chunk in stream:
        try:
            choice = chunk.get("choices", [{}])[0]
            text_content = ""
            if isinstance(choice, dict):
                if "delta" in choice and isinstance(choice["delta"], dict):
                    text_content = choice["delta"].get("content", "")
                elif "text" in choice:
                    text_content = choice.get("text", "")
                elif "content" in choice:
                    text_content = choice.get("content", "")
            if text_content:
                cleaned = clean_response_streaming(text_content)
                # Strip an initial "Risposta:" if the model emits it at the very start of generation
                cleaned = _re.sub(r'^\s*(risposta\s*:?)\s*', '', cleaned, flags=_re.IGNORECASE)
                yield cleaned
        except Exception:
            continue

def generate_answer_streaming_with_metadata(context: str, question: str, request_id: str = None) -> Generator[dict, None, None]:
    """
    Generate an answer token by token using streaming with metadata.
    Returns a generator that yields dictionaries with token and metadata.
    """
    if llm_mistral is None:
        if not ensure_mistral_loaded():
            yield {
                "type": "token",
                "token": "⚠️ LLM generation is not available. Please install llama-cpp-python and ensure the Mistral model is available."
            }
            yield {
                "type": "metadata",
                "token_count": 0,
                "finished": True
            }
            return
    
    from utils.unified_system_prompt import get_simple_system_prompt
    system_prompt = get_simple_system_prompt()
    prompt = f"[INST] {system_prompt}\n\nContesto:\n{context}\n\nDomanda:\n{question} [/INST]"
    
    
    # Use the streaming API
    print(f"🔄 Starting LLM stream with metadata, prompt length: {len(prompt)}")
    stream = llm_mistral(prompt, max_tokens=2048, stop=["</s>", "[/INST]", "[INST]"], stream=True, temperature=0.7, top_p=0.9)
    
    # Buffer to collect the full response for thinking extraction
    full_response_buffer = ""
    token_count = 0
    thinking_sent = False
    
    for chunk in stream:
        print(f"   Metadata Chunk {token_count + 1}: {chunk}")
        print(f"   Chunk type: {type(chunk)}")
        print(f"   Chunk keys: {list(chunk.keys()) if isinstance(chunk, dict) else 'Not a dict'}")
        # Check for cancellation before processing each chunk
        if request_id:
            try:
                from utils.cancellation import is_request_cancelled
                if is_request_cancelled(request_id):
                    print(f"======== LLM streaming cancelled for request {request_id}")
                    return
            except ImportError:
                pass  # If we can't import, continue without cancellation check
        
        # Check if the chunk has the expected structure
        if "choices" in chunk and len(chunk["choices"]) > 0:
            choice = chunk["choices"][0]
            print(f"   Metadata Choice structure: {choice}")
            
            # Check if the response is finished
            if choice.get("finish_reason") is not None:
                print(f"   Response finished: {choice.get('finish_reason')}")
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
                print(f"   Found content in delta: {repr(text_content)}")
            elif "text" in choice:
                text_content = choice["text"]
                print(f"   Found content in text: {repr(text_content)}")
            elif "content" in choice:
                text_content = choice["content"]
                print(f"   Found content in content: {repr(text_content)}")
            else:
                print(f"   No text content found in choice: {choice}")
            
            # Only process if we have actual text content
            if text_content and text_content.strip():
                # Clean system tokens from streaming content while preserving whitespace
                cleaned_content = clean_response_streaming(text_content)
                print(f"   Cleaned content: {repr(cleaned_content)}")
                if cleaned_content and cleaned_content.strip():  # Only yield if there's content after cleaning
                    # Add to buffer for thinking extraction
                    full_response_buffer += cleaned_content
                    
                    # Try to extract thinking section if we haven't sent it yet
                    if not thinking_sent and "**🤔 Thinking**" in full_response_buffer:
                        import re
                        thinking_pattern = r'\*\*🤔\s*Thinking\*\*(.*?)(?=\n\n\*\*Risposta\*\*)'
                        thinking_match = re.search(thinking_pattern, full_response_buffer, re.DOTALL | re.IGNORECASE)
                        
                        if thinking_match:
                            thinking_content = thinking_match.group(1).strip()
                            print(f"   Found thinking section: {len(thinking_content)} characters")
                            yield {
                                "type": "thinking",
                                "thinking": thinking_content
                            }
                            thinking_sent = True
                    
                    # Only yield tokens if we've sent the thinking section or if there's no thinking section
                    if thinking_sent or "**🤔 Thinking**" not in full_response_buffer:
                        # Ensure cleaned_content is a string
                        if isinstance(cleaned_content, str) and cleaned_content:
                            token_count += 1
                            yield {
                                "type": "token",
                                "token": cleaned_content,
                                "token_count": token_count
                            }
                        else:
                            print(f"   Skipping non-string or empty token: {type(cleaned_content)} - {repr(cleaned_content)}")
                else:
                    print(f"   Content was empty after cleaning")
            else:
                print(f"   No valid text content to yield")
        else:
            # Try alternative chunk structures (llama-cpp-python might use different format)
            print(f"   Metadata Chunk doesn't have choices, trying alternative structure: {chunk}")
            
            # Check if chunk has direct text content
            if "text" in chunk:
                text_content = chunk["text"]
                print(f"   Found direct text content: {repr(text_content)}")
                if text_content:
                    cleaned_content = clean_response(text_content)
                    token_count += 1
                    yield {
                        "type": "token",
                        "token": cleaned_content,
                        "token_count": token_count
                    }
            elif "content" in chunk:
                text_content = chunk["content"]
                print(f"   Found direct content: {repr(text_content)}")
                if text_content:
                    cleaned_content = clean_response(text_content)
                    token_count += 1
                    yield {
                        "type": "token",
                        "token": cleaned_content,
                        "token_count": token_count
                    }
            else:
                print(f"   No recognizable text content in chunk: {chunk}")
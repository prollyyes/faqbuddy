from llama_cpp import Llama

# Load once at import time
llm = Llama(
    model_path="../models/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=-1,
    verbose=True
)

def generate_answer(context: str, question: str) -> str:
    """Generate a complete answer."""
    prompt = f"[INST] Context:\n{context}\n\nQuestion:\n{question} [/INST]"
    output = llm(prompt, max_tokens=256, stop=["</s>"])
    return output["choices"][0]["text"].strip()

def generate_answer_streaming(context: str, question: str) -> list:
    """Generate an answer token by token."""
    prompt = f"[INST] Context:\n{context}\n\nQuestion:\n{question} [/INST]"
    
    # Use the streaming API
    stream = llm(prompt, max_tokens=256, stop=["</s>"], stream=True)
    
    tokens = []
    for chunk in stream:
        if chunk["choices"][0]["finish_reason"] is not None:
            break
        token = chunk["choices"][0]["delta"].get("content", "")
        if token:
            tokens.append(token)
    
    return tokens
import os
from llama_cpp import Llama

gemma_model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'models', 'gemma-3-4b-it-Q4_1.gguf'))

llm_gemma = Llama(
    model_path=gemma_model_path,
    n_ctx=2048,
    n_threads=6,
    n_gpu_layers=-1,
    verbose=False
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
    text = result["choices"][0].get("text", "").strip().lower()
    if not text:
        return "simple"
    return text.split()[0]

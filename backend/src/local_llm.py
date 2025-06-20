import os
from llama_cpp import Llama

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

def generate_answer(context: str, question: str) -> str:
    prompt = f"[INST] Context:\n{context}\n\nQuestion:\n{question} [/INST]"
    output = llm_mistral(prompt, max_tokens=256, stop=["</s>"])
    return output["choices"][0]["text"].strip()
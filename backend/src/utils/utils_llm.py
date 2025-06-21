from src.utils.local_llm import llm_mistral

def classify_question(question: str) -> str:
    prompt = (
        "Classifica la seguente domanda SOLO come 'simple' o 'complex'. "
        "Rispondi esclusivamente con una di queste due parole, senza spiegazioni, motivazioni o testo aggiuntivo.\n\n"
        "Esempi:\n"
        "Domanda: Quanti crediti vale il corso di informatica?\nRisposta: simple\n"
        "Domanda: Come posso organizzare il piano di studi per laurearmi in 3 anni?\nRisposta: complex\n"
        f"Domanda: {question}\nRisposta:"
    )
    from src.utils.local_llm import llm_gemma
    result = llm_gemma(prompt, max_tokens=2)
    text = result["choices"][0].get("text", "").strip().lower()
    if not text:
        return "simple"
    return text.split()[0]

def generate_answer(context: str, question: str) -> str:
    prompt = f"[INST] Context:\n{context}\n\nQuestion:\n{question} [/INST]"
    output = llm_mistral(prompt, max_tokens=256, stop=["</s>"])
    return output["choices"][0]["text"].strip()

def generate_answer_streaming(context: str, question: str) -> list:
    prompt = f"[INST] Context:\n{context}\n\nQuestion:\n{question} [/INST]"
    stream = llm_mistral(prompt, max_tokens=256, stop=["</s>"], stream=True)
    tokens = []
    for chunk in stream:
        if chunk["choices"][0]["finish_reason"] is not None:
            break
    token = chunk["choices"][0]["delta"].get("content", "")
    if token:
            tokens.append(token)
    return tokens


def sql_results_to_text(question: str, results: list) -> str:
    prompt = (
        "Rispondi in italiano in modo naturale e discorsivo alla seguente domanda, "
        "usando SOLO i dati forniti qui sotto.\n\n"
        f"Domanda: {question}\n"
        f"Dati:\n{results}\n\n"
        "Risposta:"
    )
    output = llm_mistral(prompt, max_tokens=150, stop=["</s>"])
    return output["choices"][0]["text"].strip()
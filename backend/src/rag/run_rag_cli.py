from .rag_pipeline import RAGPipeline

def main():
    rag = RAGPipeline()
    print("Welcome to the RAG CLI! Type your question (or 'exit' to quit):")
    while True:
        question = input("\nYour question: ").strip()
        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        answer = rag.answer(question)
        if answer is None:
            print("[INFO] This is a simple question. Please use the static database lookup.")
        else:
            print("\nRAG Answer:\n")
            print(answer)

if __name__ == "__main__":
    main() 
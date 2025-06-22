import sys
import os

# Add the project root to the Python path
# This allows us to import modules from the 'backend' directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    
from backend.src.rag.rag_core import RAGSystem

def main():
    """
    An interactive command-line interface to test the RAG system.
    """
    print("Initializing RAG System...")
    try:
        rag = RAGSystem()
        print("RAG System Initialized. You can now ask questions.")
        print("Type 'exit' or 'quit' to end the session.")
    except Exception as e:
        print(f"Error initializing RAG System: {e}")
        return

    while True:
        try:
            query = input("\nEnter your question: ")

            if query.lower() in ['exit', 'quit']:
                print("Exiting interactive test. Goodbye!")
                break

            if not query:
                print("Please enter a question.")
                continue

            result = rag.generate_response(query)
            
            print("\n--- RAG Response ---")
            print(f"Query: {query}")
            print(f"\nResponse: {result['response']}")
            
            print("\n--- Performance ---")
            print(f"Retrieval time: {result['retrieval_time']:.2f}s")
            print(f"Generation time: {result['generation_time']:.2f}s")
            print(f"Total time: {result['total_time']:.2f}s")
            
            print("\n--- Context Used ---")
            if result['context_used']:
                for i, context in enumerate(result['context_used'], 1):
                    print(f"\n{i}. {context}")
            else:
                print("No context was used.")
            print("\n" + "="*50)

        except KeyboardInterrupt:
            print("\nExiting interactive test. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            # Optional: Decide if you want to break the loop on error
            # break

if __name__ == "__main__":
    main() 
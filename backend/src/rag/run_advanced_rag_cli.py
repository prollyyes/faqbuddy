#!/usr/bin/env python3
"""
Advanced RAG CLI Interface
=========================

State-of-the-art RAG pipeline with comprehensive testing and evaluation.
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add the src directory to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rag.advanced_rag_pipeline import AdvancedRAGPipeline

def print_banner():
    """Print the CLI banner."""
    print("""
🚀 Advanced RAG Pipeline - State-of-the-Art Performance
=======================================================
🧠 Query Understanding & Intent Classification
🔍 Advanced Retrieval with Query Expansion  
📝 Chain-of-Thought Prompt Engineering
✅ Comprehensive Answer Verification
🛡️ Hallucination Prevention & Fact-Checking
🎯 Thesis-Level Research Quality

Optimized for: University FAQ System (La Sapienza)
""")

def print_help():
    """Print help information."""
    print("""
📋 Available Commands:
--------------------
• Ask any question about courses, professors, procedures, etc.
• 'stats' - Show pipeline statistics
• 'test' - Run comprehensive test suite
• 'help' - Show this help message
• 'quit' or 'exit' - Exit the program

🎯 Example Queries:
------------------
• "Da quanti crediti è il corso di Sistemi Operativi?"
• "Chi insegna il corso di Programmazione?"
• "Come posso iscrivermi al corso di Algoritmi?"
• "Qual è la differenza tra Sistemi Operativi e Reti di Calcolatori?"
• "Spiega cos'è un sistema operativo"

🔬 Advanced Features:
--------------------
• Intent Classification (Factual, Procedural, Comparative, Explanatory)
• Query Expansion & Reformulation
• Chain-of-Thought Reasoning
• Source Attribution & Citation
• Fact-Checking Against Sources
• Hallucination Detection
• Confidence Scoring
• Answer Verification
""")

def print_stats(pipeline: AdvancedRAGPipeline):
    """Print pipeline statistics."""
    stats = pipeline.get_pipeline_stats()
    
    print("\n📊 Pipeline Statistics")
    print("=" * 50)
    print(f"Total Queries Processed: {stats['total_queries']}")
    print(f"Verified Answers: {stats['verified_answers']}")
    print(f"Verification Rate: {stats.get('verification_rate', 0):.1%}")
    print(f"Average Confidence: {stats['average_confidence']:.3f}")
    print(f"Average Processing Time: {stats['average_processing_time']:.2f}s")
    
    if stats['query_types']:
        print(f"\nQuery Types:")
        for query_type, count in stats['query_types'].items():
            print(f"  {query_type}: {count}")
    
    if stats['complexity_levels']:
        print(f"\nComplexity Levels:")
        for complexity, count in stats['complexity_levels'].items():
            print(f"  {complexity}: {count}")
    
    # Verification statistics
    if 'verification_stats' in stats:
        ver_stats = stats['verification_stats']
        print(f"\nVerification Details:")
        print(f"  Total Verifications: {ver_stats['total_verifications']}")
        print(f"  Hallucination Detections: {ver_stats['hallucination_detections']}")
        print(f"  Hallucination Rate: {ver_stats.get('hallucination_rate', 0):.1%}")

def run_comprehensive_test(pipeline: AdvancedRAGPipeline):
    """Run comprehensive test suite."""
    print("\n🧪 Running Comprehensive Test Suite")
    print("=" * 50)
    
    test_queries = [
        # Factual queries
        "Da quanti crediti è il corso di Sistemi Operativi?",
        "Chi insegna il corso di Programmazione?",
        "Qual è il dipartimento di Ingegneria Informatica?",
        
        # Procedural queries
        "Come posso iscrivermi al corso di Algoritmi?",
        "Quali sono i passaggi per richiedere un esame?",
        "Come funziona il sistema di valutazione?",
        
        # Comparative queries
        "Qual è la differenza tra Sistemi Operativi e Reti di Calcolatori?",
        "Quale corso è più difficile tra Algoritmi e Basi di Dati?",
        "Confronta i corsi di Programmazione e Algoritmi",
        
        # Explanatory queries
        "Spiega cos'è un sistema operativo",
        "Cosa significa CFU?",
        "Perché è importante studiare algoritmi?",
        
        # Complex queries
        "Da quanti crediti è il corso di Sistemi Operativi e chi lo insegna?",
        "Come posso iscrivermi al corso di Algoritmi e quali sono i prerequisiti?",
        "Spiega la differenza tra i corsi di Programmazione e Algoritmi e chi li insegna"
    ]
    
    print(f"Testing {len(test_queries)} queries...")
    
    start_time = time.time()
    test_results = pipeline.test_pipeline(test_queries)
    total_time = time.time() - start_time
    
    print(f"\n🎯 Test Results Summary")
    print("=" * 50)
    print(f"Total Test Time: {total_time:.2f}s")
    print(f"Success Rate: {test_results['test_stats']['success_rate']:.1%}")
    print(f"Average Confidence: {test_results['test_stats']['average_confidence']:.3f}")
    print(f"Verification Rate: {test_results['test_stats']['verification_rate']:.1%}")
    print(f"Average Processing Time: {test_results['test_stats']['average_processing_time']:.2f}s")
    
    # Show detailed results for failed queries
    failed_queries = [r for r in test_results['detailed_results'] if not r['success']]
    if failed_queries:
        print(f"\n❌ Failed Queries ({len(failed_queries)}):")
        for result in failed_queries:
            print(f"  • {result['query']}")
            print(f"    Error: {result['error']}")
    
    return test_results

def main():
    """Main CLI function."""
    print_banner()
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY environment variable is required")
        sys.exit(1)
    
    try:
        # Initialize the advanced RAG pipeline
        print("🔧 Initializing Advanced RAG Pipeline...")
        pipeline = AdvancedRAGPipeline()
        print("✅ Pipeline initialized successfully")
        
        print_help()
        
        # Main interaction loop
        while True:
            try:
                user_input = input("\n🤔 Your question: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    print("👋 Goodbye!")
                    break
                
                elif user_input.lower() == 'help':
                    print_help()
                    continue
                
                elif user_input.lower() == 'stats':
                    print_stats(pipeline)
                    continue
                
                elif user_input.lower() == 'test':
                    run_comprehensive_test(pipeline)
                    continue
                
                # Process the query
                print("\n🧠 Processing your question...")
                result = pipeline.answer(user_input)
                
                # Display results
                print(f"\n🤖 Answer:")
                print(f"{result.answer}")
                
                print(f"\n📊 Analysis:")
                print(f"   Query Type: {result.query_analysis.intent.value}")
                print(f"   Complexity: {result.query_analysis.complexity.value}")
                print(f"   Confidence: {result.confidence_score:.3f}")
                print(f"   Verified: {'✅ YES' if result.verification_result.is_verified else '❌ NO'}")
                print(f"   Processing Time: {result.processing_time:.2f}s")
                
                if result.verification_result.unsupported_claims:
                    print(f"   ⚠️ Unsupported Claims: {len(result.verification_result.unsupported_claims)}")
                
                if result.verification_result.missing_information:
                    print(f"   ℹ️ Missing Information: {result.verification_result.missing_information}")
                
                print(f"\n📚 Sources Used: {len(result.retrieval_results)}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Please try again or type 'help' for assistance.")
    
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

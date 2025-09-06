#!/usr/bin/env python3
"""
RAGv2 Command Line Interface
============================

Interactive CLI for testing the RAGv2 pipeline on Ubuntu/Linux systems.
Automatically detects CUDA/CPU and handles all device configurations.
"""

import os
import sys
import time
import json
from typing import Dict, Any

# Add the backend directory to the path for imports
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def setup_environment():
    """Setup environment variables and device detection."""
    print("🔧 Setting up environment...")
    
    # Check for CUDA availability
    try:
        import torch
        if torch.cuda.is_available():
            print(f"🚀 CUDA detected: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA Version: {torch.version.cuda}")
        else:
            print("🖥️ CUDA not available, using CPU")
    except ImportError:
        print("🖥️ PyTorch not installed, using CPU")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check required environment variables
    required_vars = ["PINECONE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("   Please check your .env file")
        return False
    
    print("✅ Environment setup complete")
    return True

def display_feature_flags():
    """Display current feature flags configuration."""
    print("\n📋 Current Feature Flags:")
    print("-" * 40)
    
    from src.rag.config import get_feature_flags
    flags = get_feature_flags()
    
    for flag, enabled in flags.items():
        status = "✅" if enabled else "❌"
        print(f"   {status} {flag}")

def test_pipeline_components():
    """Test individual pipeline components."""
    print("\n🧪 Testing Pipeline Components...")
    print("-" * 40)
    
    try:
        # Test imports
        from src.rag.rag_pipeline_v2 import RAGv2Pipeline
        from src.rag.config import get_ragv2_namespaces
        print("✅ All imports successful")
        
        # Test namespaces
        namespaces = get_ragv2_namespaces()
        print(f"✅ RAGv2 namespaces: {namespaces}")
        
        # Test pipeline initialization
        pipeline = RAGv2Pipeline()
        print("✅ Pipeline initialization successful")
        
        return pipeline
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def interactive_query_loop(pipeline):
    """Interactive query loop with proper error handling."""
    print("\n💬 Interactive Query Mode")
    print("-" * 40)
    print("Type 'quit' or 'exit' to stop")
    print("Type 'stats' to see pipeline statistics")
    print("Type 'help' for more commands")
    
    query_count = 0
    
    while True:
        try:
            question = input("\n🤔 Your question: ").strip()
            
            if not question:
                continue
                
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
                
            if question.lower() == 'stats':
                stats = pipeline.get_pipeline_stats()
                print("\n📊 Pipeline Statistics:")
                print(json.dumps(stats, indent=2))
                continue
                
            if question.lower() == 'help':
                print("\n📖 Available Commands:")
                print("   quit/exit - Exit the program")
                print("   stats - Show pipeline statistics")
                print("   help - Show this help message")
                print("   Any other text - Ask a question to the RAG system")
                continue
            
            print("\n🧠 Thinking...")
            start_time = time.time()
            
            # Process the question
            result = pipeline.answer(question)
            
            processing_time = time.time() - start_time
            query_count += 1
            
            # Handle different result types
            if isinstance(result, dict):
                if "error" in result:
                    print(f"\n❌ Error: {result['error']}")
                else:
                    print(f"\n🤖 Assistant Answer:")
                    print(f"{result.get('answer', 'No answer generated')}")
                    
                    # Show additional info
                    if "retrieved_documents" in result:
                        print(f"\n📚 Retrieved {result['retrieved_documents']} documents")
                    
                    if "features_used" in result:
                        used_features = [f for f, used in result["features_used"].items() if used]
                        if used_features:
                            print(f"🔧 Features used: {', '.join(used_features)}")
                    
                    print(f"⏱️ Processing time: {processing_time:.2f}s")
            else:
                # Handle string responses (error cases)
                print(f"\n🤖 Response: {result}")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            print("   Continuing with next query...")
    
    print(f"\n📊 Session Summary: {query_count} queries processed")

def main():
    """Main CLI function."""
    print("🚀 RAGv2 Command Line Interface")
    print("=" * 50)
    print("Optimized for Ubuntu/Linux systems")
    
    # Setup environment
    if not setup_environment():
        return 1
    
    # Display feature flags
    display_feature_flags()
    
    # Test components
    pipeline = test_pipeline_components()
    if not pipeline:
        return 1
    
    # Start interactive mode
    try:
        interactive_query_loop(pipeline)
    except Exception as e:
        print(f"❌ CLI error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

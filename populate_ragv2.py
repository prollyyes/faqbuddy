#!/usr/bin/env python3
"""
RAGv2 Population Script (Root Level)
====================================

Simple script to populate RAGv2 namespaces from the project root.
"""

import os
import sys
from dotenv import load_dotenv

# Add backend/src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def main():
    """Main function to populate RAGv2 namespaces."""
    load_dotenv()
    
    # Check for required environment variables
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY not found in environment variables")
        print("   Please set PINECONE_API_KEY in your .env file")
        return 1
    
    try:
        from rag.populate_ragv2 import run_full_population
        
        print("🚀 Starting RAGv2 Population...")
        results = run_full_population(verbose=True)
        
        if results["success"]:
            print("✅ Population completed successfully!")
            return 0
        else:
            print("❌ Population failed!")
            for error in results.get("errors", []):
                print(f"   - {error}")
            return 1
            
    except Exception as e:
        print(f"❌ Population failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 
#!/usr/bin/env python3
"""
Simple script to run RAGv2 population from backend/src directory.
"""

import os
import sys
from dotenv import load_dotenv

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
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main()) 
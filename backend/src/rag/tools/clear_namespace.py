#!/usr/bin/env python3
"""
Clear a Pinecone namespace
Usage: python3 -m backend.src.rag.tools.clear_namespace --namespace <namespace_name>
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from pinecone import Pinecone

# Add src to path for absolute-style imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from ..config import INDEX_NAME

def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description="Clear a Pinecone namespace")
    parser.add_argument("--namespace", required=True, help="Namespace to clear")
    parser.add_argument("--confirm", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY is not set")
        sys.exit(1)

    namespace = args.namespace.strip()
    
    if not args.confirm:
        response = input(f"⚠️ Are you sure you want to clear namespace '{namespace}'? This will delete ALL vectors in this namespace. Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("❌ Operation cancelled")
            sys.exit(0)

    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    index = pc.Index(INDEX_NAME)
    
    print(f"🗑️ Clearing namespace '{namespace}'...")
    
    try:
        # Delete all vectors in the namespace
        index.delete(delete_all=True, namespace=namespace)
        print(f"✅ Successfully cleared namespace '{namespace}'")
    except Exception as e:
        print(f"❌ Error clearing namespace: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Clear Pinecone Namespace Script
==============================

Simple script to clear a specific namespace in Pinecone.
Useful for testing and re-processing data.
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from pinecone import Pinecone

def clear_namespace(namespace: str, index_name: str = "exams-index-enhanced", confirm: bool = False):
    """
    Clear all vectors from a specific namespace.
    
    Args:
        namespace: The namespace to clear
        index_name: The Pinecone index name
        confirm: Skip confirmation if True
    """
    load_dotenv()
    
    # Check environment
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        print("❌ PINECONE_API_KEY environment variable is required")
        sys.exit(1)
    
    # Initialize Pinecone
    try:
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
    except Exception as e:
        print(f"❌ Failed to connect to Pinecone: {e}")
        sys.exit(1)
    
    # Get stats before clearing
    try:
        stats = index.describe_index_stats()
        namespace_info = stats.namespaces.get(namespace, {})
        vector_count = namespace_info.get('vector_count', 0)
        
        if vector_count == 0:
            print(f"ℹ️ Namespace '{namespace}' is already empty (0 vectors)")
            return
        
        print(f"📊 Found {vector_count} vectors in namespace '{namespace}'")
        
    except Exception as e:
        print(f"⚠️ Could not get namespace stats: {e}")
        vector_count = "unknown"
    
    # Confirmation
    if not confirm:
        response = input(f"⚠️ Are you sure you want to delete {vector_count} vectors from namespace '{namespace}'? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            print("❌ Operation cancelled")
            sys.exit(0)
    
    # Clear the namespace
    try:
        print(f"🗑️ Clearing namespace '{namespace}'...")
        index.delete(delete_all=True, namespace=namespace)
        print(f"✅ Successfully cleared namespace '{namespace}'")
        
        # Verify clearing
        stats_after = index.describe_index_stats()
        namespace_info_after = stats_after.namespaces.get(namespace, {})
        remaining_count = namespace_info_after.get('vector_count', 0)
        
        if remaining_count == 0:
            print(f"✅ Verification: Namespace '{namespace}' is now empty")
        else:
            print(f"⚠️ Warning: {remaining_count} vectors still remain in namespace '{namespace}'")
        
    except Exception as e:
        print(f"❌ Failed to clear namespace: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Clear Pinecone namespace")
    parser.add_argument("namespace", help="Namespace to clear")
    parser.add_argument("--index", default="exams-index-enhanced", 
                       help="Pinecone index name (default: exams-index-enhanced)")
    parser.add_argument("--confirm", action="store_true", 
                       help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    print(f"🗑️ Pinecone Namespace Cleaner")
    print(f"Index: {args.index}")
    print(f"Namespace: {args.namespace}")
    print("=" * 50)
    
    clear_namespace(args.namespace, args.index, args.confirm)

if __name__ == "__main__":
    main()

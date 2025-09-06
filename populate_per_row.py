#!/usr/bin/env python3
"""
Populate Per-Row Namespace
==========================

This script populates the new "per_row" namespace with vectors generated
using the per-row approach: one vector per database row with minimal metadata.

Usage:
    python populate_per_row.py [--clear] [--batch-size 100] [--verify-only] [--stats-only]
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend/src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from rag.update_pinecone_per_row import PerRowPineconeUpsert

def main():
    """Main function to populate the per-row namespace."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Populate Per-Row Namespace")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for upserting")
    parser.add_argument("--clear", action="store_true", help="Clear the per_row namespace before upserting")
    parser.add_argument("--verify-only", action="store_true", help="Only verify the namespace")
    parser.add_argument("--stats-only", action="store_true", help="Only show namespace statistics")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY environment variable is required")
        sys.exit(1)
    
    print("🚀 Starting Per-Row Namespace Population")
    print("=" * 50)
    
    # Initialize upsert system
    try:
        upsert = PerRowPineconeUpsert()
    except Exception as e:
        print(f"❌ Failed to initialize upsert system: {e}")
        sys.exit(1)
    
    if args.stats_only:
        # Show statistics only
        print("\n📊 Getting namespace statistics...")
        stats = upsert.get_namespace_stats()
        return
    
    if args.verify_only:
        # Verify namespace only
        print("\n🔍 Verifying namespace...")
        verification = upsert.verify_per_row_namespace()
        print(f"Verification result: {verification}")
        return
    
    # Clear namespace if requested
    if args.clear:
        print("\n🗑️ Clearing namespace...")
        clear_result = upsert.clear_per_row_namespace()
        if not clear_result["success"]:
            print(f"❌ Failed to clear namespace: {clear_result}")
            sys.exit(1)
        print("✅ Namespace cleared successfully")
    
    # Upsert vectors
    print(f"\n📊 Upserting vectors with batch size {args.batch_size}...")
    result = upsert.upsert_per_row_vectors(batch_size=args.batch_size)
    
    if result["success"]:
        print(f"\n✅ Per-row upsert completed successfully!")
        print(f"📊 Final Statistics:")
        print(f"   Namespace: {result['namespace']}")
        print(f"   Total vectors: {result['total_vectors']}")
        print(f"   Successful upserts: {result['successful_upserts']}")
        print(f"   Failed upserts: {result['failed_upserts']}")
        print(f"   Success rate: {result['success_rate']:.2%}")
        print(f"   Table breakdown: {result['table_stats']}")
    else:
        print(f"\n❌ Per-row upsert failed: {result}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
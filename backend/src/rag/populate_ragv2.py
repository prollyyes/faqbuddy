#!/usr/bin/env python3
"""
RAGv2 Data Population Script
============================

This script populates the RAGv2 namespaces with data from:
1. Database tables (using schema-aware chunking)
2. PDF documents (if available)
3. Existing documents (if any)

Features:
- Safe upsert to RAGv2 namespaces (documents_v2, db_v2, pdf_v2)
- Progress tracking and error handling
- Batch processing for efficiency
- Verification of data population
"""

import os
import sys
import time
import argparse
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from tqdm import tqdm

from .update_pinecone_ragv2 import SafePineconeUpsert
from .config import get_feature_flags, get_ragv2_namespaces
from .utils.schema_aware_chunker import SchemaAwareChunker
from .utils.embeddings_v2 import EnhancedEmbeddings

def populate_database_chunks(batch_size: int = 100, verbose: bool = True) -> Dict[str, Any]:
    """
    Populate RAGv2 database namespace with schema-aware chunks.
    
    Args:
        batch_size: Number of vectors to upsert per batch
        verbose: Whether to show detailed progress
        
    Returns:
        Dictionary with population results
    """
    if verbose:
        print("📊 Populating Database Chunks to RAGv2...")
        print("=" * 60)
    
    try:
        # Initialize upsert system
        upsert = SafePineconeUpsert()
        
        # Run database upsert
        results = upsert.upsert_database_chunks(batch_size)
        
        if verbose:
            if results["success"]:
                print(f"✅ Database population completed successfully!")
                print(f"   Total chunks: {results['total_chunks']}")
                print(f"   Successful upserts: {results['successful_upserts']}")
                print(f"   Failed upserts: {results['failed_upserts']}")
                print(f"   Success rate: {results['success_rate']:.2%}")
            else:
                print(f"❌ Database population failed: {results.get('error', 'Unknown error')}")
        
        return results
        
    except Exception as e:
        error_msg = f"Database population failed: {str(e)}"
        if verbose:
            print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def populate_pdf_chunks(pdf_directory: str, batch_size: int = 100, verbose: bool = True) -> Dict[str, Any]:
    """
    Populate RAGv2 PDF namespace with PDF chunks.
    
    Args:
        pdf_directory: Directory containing PDF files
        batch_size: Number of vectors to upsert per batch
        verbose: Whether to show detailed progress
        
    Returns:
        Dictionary with population results
    """
    if verbose:
        print(f"📄 Populating PDF Chunks to RAGv2...")
        print("=" * 60)
    
    try:
        # Initialize upsert system
        upsert = SafePineconeUpsert()
        
        # Run PDF upsert
        results = upsert.upsert_pdf_chunks(pdf_directory, batch_size)
        
        if verbose:
            if results["success"]:
                print(f"✅ PDF population completed successfully!")
                print(f"   Total PDFs: {results['total_pdfs']}")
                print(f"   Total chunks: {results['total_chunks']}")
                print(f"   Successful upserts: {results['successful_upserts']}")
                print(f"   Failed upserts: {results['failed_upserts']}")
                print(f"   Success rate: {results['success_rate']:.2%}")
            else:
                print(f"❌ PDF population failed: {results.get('error', 'Unknown error')}")
        
        return results
        
    except Exception as e:
        error_msg = f"PDF population failed: {str(e)}"
        if verbose:
            print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def verify_population(verbose: bool = True) -> Dict[str, Any]:
    """
    Verify that RAGv2 namespaces are properly populated.
    
    Args:
        verbose: Whether to show detailed progress
        
    Returns:
        Dictionary with verification results
    """
    if verbose:
        print("🔍 Verifying RAGv2 Population...")
        print("=" * 60)
    
    try:
        # Initialize upsert system
        upsert = SafePineconeUpsert()
        
        # Run verification
        results = upsert.verify_namespaces()
        
        if verbose:
            if results["success"]:
                print("✅ Population verification completed!")
                print(f"   Index dimension: {results['index_dimension']}")
                print(f"   Index metric: {results['index_metric']}")
                
                print("\n📊 RAGv2 Namespaces:")
                for namespace, info in results["ragv2_namespaces"].items():
                    status = "✅" if info["exists"] and info["vector_count"] > 0 else "❌"
                    print(f"   {status} {namespace}: {info['vector_count']} vectors")
                
                print("\n📊 Existing Namespaces (untouched):")
                for namespace, info in results["existing_namespaces"].items():
                    status = "✅" if info["exists"] else "❌"
                    print(f"   {status} {namespace}: {info['vector_count']} vectors")
                
                if results.get('warnings'):
                    print(f"\n⚠️ Warnings: {results['warnings']}")
            else:
                print(f"❌ Verification failed: {results.get('error', 'Unknown error')}")
        
        return results
        
    except Exception as e:
        error_msg = f"Verification failed: {str(e)}"
        if verbose:
            print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

def run_full_population(pdf_directory: str = None, batch_size: int = 100, verbose: bool = True) -> Dict[str, Any]:
    """
    Run the complete RAGv2 population pipeline.
    
    Args:
        pdf_directory: Directory containing PDF files (optional)
        batch_size: Number of vectors to upsert per batch
        verbose: Whether to show detailed progress
        
    Returns:
        Dictionary with complete population results
    """
    if verbose:
        print("🚀 Starting Full RAGv2 Population Pipeline")
        print("=" * 80)
    
    start_time = time.time()
    results = {
        "success": True,
        "start_time": start_time,
        "database_population": {},
        "pdf_population": {},
        "verification": {},
        "errors": []
    }
    
    try:
        # Step 1: Populate database chunks
        results["database_population"] = populate_database_chunks(batch_size, verbose)
        if not results["database_population"]["success"]:
            results["errors"].append(f"Database population failed: {results['database_population'].get('error')}")
        
        # Step 2: Populate PDF chunks (if directory provided)
        if pdf_directory:
            results["pdf_population"] = populate_pdf_chunks(pdf_directory, batch_size, verbose)
            if not results["pdf_population"]["success"]:
                results["errors"].append(f"PDF population failed: {results['pdf_population'].get('error')}")
        else:
            results["pdf_population"] = {"skipped": True, "reason": "No PDF directory provided"}
        
        # Step 3: Verify population
        results["verification"] = verify_population(verbose)
        if not results["verification"]["success"]:
            results["errors"].append(f"Verification failed: {results['verification'].get('error')}")
        
        # Check overall success
        if results["errors"]:
            results["success"] = False
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(str(e))
        if verbose:
            print(f"❌ Population pipeline failed: {e}")
    
    results["end_time"] = time.time()
    results["total_duration"] = results["end_time"] - results["start_time"]
    
    if verbose:
        print(f"\n✅ RAGv2 Population Pipeline completed in {results['total_duration']:.2f}s")
        print(f"📊 Overall success: {'✅' if results['success'] else '❌'}")
        
        if results["errors"]:
            print(f"❌ Errors encountered: {len(results['errors'])}")
            for error in results["errors"]:
                print(f"   - {error}")
    
    return results

def main():
    """Main function for running the population pipeline."""
    parser = argparse.ArgumentParser(description="Populate RAGv2 Namespaces")
    parser.add_argument("--pdf-dir", help="Directory containing PDF files")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for upserts")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing population")
    parser.add_argument("--database-only", action="store_true", help="Only populate database chunks")
    parser.add_argument("--pdf-only", action="store_true", help="Only populate PDF chunks")
    parser.add_argument("--quiet", action="store_true", help="Suppress verbose output")
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    if not os.getenv("PINECONE_API_KEY"):
        print("❌ PINECONE_API_KEY not found in environment variables")
        print("   Please set PINECONE_API_KEY in your .env file")
        return 1
    
    verbose = not args.quiet
    
    if args.verify_only:
        # Only verify existing population
        results = verify_population(verbose)
        return 0 if results["success"] else 1
    
    elif args.database_only:
        # Only populate database chunks
        results = populate_database_chunks(args.batch_size, verbose)
        return 0 if results["success"] else 1
    
    elif args.pdf_only:
        # Only populate PDF chunks
        if not args.pdf_dir:
            print("❌ PDF directory required for PDF-only population")
            return 1
        results = populate_pdf_chunks(args.pdf_dir, args.batch_size, verbose)
        return 0 if results["success"] else 1
    
    else:
        # Run full population
        results = run_full_population(args.pdf_dir, args.batch_size, verbose)
        return 0 if results["success"] else 1

if __name__ == "__main__":
    exit(main()) 
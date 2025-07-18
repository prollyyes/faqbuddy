"""
Safe Pinecone Upsert Pipeline for RAGv2
=======================================

This module provides a safe way to upsert data to RAGv2 namespaces without affecting
existing namespaces. It uses the new namespaces (documents_v2, db_v2, pdf_v2) while
keeping the existing ones (documents, db) untouched.
"""

import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pinecone import Pinecone
from tqdm import tqdm

from .config import (
    get_ragv2_namespaces,
    get_existing_namespaces,
    INDEX_NAME,
    SCHEMA_AWARE_CHUNKING,
    INSTRUCTOR_XL_EMBEDDINGS
)
from .utils.schema_aware_chunker import SchemaAwareChunker
from .utils.embeddings_v2 import EnhancedEmbeddings
from .utils.generate_chunks import ChunkGenerator
from .utils.pdf_chunker import chunk_pdf

class SafePineconeUpsert:
    """
    Safe Pinecone upsert system for RAGv2 namespaces.
    
    Features:
    - Uses new namespaces (documents_v2, db_v2, pdf_v2)
    - Keeps existing namespaces untouched
    - Supports schema-aware chunking
    - Enhanced embeddings with instructor-xl
    - Progress tracking and error handling
    """
    
    def __init__(self):
        """Initialize the safe upsert system."""
        load_dotenv()
        
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = INDEX_NAME
        self.ragv2_namespaces = get_ragv2_namespaces()
        self.existing_namespaces = get_existing_namespaces()
        
        # Initialize components
        self.embeddings = EnhancedEmbeddings()
        self.schema_chunker = SchemaAwareChunker() if SCHEMA_AWARE_CHUNKING else None
        self.legacy_chunker = ChunkGenerator()
        
        print("🚀 Initializing Safe Pinecone Upsert for RAGv2")
        print(f"   Index: {self.index_name}")
        print(f"   RAGv2 namespaces: {self.ragv2_namespaces}")
        print(f"   Existing namespaces (untouched): {self.existing_namespaces}")
        print(f"   Schema-aware chunking: {SCHEMA_AWARE_CHUNKING}")
        print(f"   Instructor-XL embeddings: {INSTRUCTOR_XL_EMBEDDINGS}")
    
    def _get_index_info(self) -> Dict[str, Any]:
        """Get information about the Pinecone index."""
        try:
            index = self.pc.Index(self.index_name)
            stats = index.describe_index_stats()
            return {
                "dimension": stats.get("dimension"),
                "metric": stats.get("metric"),
                "namespaces": stats.get("namespaces", {}),
                "total_vector_count": stats.get("total_vector_count", 0)
            }
        except Exception as e:
            print(f"❌ Error getting index info: {e}")
            return {}
    
    def _check_namespace_exists(self, namespace: str) -> bool:
        """Check if a namespace exists in the index."""
        try:
            index = self.pc.Index(self.index_name)
            stats = index.describe_index_stats()
            return namespace in stats.get("namespaces", {})
        except Exception as e:
            print(f"❌ Error checking namespace {namespace}: {e}")
            return False
    
    def _upsert_batch(self, vectors: List[Dict[str, Any]], namespace: str) -> bool:
        """
        Upsert a batch of vectors to a specific namespace.
        
        Args:
            vectors: List of vectors to upsert
            namespace: Target namespace
            
        Returns:
            True if successful, False otherwise
        """
        try:
            index = self.pc.Index(self.index_name)
            index.upsert(vectors=vectors, namespace=namespace)
            return True
        except Exception as e:
            print(f"❌ Error upserting to namespace {namespace}: {e}")
            return False
    
    def upsert_database_chunks(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Upsert database chunks to RAGv2 namespace.
        
        Args:
            batch_size: Number of vectors to upsert per batch
            
        Returns:
            Dictionary with upsert statistics
        """
        print(f"\n📊 Upserting database chunks to {self.ragv2_namespaces['db']}...")
        
        # Get chunks based on feature flag
        if SCHEMA_AWARE_CHUNKING and self.schema_chunker:
            print("   Using schema-aware chunking...")
            chunks = self.schema_chunker.get_all_chunks()
        else:
            print("   Using legacy chunking...")
            chunks = self.legacy_chunker.get_chunks()
        
        if not chunks:
            print("   ⚠️ No chunks generated")
            return {"success": False, "error": "No chunks generated"}
        
        print(f"   Generated {len(chunks)} chunks")
        
        # Prepare vectors for upsert
        vectors = []
        successful_upserts = 0
        failed_upserts = 0
        
        for i, chunk in enumerate(tqdm(chunks, desc="Processing chunks")):
            try:
                # Generate embedding
                embedding = self.embeddings.encode_single(chunk['text'])
                
                # Prepare vector
                vector = {
                    'id': chunk['id'],
                    'values': embedding,
                    'metadata': chunk['metadata']
                }
                vectors.append(vector)
                
                # Upsert batch when full
                if len(vectors) >= batch_size:
                    if self._upsert_batch(vectors, self.ragv2_namespaces['db']):
                        successful_upserts += len(vectors)
                    else:
                        failed_upserts += len(vectors)
                    vectors = []
                    
            except Exception as e:
                print(f"   ❌ Error processing chunk {i}: {e}")
                failed_upserts += 1
        
        # Upsert remaining vectors
        if vectors:
            if self._upsert_batch(vectors, self.ragv2_namespaces['db']):
                successful_upserts += len(vectors)
            else:
                failed_upserts += len(vectors)
        
        stats = {
            "success": True,
            "namespace": self.ragv2_namespaces['db'],
            "total_chunks": len(chunks),
            "successful_upserts": successful_upserts,
            "failed_upserts": failed_upserts,
            "success_rate": successful_upserts / len(chunks) if chunks else 0
        }
        
        print(f"   ✅ Database upsert completed: {successful_upserts}/{len(chunks)} chunks")
        return stats
    
    def upsert_pdf_chunks(self, pdf_directory: str, batch_size: int = 100) -> Dict[str, Any]:
        """
        Upsert PDF chunks to RAGv2 PDF namespace.
        
        Args:
            pdf_directory: Directory containing PDF files
            batch_size: Number of vectors to upsert per batch
            
        Returns:
            Dictionary with upsert statistics
        """
        print(f"\n📄 Upserting PDF chunks to {self.ragv2_namespaces['pdf']}...")
        
        if not os.path.exists(pdf_directory):
            print(f"   ❌ PDF directory not found: {pdf_directory}")
            return {"success": False, "error": f"Directory not found: {pdf_directory}"}
        
        # Get PDF files
        pdf_files = [f for f in os.listdir(pdf_directory) if f.lower().endswith('.pdf')]
        if not pdf_files:
            print(f"   ⚠️ No PDF files found in {pdf_directory}")
            return {"success": False, "error": "No PDF files found"}
        
        print(f"   Found {len(pdf_files)} PDF files")
        
        # Process PDFs
        vectors = []
        successful_upserts = 0
        failed_upserts = 0
        total_chunks = 0
        
        for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
            try:
                pdf_path = os.path.join(pdf_directory, pdf_file)
                chunks = chunk_pdf(pdf_path, ocr=False, window_tokens=512, overlap_tokens=50)
                
                for i, chunk in enumerate(chunks):
                    try:
                        # Generate embedding
                        embedding = self.embeddings.encode_single(chunk['text'])
                        
                        # Add PDF-specific metadata
                        chunk['metadata'].update({
                            'source_type': 'pdf',
                            'pdf_file': pdf_file,
                            'pdf_path': pdf_path,
                            'chunk_index': i
                        })
                        
                        # Prepare vector
                        vector = {
                            'id': f"{os.path.splitext(pdf_file)[0]}_chunk_{i+1}",
                            'values': embedding,
                            'metadata': chunk['metadata']
                        }
                        vectors.append(vector)
                        total_chunks += 1
                        
                        # Upsert batch when full
                        if len(vectors) >= batch_size:
                            if self._upsert_batch(vectors, self.ragv2_namespaces['pdf']):
                                successful_upserts += len(vectors)
                            else:
                                failed_upserts += len(vectors)
                            vectors = []
                            
                    except Exception as e:
                        print(f"   ❌ Error processing chunk {i} from {pdf_file}: {e}")
                        failed_upserts += 1
                        
            except Exception as e:
                print(f"   ❌ Error processing PDF {pdf_file}: {e}")
                failed_upserts += 1
        
        # Upsert remaining vectors
        if vectors:
            if self._upsert_batch(vectors, self.ragv2_namespaces['pdf']):
                successful_upserts += len(vectors)
            else:
                failed_upserts += len(vectors)
        
        stats = {
            "success": True,
            "namespace": self.ragv2_namespaces['pdf'],
            "total_pdfs": len(pdf_files),
            "total_chunks": total_chunks,
            "successful_upserts": successful_upserts,
            "failed_upserts": failed_upserts,
            "success_rate": successful_upserts / total_chunks if total_chunks > 0 else 0
        }
        
        print(f"   ✅ PDF upsert completed: {successful_upserts}/{total_chunks} chunks")
        return stats
    
    def verify_namespaces(self) -> Dict[str, Any]:
        """
        Verify that RAGv2 namespaces are properly set up and existing ones are untouched.
        
        Returns:
            Dictionary with verification results
        """
        print(f"\n🔍 Verifying namespaces...")
        
        index_info = self._get_index_info()
        if not index_info:
            return {"success": False, "error": "Could not get index info"}
        
        verification = {
            "success": True,
            "index_dimension": index_info.get("dimension"),
            "index_metric": index_info.get("metric"),
            "ragv2_namespaces": {},
            "existing_namespaces": {},
            "warnings": []
        }
        
        # Check RAGv2 namespaces
        for ns_type, namespace in self.ragv2_namespaces.items():
            exists = self._check_namespace_exists(namespace)
            verification["ragv2_namespaces"][namespace] = {
                "exists": exists,
                "vector_count": index_info.get("namespaces", {}).get(namespace, {}).get("vector_count", 0)
            }
            if not exists:
                verification["warnings"].append(f"RAGv2 namespace {namespace} does not exist yet")
        
        # Check existing namespaces (should be untouched)
        for ns_type, namespace in self.existing_namespaces.items():
            exists = self._check_namespace_exists(namespace)
            verification["existing_namespaces"][namespace] = {
                "exists": exists,
                "vector_count": index_info.get("namespaces", {}).get(namespace, {}).get("vector_count", 0)
            }
            if not exists:
                verification["warnings"].append(f"Existing namespace {namespace} does not exist")
        
        print(f"   ✅ Namespace verification completed")
        for namespace, info in verification["ragv2_namespaces"].items():
            status = "✅" if info["exists"] else "❌"
            print(f"   {status} {namespace}: {info['vector_count']} vectors")
        
        return verification
    
    def run_full_upsert(self, pdf_directory: str = None, batch_size: int = 100) -> Dict[str, Any]:
        """
        Run the complete upsert pipeline for RAGv2.
        
        Args:
            pdf_directory: Directory containing PDF files (optional)
            batch_size: Number of vectors to upsert per batch
            
        Returns:
            Dictionary with complete upsert results
        """
        print("🚀 Starting Full RAGv2 Upsert Pipeline")
        print("=" * 60)
        
        start_time = time.time()
        results = {
            "success": True,
            "start_time": start_time,
            "verification": {},
            "database_upsert": {},
            "pdf_upsert": {},
            "errors": []
        }
        
        try:
            # Step 1: Verify namespaces
            results["verification"] = self.verify_namespaces()
            
            # Step 2: Upsert database chunks
            results["database_upsert"] = self.upsert_database_chunks(batch_size)
            
            # Step 3: Upsert PDF chunks (if directory provided)
            if pdf_directory:
                results["pdf_upsert"] = self.upsert_pdf_chunks(pdf_directory, batch_size)
            else:
                results["pdf_upsert"] = {"skipped": True, "reason": "No PDF directory provided"}
            
            # Step 4: Final verification
            results["final_verification"] = self.verify_namespaces()
            
        except Exception as e:
            results["success"] = False
            results["errors"].append(str(e))
            print(f"❌ Upsert pipeline failed: {e}")
        
        results["end_time"] = time.time()
        results["total_duration"] = results["end_time"] - results["start_time"]
        
        print(f"\n✅ RAGv2 Upsert Pipeline completed in {results['total_duration']:.2f}s")
        
        return results


def main():
    """Main function for running the safe upsert pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Safe Pinecone Upsert for RAGv2")
    parser.add_argument("--pdf-dir", help="Directory containing PDF files")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for upserts")
    parser.add_argument("--verify-only", action="store_true", help="Only verify namespaces")
    
    args = parser.parse_args()
    
    # Initialize upsert system
    upsert = SafePineconeUpsert()
    
    if args.verify_only:
        # Only verify namespaces
        results = upsert.verify_namespaces()
        print(f"\n📊 Verification Results:")
        print(f"   Success: {results['success']}")
        if results.get('warnings'):
            print(f"   Warnings: {results['warnings']}")
    else:
        # Run full upsert
        results = upsert.run_full_upsert(args.pdf_dir, args.batch_size)
        print(f"\n📊 Upsert Results:")
        print(f"   Success: {results['success']}")
        print(f"   Duration: {results['total_duration']:.2f}s")
        if results.get('errors'):
            print(f"   Errors: {results['errors']}")


if __name__ == "__main__":
    main() 
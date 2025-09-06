"""
Per-Row Pinecone Upsert Pipeline
================================

This module provides a safe way to upsert data to the new "per_row" namespace
using the per-row approach: one vector per semantic row with minimal metadata.

Features:
- Uses new "per_row" namespace
- One vector per database row
- Minimal metadata (node-ID + optional filters)
- Natural language representation of each row
- Prepared for graph-based relationship handling
"""

import os
import sys
from typing import List, Dict, Any
from dotenv import load_dotenv
from pinecone import Pinecone
from tqdm import tqdm

# Add the src directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.config import (
    INDEX_NAME,
    get_per_row_namespace
)
from rag.utils.per_row_chunker import PerRowChunker
from rag.utils.embeddings_v2 import EnhancedEmbeddings

class PerRowPineconeUpsert:
    """
    Per-row Pinecone upsert system for the new approach.
    
    Features:
    - Uses "per_row" namespace
    - One vector per database row
    - Minimal metadata for graph relationships
    - Enhanced embeddings with instructor-xl
    - Progress tracking and error handling
    """
    
    def __init__(self):
        """Initialize the per-row upsert system."""
        load_dotenv()
        
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = INDEX_NAME
        self.per_row_namespace = get_per_row_namespace()
        
        # Initialize components
        self.embeddings = EnhancedEmbeddings()
        self.per_row_chunker = PerRowChunker()
        
        print("🚀 Initializing Per-Row Pinecone Upsert")
        print(f"   Index: {self.index_name}")
        print(f"   Per-row namespace: {self.per_row_namespace}")
        print(f"   Enhanced embeddings: {self.embeddings.model_name}")
    
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
    
    def upsert_per_row_vectors(self, batch_size: int = 100) -> Dict[str, Any]:
        """
        Upsert per-row vectors to the per_row namespace.
        
        Args:
            batch_size: Number of vectors to upsert per batch
            
        Returns:
            Dictionary with upsert statistics
        """
        print(f"\n📊 Upserting per-row vectors to {self.per_row_namespace}...")
        
        # Get per-row vectors
        print("   Generating per-row vectors...")
        vectors_data = self.per_row_chunker.get_all_rows()
        
        if not vectors_data:
            print("   ⚠️ No vectors generated")
            return {"success": False, "error": "No vectors generated"}
        
        print(f"   Generated {len(vectors_data)} per-row vectors")
        
        # Get table statistics
        table_stats = self.per_row_chunker.get_table_stats()
        print(f"   Table statistics: {table_stats}")
        
        # Prepare vectors for upsert
        vectors = []
        successful_upserts = 0
        failed_upserts = 0
        
        for i, vector_data in enumerate(tqdm(vectors_data, desc="Processing vectors")):
            try:
                # Generate embedding
                embedding = self.embeddings.encode_single(vector_data['text'])
                
                # Clean metadata (remove null values)
                cleaned_metadata = {}
                for key, value in vector_data['metadata'].items():
                    if value is not None:
                        if isinstance(value, (str, int, float, bool)):
                            cleaned_metadata[key] = value
                        else:
                            cleaned_metadata[key] = str(value)
                
                # Prepare vector
                vector = {
                    'id': vector_data['id'],
                    'values': embedding,
                    'metadata': {
                        **cleaned_metadata,
                        'text': vector_data['text']  # Add text to metadata for retrieval
                    }
                }
                vectors.append(vector)
                
                # Upsert batch when full
                if len(vectors) >= batch_size:
                    if self._upsert_batch(vectors, self.per_row_namespace):
                        successful_upserts += len(vectors)
                    else:
                        failed_upserts += len(vectors)
                    vectors = []
                    
            except Exception as e:
                print(f"   ❌ Error processing vector {i}: {e}")
                failed_upserts += 1
        
        # Upsert remaining vectors
        if vectors:
            if self._upsert_batch(vectors, self.per_row_namespace):
                successful_upserts += len(vectors)
            else:
                failed_upserts += len(vectors)
        
        stats = {
            "success": True,
            "namespace": self.per_row_namespace,
            "total_vectors": len(vectors_data),
            "successful_upserts": successful_upserts,
            "failed_upserts": failed_upserts,
            "success_rate": successful_upserts / len(vectors_data) if vectors_data else 0,
            "table_stats": table_stats
        }
        
        print(f"   ✅ Per-row upsert completed: {successful_upserts}/{len(vectors_data)} vectors")
        return stats
    
    def clear_per_row_namespace(self) -> Dict[str, Any]:
        """
        Clear all vectors from the per_row namespace.
        
        Returns:
            Dictionary with clear operation results
        """
        print(f"\n🗑️ Clearing namespace '{self.per_row_namespace}'...")
        
        try:
            index = self.pc.Index(self.index_name)
            
            # Get current stats to show what we're clearing
            stats = index.describe_index_stats()
            if self.per_row_namespace in stats.get("namespaces", {}):
                vector_count = stats["namespaces"][self.per_row_namespace].get("vector_count", 0)
                print(f"   Found {vector_count} vectors in namespace '{self.per_row_namespace}'")
            else:
                print(f"   No vectors found in namespace '{self.per_row_namespace}'")
                return {"success": True, "message": "Namespace was already empty"}
            
            # Clear the namespace
            index.delete(namespace=self.per_row_namespace, delete_all=True)
            print(f"   ✅ Cleared namespace '{self.per_row_namespace}'")
            
            return {
                "success": True,
                "namespace": self.per_row_namespace,
                "cleared_vectors": vector_count
            }
            
        except Exception as e:
            print(f"   ❌ Error clearing namespace: {e}")
            return {"success": False, "error": str(e)}
    
    def verify_per_row_namespace(self) -> Dict[str, Any]:
        """
        Verify that the per_row namespace is properly set up.
        
        Returns:
            Dictionary with verification results
        """
        print(f"\n🔍 Verifying per-row namespace...")
        
        index_info = self._get_index_info()
        if not index_info:
            return {"success": False, "error": "Could not get index info"}
        
        verification = {
            "success": True,
            "index_dimension": index_info.get("dimension"),
            "index_metric": index_info.get("metric"),
            "per_row_namespace": {},
            "warnings": []
        }
        
        # Check per-row namespace
        exists = self._check_namespace_exists(self.per_row_namespace)
        verification["per_row_namespace"] = {
            "exists": exists,
            "vector_count": index_info.get("namespaces", {}).get(self.per_row_namespace, {}).get("vector_count", 0)
        }
        
        if not exists:
            verification["warnings"].append(f"Per-row namespace {self.per_row_namespace} does not exist yet")
        else:
            vector_count = verification["per_row_namespace"]["vector_count"]
            print(f"   ✅ Per-row namespace exists with {vector_count} vectors")
        
        # Check table statistics
        table_stats = self.per_row_chunker.get_table_stats()
        total_expected = sum(table_stats.values())
        print(f"   📊 Expected vectors from database: {total_expected}")
        
        if exists and vector_count > 0:
            if vector_count != total_expected:
                verification["warnings"].append(f"Vector count mismatch: {vector_count} in namespace vs {total_expected} expected from database")
            else:
                print(f"   ✅ Vector count matches expected: {vector_count}")
        
        print(f"   ✅ Per-row namespace verification completed")
        return verification
    
    def get_namespace_stats(self) -> Dict[str, Any]:
        """
        Get detailed statistics about the per_row namespace.
        
        Returns:
            Dictionary with namespace statistics
        """
        print(f"\n📈 Getting per-row namespace statistics...")
        
        try:
            index = self.pc.Index(self.index_name)
            stats = index.describe_index_stats()
            
            namespace_stats = stats.get("namespaces", {}).get(self.per_row_namespace, {})
            vector_count = namespace_stats.get("vector_count", 0)
            
            # Get table statistics for comparison
            table_stats = self.per_row_chunker.get_table_stats()
            total_expected = sum(table_stats.values())
            
            stats_info = {
                "namespace": self.per_row_namespace,
                "vector_count": vector_count,
                "expected_count": total_expected,
                "table_breakdown": table_stats,
                "coverage_percentage": (vector_count / total_expected * 100) if total_expected > 0 else 0
            }
            
            print(f"   📊 Namespace: {self.per_row_namespace}")
            print(f"   📊 Vectors in namespace: {vector_count}")
            print(f"   📊 Expected from database: {total_expected}")
            print(f"   📊 Coverage: {stats_info['coverage_percentage']:.1f}%")
            print(f"   📊 Table breakdown: {table_stats}")
            
            return stats_info
            
        except Exception as e:
            print(f"   ❌ Error getting namespace stats: {e}")
            return {"error": str(e)}


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Per-Row Pinecone Upsert Tool")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for upserting")
    parser.add_argument("--clear", action="store_true", help="Clear the per_row namespace before upserting")
    parser.add_argument("--verify-only", action="store_true", help="Only verify the namespace")
    parser.add_argument("--stats-only", action="store_true", help="Only show namespace statistics")
    
    args = parser.parse_args()
    
    # Initialize upsert system
    upsert = PerRowPineconeUpsert()
    
    if args.stats_only:
        # Show statistics only
        stats = upsert.get_namespace_stats()
        return
    
    if args.verify_only:
        # Verify namespace only
        verification = upsert.verify_per_row_namespace()
        print(f"Verification result: {verification}")
        return
    
    # Clear namespace if requested
    if args.clear:
        clear_result = upsert.clear_per_row_namespace()
        if not clear_result["success"]:
            print(f"❌ Failed to clear namespace: {clear_result}")
            return
    
    # Upsert vectors
    result = upsert.upsert_per_row_vectors(batch_size=args.batch_size)
    
    if result["success"]:
        print(f"✅ Per-row upsert completed successfully!")
        print(f"📊 Statistics: {result}")
    else:
        print(f"❌ Per-row upsert failed: {result}")


if __name__ == "__main__":
    main() 
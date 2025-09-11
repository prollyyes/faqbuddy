#!/usr/bin/env python3
"""
Extract Data from Specific Pinecone Namespaces
==============================================

This script extracts all document chunks from specific namespaces:
- advanced_db
- pdf_v2

It automatically detects the correct index and extracts all data for ChatGPT processing.
"""

import os
import sys
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from pinecone import Pinecone
from tqdm import tqdm

# Add the backend src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend/src'))

# Import configuration
try:
    from rag.config import INDEX_NAME
except ImportError:
    # Fallback configuration if import fails
    INDEX_NAME = "exams-index-enhanced"

class SpecificNamespaceExtractor:
    """
    Extracts data from specific Pinecone namespaces.
    """
    
    def __init__(self):
        """Initialize the extractor."""
        load_dotenv()
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Target namespaces
        self.target_namespaces = ["pdf_v2", "contextual_db"]
        
        print("🚀 Initializing Specific Namespace Extractor")
        print(f"   Target namespaces: {self.target_namespaces}")
        
        # Find the correct index
        self.index_name = self._find_correct_index()
        print(f"   Using index: {self.index_name}")
    
    def _find_correct_index(self) -> str:
        """Find the correct index that contains our target namespaces."""
        possible_indexes = [
            "exams-index-enhanced",
            "exams-index-mpnet", 
            "exams-index-advanced"
        ]
        
        print("🔍 Checking available indexes...")
        
        # List all available indexes
        available_indexes = self.pc.list_indexes().names()
        print(f"   Available indexes: {available_indexes}")
        
        # Check each possible index
        for index_name in possible_indexes:
            if index_name in available_indexes:
                print(f"   Checking index: {index_name}")
                
                try:
                    index = self.pc.Index(index_name)
                    stats = index.describe_index_stats()
                    namespaces = stats.get("namespaces", {}).keys()
                    
                    print(f"   Namespaces in {index_name}: {list(namespaces)}")
                    
                    # Check if our target namespaces exist
                    found_namespaces = [ns for ns in self.target_namespaces if ns in namespaces]
                    if found_namespaces:
                        print(f"   ✅ Found target namespaces: {found_namespaces}")
                        return index_name
                        
                except Exception as e:
                    print(f"   ❌ Error checking {index_name}: {e}")
        
        # If no specific index found, try the first available one
        if available_indexes:
            print(f"   ⚠️  No index found with target namespaces, using: {available_indexes[0]}")
            return available_indexes[0]
        
        raise ValueError("No Pinecone indexes found!")
    
    def _get_namespace_stats(self) -> Dict[str, Any]:
        """Get statistics for target namespaces."""
        try:
            index = self.pc.Index(self.index_name)
            stats = index.describe_index_stats()
            
            namespace_stats = {}
            for namespace in self.target_namespaces:
                ns_data = stats.get("namespaces", {}).get(namespace, {})
                namespace_stats[namespace] = {
                    "vector_count": ns_data.get("vector_count", 0),
                    "exists": namespace in stats.get("namespaces", {})
                }
            
            return namespace_stats
            
        except Exception as e:
            print(f"❌ Error getting namespace stats: {e}")
            return {}
    
    def _extract_namespace_data(self, namespace: str, max_vectors: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Extract all data from a specific namespace.
        
        Args:
            namespace: Namespace to extract from
            max_vectors: Maximum number of vectors to extract
            
        Returns:
            List of extracted vectors with metadata
        """
        print(f"\n🔍 Extracting data from namespace: {namespace}")
        
        try:
            index = self.pc.Index(self.index_name)
            
            # Get namespace stats
            stats = self._get_namespace_stats()
            vector_count = stats.get(namespace, {}).get("vector_count", 0)
            
            if vector_count == 0:
                print(f"   ⚠️  Namespace {namespace} is empty")
                return []
            
            print(f"   📊 Found {vector_count} vectors in namespace")
            
            extracted_data = []
            batch_size = 1000
            max_batches = 20  # Limit to prevent infinite loops
            
            # Create a dummy query vector (all zeros)
            dummy_vector = [0.0] * 768  # Assuming 768 dimensions
            
            for batch_num in range(max_batches):
                try:
                    # Query with dummy vector to get results
                    response = index.query(
                        vector=dummy_vector,
                        top_k=min(batch_size, vector_count - len(extracted_data)),
                        namespace=namespace,
                        include_metadata=True
                    )
                    
                    if not response.matches:
                        break
                    
                    for match in response.matches:
                        # Handle different text storage formats
                        text_content = ""
                        if match.metadata and "text" in match.metadata:
                            text_content = match.metadata.get("text", "")
                        elif match.metadata:
                            # For pdf_v2, text might be in other fields or we need to handle differently
                            # Let's include all metadata for now
                            text_content = str(match.metadata)
                        
                        extracted_data.append({
                            "id": match.id,
                            "score": match.score,
                            "metadata": match.metadata or {},
                            "text": text_content
                        })
                    
                    print(f"   📥 Extracted batch {batch_num + 1}: {len(response.matches)} vectors")
                    
                    # Check if we have enough data
                    if max_vectors and len(extracted_data) >= max_vectors:
                        extracted_data = extracted_data[:max_vectors]
                        break
                        
                    if len(response.matches) < batch_size:
                        break
                        
                    # Small delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"   ❌ Error in batch {batch_num + 1}: {e}")
                    break
            
            print(f"   ✅ Successfully extracted {len(extracted_data)} vectors from {namespace}")
            return extracted_data
            
        except Exception as e:
            print(f"   ❌ Error extracting from namespace {namespace}: {e}")
            return []
    
    def extract_target_namespaces(self, max_vectors_per_namespace: Optional[int] = None) -> Dict[str, Any]:
        """
        Extract data from target namespaces.
        
        Args:
            max_vectors_per_namespace: Maximum vectors to extract per namespace
            
        Returns:
            Dictionary containing extracted data
        """
        print(f"\n🚀 Starting extraction from target namespaces")
        
        # Get namespace stats first
        stats = self._get_namespace_stats()
        print(f"\n📊 Namespace Statistics:")
        for namespace, data in stats.items():
            status = "✅ Exists" if data["exists"] else "❌ Not found"
            print(f"   {namespace}: {status} ({data['vector_count']} vectors)")
        
        extracted_data = {
            "extraction_info": {
                "timestamp": datetime.now().isoformat(),
                "index_name": self.index_name,
                "target_namespaces": self.target_namespaces,
                "max_vectors_per_namespace": max_vectors_per_namespace
            },
            "namespaces": {}
        }
        
        # Extract from each target namespace
        for namespace in self.target_namespaces:
            if stats.get(namespace, {}).get("exists", False):
                namespace_data = self._extract_namespace_data(namespace, max_vectors_per_namespace)
                extracted_data["namespaces"][namespace] = {
                    "vector_count": len(namespace_data),
                    "data": namespace_data
                }
            else:
                print(f"   ⚠️  Skipping {namespace} - namespace not found")
                extracted_data["namespaces"][namespace] = {
                    "vector_count": 0,
                    "data": [],
                    "status": "namespace_not_found"
                }
        
        # Calculate summary
        total_vectors = sum(ns["vector_count"] for ns in extracted_data["namespaces"].values())
        extracted_data["extraction_info"]["total_extracted_vectors"] = total_vectors
        
        print(f"\n✅ Extraction completed!")
        print(f"   📊 Total vectors extracted: {total_vectors}")
        
        return extracted_data
    
    def save_for_chatgpt(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Save extracted data in a format suitable for ChatGPT.
        
        Args:
            data: Extracted data dictionary
            output_path: Path to save the file
        """
        print(f"\n💾 Saving data for ChatGPT processing: {output_path}")
        
        # Create a simplified format for ChatGPT
        chatgpt_data = {
            "source": "Pinecone RAG Pipeline",
            "extracted_at": datetime.now().isoformat(),
            "index": self.index_name,
            "total_documents": sum(ns["vector_count"] for ns in data["namespaces"].values()),
            "documents": []
        }
        
        # Flatten all documents
        for namespace, namespace_data in data["namespaces"].items():
            for doc in namespace_data["data"]:
                # Include all documents, even if they don't have text content
                text_content = doc.get("text", "")
                if not text_content and doc.get("metadata"):
                    # For documents without text, include metadata as text
                    text_content = f"Metadata: {doc['metadata']}"
                
                chatgpt_data["documents"].append({
                    "id": doc["id"],
                    "text": text_content,
                    "namespace": namespace,
                    "metadata": doc["metadata"]
                })
        
        # Save as JSON
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(chatgpt_data, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"   ✅ Data saved successfully ({file_size:.2f} MB)")
            print(f"   📄 Total documents: {len(chatgpt_data['documents'])}")
            
        except Exception as e:
            print(f"   ❌ Error saving data: {e}")
            raise


def main():
    """Main function to extract data from specific namespaces."""
    print("🎯 Extracting data from specific namespaces for ChatGPT")
    print("=" * 60)
    
    try:
        # Initialize extractor
        extractor = SpecificNamespaceExtractor()
        
        # Extract data
        print(f"\n📥 Extracting data from target namespaces...")
        extracted_data = extractor.extract_target_namespaces()
        
        # Save for ChatGPT
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = f"pinecone_chunks_for_chatgpt_{timestamp}.json"
        extractor.save_for_chatgpt(extracted_data, output_path)
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Review the extracted data: {output_path}")
        print(f"   2. Upload this file to ChatGPT")
        print(f"   3. Use ChatGPT to generate 200 ground truths")
        
        # Show summary
        total_docs = sum(ns["vector_count"] for ns in extracted_data["namespaces"].values())
        print(f"\n📊 Summary:")
        print(f"   📁 Output file: {output_path}")
        print(f"   📄 Total documents: {total_docs}")
        print(f"   📂 Namespaces: {list(extracted_data['namespaces'].keys())}")
        
        print(f"\n✅ Extraction completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during extraction: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

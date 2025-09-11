#!/usr/bin/env python3
"""
Pinecone Data Extraction for RAG Pipeline Evaluation
====================================================

This script extracts all data from Pinecone namespaces to create a comprehensive
dataset for generating ground truths for RAG pipeline evaluation.

Features:
- Extracts data from all available namespaces
- Preserves metadata and text content
- Formats data for GPT-5 ground truth generation
- Creates structured JSON output for evaluation
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
import argparse

# Add the backend src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../backend/src'))

# Import configuration
try:
    from rag.config import (
        INDEX_NAME, 
        get_ragv2_namespaces, 
        get_existing_namespaces, 
        get_per_row_namespace,
        ADVANCED_DB_NAMESPACE,
        ADVANCED_DB_ENABLED
    )
except ImportError:
    # Fallback configuration if import fails
    INDEX_NAME = "exams-index-enhanced"
    ADVANCED_DB_NAMESPACE = "advanced_db"
    ADVANCED_DB_ENABLED = True
    
    def get_ragv2_namespaces():
        return {
            "docs": "documents_v2",
            "db": "advanced_db" if ADVANCED_DB_ENABLED else "per_row",
            "pdf": "pdf_v2"
        }
    
    def get_existing_namespaces():
        return {
            "docs": "documents",
            "db": "db"
        }
    
    def get_per_row_namespace():
        return "per_row"

class PineconeDataExtractor:
    """
    Extracts all data from Pinecone namespaces for evaluation dataset creation.
    """
    
    def __init__(self):
        """Initialize the Pinecone data extractor."""
        load_dotenv()
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index_name = INDEX_NAME
        
        # Get all namespace configurations
        self.ragv2_namespaces = get_ragv2_namespaces()
        self.existing_namespaces = get_existing_namespaces()
        self.per_row_namespace = get_per_row_namespace()
        
        print("🚀 Initializing Pinecone Data Extractor")
        print(f"   Index: {self.index_name}")
        print(f"   RAGv2 namespaces: {self.ragv2_namespaces}")
        print(f"   Existing namespaces: {self.existing_namespaces}")
        print(f"   Per-row namespace: {self.per_row_namespace}")
        
        # Get index information
        self.index_info = self._get_index_info()
        print(f"   Total vectors: {self.index_info.get('total_vector_count', 0)}")
    
    def _get_index_info(self) -> Dict[str, Any]:
        """Get comprehensive index information."""
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
    
    def _extract_namespace_data(self, namespace: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Extract all data from a specific namespace.
        
        Args:
            namespace: Namespace to extract from
            limit: Maximum number of vectors to extract (None for all)
            
        Returns:
            List of extracted vectors with metadata
        """
        print(f"\n🔍 Extracting data from namespace: {namespace}")
        
        try:
            index = self.pc.Index(self.index_name)
            
            # Get namespace stats
            namespace_stats = self.index_info.get("namespaces", {}).get(namespace, {})
            vector_count = namespace_stats.get("vector_count", 0)
            
            if vector_count == 0:
                print(f"   ⚠️  Namespace {namespace} is empty")
                return []
            
            print(f"   📊 Found {vector_count} vectors in namespace")
            
            # For large namespaces, we'll need to use pagination
            # Since Pinecone doesn't support direct enumeration, we'll use a workaround
            # by querying with random vectors to sample the data
            
            extracted_data = []
            batch_size = 1000
            max_batches = limit // batch_size if limit else 10  # Sample up to 10k vectors per namespace
            
            # Create a dummy query vector (all zeros) to get some results
            dummy_vector = [0.0] * self.index_info.get("dimension", 768)
            
            for batch_num in range(max_batches):
                try:
                    # Query with a dummy vector to get random results
                    response = index.query(
                        vector=dummy_vector,
                        top_k=min(batch_size, vector_count - len(extracted_data)),
                        namespace=namespace,
                        include_metadata=True
                    )
                    
                    if not response.matches:
                        break
                    
                    for match in response.matches:
                        extracted_data.append({
                            "id": match.id,
                            "score": match.score,
                            "metadata": match.metadata or {},
                            "text": match.metadata.get("text", "") if match.metadata else ""
                        })
                    
                    print(f"   📥 Extracted batch {batch_num + 1}: {len(response.matches)} vectors")
                    
                    # If we have enough data or no more matches, break
                    if len(extracted_data) >= (limit or vector_count) or len(response.matches) < batch_size:
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
    
    def extract_all_data(self, max_vectors_per_namespace: Optional[int] = None) -> Dict[str, Any]:
        """
        Extract data from all available namespaces.
        
        Args:
            max_vectors_per_namespace: Maximum vectors to extract per namespace
            
        Returns:
            Dictionary containing all extracted data organized by namespace
        """
        print("\n🚀 Starting comprehensive data extraction")
        
        all_data = {
            "extraction_info": {
                "timestamp": datetime.now().isoformat(),
                "index_name": self.index_name,
                "index_info": self.index_info,
                "max_vectors_per_namespace": max_vectors_per_namespace
            },
            "namespaces": {}
        }
        
        # Extrct from all available namespaces
        all_namespaces = {}
        
        # Add RAGv2 namespaces
        all_namespaces.update(self.ragv2_namespaces)
        
        # Add existing namespaces
        all_namespaces.update(self.existing_namespaces)
        
        # Add per-row namespace
        all_namespaces["per_row"] = self.per_row_namespace
        
        # Add advanced DB namespace if enabled
        if ADVANCED_DB_ENABLED:
            all_namespaces["advanced_db"] = ADVANCED_DB_NAMESPACE
        
        # Extract from each namespace
        for namespace_type, namespace in all_namespaces.items():
            print(f"\n📂 Processing namespace type: {namespace_type}")
            
            # Check if namespace exists
            if namespace in self.index_info.get("namespaces", {}):
                namespace_data = self._extract_namespace_data(namespace, max_vectors_per_namespace)
                all_data["namespaces"][namespace_type] = {
                    "namespace": namespace,
                    "vector_count": len(namespace_data),
                    "data": namespace_data
                }
            else:
                print(f"   ⚠️  Namespace {namespace} does not exist in index")
                all_data["namespaces"][namespace_type] = {
                    "namespace": namespace,
                    "vector_count": 0,
                    "data": [],
                    "status": "namespace_not_found"
                }
        
        # Calculate summary statistics
        total_vectors = sum(ns["vector_count"] for ns in all_data["namespaces"].values())
        all_data["extraction_info"]["total_extracted_vectors"] = total_vectors
        
        print(f"\n✅ Extraction completed!")
        print(f"   📊 Total vectors extracted: {total_vectors}")
        print(f"   📂 Namespaces processed: {len(all_data['namespaces'])}")
        
        return all_data
    
    def save_extracted_data(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Save extracted data to JSON file.
        
        Args:
            data: Extracted data dictionary
            output_path: Path to save the JSON file
        """
        print(f"\n💾 Saving extracted data to: {output_path}")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"   ✅ Data saved successfully ({file_size:.2f} MB)")
            
        except Exception as e:
            print(f"   ❌ Error saving data: {e}")
            raise
    
    def create_evaluation_dataset(self, data: Dict[str, Any], output_path: str) -> None:
        """
        Create a formatted dataset for ground truth generation.
        
        Args:
            data: Extracted Pinecone data
            output_path: Path to save the evaluation dataset
        """
        print(f"\n📝 Creating evaluation dataset for ground truth generation")
        
        evaluation_dataset = {
            "dataset_info": {
                "created_at": datetime.now().isoformat(),
                "source": "Pinecone RAG Pipeline",
                "purpose": "Ground truth generation for RAG evaluation",
                "total_documents": sum(ns["vector_count"] for ns in data["namespaces"].values()),
                "namespaces": list(data["namespaces"].keys())
            },
            "documents": [],
            "instructions": {
                "task": "Generate 200 high-quality question-answer pairs for RAG pipeline evaluation",
                "requirements": [
                    "Questions should cover diverse topics from the university domain",
                    "Answers should be factual and directly derivable from the provided documents",
                    "Include both simple and complex questions",
                    "Cover different question types: factual, procedural, comparative, analytical",
                    "Ensure questions test different aspects of the RAG pipeline",
                    "Questions should be in Italian (university context)"
                ],
                "output_format": {
                    "question": "The question text",
                    "answer": "The expected answer",
                    "context_documents": ["List of document IDs that should be retrieved"],
                    "question_type": "factual|procedural|comparative|analytical",
                    "difficulty": "easy|medium|hard",
                    "domain": "academic|administrative|procedural"
                }
            }
        }
        
        # Extract all documents with their content
        for namespace_type, namespace_data in data["namespaces"].items():
            for doc in namespace_data["data"]:
                if doc.get("text"):  # Only include documents with text content
                    evaluation_dataset["documents"].append({
                        "id": doc["id"],
                        "text": doc["text"],
                        "metadata": doc["metadata"],
                        "namespace": namespace_type,
                        "source_namespace": namespace_data["namespace"]
                    })
        
        # Save the evaluation dataset
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_dataset, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
            print(f"   ✅ Evaluation dataset created successfully ({file_size:.2f} MB)")
            print(f"   📄 Total documents: {len(evaluation_dataset['documents'])}")
            
        except Exception as e:
            print(f"   ❌ Error creating evaluation dataset: {e}")
            raise


def main():
    """Main function to run the data extraction."""
    parser = argparse.ArgumentParser(description="Extract Pinecone data for RAG evaluation")
    parser.add_argument("--max-vectors", type=int, default=5000, 
                       help="Maximum vectors to extract per namespace (default: 5000)")
    parser.add_argument("--output-dir", type=str, default="./extracted_data",
                       help="Output directory for extracted data (default: ./extracted_data)")
    parser.add_argument("--extract-only", action="store_true",
                       help="Only extract raw data, don't create evaluation dataset")
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Initialize extractor
    extractor = PineconeDataExtractor()
    
    # Extract all data
    print(f"\n🔍 Extracting data (max {args.max_vectors} vectors per namespace)")
    extracted_data = extractor.extract_all_data(args.max_vectors)
    
    # Save raw extracted data
    raw_data_path = os.path.join(args.output_dir, f"pinecone_raw_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    extractor.save_extracted_data(extracted_data, raw_data_path)
    
    if not args.extract_only:
        # Create evaluation dataset
        eval_dataset_path = os.path.join(args.output_dir, f"evaluation_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        extractor.create_evaluation_dataset(extracted_data, eval_dataset_path)
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Review the evaluation dataset: {eval_dataset_path}")
        print(f"   2. Use the dataset with GPT-5 to generate 200 ground truths")
        print(f"   3. The dataset includes {len(extracted_data['namespaces'])} namespaces with diverse content")
    
    print(f"\n✅ Data extraction completed successfully!")
    print(f"   📁 Output directory: {args.output_dir}")
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)

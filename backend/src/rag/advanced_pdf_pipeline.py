"""
Advanced PDF Processing Pipeline Integration
==========================================

This module integrates the advanced PDF processor with the existing RAG system,
providing a complete end-to-end pipeline for thesis-grade PDF processing.

Features:
- Integration with existing embedding and vector storage systems
- Batch processing capabilities
- Quality monitoring and reporting
- Fallback mechanisms for reliability
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import json
from dataclasses import asdict

# Core PDF processing
from .utils.advanced_pdf_processor import (
    AdvancedPDFProcessor, 
    ProcessedChunk, 
    DocumentStructure,
    DocumentType
)
from .utils.pdf_evaluation import PDFProcessingEvaluator, DocumentProcessingMetrics

# RAG system integration
from .utils.embeddings_v2 import EnhancedEmbeddings
from .config import *
from pinecone import Pinecone

logger = logging.getLogger(__name__)

class AdvancedPDFPipeline:
    """
    Complete PDF processing pipeline for RAG integration.
    
    This pipeline provides:
    - Advanced PDF processing with context preservation
    - Quality assessment and filtering
    - Embedding generation with enhanced models
    - Vector database integration
    - Comprehensive monitoring and evaluation
    """
    
    def __init__(self,
                 pinecone_client: Optional[Pinecone] = None,
                 index_name: str = INDEX_NAME,
                 namespace: str = RAGV2_PDF_NAMESPACE,
                 enable_evaluation: bool = True,
                 quality_threshold: float = 0.7,
                 batch_size: int = 100):
        """
        Initialize the advanced PDF pipeline.
        
        Args:
            pinecone_client: Pinecone client instance
            index_name: Name of the Pinecone index
            namespace: Namespace for PDF vectors
            enable_evaluation: Whether to enable quality evaluation
            quality_threshold: Minimum quality threshold for chunks
            batch_size: Batch size for vector operations
        """
        self.index_name = index_name
        self.namespace = namespace
        self.quality_threshold = quality_threshold
        self.batch_size = batch_size
        
        # Initialize Pinecone client
        if pinecone_client:
            self.pc = pinecone_client
        else:
            self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        
        # Get index
        try:
            self.index = self.pc.Index(index_name)
            logger.info(f"Connected to Pinecone index: {index_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Pinecone index {index_name}: {e}")
            raise
        
        # Initialize PDF processor
        self.pdf_processor = AdvancedPDFProcessor(
            enable_ocr=True,
            enable_nlp=True,
            min_chunk_size=MIN_CHUNK_SIZE if 'MIN_CHUNK_SIZE' in globals() else 150,
            max_chunk_size=MAX_CHUNK_SIZE if 'MAX_CHUNK_SIZE' in globals() else 800,
            quality_threshold=quality_threshold
        )
        
        # Initialize embeddings
        self.embeddings = EnhancedEmbeddings()
        logger.info("Enhanced embeddings initialized")
        
        # Initialize evaluator if enabled
        self.evaluator = None
        if enable_evaluation:
            try:
                self.evaluator = PDFProcessingEvaluator(enable_advanced_metrics=True)
                logger.info("PDF evaluation framework initialized")
            except Exception as e:
                logger.warning(f"Could not initialize evaluator: {e}")
        
        # Processing statistics
        self.stats = {
            "documents_processed": 0,
            "chunks_created": 0,
            "vectors_uploaded": 0,
            "quality_filtered": 0,
            "processing_errors": 0,
            "total_processing_time": 0.0,
            "average_quality_score": 0.0
        }
        
        logger.info("Advanced PDF Pipeline initialized")
    
    def process_single_pdf(self, 
                          pdf_path: str,
                          doc_id: Optional[str] = None,
                          metadata_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a single PDF file through the complete pipeline.
        
        Args:
            pdf_path: Path to the PDF file
            doc_id: Optional custom document ID
            metadata_override: Optional metadata to add to all chunks
            
        Returns:
            Dictionary with processing results and metrics
        """
        logger.info(f"Processing PDF: {pdf_path}")
        start_time = time.time()
        
        try:
            # Step 1: Process PDF with advanced processor
            chunks, structure = self.pdf_processor.process_pdf(pdf_path)
            
            if not chunks:
                logger.warning(f"No chunks generated for {pdf_path}")
                return {
                    "success": False,
                    "error": "No chunks generated",
                    "processing_time": time.time() - start_time
                }
            
            logger.info(f"Generated {len(chunks)} chunks from {pdf_path}")
            
            # Step 2: Quality filtering
            high_quality_chunks = [
                chunk for chunk in chunks 
                if chunk.metadata.text_quality_score >= self.quality_threshold
            ]
            
            filtered_count = len(chunks) - len(high_quality_chunks)
            if filtered_count > 0:
                logger.info(f"Filtered out {filtered_count} low-quality chunks")
                self.stats["quality_filtered"] += filtered_count
            
            if not high_quality_chunks:
                logger.warning(f"No chunks passed quality threshold for {pdf_path}")
                return {
                    "success": False,
                    "error": "No chunks passed quality threshold",
                    "processing_time": time.time() - start_time,
                    "original_chunks": len(chunks),
                    "quality_threshold": self.quality_threshold
                }
            
            # Step 3: Generate embeddings
            logger.info("Generating embeddings for chunks...")
            embedded_chunks = []
            
            for chunk in high_quality_chunks:
                try:
                    # Generate embedding
                    embedding = self.embeddings.encode_single(chunk.text)
                    chunk.embedding = embedding
                    
                    # Add metadata override if provided
                    if metadata_override:
                        for key, value in metadata_override.items():
                            setattr(chunk.metadata, key, value)
                    
                    embedded_chunks.append(chunk)
                    
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for chunk {chunk.metadata.chunk_id}: {e}")
                    continue
            
            if not embedded_chunks:
                logger.error(f"Failed to generate embeddings for {pdf_path}")
                return {
                    "success": False,
                    "error": "Embedding generation failed",
                    "processing_time": time.time() - start_time
                }
            
            logger.info(f"Generated embeddings for {len(embedded_chunks)} chunks")
            
            # Step 4: Upload to vector database
            upload_result = self._upload_vectors(embedded_chunks)
            
            # Step 5: Evaluate processing quality
            evaluation_metrics = None
            if self.evaluator:
                try:
                    processing_time = time.time() - start_time
                    doc_id_eval = doc_id or os.path.basename(pdf_path)
                    evaluation_metrics = self.evaluator.evaluate_document_processing(
                        chunks, structure, processing_time, doc_id_eval
                    )
                except Exception as e:
                    logger.warning(f"Evaluation failed: {e}")
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(chunks, embedded_chunks, processing_time)
            
            # Prepare result
            result = {
                "success": True,
                "processing_time": processing_time,
                "document_structure": asdict(structure),
                "chunks_generated": len(chunks),
                "chunks_processed": len(embedded_chunks),
                "chunks_uploaded": upload_result["uploaded_count"],
                "upload_errors": upload_result["error_count"],
                "quality_metrics": asdict(evaluation_metrics) if evaluation_metrics else None,
                "average_quality_score": sum(
                    chunk.metadata.text_quality_score for chunk in embedded_chunks
                ) / len(embedded_chunks) if embedded_chunks else 0.0
            }
            
            logger.info(f"Successfully processed {pdf_path} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            self.stats["processing_errors"] += 1
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def process_pdf_directory(self, 
                            pdf_directory: str,
                            recursive: bool = True,
                            skip_existing: bool = True,
                            progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """
        Process all PDF files in a directory.
        
        Args:
            pdf_directory: Directory containing PDF files
            recursive: Whether to search subdirectories
            skip_existing: Whether to skip files already in vector database
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with batch processing results
        """
        logger.info(f"Processing PDF directory: {pdf_directory}")
        
        # Find PDF files
        pdf_pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = list(Path(pdf_directory).glob(pdf_pattern))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in {pdf_directory}")
            return {
                "success": False,
                "error": "No PDF files found",
                "directory": pdf_directory
            }
        
        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process files
        results = []
        successful_count = 0
        error_count = 0
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                # Skip existing if requested
                if skip_existing and self._is_pdf_processed(str(pdf_file)):
                    logger.info(f"Skipping already processed file: {pdf_file.name}")
                    continue
                
                # Process file
                result = self.process_single_pdf(str(pdf_file))
                result["file_path"] = str(pdf_file)
                result["file_name"] = pdf_file.name
                
                if result["success"]:
                    successful_count += 1
                else:
                    error_count += 1
                
                results.append(result)
                
                # Progress callback
                if progress_callback:
                    progress_callback(i + 1, len(pdf_files), pdf_file.name, result["success"])
                
                # Log progress
                if (i + 1) % 5 == 0:
                    logger.info(f"Processed {i + 1}/{len(pdf_files)} files "
                              f"({successful_count} successful, {error_count} errors)")
            
            except Exception as e:
                logger.error(f"Unexpected error processing {pdf_file}: {e}")
                error_count += 1
                results.append({
                    "success": False,
                    "error": f"Unexpected error: {str(e)}",
                    "file_path": str(pdf_file),
                    "file_name": pdf_file.name
                })
        
        # Calculate summary statistics
        processing_times = [r["processing_time"] for r in results if "processing_time" in r]
        total_chunks = sum(r.get("chunks_processed", 0) for r in results)
        total_processing_time = sum(processing_times) if processing_times else 0
        
        summary = {
            "success": True,
            "directory": pdf_directory,
            "files_found": len(pdf_files),
            "files_processed": len(results),
            "successful_files": successful_count,
            "failed_files": error_count,
            "total_chunks_processed": total_chunks,
            "total_processing_time": total_processing_time,
            "average_processing_time": (
                total_processing_time / len(processing_times) if processing_times else 0
            ),
            "processing_rate": (
                len(processing_times) / total_processing_time if total_processing_time > 0 else 0
            ),
            "detailed_results": results
        }
        
        logger.info(f"Batch processing complete: {successful_count}/{len(pdf_files)} successful")
        return summary
    
    def evaluate_pipeline_quality(self, 
                                pdf_files: List[str],
                                configurations: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Evaluate pipeline quality across different configurations.
        
        Args:
            pdf_files: List of PDF files for evaluation
            configurations: Optional list of processor configurations to test
            
        Returns:
            Comprehensive evaluation results
        """
        if not self.evaluator:
            return {"error": "Evaluator not available"}
        
        logger.info(f"Starting pipeline quality evaluation with {len(pdf_files)} files")
        
        # Default configurations if none provided
        if configurations is None:
            configurations = [
                # Fast configuration
                {
                    "enable_ocr": False,
                    "enable_nlp": False,
                    "min_chunk_size": 100,
                    "max_chunk_size": 500,
                    "quality_threshold": 0.5
                },
                # Balanced configuration
                {
                    "enable_ocr": True,
                    "enable_nlp": False,
                    "min_chunk_size": 150,
                    "max_chunk_size": 600,
                    "quality_threshold": 0.6
                },
                # High-quality configuration (current)
                {
                    "enable_ocr": True,
                    "enable_nlp": True,
                    "min_chunk_size": 150,
                    "max_chunk_size": 800,
                    "quality_threshold": 0.7
                },
                # Maximum quality configuration
                {
                    "enable_ocr": True,
                    "enable_nlp": True,
                    "min_chunk_size": 200,
                    "max_chunk_size": 1000,
                    "quality_threshold": 0.8
                }
            ]
        
        # Run benchmark evaluation
        benchmark_results = self.evaluator.benchmark_configurations(pdf_files, configurations)
        
        # Generate comprehensive report
        evaluation_report = self.evaluator.generate_evaluation_report(benchmark_results)
        
        # Add pipeline-specific metrics
        evaluation_report["pipeline_stats"] = self.get_processing_stats()
        evaluation_report["embedding_model"] = self.embeddings.model_name
        evaluation_report["vector_database"] = {
            "index_name": self.index_name,
            "namespace": self.namespace
        }
        
        return evaluation_report
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        stats = self.stats.copy()
        
        # Add calculated metrics
        if stats["documents_processed"] > 0:
            stats["average_chunks_per_document"] = stats["chunks_created"] / stats["documents_processed"]
            stats["average_processing_time_per_document"] = (
                stats["total_processing_time"] / stats["documents_processed"]
            )
            stats["quality_filter_rate"] = stats["quality_filtered"] / stats["chunks_created"]
            stats["error_rate"] = stats["processing_errors"] / stats["documents_processed"]
        
        return stats
    
    def search_processed_pdfs(self, 
                            query: str, 
                            top_k: int = 10,
                            min_score: float = 0.7) -> List[Dict[str, Any]]:
        """
        Search through processed PDF content.
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum similarity score
            
        Returns:
            List of search results with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.encode_single(query)
            
            # Search vector database
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=self.namespace,
                filter={"source_type": "pdf"}  # Filter for PDF content
            )
            
            # Process and filter results
            filtered_results = []
            for match in search_results.matches:
                if match.score >= min_score:
                    result = {
                        "text": match.metadata.get("text", ""),
                        "score": match.score,
                        "source_file": match.metadata.get("source", match.metadata.get("source_file", "")),
                        "page_number": match.metadata.get("page", match.metadata.get("page_number", 0)),
                        "chunk_type": match.metadata.get("chunk_type", ""),
                        "section_hierarchy": match.metadata.get("section_hierarchy", []),
                        "quality_score": match.metadata.get("text_quality_score", 0.0)
                    }
                    filtered_results.append(result)
            
            logger.info(f"Found {len(filtered_results)} results for query: {query[:50]}...")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def _upload_vectors(self, chunks: List[ProcessedChunk]) -> Dict[str, Any]:
        """Upload chunk embeddings to vector database."""
        logger.info(f"Uploading {len(chunks)} vectors to namespace '{self.namespace}'")
        
        vectors = []
        uploaded_count = 0
        error_count = 0
        
        for chunk in chunks:
            try:
                # Prepare vector for upload
                vector_data = {
                    "id": chunk.metadata.chunk_id,
                    "values": chunk.embedding,
                    "metadata": {
                        # Core content
                        "text": chunk.text,
                        "source_type": "pdf",
                        
                        # Basic identifiers
                        "doc_id": chunk.metadata.doc_id,
                        "source_file": chunk.metadata.source_file,
                        "page_number": chunk.metadata.page_number,
                        "chunk_index": chunk.metadata.chunk_index,
                        
                        # Content classification
                        "chunk_type": chunk.metadata.chunk_type.value,
                        "heading_level": chunk.metadata.heading_level if chunk.metadata.heading_level is not None else 0,
                        "parent_section": chunk.metadata.parent_section or "",
                        "section_hierarchy": [str(s) for s in chunk.metadata.section_hierarchy if s is not None],
                        
                        # Quality metrics
                        "text_quality_score": chunk.metadata.text_quality_score,
                        "text_length": chunk.metadata.text_length,
                        "token_count": chunk.metadata.token_count,
                        "language": chunk.metadata.language,
                        
                        # Processing metadata
                        "processing_timestamp": chunk.metadata.processing_timestamp,
                        "pipeline_version": chunk.metadata.pipeline_version,
                        "embedding_model": self.embeddings.model_name
                    }
                }
                
                vectors.append(vector_data)
                
                # Upload in batches
                if len(vectors) >= self.batch_size:
                    upload_batch_result = self._upload_batch(vectors)
                    uploaded_count += upload_batch_result["uploaded"]
                    error_count += upload_batch_result["errors"]
                    vectors = []
                    
            except Exception as e:
                logger.warning(f"Error preparing vector for chunk {chunk.metadata.chunk_id}: {e}")
                error_count += 1
        
        # Upload remaining vectors
        if vectors:
            upload_batch_result = self._upload_batch(vectors)
            uploaded_count += upload_batch_result["uploaded"]
            error_count += upload_batch_result["errors"]
        
        # Update statistics
        self.stats["vectors_uploaded"] += uploaded_count
        
        logger.info(f"Vector upload complete: {uploaded_count} uploaded, {error_count} errors")
        return {
            "uploaded_count": uploaded_count,
            "error_count": error_count,
            "total_attempted": len(chunks)
        }
    
    def _upload_batch(self, vectors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Upload a batch of vectors to Pinecone."""
        try:
            self.index.upsert(vectors=vectors, namespace=self.namespace)
            return {"uploaded": len(vectors), "errors": 0}
        except Exception as e:
            logger.error(f"Batch upload failed: {e}")
            return {"uploaded": 0, "errors": len(vectors)}
    
    def _is_pdf_processed(self, pdf_path: str) -> bool:
        """Check if a PDF file has already been processed."""
        try:
            # Simple check based on file name in metadata
            file_name = os.path.basename(pdf_path)
            
            # Query for existing vectors from this file
            query_result = self.index.query(
                vector=[0.0] * self.embeddings.embedding_dimension,  # Dummy vector
                top_k=1,
                include_metadata=True,
                namespace=self.namespace,
                filter={"source_file": file_name}
            )
            
            return len(query_result.matches) > 0
            
        except Exception as e:
            logger.warning(f"Could not check if {pdf_path} is processed: {e}")
            return False
    
    def _update_stats(self, 
                     all_chunks: List[ProcessedChunk], 
                     processed_chunks: List[ProcessedChunk], 
                     processing_time: float):
        """Update processing statistics."""
        self.stats["documents_processed"] += 1
        self.stats["chunks_created"] += len(all_chunks)
        self.stats["total_processing_time"] += processing_time
        
        if processed_chunks:
            avg_quality = sum(
                chunk.metadata.text_quality_score for chunk in processed_chunks
            ) / len(processed_chunks)
            
            # Update running average
            total_docs = self.stats["documents_processed"]
            current_avg = self.stats["average_quality_score"]
            self.stats["average_quality_score"] = (
                (current_avg * (total_docs - 1) + avg_quality) / total_docs
            )

# Example usage and CLI interface
if __name__ == "__main__":
    import argparse
    import sys
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    parser = argparse.ArgumentParser(description="Advanced PDF Processing Pipeline")
    parser.add_argument("command", choices=["process", "evaluate", "search"], 
                       help="Command to execute")
    parser.add_argument("--input", required=True, 
                       help="Input PDF file or directory")
    parser.add_argument("--namespace", default=RAGV2_PDF_NAMESPACE,
                       help="Pinecone namespace")
    parser.add_argument("--quality-threshold", type=float, default=0.7,
                       help="Quality threshold for filtering")
    parser.add_argument("--batch-size", type=int, default=100,
                       help="Batch size for vector operations")
    parser.add_argument("--output", help="Output directory for results")
    parser.add_argument("--query", help="Search query (for search command)")
    
    args = parser.parse_args()
    
    try:
        # Initialize pipeline
        pipeline = AdvancedPDFPipeline(
            namespace=args.namespace,
            quality_threshold=args.quality_threshold,
            batch_size=args.batch_size
        )
        
        if args.command == "process":
            if os.path.isfile(args.input):
                # Process single file
                result = pipeline.process_single_pdf(args.input)
                print(f"Processing result: {json.dumps(result, indent=2)}")
            else:
                # Process directory
                result = pipeline.process_pdf_directory(args.input)
                print(f"Batch processing result: {json.dumps(result, indent=2)}")
                
        elif args.command == "evaluate":
            # Find PDF files for evaluation
            if os.path.isdir(args.input):
                pdf_files = [str(p) for p in Path(args.input).glob("*.pdf")]
            else:
                pdf_files = [args.input]
            
            if not pdf_files:
                print("No PDF files found for evaluation")
                sys.exit(1)
            
            # Run evaluation
            evaluation_result = pipeline.evaluate_pipeline_quality(pdf_files)
            
            # Save or print results
            if args.output:
                os.makedirs(args.output, exist_ok=True)
                output_file = os.path.join(args.output, "pipeline_evaluation.json")
                with open(output_file, 'w') as f:
                    json.dump(evaluation_result, f, indent=2)
                print(f"Evaluation results saved to {output_file}")
            else:
                print(json.dumps(evaluation_result, indent=2))
                
        elif args.command == "search":
            if not args.query:
                print("Query required for search command")
                sys.exit(1)
            
            results = pipeline.search_processed_pdfs(args.query)
            print(f"Search results for '{args.query}':")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result['source_file']} (page {result['page_number']})")
                print(f"   Score: {result['score']:.3f}")
                print(f"   Text: {result['text'][:200]}...")
        
        # Print final statistics
        stats = pipeline.get_processing_stats()
        print(f"\nPipeline Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)

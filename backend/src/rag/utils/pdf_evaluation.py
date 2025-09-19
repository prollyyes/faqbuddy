"""
PDF Processing Pipeline Evaluation Framework
==========================================

This module provides comprehensive evaluation tools for the advanced PDF processing pipeline.
It includes metrics for quality assessment, benchmarking, and comparative analysis.

For thesis requirements, this framework enables rigorous evaluation of PDF processing
quality across different document types and processing configurations.
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics

# Text similarity and evaluation
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    SIMILARITY_AVAILABLE = True
except ImportError:
    SIMILARITY_AVAILABLE = False

# Advanced text analysis
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

from .advanced_pdf_processor import AdvancedPDFProcessor, ProcessedChunk, DocumentStructure

logger = logging.getLogger(__name__)

@dataclass
class ChunkQualityMetrics:
    """Quality metrics for individual chunks."""
    chunk_id: str
    text_quality_score: float
    readability_score: float
    information_density: float
    context_preservation_score: float
    semantic_coherence: float
    
@dataclass
class DocumentProcessingMetrics:
    """Overall document processing metrics."""
    document_id: str
    processing_time: float
    chunk_count: int
    average_chunk_quality: float
    content_coverage: float
    structure_preservation: float
    metadata_completeness: float
    overall_score: float

@dataclass
class BenchmarkResult:
    """Results from benchmark evaluation."""
    processor_config: Dict[str, Any]
    document_metrics: List[DocumentProcessingMetrics]
    average_processing_time: float
    average_quality_score: float
    chunk_count_distribution: Dict[str, int]
    quality_distribution: Dict[str, float]
    processing_success_rate: float

class PDFProcessingEvaluator:
    """
    Comprehensive evaluation framework for PDF processing pipeline.
    
    Features:
    - Quality assessment across multiple dimensions
    - Benchmarking against different configurations
    - Comparative analysis and reporting
    - Ground truth evaluation when available
    """
    
    def __init__(self, 
                 similarity_model: str = "all-mpnet-base-v2",
                 enable_advanced_metrics: bool = True):
        """
        Initialize the evaluation framework.
        
        Args:
            similarity_model: Model for semantic similarity evaluation
            enable_advanced_metrics: Whether to compute advanced metrics
        """
        self.enable_advanced_metrics = enable_advanced_metrics
        
        # Initialize similarity model if available
        self.similarity_model = None
        if SIMILARITY_AVAILABLE and enable_advanced_metrics:
            try:
                self.similarity_model = SentenceTransformer(similarity_model)
                logger.info(f"Similarity model loaded: {similarity_model}")
            except Exception as e:
                logger.warning(f"Could not load similarity model: {e}")
        
        # Evaluation cache for performance
        self.evaluation_cache = {}
        
    def evaluate_chunk_quality(self, chunk: ProcessedChunk) -> ChunkQualityMetrics:
        """
        Evaluate the quality of a single processed chunk.
        
        Args:
            chunk: Processed chunk to evaluate
            
        Returns:
            ChunkQualityMetrics with comprehensive quality assessment
        """
        text = chunk.text
        metadata = chunk.metadata
        
        # Basic text quality (already computed)
        text_quality_score = metadata.text_quality_score
        
        # Readability assessment
        readability_score = self._calculate_readability(text)
        
        # Information density
        information_density = self._calculate_information_density(text)
        
        # Context preservation (based on metadata completeness)
        context_preservation_score = self._calculate_context_preservation(metadata)
        
        # Semantic coherence
        semantic_coherence = self._calculate_semantic_coherence(text)
        
        return ChunkQualityMetrics(
            chunk_id=metadata.chunk_id,
            text_quality_score=text_quality_score,
            readability_score=readability_score,
            information_density=information_density,
            context_preservation_score=context_preservation_score,
            semantic_coherence=semantic_coherence
        )
    
    def evaluate_document_processing(self, 
                                   chunks: List[ProcessedChunk], 
                                   structure: DocumentStructure,
                                   processing_time: float,
                                   document_id: str) -> DocumentProcessingMetrics:
        """
        Evaluate the overall document processing quality.
        
        Args:
            chunks: List of processed chunks
            structure: Document structure analysis
            processing_time: Time taken to process the document
            document_id: Unique document identifier
            
        Returns:
            DocumentProcessingMetrics with comprehensive evaluation
        """
        if not chunks:
            return DocumentProcessingMetrics(
                document_id=document_id,
                processing_time=processing_time,
                chunk_count=0,
                average_chunk_quality=0.0,
                content_coverage=0.0,
                structure_preservation=0.0,
                metadata_completeness=0.0,
                overall_score=0.0
            )
        
        # Evaluate individual chunks
        chunk_metrics = [self.evaluate_chunk_quality(chunk) for chunk in chunks]
        
        # Calculate aggregate metrics
        average_chunk_quality = statistics.mean(
            [m.text_quality_score for m in chunk_metrics]
        )
        
        # Content coverage (how well the chunks cover the document)
        content_coverage = self._calculate_content_coverage(chunks, structure)
        
        # Structure preservation (how well hierarchical structure is maintained)
        structure_preservation = self._calculate_structure_preservation(chunks)
        
        # Metadata completeness
        metadata_completeness = self._calculate_metadata_completeness(chunks)
        
        # Overall score (weighted combination)
        overall_score = (
            average_chunk_quality * 0.3 +
            content_coverage * 0.25 +
            structure_preservation * 0.25 +
            metadata_completeness * 0.2
        )
        
        return DocumentProcessingMetrics(
            document_id=document_id,
            processing_time=processing_time,
            chunk_count=len(chunks),
            average_chunk_quality=average_chunk_quality,
            content_coverage=content_coverage,
            structure_preservation=structure_preservation,
            metadata_completeness=metadata_completeness,
            overall_score=overall_score
        )
    
    def benchmark_configurations(self, 
                               pdf_files: List[str],
                               configurations: List[Dict[str, Any]]) -> List[BenchmarkResult]:
        """
        Benchmark different processor configurations.
        
        Args:
            pdf_files: List of PDF files to test
            configurations: List of processor configurations to benchmark
            
        Returns:
            List of BenchmarkResult for each configuration
        """
        logger.info(f"Benchmarking {len(configurations)} configurations on {len(pdf_files)} PDFs")
        
        results = []
        
        for config_idx, config in enumerate(configurations):
            logger.info(f"Testing configuration {config_idx + 1}/{len(configurations)}")
            
            # Initialize processor with current configuration
            processor = AdvancedPDFProcessor(**config)
            
            document_metrics = []
            processing_times = []
            success_count = 0
            
            for pdf_file in pdf_files:
                try:
                    start_time = time.time()
                    chunks, structure = processor.process_pdf(pdf_file)
                    processing_time = time.time() - start_time
                    
                    # Evaluate this document
                    doc_metrics = self.evaluate_document_processing(
                        chunks, structure, processing_time, os.path.basename(pdf_file)
                    )
                    
                    document_metrics.append(doc_metrics)
                    processing_times.append(processing_time)
                    success_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to process {pdf_file} with config {config_idx}: {e}")
                    continue
            
            # Calculate benchmark metrics
            if document_metrics:
                avg_processing_time = statistics.mean(processing_times)
                avg_quality_score = statistics.mean([dm.overall_score for dm in document_metrics])
                
                # Chunk count distribution
                chunk_counts = [dm.chunk_count for dm in document_metrics]
                chunk_count_dist = {
                    "min": min(chunk_counts),
                    "max": max(chunk_counts),
                    "mean": statistics.mean(chunk_counts),
                    "median": statistics.median(chunk_counts)
                }
                
                # Quality distribution
                quality_scores = [dm.overall_score for dm in document_metrics]
                quality_dist = {
                    "min": min(quality_scores),
                    "max": max(quality_scores),
                    "mean": statistics.mean(quality_scores),
                    "std": statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0
                }
                
                success_rate = success_count / len(pdf_files)
                
            else:
                avg_processing_time = 0.0
                avg_quality_score = 0.0
                chunk_count_dist = {"min": 0, "max": 0, "mean": 0, "median": 0}
                quality_dist = {"min": 0, "max": 0, "mean": 0, "std": 0}
                success_rate = 0.0
            
            benchmark_result = BenchmarkResult(
                processor_config=config,
                document_metrics=document_metrics,
                average_processing_time=avg_processing_time,
                average_quality_score=avg_quality_score,
                chunk_count_distribution=chunk_count_dist,
                quality_distribution=quality_dist,
                processing_success_rate=success_rate
            )
            
            results.append(benchmark_result)
        
        logger.info("Benchmarking completed")
        return results
    
    def compare_with_ground_truth(self, 
                                chunks: List[ProcessedChunk],
                                ground_truth_chunks: List[str],
                                ground_truth_metadata: Optional[List[Dict[str, Any]]] = None) -> Dict[str, float]:
        """
        Compare processed chunks with ground truth.
        
        Args:
            chunks: Processed chunks from pipeline
            ground_truth_chunks: Expected chunk texts
            ground_truth_metadata: Expected metadata (optional)
            
        Returns:
            Dictionary with comparison metrics
        """
        if not self.similarity_model:
            logger.warning("Similarity model not available for ground truth comparison")
            return {"error": "Similarity model not available"}
        
        processed_texts = [chunk.text for chunk in chunks]
        
        # Text similarity comparison
        similarity_scores = []
        
        for gt_text in ground_truth_chunks:
            gt_embedding = self.similarity_model.encode([gt_text])
            
            best_similarity = 0.0
            for proc_text in processed_texts:
                proc_embedding = self.similarity_model.encode([proc_text])
                similarity = cosine_similarity(gt_embedding, proc_embedding)[0][0]
                best_similarity = max(best_similarity, similarity)
            
            similarity_scores.append(best_similarity)
        
        # Calculate metrics
        avg_similarity = statistics.mean(similarity_scores)
        min_similarity = min(similarity_scores)
        coverage = sum(1 for score in similarity_scores if score > 0.8) / len(similarity_scores)
        
        # Chunk count comparison
        count_ratio = len(processed_texts) / len(ground_truth_chunks)
        
        metrics = {
            "average_similarity": avg_similarity,
            "minimum_similarity": min_similarity,
            "coverage_80_percent": coverage,
            "chunk_count_ratio": count_ratio,
            "ground_truth_chunks": len(ground_truth_chunks),
            "processed_chunks": len(processed_texts)
        }
        
        return metrics
    
    def generate_evaluation_report(self, 
                                 benchmark_results: List[BenchmarkResult],
                                 output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive evaluation report.
        
        Args:
            benchmark_results: Results from benchmark evaluation
            output_path: Optional path to save the report
            
        Returns:
            Dictionary containing the full evaluation report
        """
        report = {
            "evaluation_summary": {
                "configurations_tested": len(benchmark_results),
                "evaluation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "evaluator_version": "1.0.0"
            },
            "configuration_comparison": [],
            "best_configuration": None,
            "recommendations": []
        }
        
        # Analyze each configuration
        for i, result in enumerate(benchmark_results):
            config_analysis = {
                "configuration_id": i,
                "configuration": result.processor_config,
                "performance_metrics": {
                    "average_processing_time": result.average_processing_time,
                    "average_quality_score": result.average_quality_score,
                    "success_rate": result.processing_success_rate,
                    "documents_processed": len(result.document_metrics)
                },
                "quality_metrics": result.quality_distribution,
                "efficiency_metrics": {
                    "chunks_per_second": (
                        sum(dm.chunk_count for dm in result.document_metrics) / 
                        (result.average_processing_time * len(result.document_metrics))
                        if result.average_processing_time > 0 and result.document_metrics else 0
                    ),
                    "avg_chunks_per_document": result.chunk_count_distribution["mean"]
                }
            }
            
            report["configuration_comparison"].append(config_analysis)
        
        # Find best configuration
        if benchmark_results:
            best_config_idx = max(
                range(len(benchmark_results)),
                key=lambda i: benchmark_results[i].average_quality_score * 0.7 + 
                             benchmark_results[i].processing_success_rate * 0.3
            )
            report["best_configuration"] = {
                "configuration_id": best_config_idx,
                "configuration": benchmark_results[best_config_idx].processor_config,
                "quality_score": benchmark_results[best_config_idx].average_quality_score,
                "success_rate": benchmark_results[best_config_idx].processing_success_rate
            }
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(benchmark_results)
        
        # Save report if path provided
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Evaluation report saved to {output_path}")
        
        return report
    
    # Helper methods for metric calculations
    
    def _calculate_readability(self, text: str) -> float:
        """Calculate readability score."""
        if not TEXTSTAT_AVAILABLE:
            # Fallback: simple heuristic
            sentences = len([s for s in text.split('.') if s.strip()])
            words = len(text.split())
            if sentences == 0:
                return 0.5
            avg_sentence_length = words / sentences
            return max(0.0, min(1.0, 1.0 - (avg_sentence_length - 15) / 35))
        
        try:
            # Flesch Reading Ease (normalized to 0-1)
            flesch_score = textstat.flesch_reading_ease(text)
            return max(0.0, min(1.0, flesch_score / 100.0))
        except:
            return 0.5
    
    def _calculate_information_density(self, text: str) -> float:
        """Calculate information density score."""
        words = text.split()
        if not words:
            return 0.0
        
        # Unique word ratio
        unique_words = len(set(words))
        unique_ratio = unique_words / len(words)
        
        # Average word length
        avg_word_length = sum(len(word) for word in words) / len(words)
        length_score = min(1.0, avg_word_length / 6.0)  # Normalize by expected avg
        
        # Combine metrics
        return (unique_ratio * 0.6 + length_score * 0.4)
    
    def _calculate_context_preservation(self, metadata) -> float:
        """Calculate context preservation score based on metadata completeness."""
        score = 0.0
        
        # Check key metadata fields
        if metadata.section_hierarchy:
            score += 0.3
        if metadata.parent_section:
            score += 0.2
        if metadata.chunk_type:
            score += 0.2
        if metadata.predecessor_id or metadata.successor_id:
            score += 0.15
        if metadata.page_number:
            score += 0.1
        if metadata.heading_level:
            score += 0.05
        
        return min(1.0, score)
    
    def _calculate_semantic_coherence(self, text: str) -> float:
        """Calculate semantic coherence score."""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if len(sentences) < 2:
            return 1.0  # Single sentence is coherent by definition
        
        if not self.similarity_model:
            # Fallback: lexical overlap
            total_overlap = 0.0
            comparisons = 0
            
            for i in range(len(sentences) - 1):
                words1 = set(sentences[i].lower().split())
                words2 = set(sentences[i + 1].lower().split())
                if words1 and words2:
                    overlap = len(words1.intersection(words2)) / len(words1.union(words2))
                    total_overlap += overlap
                    comparisons += 1
            
            return total_overlap / comparisons if comparisons > 0 else 0.5
        
        # Semantic similarity between adjacent sentences
        try:
            embeddings = self.similarity_model.encode(sentences)
            similarities = []
            
            for i in range(len(embeddings) - 1):
                sim = cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
                similarities.append(sim)
            
            return statistics.mean(similarities) if similarities else 0.5
        except:
            return 0.5
    
    def _calculate_content_coverage(self, chunks: List[ProcessedChunk], structure: DocumentStructure) -> float:
        """Calculate how well chunks cover the original document content."""
        if not chunks:
            return 0.0
        
        # Basic coverage metrics
        total_text_length = sum(len(chunk.text) for chunk in chunks)
        page_coverage = len(set(chunk.metadata.page_number for chunk in chunks)) / structure.page_count
        
        # Section coverage (if hierarchical structure exists)
        section_coverage = 1.0
        if any(chunk.metadata.section_hierarchy for chunk in chunks):
            unique_sections = set()
            for chunk in chunks:
                if chunk.metadata.section_hierarchy:
                    unique_sections.update(chunk.metadata.section_hierarchy)
            # Estimate coverage based on section diversity
            section_coverage = min(1.0, len(unique_sections) / max(5, structure.page_count))
        
        # Combine metrics
        coverage_score = (page_coverage * 0.6 + section_coverage * 0.4)
        
        # Adjust for document length (longer docs should have more content)
        length_factor = min(1.0, total_text_length / (structure.page_count * 1000))
        
        return min(1.0, coverage_score * length_factor)
    
    def _calculate_structure_preservation(self, chunks: List[ProcessedChunk]) -> float:
        """Calculate how well the hierarchical structure is preserved."""
        if not chunks:
            return 0.0
        
        score = 0.0
        
        # Check for hierarchical information
        chunks_with_hierarchy = sum(
            1 for chunk in chunks 
            if chunk.metadata.section_hierarchy and len(chunk.metadata.section_hierarchy) > 0
        )
        hierarchy_ratio = chunks_with_hierarchy / len(chunks)
        score += hierarchy_ratio * 0.4
        
        # Check for proper sequencing
        chunks_with_sequence = sum(
            1 for chunk in chunks 
            if chunk.metadata.predecessor_id or chunk.metadata.successor_id
        )
        sequence_ratio = chunks_with_sequence / len(chunks)
        score += sequence_ratio * 0.3
        
        # Check for content type classification
        chunks_with_type = sum(
            1 for chunk in chunks 
            if chunk.metadata.chunk_type
        )
        type_ratio = chunks_with_type / len(chunks)
        score += type_ratio * 0.3
        
        return min(1.0, score)
    
    def _calculate_metadata_completeness(self, chunks: List[ProcessedChunk]) -> float:
        """Calculate metadata completeness score."""
        if not chunks:
            return 0.0
        
        total_score = 0.0
        
        for chunk in chunks:
            chunk_score = 0.0
            metadata = chunk.metadata
            
            # Essential fields (higher weight)
            if metadata.chunk_id:
                chunk_score += 0.15
            if metadata.doc_id:
                chunk_score += 0.15
            if metadata.page_number:
                chunk_score += 0.1
            if metadata.text_length > 0:
                chunk_score += 0.1
            
            # Structure fields
            if metadata.chunk_type:
                chunk_score += 0.1
            if metadata.section_hierarchy:
                chunk_score += 0.1
            if metadata.parent_section:
                chunk_score += 0.05
            
            # Quality fields
            if metadata.text_quality_score > 0:
                chunk_score += 0.1
            if metadata.language:
                chunk_score += 0.05
            
            # Relationship fields
            if metadata.predecessor_id or metadata.successor_id:
                chunk_score += 0.1
            
            total_score += chunk_score
        
        return total_score / len(chunks)
    
    def _generate_recommendations(self, benchmark_results: List[BenchmarkResult]) -> List[str]:
        """Generate recommendations based on benchmark results."""
        recommendations = []
        
        if not benchmark_results:
            return ["No benchmark results available for analysis"]
        
        # Analyze processing times
        processing_times = [r.average_processing_time for r in benchmark_results if r.average_processing_time > 0]
        if processing_times:
            fastest_time = min(processing_times)
            slowest_time = max(processing_times)
            
            if slowest_time > fastest_time * 2:
                recommendations.append(
                    "Consider optimizing configurations with slow processing times. "
                    f"Fastest: {fastest_time:.2f}s, Slowest: {slowest_time:.2f}s"
                )
        
        # Analyze quality scores
        quality_scores = [r.average_quality_score for r in benchmark_results]
        if quality_scores:
            max_quality = max(quality_scores)
            avg_quality = statistics.mean(quality_scores)
            
            if max_quality - avg_quality > 0.2:
                recommendations.append(
                    f"Quality varies significantly across configurations (best: {max_quality:.2f}, "
                    f"average: {avg_quality:.2f}). Focus on configurations with higher quality scores."
                )
        
        # Analyze success rates
        success_rates = [r.processing_success_rate for r in benchmark_results]
        if success_rates:
            min_success = min(success_rates)
            if min_success < 0.8:
                recommendations.append(
                    f"Some configurations have low success rates (minimum: {min_success:.1%}). "
                    "Consider improving error handling or adjusting parameters."
                )
        
        # Configuration-specific recommendations
        for i, result in enumerate(benchmark_results):
            config = result.processor_config
            
            if result.average_processing_time > 5.0:  # Slow processing
                if config.get("enable_nlp", False):
                    recommendations.append(
                        f"Configuration {i}: Consider disabling NLP processing to improve speed"
                    )
                if config.get("enable_ocr", False):
                    recommendations.append(
                        f"Configuration {i}: OCR processing may be slowing down pipeline"
                    )
            
            if result.average_quality_score < 0.6:  # Low quality
                recommendations.append(
                    f"Configuration {i}: Consider increasing quality_threshold or "
                    "enabling advanced features for better quality"
                )
        
        # General recommendations
        recommendations.append(
            "For thesis work: prioritize configurations with highest quality scores "
            "even if processing time is slightly higher"
        )
        
        recommendations.append(
            "Consider ablation studies on individual features (OCR, NLP, chunking strategies) "
            "to understand their impact on quality and performance"
        )
        
        return recommendations

# Example usage for thesis evaluation
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python pdf_evaluation.py <pdf_directory> [output_directory]")
        sys.exit(1)
    
    pdf_directory = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) > 2 else "evaluation_results"
    
    # Find PDF files
    pdf_files = list(Path(pdf_directory).glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {pdf_directory}")
        sys.exit(1)
    
    print(f"Found {len(pdf_files)} PDF files for evaluation")
    
    # Define configurations to benchmark
    configurations = [
        {
            "enable_ocr": False,
            "enable_nlp": False,
            "min_chunk_size": 100,
            "max_chunk_size": 500,
            "quality_threshold": 0.5
        },
        {
            "enable_ocr": True,
            "enable_nlp": False,
            "min_chunk_size": 100,
            "max_chunk_size": 500,
            "quality_threshold": 0.6
        },
        {
            "enable_ocr": True,
            "enable_nlp": True,
            "min_chunk_size": 150,
            "max_chunk_size": 800,
            "quality_threshold": 0.7
        },
        {
            "enable_ocr": True,
            "enable_nlp": True,
            "min_chunk_size": 200,
            "max_chunk_size": 1000,
            "quality_threshold": 0.8
        }
    ]
    
    # Initialize evaluator
    evaluator = PDFProcessingEvaluator(enable_advanced_metrics=True)
    
    # Run benchmark
    print("Starting benchmark evaluation...")
    benchmark_results = evaluator.benchmark_configurations(
        [str(pdf) for pdf in pdf_files],
        configurations
    )
    
    # Generate report
    os.makedirs(output_directory, exist_ok=True)
    report_path = os.path.join(output_directory, "pdf_evaluation_report.json")
    
    report = evaluator.generate_evaluation_report(benchmark_results, report_path)
    
    # Print summary
    print(f"\n📊 Evaluation Complete!")
    print(f"   Configurations tested: {len(configurations)}")
    print(f"   PDF files processed: {len(pdf_files)}")
    print(f"   Report saved to: {report_path}")
    
    if report["best_configuration"]:
        best_config = report["best_configuration"]
        print(f"\n🏆 Best Configuration:")
        print(f"   Quality Score: {best_config['quality_score']:.3f}")
        print(f"   Success Rate: {best_config['success_rate']:.1%}")
        print(f"   Config: {best_config['configuration']}")
    
    print(f"\n💡 Recommendations:")
    for rec in report["recommendations"][:3]:  # Show top 3
        print(f"   • {rec}")

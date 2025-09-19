#!/usr/bin/env python3
"""
Enhanced Trace Generator for RAG Evaluation
==========================================

This module generates enhanced test traces that capture detailed retrieval
metadata needed for comprehensive evaluation metrics including:
- Chunk IDs and scores for each retrieved document
- Ranking positions and confidence scores  
- Section/heading hierarchy information
- Namespace and source type breakdown
- Reranking scores and boosts applied
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Add the backend src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend" / "src"))

from rag.advanced_rag_pipeline import AdvancedRAGPipeline
from rag.feature_flags import set_feature_flag, get_feature_flags

class EnhancedTraceGenerator:
    """Generate enhanced traces with detailed retrieval metadata."""
    
    def __init__(self, config_name: str = "enhanced"):
        """
        Initialize the enhanced trace generator.
        
        Args:
            config_name: Name for this configuration
        """
        self.config_name = config_name
        self.pipeline = None
        
    def setup_pipeline(self, **kwargs):
        """Setup the RAG pipeline with specific configuration."""
        print(f"🔧 Setting up {self.config_name} pipeline...")
        
        # Configure feature flags based on config
        self._configure_features(**kwargs)
        
        # Initialize pipeline
        self.pipeline = AdvancedRAGPipeline()
        print(f"✅ Pipeline ready with features: {get_feature_flags()}")
    
    def _configure_features(self, **kwargs):
        """Configure feature flags for this test configuration."""
        # Default features for enhanced evaluation
        feature_config = {
            "enhanced_retrieval": True,
            "cross_encoder_reranking": True,
            "query_analysis": True,
            "response_verification": True,
            "web_search_enhancement": False,  # Default off
            "context_compression": True,
            "retrieval_guards": True,
            **kwargs  # Override with passed arguments
        }
        
        for feature, enabled in feature_config.items():
            set_feature_flag(feature, enabled)
    
    def generate_enhanced_traces(self, 
                               testset_file: str,
                               output_file: str,
                               max_queries: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate enhanced traces with detailed retrieval metadata.
        
        Args:
            testset_file: Path to test questions
            output_file: Path to save enhanced traces
            max_queries: Maximum number of queries to process (None for all)
            
        Returns:
            Summary statistics
        """
        print(f"🚀 Generating enhanced traces: {self.config_name}")
        print(f"📥 Input: {testset_file}")
        print(f"📤 Output: {output_file}")
        
        # Load test questions
        testset = self._load_testset(testset_file)
        if max_queries:
            testset = testset[:max_queries]
        
        print(f"📊 Processing {len(testset)} questions")
        
        # Generate enhanced traces
        enhanced_records = []
        successful = 0
        start_time = time.time()
        
        for i, item in enumerate(testset, 1):
            question = item["question"]
            ground_truth = item.get("ground_truth", "")
            
            print(f"🔍 [{i}/{len(testset)}] Processing: {question}")
            
            try:
                # Get detailed response with metadata
                result = self._get_enhanced_response(question)
                
                # Create enhanced record
                enhanced_record = self._create_enhanced_record(
                    question, ground_truth, result, i
                )
                
                enhanced_records.append(enhanced_record)
                successful += 1
                
                print(f"   ✅ Success (confidence: {result.get('confidence_score', 0):.3f})")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                # Add error record for completeness
                enhanced_records.append(self._create_error_record(question, ground_truth, str(e), i))
        
        # Save enhanced traces
        self._save_traces(enhanced_records, output_file)
        
        # Generate summary
        total_time = time.time() - start_time
        summary = {
            "config_name": self.config_name,
            "total_questions": len(testset),
            "successful_questions": successful,
            "failed_questions": len(testset) - successful,
            "success_rate": successful / len(testset),
            "total_time": total_time,
            "avg_time_per_query": total_time / len(testset),
            "output_file": output_file,
            "features_used": get_feature_flags(),
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"\n📊 Enhanced trace generation complete:")
        print(f"   Success rate: {successful}/{len(testset)} ({summary['success_rate']:.1%})")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Avg per query: {summary['avg_time_per_query']:.2f}s")
        
        return summary
    
    def _load_testset(self, testset_file: str) -> List[Dict[str, Any]]:
        """Load test questions from file."""
        testset = []
        
        with open(testset_file, 'r', encoding='utf-8') as f:
            for line in f:
                testset.append(json.loads(line))
        
        return testset
    
    def _get_enhanced_response(self, question: str) -> Dict[str, Any]:
        """Get enhanced response with detailed metadata."""
        if not self.pipeline:
            raise RuntimeError("Pipeline not initialized. Call setup_pipeline() first.")
        
        # Get full response with metadata
        response = self.pipeline.answer(question)
        
        # Extract detailed retrieval information
        enhanced_response = {
            "answer": response.answer,
            "confidence_score": response.confidence_score,
            "processing_time": response.processing_time,
            "features_used": response.features_used,
            
            # Detailed retrieval metadata
            "retrieval_results": self._extract_retrieval_details(response.retrieval_results),
            "retrieval_stats": getattr(response, 'retrieval_stats', {}),
            
            # Query analysis
            "query_analysis": {
                "intent": response.query_analysis.intent.value,
                "complexity": response.query_analysis.complexity.value,
                "entities": response.query_analysis.entities,
                "requires_reasoning": response.query_analysis.requires_reasoning,
                "confidence": response.query_analysis.confidence
            } if hasattr(response, 'query_analysis') else {},
            
            # Verification results
            "verification_result": {
                "is_verified": response.verification_result.is_verified,
                "confidence_score": response.verification_result.confidence_score,
                "fact_check_score": response.verification_result.fact_check_score,
                "hallucination_risk": response.verification_result.hallucination_risk
            } if hasattr(response, 'verification_result') else {},
        }
        
        return enhanced_response
    
    def _extract_retrieval_details(self, retrieval_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract detailed information from retrieval results."""
        detailed_results = []
        
        for i, result in enumerate(retrieval_results):
            detailed_result = {
                # Basic retrieval info
                "rank": i + 1,
                "chunk_id": result.get('id', f'unknown_{i}'),
                "score": result.get('score', 0.0),
                "original_score": result.get('original_score'),
                "text": result.get('text', ''),
                
                # Source information
                "namespace": result.get('namespace', 'unknown'),
                "source_file": result.get('metadata', {}).get('source_file', ''),
                "page_number": result.get('metadata', {}).get('page_number'),
                
                # Content metadata
                "text_length": len(result.get('text', '')),
                "token_count": result.get('metadata', {}).get('token_count'),
                "chunk_type": result.get('metadata', {}).get('chunk_type', ''),
                "heading_level": result.get('metadata', {}).get('heading_level'),
                "parent_section": result.get('metadata', {}).get('parent_section', ''),
                "section_hierarchy": result.get('metadata', {}).get('section_hierarchy', []),
                
                # Quality metrics
                "text_quality_score": result.get('metadata', {}).get('text_quality_score'),
                "boost_applied": result.get('boost_applied', 1.0),
                
                # Reranking information (if available)
                "rerank_score": result.get('rerank_score'),
                "was_reranked": result.get('was_reranked', False),
            }
            
            detailed_results.append(detailed_result)
        
        return detailed_results
    
    def _create_enhanced_record(self, 
                              question: str, 
                              ground_truth: str, 
                              result: Dict[str, Any], 
                              query_id: int) -> Dict[str, Any]:
        """Create an enhanced test record with detailed metadata."""
        # Extract contexts for RAGAS compatibility
        contexts = [r['text'] for r in result.get('retrieval_results', []) if r.get('text')]
        
        # Create enhanced record
        record = {
            # Basic RAGAS-compatible fields
            "question": question,
            "ground_truth": ground_truth,
            "answer": result.get('answer', ''),
            "contexts": contexts,
            
            # Enhanced metadata
            "query_id": f"q_{query_id}",
            "config": self.config_name,
            "confidence_score": result.get('confidence_score', 0.0),
            "processing_time": result.get('processing_time', 0.0),
            "features_used": result.get('features_used', {}),
            
            # Detailed retrieval information
            "retrieval_results": result.get('retrieval_results', []),
            "retrieval_stats": result.get('retrieval_stats', {}),
            "total_retrieved": len(result.get('retrieval_results', [])),
            
            # Namespace breakdown
            "namespace_breakdown": self._compute_namespace_breakdown(result.get('retrieval_results', [])),
            
            # Section analysis
            "section_analysis": self._analyze_sections(result.get('retrieval_results', [])),
            
            # Query analysis
            "query_analysis": result.get('query_analysis', {}),
            
            # Verification results
            "verification_result": result.get('verification_result', {}),
            
            # Timestamp
            "timestamp": datetime.now().isoformat()
        }
        
        return record
    
    def _create_error_record(self, 
                           question: str, 
                           ground_truth: str, 
                           error: str, 
                           query_id: int) -> Dict[str, Any]:
        """Create an error record for failed queries."""
        return {
            "question": question,
            "ground_truth": ground_truth,
            "answer": f"Error: {error}",
            "contexts": [],
            "query_id": f"q_{query_id}",
            "config": self.config_name,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
    
    def _compute_namespace_breakdown(self, retrieval_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute detailed namespace breakdown."""
        breakdown = {}
        
        for result in retrieval_results:
            namespace = result.get('namespace', 'unknown')
            if namespace not in breakdown:
                breakdown[namespace] = {
                    "count": 0,
                    "avg_score": 0.0,
                    "top_score": 0.0,
                    "avg_rank": 0.0
                }
            
            breakdown[namespace]["count"] += 1
            score = result.get('score', 0.0)
            breakdown[namespace]["top_score"] = max(breakdown[namespace]["top_score"], score)
        
        # Compute averages
        for namespace, data in breakdown.items():
            ns_results = [r for r in retrieval_results if r.get('namespace') == namespace]
            if ns_results:
                data["avg_score"] = sum(r.get('score', 0.0) for r in ns_results) / len(ns_results)
                data["avg_rank"] = sum(r.get('rank', 0) for r in ns_results) / len(ns_results)
        
        return breakdown
    
    def _analyze_sections(self, retrieval_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze section diversity and coverage."""
        unique_sections = set()
        unique_headings = set()
        section_levels = []
        
        for result in retrieval_results:
            # Extract section information
            section_hierarchy = result.get('section_hierarchy', [])
            parent_section = result.get('parent_section', '')
            heading_level = result.get('heading_level')
            
            if section_hierarchy:
                unique_sections.update(section_hierarchy)
            if parent_section:
                unique_sections.add(parent_section)
            if heading_level is not None:
                section_levels.append(heading_level)
        
        return {
            "unique_sections_count": len(unique_sections),
            "unique_sections": list(unique_sections),
            "section_diversity": len(unique_sections) / max(len(retrieval_results), 1),
            "avg_heading_level": sum(section_levels) / len(section_levels) if section_levels else None,
            "heading_levels": section_levels
        }
    
    def _save_traces(self, records: List[Dict[str, Any]], output_file: str):
        """Save enhanced traces to file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        
        print(f"💾 Saved {len(records)} enhanced traces to {output_file}")

def generate_baseline_enhanced_traces():
    """Generate enhanced baseline traces."""
    generator = EnhancedTraceGenerator("baseline_enhanced")
    generator.setup_pipeline(
        enhanced_retrieval=False,
        cross_encoder_reranking=False,
        web_search_enhancement=False,
        response_verification=False
    )
    
    return generator.generate_enhanced_traces(
        "benchmark/data/testset.jsonl",
        "benchmark/logs/baseline_enhanced.jsonl"
    )

def generate_full_enhanced_traces():
    """Generate enhanced traces with all features."""
    generator = EnhancedTraceGenerator("full_enhanced")
    generator.setup_pipeline(
        enhanced_retrieval=True,
        cross_encoder_reranking=True,
        web_search_enhancement=True,
        response_verification=True,
        context_compression=True,
        retrieval_guards=True
    )
    
    return generator.generate_enhanced_traces(
        "benchmark/data/testset.jsonl",
        "benchmark/logs/full_enhanced.jsonl"
    )

def generate_ablation_traces():
    """Generate traces for ablation study."""
    configurations = [
        {
            "name": "ablation_no_rerank",
            "config": {
                "enhanced_retrieval": True,
                "cross_encoder_reranking": False,
                "web_search_enhancement": False,
                "response_verification": True
            }
        },
        {
            "name": "ablation_no_verification", 
            "config": {
                "enhanced_retrieval": True,
                "cross_encoder_reranking": True,
                "web_search_enhancement": False,
                "response_verification": False
            }
        },
        {
            "name": "ablation_no_enhancement",
            "config": {
                "enhanced_retrieval": False,
                "cross_encoder_reranking": True,
                "web_search_enhancement": False,
                "response_verification": True
            }
        },
        {
            "name": "ablation_only_web",
            "config": {
                "enhanced_retrieval": False,
                "cross_encoder_reranking": False,
                "web_search_enhancement": True,
                "response_verification": False
            }
        }
    ]
    
    summaries = {}
    
    for config in configurations:
        print(f"\n🧪 Running ablation study: {config['name']}")
        
        generator = EnhancedTraceGenerator(config['name'])
        generator.setup_pipeline(**config['config'])
        
        summary = generator.generate_enhanced_traces(
            "benchmark/data/testset.jsonl",
            f"benchmark/logs/{config['name']}.jsonl"
        )
        
        summaries[config['name']] = summary
    
    # Save ablation summary
    with open("benchmark/logs/ablation_summary.json", 'w') as f:
        json.dump(summaries, f, indent=2, ensure_ascii=False)
    
    print(f"\n🎯 Ablation study complete. Summary saved to benchmark/logs/ablation_summary.json")
    return summaries

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate enhanced RAG evaluation traces")
    parser.add_argument("--mode", choices=["baseline", "full", "ablation"], 
                       default="full", help="Generation mode")
    parser.add_argument("--config-name", help="Custom configuration name")
    parser.add_argument("--testset", default="benchmark/data/testset.jsonl",
                       help="Path to test questions")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--max-queries", type=int, help="Maximum queries to process")
    
    args = parser.parse_args()
    
    if args.mode == "baseline":
        summary = generate_baseline_enhanced_traces()
    elif args.mode == "full":
        summary = generate_full_enhanced_traces()
    elif args.mode == "ablation":
        summary = generate_ablation_traces()
    else:
        # Custom configuration
        if not args.config_name or not args.output:
            print("❌ Custom mode requires --config-name and --output")
            sys.exit(1)
        
        generator = EnhancedTraceGenerator(args.config_name)
        generator.setup_pipeline()  # Use defaults
        
        summary = generator.generate_enhanced_traces(
            args.testset,
            args.output,
            args.max_queries
        )
    
    print("\n✅ Enhanced trace generation completed successfully!")

#!/usr/bin/env python3
"""
RAGv2 Query Interface with Observability
========================================

This module provides a comprehensive interface for querying the RAGv2 system
with detailed observability and analysis capabilities.

Features:
- Interactive query interface
- Detailed response analysis
- Performance metrics
- Source attribution
- Confidence scoring
- Query history and analytics
"""

import os
import sys
import time
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

from .rag_pipeline_v2 import RAGv2Pipeline
from .config import get_feature_flags, get_ragv2_namespaces
from .utils.embeddings_v2 import EnhancedEmbeddings

@dataclass
class QueryResult:
    """Structured query result with full observability data."""
    query_id: str
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    response_time: float
    feature_flags: Dict[str, bool]
    retrieval_stats: Dict[str, Any]
    generation_stats: Dict[str, Any]
    timestamp: str
    namespace_breakdown: Dict[str, int]
    source_types: List[str]
    token_count: int
    verification_score: Optional[float] = None
    is_verified: Optional[bool] = None
    refusal_reason: Optional[str] = None

class RAGv2QueryInterface:
    """
    Comprehensive query interface for RAGv2 with observability.
    
    Features:
    - Interactive querying
    - Response analysis
    - Performance tracking
    - Query history
    - Export capabilities
    """
    
    def __init__(self, enable_logging: bool = True):
        """
        Initialize the query interface.
        
        Args:
            enable_logging: Whether to enable detailed logging
        """
        load_dotenv()
        
        # Initialize logging
        if enable_logging:
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('ragv2_queries.log'),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
        else:
            self.logger = None
        
        # Initialize RAGv2 pipeline
        self.pipeline = RAGv2Pipeline()
        
        # Query history
        self.query_history: List[QueryResult] = []
        
        # Performance tracking
        self.performance_stats = {
            "total_queries": 0,
            "average_response_time": 0,
            "total_response_time": 0,
            "feature_usage": {},
            "namespace_usage": {},
            "confidence_distribution": []
        }
        
        print("🚀 RAGv2 Query Interface Initialized")
        print(f"📊 Active features: {sum(get_feature_flags().values())}/{len(get_feature_flags())}")
    
    def query(self, question: str, detailed: bool = True) -> QueryResult:
        """
        Execute a query with full observability.
        
        Args:
            question: The question to ask
            detailed: Whether to return detailed analysis
            
        Returns:
            QueryResult with full observability data
        """
        start_time = time.time()
        query_id = f"query_{int(start_time * 1000)}"
        
        if self.logger:
            self.logger.info(f"Starting query: {query_id} - {question}")
        
        try:
            # Execute query through pipeline
            pipeline_result = self.pipeline.answer(question)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract sources and metadata from retrieval results
            # The pipeline returns retrieval_results, not sources
            retrieval_results = pipeline_result.get("retrieval_results", [])
            sources = self._convert_retrieval_to_sources(retrieval_results)
            namespace_breakdown = self._analyze_namespace_breakdown(sources)
            source_types = self._extract_source_types(sources)
            
            # Calculate confidence and token count
            confidence = self._calculate_confidence(pipeline_result)
            token_count = self._estimate_token_count(pipeline_result.get("answer", ""))
            
            # Create structured result
            result = QueryResult(
                query_id=query_id,
                question=question,
                answer=pipeline_result.get("answer", ""),
                sources=sources,
                confidence=confidence,
                response_time=response_time,
                feature_flags=get_feature_flags(),
                retrieval_stats=pipeline_result.get("retrieval_stats", {}),
                generation_stats=pipeline_result.get("generation_stats", {}),
                timestamp=datetime.now().isoformat(),
                namespace_breakdown=namespace_breakdown,
                source_types=source_types,
                token_count=token_count,
                verification_score=pipeline_result.get("verification_score"),
                is_verified=pipeline_result.get("is_verified"),
                refusal_reason=pipeline_result.get("refusal_reason")
            )
            
            # Update performance stats
            self._update_performance_stats(result)
            
            # Add to history
            self.query_history.append(result)
            
            if self.logger:
                self.logger.info(f"Query completed: {query_id} - {response_time:.3f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Query failed: {str(e)}"
            if self.logger:
                self.logger.error(f"Query {query_id} failed: {e}")
            
            # Return error result
            return QueryResult(
                query_id=query_id,
                question=question,
                answer=f"Error: {error_msg}",
                sources=[],
                confidence=0.0,
                response_time=time.time() - start_time,
                feature_flags=get_feature_flags(),
                retrieval_stats={},
                generation_stats={},
                timestamp=datetime.now().isoformat(),
                namespace_breakdown={},
                source_types=[],
                token_count=0
            )
    
    def _analyze_namespace_breakdown(self, sources: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze sources by namespace."""
        breakdown = {}
        for source in sources:
            namespace = source.get("namespace", "unknown")
            breakdown[namespace] = breakdown.get(namespace, 0) + 1
        return breakdown
    
    def _extract_source_types(self, sources: List[Dict[str, Any]]) -> List[str]:
        """Extract unique source types from sources."""
        types = set()
        for source in sources:
            source_type = source.get("metadata", {}).get("source_type", "unknown")
            types.add(source_type)
        return list(types)
    
    def _convert_retrieval_to_sources(self, retrieval_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert retrieval results to source format for analysis."""
        sources = []
        for result in retrieval_results:
            source = {
                "id": result.get("id", ""),
                "score": result.get("score", 0.0),
                "namespace": result.get("namespace", "unknown"),
                "metadata": result.get("metadata", {}),
                "text": result.get("text", "")
            }
            sources.append(source)
        return sources
    
    def _calculate_confidence(self, pipeline_result: Dict[str, Any]) -> float:
        """Calculate confidence score based on various factors."""
        # Base confidence from verification score
        verification_score = pipeline_result.get("verification_score", 0.0)
        
        # Adjust based on number of sources (use retrieval_results)
        retrieval_results = pipeline_result.get("retrieval_results", [])
        source_confidence = min(len(retrieval_results) / 5.0, 1.0)  # Cap at 5 sources
        
        # Adjust based on retrieval scores
        retrieval_scores = [r.get("score", 0.0) for r in retrieval_results]
        avg_retrieval_score = sum(retrieval_scores) / len(retrieval_scores) if retrieval_scores else 0.0
        
        # Weighted combination
        confidence = (verification_score * 0.4 + source_confidence * 0.3 + avg_retrieval_score * 0.3)
        return min(confidence, 1.0)
    
    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count for text."""
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4
    
    def _update_performance_stats(self, result: QueryResult):
        """Update performance statistics."""
        self.performance_stats["total_queries"] += 1
        self.performance_stats["total_response_time"] += result.response_time
        self.performance_stats["average_response_time"] = (
            self.performance_stats["total_response_time"] / self.performance_stats["total_queries"]
        )
        
        # Update feature usage
        for feature, enabled in result.feature_flags.items():
            if enabled:
                self.performance_stats["feature_usage"][feature] = (
                    self.performance_stats["feature_usage"].get(feature, 0) + 1
                )
        
        # Update namespace usage
        for namespace, count in result.namespace_breakdown.items():
            self.performance_stats["namespace_usage"][namespace] = (
                self.performance_stats["namespace_usage"].get(namespace, 0) + count
            )
        
        # Update confidence distribution
        self.performance_stats["confidence_distribution"].append(result.confidence)
    
    def analyze_response(self, result: QueryResult) -> Dict[str, Any]:
        """
        Perform detailed analysis of a query response.
        
        Args:
            result: QueryResult to analyze
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "query_id": result.query_id,
            "response_quality": {
                "confidence": result.confidence,
                "verification_score": result.verification_score,
                "is_verified": result.is_verified,
                "refusal_reason": result.refusal_reason
            },
            "performance": {
                "response_time": result.response_time,
                "token_count": result.token_count,
                "sources_count": len(result.sources)
            },
            "source_analysis": {
                "namespace_breakdown": result.namespace_breakdown,
                "source_types": result.source_types,
                "top_sources": sorted(result.sources, key=lambda x: x.get("score", 0), reverse=True)[:3]
            },
            "feature_usage": result.feature_flags,
            "retrieval_metrics": result.retrieval_stats,
            "generation_metrics": result.generation_stats
        }
        
        return analysis
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        if not self.query_history:
            return {"error": "No queries executed yet"}
        
        # Calculate confidence statistics
        confidences = self.performance_stats["confidence_distribution"]
        confidence_stats = {
            "mean": sum(confidences) / len(confidences),
            "min": min(confidences),
            "max": max(confidences),
            "distribution": {
                "high": len([c for c in confidences if c >= 0.8]),
                "medium": len([c for c in confidences if 0.5 <= c < 0.8]),
                "low": len([c for c in confidences if c < 0.5])
            }
        }
        
        return {
            "summary": {
                "total_queries": self.performance_stats["total_queries"],
                "average_response_time": self.performance_stats["average_response_time"],
                "total_response_time": self.performance_stats["total_response_time"]
            },
            "confidence_analysis": confidence_stats,
            "feature_usage": self.performance_stats["feature_usage"],
            "namespace_usage": self.performance_stats["namespace_usage"],
            "recent_queries": [
                {
                    "query_id": q.query_id,
                    "question": q.question[:100] + "..." if len(q.question) > 100 else q.question,
                    "confidence": q.confidence,
                    "response_time": q.response_time,
                    "timestamp": q.timestamp
                }
                for q in self.query_history[-10:]  # Last 10 queries
            ]
        }
    
    def export_query_history(self, filename: str = None) -> str:
        """Export query history to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ragv2_query_history_{timestamp}.json"
        
        # Convert QueryResult objects to dictionaries
        history_data = {
            "export_timestamp": datetime.now().isoformat(),
            "total_queries": len(self.query_history),
            "performance_stats": self.performance_stats,
            "queries": [asdict(result) for result in self.query_history]
        }
        
        with open(filename, 'w') as f:
            json.dump(history_data, f, indent=2)
        
        return filename
    
    def interactive_mode(self):
        """Run interactive query mode."""
        print("\n🎯 RAGv2 Interactive Query Mode")
        print("=" * 50)
        print("Commands:")
        print("  /help     - Show this help")
        print("  /stats    - Show performance statistics")
        print("  /export   - Export query history")
        print("  /quit     - Exit interactive mode")
        print("  /analyze  - Analyze last response")
        print("=" * 50)
        
        last_result = None
        
        while True:
            try:
                user_input = input("\n🤔 Enter your question (or command): ").strip()
                
                if not user_input:
                    continue
                
                if user_input.startswith("/"):
                    command = user_input.lower()
                    
                    if command == "/quit":
                        print("👋 Goodbye!")
                        break
                    elif command == "/help":
                        print("Commands: /help, /stats, /export, /quit, /analyze")
                    elif command == "/stats":
                        report = self.get_performance_report()
                        print("\n📊 Performance Report:")
                        print(json.dumps(report, indent=2))
                    elif command == "/export":
                        filename = self.export_query_history()
                        print(f"📁 Query history exported to: {filename}")
                    elif command == "/analyze":
                        if last_result:
                            analysis = self.analyze_response(last_result)
                            print("\n🔍 Response Analysis:")
                            print(json.dumps(analysis, indent=2))
                        else:
                            print("❌ No previous query to analyze")
                    else:
                        print(f"❌ Unknown command: {command}")
                    
                    continue
                
                # Execute query
                print(f"\n🔍 Processing: {user_input}")
                result = self.query(user_input)
                last_result = result
                
                # Display result
                print(f"\n💡 Answer:")
                print(f"   {result.answer}")
                print(f"\n📊 Metrics:")
                print(f"   Confidence: {result.confidence:.2%}")
                print(f"   Response time: {result.response_time:.3f}s")
                print(f"   Sources: {len(result.sources)}")
                print(f"   Namespaces: {result.namespace_breakdown}")
                
                if result.sources:
                    print(f"\n📚 Top Sources:")
                    for i, source in enumerate(result.sources[:3], 1):
                        score = source.get("score", 0)
                        namespace = source.get("namespace", "unknown")
                        text = source.get("metadata", {}).get("text", "")[:100]
                        print(f"   {i}. [{namespace}] (score: {score:.3f}) {text}...")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function for running the query interface."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAGv2 Query Interface")
    parser.add_argument("--question", help="Single question to ask")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--stats", action="store_true", help="Show performance statistics")
    parser.add_argument("--export", help="Export query history to file")
    parser.add_argument("--no-logging", action="store_true", help="Disable logging")
    
    args = parser.parse_args()
    
    # Initialize interface
    interface = RAGv2QueryInterface(enable_logging=not args.no_logging)
    
    if args.question:
        # Single query mode
        result = interface.query(args.question)
        analysis = interface.analyze_response(result)
        
        print(f"\n💡 Answer: {result.answer}")
        print(f"📊 Analysis: {json.dumps(analysis, indent=2)}")
        
    elif args.interactive:
        # Interactive mode
        interface.interactive_mode()
        
    elif args.stats:
        # Show statistics
        report = interface.get_performance_report()
        print(json.dumps(report, indent=2))
        
    elif args.export:
        # Export history
        filename = interface.export_query_history(args.export)
        print(f"Query history exported to: {filename}")
        
    else:
        # Default to interactive mode
        interface.interactive_mode()

if __name__ == "__main__":
    main() 
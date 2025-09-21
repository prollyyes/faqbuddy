"""
RAG Evaluation Suite
===================

This module contains evaluation tools and scripts for comprehensive
RAG pipeline benchmarking.

Key Components:
- enhanced_metrics: Advanced retrieval and generation metrics
- enhanced_trace_generator: Enhanced test trace generation
- comprehensive_evaluator: Unified evaluation framework
- ground_truth_creator: Ground truth management tools
- import_utils: Common import utilities

Main Scripts:
- run_ragas.py: RAGAS evaluation runner
- run_all_rag_tests.py: Master test runner
- run_comprehensive_evaluation.py: Complete evaluation pipeline
- run_sequential_tests.py: Sequential test runner for VRAM management

Trace Generators:
- generate_baseline_rag_traces.py: Baseline RAG configuration
- generate_rag_reranking_traces.py: RAG with re-ranking
- generate_rag_web_traces.py: RAG with web enhancement
- generate_full_advanced_traces.py: Full advanced RAG
- generate_topk_variations_traces.py: Top-k parameter variations
"""

# Import key classes and functions for easy access
try:
    from .enhanced_metrics import AdvancedEvaluator, RetrievalMetrics
    from .enhanced_trace_generator import EnhancedTraceGenerator
    from .comprehensive_evaluator import ComprehensiveEvaluator, ComprehensiveResults
    from .ground_truth_creator import GroundTruthCreator, GroundTruthEntry
    from .import_utils import (
        setup_backend_imports, 
        setup_benchmark_imports, 
        get_benchmark_paths,
        load_env_file,
        safe_import_backend_module
    )
    
    __all__ = [
        'AdvancedEvaluator',
        'RetrievalMetrics', 
        'EnhancedTraceGenerator',
        'ComprehensiveEvaluator',
        'ComprehensiveResults',
        'GroundTruthCreator',
        'GroundTruthEntry',
        'setup_backend_imports',
        'setup_benchmark_imports',
        'get_benchmark_paths',
        'load_env_file',
        'safe_import_backend_module'
    ]
    
except ImportError as e:
    # Some imports might fail if dependencies aren't installed
    print(f"⚠️ Warning: Some benchmark modules could not be imported: {e}")
    __all__ = []

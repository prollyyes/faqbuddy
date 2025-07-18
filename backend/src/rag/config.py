"""
RAGv2 Configuration and Feature Flags
====================================

This module contains all configuration settings and feature flags for the RAGv2 upgrade.
Each objective is controlled by its own feature flag for independent deployment.
"""

import os
from typing import Dict, Any

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Task 1: Schema-aware extraction & chunking
SCHEMA_AWARE_CHUNKING = os.getenv("SCHEMA_AWARE_CHUNKING", "true").lower() == "true"

# Task 2: Embedding upgrade
INSTRUCTOR_XL_EMBEDDINGS = os.getenv("INSTRUCTOR_XL_EMBEDDINGS", "false").lower() == "true"

# Task 3: Retrieval pipeline improvements
RERANKER_ENABLED = os.getenv("RERANKER_ENABLED", "false").lower() == "true"
BM25_FALLBACK = os.getenv("BM25_FALLBACK", "true").lower() == "true"  # Keep BM25 as fallback

# Task 4: Graph-RAG
GRAPH_RAG = os.getenv("GRAPH_RAG", "false").lower() == "true"

# Task 5: Generation guard-rails
HALLUCINATION_GUARDS = os.getenv("HALLUCINATION_GUARDS", "false").lower() == "true"

# Task 6: CDC-based incremental embeddings
CDC_ENABLED = os.getenv("CDC_ENABLED", "false").lower() == "true"

# Task 7: PDF ingestion
PDF_BOOST = os.getenv("PDF_BOOST", "false").lower() == "true"

# Task 8: Observability
OBSERVABILITY_ENABLED = os.getenv("OBSERVABILITY_ENABLED", "false").lower() == "true"

# ============================================================================
# MODEL CONFIGURATIONS
# ============================================================================

# Current embedding model (Task 2)
CURRENT_EMBEDDING_MODEL = "all-mpnet-base-v2"
NEW_EMBEDDING_MODEL = "hkunlp/instructor-xl"

# Cross-encoder model (Task 3)
CROSS_ENCODER_MODEL = "BAAI/bge-reranker-large"

# ============================================================================
# RETRIEVAL PARAMETERS
# ============================================================================

# Task 3: Retrieval pipeline
DENSE_TOP_K = 50  # Increased from 20
RERANKER_THRESHOLD = 0.2  # Minimum score to keep chunk
MAX_CONTEXT_TOKENS = 4000  # Maximum context tokens

# Task 1: Schema-aware chunking
MAX_CHUNK_TOKENS = 400  # Maximum tokens per chunk
NODE_TYPE_PREFIX = "node_type"

# ============================================================================
# NAMESPACE CONFIGURATION
# ============================================================================

# Existing namespaces (keep untouched)
EXISTING_DOCS_NAMESPACE = "documents"
EXISTING_DB_NAMESPACE = "db"

# New RAGv2 namespaces (safe to upsert)
RAGV2_DOCS_NAMESPACE = "documents_v2"
RAGV2_DB_NAMESPACE = "db_v2"
RAGV2_PDF_NAMESPACE = "pdf_v2"

# Index configuration
INDEX_NAME = "exams-index-enhanced"  # Same index, different namespaces

# ============================================================================
# GRAPH-RAG CONFIGURATION (Task 4)
# ============================================================================

GRAPH_DB_TYPE = os.getenv("GRAPH_DB_TYPE", "neo4j")  # "neo4j" or "age"
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# ============================================================================
# CDC CONFIGURATION (Task 6)
# ============================================================================

CDC_QUEUE_TYPE = os.getenv("CDC_QUEUE_TYPE", "memory")  # "memory", "redis", "kafka"
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# ============================================================================
# OBSERVABILITY CONFIGURATION (Task 8)
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
METRICS_ENABLED = os.getenv("METRICS_ENABLED", "true").lower() == "true"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_feature_flags() -> Dict[str, bool]:
    """Get all feature flags as a dictionary."""
    return {
        "schema_aware_chunking": SCHEMA_AWARE_CHUNKING,
        "instructor_xl_embeddings": INSTRUCTOR_XL_EMBEDDINGS,
        "reranker_enabled": RERANKER_ENABLED,
        "bm25_fallback": BM25_FALLBACK,
        "graph_rag": GRAPH_RAG,
        "hallucination_guards": HALLUCINATION_GUARDS,
        "cdc_enabled": CDC_ENABLED,
        "pdf_boost": PDF_BOOST,
        "observability_enabled": OBSERVABILITY_ENABLED,
    }

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a specific feature is enabled."""
    flags = get_feature_flags()
    return flags.get(feature_name, False)

def get_embedding_model() -> str:
    """Get the current embedding model based on feature flags."""
    return NEW_EMBEDDING_MODEL if INSTRUCTOR_XL_EMBEDDINGS else CURRENT_EMBEDDING_MODEL

def get_embedding_instruction() -> str:
    """Get the instruction prefix for instructor-xl embeddings."""
    if INSTRUCTOR_XL_EMBEDDINGS:
        return "Represent an education QA passage for retrieval: "
    return ""

def get_ragv2_namespaces() -> Dict[str, str]:
    """Get RAGv2 namespace configuration."""
    return {
        "docs": RAGV2_DOCS_NAMESPACE,
        "db": RAGV2_DB_NAMESPACE,
        "pdf": RAGV2_PDF_NAMESPACE
    }

def get_existing_namespaces() -> Dict[str, str]:
    """Get existing namespace configuration (for fallback)."""
    return {
        "docs": EXISTING_DOCS_NAMESPACE,
        "db": EXISTING_DB_NAMESPACE
    }

# ============================================================================
# VALIDATION
# ============================================================================

def validate_configuration() -> None:
    """Validate the configuration and raise errors for invalid combinations."""
    errors = []
    
    # Graph-RAG requires specific database
    if GRAPH_RAG and GRAPH_DB_TYPE not in ["neo4j", "age"]:
        errors.append(f"GRAPH_DB_TYPE must be 'neo4j' or 'age', got '{GRAPH_DB_TYPE}'")
    
    # CDC requires queue configuration
    if CDC_ENABLED and CDC_QUEUE_TYPE not in ["memory", "redis", "kafka"]:
        errors.append(f"CDC_QUEUE_TYPE must be 'memory', 'redis', or 'kafka', got '{CDC_QUEUE_TYPE}'")
    
    # Validate namespace uniqueness
    all_namespaces = [
        EXISTING_DOCS_NAMESPACE, EXISTING_DB_NAMESPACE,
        RAGV2_DOCS_NAMESPACE, RAGV2_DB_NAMESPACE, RAGV2_PDF_NAMESPACE
    ]
    if len(all_namespaces) != len(set(all_namespaces)):
        errors.append("All namespaces must be unique")
    
    if errors:
        raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")

# Validate on import
validate_configuration() 
"""
Centralized Configuration for Enhanced RAG System
================================================

This configuration file centralizes all RAG system settings for easy tuning and maintenance.
Inspired by smallRag's configuration approach for optimal performance and accuracy.
"""

import os
from typing import Dict, Any, List

# ============================================================================
# CORE RAG CONFIGURATION
# ============================================================================

# Performance Settings
PERFORMANCE_CONFIG = {
    "top_k": 4,  # Number of documents to retrieve (reduced for speed)
    "max_chunks": 4,  # Maximum chunks in context
    "max_tokens": 1000,  # Maximum tokens in context
    "max_chars_per_chunk": 400,  # Maximum characters per chunk
    "min_relevance_score": 0.3,  # Minimum relevance threshold
    "use_cross_encoder": True,  # Enable cross-encoder reranking
    "cache_size": 1000,  # LRU cache size for embeddings
    "batch_size": 32,  # Batch size for embedding generation
}

# Retrieval Settings
RETRIEVAL_CONFIG = {
    "alpha": 0.7,  # Weight for dense vs sparse fusion (increased for better semantic understanding)
    "embedding_model": "all-mpnet-base-v2",  # High-quality embedding model
    "cross_encoder_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",  # Cross-encoder for reranking
    "chunk_window": 200,  # Token window for chunking
    "chunk_overlap": 50,  # Token overlap between chunks
}

# LLM Settings
LLM_CONFIG = {
    "n_ctx": 2048,  # Context window (reduced for speed)
    "n_threads": 8,  # Optimized for M2 Pro
    "n_gpu_layers": -1,  # Use all available GPU layers
    "verbose": False,  # Reduce logging for performance
    "n_batch": 128,  # Optimized batch size
    "use_mlock": True,  # Keep model in memory
    "use_mmap": True,  # Use memory mapping
    "f16_kv": True,  # Use half precision for key/value cache
    "logits_all": False,  # Don't compute logits for all tokens
    "metal": True,  # Use Metal on Apple Silicon
    "low_vram": False,  # We have sufficient RAM
    "seed": -1,  # Random seed for consistency
    "rope_scaling_type": 0,  # Disable RoPE scaling for speed
    "repeat_penalty": 1.1,  # Light repetition penalty
    "last_n_tokens_size": 64,  # Smaller context for penalty calculation
    "temperature": 0.1,  # Lower temperature for more consistent answers
    "top_p": 0.9,  # Nucleus sampling for better quality
    "max_tokens": 1024,  # Maximum tokens for generation
}

# ============================================================================
# NAMESPACE CONFIGURATION
# ============================================================================

NAMESPACE_CONFIG = {
    'documents': {
        'boost': 1.1,
        'keywords': [
            'regolamento', 'norme', 'procedure', 'requisiti', 'criteri', 'modalità',
            'scadenze', 'termini', 'documentazione', 'certificati', 'attestati',
            'esami', 'lauree', 'tesi', 'stage', 'tirocinio', 'erasmus', 'borsa',
            'contributo', 'tassa', 'pagamento', 'iscrizione', 'immatricolazione',
            'graduatoria', 'concorso', 'ammissione', 'trasferimento', 'rinuncia'
        ]
    },
    'db': {
        'boost': 1.0,
        'keywords': [
            'quali', 'elenca', 'mostra', 'lista', 'tutti', 'corsi', 'professori',
            'studenti', 'anno', 'matricola', 'insegnante', 'corso', 'email',
            'contatti', 'dipartimento', 'facoltà', 'review', 'recensioni',
            'materiale', 'edizione', 'orario', 'aula', 'sede', 'dove',
            'quando', 'come', 'chi', 'cosa', 'dove', 'quanto'
        ]
    }
}

# ============================================================================
# PROMPT CONFIGURATION
# ============================================================================

PROMPT_CONFIG = {
    "system_prompt": """Sei FAQBuddy, un assistente intelligente per un portale universitario italiano. 

COMPITI:
- Rispondi a domande su università, corsi, professori, materiali didattici
- Fornisci informazioni accurate basate SOLO sui documenti forniti
- Mantieni un tono professionale ma amichevole
- Usa sempre il formato Markdown per una migliore leggibilità
- Cita le fonti quando appropriato

REGOLE IMPORTANTI:
- NON inventare informazioni
- Se non hai informazioni sufficienti, dillo chiaramente
- Rispondi SEMPRE in italiano
- Sii conciso ma completo
- Usa elenchi puntati per informazioni strutturate

FORMATO RISPOSTA:
- Usa titoli (# ##) per organizzare la risposta
- Usa elenchi puntati (-) per liste
- Usa grassetto (**testo**) per enfasi
- Usa corsivo (*testo*) per termini tecnici
- Cita le fonti tra parentesi quando appropriato""",
    
    "fast_prompt": """Sei FAQBuddy, un assistente per un portale universitario italiano. 
Rispondi in italiano basandoti SOLO sui documenti forniti. 
Usa formato Markdown. Non inventare informazioni.""",
    
    "query_enhancement_keywords": {
        "university": [
            'università', 'corso', 'professore', 'esame', 'materiale', 
            'segreteria', 'iscrizione', 'laurea', 'facoltà', 'dipartimento'
        ],
        "informational": ['quali', 'elenca', 'lista', 'mostra'],
        "procedural": ['come', 'procedura', 'modalità'],
        "temporal": ['quando', 'data', 'scadenza']
    }
}

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

DATABASE_CONFIG = {
    "pinecone": {
        "index_name": "exams-index-enhanced",
        "docs_namespace": "documents",
        "db_namespace": "db",
        "dimension": 768,  # all-mpnet-base-v2 dimension
        "metric": "cosine"
    },
    "local": {
        "data_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data')),
        "models_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), '../../models'))
    }
}

# ============================================================================
# ERROR HANDLING CONFIGURATION
# ============================================================================

ERROR_CONFIG = {
    "max_retries": 3,
    "retry_delay": 1.0,
    "timeout": 30.0,
    "fallback_responses": {
        "llm_unavailable": "⚠️ Errore: Modello LLM non disponibile. Controlla che il file del modello sia presente nella cartella models/.",
        "retrieval_failed": "Mi dispiace, non sono riuscito a trovare informazioni pertinenti per la tua domanda.",
        "generation_failed": "Mi dispiace, si è verificato un errore durante la generazione della risposta.",
        "general_error": "Mi dispiace, si è verificato un errore durante l'elaborazione della tua domanda."
    }
}

# ============================================================================
# MONITORING CONFIGURATION
# ============================================================================

MONITORING_CONFIG = {
    "enable_performance_tracking": True,
    "enable_cache_stats": True,
    "enable_retrieval_stats": True,
    "enable_llm_stats": True,
    "log_level": "INFO",
    "performance_thresholds": {
        "retrieval_time_warning": 5.0,  # seconds
        "generation_time_warning": 10.0,  # seconds
        "total_time_warning": 15.0  # seconds
    }
}

# ============================================================================
# OPTIMIZATION PROFILES
# ============================================================================

# Speed-optimized profile
SPEED_PROFILE = {
    "top_k": 3,
    "max_chunks": 3,
    "max_tokens": 800,
    "use_cross_encoder": False,
    "alpha": 0.8,  # More weight on dense search (faster)
    "llm_temperature": 0.05,
    "llm_max_tokens": 512
}

# Quality-optimized profile
QUALITY_PROFILE = {
    "top_k": 6,
    "max_chunks": 5,
    "max_tokens": 1200,
    "use_cross_encoder": True,
    "alpha": 0.6,  # Balanced approach
    "llm_temperature": 0.1,
    "llm_max_tokens": 1024
}

# Balanced profile (default)
BALANCED_PROFILE = {
    "top_k": 4,
    "max_chunks": 4,
    "max_tokens": 1000,
    "use_cross_encoder": True,
    "alpha": 0.7,
    "llm_temperature": 0.1,
    "llm_max_tokens": 1024
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_config(profile: str = "balanced") -> Dict[str, Any]:
    """
    Get configuration for a specific profile.
    
    Args:
        profile: "speed", "quality", or "balanced"
    
    Returns:
        Dictionary with configuration settings
    """
    profiles = {
        "speed": SPEED_PROFILE,
        "quality": QUALITY_PROFILE,
        "balanced": BALANCED_PROFILE
    }
    
    if profile not in profiles:
        print(f"⚠️ Unknown profile '{profile}', using balanced profile")
        profile = "balanced"
    
    base_config = {
        "performance": PERFORMANCE_CONFIG,
        "retrieval": RETRIEVAL_CONFIG,
        "llm": LLM_CONFIG,
        "namespace": NAMESPACE_CONFIG,
        "prompt": PROMPT_CONFIG,
        "database": DATABASE_CONFIG,
        "error": ERROR_CONFIG,
        "monitoring": MONITORING_CONFIG
    }
    
    # Override with profile-specific settings
    profile_config = profiles[profile]
    base_config["performance"].update(profile_config)
    
    return base_config

def update_config(updates: Dict[str, Any], profile: str = "balanced") -> Dict[str, Any]:
    """
    Update configuration with custom settings.
    
    Args:
        updates: Dictionary with settings to update
        profile: Base profile to start from
    
    Returns:
        Updated configuration dictionary
    """
    config = get_config(profile)
    
    # Recursively update nested dictionaries
    def update_nested(base: Dict, updates: Dict):
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                update_nested(base[key], value)
            else:
                base[key] = value
    
    update_nested(config, updates)
    return config

def get_optimization_tips() -> List[str]:
    """Get tips for optimizing RAG performance."""
    return [
        "Reduce top_k for faster retrieval",
        "Disable cross-encoder for speed (use_cross_encoder=False)",
        "Increase alpha for more dense search weight",
        "Reduce max_tokens for faster generation",
        "Use speed profile for maximum performance",
        "Use quality profile for best accuracy",
        "Monitor cache hit rates for embedding optimization",
        "Adjust chunk size based on document characteristics"
    ]

def main():
    """Test configuration functions."""
    print("=== RAG Configuration Test ===")
    
    # Test different profiles
    for profile in ["speed", "balanced", "quality"]:
        print(f"\n{profile.upper()} Profile:")
        config = get_config(profile)
        print(f"  top_k: {config['performance']['top_k']}")
        print(f"  use_cross_encoder: {config['performance']['use_cross_encoder']}")
        print(f"  alpha: {config['retrieval']['alpha']}")
    
    # Test custom updates
    print(f"\nCustom Configuration:")
    custom_config = update_config({
        "performance": {"top_k": 10},
        "retrieval": {"alpha": 0.5}
    }, "balanced")
    print(f"  top_k: {custom_config['performance']['top_k']}")
    print(f"  alpha: {custom_config['retrieval']['alpha']}")
    
    # Show optimization tips
    print(f"\nOptimization Tips:")
    for tip in get_optimization_tips():
        print(f"  - {tip}")

if __name__ == "__main__":
    main() 
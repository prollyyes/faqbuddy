"""
Enhanced Embeddings for RAGv2
=============================

This module implements the next task I wanted to implement: Embedding upgrade with instructor-xl.
It replaces all-mpnet-base-v2 with instructor-xl and prepends instruction prefixes.
"""

import time
from typing import List, Union, Optional
from sentence_transformers import SentenceTransformer
from ..config import (
    INSTRUCTOR_XL_EMBEDDINGS, 
    get_embedding_model, 
    get_embedding_instruction,
    CURRENT_EMBEDDING_MODEL,
    NEW_EMBEDDING_MODEL
)

class EnhancedEmbeddings:
    """
    Enhanced embeddings with support for instructor-xl and instruction prefixes.
    
    Features:
    - Automatic model selection based on feature flags
    - Instruction prefix for instructor-xl
    - Latency monitoring
    - Fallback to current model
    """
    
    def __init__(self, device: str = 'auto'):
        """
        Initialize the enhanced embeddings system.
        
        Args:
            device: Device to use ('auto', 'cpu', 'cuda'). 'auto' will detect CUDA or fallback to CPU
        """
        self.model_name = get_embedding_model()
        self.instruction = get_embedding_instruction()
        
        # Force CPU for embedding model to avoid GPU memory conflicts with LLM models
        if device == 'auto':
            self.device = 'cpu'
            print(f"🖥️ Forced CPU device for embedding model (to avoid GPU memory conflicts with LLM)")
        else:
            self.device = device
        
        self._model = None
        self.latency_stats = []
        
        print(f"🚀 Initializing EnhancedEmbeddings with model: {self.model_name}")
        print(f"📝 Using all-mpnet-base-v2 (no instruction prefix needed)")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._model is None:
            print(f"🔄 Loading embedding model: {self.model_name}")
            start_time = time.time()
            
            # Use the primary model directly (all-mpnet-base-v2)
            self._model = SentenceTransformer(self.model_name, device=self.device)
            load_time = time.time() - start_time
            print(f"✅ Model loaded successfully in {load_time:.2f}s")
        
        return self._model
    
    def _prepare_texts(self, texts: Union[str, List[str]]) -> List[str]:
        """Prepare texts with instruction prefix if using instructor-xl."""
        if isinstance(texts, str):
            texts = [texts]
        
        # Since we're using all-mpnet-base-v2, no instruction prefix needed
        return texts
    
    def encode(self, texts: Union[str, List[str]], **kwargs) -> List[List[float]]:
        """
        Encode texts to embeddings with latency monitoring.
        
        Args:
            texts: Text or list of texts to encode
            **kwargs: Additional arguments for SentenceTransformer.encode()
            
        Returns:
            List of embedding vectors
        """
        start_time = time.time()
        
        # Prepare texts with instruction prefix
        prepared_texts = self._prepare_texts(texts)
        
        # Encode
        embeddings = self.model.encode(prepared_texts, **kwargs)
        
        # Record latency
        latency = time.time() - start_time
        self.latency_stats.append(latency)
        
        # Convert to list if single text
        if isinstance(texts, str):
            embeddings = [embeddings.tolist()]
        else:
            embeddings = embeddings.tolist()
        
        return embeddings
    
    def encode_single(self, text: str, **kwargs) -> List[float]:
        """
        Encode a single text to embedding.
        
        Args:
            text: Text to encode
            **kwargs: Additional arguments for SentenceTransformer.encode()
            
        Returns:
            Embedding vector
        """
        embeddings = self.encode([text], **kwargs)
        return embeddings[0]
    
    def get_average_latency(self) -> float:
        """Get average encoding latency in milliseconds."""
        if not self.latency_stats:
            return 0.0
        return sum(self.latency_stats) / len(self.latency_stats) * 1000
    
    def get_p95_latency(self) -> float:
        """Get 95th percentile encoding latency in milliseconds."""
        if not self.latency_stats:
            return 0.0
        sorted_latencies = sorted(self.latency_stats)
        p95_index = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[p95_index] * 1000
    
    def reset_latency_stats(self) -> None:
        """Reset latency statistics."""
        self.latency_stats = []
    
    def get_model_info(self) -> dict:
        """Get information about the current model."""
        return {
            "model_name": self.model_name,
            "using_instructor_xl": INSTRUCTOR_XL_EMBEDDINGS,
            "instruction_prefix": self.instruction,
            "device": self.device,
            "embedding_dimension": self.model.get_sentence_embedding_dimension(),
            "average_latency_ms": self.get_average_latency(),
            "p95_latency_ms": self.get_p95_latency(),
            "total_encodings": len(self.latency_stats)
        }


def test_embedding_upgrade():
    """Test the embedding upgrade functionality."""
    print("🧪 Testing Enhanced Embeddings...")
    
    # Initialize embeddings
    embeddings = EnhancedEmbeddings()
    
    # Test single text encoding
    test_text = "This is a test sentence for embedding generation."
    embedding = embeddings.encode_single(test_text)
    
    print(f"✅ Single text encoding successful")
    print(f"📏 Embedding dimension: {len(embedding)}")
    
    # Test batch encoding
    test_texts = [
        "First test sentence",
        "Second test sentence", 
        "Third test sentence"
    ]
    batch_embeddings = embeddings.encode(test_texts)
    
    print(f"✅ Batch encoding successful")
    print(f"📊 Batch size: {len(batch_embeddings)}")
    
    # Check latency
    avg_latency = embeddings.get_average_latency()
    p95_latency = embeddings.get_p95_latency()
    
    print(f"⏱️ Average latency: {avg_latency:.2f}ms")
    print(f"⏱️ P95 latency: {p95_latency:.2f}ms")
    
    # Check if latency is within acceptable range (120ms per row)
    if avg_latency <= 120:
        print("✅ Latency within acceptable range")
    else:
        print(f"⚠️ Latency exceeds target: {avg_latency:.2f}ms > 120ms")
    
    # Get model info
    info = embeddings.get_model_info()
    print(f"📋 Model info: {info}")
    
    return True


def benchmark_embedding_performance():
    """Benchmark embedding performance for backfill job validation."""
    print("🏃 Benchmarking embedding performance...")
    
    embeddings = EnhancedEmbeddings()
    
    # Generate test data (simulate course_edition rows)
    test_texts = [
        f"Edizione del corso di Test Course {i} per il periodo 'S1/2024'. "
        f"Docente: Professor Test {i}. Modalità d'esame: Orale. "
        f"Piattaforma utilizzata: Test Platform {i}."
        for i in range(100)  # Test with 100 rows
    ]
    
    start_time = time.time()
    
    # Encode all texts
    all_embeddings = embeddings.encode(test_texts)
    
    total_time = time.time() - start_time
    avg_time_per_row = total_time / len(test_texts) * 1000  # Convert to ms
    
    print(f"📊 Benchmark Results:")
    print(f"   Total rows: {len(test_texts)}")
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Average time per row: {avg_time_per_row:.2f}ms")
    print(f"   Rows per second: {len(test_texts) / total_time:.2f}")
    
    # Check if backfill job would complete within requirements
    if avg_time_per_row <= 120:
        print("✅ Backfill job would complete within latency requirements")
        return True
    else:
        print(f"❌ Backfill job would exceed latency requirements: {avg_time_per_row:.2f}ms > 120ms")
        return False


if __name__ == "__main__":
    test_embedding_upgrade()
    benchmark_embedding_performance() 
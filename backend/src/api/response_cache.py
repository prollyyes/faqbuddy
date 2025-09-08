"""
Response Cache Manager
=====================

Simple in-memory cache for responses and retrieval results to improve performance.
"""

import hashlib
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass
from collections import OrderedDict

@dataclass
class CacheEntry:
    """Represents a cached response."""
    response: Any
    timestamp: float
    ttl: float

class ResponseCache:
    """
    Simple LRU cache for responses and retrieval results.
    
    Features:
    - LRU eviction policy
    - TTL-based expiration
    - Separate caches for different types of data
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        Initialize the response cache.
        
        Args:
            max_size: Maximum number of entries to keep
            default_ttl: Default time-to-live in seconds (5 minutes)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Separate caches for different data types
        self.response_cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.retrieval_cache: OrderedDict[str, CacheEntry] = OrderedDict()
    
    def _generate_key(self, question: str, context: str = "") -> str:
        """Generate a cache key from question and context."""
        content = f"{question}|{context}".lower().strip()
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry is expired."""
        return time.time() - entry.timestamp > entry.ttl
    
    def _cleanup_cache(self, cache: OrderedDict[str, CacheEntry]) -> None:
        """Remove expired entries and enforce size limit."""
        # Remove expired entries
        expired_keys = [key for key, entry in cache.items() if self._is_expired(entry)]
        for key in expired_keys:
            del cache[key]
        
        # Enforce size limit (LRU eviction)
        while len(cache) > self.max_size:
            cache.popitem(last=False)
    
    def get_response(self, question: str, context: str = "") -> Optional[Any]:
        """Get a cached response."""
        key = self._generate_key(question, context)
        
        if key in self.response_cache:
            entry = self.response_cache[key]
            if not self._is_expired(entry):
                # Move to end (most recently used)
                self.response_cache.move_to_end(key)
                return entry.response
            else:
                del self.response_cache[key]
        
        return None
    
    def set_response(self, question: str, response: Any, context: str = "", ttl: Optional[int] = None) -> None:
        """Cache a response."""
        key = self._generate_key(question, context)
        entry = CacheEntry(
            response=response,
            timestamp=time.time(),
            ttl=ttl or self.default_ttl
        )
        
        self.response_cache[key] = entry
        self.response_cache.move_to_end(key)
        self._cleanup_cache(self.response_cache)
    
    def get_retrieval(self, question: str, context: str = "") -> Optional[Any]:
        """Get cached retrieval results."""
        key = self._generate_key(question, context)
        
        if key in self.retrieval_cache:
            entry = self.retrieval_cache[key]
            if not self._is_expired(entry):
                # Move to end (most recently used)
                self.retrieval_cache.move_to_end(key)
                return entry.response
            else:
                del self.retrieval_cache[key]
        
        return None
    
    def set_retrieval(self, question: str, retrieval_results: Any, context: str = "", ttl: Optional[int] = None) -> None:
        """Cache retrieval results."""
        key = self._generate_key(question, context)
        entry = CacheEntry(
            response=retrieval_results,
            timestamp=time.time(),
            ttl=ttl or self.default_ttl
        )
        
        self.retrieval_cache[key] = entry
        self.retrieval_cache.move_to_end(key)
        self._cleanup_cache(self.retrieval_cache)
    
    def clear(self) -> None:
        """Clear all caches."""
        self.response_cache.clear()
        self.retrieval_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "response_cache_size": len(self.response_cache),
            "retrieval_cache_size": len(self.retrieval_cache),
            "max_size": self.max_size,
            "default_ttl": self.default_ttl
        }

# Global cache instance
response_cache = ResponseCache(max_size=50, default_ttl=300)  # 5 minutes TTL

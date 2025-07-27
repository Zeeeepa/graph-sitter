"""
Performance Caching System for Serena Analysis

This module provides intelligent caching mechanisms to optimize the performance
of Serena analysis operations, reducing redundant computations and improving
response times for large codebases.
"""

import hashlib
import json
import time
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Optional, Callable, Union
from dataclasses import dataclass, asdict
from threading import RLock
import weakref

from ..serena_types import SerenaConfig


@dataclass
class CacheEntry:
    """Represents a cached analysis result."""
    data: Any
    timestamp: float
    file_hash: str
    access_count: int = 0
    last_access: float = 0.0
    
    def is_valid(self, current_hash: str, ttl: float) -> bool:
        """Check if cache entry is still valid."""
        current_time = time.time()
        return (
            self.file_hash == current_hash and
            (current_time - self.timestamp) < ttl
        )
    
    def touch(self):
        """Update access statistics."""
        self.access_count += 1
        self.last_access = time.time()


class AnalysisCache:
    """
    High-performance caching system for Serena analysis results.
    
    Features:
    - File content-based invalidation
    - TTL (Time To Live) support
    - LRU eviction policy
    - Memory usage monitoring
    - Thread-safe operations
    """
    
    def __init__(self, 
                 max_entries: int = 1000,
                 default_ttl: float = 3600.0,  # 1 hour
                 max_memory_mb: float = 100.0):
        self.max_entries = max_entries
        self.default_ttl = default_ttl
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'memory_usage': 0
        }
    
    def _generate_key(self, operation: str, file_path: str, **kwargs) -> str:
        """Generate a unique cache key for the operation."""
        key_data = {
            'operation': operation,
            'file_path': str(file_path),
            **kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def _get_file_hash(self, file_path: Union[str, Path]) -> str:
        """Get hash of file content for invalidation."""
        try:
            path = Path(file_path)
            if not path.exists():
                return "nonexistent"
            
            with open(path, 'rb') as f:
                content = f.read()
            # Use MD5 for non-security purposes (file change detection)
            return hashlib.md5(content, usedforsecurity=False).hexdigest()
        except Exception:
            return "error"
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate memory usage of cached data."""
        try:
            return len(json.dumps(data, default=str).encode())
        except Exception:
            return 1024  # Default estimate
    
    def _evict_lru(self):
        """Evict least recently used entries."""
        if not self._cache:
            return
        
        # Sort by last access time
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_access
        )
        
        # Remove oldest entries until we're under limits
        entries_to_remove = len(sorted_entries) - self.max_entries + 1
        
        for i in range(min(entries_to_remove, len(sorted_entries) // 4)):
            key, entry = sorted_entries[i]
            del self._cache[key]
            self._stats['evictions'] += 1
    
    def get(self, operation: str, file_path: str, **kwargs) -> Optional[Any]:
        """Retrieve cached result if valid."""
        key = self._generate_key(operation, file_path, **kwargs)
        
        with self._lock:
            if key not in self._cache:
                self._stats['misses'] += 1
                return None
            
            entry = self._cache[key]
            current_hash = self._get_file_hash(file_path)
            
            if not entry.is_valid(current_hash, self.default_ttl):
                del self._cache[key]
                self._stats['misses'] += 1
                return None
            
            entry.touch()
            self._stats['hits'] += 1
            return entry.data
    
    def set(self, operation: str, file_path: str, data: Any, **kwargs):
        """Store analysis result in cache."""
        key = self._generate_key(operation, file_path, **kwargs)
        file_hash = self._get_file_hash(file_path)
        
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            file_hash=file_hash
        )
        entry.touch()
        
        with self._lock:
            # Check if we need to evict entries
            if len(self._cache) >= self.max_entries:
                self._evict_lru()
            
            self._cache[key] = entry
    
    def invalidate_file(self, file_path: str):
        """Invalidate all cache entries for a specific file."""
        file_path_str = str(file_path)
        
        with self._lock:
            keys_to_remove = []
            for key, entry in self._cache.items():
                # Check if this cache entry is for the specified file
                try:
                    key_data = json.loads(key)
                    if key_data.get('file_path') == file_path_str:
                        keys_to_remove.append(key)
                except (json.JSONDecodeError, KeyError, TypeError):
                    # Skip malformed cache keys
                    pass
            
            for key in keys_to_remove:
                del self._cache[key]
    
    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self._stats = {
                'hits': 0,
                'misses': 0,
                'evictions': 0,
                'memory_usage': 0
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                'entries': len(self._cache),
                'max_entries': self.max_entries,
                'hits': self._stats['hits'],
                'misses': self._stats['misses'],
                'hit_rate': hit_rate,
                'evictions': self._stats['evictions'],
                'memory_usage_mb': sum(
                    self._estimate_size(entry.data) 
                    for entry in self._cache.values()
                ) / (1024 * 1024)
            }


# Global cache instance
_global_cache: Optional[AnalysisCache] = None
_cache_lock = RLock()


def get_cache() -> AnalysisCache:
    """Get or create the global cache instance."""
    global _global_cache
    
    with _cache_lock:
        if _global_cache is None:
            _global_cache = AnalysisCache()
        return _global_cache


def configure_cache(max_entries: int = 1000, 
                   default_ttl: float = 3600.0,
                   max_memory_mb: float = 100.0):
    """Configure the global cache settings."""
    global _global_cache
    
    with _cache_lock:
        _global_cache = AnalysisCache(
            max_entries=max_entries,
            default_ttl=default_ttl,
            max_memory_mb=max_memory_mb
        )


def cached_analysis(operation: str, ttl: Optional[float] = None):
    """
    Decorator to cache analysis function results.
    
    Args:
        operation: Name of the analysis operation
        ttl: Time to live for cache entries (uses default if None)
    
    Usage:
        @cached_analysis("error_analysis")
        def analyze_errors(file_path: str, **kwargs):
            # Expensive analysis operation
            return results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract file_path from arguments
            file_path = None
            if args:
                file_path = args[0]
            elif 'file_path' in kwargs:
                file_path = kwargs['file_path']
            
            if not file_path:
                # Can't cache without file path
                return func(*args, **kwargs)
            
            cache = get_cache()
            
            # Try to get from cache
            cache_kwargs = {k: v for k, v in kwargs.items() if k != 'file_path'}
            cached_result = cache.get(operation, file_path, **cache_kwargs)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(operation, file_path, result, **cache_kwargs)
            
            return result
        
        return wrapper
    return decorator


class BatchCache:
    """
    Specialized cache for batch operations on multiple files.
    Optimizes for scenarios where multiple files are analyzed together.
    """
    
    def __init__(self, base_cache: Optional[AnalysisCache] = None):
        self.base_cache = base_cache or get_cache()
        self._batch_results: Dict[str, Any] = {}
        self._batch_active = False
    
    def start_batch(self):
        """Start a batch operation."""
        self._batch_active = True
        self._batch_results.clear()
    
    def end_batch(self):
        """End batch operation and commit results to cache."""
        if not self._batch_active:
            return
        
        # Commit all batch results to main cache
        for key, data in self._batch_results.items():
            # Parse key to extract operation and file_path
            try:
                operation, file_path = key.split(':', 1)
                self.base_cache.set(operation, file_path, data)
            except (ValueError, AttributeError):
                # Skip malformed batch keys
                pass
        
        self._batch_results.clear()
        self._batch_active = False
    
    def get_or_compute(self, operation: str, file_path: str, 
                      compute_func: Callable, **kwargs) -> Any:
        """Get from cache or compute and store in batch."""
        if not self._batch_active:
            # Not in batch mode, use regular cache
            cached = self.base_cache.get(operation, file_path, **kwargs)
            if cached is not None:
                return cached
            
            result = compute_func()
            self.base_cache.set(operation, file_path, result, **kwargs)
            return result
        
        # In batch mode
        batch_key = f"{operation}:{file_path}"
        
        if batch_key in self._batch_results:
            return self._batch_results[batch_key]
        
        # Check main cache first
        cached = self.base_cache.get(operation, file_path, **kwargs)
        if cached is not None:
            self._batch_results[batch_key] = cached
            return cached
        
        # Compute and store in batch
        result = compute_func()
        self._batch_results[batch_key] = result
        return result


def batch_cached_analysis(operations: list):
    """
    Context manager for batch analysis operations.
    
    Usage:
        with batch_cached_analysis(['error_analysis', 'complexity_analysis']):
            for file in files:
                analyze_errors(file)
                analyze_complexity(file)
    """
    class BatchContext:
        def __init__(self):
            self.batch_cache = BatchCache()
        
        def __enter__(self):
            self.batch_cache.start_batch()
            return self.batch_cache
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.batch_cache.end_batch()
    
    return BatchContext()

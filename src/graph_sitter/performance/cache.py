"""
Enhanced caching utilities for graph-sitter operations.

Provides both in-memory and persistent caching solutions optimized
for codebase analysis and symbol resolution operations.
"""

import hashlib
import pickle
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, TypeVar, Generic, Callable, Union
from functools import wraps
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    value: T
    timestamp: float
    access_count: int = 0
    last_access: float = 0.0
    ttl: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.timestamp > self.ttl
    
    def touch(self) -> None:
        """Update access metadata."""
        self.access_count += 1
        self.last_access = time.time()


class EnhancedCache(Generic[K, V]):
    """
    Enhanced in-memory cache with TTL, LRU eviction, and statistics.
    
    Features:
    - TTL (time-to-live) support
    - LRU eviction policy
    - Access statistics
    - Thread-safe operations
    - Memory usage monitoring
    """
    
    def __init__(self, 
                 max_size: int = 1000,
                 default_ttl: Optional[float] = None,
                 cleanup_interval: float = 300.0):  # 5 minutes
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cleanup_interval = cleanup_interval
        
        self._cache: Dict[K, CacheEntry[V]] = {}
        self._lock = threading.RLock()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'cleanups': 0,
        }
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._stats['misses'] += 1
                return default
            
            if entry.is_expired():
                del self._cache[key]
                self._stats['misses'] += 1
                return default
            
            entry.touch()
            self._stats['hits'] += 1
            return entry.value
    
    def put(self, key: K, value: V, ttl: Optional[float] = None) -> None:
        """Put value in cache."""
        with self._lock:
            # Use provided TTL or default
            effective_ttl = ttl if ttl is not None else self.default_ttl
            
            entry = CacheEntry(
                value=value,
                timestamp=time.time(),
                ttl=effective_ttl
            )
            
            self._cache[key] = entry
            
            # Evict if over capacity
            if len(self._cache) > self.max_size:
                self._evict_lru()
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_access or self._cache[k].timestamp
        )
        
        del self._cache[lru_key]
        self._stats['evictions'] += 1
    
    def _periodic_cleanup(self) -> None:
        """Periodic cleanup of expired entries."""
        while True:
            time.sleep(self.cleanup_interval)
            self.cleanup_expired()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count removed."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self._stats['cleanups'] += 1
            
            return len(expired_keys)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def size(self) -> int:
        """Get current cache size."""
        with self._lock:
            return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats['hits'] + self._stats['misses']
            hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
            
            return {
                **self._stats,
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                'total_requests': total_requests,
            }


class PersistentCache:
    """
    Persistent cache using SQLite for long-term storage.
    
    Suitable for expensive operations that should persist across
    application restarts, such as symbol analysis results.
    """
    
    def __init__(self, cache_dir: Union[str, Path], name: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.cache_dir / f"{name}.db"
        self._lock = threading.Lock()
        
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    timestamp REAL,
                    ttl REAL,
                    access_count INTEGER DEFAULT 0,
                    last_access REAL
                )
            """)
            
            # Create index for cleanup queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON cache_entries(timestamp)
            """)
            
            conn.commit()
    
    def _serialize_key(self, key: Any) -> str:
        """Serialize key to string."""
        if isinstance(key, str):
            return key
        
        # Create hash for complex keys
        key_str = str(key)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, key: Any, default: Optional[T] = None) -> Optional[T]:
        """Get value from persistent cache."""
        key_str = self._serialize_key(key)
        
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT value, timestamp, ttl FROM cache_entries WHERE key = ?",
                        (key_str,)
                    )
                    row = cursor.fetchone()
                    
                    if row is None:
                        return default
                    
                    value_blob, timestamp, ttl = row
                    
                    # Check TTL
                    if ttl is not None and time.time() - timestamp > ttl:
                        # Entry expired, remove it
                        conn.execute("DELETE FROM cache_entries WHERE key = ?", (key_str,))
                        conn.commit()
                        return default
                    
                    # Update access statistics
                    conn.execute("""
                        UPDATE cache_entries 
                        SET access_count = access_count + 1, last_access = ?
                        WHERE key = ?
                    """, (time.time(), key_str))
                    conn.commit()
                    
                    # Deserialize value
                    return pickle.loads(value_blob)
                    
            except Exception as e:
                logger.error(f"Error reading from persistent cache: {e}")
                return default
    
    def put(self, key: Any, value: T, ttl: Optional[float] = None) -> None:
        """Put value in persistent cache."""
        key_str = self._serialize_key(key)
        
        with self._lock:
            try:
                value_blob = pickle.dumps(value)
                timestamp = time.time()
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO cache_entries 
                        (key, value, timestamp, ttl, access_count, last_access)
                        VALUES (?, ?, ?, ?, 0, ?)
                    """, (key_str, value_blob, timestamp, ttl, timestamp))
                    conn.commit()
                    
            except Exception as e:
                logger.error(f"Error writing to persistent cache: {e}")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    # Remove entries where TTL has expired
                    cursor = conn.execute("""
                        DELETE FROM cache_entries 
                        WHERE ttl IS NOT NULL 
                        AND (? - timestamp) > ttl
                    """, (time.time(),))
                    
                    deleted_count = cursor.rowcount
                    conn.commit()
                    return deleted_count
                    
            except Exception as e:
                logger.error(f"Error cleaning up persistent cache: {e}")
                return 0
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM cache_entries")
                    conn.commit()
            except Exception as e:
                logger.error(f"Error clearing persistent cache: {e}")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute("""
                        SELECT 
                            COUNT(*) as total_entries,
                            SUM(access_count) as total_accesses,
                            AVG(access_count) as avg_accesses,
                            COUNT(CASE WHEN ttl IS NOT NULL 
                                  AND (? - timestamp) > ttl THEN 1 END) as expired_entries
                        FROM cache_entries
                    """, (time.time(),))
                    
                    row = cursor.fetchone()
                    if row:
                        return {
                            'total_entries': row[0] or 0,
                            'total_accesses': row[1] or 0,
                            'avg_accesses': row[2] or 0,
                            'expired_entries': row[3] or 0,
                        }
                    
            except Exception as e:
                logger.error(f"Error getting cache stats: {e}")
            
            return {'total_entries': 0, 'total_accesses': 0, 'avg_accesses': 0, 'expired_entries': 0}


# Cache decorators for common patterns
def cached(cache: Union[EnhancedCache, PersistentCache], 
          ttl: Optional[float] = None,
          key_func: Optional[Callable[..., Any]] = None):
    """
    Decorator for caching function results.
    
    Args:
        cache: Cache instance to use
        ttl: Time-to-live for cached results
        key_func: Function to generate cache key from arguments
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Compute and cache result
            result = func(*args, **kwargs)
            cache.put(cache_key, result, ttl=ttl)
            return result
        
        return wrapper
    return decorator


# Global cache instances for common use cases
symbol_cache = EnhancedCache[str, Any](max_size=5000, default_ttl=3600)  # 1 hour TTL
dependency_cache = EnhancedCache[str, Any](max_size=2000, default_ttl=1800)  # 30 min TTL

# Persistent caches (initialized lazily)
_persistent_caches: Dict[str, PersistentCache] = {}


def get_persistent_cache(name: str, cache_dir: Optional[Union[str, Path]] = None) -> PersistentCache:
    """Get or create a persistent cache instance."""
    if name not in _persistent_caches:
        if cache_dir is None:
            cache_dir = Path.home() / ".graph_sitter" / "cache"
        _persistent_caches[name] = PersistentCache(cache_dir, name)
    
    return _persistent_caches[name]


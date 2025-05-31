"""
Advanced Caching Layer

Multi-level caching system with intelligent cache strategies and optimization.
"""

import hashlib
import pickle
import threading
import time
import weakref
from abc import ABC, abstractmethod
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union
from weakref import WeakKeyDictionary, WeakValueDictionary

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


class CacheStrategy(Enum):
    """Cache eviction strategies"""
    LRU = auto()          # Least Recently Used
    LFU = auto()          # Least Frequently Used
    FIFO = auto()         # First In, First Out
    TTL = auto()          # Time To Live
    ADAPTIVE = auto()     # Adaptive based on usage patterns
    WEAK_REF = auto()     # Weak reference caching


class CacheLevel(Enum):
    """Cache hierarchy levels"""
    L1_MEMORY = auto()    # Fast in-memory cache
    L2_COMPRESSED = auto() # Compressed memory cache
    L3_PERSISTENT = auto() # Persistent disk cache


@dataclass
class CacheStats:
    """Cache performance statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0
    hit_rate: float = 0.0
    memory_usage: int = 0
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    
    def update_hit_rate(self):
        """Update hit rate calculation"""
        total = self.hits + self.misses
        self.hit_rate = self.hits / total if total > 0 else 0.0


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    value: Any
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    size: int = 0
    ttl: Optional[float] = None
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self):
        """Update access metadata"""
        self.last_accessed = time.time()
        self.access_count += 1


class CacheInterface(ABC):
    """Abstract cache interface"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put value in cache"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cache entries"""
        pass
    
    @abstractmethod
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        pass


class LRUCache(CacheInterface):
    """Least Recently Used cache implementation"""
    
    def __init__(self, max_size: int = 1000, ttl: Optional[float] = None):
        self.max_size = max_size
        self.default_ttl = ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._stats = CacheStats(max_size=max_size)
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from LRU cache"""
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                self._stats.update_hit_rate()
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                del self._cache[key]
                self._stats.misses += 1
                self._stats.evictions += 1
                self._stats.size = len(self._cache)
                self._stats.update_hit_rate()
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            
            self._stats.hits += 1
            self._stats.access_count += 1
            self._stats.update_hit_rate()
            
            return entry.value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put value in LRU cache"""
        with self._lock:
            # Calculate entry size
            try:
                size = len(pickle.dumps(value))
            except:
                size = 1  # Fallback size
            
            entry = CacheEntry(
                value=value,
                size=size,
                ttl=ttl or self.default_ttl
            )
            
            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]
            
            # Add new entry
            self._cache[key] = entry
            
            # Evict if necessary
            while len(self._cache) > self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self._stats.evictions += 1
            
            self._stats.size = len(self._cache)
            self._stats.memory_usage += size
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                self._stats.memory_usage -= entry.size
                del self._cache[key]
                self._stats.size = len(self._cache)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._stats.size = 0
            self._stats.memory_usage = 0
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self._stats


class LFUCache(CacheInterface):
    """Least Frequently Used cache implementation"""
    
    def __init__(self, max_size: int = 1000, ttl: Optional[float] = None):
        self.max_size = max_size
        self.default_ttl = ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._frequencies: defaultdict[int, Set[str]] = defaultdict(set)
        self._key_frequencies: Dict[str, int] = {}
        self._min_frequency = 0
        self._stats = CacheStats(max_size=max_size)
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from LFU cache"""
        with self._lock:
            if key not in self._cache:
                self._stats.misses += 1
                self._stats.update_hit_rate()
                return None
            
            entry = self._cache[key]
            
            # Check expiration
            if entry.is_expired():
                self._remove_key(key)
                self._stats.misses += 1
                self._stats.evictions += 1
                self._stats.update_hit_rate()
                return None
            
            # Update frequency
            self._update_frequency(key)
            entry.touch()
            
            self._stats.hits += 1
            self._stats.access_count += 1
            self._stats.update_hit_rate()
            
            return entry.value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put value in LFU cache"""
        with self._lock:
            # Calculate entry size
            try:
                size = len(pickle.dumps(value))
            except:
                size = 1
            
            # Remove existing entry if present
            if key in self._cache:
                self._remove_key(key)
            
            # Evict if necessary
            while len(self._cache) >= self.max_size:
                self._evict_lfu()
            
            # Add new entry
            entry = CacheEntry(
                value=value,
                size=size,
                ttl=ttl or self.default_ttl
            )
            
            self._cache[key] = entry
            self._key_frequencies[key] = 1
            self._frequencies[1].add(key)
            self._min_frequency = 1
            
            self._stats.size = len(self._cache)
            self._stats.memory_usage += size
    
    def _update_frequency(self, key: str) -> None:
        """Update key frequency"""
        freq = self._key_frequencies[key]
        self._frequencies[freq].remove(key)
        
        if freq == self._min_frequency and not self._frequencies[freq]:
            self._min_frequency += 1
        
        self._key_frequencies[key] = freq + 1
        self._frequencies[freq + 1].add(key)
    
    def _evict_lfu(self) -> None:
        """Evict least frequently used entry"""
        if not self._frequencies[self._min_frequency]:
            return
        
        key_to_remove = self._frequencies[self._min_frequency].pop()
        self._remove_key(key_to_remove)
        self._stats.evictions += 1
    
    def _remove_key(self, key: str) -> None:
        """Remove key from all data structures"""
        if key in self._cache:
            entry = self._cache[key]
            self._stats.memory_usage -= entry.size
            del self._cache[key]
        
        if key in self._key_frequencies:
            freq = self._key_frequencies[key]
            self._frequencies[freq].discard(key)
            del self._key_frequencies[key]
        
        self._stats.size = len(self._cache)
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        with self._lock:
            if key in self._cache:
                self._remove_key(key)
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._frequencies.clear()
            self._key_frequencies.clear()
            self._min_frequency = 0
            self._stats.size = 0
            self._stats.memory_usage = 0
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self._stats


class WeakRefCache(CacheInterface):
    """Weak reference cache for automatic memory management"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: WeakValueDictionary = WeakValueDictionary()
        self._metadata: Dict[str, CacheEntry] = {}
        self._stats = CacheStats(max_size=max_size)
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from weak reference cache"""
        with self._lock:
            try:
                value = self._cache[key]
                if key in self._metadata:
                    self._metadata[key].touch()
                self._stats.hits += 1
                self._stats.access_count += 1
                self._stats.update_hit_rate()
                return value
            except KeyError:
                self._stats.misses += 1
                self._stats.update_hit_rate()
                # Clean up metadata for garbage collected objects
                if key in self._metadata:
                    del self._metadata[key]
                return None
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put value in weak reference cache"""
        with self._lock:
            try:
                # Only cache objects that support weak references
                self._cache[key] = value
                
                try:
                    size = len(pickle.dumps(value))
                except:
                    size = 1
                
                self._metadata[key] = CacheEntry(
                    value=None,  # Don't store value in metadata
                    size=size,
                    ttl=ttl
                )
                
                self._stats.size = len(self._cache)
                self._stats.memory_usage += size
                
            except TypeError:
                # Object doesn't support weak references
                logger.warning(f"Cannot cache object of type {type(value)} - weak references not supported")
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        with self._lock:
            deleted = False
            if key in self._cache:
                del self._cache[key]
                deleted = True
            if key in self._metadata:
                entry = self._metadata[key]
                self._stats.memory_usage -= entry.size
                del self._metadata[key]
                deleted = True
            
            self._stats.size = len(self._cache)
            return deleted
    
    def clear(self) -> None:
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            self._metadata.clear()
            self._stats.size = 0
            self._stats.memory_usage = 0
    
    def get_stats(self) -> CacheStats:
        """Get cache statistics"""
        return self._stats


class MultiLevelCache(CacheInterface):
    """Multi-level cache with L1, L2, L3 hierarchy"""
    
    def __init__(self, 
                 l1_size: int = 1000,
                 l2_size: int = 5000,
                 l3_size: int = 10000,
                 l1_strategy: CacheStrategy = CacheStrategy.LRU,
                 l2_strategy: CacheStrategy = CacheStrategy.LFU,
                 l3_strategy: CacheStrategy = CacheStrategy.TTL):
        
        self.l1_cache = self._create_cache(l1_strategy, l1_size)
        self.l2_cache = self._create_cache(l2_strategy, l2_size)
        self.l3_cache = self._create_cache(l3_strategy, l3_size)
        
        self._stats = CacheStats(max_size=l1_size + l2_size + l3_size)
        self._lock = threading.RLock()
    
    def _create_cache(self, strategy: CacheStrategy, size: int) -> CacheInterface:
        """Create cache based on strategy"""
        if strategy == CacheStrategy.LRU:
            return LRUCache(size)
        elif strategy == CacheStrategy.LFU:
            return LFUCache(size)
        elif strategy == CacheStrategy.WEAK_REF:
            return WeakRefCache(size)
        else:
            return LRUCache(size)  # Default fallback
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from multi-level cache"""
        with self._lock:
            # Try L1 first
            value = self.l1_cache.get(key)
            if value is not None:
                self._stats.hits += 1
                self._stats.update_hit_rate()
                return value
            
            # Try L2
            value = self.l2_cache.get(key)
            if value is not None:
                # Promote to L1
                self.l1_cache.put(key, value)
                self._stats.hits += 1
                self._stats.update_hit_rate()
                return value
            
            # Try L3
            value = self.l3_cache.get(key)
            if value is not None:
                # Promote to L2 and L1
                self.l2_cache.put(key, value)
                self.l1_cache.put(key, value)
                self._stats.hits += 1
                self._stats.update_hit_rate()
                return value
            
            self._stats.misses += 1
            self._stats.update_hit_rate()
            return None
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Put value in multi-level cache"""
        with self._lock:
            # Store in all levels
            self.l1_cache.put(key, value, ttl)
            self.l2_cache.put(key, value, ttl)
            self.l3_cache.put(key, value, ttl)
            
            # Update stats
            self._update_stats()
    
    def delete(self, key: str) -> bool:
        """Delete value from all cache levels"""
        with self._lock:
            deleted = False
            deleted |= self.l1_cache.delete(key)
            deleted |= self.l2_cache.delete(key)
            deleted |= self.l3_cache.delete(key)
            
            self._update_stats()
            return deleted
    
    def clear(self) -> None:
        """Clear all cache levels"""
        with self._lock:
            self.l1_cache.clear()
            self.l2_cache.clear()
            self.l3_cache.clear()
            self._update_stats()
    
    def _update_stats(self) -> None:
        """Update combined statistics"""
        l1_stats = self.l1_cache.get_stats()
        l2_stats = self.l2_cache.get_stats()
        l3_stats = self.l3_cache.get_stats()
        
        self._stats.size = l1_stats.size + l2_stats.size + l3_stats.size
        self._stats.memory_usage = (l1_stats.memory_usage + 
                                   l2_stats.memory_usage + 
                                   l3_stats.memory_usage)
    
    def get_stats(self) -> CacheStats:
        """Get combined cache statistics"""
        self._update_stats()
        return self._stats
    
    def get_level_stats(self) -> Dict[str, CacheStats]:
        """Get statistics for each cache level"""
        return {
            'L1': self.l1_cache.get_stats(),
            'L2': self.l2_cache.get_stats(),
            'L3': self.l3_cache.get_stats()
        }


class CacheManager:
    """Advanced cache manager with multiple strategies and optimization"""
    
    def __init__(self):
        self._caches: Dict[str, CacheInterface] = {}
        self._default_cache = MultiLevelCache()
        self._lock = threading.RLock()
        
    def get_cache(self, name: str = "default") -> CacheInterface:
        """Get or create named cache"""
        with self._lock:
            if name == "default":
                return self._default_cache
            
            if name not in self._caches:
                self._caches[name] = LRUCache()
            
            return self._caches[name]
    
    def create_cache(self, 
                    name: str,
                    strategy: CacheStrategy = CacheStrategy.LRU,
                    max_size: int = 1000,
                    ttl: Optional[float] = None) -> CacheInterface:
        """Create a new cache with specified strategy"""
        with self._lock:
            if strategy == CacheStrategy.LRU:
                cache = LRUCache(max_size, ttl)
            elif strategy == CacheStrategy.LFU:
                cache = LFUCache(max_size, ttl)
            elif strategy == CacheStrategy.WEAK_REF:
                cache = WeakRefCache(max_size)
            else:
                cache = LRUCache(max_size, ttl)
            
            self._caches[name] = cache
            return cache
    
    def cached(self, 
              cache_name: str = "default",
              key_func: Optional[Callable] = None,
              ttl: Optional[float] = None) -> Callable[[F], F]:
        """Decorator for caching function results"""
        
        def decorator(func: F) -> F:
            cache = self.get_cache(cache_name)
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = self._generate_key(func.__name__, args, kwargs)
                
                # Try to get from cache
                result = cache.get(cache_key)
                if result is not None:
                    return result
                
                # Execute function and cache result
                result = func(*args, **kwargs)
                cache.put(cache_key, result, ttl)
                
                return result
            
            return wrapper
        
        return decorator
    
    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        """Generate cache key from function name and arguments"""
        key_data = f"{func_name}_{args}_{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get_all_stats(self) -> Dict[str, CacheStats]:
        """Get statistics for all caches"""
        stats = {"default": self._default_cache.get_stats()}
        
        for name, cache in self._caches.items():
            stats[name] = cache.get_stats()
        
        return stats
    
    def clear_all(self) -> None:
        """Clear all caches"""
        with self._lock:
            self._default_cache.clear()
            for cache in self._caches.values():
                cache.clear()


# Global cache manager instance
_global_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CacheManager()
    return _global_cache_manager


def cached(cache_name: str = "default",
          key_func: Optional[Callable] = None,
          ttl: Optional[float] = None) -> Callable[[F], F]:
    """Global caching decorator"""
    manager = get_cache_manager()
    return manager.cached(cache_name, key_func, ttl)


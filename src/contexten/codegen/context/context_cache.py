"""
Context caching for performance optimization.

This module provides intelligent caching of context enhancement results
to improve performance and reduce redundant processing.
"""

import asyncio
import time
import logging
import json
import hashlib
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    data: Any
    created_at: float
    accessed_at: float
    access_count: int
    ttl: float
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.created_at > self.ttl
    
    def touch(self) -> None:
        """Update access time and count."""
        self.accessed_at = time.time()
        self.access_count += 1


class ContextCache:
    """
    Intelligent context cache with TTL and LRU eviction.
    
    Features:
    - Time-based expiration (TTL)
    - LRU eviction when cache is full
    - Access pattern tracking
    - Memory usage monitoring
    - Async-safe operations
    """
    
    def __init__(self,
                 ttl: int = 3600,
                 max_entries: int = 1000,
                 cleanup_interval: int = 300):
        """
        Initialize context cache.
        
        Args:
            ttl: Time-to-live for cache entries in seconds
            max_entries: Maximum number of cache entries
            cleanup_interval: Cleanup interval in seconds
        """
        self.ttl = ttl
        self.max_entries = max_entries
        self.cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "cleanups": 0,
            "total_entries": 0,
            "memory_usage": 0
        }
    
    async def initialize(self) -> None:
        """Initialize the cache and start cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Context cache initialized with TTL={self.ttl}s, max_entries={self.max_entries}")
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self.stats["misses"] += 1
                return None
            
            if entry.is_expired():
                del self._cache[key]
                self.stats["misses"] += 1
                return None
            
            entry.touch()
            self.stats["hits"] += 1
            return entry.data
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
        """
        async with self._lock:
            # Use provided TTL or default
            entry_ttl = ttl or self.ttl
            
            # Create cache entry
            entry = CacheEntry(
                data=value,
                created_at=time.time(),
                accessed_at=time.time(),
                access_count=1,
                ttl=entry_ttl
            )
            
            # Check if we need to evict entries
            if len(self._cache) >= self.max_entries:
                await self._evict_lru()
            
            self._cache[key] = entry
            self.stats["total_entries"] = len(self._cache)
    
    async def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                self.stats["total_entries"] = len(self._cache)
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self.stats["total_entries"] = 0
            logger.info("Cache cleared")
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time - entry.created_at > entry.ttl
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self.stats["cleanups"] += 1
                self.stats["total_entries"] = len(self._cache)
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_requests if total_requests > 0 else 0.0
        
        return {
            **self.stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "cache_size": len(self._cache),
            "max_entries": self.max_entries,
            "ttl": self.ttl
        }
    
    async def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        async with self._lock:
            current_time = time.time()
            
            # Analyze cache entries
            total_size = 0
            oldest_entry = current_time
            newest_entry = 0
            access_counts = []
            
            for entry in self._cache.values():
                # Estimate memory usage (rough approximation)
                try:
                    entry_size = len(str(entry.data))
                    total_size += entry_size
                except:
                    total_size += 1000  # Default estimate
                
                oldest_entry = min(oldest_entry, entry.created_at)
                newest_entry = max(newest_entry, entry.created_at)
                access_counts.append(entry.access_count)
            
            avg_access_count = sum(access_counts) / len(access_counts) if access_counts else 0
            
            return {
                "total_entries": len(self._cache),
                "estimated_memory_bytes": total_size,
                "oldest_entry_age": current_time - oldest_entry if oldest_entry < current_time else 0,
                "newest_entry_age": current_time - newest_entry if newest_entry > 0 else 0,
                "average_access_count": avg_access_count,
                "max_access_count": max(access_counts) if access_counts else 0,
                "min_access_count": min(access_counts) if access_counts else 0
            }
    
    async def shutdown(self) -> None:
        """Shutdown the cache and cleanup resources."""
        logger.info("Shutting down context cache")
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        await self.clear()
        logger.info("Context cache shutdown complete")
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entries."""
        if not self._cache:
            return
        
        # Find LRU entry
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].accessed_at
        )
        
        del self._cache[lru_key]
        self.stats["evictions"] += 1
        logger.debug(f"Evicted LRU cache entry: {lru_key}")
    
    async def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired()
        except asyncio.CancelledError:
            logger.info("Cache cleanup loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Cache cleanup loop error: {e}")


class PersistentContextCache(ContextCache):
    """
    Context cache with optional persistence to disk.
    
    Extends the basic context cache with the ability to persist
    cache entries to disk for faster startup and cross-session caching.
    """
    
    def __init__(self,
                 cache_file: Optional[str] = None,
                 persist_interval: int = 600,
                 **kwargs):
        """
        Initialize persistent context cache.
        
        Args:
            cache_file: Optional file path for persistence
            persist_interval: How often to persist cache to disk (seconds)
            **kwargs: Arguments for base ContextCache
        """
        super().__init__(**kwargs)
        
        self.cache_file = cache_file
        self.persist_interval = persist_interval
        self._persist_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> None:
        """Initialize cache and load from disk if available."""
        await super().initialize()
        
        # Load from disk if cache file exists
        if self.cache_file:
            await self._load_from_disk()
            
            # Start persistence task
            self._persist_task = asyncio.create_task(self._persist_loop())
    
    async def shutdown(self) -> None:
        """Shutdown cache and persist to disk."""
        if self._persist_task:
            self._persist_task.cancel()
            try:
                await self._persist_task
            except asyncio.CancelledError:
                pass
        
        # Final persistence
        if self.cache_file:
            await self._persist_to_disk()
        
        await super().shutdown()
    
    async def _load_from_disk(self) -> None:
        """Load cache from disk."""
        try:
            import aiofiles
            
            async with aiofiles.open(self.cache_file, 'r') as f:
                data = await f.read()
                cache_data = json.loads(data)
            
            # Restore cache entries
            current_time = time.time()
            loaded_count = 0
            
            for key, entry_data in cache_data.items():
                try:
                    entry = CacheEntry(
                        data=entry_data['data'],
                        created_at=entry_data['created_at'],
                        accessed_at=entry_data['accessed_at'],
                        access_count=entry_data['access_count'],
                        ttl=entry_data['ttl']
                    )
                    
                    # Only load non-expired entries
                    if not entry.is_expired():
                        self._cache[key] = entry
                        loaded_count += 1
                
                except Exception as e:
                    logger.warning(f"Failed to load cache entry {key}: {e}")
            
            logger.info(f"Loaded {loaded_count} cache entries from disk")
            
        except FileNotFoundError:
            logger.info("No cache file found, starting with empty cache")
        except Exception as e:
            logger.error(f"Failed to load cache from disk: {e}")
    
    async def _persist_to_disk(self) -> None:
        """Persist cache to disk."""
        if not self.cache_file:
            return
        
        try:
            import aiofiles
            
            async with self._lock:
                # Convert cache to serializable format
                cache_data = {}
                for key, entry in self._cache.items():
                    if not entry.is_expired():
                        cache_data[key] = {
                            'data': entry.data,
                            'created_at': entry.created_at,
                            'accessed_at': entry.accessed_at,
                            'access_count': entry.access_count,
                            'ttl': entry.ttl
                        }
            
            # Write to disk
            async with aiofiles.open(self.cache_file, 'w') as f:
                await f.write(json.dumps(cache_data, indent=2))
            
            logger.debug(f"Persisted {len(cache_data)} cache entries to disk")
            
        except Exception as e:
            logger.error(f"Failed to persist cache to disk: {e}")
    
    async def _persist_loop(self) -> None:
        """Background persistence loop."""
        try:
            while True:
                await asyncio.sleep(self.persist_interval)
                await self._persist_to_disk()
        except asyncio.CancelledError:
            logger.info("Cache persistence loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Cache persistence loop error: {e}")


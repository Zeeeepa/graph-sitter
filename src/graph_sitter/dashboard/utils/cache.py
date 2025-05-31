"""Cache management utilities."""

import asyncio
import json
import time
from typing import Any, Dict, Optional


class CacheManager:
    """Simple in-memory cache manager with TTL support."""
    
    def __init__(self):
        """Initialize cache manager."""
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        async with self._lock:
            if key not in self._cache:
                return None
                
            entry = self._cache[key]
            
            # Check if expired
            if entry["expires_at"] and time.time() > entry["expires_at"]:
                del self._cache[key]
                return None
                
            return entry["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (None for no expiration)
        """
        async with self._lock:
            expires_at = None
            if ttl:
                expires_at = time.time() + ttl
                
            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time()
            }
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> int:
        """Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self._cache.items():
                if entry["expires_at"] and current_time > entry["expires_at"]:
                    expired_keys.append(key)
                    
            for key in expired_keys:
                del self._cache[key]
                
            return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        async with self._lock:
            total_entries = len(self._cache)
            expired_count = 0
            current_time = time.time()
            
            for entry in self._cache.values():
                if entry["expires_at"] and current_time > entry["expires_at"]:
                    expired_count += 1
                    
            return {
                "total_entries": total_entries,
                "active_entries": total_entries - expired_count,
                "expired_entries": expired_count,
                "memory_usage_estimate": len(json.dumps(self._cache, default=str))
            }


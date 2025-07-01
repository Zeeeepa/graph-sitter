"""Caching layer for performance optimization."""

import hashlib
import json
import logging
import os
import pickle
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from .config import AutogenConfig, CacheConfig
from .exceptions import CacheError

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache."""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all values from the cache."""
        pass
    
    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend."""
    
    def __init__(self, config: CacheConfig):
        """Initialize the memory cache backend."""
        self.config = config
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._current_size = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if entry["expires_at"] and time.time() > entry["expires_at"]:
            await self.delete(key)
            return None
        
        # Update access time
        entry["accessed_at"] = time.time()
        
        return entry["value"]
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache."""
        # Calculate expiration time
        expires_at = None
        if ttl:
            expires_at = time.time() + ttl
        
        # Estimate size
        try:
            value_size = len(pickle.dumps(value))
        except Exception:
            value_size = 1024  # Default estimate
        
        # Check if we need to evict items
        await self._ensure_space(value_size)
        
        # Store the value
        self._cache[key] = {
            "value": value,
            "created_at": time.time(),
            "accessed_at": time.time(),
            "expires_at": expires_at,
            "size": value_size,
        }
        
        self._current_size += value_size
    
    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        if key in self._cache:
            entry = self._cache.pop(key)
            self._current_size -= entry["size"]
            return True
        return False
    
    async def clear(self) -> None:
        """Clear all values from the cache."""
        self._cache.clear()
        self._current_size = 0
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        
        # Check if expired
        if entry["expires_at"] and time.time() > entry["expires_at"]:
            await self.delete(key)
            return False
        
        return True
    
    async def _ensure_space(self, needed_size: int) -> None:
        """Ensure there's enough space in the cache."""
        if self._current_size + needed_size <= self.config.max_memory_size:
            return
        
        # Sort by access time (LRU eviction)
        items = list(self._cache.items())
        items.sort(key=lambda x: x[1]["accessed_at"])
        
        # Evict items until we have enough space
        for key, entry in items:
            if self._current_size + needed_size <= self.config.max_memory_size:
                break
            
            await self.delete(key)
            logger.debug(f"Evicted cache entry: {key}")


class FileCacheBackend(CacheBackend):
    """File-based cache backend."""
    
    def __init__(self, config: CacheConfig):
        """Initialize the file cache backend."""
        self.config = config
        self.cache_dir = config.file_cache_dir
        
        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_file_path(self, key: str) -> str:
        """Get the file path for a cache key."""
        # Hash the key to create a safe filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache."""
        file_path = self._get_file_path(key)
        
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
            
            # Check if expired
            if data["expires_at"] and time.time() > data["expires_at"]:
                await self.delete(key)
                return None
            
            return data["value"]
        
        except Exception as e:
            logger.warning(f"Failed to read cache file {file_path}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache."""
        file_path = self._get_file_path(key)
        
        # Calculate expiration time
        expires_at = None
        if ttl:
            expires_at = time.time() + ttl
        
        data = {
            "value": value,
            "created_at": time.time(),
            "expires_at": expires_at,
        }
        
        try:
            with open(file_path, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            logger.error(f"Failed to write cache file {file_path}: {e}")
            raise CacheError(f"Failed to write to cache: {e}")
    
    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        file_path = self._get_file_path(key)
        
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                return True
            except Exception as e:
                logger.warning(f"Failed to delete cache file {file_path}: {e}")
        
        return False
    
    async def clear(self) -> None:
        """Clear all values from the cache."""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".cache"):
                    file_path = os.path.join(self.cache_dir, filename)
                    os.remove(file_path)
        except Exception as e:
            logger.error(f"Failed to clear cache directory: {e}")
            raise CacheError(f"Failed to clear cache: {e}")
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in the cache."""
        file_path = self._get_file_path(key)
        
        if not os.path.exists(file_path):
            return False
        
        # Check if expired
        try:
            with open(file_path, "rb") as f:
                data = pickle.load(f)
            
            if data["expires_at"] and time.time() > data["expires_at"]:
                await self.delete(key)
                return False
            
            return True
        
        except Exception:
            return False


class CacheManager:
    """Manages caching for autogenlib."""
    
    def __init__(self, config: AutogenConfig):
        """Initialize the cache manager."""
        self.config = config
        self.cache_config = CacheConfig()
        
        # Initialize backend
        if self.cache_config.backend == "file":
            self.backend = FileCacheBackend(self.cache_config)
        else:
            self.backend = MemoryCacheBackend(self.cache_config)
        
        logger.info(f"CacheManager initialized with {self.cache_config.backend} backend")
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Generate a cache key from data."""
        # Convert data to a stable string representation
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)
        
        # Create hash
        key_hash = hashlib.sha256(data_str.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    async def get_codebase_analysis(self, codebase_path: str) -> Optional[Any]:
        """Get cached codebase analysis."""
        if not self.config.cache_enabled:
            return None
        
        key = self._generate_key("codebase_analysis", codebase_path)
        return await self.backend.get(key)
    
    async def set_codebase_analysis(self, codebase_path: str, analysis: Any) -> None:
        """Cache codebase analysis."""
        if not self.config.cache_enabled:
            return
        
        key = self._generate_key("codebase_analysis", codebase_path)
        await self.backend.set(key, analysis, self.config.cache_ttl)
    
    async def get_enhanced_prompt(self, prompt: str, context_data: Any) -> Optional[str]:
        """Get cached enhanced prompt."""
        if not self.config.cache_enabled:
            return None
        
        key = self._generate_key("enhanced_prompt", {"prompt": prompt, "context": context_data})
        return await self.backend.get(key)
    
    async def set_enhanced_prompt(self, prompt: str, context_data: Any, enhanced_prompt: str) -> None:
        """Cache enhanced prompt."""
        if not self.config.cache_enabled:
            return
        
        key = self._generate_key("enhanced_prompt", {"prompt": prompt, "context": context_data})
        await self.backend.set(key, enhanced_prompt, self.config.cache_ttl)
    
    async def get_task_result(self, task_request: Any) -> Optional[Any]:
        """Get cached task result."""
        if not self.config.cache_enabled:
            return None
        
        key = self._generate_key("task_result", task_request)
        return await self.backend.get(key)
    
    async def set_task_result(self, task_request: Any, result: Any) -> None:
        """Cache task result."""
        if not self.config.cache_enabled:
            return
        
        key = self._generate_key("task_result", task_request)
        await self.backend.set(key, result, self.config.cache_ttl)
    
    async def clear_all(self) -> None:
        """Clear all cached data."""
        await self.backend.clear()
        logger.info("All cache data cleared")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "backend": self.cache_config.backend,
            "enabled": self.config.cache_enabled,
            "ttl": self.config.cache_ttl,
        }


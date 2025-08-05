"""Caching system for generated code."""

import os
import json
import hashlib
from typing import Optional, Dict, Any
from pathlib import Path

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class CodeCache:
    """Simple file-based cache for generated code."""
    
    def __init__(self, enabled: bool = False, cache_dir: Optional[str] = None):
        """Initialize the cache.
        
        Args:
            enabled: Whether caching is enabled
            cache_dir: Directory to store cache files (defaults to ~/.autogenlib_cache)
        """
        self.enabled = enabled
        
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path.home() / ".autogenlib_cache"
        
        if self.enabled:
            self.cache_dir.mkdir(exist_ok=True)
            logger.debug(f"Initialized code cache at {self.cache_dir}")
    
    def _get_cache_key(self, fullname: str) -> str:
        """Generate a cache key for a module name."""
        # Use a hash to avoid filesystem issues with special characters
        return hashlib.md5(fullname.encode()).hexdigest()
    
    def _get_cache_path(self, fullname: str) -> Path:
        """Get the cache file path for a module."""
        key = self._get_cache_key(fullname)
        return self.cache_dir / f"{key}.json"
    
    def get(self, fullname: str) -> Optional[str]:
        """Get cached code for a module.
        
        Args:
            fullname: Full module name
            
        Returns:
            Cached code or None if not found/disabled
        """
        if not self.enabled:
            return None
        
        try:
            cache_path = self._get_cache_path(fullname)
            
            if not cache_path.exists():
                return None
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate cache entry
            if data.get("fullname") != fullname:
                logger.warning(f"Cache key mismatch for {fullname}")
                return None
            
            code = data.get("code")
            if code:
                logger.debug(f"Cache hit for {fullname}")
                return code
            
        except Exception as e:
            logger.warning(f"Failed to read cache for {fullname}: {e}")
        
        return None
    
    def set(self, fullname: str, code: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Cache code for a module.
        
        Args:
            fullname: Full module name
            code: Generated code to cache
            metadata: Optional metadata to store with the code
        """
        if not self.enabled:
            return
        
        try:
            cache_path = self._get_cache_path(fullname)
            
            data = {
                "fullname": fullname,
                "code": code,
                "metadata": metadata or {},
                "timestamp": __import__("time").time()
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"Cached code for {fullname}")
            
        except Exception as e:
            logger.warning(f"Failed to cache code for {fullname}: {e}")
    
    def clear(self) -> None:
        """Clear all cached code."""
        if not self.enabled:
            return
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cleared code cache")
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")
    
    def list_cached(self) -> list[str]:
        """List all cached module names.
        
        Returns:
            List of cached module names
        """
        if not self.enabled:
            return []
        
        cached = []
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    fullname = data.get("fullname")
                    if fullname:
                        cached.append(fullname)
                except Exception as e:
                    logger.debug(f"Failed to read cache file {cache_file}: {e}")
        except Exception as e:
            logger.warning(f"Failed to list cached modules: {e}")
        
        return cached
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        info = {
            "enabled": self.enabled,
            "cache_dir": str(self.cache_dir),
            "cached_modules": 0,
            "total_size": 0
        }
        
        if not self.enabled:
            return info
        
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            info["cached_modules"] = len(cache_files)
            
            total_size = 0
            for cache_file in cache_files:
                total_size += cache_file.stat().st_size
            
            info["total_size"] = total_size
            info["total_size_mb"] = round(total_size / (1024 * 1024), 2)
            
        except Exception as e:
            logger.warning(f"Failed to get cache info: {e}")
        
        return info


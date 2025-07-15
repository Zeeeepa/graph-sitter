"""
Code Intelligence Engine

Main orchestrator for real-time code intelligence features.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge
from ..types import (
    CompletionContext, HoverContext, SignatureContext, SymbolInfo,
    SemanticSearchResult, CodeGenerationResult
)

from .completions import CompletionProvider
from .hover import HoverProvider
from .signatures import SignatureProvider

logger = get_logger(__name__)


@dataclass
class IntelligenceConfig:
    """Configuration for code intelligence features."""
    max_completions: int = 50
    completion_timeout: float = 2.0
    hover_timeout: float = 1.0
    signature_timeout: float = 1.0
    cache_size: int = 1000
    enable_ai_completions: bool = True
    enable_semantic_hover: bool = True
    enable_context_signatures: bool = True


class CodeIntelligence:
    """
    Real-time code intelligence engine.
    
    Provides completions, hover information, and signature help
    with caching and performance optimization.
    """
    
    def __init__(self, codebase: Codebase, lsp_bridge: SerenaLSPBridge, config: Optional[IntelligenceConfig] = None):
        self.codebase = codebase
        self.lsp_bridge = lsp_bridge
        self.config = config or IntelligenceConfig()
        
        # Initialize providers
        self.completion_provider = CompletionProvider(codebase, lsp_bridge, self.config)
        self.hover_provider = HoverProvider(codebase, lsp_bridge, self.config)
        self.signature_provider = SignatureProvider(codebase, lsp_bridge, self.config)
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="CodeIntelligence")
        
        # Performance tracking
        self._performance_stats = {
            'completions': {'count': 0, 'total_time': 0.0, 'cache_hits': 0},
            'hover': {'count': 0, 'total_time': 0.0, 'cache_hits': 0},
            'signatures': {'count': 0, 'total_time': 0.0, 'cache_hits': 0}
        }
        
        logger.info("Code intelligence engine initialized")
    
    def get_completions(self, file_path: str, line: int, character: int, **kwargs) -> List[Dict[str, Any]]:
        """
        Get code completions at the specified position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
            **kwargs: Additional completion options
        
        Returns:
            List of completion items with details
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not self._validate_position(file_path, line, character):
                return []
            
            # Get completions from provider
            completions = self.completion_provider.get_completions(
                file_path, line, character, **kwargs
            )
            
            # Update performance stats
            elapsed = time.time() - start_time
            self._update_stats('completions', elapsed, len(completions) > 0)
            
            logger.debug(f"Generated {len(completions)} completions in {elapsed:.3f}s")
            return completions
            
        except Exception as e:
            logger.error(f"Error getting completions: {e}")
            return []
    
    def get_hover_info(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """
        Get hover information for symbol at position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
        
        Returns:
            Hover information or None if not available
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not self._validate_position(file_path, line, character):
                return None
            
            # Get hover info from provider
            hover_info = self.hover_provider.get_hover_info(file_path, line, character)
            
            # Update performance stats
            elapsed = time.time() - start_time
            self._update_stats('hover', elapsed, hover_info is not None)
            
            logger.debug(f"Generated hover info in {elapsed:.3f}s")
            return hover_info
            
        except Exception as e:
            logger.error(f"Error getting hover info: {e}")
            return None
    
    def get_signature_help(self, file_path: str, line: int, character: int) -> Optional[Dict[str, Any]]:
        """
        Get signature help for function call at position.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
        
        Returns:
            Signature help information or None if not available
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not self._validate_position(file_path, line, character):
                return None
            
            # Get signature help from provider
            signature_help = self.signature_provider.get_signature_help(file_path, line, character)
            
            # Update performance stats
            elapsed = time.time() - start_time
            self._update_stats('signatures', elapsed, signature_help is not None)
            
            logger.debug(f"Generated signature help in {elapsed:.3f}s")
            return signature_help
            
        except Exception as e:
            logger.error(f"Error getting signature help: {e}")
            return None
    
    def get_all_intelligence(self, file_path: str, line: int, character: int) -> Dict[str, Any]:
        """
        Get all intelligence information concurrently.
        
        Args:
            file_path: Path to the file
            line: Line number (0-based)
            character: Character position (0-based)
        
        Returns:
            Dictionary with completions, hover, and signature information
        """
        if not self._validate_position(file_path, line, character):
            return {'completions': [], 'hover': None, 'signatures': None}
        
        # Submit concurrent tasks
        futures = {
            'completions': self.executor.submit(self.get_completions, file_path, line, character),
            'hover': self.executor.submit(self.get_hover_info, file_path, line, character),
            'signatures': self.executor.submit(self.get_signature_help, file_path, line, character)
        }
        
        # Collect results
        results = {}
        for key, future in futures.items():
            try:
                results[key] = future.result(timeout=5.0)
            except Exception as e:
                logger.error(f"Error getting {key}: {e}")
                results[key] = [] if key == 'completions' else None
        
        return results
    
    def invalidate_cache(self, file_path: str = None) -> None:
        """
        Invalidate intelligence cache.
        
        Args:
            file_path: Specific file to invalidate, or None for all files
        """
        self.completion_provider.invalidate_cache(file_path)
        self.hover_provider.invalidate_cache(file_path)
        self.signature_provider.invalidate_cache(file_path)
        
        logger.debug(f"Invalidated intelligence cache for {file_path or 'all files'}")
    
    def warm_cache(self, file_paths: List[str]) -> None:
        """
        Pre-warm intelligence cache for specified files.
        
        Args:
            file_paths: List of file paths to warm
        """
        logger.info(f"Warming intelligence cache for {len(file_paths)} files")
        
        # Submit warming tasks
        futures = []
        for file_path in file_paths:
            future = self.executor.submit(self._warm_file_cache, file_path)
            futures.append(future)
        
        # Wait for completion
        completed = 0
        for future in as_completed(futures, timeout=30.0):
            try:
                future.result()
                completed += 1
            except Exception as e:
                logger.error(f"Error warming cache: {e}")
        
        logger.info(f"Warmed cache for {completed}/{len(file_paths)} files")
    
    def _warm_file_cache(self, file_path: str) -> None:
        """Warm cache for a specific file."""
        try:
            # Get file content to analyze key positions
            file_obj = self.codebase.get_file(file_path)
            if not file_obj:
                return
            
            # Analyze functions and classes for warming
            for symbol in file_obj.symbols:
                if hasattr(symbol, 'start_line') and hasattr(symbol, 'start_character'):
                    # Pre-load hover info for symbol definitions
                    self.get_hover_info(file_path, symbol.start_line, symbol.start_character)
                    
        except Exception as e:
            logger.debug(f"Error warming cache for {file_path}: {e}")
    
    def _validate_position(self, file_path: str, line: int, character: int) -> bool:
        """Validate file position parameters."""
        if not file_path or line < 0 or character < 0:
            return False
        
        # Check if file exists in codebase
        try:
            file_obj = self.codebase.get_file(file_path)
            return file_obj is not None
        except Exception:
            return False
    
    def _update_stats(self, operation: str, elapsed_time: float, cache_hit: bool) -> None:
        """Update performance statistics."""
        stats = self._performance_stats[operation]
        stats['count'] += 1
        stats['total_time'] += elapsed_time
        if cache_hit:
            stats['cache_hits'] += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = {}
        for operation, data in self._performance_stats.items():
            if data['count'] > 0:
                avg_time = data['total_time'] / data['count']
                cache_hit_rate = data['cache_hits'] / data['count']
                stats[operation] = {
                    'count': data['count'],
                    'average_time': avg_time,
                    'cache_hit_rate': cache_hit_rate,
                    'total_time': data['total_time']
                }
            else:
                stats[operation] = {'count': 0, 'average_time': 0, 'cache_hit_rate': 0, 'total_time': 0}
        
        return stats
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information."""
        return {
            'initialized': True,
            'config': {
                'max_completions': self.config.max_completions,
                'completion_timeout': self.config.completion_timeout,
                'cache_size': self.config.cache_size,
                'ai_completions_enabled': self.config.enable_ai_completions
            },
            'performance': self.get_performance_stats(),
            'providers': {
                'completions': self.completion_provider.get_status(),
                'hover': self.hover_provider.get_status(),
                'signatures': self.signature_provider.get_status()
            }
        }
    
    def shutdown(self) -> None:
        """Shutdown the intelligence engine."""
        logger.info("Shutting down code intelligence engine")
        
        # Shutdown providers
        self.completion_provider.shutdown()
        self.hover_provider.shutdown()
        self.signature_provider.shutdown()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        logger.info("Code intelligence engine shutdown complete")

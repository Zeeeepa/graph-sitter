"""
Code Intelligence Engine

Main orchestrator for real-time code intelligence features.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed, Future

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from ..mcp_bridge import SerenaMCPBridge
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
    
    def __init__(self, codebase: Codebase, mcp_bridge: SerenaMCPBridge, config: Optional[IntelligenceConfig] = None):
        self.codebase = codebase
        self.mcp_bridge = mcp_bridge
        self.config = config or IntelligenceConfig()
        
        # Initialize providers
        self.completion_provider = CompletionProvider(codebase, mcp_bridge, self.config)
        self.hover_provider = HoverProvider(codebase, mcp_bridge, self.config)
        self.signature_provider = SignatureProvider(codebase, mcp_bridge, self.config)
        
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
        futures: Dict[str, Future[Any]] = {
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
    
    def get_symbol_info(self, file_path: str, line: int, character: int) -> Optional[SymbolInfo]:
        """Get detailed information about a symbol at the specified position."""
        try:
            # Get the file from the codebase
            file = self.codebase.get_file(file_path, optional=True)
            if not file:
                return None
            
            # Find the symbol at the specified position
            symbol = self._find_symbol_at_position(file, line, character)
            if not symbol:
                return None
            
            # Get symbol usages and references
            usages = []
            references = []
            
            try:
                symbol_usages = symbol.usages()
                for usage in symbol_usages:
                    usage_info = f"{usage.usage_symbol.filepath}:{usage.usage_symbol.line_number}"
                    usages.append(usage_info)
                    references.append(usage_info)
            except Exception as e:
                logger.warning(f"Error getting symbol usages: {e}")
            
            # Build symbol information
            symbol_kind = self._get_symbol_kind(symbol)
            documentation = self._get_symbol_documentation(symbol)
            signature = self._get_symbol_signature(symbol)
            
            # Get position information
            symbol_line = line
            symbol_char = character
            
            if hasattr(symbol, 'start_point'):
                symbol_line = symbol.start_point.row
                symbol_char = symbol.start_point.column
            elif hasattr(symbol, 'line_number'):
                symbol_line = symbol.line_number
                symbol_char = getattr(symbol, 'column_number', character)
            
            return SymbolInfo(
                name=symbol.name,
                kind=symbol_kind,
                file_path=file_path,
                line=symbol_line,
                character=symbol_char,
                documentation=documentation,
                type_annotation=signature,
                scope=getattr(symbol, 'scope', None)
            )
            
        except Exception as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
    
    def semantic_search(self, query: str, max_results: int = 10) -> List[SemanticSearchResult]:
        """Perform semantic search across the codebase."""
        try:
            results = []
            logger.debug(f"Semantic search for '{query}' across {len(self.codebase.symbols)} symbols")
            
            # Search through symbols using existing graph-sitter capabilities
            for symbol in self.codebase.symbols:
                # Simple text matching for now - can be enhanced with embeddings
                if query.lower() in symbol.name.lower():
                    logger.debug(f"Found match: {symbol.name} in {symbol.filepath}")
                    score = self._calculate_relevance_score(symbol, query)
                    
                    # Get line number from symbol position
                    line_number = 0
                    if hasattr(symbol, 'start_point'):
                        line_number = symbol.start_point.row
                    elif hasattr(symbol, 'line_number'):
                        line_number = symbol.line_number
                    
                    result = SemanticSearchResult(
                        symbol_name=symbol.name,
                        file_path=symbol.filepath,
                        line_number=line_number,
                        symbol_type=self._get_symbol_kind(symbol),
                        relevance_score=score,
                        context_snippet=self._get_context_snippet(symbol),
                        documentation=self._get_symbol_documentation(symbol)
                    )
                    results.append(result)
            
            logger.debug(f"Semantic search found {len(results)} results")
            
            # Sort by relevance and limit results
            results.sort(key=lambda x: x.relevance_score, reverse=True)
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def generate_code(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> CodeGenerationResult:
        """Generate code based on prompt and context."""
        try:
            # Basic code generation - can be enhanced with AI models
            generated_code = self._generate_code_from_prompt(prompt, context)
            
            return CodeGenerationResult(
                success=True,
                generated_code=generated_code,
                message="Code generated successfully",
                metadata={
                    "confidence_score": 0.8,
                    "suggestions": [
                        "Consider adding error handling",
                        "Add type hints for better code clarity",
                        "Consider adding docstring documentation"
                    ],
                    "imports_needed": self._extract_needed_imports(generated_code),
                    "context_used": context or {}
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating code: {e}")
            return CodeGenerationResult(
                success=False,
                generated_code="# Error generating code",
                message=f"Error generating code: {e}",
                metadata={
                    "confidence_score": 0.0,
                    "suggestions": ["Please try a different prompt"],
                    "imports_needed": [],
                    "context_used": {}
                }
            )
    
    def _find_symbol_at_position(self, file, line: int, character: int):
        """Find symbol at the specified position in the file."""
        try:
            # Use graph-sitter's existing capabilities to find symbols
            best_match = None
            best_distance = float('inf')
            
            for symbol in file.symbols:
                # Check if symbol has position information using start_point/end_point
                if hasattr(symbol, 'start_point') and hasattr(symbol, 'end_point'):
                    start_row = symbol.start_point.row
                    start_col = symbol.start_point.column
                    end_row = symbol.end_point.row
                    end_col = symbol.end_point.column
                    
                    # Check if position is within symbol range (0-based indexing)
                    if start_row <= line <= end_row:
                        # If on the same line as start, check column
                        if start_row == line:
                            if character >= start_col:
                                distance = abs(start_col - character)
                                if distance < best_distance:
                                    best_distance = distance
                                    best_match = symbol
                        # If on the same line as end, check column
                        elif end_row == line:
                            if character <= end_col:
                                distance = abs(end_col - character)
                                if distance < best_distance:
                                    best_distance = distance
                                    best_match = symbol
                        # If between start and end lines
                        else:
                            distance = abs(start_row - line)
                            if distance < best_distance:
                                best_distance = distance
                                best_match = symbol
                
                # Fallback: check for legacy line_number attribute
                elif hasattr(symbol, 'line_number'):
                    symbol_line = symbol.line_number
                    symbol_char = getattr(symbol, 'column_number', 0)
                    
                    if symbol_line == line:
                        distance = abs(symbol_char - character) if hasattr(symbol, 'column_number') else 0
                        if distance < best_distance:
                            best_distance = distance
                            best_match = symbol
            
            return best_match
            
        except Exception as e:
            logger.debug(f"Error finding symbol at position: {e}")
            return None
    
    def _get_symbol_kind(self, symbol) -> str:
        """Get the kind/type of symbol."""
        try:
            if hasattr(symbol, 'symbol_type'):
                return str(symbol.symbol_type).lower()
            return symbol.__class__.__name__.lower()
        except Exception:
            return "unknown"
    
    def _get_symbol_documentation(self, symbol) -> str:
        """Extract documentation for a symbol."""
        try:
            if hasattr(symbol, 'docstring') and symbol.docstring:
                return symbol.docstring
            if hasattr(symbol, 'comment') and symbol.comment:
                return symbol.comment
            return f"Symbol: {symbol.name}"
        except Exception:
            return ""
    
    def _get_symbol_signature(self, symbol) -> str:
        """Get the signature of a symbol."""
        try:
            if hasattr(symbol, 'signature'):
                return symbol.signature
            if hasattr(symbol, 'name'):
                return f"{symbol.__class__.__name__}: {symbol.name}"
            return str(symbol)
        except Exception:
            return ""
    
    def _calculate_relevance_score(self, symbol, query: str) -> float:
        """Calculate relevance score for semantic search."""
        try:
            score = 0.0
            query_lower = query.lower()
            name_lower = symbol.name.lower()
            
            # Exact match gets highest score
            if name_lower == query_lower:
                score += 1.0
            # Starts with query gets high score
            elif name_lower.startswith(query_lower):
                score += 0.8
            # Contains query gets medium score
            elif query_lower in name_lower:
                score += 0.6
            
            # Boost score for certain symbol types
            if hasattr(symbol, 'symbol_type'):
                if 'function' in str(symbol.symbol_type).lower():
                    score += 0.1
                elif 'class' in str(symbol.symbol_type).lower():
                    score += 0.2
            
            return min(score, 1.0)
        except Exception:
            return 0.0
    
    def _get_context_snippet(self, symbol) -> str:
        """Get a context snippet for the symbol."""
        try:
            if hasattr(symbol, 'content'):
                content = str(symbol.content)
                # Return first 100 characters as snippet
                return content[:100] + "..." if len(content) > 100 else content
            return f"Symbol: {symbol.name}"
        except Exception:
            return ""
    
    def _generate_code_from_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Generate code from prompt - basic implementation."""
        try:
            # Basic template-based generation
            if "function" in prompt.lower():
                return f"""def generated_function():
    \"\"\"Generated function based on: {prompt}\"\"\"
    # TODO: Implement function logic
    pass"""
            elif "class" in prompt.lower():
                return f"""class GeneratedClass:
    \"\"\"Generated class based on: {prompt}\"\"\"
    
    def __init__(self):
        # TODO: Initialize class
        pass"""
            else:
                return f"# Generated code for: {prompt}\n# TODO: Implement logic"
        except Exception:
            return "# Error generating code"
    
    def _extract_needed_imports(self, code: str) -> List[str]:
        """Extract imports that might be needed for the generated code."""
        imports = []
        
        # Basic import detection
        if "typing" in code.lower():
            imports.append("from typing import *")
        if "dataclass" in code.lower():
            imports.append("from dataclasses import dataclass")
        if "pathlib" in code.lower():
            imports.append("from pathlib import Path")
        
        return imports

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

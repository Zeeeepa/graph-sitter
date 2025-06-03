"""
Context enhancement pipeline for intelligent codebase context integration.

This module provides the main pipeline for enhancing code generation prompts
with relevant codebase context using graph_sitter analysis functions.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

# Import graph_sitter analysis functions
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.symbol import Symbol

from .relevance_scorer import RelevanceScorer
from .context_cache import ContextCache
from .token_manager import TokenManager


logger = logging.getLogger(__name__)


@dataclass
class ContextItem:
    """Container for a context item with metadata."""
    content: str
    item_type: str  # 'codebase', 'file', 'class', 'function', 'symbol'
    relevance_score: float
    token_count: int
    source_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ContextEnhancementResult:
    """Result of context enhancement process."""
    enhanced_prompt: str
    original_prompt: str
    context_items: List[ContextItem]
    total_tokens: int
    enhancement_time: float
    cache_hit: bool = False


class ContextPipeline:
    """
    Intelligent context enhancement pipeline.
    
    This pipeline analyzes code generation prompts and enhances them with
    relevant codebase context using graph_sitter analysis functions.
    
    Features:
    - Intelligent context selection based on relevance scoring
    - Token limit management to stay within API constraints
    - Caching for performance optimization
    - Multiple context types (codebase, file, class, function, symbol)
    """
    
    def __init__(self,
                 max_tokens: int = 8000,
                 cache_ttl: int = 3600,
                 enable_caching: bool = True,
                 relevance_threshold: float = 0.3):
        """
        Initialize context enhancement pipeline.
        
        Args:
            max_tokens: Maximum tokens to include in context
            cache_ttl: Cache time-to-live in seconds
            enable_caching: Whether to enable context caching
            relevance_threshold: Minimum relevance score for inclusion
        """
        self.max_tokens = max_tokens
        self.cache_ttl = cache_ttl
        self.enable_caching = enable_caching
        self.relevance_threshold = relevance_threshold
        
        # Initialize components
        self.relevance_scorer = RelevanceScorer()
        self.token_manager = TokenManager()
        self.context_cache: Optional[ContextCache] = None
        
        if enable_caching:
            self.context_cache = ContextCache(ttl=cache_ttl)
        
        # Performance metrics
        self.metrics = {
            "total_enhancements": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "average_enhancement_time": 0.0,
            "average_context_items": 0.0,
            "average_tokens_used": 0.0
        }
        
        self._enhancement_times: List[float] = []
        self._context_counts: List[int] = []
        self._token_counts: List[int] = []
    
    async def initialize(self) -> None:
        """Initialize the context pipeline."""
        await self.relevance_scorer.initialize()
        
        if self.context_cache:
            await self.context_cache.initialize()
        
        logger.info("Context pipeline initialized")
    
    async def enhance_prompt(self,
                           prompt: str,
                           codebase: Codebase,
                           additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Enhance a prompt with relevant codebase context.
        
        Args:
            prompt: Original prompt to enhance
            codebase: Codebase to extract context from
            additional_context: Optional additional context information
            
        Returns:
            Enhanced prompt with context
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = self._generate_cache_key(prompt, codebase, additional_context)
            
            if self.context_cache:
                cached_result = await self.context_cache.get(cache_key)
                if cached_result:
                    self._record_enhancement(
                        enhancement_time=time.time() - start_time,
                        context_count=len(cached_result.context_items),
                        token_count=cached_result.total_tokens,
                        cache_hit=True
                    )
                    return cached_result.enhanced_prompt
            
            # Generate context enhancement
            result = await self._generate_enhancement(prompt, codebase, additional_context)
            
            # Cache the result
            if self.context_cache:
                await self.context_cache.set(cache_key, result)
            
            # Record metrics
            self._record_enhancement(
                enhancement_time=result.enhancement_time,
                context_count=len(result.context_items),
                token_count=result.total_tokens,
                cache_hit=False
            )
            
            return result.enhanced_prompt
            
        except Exception as e:
            logger.error(f"Failed to enhance prompt: {e}")
            # Return original prompt on error
            return prompt
    
    async def get_codebase_context(self, codebase: Codebase) -> Dict[str, Any]:
        """
        Get comprehensive codebase context information.
        
        Args:
            codebase: Codebase to analyze
            
        Returns:
            Dictionary containing codebase context
        """
        try:
            # Get basic codebase summary
            summary = get_codebase_summary(codebase)
            
            # Get detailed information
            files = list(codebase.files)
            functions = list(codebase.functions)
            classes = list(codebase.classes)
            symbols = list(codebase.symbols)
            
            # Calculate complexity metrics
            total_lines = sum(
                len(file.content.split('\n')) if hasattr(file, 'content') else 0
                for file in files
            )
            
            # Get language distribution
            language_stats = {}
            for file in files:
                if hasattr(file, 'language'):
                    lang = file.language
                    language_stats[lang] = language_stats.get(lang, 0) + 1
            
            # Get dependency information
            imports = list(codebase.imports)
            external_modules = list(codebase.external_modules)
            
            return {
                "summary": summary,
                "statistics": {
                    "total_files": len(files),
                    "total_functions": len(functions),
                    "total_classes": len(classes),
                    "total_symbols": len(symbols),
                    "total_lines": total_lines,
                    "total_imports": len(imports),
                    "external_modules": len(external_modules)
                },
                "languages": language_stats,
                "complexity": {
                    "average_functions_per_file": len(functions) / max(len(files), 1),
                    "average_classes_per_file": len(classes) / max(len(files), 1),
                    "average_lines_per_file": total_lines / max(len(files), 1)
                },
                "top_files": [
                    {
                        "name": file.name,
                        "functions": len(file.functions),
                        "classes": len(file.classes),
                        "imports": len(file.imports)
                    }
                    for file in sorted(files, key=lambda f: len(f.functions) + len(f.classes), reverse=True)[:10]
                ],
                "top_classes": [
                    {
                        "name": cls.name,
                        "methods": len(cls.methods),
                        "attributes": len(cls.attributes),
                        "file": cls.file.name if hasattr(cls, 'file') else None
                    }
                    for cls in sorted(classes, key=lambda c: len(c.methods), reverse=True)[:10]
                ],
                "top_functions": [
                    {
                        "name": func.name,
                        "parameters": len(func.parameters),
                        "calls": len(func.function_calls),
                        "file": func.file.name if hasattr(func, 'file') else None
                    }
                    for func in sorted(functions, key=lambda f: len(f.function_calls), reverse=True)[:10]
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get codebase context: {e}")
            return {"error": str(e)}
    
    async def _generate_enhancement(self,
                                  prompt: str,
                                  codebase: Codebase,
                                  additional_context: Optional[Dict[str, Any]]) -> ContextEnhancementResult:
        """Generate context enhancement for a prompt."""
        start_time = time.time()
        
        # Extract relevant context items
        context_items = await self._extract_context_items(prompt, codebase, additional_context)
        
        # Score and rank context items
        scored_items = await self._score_context_items(prompt, context_items)
        
        # Select optimal context within token limits
        selected_items = await self._select_optimal_context(scored_items)
        
        # Build enhanced prompt
        enhanced_prompt = await self._build_enhanced_prompt(prompt, selected_items)
        
        total_tokens = sum(item.token_count for item in selected_items)
        enhancement_time = time.time() - start_time
        
        return ContextEnhancementResult(
            enhanced_prompt=enhanced_prompt,
            original_prompt=prompt,
            context_items=selected_items,
            total_tokens=total_tokens,
            enhancement_time=enhancement_time
        )
    
    async def _extract_context_items(self,
                                   prompt: str,
                                   codebase: Codebase,
                                   additional_context: Optional[Dict[str, Any]]) -> List[ContextItem]:
        """Extract potential context items from codebase."""
        context_items = []
        
        try:
            # Add codebase summary
            codebase_summary = get_codebase_summary(codebase)
            context_items.append(ContextItem(
                content=codebase_summary,
                item_type="codebase",
                relevance_score=0.0,  # Will be scored later
                token_count=self.token_manager.count_tokens(codebase_summary),
                metadata={"type": "summary"}
            ))
            
            # Add file summaries for relevant files
            files = list(codebase.files)
            for file in files[:20]:  # Limit to prevent excessive processing
                try:
                    file_summary = get_file_summary(file)
                    context_items.append(ContextItem(
                        content=file_summary,
                        item_type="file",
                        relevance_score=0.0,
                        token_count=self.token_manager.count_tokens(file_summary),
                        source_path=file.name,
                        metadata={"file_name": file.name}
                    ))
                except Exception as e:
                    logger.warning(f"Failed to get summary for file {file.name}: {e}")
            
            # Add class summaries for relevant classes
            classes = list(codebase.classes)
            for cls in classes[:15]:  # Limit to prevent excessive processing
                try:
                    class_summary = get_class_summary(cls)
                    context_items.append(ContextItem(
                        content=class_summary,
                        item_type="class",
                        relevance_score=0.0,
                        token_count=self.token_manager.count_tokens(class_summary),
                        source_path=getattr(cls.file, 'name', None) if hasattr(cls, 'file') else None,
                        metadata={"class_name": cls.name}
                    ))
                except Exception as e:
                    logger.warning(f"Failed to get summary for class {cls.name}: {e}")
            
            # Add function summaries for relevant functions
            functions = list(codebase.functions)
            for func in functions[:15]:  # Limit to prevent excessive processing
                try:
                    function_summary = get_function_summary(func)
                    context_items.append(ContextItem(
                        content=function_summary,
                        item_type="function",
                        relevance_score=0.0,
                        token_count=self.token_manager.count_tokens(function_summary),
                        source_path=getattr(func.file, 'name', None) if hasattr(func, 'file') else None,
                        metadata={"function_name": func.name}
                    ))
                except Exception as e:
                    logger.warning(f"Failed to get summary for function {func.name}: {e}")
            
            # Add additional context if provided
            if additional_context:
                for key, value in additional_context.items():
                    if isinstance(value, str):
                        context_items.append(ContextItem(
                            content=f"{key}: {value}",
                            item_type="additional",
                            relevance_score=0.0,
                            token_count=self.token_manager.count_tokens(f"{key}: {value}"),
                            metadata={"context_key": key}
                        ))
            
        except Exception as e:
            logger.error(f"Failed to extract context items: {e}")
        
        return context_items
    
    async def _score_context_items(self,
                                 prompt: str,
                                 context_items: List[ContextItem]) -> List[ContextItem]:
        """Score context items for relevance to the prompt."""
        scored_items = []
        
        for item in context_items:
            try:
                # Calculate relevance score
                relevance_score = await self.relevance_scorer.score_relevance(
                    prompt, item.content, item.item_type
                )
                
                # Create new item with score
                scored_item = ContextItem(
                    content=item.content,
                    item_type=item.item_type,
                    relevance_score=relevance_score,
                    token_count=item.token_count,
                    source_path=item.source_path,
                    metadata=item.metadata
                )
                
                # Only include items above threshold
                if relevance_score >= self.relevance_threshold:
                    scored_items.append(scored_item)
                
            except Exception as e:
                logger.warning(f"Failed to score context item: {e}")
        
        # Sort by relevance score (descending)
        scored_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return scored_items
    
    async def _select_optimal_context(self, scored_items: List[ContextItem]) -> List[ContextItem]:
        """Select optimal context items within token limits."""
        selected_items = []
        total_tokens = 0
        
        # Reserve tokens for prompt and response
        available_tokens = self.max_tokens - 1000  # Reserve 1000 tokens
        
        # Prioritize by type and relevance
        type_priorities = {
            "codebase": 1.0,
            "class": 0.9,
            "function": 0.8,
            "file": 0.7,
            "symbol": 0.6,
            "additional": 0.5
        }
        
        # Sort by weighted score (relevance * type_priority)
        weighted_items = []
        for item in scored_items:
            type_priority = type_priorities.get(item.item_type, 0.5)
            weighted_score = item.relevance_score * type_priority
            weighted_items.append((weighted_score, item))
        
        weighted_items.sort(key=lambda x: x[0], reverse=True)
        
        # Select items within token limit
        for weighted_score, item in weighted_items:
            if total_tokens + item.token_count <= available_tokens:
                selected_items.append(item)
                total_tokens += item.token_count
            else:
                # Try to include partial content if it's a large item
                if item.token_count > 500 and total_tokens < available_tokens - 100:
                    # Truncate content to fit
                    remaining_tokens = available_tokens - total_tokens
                    truncated_content = self.token_manager.truncate_to_tokens(
                        item.content, remaining_tokens - 50
                    )
                    
                    if truncated_content:
                        truncated_item = ContextItem(
                            content=truncated_content + "...",
                            item_type=item.item_type,
                            relevance_score=item.relevance_score,
                            token_count=remaining_tokens - 50,
                            source_path=item.source_path,
                            metadata={**(item.metadata or {}), "truncated": True}
                        )
                        selected_items.append(truncated_item)
                        break
        
        return selected_items
    
    async def _build_enhanced_prompt(self, prompt: str, context_items: List[ContextItem]) -> str:
        """Build enhanced prompt with context."""
        if not context_items:
            return prompt
        
        # Build context sections
        context_sections = []
        
        # Group by type
        by_type = {}
        for item in context_items:
            if item.item_type not in by_type:
                by_type[item.item_type] = []
            by_type[item.item_type].append(item)
        
        # Add codebase context first
        if "codebase" in by_type:
            context_sections.append("## Codebase Overview")
            for item in by_type["codebase"]:
                context_sections.append(item.content)
            context_sections.append("")
        
        # Add class context
        if "class" in by_type:
            context_sections.append("## Relevant Classes")
            for item in by_type["class"]:
                context_sections.append(item.content)
            context_sections.append("")
        
        # Add function context
        if "function" in by_type:
            context_sections.append("## Relevant Functions")
            for item in by_type["function"]:
                context_sections.append(item.content)
            context_sections.append("")
        
        # Add file context
        if "file" in by_type:
            context_sections.append("## Relevant Files")
            for item in by_type["file"]:
                context_sections.append(item.content)
            context_sections.append("")
        
        # Add additional context
        if "additional" in by_type:
            context_sections.append("## Additional Context")
            for item in by_type["additional"]:
                context_sections.append(item.content)
            context_sections.append("")
        
        # Combine everything
        enhanced_prompt = f"""# Code Generation Request

## Context Information
{chr(10).join(context_sections)}

## Request
{prompt}

Please use the provided context information to generate high-quality, contextually appropriate code that integrates well with the existing codebase."""
        
        return enhanced_prompt
    
    def _generate_cache_key(self,
                          prompt: str,
                          codebase: Codebase,
                          additional_context: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for context enhancement."""
        import hashlib
        
        # Create hash from prompt and codebase identifier
        content = f"{prompt}:{getattr(codebase, 'id', 'unknown')}"
        
        if additional_context:
            content += f":{str(sorted(additional_context.items()))}"
        
        return hashlib.md5(content.encode()).hexdigest()
    
    def _record_enhancement(self,
                          enhancement_time: float,
                          context_count: int,
                          token_count: int,
                          cache_hit: bool) -> None:
        """Record enhancement metrics."""
        self.metrics["total_enhancements"] += 1
        
        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1
        
        self._enhancement_times.append(enhancement_time)
        self._context_counts.append(context_count)
        self._token_counts.append(token_count)
        
        # Keep only last 1000 measurements
        if len(self._enhancement_times) > 1000:
            self._enhancement_times.pop(0)
            self._context_counts.pop(0)
            self._token_counts.pop(0)
        
        # Update averages
        if self._enhancement_times:
            self.metrics["average_enhancement_time"] = sum(self._enhancement_times) / len(self._enhancement_times)
            self.metrics["average_context_items"] = sum(self._context_counts) / len(self._context_counts)
            self.metrics["average_tokens_used"] = sum(self._token_counts) / len(self._token_counts)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get context pipeline metrics."""
        cache_hit_rate = 0.0
        if self.metrics["total_enhancements"] > 0:
            cache_hit_rate = self.metrics["cache_hits"] / self.metrics["total_enhancements"]
        
        return {
            **self.metrics,
            "cache_hit_rate": cache_hit_rate,
            "cache_enabled": self.enable_caching
        }
    
    async def shutdown(self) -> None:
        """Shutdown the context pipeline."""
        if self.context_cache:
            await self.context_cache.shutdown()
        
        logger.info("Context pipeline shutdown complete")


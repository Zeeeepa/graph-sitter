"""Context Gatherer for rich context extraction from GraphSitter analysis."""

import logging
from typing import Any, Dict, List, Union, Optional, Set
from functools import lru_cache
import time
import threading

from graph_sitter.core.file import File
from graph_sitter.core.interfaces.editable import Editable

logger = logging.getLogger(__name__)

# Cache for expensive context operations
_context_cache: Dict[str, Any] = {}
_cache_lock = threading.Lock()
_cache_ttl = 300  # 5 minutes TTL for context cache


class ContextGatherer:
    """Rich context extraction from GraphSitter analysis with performance optimizations."""
    
    def __init__(self, codebase, enable_cache: bool = True, max_context_items: int = 50):
        """Initialize with codebase reference and performance settings.
        
        Args:
            codebase: The codebase instance
            enable_cache: Whether to enable context caching
            max_context_items: Maximum items to include in context (for performance)
        """
        self.codebase = codebase
        self.enable_cache = enable_cache
        self.max_context_items = max_context_items
        self._processed_targets: Set[str] = set()  # Avoid circular references
    
    def gather_target_context(self, target: Editable, include_relationships: bool = True) -> Dict[str, Any]:
        """Gather comprehensive context for a target editable object with caching.
        
        Args:
            target: The target editable object to gather context for
            include_relationships: Whether to include relationship analysis
            
        Returns:
            Dictionary containing rich context information
        """
        # Create cache key
        cache_key = None
        if self.enable_cache:
            target_id = self._get_target_id(target)
            cache_key = f"context:{target_id}:{include_relationships}"
            
            with _cache_lock:
                if cache_key in _context_cache:
                    cached_data, timestamp = _context_cache[cache_key]
                    if time.time() - timestamp < _cache_ttl:
                        logger.debug(f"Using cached context for {target_id}")
                        return cached_data
        
        start_time = time.time()
        
        try:
            context = {
                "target_info": self._get_target_info(target),
                "static_analysis": self._get_static_analysis(target),
                "codebase_summary": self._get_codebase_summary()
            }
            
            if include_relationships:
                context["relationships"] = self._get_relationships(target)
            
            # Cache the result
            if self.enable_cache and cache_key:
                with _cache_lock:
                    _context_cache[cache_key] = (context, time.time())
            
            duration = time.time() - start_time
            logger.debug(f"Context gathering completed in {duration:.2f}s")
            
            return context
            
        except Exception as e:
            logger.error(f"Error gathering context for target: {e}")
            # Return minimal context on error
            return {
                "target_info": {"error": str(e)},
                "static_analysis": {},
                "relationships": {},
                "codebase_summary": {}
            }
    
    def _get_target_id(self, target: Editable) -> str:
        """Generate a unique identifier for a target."""
        try:
            file_path = target.file.filepath if hasattr(target, "file") else "unknown"
            name = getattr(target, "name", "unknown")
            line_start = getattr(target, "line_start", 0)
            return f"{file_path}:{name}:{line_start}"
        except Exception:
            return f"{target.__class__.__name__}:{id(target)}"

    def _get_target_info(self, target: Editable) -> Dict[str, Any]:
        """Get basic information about the target."""
        info = {
            "type": target.__class__.__name__,
            "name": getattr(target, "name", "unknown"),
            "location": {
                "file": target.file.filepath if hasattr(target, "file") else "unknown",
                "line_start": getattr(target, "line_start", None),
                "line_end": getattr(target, "line_end", None)
            },
            "source_preview": self._get_source_preview(target)
        }
        
        # Add signature for functions/methods
        if hasattr(target, "signature"):
            info["signature"] = target.signature
        
        # Add class info for methods
        if hasattr(target, "parent_class") and target.parent_class:
            info["parent_class"] = target.parent_class.name
        
        return info
    
    def _get_static_analysis(self, target: Editable) -> Dict[str, Any]:
        """Get static analysis information with performance optimizations."""
        analysis = {
            "call_sites": [],
            "dependencies": [],
            "usages": []
        }
        
        try:
            # Get call sites with context (limited for performance)
            if hasattr(target, "call_sites"):
                call_sites = list(target.call_sites)[:self.max_context_items]
                for call_site in call_sites:
                    try:
                        call_context = {
                            "location": {
                                "file": call_site.file.filepath if hasattr(call_site, "file") else "unknown",
                                "line": getattr(call_site, "line_start", None)
                            },
                            "context": self._get_surrounding_context(call_site, lines=2)  # Reduced context
                        }
                        analysis["call_sites"].append(call_context)
                    except Exception as e:
                        logger.debug(f"Error processing call site: {e}")
                        continue
            
            # Get dependencies (limited for performance)
            if hasattr(target, "dependencies"):
                dependencies = list(target.dependencies)[:self.max_context_items]
                for dep in dependencies:
                    try:
                        dep_info = {
                            "name": getattr(dep, "name", str(dep)),
                            "type": dep.__class__.__name__,
                            "location": {
                                "file": dep.file.filepath if hasattr(dep, "file") else "unknown"
                            }
                        }
                        analysis["dependencies"].append(dep_info)
                    except Exception as e:
                        logger.debug(f"Error processing dependency: {e}")
                        continue
            
            # Get usages (limited for performance)
            if hasattr(target, "usages"):
                usages = list(target.usages)[:self.max_context_items]
                for usage in usages:
                    try:
                        usage_info = {
                            "location": {
                                "file": usage.file.filepath if hasattr(usage, "file") else "unknown",
                                "line": getattr(usage, "line_start", None)
                            },
                            "context": self._get_surrounding_context(usage, lines=1)  # Minimal context
                        }
                        analysis["usages"].append(usage_info)
                    except Exception as e:
                        logger.debug(f"Error processing usage: {e}")
                        continue
        
        except Exception as e:
            logger.warning(f"Error gathering static analysis: {e}")
        
        return analysis
    
    def _get_relationships(self, target: Editable) -> Dict[str, Any]:
        """Get relationship information with circular reference protection."""
        relationships = {
            "parent_child": {},
            "siblings": []
        }
        
        target_id = self._get_target_id(target)
        if target_id in self._processed_targets:
            logger.debug(f"Skipping circular reference for {target_id}")
            return relationships
        
        self._processed_targets.add(target_id)
        
        try:
            # Parent/child relationships
            if hasattr(target, "parent") and target.parent:
                try:
                    relationships["parent_child"]["parent"] = {
                        "name": getattr(target.parent, "name", "unknown"),
                        "type": target.parent.__class__.__name__
                    }
                except Exception as e:
                    logger.debug(f"Error processing parent: {e}")
            
            if hasattr(target, "children"):
                try:
                    children = list(target.children)[:5]  # Limit to first 5
                    relationships["parent_child"]["children"] = [
                        {
                            "name": getattr(child, "name", "unknown"),
                            "type": child.__class__.__name__
                        }
                        for child in children
                    ]
                except Exception as e:
                    logger.debug(f"Error processing children: {e}")
            
            # Sibling methods/functions (limited for performance)
            if hasattr(target, "parent_class") and target.parent_class:
                try:
                    siblings = []
                    if hasattr(target.parent_class, "methods"):
                        methods = list(target.parent_class.methods)[:5]
                        for method in methods:
                            if method != target:
                                siblings.append({
                                    "name": getattr(method, "name", "unknown"),
                                    "type": "method"
                                })
                    relationships["siblings"] = siblings
                except Exception as e:
                    logger.debug(f"Error processing class siblings: {e}")
            elif hasattr(target, "file") and target.file:
                try:
                    # For functions, get other functions in the same file
                    siblings = []
                    if hasattr(target.file, "functions"):
                        functions = list(target.file.functions)[:5]
                        for func in functions:
                            if func != target:
                                siblings.append({
                                    "name": getattr(func, "name", "unknown"),
                                    "type": "function"
                                })
                    relationships["siblings"] = siblings
                except Exception as e:
                    logger.debug(f"Error processing file siblings: {e}")
        
        except Exception as e:
            logger.warning(f"Error gathering relationships: {e}")
        finally:
            # Clean up to prevent memory leaks
            self._processed_targets.discard(target_id)
        
        return relationships
    
    @lru_cache(maxsize=128)
    def _get_codebase_summary(self) -> Dict[str, Any]:
        """Get high-level codebase overview with caching."""
        try:
            # Use cached computation for expensive operations
            summary = {
                "total_files": self._safe_len(getattr(self.codebase, "files", [])),
                "total_classes": self._safe_len(getattr(self.codebase, "classes", [])),
                "total_functions": self._safe_len(getattr(self.codebase, "functions", [])),
                "languages": self._get_languages_cached(),
                "main_directories": self._get_main_directories()
            }
            
            # Add project description if available
            if hasattr(self.codebase, "description"):
                summary["description"] = self.codebase.description
            
            return summary
        except Exception as e:
            logger.warning(f"Error gathering codebase summary: {e}")
            return {"error": str(e)}
    
    def _safe_len(self, collection) -> int:
        """Safely get length of a collection."""
        try:
            return len(collection) if collection else 0
        except Exception:
            return 0
    
    @lru_cache(maxsize=32)
    def _get_languages_cached(self) -> List[str]:
        """Get languages with caching."""
        try:
            languages = set()
            files = getattr(self.codebase, "files", [])
            # Sample files for performance
            sample_size = min(100, len(files)) if files else 0
            for i, file in enumerate(files):
                if i >= sample_size:
                    break
                if hasattr(file, "language") and file.language:
                    languages.add(file.language)
            return sorted(list(languages))
        except Exception:
            return []

    def _get_main_directories(self) -> List[str]:
        """Get main directories in the codebase."""
        try:
            directories = set()
            for file in self.codebase.files[:100]:  # Sample first 100 files
                parts = file.filepath.split("/")
                if len(parts) > 1:
                    directories.add(parts[0])
            return sorted(list(directories))[:10]  # Return top 10
        except Exception:
            return []
    
    def _get_source_preview(self, target: Editable, max_lines: int = 10) -> str:
        """Get a preview of the source code."""
        try:
            if hasattr(target, "source"):
                lines = target.source.split("\n")
                if len(lines) <= max_lines:
                    return target.source
                else:
                    preview_lines = lines[:max_lines]
                    return "\n".join(preview_lines) + f"\n... ({len(lines) - max_lines} more lines)"
            elif hasattr(target, "extended_source"):
                lines = target.extended_source.split("\n")
                if len(lines) <= max_lines:
                    return target.extended_source
                else:
                    preview_lines = lines[:max_lines]
                    return "\n".join(preview_lines) + f"\n... ({len(lines) - max_lines} more lines)"
            else:
                return "Source not available"
        except Exception:
            return "Error retrieving source"
    
    def _get_surrounding_context(self, target: Editable, lines: int = 3) -> str:
        """Get surrounding context for a target."""
        try:
            if not hasattr(target, "file") or not hasattr(target, "line_start"):
                return "Context not available"
            
            file_lines = target.file.source.split("\n")
            start_line = max(0, target.line_start - lines - 1)
            end_line = min(len(file_lines), target.line_start + lines)
            
            context_lines = file_lines[start_line:end_line]
            return "\n".join(context_lines)
        except Exception:
            return "Error retrieving context"
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format gathered context for use in AI prompts."""
        formatted_parts = []
        
        # Target information
        if "target_info" in context:
            target_info = context["target_info"]
            formatted_parts.append(f"=== TARGET INFORMATION ===")
            formatted_parts.append(f"Type: {target_info.get('type', 'unknown')}")
            formatted_parts.append(f"Name: {target_info.get('name', 'unknown')}")
            formatted_parts.append(f"Location: {target_info.get('location', {}).get('file', 'unknown')}")
            if target_info.get("signature"):
                formatted_parts.append(f"Signature: {target_info['signature']}")
            formatted_parts.append(f"Source Preview:\n{target_info.get('source_preview', 'Not available')}")
            formatted_parts.append("")
        
        # Static analysis
        if "static_analysis" in context:
            analysis = context["static_analysis"]
            if analysis.get("call_sites"):
                formatted_parts.append("=== CALL SITES ===")
                for i, call_site in enumerate(analysis["call_sites"][:3]):  # Show top 3
                    formatted_parts.append(f"Call Site {i+1}: {call_site.get('location', {}).get('file', 'unknown')}")
                    if call_site.get("context"):
                        formatted_parts.append(f"Context:\n{call_site['context']}")
                formatted_parts.append("")
            
            if analysis.get("dependencies"):
                formatted_parts.append("=== DEPENDENCIES ===")
                for dep in analysis["dependencies"][:5]:  # Show top 5
                    formatted_parts.append(f"- {dep.get('name', 'unknown')} ({dep.get('type', 'unknown')})")
                formatted_parts.append("")
        
        # Relationships
        if "relationships" in context:
            relationships = context["relationships"]
            if relationships.get("siblings"):
                formatted_parts.append("=== RELATED SYMBOLS ===")
                for sibling in relationships["siblings"][:3]:  # Show top 3
                    formatted_parts.append(f"- {sibling.get('name', 'unknown')} ({sibling.get('type', 'unknown')})")
                formatted_parts.append("")
        
        # Codebase summary
        if "codebase_summary" in context:
            summary = context["codebase_summary"]
            formatted_parts.append("=== CODEBASE OVERVIEW ===")
            formatted_parts.append(f"Files: {summary.get('total_files', 0)}")
            formatted_parts.append(f"Classes: {summary.get('total_classes', 0)}")
            formatted_parts.append(f"Functions: {summary.get('total_functions', 0)}")
            if summary.get("languages"):
                formatted_parts.append(f"Languages: {', '.join(summary['languages'])}")
            formatted_parts.append("")
        
        return "\n".join(formatted_parts)
    
    def optimize_context_size(self, context: str, max_tokens: int = 8000) -> str:
        """Optimize context size by intelligent truncation with improved algorithms."""
        from graph_sitter.ai.utils import count_tokens, truncate_to_token_limit
        
        # Use the enhanced token counting utilities
        current_tokens = count_tokens(context)
        
        if current_tokens <= max_tokens:
            return context
        
        # Use the new truncation utility with middle strategy for better context preservation
        return truncate_to_token_limit(context, max_tokens, truncation_strategy="middle")
    
    def clear_cache(self) -> None:
        """Clear the context cache."""
        with _cache_lock:
            _context_cache.clear()
            logger.info("Context cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current context cache."""
        with _cache_lock:
            current_time = time.time()
            active_entries = sum(
                1 for _, (_, timestamp) in _context_cache.items()
                if current_time - timestamp < _cache_ttl
            )
            
            return {
                "total_entries": len(_context_cache),
                "active_entries": active_entries,
                "cache_ttl": _cache_ttl,
                "cache_keys": list(_context_cache.keys())
            }
    
    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries and return number of entries removed."""
        with _cache_lock:
            current_time = time.time()
            expired_keys = [
                key for key, (_, timestamp) in _context_cache.items()
                if current_time - timestamp >= _cache_ttl
            ]
            
            for key in expired_keys:
                del _context_cache[key]
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for context gathering."""
        cache_info = self.get_cache_info()
        
        return {
            "max_context_items": self.max_context_items,
            "cache_enabled": self.enable_cache,
            "cache_stats": cache_info,
            "processed_targets_count": len(self._processed_targets)
        }

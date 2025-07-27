#!/usr/bin/env python3
"""
Advanced API Layer for Serena Integration

This module provides a unified, high-level API for accessing all advanced
Serena integration features including knowledge extraction, error analysis,
context inclusion, and relationship mapping.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import asdict
from pathlib import Path

from graph_sitter.core.codebase import Codebase

from .knowledge_integration import AdvancedKnowledgeIntegration, KnowledgeContext, KnowledgeGraph
from .advanced_context import AdvancedContextEngine, ContextualError
from .advanced_error_viewer import AdvancedErrorViewer, ErrorViewConfig, ErrorCluster

logger = logging.getLogger(__name__)


class SerenaAdvancedAPI:
    """
    Unified API for advanced Serena integration features.
    
    This class provides high-level access to all Serena integration capabilities
    including knowledge extraction, error analysis, context inclusion, and
    intelligent code understanding.
    """
    
    def __init__(
        self,
        codebase: Codebase,
        enable_serena: bool = True,
        enable_caching: bool = True,
        max_workers: int = 4
    ):
        self.codebase = codebase
        self.enable_serena = enable_serena
        self.enable_caching = enable_caching
        
        # Initialize core components
        self.knowledge_integration = AdvancedKnowledgeIntegration(
            codebase=codebase,
            enable_serena=enable_serena,
            enable_caching=enable_caching,
            max_workers=max_workers
        )
        
        self.context_engine = AdvancedContextEngine(
            codebase=codebase,
            knowledge_integration=self.knowledge_integration
        )
        
        self.error_viewer = AdvancedErrorViewer(
            codebase=codebase,
            knowledge_integration=self.knowledge_integration
        )
        
        # API state
        self._initialized = True
        logger.info("SerenaAdvancedAPI initialized successfully")
    
    # ============================================================================
    # Knowledge Extraction API
    # ============================================================================
    
    async def extract_knowledge(
        self,
        file_path: str,
        symbol_name: Optional[str] = None,
        line_number: Optional[int] = None,
        include_context: bool = True,
        extractors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract comprehensive knowledge about a code element.
        
        Args:
            file_path: Path to the file
            symbol_name: Name of the symbol (function, class, etc.)
            line_number: Line number for context
            include_context: Whether to include contextual analysis
            extractors: List of extractors to use (semantic, architectural, dependency)
        
        Returns:
            Comprehensive knowledge about the code element
        """
        try:
            knowledge = await self.knowledge_integration.extract_comprehensive_knowledge(
                file_path=file_path,
                symbol_name=symbol_name,
                line_number=line_number,
                include_context=include_context
            )
            
            # Filter by requested extractors
            if extractors:
                filtered_knowledge = {
                    key: value for key, value in knowledge.items()
                    if key in extractors or key in ["context", "extraction_timestamp", "extractors_used"]
                }
                return filtered_knowledge
            
            return knowledge
            
        except Exception as e:
            logger.error(f"Knowledge extraction failed: {e}")
            return {"error": str(e)}
    
    async def build_knowledge_graph(
        self,
        include_semantic_layers: bool = True,
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Build a comprehensive knowledge graph of the codebase.
        
        Args:
            include_semantic_layers: Whether to include semantic analysis layers
            include_metrics: Whether to include graph metrics
        
        Returns:
            Knowledge graph representation
        """
        try:
            knowledge_graph = await self.knowledge_integration.build_knowledge_graph(
                include_semantic_layers=include_semantic_layers
            )
            
            # Convert to serializable format
            graph_data = {
                "nodes": knowledge_graph.nodes,
                "edges": knowledge_graph.edges,
                "clusters": knowledge_graph.clusters,
                "semantic_layers": knowledge_graph.semantic_layers if include_semantic_layers else {}
            }
            
            if include_metrics:
                graph_data["metrics"] = knowledge_graph.metrics
            
            return graph_data
            
        except Exception as e:
            logger.error(f"Knowledge graph building failed: {e}")
            return {"error": str(e)}
    
    async def search_semantic_patterns(
        self,
        query: str,
        pattern_type: Optional[str] = None,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search for semantic patterns in the codebase.
        
        Args:
            query: Search query
            pattern_type: Type of pattern to search for
            max_results: Maximum number of results
        
        Returns:
            Search results with semantic patterns
        """
        try:
            if self.knowledge_integration.semantic_search:
                results = await self.knowledge_integration.semantic_search.search_patterns(
                    query=query,
                    pattern_type=pattern_type,
                    max_results=max_results
                )
                return results
            else:
                return {
                    "patterns": [],
                    "message": "Semantic search not available (Serena not initialized)"
                }
                
        except Exception as e:
            logger.error(f"Semantic pattern search failed: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # Error Analysis API
    # ============================================================================
    
    async def analyze_error_comprehensive(
        self,
        error_info: Dict[str, Any],
        include_visualizations: bool = True,
        include_suggestions: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive error analysis with full context.
        
        Args:
            error_info: Error information dictionary
            include_visualizations: Whether to include error visualizations
            include_suggestions: Whether to include fix suggestions
        
        Returns:
            Comprehensive error analysis
        """
        try:
            analysis = await self.error_viewer.view_error_comprehensive(
                error_info=error_info,
                include_visualizations=include_visualizations
            )
            
            if not include_suggestions:
                # Remove suggestions if not requested
                analysis.pop("fix_recommendations", None)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Comprehensive error analysis failed: {e}")
            return {"error": str(e)}
    
    async def analyze_error_context(
        self,
        error_info: Dict[str, Any],
        context_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Analyze error context with specified depth.
        
        Args:
            error_info: Error information dictionary
            context_depth: Depth of context analysis
        
        Returns:
            Error context analysis
        """
        try:
            contextual_error = await self.context_engine.analyze_error_context(
                error_info=error_info,
                include_deep_analysis=context_depth > 2
            )
            
            # Convert to serializable format
            return {
                "error_overview": {
                    "id": contextual_error.error_id,
                    "type": contextual_error.error_type,
                    "severity": contextual_error.severity,
                    "location": {
                        "file_path": contextual_error.file_path,
                        "line_number": contextual_error.line_number,
                        "function_name": contextual_error.function_name,
                        "class_name": contextual_error.class_name
                    }
                },
                "context_layers": {
                    "immediate": contextual_error.immediate_context,
                    "function": contextual_error.function_context,
                    "class": contextual_error.class_context,
                    "file": contextual_error.file_context,
                    "module": contextual_error.module_context,
                    "project": contextual_error.project_context
                },
                "relationships": {
                    "related_symbols": contextual_error.related_symbols,
                    "dependency_chain": contextual_error.dependency_chain,
                    "impact_analysis": contextual_error.impact_analysis
                },
                "suggestions": {
                    "fix_suggestions": [asdict(fix) if hasattr(fix, '__dict__') else fix for fix in contextual_error.fix_suggestions],
                    "code_examples": contextual_error.code_examples,
                    "best_practices": contextual_error.best_practices
                }
            }
            
        except Exception as e:
            logger.error(f"Error context analysis failed: {e}")
            return {"error": str(e)}
    
    async def cluster_errors(
        self,
        errors: List[Dict[str, Any]],
        cluster_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Cluster related errors for better organization.
        
        Args:
            errors: List of error information dictionaries
            cluster_types: Types of clustering to perform
        
        Returns:
            Error clusters with analysis
        """
        try:
            clusters = await self.error_viewer.cluster_related_errors(errors)
            
            # Filter by cluster types if specified
            if cluster_types:
                clusters = [c for c in clusters if c.cluster_type in cluster_types]
            
            # Convert to serializable format
            cluster_data = []
            for cluster in clusters:
                cluster_data.append({
                    "cluster_id": cluster.cluster_id,
                    "cluster_type": cluster.cluster_type,
                    "errors": cluster.errors,
                    "common_patterns": cluster.common_patterns,
                    "suggested_fixes": cluster.suggested_fixes,
                    "priority_score": cluster.priority_score
                })
            
            return {
                "clusters": cluster_data,
                "summary": {
                    "total_clusters": len(cluster_data),
                    "cluster_types": list(set(c["cluster_type"] for c in cluster_data)),
                    "highest_priority": max((c["priority_score"] for c in cluster_data), default=0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error clustering failed: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # Context Analysis API
    # ============================================================================
    
    async def analyze_symbol_context(
        self,
        file_path: str,
        symbol_name: str,
        symbol_type: Optional[str] = None,
        include_relationships: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze context for a specific symbol.
        
        Args:
            file_path: Path to the file containing the symbol
            symbol_name: Name of the symbol
            symbol_type: Type of symbol (function, class, variable)
            include_relationships: Whether to include relationship analysis
        
        Returns:
            Symbol context analysis
        """
        try:
            # Create a mock error to leverage context analysis
            mock_error = {
                "id": f"context_analysis_{symbol_name}",
                "type": "context_analysis",
                "severity": "info",
                "file_path": file_path,
                "function_name": symbol_name if symbol_type == "function" else None,
                "class_name": symbol_name if symbol_type == "class" else None,
                "message": f"Context analysis for {symbol_name}",
                "description": f"Analyzing context for symbol {symbol_name}"
            }
            
            contextual_error = await self.context_engine.analyze_error_context(
                error_info=mock_error,
                include_deep_analysis=include_relationships
            )
            
            return {
                "symbol_info": {
                    "name": symbol_name,
                    "type": symbol_type,
                    "file_path": file_path
                },
                "context": {
                    "immediate": contextual_error.immediate_context,
                    "function": contextual_error.function_context,
                    "class": contextual_error.class_context,
                    "file": contextual_error.file_context
                },
                "relationships": {
                    "related_symbols": contextual_error.related_symbols,
                    "dependency_chain": contextual_error.dependency_chain
                } if include_relationships else {}
            }
            
        except Exception as e:
            logger.error(f"Symbol context analysis failed: {e}")
            return {"error": str(e)}
    
    async def analyze_file_context(
        self,
        file_path: str,
        include_dependencies: bool = True,
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze context for an entire file.
        
        Args:
            file_path: Path to the file
            include_dependencies: Whether to include dependency analysis
            include_metrics: Whether to include file metrics
        
        Returns:
            File context analysis
        """
        try:
            # Extract knowledge for the file
            knowledge = await self.extract_knowledge(
                file_path=file_path,
                include_context=True
            )
            
            # Get file object
            file_obj = None
            for file in self.codebase.files:
                if file.filepath == file_path or file.name == file_path:
                    file_obj = file
                    break
            
            if not file_obj:
                return {"error": f"File not found: {file_path}"}
            
            context = {
                "file_info": {
                    "name": file_obj.name,
                    "path": file_obj.filepath,
                    "size": len(file_obj.source),
                    "line_count": len(file_obj.source.splitlines())
                },
                "symbols": {
                    "functions": [f.name for f in file_obj.functions],
                    "classes": [c.name for c in file_obj.classes],
                    "global_vars": [v.name for v in file_obj.global_vars],
                    "imports": [i.name for i in file_obj.imports]
                }
            }
            
            if include_dependencies:
                context["dependencies"] = {
                    "imports": [i.name for i in file_obj.imports],
                    "internal_deps": [],  # Would be calculated
                    "external_deps": []   # Would be calculated
                }
            
            if include_metrics:
                context["metrics"] = {
                    "complexity_score": 0,  # Would be calculated
                    "maintainability_index": 0,  # Would be calculated
                    "test_coverage": 0  # Would be calculated
                }
            
            # Add knowledge insights if available
            if "contextual_analysis" in knowledge:
                context["insights"] = knowledge["contextual_analysis"]
            
            return context
            
        except Exception as e:
            logger.error(f"File context analysis failed: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # Relationship Analysis API
    # ============================================================================
    
    async def analyze_dependencies(
        self,
        file_path: str,
        symbol_name: Optional[str] = None,
        include_transitive: bool = True,
        max_depth: int = 5
    ) -> Dict[str, Any]:
        """
        Analyze dependencies for a file or symbol.
        
        Args:
            file_path: Path to the file
            symbol_name: Name of the symbol (optional)
            include_transitive: Whether to include transitive dependencies
            max_depth: Maximum depth for transitive dependencies
        
        Returns:
            Dependency analysis
        """
        try:
            knowledge = await self.extract_knowledge(
                file_path=file_path,
                symbol_name=symbol_name,
                extractors=["dependency"]
            )
            
            dependency_data = knowledge.get("dependency", {})
            
            analysis = {
                "direct_dependencies": dependency_data.get("direct_dependencies", {}),
                "reverse_dependencies": dependency_data.get("reverse_dependencies", {}),
                "impact_analysis": dependency_data.get("impact_analysis", {})
            }
            
            if include_transitive:
                analysis["transitive_dependencies"] = dependency_data.get("transitive_dependencies", {})
                analysis["circular_dependencies"] = dependency_data.get("circular_dependencies", {})
            
            return analysis
            
        except Exception as e:
            logger.error(f"Dependency analysis failed: {e}")
            return {"error": str(e)}
    
    async def find_related_symbols(
        self,
        file_path: str,
        symbol_name: str,
        relation_types: Optional[List[str]] = None,
        max_results: int = 20
    ) -> Dict[str, Any]:
        """
        Find symbols related to the given symbol.
        
        Args:
            file_path: Path to the file containing the symbol
            symbol_name: Name of the symbol
            relation_types: Types of relations to find (calls, uses, inherits, etc.)
            max_results: Maximum number of results
        
        Returns:
            Related symbols analysis
        """
        try:
            knowledge = await self.extract_knowledge(
                file_path=file_path,
                symbol_name=symbol_name,
                extractors=["semantic", "dependency"]
            )
            
            semantic_data = knowledge.get("semantic", {})
            dependency_data = knowledge.get("dependency", {})
            
            related_symbols = {
                "semantic_relationships": semantic_data.get("semantic_relationships", {}),
                "dependency_relationships": dependency_data.get("direct_dependencies", {}),
                "usage_patterns": semantic_data.get("usage_patterns", {})
            }
            
            # Filter by relation types if specified
            if relation_types:
                filtered_symbols = {}
                for rel_type in relation_types:
                    if rel_type in related_symbols:
                        filtered_symbols[rel_type] = related_symbols[rel_type]
                related_symbols = filtered_symbols
            
            return {
                "symbol": {
                    "name": symbol_name,
                    "file_path": file_path
                },
                "related_symbols": related_symbols,
                "summary": {
                    "total_relations": sum(len(v) if isinstance(v, list) else 1 for v in related_symbols.values()),
                    "relation_types": list(related_symbols.keys())
                }
            }
            
        except Exception as e:
            logger.error(f"Related symbols analysis failed: {e}")
            return {"error": str(e)}
    
    # ============================================================================
    # Architectural Analysis API
    # ============================================================================
    
    async def analyze_architecture(
        self,
        scope: str = "project",  # "project", "module", "file"
        include_patterns: bool = True,
        include_metrics: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze architectural patterns and structure.
        
        Args:
            scope: Scope of analysis (project, module, file)
            include_patterns: Whether to include pattern detection
            include_metrics: Whether to include architectural metrics
        
        Returns:
            Architectural analysis
        """
        try:
            if scope == "project":
                # Analyze entire project architecture
                knowledge_graph = await self.build_knowledge_graph(
                    include_semantic_layers=True,
                    include_metrics=include_metrics
                )
                
                analysis = {
                    "scope": "project",
                    "structure": {
                        "total_files": len(knowledge_graph["nodes"]),
                        "total_components": len([n for n in knowledge_graph["nodes"].values() if n["type"] in ["function", "class"]]),
                        "modules": len(knowledge_graph["clusters"])
                    }
                }
                
                if include_patterns:
                    analysis["patterns"] = self._detect_architectural_patterns(knowledge_graph)
                
                if include_metrics:
                    analysis["metrics"] = knowledge_graph.get("metrics", {})
                
                return analysis
            
            else:
                return {"error": f"Scope '{scope}' not yet implemented"}
                
        except Exception as e:
            logger.error(f"Architectural analysis failed: {e}")
            return {"error": str(e)}
    
    def _detect_architectural_patterns(self, knowledge_graph: Dict[str, Any]) -> List[str]:
        """Detect architectural patterns from knowledge graph."""
        patterns = []
        
        # Analyze node types and relationships
        nodes = knowledge_graph.get("nodes", {})
        edges = knowledge_graph.get("edges", [])
        
        # Simple pattern detection based on naming conventions
        file_paths = [node["path"] for node in nodes.values() if node["type"] == "file"]
        
        if any("controller" in path.lower() for path in file_paths):
            patterns.append("MVC Pattern")
        if any("service" in path.lower() for path in file_paths):
            patterns.append("Service Layer Pattern")
        if any("repository" in path.lower() for path in file_paths):
            patterns.append("Repository Pattern")
        if any("factory" in path.lower() for path in file_paths):
            patterns.append("Factory Pattern")
        
        return patterns
    
    # ============================================================================
    # Utility Methods
    # ============================================================================
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get the status of the API and its components."""
        return {
            "initialized": self._initialized,
            "serena_enabled": self.enable_serena,
            "caching_enabled": self.enable_caching,
            "components": {
                "knowledge_integration": self.knowledge_integration is not None,
                "context_engine": self.context_engine is not None,
                "error_viewer": self.error_viewer is not None
            },
            "codebase_info": {
                "total_files": len(list(self.codebase.files)),
                "total_functions": len(list(self.codebase.functions)),
                "total_classes": len(list(self.codebase.classes))
            }
        }
    
    def clear_caches(self) -> Dict[str, bool]:
        """Clear all caches."""
        try:
            if self.knowledge_integration and hasattr(self.knowledge_integration, 'knowledge_cache'):
                self.knowledge_integration.knowledge_cache.clear()
            
            if self.context_engine and hasattr(self.context_engine, 'context_cache'):
                self.context_engine.context_cache.clear()
            
            if self.error_viewer and hasattr(self.error_viewer, 'error_cache'):
                self.error_viewer.error_cache.clear()
            
            return {"success": True, "message": "All caches cleared"}
            
        except Exception as e:
            logger.error(f"Failed to clear caches: {e}")
            return {"success": False, "error": str(e)}
    
    async def shutdown(self):
        """Shutdown the API and cleanup resources."""
        try:
            if self.knowledge_integration:
                self.knowledge_integration.shutdown()
            
            self._initialized = False
            logger.info("SerenaAdvancedAPI shutdown completed")
            
        except Exception as e:
            logger.error(f"Shutdown failed: {e}")


# Convenience functions for easy access
async def create_serena_api(
    codebase: Codebase,
    enable_serena: bool = True,
    enable_caching: bool = True,
    max_workers: int = 4
) -> SerenaAdvancedAPI:
    """Create and initialize a Serena Advanced API instance."""
    return SerenaAdvancedAPI(
        codebase=codebase,
        enable_serena=enable_serena,
        enable_caching=enable_caching,
        max_workers=max_workers
    )


async def quick_error_analysis(
    codebase: Codebase,
    error_info: Dict[str, Any],
    enable_serena: bool = True
) -> Dict[str, Any]:
    """Quick error analysis with default settings."""
    api = await create_serena_api(codebase, enable_serena=enable_serena)
    try:
        return await api.analyze_error_comprehensive(error_info)
    finally:
        await api.shutdown()


async def quick_knowledge_extraction(
    codebase: Codebase,
    file_path: str,
    symbol_name: Optional[str] = None,
    enable_serena: bool = True
) -> Dict[str, Any]:
    """Quick knowledge extraction with default settings."""
    api = await create_serena_api(codebase, enable_serena=enable_serena)
    try:
        return await api.extract_knowledge(file_path, symbol_name)
    finally:
        await api.shutdown()


#!/usr/bin/env python3
"""
Advanced Serena Knowledge Integration for Graph-Sitter

This module provides comprehensive integration with Serena's codebase knowledge features,
enabling advanced error analysis, context inclusion, and semantic understanding.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.symbol import Symbol

# Import Serena components
try:
    from .mcp_bridge import SerenaMCPBridge
    from .semantic_tools import SerenaSemanticTools
    from .code_intelligence import SerenaCodeIntelligence
    from .symbol_intelligence import SerenaSymbolIntelligence
    from .semantic_search import SerenaSemanticSearch
except ImportError:
    # Fallback for when Serena components are not available
    SerenaMCPBridge = None
    SerenaSemanticTools = None
    SerenaCodeIntelligence = None
    SerenaSymbolIntelligence = None
    SerenaSemanticSearch = None

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeContext:
    """Comprehensive context for code knowledge extraction."""
    file_path: str
    symbol_name: Optional[str] = None
    symbol_type: Optional[str] = None
    line_number: Optional[int] = None
    semantic_context: Dict[str, Any] = field(default_factory=dict)
    architectural_context: Dict[str, Any] = field(default_factory=dict)
    dependency_context: Dict[str, Any] = field(default_factory=dict)
    error_context: Dict[str, Any] = field(default_factory=dict)
    performance_context: Dict[str, Any] = field(default_factory=dict)
    security_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeGraph:
    """Knowledge graph representation of codebase understanding."""
    nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    clusters: Dict[str, List[str]] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    semantic_layers: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AdvancedErrorContext:
    """Advanced error context with deep semantic understanding."""
    error_id: str
    error_type: str
    severity: str
    file_path: str
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    message: str = ""
    description: str = ""
    
    # Advanced context
    semantic_context: Dict[str, Any] = field(default_factory=dict)
    architectural_impact: Dict[str, Any] = field(default_factory=dict)
    dependency_chain: List[str] = field(default_factory=list)
    related_errors: List[str] = field(default_factory=list)
    fix_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    code_examples: List[Dict[str, Any]] = field(default_factory=list)
    
    # Knowledge integration
    serena_insights: Dict[str, Any] = field(default_factory=dict)
    pattern_matches: List[Dict[str, Any]] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)


class KnowledgeExtractor(ABC):
    """Abstract base class for knowledge extractors."""
    
    @abstractmethod
    async def extract(self, context: KnowledgeContext) -> Dict[str, Any]:
        """Extract knowledge from the given context."""
        pass
    
    @abstractmethod
    def get_extractor_type(self) -> str:
        """Get the type of this extractor."""
        pass


class SemanticKnowledgeExtractor(KnowledgeExtractor):
    """Extract semantic knowledge using Serena's capabilities."""
    
    def __init__(self, semantic_tools: Optional[SerenaSemanticTools] = None):
        self.semantic_tools = semantic_tools
        self.cache = {}
    
    async def extract(self, context: KnowledgeContext) -> Dict[str, Any]:
        """Extract semantic knowledge from code context."""
        cache_key = f"{context.file_path}:{context.symbol_name}:{context.line_number}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        semantic_knowledge = {
            "symbol_semantics": {},
            "type_information": {},
            "usage_patterns": {},
            "semantic_relationships": {},
            "intent_analysis": {},
            "complexity_metrics": {}
        }
        
        try:
            if self.semantic_tools:
                # Use Serena's semantic analysis
                semantic_analysis = await self.semantic_tools.analyze_semantics(
                    file_path=context.file_path,
                    symbol_name=context.symbol_name,
                    line_number=context.line_number
                )
                semantic_knowledge.update(semantic_analysis)
            else:
                # Fallback to basic semantic analysis
                semantic_knowledge = await self._basic_semantic_analysis(context)
            
            self.cache[cache_key] = semantic_knowledge
            return semantic_knowledge
            
        except Exception as e:
            logger.error(f"Semantic knowledge extraction failed: {e}")
            return semantic_knowledge
    
    async def _basic_semantic_analysis(self, context: KnowledgeContext) -> Dict[str, Any]:
        """Basic semantic analysis when Serena tools are not available."""
        return {
            "symbol_semantics": {
                "name": context.symbol_name,
                "type": context.symbol_type,
                "scope": "unknown",
                "visibility": "unknown"
            },
            "type_information": {
                "inferred_type": "unknown",
                "type_confidence": 0.0
            },
            "usage_patterns": {
                "access_patterns": [],
                "modification_patterns": [],
                "call_patterns": []
            },
            "semantic_relationships": {
                "related_symbols": [],
                "dependency_symbols": [],
                "usage_symbols": []
            },
            "intent_analysis": {
                "purpose": "unknown",
                "behavior": "unknown",
                "side_effects": []
            },
            "complexity_metrics": {
                "semantic_complexity": 0,
                "cognitive_load": 0
            }
        }
    
    def get_extractor_type(self) -> str:
        return "semantic"


class ArchitecturalKnowledgeExtractor(KnowledgeExtractor):
    """Extract architectural knowledge and patterns."""
    
    def __init__(self, code_intelligence: Optional[SerenaCodeIntelligence] = None):
        self.code_intelligence = code_intelligence
        self.pattern_cache = {}
    
    async def extract(self, context: KnowledgeContext) -> Dict[str, Any]:
        """Extract architectural knowledge from code context."""
        architectural_knowledge = {
            "design_patterns": {},
            "architectural_layers": {},
            "component_relationships": {},
            "coupling_analysis": {},
            "cohesion_analysis": {},
            "architectural_smells": {}
        }
        
        try:
            if self.code_intelligence:
                # Use Serena's architectural analysis
                arch_analysis = await self.code_intelligence.analyze_architecture(
                    file_path=context.file_path,
                    symbol_name=context.symbol_name
                )
                architectural_knowledge.update(arch_analysis)
            else:
                # Fallback to basic architectural analysis
                architectural_knowledge = await self._basic_architectural_analysis(context)
            
            return architectural_knowledge
            
        except Exception as e:
            logger.error(f"Architectural knowledge extraction failed: {e}")
            return architectural_knowledge
    
    async def _basic_architectural_analysis(self, context: KnowledgeContext) -> Dict[str, Any]:
        """Basic architectural analysis when Serena tools are not available."""
        return {
            "design_patterns": {
                "detected_patterns": [],
                "pattern_confidence": {}
            },
            "architectural_layers": {
                "layer": "unknown",
                "layer_violations": []
            },
            "component_relationships": {
                "dependencies": [],
                "dependents": [],
                "coupling_strength": 0.0
            },
            "coupling_analysis": {
                "afferent_coupling": 0,
                "efferent_coupling": 0,
                "coupling_ratio": 0.0
            },
            "cohesion_analysis": {
                "cohesion_type": "unknown",
                "cohesion_strength": 0.0
            },
            "architectural_smells": {
                "detected_smells": [],
                "severity_scores": {}
            }
        }
    
    def get_extractor_type(self) -> str:
        return "architectural"


class DependencyKnowledgeExtractor(KnowledgeExtractor):
    """Extract dependency knowledge and impact analysis."""
    
    def __init__(self, symbol_intelligence: Optional[SerenaSymbolIntelligence] = None):
        self.symbol_intelligence = symbol_intelligence
        self.dependency_cache = {}
    
    async def extract(self, context: KnowledgeContext) -> Dict[str, Any]:
        """Extract dependency knowledge from code context."""
        dependency_knowledge = {
            "direct_dependencies": {},
            "transitive_dependencies": {},
            "reverse_dependencies": {},
            "dependency_graph": {},
            "impact_analysis": {},
            "circular_dependencies": {}
        }
        
        try:
            if self.symbol_intelligence:
                # Use Serena's dependency analysis
                dep_analysis = await self.symbol_intelligence.analyze_dependencies(
                    file_path=context.file_path,
                    symbol_name=context.symbol_name
                )
                dependency_knowledge.update(dep_analysis)
            else:
                # Fallback to basic dependency analysis
                dependency_knowledge = await self._basic_dependency_analysis(context)
            
            return dependency_knowledge
            
        except Exception as e:
            logger.error(f"Dependency knowledge extraction failed: {e}")
            return dependency_knowledge
    
    async def _basic_dependency_analysis(self, context: KnowledgeContext) -> Dict[str, Any]:
        """Basic dependency analysis when Serena tools are not available."""
        return {
            "direct_dependencies": {
                "imports": [],
                "function_calls": [],
                "class_references": []
            },
            "transitive_dependencies": {
                "depth": 0,
                "dependencies": []
            },
            "reverse_dependencies": {
                "used_by": [],
                "impact_scope": "unknown"
            },
            "dependency_graph": {
                "nodes": [],
                "edges": []
            },
            "impact_analysis": {
                "change_impact": "unknown",
                "affected_components": []
            },
            "circular_dependencies": {
                "detected": False,
                "cycles": []
            }
        }
    
    def get_extractor_type(self) -> str:
        return "dependency"


class AdvancedKnowledgeIntegration:
    """
    Advanced knowledge integration system that combines graph-sitter analysis
    with Serena's codebase knowledge features.
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
        self.max_workers = max_workers
        
        # Initialize Serena components
        self.mcp_bridge = None
        self.semantic_tools = None
        self.code_intelligence = None
        self.symbol_intelligence = None
        self.semantic_search = None
        
        if enable_serena:
            self._initialize_serena_components()
        
        # Initialize knowledge extractors
        self.extractors = {
            "semantic": SemanticKnowledgeExtractor(self.semantic_tools),
            "architectural": ArchitecturalKnowledgeExtractor(self.code_intelligence),
            "dependency": DependencyKnowledgeExtractor(self.symbol_intelligence)
        }
        
        # Caches
        self.knowledge_cache = {} if enable_caching else None
        self.context_cache = {} if enable_caching else None
        self.graph_cache = {} if enable_caching else None
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def _initialize_serena_components(self):
        """Initialize Serena MCP components if available."""
        try:
            if SerenaMCPBridge:
                self.mcp_bridge = SerenaMCPBridge()
                if self.mcp_bridge.is_initialized:
                    self.semantic_tools = SerenaSemanticTools(self.mcp_bridge)
                    self.code_intelligence = SerenaCodeIntelligence(self.mcp_bridge)
                    self.symbol_intelligence = SerenaSymbolIntelligence(self.mcp_bridge)
                    self.semantic_search = SerenaSemanticSearch(self.mcp_bridge)
                    logger.info("Serena components initialized successfully")
                else:
                    logger.warning("Serena MCP bridge failed to initialize")
            else:
                logger.info("Serena components not available, using fallback implementations")
        except Exception as e:
            logger.error(f"Failed to initialize Serena components: {e}")
    
    async def extract_comprehensive_knowledge(
        self,
        file_path: str,
        symbol_name: Optional[str] = None,
        line_number: Optional[int] = None,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """
        Extract comprehensive knowledge about a code element using all available extractors.
        """
        context = KnowledgeContext(
            file_path=file_path,
            symbol_name=symbol_name,
            line_number=line_number
        )
        
        # Check cache first
        cache_key = f"{file_path}:{symbol_name}:{line_number}"
        if self.knowledge_cache and cache_key in self.knowledge_cache:
            return self.knowledge_cache[cache_key]
        
        # Extract knowledge using all extractors
        knowledge = {
            "context": context.__dict__,
            "extraction_timestamp": time.time(),
            "extractors_used": list(self.extractors.keys())
        }
        
        # Run extractors in parallel
        extraction_tasks = []
        for extractor_name, extractor in self.extractors.items():
            task = asyncio.create_task(extractor.extract(context))
            extraction_tasks.append((extractor_name, task))
        
        # Collect results
        for extractor_name, task in extraction_tasks:
            try:
                result = await task
                knowledge[extractor_name] = result
            except Exception as e:
                logger.error(f"Extractor {extractor_name} failed: {e}")
                knowledge[extractor_name] = {"error": str(e)}
        
        # Add contextual information if requested
        if include_context:
            knowledge["contextual_analysis"] = await self._analyze_context(context)
        
        # Cache the result
        if self.knowledge_cache:
            self.knowledge_cache[cache_key] = knowledge
        
        return knowledge
    
    async def _analyze_context(self, context: KnowledgeContext) -> Dict[str, Any]:
        """Analyze the broader context around a code element."""
        contextual_analysis = {
            "file_context": {},
            "module_context": {},
            "project_context": {},
            "ecosystem_context": {}
        }
        
        try:
            # File-level context
            file_obj = self._get_file_object(context.file_path)
            if file_obj:
                contextual_analysis["file_context"] = {
                    "file_size": len(file_obj.source),
                    "function_count": len(file_obj.functions),
                    "class_count": len(file_obj.classes),
                    "import_count": len(file_obj.imports),
                    "complexity_score": await self._calculate_file_complexity(file_obj)
                }
            
            # Module-level context
            module_path = Path(context.file_path).parent
            contextual_analysis["module_context"] = {
                "module_path": str(module_path),
                "related_files": await self._get_related_files(context.file_path),
                "module_dependencies": await self._get_module_dependencies(context.file_path)
            }
            
            # Project-level context
            contextual_analysis["project_context"] = {
                "total_files": len(list(self.codebase.files)),
                "total_functions": len(list(self.codebase.functions)),
                "total_classes": len(list(self.codebase.classes)),
                "architectural_patterns": await self._detect_architectural_patterns()
            }
            
            # Ecosystem context (if Serena is available)
            if self.semantic_search:
                contextual_analysis["ecosystem_context"] = await self._get_ecosystem_context(context)
        
        except Exception as e:
            logger.error(f"Context analysis failed: {e}")
            contextual_analysis["error"] = str(e)
        
        return contextual_analysis
    
    def _get_file_object(self, file_path: str) -> Optional[SourceFile]:
        """Get the SourceFile object for a given path."""
        for file in self.codebase.files:
            if file.filepath == file_path or file.name == file_path:
                return file
        return None
    
    async def _calculate_file_complexity(self, file_obj: SourceFile) -> float:
        """Calculate complexity score for a file."""
        try:
            total_complexity = 0
            function_count = len(file_obj.functions)
            
            for func in file_obj.functions:
                # Use basic complexity calculation
                complexity = self._calculate_cyclomatic_complexity(func)
                total_complexity += complexity
            
            return total_complexity / max(1, function_count)
        except Exception:
            return 0.0
    
    def _calculate_cyclomatic_complexity(self, func: Function) -> int:
        """Calculate cyclomatic complexity for a function."""
        try:
            if hasattr(func, 'source'):
                source = func.source.lower()
                complexity = 1  # Base complexity
                complexity += source.count('if ')
                complexity += source.count('elif ')
                complexity += source.count('for ')
                complexity += source.count('while ')
                complexity += source.count('except ')
                complexity += source.count(' and ')
                complexity += source.count(' or ')
                return complexity
            return 1
        except Exception:
            return 1
    
    async def _get_related_files(self, file_path: str) -> List[str]:
        """Get files related to the given file."""
        related_files = []
        try:
            file_obj = self._get_file_object(file_path)
            if file_obj:
                # Find files that import from this file or are imported by this file
                for other_file in self.codebase.files:
                    if other_file.filepath != file_path:
                        # Check if other_file imports from file_obj
                        for imp in other_file.imports:
                            if hasattr(imp, 'imported_symbol') and hasattr(imp.imported_symbol, 'filepath'):
                                if imp.imported_symbol.filepath == file_path:
                                    related_files.append(other_file.filepath)
                                    break
        except Exception as e:
            logger.error(f"Failed to get related files: {e}")
        
        return related_files[:10]  # Limit to top 10
    
    async def _get_module_dependencies(self, file_path: str) -> List[str]:
        """Get module-level dependencies."""
        dependencies = []
        try:
            file_obj = self._get_file_object(file_path)
            if file_obj:
                for imp in file_obj.imports:
                    dependencies.append(imp.name)
        except Exception as e:
            logger.error(f"Failed to get module dependencies: {e}")
        
        return dependencies[:20]  # Limit to top 20
    
    async def _detect_architectural_patterns(self) -> List[str]:
        """Detect architectural patterns in the codebase."""
        patterns = []
        try:
            file_paths = [file.filepath for file in self.codebase.files]
            
            # Detect common patterns
            if any('controller' in path.lower() for path in file_paths):
                patterns.append('MVC Pattern')
            if any('service' in path.lower() for path in file_paths):
                patterns.append('Service Layer Pattern')
            if any('repository' in path.lower() for path in file_paths):
                patterns.append('Repository Pattern')
            if any('factory' in path.lower() for path in file_paths):
                patterns.append('Factory Pattern')
            if any('adapter' in path.lower() for path in file_paths):
                patterns.append('Adapter Pattern')
            if any('observer' in path.lower() for path in file_paths):
                patterns.append('Observer Pattern')
        except Exception as e:
            logger.error(f"Failed to detect architectural patterns: {e}")
        
        return patterns
    
    async def _get_ecosystem_context(self, context: KnowledgeContext) -> Dict[str, Any]:
        """Get ecosystem context using Serena's semantic search."""
        ecosystem_context = {}
        try:
            if self.semantic_search and context.symbol_name:
                # Search for similar patterns in the ecosystem
                search_results = await self.semantic_search.search_similar_patterns(
                    symbol_name=context.symbol_name,
                    context_type=context.symbol_type
                )
                ecosystem_context = {
                    "similar_patterns": search_results.get("patterns", []),
                    "best_practices": search_results.get("best_practices", []),
                    "common_issues": search_results.get("common_issues", []),
                    "recommendations": search_results.get("recommendations", [])
                }
        except Exception as e:
            logger.error(f"Failed to get ecosystem context: {e}")
            ecosystem_context["error"] = str(e)
        
        return ecosystem_context
    
    async def build_knowledge_graph(self, include_semantic_layers: bool = True) -> KnowledgeGraph:
        """Build a comprehensive knowledge graph of the codebase."""
        cache_key = f"knowledge_graph_{include_semantic_layers}"
        if self.graph_cache and cache_key in self.graph_cache:
            return self.graph_cache[cache_key]
        
        knowledge_graph = KnowledgeGraph()
        
        try:
            # Build nodes for files, functions, and classes
            await self._build_graph_nodes(knowledge_graph)
            
            # Build edges representing relationships
            await self._build_graph_edges(knowledge_graph)
            
            # Detect clusters and communities
            await self._detect_graph_clusters(knowledge_graph)
            
            # Calculate graph metrics
            await self._calculate_graph_metrics(knowledge_graph)
            
            # Add semantic layers if requested
            if include_semantic_layers:
                await self._add_semantic_layers(knowledge_graph)
            
            # Cache the result
            if self.graph_cache:
                self.graph_cache[cache_key] = knowledge_graph
        
        except Exception as e:
            logger.error(f"Failed to build knowledge graph: {e}")
            knowledge_graph.metrics["error"] = str(e)
        
        return knowledge_graph
    
    async def _build_graph_nodes(self, graph: KnowledgeGraph):
        """Build nodes for the knowledge graph."""
        # Add file nodes
        for file in self.codebase.files:
            node_id = f"file:{file.filepath}"
            graph.nodes[node_id] = {
                "type": "file",
                "name": file.name,
                "path": file.filepath,
                "size": len(file.source),
                "functions": len(file.functions),
                "classes": len(file.classes),
                "imports": len(file.imports)
            }
        
        # Add function nodes
        for file in self.codebase.files:
            for func in file.functions:
                node_id = f"function:{file.filepath}:{func.name}"
                graph.nodes[node_id] = {
                    "type": "function",
                    "name": func.name,
                    "file": file.filepath,
                    "parameters": len(func.parameters),
                    "complexity": self._calculate_cyclomatic_complexity(func),
                    "calls": len(func.function_calls)
                }
        
        # Add class nodes
        for file in self.codebase.files:
            for cls in file.classes:
                node_id = f"class:{file.filepath}:{cls.name}"
                graph.nodes[node_id] = {
                    "type": "class",
                    "name": cls.name,
                    "file": file.filepath,
                    "methods": len(cls.methods),
                    "attributes": len(cls.attributes),
                    "inheritance": len(cls.parent_class_names)
                }
    
    async def _build_graph_edges(self, graph: KnowledgeGraph):
        """Build edges for the knowledge graph."""
        # File-to-file dependencies
        for file in self.codebase.files:
            for imp in file.imports:
                if hasattr(imp, 'imported_symbol') and hasattr(imp.imported_symbol, 'filepath'):
                    source_id = f"file:{file.filepath}"
                    target_id = f"file:{imp.imported_symbol.filepath}"
                    graph.edges.append({
                        "source": source_id,
                        "target": target_id,
                        "type": "imports",
                        "weight": 1.0
                    })
        
        # Function call relationships
        for file in self.codebase.files:
            for func in file.functions:
                source_id = f"function:{file.filepath}:{func.name}"
                for call in func.function_calls:
                    # Try to find the target function
                    target_id = self._find_function_node_id(call.name)
                    if target_id:
                        graph.edges.append({
                            "source": source_id,
                            "target": target_id,
                            "type": "calls",
                            "weight": 1.0
                        })
    
    def _find_function_node_id(self, function_name: str) -> Optional[str]:
        """Find the node ID for a function by name."""
        for file in self.codebase.files:
            for func in file.functions:
                if func.name == function_name:
                    return f"function:{file.filepath}:{func.name}"
        return None
    
    async def _detect_graph_clusters(self, graph: KnowledgeGraph):
        """Detect clusters in the knowledge graph."""
        # Simple clustering based on file directories
        directory_clusters = defaultdict(list)
        
        for node_id, node_data in graph.nodes.items():
            if node_data["type"] == "file":
                directory = str(Path(node_data["path"]).parent)
                directory_clusters[directory].append(node_id)
        
        graph.clusters = dict(directory_clusters)
    
    async def _calculate_graph_metrics(self, graph: KnowledgeGraph):
        """Calculate metrics for the knowledge graph."""
        graph.metrics = {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "node_types": {
                "files": len([n for n in graph.nodes.values() if n["type"] == "file"]),
                "functions": len([n for n in graph.nodes.values() if n["type"] == "function"]),
                "classes": len([n for n in graph.nodes.values() if n["type"] == "class"])
            },
            "edge_types": {
                "imports": len([e for e in graph.edges if e["type"] == "imports"]),
                "calls": len([e for e in graph.edges if e["type"] == "calls"])
            },
            "clusters": len(graph.clusters),
            "density": len(graph.edges) / max(1, len(graph.nodes) * (len(graph.nodes) - 1) / 2)
        }
    
    async def _add_semantic_layers(self, graph: KnowledgeGraph):
        """Add semantic layers to the knowledge graph."""
        if self.semantic_tools:
            try:
                # Add semantic similarity layer
                semantic_similarities = await self.semantic_tools.calculate_semantic_similarities(
                    list(graph.nodes.keys())
                )
                graph.semantic_layers["similarity"] = semantic_similarities
                
                # Add conceptual clustering layer
                conceptual_clusters = await self.semantic_tools.detect_conceptual_clusters(
                    list(graph.nodes.keys())
                )
                graph.semantic_layers["conceptual_clusters"] = conceptual_clusters
                
            except Exception as e:
                logger.error(f"Failed to add semantic layers: {e}")
                graph.semantic_layers["error"] = str(e)
    
    def shutdown(self):
        """Shutdown the knowledge integration system."""
        if self.executor:
            self.executor.shutdown(wait=True)
        
        if self.mcp_bridge:
            self.mcp_bridge.shutdown()
        
        # Clear caches
        if self.knowledge_cache:
            self.knowledge_cache.clear()
        if self.context_cache:
            self.context_cache.clear()
        if self.graph_cache:
            self.graph_cache.clear()

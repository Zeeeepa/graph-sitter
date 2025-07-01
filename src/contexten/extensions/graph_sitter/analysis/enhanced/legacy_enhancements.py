#!/usr/bin/env python3
"""
Graph-Sitter Enhancement Module

This module contains enhanced analysis functions that leverage graph-sitter's
pre-computed graph elements and advanced features for comprehensive codebase analysis.

Consolidated from the original graph_sitter_enhancements.py file.
"""

import logging
from collections import defaultdict
from typing import Dict, List, Any, Optional, Union

# Import models
from .models import (
    ImportLoop, TrainingDataItem, DeadCodeItem, GraphAnalysisResult,
    EnhancedFunctionMetrics, EnhancedClassMetrics
)

logger = logging.getLogger(__name__)

try:
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.enums import EdgeType, SymbolType
    import networkx as nx
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Dependencies not available: {e}")
    DEPENDENCIES_AVAILABLE = False
    # Create dummy classes for type hints
    class ExternalModule: pass
    class Import: pass
    class Symbol: pass
    class EdgeType: pass
    class SymbolType: pass


# ============================================================================
# CORE ENHANCEMENT FUNCTIONS
# ============================================================================

def hop_through_imports(imp: Import) -> Union[Symbol, ExternalModule]:
    """Finds the root symbol for an import by following the import chain."""
    if not DEPENDENCIES_AVAILABLE:
        return imp
    
    if isinstance(imp.imported_symbol, Import):
        return hop_through_imports(imp.imported_symbol)
    return imp.imported_symbol


def get_function_context(function) -> TrainingDataItem:
    """Extract function implementation, dependencies, and usages for ML training."""
    if not DEPENDENCIES_AVAILABLE:
        return TrainingDataItem(
            implementation={"source": "", "filepath": ""},
            dependencies=[],
            usages=[],
            metadata={}
        )
    
    context = TrainingDataItem(
        implementation={
            "source": getattr(function, 'source', ''),
            "filepath": getattr(function, 'filepath', '')
        },
        dependencies=[],
        usages=[],
        metadata={
            "name": getattr(function, 'name', ''),
            "line_start": getattr(function, 'line_start', 0),
            "line_end": getattr(function, 'line_end', 0),
            "is_async": getattr(function, 'is_async', False),
            "parameter_count": len(getattr(function, 'parameters', [])),
        }
    )

    # Add dependencies
    for dep in getattr(function, 'dependencies', []):
        # Hop through imports to find the root symbol source
        if isinstance(dep, Import):
            dep = hop_through_imports(dep)
        
        if hasattr(dep, 'source') and hasattr(dep, 'filepath'):
            context.dependencies.append({
                "source": dep.source, 
                "filepath": dep.filepath,
                "name": getattr(dep, 'name', ''),
                "type": type(dep).__name__
            })

    # Add usages
    for usage in getattr(function, 'usages', []):
        if hasattr(usage, 'usage_symbol'):
            usage_symbol = usage.usage_symbol
            if hasattr(usage_symbol, 'source') and hasattr(usage_symbol, 'filepath'):
                context.usages.append({
                    "source": usage_symbol.source,
                    "filepath": usage_symbol.filepath,
                    "name": getattr(usage_symbol, 'name', ''),
                    "type": type(usage_symbol).__name__
                })

    return context


# ============================================================================
# IMPORT LOOP DETECTION
# ============================================================================

def detect_import_loops(codebase) -> List[ImportLoop]:
    """Detect circular import dependencies using NetworkX."""
    if not DEPENDENCIES_AVAILABLE:
        logger.warning("Dependencies not available - skipping import loop detection")
        return []
    
    try:
        G = nx.MultiDiGraph()
        import_map = {}  # Track imports for each edge
        
        # Add edges for all imports
        for imp in codebase.imports:
            if hasattr(imp, 'from_file') and hasattr(imp, 'to_file') and imp.from_file and imp.to_file:
                from_path = imp.from_file.filepath
                to_path = imp.to_file.filepath
                
                edge_key = (from_path, to_path)
                if edge_key not in import_map:
                    import_map[edge_key] = []
                
                import_map[edge_key].append({
                    "import_statement": getattr(imp, 'source', ''),
                    "is_dynamic": getattr(imp, 'is_dynamic', False),
                    "line_number": getattr(imp, 'line_start', 0)
                })
                
                G.add_edge(from_path, to_path, import_obj=imp)
        
        # Find strongly connected components (import loops)
        cycles = list(nx.strongly_connected_components(G))
        import_loops = []
        
        for cycle in cycles:
            if len(cycle) > 1:  # Only actual loops
                cycle_list = list(cycle)
                
                # Determine loop type and severity
                loop_imports = []
                has_dynamic = False
                has_static = False
                
                for i in range(len(cycle_list)):
                    from_file = cycle_list[i]
                    to_file = cycle_list[(i + 1) % len(cycle_list)]
                    
                    edge_key = (from_file, to_file)
                    if edge_key in import_map:
                        for imp_info in import_map[edge_key]:
                            loop_imports.append(imp_info)
                            if imp_info["is_dynamic"]:
                                has_dynamic = True
                            else:
                                has_static = True
                
                # Determine loop type and severity
                if has_dynamic and has_static:
                    loop_type = "mixed"
                    severity = "critical"
                elif has_dynamic:
                    loop_type = "dynamic"
                    severity = "warning"
                else:
                    loop_type = "static"
                    severity = "info"
                
                import_loops.append(ImportLoop(
                    files=cycle_list,
                    loop_type=loop_type,
                    severity=severity,
                    imports=loop_imports
                ))
        
        return import_loops
        
    except Exception as e:
        logger.error(f"Error detecting import loops: {e}")
        return []


# ============================================================================
# GRAPH STRUCTURE ANALYSIS
# ============================================================================

def analyze_graph_structure(codebase) -> GraphAnalysisResult:
    """Analyze the graph structure of the codebase."""
    if not DEPENDENCIES_AVAILABLE:
        return GraphAnalysisResult(
            total_nodes=0, total_edges=0, symbol_usage_edges=0,
            import_resolution_edges=0, export_edges=0,
            strongly_connected_components=[], import_loops=[]
        )
    
    try:
        # Get basic graph metrics
        nodes = codebase.ctx.get_nodes()
        edges = codebase.ctx.edges
        
        # Count different types of edges
        symbol_usage_edges = len([x for x in edges if x[2].type == EdgeType.SYMBOL_USAGE])
        import_resolution_edges = len([x for x in edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION])
        export_edges = len([x for x in edges if x[2].type == EdgeType.EXPORT])
        
        # Find strongly connected components
        G = nx.DiGraph()
        for edge in edges:
            G.add_edge(edge[0], edge[1])
        
        strongly_connected = list(nx.strongly_connected_components(G))
        scc_lists = [list(component) for component in strongly_connected if len(component) > 1]
        
        # Detect import loops
        import_loops = detect_import_loops(codebase)
        
        return GraphAnalysisResult(
            total_nodes=len(nodes),
            total_edges=len(edges),
            symbol_usage_edges=symbol_usage_edges,
            import_resolution_edges=import_resolution_edges,
            export_edges=export_edges,
            strongly_connected_components=scc_lists,
            import_loops=import_loops
        )
        
    except Exception as e:
        logger.error(f"Error analyzing graph structure: {e}")
        return GraphAnalysisResult(
            total_nodes=0, total_edges=0, symbol_usage_edges=0,
            import_resolution_edges=0, export_edges=0,
            strongly_connected_components=[], import_loops=[]
        )


# ============================================================================
# DEAD CODE DETECTION
# ============================================================================

def detect_dead_code(codebase) -> List[DeadCodeItem]:
    """Detect unused functions, classes, and variables using usage analysis."""
    if not DEPENDENCIES_AVAILABLE:
        logger.warning("Dependencies not available - skipping dead code detection")
        return []
    
    dead_code_items = []
    
    try:
        # Check for unused functions
        for function in codebase.functions:
            if not getattr(function, 'usages', []):
                # Skip main functions and special methods
                if function.name not in ['main', '__init__', '__main__'] and not function.name.startswith('_'):
                    dead_code_items.append(DeadCodeItem(
                        type="function",
                        name=function.name,
                        file_path=getattr(function, 'filepath', ''),
                        line_start=getattr(function, 'line_start', 0),
                        line_end=getattr(function, 'line_end', 0),
                        reason="No usages found",
                        confidence=0.8
                    ))
        
        # Check for unused classes
        for cls in codebase.classes:
            if not getattr(cls, 'usages', []):
                # Skip base classes and exception classes
                if not cls.name.endswith('Base') and not cls.name.endswith('Exception'):
                    dead_code_items.append(DeadCodeItem(
                        type="class",
                        name=cls.name,
                        file_path=getattr(cls, 'filepath', ''),
                        line_start=getattr(cls, 'line_start', 0),
                        line_end=getattr(cls, 'line_end', 0),
                        reason="No usages found",
                        confidence=0.7
                    ))
        
        # Check for unused global variables
        for global_var in codebase.global_vars:
            if not getattr(global_var, 'usages', []):
                # Skip constants and configuration variables
                if not global_var.name.isupper() and not global_var.name.startswith('_'):
                    dead_code_items.append(DeadCodeItem(
                        type="variable",
                        name=global_var.name,
                        file_path=getattr(global_var, 'filepath', ''),
                        line_start=getattr(global_var, 'line_start', 0),
                        line_end=getattr(global_var, 'line_end', 0),
                        reason="No usages found",
                        confidence=0.6
                    ))
                    
    except Exception as e:
        logger.error(f"Error detecting dead code: {e}")
    
    return dead_code_items


# ============================================================================
# TRAINING DATA GENERATION
# ============================================================================

def generate_training_data(codebase) -> List[TrainingDataItem]:
    """Generate training data for LLMs using graph-sitter analysis."""
    if not DEPENDENCIES_AVAILABLE:
        return []
    
    training_data = []
    
    try:
        # Process each function in the codebase
        for function in codebase.functions:
            # Skip if function is too small or has no meaningful content
            if hasattr(function, 'source'):
                source_lines = function.source.split("\n")
                if len(source_lines) < 2:
                    continue
                
                # Get function context
                context = get_function_context(function)
                
                # Only keep functions with enough context for training
                if len(context.dependencies) + len(context.usages) > 0:
                    training_data.append(context)
                    
    except Exception as e:
        logger.error(f"Error generating training data: {e}")
    
    return training_data


# ============================================================================
# ENHANCED METRICS ANALYSIS
# ============================================================================

def analyze_function_enhanced(function) -> EnhancedFunctionMetrics:
    """Analyze a function using graph-sitter enhanced features."""
    if not DEPENDENCIES_AVAILABLE:
        return EnhancedFunctionMetrics(
            name="", file_path="", line_start=0, line_end=0,
            cyclomatic_complexity=0, halstead_volume=0.0,
            maintainability_index=0, lines_of_code=0
        )
    
    try:
        # Extract basic information
        name = getattr(function, 'name', '')
        file_path = getattr(function, 'filepath', '')
        line_start = getattr(function, 'line_start', 0)
        line_end = getattr(function, 'line_end', 0)
        
        # Calculate basic metrics (these would need to be implemented)
        cyclomatic_complexity = 1  # Placeholder
        halstead_volume = 0.0  # Placeholder
        maintainability_index = 100  # Placeholder
        lines_of_code = line_end - line_start if line_end > line_start else 0
        
        # Extract graph-sitter specific information
        dependencies = [dep.name for dep in getattr(function, 'dependencies', []) if hasattr(dep, 'name')]
        usages = [usage.name for usage in getattr(function, 'usages', []) if hasattr(usage, 'name')]
        call_sites = [site.name for site in getattr(function, 'call_sites', []) if hasattr(site, 'name')]
        function_calls = [call.name for call in getattr(function, 'function_calls', []) if hasattr(call, 'name')]
        parameters = [param.name for param in getattr(function, 'parameters', []) if hasattr(param, 'name')]
        return_statements = [stmt for stmt in getattr(function, 'return_statements', [])]
        decorators = [dec.name for dec in getattr(function, 'decorators', []) if hasattr(dec, 'name')]
        
        is_async = getattr(function, 'is_async', False)
        is_generator = getattr(function, 'is_generator', False)
        docstring = getattr(function, 'docstring', '')
        
        return EnhancedFunctionMetrics(
            name=name,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            cyclomatic_complexity=cyclomatic_complexity,
            halstead_volume=halstead_volume,
            maintainability_index=maintainability_index,
            lines_of_code=lines_of_code,
            dependencies=dependencies,
            usages=usages,
            call_sites=call_sites,
            function_calls=function_calls,
            parameters=parameters,
            return_statements=[str(stmt) for stmt in return_statements],
            decorators=decorators,
            is_async=is_async,
            is_generator=is_generator,
            docstring=docstring
        )
        
    except Exception as e:
        logger.error(f"Error analyzing function {getattr(function, 'name', 'unknown')}: {e}")
        return EnhancedFunctionMetrics(
            name=getattr(function, 'name', ''),
            file_path=getattr(function, 'filepath', ''),
            line_start=0, line_end=0,
            cyclomatic_complexity=0, halstead_volume=0.0,
            maintainability_index=0, lines_of_code=0
        )


def analyze_class_enhanced(cls) -> EnhancedClassMetrics:
    """Analyze a class using graph-sitter enhanced features."""
    if not DEPENDENCIES_AVAILABLE:
        return EnhancedClassMetrics(
            name="", file_path="", line_start=0, line_end=0,
            depth_of_inheritance=0, method_count=0,
            attribute_count=0, lines_of_code=0
        )
    
    try:
        # Extract basic information
        name = getattr(cls, 'name', '')
        file_path = getattr(cls, 'filepath', '')
        line_start = getattr(cls, 'line_start', 0)
        line_end = getattr(cls, 'line_end', 0)
        
        # Calculate basic metrics
        depth_of_inheritance = len(getattr(cls, 'superclasses', []))
        method_count = len(getattr(cls, 'methods', []))
        attribute_count = len(getattr(cls, 'attributes', []))
        lines_of_code = line_end - line_start if line_end > line_start else 0
        
        # Extract graph-sitter specific information
        parent_classes = [parent.name for parent in getattr(cls, 'superclasses', []) if hasattr(parent, 'name')]
        subclasses = [sub.name for sub in getattr(cls, 'subclasses', []) if hasattr(sub, 'name')]
        methods = [method.name for method in getattr(cls, 'methods', []) if hasattr(method, 'name')]
        attributes = [attr.name for attr in getattr(cls, 'attributes', []) if hasattr(attr, 'name')]
        decorators = [dec.name for dec in getattr(cls, 'decorators', []) if hasattr(dec, 'name')]
        usages = [usage.name for usage in getattr(cls, 'usages', []) if hasattr(usage, 'name')]
        dependencies = [dep.name for dep in getattr(cls, 'dependencies', []) if hasattr(dep, 'name')]
        
        is_abstract = getattr(cls, 'is_abstract', False)
        
        return EnhancedClassMetrics(
            name=name,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            depth_of_inheritance=depth_of_inheritance,
            method_count=method_count,
            attribute_count=attribute_count,
            lines_of_code=lines_of_code,
            parent_classes=parent_classes,
            subclasses=subclasses,
            methods=methods,
            attributes=attributes,
            decorators=decorators,
            usages=usages,
            dependencies=dependencies,
            is_abstract=is_abstract
        )
        
    except Exception as e:
        logger.error(f"Error analyzing class {getattr(cls, 'name', 'unknown')}: {e}")
        return EnhancedClassMetrics(
            name=getattr(cls, 'name', ''),
            file_path=getattr(cls, 'filepath', ''),
            line_start=0, line_end=0,
            depth_of_inheritance=0, method_count=0,
            attribute_count=0, lines_of_code=0
        )


# ============================================================================
# ENHANCED SUMMARY FUNCTIONS
# ============================================================================

def get_codebase_summary_enhanced(codebase) -> Dict[str, Any]:
    """Get enhanced codebase summary using graph-sitter features."""
    if not DEPENDENCIES_AVAILABLE:
        return {"error": "Graph-sitter dependencies not available"}
    
    try:
        summary = {
            "basic_metrics": {
                "total_files": len(list(codebase.files)),
                "total_functions": len(list(codebase.functions)),
                "total_classes": len(list(codebase.classes)),
                "total_imports": len(list(codebase.imports)),
                "total_symbols": len(list(codebase.symbols)),
                "external_modules": len(list(codebase.external_modules)),
                "global_variables": len(list(codebase.global_vars)),
                "interfaces": len(list(codebase.interfaces)) if hasattr(codebase, 'interfaces') else 0,
            },
            "graph_metrics": {},
            "analysis_results": {
                "dead_code_items": len(detect_dead_code(codebase)),
                "import_loops": len(detect_import_loops(codebase)),
                "training_data_functions": len(generate_training_data(codebase)),
            }
        }
        
        # Add graph analysis if available
        graph_analysis = analyze_graph_structure(codebase)
        summary["graph_metrics"] = {
            "total_nodes": graph_analysis.total_nodes,
            "total_edges": graph_analysis.total_edges,
            "symbol_usage_edges": graph_analysis.symbol_usage_edges,
            "import_resolution_edges": graph_analysis.import_resolution_edges,
            "export_edges": graph_analysis.export_edges,
            "strongly_connected_components": len(graph_analysis.strongly_connected_components),
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error generating enhanced codebase summary: {e}")
        return {"error": str(e)}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def generate_import_loop_recommendations(import_loops: List[ImportLoop]) -> List[str]:
    """Generate recommendations for fixing import loops."""
    recommendations = []
    
    critical_loops = [loop for loop in import_loops if loop.severity == "critical"]
    if critical_loops:
        recommendations.append("🚨 Critical: Fix mixed static/dynamic import loops immediately")
        recommendations.append("Consider using dependency injection or factory patterns")
    
    if len(import_loops) > 5:
        recommendations.append("📊 High number of import loops detected - consider architectural refactoring")
    
    if import_loops:
        recommendations.append("💡 Consider moving shared code to separate modules")
        recommendations.append("🔄 Use lazy imports where appropriate")
    
    return recommendations


def generate_dead_code_recommendations(dead_code_items: List[DeadCodeItem]) -> List[str]:
    """Generate recommendations for handling dead code."""
    recommendations = []
    
    high_confidence_items = [item for item in dead_code_items if item.confidence > 0.7]
    if high_confidence_items:
        recommendations.append(f"🗑️ {len(high_confidence_items)} high-confidence dead code items can be safely removed")
    
    if len(dead_code_items) > 10:
        recommendations.append("📈 Consider implementing automated dead code removal in CI/CD")
    
    if dead_code_items:
        recommendations.append("🔍 Review dead code items before removal - some may be used dynamically")
        recommendations.append("📝 Update documentation to reflect removed functionality")
    
    return recommendations


def generate_graph_insights(graph_analysis: GraphAnalysisResult) -> List[str]:
    """Generate insights from graph analysis."""
    insights = []
    
    if graph_analysis.total_nodes > 1000:
        insights.append(f"📊 Large codebase with {graph_analysis.total_nodes:,} nodes")
    
    edge_ratio = graph_analysis.total_edges / graph_analysis.total_nodes if graph_analysis.total_nodes > 0 else 0
    if edge_ratio > 3:
        insights.append(f"🔗 High connectivity (edge ratio: {edge_ratio:.1f}) - well-connected codebase")
    elif edge_ratio < 1:
        insights.append(f"🔗 Low connectivity (edge ratio: {edge_ratio:.1f}) - loosely coupled modules")
    
    if graph_analysis.import_loops:
        insights.append(f"🔄 {len(graph_analysis.import_loops)} import loops detected")
    
    return insights


def generate_graph_recommendations(graph_analysis: GraphAnalysisResult) -> List[str]:
    """Generate recommendations from graph analysis."""
    recommendations = []
    
    if graph_analysis.strongly_connected_components:
        recommendations.append("🔄 Consider breaking up strongly connected components")
    
    if graph_analysis.symbol_usage_edges < graph_analysis.total_edges * 0.3:
        recommendations.append("📊 Low symbol usage ratio - consider code organization review")
    
    return recommendations


#!/usr/bin/env python3
"""
🔧 ENHANCED GRAPH-SITTER INTEGRATION 🔧

This module provides enhanced integration with graph-sitter's advanced features,
consolidating functionality from graph_sitter_enhancements.py and enhanced_analyzer.py.

Features:
- Pre-computed graph element access
- Advanced function and class metrics
- Enhanced dependency analysis
- Tree-sitter query patterns
- Performance optimizations
"""

import logging
import ast
import math
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union, Set

logger = logging.getLogger(__name__)

try:
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import Class
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
    class Function: pass
    class Class: pass
    class EdgeType: pass
    class SymbolType: pass


@dataclass
class EnhancedFunctionMetrics:
    """Enhanced function metrics using graph-sitter."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    
    # Basic metrics
    cyclomatic_complexity: int = 0
    halstead_volume: float = 0.0
    maintainability_index: int = 0
    lines_of_code: int = 0
    
    # Graph-sitter enhanced metrics
    dependencies: List[str] = field(default_factory=list)
    usages: List[str] = field(default_factory=list)
    call_sites: List[str] = field(default_factory=list)
    function_calls: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    return_statements: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_method: bool = False
    is_property: bool = False
    is_static: bool = False
    is_class_method: bool = False


@dataclass
class EnhancedClassMetrics:
    """Enhanced class metrics using graph-sitter."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    
    # Basic metrics
    methods_count: int = 0
    attributes_count: int = 0
    inheritance_depth: int = 0
    coupling: int = 0
    cohesion: float = 0.0
    
    # Graph-sitter enhanced metrics
    dependencies: List[str] = field(default_factory=list)
    usages: List[str] = field(default_factory=list)
    superclasses: List[str] = field(default_factory=list)
    subclasses: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_abstract: bool = False
    is_dataclass: bool = False


def get_codebase_summary_enhanced(codebase) -> Dict[str, Any]:
    """Get enhanced codebase summary using graph-sitter features."""
    if not DEPENDENCIES_AVAILABLE:
        return {"error": "Dependencies not available"}
    
    try:
        summary = {
            "basic_stats": {
                "total_files": len(codebase.files),
                "total_functions": len(codebase.functions),
                "total_classes": len(codebase.classes),
                "total_imports": len(codebase.imports),
                "total_symbols": len(codebase.symbols)
            },
            "file_analysis": {},
            "symbol_distribution": {},
            "complexity_metrics": {},
            "dependency_analysis": {}
        }
        
        # File analysis
        file_extensions = Counter()
        total_lines = 0
        
        for file in codebase.files:
            ext = file.filepath.suffix if hasattr(file.filepath, 'suffix') else ''
            file_extensions[ext] += 1
            
            if hasattr(file, 'source'):
                total_lines += len(file.source.splitlines())
        
        summary["file_analysis"] = {
            "extensions": dict(file_extensions),
            "total_lines_of_code": total_lines,
            "average_lines_per_file": total_lines / len(codebase.files) if codebase.files else 0
        }
        
        # Symbol distribution
        symbol_types = Counter()
        for symbol in codebase.symbols:
            symbol_types[symbol.__class__.__name__] += 1
        
        summary["symbol_distribution"] = dict(symbol_types)
        
        # Complexity metrics
        function_complexities = []
        for function in codebase.functions:
            complexity = calculate_cyclomatic_complexity(function)
            function_complexities.append(complexity)
        
        if function_complexities:
            summary["complexity_metrics"] = {
                "average_cyclomatic_complexity": sum(function_complexities) / len(function_complexities),
                "max_cyclomatic_complexity": max(function_complexities),
                "functions_over_10_complexity": len([c for c in function_complexities if c > 10])
            }
        
        # Dependency analysis
        import_count = len(codebase.imports)
        external_imports = 0
        internal_imports = 0
        
        for imp in codebase.imports:
            if hasattr(imp, 'resolved_symbol') and imp.resolved_symbol:
                if isinstance(imp.resolved_symbol, ExternalModule):
                    external_imports += 1
                else:
                    internal_imports += 1
        
        summary["dependency_analysis"] = {
            "total_imports": import_count,
            "external_imports": external_imports,
            "internal_imports": internal_imports,
            "import_ratio": external_imports / import_count if import_count > 0 else 0
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting enhanced summary: {e}")
        return {"error": str(e)}


def analyze_function_enhanced(function) -> EnhancedFunctionMetrics:
    """Analyze a function with enhanced graph-sitter metrics."""
    if not DEPENDENCIES_AVAILABLE:
        return EnhancedFunctionMetrics("", "", 0, 0)
    
    try:
        metrics = EnhancedFunctionMetrics(
            name=function.name,
            file_path=str(function.filepath) if hasattr(function, 'filepath') else '',
            line_start=function.start_point[0] if hasattr(function, 'start_point') else 0,
            line_end=function.end_point[0] if hasattr(function, 'end_point') else 0
        )
        
        # Basic metrics
        metrics.cyclomatic_complexity = calculate_cyclomatic_complexity(function)
        metrics.halstead_volume = calculate_halstead_volume(function)
        metrics.maintainability_index = calculate_maintainability_index(function)
        metrics.lines_of_code = calculate_lines_of_code(function)
        
        # Graph-sitter enhanced metrics
        if hasattr(function, 'dependencies'):
            metrics.dependencies = [str(dep) for dep in function.dependencies]
        
        if hasattr(function, 'usages'):
            metrics.usages = [str(usage) for usage in function.usages]
        
        if hasattr(function, 'call_sites'):
            metrics.call_sites = [str(call) for call in function.call_sites]
        
        if hasattr(function, 'function_calls'):
            metrics.function_calls = [str(call) for call in function.function_calls]
        
        if hasattr(function, 'parameters'):
            metrics.parameters = [param.name for param in function.parameters]
        
        if hasattr(function, 'decorators'):
            metrics.decorators = [dec.name for dec in function.decorators]
        
        # Function properties
        metrics.is_async = getattr(function, 'is_async', False)
        metrics.is_method = getattr(function, 'is_method', False)
        metrics.is_property = getattr(function, 'is_property', False)
        metrics.is_static = getattr(function, 'is_static', False)
        metrics.is_class_method = getattr(function, 'is_class_method', False)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error analyzing function {function.name}: {e}")
        return EnhancedFunctionMetrics(function.name, "", 0, 0)


def analyze_class_enhanced(cls) -> EnhancedClassMetrics:
    """Analyze a class with enhanced graph-sitter metrics."""
    if not DEPENDENCIES_AVAILABLE:
        return EnhancedClassMetrics("", "", 0, 0)
    
    try:
        metrics = EnhancedClassMetrics(
            name=cls.name,
            file_path=str(cls.filepath) if hasattr(cls, 'filepath') else '',
            line_start=cls.start_point[0] if hasattr(cls, 'start_point') else 0,
            line_end=cls.end_point[0] if hasattr(cls, 'end_point') else 0
        )
        
        # Basic metrics
        if hasattr(cls, 'methods'):
            metrics.methods_count = len(cls.methods)
            metrics.methods = [method.name for method in cls.methods]
        
        if hasattr(cls, 'attributes'):
            metrics.attributes_count = len(cls.attributes)
            metrics.attributes = [attr.name for attr in cls.attributes]
        
        # Inheritance analysis
        if hasattr(cls, 'superclasses'):
            metrics.superclasses = [sc.name for sc in cls.superclasses]
            metrics.inheritance_depth = len(cls.superclasses)
        
        if hasattr(cls, 'subclasses'):
            metrics.subclasses = [sc.name for sc in cls.subclasses]
        
        # Graph-sitter enhanced metrics
        if hasattr(cls, 'dependencies'):
            metrics.dependencies = [str(dep) for dep in cls.dependencies]
        
        if hasattr(cls, 'usages'):
            metrics.usages = [str(usage) for usage in cls.usages]
        
        if hasattr(cls, 'decorators'):
            metrics.decorators = [dec.name for dec in cls.decorators]
        
        # Calculate coupling and cohesion
        metrics.coupling = calculate_class_coupling(cls)
        metrics.cohesion = calculate_class_cohesion(cls)
        
        # Class properties
        metrics.is_abstract = is_abstract_class(cls)
        metrics.is_dataclass = is_dataclass(cls)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error analyzing class {cls.name}: {e}")
        return EnhancedClassMetrics(cls.name, "", 0, 0)


def calculate_cyclomatic_complexity(function) -> int:
    """Calculate cyclomatic complexity of a function."""
    try:
        if not hasattr(function, 'source'):
            return 1
        
        source = function.source
        tree = ast.parse(source)
        
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(node, ast.comprehension):
                complexity += 1
        
        return complexity
        
    except Exception:
        return 1


def calculate_halstead_volume(function) -> float:
    """Calculate Halstead volume metric."""
    try:
        if not hasattr(function, 'source'):
            return 0.0
        
        source = function.source
        tree = ast.parse(source)
        
        operators = set()
        operands = set()
        total_operators = 0
        total_operands = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.operator):
                operators.add(type(node).__name__)
                total_operators += 1
            elif isinstance(node, (ast.Name, ast.Constant)):
                operands.add(str(node))
                total_operands += 1
        
        n1 = len(operators)  # Unique operators
        n2 = len(operands)   # Unique operands
        N1 = total_operators # Total operators
        N2 = total_operands  # Total operands
        
        if n1 + n2 == 0:
            return 0.0
        
        vocabulary = n1 + n2
        length = N1 + N2
        
        if vocabulary <= 0:
            return 0.0
        
        volume = length * math.log2(vocabulary)
        return volume
        
    except Exception:
        return 0.0


def calculate_maintainability_index(function) -> int:
    """Calculate maintainability index."""
    try:
        halstead_volume = calculate_halstead_volume(function)
        cyclomatic_complexity = calculate_cyclomatic_complexity(function)
        lines_of_code = calculate_lines_of_code(function)
        
        if lines_of_code == 0:
            return 100
        
        # Simplified maintainability index calculation
        mi = 171 - 5.2 * math.log(halstead_volume) - 0.23 * cyclomatic_complexity - 16.2 * math.log(lines_of_code)
        
        # Normalize to 0-100 scale
        mi = max(0, min(100, int(mi)))
        
        return mi
        
    except Exception:
        return 50  # Default moderate maintainability


def calculate_lines_of_code(function) -> int:
    """Calculate lines of code for a function."""
    try:
        if hasattr(function, 'source'):
            return len([line for line in function.source.splitlines() if line.strip()])
        elif hasattr(function, 'start_point') and hasattr(function, 'end_point'):
            return function.end_point[0] - function.start_point[0] + 1
        else:
            return 0
    except Exception:
        return 0


def calculate_class_coupling(cls) -> int:
    """Calculate coupling metric for a class."""
    try:
        coupling = 0
        
        if hasattr(cls, 'dependencies'):
            coupling += len(cls.dependencies)
        
        if hasattr(cls, 'usages'):
            coupling += len(cls.usages)
        
        return coupling
        
    except Exception:
        return 0


def calculate_class_cohesion(cls) -> float:
    """Calculate cohesion metric for a class."""
    try:
        if not hasattr(cls, 'methods') or len(cls.methods) == 0:
            return 1.0
        
        # Simplified cohesion calculation based on method interactions
        method_interactions = 0
        total_possible_interactions = len(cls.methods) * (len(cls.methods) - 1)
        
        if total_possible_interactions == 0:
            return 1.0
        
        # Count method calls between methods in the same class
        for method in cls.methods:
            if hasattr(method, 'function_calls'):
                for call in method.function_calls:
                    if hasattr(call, 'resolved_symbol'):
                        if call.resolved_symbol in cls.methods:
                            method_interactions += 1
        
        cohesion = method_interactions / total_possible_interactions
        return min(1.0, cohesion)
        
    except Exception:
        return 0.5  # Default moderate cohesion


def is_abstract_class(cls) -> bool:
    """Check if a class is abstract."""
    try:
        if hasattr(cls, 'decorators'):
            for decorator in cls.decorators:
                if 'abstractmethod' in str(decorator) or 'ABC' in str(decorator):
                    return True
        
        if hasattr(cls, 'superclasses'):
            for superclass in cls.superclasses:
                if 'ABC' in superclass.name or 'Abstract' in superclass.name:
                    return True
        
        return False
        
    except Exception:
        return False


def is_dataclass(cls) -> bool:
    """Check if a class is a dataclass."""
    try:
        if hasattr(cls, 'decorators'):
            for decorator in cls.decorators:
                if 'dataclass' in str(decorator):
                    return True
        
        return False
        
    except Exception:
        return False


def get_function_context(function) -> Dict[str, Any]:
    """Get comprehensive context for a function."""
    if not DEPENDENCIES_AVAILABLE:
        return {}
    
    try:
        context = {
            "implementation": {
                "source": getattr(function, 'source', ''),
                "filepath": str(getattr(function, 'filepath', ''))
            },
            "dependencies": [],
            "usages": [],
            "metrics": {}
        }
        
        # Add dependencies
        if hasattr(function, 'dependencies'):
            for dep in function.dependencies:
                dep_info = {
                    "name": getattr(dep, 'name', str(dep)),
                    "type": dep.__class__.__name__,
                    "filepath": str(getattr(dep, 'filepath', ''))
                }
                context["dependencies"].append(dep_info)
        
        # Add usages
        if hasattr(function, 'usages'):
            for usage in function.usages:
                usage_info = {
                    "filepath": str(getattr(usage, 'filepath', '')),
                    "line": getattr(usage, 'start_point', [0])[0]
                }
                context["usages"].append(usage_info)
        
        # Add metrics
        metrics = analyze_function_enhanced(function)
        context["metrics"] = {
            "cyclomatic_complexity": metrics.cyclomatic_complexity,
            "halstead_volume": metrics.halstead_volume,
            "maintainability_index": metrics.maintainability_index,
            "lines_of_code": metrics.lines_of_code,
            "is_async": metrics.is_async,
            "is_method": metrics.is_method,
            "parameter_count": len(metrics.parameters)
        }
        
        return context
        
    except Exception as e:
        logger.error(f"Error getting function context: {e}")
        return {}


def analyze_graph_structure(codebase) -> Dict[str, Any]:
    """Analyze the graph structure of the codebase."""
    if not DEPENDENCIES_AVAILABLE:
        return {}
    
    try:
        analysis = {
            "basic_metrics": {},
            "connectivity": {},
            "centrality": {},
            "components": {}
        }
        
        # Build a graph from the codebase
        graph = nx.DiGraph()
        
        # Add nodes for all symbols
        for symbol in codebase.symbols:
            graph.add_node(symbol.name, type=symbol.__class__.__name__)
        
        # Add edges for dependencies
        for symbol in codebase.symbols:
            if hasattr(symbol, 'dependencies'):
                for dep in symbol.dependencies:
                    if hasattr(dep, 'name'):
                        graph.add_edge(symbol.name, dep.name)
        
        # Basic metrics
        analysis["basic_metrics"] = {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "density": nx.density(graph),
            "is_connected": nx.is_weakly_connected(graph)
        }
        
        # Connectivity analysis
        if graph.number_of_nodes() > 0:
            try:
                strongly_connected = list(nx.strongly_connected_components(graph))
                weakly_connected = list(nx.weakly_connected_components(graph))
                
                analysis["connectivity"] = {
                    "strongly_connected_components": len(strongly_connected),
                    "weakly_connected_components": len(weakly_connected),
                    "largest_scc_size": max(len(comp) for comp in strongly_connected) if strongly_connected else 0,
                    "largest_wcc_size": max(len(comp) for comp in weakly_connected) if weakly_connected else 0
                }
            except Exception as e:
                logger.warning(f"Error analyzing connectivity: {e}")
        
        # Centrality analysis (for smaller graphs)
        if graph.number_of_nodes() < 1000:
            try:
                in_degree_centrality = nx.in_degree_centrality(graph)
                out_degree_centrality = nx.out_degree_centrality(graph)
                
                analysis["centrality"] = {
                    "max_in_degree": max(in_degree_centrality.values()) if in_degree_centrality else 0,
                    "max_out_degree": max(out_degree_centrality.values()) if out_degree_centrality else 0,
                    "avg_in_degree": sum(in_degree_centrality.values()) / len(in_degree_centrality) if in_degree_centrality else 0,
                    "avg_out_degree": sum(out_degree_centrality.values()) / len(out_degree_centrality) if out_degree_centrality else 0
                }
            except Exception as e:
                logger.warning(f"Error analyzing centrality: {e}")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing graph structure: {e}")
        return {}

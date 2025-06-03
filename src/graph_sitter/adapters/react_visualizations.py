"""
React-based Visualizations for Comprehensive Codebase Analysis

This module provides React-compatible visualization components that integrate
with the existing analysis system to create interactive, dynamic visualizations
for all types of codebase analysis including the three core patterns:
1. Class method relationships
2. Function blast radius  
3. Symbol dependencies
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
import networkx as nx

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.symbol import Symbol
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.detached_symbols.function_call import FunctionCall
from graph_sitter.core.dataclasses.usage import Usage
from graph_sitter.core.import_resolution import Import
from graph_sitter.python.function import PyFunction
from graph_sitter.python.symbol import PySymbol

# Color palette for different visualization types
COLOR_PALETTE = {
    "StartMethod": "#9CDCFE",      # Light blue for root/entry point methods
    "PyFunction": "#A277FF",       # Purple for regular Python functions
    "PyClass": "#FFCA85",          # Warm peach for class definitions
    "ExternalModule": "#F694FF",   # Pink for external module calls
    "StartClass": "#FFE082",       # Yellow for the starting class
    "StartFunction": "#9CDCFE",    # Starting function (light blue)
    "HTTP_METHOD": "#FFCA85",      # HTTP method handlers (orange)
    "Critical": "#FF6B6B",         # Critical issues (red)
    "Warning": "#FFD93D",          # Warning issues (yellow)
    "Info": "#6BCF7F",             # Info/success (green)
    "Dependency": "#A8E6CF",       # Dependencies (light green)
    "Usage": "#FFB3BA",            # Usages (light red)
    "Import": "#B3D9FF",           # Imports (light blue)
}

HTTP_METHODS = ["get", "put", "patch", "post", "head", "delete"]

@dataclass
class VisualizationNode:
    """Represents a node in the visualization graph"""
    id: str
    label: str
    type: str
    color: str
    size: int = 10
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass 
class VisualizationEdge:
    """Represents an edge in the visualization graph"""
    source: str
    target: str
    label: str = ""
    type: str = "default"
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class VisualizationData:
    """Complete visualization data structure"""
    nodes: List[VisualizationNode]
    edges: List[VisualizationEdge]
    metadata: Dict[str, Any]
    layout_config: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'nodes': [node.to_dict() for node in self.nodes],
            'edges': [edge.to_dict() for edge in self.edges],
            'metadata': self.metadata,
            'layout_config': self.layout_config
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

class ReactVisualizationGenerator:
    """
    Generates React-compatible visualization data for comprehensive codebase analysis.
    
    This class integrates all visualization patterns and provides a unified interface
    for generating interactive React visualizations.
    """
    
    def __init__(self, max_depth: int = 10, ignore_external_modules: bool = True):
        self.max_depth = max_depth
        self.ignore_external_modules = ignore_external_modules
        self.visited = set()
        
    def generate_comprehensive_visualization(self, codebase: Codebase, 
                                           target_element: Optional[Union[Class, Function, Symbol]] = None,
                                           visualization_types: List[str] = None) -> Dict[str, VisualizationData]:
        """
        Generate comprehensive visualizations for all analysis types.
        
        Args:
            codebase: The codebase to analyze
            target_element: Optional specific element to focus on
            visualization_types: List of visualization types to generate
            
        Returns:
            Dictionary mapping visualization type to VisualizationData
        """
        if visualization_types is None:
            visualization_types = [
                'class_method_relationships',
                'function_blast_radius', 
                'symbol_dependencies',
                'call_graph',
                'dependency_graph',
                'complexity_heatmap',
                'issue_dashboard',
                'metrics_overview'
            ]
        
        visualizations = {}
        
        for viz_type in visualization_types:
            try:
                if viz_type == 'class_method_relationships':
                    visualizations[viz_type] = self.generate_class_method_visualization(codebase, target_element)
                elif viz_type == 'function_blast_radius':
                    visualizations[viz_type] = self.generate_blast_radius_visualization(codebase, target_element)
                elif viz_type == 'symbol_dependencies':
                    visualizations[viz_type] = self.generate_symbol_dependencies_visualization(codebase, target_element)
                elif viz_type == 'call_graph':
                    visualizations[viz_type] = self.generate_call_graph_visualization(codebase)
                elif viz_type == 'dependency_graph':
                    visualizations[viz_type] = self.generate_dependency_graph_visualization(codebase)
                elif viz_type == 'complexity_heatmap':
                    visualizations[viz_type] = self.generate_complexity_heatmap(codebase)
                elif viz_type == 'issue_dashboard':
                    visualizations[viz_type] = self.generate_issue_dashboard(codebase)
                elif viz_type == 'metrics_overview':
                    visualizations[viz_type] = self.generate_metrics_overview(codebase)
            except Exception as e:
                print(f"Error generating {viz_type}: {e}")
                continue
                
        return visualizations
    
    def generate_class_method_visualization(self, codebase: Codebase, 
                                          target_class: Optional[Class] = None) -> VisualizationData:
        """
        Generate visualization for class method relationships.
        Based on the first pattern: visualize-class-method-relationships
        """
        nodes = []
        edges = []
        self.visited.clear()
        
        # Find target class or use first available class
        if target_class is None:
            classes = list(codebase.classes)
            if not classes:
                return VisualizationData([], [], {}, {})
            target_class = classes[0]
        
        # Add the main class node
        class_id = f"class_{target_class.name}_{id(target_class)}"
        nodes.append(VisualizationNode(
            id=class_id,
            label=target_class.name,
            type="StartClass",
            color=COLOR_PALETTE["StartClass"],
            size=20,
            metadata={"type": "class", "methods_count": len(target_class.methods)}
        ))
        
        # Add method nodes and edges
        for method in target_class.methods:
            method_id = f"method_{method.name}_{id(method)}"
            method_name = f"{target_class.name}.{method.name}"
            
            nodes.append(VisualizationNode(
                id=method_id,
                label=method_name,
                type="StartMethod",
                color=COLOR_PALETTE["StartMethod"],
                size=15,
                metadata={
                    "type": "method",
                    "function_calls": len(method.function_calls),
                    "parameters": len(method.parameters)
                }
            ))
            
            edges.append(VisualizationEdge(
                source=class_id,
                target=method_id,
                label="contains",
                type="containment"
            ))
            
            self.visited.add(method)
            
            # Add downstream call traces for each method
            self._add_downstream_calls(method, method_id, nodes, edges, 0)
        
        return VisualizationData(
            nodes=nodes,
            edges=edges,
            metadata={
                "visualization_type": "class_method_relationships",
                "target_class": target_class.name,
                "total_methods": len(target_class.methods),
                "generated_at": datetime.utcnow().isoformat()
            },
            layout_config={
                "algorithm": "hierarchical",
                "direction": "TB",
                "spacing": 100
            }
        )
    
    def generate_blast_radius_visualization(self, codebase: Codebase,
                                          target_function: Optional[Function] = None) -> VisualizationData:
        """
        Generate visualization for function blast radius.
        Based on the second pattern: visualize-function-blast-radius
        """
        nodes = []
        edges = []
        
        # Find target function or use first available function
        if target_function is None:
            functions = list(codebase.functions)
            if not functions:
                return VisualizationData([], [], {}, {})
            target_function = functions[0]
        
        # Add the starting function node
        func_id = f"func_{target_function.name}_{id(target_function)}"
        nodes.append(VisualizationNode(
            id=func_id,
            label=target_function.name,
            type="StartFunction",
            color=COLOR_PALETTE["StartFunction"],
            size=20,
            metadata={
                "type": "function",
                "usages_count": len(target_function.usages) if hasattr(target_function, 'usages') else 0
            }
        ))
        
        # Build blast radius visualization
        self._build_blast_radius(target_function, func_id, nodes, edges, 0)
        
        return VisualizationData(
            nodes=nodes,
            edges=edges,
            metadata={
                "visualization_type": "function_blast_radius",
                "target_function": target_function.name,
                "blast_radius_size": len(nodes) - 1,
                "generated_at": datetime.utcnow().isoformat()
            },
            layout_config={
                "algorithm": "force",
                "center_node": func_id,
                "repulsion": 200
            }
        )
    
    def generate_symbol_dependencies_visualization(self, codebase: Codebase,
                                                 target_symbol: Optional[Symbol] = None) -> VisualizationData:
        """
        Generate visualization for symbol dependencies.
        Based on the third pattern: visualize-symbol-dependencies
        """
        nodes = []
        edges = []
        
        # Find target symbol or use first available symbol
        if target_symbol is None:
            symbols = list(codebase.symbols)
            if not symbols:
                return VisualizationData([], [], {}, {})
            target_symbol = symbols[0]
        
        # Add the starting symbol node
        symbol_id = f"symbol_{target_symbol.name}_{id(target_symbol)}"
        nodes.append(VisualizationNode(
            id=symbol_id,
            label=target_symbol.name,
            type="StartFunction",
            color=COLOR_PALETTE["StartFunction"],
            size=20,
            metadata={
                "type": "symbol",
                "dependencies_count": len(target_symbol.dependencies)
            }
        ))
        
        # Build dependencies visualization
        self._build_dependencies_visualization(target_symbol, symbol_id, nodes, edges, 0)
        
        return VisualizationData(
            nodes=nodes,
            edges=edges,
            metadata={
                "visualization_type": "symbol_dependencies",
                "target_symbol": target_symbol.name,
                "dependencies_count": len(nodes) - 1,
                "generated_at": datetime.utcnow().isoformat()
            },
            layout_config={
                "algorithm": "hierarchical",
                "direction": "LR",
                "spacing": 150
            }
        )
    
    def generate_call_graph_visualization(self, codebase: Codebase) -> VisualizationData:
        """Generate comprehensive call graph visualization"""
        nodes = []
        edges = []
        
        # Add all functions as nodes
        for func in codebase.functions:
            func_id = f"func_{func.name}_{id(func)}"
            nodes.append(VisualizationNode(
                id=func_id,
                label=func.name,
                type="PyFunction",
                color=COLOR_PALETTE["PyFunction"],
                size=10 + len(func.function_calls),
                metadata={
                    "type": "function",
                    "calls_count": len(func.function_calls),
                    "parameters": len(func.parameters)
                }
            ))
            
            # Add edges for function calls
            for call in func.function_calls:
                if call.function_definition:
                    target_id = f"func_{call.function_definition.name}_{id(call.function_definition)}"
                    edges.append(VisualizationEdge(
                        source=func_id,
                        target=target_id,
                        label="calls",
                        type="function_call",
                        metadata={"call_name": call.name}
                    ))
        
        return VisualizationData(
            nodes=nodes,
            edges=edges,
            metadata={
                "visualization_type": "call_graph",
                "total_functions": len(nodes),
                "total_calls": len(edges),
                "generated_at": datetime.utcnow().isoformat()
            },
            layout_config={
                "algorithm": "force",
                "repulsion": 300,
                "attraction": 0.1
            }
        )
    
    def generate_dependency_graph_visualization(self, codebase: Codebase) -> VisualizationData:
        """Generate dependency graph visualization"""
        nodes = []
        edges = []
        
        # Add files as nodes
        for file in codebase.files:
            file_id = f"file_{file.name}_{id(file)}"
            nodes.append(VisualizationNode(
                id=file_id,
                label=file.name,
                type="File",
                color=COLOR_PALETTE["Info"],
                size=10 + len(file.imports),
                metadata={
                    "type": "file",
                    "imports_count": len(file.imports),
                    "functions_count": len(file.functions)
                }
            ))
            
            # Add edges for imports
            for imp in file.imports:
                if imp.imported_symbol and hasattr(imp.imported_symbol, 'filepath'):
                    target_id = f"file_{imp.imported_symbol.filepath}_{id(imp.imported_symbol)}"
                    edges.append(VisualizationEdge(
                        source=file_id,
                        target=target_id,
                        label="imports",
                        type="import",
                        metadata={"import_name": imp.name}
                    ))
        
        return VisualizationData(
            nodes=nodes,
            edges=edges,
            metadata={
                "visualization_type": "dependency_graph",
                "total_files": len(nodes),
                "total_imports": len(edges),
                "generated_at": datetime.utcnow().isoformat()
            },
            layout_config={
                "algorithm": "circular",
                "spacing": 200
            }
        )
    
    def generate_complexity_heatmap(self, codebase: Codebase) -> VisualizationData:
        """Generate complexity heatmap visualization"""
        nodes = []
        
        # Calculate complexity for each function
        for func in codebase.functions:
            complexity = self._calculate_function_complexity(func)
            color = self._get_complexity_color(complexity)
            
            func_id = f"func_{func.name}_{id(func)}"
            nodes.append(VisualizationNode(
                id=func_id,
                label=func.name,
                type="ComplexityNode",
                color=color,
                size=10 + complexity,
                metadata={
                    "type": "function",
                    "complexity": complexity,
                    "file": func.filepath if hasattr(func, 'filepath') else 'unknown'
                }
            ))
        
        return VisualizationData(
            nodes=nodes,
            edges=[],
            metadata={
                "visualization_type": "complexity_heatmap",
                "total_functions": len(nodes),
                "avg_complexity": sum(node.metadata.get('complexity', 0) for node in nodes) / len(nodes) if nodes else 0,
                "generated_at": datetime.utcnow().isoformat()
            },
            layout_config={
                "algorithm": "grid",
                "columns": 10
            }
        )
    
    def generate_issue_dashboard(self, codebase: Codebase) -> VisualizationData:
        """Generate issue dashboard visualization"""
        nodes = []
        edges = []
        
        # Analyze issues in the codebase
        issues = self._analyze_codebase_issues(codebase)
        
        for issue in issues:
            issue_id = f"issue_{issue['id']}"
            color = COLOR_PALETTE.get(issue['severity'], COLOR_PALETTE["Info"])
            
            nodes.append(VisualizationNode(
                id=issue_id,
                label=issue['title'],
                type=f"Issue_{issue['severity']}",
                color=color,
                size=15 if issue['severity'] == 'Critical' else 10,
                metadata=issue
            ))
            
            # Connect issues to affected elements
            if issue.get('affected_element'):
                element_id = f"element_{issue['affected_element']}"
                edges.append(VisualizationEdge(
                    source=issue_id,
                    target=element_id,
                    label="affects",
                    type="issue_relation"
                ))
        
        return VisualizationData(
            nodes=nodes,
            edges=edges,
            metadata={
                "visualization_type": "issue_dashboard",
                "total_issues": len(nodes),
                "critical_issues": len([n for n in nodes if n.metadata.get('severity') == 'Critical']),
                "generated_at": datetime.utcnow().isoformat()
            },
            layout_config={
                "algorithm": "force",
                "groupBy": "severity"
            }
        )
    
    def generate_metrics_overview(self, codebase: Codebase) -> VisualizationData:
        """Generate metrics overview visualization"""
        nodes = []
        
        # Calculate various metrics
        metrics = {
            "total_files": len(list(codebase.files)),
            "total_functions": len(list(codebase.functions)),
            "total_classes": len(list(codebase.classes)),
            "total_imports": len(list(codebase.imports)),
            "avg_complexity": self._calculate_average_complexity(codebase)
        }
        
        # Create metric nodes
        for metric_name, value in metrics.items():
            metric_id = f"metric_{metric_name}"
            nodes.append(VisualizationNode(
                id=metric_id,
                label=f"{metric_name}: {value}",
                type="Metric",
                color=COLOR_PALETTE["Info"],
                size=15,
                metadata={
                    "type": "metric",
                    "name": metric_name,
                    "value": value
                }
            ))
        
        return VisualizationData(
            nodes=nodes,
            edges=[],
            metadata={
                "visualization_type": "metrics_overview",
                "metrics": metrics,
                "generated_at": datetime.utcnow().isoformat()
            },
            layout_config={
                "algorithm": "circular",
                "spacing": 100
            }
        )
    
    # Helper methods for building visualizations
    
    def _add_downstream_calls(self, src_func: Function, src_id: str, 
                            nodes: List[VisualizationNode], edges: List[VisualizationEdge], 
                            depth: int):
        """Add downstream function calls to visualization (from pattern 1)"""
        if depth >= self.max_depth or isinstance(src_func, ExternalModule):
            return
        
        for call in src_func.function_calls:
            if call.name == src_func.name:
                continue
            
            func = call.function_definition
            if not func:
                continue
            
            if isinstance(func, ExternalModule) and self.ignore_external_modules:
                continue
            
            # Determine function name and type
            if isinstance(func, (Class, ExternalModule)):
                func_name = func.name
                func_type = func.__class__.__name__
            elif isinstance(func, Function):
                func_name = f"{func.parent_class.name}.{func.name}" if func.is_method else func.name
                func_type = "PyFunction"
            else:
                continue
            
            func_id = f"func_{func_name}_{id(func)}"
            
            # Add node if not already visited
            if func not in self.visited:
                nodes.append(VisualizationNode(
                    id=func_id,
                    label=func_name,
                    type=func_type,
                    color=COLOR_PALETTE.get(func_type, COLOR_PALETTE["PyFunction"]),
                    size=12,
                    metadata={
                        "type": "function",
                        "file_path": getattr(call, 'filepath', 'unknown'),
                        "start_point": getattr(call, 'start_point', None),
                        "end_point": getattr(call, 'end_point', None)
                    }
                ))
                self.visited.add(func)
            
            # Add edge
            edges.append(VisualizationEdge(
                source=src_id,
                target=func_id,
                label=call.name,
                type="function_call",
                metadata={
                    "call_name": call.name,
                    "file_path": getattr(call, 'filepath', 'unknown')
                }
            ))
            
            # Recurse for further calls
            if isinstance(func, Function):
                self._add_downstream_calls(func, func_id, nodes, edges, depth + 1)
    
    def _build_blast_radius(self, symbol: Union[Function, Symbol], src_id: str,
                          nodes: List[VisualizationNode], edges: List[VisualizationEdge],
                          depth: int):
        """Build blast radius visualization (from pattern 2)"""
        if depth >= self.max_depth:
            return
        
        # Get usages of the symbol
        usages = getattr(symbol, 'usages', [])
        
        for usage in usages:
            usage_symbol = getattr(usage, 'usage_symbol', None)
            if not usage_symbol:
                continue
            
            # Determine color based on symbol type
            if self._is_http_method(usage_symbol):
                color = COLOR_PALETTE["HTTP_METHOD"]
            else:
                color = COLOR_PALETTE.get(usage_symbol.__class__.__name__, COLOR_PALETTE["PyFunction"])
            
            usage_id = f"usage_{usage_symbol.name}_{id(usage_symbol)}"
            
            # Add node if not already added
            if not any(node.id == usage_id for node in nodes):
                nodes.append(VisualizationNode(
                    id=usage_id,
                    label=usage_symbol.name,
                    type=usage_symbol.__class__.__name__,
                    color=color,
                    size=12,
                    metadata={
                        "type": "usage",
                        "is_http_method": self._is_http_method(usage_symbol)
                    }
                ))
            
            # Add edge
            edges.append(VisualizationEdge(
                source=src_id,
                target=usage_id,
                label="used_by",
                type="usage",
                metadata=self._generate_edge_meta(usage)
            ))
            
            # Recurse to process usages of this symbol
            self._build_blast_radius(usage_symbol, usage_id, nodes, edges, depth + 1)
    
    def _build_dependencies_visualization(self, symbol: Symbol, src_id: str,
                                        nodes: List[VisualizationNode], edges: List[VisualizationEdge],
                                        depth: int):
        """Build dependencies visualization (from pattern 3)"""
        if depth >= self.max_depth:
            return
        
        for dep in symbol.dependencies:
            dep_symbol = None
            
            if isinstance(dep, Symbol):
                dep_symbol = dep
            elif isinstance(dep, Import):
                dep_symbol = getattr(dep, 'resolved_symbol', None) or getattr(dep, 'imported_symbol', None)
            
            if dep_symbol:
                dep_id = f"dep_{dep_symbol.name}_{id(dep_symbol)}"
                
                # Add dependency node
                if not any(node.id == dep_id for node in nodes):
                    nodes.append(VisualizationNode(
                        id=dep_id,
                        label=dep_symbol.name,
                        type=dep_symbol.__class__.__name__,
                        color=COLOR_PALETTE.get(dep_symbol.__class__.__name__, COLOR_PALETTE["Dependency"]),
                        size=10,
                        metadata={"type": "dependency"}
                    ))
                
                # Add edge
                edges.append(VisualizationEdge(
                    source=src_id,
                    target=dep_id,
                    label="depends_on",
                    type="dependency"
                ))
                
                # Recurse if not a class (to avoid infinite loops)
                if not isinstance(dep_symbol, Class):
                    self._build_dependencies_visualization(dep_symbol, dep_id, nodes, edges, depth + 1)
    
    def _is_http_method(self, symbol) -> bool:
        """Check if a symbol represents an HTTP method handler"""
        if isinstance(symbol, PyFunction) and hasattr(symbol, 'is_method') and symbol.is_method:
            return symbol.name in HTTP_METHODS
        return False
    
    def _generate_edge_meta(self, usage) -> Dict[str, Any]:
        """Generate metadata for graph edges based on usage"""
        if hasattr(usage, 'match'):
            match = usage.match
            return {
                "name": getattr(match, 'source', ''),
                "file_path": getattr(match, 'filepath', ''),
                "start_point": getattr(match, 'start_point', None),
                "end_point": getattr(match, 'end_point', None),
                "symbol_name": match.__class__.__name__
            }
        return {}
    
    def _calculate_function_complexity(self, func: Function) -> int:
        """Calculate complexity score for a function"""
        complexity = 1  # Base complexity
        complexity += len(func.function_calls) * 0.5
        complexity += len(func.parameters) * 0.2
        if hasattr(func, 'return_statements'):
            complexity += len(func.return_statements) * 0.3
        return int(complexity)
    
    def _get_complexity_color(self, complexity: int) -> str:
        """Get color based on complexity level"""
        if complexity <= 5:
            return COLOR_PALETTE["Info"]  # Green for low complexity
        elif complexity <= 10:
            return COLOR_PALETTE["Warning"]  # Yellow for medium complexity
        else:
            return COLOR_PALETTE["Critical"]  # Red for high complexity
    
    def _calculate_average_complexity(self, codebase: Codebase) -> float:
        """Calculate average complexity across all functions"""
        functions = list(codebase.functions)
        if not functions:
            return 0.0
        
        total_complexity = sum(self._calculate_function_complexity(func) for func in functions)
        return total_complexity / len(functions)
    
    def _analyze_codebase_issues(self, codebase: Codebase) -> List[Dict[str, Any]]:
        """Analyze codebase and identify issues"""
        issues = []
        
        # Check for large functions
        for func in codebase.functions:
            complexity = self._calculate_function_complexity(func)
            if complexity > 15:
                issues.append({
                    "id": f"complexity_{id(func)}",
                    "title": f"High complexity in {func.name}",
                    "severity": "Critical",
                    "type": "complexity",
                    "affected_element": func.name,
                    "description": f"Function has complexity score of {complexity}"
                })
        
        # Check for files with many imports
        for file in codebase.files:
            if len(file.imports) > 20:
                issues.append({
                    "id": f"imports_{id(file)}",
                    "title": f"Too many imports in {file.name}",
                    "severity": "Warning",
                    "type": "imports",
                    "affected_element": file.name,
                    "description": f"File has {len(file.imports)} imports"
                })
        
        return issues

# React Component Generator
class ReactComponentGenerator:
    """
    Generates React component code for visualizations
    """
    
    @staticmethod
    def generate_visualization_component(viz_data: VisualizationData, 
                                       component_name: str = "CodebaseVisualization") -> str:
        """Generate React component code for a visualization"""
        
        component_code = f'''
import React, {{ useState, useEffect, useRef }} from 'react';
import {{ Network }} from 'vis-network/standalone/esm/vis-network';

const {component_name} = ({{ data, options = {{}} }}) => {{
  const networkRef = useRef(null);
  const [network, setNetwork] = useState(null);
  
  const defaultOptions = {{
    layout: {{
      hierarchical: {{
        enabled: {str(viz_data.layout_config.get('algorithm') == 'hierarchical').lower()},
        direction: '{viz_data.layout_config.get('direction', 'UD')}',
        spacing: {viz_data.layout_config.get('spacing', 100)}
      }}
    }},
    physics: {{
      enabled: {str(viz_data.layout_config.get('algorithm') == 'force').lower()},
      repulsion: {{
        nodeDistance: {viz_data.layout_config.get('repulsion', 200)}
      }}
    }},
    nodes: {{
      shape: 'dot',
      scaling: {{
        min: 10,
        max: 30
      }},
      font: {{
        size: 12,
        face: 'Tahoma'
      }}
    }},
    edges: {{
      width: 2,
      color: {{ inherit: 'from' }},
      smooth: {{
        type: 'continuous'
      }}
    }},
    interaction: {{
      hover: true,
      tooltipDelay: 200
    }}
  }};
  
  useEffect(() => {{
    if (networkRef.current && data) {{
      const networkData = {{
        nodes: data.nodes.map(node => ({{
          id: node.id,
          label: node.label,
          color: node.color,
          size: node.size,
          title: `Type: ${{node.type}}\\nMetadata: ${{JSON.stringify(node.metadata, null, 2)}}`
        }})),
        edges: data.edges.map(edge => ({{
          from: edge.source,
          to: edge.target,
          label: edge.label,
          title: `Type: ${{edge.type}}\\nMetadata: ${{JSON.stringify(edge.metadata, null, 2)}}`
        }}))
      }};
      
      const mergedOptions = {{ ...defaultOptions, ...options }};
      const net = new Network(networkRef.current, networkData, mergedOptions);
      setNetwork(net);
      
      // Event handlers
      net.on('click', (params) => {{
        if (params.nodes.length > 0) {{
          const nodeId = params.nodes[0];
          const node = data.nodes.find(n => n.id === nodeId);
          console.log('Node clicked:', node);
        }}
      }});
      
      return () => {{
        net.destroy();
      }};
    }}
  }}, [data, options]);
  
  return (
    <div style={{{{ width: '100%', height: '600px' }}}}>
      <div ref={{networkRef}} style={{{{ width: '100%', height: '100%' }}}} />
      <div style={{{{ marginTop: '10px', padding: '10px', backgroundColor: '#f5f5f5' }}}}>
        <h4>Visualization Metadata</h4>
        <p><strong>Type:</strong> {viz_data.metadata.get('visualization_type', 'Unknown')}</p>
        <p><strong>Generated:</strong> {viz_data.metadata.get('generated_at', 'Unknown')}</p>
        <p><strong>Nodes:</strong> {len(viz_data.nodes)}</p>
        <p><strong>Edges:</strong> {len(viz_data.edges)}</p>
      </div>
    </div>
  );
}};

export default {component_name};
'''
        return component_code
    
    @staticmethod
    def generate_dashboard_component(visualizations: Dict[str, VisualizationData]) -> str:
        """Generate a React dashboard component with multiple visualizations"""
        
        dashboard_code = '''
import React, { useState } from 'react';
import CodebaseVisualization from './CodebaseVisualization';

const CodebaseDashboard = ({ visualizationData }) => {
  const [activeTab, setActiveTab] = useState('class_method_relationships');
  
  const tabs = [
    { key: 'class_method_relationships', label: 'Class Methods' },
    { key: 'function_blast_radius', label: 'Blast Radius' },
    { key: 'symbol_dependencies', label: 'Dependencies' },
    { key: 'call_graph', label: 'Call Graph' },
    { key: 'dependency_graph', label: 'File Dependencies' },
    { key: 'complexity_heatmap', label: 'Complexity' },
    { key: 'issue_dashboard', label: 'Issues' },
    { key: 'metrics_overview', label: 'Metrics' }
  ];
  
  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <div style={{ borderBottom: '1px solid #ccc', padding: '10px' }}>
        <h2>Codebase Analysis Dashboard</h2>
        <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: '8px 16px',
                border: '1px solid #ccc',
                backgroundColor: activeTab === tab.key ? '#007bff' : '#fff',
                color: activeTab === tab.key ? '#fff' : '#000',
                cursor: 'pointer',
                borderRadius: '4px'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
      
      <div style={{ padding: '20px', height: 'calc(100vh - 120px)' }}>
        {visualizationData[activeTab] && (
          <CodebaseVisualization 
            data={visualizationData[activeTab]}
            options={{
              // Tab-specific options can be added here
            }}
          />
        )}
      </div>
    </div>
  );
};

export default CodebaseDashboard;
'''
        return dashboard_code

# Factory function for easy usage
def create_react_visualizations(codebase: Codebase, 
                               target_element: Optional[Union[Class, Function, Symbol]] = None,
                               visualization_types: List[str] = None) -> Dict[str, Any]:
    """
    Factory function to create comprehensive React visualizations.
    
    Args:
        codebase: The codebase to analyze
        target_element: Optional specific element to focus on
        visualization_types: List of visualization types to generate
        
    Returns:
        Dictionary containing visualization data and React components
    """
    generator = ReactVisualizationGenerator()
    visualizations = generator.generate_comprehensive_visualization(
        codebase, target_element, visualization_types
    )
    
    component_generator = ReactComponentGenerator()
    
    # Generate React components
    components = {}
    for viz_type, viz_data in visualizations.items():
        component_name = f"{viz_type.title().replace('_', '')}Visualization"
        components[viz_type] = {
            'data': viz_data.to_dict(),
            'component_code': component_generator.generate_visualization_component(
                viz_data, component_name
            )
        }
    
    # Generate dashboard component
    dashboard_component = component_generator.generate_dashboard_component(visualizations)
    
    return {
        'visualizations': visualizations,
        'components': components,
        'dashboard_component': dashboard_component,
        'metadata': {
            'total_visualizations': len(visualizations),
            'generated_at': datetime.utcnow().isoformat(),
            'codebase_summary': {
                'files': len(list(codebase.files)),
                'functions': len(list(codebase.functions)),
                'classes': len(list(codebase.classes))
            }
        }
    }

# Export main classes and functions
__all__ = [
    'ReactVisualizationGenerator',
    'ReactComponentGenerator', 
    'VisualizationData',
    'VisualizationNode',
    'VisualizationEdge',
    'create_react_visualizations',
    'COLOR_PALETTE'
]

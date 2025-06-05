"""
Blast Radius Analysis System

This module provides comprehensive blast radius analysis for understanding
the impact and propagation of changes, errors, or issues throughout a codebase.
"""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class

logger = logging.getLogger(__name__)


@dataclass
class BlastRadiusNode:
    """Represents a node in the blast radius analysis."""
    id: str
    name: str
    type: str  # 'function', 'class', 'module', 'file'
    file_path: str
    impact_level: int  # 0 = origin, 1 = direct impact, 2+ = indirect impact
    impact_score: float  # 0.0 - 1.0
    dependencies: List[str]
    dependents: List[str]
    metadata: Dict[str, Any]


@dataclass
class BlastRadiusResult:
    """Complete blast radius analysis result."""
    origin_id: str
    origin_type: str
    total_affected_nodes: int
    max_impact_level: int
    impact_graph: Dict[str, BlastRadiusNode]
    impact_levels: Dict[int, List[str]]
    critical_paths: List[List[str]]
    impact_summary: Dict[str, Any]
    visualization_data: Dict[str, Any]


class BlastRadiusAnalyzer:
    """
    Comprehensive blast radius analysis system.
    
    Analyzes the potential impact of changes, errors, or issues by tracing
    dependencies and relationships throughout the codebase.
    """
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.dependency_graph = nx.DiGraph()
        self.reverse_graph = nx.DiGraph()
        self._build_dependency_graphs()
    
    def _build_dependency_graphs(self):
        """Build dependency graphs for the codebase."""
        logger.info("Building dependency graphs for blast radius analysis")
        
        # Add nodes for all code elements
        self._add_function_nodes()
        self._add_class_nodes()
        self._add_module_nodes()
        
        # Add edges for dependencies
        self._add_function_dependencies()
        self._add_class_dependencies()
        self._add_module_dependencies()
        
        # Create reverse graph for impact analysis
        self.reverse_graph = self.dependency_graph.reverse()
    
    def _add_function_nodes(self):
        """Add function nodes to the dependency graph."""
        for function in self.codebase.functions:
            node_id = f"function:{function.file_path}:{function.name}"
            self.dependency_graph.add_node(node_id, {
                'type': 'function',
                'name': function.name,
                'file_path': function.file_path,
                'start_line': getattr(function, 'start_line', 0),
                'complexity': getattr(function, 'complexity', 1),
                'class_name': getattr(function, 'class_name', None)
            })
    
    def _add_class_nodes(self):
        """Add class nodes to the dependency graph."""
        for cls in self.codebase.classes:
            node_id = f"class:{cls.file_path}:{cls.name}"
            self.dependency_graph.add_node(node_id, {
                'type': 'class',
                'name': cls.name,
                'file_path': cls.file_path,
                'start_line': getattr(cls, 'start_line', 0),
                'base_classes': getattr(cls, 'base_classes', []),
                'methods': getattr(cls, 'methods', [])
            })
    
    def _add_module_nodes(self):
        """Add module nodes to the dependency graph."""
        modules = set()
        
        # Extract modules from functions and classes
        for function in self.codebase.functions:
            module_path = function.file_path
            if module_path not in modules:
                modules.add(module_path)
                node_id = f"module:{module_path}"
                self.dependency_graph.add_node(node_id, {
                    'type': 'module',
                    'name': module_path.split('/')[-1],
                    'file_path': module_path,
                    'functions': [],
                    'classes': []
                })
        
        for cls in self.codebase.classes:
            module_path = cls.file_path
            if module_path not in modules:
                modules.add(module_path)
                node_id = f"module:{module_path}"
                self.dependency_graph.add_node(node_id, {
                    'type': 'module',
                    'name': module_path.split('/')[-1],
                    'file_path': module_path,
                    'functions': [],
                    'classes': []
                })
    
    def _add_function_dependencies(self):
        """Add function dependency edges."""
        for function in self.codebase.functions:
            if not hasattr(function, 'source_code'):
                continue
                
            source = function.source_code
            function_id = f"function:{function.file_path}:{function.name}"
            
            # Find function calls in the source code
            import re
            
            # Simple pattern to find function calls
            call_patterns = [
                r'(\w+)\s*\(',  # Simple function calls
                r'self\.(\w+)\s*\(',  # Method calls
                r'(\w+)\.(\w+)\s*\(',  # Object method calls
            ]
            
            for pattern in call_patterns:
                matches = re.finditer(pattern, source)
                for match in matches:
                    called_function = match.group(1)
                    
                    # Find the actual function node
                    for target_function in self.codebase.functions:
                        if target_function.name == called_function:
                            target_id = f"function:{target_function.file_path}:{target_function.name}"
                            if target_id != function_id:  # Avoid self-loops
                                self.dependency_graph.add_edge(function_id, target_id, {
                                    'type': 'function_call',
                                    'weight': 1.0
                                })
    
    def _add_class_dependencies(self):
        """Add class dependency edges."""
        for cls in self.codebase.classes:
            class_id = f"class:{cls.file_path}:{cls.name}"
            
            # Add inheritance relationships
            if hasattr(cls, 'base_classes'):
                for base_class in cls.base_classes:
                    # Find the base class node
                    for target_class in self.codebase.classes:
                        if target_class.name == base_class:
                            target_id = f"class:{target_class.file_path}:{target_class.name}"
                            self.dependency_graph.add_edge(class_id, target_id, {
                                'type': 'inheritance',
                                'weight': 2.0  # Higher weight for inheritance
                            })
            
            # Add method dependencies
            if hasattr(cls, 'methods'):
                for method in cls.methods:
                    method_id = f"function:{cls.file_path}:{method}"
                    if self.dependency_graph.has_node(method_id):
                        self.dependency_graph.add_edge(class_id, method_id, {
                            'type': 'contains_method',
                            'weight': 1.5
                        })
    
    def _add_module_dependencies(self):
        """Add module dependency edges."""
        # Add containment relationships
        for function in self.codebase.functions:
            module_id = f"module:{function.file_path}"
            function_id = f"function:{function.file_path}:{function.name}"
            
            if self.dependency_graph.has_node(module_id):
                self.dependency_graph.add_edge(module_id, function_id, {
                    'type': 'contains_function',
                    'weight': 1.0
                })
        
        for cls in self.codebase.classes:
            module_id = f"module:{cls.file_path}"
            class_id = f"class:{cls.file_path}:{cls.name}"
            
            if self.dependency_graph.has_node(module_id):
                self.dependency_graph.add_edge(module_id, class_id, {
                    'type': 'contains_class',
                    'weight': 1.0
                })
    
    def analyze_blast_radius(self, 
                           origin_id: str, 
                           origin_type: str = 'auto',
                           max_depth: int = 5,
                           include_reverse: bool = True) -> BlastRadiusResult:
        """
        Analyze blast radius from a given origin point.
        
        Args:
            origin_id: ID of the origin element (function name, class name, etc.)
            origin_type: Type of origin ('function', 'class', 'module', 'auto')
            max_depth: Maximum depth to analyze
            include_reverse: Whether to include reverse dependencies (what depends on this)
            
        Returns:
            BlastRadiusResult with complete analysis
        """
        logger.info(f"Analyzing blast radius for {origin_id} (type: {origin_type})")
        
        # Find the actual node ID
        actual_origin_id = self._find_node_id(origin_id, origin_type)
        if not actual_origin_id:
            raise ValueError(f"Could not find node for {origin_id} of type {origin_type}")
        
        # Perform forward impact analysis (what this affects)
        forward_impact = self._analyze_forward_impact(actual_origin_id, max_depth)
        
        # Perform reverse impact analysis (what affects this)
        reverse_impact = {}
        if include_reverse:
            reverse_impact = self._analyze_reverse_impact(actual_origin_id, max_depth)
        
        # Combine results
        all_affected = {**forward_impact, **reverse_impact}
        
        # Create blast radius nodes
        impact_graph = self._create_impact_graph(actual_origin_id, all_affected)
        
        # Organize by impact levels
        impact_levels = self._organize_by_impact_levels(impact_graph)
        
        # Find critical paths
        critical_paths = self._find_critical_paths(actual_origin_id, impact_graph)
        
        # Create impact summary
        impact_summary = self._create_impact_summary(impact_graph, impact_levels)
        
        # Generate visualization data
        visualization_data = self._generate_visualization_data(impact_graph, impact_levels)
        
        return BlastRadiusResult(
            origin_id=actual_origin_id,
            origin_type=origin_type,
            total_affected_nodes=len(impact_graph),
            max_impact_level=max(impact_levels.keys()) if impact_levels else 0,
            impact_graph=impact_graph,
            impact_levels=impact_levels,
            critical_paths=critical_paths,
            impact_summary=impact_summary,
            visualization_data=visualization_data
        )
    
    def _find_node_id(self, identifier: str, node_type: str) -> Optional[str]:
        """Find the actual node ID for a given identifier."""
        if node_type == 'auto':
            # Try to find the node by searching all types
            for node_id in self.dependency_graph.nodes():
                node_data = self.dependency_graph.nodes[node_id]
                if node_data.get('name') == identifier:
                    return node_id
        else:
            # Search for specific type
            for node_id in self.dependency_graph.nodes():
                node_data = self.dependency_graph.nodes[node_id]
                if (node_data.get('type') == node_type and 
                    node_data.get('name') == identifier):
                    return node_id
        
        return None
    
    def _analyze_forward_impact(self, origin_id: str, max_depth: int) -> Dict[str, int]:
        """Analyze forward impact (what this node affects)."""
        impact = {}
        visited = set()
        queue = deque([(origin_id, 0)])
        
        while queue:
            node_id, depth = queue.popleft()
            
            if node_id in visited or depth > max_depth:
                continue
                
            visited.add(node_id)
            impact[node_id] = depth
            
            # Add successors
            for successor in self.dependency_graph.successors(node_id):
                if successor not in visited:
                    queue.append((successor, depth + 1))
        
        return impact
    
    def _analyze_reverse_impact(self, origin_id: str, max_depth: int) -> Dict[str, int]:
        """Analyze reverse impact (what affects this node)."""
        impact = {}
        visited = set()
        queue = deque([(origin_id, 0)])
        
        while queue:
            node_id, depth = queue.popleft()
            
            if node_id in visited or depth > max_depth:
                continue
                
            visited.add(node_id)
            impact[node_id] = depth
            
            # Add predecessors
            for predecessor in self.dependency_graph.predecessors(node_id):
                if predecessor not in visited:
                    queue.append((predecessor, depth + 1))
        
        return impact
    
    def _create_impact_graph(self, origin_id: str, all_affected: Dict[str, int]) -> Dict[str, BlastRadiusNode]:
        """Create impact graph with blast radius nodes."""
        impact_graph = {}
        
        for node_id, impact_level in all_affected.items():
            if not self.dependency_graph.has_node(node_id):
                continue
                
            node_data = self.dependency_graph.nodes[node_id]
            
            # Calculate impact score
            impact_score = self._calculate_impact_score(node_id, impact_level, origin_id)
            
            # Get dependencies and dependents
            dependencies = list(self.dependency_graph.successors(node_id))
            dependents = list(self.dependency_graph.predecessors(node_id))
            
            blast_node = BlastRadiusNode(
                id=node_id,
                name=node_data.get('name', 'unknown'),
                type=node_data.get('type', 'unknown'),
                file_path=node_data.get('file_path', ''),
                impact_level=impact_level,
                impact_score=impact_score,
                dependencies=dependencies,
                dependents=dependents,
                metadata=node_data
            )
            
            impact_graph[node_id] = blast_node
        
        return impact_graph
    
    def _calculate_impact_score(self, node_id: str, impact_level: int, origin_id: str) -> float:
        """Calculate impact score for a node."""
        if node_id == origin_id:
            return 1.0
        
        # Base score decreases with distance
        base_score = 1.0 / (impact_level + 1)
        
        # Adjust based on node type and properties
        node_data = self.dependency_graph.nodes[node_id]
        node_type = node_data.get('type', 'unknown')
        
        # Higher impact for critical node types
        type_multipliers = {
            'class': 1.2,
            'function': 1.0,
            'module': 1.5
        }
        
        multiplier = type_multipliers.get(node_type, 1.0)
        
        # Adjust for complexity if available
        complexity = node_data.get('complexity', 1)
        if complexity > 10:
            multiplier *= 1.1
        
        return min(base_score * multiplier, 1.0)
    
    def _organize_by_impact_levels(self, impact_graph: Dict[str, BlastRadiusNode]) -> Dict[int, List[str]]:
        """Organize nodes by impact levels."""
        impact_levels = defaultdict(list)
        
        for node_id, node in impact_graph.items():
            impact_levels[node.impact_level].append(node_id)
        
        return dict(impact_levels)
    
    def _find_critical_paths(self, origin_id: str, impact_graph: Dict[str, BlastRadiusNode]) -> List[List[str]]:
        """Find critical paths in the blast radius."""
        critical_paths = []
        
        # Find paths to high-impact nodes
        high_impact_nodes = [
            node_id for node_id, node in impact_graph.items()
            if node.impact_score > 0.7 and node_id != origin_id
        ]
        
        for target_id in high_impact_nodes:
            try:
                if nx.has_path(self.dependency_graph, origin_id, target_id):
                    path = nx.shortest_path(self.dependency_graph, origin_id, target_id)
                    critical_paths.append(path)
            except nx.NetworkXNoPath:
                continue
        
        # Sort by path length and impact
        critical_paths.sort(key=lambda path: (
            len(path),
            -impact_graph[path[-1]].impact_score if path[-1] in impact_graph else 0
        ))
        
        return critical_paths[:10]  # Return top 10 critical paths
    
    def _create_impact_summary(self, impact_graph: Dict[str, BlastRadiusNode], 
                             impact_levels: Dict[int, List[str]]) -> Dict[str, Any]:
        """Create impact summary statistics."""
        total_nodes = len(impact_graph)
        
        # Count by type
        type_counts = defaultdict(int)
        for node in impact_graph.values():
            type_counts[node.type] += 1
        
        # Count by severity
        severity_counts = {
            'high': len([n for n in impact_graph.values() if n.impact_score > 0.7]),
            'medium': len([n for n in impact_graph.values() if 0.3 < n.impact_score <= 0.7]),
            'low': len([n for n in impact_graph.values() if n.impact_score <= 0.3])
        }
        
        # Calculate average impact score
        avg_impact_score = sum(n.impact_score for n in impact_graph.values()) / total_nodes if total_nodes > 0 else 0
        
        return {
            'total_affected_nodes': total_nodes,
            'nodes_by_type': dict(type_counts),
            'nodes_by_severity': severity_counts,
            'impact_levels_count': len(impact_levels),
            'max_impact_level': max(impact_levels.keys()) if impact_levels else 0,
            'average_impact_score': avg_impact_score,
            'high_impact_percentage': (severity_counts['high'] / total_nodes * 100) if total_nodes > 0 else 0
        }
    
    def _generate_visualization_data(self, impact_graph: Dict[str, BlastRadiusNode], 
                                   impact_levels: Dict[int, List[str]]) -> Dict[str, Any]:
        """Generate data for blast radius visualization."""
        nodes = []
        edges = []
        
        # Create nodes for visualization
        for node_id, node in impact_graph.items():
            nodes.append({
                'id': node_id,
                'name': node.name,
                'type': node.type,
                'impact_level': node.impact_level,
                'impact_score': node.impact_score,
                'file_path': node.file_path,
                'size': max(10, node.impact_score * 50),  # Node size based on impact
                'color': self._get_impact_color(node.impact_score),
                'group': node.impact_level
            })
        
        # Create edges for visualization
        for node_id, node in impact_graph.items():
            for dep_id in node.dependencies:
                if dep_id in impact_graph:
                    edges.append({
                        'source': node_id,
                        'target': dep_id,
                        'type': 'dependency',
                        'weight': 1.0
                    })
        
        # Create level-based layout data
        level_layout = {}
        for level, node_ids in impact_levels.items():
            level_layout[level] = [
                {'id': node_id, 'name': impact_graph[node_id].name}
                for node_id in node_ids if node_id in impact_graph
            ]
        
        return {
            'nodes': nodes,
            'edges': edges,
            'level_layout': level_layout,
            'graph_type': 'blast_radius',
            'layout_algorithm': 'force_directed',
            'color_scheme': 'impact_based'
        }
    
    def _get_impact_color(self, impact_score: float) -> str:
        """Get color based on impact score."""
        if impact_score > 0.7:
            return '#ff4444'  # Red for high impact
        elif impact_score > 0.3:
            return '#ffaa44'  # Orange for medium impact
        else:
            return '#44aaff'  # Blue for low impact
    
    def analyze_error_blast_radius(self, error_location: Dict[str, Any]) -> BlastRadiusResult:
        """Analyze blast radius for a specific error."""
        # Determine origin based on error location
        if error_location.get('function'):
            origin_id = error_location['function']
            origin_type = 'function'
        elif error_location.get('class'):
            origin_id = error_location['class']
            origin_type = 'class'
        else:
            # Use file as origin
            origin_id = error_location.get('file', 'unknown')
            origin_type = 'module'
        
        return self.analyze_blast_radius(origin_id, origin_type)
    
    def get_impact_recommendations(self, blast_result: BlastRadiusResult) -> List[str]:
        """Get recommendations based on blast radius analysis."""
        recommendations = []
        
        total_affected = blast_result.total_affected_nodes
        high_impact_count = blast_result.impact_summary['nodes_by_severity']['high']
        
        if total_affected > 50:
            recommendations.append("High blast radius detected - consider isolating this component")
        
        if high_impact_count > 10:
            recommendations.append("Many high-impact dependencies - review architecture for tight coupling")
        
        if blast_result.max_impact_level > 4:
            recommendations.append("Deep dependency chain detected - consider reducing coupling depth")
        
        # Critical path recommendations
        if len(blast_result.critical_paths) > 5:
            recommendations.append("Multiple critical paths found - implement circuit breakers or fallbacks")
        
        # Type-specific recommendations
        type_counts = blast_result.impact_summary['nodes_by_type']
        if type_counts.get('class', 0) > type_counts.get('function', 0):
            recommendations.append("Class-heavy impact - consider using composition over inheritance")
        
        return recommendations


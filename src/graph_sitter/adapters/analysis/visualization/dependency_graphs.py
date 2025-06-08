#!/usr/bin/env python3
"""
🕸️ DEPENDENCY GRAPHS MODULE 🕸️

Advanced dependency graph generation and visualization for codebase analysis.
Provides interactive network visualizations of code dependencies and relationships.

Features:
- DependencyGraphGenerator: Core graph generation engine
- Interactive D3.js network visualizations
- Call graph analysis and visualization
- Import dependency mapping
- Circular dependency detection
- Module relationship analysis
"""

import logging
import json
import networkx as nx
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from pathlib import Path
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class GraphNode:
    """Represents a node in the dependency graph."""
    id: str
    name: str
    type: str  # module, function, class, file
    size: int = 1  # For visualization sizing
    group: str = ""  # For grouping/coloring
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphEdge:
    """Represents an edge in the dependency graph."""
    source: str
    target: str
    type: str  # import, call, inheritance, etc.
    weight: float = 1.0  # Strength of relationship
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GraphConfig:
    """Configuration for graph generation and visualization."""
    layout: str = "force"  # force, hierarchical, circular
    show_labels: bool = True
    show_weights: bool = False
    color_by_group: bool = True
    interactive: bool = True
    width: int = 800
    height: int = 600
    node_size_range: Tuple[int, int] = (5, 50)
    edge_width_range: Tuple[int, int] = (1, 10)

class DependencyGraphGenerator:
    """
    Core engine for generating dependency graphs from codebase analysis.
    """
    
    def __init__(self, config: Optional[GraphConfig] = None):
        """Initialize the dependency graph generator."""
        self.config = config or GraphConfig()
        self.graph = nx.DiGraph()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.circular_dependencies: List[List[str]] = []
    
    def add_node(self, node: GraphNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        self.graph.add_node(node.id, **node.__dict__)
    
    def add_edge(self, edge: GraphEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
        self.graph.add_edge(edge.source, edge.target, **edge.__dict__)
    
    def add_import_dependency(self, importer: str, imported: str, import_type: str = "import") -> None:
        """Add an import dependency between modules."""
        # Create nodes if they don't exist
        if importer not in self.nodes:
            self.add_node(GraphNode(
                id=importer,
                name=Path(importer).stem,
                type="module",
                group="module"
            ))
        
        if imported not in self.nodes:
            self.add_node(GraphNode(
                id=imported,
                name=Path(imported).stem,
                type="module",
                group="module"
            ))
        
        # Add edge
        self.add_edge(GraphEdge(
            source=importer,
            target=imported,
            type=import_type,
            metadata={"import_type": import_type}
        ))
    
    def add_function_call(self, caller: str, callee: str, call_count: int = 1) -> None:
        """Add a function call relationship."""
        # Create nodes if they don't exist
        if caller not in self.nodes:
            self.add_node(GraphNode(
                id=caller,
                name=caller.split('.')[-1],
                type="function",
                group="function"
            ))
        
        if callee not in self.nodes:
            self.add_node(GraphNode(
                id=callee,
                name=callee.split('.')[-1],
                type="function",
                group="function"
            ))
        
        # Add edge with call count as weight
        self.add_edge(GraphEdge(
            source=caller,
            target=callee,
            type="call",
            weight=call_count,
            metadata={"call_count": call_count}
        ))
    
    def add_class_inheritance(self, child: str, parent: str) -> None:
        """Add a class inheritance relationship."""
        # Create nodes if they don't exist
        if child not in self.nodes:
            self.add_node(GraphNode(
                id=child,
                name=child.split('.')[-1],
                type="class",
                group="class"
            ))
        
        if parent not in self.nodes:
            self.add_node(GraphNode(
                id=parent,
                name=parent.split('.')[-1],
                type="class",
                group="class"
            ))
        
        # Add edge
        self.add_edge(GraphEdge(
            source=child,
            target=parent,
            type="inheritance",
            metadata={"relationship": "inherits_from"}
        ))
    
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies in the graph."""
        try:
            # Find all strongly connected components with more than one node
            cycles = [cycle for cycle in nx.strongly_connected_components(self.graph) if len(cycle) > 1]
            
            # Convert to list of lists for easier handling
            self.circular_dependencies = [list(cycle) for cycle in cycles]
            
            return self.circular_dependencies
        except Exception as e:
            logger.error(f"Error detecting circular dependencies: {e}")
            return []
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate graph metrics and statistics."""
        metrics = {
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "density": nx.density(self.graph),
            "circular_dependencies": len(self.circular_dependencies),
            "strongly_connected_components": nx.number_strongly_connected_components(self.graph),
            "weakly_connected_components": nx.number_weakly_connected_components(self.graph)
        }
        
        # Calculate centrality measures
        try:
            metrics["in_degree_centrality"] = nx.in_degree_centrality(self.graph)
            metrics["out_degree_centrality"] = nx.out_degree_centrality(self.graph)
            metrics["betweenness_centrality"] = nx.betweenness_centrality(self.graph)
            metrics["pagerank"] = nx.pagerank(self.graph)
        except Exception as e:
            logger.warning(f"Could not calculate centrality measures: {e}")
        
        return metrics
    
    def get_most_connected_nodes(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """Get the most connected nodes in the graph."""
        degree_dict = dict(self.graph.degree())
        return sorted(degree_dict.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def get_critical_paths(self) -> List[List[str]]:
        """Identify critical paths in the dependency graph."""
        critical_paths = []
        
        try:
            # Find longest paths between nodes
            for source in self.graph.nodes():
                for target in self.graph.nodes():
                    if source != target and nx.has_path(self.graph, source, target):
                        try:
                            path = nx.shortest_path(self.graph, source, target)
                            if len(path) > 3:  # Only consider paths longer than 3 nodes
                                critical_paths.append(path)
                        except nx.NetworkXNoPath:
                            continue
        except Exception as e:
            logger.warning(f"Error finding critical paths: {e}")
        
        return critical_paths
    
    def export_to_json(self) -> Dict[str, Any]:
        """Export graph data to JSON format for visualization."""
        nodes_data = []
        for node_id, node in self.nodes.items():
            node_data = {
                "id": node.id,
                "name": node.name,
                "type": node.type,
                "size": node.size,
                "group": node.group,
                "metadata": node.metadata
            }
            nodes_data.append(node_data)
        
        edges_data = []
        for edge in self.edges:
            edge_data = {
                "source": edge.source,
                "target": edge.target,
                "type": edge.type,
                "weight": edge.weight,
                "metadata": edge.metadata
            }
            edges_data.append(edge_data)
        
        return {
            "nodes": nodes_data,
            "edges": edges_data,
            "metrics": self.calculate_metrics(),
            "circular_dependencies": self.circular_dependencies,
            "config": self.config.__dict__
        }

def create_dependency_graph(
    dependencies: Dict[str, List[str]],
    config: Optional[GraphConfig] = None
) -> DependencyGraphGenerator:
    """
    Create a dependency graph from a dictionary of dependencies.
    
    Args:
        dependencies: Dict mapping source to list of targets
        config: Graph configuration
    
    Returns:
        Configured DependencyGraphGenerator
    """
    generator = DependencyGraphGenerator(config)
    
    for source, targets in dependencies.items():
        for target in targets:
            generator.add_import_dependency(source, target)
    
    # Detect circular dependencies
    generator.detect_circular_dependencies()
    
    return generator

def visualize_call_graph(
    call_data: Dict[str, Dict[str, int]],
    config: Optional[GraphConfig] = None
) -> str:
    """
    Create an interactive visualization of function call relationships.
    
    Args:
        call_data: Dict mapping caller to dict of callee->call_count
        config: Graph configuration
    
    Returns:
        HTML string with interactive visualization
    """
    config = config or GraphConfig()
    generator = DependencyGraphGenerator(config)
    
    # Add function calls to graph
    for caller, callees in call_data.items():
        for callee, count in callees.items():
            generator.add_function_call(caller, callee, count)
    
    # Generate visualization
    graph_data = generator.export_to_json()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Function Call Graph</title>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            .graph-container {{
                width: 100%;
                height: {config.height}px;
                border: 1px solid #ccc;
                position: relative;
            }}
            .node {{
                stroke: #fff;
                stroke-width: 2px;
                cursor: pointer;
            }}
            .link {{
                stroke: #999;
                stroke-opacity: 0.6;
            }}
            .node-label {{
                font-family: Arial, sans-serif;
                font-size: 12px;
                pointer-events: none;
            }}
            .tooltip {{
                position: absolute;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s;
            }}
        </style>
    </head>
    <body>
        <div class="graph-container">
            <svg id="call-graph" width="{config.width}" height="{config.height}"></svg>
            <div class="tooltip" id="tooltip"></div>
        </div>
        
        <script>
            const graphData = {json.dumps(graph_data)};
            
            const svg = d3.select("#call-graph");
            const width = {config.width};
            const height = {config.height};
            
            const simulation = d3.forceSimulation(graphData.nodes)
                .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(100))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2));
            
            const link = svg.append("g")
                .selectAll("line")
                .data(graphData.edges)
                .enter().append("line")
                .attr("class", "link")
                .attr("stroke-width", d => Math.sqrt(d.weight) * 2);
            
            const node = svg.append("g")
                .selectAll("circle")
                .data(graphData.nodes)
                .enter().append("circle")
                .attr("class", "node")
                .attr("r", d => Math.max(5, Math.min(20, d.size * 3)))
                .attr("fill", d => d3.schemeCategory10[d.group.charCodeAt(0) % 10])
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            const label = svg.append("g")
                .selectAll("text")
                .data(graphData.nodes)
                .enter().append("text")
                .attr("class", "node-label")
                .text(d => d.name)
                .attr("dx", 15)
                .attr("dy", 4);
            
            const tooltip = d3.select("#tooltip");
            
            node.on("mouseover", function(event, d) {{
                tooltip.style("opacity", 1)
                    .html(`<strong>${{d.name}}</strong><br/>Type: ${{d.type}}<br/>Connections: ${{d.size}}`)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", function() {{
                tooltip.style("opacity", 0);
            }});
            
            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
                
                label
                    .attr("x", d => d.x)
                    .attr("y", d => d.y);
            }});
            
            function dragstarted(event, d) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }}
            
            function dragged(event, d) {{
                d.fx = event.x;
                d.fy = event.y;
            }}
            
            function dragended(event, d) {{
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }}
        </script>
    </body>
    </html>
    """
    
    return html

def visualize_import_graph(
    import_data: Dict[str, List[str]],
    config: Optional[GraphConfig] = None
) -> str:
    """
    Create an interactive visualization of module import relationships.
    
    Args:
        import_data: Dict mapping module to list of imported modules
        config: Graph configuration
    
    Returns:
        HTML string with interactive visualization
    """
    config = config or GraphConfig()
    generator = create_dependency_graph(import_data, config)
    
    # Detect circular dependencies
    circular_deps = generator.detect_circular_dependencies()
    
    graph_data = generator.export_to_json()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Import Dependency Graph</title>
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <style>
            .graph-container {{
                width: 100%;
                height: {config.height}px;
                border: 1px solid #ccc;
                position: relative;
            }}
            .node {{
                stroke: #fff;
                stroke-width: 2px;
                cursor: pointer;
            }}
            .node.circular {{
                stroke: #ff0000;
                stroke-width: 3px;
            }}
            .link {{
                stroke: #999;
                stroke-opacity: 0.6;
                marker-end: url(#arrowhead);
            }}
            .link.circular {{
                stroke: #ff0000;
                stroke-width: 2px;
            }}
            .node-label {{
                font-family: Arial, sans-serif;
                font-size: 10px;
                pointer-events: none;
            }}
            .tooltip {{
                position: absolute;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-size: 12px;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s;
            }}
            .circular-deps {{
                position: absolute;
                top: 10px;
                right: 10px;
                background: rgba(255, 0, 0, 0.1);
                padding: 10px;
                border-radius: 4px;
                max-width: 200px;
            }}
        </style>
    </head>
    <body>
        <div class="graph-container">
            <svg id="import-graph" width="{config.width}" height="{config.height}">
                <defs>
                    <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                            refX="9" refY="3.5" orient="auto">
                        <polygon points="0 0, 10 3.5, 0 7" fill="#999" />
                    </marker>
                </defs>
            </svg>
            <div class="tooltip" id="tooltip"></div>
            {f'<div class="circular-deps"><strong>Circular Dependencies:</strong><br/>{"<br/>".join([" → ".join(cycle) for cycle in circular_deps])}</div>' if circular_deps else ''}
        </div>
        
        <script>
            const graphData = {json.dumps(graph_data)};
            const circularDeps = {json.dumps(circular_deps)};
            
            // Mark nodes and edges involved in circular dependencies
            const circularNodes = new Set();
            circularDeps.forEach(cycle => {{
                cycle.forEach(node => circularNodes.add(node));
            }});
            
            const svg = d3.select("#import-graph");
            const width = {config.width};
            const height = {config.height};
            
            const simulation = d3.forceSimulation(graphData.nodes)
                .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(150))
                .force("charge", d3.forceManyBody().strength(-400))
                .force("center", d3.forceCenter(width / 2, height / 2));
            
            const link = svg.append("g")
                .selectAll("line")
                .data(graphData.edges)
                .enter().append("line")
                .attr("class", d => circularNodes.has(d.source.id) && circularNodes.has(d.target.id) ? "link circular" : "link");
            
            const node = svg.append("g")
                .selectAll("circle")
                .data(graphData.nodes)
                .enter().append("circle")
                .attr("class", d => circularNodes.has(d.id) ? "node circular" : "node")
                .attr("r", 8)
                .attr("fill", d => circularNodes.has(d.id) ? "#ff6b6b" : d3.schemeCategory10[d.group.charCodeAt(0) % 10])
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            const label = svg.append("g")
                .selectAll("text")
                .data(graphData.nodes)
                .enter().append("text")
                .attr("class", "node-label")
                .text(d => d.name)
                .attr("dx", 12)
                .attr("dy", 4);
            
            const tooltip = d3.select("#tooltip");
            
            node.on("mouseover", function(event, d) {{
                const isCircular = circularNodes.has(d.id);
                tooltip.style("opacity", 1)
                    .html(`<strong>${{d.name}}</strong><br/>Type: ${{d.type}}<br/>${{isCircular ? '<span style="color: #ff6b6b;">⚠️ Circular Dependency</span>' : 'No circular dependencies'}}`)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 10) + "px");
            }})
            .on("mouseout", function() {{
                tooltip.style("opacity", 0);
            }});
            
            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
                
                label
                    .attr("x", d => d.x)
                    .attr("y", d => d.y);
            }});
            
            function dragstarted(event, d) {{
                if (!event.active) simulation.alphaTarget(0.3).restart();
                d.fx = d.x;
                d.fy = d.y;
            }}
            
            function dragged(event, d) {{
                d.fx = event.x;
                d.fy = event.y;
            }}
            
            function dragended(event, d) {{
                if (!event.active) simulation.alphaTarget(0);
                d.fx = null;
                d.fy = null;
            }}
        </script>
    </body>
    </html>
    """
    
    return html


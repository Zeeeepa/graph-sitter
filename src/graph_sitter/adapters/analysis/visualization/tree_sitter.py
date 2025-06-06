"""
Tree-sitter Visualization Module

Creates interactive visualizations of syntax trees and code structure
using tree-sitter parsing and D3.js exports.
"""

import json
import html
import tempfile
import webbrowser
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TreeSitterVisualizer:
    """Creates visualizations of tree-sitter syntax trees and code structure."""
    
    def __init__(self):
        self.d3_template = self._get_d3_template()
        self.node_colors = {
            'function': '#4CAF50',
            'class': '#2196F3', 
            'import': '#FF9800',
            'variable': '#9C27B0',
            'statement': '#607D8B',
            'expression': '#795548',
            'literal': '#E91E63',
            'identifier': '#009688',
            'keyword': '#F44336',
            'operator': '#3F51B5',
            'comment': '#9E9E9E',
            'string': '#8BC34A',
            'number': '#FF5722'
        }
    
    def generate_data(self, codebase) -> Dict[str, Any]:
        """Generate visualization data for the codebase."""
        try:
            if hasattr(codebase, 'files'):
                return self._generate_data_graph_sitter(codebase)
            else:
                return self._generate_data_ast(codebase)
        except Exception as e:
            logger.error(f"Visualization data generation failed: {e}")
            return {}
    
    def _generate_data_graph_sitter(self, codebase) -> Dict[str, Any]:
        """Generate visualization data using graph-sitter."""
        visualization_data = {
            'codebase_overview': self._create_codebase_overview(codebase),
            'dependency_graph': self._create_dependency_graph(codebase),
            'syntax_trees': self._create_syntax_trees(codebase),
            'call_graph': self._create_call_graph(codebase),
            'class_hierarchy': self._create_class_hierarchy(codebase),
            'file_structure': self._create_file_structure(codebase)
        }
        
        return visualization_data
    
    def _generate_data_ast(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate visualization data using AST data."""
        visualization_data = {
            'codebase_overview': self._create_overview_from_ast(file_analyses),
            'file_structure': self._create_file_structure_from_ast(file_analyses),
            'function_distribution': self._create_function_distribution(file_analyses),
            'complexity_heatmap': self._create_complexity_heatmap(file_analyses)
        }
        
        return visualization_data
    
    def _create_codebase_overview(self, codebase) -> Dict[str, Any]:
        """Create high-level codebase overview visualization data."""
        return {
            'type': 'overview',
            'stats': {
                'total_files': len(codebase.files),
                'total_functions': len(codebase.functions),
                'total_classes': len(codebase.classes),
                'total_imports': sum(len(f.imports) for f in codebase.files)
            },
            'file_types': self._analyze_file_types(codebase),
            'size_distribution': self._analyze_size_distribution(codebase)
        }
    
    def _create_dependency_graph(self, codebase) -> Dict[str, Any]:
        """Create dependency graph visualization data."""
        nodes = []
        links = []
        
        # Create nodes for each file
        for file in codebase.files:
            nodes.append({
                'id': file.filepath,
                'name': Path(file.filepath).name,
                'type': 'file',
                'size': len(file.functions) + len(file.classes),
                'color': self._get_file_color(file)
            })
        
        # Create links for imports
        for file in codebase.files:
            for import_stmt in file.imports:
                if hasattr(import_stmt, 'resolved_symbol') and import_stmt.resolved_symbol:
                    target_file = import_stmt.resolved_symbol.file
                    if target_file:
                        links.append({
                            'source': file.filepath,
                            'target': target_file.filepath,
                            'type': 'import',
                            'strength': 1
                        })
        
        return {
            'type': 'dependency_graph',
            'nodes': nodes,
            'links': links
        }
    
    def _create_syntax_trees(self, codebase) -> Dict[str, Any]:
        """Create syntax tree visualization data for selected files."""
        syntax_trees = {}
        
        # Select a few representative files
        sample_files = list(codebase.files)[:5]  # Limit to first 5 files
        
        for file in sample_files:
            if hasattr(file, 'source') and len(file.source) < 10000:  # Skip very large files
                tree_data = self._create_file_syntax_tree(file)
                if tree_data:
                    syntax_trees[file.filepath] = tree_data
        
        return {
            'type': 'syntax_trees',
            'trees': syntax_trees
        }
    
    def _create_call_graph(self, codebase) -> Dict[str, Any]:
        """Create call graph visualization data."""
        nodes = []
        links = []
        
        # Create nodes for functions
        for function in codebase.functions:
            nodes.append({
                'id': f"{function.filepath}::{function.name}",
                'name': function.name,
                'file': function.filepath,
                'type': 'function',
                'complexity': getattr(function, 'complexity', 1),
                'color': self._get_complexity_color(getattr(function, 'complexity', 1))
            })
        
        # Create links for function calls
        for function in codebase.functions:
            if hasattr(function, 'function_calls'):
                for call in function.function_calls:
                    if hasattr(call, 'function_definition'):
                        target_func = call.function_definition
                        links.append({
                            'source': f"{function.filepath}::{function.name}",
                            'target': f"{target_func.filepath}::{target_func.name}",
                            'type': 'call',
                            'strength': 1
                        })
        
        return {
            'type': 'call_graph',
            'nodes': nodes,
            'links': links
        }
    
    def _create_class_hierarchy(self, codebase) -> Dict[str, Any]:
        """Create class hierarchy visualization data."""
        nodes = []
        links = []
        
        # Create nodes for classes
        for cls in codebase.classes:
            nodes.append({
                'id': f"{cls.filepath}::{cls.name}",
                'name': cls.name,
                'file': cls.filepath,
                'type': 'class',
                'methods': len(getattr(cls, 'methods', [])),
                'color': self._get_class_color(cls)
            })
        
        # Create links for inheritance
        for cls in codebase.classes:
            if hasattr(cls, 'superclasses'):
                for parent in cls.superclasses:
                    links.append({
                        'source': f"{parent.filepath}::{parent.name}",
                        'target': f"{cls.filepath}::{cls.name}",
                        'type': 'inheritance',
                        'strength': 2
                    })
        
        return {
            'type': 'class_hierarchy',
            'nodes': nodes,
            'links': links
        }
    
    def _create_file_structure(self, codebase) -> Dict[str, Any]:
        """Create file structure tree visualization data."""
        root = {'name': 'root', 'children': []}
        
        for file in codebase.files:
            path_parts = Path(file.filepath).parts
            current = root
            
            for part in path_parts[:-1]:  # Directories
                # Find or create directory node
                dir_node = None
                for child in current['children']:
                    if child['name'] == part and child['type'] == 'directory':
                        dir_node = child
                        break
                
                if not dir_node:
                    dir_node = {
                        'name': part,
                        'type': 'directory',
                        'children': []
                    }
                    current['children'].append(dir_node)
                
                current = dir_node
            
            # Add file node
            file_node = {
                'name': path_parts[-1],
                'type': 'file',
                'path': file.filepath,
                'size': len(file.functions) + len(file.classes),
                'functions': len(file.functions),
                'classes': len(file.classes)
            }
            current['children'].append(file_node)
        
        return {
            'type': 'file_structure',
            'tree': root
        }
    
    def _create_file_syntax_tree(self, file) -> Optional[Dict[str, Any]]:
        """Create syntax tree data for a single file."""
        try:
            # This is a simplified representation
            # In a full implementation, we'd parse the actual tree-sitter AST
            
            tree_data = {
                'name': Path(file.filepath).name,
                'type': 'file',
                'children': []
            }
            
            # Add imports
            if hasattr(file, 'imports') and file.imports:
                imports_node = {
                    'name': 'imports',
                    'type': 'imports',
                    'children': []
                }
                
                for import_stmt in file.imports:
                    import_node = {
                        'name': getattr(import_stmt, 'module_name', 'unknown'),
                        'type': 'import',
                        'line': getattr(import_stmt, 'line_number', 0)
                    }
                    imports_node['children'].append(import_node)
                
                tree_data['children'].append(imports_node)
            
            # Add classes
            for cls in file.classes:
                class_node = {
                    'name': cls.name,
                    'type': 'class',
                    'line': getattr(cls, 'start_line', 0),
                    'children': []
                }
                
                # Add methods
                for method in getattr(cls, 'methods', []):
                    method_node = {
                        'name': method.name,
                        'type': 'method',
                        'line': getattr(method, 'start_line', 0)
                    }
                    class_node['children'].append(method_node)
                
                tree_data['children'].append(class_node)
            
            # Add standalone functions
            for function in file.functions:
                # Skip methods (already added under classes)
                if not any(function in getattr(cls, 'methods', []) for cls in file.classes):
                    function_node = {
                        'name': function.name,
                        'type': 'function',
                        'line': getattr(function, 'start_line', 0)
                    }
                    tree_data['children'].append(function_node)
            
            return tree_data
        
        except Exception as e:
            logger.warning(f"Failed to create syntax tree for {file.filepath}: {e}")
            return None
    
    def _create_overview_from_ast(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Create overview from AST data."""
        total_functions = sum(len(analysis.get('functions', [])) for analysis in file_analyses.values())
        total_classes = sum(len(analysis.get('classes', [])) for analysis in file_analyses.values())
        total_imports = sum(len(analysis.get('imports', [])) for analysis in file_analyses.values())
        
        return {
            'type': 'overview',
            'stats': {
                'total_files': len(file_analyses),
                'total_functions': total_functions,
                'total_classes': total_classes,
                'total_imports': total_imports
            }
        }
    
    def _create_file_structure_from_ast(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Create file structure from AST data."""
        files_data = []
        
        for filepath, analysis in file_analyses.items():
            files_data.append({
                'name': Path(filepath).name,
                'path': filepath,
                'functions': len(analysis.get('functions', [])),
                'classes': len(analysis.get('classes', [])),
                'imports': len(analysis.get('imports', []))
            })
        
        return {
            'type': 'file_list',
            'files': files_data
        }
    
    def _create_function_distribution(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Create function distribution visualization."""
        distribution = {}
        
        for filepath, analysis in file_analyses.items():
            func_count = len(analysis.get('functions', []))
            distribution[filepath] = func_count
        
        return {
            'type': 'function_distribution',
            'data': distribution
        }
    
    def _create_complexity_heatmap(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Create complexity heatmap data."""
        heatmap_data = []
        
        for filepath, analysis in file_analyses.items():
            for func in analysis.get('functions', []):
                complexity = func.get('complexity', 1)
                heatmap_data.append({
                    'file': filepath,
                    'function': func.get('name', 'unknown'),
                    'complexity': complexity,
                    'line': func.get('line_start', 0)
                })
        
        return {
            'type': 'complexity_heatmap',
            'data': heatmap_data
        }
    
    def _analyze_file_types(self, codebase) -> Dict[str, int]:
        """Analyze distribution of file types."""
        file_types = {}
        
        for file in codebase.files:
            ext = Path(file.filepath).suffix
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return file_types
    
    def _analyze_size_distribution(self, codebase) -> List[Dict[str, Any]]:
        """Analyze size distribution of files."""
        sizes = []
        
        for file in codebase.files:
            size = len(file.functions) + len(file.classes)
            sizes.append({
                'file': file.filepath,
                'size': size,
                'functions': len(file.functions),
                'classes': len(file.classes)
            })
        
        return sorted(sizes, key=lambda x: x['size'], reverse=True)
    
    def _get_file_color(self, file) -> str:
        """Get color for file based on its characteristics."""
        func_count = len(file.functions)
        class_count = len(file.classes)
        
        if class_count > func_count:
            return self.node_colors['class']
        elif func_count > 0:
            return self.node_colors['function']
        else:
            return self.node_colors['import']
    
    def _get_complexity_color(self, complexity: int) -> str:
        """Get color based on complexity level."""
        if complexity <= 5:
            return '#4CAF50'  # Green - low complexity
        elif complexity <= 10:
            return '#FF9800'  # Orange - moderate complexity
        else:
            return '#F44336'  # Red - high complexity
    
    def _get_class_color(self, cls) -> str:
        """Get color for class based on its characteristics."""
        method_count = len(getattr(cls, 'methods', []))
        
        if method_count > 10:
            return '#F44336'  # Red - large class
        elif method_count > 5:
            return '#FF9800'  # Orange - medium class
        else:
            return '#4CAF50'  # Green - small class
    
    def export_html(self, visualization_data: Dict[str, Any], output_path: str):
        """Export visualization as interactive HTML."""
        try:
            html_content = self._generate_html(visualization_data)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Visualization exported to {output_path}")
        
        except Exception as e:
            logger.error(f"Failed to export HTML visualization: {e}")
    
    def _generate_html(self, visualization_data: Dict[str, Any]) -> str:
        """Generate HTML content for visualization."""
        data_json = json.dumps(visualization_data, indent=2)
        
        return self.d3_template.format(
            title="Codebase Analysis Visualization",
            data=data_json
        )
    
    def _get_d3_template(self) -> str:
        """Get D3.js HTML template for visualizations."""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .visualization {{
            margin: 20px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
        }}
        
        .node {{
            cursor: pointer;
        }}
        
        .link {{
            stroke: #999;
            stroke-opacity: 0.6;
        }}
        
        .tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 4px;
            pointer-events: none;
            font-size: 12px;
        }}
        
        h1, h2 {{
            color: #333;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }}
        
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        
        <div id="overview" class="visualization">
            <h2>Codebase Overview</h2>
            <div id="stats" class="stats"></div>
        </div>
        
        <div id="dependency-graph" class="visualization">
            <h2>Dependency Graph</h2>
            <svg width="800" height="600"></svg>
        </div>
        
        <div id="call-graph" class="visualization">
            <h2>Call Graph</h2>
            <svg width="800" height="600"></svg>
        </div>
        
        <div id="file-structure" class="visualization">
            <h2>File Structure</h2>
            <div id="file-tree"></div>
        </div>
    </div>
    
    <script>
        const data = {data};
        
        // Create overview stats
        if (data.codebase_overview) {{
            const stats = data.codebase_overview.stats;
            const statsContainer = d3.select("#stats");
            
            Object.entries(stats).forEach(([key, value]) => {{
                const card = statsContainer.append("div").attr("class", "stat-card");
                card.append("div").attr("class", "stat-number").text(value);
                card.append("div").attr("class", "stat-label").text(key.replace(/_/g, " ").toUpperCase());
            }});
        }}
        
        // Create dependency graph
        if (data.dependency_graph) {{
            createForceGraph("#dependency-graph svg", data.dependency_graph);
        }}
        
        // Create call graph
        if (data.call_graph) {{
            createForceGraph("#call-graph svg", data.call_graph);
        }}
        
        function createForceGraph(selector, graphData) {{
            const svg = d3.select(selector);
            const width = +svg.attr("width");
            const height = +svg.attr("height");
            
            svg.selectAll("*").remove();
            
            const simulation = d3.forceSimulation(graphData.nodes)
                .force("link", d3.forceLink(graphData.links).id(d => d.id))
                .force("charge", d3.forceManyBody().strength(-300))
                .force("center", d3.forceCenter(width / 2, height / 2));
            
            const link = svg.append("g")
                .selectAll("line")
                .data(graphData.links)
                .enter().append("line")
                .attr("class", "link")
                .attr("stroke-width", d => Math.sqrt(d.strength || 1));
            
            const node = svg.append("g")
                .selectAll("circle")
                .data(graphData.nodes)
                .enter().append("circle")
                .attr("class", "node")
                .attr("r", d => Math.sqrt((d.size || 1) * 10))
                .attr("fill", d => d.color || "#69b3a2")
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));
            
            node.append("title")
                .text(d => d.name);
            
            simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);
                
                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
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
        }}
        
        // Create file structure tree
        if (data.file_structure) {{
            createFileTree("#file-tree", data.file_structure.tree);
        }}
        
        function createFileTree(selector, treeData) {{
            const container = d3.select(selector);
            container.selectAll("*").remove();
            
            function createTreeNode(node, depth = 0) {{
                const nodeDiv = container.append("div")
                    .style("margin-left", (depth * 20) + "px")
                    .style("padding", "2px 0");
                
                if (node.type === "directory") {{
                    nodeDiv.append("span")
                        .style("font-weight", "bold")
                        .style("color", "#666")
                        .text("📁 " + node.name);
                    
                    if (node.children) {{
                        node.children.forEach(child => createTreeNode(child, depth + 1));
                    }}
                }} else {{
                    nodeDiv.append("span")
                        .style("color", "#333")
                        .text("📄 " + node.name + 
                              (node.functions ? ` (${node.functions} functions, ${node.classes} classes)` : ""));
                }}
            }}
            
            createTreeNode(treeData);
        }}
    </script>
</body>
</html>'''
    
    def open_in_browser(self, output_path: str):
        """Open the generated HTML file in the default browser."""
        try:
            webbrowser.open(f"file://{Path(output_path).absolute()}")
        except Exception as e:
            logger.warning(f"Failed to open browser: {e}")
    
    def create_temporary_visualization(self, visualization_data: Dict[str, Any]) -> str:
        """Create a temporary HTML file and return its path."""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
                html_content = self._generate_html(visualization_data)
                f.write(html_content)
                return f.name
        except Exception as e:
            logger.error(f"Failed to create temporary visualization: {e}")
            return ""


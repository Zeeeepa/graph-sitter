"""
Visualize class for graph-sitter code visualization

This module provides visualization capabilities for code relationships,
dependency graphs, and other codebase insights using the actual graph-sitter API.
"""

from graph_sitter import Codebase
import json
from typing import Dict, List, Any, Optional, Set
import matplotlib.pyplot as plt
import networkx as nx
from graph_sitter.configs.models.codebase import CodebaseConfig


class Visualize:
    """
    Visualize class providing code visualization and graph representation.
    
    Usage example:
    
    from graph_sitter import Codebase
    from contexten.extensions.graph_sitter.visualize import Visualize
    
    codebase = Codebase("path/to/repo")
    visualizer = Visualize(codebase)
    
    # Generate dependency graph
    dep_graph = visualizer.dependency_graph()
    
    # Generate call graph
    call_graph = visualizer.call_graph()
    
    # Generate class hierarchy
    class_hierarchy = visualizer.class_hierarchy()
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize Visualize with a Codebase instance."""
        self.codebase = codebase
    
    def dependency_graph(self, output_path: str = "dependency_graph.png"):
        """Generate a dependency graph visualization."""
        G = nx.DiGraph()
        
        # Add nodes for each file
        files_attr = getattr(self.codebase, 'files', [])
        files = list(files_attr) if hasattr(files_attr, '__iter__') else []
        
        for file in files:
            if hasattr(file, 'path') and file.path:
                G.add_node(file.path, type='file')
    
        # Add edges for dependencies
        for file in files:
            if not (hasattr(file, 'path') and file.path):
                continue
            imports = getattr(file, 'imports', [])
            if hasattr(imports, '__iter__'):
                imports_list = list(imports)
                for imp in imports_list:
                    if hasattr(imp, 'target_file') and imp.target_file:
                        G.add_edge(file.path, imp.target_file)
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='lightblue', 
                node_size=500, font_size=8, arrows=True)
        plt.title("Codebase Dependency Graph")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {
            'graph_file': output_path,
            'total_files': len(files),
            'total_dependencies': G.number_of_edges(),
            'circular_dependencies': len(list(nx.simple_cycles(G)))
        }
    
    def call_graph(self, function_name: Optional[str] = None, output_path: str = "call_graph.png"):
        """Generate a function call graph visualization."""
        G = nx.DiGraph()
        
        # Add function nodes
        functions_attr = getattr(self.codebase, 'functions', [])
        functions = list(functions_attr) if hasattr(functions_attr, '__iter__') else []
        
        for func in functions:
            G.add_node(func.name, 
                      type='function',
                      is_async=func.is_async,
                      is_generator=getattr(func, 'is_generator', False),
                      complexity=getattr(func, 'complexity', 0))
        
        # Add call edges
        for func in functions:
            calls = getattr(func, 'function_calls', [])
            if hasattr(calls, '__iter__'):
                calls_list = list(calls)
                for call in calls_list:
                    if hasattr(call, 'name'):
                        G.add_edge(func.name, call.name)
        
        # Filter to specific function if requested
        if function_name and function_name in G:
            subgraph_nodes = set([function_name])
            subgraph_nodes.update(G.successors(function_name))
            subgraph_nodes.update(G.predecessors(function_name))
            G = G.subgraph(subgraph_nodes)
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='lightgreen', 
                node_size=500, font_size=8, arrows=True)
        plt.title(f"Function Call Graph{' for ' + function_name if function_name else ''}")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {
            'graph_file': output_path,
            'total_functions': len(functions),
            'total_calls': G.number_of_edges(),
            'focus_function': function_name
        }
    
    def class_hierarchy(self, output_path: str = "class_hierarchy.png"):
        """Generate a class hierarchy visualization."""
        G = nx.DiGraph()
        
        # Add class nodes
        classes_attr = getattr(self.codebase, 'classes', [])
        classes = list(classes_attr) if hasattr(classes_attr, '__iter__') else []
        
        for cls in classes:
            methods = getattr(cls, 'methods', [])
            methods_list = list(methods) if hasattr(methods, '__iter__') else []
            G.add_node(cls.name, 
                      type='class',
                      methods_count=len(methods_list),
                      is_abstract=getattr(cls, 'is_abstract', False))
        
        # Add inheritance edges
        for cls in classes:
            superclasses = getattr(cls, 'superclasses', [])
            if hasattr(superclasses, '__iter__'):
                superclasses_list = list(superclasses)
                for parent in superclasses_list:
                    if hasattr(parent, 'name'):
                        G.add_edge(parent.name, cls.name)
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, node_color='lightcoral', 
                node_size=500, font_size=8, arrows=True)
        plt.title("Class Hierarchy")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return {
            'graph_file': output_path,
            'total_classes': len(classes),
            'inheritance_relationships': G.number_of_edges()
        }
    
    def symbol_usage_graph(self, symbol_name: Optional[str] = None, output_path: str = "symbol_usage.png"):
        """
        Generate a symbol usage graph showing where symbols are used.
        
        Args:
            symbol_name: If specified, generate usage graph for specific symbol
            
        Returns:
            Dictionary representation of the symbol usage graph
        """
        nodes = []
        edges = []
        
        symbols = [self.codebase.get_symbol(symbol_name)] if symbol_name else self.codebase.symbols
        symbols = [s for s in symbols if s is not None]
        
        # Add symbol nodes
        for symbol in symbols:
            nodes.append({
                "id": symbol.name,
                "type": "symbol",
                "symbol_type": str(symbol.symbol_type) if hasattr(symbol, 'symbol_type') else "unknown",
                "label": symbol.name,
                "file": symbol.file.name if hasattr(symbol, 'file') else "unknown",
                "usages_count": len(symbol.usages) if hasattr(symbol, 'usages') else 0
            })
        
        # Add usage edges
        for symbol in symbols:
            if hasattr(symbol, 'usages'):
                for usage in symbol.usages:
                    if hasattr(usage, 'name'):
                        edges.append({
                            "source": symbol.name,
                            "target": usage.name,
                            "type": "used_by"
                        })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_symbols": len(symbols),
                "total_usages": len(edges)
            }
        }
    
    def export_graph(self, graph_data: Dict[str, Any], filename: str, format: str = "json"):
        """
        Export graph data to various formats.
        
        Args:
            graph_data: Graph data from other methods
            filename: Output filename
            format: Export format ("json", "graphml", "dot")
        """
        if format == "json":
            with open(filename, 'w') as f:
                json.dump(graph_data, f, indent=2)
        elif format == "dot":
            # Simple DOT format export
            with open(filename, 'w') as f:
                f.write("digraph G {\n")
                for node in graph_data["nodes"]:
                    f.write(f'  "{node["id"]}" [label="{node["label"]}", type="{node["type"]}"];\n')
                for edge in graph_data["edges"]:
                    f.write(f'  "{edge["source"]}" -> "{edge["target"]}" [type="{edge["type"]}"];\n')
                f.write("}\n")
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def generate_summary_report(self, output_path: str = "codebase_report.json") -> Dict[str, Any]:
        """Generate a comprehensive summary report of the codebase."""
        files_attr = getattr(self.codebase, 'files', [])
        files = list(files_attr) if hasattr(files_attr, '__iter__') else []
        
        functions_attr = getattr(self.codebase, 'functions', [])
        functions = list(functions_attr) if hasattr(functions_attr, '__iter__') else []
        
        classes_attr = getattr(self.codebase, 'classes', [])
        classes = list(classes_attr) if hasattr(classes_attr, '__iter__') else []
        
        imports_attr = getattr(self.codebase, 'imports', [])
        imports = list(imports_attr) if hasattr(imports_attr, '__iter__') else []
        
        # Calculate metrics
        total_lines = sum(getattr(f, 'line_count', 0) for f in files)
        avg_file_size = total_lines / len(files) if files else 0
        
        # Function metrics
        async_functions = [f for f in functions if getattr(f, 'is_async', False)]
        generator_functions = [f for f in functions if getattr(f, 'is_generator', False)]
        
        # Class metrics
        abstract_classes = [c for c in classes if getattr(c, 'is_abstract', False)]
        
        report = {
            'summary': {
                'total_files': len(files),
                'total_functions': len(functions),
                'total_classes': len(classes),
                'total_imports': len(imports),
                'total_lines': total_lines,
                'average_file_size': avg_file_size
            },
            'function_analysis': {
                'async_functions': len(async_functions),
                'generator_functions': len(generator_functions),
                'regular_functions': len(functions) - len(async_functions) - len(generator_functions)
            },
            'class_analysis': {
                'abstract_classes': len(abstract_classes),
                'concrete_classes': len(classes) - len(abstract_classes)
            },
            'file_analysis': {
                'python_files': len([f for f in files if f.path.endswith('.py')]) if files else 0,
                'other_files': len([f for f in files if not f.path.endswith('.py')]) if files else 0
            }
        }
        
        # Save report
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

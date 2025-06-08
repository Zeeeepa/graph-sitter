"""
Visualize class for graph-sitter code visualization

This module provides visualization capabilities for code relationships,
dependency graphs, and other codebase insights using the actual graph-sitter API.
"""

from graph_sitter import Codebase
import json
from typing import Dict, List, Any


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
    
    def dependency_graph(self, format: str = "json") -> Dict[str, Any]:
        """
        Generate a dependency graph showing relationships between files and modules.
        
        Args:
            format: Output format ("json", "networkx", "graphviz")
            
        Returns:
            Dictionary representation of the dependency graph
        """
        nodes = []
        edges = []
        
        # Add file nodes
        for file in self.codebase.files:
            nodes.append({
                "id": file.name,
                "type": "file",
                "label": file.name,
                "symbols_count": len(file.symbols),
                "imports_count": len(file.imports)
            })
        
        # Add external module nodes
        for ext_mod in self.codebase.external_modules:
            nodes.append({
                "id": ext_mod.name,
                "type": "external_module", 
                "label": ext_mod.name
            })
        
        # Add import edges
        for file in self.codebase.files:
            for import_stmt in file.imports:
                if import_stmt.imported_symbol:
                    target = import_stmt.imported_symbol.name if hasattr(import_stmt.imported_symbol, 'name') else str(import_stmt.imported_symbol)
                    edges.append({
                        "source": file.name,
                        "target": target,
                        "type": "imports",
                        "import_type": import_stmt.import_type if hasattr(import_stmt, 'import_type') else "unknown"
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_files": len(self.codebase.files),
                "total_external_modules": len(self.codebase.external_modules),
                "total_imports": len(self.codebase.imports)
            }
        }
    
    def call_graph(self, function_name: str = None) -> Dict[str, Any]:
        """
        Generate a call graph showing function call relationships.
        
        Args:
            function_name: If specified, generate call graph for specific function
            
        Returns:
            Dictionary representation of the call graph
        """
        nodes = []
        edges = []
        
        functions = [self.codebase.get_function(function_name)] if function_name else self.codebase.functions
        functions = [f for f in functions if f is not None]
        
        # Add function nodes
        for func in functions:
            nodes.append({
                "id": func.name,
                "type": "function",
                "label": func.name,
                "file": func.file.name if hasattr(func, 'file') else "unknown",
                "call_sites_count": len(func.call_sites),
                "function_calls_count": len(func.function_calls),
                "is_async": func.is_async,
                "is_generator": func.is_generator
            })
        
        # Add call edges
        for func in functions:
            for called_func in func.function_calls:
                if hasattr(called_func, 'name'):
                    edges.append({
                        "source": func.name,
                        "target": called_func.name,
                        "type": "calls"
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_functions": len(functions),
                "total_calls": len(edges)
            }
        }
    
    def class_hierarchy(self) -> Dict[str, Any]:
        """
        Generate a class hierarchy visualization.
        
        Returns:
            Dictionary representation of the class hierarchy
        """
        nodes = []
        edges = []
        
        # Add class nodes
        for cls in self.codebase.classes:
            nodes.append({
                "id": cls.name,
                "type": "class",
                "label": cls.name,
                "file": cls.file.name if hasattr(cls, 'file') else "unknown",
                "methods_count": len(cls.methods),
                "attributes_count": len(cls.attributes),
                "parent_classes": cls.parent_class_names
            })
        
        # Add inheritance edges
        for cls in self.codebase.classes:
            for parent_name in cls.parent_class_names:
                edges.append({
                    "source": parent_name,
                    "target": cls.name,
                    "type": "inherits"
                })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_classes": len(self.codebase.classes),
                "inheritance_relationships": len(edges)
            }
        }
    
    def symbol_usage_graph(self, symbol_name: str = None) -> Dict[str, Any]:
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
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive summary report of the codebase.
        
        Returns:
            Dictionary containing various codebase metrics and insights
        """
        return {
            "files": {
                "total": len(self.codebase.files),
                "with_classes": len([f for f in self.codebase.files if f.classes]),
                "with_functions": len([f for f in self.codebase.files if f.functions]),
                "with_imports": len([f for f in self.codebase.files if f.imports])
            },
            "symbols": {
                "total": len(self.codebase.symbols),
                "classes": len(self.codebase.classes),
                "functions": len(self.codebase.functions)
            },
            "dependencies": {
                "total_imports": len(self.codebase.imports),
                "external_modules": len(self.codebase.external_modules)
            },
            "complexity": {
                "avg_functions_per_file": len(self.codebase.functions) / len(self.codebase.files) if self.codebase.files else 0,
                "avg_classes_per_file": len(self.codebase.classes) / len(self.codebase.files) if self.codebase.files else 0
            }
        }


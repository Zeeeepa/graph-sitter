#!/usr/bin/env python3
"""
Deep Comprehensive Analysis Module for Graph-sitter
==================================================

This module provides deep, comprehensive analysis capabilities that go beyond
the basic analysis functions. It includes advanced metrics, visualization data,
dependency analysis, and comprehensive codebase insights.
"""

import sys
import json
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from collections import defaultdict, Counter
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeepCodebaseAnalyzer:
    """Comprehensive deep analysis of codebases using graph-sitter."""
    
    def __init__(self, codebase):
        self.codebase = codebase
        self.analysis_cache = {}
        
    def analyze_comprehensive_metrics(self) -> Dict[str, Any]:
        """Generate comprehensive codebase metrics."""
        try:
            logger.info("Starting comprehensive metrics analysis...")
            
            # Basic counts
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            symbols = list(self.codebase.symbols)
            imports = []
            
            # Collect all imports
            for file in files:
                imports.extend(file.imports)
            
            # Advanced metrics
            metrics = {
                "basic_counts": {
                    "total_files": len(files),
                    "total_functions": len(functions),
                    "total_classes": len(classes),
                    "total_symbols": len(symbols),
                    "total_imports": len(imports)
                },
                "complexity_metrics": self._calculate_complexity_metrics(files, functions, classes),
                "dependency_metrics": self._calculate_dependency_metrics(files, imports),
                "code_quality_metrics": self._calculate_quality_metrics(files, functions, classes),
                "distribution_metrics": self._calculate_distribution_metrics(files, functions, classes),
                "architectural_metrics": self._calculate_architectural_metrics(files, classes, functions)
            }
            
            logger.info("Comprehensive metrics analysis completed")
            return metrics
            
        except Exception as e:
            logger.error(f"Error in comprehensive metrics analysis: {e}")
            return {"error": str(e), "traceback": traceback.format_exc()}
    
    def _calculate_complexity_metrics(self, files, functions, classes) -> Dict[str, Any]:
        """Calculate complexity metrics."""
        try:
            # Function complexity analysis
            function_complexities = []
            for func in functions:
                # Estimate complexity based on dependencies and parameters
                complexity = len(func.dependencies) + len(func.parameters) + 1
                function_complexities.append(complexity)
            
            # Class complexity analysis
            class_complexities = []
            for cls in classes:
                # Estimate complexity based on methods and attributes
                complexity = len(cls.methods) + len(cls.attributes) + len(cls.decorators)
                class_complexities.append(complexity)
            
            # File complexity analysis
            file_complexities = []
            for file in files:
                # Estimate complexity based on symbols and imports
                complexity = len(file.symbols) + len(file.imports)
                file_complexities.append(complexity)
            
            return {
                "function_complexity": {
                    "average": sum(function_complexities) / len(function_complexities) if function_complexities else 0,
                    "max": max(function_complexities) if function_complexities else 0,
                    "min": min(function_complexities) if function_complexities else 0,
                    "distribution": self._get_distribution(function_complexities)
                },
                "class_complexity": {
                    "average": sum(class_complexities) / len(class_complexities) if class_complexities else 0,
                    "max": max(class_complexities) if class_complexities else 0,
                    "min": min(class_complexities) if class_complexities else 0,
                    "distribution": self._get_distribution(class_complexities)
                },
                "file_complexity": {
                    "average": sum(file_complexities) / len(file_complexities) if file_complexities else 0,
                    "max": max(file_complexities) if file_complexities else 0,
                    "min": min(file_complexities) if file_complexities else 0,
                    "distribution": self._get_distribution(file_complexities)
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating complexity metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_dependency_metrics(self, files, imports) -> Dict[str, Any]:
        """Calculate dependency metrics."""
        try:
            # Import analysis
            import_sources = [imp.name for imp in imports if hasattr(imp, 'name')]
            import_counter = Counter(import_sources)
            
            # File dependency analysis
            file_dependencies = {}
            for file in files:
                file_dependencies[file.name] = {
                    "imports": len(file.imports),
                    "symbols": len(file.symbols),
                    "functions": len(file.functions),
                    "classes": len(file.classes)
                }
            
            # Most connected files
            most_connected = sorted(
                file_dependencies.items(),
                key=lambda x: x[1]["imports"] + x[1]["symbols"],
                reverse=True
            )[:10]
            
            return {
                "most_imported_modules": dict(import_counter.most_common(10)),
                "total_unique_imports": len(set(import_sources)),
                "average_imports_per_file": len(imports) / len(files) if files else 0,
                "most_connected_files": most_connected,
                "dependency_graph_stats": {
                    "total_edges": len(imports),
                    "total_nodes": len(files),
                    "density": len(imports) / (len(files) * (len(files) - 1)) if len(files) > 1 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating dependency metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_quality_metrics(self, files, functions, classes) -> Dict[str, Any]:
        """Calculate code quality metrics."""
        try:
            # Function quality metrics
            functions_with_params = [f for f in functions if len(f.parameters) > 0]
            functions_with_docs = [f for f in functions if hasattr(f, 'docstring') and f.docstring]
            
            # Class quality metrics
            classes_with_methods = [c for c in classes if len(c.methods) > 0]
            classes_with_docs = [c for c in classes if hasattr(c, 'docstring') and c.docstring]
            
            # File quality metrics
            files_with_imports = [f for f in files if len(f.imports) > 0]
            files_with_classes = [f for f in files if len(f.classes) > 0]
            files_with_functions = [f for f in files if len(f.functions) > 0]
            
            return {
                "function_quality": {
                    "total_functions": len(functions),
                    "functions_with_parameters": len(functions_with_params),
                    "functions_with_documentation": len(functions_with_docs),
                    "parameter_usage_rate": len(functions_with_params) / len(functions) if functions else 0,
                    "documentation_rate": len(functions_with_docs) / len(functions) if functions else 0
                },
                "class_quality": {
                    "total_classes": len(classes),
                    "classes_with_methods": len(classes_with_methods),
                    "classes_with_documentation": len(classes_with_docs),
                    "method_usage_rate": len(classes_with_methods) / len(classes) if classes else 0,
                    "documentation_rate": len(classes_with_docs) / len(classes) if classes else 0
                },
                "file_quality": {
                    "total_files": len(files),
                    "files_with_imports": len(files_with_imports),
                    "files_with_classes": len(files_with_classes),
                    "files_with_functions": len(files_with_functions),
                    "import_usage_rate": len(files_with_imports) / len(files) if files else 0,
                    "class_definition_rate": len(files_with_classes) / len(files) if files else 0,
                    "function_definition_rate": len(files_with_functions) / len(files) if files else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_distribution_metrics(self, files, functions, classes) -> Dict[str, Any]:
        """Calculate distribution metrics across the codebase."""
        try:
            # File size distribution (by symbol count)
            file_sizes = [len(file.symbols) for file in files]
            
            # Function parameter distribution
            function_param_counts = [len(func.parameters) for func in functions]
            
            # Class method distribution
            class_method_counts = [len(cls.methods) for cls in classes]
            
            # Directory distribution
            file_paths = [getattr(file, 'filepath', file.name) for file in files]
            directories = [str(Path(path).parent) for path in file_paths]
            directory_counter = Counter(directories)
            
            return {
                "file_size_distribution": {
                    "by_symbol_count": self._get_distribution(file_sizes),
                    "average_symbols_per_file": sum(file_sizes) / len(file_sizes) if file_sizes else 0
                },
                "function_parameter_distribution": {
                    "distribution": self._get_distribution(function_param_counts),
                    "average_parameters": sum(function_param_counts) / len(function_param_counts) if function_param_counts else 0
                },
                "class_method_distribution": {
                    "distribution": self._get_distribution(class_method_counts),
                    "average_methods": sum(class_method_counts) / len(class_method_counts) if class_method_counts else 0
                },
                "directory_distribution": dict(directory_counter.most_common(10))
            }
            
        except Exception as e:
            logger.error(f"Error calculating distribution metrics: {e}")
            return {"error": str(e)}
    
    def _calculate_architectural_metrics(self, files, classes, functions) -> Dict[str, Any]:
        """Calculate architectural metrics."""
        try:
            # Inheritance analysis
            inheritance_chains = []
            for cls in classes:
                if hasattr(cls, 'parent_class_names') and cls.parent_class_names:
                    inheritance_chains.append(len(cls.parent_class_names))
            
            # Module coupling analysis
            module_connections = defaultdict(set)
            for file in files:
                file_name = file.name
                for imp in file.imports:
                    if hasattr(imp, 'name'):
                        module_connections[file_name].add(imp.name)
            
            # Calculate coupling metrics
            coupling_scores = {name: len(connections) for name, connections in module_connections.items()}
            
            return {
                "inheritance_metrics": {
                    "classes_with_inheritance": len(inheritance_chains),
                    "average_inheritance_depth": sum(inheritance_chains) / len(inheritance_chains) if inheritance_chains else 0,
                    "max_inheritance_depth": max(inheritance_chains) if inheritance_chains else 0
                },
                "coupling_metrics": {
                    "average_coupling": sum(coupling_scores.values()) / len(coupling_scores) if coupling_scores else 0,
                    "max_coupling": max(coupling_scores.values()) if coupling_scores else 0,
                    "highly_coupled_modules": sorted(coupling_scores.items(), key=lambda x: x[1], reverse=True)[:5]
                },
                "cohesion_metrics": {
                    "files_per_class": len(files) / len(classes) if classes else 0,
                    "functions_per_file": len(functions) / len(files) if files else 0,
                    "classes_per_file": len(classes) / len(files) if files else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating architectural metrics: {e}")
            return {"error": str(e)}
    
    def _get_distribution(self, values: List[int]) -> Dict[str, int]:
        """Get distribution of values in ranges."""
        if not values:
            return {}
        
        ranges = {
            "0-5": 0,
            "6-10": 0,
            "11-20": 0,
            "21-50": 0,
            "51+": 0
        }
        
        for value in values:
            if value <= 5:
                ranges["0-5"] += 1
            elif value <= 10:
                ranges["6-10"] += 1
            elif value <= 20:
                ranges["11-20"] += 1
            elif value <= 50:
                ranges["21-50"] += 1
            else:
                ranges["51+"] += 1
        
        return ranges
    
    def analyze_hotspots(self) -> Dict[str, Any]:
        """Identify code hotspots and areas of concern."""
        try:
            logger.info("Analyzing code hotspots...")
            
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            
            hotspots = {
                "complex_functions": self._identify_complex_functions(functions),
                "large_classes": self._identify_large_classes(classes),
                "highly_coupled_files": self._identify_coupled_files(files),
                "potential_issues": self._identify_potential_issues(files, functions, classes)
            }
            
            logger.info("Hotspot analysis completed")
            return hotspots
            
        except Exception as e:
            logger.error(f"Error in hotspot analysis: {e}")
            return {"error": str(e), "traceback": traceback.format_exc()}
    
    def _identify_complex_functions(self, functions) -> List[Dict[str, Any]]:
        """Identify complex functions that may need refactoring."""
        complex_functions = []
        
        for func in functions:
            complexity_score = len(func.dependencies) + len(func.parameters)
            if complexity_score > 10:  # Threshold for complexity
                complex_functions.append({
                    "name": func.name,
                    "file": getattr(func, 'filepath', 'Unknown'),
                    "complexity_score": complexity_score,
                    "dependencies": len(func.dependencies),
                    "parameters": len(func.parameters),
                    "reason": "High complexity due to many dependencies and parameters"
                })
        
        return sorted(complex_functions, key=lambda x: x["complexity_score"], reverse=True)[:10]
    
    def _identify_large_classes(self, classes) -> List[Dict[str, Any]]:
        """Identify large classes that may need refactoring."""
        large_classes = []
        
        for cls in classes:
            size_score = len(cls.methods) + len(cls.attributes)
            if size_score > 15:  # Threshold for large classes
                large_classes.append({
                    "name": cls.name,
                    "file": getattr(cls, 'filepath', 'Unknown'),
                    "size_score": size_score,
                    "methods": len(cls.methods),
                    "attributes": len(cls.attributes),
                    "reason": "Large class with many methods and attributes"
                })
        
        return sorted(large_classes, key=lambda x: x["size_score"], reverse=True)[:10]
    
    def _identify_coupled_files(self, files) -> List[Dict[str, Any]]:
        """Identify highly coupled files."""
        coupled_files = []
        
        for file in files:
            coupling_score = len(file.imports) + len(file.symbols)
            if coupling_score > 20:  # Threshold for high coupling
                coupled_files.append({
                    "name": file.name,
                    "path": getattr(file, 'filepath', 'Unknown'),
                    "coupling_score": coupling_score,
                    "imports": len(file.imports),
                    "symbols": len(file.symbols),
                    "reason": "High coupling due to many imports and symbol references"
                })
        
        return sorted(coupled_files, key=lambda x: x["coupling_score"], reverse=True)[:10]
    
    def _identify_potential_issues(self, files, functions, classes) -> List[Dict[str, Any]]:
        """Identify potential code issues."""
        issues = []
        
        # Functions without parameters (potential utility functions)
        for func in functions:
            if len(func.parameters) == 0 and len(func.dependencies) > 5:
                issues.append({
                    "type": "function_without_params",
                    "name": func.name,
                    "file": getattr(func, 'filepath', 'Unknown'),
                    "severity": "medium",
                    "description": "Function with no parameters but many dependencies"
                })
        
        # Classes without methods (potential data classes)
        for cls in classes:
            if len(cls.methods) == 0 and len(cls.attributes) > 0:
                issues.append({
                    "type": "class_without_methods",
                    "name": cls.name,
                    "file": getattr(cls, 'filepath', 'Unknown'),
                    "severity": "low",
                    "description": "Class with attributes but no methods"
                })
        
        # Files with many imports but few symbols
        for file in files:
            if len(file.imports) > 10 and len(file.symbols) < 5:
                issues.append({
                    "type": "import_heavy_file",
                    "name": file.name,
                    "file": getattr(file, 'filepath', 'Unknown'),
                    "severity": "medium",
                    "description": "File with many imports but few defined symbols"
                })
        
        return issues[:20]  # Return top 20 issues
    
    def generate_visualization_data(self) -> Dict[str, Any]:
        """Generate data for codebase visualization."""
        try:
            logger.info("Generating visualization data...")
            
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            
            # Node data for graph visualization
            nodes = []
            edges = []
            
            # Add file nodes
            for file in files:
                nodes.append({
                    "id": f"file_{file.name}",
                    "label": file.name,
                    "type": "file",
                    "size": len(file.symbols),
                    "color": "#3498db",
                    "metadata": {
                        "imports": len(file.imports),
                        "symbols": len(file.symbols),
                        "functions": len(file.functions),
                        "classes": len(file.classes)
                    }
                })
            
            # Add class nodes
            for cls in classes:
                nodes.append({
                    "id": f"class_{cls.name}",
                    "label": cls.name,
                    "type": "class",
                    "size": len(cls.methods) + len(cls.attributes),
                    "color": "#e74c3c",
                    "metadata": {
                        "methods": len(cls.methods),
                        "attributes": len(cls.attributes),
                        "decorators": len(cls.decorators)
                    }
                })
            
            # Add function nodes
            for func in functions:
                nodes.append({
                    "id": f"function_{func.name}",
                    "label": func.name,
                    "type": "function",
                    "size": len(func.parameters) + len(func.dependencies),
                    "color": "#2ecc71",
                    "metadata": {
                        "parameters": len(func.parameters),
                        "dependencies": len(func.dependencies)
                    }
                })
            
            # Add edges for imports and dependencies
            for file in files:
                for imp in file.imports:
                    if hasattr(imp, 'name'):
                        edges.append({
                            "source": f"file_{file.name}",
                            "target": f"import_{imp.name}",
                            "type": "import",
                            "weight": 1
                        })
            
            visualization_data = {
                "graph": {
                    "nodes": nodes,
                    "edges": edges
                },
                "hierarchy": self._generate_hierarchy_data(files, classes, functions),
                "metrics_charts": self._generate_chart_data(files, functions, classes),
                "heatmap": self._generate_heatmap_data(files, functions, classes)
            }
            
            logger.info("Visualization data generated")
            return visualization_data
            
        except Exception as e:
            logger.error(f"Error generating visualization data: {e}")
            return {"error": str(e), "traceback": traceback.format_exc()}
    
    def _generate_hierarchy_data(self, files, classes, functions) -> Dict[str, Any]:
        """Generate hierarchical data for tree visualization."""
        hierarchy = {
            "name": "Codebase",
            "children": []
        }
        
        # Group by directories
        file_groups = defaultdict(list)
        for file in files:
            file_path = getattr(file, 'filepath', file.name)
            directory = str(Path(file_path).parent)
            file_groups[directory].append(file)
        
        for directory, dir_files in file_groups.items():
            dir_node = {
                "name": directory,
                "type": "directory",
                "children": []
            }
            
            for file in dir_files:
                file_node = {
                    "name": file.name,
                    "type": "file",
                    "size": len(file.symbols),
                    "children": []
                }
                
                # Add classes in this file
                file_classes = [cls for cls in classes if getattr(cls, 'filepath', '').endswith(file.name)]
                for cls in file_classes:
                    class_node = {
                        "name": cls.name,
                        "type": "class",
                        "size": len(cls.methods) + len(cls.attributes)
                    }
                    file_node["children"].append(class_node)
                
                # Add functions in this file
                file_functions = [func for func in functions if getattr(func, 'filepath', '').endswith(file.name)]
                for func in file_functions:
                    function_node = {
                        "name": func.name,
                        "type": "function",
                        "size": len(func.parameters) + len(func.dependencies)
                    }
                    file_node["children"].append(function_node)
                
                dir_node["children"].append(file_node)
            
            hierarchy["children"].append(dir_node)
        
        return hierarchy
    
    def _generate_chart_data(self, files, functions, classes) -> Dict[str, Any]:
        """Generate data for various charts."""
        return {
            "complexity_distribution": {
                "labels": ["Low (0-5)", "Medium (6-10)", "High (11-20)", "Very High (21+)"],
                "data": self._get_complexity_distribution(functions)
            },
            "file_size_distribution": {
                "labels": ["Small (0-10)", "Medium (11-50)", "Large (51-100)", "Very Large (101+)"],
                "data": self._get_file_size_distribution(files)
            },
            "class_method_distribution": {
                "labels": ["Few (0-5)", "Some (6-10)", "Many (11-20)", "Too Many (21+)"],
                "data": self._get_class_method_distribution(classes)
            }
        }
    
    def _generate_heatmap_data(self, files, functions, classes) -> List[List[int]]:
        """Generate heatmap data for complexity visualization."""
        # Create a simple heatmap based on file complexity
        heatmap = []
        
        # Group files into a grid (10x10 for simplicity)
        grid_size = 10
        files_per_cell = max(1, len(files) // (grid_size * grid_size))
        
        for i in range(grid_size):
            row = []
            for j in range(grid_size):
                cell_index = i * grid_size + j
                start_idx = cell_index * files_per_cell
                end_idx = min(start_idx + files_per_cell, len(files))
                
                if start_idx < len(files):
                    cell_files = files[start_idx:end_idx]
                    complexity = sum(len(f.symbols) + len(f.imports) for f in cell_files)
                    row.append(complexity)
                else:
                    row.append(0)
            heatmap.append(row)
        
        return heatmap
    
    def _get_complexity_distribution(self, functions) -> List[int]:
        """Get complexity distribution for functions."""
        distribution = [0, 0, 0, 0]  # Low, Medium, High, Very High
        
        for func in functions:
            complexity = len(func.dependencies) + len(func.parameters)
            if complexity <= 5:
                distribution[0] += 1
            elif complexity <= 10:
                distribution[1] += 1
            elif complexity <= 20:
                distribution[2] += 1
            else:
                distribution[3] += 1
        
        return distribution
    
    def _get_file_size_distribution(self, files) -> List[int]:
        """Get file size distribution."""
        distribution = [0, 0, 0, 0]  # Small, Medium, Large, Very Large
        
        for file in files:
            size = len(file.symbols)
            if size <= 10:
                distribution[0] += 1
            elif size <= 50:
                distribution[1] += 1
            elif size <= 100:
                distribution[2] += 1
            else:
                distribution[3] += 1
        
        return distribution
    
    def _get_class_method_distribution(self, classes) -> List[int]:
        """Get class method distribution."""
        distribution = [0, 0, 0, 0]  # Few, Some, Many, Too Many
        
        for cls in classes:
            methods = len(cls.methods)
            if methods <= 5:
                distribution[0] += 1
            elif methods <= 10:
                distribution[1] += 1
            elif methods <= 20:
                distribution[2] += 1
            else:
                distribution[3] += 1
        
        return distribution

# Export the analyzer class
__all__ = ['DeepCodebaseAnalyzer']

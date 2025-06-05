"""
Visualization Interface - Interactive visualization selection and rendering system
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class

logger = logging.getLogger(__name__)


class VisualizationInterface:
    """
    Interactive visualization interface for codebase analysis.
    
    Provides dropdown selections for different analysis types and target components,
    with real-time rendering updates and export capabilities.
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize the visualization interface."""
        self.codebase = codebase
        self.available_visualizations = {
            'dependency': 'Dependency Analysis',
            'call_graph': 'Call Graph',
            'blast_radius': 'Blast Radius Analysis',
            'complexity_heatmap': 'Complexity Heatmap',
            'class_relationships': 'Class Relationships',
            'file_structure': 'File Structure Tree',
            'import_graph': 'Import Dependencies',
            'function_flow': 'Function Flow Diagram'
        }
    
    def get_available_visualizations(self) -> Dict[str, str]:
        """Get list of available visualization types."""
        return self.available_visualizations.copy()
    
    def get_available_targets(self, viz_type: str) -> List[Dict[str, str]]:
        """
        Get available targets for a specific visualization type.
        
        Args:
            viz_type: Type of visualization
            
        Returns:
            List of available targets with their metadata
        """
        targets = []
        
        if viz_type in ['blast_radius', 'function_flow']:
            # Function-based visualizations
            for func in self.codebase.functions:
                targets.append({
                    'name': func.name,
                    'type': 'function',
                    'file': func.file.path if func.file else 'unknown',
                    'description': f"Function: {func.name}"
                })
        
        elif viz_type in ['class_relationships', 'blast_radius']:
            # Class-based visualizations
            for cls in self.codebase.classes:
                targets.append({
                    'name': cls.name,
                    'type': 'class',
                    'file': cls.file.path if cls.file else 'unknown',
                    'description': f"Class: {cls.name}"
                })
        
        elif viz_type in ['dependency', 'import_graph']:
            # File-based visualizations
            for file in self.codebase.files:
                targets.append({
                    'name': file.path,
                    'type': 'file',
                    'file': file.path,
                    'description': f"File: {file.path}"
                })
        
        return targets
    
    def generate_all_visualizations(self) -> Dict[str, Any]:
        """Generate data for all visualization types."""
        visualization_data = {}
        
        for viz_type in self.available_visualizations.keys():
            try:
                visualization_data[viz_type] = self.get_visualization(viz_type)
            except Exception as e:
                logger.warning(f"Failed to generate {viz_type} visualization: {e}")
                visualization_data[viz_type] = {'error': str(e)}
        
        return visualization_data
    
    def get_visualization(self, 
                         viz_type: str, 
                         target: Optional[str] = None,
                         **kwargs) -> Dict[str, Any]:
        """
        Get specific visualization data.
        
        Args:
            viz_type: Type of visualization
            target: Target component (function name, class name, etc.)
            **kwargs: Additional parameters for visualization
            
        Returns:
            Visualization data in format suitable for rendering
        """
        if viz_type not in self.available_visualizations:
            raise ValueError(f"Unknown visualization type: {viz_type}")
        
        # Route to specific visualization generator
        generators = {
            'dependency': self._generate_dependency_visualization,
            'call_graph': self._generate_call_graph_visualization,
            'blast_radius': self._generate_blast_radius_visualization,
            'complexity_heatmap': self._generate_complexity_heatmap,
            'class_relationships': self._generate_class_relationships,
            'file_structure': self._generate_file_structure,
            'import_graph': self._generate_import_graph,
            'function_flow': self._generate_function_flow
        }
        
        generator = generators.get(viz_type)
        if not generator:
            raise ValueError(f"No generator available for {viz_type}")
        
        return generator(target, **kwargs)
    
    def _generate_dependency_visualization(self, target: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate dependency analysis visualization."""
        nodes = []
        edges = []
        
        # Get all files and their dependencies
        for file in self.codebase.files:
            nodes.append({
                'id': file.path,
                'label': file.name,
                'type': 'file',
                'size': len(file.content) if hasattr(file, 'content') else 10
            })
            
            # Add import dependencies as edges
            for import_stmt in file.imports:
                if hasattr(import_stmt, 'module_name'):
                    edges.append({
                        'source': file.path,
                        'target': import_stmt.module_name,
                        'type': 'import'
                    })
        
        return {
            'type': 'network',
            'data': {
                'nodes': nodes,
                'edges': edges
            },
            'layout': 'force-directed',
            'config': {
                'title': f'Dependency Analysis{f" - {target}" if target else ""}',
                'node_color_by': 'type',
                'edge_color_by': 'type'
            }
        }
    
    def _generate_call_graph_visualization(self, target: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate call graph visualization."""
        nodes = []
        edges = []
        
        # Add function nodes
        for func in self.codebase.functions:
            nodes.append({
                'id': func.name,
                'label': func.name,
                'type': 'function',
                'file': func.file.path if func.file else 'unknown',
                'complexity': getattr(func, 'complexity', 1)
            })
        
        # Add call relationships (simplified - would need actual call analysis)
        # This is a placeholder implementation
        for func in self.codebase.functions:
            # In a real implementation, you'd analyze function calls
            # For now, we'll create some sample connections
            pass
        
        return {
            'type': 'network',
            'data': {
                'nodes': nodes,
                'edges': edges
            },
            'layout': 'hierarchical',
            'config': {
                'title': f'Call Graph{f" - {target}" if target else ""}',
                'node_size_by': 'complexity',
                'highlight_target': target
            }
        }
    
    def _generate_blast_radius_visualization(self, target: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate blast radius analysis visualization."""
        if not target:
            return {'error': 'Target component required for blast radius analysis'}
        
        # Find the target component
        target_component = None
        component_type = None
        
        # Check if target is a function
        for func in self.codebase.functions:
            if func.name == target:
                target_component = func
                component_type = 'function'
                break
        
        # Check if target is a class
        if not target_component:
            for cls in self.codebase.classes:
                if cls.name == target:
                    target_component = cls
                    component_type = 'class'
                    break
        
        if not target_component:
            return {'error': f'Target component "{target}" not found'}
        
        # Generate blast radius data
        nodes = [{'id': target, 'label': target, 'type': component_type, 'level': 0}]
        edges = []
        
        # Add directly connected components (level 1)
        # This is simplified - would need actual dependency analysis
        level_1_components = self._find_connected_components(target_component)
        
        for comp in level_1_components:
            nodes.append({
                'id': comp['name'],
                'label': comp['name'],
                'type': comp['type'],
                'level': 1
            })
            edges.append({
                'source': target,
                'target': comp['name'],
                'type': 'dependency'
            })
        
        return {
            'type': 'network',
            'data': {
                'nodes': nodes,
                'edges': edges
            },
            'layout': 'radial',
            'config': {
                'title': f'Blast Radius Analysis - {target}',
                'center_node': target,
                'node_color_by': 'level'
            }
        }
    
    def _generate_complexity_heatmap(self, target: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate complexity heatmap visualization."""
        heatmap_data = []
        
        # Group functions by file
        files_data = {}
        for func in self.codebase.functions:
            file_path = func.file.path if func.file else 'unknown'
            if file_path not in files_data:
                files_data[file_path] = []
            
            files_data[file_path].append({
                'name': func.name,
                'complexity': getattr(func, 'complexity', 1),
                'lines': getattr(func, 'lines_of_code', 10)
            })
        
        # Convert to heatmap format
        for file_path, functions in files_data.items():
            for func in functions:
                heatmap_data.append({
                    'file': file_path,
                    'function': func['name'],
                    'complexity': func['complexity'],
                    'lines': func['lines']
                })
        
        return {
            'type': 'heatmap',
            'data': heatmap_data,
            'config': {
                'title': f'Complexity Heatmap{f" - {target}" if target else ""}',
                'x_axis': 'file',
                'y_axis': 'function',
                'color_by': 'complexity'
            }
        }
    
    def _generate_class_relationships(self, target: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate class relationships visualization."""
        nodes = []
        edges = []
        
        # Add class nodes
        for cls in self.codebase.classes:
            nodes.append({
                'id': cls.name,
                'label': cls.name,
                'type': 'class',
                'file': cls.file.path if cls.file else 'unknown',
                'methods': len(cls.methods) if hasattr(cls, 'methods') else 0
            })
        
        # Add inheritance relationships
        for cls in self.codebase.classes:
            if hasattr(cls, 'base_classes'):
                for base_class in cls.base_classes:
                    edges.append({
                        'source': base_class,
                        'target': cls.name,
                        'type': 'inheritance'
                    })
        
        return {
            'type': 'network',
            'data': {
                'nodes': nodes,
                'edges': edges
            },
            'layout': 'hierarchical',
            'config': {
                'title': f'Class Relationships{f" - {target}" if target else ""}',
                'node_size_by': 'methods',
                'edge_color_by': 'type'
            }
        }
    
    def _generate_file_structure(self, target: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate file structure tree visualization."""
        tree_data = []
        
        # Build file tree structure
        for file in self.codebase.files:
            path_parts = file.path.split('/')
            tree_data.append({
                'path': file.path,
                'name': file.name,
                'type': 'file',
                'size': len(file.content) if hasattr(file, 'content') else 0,
                'depth': len(path_parts)
            })
        
        return {
            'type': 'tree',
            'data': tree_data,
            'config': {
                'title': f'File Structure{f" - {target}" if target else ""}',
                'node_size_by': 'size'
            }
        }
    
    def _generate_import_graph(self, target: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate import dependencies graph."""
        return self._generate_dependency_visualization(target, **kwargs)
    
    def _generate_function_flow(self, target: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate function flow diagram."""
        if not target:
            return {'error': 'Target function required for function flow analysis'}
        
        # Find target function
        target_function = None
        for func in self.codebase.functions:
            if func.name == target:
                target_function = func
                break
        
        if not target_function:
            return {'error': f'Function "{target}" not found'}
        
        # Generate flow diagram (simplified)
        flow_data = {
            'function': target,
            'file': target_function.file.path if target_function.file else 'unknown',
            'steps': [
                {'id': 1, 'type': 'start', 'label': f'Function {target} starts'},
                {'id': 2, 'type': 'process', 'label': 'Process logic'},
                {'id': 3, 'type': 'end', 'label': 'Function returns'}
            ],
            'connections': [
                {'from': 1, 'to': 2},
                {'from': 2, 'to': 3}
            ]
        }
        
        return {
            'type': 'flowchart',
            'data': flow_data,
            'config': {
                'title': f'Function Flow - {target}'
            }
        }
    
    def _find_connected_components(self, component) -> List[Dict[str, str]]:
        """Find components connected to the given component."""
        # This is a simplified implementation
        # In practice, you'd analyze actual dependencies, calls, etc.
        connected = []
        
        # For demonstration, return some sample connections
        if hasattr(component, 'name'):
            # Add some sample connected components
            connected.append({
                'name': f'{component.name}_helper',
                'type': 'function'
            })
        
        return connected
    
    def export_visualization(self, 
                           viz_type: str, 
                           target: Optional[str] = None,
                           format: str = 'json',
                           output_path: Optional[str] = None) -> str:
        """
        Export visualization data to file.
        
        Args:
            viz_type: Type of visualization
            target: Target component
            format: Export format (json, svg, png)
            output_path: Output file path
            
        Returns:
            Path to exported file
        """
        viz_data = self.get_visualization(viz_type, target)
        
        if not output_path:
            output_path = f'{viz_type}_{target or "all"}.{format}'
        
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(viz_data, f, indent=2)
        else:
            # For other formats, you'd need additional libraries like matplotlib, plotly, etc.
            raise ValueError(f"Export format '{format}' not yet implemented")
        
        return output_path


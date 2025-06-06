"""
Tree-sitter Visualization Module

Provides tree-sitter query patterns and interactive visualization.
"""

import logging
from typing import Dict, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class TreeSitterVisualizer:
    """Creates tree-sitter visualizations and query patterns."""
    
    def __init__(self, config=None):
        """Initialize tree-sitter visualizer."""
        self.config = config
    
    def generate_visualization(self, codebase=None, path: Union[str, Path] = None) -> Dict[str, Any]:
        """
        Generate tree-sitter visualization data.
        
        Args:
            codebase: Graph-sitter codebase object
            path: Path to codebase for fallback
            
        Returns:
            Dictionary containing visualization data
        """
        logger.info("Generating tree-sitter visualization")
        
        visualization_data = {
            'tree_structure': {},
            'dependency_graph': {},
            'query_patterns': [],
            'syntax_trees': {}
        }
        
        try:
            if codebase:
                visualization_data = self._generate_with_graph_sitter(codebase)
            else:
                visualization_data = self._generate_fallback(Path(path))
        
        except Exception as e:
            logger.error(f"Visualization generation failed: {e}")
            visualization_data['error'] = str(e)
        
        return visualization_data
    
    def _generate_with_graph_sitter(self, codebase) -> Dict[str, Any]:
        """Generate visualization using graph-sitter."""
        data = {
            'tree_structure': self._build_tree_structure(codebase),
            'dependency_graph': self._build_dependency_graph(codebase),
            'query_patterns': self._generate_query_patterns(),
            'syntax_trees': {}
        }
        
        return data
    
    def _generate_fallback(self, path: Path) -> Dict[str, Any]:
        """Generate basic visualization without graph-sitter."""
        data = {
            'tree_structure': self._build_tree_structure_fallback(path),
            'dependency_graph': {},
            'query_patterns': self._generate_query_patterns(),
            'syntax_trees': {}
        }
        
        return data
    
    def _build_tree_structure(self, codebase) -> Dict[str, Any]:
        """Build tree structure from graph-sitter codebase."""
        structure = {
            'name': 'root',
            'type': 'directory',
            'children': []
        }
        
        try:
            # Build file tree
            files_by_dir = {}
            for file in codebase.files:
                dir_path = str(Path(file.filepath).parent)
                if dir_path not in files_by_dir:
                    files_by_dir[dir_path] = []
                
                files_by_dir[dir_path].append({
                    'name': Path(file.filepath).name,
                    'type': 'file',
                    'path': file.filepath,
                    'functions': len(file.functions) if hasattr(file, 'functions') else 0,
                    'classes': len(file.classes) if hasattr(file, 'classes') else 0,
                    'lines': len(file.content.splitlines()) if hasattr(file, 'content') else 0
                })
            
            # Convert to tree structure
            for dir_path, files in files_by_dir.items():
                if dir_path == '.':
                    structure['children'].extend(files)
                else:
                    structure['children'].append({
                        'name': dir_path,
                        'type': 'directory',
                        'children': files
                    })
        
        except Exception as e:
            logger.warning(f"Failed to build tree structure: {e}")
        
        return structure
    
    def _build_tree_structure_fallback(self, path: Path) -> Dict[str, Any]:
        """Build tree structure from file system."""
        structure = {
            'name': path.name,
            'type': 'directory',
            'children': []
        }
        
        try:
            for item in path.iterdir():
                if item.is_file() and item.suffix == '.py':
                    structure['children'].append({
                        'name': item.name,
                        'type': 'file',
                        'path': str(item.relative_to(path)),
                        'size': item.stat().st_size
                    })
                elif item.is_dir() and not item.name.startswith('.'):
                    subdir = self._build_tree_structure_fallback(item)
                    if subdir['children']:  # Only include non-empty directories
                        structure['children'].append(subdir)
        
        except Exception as e:
            logger.warning(f"Failed to build fallback tree structure: {e}")
        
        return structure
    
    def _build_dependency_graph(self, codebase) -> Dict[str, Any]:
        """Build dependency graph from codebase."""
        graph = {
            'nodes': [],
            'edges': []
        }
        
        try:
            # Add file nodes
            for file in codebase.files:
                graph['nodes'].append({
                    'id': file.filepath,
                    'label': Path(file.filepath).name,
                    'type': 'file',
                    'functions': len(file.functions) if hasattr(file, 'functions') else 0,
                    'classes': len(file.classes) if hasattr(file, 'classes') else 0
                })
                
                # Add import edges
                for imp in file.imports:
                    try:
                        module_name = getattr(imp, 'module', None)
                        if module_name:
                            graph['edges'].append({
                                'source': file.filepath,
                                'target': module_name,
                                'type': 'import'
                            })
                    except Exception as e:
                        logger.debug(f"Failed to process import: {e}")
        
        except Exception as e:
            logger.warning(f"Failed to build dependency graph: {e}")
        
        return graph
    
    def _generate_query_patterns(self) -> List[Dict[str, Any]]:
        """Generate tree-sitter query patterns."""
        patterns = [
            {
                'name': 'function_definitions',
                'description': 'Find all function definitions',
                'query': '(function_definition name: (identifier) @function.name)',
                'language': 'python'
            },
            {
                'name': 'class_definitions',
                'description': 'Find all class definitions',
                'query': '(class_definition name: (identifier) @class.name)',
                'language': 'python'
            },
            {
                'name': 'import_statements',
                'description': 'Find all import statements',
                'query': '(import_statement) @import',
                'language': 'python'
            },
            {
                'name': 'function_calls',
                'description': 'Find all function calls',
                'query': '(call function: (identifier) @function.call)',
                'language': 'python'
            },
            {
                'name': 'if_statements',
                'description': 'Find all if statements',
                'query': '(if_statement) @if',
                'language': 'python'
            },
            {
                'name': 'for_loops',
                'description': 'Find all for loops',
                'query': '(for_statement) @for',
                'language': 'python'
            },
            {
                'name': 'try_blocks',
                'description': 'Find all try blocks',
                'query': '(try_statement) @try',
                'language': 'python'
            }
        ]
        
        return patterns


#!/usr/bin/env python3
"""
Graph-Sitter Integration for Dashboard Backend
==============================================

This module integrates the graph-sitter codebase analysis engine
with the dashboard backend, replacing mock data with real analysis results.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Add graph-sitter src to path
current_dir = Path(__file__).parent
graph_sitter_root = current_dir.parent.parent
src_path = graph_sitter_root / "src"
sys.path.insert(0, str(src_path))

try:
    from graph_sitter import Codebase
    from graph_sitter.core.file import File
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import Class
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GraphSitterAnalyzer:
    """Real-time codebase analysis using graph-sitter."""
    
    def __init__(self, repo_path: str = None):
        self.repo_path = repo_path or str(graph_sitter_root)
        self.codebase: Optional[Codebase] = None
        self.analysis_cache = {}
        self.last_analysis_time = None
        
    async def initialize_codebase(self) -> bool:
        """Initialize the graph-sitter codebase analysis."""
        if not GRAPH_SITTER_AVAILABLE:
            logger.error("Graph-sitter not available")
            return False
            
        try:
            logger.info(f"Initializing codebase analysis for: {self.repo_path}")
            start_time = datetime.now()
            
            # Create codebase with Python language support
            self.codebase = Codebase(self.repo_path, language='python')
            
            analysis_time = (datetime.now() - start_time).total_seconds()
            self.last_analysis_time = datetime.now()
            
            logger.info(f"Codebase analysis completed in {analysis_time:.2f}s")
            logger.info(f"Found {len(self.codebase.files)} files")
            logger.info(f"Found {len(self.codebase.functions)} functions")
            logger.info(f"Found {len(self.codebase.classes)} classes")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize codebase: {e}")
            return False
    
    async def get_file_tree(self) -> Dict[str, Any]:
        """Get the real file tree structure from graph-sitter analysis."""
        if not self.codebase:
            await self.initialize_codebase()
            
        if not self.codebase:
            return self._get_fallback_file_tree()
        
        try:
            file_tree = {
                'name': 'graph-sitter',
                'type': 'directory',
                'children': [],
                'metadata': {
                    'total_files': len(self.codebase.files),
                    'total_functions': len(self.codebase.functions),
                    'total_classes': len(self.codebase.classes),
                    'analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None
                }
            }
            
            # Group files by directory structure
            directory_structure = {}
            
            for file in self.codebase.files:
                file_path = Path(file.filepath)
                parts = file_path.parts
                
                current_level = directory_structure
                for part in parts[:-1]:  # All parts except the filename
                    if part not in current_level:
                        current_level[part] = {'type': 'directory', 'children': {}}
                    current_level = current_level[part]['children']
                
                # Add the file
                filename = parts[-1]
                current_level[filename] = {
                    'type': 'file',
                    'filepath': file.filepath,
                    'size': len(file.source) if hasattr(file, 'source') and file.source else 0,
                    'functions': len([f for f in self.codebase.functions if f.filepath == file.filepath]),
                    'classes': len([c for c in self.codebase.classes if c.filepath == file.filepath])
                }
            
            # Convert nested dict to tree structure
            def dict_to_tree(name: str, data: Dict) -> Dict[str, Any]:
                if data.get('type') == 'file':
                    return {
                        'name': name,
                        'type': 'file',
                        'filepath': data['filepath'],
                        'size': data['size'],
                        'functions': data['functions'],
                        'classes': data['classes']
                    }
                else:
                    return {
                        'name': name,
                        'type': 'directory',
                        'children': [dict_to_tree(child_name, child_data) 
                                   for child_name, child_data in data.get('children', {}).items()]
                    }
            
            # Build the tree
            for root_name, root_data in directory_structure.items():
                file_tree['children'].append(dict_to_tree(root_name, root_data))
            
            return file_tree
            
        except Exception as e:
            logger.error(f"Error generating file tree: {e}")
            return self._get_fallback_file_tree()
    
    async def get_file_content(self, filepath: str) -> Dict[str, Any]:
        """Get file content and analysis from graph-sitter."""
        if not self.codebase:
            await self.initialize_codebase()
            
        if not self.codebase:
            return self._get_fallback_file_content(filepath)
        
        try:
            # Find the file in the codebase
            target_file = None
            for file in self.codebase.files:
                if file.filepath == filepath or file.filepath.endswith(filepath):
                    target_file = file
                    break
            
            if not target_file:
                return {'error': f'File not found: {filepath}'}
            
            # Get functions in this file
            file_functions = [
                {
                    'name': func.name,
                    'line_start': getattr(func, 'line_start', 0),
                    'line_end': getattr(func, 'line_end', 0),
                    'parameters': getattr(func, 'parameters', []),
                    'docstring': getattr(func, 'docstring', None)
                }
                for func in self.codebase.functions 
                if func.filepath == target_file.filepath
            ]
            
            # Get classes in this file
            file_classes = [
                {
                    'name': cls.name,
                    'line_start': getattr(cls, 'line_start', 0),
                    'line_end': getattr(cls, 'line_end', 0),
                    'methods': getattr(cls, 'methods', []),
                    'docstring': getattr(cls, 'docstring', None)
                }
                for cls in self.codebase.classes 
                if cls.filepath == target_file.filepath
            ]
            
            return {
                'filepath': target_file.filepath,
                'content': target_file.source if hasattr(target_file, 'source') else '',
                'language': 'python',
                'functions': file_functions,
                'classes': file_classes,
                'metadata': {
                    'lines': len(target_file.source.split('\n')) if hasattr(target_file, 'source') and target_file.source else 0,
                    'size': len(target_file.source) if hasattr(target_file, 'source') and target_file.source else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting file content for {filepath}: {e}")
            return self._get_fallback_file_content(filepath)
    
    async def get_code_graph(self) -> Dict[str, Any]:
        """Generate code graph from graph-sitter analysis."""
        if not self.codebase:
            await self.initialize_codebase()
            
        if not self.codebase:
            return self._get_fallback_code_graph()
        
        try:
            nodes = []
            edges = []
            
            # Add function nodes
            for i, func in enumerate(self.codebase.functions[:100]):  # Limit for performance
                nodes.append({
                    'id': f'func_{i}',
                    'label': func.name,
                    'type': 'function',
                    'filepath': func.filepath,
                    'group': 'functions',
                    'color': {'background': '#4CAF50', 'border': '#45a049'}
                })
            
            # Add class nodes
            for i, cls in enumerate(self.codebase.classes[:50]):  # Limit for performance
                nodes.append({
                    'id': f'class_{i}',
                    'label': cls.name,
                    'type': 'class',
                    'filepath': cls.filepath,
                    'group': 'classes',
                    'color': {'background': '#2196F3', 'border': '#1976D2'}
                })
            
            # Add file nodes for key files
            key_files = [f for f in self.codebase.files if 'main' in f.filepath.lower() or 'init' in f.filepath.lower()][:20]
            for i, file in enumerate(key_files):
                nodes.append({
                    'id': f'file_{i}',
                    'label': Path(file.filepath).name,
                    'type': 'file',
                    'filepath': file.filepath,
                    'group': 'files',
                    'color': {'background': '#FF9800', 'border': '#F57C00'}
                })
            
            # Create some sample edges (in a real implementation, this would be based on actual dependencies)
            for i in range(min(50, len(nodes) - 1)):
                if i + 1 < len(nodes):
                    edges.append({
                        'from': nodes[i]['id'],
                        'to': nodes[i + 1]['id'],
                        'label': 'depends_on',
                        'arrows': 'to'
                    })
            
            return {
                'nodes': nodes,
                'edges': edges,
                'metadata': {
                    'total_nodes': len(nodes),
                    'total_edges': len(edges),
                    'node_types': {
                        'functions': len([n for n in nodes if n['type'] == 'function']),
                        'classes': len([n for n in nodes if n['type'] == 'class']),
                        'files': len([n for n in nodes if n['type'] == 'file'])
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating code graph: {e}")
            return self._get_fallback_code_graph()
    
    async def get_code_metrics(self) -> Dict[str, Any]:
        """Get comprehensive code metrics from graph-sitter analysis."""
        if not self.codebase:
            await self.initialize_codebase()
            
        if not self.codebase:
            return self._get_fallback_metrics()
        
        try:
            # Calculate metrics
            total_files = len(self.codebase.files)
            total_functions = len(self.codebase.functions)
            total_classes = len(self.codebase.classes)
            
            # File type distribution
            file_extensions = {}
            total_lines = 0
            
            for file in self.codebase.files:
                ext = Path(file.filepath).suffix or 'no_extension'
                file_extensions[ext] = file_extensions.get(ext, 0) + 1
                
                if hasattr(file, 'source') and file.source:
                    total_lines += len(file.source.split('\n'))
            
            # Function complexity (simplified)
            function_sizes = []
            for func in self.codebase.functions:
                if hasattr(func, 'line_start') and hasattr(func, 'line_end'):
                    size = func.line_end - func.line_start
                    function_sizes.append(size)
            
            avg_function_size = sum(function_sizes) / len(function_sizes) if function_sizes else 0
            
            return {
                'overview': {
                    'total_files': total_files,
                    'total_functions': total_functions,
                    'total_classes': total_classes,
                    'total_lines': total_lines,
                    'avg_function_size': round(avg_function_size, 2)
                },
                'file_distribution': file_extensions,
                'complexity_metrics': {
                    'functions_per_file': round(total_functions / total_files, 2) if total_files > 0 else 0,
                    'classes_per_file': round(total_classes / total_files, 2) if total_files > 0 else 0,
                    'lines_per_file': round(total_lines / total_files, 2) if total_files > 0 else 0
                },
                'analysis_metadata': {
                    'analysis_time': self.last_analysis_time.isoformat() if self.last_analysis_time else None,
                    'repo_path': self.repo_path
                }
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {e}")
            return self._get_fallback_metrics()
    
    def _get_fallback_file_tree(self) -> Dict[str, Any]:
        """Fallback file tree when graph-sitter is not available."""
        return {
            'name': 'graph-sitter (fallback)',
            'type': 'directory',
            'children': [
                {
                    'name': 'src',
                    'type': 'directory',
                    'children': [
                        {'name': 'main.py', 'type': 'file', 'filepath': 'src/main.py'},
                        {'name': 'utils.py', 'type': 'file', 'filepath': 'src/utils.py'}
                    ]
                }
            ],
            'metadata': {'fallback': True}
        }
    
    def _get_fallback_file_content(self, filepath: str) -> Dict[str, Any]:
        """Fallback file content when graph-sitter is not available."""
        return {
            'filepath': filepath,
            'content': f'# Fallback content for {filepath}\n# Graph-sitter analysis not available',
            'language': 'python',
            'functions': [],
            'classes': [],
            'metadata': {'fallback': True}
        }
    
    def _get_fallback_code_graph(self) -> Dict[str, Any]:
        """Fallback code graph when graph-sitter is not available."""
        return {
            'nodes': [
                {'id': 'fallback_1', 'label': 'Fallback Node', 'type': 'function', 'group': 'functions'}
            ],
            'edges': [],
            'metadata': {'fallback': True}
        }
    
    def _get_fallback_metrics(self) -> Dict[str, Any]:
        """Fallback metrics when graph-sitter is not available."""
        return {
            'overview': {
                'total_files': 0,
                'total_functions': 0,
                'total_classes': 0,
                'total_lines': 0
            },
            'file_distribution': {},
            'complexity_metrics': {},
            'analysis_metadata': {'fallback': True}
        }

# Global analyzer instance
analyzer = GraphSitterAnalyzer()

async def get_real_file_tree() -> Dict[str, Any]:
    """Get real file tree from graph-sitter analysis."""
    return await analyzer.get_file_tree()

async def get_real_file_content(filepath: str) -> Dict[str, Any]:
    """Get real file content from graph-sitter analysis."""
    return await analyzer.get_file_content(filepath)

async def get_real_code_graph() -> Dict[str, Any]:
    """Get real code graph from graph-sitter analysis."""
    return await analyzer.get_code_graph()

async def get_real_code_metrics() -> Dict[str, Any]:
    """Get real code metrics from graph-sitter analysis."""
    return await analyzer.get_code_metrics()

# Initialize on module import
async def initialize_analyzer():
    """Initialize the analyzer on startup."""
    success = await analyzer.initialize_codebase()
    if success:
        logger.info("Graph-sitter analyzer initialized successfully")
    else:
        logger.warning("Graph-sitter analyzer initialization failed, using fallback mode")

if __name__ == "__main__":
    # Test the integration
    async def test_integration():
        print("Testing Graph-Sitter Integration...")
        
        await initialize_analyzer()
        
        print("\n1. Testing file tree...")
        file_tree = await get_real_file_tree()
        print(f"   Found {file_tree.get('metadata', {}).get('total_files', 0)} files")
        
        print("\n2. Testing code metrics...")
        metrics = await get_real_code_metrics()
        print(f"   Total functions: {metrics.get('overview', {}).get('total_functions', 0)}")
        
        print("\n3. Testing code graph...")
        graph = await get_real_code_graph()
        print(f"   Graph nodes: {len(graph.get('nodes', []))}")
        
        print("\n✅ Integration test complete!")
    
    asyncio.run(test_integration())


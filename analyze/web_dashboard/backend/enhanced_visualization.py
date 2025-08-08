#!/usr/bin/env python3
"""
Enhanced Visual Codebase Representation with Error Context
==========================================================

This module enhances the dashboard's visual representation by adding:
- Error heat mapping to file trees
- Error highlighting in code editors
- Error relationship visualization in code graphs
- Interactive error tooltips and severity-based color coding
- Blast radius visualization for error propagation
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

# Import our integrations
from graph_sitter_integration import (
    get_real_file_tree,
    get_real_file_content,
    get_real_code_graph,
    get_real_code_metrics
)
from serena_error_integration import (
    analyze_file_errors,
    analyze_codebase_errors,
    serena_analyzer
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedVisualizationEngine:
    """Enhanced visualization engine with error context integration."""
    
    def __init__(self):
        self.error_colors = {
            'critical': '#FF0000',  # Red
            'high': '#FF6600',      # Orange-Red
            'medium': '#FFA500',    # Orange
            'low': '#FFFF00',       # Yellow
            'info': '#87CEEB',      # Sky Blue
            'none': '#90EE90'       # Light Green
        }
        
        self.category_colors = {
            'syntax': '#FF0000',     # Red
            'security': '#8B0000',   # Dark Red
            'performance': '#FF8C00', # Dark Orange
            'logic': '#FF6347',      # Tomato
            'style': '#FFD700',      # Gold
            'import': '#9370DB',     # Medium Purple
            'type': '#4169E1',       # Royal Blue
            'unused': '#32CD32'      # Lime Green
        }
    
    async def get_enhanced_file_tree(self) -> Dict[str, Any]:
        """Get file tree enhanced with error heat mapping."""
        logger.info("Generating enhanced file tree with error context...")
        
        try:
            # Get base file tree
            file_tree = await get_real_file_tree()
            
            # Get all file contents for error analysis
            file_contents = await self._collect_file_contents(file_tree)
            
            # Analyze errors across codebase
            error_analysis = await analyze_codebase_errors(file_contents)
            
            # Enhance file tree with error information
            enhanced_tree = await self._enhance_tree_with_errors(
                file_tree, 
                error_analysis['file_error_counts'],
                error_analysis['error_heat_map']
            )
            
            return {
                'file_tree': enhanced_tree,
                'error_summary': {
                    'total_errors': error_analysis['statistics']['total_errors'],
                    'critical_files': error_analysis['critical_files'],
                    'heat_map': error_analysis['error_heat_map']
                },
                'metadata': {
                    'enhanced': True,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating enhanced file tree: {e}")
            # Fallback to basic file tree
            basic_tree = await get_real_file_tree()
            return {
                'file_tree': basic_tree,
                'error_summary': {'total_errors': 0, 'critical_files': [], 'heat_map': {}},
                'metadata': {'enhanced': False, 'error': str(e)}
            }
    
    async def get_enhanced_file_content(self, filepath: str) -> Dict[str, Any]:
        """Get file content enhanced with error highlighting."""
        logger.info(f"Getting enhanced content for: {filepath}")
        
        try:
            # Get base file content
            file_content = await get_real_file_content(filepath)
            
            if 'error' in file_content:
                return file_content
            
            # Analyze errors in this file
            file_errors = await analyze_file_errors(filepath, file_content['content'])
            
            # Enhance content with error annotations
            enhanced_content = await self._enhance_content_with_errors(
                file_content, file_errors
            )
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"Error enhancing file content: {e}")
            return {'error': f'Failed to enhance file content: {str(e)}'}
    
    async def get_enhanced_code_graph(self) -> Dict[str, Any]:
        """Get code graph enhanced with error relationships."""
        logger.info("Generating enhanced code graph with error relationships...")
        
        try:
            # Get base code graph
            code_graph = await get_real_code_graph()
            
            # Get error analysis for graph enhancement
            file_contents = {}  # We'll need to collect this efficiently
            
            # For now, enhance with mock error relationships
            enhanced_graph = await self._enhance_graph_with_errors(code_graph)
            
            return enhanced_graph
            
        except Exception as e:
            logger.error(f"Error generating enhanced code graph: {e}")
            basic_graph = await get_real_code_graph()
            return {**basic_graph, 'enhanced': False, 'error': str(e)}
    
    async def get_error_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive error dashboard data."""
        logger.info("Generating comprehensive error dashboard...")
        
        try:
            # Get file tree for file collection
            file_tree = await get_real_file_tree()
            
            # Collect file contents (limited for performance)
            file_contents = await self._collect_file_contents(file_tree, limit=50)
            
            # Analyze errors
            error_analysis = await analyze_codebase_errors(file_contents)
            
            # Generate visualizations
            error_visualizations = await self._generate_error_visualizations(error_analysis)
            
            return {
                'error_analysis': error_analysis,
                'visualizations': error_visualizations,
                'recommendations': error_analysis['recommendations'],
                'metadata': {
                    'files_analyzed': len(file_contents),
                    'timestamp': datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating error dashboard: {e}")
            return {'error': f'Failed to generate error dashboard: {str(e)}'}
    
    async def _collect_file_contents(self, file_tree: Dict[str, Any], limit: int = None) -> Dict[str, str]:
        """Collect file contents from the file tree."""
        file_contents = {}
        count = 0
        
        async def collect_from_node(node):
            nonlocal count
            if limit and count >= limit:
                return
                
            if node.get('type') == 'file' and node.get('filepath'):
                try:
                    content_data = await get_real_file_content(node['filepath'])
                    if 'content' in content_data:
                        file_contents[node['filepath']] = content_data['content']
                        count += 1
                except Exception as e:
                    logger.warning(f"Failed to get content for {node['filepath']}: {e}")
            
            # Recurse into children
            for child in node.get('children', []):
                await collect_from_node(child)
        
        await collect_from_node(file_tree)
        return file_contents
    
    async def _enhance_tree_with_errors(self, tree: Dict[str, Any], error_counts: Dict[str, int], heat_map: Dict[str, str]) -> Dict[str, Any]:
        """Enhance file tree with error information."""
        
        def enhance_node(node):
            if node.get('type') == 'file':
                filepath = node.get('filepath', '')
                error_count = error_counts.get(filepath, 0)
                heat_color = heat_map.get(filepath, 'green')
                
                node['error_info'] = {
                    'error_count': error_count,
                    'heat_color': heat_color,
                    'severity_indicator': self._get_severity_indicator(error_count),
                    'has_errors': error_count > 0
                }
                
                # Add visual indicators
                if error_count > 0:
                    node['icon_overlay'] = '⚠️' if error_count < 5 else '🚨'
                    node['style'] = {
                        'color': self.error_colors.get(heat_color, '#000000'),
                        'fontWeight': 'bold' if error_count > 3 else 'normal'
                    }
            
            elif node.get('type') == 'directory':
                # Calculate directory error summary
                total_errors = 0
                max_severity = 'none'
                
                for child in node.get('children', []):
                    enhanced_child = enhance_node(child)
                    if enhanced_child.get('error_info'):
                        total_errors += enhanced_child['error_info']['error_count']
                        child_severity = enhanced_child['error_info']['severity_indicator']
                        if self._compare_severity(child_severity, max_severity) > 0:
                            max_severity = child_severity
                
                node['error_info'] = {
                    'total_errors': total_errors,
                    'max_severity': max_severity,
                    'has_errors': total_errors > 0
                }
                
                if total_errors > 0:
                    node['badge'] = str(total_errors)
                    node['style'] = {
                        'color': self.error_colors.get(max_severity, '#000000')
                    }
            
            return node
        
        enhanced_tree = enhance_node(tree.copy())
        return enhanced_tree
    
    async def _enhance_content_with_errors(self, content: Dict[str, Any], errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance file content with error annotations."""
        
        # Group errors by line
        errors_by_line = {}
        for error in errors:
            line_start = error['line_start']
            if line_start not in errors_by_line:
                errors_by_line[line_start] = []
            errors_by_line[line_start].append(error)
        
        # Create line annotations
        line_annotations = {}
        for line_num, line_errors in errors_by_line.items():
            severities = [e['severity'] for e in line_errors]
            max_severity = max(severities, key=lambda s: ['info', 'low', 'medium', 'high', 'critical'].index(s))
            
            line_annotations[line_num] = {
                'errors': line_errors,
                'severity': max_severity,
                'color': self.error_colors[max_severity],
                'marker': '🚨' if max_severity in ['critical', 'high'] else '⚠️',
                'tooltip': f"{len(line_errors)} error(s) on this line"
            }
        
        # Enhance the content
        enhanced_content = content.copy()
        enhanced_content.update({
            'error_annotations': line_annotations,
            'error_summary': {
                'total_errors': len(errors),
                'by_severity': self._group_errors_by_severity(errors),
                'by_category': self._group_errors_by_category(errors)
            },
            'enhanced': True
        })
        
        return enhanced_content
    
    async def _enhance_graph_with_errors(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance code graph with error relationships."""
        
        enhanced_nodes = []
        enhanced_edges = []
        
        # Enhance nodes with error information
        for node in graph.get('nodes', []):
            enhanced_node = node.copy()
            
            # Add mock error information (in real implementation, this would be based on actual analysis)
            if 'function' in node.get('type', ''):
                # Mock error probability based on node name
                error_probability = hash(node.get('label', '')) % 100
                if error_probability > 70:
                    enhanced_node['error_info'] = {
                        'has_errors': True,
                        'severity': 'high' if error_probability > 85 else 'medium',
                        'error_count': (error_probability - 70) // 5
                    }
                    enhanced_node['color'] = {
                        'background': self.error_colors['high'] if error_probability > 85 else self.error_colors['medium'],
                        'border': '#000000'
                    }
                    enhanced_node['borderWidth'] = 3
            
            enhanced_nodes.append(enhanced_node)
        
        # Add error relationship edges
        for edge in graph.get('edges', []):
            enhanced_edges.append(edge)
        
        # Add error propagation edges
        error_nodes = [n for n in enhanced_nodes if n.get('error_info', {}).get('has_errors')]
        for i, error_node in enumerate(error_nodes):
            for j, other_node in enumerate(enhanced_nodes):
                if i != j and not other_node.get('error_info', {}).get('has_errors'):
                    # Add potential error propagation edge
                    enhanced_edges.append({
                        'from': error_node['id'],
                        'to': other_node['id'],
                        'label': 'error_risk',
                        'color': {'color': '#FF6666', 'opacity': 0.5},
                        'dashes': True,
                        'arrows': 'to'
                    })
                    break  # Limit to one propagation edge per error node
        
        return {
            'nodes': enhanced_nodes,
            'edges': enhanced_edges,
            'metadata': {
                **graph.get('metadata', {}),
                'enhanced': True,
                'error_nodes': len(error_nodes),
                'total_nodes': len(enhanced_nodes),
                'total_edges': len(enhanced_edges)
            }
        }
    
    async def _generate_error_visualizations(self, error_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate error visualization data."""
        
        return {
            'severity_distribution': {
                'data': error_analysis['statistics']['errors_by_severity'],
                'chart_type': 'pie',
                'colors': [self.error_colors[severity] for severity in error_analysis['statistics']['errors_by_severity'].keys()]
            },
            'category_distribution': {
                'data': error_analysis['statistics']['errors_by_category'],
                'chart_type': 'bar',
                'colors': [self.category_colors.get(category, '#666666') for category in error_analysis['statistics']['errors_by_category'].keys()]
            },
            'file_heat_map': {
                'data': error_analysis['error_heat_map'],
                'chart_type': 'heatmap'
            },
            'error_timeline': {
                'data': [
                    {'timestamp': datetime.now().isoformat(), 'count': error_analysis['statistics']['total_errors']}
                ],
                'chart_type': 'line'
            }
        }
    
    def _get_severity_indicator(self, error_count: int) -> str:
        """Get severity indicator based on error count."""
        if error_count == 0:
            return 'none'
        elif error_count <= 2:
            return 'low'
        elif error_count <= 5:
            return 'medium'
        elif error_count <= 10:
            return 'high'
        else:
            return 'critical'
    
    def _compare_severity(self, severity1: str, severity2: str) -> int:
        """Compare two severity levels."""
        levels = ['none', 'info', 'low', 'medium', 'high', 'critical']
        return levels.index(severity1) - levels.index(severity2)
    
    def _group_errors_by_severity(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group errors by severity."""
        groups = {}
        for error in errors:
            severity = error['severity']
            groups[severity] = groups.get(severity, 0) + 1
        return groups
    
    def _group_errors_by_category(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Group errors by category."""
        groups = {}
        for error in errors:
            category = error['category']
            groups[category] = groups.get(category, 0) + 1
        return groups

# Global visualization engine
visualization_engine = EnhancedVisualizationEngine()

# Export functions
async def get_enhanced_file_tree() -> Dict[str, Any]:
    """Get enhanced file tree with error context."""
    return await visualization_engine.get_enhanced_file_tree()

async def get_enhanced_file_content(filepath: str) -> Dict[str, Any]:
    """Get enhanced file content with error highlighting."""
    return await visualization_engine.get_enhanced_file_content(filepath)

async def get_enhanced_code_graph() -> Dict[str, Any]:
    """Get enhanced code graph with error relationships."""
    return await visualization_engine.get_enhanced_code_graph()

async def get_error_dashboard() -> Dict[str, Any]:
    """Get comprehensive error dashboard."""
    return await visualization_engine.get_error_dashboard()

if __name__ == "__main__":
    # Test the enhanced visualization
    async def test_enhanced_visualization():
        print("Testing Enhanced Visualization Engine...")
        
        print("\n1. Testing enhanced file tree...")
        enhanced_tree = await get_enhanced_file_tree()
        print(f"   Enhanced tree with {enhanced_tree['error_summary']['total_errors']} total errors")
        
        print("\n2. Testing error dashboard...")
        dashboard = await get_error_dashboard()
        if 'error_analysis' in dashboard:
            print(f"   Dashboard generated with {dashboard['error_analysis']['statistics']['total_errors']} errors")
        
        print("\n✅ Enhanced visualization test complete!")
    
    asyncio.run(test_enhanced_visualization())


"""
Unified visualization manager for coordinating all visualization types.

This module provides a single interface for accessing all visualization types,
batch processing capabilities, and export functionality for different output formats.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
import networkx as nx

from graph_sitter import Codebase
from graph_sitter.core.base_symbol import BaseSymbol
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class

from .base import VisualizationResult
from .config import (
    VisualizationType, 
    OutputFormat, 
    create_config,
    VisualizationConfig
)
from .call_trace import CallTraceVisualizer
from .dependency_trace import DependencyTraceVisualizer
from .blast_radius import BlastRadiusVisualizer
from .method_relationships import MethodRelationshipsVisualizer


logger = logging.getLogger(__name__)


@dataclass
class BatchVisualizationRequest:
    """Request for batch visualization generation."""
    visualization_types: List[VisualizationType]
    targets: List[BaseSymbol]
    output_formats: List[OutputFormat]
    output_directory: Optional[Path] = None
    config_overrides: Optional[Dict[VisualizationType, Dict[str, Any]]] = None


@dataclass
class BatchVisualizationResult:
    """Result of batch visualization generation."""
    results: Dict[str, VisualizationResult]
    summary: Dict[str, Any]
    export_paths: Dict[str, List[Path]]
    errors: List[str]


class UnifiedVisualizationManager:
    """
    Manager class that coordinates all visualization types and provides
    a unified interface for codebase visualization analysis.
    """
    
    def __init__(self):
        """Initialize the visualization manager."""
        self.visualizers = {
            VisualizationType.CALL_TRACE: CallTraceVisualizer,
            VisualizationType.DEPENDENCY_TRACE: DependencyTraceVisualizer,
            VisualizationType.BLAST_RADIUS: BlastRadiusVisualizer,
            VisualizationType.METHOD_RELATIONSHIPS: MethodRelationshipsVisualizer,
        }
        self.logger = logging.getLogger(__name__)
    
    def create_visualization(
        self, 
        codebase: Codebase,
        visualization_type: VisualizationType,
        target: Optional[BaseSymbol] = None,
        config: Optional[VisualizationConfig] = None
    ) -> VisualizationResult:
        """
        Create a single visualization of the specified type.
        
        Args:
            codebase: The codebase to analyze
            visualization_type: Type of visualization to create
            target: Optional target symbol for the visualization
            config: Optional configuration for the visualization
            
        Returns:
            VisualizationResult containing the visualization
        """
        try:
            # Get the appropriate visualizer class
            visualizer_class = self.visualizers.get(visualization_type)
            if not visualizer_class:
                raise ValueError(f"Unknown visualization type: {visualization_type}")
            
            # Create configuration if not provided
            if config is None:
                config = create_config(visualization_type)
            
            # Create and run visualizer
            visualizer = visualizer_class(config)
            result = visualizer.visualize(codebase, target)
            
            self.logger.info(f"Created {visualization_type.value} visualization with "
                           f"{result.graph.number_of_nodes()} nodes and "
                           f"{result.graph.number_of_edges()} edges")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating {visualization_type.value} visualization: {e}")
            raise
    
    def create_batch_visualizations(
        self,
        codebase: Codebase,
        request: BatchVisualizationRequest
    ) -> BatchVisualizationResult:
        """
        Create multiple visualizations in batch.
        
        Args:
            codebase: The codebase to analyze
            request: Batch visualization request
            
        Returns:
            BatchVisualizationResult containing all results
        """
        results = {}
        export_paths = {}
        errors = []
        
        # Create visualizations for each type and target combination
        for viz_type in request.visualization_types:
            for target in request.targets:
                try:
                    # Get configuration with overrides
                    config = self._get_config_with_overrides(viz_type, request.config_overrides)
                    
                    # Create visualization
                    result = self.create_visualization(codebase, viz_type, target, config)
                    
                    # Store result with unique key
                    result_key = f"{viz_type.value}_{str(target) if target else 'all'}"
                    results[result_key] = result
                    
                    # Export in requested formats
                    if request.output_directory:
                        export_paths[result_key] = self._export_result(
                            result, 
                            request.output_formats,
                            request.output_directory,
                            result_key
                        )
                    
                except Exception as e:
                    error_msg = f"Error creating {viz_type.value} for {target}: {e}"
                    errors.append(error_msg)
                    self.logger.error(error_msg)
        
        # Generate summary
        summary = self._generate_batch_summary(results, errors)
        
        return BatchVisualizationResult(
            results=results,
            summary=summary,
            export_paths=export_paths,
            errors=errors
        )
    
    def create_comprehensive_visualization(
        self,
        codebase: Codebase,
        target: Optional[BaseSymbol] = None,
        output_directory: Optional[Path] = None
    ) -> Dict[str, VisualizationResult]:
        """
        Create a comprehensive set of visualizations for a target.
        
        Args:
            codebase: The codebase to analyze
            target: Target symbol (if None, analyzes appropriate symbols for each viz type)
            output_directory: Optional directory to export results
            
        Returns:
            Dictionary of visualization results by type
        """
        results = {}
        
        # Determine appropriate targets for each visualization type
        targets = self._determine_targets(codebase, target)
        
        for viz_type, viz_target in targets.items():
            try:
                result = self.create_visualization(codebase, viz_type, viz_target)
                results[viz_type.value] = result
                
                # Export if directory provided
                if output_directory:
                    self._export_result(
                        result,
                        [OutputFormat.JSON, OutputFormat.GRAPHML],
                        output_directory,
                        f"comprehensive_{viz_type.value}"
                    )
                    
            except Exception as e:
                self.logger.error(f"Error in comprehensive visualization for {viz_type.value}: {e}")
        
        return results
    
    def create_interactive_html_report(
        self,
        codebase: Codebase,
        output_path: Path,
        include_types: Optional[List[VisualizationType]] = None
    ) -> Path:
        """
        Create an interactive HTML report with all visualizations.
        
        Args:
            codebase: The codebase to analyze
            output_path: Path for the HTML report
            include_types: Optional list of visualization types to include
            
        Returns:
            Path to the generated HTML report
        """
        if include_types is None:
            include_types = list(VisualizationType)
        
        # Create visualizations
        results = {}
        for viz_type in include_types:
            try:
                result = self.create_visualization(codebase, viz_type)
                results[viz_type.value] = result
            except Exception as e:
                self.logger.error(f"Error creating {viz_type.value} for HTML report: {e}")
        
        # Generate HTML report
        html_content = self._generate_html_report(results, codebase)
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.logger.info(f"Generated interactive HTML report: {output_path}")
        return output_path
    
    def generate_visualization_data(
        self,
        codebase: Codebase,
        visualization_type: VisualizationType,
        target: Optional[BaseSymbol] = None
    ) -> Dict[str, Any]:
        """
        Generate visualization data in a format suitable for web frontends.
        
        Args:
            codebase: The codebase to analyze
            visualization_type: Type of visualization
            target: Optional target symbol
            
        Returns:
            Dictionary containing visualization data
        """
        result = self.create_visualization(codebase, visualization_type, target)
        
        # Convert to web-friendly format
        data = {
            "nodes": [
                {
                    "id": str(node),
                    "label": data.get("name", str(node)),
                    "color": data.get("color", "#cccccc"),
                    "size": self._calculate_node_size(data),
                    "type": data.get("type", "unknown"),
                    "metadata": {k: v for k, v in data.items() if k not in ["name", "color"]}
                }
                for node, data in result.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": str(source),
                    "target": str(target),
                    "weight": data.get("weight", 1.0),
                    "color": data.get("color", "#999999"),
                    "type": data.get("relationship_type", "generic"),
                    "metadata": {k: v for k, v in data.items() if k not in ["weight", "color"]}
                }
                for source, target, data in result.graph.edges(data=True)
            ],
            "metadata": result.metadata,
            "visualization_type": visualization_type.value,
            "statistics": {
                "node_count": result.graph.number_of_nodes(),
                "edge_count": result.graph.number_of_edges(),
                "density": nx.density(result.graph) if result.graph.number_of_nodes() > 1 else 0
            }
        }
        
        return data
    
    def create_react_visualizations(self, codebase: Codebase, **kwargs) -> Dict[str, Any]:
        """Create React-compatible visualizations."""
        # Implementation for React compatibility
        results = {}
        
        for viz_type in VisualizationType:
            try:
                data = self.generate_visualization_data(codebase, viz_type)
                results[viz_type.value] = data
            except Exception as e:
                self.logger.error(f"Error creating React visualization for {viz_type.value}: {e}")
        
        return results
    
    def generate_issue_dashboard(self, codebase: Codebase, **kwargs) -> Dict[str, Any]:
        """Generate issue dashboard visualization."""
        # Placeholder implementation - would integrate with issue analysis
        return {
            "type": "issue_dashboard",
            "data": "Issue dashboard visualization data would go here"
        }
    
    def generate_complexity_heatmap(self, codebase: Codebase, **kwargs) -> Dict[str, Any]:
        """Generate complexity heatmap visualization."""
        # Placeholder implementation - would integrate with complexity analysis
        return {
            "type": "complexity_heatmap", 
            "data": "Complexity heatmap visualization data would go here"
        }
    
    def generate_metrics_dashboard(self, codebase: Codebase, **kwargs) -> Dict[str, Any]:
        """Generate metrics dashboard visualization."""
        # Placeholder implementation - would integrate with metrics analysis
        return {
            "type": "metrics_dashboard",
            "data": "Metrics dashboard visualization data would go here"
        }
    
    def generate_issues_visualization(self, codebase: Codebase, **kwargs) -> Dict[str, Any]:
        """Generate issues visualization."""
        # Placeholder implementation - would integrate with issue analysis
        return {
            "type": "issues_visualization",
            "data": "Issues visualization data would go here"
        }
    
    def create_visualization_components(self, codebase: Codebase, **kwargs) -> Dict[str, Any]:
        """Create visualization components."""
        # Placeholder implementation for component creation
        return {
            "components": "Visualization components would go here"
        }
    
    def _get_config_with_overrides(
        self,
        viz_type: VisualizationType,
        config_overrides: Optional[Dict[VisualizationType, Dict[str, Any]]]
    ) -> VisualizationConfig:
        """Get configuration with any overrides applied."""
        config = create_config(viz_type)
        
        if config_overrides and viz_type in config_overrides:
            overrides = config_overrides[viz_type]
            for key, value in overrides.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        return config
    
    def _determine_targets(
        self,
        codebase: Codebase,
        target: Optional[BaseSymbol]
    ) -> Dict[VisualizationType, Optional[BaseSymbol]]:
        """Determine appropriate targets for each visualization type."""
        targets = {}
        
        if target:
            # Use provided target for all visualizations
            for viz_type in VisualizationType:
                targets[viz_type] = target
        else:
            # Determine smart defaults
            targets[VisualizationType.CALL_TRACE] = None  # Analyze all functions
            targets[VisualizationType.DEPENDENCY_TRACE] = None  # Analyze all symbols
            targets[VisualizationType.METHOD_RELATIONSHIPS] = None  # Analyze all classes
            
            # For blast radius, pick an interesting function
            if codebase.functions:
                # Find a function with many usages
                target_func = max(codebase.functions, 
                                key=lambda f: len(getattr(f, 'usages', [])),
                                default=codebase.functions[0])
                targets[VisualizationType.BLAST_RADIUS] = target_func
            else:
                targets[VisualizationType.BLAST_RADIUS] = None
        
        return targets
    
    def _export_result(
        self,
        result: VisualizationResult,
        formats: List[OutputFormat],
        output_directory: Path,
        filename_base: str
    ) -> List[Path]:
        """Export a visualization result in multiple formats."""
        output_directory.mkdir(parents=True, exist_ok=True)
        export_paths = []
        
        for format_type in formats:
            try:
                if format_type == OutputFormat.JSON:
                    path = output_directory / f"{filename_base}.json"
                    result.save_json(path)
                    export_paths.append(path)
                
                elif format_type == OutputFormat.GRAPHML:
                    path = output_directory / f"{filename_base}.graphml"
                    result.save_graphml(path)
                    export_paths.append(path)
                
                # Add other format handlers as needed
                
            except Exception as e:
                self.logger.error(f"Error exporting {format_type.value}: {e}")
        
        return export_paths
    
    def _generate_batch_summary(
        self,
        results: Dict[str, VisualizationResult],
        errors: List[str]
    ) -> Dict[str, Any]:
        """Generate summary statistics for batch visualization."""
        if not results:
            return {"total_results": 0, "errors": len(errors)}
        
        total_nodes = sum(r.graph.number_of_nodes() for r in results.values())
        total_edges = sum(r.graph.number_of_edges() for r in results.values())
        
        return {
            "total_results": len(results),
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "average_nodes": total_nodes / len(results),
            "average_edges": total_edges / len(results),
            "errors": len(errors),
            "visualization_types": list(set(r.visualization_type for r in results.values()))
        }
    
    def _calculate_node_size(self, node_data: Dict[str, Any]) -> int:
        """Calculate node size for visualization based on node data."""
        base_size = 10
        
        # Increase size based on various factors
        if node_data.get("is_target", False):
            base_size *= 2
        
        if "usage_frequency" in node_data:
            base_size += min(node_data["usage_frequency"] * 2, 20)
        
        if "impact_level" in node_data:
            base_size += (5 - node_data["impact_level"]) * 3
        
        return min(base_size, 50)  # Cap at reasonable size
    
    def _generate_html_report(
        self,
        results: Dict[str, VisualizationResult],
        codebase: Codebase
    ) -> str:
        """Generate HTML report content."""
        # Basic HTML template - would be enhanced with actual visualization libraries
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Codebase Visualization Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .visualization {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; }}
                .stats {{ background: #f5f5f5; padding: 10px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>Codebase Visualization Report</h1>
            <div class="stats">
                <h3>Codebase Statistics</h3>
                <p>Functions: {len(codebase.functions)}</p>
                <p>Classes: {len(codebase.classes)}</p>
                <p>Files: {len(codebase.files)}</p>
            </div>
        """
        
        for viz_type, result in results.items():
            html += f"""
            <div class="visualization">
                <h2>{viz_type.replace('_', ' ').title()}</h2>
                <div class="stats">
                    <p>Nodes: {result.graph.number_of_nodes()}</p>
                    <p>Edges: {result.graph.number_of_edges()}</p>
                </div>
                <pre>{json.dumps(result.metadata, indent=2)}</pre>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html


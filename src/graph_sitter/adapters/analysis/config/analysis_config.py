"""
Analysis Configuration

Main configuration class that orchestrates all analysis settings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

from .graph_sitter_config import GraphSitterConfig
from .performance_config import PerformanceConfig


@dataclass
class AnalysisConfig:
    """
    Comprehensive configuration for codebase analysis.
    
    Combines graph-sitter settings, performance options, and analysis features.
    """
    
    # Core Configuration
    graph_sitter: GraphSitterConfig = field(default_factory=GraphSitterConfig)
    """Graph-sitter specific configuration"""
    
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    """Performance optimization configuration"""
    
    # Analysis Features
    enable_tree_sitter: bool = True
    """Enable tree-sitter integration and syntax analysis"""
    
    enable_ai_analysis: bool = True
    """Enable AI-powered code analysis and suggestions"""
    
    enable_visualization: bool = True
    """Enable visualization generation"""
    
    enable_metrics_collection: bool = True
    """Enable comprehensive metrics collection"""
    
    enable_dependency_analysis: bool = True
    """Enable dependency tracking and analysis"""
    
    enable_dead_code_detection: bool = True
    """Enable dead code detection"""
    
    enable_import_analysis: bool = True
    """Enable import relationship analysis"""
    
    enable_test_analysis: bool = True
    """Enable test-specific analysis"""
    
    # Output Configuration
    output_formats: Set[str] = field(default_factory=lambda: {'json', 'html'})
    """Enabled output formats: json, html, text, csv"""
    
    export_visualizations: bool = True
    """Export interactive visualizations"""
    
    generate_reports: bool = True
    """Generate comprehensive analysis reports"""
    
    # File Filtering
    include_patterns: List[str] = field(default_factory=lambda: ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx'])
    """File patterns to include in analysis"""
    
    exclude_patterns: List[str] = field(default_factory=lambda: ['node_modules/*', '.git/*', '__pycache__/*', '*.pyc'])
    """File patterns to exclude from analysis"""
    
    exclude_directories: Set[str] = field(default_factory=lambda: {'.git', 'node_modules', '__pycache__', '.pytest_cache'})
    """Directories to exclude from analysis"""
    
    max_file_size_kb: int = 1024
    """Maximum file size to analyze in KB"""
    
    # Language-Specific Settings
    python_settings: Dict[str, Any] = field(default_factory=dict)
    """Python-specific analysis settings"""
    
    javascript_settings: Dict[str, Any] = field(default_factory=dict)
    """JavaScript/TypeScript-specific analysis settings"""
    
    # AI Configuration
    ai_max_requests: int = 150
    """Maximum AI requests per analysis session"""
    
    ai_context_window: int = 8000
    """Maximum context window for AI requests"""
    
    ai_temperature: float = 0.1
    """Temperature setting for AI requests"""
    
    # Visualization Settings
    visualization_theme: str = 'default'
    """Theme for visualizations: default, dark, light"""
    
    max_graph_nodes: int = 1000
    """Maximum nodes to display in graph visualizations"""
    
    enable_interactive_graphs: bool = True
    """Enable interactive graph features"""
    
    # Reporting Configuration
    report_title: Optional[str] = None
    """Custom title for analysis reports"""
    
    include_source_code: bool = False
    """Include source code snippets in reports"""
    
    detailed_metrics: bool = True
    """Include detailed metrics in reports"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format."""
        result = {}
        for field_name, field_obj in self.__dataclass_fields__.items():
            value = getattr(self, field_name)
            if hasattr(value, 'to_dict'):
                result[field_name] = value.to_dict()
            elif isinstance(value, (set, list)):
                result[field_name] = list(value) if isinstance(value, set) else value
            elif isinstance(value, Path):
                result[field_name] = str(value)
            else:
                result[field_name] = value
        return result
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AnalysisConfig':
        """Create configuration from dictionary."""
        # Handle nested configurations
        if 'graph_sitter' in config_dict:
            config_dict['graph_sitter'] = GraphSitterConfig.from_dict(config_dict['graph_sitter'])
        if 'performance' in config_dict:
            config_dict['performance'] = PerformanceConfig(**config_dict['performance'])
        
        # Convert sets back from lists
        if 'output_formats' in config_dict:
            config_dict['output_formats'] = set(config_dict['output_formats'])
        if 'exclude_directories' in config_dict:
            config_dict['exclude_directories'] = set(config_dict['exclude_directories'])
        
        return cls(**{
            k: v for k, v in config_dict.items()
            if k in cls.__dataclass_fields__
        })
    
    @classmethod
    def get_comprehensive_config(cls) -> 'AnalysisConfig':
        """Get a comprehensive analysis configuration with all features enabled."""
        config = cls()
        config.graph_sitter = config.graph_sitter.get_performance_config()
        config.performance = config.performance.get_optimized_config()
        config.enable_tree_sitter = True
        config.enable_ai_analysis = True
        config.enable_visualization = True
        config.enable_metrics_collection = True
        config.enable_dependency_analysis = True
        config.enable_dead_code_detection = True
        config.enable_import_analysis = True
        config.enable_test_analysis = True
        config.output_formats = {'json', 'html', 'text'}
        config.detailed_metrics = True
        config.include_source_code = True
        return config
    
    @classmethod
    def get_basic_config(cls) -> 'AnalysisConfig':
        """Get a basic analysis configuration for quick analysis."""
        config = cls()
        config.graph_sitter = config.graph_sitter.get_minimal_config()
        config.performance = config.performance.get_conservative_config()
        config.enable_ai_analysis = False
        config.enable_visualization = False
        config.output_formats = {'json'}
        config.detailed_metrics = False
        config.include_source_code = False
        return config
    
    @classmethod
    def get_debug_config(cls) -> 'AnalysisConfig':
        """Get a debug configuration for troubleshooting."""
        config = cls()
        config.graph_sitter = config.graph_sitter.get_debug_config()
        config.performance.enable_memory_monitoring = True
        config.performance.enable_progress_reporting = True
        config.include_source_code = True
        config.detailed_metrics = True
        return config


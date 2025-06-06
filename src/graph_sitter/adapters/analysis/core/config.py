"""
Analysis Configuration Module

Provides configuration management for analysis features, integrating with
graph-sitter's advanced settings and CodebaseConfig options.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

try:
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from graph_sitter.configs.models.secrets import SecretsConfig
    GRAPH_SITTER_AVAILABLE = True
except ImportError:
    GRAPH_SITTER_AVAILABLE = False
    CodebaseConfig = None
    SecretsConfig = None


@dataclass
class AnalysisConfig:
    """Configuration for codebase analysis features."""
    
    # Core analysis settings
    debug: bool = False
    verbose: bool = False
    include_tests: bool = True
    include_docs: bool = True
    
    # Graph-sitter advanced settings (from graph-sitter.com/introduction/advanced-settings)
    verify_graph: bool = False
    track_graph: bool = False
    method_usages: bool = True
    sync_enabled: bool = False
    full_range_index: bool = False
    ignore_process_errors: bool = True
    disable_graph: bool = False
    disable_file_parse: bool = False
    exp_lazy_graph: bool = False
    generics: bool = True
    py_resolve_syspath: bool = False
    allow_external: bool = False
    ts_dependency_manager: bool = False
    ts_language_engine: bool = False
    v8_ts_engine: bool = False
    unpacking_assignment_partial_removal: bool = False
    
    # Analysis feature toggles
    enable_metrics: bool = True
    enable_visualization: bool = True
    enable_pattern_detection: bool = True
    enable_dead_code_detection: bool = True
    enable_import_loop_detection: bool = True
    enable_ai_insights: bool = False  # Requires API keys
    
    # Output settings
    output_format: str = "json"  # json, html, text
    export_html: bool = False
    html_template: Optional[str] = None
    
    # File filtering
    file_extensions: List[str] = field(default_factory=lambda: ['.py', '.ts', '.js', '.jsx', '.tsx'])
    exclude_patterns: List[str] = field(default_factory=lambda: ['__pycache__', '.git', 'node_modules', '.venv'])
    
    # Import resolution paths (from advanced settings)
    import_resolution_paths: List[str] = field(default_factory=list)
    import_resolution_overrides: Dict[str, str] = field(default_factory=dict)
    
    # API keys for AI features
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    def to_codebase_config(self) -> Optional[CodebaseConfig]:
        """Convert to graph-sitter CodebaseConfig if available."""
        if not GRAPH_SITTER_AVAILABLE:
            return None
            
        return CodebaseConfig(
            debug=self.debug,
            verify_graph=self.verify_graph,
            track_graph=self.track_graph,
            method_usages=self.method_usages,
            sync_enabled=self.sync_enabled,
            full_range_index=self.full_range_index,
            ignore_process_errors=self.ignore_process_errors,
            disable_graph=self.disable_graph,
            disable_file_parse=self.disable_file_parse,
            exp_lazy_graph=self.exp_lazy_graph,
            generics=self.generics,
            import_resolution_paths=self.import_resolution_paths,
            import_resolution_overrides=self.import_resolution_overrides,
            py_resolve_syspath=self.py_resolve_syspath,
            allow_external=self.allow_external,
            ts_dependency_manager=self.ts_dependency_manager,
            ts_language_engine=self.ts_language_engine,
            v8_ts_engine=self.v8_ts_engine,
            unpacking_assignment_partial_removal=self.unpacking_assignment_partial_removal
        )
    
    def to_secrets_config(self) -> Optional[SecretsConfig]:
        """Convert to graph-sitter SecretsConfig if available."""
        if not GRAPH_SITTER_AVAILABLE:
            return None
            
        secrets = {}
        if self.openai_api_key:
            secrets['openai_api_key'] = self.openai_api_key
        if self.anthropic_api_key:
            secrets['anthropic_api_key'] = self.anthropic_api_key
            
        return SecretsConfig(**secrets) if secrets else None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'AnalysisConfig':
        """Create config from dictionary."""
        return cls(**config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'debug': self.debug,
            'verbose': self.verbose,
            'include_tests': self.include_tests,
            'include_docs': self.include_docs,
            'verify_graph': self.verify_graph,
            'track_graph': self.track_graph,
            'method_usages': self.method_usages,
            'sync_enabled': self.sync_enabled,
            'full_range_index': self.full_range_index,
            'ignore_process_errors': self.ignore_process_errors,
            'disable_graph': self.disable_graph,
            'disable_file_parse': self.disable_file_parse,
            'exp_lazy_graph': self.exp_lazy_graph,
            'generics': self.generics,
            'py_resolve_syspath': self.py_resolve_syspath,
            'allow_external': self.allow_external,
            'ts_dependency_manager': self.ts_dependency_manager,
            'ts_language_engine': self.ts_language_engine,
            'v8_ts_engine': self.v8_ts_engine,
            'unpacking_assignment_partial_removal': self.unpacking_assignment_partial_removal,
            'enable_metrics': self.enable_metrics,
            'enable_visualization': self.enable_visualization,
            'enable_pattern_detection': self.enable_pattern_detection,
            'enable_dead_code_detection': self.enable_dead_code_detection,
            'enable_import_loop_detection': self.enable_import_loop_detection,
            'enable_ai_insights': self.enable_ai_insights,
            'output_format': self.output_format,
            'export_html': self.export_html,
            'html_template': self.html_template,
            'file_extensions': self.file_extensions,
            'exclude_patterns': self.exclude_patterns,
            'import_resolution_paths': self.import_resolution_paths,
            'import_resolution_overrides': self.import_resolution_overrides,
            'openai_api_key': self.openai_api_key,
            'anthropic_api_key': self.anthropic_api_key
        }


@dataclass
class AnalysisResult:
    """Container for analysis results."""
    
    # Basic info
    codebase_path: str
    language: str
    total_files: int
    total_lines: int
    
    # Metrics
    quality_metrics: Optional[Dict[str, Any]] = None
    complexity_metrics: Optional[Dict[str, Any]] = None
    
    # Detection results
    import_loops: List[Dict[str, Any]] = field(default_factory=list)
    dead_code: List[Dict[str, Any]] = field(default_factory=list)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # AI insights
    ai_insights: Optional[Dict[str, Any]] = None
    training_data: List[Dict[str, Any]] = field(default_factory=list)
    
    # Visualization data
    tree_structure: Optional[Dict[str, Any]] = None
    dependency_graph: Optional[Dict[str, Any]] = None
    
    # Execution metadata
    analysis_time: float = 0.0
    config_used: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            'codebase_path': self.codebase_path,
            'language': self.language,
            'total_files': self.total_files,
            'total_lines': self.total_lines,
            'quality_metrics': self.quality_metrics,
            'complexity_metrics': self.complexity_metrics,
            'import_loops': self.import_loops,
            'dead_code': self.dead_code,
            'patterns': self.patterns,
            'ai_insights': self.ai_insights,
            'training_data': self.training_data,
            'tree_structure': self.tree_structure,
            'dependency_graph': self.dependency_graph,
            'analysis_time': self.analysis_time,
            'config_used': self.config_used,
            'errors': self.errors,
            'warnings': self.warnings
        }


"""
⚙️ Advanced Configuration System

Comprehensive configuration system based on graph-sitter.com advanced settings:
- Debug and performance tuning options
- Import resolution and path configuration
- Engine-specific settings (TypeScript, Python, etc.)
- Analysis behavior customization
- Export and visualization preferences
- Integration with CodebaseConfig from graph-sitter

Provides fine-grained control over all analysis aspects and performance optimization.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
from enum import Enum


class AnalysisLevel(Enum):
    """Analysis depth levels"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    DEEP = "deep"


class ExportFormat(Enum):
    """Supported export formats"""
    JSON = "json"
    HTML = "html"
    DOT = "dot"
    SVG = "svg"
    PDF = "pdf"
    CSV = "csv"


class VisualizationTheme(Enum):
    """Visualization themes"""
    LIGHT = "light"
    DARK = "dark"
    HIGH_CONTRAST = "high_contrast"
    COLORBLIND_FRIENDLY = "colorblind_friendly"


@dataclass
class DebugConfig:
    """Debug configuration options"""
    enabled: bool = False
    verbose_logging: bool = False
    log_graph_operations: bool = False
    log_file_parsing: bool = False
    enable_assertions: bool = False
    collect_debug_metrics: bool = False
    debug_output_dir: str = "./debug_output"
    max_log_size_mb: int = 100
    
    # Graph debugging
    verify_graph: bool = False
    track_graph_changes: bool = False
    dump_graph_on_error: bool = False


@dataclass
class PerformanceConfig:
    """Performance optimization settings"""
    # Memory management
    max_memory_usage_mb: int = 2048
    enable_memory_monitoring: bool = True
    garbage_collect_frequency: int = 100
    
    # Processing limits
    max_file_size_mb: int = 10
    max_files_per_batch: int = 1000
    max_analysis_depth: int = 10
    max_nodes_in_graph: int = 100000
    
    # Caching
    enable_analysis_cache: bool = True
    cache_expiry_hours: int = 24
    max_cache_size_mb: int = 500
    
    # Parallel processing
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4
    chunk_size: int = 100
    
    # Timeouts
    analysis_timeout_seconds: int = 300
    ai_request_timeout_seconds: int = 60
    file_parse_timeout_seconds: int = 30


@dataclass
class ImportResolutionConfig:
    """Import resolution configuration"""
    # Path resolution
    resolution_paths: List[str] = field(default_factory=list)
    resolution_overrides: Dict[str, str] = field(default_factory=dict)
    
    # Python-specific
    resolve_sys_path: bool = False
    python_path_extensions: List[str] = field(default_factory=list)
    
    # TypeScript-specific
    enable_ts_dependency_manager: bool = False
    enable_ts_language_engine: bool = False
    enable_v8_ts_engine: bool = False
    ts_config_path: str = ""
    
    # General settings
    allow_external_imports: bool = False
    ignore_missing_imports: bool = True
    max_import_depth: int = 10


@dataclass
class LanguageEngineConfig:
    """Language-specific engine configuration"""
    # Python settings
    python_version: str = "3.8"
    enable_python_type_checking: bool = False
    python_interpreter_path: str = ""
    
    # TypeScript settings
    typescript_version: str = "latest"
    enable_typescript_compiler: bool = False
    typescript_config_path: str = ""
    
    # JavaScript settings
    javascript_engine: str = "node"
    enable_babel_parsing: bool = False
    
    # Generic settings
    enable_syntax_highlighting: bool = True
    enable_semantic_analysis: bool = True
    custom_parsers: Dict[str, str] = field(default_factory=dict)


@dataclass
class AnalysisConfig:
    """Core analysis configuration"""
    # Analysis scope
    analysis_level: AnalysisLevel = AnalysisLevel.STANDARD
    include_tests: bool = True
    include_documentation: bool = True
    include_config_files: bool = False
    
    # Feature toggles
    enable_metrics_calculation: bool = True
    enable_dependency_analysis: bool = True
    enable_dead_code_detection: bool = True
    enable_complexity_analysis: bool = True
    enable_security_analysis: bool = False
    enable_performance_analysis: bool = False
    
    # AI integration
    enable_ai_analysis: bool = False
    ai_provider: str = "openai"
    ai_model: str = "gpt-4"
    max_ai_requests: int = 150
    ai_analysis_types: List[str] = field(default_factory=lambda: ["quality", "security"])
    
    # Tree-sitter settings
    enable_tree_sitter: bool = True
    tree_sitter_languages: List[str] = field(default_factory=lambda: ["python", "typescript", "javascript"])
    enable_query_patterns: bool = True
    custom_query_patterns: Dict[str, str] = field(default_factory=dict)
    
    # Method and symbol resolution
    enable_method_usages: bool = True
    enable_generics_resolution: bool = True
    enable_symbol_tracking: bool = True
    
    # Graph construction
    disable_graph_construction: bool = False
    enable_lazy_graph_loading: bool = False
    full_range_indexing: bool = False
    
    # Error handling
    ignore_process_errors: bool = True
    continue_on_parse_errors: bool = True
    max_error_count: int = 100


@dataclass
class VisualizationConfig:
    """Visualization and reporting configuration"""
    # Theme and appearance
    theme: VisualizationTheme = VisualizationTheme.LIGHT
    color_scheme: str = "default"
    font_family: str = "Arial, sans-serif"
    font_size: int = 12
    
    # Chart settings
    chart_width: int = 800
    chart_height: int = 600
    enable_interactive_charts: bool = True
    enable_animations: bool = True
    
    # Content settings
    include_source_code: bool = False
    max_source_lines_displayed: int = 50
    include_metrics_details: bool = True
    include_dependency_graphs: bool = True
    
    # Export settings
    default_export_format: ExportFormat = ExportFormat.HTML
    export_directory: str = "./analysis_reports"
    auto_open_reports: bool = True
    
    # Network graph settings
    max_nodes_in_graph: int = 1000
    node_size_range: Tuple[int, int] = (5, 20)
    edge_thickness_range: Tuple[int, int] = (1, 5)
    enable_node_clustering: bool = True


@dataclass
class ExportConfig:
    """Export and output configuration"""
    # Output paths
    output_directory: str = "./analysis_output"
    report_filename_template: str = "analysis_report_{timestamp}"
    create_timestamped_directories: bool = True
    
    # Format-specific settings
    json_indent: int = 2
    json_sort_keys: bool = True
    html_include_css: bool = True
    html_include_javascript: bool = True
    csv_delimiter: str = ","
    
    # Compression
    enable_compression: bool = False
    compression_format: str = "zip"
    
    # File management
    max_output_files: int = 100
    auto_cleanup_old_files: bool = True
    file_retention_days: int = 30


@dataclass
class IntegrationConfig:
    """Integration with external tools and services"""
    # Version control
    git_integration: bool = True
    track_file_changes: bool = True
    include_git_blame: bool = False
    
    # CI/CD integration
    enable_ci_mode: bool = False
    fail_on_quality_threshold: bool = False
    quality_threshold: float = 7.0
    
    # External tools
    enable_linter_integration: bool = False
    linter_commands: Dict[str, str] = field(default_factory=dict)
    
    # Notifications
    enable_notifications: bool = False
    notification_webhooks: List[str] = field(default_factory=list)
    
    # Database integration
    enable_database_storage: bool = False
    database_connection_string: str = ""


@dataclass
class AdvancedSettings:
    """Advanced configuration settings from graph-sitter.com"""
    # Core graph-sitter settings
    debug: bool = False
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
    
    # Import resolution
    import_resolution_paths: List[str] = field(default_factory=list)
    import_resolution_overrides: Dict[str, str] = field(default_factory=dict)
    py_resolve_syspath: bool = False
    allow_external: bool = False
    
    # TypeScript settings
    ts_dependency_manager: bool = False
    ts_language_engine: bool = False
    v8_ts_engine: bool = False
    
    # Experimental features
    unpacking_assignment_partial_removal: bool = False
    enable_experimental_features: bool = False
    experimental_feature_flags: Dict[str, bool] = field(default_factory=dict)


@dataclass
class ComprehensiveAnalysisConfig:
    """Complete configuration for the analysis system"""
    # Core configurations
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    import_resolution: ImportResolutionConfig = field(default_factory=ImportResolutionConfig)
    language_engines: LanguageEngineConfig = field(default_factory=LanguageEngineConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    integration: IntegrationConfig = field(default_factory=IntegrationConfig)
    advanced: AdvancedSettings = field(default_factory=AdvancedSettings)
    
    # Metadata
    config_version: str = "1.0.0"
    created_at: str = ""
    last_modified: str = ""
    description: str = ""


class ConfigurationManager:
    """
    Manager for loading, saving, and validating configurations
    """
    
    def __init__(self):
        self.config_cache = {}
        self.default_config_paths = [
            "./analysis_config.json",
            "~/.graph_sitter/analysis_config.json",
            "/etc/graph_sitter/analysis_config.json"
        ]
    
    def create_default_config(self) -> ComprehensiveAnalysisConfig:
        """Create a default configuration"""
        config = ComprehensiveAnalysisConfig()
        config.created_at = self._get_current_timestamp()
        config.description = "Default analysis configuration"
        return config
    
    def load_config(self, config_path: Optional[str] = None) -> ComprehensiveAnalysisConfig:
        """Load configuration from file or create default"""
        if config_path:
            paths_to_try = [config_path]
        else:
            paths_to_try = self.default_config_paths
        
        for path in paths_to_try:
            expanded_path = os.path.expanduser(path)
            if os.path.exists(expanded_path):
                try:
                    return self._load_config_from_file(expanded_path)
                except Exception as e:
                    print(f"Error loading config from {expanded_path}: {e}")
                    continue
        
        # Return default config if no file found
        print("No configuration file found, using defaults")
        return self.create_default_config()
    
    def save_config(self, config: ComprehensiveAnalysisConfig, config_path: str) -> bool:
        """Save configuration to file"""
        try:
            config.last_modified = self._get_current_timestamp()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Convert to dictionary and save
            config_dict = asdict(config)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            return True
            
        except Exception as e:
            print(f"Error saving config to {config_path}: {e}")
            return False
    
    def validate_config(self, config: ComprehensiveAnalysisConfig) -> Tuple[bool, List[str]]:
        """Validate configuration and return issues"""
        issues = []
        
        # Validate performance settings
        if config.performance.max_memory_usage_mb < 256:
            issues.append("Memory limit too low (minimum 256MB)")
        
        if config.performance.max_worker_threads < 1:
            issues.append("Worker thread count must be at least 1")
        
        # Validate paths
        if config.export.output_directory:
            try:
                os.makedirs(config.export.output_directory, exist_ok=True)
            except Exception as e:
                issues.append(f"Cannot create output directory: {e}")
        
        # Validate AI settings
        if config.analysis.enable_ai_analysis:
            if not config.analysis.ai_provider:
                issues.append("AI provider must be specified when AI analysis is enabled")
            
            if config.analysis.max_ai_requests < 1:
                issues.append("AI request limit must be at least 1")
        
        # Validate visualization settings
        if config.visualization.chart_width < 100 or config.visualization.chart_height < 100:
            issues.append("Chart dimensions too small (minimum 100x100)")
        
        # Validate import resolution
        for path in config.import_resolution.resolution_paths:
            if not os.path.exists(os.path.expanduser(path)):
                issues.append(f"Import resolution path does not exist: {path}")
        
        return len(issues) == 0, issues
    
    def merge_configs(self, base_config: ComprehensiveAnalysisConfig, 
                     override_config: Dict[str, Any]) -> ComprehensiveAnalysisConfig:
        """Merge configuration with overrides"""
        # Convert base config to dict
        base_dict = asdict(base_config)
        
        # Deep merge override config
        merged_dict = self._deep_merge(base_dict, override_config)
        
        # Convert back to config object
        return self._dict_to_config(merged_dict)
    
    def get_graph_sitter_config(self, config: ComprehensiveAnalysisConfig) -> Dict[str, Any]:
        """Convert to graph-sitter CodebaseConfig format"""
        return {
            'debug': config.advanced.debug,
            'verify_graph': config.advanced.verify_graph,
            'track_graph': config.advanced.track_graph,
            'method_usages': config.advanced.method_usages,
            'sync_enabled': config.advanced.sync_enabled,
            'full_range_index': config.advanced.full_range_index,
            'ignore_process_errors': config.advanced.ignore_process_errors,
            'disable_graph': config.advanced.disable_graph,
            'disable_file_parse': config.advanced.disable_file_parse,
            'exp_lazy_graph': config.advanced.exp_lazy_graph,
            'generics': config.advanced.generics,
            'import_resolution_paths': config.import_resolution.resolution_paths,
            'import_resolution_overrides': config.import_resolution.resolution_overrides,
            'py_resolve_syspath': config.import_resolution.resolve_sys_path,
            'allow_external': config.import_resolution.allow_external_imports,
            'ts_dependency_manager': config.import_resolution.enable_ts_dependency_manager,
            'ts_language_engine': config.import_resolution.enable_ts_language_engine,
            'v8_ts_engine': config.import_resolution.enable_v8_ts_engine,
            'unpacking_assignment_partial_removal': config.advanced.unpacking_assignment_partial_removal
        }
    
    def _load_config_from_file(self, file_path: str) -> ComprehensiveAnalysisConfig:
        """Load configuration from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        return self._dict_to_config(config_dict)
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> ComprehensiveAnalysisConfig:
        """Convert dictionary to configuration object"""
        # This is a simplified conversion - in practice, you'd want more robust handling
        try:
            # Create default config and update with loaded values
            config = self.create_default_config()
            
            # Update each section if present
            if 'analysis' in config_dict:
                config.analysis = AnalysisConfig(**config_dict['analysis'])
            if 'debug' in config_dict:
                config.debug = DebugConfig(**config_dict['debug'])
            if 'performance' in config_dict:
                config.performance = PerformanceConfig(**config_dict['performance'])
            # ... continue for other sections
            
            return config
            
        except Exception as e:
            print(f"Error converting dict to config: {e}")
            return self.create_default_config()
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string"""
        from datetime import datetime
        return datetime.now().isoformat()


class ConfigurationPresets:
    """
    Predefined configuration presets for common use cases
    """
    
    @staticmethod
    def get_development_preset() -> ComprehensiveAnalysisConfig:
        """Configuration optimized for development environment"""
        config = ComprehensiveAnalysisConfig()
        
        # Enable debugging
        config.debug.enabled = True
        config.debug.verbose_logging = True
        
        # Moderate performance settings
        config.performance.max_memory_usage_mb = 1024
        config.performance.enable_parallel_processing = True
        config.performance.max_worker_threads = 2
        
        # Enable most analysis features
        config.analysis.analysis_level = AnalysisLevel.COMPREHENSIVE
        config.analysis.enable_ai_analysis = False  # Disabled by default
        config.analysis.enable_tree_sitter = True
        
        # Interactive visualizations
        config.visualization.enable_interactive_charts = True
        config.visualization.auto_open_reports = True
        
        config.description = "Development environment preset"
        return config
    
    @staticmethod
    def get_production_preset() -> ComprehensiveAnalysisConfig:
        """Configuration optimized for production environment"""
        config = ComprehensiveAnalysisConfig()
        
        # Minimal debugging
        config.debug.enabled = False
        config.debug.verbose_logging = False
        
        # High performance settings
        config.performance.max_memory_usage_mb = 4096
        config.performance.enable_parallel_processing = True
        config.performance.max_worker_threads = 8
        
        # Focused analysis
        config.analysis.analysis_level = AnalysisLevel.STANDARD
        config.analysis.enable_security_analysis = True
        config.analysis.enable_performance_analysis = True
        
        # CI/CD integration
        config.integration.enable_ci_mode = True
        config.integration.fail_on_quality_threshold = True
        
        config.description = "Production environment preset"
        return config
    
    @staticmethod
    def get_research_preset() -> ComprehensiveAnalysisConfig:
        """Configuration optimized for research and deep analysis"""
        config = ComprehensiveAnalysisConfig()
        
        # Comprehensive debugging
        config.debug.enabled = True
        config.debug.collect_debug_metrics = True
        
        # Maximum analysis depth
        config.analysis.analysis_level = AnalysisLevel.DEEP
        config.analysis.enable_ai_analysis = True
        config.analysis.max_ai_requests = 500
        
        # All features enabled
        config.analysis.enable_security_analysis = True
        config.analysis.enable_performance_analysis = True
        config.analysis.enable_complexity_analysis = True
        
        # Detailed visualizations
        config.visualization.include_source_code = True
        config.visualization.include_metrics_details = True
        
        config.description = "Research and deep analysis preset"
        return config
    
    @staticmethod
    def get_lightweight_preset() -> ComprehensiveAnalysisConfig:
        """Configuration for lightweight, fast analysis"""
        config = ComprehensiveAnalysisConfig()
        
        # Minimal settings
        config.debug.enabled = False
        config.performance.max_memory_usage_mb = 512
        config.performance.max_worker_threads = 1
        
        # Basic analysis only
        config.analysis.analysis_level = AnalysisLevel.BASIC
        config.analysis.enable_ai_analysis = False
        config.analysis.enable_tree_sitter = False
        
        # Simple outputs
        config.visualization.enable_interactive_charts = False
        config.export.default_export_format = ExportFormat.JSON
        
        config.description = "Lightweight analysis preset"
        return config


# Convenience functions for direct use

def create_default_config() -> ComprehensiveAnalysisConfig:
    """Create default configuration"""
    manager = ConfigurationManager()
    return manager.create_default_config()


def load_config_from_file(config_path: str) -> ComprehensiveAnalysisConfig:
    """Load configuration from file"""
    manager = ConfigurationManager()
    return manager.load_config(config_path)


def validate_config(config: ComprehensiveAnalysisConfig) -> Tuple[bool, List[str]]:
    """Validate configuration"""
    manager = ConfigurationManager()
    return manager.validate_config(config)


def get_preset_config(preset_name: str) -> ComprehensiveAnalysisConfig:
    """Get predefined configuration preset"""
    presets = {
        'development': ConfigurationPresets.get_development_preset,
        'production': ConfigurationPresets.get_production_preset,
        'research': ConfigurationPresets.get_research_preset,
        'lightweight': ConfigurationPresets.get_lightweight_preset
    }
    
    if preset_name not in presets:
        raise ValueError(f"Unknown preset: {preset_name}. Available: {list(presets.keys())}")
    
    return presets[preset_name]()


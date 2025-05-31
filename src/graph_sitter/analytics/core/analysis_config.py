"""
Configuration classes for the Analytics Engine

This module provides configuration options for customizing the behavior
of the analytics engine and individual analyzers.
"""

from typing import Set, List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class AnalysisDepth(str, Enum):
    """Analysis depth levels."""
    QUICK = "quick"          # Fast analysis with basic metrics
    STANDARD = "standard"    # Standard analysis with most features
    DEEP = "deep"           # Comprehensive analysis with all features


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    HTML = "html"
    MARKDOWN = "markdown"
    CSV = "csv"
    XML = "xml"


class AnalysisConfig(BaseModel):
    """Configuration for analytics engine execution."""
    
    # Analysis types to enable
    enable_complexity: bool = True
    enable_performance: bool = True
    enable_security: bool = True
    enable_dead_code: bool = True
    enable_dependency: bool = True
    
    # Performance settings
    max_workers: int = Field(default=4, ge=1, le=16)
    timeout_seconds: int = Field(default=300, ge=30, le=3600)
    incremental: bool = False
    cache_results: bool = True
    
    # Analysis depth
    analysis_depth: AnalysisDepth = AnalysisDepth.STANDARD
    deep_analysis: bool = False  # Deprecated, use analysis_depth
    
    # Language and file filtering
    languages: Optional[Set[str]] = None
    include_patterns: List[str] = Field(default_factory=lambda: ["**/*"])
    exclude_patterns: List[str] = Field(default_factory=lambda: [
        "**/node_modules/**",
        "**/venv/**",
        "**/env/**",
        "**/.git/**",
        "**/build/**",
        "**/dist/**",
        "**/__pycache__/**",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.min.js",
        "**/*.min.css"
    ])
    
    # File size limits
    max_file_size_mb: float = Field(default=10.0, ge=0.1, le=100.0)
    max_total_size_gb: float = Field(default=5.0, ge=0.1, le=50.0)
    
    # Output settings
    generate_reports: bool = True
    export_format: ExportFormat = ExportFormat.JSON
    output_directory: Optional[str] = None
    
    # Analyzer-specific settings
    complexity_settings: Dict[str, Any] = Field(default_factory=dict)
    performance_settings: Dict[str, Any] = Field(default_factory=dict)
    security_settings: Dict[str, Any] = Field(default_factory=dict)
    dead_code_settings: Dict[str, Any] = Field(default_factory=dict)
    dependency_settings: Dict[str, Any] = Field(default_factory=dict)
    
    # Quality thresholds
    quality_thresholds: Dict[str, float] = Field(default_factory=lambda: {
        "complexity_threshold": 10.0,
        "maintainability_threshold": 60.0,
        "security_score_threshold": 80.0,
        "performance_score_threshold": 70.0,
        "overall_quality_threshold": 75.0
    })
    
    # Reporting settings
    include_source_code: bool = False
    include_recommendations: bool = True
    include_metrics_history: bool = False
    
    # Advanced settings
    parallel_file_processing: bool = True
    memory_limit_mb: Optional[int] = None
    temp_directory: Optional[str] = None
    
    @validator('languages')
    def validate_languages(cls, v):
        """Validate supported languages."""
        if v is not None:
            supported_languages = {
                "python", "typescript", "javascript", "java", 
                "cpp", "c", "rust", "go", "php", "ruby", 
                "csharp", "kotlin", "swift", "scala"
            }
            invalid_languages = v - supported_languages
            if invalid_languages:
                raise ValueError(f"Unsupported languages: {invalid_languages}")
        return v
    
    @validator('deep_analysis')
    def validate_deep_analysis(cls, v, values):
        """Handle deprecated deep_analysis field."""
        if v and 'analysis_depth' in values:
            values['analysis_depth'] = AnalysisDepth.DEEP
        return v
    
    def get_analyzer_config(self, analyzer_name: str) -> Dict[str, Any]:
        """Get configuration for a specific analyzer."""
        config_map = {
            'complexity': self.complexity_settings,
            'performance': self.performance_settings,
            'security': self.security_settings,
            'dead_code': self.dead_code_settings,
            'dependency': self.dependency_settings
        }
        
        base_config = {
            'max_workers': self.max_workers,
            'timeout_seconds': self.timeout_seconds,
            'analysis_depth': self.analysis_depth,
            'languages': self.languages,
            'quality_thresholds': self.quality_thresholds
        }
        
        analyzer_config = config_map.get(analyzer_name, {})
        return {**base_config, **analyzer_config}
    
    def is_analyzer_enabled(self, analyzer_name: str) -> bool:
        """Check if an analyzer is enabled."""
        analyzer_flags = {
            'complexity': self.enable_complexity,
            'performance': self.enable_performance,
            'security': self.enable_security,
            'dead_code': self.enable_dead_code,
            'dependency': self.enable_dependency
        }
        return analyzer_flags.get(analyzer_name, False)
    
    def get_file_filters(self) -> Dict[str, List[str]]:
        """Get file filtering patterns."""
        return {
            'include_patterns': self.include_patterns,
            'exclude_patterns': self.exclude_patterns
        }
    
    def should_analyze_file(self, file_path: str, file_size_mb: float) -> bool:
        """Check if a file should be analyzed based on filters."""
        import fnmatch
        
        # Check file size
        if file_size_mb > self.max_file_size_mb:
            return False
        
        # Check include patterns
        if self.include_patterns:
            included = any(fnmatch.fnmatch(file_path, pattern) 
                          for pattern in self.include_patterns)
            if not included:
                return False
        
        # Check exclude patterns
        if self.exclude_patterns:
            excluded = any(fnmatch.fnmatch(file_path, pattern) 
                          for pattern in self.exclude_patterns)
            if excluded:
                return False
        
        return True
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance-related settings."""
        return {
            'max_workers': self.max_workers,
            'timeout_seconds': self.timeout_seconds,
            'parallel_file_processing': self.parallel_file_processing,
            'memory_limit_mb': self.memory_limit_mb,
            'cache_results': self.cache_results,
            'incremental': self.incremental
        }
    
    def get_output_settings(self) -> Dict[str, Any]:
        """Get output and reporting settings."""
        return {
            'generate_reports': self.generate_reports,
            'export_format': self.export_format,
            'output_directory': self.output_directory,
            'include_source_code': self.include_source_code,
            'include_recommendations': self.include_recommendations,
            'include_metrics_history': self.include_metrics_history
        }
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"


class ComplexityAnalysisConfig(BaseModel):
    """Configuration specific to complexity analysis."""
    
    # Complexity thresholds
    cyclomatic_complexity_threshold: int = Field(default=10, ge=1, le=50)
    cognitive_complexity_threshold: int = Field(default=15, ge=1, le=100)
    nesting_depth_threshold: int = Field(default=4, ge=1, le=20)
    
    # Maintainability settings
    maintainability_index_threshold: float = Field(default=60.0, ge=0.0, le=100.0)
    
    # Halstead metrics settings
    calculate_halstead_metrics: bool = True
    halstead_volume_threshold: float = Field(default=1000.0, ge=0.0)
    
    # Analysis scope
    analyze_functions: bool = True
    analyze_classes: bool = True
    analyze_modules: bool = True
    
    # Reporting settings
    include_function_details: bool = True
    include_class_details: bool = True
    max_results_per_category: int = Field(default=100, ge=10, le=1000)


class SecurityAnalysisConfig(BaseModel):
    """Configuration specific to security analysis."""
    
    # Vulnerability detection
    detect_sql_injection: bool = True
    detect_xss: bool = True
    detect_command_injection: bool = True
    detect_path_traversal: bool = True
    detect_hardcoded_secrets: bool = True
    
    # Security best practices
    check_authentication: bool = True
    check_authorization: bool = True
    check_input_validation: bool = True
    check_output_encoding: bool = True
    check_crypto_usage: bool = True
    
    # Dependency security
    check_vulnerable_dependencies: bool = True
    dependency_database_url: Optional[str] = None
    
    # Severity thresholds
    critical_severity_threshold: float = Field(default=9.0, ge=0.0, le=10.0)
    high_severity_threshold: float = Field(default=7.0, ge=0.0, le=10.0)
    medium_severity_threshold: float = Field(default=4.0, ge=0.0, le=10.0)
    
    # Custom rules
    custom_rules_file: Optional[str] = None
    exclude_rules: List[str] = Field(default_factory=list)


class PerformanceAnalysisConfig(BaseModel):
    """Configuration specific to performance analysis."""
    
    # Algorithm complexity detection
    detect_nested_loops: bool = True
    detect_recursive_calls: bool = True
    detect_inefficient_patterns: bool = True
    
    # Performance thresholds
    max_acceptable_complexity: str = "O(n^2)"
    nested_loop_threshold: int = Field(default=3, ge=2, le=10)
    
    # Language-specific optimizations
    check_python_optimizations: bool = True
    check_javascript_optimizations: bool = True
    check_java_optimizations: bool = True
    
    # Resource usage analysis
    analyze_memory_usage: bool = True
    analyze_cpu_usage: bool = True
    analyze_io_operations: bool = True
    
    # Profiling settings
    enable_profiling: bool = False
    profiling_sample_rate: float = Field(default=0.1, ge=0.01, le=1.0)


class DeadCodeAnalysisConfig(BaseModel):
    """Configuration specific to dead code analysis."""
    
    # Detection types
    detect_unused_functions: bool = True
    detect_unused_classes: bool = True
    detect_unused_variables: bool = True
    detect_unused_imports: bool = True
    detect_unreachable_code: bool = True
    
    # Confidence thresholds
    minimum_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # Analysis scope
    analyze_test_files: bool = False
    analyze_generated_files: bool = False
    
    # Exclusions
    exclude_main_functions: bool = True
    exclude_exported_symbols: bool = True
    exclude_public_apis: bool = True
    
    # Custom patterns
    keep_patterns: List[str] = Field(default_factory=list)
    ignore_patterns: List[str] = Field(default_factory=list)


class DependencyAnalysisConfig(BaseModel):
    """Configuration specific to dependency analysis."""
    
    # Analysis types
    detect_circular_dependencies: bool = True
    calculate_coupling_metrics: bool = True
    analyze_dependency_depth: bool = True
    
    # Thresholds
    max_dependency_depth: int = Field(default=10, ge=1, le=50)
    max_coupling_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    
    # Scope
    include_external_dependencies: bool = True
    include_test_dependencies: bool = False
    
    # Graph generation
    generate_dependency_graph: bool = True
    max_graph_nodes: int = Field(default=1000, ge=10, le=10000)
    
    # Architecture validation
    validate_layer_dependencies: bool = False
    layer_rules_file: Optional[str] = None


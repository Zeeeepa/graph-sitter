"""

from enum import Enum
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import json

from pydantic import BaseModel, Field, validator
import yaml

Configuration system for the analytics engine.

This module provides comprehensive configuration management for code analysis,
including analyzer settings, thresholds, and performance tuning options.
"""

class AnalysisLanguage(str, Enum):
    """Supported programming languages for analysis."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    RUST = "rust"
    GO = "go"
    CSHARP = "csharp"
    PHP = "php"
    RUBY = "ruby"

class AnalyzerType(str, Enum):
    """Types of code analyzers available."""
    COMPLEXITY = "complexity"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DEAD_CODE = "dead_code"
    DEPENDENCIES = "dependencies"
    STYLE = "style"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    CUSTOM = "custom"

class ExportFormat(str, Enum):
    """Supported export formats for analysis results."""
    JSON = "json"
    CSV = "csv"
    HTML = "html"
    PDF = "pdf"
    MARKDOWN = "markdown"
    XML = "xml"

class QualityThresholds(BaseModel):
    """Quality thresholds for different metrics."""
    
    # Complexity thresholds
    cyclomatic_complexity_max: int = Field(default=10, ge=1, le=50)
    cognitive_complexity_max: int = Field(default=15, ge=1, le=100)
    nesting_depth_max: int = Field(default=4, ge=1, le=20)
    
    # Size thresholds
    function_length_max: int = Field(default=50, ge=1, le=1000)
    class_length_max: int = Field(default=500, ge=1, le=5000)
    file_length_max: int = Field(default=1000, ge=1, le=10000)
    
    # Quality scores (0-100)
    maintainability_min: float = Field(default=60.0, ge=0.0, le=100.0)
    reliability_min: float = Field(default=80.0, ge=0.0, le=100.0)
    security_min: float = Field(default=90.0, ge=0.0, le=100.0)
    
    # Performance thresholds
    execution_time_max_ms: int = Field(default=1000, ge=1)
    memory_usage_max_mb: int = Field(default=100, ge=1)
    
    # Coverage thresholds
    test_coverage_min: float = Field(default=80.0, ge=0.0, le=100.0)
    branch_coverage_min: float = Field(default=70.0, ge=0.0, le=100.0)

class AnalyzerConfig(BaseModel):
    """Configuration for individual analyzers."""
    
    enabled: bool = True
    priority: int = Field(default=1, ge=1, le=10)
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    
    # Analyzer-specific settings
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    # File filters
    include_patterns: List[str] = Field(default_factory=list)
    exclude_patterns: List[str] = Field(default_factory=list)
    
    # Language-specific configuration
    language_settings: Dict[AnalysisLanguage, Dict[str, Any]] = Field(default_factory=dict)

class PerformanceConfig(BaseModel):
    """Performance and resource configuration."""
    
    # Parallel processing
    max_workers: int = Field(default=4, ge=1, le=32)
    chunk_size: int = Field(default=100, ge=1, le=10000)
    
    # Memory management
    max_memory_mb: int = Field(default=2048, ge=256, le=16384)
    gc_threshold: int = Field(default=1000, ge=100, le=10000)
    
    # Caching
    enable_caching: bool = True
    cache_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    max_cache_size_mb: int = Field(default=512, ge=64, le=4096)
    
    # Timeouts
    analysis_timeout_seconds: int = Field(default=1800, ge=60, le=7200)
    file_timeout_seconds: int = Field(default=30, ge=1, le=300)
    
    # Batch processing
    batch_size: int = Field(default=50, ge=1, le=1000)
    batch_timeout_seconds: int = Field(default=600, ge=60, le=3600)

class OutputConfig(BaseModel):
    """Configuration for analysis output and reporting."""
    
    # Export formats
    export_formats: List[ExportFormat] = Field(default=[ExportFormat.JSON])
    
    # Output paths
    output_directory: Optional[Path] = None
    report_filename_template: str = "analysis_report_{timestamp}"
    
    # Report content
    include_source_code: bool = False
    include_metrics_details: bool = True
    include_recommendations: bool = True
    include_trends: bool = False
    
    # Visualization
    generate_charts: bool = True
    chart_format: str = "png"
    chart_dpi: int = Field(default=300, ge=72, le=600)
    
    # Filtering
    min_severity_level: str = "info"  # debug, info, warning, error, critical
    max_results_per_analyzer: int = Field(default=1000, ge=1, le=10000)

class AnalysisConfig(BaseModel):
    """Comprehensive configuration for code analysis."""
    
    # Basic settings
    name: str = Field(default="Default Analysis", min_length=1, max_length=255)
    description: Optional[str] = None
    version: str = "1.0.0"
    
    # Languages and analyzers
    target_languages: Set[AnalysisLanguage] = Field(default={AnalysisLanguage.PYTHON})
    enabled_analyzers: Set[AnalyzerType] = Field(default={
        AnalyzerType.COMPLEXITY,
        AnalyzerType.MAINTAINABILITY,
        AnalyzerType.SECURITY
    })
    
    # Configuration sections
    quality_thresholds: QualityThresholds = Field(default_factory=QualityThresholds)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    
    # Analyzer-specific configurations
    analyzer_configs: Dict[AnalyzerType, AnalyzerConfig] = Field(default_factory=dict)
    
    # File filtering
    include_file_patterns: List[str] = Field(default_factory=lambda: ["**/*.py", "**/*.ts", "**/*.js"])
    exclude_file_patterns: List[str] = Field(default_factory=lambda: [
        "**/node_modules/**",
        "**/venv/**",
        "**/.*/**",
        "**/__pycache__/**",
        "**/dist/**",
        "**/build/**"
    ])
    
    # Directory filtering
    include_directories: List[str] = Field(default_factory=list)
    exclude_directories: List[str] = Field(default_factory=lambda: [
        "node_modules",
        "venv",
        ".git",
        "__pycache__",
        "dist",
        "build",
        ".pytest_cache",
        ".mypy_cache"
    ])
    
    # Advanced settings
    incremental_analysis: bool = True
    baseline_comparison: bool = False
    trend_analysis: bool = False
    
    # Integration settings
    webhook_url: Optional[str] = None
    notification_settings: Dict[str, Any] = Field(default_factory=dict)
    
    # Custom settings
    custom_rules: Dict[str, Any] = Field(default_factory=dict)
    plugin_settings: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('target_languages')
    def validate_target_languages(cls, v):
        """Ensure at least one language is specified."""
        if not v:
            raise ValueError("At least one target language must be specified")
        return v
    
    @validator('enabled_analyzers')
    def validate_enabled_analyzers(cls, v):
        """Ensure at least one analyzer is enabled."""
        if not v:
            raise ValueError("At least one analyzer must be enabled")
        return v
    
    @validator('include_file_patterns')
    def validate_file_patterns(cls, v):
        """Ensure file patterns are valid."""
        if not v:
            raise ValueError("At least one file pattern must be specified")
        return v
    
    def get_analyzer_config(self, analyzer_type: AnalyzerType) -> AnalyzerConfig:
        """Get configuration for a specific analyzer."""
        return self.analyzer_configs.get(analyzer_type, AnalyzerConfig())
    
    def is_analyzer_enabled(self, analyzer_type: AnalyzerType) -> bool:
        """Check if an analyzer is enabled."""
        return (
            analyzer_type in self.enabled_analyzers and
            self.get_analyzer_config(analyzer_type).enabled
        )
    
    def get_language_file_patterns(self, language: AnalysisLanguage) -> List[str]:
        """Get file patterns for a specific language."""
        language_patterns = {
            AnalysisLanguage.PYTHON: ["**/*.py", "**/*.pyi"],
            AnalysisLanguage.TYPESCRIPT: ["**/*.ts", "**/*.tsx"],
            AnalysisLanguage.JAVASCRIPT: ["**/*.js", "**/*.jsx", "**/*.mjs"],
            AnalysisLanguage.JAVA: ["**/*.java"],
            AnalysisLanguage.CPP: ["**/*.cpp", "**/*.cxx", "**/*.cc", "**/*.h", "**/*.hpp"],
            AnalysisLanguage.RUST: ["**/*.rs"],
            AnalysisLanguage.GO: ["**/*.go"],
            AnalysisLanguage.CSHARP: ["**/*.cs"],
            AnalysisLanguage.PHP: ["**/*.php"],
            AnalysisLanguage.RUBY: ["**/*.rb"]
        }
        return language_patterns.get(language, [])
    
    def get_effective_file_patterns(self) -> List[str]:
        """Get effective file patterns based on target languages."""
        patterns = set(self.include_file_patterns)
        
        # Add language-specific patterns
        for language in self.target_languages:
            patterns.update(self.get_language_file_patterns(language))
        
        return list(patterns)
    
    def should_analyze_file(self, file_path: str) -> bool:
        """Check if a file should be analyzed based on patterns."""
        
        # Check exclude patterns first
        for pattern in self.exclude_file_patterns:
            if fnmatch(file_path, pattern):
                return False
        
        # Check include patterns
        effective_patterns = self.get_effective_file_patterns()
        for pattern in effective_patterns:
            if fnmatch(file_path, pattern):
                return True
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisConfig":
        """Create configuration from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_file(cls, file_path: Path) -> "AnalysisConfig":
        """Load configuration from file."""
        import json
        import yaml
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
        elif file_path.suffix.lower() in ['.yml', '.yaml']:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
        else:
            raise ValueError(f"Unsupported configuration file format: {file_path.suffix}")
        
        return cls.from_dict(data)
    
    def save_to_file(self, file_path: Path) -> None:
        """Save configuration to file."""
        
        data = self.to_dict()
        
        if file_path.suffix.lower() == '.json':
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif file_path.suffix.lower() in ['.yml', '.yaml']:
            with open(file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported configuration file format: {file_path.suffix}")

# Predefined configuration templates
class ConfigTemplates:
    """Predefined configuration templates for common use cases."""
    
    @staticmethod
    def minimal() -> AnalysisConfig:
        """Minimal configuration for basic analysis."""
        return AnalysisConfig(
            name="Minimal Analysis",
            enabled_analyzers={AnalyzerType.COMPLEXITY},
            target_languages={AnalysisLanguage.PYTHON}
        )
    
    @staticmethod
    def comprehensive() -> AnalysisConfig:
        """Comprehensive configuration for thorough analysis."""
        return AnalysisConfig(
            name="Comprehensive Analysis",
            enabled_analyzers={
                AnalyzerType.COMPLEXITY,
                AnalyzerType.SECURITY,
                AnalyzerType.PERFORMANCE,
                AnalyzerType.MAINTAINABILITY,
                AnalyzerType.DEAD_CODE,
                AnalyzerType.DEPENDENCIES,
                AnalyzerType.STYLE,
                AnalyzerType.DOCUMENTATION
            },
            target_languages={
                AnalysisLanguage.PYTHON,
                AnalysisLanguage.TYPESCRIPT,
                AnalysisLanguage.JAVASCRIPT
            }
        )
    
    @staticmethod
    def security_focused() -> AnalysisConfig:
        """Security-focused configuration."""
        config = AnalysisConfig(
            name="Security Analysis",
            enabled_analyzers={
                AnalyzerType.SECURITY,
                AnalyzerType.DEPENDENCIES
            }
        )
        config.quality_thresholds.security_min = 95.0
        return config
    
    @staticmethod
    def performance_focused() -> AnalysisConfig:
        """Performance-focused configuration."""
        return AnalysisConfig(
            name="Performance Analysis",
            enabled_analyzers={
                AnalyzerType.PERFORMANCE,
                AnalyzerType.COMPLEXITY,
                AnalyzerType.DEAD_CODE
            }
        )

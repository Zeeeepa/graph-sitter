"""
⚙️ Analysis Configuration and Results

Consolidated configuration system combining features from all PRs and tools:
- Advanced configuration options from PR #211
- Modular configuration from PR #212  
- Preset configurations from PR #213
- Comprehensive settings from PR #214
- Enhanced options from existing tools

Provides unified configuration interface for all analysis features.
"""

import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union
from pathlib import Path


@dataclass
class AIConfig:
    """Configuration for AI-powered analysis"""
    enabled: bool = False
    provider: str = "openai"  # openai, claude, local
    api_key: Optional[str] = None
    model: str = "gpt-4"
    max_requests: int = 150
    analysis_types: List[str] = field(default_factory=lambda: ["quality", "security"])
    timeout_seconds: int = 60
    enable_training_data_generation: bool = False


@dataclass
class VisualizationConfig:
    """Configuration for visualization and reporting"""
    enabled: bool = True
    generate_html_report: bool = True
    generate_interactive_viz: bool = True
    theme: str = "light"  # light, dark, high_contrast
    include_source_code: bool = False
    auto_open_browser: bool = False
    export_formats: List[str] = field(default_factory=lambda: ["html", "json"])
    output_directory: str = "./analysis_output"


@dataclass
class MetricsConfig:
    """Configuration for metrics calculation"""
    enabled: bool = True
    calculate_complexity: bool = True
    calculate_halstead: bool = True
    calculate_maintainability: bool = True
    calculate_quality_score: bool = True
    include_function_metrics: bool = True
    include_class_metrics: bool = True
    include_file_metrics: bool = True


@dataclass
class PatternDetectionConfig:
    """Configuration for pattern detection"""
    enabled: bool = True
    detect_dead_code: bool = True
    detect_import_loops: bool = True
    detect_code_smells: bool = True
    detect_anti_patterns: bool = True
    detect_security_issues: bool = False
    custom_patterns: List[str] = field(default_factory=list)


@dataclass
class GraphSitterConfig:
    """Configuration for graph-sitter integration"""
    enabled: bool = True
    use_advanced_config: bool = False
    enable_lazy_loading: bool = False
    enable_method_usages: bool = True
    enable_generics: bool = True
    debug_mode: bool = False
    verify_graph: bool = False
    import_resolution_paths: List[str] = field(default_factory=list)
    allow_external_imports: bool = False


@dataclass
class PerformanceConfig:
    """Configuration for performance optimization"""
    max_file_size_mb: int = 10
    max_files_per_batch: int = 1000
    enable_parallel_processing: bool = True
    max_worker_threads: int = 4
    enable_caching: bool = True
    cache_expiry_hours: int = 24
    timeout_seconds: int = 300


@dataclass
class AnalysisConfig:
    """
    Comprehensive analysis configuration.
    
    Combines all configuration options from PRs and existing tools.
    """
    # Core settings
    analysis_name: str = "Comprehensive Analysis"
    analysis_level: str = "standard"  # quick, standard, comprehensive, deep
    
    # Feature toggles
    enable_metrics: bool = True
    enable_pattern_detection: bool = True
    enable_ai_analysis: bool = False
    enable_visualization: bool = True
    enable_graph_sitter: bool = True
    
    # Component configurations
    ai_config: AIConfig = field(default_factory=AIConfig)
    visualization_config: VisualizationConfig = field(default_factory=VisualizationConfig)
    metrics_config: MetricsConfig = field(default_factory=MetricsConfig)
    pattern_detection_config: PatternDetectionConfig = field(default_factory=PatternDetectionConfig)
    graph_sitter_config: GraphSitterConfig = field(default_factory=GraphSitterConfig)
    performance_config: PerformanceConfig = field(default_factory=PerformanceConfig)
    
    # Legacy compatibility
    use_advanced_graph_sitter_config: bool = False
    generate_training_data: bool = False
    generate_html_report: bool = True
    generate_interactive_viz: bool = True
    
    # File filtering
    include_extensions: List[str] = field(default_factory=lambda: [".py", ".js", ".ts", ".jsx", ".tsx"])
    exclude_patterns: List[str] = field(default_factory=lambda: ["__pycache__", ".git", "node_modules"])
    exclude_test_files: bool = False
    
    # Output settings
    output_directory: str = "./analysis_output"
    save_intermediate_results: bool = False
    verbose_logging: bool = False


@dataclass
class QualityMetrics:
    """Quality metrics results"""
    maintainability_index: float = 0.0
    cyclomatic_complexity: float = 0.0
    halstead_difficulty: float = 0.0
    halstead_effort: float = 0.0
    halstead_volume: float = 0.0
    halstead_bugs: float = 0.0
    comment_ratio: float = 0.0
    documentation_coverage: float = 0.0
    test_coverage_estimate: float = 0.0
    technical_debt_ratio: float = 0.0
    quality_score: float = 0.0


@dataclass
class ComplexityMetrics:
    """Complexity metrics results"""
    total_complexity: int = 0
    average_complexity: float = 0.0
    max_complexity: int = 0
    complexity_distribution: Dict[str, int] = field(default_factory=dict)
    high_complexity_functions: List[str] = field(default_factory=list)
    complexity_by_file: Dict[str, float] = field(default_factory=dict)


@dataclass
class PatternResults:
    """Pattern detection results"""
    dead_code_items: List[str] = field(default_factory=list)
    import_loops: List[Dict[str, Any]] = field(default_factory=list)
    code_smells: List[Dict[str, Any]] = field(default_factory=list)
    anti_patterns: List[Dict[str, Any]] = field(default_factory=list)
    security_issues: List[Dict[str, Any]] = field(default_factory=list)
    pattern_summary: Dict[str, int] = field(default_factory=dict)


@dataclass
class AIResults:
    """AI analysis results"""
    insights: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    issues_detected: List[Dict[str, Any]] = field(default_factory=list)
    improvement_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    training_data: Optional[Dict[str, Any]] = None
    confidence_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class AnalysisResult:
    """
    Comprehensive analysis results.
    
    Contains all analysis data from all components.
    """
    # Metadata
    analysis_id: str = ""
    timestamp: str = ""
    path: str = ""
    analysis_config: Optional[AnalysisConfig] = None
    analysis_duration: float = 0.0
    success: bool = False
    error: Optional[str] = None
    
    # Basic statistics
    file_count: int = 0
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0
    total_lines: int = 0
    
    # Detailed analysis results
    file_analysis: Dict[str, Any] = field(default_factory=dict)
    function_analysis: Dict[str, Any] = field(default_factory=dict)
    class_analysis: Dict[str, Any] = field(default_factory=dict)
    import_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Metrics
    quality_metrics: Dict[str, QualityMetrics] = field(default_factory=dict)
    complexity_metrics: ComplexityMetrics = field(default_factory=ComplexityMetrics)
    
    # Pattern detection
    code_patterns: PatternResults = field(default_factory=PatternResults)
    dead_code: List[str] = field(default_factory=list)
    import_loops: List[Dict[str, Any]] = field(default_factory=list)
    
    # AI analysis
    ai_insights: Optional[AIResults] = None
    training_data: Optional[Dict[str, Any]] = None
    
    # Dependency analysis
    dependency_graph: Dict[str, Any] = field(default_factory=dict)
    call_graphs: Dict[str, Any] = field(default_factory=dict)
    
    # Visualization
    visualization_data: Dict[str, Any] = field(default_factory=dict)
    report_path: Optional[str] = None
    
    def __post_init__(self):
        """Initialize metadata"""
        if not self.analysis_id:
            self.analysis_id = f"analysis_{int(time.time())}"
        if not self.timestamp:
            self.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def save_to_file(self, filepath: str):
        """Save results to file"""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.to_json())
    
    def print_summary(self):
        """Print analysis summary"""
        print(f"\n🔍 Analysis Summary: {self.analysis_id}")
        print("=" * 50)
        print(f"📁 Path: {self.path}")
        print(f"⏱️  Duration: {self.analysis_duration:.2f}s")
        print(f"✅ Success: {self.success}")
        
        if self.error:
            print(f"❌ Error: {self.error}")
            return
        
        print(f"\n📊 Basic Statistics:")
        print(f"  📄 Files: {self.file_count}")
        print(f"  🔧 Functions: {self.function_count}")
        print(f"  🏗️  Classes: {self.class_count}")
        print(f"  📦 Imports: {self.import_count}")
        print(f"  📝 Total Lines: {self.total_lines}")
        
        if self.quality_metrics:
            avg_quality = sum(m.quality_score for m in self.quality_metrics.values()) / len(self.quality_metrics)
            print(f"\n📈 Quality Score: {avg_quality:.1f}/10")
        
        if self.dead_code:
            print(f"🗑️  Dead Code Items: {len(self.dead_code)}")
        
        if self.import_loops:
            print(f"🔄 Import Loops: {len(self.import_loops)}")
        
        if self.ai_insights and self.ai_insights.insights:
            print(f"🤖 AI Insights: {len(self.ai_insights.insights)}")
        
        if self.report_path:
            print(f"\n📋 Report: {self.report_path}")


class AnalysisPresets:
    """
    Predefined analysis configurations for common use cases.
    
    Combines presets from all PRs and tools.
    """
    
    @staticmethod
    def quick() -> AnalysisConfig:
        """Quick analysis with basic metrics"""
        config = AnalysisConfig()
        config.analysis_name = "Quick Analysis"
        config.analysis_level = "quick"
        config.enable_ai_analysis = False
        config.enable_pattern_detection = False
        config.visualization_config.generate_interactive_viz = False
        config.metrics_config.include_function_metrics = False
        config.metrics_config.include_class_metrics = False
        return config
    
    @staticmethod
    def standard() -> AnalysisConfig:
        """Standard analysis with core features"""
        config = AnalysisConfig()
        config.analysis_name = "Standard Analysis"
        config.analysis_level = "standard"
        return config
    
    @staticmethod
    def comprehensive() -> AnalysisConfig:
        """Comprehensive analysis with all features"""
        config = AnalysisConfig()
        config.analysis_name = "Comprehensive Analysis"
        config.analysis_level = "comprehensive"
        config.enable_ai_analysis = False  # Disabled by default (requires API key)
        config.pattern_detection_config.detect_security_issues = True
        config.graph_sitter_config.use_advanced_config = True
        config.visualization_config.generate_interactive_viz = True
        return config
    
    @staticmethod
    def quality_focused() -> AnalysisConfig:
        """Quality-focused analysis"""
        config = AnalysisConfig()
        config.analysis_name = "Quality Analysis"
        config.analysis_level = "comprehensive"
        config.enable_ai_analysis = False
        config.metrics_config.calculate_quality_score = True
        config.pattern_detection_config.detect_code_smells = True
        config.pattern_detection_config.detect_anti_patterns = True
        return config
    
    @staticmethod
    def security_focused() -> AnalysisConfig:
        """Security-focused analysis"""
        config = AnalysisConfig()
        config.analysis_name = "Security Analysis"
        config.analysis_level = "comprehensive"
        config.pattern_detection_config.detect_security_issues = True
        config.ai_config.enabled = False  # Can be enabled with API key
        config.ai_config.analysis_types = ["security"]
        return config
    
    @staticmethod
    def ai_powered() -> AnalysisConfig:
        """AI-powered analysis (requires API key)"""
        config = AnalysisConfig()
        config.analysis_name = "AI-Powered Analysis"
        config.analysis_level = "comprehensive"
        config.enable_ai_analysis = True
        config.ai_config.enabled = True
        config.ai_config.analysis_types = ["quality", "security", "performance"]
        config.generate_training_data = True
        return config
    
    @staticmethod
    def enhanced() -> AnalysisConfig:
        """Enhanced analysis with graph-sitter features"""
        config = AnalysisConfig()
        config.analysis_name = "Enhanced Analysis"
        config.analysis_level = "comprehensive"
        config.use_advanced_graph_sitter_config = True
        config.graph_sitter_config.use_advanced_config = True
        config.graph_sitter_config.enable_method_usages = True
        config.graph_sitter_config.enable_generics = True
        return config
    
    @staticmethod
    def performance_optimized() -> AnalysisConfig:
        """Performance-optimized analysis for large codebases"""
        config = AnalysisConfig()
        config.analysis_name = "Performance Optimized"
        config.analysis_level = "standard"
        config.performance_config.enable_parallel_processing = True
        config.performance_config.max_worker_threads = 8
        config.performance_config.enable_caching = True
        config.graph_sitter_config.enable_lazy_loading = True
        config.visualization_config.generate_interactive_viz = False
        return config
    
    @staticmethod
    def legacy_compatible() -> AnalysisConfig:
        """Configuration compatible with legacy tools"""
        config = AnalysisConfig()
        config.analysis_name = "Legacy Compatible"
        config.analysis_level = "standard"
        config.enable_graph_sitter = True
        config.use_advanced_graph_sitter_config = False
        return config


# Convenience functions
def create_custom_config(**kwargs) -> AnalysisConfig:
    """Create custom configuration with overrides"""
    config = AnalysisConfig()
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            # Handle nested config updates
            if '.' in key:
                parts = key.split('.')
                obj = config
                for part in parts[:-1]:
                    obj = getattr(obj, part)
                setattr(obj, parts[-1], value)
    
    return config


def load_config_from_file(filepath: str) -> AnalysisConfig:
    """Load configuration from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert dict to AnalysisConfig
    # This is a simplified implementation
    config = AnalysisConfig()
    
    # Update config with loaded data
    for key, value in data.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config


def save_config_to_file(config: AnalysisConfig, filepath: str):
    """Save configuration to JSON file"""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(asdict(config), f, indent=2, default=str)


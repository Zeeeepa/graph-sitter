"""
Analysis Configuration System

Centralized configuration for all analysis types, targets, and behaviors.
This eliminates the "chaotic" nature mentioned by the user by providing
organized, consistent configuration across all analysis components.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from enum import Enum


class AnalysisType(Enum):
    """Enumeration of available analysis types."""
    ERROR_ANALYSIS = "error_analysis"
    BLAST_RADIUS = "blast_radius"
    DEPENDENCY = "dependency"
    COMPLEXITY = "complexity"
    PERFORMANCE = "performance"
    SECURITY = "security"
    QUALITY = "quality"


class TargetType(Enum):
    """Enumeration of analysis target types."""
    # Error analysis targets
    SYNTAX = "syntax"
    RUNTIME = "runtime"
    LOGICAL = "logical"
    PERFORMANCE_ERROR = "performance"
    SECURITY_ERROR = "security"
    
    # Blast radius targets
    ERROR = "error"
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    FILE = "file"
    
    # Dependency targets
    IMPORTS = "imports"
    INHERITANCE = "inheritance"
    CALLS = "calls"
    
    # Complexity targets
    CYCLOMATIC = "cyclomatic"
    COGNITIVE = "cognitive"
    HALSTEAD = "halstead"
    
    # Performance targets
    BOTTLENECKS = "bottlenecks"
    OPTIMIZATION = "optimization"
    MEMORY = "memory"


class SeverityLevel(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AnalysisTarget:
    """Configuration for an analysis target."""
    name: str
    description: str
    applicable_types: List[AnalysisType]
    default_params: Dict[str, Any]
    visualization_types: List[str]


@dataclass
class AnalysisTypeConfig:
    """Configuration for an analysis type."""
    name: str
    description: str
    icon: str
    color: str
    targets: List[TargetType]
    default_target: Optional[TargetType]
    visualization_types: List[str]
    default_params: Dict[str, Any]
    requires_codebase: bool = True
    supports_progressive_loading: bool = True


@dataclass
class VisualizationConfig:
    """Configuration for visualization options."""
    name: str
    description: str
    component_type: str
    supported_analysis_types: List[AnalysisType]
    default_params: Dict[str, Any]
    interactive_features: List[str]


# Analysis Type Configurations
ANALYSIS_TYPE_CONFIGS = {
    AnalysisType.ERROR_ANALYSIS: AnalysisTypeConfig(
        name="Error Analysis",
        description="Comprehensive error detection and impact assessment",
        icon="Bug",
        color="text-red-600",
        targets=[
            TargetType.SYNTAX,
            TargetType.RUNTIME,
            TargetType.LOGICAL,
            TargetType.PERFORMANCE_ERROR,
            TargetType.SECURITY_ERROR
        ],
        default_target=TargetType.SYNTAX,
        visualization_types=["error_map", "severity_chart", "resolution_guide"],
        default_params={
            "max_errors": 100,
            "severity_threshold": SeverityLevel.MEDIUM,
            "include_warnings": True,
            "check_imports": True,
            "analyze_complexity": True
        }
    ),
    
    AnalysisType.BLAST_RADIUS: AnalysisTypeConfig(
        name="Blast Radius",
        description="Impact analysis from selected point",
        icon="Zap",
        color="text-orange-600",
        targets=[
            TargetType.ERROR,
            TargetType.FUNCTION,
            TargetType.CLASS,
            TargetType.MODULE
        ],
        default_target=TargetType.ERROR,
        visualization_types=["impact_graph", "heatmap", "propagation"],
        default_params={
            "max_depth": 5,
            "include_reverse": True,
            "impact_threshold": 0.1,
            "show_critical_paths": True,
            "calculate_scores": True
        }
    ),
    
    AnalysisType.DEPENDENCY: AnalysisTypeConfig(
        name="Dependency Analysis",
        description="Module dependencies and import relationships",
        icon="Network",
        color="text-blue-600",
        targets=[
            TargetType.MODULE,
            TargetType.CLASS,
            TargetType.FUNCTION,
            TargetType.IMPORTS
        ],
        default_target=TargetType.MODULE,
        visualization_types=["graph", "tree", "matrix"],
        default_params={
            "include_external": False,
            "show_circular": True,
            "group_by_module": True,
            "calculate_coupling": True,
            "detect_cycles": True
        }
    ),
    
    AnalysisType.COMPLEXITY: AnalysisTypeConfig(
        name="Complexity Analysis",
        description="Code complexity metrics and heatmap",
        icon="BarChart3",
        color="text-purple-600",
        targets=[
            TargetType.FILE,
            TargetType.CLASS,
            TargetType.FUNCTION,
            TargetType.CYCLOMATIC,
            TargetType.COGNITIVE
        ],
        default_target=TargetType.FUNCTION,
        visualization_types=["heatmap", "metrics", "trends"],
        default_params={
            "complexity_threshold": 10,
            "include_cognitive": True,
            "include_halstead": False,
            "show_trends": True,
            "highlight_hotspots": True
        }
    ),
    
    AnalysisType.PERFORMANCE: AnalysisTypeConfig(
        name="Performance Analysis",
        description="Performance bottlenecks and optimization opportunities",
        icon="TrendingUp",
        color="text-green-600",
        targets=[
            TargetType.FUNCTION,
            TargetType.CLASS,
            TargetType.MODULE,
            TargetType.BOTTLENECKS
        ],
        default_target=TargetType.BOTTLENECKS,
        visualization_types=["bottleneck_graph", "performance_metrics", "optimization_suggestions"],
        default_params={
            "performance_threshold": 0.8,
            "include_memory": True,
            "analyze_loops": True,
            "check_algorithms": True,
            "suggest_optimizations": True
        }
    ),
    
    AnalysisType.SECURITY: AnalysisTypeConfig(
        name="Security Analysis",
        description="Security vulnerabilities and risk assessment",
        icon="Shield",
        color="text-red-700",
        targets=[
            TargetType.SECURITY_ERROR,
            TargetType.FUNCTION,
            TargetType.MODULE
        ],
        default_target=TargetType.SECURITY_ERROR,
        visualization_types=["vulnerability_map", "risk_assessment", "security_score"],
        default_params={
            "severity_threshold": SeverityLevel.HIGH,
            "check_inputs": True,
            "analyze_permissions": True,
            "scan_dependencies": True,
            "include_cwe": True
        }
    ),
    
    AnalysisType.QUALITY: AnalysisTypeConfig(
        name="Code Quality",
        description="Code quality metrics and improvement suggestions",
        icon="CheckCircle",
        color="text-indigo-600",
        targets=[
            TargetType.FILE,
            TargetType.CLASS,
            TargetType.FUNCTION
        ],
        default_target=TargetType.FUNCTION,
        visualization_types=["quality_score", "improvement_suggestions", "trends"],
        default_params={
            "quality_threshold": 0.7,
            "include_documentation": True,
            "check_naming": True,
            "analyze_structure": True,
            "suggest_refactoring": True
        }
    )
}

# Target Configurations
TARGET_CONFIGS = {
    # Error Analysis Targets
    TargetType.SYNTAX: AnalysisTarget(
        name="Syntax Errors",
        description="Python syntax errors and parsing issues",
        applicable_types=[AnalysisType.ERROR_ANALYSIS],
        default_params={"use_ast": True, "check_encoding": True},
        visualization_types=["error_list", "file_heatmap"]
    ),
    
    TargetType.RUNTIME: AnalysisTarget(
        name="Runtime Errors",
        description="Potential runtime errors and exceptions",
        applicable_types=[AnalysisType.ERROR_ANALYSIS],
        default_params={"predict_exceptions": True, "analyze_patterns": True},
        visualization_types=["error_prediction", "risk_heatmap"]
    ),
    
    TargetType.LOGICAL: AnalysisTarget(
        name="Logical Errors",
        description="Logic errors and code smells",
        applicable_types=[AnalysisType.ERROR_ANALYSIS, AnalysisType.QUALITY],
        default_params={"check_patterns": True, "analyze_flow": True},
        visualization_types=["code_smell_map", "logic_flow"]
    ),
    
    # Blast Radius Targets
    TargetType.ERROR: AnalysisTarget(
        name="Error Impact",
        description="Impact analysis from error locations",
        applicable_types=[AnalysisType.BLAST_RADIUS],
        default_params={"trace_dependencies": True, "calculate_impact": True},
        visualization_types=["impact_graph", "propagation_map"]
    ),
    
    TargetType.FUNCTION: AnalysisTarget(
        name="Function Impact",
        description="Impact analysis from specific functions",
        applicable_types=[AnalysisType.BLAST_RADIUS, AnalysisType.DEPENDENCY, AnalysisType.COMPLEXITY, AnalysisType.PERFORMANCE],
        default_params={"include_callers": True, "analyze_usage": True},
        visualization_types=["call_graph", "usage_heatmap"]
    ),
    
    TargetType.CLASS: AnalysisTarget(
        name="Class Impact",
        description="Impact analysis from class definitions",
        applicable_types=[AnalysisType.BLAST_RADIUS, AnalysisType.DEPENDENCY, AnalysisType.COMPLEXITY],
        default_params={"include_inheritance": True, "analyze_methods": True},
        visualization_types=["class_hierarchy", "method_usage"]
    ),
    
    TargetType.MODULE: AnalysisTarget(
        name="Module Impact",
        description="Impact analysis from module level",
        applicable_types=[AnalysisType.BLAST_RADIUS, AnalysisType.DEPENDENCY, AnalysisType.PERFORMANCE],
        default_params={"include_imports": True, "analyze_exports": True},
        visualization_types=["module_graph", "import_tree"]
    ),
    
    # Dependency Targets
    TargetType.IMPORTS: AnalysisTarget(
        name="Import Analysis",
        description="Import and export relationships",
        applicable_types=[AnalysisType.DEPENDENCY],
        default_params={"include_external": False, "detect_circular": True},
        visualization_types=["import_graph", "dependency_matrix"]
    ),
    
    # Complexity Targets
    TargetType.CYCLOMATIC: AnalysisTarget(
        name="Cyclomatic Complexity",
        description="Cyclomatic complexity analysis",
        applicable_types=[AnalysisType.COMPLEXITY],
        default_params={"threshold": 10, "include_nested": True},
        visualization_types=["complexity_heatmap", "complexity_trends"]
    ),
    
    # Performance Targets
    TargetType.BOTTLENECKS: AnalysisTarget(
        name="Performance Bottlenecks",
        description="Performance bottleneck identification",
        applicable_types=[AnalysisType.PERFORMANCE],
        default_params={"analyze_loops": True, "check_algorithms": True},
        visualization_types=["bottleneck_graph", "performance_profile"]
    )
}

# Visualization Configurations
VISUALIZATION_CONFIGS = {
    "error_map": VisualizationConfig(
        name="Error Map",
        description="Interactive map of errors across the codebase",
        component_type="ErrorMapVisualization",
        supported_analysis_types=[AnalysisType.ERROR_ANALYSIS],
        default_params={"color_by_severity": True, "group_by_type": True},
        interactive_features=["zoom", "filter", "tooltip", "drill_down"]
    ),
    
    "impact_graph": VisualizationConfig(
        name="Impact Graph",
        description="Interactive graph showing blast radius impact",
        component_type="BlastRadiusVisualization",
        supported_analysis_types=[AnalysisType.BLAST_RADIUS],
        default_params={"layout": "force_directed", "show_levels": True},
        interactive_features=["zoom", "drag", "filter", "highlight", "tooltip"]
    ),
    
    "dependency_graph": VisualizationConfig(
        name="Dependency Graph",
        description="Interactive dependency relationship graph",
        component_type="DependencyGraphVisualization",
        supported_analysis_types=[AnalysisType.DEPENDENCY],
        default_params={"layout": "hierarchical", "group_modules": True},
        interactive_features=["zoom", "collapse", "filter", "search"]
    ),
    
    "complexity_heatmap": VisualizationConfig(
        name="Complexity Heatmap",
        description="Heatmap showing complexity across codebase",
        component_type="ComplexityHeatmapVisualization",
        supported_analysis_types=[AnalysisType.COMPLEXITY],
        default_params={"color_scale": "red_yellow_green", "show_values": True},
        interactive_features=["zoom", "tooltip", "filter", "threshold_slider"]
    )
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    "default_port": 8080,
    "progressive_loading": True,
    "auto_refresh": False,
    "export_formats": ["json", "csv", "svg", "png"],
    "theme": "light",
    "layout": "responsive",
    "max_nodes_before_pagination": 1000,
    "default_analysis_type": AnalysisType.ERROR_ANALYSIS,
    "show_welcome_tour": True,
    "enable_keyboard_shortcuts": True,
    "cache_visualizations": True,
    "animation_duration": 500
}

# Auto-trigger Configuration
AUTO_TRIGGER_CONFIG = {
    "keywords": ["analysis", "analyze", "audit", "review", "inspect"],
    "enabled": True,
    "default_analysis_types": [AnalysisType.ERROR_ANALYSIS, AnalysisType.COMPLEXITY],
    "auto_open_dashboard": True,
    "save_results": True,
    "generate_report": True
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    "max_files": 10000,
    "max_functions": 50000,
    "timeout_seconds": 300,
    "parallel_processing": True,
    "max_workers": 4,
    "chunk_size": 100,
    "memory_limit_mb": 1024,
    "enable_caching": True,
    "cache_ttl_hours": 24
}

# Export Configuration
EXPORT_CONFIG = {
    "default_format": "json",
    "include_metadata": True,
    "compress_large_files": True,
    "max_file_size_mb": 100,
    "timestamp_files": True,
    "create_summary": True,
    "include_visualizations": True
}


def get_analysis_config(analysis_type: AnalysisType) -> AnalysisTypeConfig:
    """Get configuration for a specific analysis type."""
    return ANALYSIS_TYPE_CONFIGS.get(analysis_type)


def get_target_config(target_type: TargetType) -> AnalysisTarget:
    """Get configuration for a specific target type."""
    return TARGET_CONFIGS.get(target_type)


def get_visualization_config(viz_type: str) -> VisualizationConfig:
    """Get configuration for a specific visualization type."""
    return VISUALIZATION_CONFIGS.get(viz_type)


def get_available_targets(analysis_type: AnalysisType) -> List[TargetType]:
    """Get available targets for an analysis type."""
    config = get_analysis_config(analysis_type)
    return config.targets if config else []


def get_available_visualizations(analysis_type: AnalysisType) -> List[str]:
    """Get available visualizations for an analysis type."""
    config = get_analysis_config(analysis_type)
    return config.visualization_types if config else []


def is_target_compatible(analysis_type: AnalysisType, target_type: TargetType) -> bool:
    """Check if a target is compatible with an analysis type."""
    target_config = get_target_config(target_type)
    return target_config and analysis_type in target_config.applicable_types


def get_default_params(analysis_type: AnalysisType, target_type: Optional[TargetType] = None) -> Dict[str, Any]:
    """Get default parameters for analysis type and target combination."""
    params = {}
    
    # Get analysis type defaults
    analysis_config = get_analysis_config(analysis_type)
    if analysis_config:
        params.update(analysis_config.default_params)
    
    # Override with target-specific defaults
    if target_type:
        target_config = get_target_config(target_type)
        if target_config:
            params.update(target_config.default_params)
    
    return params


def validate_analysis_request(analysis_type: AnalysisType, target_type: TargetType) -> bool:
    """Validate that an analysis request is valid."""
    if not get_analysis_config(analysis_type):
        return False
    
    if not get_target_config(target_type):
        return False
    
    return is_target_compatible(analysis_type, target_type)


# Quick preset configurations for common analysis scenarios
ANALYSIS_PRESETS = {
    "syntax_check": {
        "analysis_type": AnalysisType.ERROR_ANALYSIS,
        "target_type": TargetType.SYNTAX,
        "description": "Quick syntax error check",
        "params": {"fast_mode": True}
    },
    
    "error_impact": {
        "analysis_type": AnalysisType.BLAST_RADIUS,
        "target_type": TargetType.ERROR,
        "description": "Analyze error impact and propagation",
        "params": {"max_depth": 3}
    },
    
    "dependency_overview": {
        "analysis_type": AnalysisType.DEPENDENCY,
        "target_type": TargetType.MODULE,
        "description": "High-level dependency overview",
        "params": {"include_external": False}
    },
    
    "complexity_hotspots": {
        "analysis_type": AnalysisType.COMPLEXITY,
        "target_type": TargetType.FUNCTION,
        "description": "Find complexity hotspots",
        "params": {"threshold": 15, "highlight_hotspots": True}
    },
    
    "performance_audit": {
        "analysis_type": AnalysisType.PERFORMANCE,
        "target_type": TargetType.BOTTLENECKS,
        "description": "Comprehensive performance audit",
        "params": {"include_memory": True, "suggest_optimizations": True}
    }
}


def get_preset_config(preset_name: str) -> Optional[Dict[str, Any]]:
    """Get configuration for a preset analysis."""
    return ANALYSIS_PRESETS.get(preset_name)


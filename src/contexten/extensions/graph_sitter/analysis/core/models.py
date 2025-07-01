#!/usr/bin/env python3
"""
Unified Data Models for Graph-Sitter Analysis System

This module contains all data classes and models used throughout the analysis system,
consolidating models from the original three analysis files.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Union


# ============================================================================
# CORE ANALYSIS MODELS
# ============================================================================

@dataclass
class CodeIssue:
    """Represents a code issue with detailed information."""
    type: str
    severity: str  # 'critical', 'major', 'minor', 'info'
    message: str
    file_path: str
    line_start: int
    line_end: Optional[int] = None
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None
    confidence: float = 1.0


@dataclass
class DeadCodeItem:
    """Represents dead/unused code."""
    type: str  # 'function', 'class', 'variable'
    name: str
    file_path: str
    line_start: int
    line_end: int
    reason: str
    confidence: float


@dataclass
class FunctionMetrics:
    """Comprehensive function metrics."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    cyclomatic_complexity: int
    halstead_volume: float
    maintainability_index: int
    lines_of_code: int
    parameters_count: int
    return_statements: int
    dependencies: List[str] = field(default_factory=list)
    usages: List[str] = field(default_factory=list)
    call_sites: List[str] = field(default_factory=list)
    complexity_rank: str = "A"
    loc: int = 0
    lloc: int = 0
    sloc: int = 0
    comments: int = 0
    halstead_n1: int = 0
    halstead_n2: int = 0
    halstead_N1: int = 0
    halstead_N2: int = 0
    docstring: str = ""
    function_calls: int = 0
    parameters: int = 0
    returns: int = 0


@dataclass
class ClassMetrics:
    """Metrics for a class."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    depth_of_inheritance: int
    method_count: int
    attribute_count: int
    lines_of_code: int
    parent_classes: List[str] = field(default_factory=list)


@dataclass
class FileAnalysis:
    """Analysis results for a single file."""
    file_path: str
    lines_of_code: int
    logical_lines: int
    source_lines: int
    comment_lines: int
    comment_density: float
    functions: List[FunctionMetrics] = field(default_factory=list)
    classes: List[ClassMetrics] = field(default_factory=list)
    issues: List[CodeIssue] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    complexity_score: float = 0.0


@dataclass
class ComprehensiveAnalysisResult:
    """Complete analysis results."""
    # Basic metrics
    total_files: int
    total_functions: int
    total_classes: int
    total_lines: int
    total_logical_lines: int
    total_source_lines: int
    total_comment_lines: int
    
    # Quality metrics
    average_maintainability_index: float
    average_cyclomatic_complexity: float
    average_halstead_volume: float
    average_depth_of_inheritance: float
    comment_density: float
    technical_debt_ratio: float
    
    # Analysis results
    files: List[FileAnalysis] = field(default_factory=list)
    issues: List[CodeIssue] = field(default_factory=list)
    dead_code_items: List[DeadCodeItem] = field(default_factory=list)
    
    # Advanced metrics
    function_metrics: List[FunctionMetrics] = field(default_factory=list)
    class_metrics: List[ClassMetrics] = field(default_factory=list)
    
    # Investigation results
    top_level_functions: List[str] = field(default_factory=list)
    top_level_classes: List[str] = field(default_factory=list)
    inheritance_hierarchy: Dict[str, Any] = field(default_factory=dict)
    dependency_graph: Dict[str, List[str]] = field(default_factory=dict)
    usage_patterns: Dict[str, Any] = field(default_factory=dict)
    
    # Performance metrics
    analysis_time: float = 0.0
    files_per_second: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# ============================================================================
# GRAPH-SITTER ENHANCED MODELS
# ============================================================================

@dataclass
class ImportLoop:
    """Represents a circular import dependency."""
    files: List[str]
    loop_type: str  # 'static', 'dynamic', 'mixed'
    severity: str   # 'critical', 'warning', 'info'
    imports: List[Dict[str, Any]]


@dataclass
class TrainingDataItem:
    """Training data item for ML models."""
    implementation: Dict[str, str]
    dependencies: List[Dict[str, str]]
    usages: List[Dict[str, str]]
    metadata: Dict[str, Any]


@dataclass
class GraphAnalysisResult:
    """Results from graph-based analysis."""
    total_nodes: int
    total_edges: int
    symbol_usage_edges: int
    import_resolution_edges: int
    export_edges: int
    strongly_connected_components: List[List[str]]
    import_loops: List[ImportLoop]


@dataclass
class EnhancedFunctionMetrics:
    """Enhanced function metrics using graph-sitter."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    # Basic metrics
    cyclomatic_complexity: int
    halstead_volume: float
    maintainability_index: int
    lines_of_code: int
    # Graph-sitter enhanced metrics
    dependencies: List[str] = field(default_factory=list)
    usages: List[str] = field(default_factory=list)
    call_sites: List[str] = field(default_factory=list)
    function_calls: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    return_statements: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    is_async: bool = False
    is_generator: bool = False
    docstring: str = ""


@dataclass
class EnhancedClassMetrics:
    """Enhanced class metrics using graph-sitter."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    # Basic metrics
    depth_of_inheritance: int
    method_count: int
    attribute_count: int
    lines_of_code: int
    # Graph-sitter enhanced metrics
    parent_classes: List[str] = field(default_factory=list)
    subclasses: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    attributes: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    usages: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    is_abstract: bool = False


# ============================================================================
# ANALYSIS CONFIGURATION MODELS
# ============================================================================

@dataclass
class AnalysisOptions:
    """Configuration options for analysis."""
    use_graph_sitter: bool = True
    include_dead_code: bool = False
    include_import_loops: bool = False
    include_training_data: bool = False
    include_enhanced_metrics: bool = False
    include_graph_analysis: bool = False
    extensions: Optional[List[str]] = None
    max_complexity: int = 10
    min_maintainability: int = 20
    confidence_threshold: float = 0.5


@dataclass
class AnalysisContext:
    """Context information for analysis operations."""
    codebase_path: str
    options: AnalysisOptions
    start_time: float
    total_files: int = 0
    processed_files: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def create_default_analysis_options() -> AnalysisOptions:
    """Create default analysis options."""
    return AnalysisOptions()


def merge_analysis_results(*results: ComprehensiveAnalysisResult) -> ComprehensiveAnalysisResult:
    """Merge multiple analysis results into one."""
    if not results:
        return ComprehensiveAnalysisResult(
            total_files=0, total_functions=0, total_classes=0,
            total_lines=0, total_logical_lines=0, total_source_lines=0,
            total_comment_lines=0, average_maintainability_index=0.0,
            average_cyclomatic_complexity=0.0, average_halstead_volume=0.0,
            average_depth_of_inheritance=0.0, comment_density=0.0,
            technical_debt_ratio=0.0
        )
    
    merged = ComprehensiveAnalysisResult(
        total_files=sum(r.total_files for r in results),
        total_functions=sum(r.total_functions for r in results),
        total_classes=sum(r.total_classes for r in results),
        total_lines=sum(r.total_lines for r in results),
        total_logical_lines=sum(r.total_logical_lines for r in results),
        total_source_lines=sum(r.total_source_lines for r in results),
        total_comment_lines=sum(r.total_comment_lines for r in results),
        
        # Calculate weighted averages
        average_maintainability_index=sum(r.average_maintainability_index * r.total_functions for r in results) / sum(r.total_functions for r in results) if sum(r.total_functions for r in results) > 0 else 0.0,
        average_cyclomatic_complexity=sum(r.average_cyclomatic_complexity * r.total_functions for r in results) / sum(r.total_functions for r in results) if sum(r.total_functions for r in results) > 0 else 0.0,
        average_halstead_volume=sum(r.average_halstead_volume * r.total_functions for r in results) / sum(r.total_functions for r in results) if sum(r.total_functions for r in results) > 0 else 0.0,
        average_depth_of_inheritance=sum(r.average_depth_of_inheritance * r.total_classes for r in results) / sum(r.total_classes for r in results) if sum(r.total_classes for r in results) > 0 else 0.0,
        comment_density=sum(r.comment_density * r.total_lines for r in results) / sum(r.total_lines for r in results) if sum(r.total_lines for r in results) > 0 else 0.0,
        technical_debt_ratio=sum(r.technical_debt_ratio for r in results) / len(results),
        
        # Combine lists
        files=[f for r in results for f in r.files],
        issues=[i for r in results for i in r.issues],
        dead_code_items=[d for r in results for d in r.dead_code_items],
        function_metrics=[f for r in results for f in r.function_metrics],
        class_metrics=[c for r in results for c in r.class_metrics],
        
        # Combine dictionaries
        inheritance_hierarchy={k: v for r in results for k, v in r.inheritance_hierarchy.items()},
        dependency_graph={k: v for r in results for k, v in r.dependency_graph.items()},
        usage_patterns={k: v for r in results for k, v in r.usage_patterns.items()},
        
        # Performance metrics
        analysis_time=sum(r.analysis_time for r in results),
        files_per_second=sum(r.files_per_second for r in results) / len(results)
    )
    
    return merged


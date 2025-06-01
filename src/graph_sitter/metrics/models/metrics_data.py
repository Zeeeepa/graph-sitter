"""Data models for storing and representing code metrics."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

@dataclass
class HalsteadMetrics:
    """Halstead complexity metrics.
    
    Based on the formula: V = (N1 + N2) * log2(n1 + n2)
    Where:
    - n1: number of distinct operators
    - n2: number of distinct operands  
    - N1: total number of operators
    - N2: total number of operands
    """
    n1: int = 0  # distinct operators
    n2: int = 0  # distinct operands
    N1: int = 0  # total operators
    N2: int = 0  # total operands
    
    @property
    def vocabulary(self) -> int:
        """Total vocabulary (n1 + n2)."""
        return self.n1 + self.n2
    
    @property
    def length(self) -> int:
        """Program length (N1 + N2)."""
        return self.N1 + self.N2
    
    @property
    def volume(self) -> float:
        """Halstead volume: V = (N1 + N2) * log2(n1 + n2)."""
        if self.vocabulary <= 1:
            return 0.0
        return self.length * math.log2(self.vocabulary)
    
    @property
    def difficulty(self) -> float:
        """Halstead difficulty: D = (n1/2) * (N2/n2)."""
        if self.n2 == 0:
            return 0.0
        return (self.n1 / 2) * (self.N2 / self.n2)
    
    @property
    def effort(self) -> float:
        """Halstead effort: E = D * V."""
        return self.difficulty * self.volume

@dataclass
class FunctionMetrics:
    """Metrics for a single function."""
    name: str
    file_path: str
    start_line: int
    end_line: int
    
    # Core metrics
    cyclomatic_complexity: int = 0
    halstead: HalsteadMetrics = field(default_factory=HalsteadMetrics)
    maintainability_index: float = 0.0
    
    # Lines of code metrics
    total_lines: int = 0
    logical_lines: int = 0
    source_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # Function-specific metrics
    parameter_count: int = 0
    return_statement_count: int = 0
    function_call_count: int = 0
    nesting_depth: int = 0
    
    # Quality metrics
    is_recursive: bool = False
    is_dead_code: bool = False
    has_unused_parameters: bool = False
    
    # Context metrics
    call_site_count: int = 0
    dependency_count: int = 0
    
    # Timestamp
    calculated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def comment_ratio(self) -> float:
        """Ratio of comment lines to total lines."""
        if self.total_lines == 0:
            return 0.0
        return self.comment_lines / self.total_lines
    
    @property
    def complexity_per_line(self) -> float:
        """Cyclomatic complexity per logical line."""
        if self.logical_lines == 0:
            return 0.0
        return self.cyclomatic_complexity / self.logical_lines

@dataclass
class ClassMetrics:
    """Metrics for a single class."""
    name: str
    file_path: str
    start_line: int
    end_line: int
    
    # Core metrics
    cyclomatic_complexity: int = 0
    halstead: HalsteadMetrics = field(default_factory=HalsteadMetrics)
    maintainability_index: float = 0.0
    
    # Lines of code metrics
    total_lines: int = 0
    logical_lines: int = 0
    source_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # Class-specific metrics
    method_count: int = 0
    attribute_count: int = 0
    depth_of_inheritance: int = 0
    number_of_children: int = 0
    
    # Method metrics aggregation
    function_metrics: List[FunctionMetrics] = field(default_factory=list)
    
    # Quality metrics
    has_dead_methods: bool = False
    
    # Timestamp
    calculated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def comment_ratio(self) -> float:
        """Ratio of comment lines to total lines."""
        if self.total_lines == 0:
            return 0.0
        return self.comment_lines / self.total_lines
    
    @property
    def average_method_complexity(self) -> float:
        """Average cyclomatic complexity of methods."""
        if not self.function_metrics:
            return 0.0
        return sum(m.cyclomatic_complexity for m in self.function_metrics) / len(self.function_metrics)

@dataclass
class FileMetrics:
    """Metrics for a single file."""
    file_path: str
    language: str
    
    # Core metrics
    cyclomatic_complexity: int = 0
    halstead: HalsteadMetrics = field(default_factory=HalsteadMetrics)
    maintainability_index: float = 0.0
    
    # Lines of code metrics
    total_lines: int = 0
    logical_lines: int = 0
    source_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    
    # File-specific metrics
    class_count: int = 0
    function_count: int = 0
    import_count: int = 0
    global_var_count: int = 0
    interface_count: int = 0
    
    # Aggregated metrics from classes and functions
    class_metrics: List[ClassMetrics] = field(default_factory=list)
    function_metrics: List[FunctionMetrics] = field(default_factory=list)
    
    # Quality metrics
    has_dead_code: bool = False
    test_coverage: float = 0.0
    is_test_file: bool = False
    
    # Timestamp
    calculated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def comment_ratio(self) -> float:
        """Ratio of comment lines to total lines."""
        if self.total_lines == 0:
            return 0.0
        return self.comment_lines / self.total_lines
    
    @property
    def average_function_complexity(self) -> float:
        """Average cyclomatic complexity of functions."""
        if not self.function_metrics:
            return 0.0
        return sum(f.cyclomatic_complexity for f in self.function_metrics) / len(self.function_metrics)
    
    @property
    def average_class_complexity(self) -> float:
        """Average cyclomatic complexity of classes."""
        if not self.class_metrics:
            return 0.0
        return sum(c.cyclomatic_complexity for c in self.class_metrics) / len(self.class_metrics)

@dataclass
class CodebaseMetrics:
    """Metrics for an entire codebase."""
    project_name: str
    total_files: int = 0
    
    # Aggregated core metrics
    total_cyclomatic_complexity: int = 0
    average_cyclomatic_complexity: float = 0.0
    total_halstead_volume: float = 0.0
    average_maintainability_index: float = 0.0
    
    # Aggregated lines of code metrics
    total_lines: int = 0
    total_logical_lines: int = 0
    total_source_lines: int = 0
    total_comment_lines: int = 0
    total_blank_lines: int = 0
    
    # Codebase-specific metrics
    total_classes: int = 0
    total_functions: int = 0
    total_imports: int = 0
    total_global_vars: int = 0
    total_interfaces: int = 0
    
    # Language distribution
    language_distribution: Dict[str, int] = field(default_factory=dict)
    
    # File metrics aggregation
    file_metrics: List[FileMetrics] = field(default_factory=list)
    
    # Quality metrics
    dead_code_files: int = 0
    test_files: int = 0
    average_test_coverage: float = 0.0
    
    # Growth tracking
    calculated_at: datetime = field(default_factory=datetime.now)
    git_commit_hash: Optional[str] = None
    
    @property
    def comment_ratio(self) -> float:
        """Overall comment ratio for the codebase."""
        if self.total_lines == 0:
            return 0.0
        return self.total_comment_lines / self.total_lines
    
    @property
    def test_file_ratio(self) -> float:
        """Ratio of test files to total files."""
        if self.total_files == 0:
            return 0.0
        return self.test_files / self.total_files

@dataclass
class MetricsData:
    """Container for all metrics data."""
    codebase_metrics: CodebaseMetrics
    file_metrics: Dict[str, FileMetrics] = field(default_factory=dict)
    class_metrics: Dict[str, List[ClassMetrics]] = field(default_factory=dict)
    function_metrics: Dict[str, List[FunctionMetrics]] = field(default_factory=dict)
    
    # Metadata
    calculation_duration: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def get_file_metrics(self, file_path: str) -> Optional[FileMetrics]:
        """Get metrics for a specific file."""
        return self.file_metrics.get(file_path)
    
    def get_function_metrics(self, file_path: str, function_name: str) -> Optional[FunctionMetrics]:
        """Get metrics for a specific function."""
        file_functions = self.function_metrics.get(file_path, [])
        for func_metrics in file_functions:
            if func_metrics.name == function_name:
                return func_metrics
        return None
    
    def get_class_metrics(self, file_path: str, class_name: str) -> Optional[ClassMetrics]:
        """Get metrics for a specific class."""
        file_classes = self.class_metrics.get(file_path, [])
        for class_metrics in file_classes:
            if class_metrics.name == class_name:
                return class_metrics
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics data to dictionary for serialization."""
        return {
            "codebase_metrics": self.codebase_metrics.__dict__,
            "file_metrics": {k: v.__dict__ for k, v in self.file_metrics.items()},
            "class_metrics": {
                k: [c.__dict__ for c in v] for k, v in self.class_metrics.items()
            },
            "function_metrics": {
                k: [f.__dict__ for f in v] for k, v in self.function_metrics.items()
            },
            "calculation_duration": self.calculation_duration,
            "errors": self.errors,
            "warnings": self.warnings,
        }

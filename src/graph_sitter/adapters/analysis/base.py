"""
Base classes and interfaces for analysis components.

This module provides the foundation for all analysis components in graph-sitter,
ensuring consistent interfaces and standardized behavior across different
analysis types.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from graph_sitter.core.codebase import Codebase


class AnalysisType(Enum):
    """Enumeration of available analysis types."""
    CALL_GRAPH = "call_graph"
    DEAD_CODE = "dead_code"
    DEPENDENCIES = "dependencies"
    METRICS = "metrics"
    FUNCTION_CONTEXT = "function_context"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"


class IssueSeverity(Enum):
    """Enumeration of issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


@dataclass
class AnalysisIssue:
    """Standardized representation of an analysis issue."""
    
    type: str
    severity: IssueSeverity
    description: str
    file: Optional[str] = None
    location: Optional[Union[str, int]] = None
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    rule_id: Optional[str] = None
    suggestion: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert issue to dictionary format."""
        return {
            'type': self.type,
            'severity': self.severity.value,
            'description': self.description,
            'file': self.file,
            'location': self.location,
            'line_number': self.line_number,
            'column_number': self.column_number,
            'rule_id': self.rule_id,
            'suggestion': self.suggestion,
            'metadata': self.metadata or {}
        }


@dataclass
class AnalysisMetric:
    """Standardized representation of an analysis metric."""
    
    name: str
    value: Union[int, float, str]
    unit: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary format."""
        return {
            'name': self.name,
            'value': self.value,
            'unit': self.unit,
            'description': self.description,
            'category': self.category
        }


@dataclass
class AnalysisResult:
    """Standardized result container for analysis operations."""
    
    analysis_type: AnalysisType
    timestamp: datetime
    issues: List[AnalysisIssue]
    metrics: List[AnalysisMetric]
    raw_data: Dict[str, Any]
    recommendations: List[str]
    execution_time: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            'analysis_type': self.analysis_type.value,
            'timestamp': self.timestamp.isoformat(),
            'issues': [issue.to_dict() for issue in self.issues],
            'metrics': [metric.to_dict() for metric in self.metrics],
            'raw_data': self.raw_data,
            'recommendations': self.recommendations,
            'execution_time': self.execution_time,
            'success': self.success,
            'error_message': self.error_message
        }
    
    def get_issues_by_severity(self, severity: IssueSeverity) -> List[AnalysisIssue]:
        """Get issues filtered by severity level."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_metrics_by_category(self, category: str) -> List[AnalysisMetric]:
        """Get metrics filtered by category."""
        return [metric for metric in self.metrics if metric.category == category]


class BaseAnalyzer(ABC):
    """
    Abstract base class for all analysis components.
    
    This class defines the standard interface that all analyzers must implement,
    ensuring consistency across different analysis types.
    """
    
    def __init__(self, codebase: Codebase, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the analyzer.
        
        Args:
            codebase: The codebase to analyze
            config: Optional configuration for the analyzer
        """
        self.codebase = codebase
        self.config = config or {}
        self.analysis_type = self._get_analysis_type()
    
    @abstractmethod
    def _get_analysis_type(self) -> AnalysisType:
        """Return the analysis type for this analyzer."""
        pass
    
    @abstractmethod
    def analyze(self) -> AnalysisResult:
        """
        Perform the analysis and return results.
        
        Returns:
            AnalysisResult containing issues, metrics, and recommendations
        """
        pass
    
    def validate_codebase(self) -> bool:
        """
        Validate that the codebase is suitable for this analysis.
        
        Returns:
            True if the codebase can be analyzed, False otherwise
        """
        return self.codebase is not None
    
    def get_supported_languages(self) -> List[str]:
        """
        Get the list of programming languages supported by this analyzer.
        
        Returns:
            List of supported language names
        """
        return ["python", "typescript", "javascript"]  # Default support
    
    def create_issue(
        self,
        issue_type: str,
        severity: IssueSeverity,
        description: str,
        **kwargs
    ) -> AnalysisIssue:
        """
        Create a standardized analysis issue.
        
        Args:
            issue_type: Type of the issue
            severity: Severity level
            description: Human-readable description
            **kwargs: Additional issue properties
            
        Returns:
            AnalysisIssue instance
        """
        return AnalysisIssue(
            type=issue_type,
            severity=severity,
            description=description,
            **kwargs
        )
    
    def create_metric(
        self,
        name: str,
        value: Union[int, float, str],
        **kwargs
    ) -> AnalysisMetric:
        """
        Create a standardized analysis metric.
        
        Args:
            name: Name of the metric
            value: Metric value
            **kwargs: Additional metric properties
            
        Returns:
            AnalysisMetric instance
        """
        return AnalysisMetric(
            name=name,
            value=value,
            **kwargs
        )
    
    def create_result(
        self,
        issues: List[AnalysisIssue],
        metrics: List[AnalysisMetric],
        raw_data: Dict[str, Any],
        recommendations: List[str],
        **kwargs
    ) -> AnalysisResult:
        """
        Create a standardized analysis result.
        
        Args:
            issues: List of issues found
            metrics: List of metrics calculated
            raw_data: Raw analysis data
            recommendations: List of recommendations
            **kwargs: Additional result properties
            
        Returns:
            AnalysisResult instance
        """
        return AnalysisResult(
            analysis_type=self.analysis_type,
            timestamp=datetime.now(),
            issues=issues,
            metrics=metrics,
            raw_data=raw_data,
            recommendations=recommendations,
            **kwargs
        )


class StructuralAnalyzer(BaseAnalyzer):
    """Base class for structural analysis (call graphs, dependencies, etc.)."""
    
    def get_supported_languages(self) -> List[str]:
        return ["python", "typescript", "javascript", "java", "cpp"]


class QualityAnalyzer(BaseAnalyzer):
    """Base class for code quality analysis (metrics, style, etc.)."""
    
    def get_supported_languages(self) -> List[str]:
        return ["python", "typescript", "javascript"]


class SecurityAnalyzer(BaseAnalyzer):
    """Base class for security analysis."""
    
    def get_supported_languages(self) -> List[str]:
        return ["python", "typescript", "javascript", "java"]


class PerformanceAnalyzer(BaseAnalyzer):
    """Base class for performance analysis."""
    
    def get_supported_languages(self) -> List[str]:
        return ["python", "typescript", "javascript", "cpp", "java"]


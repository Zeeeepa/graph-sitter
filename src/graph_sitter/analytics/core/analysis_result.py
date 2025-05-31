"""
Data structures for analysis results and reports.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import json


class Severity(Enum):
    """Severity levels for analysis findings."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingType(Enum):
    """Types of analysis findings."""
    COMPLEXITY = "complexity"
    PERFORMANCE = "performance"
    SECURITY = "security"
    DEAD_CODE = "dead_code"
    DEPENDENCY = "dependency"
    MAINTAINABILITY = "maintainability"
    BUG_RISK = "bug_risk"


@dataclass
class Finding:
    """Represents a single analysis finding."""
    
    type: FindingType
    severity: Severity
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    rule_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary for serialization."""
        return {
            "type": self.type.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "column_number": self.column_number,
            "code_snippet": self.code_snippet,
            "recommendation": self.recommendation,
            "rule_id": self.rule_id,
            "metadata": self.metadata
        }


@dataclass
class AnalysisMetrics:
    """Metrics collected during analysis."""
    
    # General metrics
    files_analyzed: int = 0
    lines_analyzed: int = 0
    symbols_analyzed: int = 0
    execution_time: float = 0.0
    
    # Issue counts by severity
    critical_issues: int = 0
    high_issues: int = 0
    medium_issues: int = 0
    low_issues: int = 0
    
    # Quality metrics
    quality_score: Optional[float] = None  # 0-100 scale
    maintainability_index: Optional[float] = None
    technical_debt_ratio: Optional[float] = None
    
    # Specific metrics (populated by individual analyzers)
    complexity_metrics: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    security_metrics: Dict[str, Any] = field(default_factory=dict)
    dead_code_metrics: Dict[str, Any] = field(default_factory=dict)
    dependency_metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_issues(self) -> int:
        """Total number of issues found."""
        return self.critical_issues + self.high_issues + self.medium_issues + self.low_issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            "files_analyzed": self.files_analyzed,
            "lines_analyzed": self.lines_analyzed,
            "symbols_analyzed": self.symbols_analyzed,
            "execution_time": self.execution_time,
            "critical_issues": self.critical_issues,
            "high_issues": self.high_issues,
            "medium_issues": self.medium_issues,
            "low_issues": self.low_issues,
            "total_issues": self.total_issues,
            "quality_score": self.quality_score,
            "maintainability_index": self.maintainability_index,
            "technical_debt_ratio": self.technical_debt_ratio,
            "complexity_metrics": self.complexity_metrics,
            "performance_metrics": self.performance_metrics,
            "security_metrics": self.security_metrics,
            "dead_code_metrics": self.dead_code_metrics,
            "dependency_metrics": self.dependency_metrics
        }


@dataclass
class AnalysisResult:
    """Result from a single analyzer."""
    
    analyzer_name: str
    status: str  # "completed", "failed", "partial"
    findings: List[Finding] = field(default_factory=list)
    metrics: AnalysisMetrics = field(default_factory=AnalysisMetrics)
    recommendations: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def add_finding(self, finding: Finding):
        """Add a finding to the result."""
        self.findings.append(finding)
        
        # Update metrics
        if finding.severity == Severity.CRITICAL:
            self.metrics.critical_issues += 1
        elif finding.severity == Severity.HIGH:
            self.metrics.high_issues += 1
        elif finding.severity == Severity.MEDIUM:
            self.metrics.medium_issues += 1
        elif finding.severity == Severity.LOW:
            self.metrics.low_issues += 1
    
    def get_findings_by_severity(self, severity: Severity) -> List[Finding]:
        """Get all findings of a specific severity."""
        return [f for f in self.findings if f.severity == severity]
    
    def get_findings_by_type(self, finding_type: FindingType) -> List[Finding]:
        """Get all findings of a specific type."""
        return [f for f in self.findings if f.type == finding_type]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for serialization."""
        return {
            "analyzer_name": self.analyzer_name,
            "status": self.status,
            "findings": [f.to_dict() for f in self.findings],
            "metrics": self.metrics.to_dict(),
            "recommendations": self.recommendations,
            "error_message": self.error_message,
            "warnings": self.warnings
        }


@dataclass
class AnalysisReport:
    """Comprehensive analysis report containing all results."""
    
    codebase_name: str
    analysis_results: Dict[str, AnalysisResult]
    execution_time: float
    total_files_analyzed: int
    total_lines_analyzed: int
    overall_quality_score: float
    summary_findings: List[Finding] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    timestamp: float = 0.0
    
    @property
    def total_findings(self) -> int:
        """Total number of findings across all analyzers."""
        return sum(len(result.findings) for result in self.analysis_results.values())
    
    @property
    def critical_findings(self) -> List[Finding]:
        """All critical findings across analyzers."""
        critical = []
        for result in self.analysis_results.values():
            critical.extend(result.get_findings_by_severity(Severity.CRITICAL))
        return critical
    
    @property
    def high_findings(self) -> List[Finding]:
        """All high severity findings across analyzers."""
        high = []
        for result in self.analysis_results.values():
            high.extend(result.get_findings_by_severity(Severity.HIGH))
        return high
    
    def get_analyzer_result(self, analyzer_name: str) -> Optional[AnalysisResult]:
        """Get result from a specific analyzer."""
        return self.analysis_results.get(analyzer_name)
    
    def get_findings_by_file(self, file_path: str) -> List[Finding]:
        """Get all findings for a specific file."""
        findings = []
        for result in self.analysis_results.values():
            findings.extend([f for f in result.findings if f.file_path == file_path])
        return findings
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for the report."""
        total_critical = sum(result.metrics.critical_issues for result in self.analysis_results.values())
        total_high = sum(result.metrics.high_issues for result in self.analysis_results.values())
        total_medium = sum(result.metrics.medium_issues for result in self.analysis_results.values())
        total_low = sum(result.metrics.low_issues for result in self.analysis_results.values())
        
        return {
            "codebase_name": self.codebase_name,
            "total_files": self.total_files_analyzed,
            "total_lines": self.total_lines_analyzed,
            "execution_time": self.execution_time,
            "overall_quality_score": self.overall_quality_score,
            "total_findings": self.total_findings,
            "critical_issues": total_critical,
            "high_issues": total_high,
            "medium_issues": total_medium,
            "low_issues": total_low,
            "analyzers_run": list(self.analysis_results.keys()),
            "successful_analyzers": [name for name, result in self.analysis_results.items() if result.status == "completed"],
            "failed_analyzers": [name for name, result in self.analysis_results.items() if result.status == "failed"]
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return {
            "codebase_name": self.codebase_name,
            "analysis_results": {name: result.to_dict() for name, result in self.analysis_results.items()},
            "execution_time": self.execution_time,
            "total_files_analyzed": self.total_files_analyzed,
            "total_lines_analyzed": self.total_lines_analyzed,
            "overall_quality_score": self.overall_quality_score,
            "summary_findings": [f.to_dict() for f in self.summary_findings],
            "recommendations": self.recommendations,
            "timestamp": self.timestamp,
            "summary_stats": self.get_summary_stats()
        }
    
    def to_json(self, indent: int = 2) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    def save_to_file(self, file_path: str, format: str = "json"):
        """Save report to file in specified format."""
        if format.lower() == "json":
            with open(file_path, 'w') as f:
                f.write(self.to_json())
        else:
            raise ValueError(f"Unsupported format: {format}")


"""
Issue Detector - Comprehensive issue detection and categorization system
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.adapters.analysis.enhanced_analysis import AnalysisReport

logger = logging.getLogger(__name__)


class IssueSeverity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(Enum):
    """Issue types."""
    ERROR = "error"
    WARNING = "warning"
    SUGGESTION = "suggestion"
    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    ARCHITECTURE = "architecture"


@dataclass
class CodeIssue:
    """Represents a detected code issue."""
    id: str
    title: str
    description: str
    severity: IssueSeverity
    issue_type: IssueType
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class IssueDetector:
    """
    Comprehensive issue detection system.
    
    Detects various types of code issues including:
    - Dead code
    - Circular dependencies
    - High complexity functions
    - Security vulnerabilities
    - Performance bottlenecks
    - Documentation issues
    - Architectural violations
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize the issue detector."""
        self.codebase = codebase
        self.detected_issues: List[CodeIssue] = []
    
    def detect_comprehensive_issues(self, analysis_report: AnalysisReport) -> List[Dict[str, Any]]:
        """
        Detect comprehensive issues from analysis report.
        
        Args:
            analysis_report: The analysis report to process
            
        Returns:
            List of detected issues
        """
        self.detected_issues = []
        
        # Detect different types of issues
        self._detect_complexity_issues(analysis_report)
        self._detect_dead_code_issues(analysis_report)
        self._detect_dependency_issues(analysis_report)
        self._detect_documentation_issues(analysis_report)
        self._detect_security_issues(analysis_report)
        self._detect_performance_issues(analysis_report)
        self._detect_architectural_issues(analysis_report)
        
        # Convert to dict format for compatibility
        return [self._issue_to_dict(issue) for issue in self.detected_issues]
    
    def _detect_complexity_issues(self, analysis_report: AnalysisReport):
        """Detect high complexity functions and classes."""
        function_analysis = analysis_report.function_analysis
        
        for func_data in function_analysis:
            complexity = func_data.get('complexity', 0)
            
            if complexity > 20:
                severity = IssueSeverity.CRITICAL
                suggestion = "Consider breaking this function into smaller, more focused functions."
            elif complexity > 15:
                severity = IssueSeverity.HIGH
                suggestion = "This function is quite complex. Consider refactoring."
            elif complexity > 10:
                severity = IssueSeverity.MEDIUM
                suggestion = "This function has moderate complexity. Review for potential simplification."
            else:
                continue
            
            issue = CodeIssue(
                id=f"complexity_{func_data.get('name', 'unknown')}",
                title=f"High Complexity Function: {func_data.get('name', 'Unknown')}",
                description=f"Function has cyclomatic complexity of {complexity}",
                severity=severity,
                issue_type=IssueType.MAINTAINABILITY,
                file_path=func_data.get('file_path', ''),
                line_number=func_data.get('line_number'),
                function_name=func_data.get('name'),
                suggestion=suggestion,
                metadata={'complexity': complexity}
            )
            self.detected_issues.append(issue)
    
    def _detect_dead_code_issues(self, analysis_report: AnalysisReport):
        """Detect dead code issues."""
        dead_code_analysis = analysis_report.dead_code_analysis
        
        if 'unused_functions' in dead_code_analysis:
            for func_name in dead_code_analysis['unused_functions']:
                issue = CodeIssue(
                    id=f"dead_code_function_{func_name}",
                    title=f"Unused Function: {func_name}",
                    description=f"Function '{func_name}' appears to be unused",
                    severity=IssueSeverity.MEDIUM,
                    issue_type=IssueType.MAINTAINABILITY,
                    file_path="",  # Would need to be populated from analysis
                    function_name=func_name,
                    suggestion="Consider removing this function if it's truly unused, or add documentation explaining its purpose."
                )
                self.detected_issues.append(issue)
        
        if 'unused_classes' in dead_code_analysis:
            for class_name in dead_code_analysis['unused_classes']:
                issue = CodeIssue(
                    id=f"dead_code_class_{class_name}",
                    title=f"Unused Class: {class_name}",
                    description=f"Class '{class_name}' appears to be unused",
                    severity=IssueSeverity.MEDIUM,
                    issue_type=IssueType.MAINTAINABILITY,
                    file_path="",
                    class_name=class_name,
                    suggestion="Consider removing this class if it's truly unused."
                )
                self.detected_issues.append(issue)
    
    def _detect_dependency_issues(self, analysis_report: AnalysisReport):
        """Detect dependency-related issues."""
        dependency_analysis = analysis_report.dependency_analysis
        
        # Circular dependencies
        if 'circular_dependencies' in dependency_analysis:
            for cycle in dependency_analysis['circular_dependencies']:
                cycle_str = " -> ".join(cycle)
                issue = CodeIssue(
                    id=f"circular_dep_{hash(cycle_str)}",
                    title="Circular Dependency Detected",
                    description=f"Circular dependency found: {cycle_str}",
                    severity=IssueSeverity.HIGH,
                    issue_type=IssueType.ARCHITECTURE,
                    file_path="",
                    suggestion="Refactor to break the circular dependency by introducing interfaces or reorganizing modules.",
                    metadata={'cycle': cycle}
                )
                self.detected_issues.append(issue)
        
        # High coupling
        if 'coupling_metrics' in dependency_analysis:
            coupling_metrics = dependency_analysis['coupling_metrics']
            for module, coupling in coupling_metrics.items():
                if coupling > 10:  # Threshold for high coupling
                    issue = CodeIssue(
                        id=f"high_coupling_{module}",
                        title=f"High Coupling: {module}",
                        description=f"Module '{module}' has high coupling ({coupling} dependencies)",
                        severity=IssueSeverity.MEDIUM,
                        issue_type=IssueType.ARCHITECTURE,
                        file_path=module,
                        suggestion="Consider reducing dependencies by using dependency injection or breaking the module into smaller parts."
                    )
                    self.detected_issues.append(issue)
    
    def _detect_documentation_issues(self, analysis_report: AnalysisReport):
        """Detect documentation-related issues."""
        function_analysis = analysis_report.function_analysis
        class_analysis = analysis_report.class_analysis
        
        # Functions without docstrings
        for func_data in function_analysis:
            if not func_data.get('has_docstring', False):
                issue = CodeIssue(
                    id=f"no_docstring_func_{func_data.get('name', 'unknown')}",
                    title=f"Missing Docstring: {func_data.get('name', 'Unknown')}",
                    description=f"Function '{func_data.get('name', 'Unknown')}' lacks documentation",
                    severity=IssueSeverity.LOW,
                    issue_type=IssueType.DOCUMENTATION,
                    file_path=func_data.get('file_path', ''),
                    line_number=func_data.get('line_number'),
                    function_name=func_data.get('name'),
                    suggestion="Add a docstring explaining the function's purpose, parameters, and return value."
                )
                self.detected_issues.append(issue)
        
        # Classes without docstrings
        for class_data in class_analysis:
            if not class_data.get('has_docstring', False):
                issue = CodeIssue(
                    id=f"no_docstring_class_{class_data.get('name', 'unknown')}",
                    title=f"Missing Docstring: {class_data.get('name', 'Unknown')}",
                    description=f"Class '{class_data.get('name', 'Unknown')}' lacks documentation",
                    severity=IssueSeverity.LOW,
                    issue_type=IssueType.DOCUMENTATION,
                    file_path=class_data.get('file_path', ''),
                    line_number=class_data.get('line_number'),
                    class_name=class_data.get('name'),
                    suggestion="Add a docstring explaining the class's purpose and usage."
                )
                self.detected_issues.append(issue)
    
    def _detect_security_issues(self, analysis_report: AnalysisReport):
        """Detect potential security issues."""
        # This is a simplified implementation - in practice, you'd want more sophisticated security analysis
        function_analysis = analysis_report.function_analysis
        
        security_patterns = [
            (r'eval\s*\(', "Use of eval() function", "Avoid using eval() as it can execute arbitrary code."),
            (r'exec\s*\(', "Use of exec() function", "Avoid using exec() as it can execute arbitrary code."),
            (r'subprocess\.call\s*\(.*shell\s*=\s*True', "Shell injection risk", "Avoid using shell=True in subprocess calls."),
            (r'sql.*\+.*', "Potential SQL injection", "Use parameterized queries instead of string concatenation."),
        ]
        
        for func_data in function_analysis:
            func_code = func_data.get('code', '')
            
            for pattern, title, suggestion in security_patterns:
                if re.search(pattern, func_code, re.IGNORECASE):
                    issue = CodeIssue(
                        id=f"security_{func_data.get('name', 'unknown')}_{hash(pattern)}",
                        title=f"Security Issue: {title}",
                        description=f"Potential security issue in function '{func_data.get('name', 'Unknown')}'",
                        severity=IssueSeverity.HIGH,
                        issue_type=IssueType.SECURITY,
                        file_path=func_data.get('file_path', ''),
                        line_number=func_data.get('line_number'),
                        function_name=func_data.get('name'),
                        suggestion=suggestion
                    )
                    self.detected_issues.append(issue)
    
    def _detect_performance_issues(self, analysis_report: AnalysisReport):
        """Detect potential performance issues."""
        function_analysis = analysis_report.function_analysis
        
        for func_data in function_analysis:
            # Check for long functions (potential performance issue)
            lines_of_code = func_data.get('lines_of_code', 0)
            if lines_of_code > 100:
                issue = CodeIssue(
                    id=f"long_function_{func_data.get('name', 'unknown')}",
                    title=f"Long Function: {func_data.get('name', 'Unknown')}",
                    description=f"Function has {lines_of_code} lines of code",
                    severity=IssueSeverity.MEDIUM,
                    issue_type=IssueType.PERFORMANCE,
                    file_path=func_data.get('file_path', ''),
                    line_number=func_data.get('line_number'),
                    function_name=func_data.get('name'),
                    suggestion="Consider breaking this function into smaller functions for better performance and maintainability."
                )
                self.detected_issues.append(issue)
    
    def _detect_architectural_issues(self, analysis_report: AnalysisReport):
        """Detect architectural issues."""
        # Check for god classes (classes with too many methods)
        class_analysis = analysis_report.class_analysis
        
        for class_data in class_analysis:
            method_count = class_data.get('method_count', 0)
            if method_count > 20:
                issue = CodeIssue(
                    id=f"god_class_{class_data.get('name', 'unknown')}",
                    title=f"God Class: {class_data.get('name', 'Unknown')}",
                    description=f"Class has {method_count} methods, which may indicate it has too many responsibilities",
                    severity=IssueSeverity.MEDIUM,
                    issue_type=IssueType.ARCHITECTURE,
                    file_path=class_data.get('file_path', ''),
                    line_number=class_data.get('line_number'),
                    class_name=class_data.get('name'),
                    suggestion="Consider breaking this class into smaller, more focused classes following the Single Responsibility Principle."
                )
                self.detected_issues.append(issue)
    
    def _issue_to_dict(self, issue: CodeIssue) -> Dict[str, Any]:
        """Convert CodeIssue to dictionary format."""
        return {
            'id': issue.id,
            'title': issue.title,
            'description': issue.description,
            'severity': issue.severity.value,
            'type': issue.issue_type.value,
            'file_path': issue.file_path,
            'line_number': issue.line_number,
            'column_number': issue.column_number,
            'function_name': issue.function_name,
            'class_name': issue.class_name,
            'suggestion': issue.suggestion,
            'code_snippet': issue.code_snippet,
            'metadata': issue.metadata or {}
        }
    
    def get_issues_by_severity(self, severity: IssueSeverity) -> List[CodeIssue]:
        """Get issues filtered by severity."""
        return [issue for issue in self.detected_issues if issue.severity == severity]
    
    def get_issues_by_type(self, issue_type: IssueType) -> List[CodeIssue]:
        """Get issues filtered by type."""
        return [issue for issue in self.detected_issues if issue.issue_type == issue_type]
    
    def get_critical_issues(self) -> List[CodeIssue]:
        """Get all critical issues."""
        return self.get_issues_by_severity(IssueSeverity.CRITICAL)


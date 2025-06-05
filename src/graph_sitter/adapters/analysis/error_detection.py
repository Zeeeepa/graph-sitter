"""
Comprehensive Error Detection and Analysis System

This module provides advanced error detection capabilities including:
- Syntax error detection
- Runtime error prediction
- Logical error identification
- Performance issue detection
- Security vulnerability scanning
"""

import ast
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
from pathlib import Path

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class

logger = logging.getLogger(__name__)


@dataclass
class ErrorInstance:
    """Represents a detected error or issue."""
    error_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    location: Dict[str, Any]  # file, line, column, function, class
    message: str
    description: str
    suggestion: Optional[str] = None
    blast_radius: Optional[List[str]] = None
    impact_score: float = 0.0


@dataclass
class ErrorAnalysisResult:
    """Complete error analysis result."""
    codebase_id: str
    total_errors: int
    errors_by_type: Dict[str, List[ErrorInstance]]
    errors_by_severity: Dict[str, List[ErrorInstance]]
    blast_radius_map: Dict[str, List[str]]
    impact_assessment: Dict[str, Any]
    resolution_priorities: List[ErrorInstance]
    recommendations: List[str]


class ErrorDetector:
    """Comprehensive error detection system."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self.errors: List[ErrorInstance] = []
        
        # Error patterns for different types
        self.syntax_patterns = [
            r'SyntaxError',
            r'IndentationError',
            r'TabError'
        ]
        
        self.runtime_patterns = [
            r'NameError',
            r'AttributeError',
            r'KeyError',
            r'IndexError',
            r'TypeError',
            r'ValueError'
        ]
        
        self.security_patterns = [
            r'eval\s*\(',
            r'exec\s*\(',
            r'__import__\s*\(',
            r'input\s*\(',  # In Python 2 context
            r'pickle\.loads',
            r'subprocess\.call.*shell=True'
        ]
        
        self.performance_patterns = [
            r'for.*in.*range\(len\(',  # Inefficient iteration
            r'\.append\(.*\)\s*$',     # List append in loop (potential)
            r'time\.sleep\(',           # Blocking sleep calls
            r'while\s+True:',          # Infinite loops
        ]
    
    def detect_all_errors(self) -> ErrorAnalysisResult:
        """Perform comprehensive error detection."""
        logger.info("Starting comprehensive error detection")
        
        self.errors = []
        
        # Run all detection methods
        self._detect_syntax_errors()
        self._detect_runtime_errors()
        self._detect_logical_errors()
        self._detect_performance_issues()
        self._detect_security_vulnerabilities()
        self._detect_code_quality_issues()
        
        # Analyze results
        return self._create_analysis_result()
    
    def _detect_syntax_errors(self):
        """Detect syntax errors in Python files."""
        for file_path in self.codebase.files:
            if not str(file_path).endswith('.py'):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to parse with AST
                try:
                    ast.parse(content)
                except SyntaxError as e:
                    error = ErrorInstance(
                        error_type='syntax_error',
                        severity='high',
                        location={
                            'file': str(file_path),
                            'line': e.lineno,
                            'column': e.offset,
                            'function': None,
                            'class': None
                        },
                        message=f"Syntax Error: {e.msg}",
                        description=f"Python syntax error at line {e.lineno}",
                        suggestion="Fix the syntax error according to Python grammar rules"
                    )
                    self.errors.append(error)
                    
            except Exception as e:
                logger.warning(f"Could not analyze file {file_path}: {e}")
    
    def _detect_runtime_errors(self):
        """Predict potential runtime errors."""
        for function in self.codebase.functions:
            self._analyze_function_for_runtime_errors(function)
    
    def _analyze_function_for_runtime_errors(self, function: Function):
        """Analyze a function for potential runtime errors."""
        if not hasattr(function, 'source_code'):
            return
            
        source = function.source_code
        
        # Check for common runtime error patterns
        patterns = [
            (r'(\w+)\[(\w+)\]', 'IndexError/KeyError risk'),
            (r'(\w+)\.(\w+)', 'AttributeError risk'),
            (r'int\((\w+)\)', 'ValueError risk in type conversion'),
            (r'float\((\w+)\)', 'ValueError risk in type conversion'),
            (r'open\([^)]+\)', 'FileNotFoundError risk'),
        ]
        
        for pattern, description in patterns:
            matches = re.finditer(pattern, source)
            for match in matches:
                error = ErrorInstance(
                    error_type='runtime_prediction',
                    severity='medium',
                    location={
                        'file': function.file_path,
                        'line': function.start_line + source[:match.start()].count('\n'),
                        'column': match.start(),
                        'function': function.name,
                        'class': getattr(function, 'class_name', None)
                    },
                    message=f"Potential runtime error: {description}",
                    description=f"Code pattern that may cause runtime errors: {match.group()}",
                    suggestion="Add error handling (try/except) or input validation"
                )
                self.errors.append(error)
    
    def _detect_logical_errors(self):
        """Detect logical errors and code smells."""
        for function in self.codebase.functions:
            self._analyze_function_for_logical_errors(function)
    
    def _analyze_function_for_logical_errors(self, function: Function):
        """Analyze function for logical errors."""
        if not hasattr(function, 'source_code'):
            return
            
        source = function.source_code
        
        # Check for logical issues
        logical_patterns = [
            (r'if\s+(\w+)\s*==\s*True:', 'Use "if variable:" instead of "if variable == True:"'),
            (r'if\s+(\w+)\s*==\s*False:', 'Use "if not variable:" instead of "if variable == False:"'),
            (r'if\s+len\((\w+)\)\s*>\s*0:', 'Use "if container:" instead of "if len(container) > 0:"'),
            (r'except\s*:', 'Bare except clause catches all exceptions'),
            (r'return\s+None', 'Explicit return None (may be unnecessary)'),
        ]
        
        for pattern, description in logical_patterns:
            matches = re.finditer(pattern, source)
            for match in matches:
                error = ErrorInstance(
                    error_type='logical_issue',
                    severity='low',
                    location={
                        'file': function.file_path,
                        'line': function.start_line + source[:match.start()].count('\n'),
                        'column': match.start(),
                        'function': function.name,
                        'class': getattr(function, 'class_name', None)
                    },
                    message=f"Code smell: {description}",
                    description=f"Logical issue or code smell detected: {match.group()}",
                    suggestion=description
                )
                self.errors.append(error)
    
    def _detect_performance_issues(self):
        """Detect performance-related issues."""
        for function in self.codebase.functions:
            self._analyze_function_for_performance(function)
    
    def _analyze_function_for_performance(self, function: Function):
        """Analyze function for performance issues."""
        if not hasattr(function, 'source_code'):
            return
            
        source = function.source_code
        
        # Check complexity
        if hasattr(function, 'complexity') and function.complexity > 15:
            error = ErrorInstance(
                error_type='performance_issue',
                severity='medium',
                location={
                    'file': function.file_path,
                    'line': function.start_line,
                    'column': 0,
                    'function': function.name,
                    'class': getattr(function, 'class_name', None)
                },
                message=f"High complexity function (complexity: {function.complexity})",
                description="Function has high cyclomatic complexity which may impact performance and maintainability",
                suggestion="Consider breaking this function into smaller, more focused functions"
            )
            self.errors.append(error)
        
        # Check for performance anti-patterns
        perf_patterns = [
            (r'for\s+\w+\s+in\s+range\(len\([^)]+\)\):', 'Inefficient iteration pattern'),
            (r'\.append\([^)]+\)\s*$', 'Potential inefficient list building'),
            (r'time\.sleep\([^)]+\)', 'Blocking sleep call'),
            (r'while\s+True\s*:', 'Infinite loop detected'),
        ]
        
        for pattern, description in perf_patterns:
            matches = re.finditer(pattern, source, re.MULTILINE)
            for match in matches:
                error = ErrorInstance(
                    error_type='performance_issue',
                    severity='medium',
                    location={
                        'file': function.file_path,
                        'line': function.start_line + source[:match.start()].count('\n'),
                        'column': match.start(),
                        'function': function.name,
                        'class': getattr(function, 'class_name', None)
                    },
                    message=f"Performance issue: {description}",
                    description=f"Performance anti-pattern detected: {match.group()}",
                    suggestion=self._get_performance_suggestion(pattern)
                )
                self.errors.append(error)
    
    def _detect_security_vulnerabilities(self):
        """Detect potential security vulnerabilities."""
        for function in self.codebase.functions:
            self._analyze_function_for_security(function)
    
    def _analyze_function_for_security(self, function: Function):
        """Analyze function for security vulnerabilities."""
        if not hasattr(function, 'source_code'):
            return
            
        source = function.source_code
        
        # Check for security issues
        security_patterns = [
            (r'eval\s*\(', 'Use of eval() is dangerous'),
            (r'exec\s*\(', 'Use of exec() is dangerous'),
            (r'pickle\.loads\s*\(', 'Pickle deserialization can be unsafe'),
            (r'subprocess\.call\([^)]*shell=True', 'Shell injection vulnerability'),
            (r'os\.system\s*\(', 'Command injection vulnerability'),
        ]
        
        for pattern, description in security_patterns:
            matches = re.finditer(pattern, source)
            for match in matches:
                error = ErrorInstance(
                    error_type='security_vulnerability',
                    severity='high',
                    location={
                        'file': function.file_path,
                        'line': function.start_line + source[:match.start()].count('\n'),
                        'column': match.start(),
                        'function': function.name,
                        'class': getattr(function, 'class_name', None)
                    },
                    message=f"Security vulnerability: {description}",
                    description=f"Potential security issue detected: {match.group()}",
                    suggestion=self._get_security_suggestion(pattern)
                )
                self.errors.append(error)
    
    def _detect_code_quality_issues(self):
        """Detect code quality issues."""
        for function in self.codebase.functions:
            self._analyze_function_for_quality(function)
    
    def _analyze_function_for_quality(self, function: Function):
        """Analyze function for code quality issues."""
        if not hasattr(function, 'source_code'):
            return
            
        source = function.source_code
        lines = source.split('\n')
        
        # Check function length
        if len(lines) > 50:
            error = ErrorInstance(
                error_type='code_quality',
                severity='low',
                location={
                    'file': function.file_path,
                    'line': function.start_line,
                    'column': 0,
                    'function': function.name,
                    'class': getattr(function, 'class_name', None)
                },
                message=f"Long function ({len(lines)} lines)",
                description="Function is longer than recommended (50+ lines)",
                suggestion="Consider breaking this function into smaller, more focused functions"
            )
            self.errors.append(error)
        
        # Check for missing docstrings
        if not re.search(r'""".*?"""', source, re.DOTALL) and not re.search(r"'''.*?'''", source, re.DOTALL):
            error = ErrorInstance(
                error_type='code_quality',
                severity='low',
                location={
                    'file': function.file_path,
                    'line': function.start_line,
                    'column': 0,
                    'function': function.name,
                    'class': getattr(function, 'class_name', None)
                },
                message="Missing docstring",
                description="Function lacks documentation",
                suggestion="Add a docstring to document the function's purpose, parameters, and return value"
            )
            self.errors.append(error)
    
    def _get_performance_suggestion(self, pattern: str) -> str:
        """Get performance improvement suggestion for a pattern."""
        suggestions = {
            r'for\s+\w+\s+in\s+range\(len\([^)]+\)\):': 'Use "for item in container:" instead of "for i in range(len(container)):"',
            r'\.append\([^)]+\)\s*$': 'Consider using list comprehension or pre-allocating list size',
            r'time\.sleep\([^)]+\)': 'Consider using async/await or threading for non-blocking operations',
            r'while\s+True\s*:': 'Ensure loop has proper exit conditions to prevent infinite execution',
        }
        
        for pat, suggestion in suggestions.items():
            if pat == pattern:
                return suggestion
        
        return "Review for performance optimization opportunities"
    
    def _get_security_suggestion(self, pattern: str) -> str:
        """Get security improvement suggestion for a pattern."""
        suggestions = {
            r'eval\s*\(': 'Avoid eval(). Use ast.literal_eval() for safe evaluation or alternative approaches',
            r'exec\s*\(': 'Avoid exec(). Consider alternative approaches like importlib or configuration files',
            r'pickle\.loads\s*\(': 'Use safer serialization formats like JSON, or validate pickle data sources',
            r'subprocess\.call\([^)]*shell=True': 'Avoid shell=True. Use list arguments and validate inputs',
            r'os\.system\s*\(': 'Use subprocess module with proper input validation instead of os.system()',
        }
        
        for pat, suggestion in suggestions.items():
            if pat == pattern:
                return suggestion
        
        return "Review for security implications and implement proper input validation"
    
    def _create_analysis_result(self) -> ErrorAnalysisResult:
        """Create comprehensive error analysis result."""
        # Group errors by type
        errors_by_type = {}
        for error in self.errors:
            if error.error_type not in errors_by_type:
                errors_by_type[error.error_type] = []
            errors_by_type[error.error_type].append(error)
        
        # Group errors by severity
        errors_by_severity = {}
        for error in self.errors:
            if error.severity not in errors_by_severity:
                errors_by_severity[error.severity] = []
            errors_by_severity[error.severity].append(error)
        
        # Calculate blast radius and impact
        blast_radius_map = self._calculate_blast_radius()
        impact_assessment = self._assess_impact()
        
        # Prioritize resolution
        resolution_priorities = self._prioritize_errors()
        
        # Generate recommendations
        recommendations = self._generate_recommendations()
        
        return ErrorAnalysisResult(
            codebase_id=getattr(self.codebase, 'id', 'unknown'),
            total_errors=len(self.errors),
            errors_by_type=errors_by_type,
            errors_by_severity=errors_by_severity,
            blast_radius_map=blast_radius_map,
            impact_assessment=impact_assessment,
            resolution_priorities=resolution_priorities,
            recommendations=recommendations
        )
    
    def _calculate_blast_radius(self) -> Dict[str, List[str]]:
        """Calculate blast radius for each error."""
        blast_radius_map = {}
        
        for error in self.errors:
            error_id = f"{error.location['file']}:{error.location['line']}"
            affected_components = []
            
            # Find components that might be affected
            if error.location.get('function'):
                # Find functions that call this function
                affected_components.extend(self._find_function_callers(error.location['function']))
            
            if error.location.get('class'):
                # Find classes that inherit or use this class
                affected_components.extend(self._find_class_dependencies(error.location['class']))
            
            blast_radius_map[error_id] = affected_components
            error.blast_radius = affected_components
        
        return blast_radius_map
    
    def _find_function_callers(self, function_name: str) -> List[str]:
        """Find functions that call the given function."""
        callers = []
        
        for function in self.codebase.functions:
            if hasattr(function, 'source_code') and function_name in function.source_code:
                callers.append(f"{function.file_path}:{function.name}")
        
        return callers
    
    def _find_class_dependencies(self, class_name: str) -> List[str]:
        """Find classes and functions that depend on the given class."""
        dependencies = []
        
        # Check functions for class usage
        for function in self.codebase.functions:
            if hasattr(function, 'source_code') and class_name in function.source_code:
                dependencies.append(f"{function.file_path}:{function.name}")
        
        # Check classes for inheritance
        for cls in self.codebase.classes:
            if hasattr(cls, 'base_classes') and class_name in cls.base_classes:
                dependencies.append(f"{cls.file_path}:{cls.name}")
        
        return dependencies
    
    def _assess_impact(self) -> Dict[str, Any]:
        """Assess the overall impact of detected errors."""
        impact = {
            'critical_issues': len([e for e in self.errors if e.severity == 'critical']),
            'high_issues': len([e for e in self.errors if e.severity == 'high']),
            'medium_issues': len([e for e in self.errors if e.severity == 'medium']),
            'low_issues': len([e for e in self.errors if e.severity == 'low']),
            'security_vulnerabilities': len([e for e in self.errors if e.error_type == 'security_vulnerability']),
            'performance_issues': len([e for e in self.errors if e.error_type == 'performance_issue']),
            'maintainability_score': self._calculate_maintainability_score(),
            'risk_level': self._calculate_risk_level()
        }
        
        return impact
    
    def _calculate_maintainability_score(self) -> float:
        """Calculate maintainability score (0-100)."""
        total_functions = len(list(self.codebase.functions))
        if total_functions == 0:
            return 100.0
        
        # Start with perfect score
        score = 100.0
        
        # Deduct for various issues
        quality_issues = len([e for e in self.errors if e.error_type == 'code_quality'])
        logical_issues = len([e for e in self.errors if e.error_type == 'logical_issue'])
        performance_issues = len([e for e in self.errors if e.error_type == 'performance_issue'])
        
        # Calculate deductions
        score -= (quality_issues / total_functions) * 30
        score -= (logical_issues / total_functions) * 20
        score -= (performance_issues / total_functions) * 25
        
        return max(score, 0.0)
    
    def _calculate_risk_level(self) -> str:
        """Calculate overall risk level."""
        critical_count = len([e for e in self.errors if e.severity == 'critical'])
        high_count = len([e for e in self.errors if e.severity == 'high'])
        security_count = len([e for e in self.errors if e.error_type == 'security_vulnerability'])
        
        if critical_count > 0 or security_count > 2:
            return 'critical'
        elif high_count > 5 or security_count > 0:
            return 'high'
        elif len(self.errors) > 20:
            return 'medium'
        else:
            return 'low'
    
    def _prioritize_errors(self) -> List[ErrorInstance]:
        """Prioritize errors for resolution."""
        # Sort by severity and impact
        severity_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        
        return sorted(self.errors, key=lambda e: (
            severity_order.get(e.severity, 0),
            len(e.blast_radius) if e.blast_radius else 0,
            1 if e.error_type == 'security_vulnerability' else 0
        ), reverse=True)
    
    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Security recommendations
        security_issues = [e for e in self.errors if e.error_type == 'security_vulnerability']
        if security_issues:
            recommendations.append(f"Address {len(security_issues)} security vulnerabilities immediately")
        
        # Performance recommendations
        perf_issues = [e for e in self.errors if e.error_type == 'performance_issue']
        if perf_issues:
            recommendations.append(f"Optimize {len(perf_issues)} performance bottlenecks")
        
        # Code quality recommendations
        quality_issues = [e for e in self.errors if e.error_type == 'code_quality']
        if quality_issues:
            recommendations.append(f"Improve code quality by addressing {len(quality_issues)} issues")
        
        # General recommendations
        if len(self.errors) > 50:
            recommendations.append("Consider implementing automated code quality checks")
        
        recommendations.extend([
            "Implement comprehensive error handling patterns",
            "Add unit tests for critical functions",
            "Set up continuous integration with code quality checks",
            "Consider using static analysis tools like pylint or mypy"
        ])
        
        return recommendations


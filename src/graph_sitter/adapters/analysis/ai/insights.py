"""
AI-Powered Code Insights Module

Generates AI-powered insights and suggestions for code improvement.
Provides automated code analysis and recommendations.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class AIInsightGenerator:
    """Generates AI-powered insights for code analysis."""
    
    def __init__(self):
        self.insight_categories = {
            'code_quality': 'Code Quality Issues',
            'performance': 'Performance Optimizations',
            'maintainability': 'Maintainability Improvements',
            'security': 'Security Considerations',
            'best_practices': 'Best Practice Recommendations',
            'refactoring': 'Refactoring Opportunities'
        }
        
        # Predefined insight patterns (in lieu of actual AI API)
        self.insight_patterns = self._initialize_insight_patterns()
    
    def generate_insights(self, codebase) -> Dict[str, Any]:
        """Generate AI-powered insights for the codebase."""
        try:
            if hasattr(codebase, 'functions'):
                return self._generate_insights_graph_sitter(codebase)
            else:
                return self._generate_insights_ast(codebase)
        except Exception as e:
            logger.error(f"AI insight generation failed: {e}")
            return self._get_default_insights()
    
    def _generate_insights_graph_sitter(self, codebase) -> Dict[str, Any]:
        """Generate insights using graph-sitter data."""
        insights = {
            'summary': self._generate_summary_insights(codebase),
            'code_quality': self._analyze_code_quality(codebase),
            'performance': self._analyze_performance_issues(codebase),
            'maintainability': self._analyze_maintainability(codebase),
            'security': self._analyze_security_issues(codebase),
            'best_practices': self._analyze_best_practices(codebase),
            'refactoring': self._suggest_refactoring(codebase),
            'recommendations': self._generate_recommendations(codebase)
        }
        
        return insights
    
    def _generate_insights_ast(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate insights using AST data."""
        insights = {
            'summary': self._generate_summary_from_ast(file_analyses),
            'code_quality': self._analyze_quality_from_ast(file_analyses),
            'recommendations': self._generate_basic_recommendations(file_analyses)
        }
        
        return insights
    
    def _generate_summary_insights(self, codebase) -> Dict[str, Any]:
        """Generate high-level summary insights."""
        total_functions = len(codebase.functions)
        total_classes = len(codebase.classes)
        total_files = len(codebase.files)
        
        # Calculate complexity distribution
        complexities = [getattr(f, 'complexity', 1) for f in codebase.functions if hasattr(f, 'complexity')]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        
        # Analyze documentation coverage
        documented_functions = sum(1 for f in codebase.functions if hasattr(f, 'docstring') and f.docstring)
        doc_coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 0
        
        return {
            'codebase_health_score': self._calculate_health_score(codebase),
            'key_metrics': {
                'total_files': total_files,
                'total_functions': total_functions,
                'total_classes': total_classes,
                'average_complexity': round(avg_complexity, 2),
                'documentation_coverage': round(doc_coverage, 1)
            },
            'overall_assessment': self._generate_overall_assessment(avg_complexity, doc_coverage),
            'priority_areas': self._identify_priority_areas(codebase)
        }
    
    def _analyze_code_quality(self, codebase) -> List[Dict[str, Any]]:
        """Analyze code quality issues."""
        quality_issues = []
        
        # Analyze functions for quality issues
        for function in codebase.functions:
            issues = self._analyze_function_quality(function)
            quality_issues.extend(issues)
        
        # Analyze classes for quality issues
        for cls in codebase.classes:
            issues = self._analyze_class_quality(cls)
            quality_issues.extend(issues)
        
        return quality_issues
    
    def _analyze_performance_issues(self, codebase) -> List[Dict[str, Any]]:
        """Analyze potential performance issues."""
        performance_issues = []
        
        for function in codebase.functions:
            if hasattr(function, 'source'):
                issues = self._detect_performance_patterns(function)
                performance_issues.extend(issues)
        
        return performance_issues
    
    def _analyze_maintainability(self, codebase) -> List[Dict[str, Any]]:
        """Analyze maintainability issues."""
        maintainability_issues = []
        
        # Check for large functions
        for function in codebase.functions:
            if hasattr(function, 'source'):
                lines = len(function.source.splitlines())
                if lines > 50:
                    maintainability_issues.append({
                        'type': 'large_function',
                        'severity': 'medium',
                        'function': function.name,
                        'file': function.filepath,
                        'line': getattr(function, 'start_line', 0),
                        'message': f"Function '{function.name}' is {lines} lines long - consider breaking it down",
                        'suggestion': "Break this function into smaller, more focused functions",
                        'impact': 'Improves readability and testability'
                    })
        
        # Check for large classes
        for cls in codebase.classes:
            method_count = len(getattr(cls, 'methods', []))
            if method_count > 20:
                maintainability_issues.append({
                    'type': 'large_class',
                    'severity': 'medium',
                    'class': cls.name,
                    'file': cls.filepath,
                    'line': getattr(cls, 'start_line', 0),
                    'message': f"Class '{cls.name}' has {method_count} methods - consider splitting responsibilities",
                    'suggestion': "Apply Single Responsibility Principle and split into smaller classes",
                    'impact': 'Reduces complexity and improves maintainability'
                })
        
        return maintainability_issues
    
    def _analyze_security_issues(self, codebase) -> List[Dict[str, Any]]:
        """Analyze potential security issues."""
        security_issues = []
        
        for function in codebase.functions:
            if hasattr(function, 'source'):
                issues = self._detect_security_patterns(function)
                security_issues.extend(issues)
        
        return security_issues
    
    def _analyze_best_practices(self, codebase) -> List[Dict[str, Any]]:
        """Analyze adherence to best practices."""
        best_practice_issues = []
        
        # Check for missing docstrings
        for function in codebase.functions:
            if not (hasattr(function, 'docstring') and function.docstring):
                if not function.name.startswith('_'):  # Skip private functions
                    best_practice_issues.append({
                        'type': 'missing_docstring',
                        'severity': 'low',
                        'function': function.name,
                        'file': function.filepath,
                        'line': getattr(function, 'start_line', 0),
                        'message': f"Function '{function.name}' lacks documentation",
                        'suggestion': "Add a docstring explaining the function's purpose, parameters, and return value",
                        'impact': 'Improves code documentation and maintainability'
                    })
        
        # Check for type hints
        for function in codebase.functions:
            if not (hasattr(function, 'return_type') and function.return_type):
                if not function.name.startswith('_'):  # Skip private functions
                    best_practice_issues.append({
                        'type': 'missing_type_hints',
                        'severity': 'low',
                        'function': function.name,
                        'file': function.filepath,
                        'line': getattr(function, 'start_line', 0),
                        'message': f"Function '{function.name}' lacks type hints",
                        'suggestion': "Add type hints for parameters and return value",
                        'impact': 'Improves code clarity and enables better IDE support'
                    })
        
        return best_practice_issues
    
    def _suggest_refactoring(self, codebase) -> List[Dict[str, Any]]:
        """Suggest refactoring opportunities."""
        refactoring_suggestions = []
        
        # Detect duplicate code patterns
        function_signatures = defaultdict(list)
        for function in codebase.functions:
            if hasattr(function, 'source'):
                # Simple signature based on parameter count and basic structure
                param_count = len(getattr(function, 'parameters', []))
                line_count = len(function.source.splitlines())
                signature = (param_count, line_count // 10)  # Group by rough size
                function_signatures[signature].append(function)
        
        for signature, functions in function_signatures.items():
            if len(functions) > 2:  # Multiple functions with similar signatures
                refactoring_suggestions.append({
                    'type': 'potential_duplication',
                    'severity': 'medium',
                    'functions': [f.name for f in functions],
                    'files': [f.filepath for f in functions],
                    'message': f"Found {len(functions)} functions with similar structure",
                    'suggestion': "Review these functions for potential code duplication and extract common functionality",
                    'impact': 'Reduces code duplication and improves maintainability'
                })
        
        return refactoring_suggestions
    
    def _generate_recommendations(self, codebase) -> List[Dict[str, Any]]:
        """Generate overall recommendations."""
        recommendations = []
        
        # Calculate metrics for recommendations
        total_functions = len(codebase.functions)
        documented_functions = sum(1 for f in codebase.functions if hasattr(f, 'docstring') and f.docstring)
        doc_coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 0
        
        complexities = [getattr(f, 'complexity', 1) for f in codebase.functions if hasattr(f, 'complexity')]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        high_complexity_count = len([c for c in complexities if c > 10])
        
        # Documentation recommendations
        if doc_coverage < 50:
            recommendations.append({
                'category': 'documentation',
                'priority': 'high',
                'title': 'Improve Documentation Coverage',
                'description': f"Only {doc_coverage:.1f}% of functions have docstrings",
                'action': 'Add docstrings to public functions and classes',
                'benefit': 'Improves code maintainability and team collaboration'
            })
        
        # Complexity recommendations
        if avg_complexity > 8:
            recommendations.append({
                'category': 'complexity',
                'priority': 'high',
                'title': 'Reduce Code Complexity',
                'description': f"Average function complexity is {avg_complexity:.1f}",
                'action': 'Refactor complex functions into smaller, more focused functions',
                'benefit': 'Improves code readability and reduces bug risk'
            })
        
        if high_complexity_count > 0:
            recommendations.append({
                'category': 'complexity',
                'priority': 'medium',
                'title': 'Address High-Complexity Functions',
                'description': f"{high_complexity_count} functions have complexity > 10",
                'action': 'Prioritize refactoring the most complex functions',
                'benefit': 'Reduces maintenance burden and improves testability'
            })
        
        # Testing recommendations
        test_files = [f for f in codebase.files if 'test' in f.filepath.lower()]
        if len(test_files) < len(codebase.files) * 0.2:  # Less than 20% test files
            recommendations.append({
                'category': 'testing',
                'priority': 'medium',
                'title': 'Increase Test Coverage',
                'description': f"Only {len(test_files)} test files found for {len(codebase.files)} source files",
                'action': 'Add unit tests for critical functions and classes',
                'benefit': 'Improves code reliability and enables safer refactoring'
            })
        
        return recommendations
    
    def _analyze_function_quality(self, function) -> List[Dict[str, Any]]:
        """Analyze quality issues in a specific function."""
        issues = []
        
        if hasattr(function, 'source'):
            source = function.source
            
            # Check for magic numbers
            import re
            magic_numbers = re.findall(r'\b(?<![\w.])\d{2,}\b(?![\w.])', source)
            if magic_numbers:
                issues.append({
                    'type': 'magic_numbers',
                    'severity': 'low',
                    'function': function.name,
                    'file': function.filepath,
                    'line': getattr(function, 'start_line', 0),
                    'message': f"Function contains magic numbers: {', '.join(set(magic_numbers))}",
                    'suggestion': "Replace magic numbers with named constants",
                    'impact': 'Improves code readability and maintainability'
                })
            
            # Check for TODO/FIXME comments
            if re.search(r'#.*(?:TODO|FIXME|HACK|XXX)', source, re.IGNORECASE):
                issues.append({
                    'type': 'technical_debt',
                    'severity': 'low',
                    'function': function.name,
                    'file': function.filepath,
                    'line': getattr(function, 'start_line', 0),
                    'message': "Function contains TODO/FIXME comments",
                    'suggestion': "Address technical debt items or create proper issues",
                    'impact': 'Reduces technical debt and improves code quality'
                })
        
        return issues
    
    def _analyze_class_quality(self, cls) -> List[Dict[str, Any]]:
        """Analyze quality issues in a specific class."""
        issues = []
        
        # Check for classes with too many methods
        method_count = len(getattr(cls, 'methods', []))
        if method_count > 15:
            issues.append({
                'type': 'large_class',
                'severity': 'medium',
                'class': cls.name,
                'file': cls.filepath,
                'line': getattr(cls, 'start_line', 0),
                'message': f"Class has {method_count} methods",
                'suggestion': "Consider splitting into smaller, more focused classes",
                'impact': 'Improves adherence to Single Responsibility Principle'
            })
        
        return issues
    
    def _detect_performance_patterns(self, function) -> List[Dict[str, Any]]:
        """Detect potential performance issues in a function."""
        issues = []
        
        if hasattr(function, 'source'):
            source = function.source.lower()
            
            # Check for nested loops
            import re
            loop_count = len(re.findall(r'\bfor\b.*:\s*\n.*\bfor\b', source, re.MULTILINE))
            if loop_count > 0:
                issues.append({
                    'type': 'nested_loops',
                    'severity': 'medium',
                    'function': function.name,
                    'file': function.filepath,
                    'line': getattr(function, 'start_line', 0),
                    'message': "Function contains nested loops",
                    'suggestion': "Consider optimizing nested loops or using more efficient algorithms",
                    'impact': 'Improves performance for large datasets'
                })
            
            # Check for string concatenation in loops
            if 'for' in source and '+=' in source and ('str' in source or '"' in source):
                issues.append({
                    'type': 'string_concatenation_in_loop',
                    'severity': 'low',
                    'function': function.name,
                    'file': function.filepath,
                    'line': getattr(function, 'start_line', 0),
                    'message': "Potential string concatenation in loop",
                    'suggestion': "Use join() or list comprehension for better performance",
                    'impact': 'Improves performance when processing many strings'
                })
        
        return issues
    
    def _detect_security_patterns(self, function) -> List[Dict[str, Any]]:
        """Detect potential security issues in a function."""
        issues = []
        
        if hasattr(function, 'source'):
            source = function.source.lower()
            
            # Check for SQL injection patterns
            if 'sql' in source and ('+' in source or 'format' in source):
                issues.append({
                    'type': 'potential_sql_injection',
                    'severity': 'high',
                    'function': function.name,
                    'file': function.filepath,
                    'line': getattr(function, 'start_line', 0),
                    'message': "Potential SQL injection vulnerability",
                    'suggestion': "Use parameterized queries or ORM methods",
                    'impact': 'Prevents SQL injection attacks'
                })
            
            # Check for hardcoded secrets
            import re
            if re.search(r'(password|secret|key|token)\s*=\s*["\'][^"\']+["\']', source, re.IGNORECASE):
                issues.append({
                    'type': 'hardcoded_secret',
                    'severity': 'high',
                    'function': function.name,
                    'file': function.filepath,
                    'line': getattr(function, 'start_line', 0),
                    'message': "Potential hardcoded secret or password",
                    'suggestion': "Use environment variables or secure configuration",
                    'impact': 'Prevents exposure of sensitive information'
                })
        
        return issues
    
    def _calculate_health_score(self, codebase) -> float:
        """Calculate overall codebase health score."""
        total_functions = len(codebase.functions)
        if total_functions == 0:
            return 100.0
        
        # Documentation score
        documented_functions = sum(1 for f in codebase.functions if hasattr(f, 'docstring') and f.docstring)
        doc_score = (documented_functions / total_functions) * 100
        
        # Complexity score
        complexities = [getattr(f, 'complexity', 1) for f in codebase.functions if hasattr(f, 'complexity')]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 1
        complexity_score = max(0, 100 - (avg_complexity - 1) * 10)
        
        # Size score (penalize very large functions)
        large_functions = sum(1 for f in codebase.functions 
                            if hasattr(f, 'source') and len(f.source.splitlines()) > 50)
        size_score = max(0, 100 - (large_functions / total_functions) * 100)
        
        # Weighted average
        health_score = (doc_score * 0.3 + complexity_score * 0.4 + size_score * 0.3)
        return round(health_score, 1)
    
    def _generate_overall_assessment(self, avg_complexity: float, doc_coverage: float) -> str:
        """Generate overall assessment text."""
        if avg_complexity <= 5 and doc_coverage >= 80:
            return "Excellent: Well-documented codebase with low complexity"
        elif avg_complexity <= 8 and doc_coverage >= 60:
            return "Good: Generally well-maintained with room for improvement"
        elif avg_complexity <= 12 and doc_coverage >= 40:
            return "Fair: Moderate complexity with adequate documentation"
        else:
            return "Needs Attention: High complexity or poor documentation coverage"
    
    def _identify_priority_areas(self, codebase) -> List[str]:
        """Identify priority areas for improvement."""
        areas = []
        
        # Check documentation
        total_functions = len(codebase.functions)
        documented_functions = sum(1 for f in codebase.functions if hasattr(f, 'docstring') and f.docstring)
        doc_coverage = (documented_functions / total_functions * 100) if total_functions > 0 else 0
        
        if doc_coverage < 50:
            areas.append("Documentation")
        
        # Check complexity
        complexities = [getattr(f, 'complexity', 1) for f in codebase.functions if hasattr(f, 'complexity')]
        high_complexity_count = len([c for c in complexities if c > 10])
        
        if high_complexity_count > total_functions * 0.1:  # More than 10% high complexity
            areas.append("Code Complexity")
        
        # Check testing
        test_files = [f for f in codebase.files if 'test' in f.filepath.lower()]
        if len(test_files) < len(codebase.files) * 0.2:
            areas.append("Test Coverage")
        
        return areas or ["Code Quality"]
    
    def _generate_summary_from_ast(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary insights from AST data."""
        total_functions = sum(len(analysis.get('functions', [])) for analysis in file_analyses.values())
        total_classes = sum(len(analysis.get('classes', [])) for analysis in file_analyses.values())
        
        return {
            'key_metrics': {
                'total_files': len(file_analyses),
                'total_functions': total_functions,
                'total_classes': total_classes
            },
            'overall_assessment': "Basic analysis completed (limited without graph-sitter)"
        }
    
    def _analyze_quality_from_ast(self, file_analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze quality from AST data."""
        issues = []
        
        for filepath, analysis in file_analyses.items():
            for func in analysis.get('functions', []):
                if func.get('complexity', 1) > 10:
                    issues.append({
                        'type': 'high_complexity',
                        'severity': 'medium',
                        'function': func.get('name', 'unknown'),
                        'file': filepath,
                        'message': f"Function has high complexity ({func.get('complexity', 1)})",
                        'suggestion': "Consider breaking down into smaller functions"
                    })
        
        return issues
    
    def _generate_basic_recommendations(self, file_analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate basic recommendations from AST data."""
        return [
            {
                'category': 'analysis',
                'priority': 'medium',
                'title': 'Enable Graph-sitter Analysis',
                'description': 'Install graph-sitter for enhanced analysis capabilities',
                'action': 'Install graph-sitter package for deeper code insights',
                'benefit': 'Enables advanced analysis features and AI insights'
            }
        ]
    
    def _initialize_insight_patterns(self) -> Dict[str, Any]:
        """Initialize predefined insight patterns."""
        return {
            'complexity_thresholds': {
                'low': 5,
                'medium': 10,
                'high': 20
            },
            'size_thresholds': {
                'function_lines': 50,
                'class_methods': 20
            },
            'quality_indicators': {
                'good': ['docstring', 'type_hints', 'error_handling'],
                'bad': ['magic_numbers', 'todo_comments', 'hardcoded_values']
            }
        }
    
    def _get_default_insights(self) -> Dict[str, Any]:
        """Return default insights when generation fails."""
        return {
            'summary': {
                'overall_assessment': 'Analysis failed - please check configuration',
                'key_metrics': {},
                'priority_areas': []
            },
            'recommendations': [
                {
                    'category': 'system',
                    'priority': 'high',
                    'title': 'Fix Analysis Configuration',
                    'description': 'AI insight generation encountered an error',
                    'action': 'Check system configuration and dependencies',
                    'benefit': 'Enables proper code analysis and insights'
                }
            ]
        }


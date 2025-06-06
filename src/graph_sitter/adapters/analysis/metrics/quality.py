"""
Quality Metrics Analysis

Analyzes code quality metrics including maintainability, documentation coverage,
test coverage, and technical debt indicators.
"""

import ast
import re
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """Analyzes various code quality metrics."""
    
    def __init__(self):
        self.docstring_patterns = [
            r'""".*?"""',
            r"'''.*?'''",
            r'#.*?$'
        ]
        
        self.test_patterns = [
            r'test_.*\.py$',
            r'.*_test\.py$',
            r'tests?/.*\.py$'
        ]
        
        self.quality_indicators = {
            'good': ['docstring', 'type_hints', 'error_handling', 'logging'],
            'bad': ['todo', 'fixme', 'hack', 'magic_numbers', 'long_functions']
        }
    
    def analyze_codebase(self, codebase) -> Dict[str, Any]:
        """Analyze quality metrics for entire codebase."""
        try:
            if hasattr(codebase, 'files'):
                return self._analyze_graph_sitter_codebase(codebase)
            else:
                return self._analyze_ast_codebase(codebase)
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            return self._get_default_quality_metrics()
    
    def _analyze_graph_sitter_codebase(self, codebase) -> Dict[str, Any]:
        """Analyze codebase using graph-sitter."""
        metrics = {
            'total_files': len(codebase.files),
            'total_functions': len(codebase.functions),
            'total_classes': len(codebase.classes),
            'documented_functions': 0,
            'documented_classes': 0,
            'test_files': 0,
            'test_functions': 0,
            'type_annotated_functions': 0,
            'error_handling_functions': 0,
            'quality_issues': [],
            'maintainability_score': 0,
            'documentation_coverage': 0,
            'test_coverage': 0,
            'technical_debt_ratio': 0
        }
        
        # Analyze functions
        for function in codebase.functions:
            if hasattr(function, 'docstring') and function.docstring:
                metrics['documented_functions'] += 1
            
            if hasattr(function, 'return_type') and function.return_type:
                metrics['type_annotated_functions'] += 1
            
            if self._has_error_handling(function):
                metrics['error_handling_functions'] += 1
            
            # Check for quality issues
            issues = self._analyze_function_quality(function)
            metrics['quality_issues'].extend(issues)
        
        # Analyze classes
        for cls in codebase.classes:
            if hasattr(cls, 'docstring') and cls.docstring:
                metrics['documented_classes'] += 1
        
        # Analyze files for tests
        for file in codebase.files:
            if self._is_test_file(file.filepath):
                metrics['test_files'] += 1
                # Count test functions in this file
                test_funcs = [f for f in file.functions if f.name.startswith('test_')]
                metrics['test_functions'] += len(test_funcs)
        
        # Calculate derived metrics
        metrics['documentation_coverage'] = self._calculate_documentation_coverage(metrics)
        metrics['test_coverage'] = self._calculate_test_coverage(metrics)
        metrics['technical_debt_ratio'] = self._calculate_technical_debt(metrics)
        metrics['maintainability_score'] = self._calculate_maintainability_score(metrics)
        
        return metrics
    
    def _analyze_ast_codebase(self, file_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze codebase using AST data."""
        metrics = {
            'total_files': len(file_analyses),
            'total_functions': 0,
            'total_classes': 0,
            'documented_functions': 0,
            'documented_classes': 0,
            'test_files': 0,
            'test_functions': 0,
            'type_annotated_functions': 0,
            'error_handling_functions': 0,
            'quality_issues': [],
            'maintainability_score': 0,
            'documentation_coverage': 0,
            'test_coverage': 0,
            'technical_debt_ratio': 0
        }
        
        for filepath, analysis in file_analyses.items():
            if self._is_test_file(filepath):
                metrics['test_files'] += 1
            
            # Analyze functions
            for func in analysis.get('functions', []):
                metrics['total_functions'] += 1
                
                if func.get('docstring'):
                    metrics['documented_functions'] += 1
                
                if func.get('return_type'):
                    metrics['type_annotated_functions'] += 1
                
                if func.get('name', '').startswith('test_'):
                    metrics['test_functions'] += 1
            
            # Analyze classes
            for cls in analysis.get('classes', []):
                metrics['total_classes'] += 1
                
                if cls.get('docstring'):
                    metrics['documented_classes'] += 1
        
        # Calculate derived metrics
        metrics['documentation_coverage'] = self._calculate_documentation_coverage(metrics)
        metrics['test_coverage'] = self._calculate_test_coverage(metrics)
        metrics['technical_debt_ratio'] = self._calculate_technical_debt(metrics)
        metrics['maintainability_score'] = self._calculate_maintainability_score(metrics)
        
        return metrics
    
    def analyze_function(self, function) -> Dict[str, Any]:
        """Analyze quality metrics for a single function."""
        metrics = {
            'has_docstring': False,
            'has_type_hints': False,
            'has_error_handling': False,
            'complexity_score': 1,
            'length_score': 1,
            'quality_score': 0,
            'issues': []
        }
        
        try:
            # Check docstring
            if hasattr(function, 'docstring') and function.docstring:
                metrics['has_docstring'] = True
            
            # Check type hints
            if hasattr(function, 'return_type') and function.return_type:
                metrics['has_type_hints'] = True
            
            # Check error handling
            metrics['has_error_handling'] = self._has_error_handling(function)
            
            # Analyze quality issues
            metrics['issues'] = self._analyze_function_quality(function)
            
            # Calculate overall quality score
            metrics['quality_score'] = self._calculate_function_quality_score(metrics)
            
        except Exception as e:
            logger.warning(f"Failed to analyze function quality: {e}")
            metrics['issues'].append({'type': 'analysis_error', 'message': str(e)})
        
        return metrics
    
    def _has_error_handling(self, function) -> bool:
        """Check if function has error handling."""
        try:
            if hasattr(function, 'source'):
                source = function.source.lower()
                return any(keyword in source for keyword in ['try:', 'except:', 'raise', 'assert'])
            return False
        except:
            return False
    
    def _analyze_function_quality(self, function) -> List[Dict[str, Any]]:
        """Analyze quality issues in a function."""
        issues = []
        
        try:
            if hasattr(function, 'source'):
                source = function.source
                
                # Check for TODO/FIXME comments
                if re.search(r'#.*(?:TODO|FIXME|HACK|XXX)', source, re.IGNORECASE):
                    issues.append({
                        'type': 'technical_debt',
                        'severity': 'minor',
                        'message': 'Contains TODO/FIXME comments'
                    })
                
                # Check for magic numbers
                magic_numbers = re.findall(r'\b(?<![\w.])\d{2,}\b(?![\w.])', source)
                if magic_numbers:
                    issues.append({
                        'type': 'magic_numbers',
                        'severity': 'minor',
                        'message': f'Contains magic numbers: {", ".join(set(magic_numbers))}'
                    })
                
                # Check function length
                lines = len(source.splitlines())
                if lines > 50:
                    issues.append({
                        'type': 'long_function',
                        'severity': 'major' if lines > 100 else 'minor',
                        'message': f'Function is {lines} lines long (consider breaking it down)'
                    })
                
                # Check for missing docstring
                if not (hasattr(function, 'docstring') and function.docstring):
                    issues.append({
                        'type': 'missing_documentation',
                        'severity': 'minor',
                        'message': 'Function lacks docstring'
                    })
                
                # Check for complex nested structures
                nesting_level = self._calculate_nesting_level(source)
                if nesting_level > 4:
                    issues.append({
                        'type': 'high_nesting',
                        'severity': 'major',
                        'message': f'High nesting level ({nesting_level})'
                    })
        
        except Exception as e:
            logger.warning(f"Failed to analyze function quality issues: {e}")
        
        return issues
    
    def _calculate_nesting_level(self, source: str) -> int:
        """Calculate maximum nesting level in source code."""
        try:
            tree = ast.parse(source)
            max_depth = 0
            
            def visit_node(node, depth=0):
                nonlocal max_depth
                max_depth = max(max_depth, depth)
                
                if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    depth += 1
                
                for child in ast.iter_child_nodes(node):
                    visit_node(child, depth)
            
            visit_node(tree)
            return max_depth
        except:
            return 0
    
    def _is_test_file(self, filepath: str) -> bool:
        """Check if file is a test file."""
        return any(re.search(pattern, filepath) for pattern in self.test_patterns)
    
    def _calculate_documentation_coverage(self, metrics: Dict[str, Any]) -> float:
        """Calculate documentation coverage percentage."""
        total_items = metrics['total_functions'] + metrics['total_classes']
        documented_items = metrics['documented_functions'] + metrics['documented_classes']
        
        if total_items == 0:
            return 100.0
        
        return (documented_items / total_items) * 100
    
    def _calculate_test_coverage(self, metrics: Dict[str, Any]) -> float:
        """Calculate test coverage percentage (simplified)."""
        if metrics['total_functions'] == 0:
            return 0.0
        
        # Simple heuristic: ratio of test functions to total functions
        return min(100.0, (metrics['test_functions'] / metrics['total_functions']) * 100)
    
    def _calculate_technical_debt(self, metrics: Dict[str, Any]) -> float:
        """Calculate technical debt ratio."""
        total_issues = len(metrics['quality_issues'])
        total_items = metrics['total_functions'] + metrics['total_classes']
        
        if total_items == 0:
            return 0.0
        
        return (total_issues / total_items) * 100
    
    def _calculate_maintainability_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall maintainability score."""
        # Weighted combination of various factors
        doc_weight = 0.3
        test_weight = 0.3
        debt_weight = 0.4
        
        doc_score = metrics['documentation_coverage']
        test_score = metrics['test_coverage']
        debt_penalty = metrics['technical_debt_ratio']
        
        # Calculate weighted score
        score = (doc_score * doc_weight + test_score * test_weight) - (debt_penalty * debt_weight)
        
        # Normalize to 0-100 range
        return max(0.0, min(100.0, score))
    
    def _calculate_function_quality_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate quality score for a single function."""
        score = 100.0
        
        # Deduct points for missing features
        if not metrics['has_docstring']:
            score -= 20
        
        if not metrics['has_type_hints']:
            score -= 15
        
        if not metrics['has_error_handling']:
            score -= 10
        
        # Deduct points for issues
        for issue in metrics['issues']:
            severity = issue.get('severity', 'minor')
            if severity == 'critical':
                score -= 25
            elif severity == 'major':
                score -= 15
            elif severity == 'minor':
                score -= 5
        
        return max(0.0, score)
    
    def _get_default_quality_metrics(self) -> Dict[str, Any]:
        """Return default quality metrics when analysis fails."""
        return {
            'total_files': 0,
            'total_functions': 0,
            'total_classes': 0,
            'documented_functions': 0,
            'documented_classes': 0,
            'test_files': 0,
            'test_functions': 0,
            'type_annotated_functions': 0,
            'error_handling_functions': 0,
            'quality_issues': [],
            'maintainability_score': 0,
            'documentation_coverage': 0,
            'test_coverage': 0,
            'technical_debt_ratio': 0
        }
    
    def generate_quality_report(self, metrics: Dict[str, Any]) -> str:
        """Generate a human-readable quality report."""
        report = []
        report.append("📊 CODE QUALITY REPORT")
        report.append("=" * 50)
        
        # Overview
        report.append(f"📁 Total Files: {metrics['total_files']}")
        report.append(f"⚡ Total Functions: {metrics['total_functions']}")
        report.append(f"🏗️  Total Classes: {metrics['total_classes']}")
        report.append("")
        
        # Quality scores
        report.append("📈 QUALITY SCORES")
        report.append("-" * 30)
        report.append(f"Maintainability: {metrics['maintainability_score']:.1f}%")
        report.append(f"Documentation Coverage: {metrics['documentation_coverage']:.1f}%")
        report.append(f"Test Coverage: {metrics['test_coverage']:.1f}%")
        report.append(f"Technical Debt Ratio: {metrics['technical_debt_ratio']:.1f}%")
        report.append("")
        
        # Documentation stats
        report.append("📚 DOCUMENTATION")
        report.append("-" * 30)
        report.append(f"Documented Functions: {metrics['documented_functions']}/{metrics['total_functions']}")
        report.append(f"Documented Classes: {metrics['documented_classes']}/{metrics['total_classes']}")
        report.append("")
        
        # Testing stats
        report.append("🧪 TESTING")
        report.append("-" * 30)
        report.append(f"Test Files: {metrics['test_files']}")
        report.append(f"Test Functions: {metrics['test_functions']}")
        report.append("")
        
        # Quality issues
        if metrics['quality_issues']:
            report.append("⚠️  QUALITY ISSUES")
            report.append("-" * 30)
            
            issue_counts = Counter(issue.get('type', 'unknown') for issue in metrics['quality_issues'])
            for issue_type, count in issue_counts.most_common():
                report.append(f"{issue_type.replace('_', ' ').title()}: {count}")
        
        return "\n".join(report)


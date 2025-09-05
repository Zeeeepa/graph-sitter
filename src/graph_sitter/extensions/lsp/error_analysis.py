"""
Comprehensive Error Analysis for Graph-Sitter

This module provides comprehensive error analysis capabilities by leveraging
existing graph-sitter infrastructure and adding intelligent error detection.
"""

import ast
import time
from typing import Dict, List, Optional, Any
from collections import defaultdict

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ComprehensiveErrorAnalyzer:
    """
    Comprehensive error analyzer that leverages existing graph-sitter capabilities
    to provide intelligent error detection and analysis.
    """
    
    def __init__(self, codebase):
        self.codebase = codebase
        self._cache = {}
        logger.info("Comprehensive error analyzer initialized")
    
    def get_comprehensive_errors(self, max_errors: Optional[int] = None) -> Dict[str, Any]:
        """
        Get comprehensive error analysis leveraging existing graph-sitter analysis.
        
        Returns comprehensive error information organized by severity.
        """
        start_time = time.time()
        
        try:
            # Leverage existing graph-sitter analysis
            all_errors = []
            
            # 1. Syntax errors from parsing
            syntax_errors = self._get_syntax_errors()
            all_errors.extend(syntax_errors)
            
            # 2. Logic errors from AST analysis
            logic_errors = self._get_logic_errors()
            all_errors.extend(logic_errors)
            
            # 3. Code quality issues
            quality_errors = self._get_quality_errors()
            all_errors.extend(quality_errors)
            
            # 4. Leverage existing graph-sitter function/class analysis
            structural_errors = self._get_structural_errors()
            all_errors.extend(structural_errors)
            
            # Apply limit if specified
            if max_errors:
                all_errors = all_errors[:max_errors]
            
            # Organize by severity
            errors_by_severity = self._organize_by_severity(all_errors)
            
            analysis_duration = time.time() - start_time
            
            result = {
                'total_count': len(all_errors),
                'critical_count': len(errors_by_severity.get('critical', [])),
                'error_count': len(errors_by_severity.get('error', [])),
                'warning_count': len(errors_by_severity.get('warning', [])),
                'info_count': len(errors_by_severity.get('info', [])),
                'errors_by_severity': errors_by_severity,
                'errors_by_category': self._organize_by_category(all_errors),
                'errors_by_file': self._organize_by_file(all_errors),
                'analysis_duration': analysis_duration,
                'files_analyzed': len(set(e['file_path'] for e in all_errors)),
                'most_problematic_files': self._get_most_problematic_files(all_errors)
            }
            
            logger.info(f"Comprehensive analysis completed: {len(all_errors)} errors in {analysis_duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error during comprehensive analysis: {e}")
            return {
                'total_count': 0,
                'error': str(e),
                'analysis_duration': time.time() - start_time
            }
    
    def get_file_errors(self, file_path: str) -> List[Dict[str, Any]]:
        """Get errors for a specific file."""
        if file_path in self._cache:
            return self._cache[file_path]
        
        file_errors = []
        
        # Find the file object
        file_obj = None
        for f in self.codebase.files:
            if f.file_path == file_path or f.name == file_path:
                file_obj = f
                break
        
        if not file_obj:
            return []
        
        # Analyze this specific file
        file_errors.extend(self._analyze_file_syntax(file_obj))
        file_errors.extend(self._analyze_file_logic(file_obj))
        file_errors.extend(self._analyze_file_quality(file_obj))
        
        self._cache[file_path] = file_errors
        return file_errors
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get comprehensive error summary."""
        comprehensive_errors = self.get_comprehensive_errors()
        
        return {
            'total_errors': comprehensive_errors['total_count'],
            'critical_errors': comprehensive_errors['critical_count'],
            'errors': comprehensive_errors['error_count'],
            'warnings': comprehensive_errors['warning_count'],
            'info_hints': comprehensive_errors['info_count'],
            'files_with_errors': comprehensive_errors['files_analyzed'],
            'errors_by_category': comprehensive_errors['errors_by_category'],
            'most_problematic_files': comprehensive_errors['most_problematic_files'],
            'analysis_duration': comprehensive_errors['analysis_duration']
        }
    
    def _get_syntax_errors(self) -> List[Dict[str, Any]]:
        """Get syntax errors from parsing files."""
        errors = []
        for file_obj in self.codebase.files:
            if not file_obj.file_path.endswith('.py'):
                continue
            errors.extend(self._analyze_file_syntax(file_obj))
        return errors
    
    def _get_logic_errors(self) -> List[Dict[str, Any]]:
        """Get logic errors from AST analysis."""
        errors = []
        for file_obj in self.codebase.files:
            if not file_obj.file_path.endswith('.py'):
                continue
            errors.extend(self._analyze_file_logic(file_obj))
        return errors
    
    def _get_quality_errors(self) -> List[Dict[str, Any]]:
        """Get code quality issues."""
        errors = []
        for file_obj in self.codebase.files:
            if not file_obj.file_path.endswith('.py'):
                continue
            errors.extend(self._analyze_file_quality(file_obj))
        return errors
    
    def _get_structural_errors(self) -> List[Dict[str, Any]]:
        """Get structural errors using existing graph-sitter analysis."""
        errors = []
        
        # Leverage existing function analysis
        try:
            for func in self.codebase.functions:
                # Check for functions with too many parameters
                if hasattr(func, 'parameters') and len(func.parameters) > 8:
                    file_path = getattr(func, 'file_path', getattr(func, 'filepath', 'unknown'))
                    start_line = getattr(func, 'start_line', getattr(func, 'line_number', 1))
                    
                    errors.append({
                        'id': f"too_many_params_{file_path}_{start_line}",
                        'message': f"Function '{func.name}' has too many parameters ({len(func.parameters)})",
                        'severity': 'warning',
                        'category': 'complexity',
                        'file_path': file_path,
                        'line': start_line,
                        'column': 0,
                        'suggestions': [f"Consider reducing parameters in '{func.name}'", "Use parameter objects or configuration"]
                    })
                
                # Check for functions with no docstring
                if hasattr(func, 'docstring') and not func.docstring and not func.name.startswith('_'):
                    file_path = getattr(func, 'file_path', getattr(func, 'filepath', 'unknown'))
                    start_line = getattr(func, 'start_line', getattr(func, 'line_number', 1))
                    
                    errors.append({
                        'id': f"no_docstring_{file_path}_{start_line}",
                        'message': f"Function '{func.name}' has no docstring",
                        'severity': 'info',
                        'category': 'documentation',
                        'file_path': file_path,
                        'line': start_line,
                        'column': 0,
                        'suggestions': [f"Add docstring to '{func.name}'", "Document function purpose and parameters"]
                    })
        except Exception as e:
            logger.debug(f"Error in structural analysis for functions: {e}")
        
        # Leverage existing class analysis
        try:
            for cls in self.codebase.classes:
                # Check for classes with too many methods
                if hasattr(cls, 'methods') and len(cls.methods) > 20:
                    file_path = getattr(cls, 'file_path', getattr(cls, 'filepath', 'unknown'))
                    start_line = getattr(cls, 'start_line', getattr(cls, 'line_number', 1))
                    
                    errors.append({
                        'id': f"too_many_methods_{file_path}_{start_line}",
                        'message': f"Class '{cls.name}' has too many methods ({len(cls.methods)})",
                        'severity': 'warning',
                        'category': 'complexity',
                        'file_path': file_path,
                        'line': start_line,
                        'column': 0,
                        'suggestions': [f"Consider breaking down class '{cls.name}'", "Extract related methods into separate classes"]
                    })
        except Exception as e:
            logger.debug(f"Error in structural analysis for classes: {e}")
        
        return errors
    
    def _analyze_file_syntax(self, file_obj) -> List[Dict[str, Any]]:
        """Analyze file for syntax errors."""
        errors = []
        try:
            ast.parse(file_obj.content)
        except SyntaxError as e:
            errors.append({
                'id': f"syntax_{file_obj.file_path}_{e.lineno}",
                'message': f"Syntax error: {e.msg}",
                'severity': 'error',
                'category': 'syntax',
                'file_path': file_obj.file_path,
                'line': e.lineno or 1,
                'column': e.offset or 1,
                'suggestions': ["Check for missing parentheses, brackets, or quotes", "Verify proper indentation"]
            })
        except Exception:
            pass  # Skip files that can't be parsed
        return errors
    
    def _analyze_file_logic(self, file_obj) -> List[Dict[str, Any]]:
        """Analyze file for logic errors."""
        errors = []
        try:
            tree = ast.parse(file_obj.content)
            
            # Track variables
            defined_vars = set()
            used_vars = set()
            imports = set()
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name)
                    else:
                        if node.module:
                            imports.add(node.module)
                        for alias in node.names:
                            imports.add(alias.name)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            defined_vars.add(target.id)
                elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    defined_vars.add(node.name)
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                    used_vars.add(node.id)
            
            # Check for undefined variables
            undefined_vars = used_vars - defined_vars - imports - {'__name__', '__file__', '__doc__'}
            for var in undefined_vars:
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id == var and isinstance(node.ctx, ast.Load):
                        errors.append({
                            'id': f"undefined_{file_obj.file_path}_{node.lineno}_{var}",
                            'message': f"Undefined variable '{var}'",
                            'severity': 'error',
                            'category': 'logic',
                            'file_path': file_obj.file_path,
                            'line': node.lineno,
                            'column': node.col_offset,
                            'suggestions': [f"Define variable '{var}' before use", f"Check for typos in '{var}'"]
                        })
                        break
                        
        except Exception:
            pass  # Skip files that can't be parsed
        return errors
    
    def _analyze_file_quality(self, file_obj) -> List[Dict[str, Any]]:
        """Analyze file for code quality issues."""
        errors = []
        try:
            tree = ast.parse(file_obj.content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check complexity
                    complexity = self._calculate_complexity(node)
                    if complexity > 10:
                        errors.append({
                            'id': f"complexity_{file_obj.file_path}_{node.lineno}_{node.name}",
                            'message': f"Function '{node.name}' has high complexity ({complexity})",
                            'severity': 'warning',
                            'category': 'complexity',
                            'file_path': file_obj.file_path,
                            'line': node.lineno,
                            'column': node.col_offset,
                            'suggestions': [f"Break down function '{node.name}' into smaller functions"]
                        })
                    
                    # Check for unused parameters
                    for arg in node.args.args:
                        if not self._is_param_used(node, arg.arg) and not arg.arg.startswith('_'):
                            errors.append({
                                'id': f"unused_param_{file_obj.file_path}_{node.lineno}_{arg.arg}",
                                'message': f"Unused parameter '{arg.arg}' in function '{node.name}'",
                                'severity': 'warning',
                                'category': 'unused',
                                'file_path': file_obj.file_path,
                                'line': node.lineno,
                                'column': node.col_offset,
                                'suggestions': [f"Remove unused parameter '{arg.arg}'"]
                            })
                            
        except Exception:
            pass  # Skip files that can't be parsed
        return errors
    
    def _is_param_used(self, func_node: ast.FunctionDef, param_name: str) -> bool:
        """Check if parameter is used in function."""
        for node in ast.walk(func_node):
            if isinstance(node, ast.Name) and node.id == param_name and isinstance(node.ctx, ast.Load):
                return True
        return False
    
    def _calculate_complexity(self, func_node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
        return complexity
    
    def _organize_by_severity(self, errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize errors by severity."""
        by_severity = defaultdict(list)
        for error in errors:
            by_severity[error['severity']].append(error)
        return dict(by_severity)
    
    def _organize_by_category(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Organize errors by category."""
        by_category = defaultdict(int)
        for error in errors:
            by_category[error['category']] += 1
        return dict(by_category)
    
    def _organize_by_file(self, errors: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize errors by file."""
        by_file = defaultdict(list)
        for error in errors:
            by_file[error['file_path']].append(error)
        return dict(by_file)
    
    def _get_most_problematic_files(self, errors: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get files with most errors."""
        file_counts = defaultdict(int)
        for error in errors:
            file_counts[error['file_path']] += 1
        
        sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
        return [{'file_path': f, 'error_count': c} for f, c in sorted_files[:limit]]


# Add FullErrors property to Codebase class
def add_full_errors_to_codebase():
    """Add FullErrors property to Codebase class."""
    try:
        from graph_sitter.core.codebase import Codebase
        
        def _get_full_errors(self):
            """Get comprehensive error analysis."""
            if not hasattr(self, '_full_errors_analyzer'):
                self._full_errors_analyzer = ComprehensiveErrorAnalyzer(self)
            return self._full_errors_analyzer
        
        # Add property to Codebase class
        Codebase.FullErrors = property(_get_full_errors)
        
        logger.info("FullErrors property added to Codebase class")
        
    except ImportError:
        logger.warning("Could not add FullErrors property - Codebase class not available")
    except Exception as e:
        logger.error(f"Failed to add FullErrors property: {e}")


# Auto-add FullErrors property when module is imported
add_full_errors_to_codebase()


# Convenience functions
def analyze_codebase_errors(codebase) -> ComprehensiveErrorAnalyzer:
    """Create and return a comprehensive error analyzer for a codebase."""
    return ComprehensiveErrorAnalyzer(codebase)


def get_repo_error_analysis(repo_path: str, max_errors: Optional[int] = None) -> Dict[str, Any]:
    """Get comprehensive error analysis for a repository by path."""
    try:
        from graph_sitter.core.codebase import Codebase
        
        codebase = Codebase(repo_path)
        analyzer = ComprehensiveErrorAnalyzer(codebase)
        return analyzer.get_comprehensive_errors(max_errors=max_errors)
        
    except Exception as e:
        logger.error(f"Error analyzing repository {repo_path}: {e}")
        return {'total_count': 0, 'error': str(e)}

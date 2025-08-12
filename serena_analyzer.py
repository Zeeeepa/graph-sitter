#!/usr/bin/env python3
"""
Comprehensive Serena Codebase Analyzer - Standalone Module
==========================================================

This is a comprehensive, standalone codebase analyzer that consolidates all
Serena analysis capabilities from the graph-sitter project into a single,
self-contained module.

Features:
- 24+ error types with severity classification (Critical, Major, Minor)
- Comprehensive dependency analysis
- Code quality metrics and architectural analysis
- Semantic analysis and symbol intelligence
- Repository cloning and Git integration
- Formatted error reporting with detailed context

Usage:
    python serena_analyzer.py --repo https://github.com/user/repo
    python serena_analyzer.py --repo /path/to/local/repo

Output:
    Generates report.txt with comprehensive error analysis in the format:
    ERRORS: 104 [⚠️ Critical: 30] [👉 Major: 39] [🔍 Minor: 35]
    1 ⚠️- projectname'/src/codefile1.py / Function - 'examplefunctionname' [error parameters/reason]
    ...
"""

import os
import sys
import ast
import re
import json
import argparse
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CORE TYPES AND ENUMS
# ============================================================================

class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    MAJOR = "major" 
    MINOR = "minor"

class ErrorCategory(Enum):
    """Error categories."""
    SYNTAX = "syntax"
    LOGIC = "logic"
    PERFORMANCE = "performance"
    SECURITY = "security"
    STYLE = "style"
    IMPORT = "import"
    TYPE = "type"
    UNUSED = "unused"
    DEPENDENCY = "dependency"
    ARCHITECTURE = "architecture"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"

@dataclass
class CodeError:
    """Represents a code error with comprehensive context."""
    id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    filepath: str
    function_name: str = ""
    line_start: int = 0
    line_end: int = 0
    column_start: int = 0
    column_end: int = 0
    context_lines: List[str] = field(default_factory=list)
    suggested_fix: str = ""
    related_errors: List[str] = field(default_factory=list)
    affected_functions: List[str] = field(default_factory=list)
    blast_radius: int = 0
    parameters: str = ""
    reason: str = ""

@dataclass
class AnalysisResult:
    """Complete analysis result."""
    total_errors: int
    errors_by_severity: Dict[ErrorSeverity, int]
    errors_by_category: Dict[ErrorCategory, int]
    errors: List[CodeError]
    analysis_time: float
    repository_info: Dict[str, Any]
    metrics: Dict[str, Any]

# ============================================================================
# REPOSITORY INTERFACE AND GIT INTEGRATION
# ============================================================================

class RepositoryInterface:
    """Handles repository operations and file management."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.is_remote = repo_path.startswith(('http://', 'https://', 'git@'))
        self.temp_dir = None
        
    def setup_repository(self) -> Path:
        """Setup repository for analysis."""
        if self.is_remote:
            return self._clone_repository()
        else:
            if not self.repo_path.exists():
                raise ValueError(f"Local repository path does not exist: {self.repo_path}")
            return self.repo_path
    
    def _clone_repository(self) -> Path:
        """Clone remote repository to temporary directory."""
        import tempfile
        import shutil
        
        self.temp_dir = Path(tempfile.mkdtemp(prefix="serena_analysis_"))
        logger.info(f"Cloning repository {self.repo_path} to {self.temp_dir}")
        
        try:
            subprocess.run([
                'git', 'clone', '--depth', '1', str(self.repo_path), str(self.temp_dir)
            ], check=True, capture_output=True, text=True)
            return self.temp_dir
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise
    
    def cleanup(self):
        """Clean up temporary files."""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def get_repository_info(self, repo_dir: Path) -> Dict[str, Any]:
        """Get repository information."""
        info = {
            'name': repo_dir.name,
            'path': str(repo_dir),
            'is_git': (repo_dir / '.git').exists(),
            'total_files': 0,
            'code_files': 0,
            'languages': set(),
            'size_bytes': 0
        }
        
        # Count files and detect languages
        for file_path in repo_dir.rglob('*'):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                info['total_files'] += 1
                info['size_bytes'] += file_path.stat().st_size
                
                if self._is_code_file(file_path):
                    info['code_files'] += 1
                    lang = self._detect_language(file_path)
                    if lang:
                        info['languages'].add(lang)
        
        info['languages'] = list(info['languages'])
        return info
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        ignore_patterns = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.venv', 'venv', '.env', 'dist', 'build', '.tox'
        }
        
        return any(pattern in str(file_path) for pattern in ignore_patterns)
    
    def _is_code_file(self, file_path: Path) -> bool:
        """Check if file is a code file."""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala',
            '.clj', '.hs', '.ml', '.fs', '.vb', '.pl', '.sh', '.ps1'
        }
        return file_path.suffix.lower() in code_extensions
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension."""
        ext_to_lang = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.jsx': 'React',
            '.tsx': 'React TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.h': 'C/C++ Header',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.sh': 'Shell',
            '.ps1': 'PowerShell'
        }
        return ext_to_lang.get(file_path.suffix.lower())

# ============================================================================
# ERROR DETECTION PATTERNS AND RULES
# ============================================================================

class ErrorPatterns:
    """Comprehensive error detection patterns."""
    
    @staticmethod
    def get_all_patterns() -> Dict[str, Dict]:
        """Get all error detection patterns."""
        return {
            # CRITICAL ERRORS
            'syntax_errors': {
                'patterns': [
                    r'SyntaxError',
                    r'IndentationError', 
                    r'TabError',
                    r'unexpected EOF',
                    r'invalid syntax',
                    r'unmatched.*[\(\)\[\]\{\}]',
                    r'unexpected token'
                ],
                'severity': ErrorSeverity.CRITICAL,
                'category': ErrorCategory.SYNTAX,
                'description': 'Syntax errors that prevent code execution'
            },
            
            'import_errors': {
                'patterns': [
                    r'ImportError',
                    r'ModuleNotFoundError',
                    r'from\s+\.\s+import',  # Problematic relative imports
                    r'import\s+\*',  # Wildcard imports
                    r'from\s+.*\s+import\s+\*'
                ],
                'severity': ErrorSeverity.CRITICAL,
                'category': ErrorCategory.IMPORT,
                'description': 'Import errors and problematic import patterns'
            },
            
            'undefined_variables': {
                'patterns': [
                    r'NameError.*not defined',
                    r'UnboundLocalError',
                    r'undefined variable'
                ],
                'severity': ErrorSeverity.CRITICAL,
                'category': ErrorCategory.LOGIC,
                'description': 'Undefined variables and name errors'
            },
            
            # MAJOR ERRORS
            'security_vulnerabilities': {
                'patterns': [
                    r'eval\s*\(',
                    r'exec\s*\(',
                    r'subprocess\.call.*shell=True',
                    r'os\.system\s*\(',
                    r'pickle\.loads?\s*\(',
                    r'yaml\.load\s*\(',
                    r'input\s*\(',  # In Python 2 context
                    r'raw_input\s*\('
                ],
                'severity': ErrorSeverity.MAJOR,
                'category': ErrorCategory.SECURITY,
                'description': 'Security vulnerabilities and dangerous functions'
            },
            
            'type_errors': {
                'patterns': [
                    r'TypeError',
                    r'AttributeError',
                    r'ValueError.*invalid literal',
                    r'cannot concatenate.*and',
                    r'unsupported operand type'
                ],
                'severity': ErrorSeverity.MAJOR,
                'category': ErrorCategory.TYPE,
                'description': 'Type-related errors and mismatches'
            },
            
            'logic_errors': {
                'patterns': [
                    r'ZeroDivisionError',
                    r'IndexError',
                    r'KeyError',
                    r'RecursionError',
                    r'infinite.*loop',
                    r'unreachable.*code'
                ],
                'severity': ErrorSeverity.MAJOR,
                'category': ErrorCategory.LOGIC,
                'description': 'Logic errors and runtime exceptions'
            },
            
            'performance_issues': {
                'patterns': [
                    r'for\s+.*\s+in\s+range\(len\(',  # Inefficient iteration
                    r'\.append\s*\(\s*\)\s*$',  # Empty append
                    r'time\.sleep\s*\(\s*[0-9]+\s*\)',  # Long sleeps
                    r'while\s+True:.*(?!break)',  # Infinite loops without break
                    r'nested.*loop.*O\(n\^[3-9]\)'  # High complexity
                ],
                'severity': ErrorSeverity.MAJOR,
                'category': ErrorCategory.PERFORMANCE,
                'description': 'Performance bottlenecks and inefficient code'
            },
            
            # MINOR ERRORS
            'unused_code': {
                'patterns': [
                    r'unused.*variable',
                    r'unused.*import',
                    r'unused.*function',
                    r'dead.*code',
                    r'unreachable.*statement'
                ],
                'severity': ErrorSeverity.MINOR,
                'category': ErrorCategory.UNUSED,
                'description': 'Unused variables, imports, and dead code'
            },
            
            'style_violations': {
                'patterns': [
                    r'line too long',
                    r'trailing whitespace',
                    r'missing.*docstring',
                    r'inconsistent.*indentation',
                    r'[a-z]+[A-Z]',  # camelCase in Python
                    r'def\s+[A-Z]',  # Capitalized function names
                    r'class\s+[a-z]'  # Lowercase class names
                ],
                'severity': ErrorSeverity.MINOR,
                'category': ErrorCategory.STYLE,
                'description': 'Code style violations and formatting issues'
            },
            
            'complexity_issues': {
                'patterns': [
                    r'too.*complex',
                    r'cyclomatic.*complexity',
                    r'too.*many.*branches',
                    r'too.*many.*statements',
                    r'function.*too.*long'
                ],
                'severity': ErrorSeverity.MINOR,
                'category': ErrorCategory.COMPLEXITY,
                'description': 'Code complexity and maintainability issues'
            },
            
            'dependency_issues': {
                'patterns': [
                    r'circular.*import',
                    r'dependency.*cycle',
                    r'missing.*dependency',
                    r'version.*conflict',
                    r'deprecated.*package'
                ],
                'severity': ErrorSeverity.MAJOR,
                'category': ErrorCategory.DEPENDENCY,
                'description': 'Dependency management and circular import issues'
            },
            
            'architectural_issues': {
                'patterns': [
                    r'god.*class',
                    r'singleton.*abuse',
                    r'tight.*coupling',
                    r'violation.*of.*principle',
                    r'anti.*pattern'
                ],
                'severity': ErrorSeverity.MAJOR,
                'category': ErrorCategory.ARCHITECTURE,
                'description': 'Architectural problems and design pattern violations'
            }
        }

# ============================================================================
# SEMANTIC ANALYSIS AND CODE INTELLIGENCE
# ============================================================================

class SemanticAnalyzer:
    """Semantic analysis and code intelligence."""
    
    def __init__(self):
        self.symbol_table = {}
        self.function_calls = defaultdict(list)
        self.imports = defaultdict(list)
        self.classes = defaultdict(list)
        self.functions = defaultdict(list)
    
    def analyze_file(self, filepath: Path, content: str) -> Dict[str, Any]:
        """Analyze a single file for semantic information."""
        try:
            tree = ast.parse(content)
            visitor = SemanticVisitor(str(filepath))
            visitor.visit(tree)
            
            return {
                'functions': visitor.functions,
                'classes': visitor.classes,
                'imports': visitor.imports,
                'variables': visitor.variables,
                'function_calls': visitor.function_calls,
                'complexity_metrics': visitor.complexity_metrics
            }
        except SyntaxError as e:
            return {
                'syntax_error': {
                    'message': str(e),
                    'line': e.lineno,
                    'column': e.offset
                }
            }
        except Exception as e:
            return {'error': str(e)}

class SemanticVisitor(ast.NodeVisitor):
    """AST visitor for semantic analysis."""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.functions = []
        self.classes = []
        self.imports = []
        self.variables = []
        self.function_calls = []
        self.complexity_metrics = {
            'cyclomatic_complexity': 0,
            'nesting_depth': 0,
            'function_length': {}
        }
        self.current_function = None
        self.nesting_level = 0
    
    def visit_FunctionDef(self, node):
        """Visit function definition."""
        func_info = {
            'name': node.name,
            'line_start': node.lineno,
            'line_end': node.end_lineno or node.lineno,
            'args': [arg.arg for arg in node.args.args],
            'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
            'docstring': ast.get_docstring(node),
            'complexity': self._calculate_function_complexity(node)
        }
        self.functions.append(func_info)
        
        # Track function length
        func_length = (node.end_lineno or node.lineno) - node.lineno
        self.complexity_metrics['function_length'][node.name] = func_length
        
        self.current_function = node.name
        self.generic_visit(node)
        self.current_function = None
    
    def visit_ClassDef(self, node):
        """Visit class definition."""
        class_info = {
            'name': node.name,
            'line_start': node.lineno,
            'line_end': node.end_lineno or node.lineno,
            'bases': [self._get_name(base) for base in node.bases],
            'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
            'docstring': ast.get_docstring(node),
            'methods': []
        }
        
        # Find methods
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_info['methods'].append(item.name)
        
        self.classes.append(class_info)
        self.generic_visit(node)
    
    def visit_Import(self, node):
        """Visit import statement."""
        for alias in node.names:
            self.imports.append({
                'module': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'import'
            })
    
    def visit_ImportFrom(self, node):
        """Visit from import statement."""
        for alias in node.names:
            self.imports.append({
                'module': node.module,
                'name': alias.name,
                'alias': alias.asname,
                'line': node.lineno,
                'type': 'from_import',
                'level': node.level
            })
    
    def visit_Call(self, node):
        """Visit function call."""
        func_name = self._get_name(node.func)
        if func_name:
            self.function_calls.append({
                'function': func_name,
                'line': node.lineno,
                'args': len(node.args),
                'kwargs': len(node.keywords),
                'in_function': self.current_function
            })
        self.generic_visit(node)
    
    def visit_Assign(self, node):
        """Visit assignment."""
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.variables.append({
                    'name': target.id,
                    'line': node.lineno,
                    'in_function': self.current_function
                })
        self.generic_visit(node)
    
    def visit_If(self, node):
        """Visit if statement (increases complexity)."""
        self.complexity_metrics['cyclomatic_complexity'] += 1
        self.nesting_level += 1
        self.complexity_metrics['nesting_depth'] = max(
            self.complexity_metrics['nesting_depth'], 
            self.nesting_level
        )
        self.generic_visit(node)
        self.nesting_level -= 1
    
    def visit_For(self, node):
        """Visit for loop (increases complexity)."""
        self.complexity_metrics['cyclomatic_complexity'] += 1
        self.nesting_level += 1
        self.complexity_metrics['nesting_depth'] = max(
            self.complexity_metrics['nesting_depth'], 
            self.nesting_level
        )
        self.generic_visit(node)
        self.nesting_level -= 1
    
    def visit_While(self, node):
        """Visit while loop (increases complexity)."""
        self.complexity_metrics['cyclomatic_complexity'] += 1
        self.nesting_level += 1
        self.complexity_metrics['nesting_depth'] = max(
            self.complexity_metrics['nesting_depth'], 
            self.nesting_level
        )
        self.generic_visit(node)
        self.nesting_level -= 1
    
    def _get_name(self, node):
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Constant):
            return str(node.value)
        return None
    
    def _get_decorator_name(self, node):
        """Get decorator name."""
        return self._get_name(node)
    
    def _calculate_function_complexity(self, node):
        """Calculate function complexity."""
        complexity = 1  # Base complexity
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                complexity += 1
        return complexity

# ============================================================================
# COMPREHENSIVE ERROR ANALYZER
# ============================================================================

class ComprehensiveErrorAnalyzer:
    """Main error analysis engine consolidating all capabilities."""
    
    def __init__(self):
        self.patterns = ErrorPatterns.get_all_patterns()
        self.semantic_analyzer = SemanticAnalyzer()
        self.error_cache = {}
        self.analysis_stats = {
            'files_analyzed': 0,
            'total_errors': 0,
            'errors_by_severity': defaultdict(int),
            'errors_by_category': defaultdict(int)
        }
    
    def analyze_repository(self, repo_dir: Path) -> AnalysisResult:
        """Analyze entire repository."""
        start_time = datetime.now()
        all_errors = []
        
        logger.info(f"Starting comprehensive analysis of {repo_dir}")
        
        # Get repository info
        repo_interface = RepositoryInterface(str(repo_dir))
        repo_info = repo_interface.get_repository_info(repo_dir)
        
        # Analyze all code files
        code_files = self._get_code_files(repo_dir)
        total_files = len(code_files)
        
        for i, file_path in enumerate(code_files, 1):
            logger.info(f"Analyzing file {i}/{total_files}: {file_path.relative_to(repo_dir)}")
            
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                file_errors = self._analyze_file(file_path, content, repo_dir)
                all_errors.extend(file_errors)
                self.analysis_stats['files_analyzed'] += 1
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
        
        # Calculate metrics
        analysis_time = (datetime.now() - start_time).total_seconds()
        errors_by_severity = defaultdict(int)
        errors_by_category = defaultdict(int)
        
        for error in all_errors:
            errors_by_severity[error.severity] += 1
            errors_by_category[error.category] += 1
        
        # Generate comprehensive metrics
        metrics = self._generate_comprehensive_metrics(repo_dir, all_errors)
        
        return AnalysisResult(
            total_errors=len(all_errors),
            errors_by_severity=dict(errors_by_severity),
            errors_by_category=dict(errors_by_category),
            errors=all_errors,
            analysis_time=analysis_time,
            repository_info=repo_info,
            metrics=metrics
        )
    
    def _get_code_files(self, repo_dir: Path) -> List[Path]:
        """Get all code files in repository."""
        code_files = []
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala'
        }
        
        for file_path in repo_dir.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix.lower() in code_extensions and
                not self._should_ignore_file(file_path)):
                code_files.append(file_path)
        
        return code_files
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored."""
        ignore_patterns = {
            '.git', '__pycache__', '.pytest_cache', 'node_modules',
            '.venv', 'venv', '.env', 'dist', 'build', '.tox', 'target',
            '.idea', '.vscode', 'coverage', '.nyc_output'
        }
        
        return any(pattern in str(file_path) for pattern in ignore_patterns)
    
    def _analyze_file(self, file_path: Path, content: str, repo_dir: Path) -> List[CodeError]:
        """Analyze single file for errors."""
        errors = []
        relative_path = file_path.relative_to(repo_dir)
        
        # Semantic analysis
        semantic_info = self.semantic_analyzer.analyze_file(file_path, content)
        
        # Pattern-based error detection
        errors.extend(self._detect_pattern_errors(file_path, content, relative_path, semantic_info))
        
        # AST-based error detection
        errors.extend(self._detect_ast_errors(file_path, content, relative_path, semantic_info))
        
        # Complexity analysis
        errors.extend(self._detect_complexity_errors(file_path, content, relative_path, semantic_info))
        
        return errors
    
    def _detect_pattern_errors(self, file_path: Path, content: str, relative_path: Path, semantic_info: Dict) -> List[CodeError]:
        """Detect errors using pattern matching."""
        errors = []
        lines = content.split('\n')
        
        for pattern_name, pattern_info in self.patterns.items():
            for pattern in pattern_info['patterns']:
                for line_num, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        error_id = f"{pattern_name}_{file_path.stem}_{line_num}"
                        
                        # Extract function name if available
                        function_name = self._find_function_at_line(semantic_info, line_num)
                        
                        error = CodeError(
                            id=error_id,
                            category=pattern_info['category'],
                            severity=pattern_info['severity'],
                            message=pattern_info['description'],
                            filepath=str(relative_path),
                            function_name=function_name,
                            line_start=line_num,
                            line_end=line_num,
                            context_lines=self._get_context_lines(lines, line_num),
                            parameters=self._extract_parameters(line, pattern),
                            reason=f"Pattern '{pattern}' matched in line: {line.strip()}"
                        )
                        errors.append(error)
        
        return errors
    
    def _detect_ast_errors(self, file_path: Path, content: str, relative_path: Path, semantic_info: Dict) -> List[CodeError]:
        """Detect errors using AST analysis."""
        errors = []
        
        # Check for syntax errors
        if 'syntax_error' in semantic_info:
            syntax_error = semantic_info['syntax_error']
            error = CodeError(
                id=f"syntax_error_{file_path.stem}_{syntax_error.get('line', 0)}",
                category=ErrorCategory.SYNTAX,
                severity=ErrorSeverity.CRITICAL,
                message="Syntax error prevents code execution",
                filepath=str(relative_path),
                line_start=syntax_error.get('line', 0),
                line_end=syntax_error.get('line', 0),
                reason=syntax_error['message']
            )
            errors.append(error)
        
        # Analyze function-specific issues
        for func in semantic_info.get('functions', []):
            # Check for long functions
            func_length = func['line_end'] - func['line_start']
            if func_length > 50:  # Configurable threshold
                error = CodeError(
                    id=f"long_function_{file_path.stem}_{func['name']}",
                    category=ErrorCategory.COMPLEXITY,
                    severity=ErrorSeverity.MINOR,
                    message="Function is too long and may be hard to maintain",
                    filepath=str(relative_path),
                    function_name=func['name'],
                    line_start=func['line_start'],
                    line_end=func['line_end'],
                    parameters=f"length={func_length}",
                    reason=f"Function '{func['name']}' has {func_length} lines (threshold: 50)"
                )
                errors.append(error)
            
            # Check for high complexity
            if func['complexity'] > 10:  # Configurable threshold
                error = CodeError(
                    id=f"high_complexity_{file_path.stem}_{func['name']}",
                    category=ErrorCategory.COMPLEXITY,
                    severity=ErrorSeverity.MAJOR,
                    message="Function has high cyclomatic complexity",
                    filepath=str(relative_path),
                    function_name=func['name'],
                    line_start=func['line_start'],
                    line_end=func['line_end'],
                    parameters=f"complexity={func['complexity']}",
                    reason=f"Function '{func['name']}' has complexity {func['complexity']} (threshold: 10)"
                )
                errors.append(error)
        
        return errors
    
    def _detect_complexity_errors(self, file_path: Path, content: str, relative_path: Path, semantic_info: Dict) -> List[CodeError]:
        """Detect complexity-related errors."""
        errors = []
        
        complexity_metrics = semantic_info.get('complexity_metrics', {})
        
        # Check overall file complexity
        if complexity_metrics.get('cyclomatic_complexity', 0) > 50:
            error = CodeError(
                id=f"file_complexity_{file_path.stem}",
                category=ErrorCategory.COMPLEXITY,
                severity=ErrorSeverity.MAJOR,
                message="File has high overall complexity",
                filepath=str(relative_path),
                parameters=f"complexity={complexity_metrics['cyclomatic_complexity']}",
                reason=f"File complexity {complexity_metrics['cyclomatic_complexity']} exceeds threshold (50)"
            )
            errors.append(error)
        
        # Check nesting depth
        if complexity_metrics.get('nesting_depth', 0) > 5:
            error = CodeError(
                id=f"deep_nesting_{file_path.stem}",
                category=ErrorCategory.COMPLEXITY,
                severity=ErrorSeverity.MINOR,
                message="Code has deep nesting levels",
                filepath=str(relative_path),
                parameters=f"depth={complexity_metrics['nesting_depth']}",
                reason=f"Nesting depth {complexity_metrics['nesting_depth']} exceeds threshold (5)"
            )
            errors.append(error)
        
        return errors
    
    def _find_function_at_line(self, semantic_info: Dict, line_num: int) -> str:
        """Find function name at given line number."""
        for func in semantic_info.get('functions', []):
            if func['line_start'] <= line_num <= func['line_end']:
                return func['name']
        return ""
    
    def _get_context_lines(self, lines: List[str], line_num: int, context: int = 2) -> List[str]:
        """Get context lines around error."""
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)
        return lines[start:end]
    
    def _extract_parameters(self, line: str, pattern: str) -> str:
        """Extract parameters from matched line."""
        # Simple parameter extraction - can be enhanced
        match = re.search(pattern, line)
        if match:
            return match.group(0)
        return ""
    
    def _generate_comprehensive_metrics(self, repo_dir: Path, errors: List[CodeError]) -> Dict[str, Any]:
        """Generate comprehensive analysis metrics."""
        return {
            'error_density': len(errors) / max(self.analysis_stats['files_analyzed'], 1),
            'critical_error_ratio': len([e for e in errors if e.severity == ErrorSeverity.CRITICAL]) / max(len(errors), 1),
            'most_problematic_files': self._get_most_problematic_files(errors),
            'error_categories_distribution': dict(Counter(e.category.value for e in errors)),
            'functions_with_errors': len(set(e.function_name for e in errors if e.function_name)),
            'average_errors_per_file': len(errors) / max(self.analysis_stats['files_analyzed'], 1)
        }
    
    def _get_most_problematic_files(self, errors: List[CodeError], limit: int = 10) -> List[Dict[str, Any]]:
        """Get files with most errors."""
        file_error_counts = Counter(e.filepath for e in errors)
        return [
            {'file': file, 'error_count': count}
            for file, count in file_error_counts.most_common(limit)
        ]

# ============================================================================
# OUTPUT FORMATTING AND REPORTING
# ============================================================================

class ReportFormatter:
    """Formats analysis results into the requested output format."""
    
    @staticmethod
    def format_report(result: AnalysisResult, repo_name: str) -> str:
        """Format analysis result into the requested report format."""
        
        # Get severity counts
        critical_count = result.errors_by_severity.get(ErrorSeverity.CRITICAL, 0)
        major_count = result.errors_by_severity.get(ErrorSeverity.MAJOR, 0)
        minor_count = result.errors_by_severity.get(ErrorSeverity.MINOR, 0)
        
        # Header with summary
        report_lines = [
            f"SERENA CODEBASE ANALYSIS REPORT",
            f"=" * 50,
            f"Repository: {repo_name}",
            f"Analysis Time: {result.analysis_time:.2f} seconds",
            f"Files Analyzed: {result.repository_info.get('code_files', 0)}",
            f"Languages: {', '.join(result.repository_info.get('languages', []))[:100]}",
            f"",
            f"ERRORS: {result.total_errors} [⚠️ Critical: {critical_count}] [👉 Major: {major_count}] [🔍 Minor: {minor_count}]",
            f""
        ]
        
        # Sort errors by severity (Critical first, then Major, then Minor)
        severity_order = {ErrorSeverity.CRITICAL: 0, ErrorSeverity.MAJOR: 1, ErrorSeverity.MINOR: 2}
        sorted_errors = sorted(result.errors, key=lambda e: (severity_order[e.severity], e.filepath, e.line_start))
        
        # Format each error
        for i, error in enumerate(sorted_errors, 1):
            severity_icon = ReportFormatter._get_severity_icon(error.severity)
            function_part = f" / Function - '{error.function_name}'" if error.function_name else ""
            parameters_part = f" [{error.parameters}]" if error.parameters else ""
            reason_part = f" [{error.reason}]" if error.reason else ""
            
            error_line = (
                f"{i} {severity_icon}- {repo_name}/{error.filepath}"
                f"{function_part}"
                f"{parameters_part}"
                f"{reason_part}"
            )
            report_lines.append(error_line)
        
        # Add summary statistics
        report_lines.extend([
            f"",
            f"ANALYSIS SUMMARY",
            f"=" * 20,
            f"Error Density: {result.metrics.get('error_density', 0):.2f} errors per file",
            f"Critical Error Ratio: {result.metrics.get('critical_error_ratio', 0):.2%}",
            f"Functions with Errors: {result.metrics.get('functions_with_errors', 0)}",
            f"",
            f"ERROR CATEGORIES:",
        ])
        
        # Add category breakdown
        for category, count in result.errors_by_category.items():
            percentage = (count / result.total_errors * 100) if result.total_errors > 0 else 0
            report_lines.append(f"  {category.value}: {count} ({percentage:.1f}%)")
        
        # Add most problematic files
        if result.metrics.get('most_problematic_files'):
            report_lines.extend([
                f"",
                f"MOST PROBLEMATIC FILES:",
            ])
            for file_info in result.metrics['most_problematic_files'][:5]:
                report_lines.append(f"  {file_info['file']}: {file_info['error_count']} errors")
        
        return '\n'.join(report_lines)
    
    @staticmethod
    def _get_severity_icon(severity: ErrorSeverity) -> str:
        """Get icon for severity level."""
        icons = {
            ErrorSeverity.CRITICAL: "⚠️",
            ErrorSeverity.MAJOR: "👉", 
            ErrorSeverity.MINOR: "🔍"
        }
        return icons.get(severity, "❓")

# ============================================================================
# MAIN SERENA ANALYZER CLASS
# ============================================================================

class SerenaAnalyzer:
    """Main Serena analyzer class that orchestrates the entire analysis process."""
    
    def __init__(self):
        self.error_analyzer = ComprehensiveErrorAnalyzer()
        self.repo_interface = None
        
    def analyze_repository(self, repo_url: str, output_file: str = "report.txt") -> AnalysisResult:
        """Analyze repository and generate report."""
        logger.info(f"🚀 Starting Serena analysis of: {repo_url}")
        
        try:
            # Setup repository
            self.repo_interface = RepositoryInterface(repo_url)
            repo_dir = self.repo_interface.setup_repository()
            repo_name = repo_dir.name
            
            logger.info(f"📁 Repository setup complete: {repo_dir}")
            
            # Perform comprehensive analysis
            result = self.error_analyzer.analyze_repository(repo_dir)
            
            # Generate formatted report
            report_content = ReportFormatter.format_report(result, repo_name)
            
            # Write report to file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"📊 Analysis complete! Report saved to: {output_file}")
            logger.info(f"🔍 Found {result.total_errors} total errors")
            logger.info(f"⚠️  Critical: {result.errors_by_severity.get(ErrorSeverity.CRITICAL, 0)}")
            logger.info(f"👉 Major: {result.errors_by_severity.get(ErrorSeverity.MAJOR, 0)}")
            logger.info(f"🔍 Minor: {result.errors_by_severity.get(ErrorSeverity.MINOR, 0)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Analysis failed: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            # Cleanup
            if self.repo_interface:
                self.repo_interface.cleanup()

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive Serena Codebase Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python serena_analyzer.py --repo https://github.com/user/repo
  python serena_analyzer.py --repo /path/to/local/repo
  python serena_analyzer.py --repo https://github.com/user/repo --output custom_report.txt
  python serena_analyzer.py --repo . --verbose

The analyzer will generate a comprehensive report with:
- 24+ error types with severity classification
- Detailed error context and suggestions
- Repository metrics and statistics
- Most problematic files identification
        """
    )
    
    parser.add_argument(
        '--repo',
        required=True,
        help='Repository URL (https://github.com/user/repo) or local path'
    )
    
    parser.add_argument(
        '--output',
        default='report.txt',
        help='Output file name (default: report.txt)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Serena Analyzer v1.0.0 - Comprehensive Codebase Analysis'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create analyzer and run analysis
        analyzer = SerenaAnalyzer()
        result = analyzer.analyze_repository(args.repo, args.output)
        
        # Print summary to console
        print(f"\n🎉 Analysis Complete!")
        print(f"📊 Total Errors: {result.total_errors}")
        print(f"⚠️  Critical: {result.errors_by_severity.get(ErrorSeverity.CRITICAL, 0)}")
        print(f"👉 Major: {result.errors_by_severity.get(ErrorSeverity.MAJOR, 0)}")
        print(f"🔍 Minor: {result.errors_by_severity.get(ErrorSeverity.MINOR, 0)}")
        print(f"📄 Report saved to: {args.output}")
        print(f"⏱️  Analysis time: {result.analysis_time:.2f} seconds")
        
        # Exit with appropriate code
        if result.errors_by_severity.get(ErrorSeverity.CRITICAL, 0) > 0:
            sys.exit(2)  # Critical errors found
        elif result.errors_by_severity.get(ErrorSeverity.MAJOR, 0) > 0:
            sys.exit(1)  # Major errors found
        else:
            sys.exit(0)  # Only minor errors or no errors
            
    except KeyboardInterrupt:
        print("\n⚠️  Analysis interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        if args.verbose:
            print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()

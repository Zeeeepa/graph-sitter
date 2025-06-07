#!/usr/bin/env python3
"""
Unified Analysis Engine

Consolidated analysis system that uses official tree-sitter patterns and eliminates
fragmented functionality. This replaces the multiple analyzer modules with a single,
well-structured system that follows tree-sitter best practices.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field

from .core.tree_sitter_core import TreeSitterCore, get_tree_sitter_core, ParseResult
from .queries.python_queries import PythonQueries
from .queries.javascript_queries import JavaScriptQueries
from .queries.common_queries import CommonQueries

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Comprehensive analysis result."""
    
    file_path: str
    language: str
    parse_time: float
    has_errors: bool
    
    # Basic metrics
    line_metrics: Dict[str, int] = field(default_factory=dict)
    complexity_metrics: Dict[str, int] = field(default_factory=dict)
    
    # Code elements
    functions: List[Dict[str, Any]] = field(default_factory=list)
    classes: List[Dict[str, Any]] = field(default_factory=list)
    imports: List[Dict[str, Any]] = field(default_factory=list)
    
    # Quality metrics
    code_smells: List[Dict[str, Any]] = field(default_factory=list)
    error_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Additional analysis data
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodebaseAnalysisResult:
    """Result of analyzing an entire codebase."""
    
    codebase_path: str
    total_files: int
    analyzed_files: int
    analysis_time: float
    
    # Aggregated metrics
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    
    # Per-file results
    file_results: List[AnalysisResult] = field(default_factory=list)
    
    # Language distribution
    language_stats: Dict[str, int] = field(default_factory=dict)
    
    # Quality summary
    quality_summary: Dict[str, Any] = field(default_factory=dict)
    
    # Errors and warnings
    errors: List[str] = field(default_factory=list)


class UnifiedAnalyzer:
    """
    Unified analysis engine using official tree-sitter patterns.
    
    This class consolidates all analysis functionality and provides a clean,
    efficient interface that follows tree-sitter best practices.
    """
    
    def __init__(self, tree_sitter_core: Optional[TreeSitterCore] = None):
        """
        Initialize the unified analyzer.
        
        Args:
            tree_sitter_core: Optional tree-sitter core instance
        """
        self.core = tree_sitter_core or get_tree_sitter_core()
        self.logger = logging.getLogger(__name__)
        
        # Initialize language-specific query engines
        self.python_queries = PythonQueries(self.core)
        self.javascript_queries = JavaScriptQueries(self.core)
        self.common_queries = CommonQueries(self.core)
        
        # Supported file extensions
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.rs': 'rust',
            '.go': 'go',
        }
    
    def analyze_file(self, file_path: Union[str, Path], language: Optional[str] = None) -> Optional[AnalysisResult]:
        """
        Analyze a single file using tree-sitter.
        
        Args:
            file_path: Path to the file to analyze
            language: Programming language (auto-detected if None)
            
        Returns:
            AnalysisResult if successful, None otherwise
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            self.logger.error(f"File not found: {file_path}")
            return None
        
        # Parse the file
        parse_result = self.core.parse_file(file_path, language)
        if not parse_result:
            self.logger.error(f"Failed to parse {file_path}")
            return None
        
        self.logger.info(f"Analyzing {file_path} ({parse_result.language})")
        
        # Create analysis result
        result = AnalysisResult(
            file_path=str(file_path),
            language=parse_result.language,
            parse_time=parse_result.parse_time,
            has_errors=parse_result.has_errors
        )
        
        # Perform language-specific analysis
        if parse_result.language == 'python':
            self._analyze_python_file(parse_result, result)
        elif parse_result.language in ['javascript', 'typescript']:
            self._analyze_javascript_file(parse_result, result)
        else:
            self._analyze_generic_file(parse_result, result)
        
        # Perform common analysis
        self._analyze_common_patterns(parse_result, result)
        
        return result
    
    def _analyze_python_file(self, parse_result: ParseResult, result: AnalysisResult) -> None:
        """Analyze Python-specific patterns."""
        try:
            # Find functions
            functions = self.python_queries.find_functions(parse_result)
            for func_match in functions:
                func_name = self._extract_function_name(func_match, 'python')
                complexity = self.python_queries.analyze_function_complexity(
                    func_match.node, parse_result.source_code
                )
                
                result.functions.append({
                    'name': func_name,
                    'start_line': func_match.start_point[0] + 1,
                    'end_line': func_match.end_point[0] + 1,
                    'complexity': complexity,
                    'text': func_match.text[:200] + '...' if len(func_match.text) > 200 else func_match.text
                })
            
            # Find classes
            classes = self.python_queries.find_classes(parse_result)
            for class_match in classes:
                class_name = self._extract_class_name(class_match, 'python')
                
                result.classes.append({
                    'name': class_name,
                    'start_line': class_match.start_point[0] + 1,
                    'end_line': class_match.end_point[0] + 1,
                    'text': class_match.text[:200] + '...' if len(class_match.text) > 200 else class_match.text
                })
            
            # Find imports
            imports = self.python_queries.find_imports(parse_result)
            for import_match in imports:
                result.imports.append({
                    'text': import_match.text,
                    'line': import_match.start_point[0] + 1
                })
            
            # Find error patterns
            error_patterns = self.python_queries.find_error_patterns(parse_result)
            for error_match in error_patterns:
                result.error_patterns.append({
                    'type': 'python_error_pattern',
                    'line': error_match.start_point[0] + 1,
                    'description': f"Potential issue: {error_match.text[:100]}..."
                })
            
            # Calculate complexity metrics
            complexity_patterns = self.python_queries.find_complexity_patterns(parse_result)
            result.complexity_metrics = {
                'total_complexity_patterns': len(complexity_patterns),
                'cyclomatic_complexity': len(complexity_patterns) + 1,  # Base complexity
                'functions_count': len(result.functions),
                'classes_count': len(result.classes)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing Python file: {e}")
    
    def _analyze_javascript_file(self, parse_result: ParseResult, result: AnalysisResult) -> None:
        """Analyze JavaScript/TypeScript-specific patterns."""
        try:
            # Find functions
            functions = self.javascript_queries.find_functions(parse_result)
            for func_match in functions:
                func_name = self._extract_function_name(func_match, 'javascript')
                
                result.functions.append({
                    'name': func_name,
                    'start_line': func_match.start_point[0] + 1,
                    'end_line': func_match.end_point[0] + 1,
                    'text': func_match.text[:200] + '...' if len(func_match.text) > 200 else func_match.text
                })
            
            # Find classes
            classes = self.javascript_queries.find_classes(parse_result)
            for class_match in classes:
                class_name = self._extract_class_name(class_match, 'javascript')
                
                result.classes.append({
                    'name': class_name,
                    'start_line': class_match.start_point[0] + 1,
                    'end_line': class_match.end_point[0] + 1,
                    'text': class_match.text[:200] + '...' if len(class_match.text) > 200 else class_match.text
                })
            
            # Find async patterns
            async_patterns = self.javascript_queries.find_async_patterns(parse_result)
            result.metadata['async_patterns'] = len(async_patterns)
            
            # Find error patterns
            error_patterns = self.javascript_queries.find_error_patterns(parse_result)
            for error_match in error_patterns:
                result.error_patterns.append({
                    'type': 'javascript_error_pattern',
                    'line': error_match.start_point[0] + 1,
                    'description': f"Potential issue: {error_match.text[:100]}..."
                })
            
            # Calculate complexity metrics
            complexity_patterns = self.javascript_queries.find_complexity_patterns(parse_result)
            result.complexity_metrics = {
                'total_complexity_patterns': len(complexity_patterns),
                'cyclomatic_complexity': len(complexity_patterns) + 1,
                'functions_count': len(result.functions),
                'classes_count': len(result.classes),
                'async_patterns': len(async_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing JavaScript file: {e}")
    
    def _analyze_generic_file(self, parse_result: ParseResult, result: AnalysisResult) -> None:
        """Analyze files with generic patterns when language-specific analysis isn't available."""
        try:
            # Basic node counting
            node_counts = {}
            
            def count_nodes(node):
                node_type = node.type
                node_counts[node_type] = node_counts.get(node_type, 0) + 1
                for child in node.children:
                    count_nodes(child)
            
            count_nodes(parse_result.tree.root_node)
            
            result.metadata['node_counts'] = node_counts
            result.complexity_metrics = {
                'total_nodes': sum(node_counts.values()),
                'unique_node_types': len(node_counts)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing generic file: {e}")
    
    def _analyze_common_patterns(self, parse_result: ParseResult, result: AnalysisResult) -> None:
        """Analyze common patterns across all languages."""
        try:
            # Calculate line metrics
            result.line_metrics = self.common_queries.calculate_file_metrics(parse_result)
            
            # Find large functions
            large_functions = self.common_queries.find_large_functions(
                parse_result, parse_result.language, line_threshold=50
            )
            
            for large_func in large_functions:
                result.code_smells.append({
                    'type': 'large_function',
                    'line': large_func.start_point[0] + 1,
                    'description': f"Function is too large ({large_func.end_point[0] - large_func.start_point[0] + 1} lines)"
                })
            
        except Exception as e:
            self.logger.error(f"Error analyzing common patterns: {e}")
    
    def _extract_function_name(self, func_match, language: str) -> str:
        """Extract function name from a function match."""
        if 'function.name' in func_match.captures:
            name_node = func_match.captures['function.name']
            return name_node.text.decode('utf-8', errors='ignore')
        elif 'method.name' in func_match.captures:
            name_node = func_match.captures['method.name']
            return name_node.text.decode('utf-8', errors='ignore')
        else:
            return '<anonymous>'
    
    def _extract_class_name(self, class_match, language: str) -> str:
        """Extract class name from a class match."""
        if 'class.name' in class_match.captures:
            name_node = class_match.captures['class.name']
            return name_node.text.decode('utf-8', errors='ignore')
        else:
            return '<anonymous>'
    
    def analyze_codebase(self, codebase_path: Union[str, Path], 
                        include_patterns: Optional[List[str]] = None,
                        exclude_patterns: Optional[List[str]] = None) -> CodebaseAnalysisResult:
        """
        Analyze an entire codebase.
        
        Args:
            codebase_path: Path to the codebase root
            include_patterns: File patterns to include (e.g., ['*.py', '*.js'])
            exclude_patterns: File patterns to exclude (e.g., ['*test*', '*__pycache__*'])
            
        Returns:
            CodebaseAnalysisResult with aggregated analysis
        """
        codebase_path = Path(codebase_path)
        start_time = time.time()
        
        self.logger.info(f"Starting codebase analysis: {codebase_path}")
        
        # Find files to analyze
        files_to_analyze = self._find_files_to_analyze(
            codebase_path, include_patterns, exclude_patterns
        )
        
        result = CodebaseAnalysisResult(
            codebase_path=str(codebase_path),
            total_files=len(files_to_analyze),
            analyzed_files=0,
            analysis_time=0.0
        )
        
        # Analyze each file
        for file_path in files_to_analyze:
            try:
                file_result = self.analyze_file(file_path)
                if file_result:
                    result.file_results.append(file_result)
                    result.analyzed_files += 1
                    
                    # Update aggregated metrics
                    result.total_lines += file_result.line_metrics.get('total_lines', 0)
                    result.total_functions += len(file_result.functions)
                    result.total_classes += len(file_result.classes)
                    
                    # Update language stats
                    lang = file_result.language
                    result.language_stats[lang] = result.language_stats.get(lang, 0) + 1
                    
            except Exception as e:
                self.logger.error(f"Error analyzing {file_path}: {e}")
                result.errors.append(f"Failed to analyze {file_path}: {e}")
        
        result.analysis_time = time.time() - start_time
        
        # Calculate quality summary
        result.quality_summary = self._calculate_quality_summary(result)
        
        self.logger.info(f"Codebase analysis completed: {result.analyzed_files}/{result.total_files} files")
        
        return result
    
    def _find_files_to_analyze(self, codebase_path: Path, 
                              include_patterns: Optional[List[str]] = None,
                              exclude_patterns: Optional[List[str]] = None) -> List[Path]:
        """Find files to analyze based on patterns."""
        files = []
        
        # Default include patterns based on supported extensions
        if include_patterns is None:
            include_patterns = [f"*{ext}" for ext in self.supported_extensions.keys()]
        
        # Default exclude patterns
        if exclude_patterns is None:
            exclude_patterns = [
                '*__pycache__*', '*.pyc', '*node_modules*', '*.min.js',
                '*test*', '*spec*', '*.d.ts', '*build*', '*dist*'
            ]
        
        for pattern in include_patterns:
            for file_path in codebase_path.rglob(pattern):
                if file_path.is_file():
                    # Check exclude patterns
                    should_exclude = False
                    for exclude_pattern in exclude_patterns:
                        if file_path.match(exclude_pattern):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        files.append(file_path)
        
        return files
    
    def _calculate_quality_summary(self, result: CodebaseAnalysisResult) -> Dict[str, Any]:
        """Calculate quality summary metrics."""
        if not result.file_results:
            return {}
        
        total_code_smells = sum(len(fr.code_smells) for fr in result.file_results)
        total_error_patterns = sum(len(fr.error_patterns) for fr in result.file_results)
        files_with_errors = sum(1 for fr in result.file_results if fr.has_errors)
        
        avg_complexity = 0
        if result.file_results:
            complexities = [
                fr.complexity_metrics.get('cyclomatic_complexity', 1) 
                for fr in result.file_results
            ]
            avg_complexity = sum(complexities) / len(complexities)
        
        return {
            'total_code_smells': total_code_smells,
            'total_error_patterns': total_error_patterns,
            'files_with_parse_errors': files_with_errors,
            'average_complexity': avg_complexity,
            'quality_score': max(0, 100 - (total_code_smells * 2) - (total_error_patterns * 3) - (files_with_errors * 5))
        }


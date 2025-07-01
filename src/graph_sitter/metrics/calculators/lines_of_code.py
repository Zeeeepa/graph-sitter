"""Lines of Code Calculator.

from typing import TYPE_CHECKING, Optional, Dict, Any, Tuple
import re

from ..core.base_calculator import BaseMetricsCalculator

from __future__ import annotations
from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.metrics.models.metrics_data import (

Calculates various lines of code metrics including:
- Total Lines of Code (LOC)
- Logical Lines of Code (LLOC) 
- Source Lines of Code (SLOC)
- Comment Lines
- Blank Lines
- Comment Ratio Analysis

These metrics provide insights into code size, documentation quality,
and overall code structure.
"""

if TYPE_CHECKING:
        FunctionMetrics,
        ClassMetrics,
        FileMetrics,
        CodebaseMetrics,
    )

class LinesOfCodeCalculator(BaseMetricsCalculator):
    """Calculator for various lines of code metrics."""
    
    @property
    def name(self) -> str:
        return "lines_of_code"
    
    @property
    def description(self) -> str:
        return "Calculates total, logical, source, comment, and blank lines of code"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration options
        self.count_empty_lines = self.config.get("count_empty_lines", True)
        self.count_comment_only_lines = self.config.get("count_comment_only_lines", True)
        self.count_docstrings_as_comments = self.config.get("count_docstrings_as_comments", True)
        self.exclude_generated_code = self.config.get("exclude_generated_code", True)
        
        # Language-specific comment patterns
        self.comment_patterns = {
            "python": {
                "single_line": [r'#.*$'],
                "multi_line_start": [r'"""', r"'''"],
                "multi_line_end": [r'"""', r"'''"],
                "docstring": [r'""".*?"""', r"'''.*?'''"],
            },
            "javascript": {
                "single_line": [r'//.*$'],
                "multi_line_start": [r'/\*'],
                "multi_line_end": [r'\*/'],
                "docstring": [r'/\*\*.*?\*/'],
            },
            "typescript": {
                "single_line": [r'//.*$'],
                "multi_line_start": [r'/\*'],
                "multi_line_end": [r'\*/'],
                "docstring": [r'/\*\*.*?\*/'],
            },
            "java": {
                "single_line": [r'//.*$'],
                "multi_line_start": [r'/\*'],
                "multi_line_end": [r'\*/'],
                "docstring": [r'/\*\*.*?\*/'],
            },
            "cpp": {
                "single_line": [r'//.*$'],
                "multi_line_start": [r'/\*'],
                "multi_line_end": [r'\*/'],
                "docstring": [r'/\*\*.*?\*/'],
            },
            "c": {
                "single_line": [r'//.*$'],
                "multi_line_start": [r'/\*'],
                "multi_line_end": [r'\*/'],
                "docstring": [],
            },
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if this calculator supports the given language."""
        return language.lower() in self.comment_patterns
    
    def _analyze_lines(self, code: str, language: str = "python") -> Tuple[int, int, int, int, int]:
        """Analyze lines of code and return various metrics.
        
        Args:
            code: Source code to analyze.
            language: Programming language.
            
        Returns:
            Tuple of (total_lines, logical_lines, source_lines, comment_lines, blank_lines).
        """
        if not code:
            return 0, 0, 0, 0, 0
        
        lines = code.split('\n')
        total_lines = len(lines)
        
        logical_lines = 0
        source_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        language = language.lower()
        patterns = self.comment_patterns.get(language, self.comment_patterns["python"])
        
        in_multiline_comment = False
        multiline_comment_end_pattern = None
        
        for line in lines:
            stripped_line = line.strip()
            
            # Check for blank lines
            if not stripped_line:
                blank_lines += 1
                continue
            
            # Check for multi-line comment continuation
            if in_multiline_comment:
                comment_lines += 1
                # Check if this line ends the multi-line comment
                if multiline_comment_end_pattern and re.search(multiline_comment_end_pattern, line):
                    in_multiline_comment = False
                    multiline_comment_end_pattern = None
                continue
            
            # Check for multi-line comment start
            multiline_started = False
            for start_pattern in patterns.get("multi_line_start", []):
                if re.search(start_pattern, line):
                    in_multiline_comment = True
                    multiline_started = True
                    comment_lines += 1
                    
                    # Find corresponding end pattern
                    if language == "python":
                        if '"""' in line:
                            multiline_comment_end_pattern = r'"""'
                        elif "'''" in line:
                            multiline_comment_end_pattern = r"'''"
                        
                        # Check if comment ends on same line
                        if line.count('"""') >= 2 or line.count("'''") >= 2:
                            in_multiline_comment = False
                            multiline_comment_end_pattern = None
                    else:
                        multiline_comment_end_pattern = r'\*/'
                        # Check if comment ends on same line
                        if re.search(r'/\*.*?\*/', line):
                            in_multiline_comment = False
                            multiline_comment_end_pattern = None
                    break
            
            if multiline_started:
                continue
            
            # Check for single-line comments
            is_comment_line = False
            for comment_pattern in patterns.get("single_line", []):
                if re.match(r'^\s*' + comment_pattern, line):
                    is_comment_line = True
                    comment_lines += 1
                    break
            
            if is_comment_line:
                continue
            
            # Check for docstrings (Python)
            if language == "python" and self.count_docstrings_as_comments:
                if re.match(r'^\s*(""".*?"""|\'\'\'.*?\'\'\')', line, re.DOTALL):
                    comment_lines += 1
                    continue
            
            # If we get here, it's a source line
            source_lines += 1
            
            # Check if it's a logical line (contains meaningful code)
            if self._is_logical_line(stripped_line, language):
                logical_lines += 1
        
        return total_lines, logical_lines, source_lines, comment_lines, blank_lines
    
    def _is_logical_line(self, line: str, language: str) -> bool:
        """Determine if a line contains logical code.
        
        Args:
            line: Stripped line of code.
            language: Programming language.
            
        Returns:
            True if the line contains logical code.
        """
        if not line:
            return False
        
        # Language-specific logical line patterns
        if language == "python":
            # Exclude lines that are only structural (like lone colons, pass statements)
            if line in [':', 'pass', '...', 'Ellipsis']:
                return False
            # Exclude import statements if configured
            if line.startswith(('import ', 'from ')):
                return True  # Imports are considered logical
            
        elif language in ["javascript", "typescript", "java", "cpp", "c"]:
            # Exclude lines that are only braces or semicolons
            if line in ['{', '}', ';']:
                return False
            # Exclude preprocessor directives in C/C++
            if language in ["cpp", "c"] and line.startswith('#'):
                return False
        
        # Check for generated code markers
        if self.exclude_generated_code:
            generated_markers = [
                'auto-generated', 'generated automatically', 'do not edit',
                'autogenerated', 'code generated', 'automatically created'
            ]
            line_lower = line.lower()
            if any(marker in line_lower for marker in generated_markers):
                return False
        
        return True
    
    def _get_function_code(self, function: Function) -> str:
        """Extract source code for a function."""
        try:
            if hasattr(function, 'source_code'):
                return function.source_code
            elif hasattr(function, 'code_block') and function.code_block:
                return str(function.code_block)
            elif hasattr(function, 'body') and function.body:
                return str(function.body)
            else:
                if hasattr(function, 'file') and function.file:
                    file_content = self._get_file_content(function.file)
                    if file_content and hasattr(function, 'start_line') and hasattr(function, 'end_line'):
                        lines = file_content.split('\n')
                        start_idx = max(0, function.start_line - 1)
                        end_idx = min(len(lines), function.end_line)
                        return '\n'.join(lines[start_idx:end_idx])
                return ""
        except Exception as e:
            self.add_warning(f"Could not extract code for function {function.name}: {str(e)}")
            return ""
    
    def _get_class_code(self, class_def: Class) -> str:
        """Extract source code for a class."""
        try:
            if hasattr(class_def, 'source_code'):
                return class_def.source_code
            elif hasattr(class_def, 'code_block') and class_def.code_block:
                return str(class_def.code_block)
            elif hasattr(class_def, 'body') and class_def.body:
                return str(class_def.body)
            else:
                if hasattr(class_def, 'file') and class_def.file:
                    file_content = self._get_file_content(class_def.file)
                    if file_content and hasattr(class_def, 'start_line') and hasattr(class_def, 'end_line'):
                        lines = file_content.split('\n')
                        start_idx = max(0, class_def.start_line - 1)
                        end_idx = min(len(lines), class_def.end_line)
                        return '\n'.join(lines[start_idx:end_idx])
                return ""
        except Exception as e:
            self.add_warning(f"Could not extract code for class {class_def.name}: {str(e)}")
            return ""
    
    def _get_file_content(self, file: SourceFile) -> str:
        """Get the content of a source file."""
        try:
            if hasattr(file, 'content'):
                return file.content
            elif hasattr(file, 'source_code'):
                return file.source_code
            elif hasattr(file, 'path'):
                with open(file.path, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            self.add_warning(f"Could not read file content for {getattr(file, 'path', 'unknown')}: {str(e)}")
            return ""
    
    def _detect_language_from_file(self, file: SourceFile) -> str:
        """Detect programming language from file extension."""
        if not hasattr(file, 'path'):
            return "python"
        
        path_str = str(file.path).lower()
        
        if path_str.endswith('.py'):
            return "python"
        elif path_str.endswith(('.js', '.jsx')):
            return "javascript"
        elif path_str.endswith(('.ts', '.tsx')):
            return "typescript"
        elif path_str.endswith('.java'):
            return "java"
        elif path_str.endswith(('.cpp', '.cc', '.cxx')):
            return "cpp"
        elif path_str.endswith('.c'):
            return "c"
        
        return "python"  # Default fallback
    
    def _calculate_function_metrics(
        self, 
        function: Function, 
        existing_metrics: Optional[FunctionMetrics] = None
    ) -> Optional[FunctionMetrics]:
        """Calculate lines of code metrics for a function."""
        if existing_metrics is None:
            return None
        
        try:
            # Get function source code
            code = self._get_function_code(function)
            if not code:
                self.add_warning(f"No source code found for function {function.name}")
                return existing_metrics
            
            # Detect language
            language = self._detect_language_from_file(function.file) if function.file else "python"
            
            # Analyze lines
            total_lines, logical_lines, source_lines, comment_lines, blank_lines = self._analyze_lines(code, language)
            
            # Update metrics
            existing_metrics.total_lines = total_lines
            existing_metrics.logical_lines = logical_lines
            existing_metrics.source_lines = source_lines
            existing_metrics.comment_lines = comment_lines
            existing_metrics.blank_lines = blank_lines
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating lines of code for function {function.name}: {str(e)}")
            return existing_metrics
    
    def _calculate_class_metrics(
        self, 
        class_def: Class, 
        existing_metrics: Optional[ClassMetrics] = None
    ) -> Optional[ClassMetrics]:
        """Calculate lines of code metrics for a class."""
        if existing_metrics is None:
            return None
        
        try:
            # Get class source code
            code = self._get_class_code(class_def)
            if not code:
                self.add_warning(f"No source code found for class {class_def.name}")
                return existing_metrics
            
            # Detect language
            language = self._detect_language_from_file(class_def.file) if class_def.file else "python"
            
            # Analyze lines
            total_lines, logical_lines, source_lines, comment_lines, blank_lines = self._analyze_lines(code, language)
            
            # Update metrics
            existing_metrics.total_lines = total_lines
            existing_metrics.logical_lines = logical_lines
            existing_metrics.source_lines = source_lines
            existing_metrics.comment_lines = comment_lines
            existing_metrics.blank_lines = blank_lines
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating lines of code for class {class_def.name}: {str(e)}")
            return existing_metrics
    
    def _calculate_file_metrics(
        self, 
        file: SourceFile, 
        existing_metrics: Optional[FileMetrics] = None
    ) -> Optional[FileMetrics]:
        """Calculate lines of code metrics for a file."""
        if existing_metrics is None:
            return None
        
        try:
            # Get file content
            content = self._get_file_content(file)
            if not content:
                self.add_warning(f"No content found for file {getattr(file, 'path', 'unknown')}")
                return existing_metrics
            
            # Detect language
            language = self._detect_language_from_file(file)
            
            # Analyze lines
            total_lines, logical_lines, source_lines, comment_lines, blank_lines = self._analyze_lines(content, language)
            
            # Update metrics
            existing_metrics.total_lines = total_lines
            existing_metrics.logical_lines = logical_lines
            existing_metrics.source_lines = source_lines
            existing_metrics.comment_lines = comment_lines
            existing_metrics.blank_lines = blank_lines
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating lines of code for file {getattr(file, 'path', 'unknown')}: {str(e)}")
            return existing_metrics
    
    def _calculate_codebase_metrics(
        self, 
        codebase: Codebase, 
        existing_metrics: Optional[CodebaseMetrics] = None
    ) -> Optional[CodebaseMetrics]:
        """Calculate lines of code metrics for the entire codebase."""
        if existing_metrics is None:
            return None
        
        try:
            # Codebase lines of code will be aggregated from file metrics
            # This is handled in the metrics engine aggregation step
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating lines of code for codebase: {str(e)}")
            return existing_metrics
    
    def get_lines_analysis(self, metrics) -> Dict[str, Any]:
        """Get detailed analysis of lines of code metrics.
        
        Args:
            metrics: Metrics object with line counts.
            
        Returns:
            Dictionary with detailed analysis.
        """
        total_lines = getattr(metrics, 'total_lines', 0)
        logical_lines = getattr(metrics, 'logical_lines', 0)
        source_lines = getattr(metrics, 'source_lines', 0)
        comment_lines = getattr(metrics, 'comment_lines', 0)
        blank_lines = getattr(metrics, 'blank_lines', 0)
        
        analysis = {
            "total_lines": total_lines,
            "logical_lines": logical_lines,
            "source_lines": source_lines,
            "comment_lines": comment_lines,
            "blank_lines": blank_lines,
        }
        
        if total_lines > 0:
            analysis.update({
                "comment_ratio": comment_lines / total_lines,
                "blank_ratio": blank_lines / total_lines,
                "source_ratio": source_lines / total_lines,
                "logical_ratio": logical_lines / total_lines,
            })
        else:
            analysis.update({
                "comment_ratio": 0.0,
                "blank_ratio": 0.0,
                "source_ratio": 0.0,
                "logical_ratio": 0.0,
            })
        
        # Quality indicators
        if analysis["comment_ratio"] >= 0.2:
            analysis["documentation_quality"] = "good"
        elif analysis["comment_ratio"] >= 0.1:
            analysis["documentation_quality"] = "moderate"
        else:
            analysis["documentation_quality"] = "poor"
        
        if analysis["logical_ratio"] >= 0.7:
            analysis["code_density"] = "high"
        elif analysis["logical_ratio"] >= 0.5:
            analysis["code_density"] = "moderate"
        else:
            analysis["code_density"] = "low"
        
        return analysis
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for this calculator."""
        return {
            "type": "object",
            "properties": {
                "count_empty_lines": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to count empty lines in total line count"
                },
                "count_comment_only_lines": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to count comment-only lines in total line count"
                },
                "count_docstrings_as_comments": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to count docstrings as comment lines"
                },
                "exclude_generated_code": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to exclude auto-generated code from metrics"
                }
            },
            "additionalProperties": False
        }

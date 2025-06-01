"""Cyclomatic Complexity Calculator.

Calculates cyclomatic complexity for functions, classes, files, and codebases.
Cyclomatic complexity measures the number of linearly independent paths through
a program's source code.

Formula: CC = E - N + 2P
Where:
- E = number of edges in the control flow graph
- N = number of nodes in the control flow graph  
- P = number of connected components (usually 1 for a single function)

Simplified approach: CC = 1 + number of decision points
Decision points include: if, elif, while, for, try/except, and, or, etc.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Set, Any, Dict
import re

from ..core.base_calculator import BaseMetricsCalculator

if TYPE_CHECKING:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import Class
    from graph_sitter.metrics.models.metrics_data import (
        FunctionMetrics,
        ClassMetrics,
        FileMetrics,
        CodebaseMetrics,
    )


class CyclomaticComplexityCalculator(BaseMetricsCalculator):
    """Calculator for cyclomatic complexity metrics."""
    
    @property
    def name(self) -> str:
        return "cyclomatic_complexity"
    
    @property
    def description(self) -> str:
        return "Calculates cyclomatic complexity based on control flow decision points"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration options
        self.count_boolean_operators = self.config.get("count_boolean_operators", True)
        self.count_exception_handlers = self.config.get("count_exception_handlers", True)
        self.count_case_statements = self.config.get("count_case_statements", True)
        self.count_ternary_operators = self.config.get("count_ternary_operators", True)
        
        # Language-specific decision point patterns
        self.decision_patterns = {
            "python": {
                "if_statements": [r"\bif\b", r"\belif\b"],
                "loops": [r"\bfor\b", r"\bwhile\b"],
                "boolean_operators": [r"\band\b", r"\bor\b"] if self.count_boolean_operators else [],
                "exception_handling": [r"\btry\b", r"\bexcept\b", r"\bfinally\b"] if self.count_exception_handlers else [],
                "ternary": [r"\bif\b.*\belse\b"] if self.count_ternary_operators else [],
                "comprehensions": [r"\bfor\b.*\bin\b", r"\bif\b.*\bfor\b"],
            },
            "javascript": {
                "if_statements": [r"\bif\b"],
                "loops": [r"\bfor\b", r"\bwhile\b", r"\bdo\b"],
                "boolean_operators": [r"&&", r"\|\|"] if self.count_boolean_operators else [],
                "exception_handling": [r"\btry\b", r"\bcatch\b", r"\bfinally\b"] if self.count_exception_handlers else [],
                "switch_case": [r"\bcase\b"] if self.count_case_statements else [],
                "ternary": [r"\?.*:"] if self.count_ternary_operators else [],
            },
            "typescript": {
                "if_statements": [r"\bif\b"],
                "loops": [r"\bfor\b", r"\bwhile\b", r"\bdo\b"],
                "boolean_operators": [r"&&", r"\|\|"] if self.count_boolean_operators else [],
                "exception_handling": [r"\btry\b", r"\bcatch\b", r"\bfinally\b"] if self.count_exception_handlers else [],
                "switch_case": [r"\bcase\b"] if self.count_case_statements else [],
                "ternary": [r"\?.*:"] if self.count_ternary_operators else [],
            },
            "java": {
                "if_statements": [r"\bif\b"],
                "loops": [r"\bfor\b", r"\bwhile\b", r"\bdo\b"],
                "boolean_operators": [r"&&", r"\|\|"] if self.count_boolean_operators else [],
                "exception_handling": [r"\btry\b", r"\bcatch\b", r"\bfinally\b"] if self.count_exception_handlers else [],
                "switch_case": [r"\bcase\b"] if self.count_case_statements else [],
                "ternary": [r"\?.*:"] if self.count_ternary_operators else [],
            },
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if this calculator supports the given language."""
        return language.lower() in self.decision_patterns
    
    def _calculate_complexity_from_code(self, code: str, language: str = "python") -> int:
        """Calculate cyclomatic complexity from source code.
        
        Args:
            code: Source code to analyze.
            language: Programming language.
            
        Returns:
            Cyclomatic complexity value.
        """
        if not code or not code.strip():
            return 1  # Base complexity
        
        language = language.lower()
        patterns = self.decision_patterns.get(language, self.decision_patterns["python"])
        
        complexity = 1  # Base complexity
        
        # Remove comments and strings to avoid false positives
        cleaned_code = self._clean_code(code, language)
        
        # Count decision points
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, cleaned_code, re.IGNORECASE | re.MULTILINE)
                complexity += len(matches)
        
        return complexity
    
    def _clean_code(self, code: str, language: str) -> str:
        """Remove comments and string literals to avoid false positives.
        
        Args:
            code: Source code to clean.
            language: Programming language.
            
        Returns:
            Cleaned code.
        """
        if language == "python":
            # Remove Python comments and strings
            # This is a simplified approach - a full parser would be more accurate
            lines = []
            for line in code.split('\n'):
                # Remove comments (but not in strings)
                if '#' in line:
                    # Simple heuristic: if # is not in quotes, remove everything after it
                    in_string = False
                    quote_char = None
                    for i, char in enumerate(line):
                        if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                            if not in_string:
                                in_string = True
                                quote_char = char
                            elif char == quote_char:
                                in_string = False
                                quote_char = None
                        elif char == '#' and not in_string:
                            line = line[:i]
                            break
                
                # Remove string literals (simplified)
                line = re.sub(r'""".*?"""', '', line, flags=re.DOTALL)
                line = re.sub(r"'''.*?'''", '', line, flags=re.DOTALL)
                line = re.sub(r'"[^"]*"', '', line)
                line = re.sub(r"'[^']*'", '', line)
                
                lines.append(line)
            
            return '\n'.join(lines)
        
        elif language in ["javascript", "typescript", "java"]:
            # Remove C-style comments and strings
            # Remove single-line comments
            code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
            # Remove multi-line comments
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            # Remove string literals
            code = re.sub(r'"[^"]*"', '', code)
            code = re.sub(r"'[^']*'", '', code)
            code = re.sub(r'`[^`]*`', '', code)  # Template literals
            
            return code
        
        return code
    
    def _get_function_code(self, function: Function) -> str:
        """Extract source code for a function.
        
        Args:
            function: Function to extract code from.
            
        Returns:
            Function source code.
        """
        try:
            # Try to get the function's source code
            if hasattr(function, 'source_code'):
                return function.source_code
            elif hasattr(function, 'code_block') and function.code_block:
                return str(function.code_block)
            elif hasattr(function, 'body') and function.body:
                return str(function.body)
            else:
                # Fallback: try to extract from file
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
        """Extract source code for a class.
        
        Args:
            class_def: Class to extract code from.
            
        Returns:
            Class source code.
        """
        try:
            # Try to get the class's source code
            if hasattr(class_def, 'source_code'):
                return class_def.source_code
            elif hasattr(class_def, 'code_block') and class_def.code_block:
                return str(class_def.code_block)
            elif hasattr(class_def, 'body') and class_def.body:
                return str(class_def.body)
            else:
                # Fallback: try to extract from file
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
        """Get the content of a source file.
        
        Args:
            file: Source file to read.
            
        Returns:
            File content as string.
        """
        try:
            if hasattr(file, 'content'):
                return file.content
            elif hasattr(file, 'source_code'):
                return file.source_code
            elif hasattr(file, 'path'):
                # Try to read from filesystem
                with open(file.path, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            self.add_warning(f"Could not read file content for {getattr(file, 'path', 'unknown')}: {str(e)}")
            return ""
    
    def _detect_language_from_file(self, file: SourceFile) -> str:
        """Detect programming language from file extension.
        
        Args:
            file: Source file to analyze.
            
        Returns:
            Detected language name.
        """
        if not hasattr(file, 'path'):
            return "python"  # Default
        
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
        elif path_str.endswith('.cs'):
            return "csharp"
        
        return "python"  # Default fallback
    
    def _calculate_function_metrics(
        self, 
        function: Function, 
        existing_metrics: Optional[FunctionMetrics] = None
    ) -> Optional[FunctionMetrics]:
        """Calculate cyclomatic complexity for a function."""
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
            
            # Calculate complexity
            complexity = self._calculate_complexity_from_code(code, language)
            existing_metrics.cyclomatic_complexity = complexity
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating cyclomatic complexity for function {function.name}: {str(e)}")
            return existing_metrics
    
    def _calculate_class_metrics(
        self, 
        class_def: Class, 
        existing_metrics: Optional[ClassMetrics] = None
    ) -> Optional[ClassMetrics]:
        """Calculate cyclomatic complexity for a class."""
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
            
            # Calculate complexity for the class itself
            complexity = self._calculate_complexity_from_code(code, language)
            
            # Add complexity from methods (already calculated in function metrics)
            method_complexity = sum(m.cyclomatic_complexity for m in existing_metrics.function_metrics)
            
            # Total class complexity is class-level + method-level complexity
            existing_metrics.cyclomatic_complexity = complexity + method_complexity
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating cyclomatic complexity for class {class_def.name}: {str(e)}")
            return existing_metrics
    
    def _calculate_file_metrics(
        self, 
        file: SourceFile, 
        existing_metrics: Optional[FileMetrics] = None
    ) -> Optional[FileMetrics]:
        """Calculate cyclomatic complexity for a file."""
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
            
            # Calculate file-level complexity
            file_complexity = self._calculate_complexity_from_code(content, language)
            
            # Add complexity from functions and classes (already calculated)
            function_complexity = sum(f.cyclomatic_complexity for f in existing_metrics.function_metrics)
            class_complexity = sum(c.cyclomatic_complexity for c in existing_metrics.class_metrics)
            
            # Total file complexity includes file-level + function/class complexity
            existing_metrics.cyclomatic_complexity = file_complexity + function_complexity + class_complexity
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating cyclomatic complexity for file {getattr(file, 'path', 'unknown')}: {str(e)}")
            return existing_metrics
    
    def _calculate_codebase_metrics(
        self, 
        codebase: Codebase, 
        existing_metrics: Optional[CodebaseMetrics] = None
    ) -> Optional[CodebaseMetrics]:
        """Calculate cyclomatic complexity for the entire codebase."""
        if existing_metrics is None:
            return None
        
        try:
            # Codebase complexity will be aggregated from file metrics
            # This is handled in the metrics engine aggregation step
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating cyclomatic complexity for codebase: {str(e)}")
            return existing_metrics
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for this calculator."""
        return {
            "type": "object",
            "properties": {
                "count_boolean_operators": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to count boolean operators (and, or, &&, ||) as decision points"
                },
                "count_exception_handlers": {
                    "type": "boolean", 
                    "default": True,
                    "description": "Whether to count exception handlers (try, catch, except) as decision points"
                },
                "count_case_statements": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to count case statements in switch blocks as decision points"
                },
                "count_ternary_operators": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to count ternary operators (? :) as decision points"
                }
            },
            "additionalProperties": False
        }


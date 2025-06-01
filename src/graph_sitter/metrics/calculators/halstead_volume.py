"""Halstead Volume Calculator.

from collections import Counter
from typing import TYPE_CHECKING, Optional, Set, Dict, List, Any
import math
import re

from ..core.base_calculator import BaseMetricsCalculator
from ..models.metrics_data import HalsteadMetrics

from __future__ import annotations
from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.metrics.models.metrics_data import (

Calculates Halstead complexity metrics including volume, difficulty, and effort.
Halstead metrics are based on the count of operators and operands in the code.

Key metrics:
- n1: number of distinct operators
- n2: number of distinct operands
- N1: total number of operators
- N2: total number of operands
- Volume: V = (N1 + N2) * log2(n1 + n2)
- Difficulty: D = (n1/2) * (N2/n2)
- Effort: E = D * V
"""

if TYPE_CHECKING:
        FunctionMetrics,
        ClassMetrics,
        FileMetrics,
        CodebaseMetrics,
    )

class HalsteadVolumeCalculator(BaseMetricsCalculator):
    """Calculator for Halstead complexity metrics."""
    
    @property
    def name(self) -> str:
        return "halstead_volume"
    
    @property
    def description(self) -> str:
        return "Calculates Halstead volume, difficulty, and effort metrics based on operators and operands"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration options
        self.include_keywords = self.config.get("include_keywords", True)
        self.include_literals = self.config.get("include_literals", True)
        self.include_identifiers = self.config.get("include_identifiers", True)
        
        # Language-specific operator and operand patterns
        self.language_patterns = {
            "python": {
                "operators": [
                    # Arithmetic operators
                    r'\+', r'-', r'\*', r'/', r'//', r'%', r'\*\*',
                    # Comparison operators
                    r'==', r'!=', r'<', r'>', r'<=', r'>=', r'is', r'in',
                    # Logical operators
                    r'\band\b', r'\bor\b', r'\bnot\b',
                    # Bitwise operators
                    r'&', r'\|', r'\^', r'~', r'<<', r'>>',
                    # Assignment operators
                    r'=', r'\+=', r'-=', r'\*=', r'/=', r'//=', r'%=', r'\*\*=',
                    r'&=', r'\|=', r'\^=', r'<<=', r'>>=',
                    # Other operators
                    r'\.', r'->', r'=>', r'::', r'@',
                    # Delimiters
                    r'\(', r'\)', r'\[', r'\]', r'\{', r'\}', r',', r':', r';',
                ],
                "keywords": [
                    r'\bdef\b', r'\bclass\b', r'\bif\b', r'\belif\b', r'\belse\b',
                    r'\bfor\b', r'\bwhile\b', r'\btry\b', r'\bexcept\b', r'\bfinally\b',
                    r'\bwith\b', r'\bas\b', r'\bimport\b', r'\bfrom\b', r'\breturn\b',
                    r'\byield\b', r'\braise\b', r'\bassert\b', r'\bbreak\b', r'\bcontinue\b',
                    r'\bpass\b', r'\blambda\b', r'\bglobal\b', r'\bnonlocal\b',
                    r'\bTrue\b', r'\bFalse\b', r'\bNone\b',
                ] if self.include_keywords else [],
                "literals": [
                    r'\b\d+\b',  # Numbers
                    r'"[^"]*"',  # String literals
                    r"'[^']*'",  # String literals
                    r'""".*?"""',  # Multi-line strings
                    r"'''.*?'''",  # Multi-line strings
                ] if self.include_literals else [],
                "identifiers": [
                    r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',  # Variable names, function names, etc.
                ] if self.include_identifiers else [],
            },
            "javascript": {
                "operators": [
                    # Arithmetic operators
                    r'\+', r'-', r'\*', r'/', r'%', r'\*\*',
                    # Comparison operators
                    r'===', r'!==', r'==', r'!=', r'<', r'>', r'<=', r'>=',
                    # Logical operators
                    r'&&', r'\|\|', r'!',
                    # Bitwise operators
                    r'&', r'\|', r'\^', r'~', r'<<', r'>>', r'>>>',
                    # Assignment operators
                    r'=', r'\+=', r'-=', r'\*=', r'/=', r'%=', r'\*\*=',
                    r'&=', r'\|=', r'\^=', r'<<=', r'>>=', r'>>>=',
                    # Other operators
                    r'\.', r'->', r'=>', r'\?', r':',
                    # Delimiters
                    r'\(', r'\)', r'\[', r'\]', r'\{', r'\}', r',', r';',
                ],
                "keywords": [
                    r'\bfunction\b', r'\bclass\b', r'\bif\b', r'\belse\b',
                    r'\bfor\b', r'\bwhile\b', r'\bdo\b', r'\btry\b', r'\bcatch\b', r'\bfinally\b',
                    r'\bswitch\b', r'\bcase\b', r'\bdefault\b', r'\breturn\b',
                    r'\bthrow\b', r'\bbreak\b', r'\bcontinue\b', r'\bvar\b', r'\blet\b', r'\bconst\b',
                    r'\btrue\b', r'\bfalse\b', r'\bnull\b', r'\bundefined\b',
                ] if self.include_keywords else [],
                "literals": [
                    r'\b\d+\.?\d*\b',  # Numbers
                    r'"[^"]*"',  # String literals
                    r"'[^']*'",  # String literals
                    r'`[^`]*`',  # Template literals
                ] if self.include_literals else [],
                "identifiers": [
                    r'\b[a-zA-Z_$][a-zA-Z0-9_$]*\b',  # Variable names, function names, etc.
                ] if self.include_identifiers else [],
            },
        }
        
        # Add TypeScript patterns (similar to JavaScript)
        self.language_patterns["typescript"] = self.language_patterns["javascript"].copy()
        
        # Add Java patterns (similar to JavaScript with some differences)
        self.language_patterns["java"] = {
            "operators": self.language_patterns["javascript"]["operators"],
            "keywords": [
                r'\bclass\b', r'\binterface\b', r'\bif\b', r'\belse\b',
                r'\bfor\b', r'\bwhile\b', r'\bdo\b', r'\btry\b', r'\bcatch\b', r'\bfinally\b',
                r'\bswitch\b', r'\bcase\b', r'\bdefault\b', r'\breturn\b',
                r'\bthrow\b', r'\bbreak\b', r'\bcontinue\b', r'\bpublic\b', r'\bprivate\b',
                r'\bprotected\b', r'\bstatic\b', r'\bfinal\b', r'\babstract\b',
                r'\btrue\b', r'\bfalse\b', r'\bnull\b',
            ] if self.include_keywords else [],
            "literals": self.language_patterns["javascript"]["literals"],
            "identifiers": [
                r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
            ] if self.include_identifiers else [],
        }
    
    def supports_language(self, language: str) -> bool:
        """Check if this calculator supports the given language."""
        return language.lower() in self.language_patterns
    
    def _calculate_halstead_metrics(self, code: str, language: str = "python") -> HalsteadMetrics:
        """Calculate Halstead metrics from source code.
        
        Args:
            code: Source code to analyze.
            language: Programming language.
            
        Returns:
            HalsteadMetrics object with calculated values.
        """
        if not code or not code.strip():
            return HalsteadMetrics()
        
        language = language.lower()
        patterns = self.language_patterns.get(language, self.language_patterns["python"])
        
        # Clean code (remove comments and string contents)
        cleaned_code = self._clean_code(code, language)
        
        # Count operators and operands
        operators = Counter()
        operands = Counter()
        
        # Count operators
        for pattern in patterns["operators"]:
            matches = re.findall(pattern, cleaned_code)
            for match in matches:
                operators[match] += 1
        
        # Count keywords (treated as operators)
        for pattern in patterns["keywords"]:
            matches = re.findall(pattern, cleaned_code, re.IGNORECASE)
            for match in matches:
                operators[match.lower()] += 1
        
        # Count literals (treated as operands)
        for pattern in patterns["literals"]:
            matches = re.findall(pattern, cleaned_code)
            for match in matches:
                # Normalize literals (e.g., all numbers become "NUMBER")
                if re.match(r'\d+', match):
                    operands["NUMBER"] += 1
                elif match.startswith('"') or match.startswith("'") or match.startswith('`'):
                    operands["STRING"] += 1
                else:
                    operands[match] += 1
        
        # Count identifiers (treated as operands)
        if patterns["identifiers"]:
            # Remove operators and keywords from identifier matching
            temp_code = cleaned_code
            for pattern in patterns["operators"] + patterns["keywords"]:
                temp_code = re.sub(pattern, ' ', temp_code, flags=re.IGNORECASE)
            
            for pattern in patterns["identifiers"]:
                matches = re.findall(pattern, temp_code)
                for match in matches:
                    # Filter out language keywords and built-ins
                    if not self._is_builtin_identifier(match, language):
                        operands[match] += 1
        
        # Calculate Halstead metrics
        n1 = len(operators)  # distinct operators
        n2 = len(operands)   # distinct operands
        N1 = sum(operators.values())  # total operators
        N2 = sum(operands.values())   # total operands
        
        return HalsteadMetrics(n1=n1, n2=n2, N1=N1, N2=N2)
    
    def _clean_code(self, code: str, language: str) -> str:
        """Remove comments and string contents to avoid false positives.
        
        Args:
            code: Source code to clean.
            language: Programming language.
            
        Returns:
            Cleaned code.
        """
        if language == "python":
            # Remove Python comments and string contents
            lines = []
            for line in code.split('\n'):
                # Remove comments (simplified approach)
                if '#' in line:
                    # Find # not in strings
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
                
                # Replace string contents with placeholders
                line = re.sub(r'""".*?"""', '"""STRING"""', line, flags=re.DOTALL)
                line = re.sub(r"'''.*?'''", "'''STRING'''", line, flags=re.DOTALL)
                line = re.sub(r'"[^"]*"', '"STRING"', line)
                line = re.sub(r"'[^']*'", "'STRING'", line)
                
                lines.append(line)
            
            return '\n'.join(lines)
        
        elif language in ["javascript", "typescript", "java"]:
            # Remove C-style comments and string contents
            # Remove single-line comments
            code = re.sub(r'//.*$', '', code, flags=re.MULTILINE)
            # Remove multi-line comments
            code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
            # Replace string contents with placeholders
            code = re.sub(r'"[^"]*"', '"STRING"', code)
            code = re.sub(r"'[^']*'", "'STRING'", code)
            if language in ["javascript", "typescript"]:
                code = re.sub(r'`[^`]*`', '`STRING`', code)  # Template literals
            
            return code
        
        return code
    
    def _is_builtin_identifier(self, identifier: str, language: str) -> bool:
        """Check if an identifier is a built-in language construct.
        
        Args:
            identifier: Identifier to check.
            language: Programming language.
            
        Returns:
            True if the identifier is a built-in.
        """
        builtins = {
            "python": {
                "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
                "callable", "chr", "classmethod", "compile", "complex", "delattr",
                "dict", "dir", "divmod", "enumerate", "eval", "exec", "filter",
                "float", "format", "frozenset", "getattr", "globals", "hasattr",
                "hash", "help", "hex", "id", "input", "int", "isinstance",
                "issubclass", "iter", "len", "list", "locals", "map", "max",
                "memoryview", "min", "next", "object", "oct", "open", "ord",
                "pow", "print", "property", "range", "repr", "reversed", "round",
                "set", "setattr", "slice", "sorted", "staticmethod", "str", "sum",
                "super", "tuple", "type", "vars", "zip", "__import__",
            },
            "javascript": {
                "Array", "Boolean", "Date", "Error", "Function", "JSON", "Math",
                "Number", "Object", "RegExp", "String", "console", "window",
                "document", "parseInt", "parseFloat", "isNaN", "isFinite",
                "encodeURI", "decodeURI", "encodeURIComponent", "decodeURIComponent",
            },
            "typescript": {
                "Array", "Boolean", "Date", "Error", "Function", "JSON", "Math",
                "Number", "Object", "RegExp", "String", "console", "window",
                "document", "parseInt", "parseFloat", "isNaN", "isFinite",
                "encodeURI", "decodeURI", "encodeURIComponent", "decodeURIComponent",
            },
            "java": {
                "System", "String", "Object", "Class", "Integer", "Double", "Float",
                "Boolean", "Character", "Byte", "Short", "Long", "Math", "Arrays",
                "Collections", "List", "Map", "Set", "ArrayList", "HashMap", "HashSet",
            },
        }
        
        return identifier in builtins.get(language, set())
    
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
        
        return "python"  # Default fallback
    
    def _calculate_function_metrics(
        self, 
        function: Function, 
        existing_metrics: Optional[FunctionMetrics] = None
    ) -> Optional[FunctionMetrics]:
        """Calculate Halstead metrics for a function."""
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
            
            # Calculate Halstead metrics
            halstead_metrics = self._calculate_halstead_metrics(code, language)
            existing_metrics.halstead = halstead_metrics
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating Halstead metrics for function {function.name}: {str(e)}")
            return existing_metrics
    
    def _calculate_class_metrics(
        self, 
        class_def: Class, 
        existing_metrics: Optional[ClassMetrics] = None
    ) -> Optional[ClassMetrics]:
        """Calculate Halstead metrics for a class."""
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
            
            # Calculate Halstead metrics for the class
            halstead_metrics = self._calculate_halstead_metrics(code, language)
            
            # Aggregate metrics from methods
            for method_metrics in existing_metrics.function_metrics:
                halstead_metrics.n1 += method_metrics.halstead.n1
                halstead_metrics.n2 += method_metrics.halstead.n2
                halstead_metrics.N1 += method_metrics.halstead.N1
                halstead_metrics.N2 += method_metrics.halstead.N2
            
            existing_metrics.halstead = halstead_metrics
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating Halstead metrics for class {class_def.name}: {str(e)}")
            return existing_metrics
    
    def _calculate_file_metrics(
        self, 
        file: SourceFile, 
        existing_metrics: Optional[FileMetrics] = None
    ) -> Optional[FileMetrics]:
        """Calculate Halstead metrics for a file."""
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
            
            # Calculate file-level Halstead metrics
            halstead_metrics = self._calculate_halstead_metrics(content, language)
            
            # Note: Function and class metrics are already calculated separately
            # The file-level metrics represent the overall file complexity
            existing_metrics.halstead = halstead_metrics
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating Halstead metrics for file {getattr(file, 'path', 'unknown')}: {str(e)}")
            return existing_metrics
    
    def _calculate_codebase_metrics(
        self, 
        codebase: Codebase, 
        existing_metrics: Optional[CodebaseMetrics] = None
    ) -> Optional[CodebaseMetrics]:
        """Calculate Halstead metrics for the entire codebase."""
        if existing_metrics is None:
            return None
        
        try:
            # Codebase Halstead metrics will be aggregated from file metrics
            # This is handled in the metrics engine aggregation step
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating Halstead metrics for codebase: {str(e)}")
            return existing_metrics
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for this calculator."""
        return {
            "type": "object",
            "properties": {
                "include_keywords": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include language keywords as operators"
                },
                "include_literals": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include literals (numbers, strings) as operands"
                },
                "include_identifiers": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include user-defined identifiers as operands"
                }
            },
            "additionalProperties": False
        }

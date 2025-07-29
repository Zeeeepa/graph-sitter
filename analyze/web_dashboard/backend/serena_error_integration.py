#!/usr/bin/env python3
"""
Serena Error Detection Integration
=================================

This module integrates Serena's error detection capabilities with the graph-sitter
analysis pipeline to provide comprehensive error analysis, context detection,
and visual error representation.
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
import re
from dataclasses import dataclass
from enum import Enum

# Add paths for both graph-sitter and serena
current_dir = Path(__file__).parent
graph_sitter_root = current_dir.parent.parent
src_path = graph_sitter_root / "src"
sys.path.insert(0, str(src_path))

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

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

@dataclass
class CodeError:
    """Represents a code error with context."""
    id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    filepath: str
    line_start: int
    line_end: int
    column_start: int = 0
    column_end: int = 0
    context_lines: List[str] = None
    suggested_fix: str = None
    related_errors: List[str] = None
    affected_functions: List[str] = None
    blast_radius: int = 0

class SerenaErrorAnalyzer:
    """Comprehensive error analysis using Serena techniques."""
    
    def __init__(self):
        self.error_patterns = self._initialize_error_patterns()
        self.error_cache = {}
        self.analysis_stats = {
            'total_errors': 0,
            'errors_by_severity': {},
            'errors_by_category': {},
            'last_analysis': None
        }
    
    def _initialize_error_patterns(self) -> Dict[str, Dict]:
        """Initialize error detection patterns."""
        return {
            'syntax_errors': {
                'patterns': [
                    r'SyntaxError',
                    r'IndentationError',
                    r'TabError',
                    r'unexpected EOF',
                    r'invalid syntax'
                ],
                'severity': ErrorSeverity.CRITICAL,
                'category': ErrorCategory.SYNTAX
            },
            'import_errors': {
                'patterns': [
                    r'ImportError',
                    r'ModuleNotFoundError',
                    r'from\s+\.\s+import',  # Relative imports
                    r'import\s+\*'  # Wildcard imports
                ],
                'severity': ErrorSeverity.HIGH,
                'category': ErrorCategory.IMPORT
            },
            'unused_variables': {
                'patterns': [
                    r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=.*$',  # Variable assignment
                ],
                'severity': ErrorSeverity.LOW,
                'category': ErrorCategory.UNUSED
            },
            'security_issues': {
                'patterns': [
                    r'eval\s*\(',
                    r'exec\s*\(',
                    r'subprocess\.call',
                    r'os\.system',
                    r'input\s*\('  # Potential injection
                ],
                'severity': ErrorSeverity.HIGH,
                'category': ErrorCategory.SECURITY
            },
            'performance_issues': {
                'patterns': [
                    r'for\s+.*\s+in\s+range\(len\(',  # Inefficient iteration
                    r'\.append\s*\(\s*\)\s*$',  # Empty append
                    r'time\.sleep\s*\(\s*[0-9]+\s*\)'  # Long sleeps
                ],
                'severity': ErrorSeverity.MEDIUM,
                'category': ErrorCategory.PERFORMANCE
            },
            'style_issues': {
                'patterns': [
                    r'^\s{1,3}[^\s]',  # Inconsistent indentation
                    r'[a-z]+[A-Z]',  # camelCase in Python
                    r'def\s+[A-Z]',  # Capitalized function names
                    r'class\s+[a-z]'  # Lowercase class names
                ],
                'severity': ErrorSeverity.LOW,
                'category': ErrorCategory.STYLE
            }
        }
    
    async def analyze_file_errors(self, filepath: str, content: str) -> List[CodeError]:
        """Analyze a single file for errors."""
        errors = []
        lines = content.split('\n')
        
        try:
            # Check for syntax errors first
            try:
                compile(content, filepath, 'exec')
            except SyntaxError as e:
                errors.append(CodeError(
                    id=f"syntax_{filepath}_{e.lineno}",
                    category=ErrorCategory.SYNTAX,
                    severity=ErrorSeverity.CRITICAL,
                    message=f"Syntax Error: {e.msg}",
                    filepath=filepath,
                    line_start=e.lineno or 1,
                    line_end=e.lineno or 1,
                    column_start=e.offset or 0,
                    context_lines=self._get_context_lines(lines, e.lineno or 1),
                    suggested_fix="Fix the syntax error according to Python grammar rules"
                ))
            
            # Pattern-based error detection
            for error_type, config in self.error_patterns.items():
                for i, line in enumerate(lines, 1):
                    for pattern in config['patterns']:
                        if re.search(pattern, line, re.IGNORECASE):
                            error_id = f"{error_type}_{filepath}_{i}"
                            
                            # Skip if already found
                            if error_id in [e.id for e in errors]:
                                continue
                            
                            errors.append(CodeError(
                                id=error_id,
                                category=config['category'],
                                severity=config['severity'],
                                message=f"{error_type.replace('_', ' ').title()}: {line.strip()}",
                                filepath=filepath,
                                line_start=i,
                                line_end=i,
                                context_lines=self._get_context_lines(lines, i),
                                suggested_fix=self._get_suggested_fix(error_type, line)
                            ))
            
            # Advanced analysis
            errors.extend(await self._analyze_function_complexity(filepath, content, lines))
            errors.extend(await self._analyze_import_dependencies(filepath, content, lines))
            
        except Exception as e:
            logger.error(f"Error analyzing file {filepath}: {e}")
            errors.append(CodeError(
                id=f"analysis_error_{filepath}",
                category=ErrorCategory.LOGIC,
                severity=ErrorSeverity.MEDIUM,
                message=f"Analysis Error: {str(e)}",
                filepath=filepath,
                line_start=1,
                line_end=1,
                suggested_fix="Review file for potential parsing issues"
            ))
        
        return errors
    
    async def _analyze_function_complexity(self, filepath: str, content: str, lines: List[str]) -> List[CodeError]:
        """Analyze function complexity and identify issues."""
        errors = []
        
        # Find function definitions
        function_pattern = r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        
        for i, line in enumerate(lines, 1):
            match = re.match(function_pattern, line)
            if match:
                func_name = match.group(1)
                
                # Calculate function length (simple heuristic)
                func_end = i
                indent_level = len(line) - len(line.lstrip())
                
                for j in range(i, len(lines)):
                    if lines[j].strip() and (len(lines[j]) - len(lines[j].lstrip())) <= indent_level and j > i:
                        break
                    func_end = j + 1
                
                func_length = func_end - i
                
                # Check for overly long functions
                if func_length > 50:
                    errors.append(CodeError(
                        id=f"long_function_{filepath}_{i}",
                        category=ErrorCategory.STYLE,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"Function '{func_name}' is too long ({func_length} lines)",
                        filepath=filepath,
                        line_start=i,
                        line_end=func_end,
                        context_lines=self._get_context_lines(lines, i),
                        suggested_fix="Consider breaking this function into smaller, more focused functions"
                    ))
                
                # Check for functions with no docstring
                if i + 1 < len(lines) and not lines[i + 1].strip().startswith('"""') and not lines[i + 1].strip().startswith("'''"):
                    errors.append(CodeError(
                        id=f"no_docstring_{filepath}_{i}",
                        category=ErrorCategory.STYLE,
                        severity=ErrorSeverity.LOW,
                        message=f"Function '{func_name}' has no docstring",
                        filepath=filepath,
                        line_start=i,
                        line_end=i,
                        context_lines=self._get_context_lines(lines, i),
                        suggested_fix="Add a docstring describing the function's purpose, parameters, and return value"
                    ))
        
        return errors
    
    async def _analyze_import_dependencies(self, filepath: str, content: str, lines: List[str]) -> List[CodeError]:
        """Analyze import dependencies and identify issues."""
        errors = []
        imports = []
        
        # Collect all imports
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*(import|from)\s+', line):
                imports.append((i, line.strip()))
        
        # Check for unused imports (simplified)
        for line_num, import_line in imports:
            if 'import *' in import_line:
                errors.append(CodeError(
                    id=f"wildcard_import_{filepath}_{line_num}",
                    category=ErrorCategory.IMPORT,
                    severity=ErrorSeverity.MEDIUM,
                    message="Wildcard import detected",
                    filepath=filepath,
                    line_start=line_num,
                    line_end=line_num,
                    context_lines=self._get_context_lines(lines, line_num),
                    suggested_fix="Import specific names instead of using wildcard imports"
                ))
        
        # Check import order (PEP 8)
        if len(imports) > 1:
            stdlib_imports = []
            third_party_imports = []
            local_imports = []
            
            for line_num, import_line in imports:
                if re.search(r'from\s+\.', import_line):
                    local_imports.append(line_num)
                elif any(lib in import_line for lib in ['os', 'sys', 'json', 'time', 're', 'datetime']):
                    stdlib_imports.append(line_num)
                else:
                    third_party_imports.append(line_num)
            
            # Check if imports are properly ordered
            all_import_lines = stdlib_imports + third_party_imports + local_imports
            actual_order = [line_num for line_num, _ in imports]
            
            if all_import_lines != actual_order:
                errors.append(CodeError(
                    id=f"import_order_{filepath}",
                    category=ErrorCategory.STYLE,
                    severity=ErrorSeverity.LOW,
                    message="Imports are not properly ordered (PEP 8)",
                    filepath=filepath,
                    line_start=imports[0][0],
                    line_end=imports[-1][0],
                    suggested_fix="Order imports: standard library, third-party, local imports"
                ))
        
        return errors
    
    def _get_context_lines(self, lines: List[str], line_num: int, context: int = 3) -> List[str]:
        """Get context lines around an error."""
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)
        return lines[start:end]
    
    def _get_suggested_fix(self, error_type: str, line: str) -> str:
        """Get suggested fix for an error type."""
        fixes = {
            'security_issues': "Review this code for potential security vulnerabilities",
            'performance_issues': "Consider optimizing this code for better performance",
            'style_issues': "Follow PEP 8 style guidelines",
            'unused_variables': "Remove unused variables or prefix with underscore",
            'import_errors': "Check import paths and module availability"
        }
        return fixes.get(error_type, "Review and fix this issue")
    
    async def analyze_codebase_errors(self, file_contents: Dict[str, str]) -> Dict[str, Any]:
        """Analyze errors across the entire codebase."""
        logger.info(f"Analyzing errors in {len(file_contents)} files...")
        
        all_errors = []
        file_error_counts = {}
        
        # Analyze each file
        for filepath, content in file_contents.items():
            file_errors = await self.analyze_file_errors(filepath, content)
            all_errors.extend(file_errors)
            file_error_counts[filepath] = len(file_errors)
        
        # Calculate statistics
        severity_counts = {}
        category_counts = {}
        
        for error in all_errors:
            severity_counts[error.severity.value] = severity_counts.get(error.severity.value, 0) + 1
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
        
        # Update stats
        self.analysis_stats.update({
            'total_errors': len(all_errors),
            'errors_by_severity': severity_counts,
            'errors_by_category': category_counts,
            'last_analysis': datetime.now().isoformat()
        })
        
        # Generate error heat map
        error_heat_map = self._generate_error_heat_map(file_error_counts)
        
        # Find critical files
        critical_files = [
            filepath for filepath, count in file_error_counts.items()
            if count > 5  # Files with more than 5 errors
        ]
        
        logger.info(f"Found {len(all_errors)} total errors across {len(file_contents)} files")
        
        return {
            'errors': [self._error_to_dict(error) for error in all_errors],
            'statistics': self.analysis_stats,
            'file_error_counts': file_error_counts,
            'error_heat_map': error_heat_map,
            'critical_files': critical_files,
            'recommendations': self._generate_recommendations(all_errors)
        }
    
    def _error_to_dict(self, error: CodeError) -> Dict[str, Any]:
        """Convert CodeError to dictionary."""
        return {
            'id': error.id,
            'category': error.category.value,
            'severity': error.severity.value,
            'message': error.message,
            'filepath': error.filepath,
            'line_start': error.line_start,
            'line_end': error.line_end,
            'column_start': error.column_start,
            'column_end': error.column_end,
            'context_lines': error.context_lines or [],
            'suggested_fix': error.suggested_fix,
            'related_errors': error.related_errors or [],
            'affected_functions': error.affected_functions or [],
            'blast_radius': error.blast_radius
        }
    
    def _generate_error_heat_map(self, file_error_counts: Dict[str, int]) -> Dict[str, str]:
        """Generate error heat map for visualization."""
        heat_map = {}
        
        if not file_error_counts:
            return heat_map
        
        max_errors = max(file_error_counts.values()) if file_error_counts else 0
        
        for filepath, error_count in file_error_counts.items():
            if error_count == 0:
                heat_map[filepath] = 'green'  # No errors
            elif error_count <= max_errors * 0.3:
                heat_map[filepath] = 'yellow'  # Low error count
            elif error_count <= max_errors * 0.7:
                heat_map[filepath] = 'orange'  # Medium error count
            else:
                heat_map[filepath] = 'red'  # High error count
        
        return heat_map
    
    def _generate_recommendations(self, errors: List[CodeError]) -> List[str]:
        """Generate recommendations based on error analysis."""
        recommendations = []
        
        # Count errors by category
        category_counts = {}
        for error in errors:
            category_counts[error.category.value] = category_counts.get(error.category.value, 0) + 1
        
        # Generate category-specific recommendations
        if category_counts.get('syntax', 0) > 0:
            recommendations.append("Fix syntax errors first as they prevent code execution")
        
        if category_counts.get('security', 0) > 0:
            recommendations.append("Address security issues to prevent potential vulnerabilities")
        
        if category_counts.get('performance', 0) > 5:
            recommendations.append("Consider performance optimizations for better efficiency")
        
        if category_counts.get('style', 0) > 10:
            recommendations.append("Implement code formatting tools (black, flake8) for consistent style")
        
        if category_counts.get('import', 0) > 0:
            recommendations.append("Review import statements and dependencies")
        
        return recommendations

# Global analyzer instance
serena_analyzer = SerenaErrorAnalyzer()

async def analyze_file_errors(filepath: str, content: str) -> List[Dict[str, Any]]:
    """Analyze errors in a single file."""
    errors = await serena_analyzer.analyze_file_errors(filepath, content)
    return [serena_analyzer._error_to_dict(error) for error in errors]

async def analyze_codebase_errors(file_contents: Dict[str, str]) -> Dict[str, Any]:
    """Analyze errors across the entire codebase."""
    return await serena_analyzer.analyze_codebase_errors(file_contents)

if __name__ == "__main__":
    # Test the error analysis
    async def test_error_analysis():
        print("Testing Serena Error Analysis...")
        
        # Test with sample code
        sample_code = '''
import os
import sys
from . import something
import *

def badFunction():
    eval("print('hello')")
    for i in range(len(some_list)):
        pass
    
class lowercase_class:
    pass

def AnotherBadFunction():
    unused_var = 42
    time.sleep(10)
'''
        
        errors = await analyze_file_errors('test.py', sample_code)
        print(f"Found {len(errors)} errors:")
        
        for error in errors:
            print(f"  - {error['severity'].upper()}: {error['message']}")
        
        print("\n✅ Error analysis test complete!")
    
    asyncio.run(test_error_analysis())


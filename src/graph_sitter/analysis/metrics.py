"""
Advanced code metrics implementation following graph-sitter.com patterns.

This module provides comprehensive code metrics including:
- Cyclomatic complexity
- Maintainability index
- Function and class metrics
- Codebase-level statistics
"""

import ast
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.class_definition import Class
from graph_sitter.core.file import SourceFile


@dataclass
class FunctionMetrics:
    """Comprehensive metrics for a function."""
    name: str
    qualified_name: str
    lines_of_code: int
    cyclomatic_complexity: int
    parameters_count: int
    return_statements_count: int
    call_sites_count: int
    function_calls_count: int
    is_recursive: bool
    is_async: bool
    is_generator: bool
    nesting_depth: int
    cognitive_complexity: int
    maintainability_index: float
    
    @property
    def complexity_rating(self) -> str:
        """Get complexity rating based on cyclomatic complexity."""
        if self.cyclomatic_complexity <= 5:
            return "Low"
        elif self.cyclomatic_complexity <= 10:
            return "Moderate"
        elif self.cyclomatic_complexity <= 20:
            return "High"
        else:
            return "Very High"


@dataclass
class ClassMetrics:
    """Comprehensive metrics for a class."""
    name: str
    qualified_name: str
    methods_count: int
    attributes_count: int
    inheritance_depth: int
    parent_classes: List[str]
    child_classes: List[str]
    is_abstract: bool
    lines_of_code: int
    public_methods: int
    private_methods: int
    complexity_score: float
    cohesion_score: float
    coupling_score: float
    
    @property
    def design_quality_rating(self) -> str:
        """Get design quality rating based on metrics."""
        score = (self.cohesion_score * 0.4 + 
                (1 - self.coupling_score) * 0.3 + 
                (1 - min(self.complexity_score / 100, 1)) * 0.3)
        
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Fair"
        else:
            return "Poor"


@dataclass
class FileMetrics:
    """Comprehensive metrics for a file."""
    filepath: str
    filename: str
    lines_of_code: int
    functions_count: int
    classes_count: int
    imports_count: int
    complexity_score: float
    maintainability_index: float
    test_coverage_estimate: float
    documentation_coverage: float
    
    @property
    def quality_score(self) -> float:
        """Calculate overall quality score for the file."""
        return (
            self.maintainability_index * 0.3 +
            self.test_coverage_estimate * 0.25 +
            self.documentation_coverage * 0.25 +
            (100 - min(self.complexity_score, 100)) * 0.2
        ) / 100


class CodeMetrics:
    """
    Advanced code metrics analyzer following graph-sitter.com patterns.
    
    Provides comprehensive analysis capabilities including:
    - Cyclomatic complexity calculation
    - Maintainability index computation
    - Dead code detection
    - Dependency analysis
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize metrics analyzer with codebase."""
        self.codebase = codebase
        self._function_cache: Dict[str, FunctionMetrics] = {}
        self._class_cache: Dict[str, ClassMetrics] = {}
    
    def analyze_function(self, function: Function) -> FunctionMetrics:
        """
        Analyze a function and return comprehensive metrics.
        
        Based on graph-sitter.com function analysis patterns.
        """
        if function.qualified_name in self._function_cache:
            return self._function_cache[function.qualified_name]
        
        # Basic metrics from graph-sitter API
        lines_of_code = self._calculate_function_loc(function)
        cyclomatic_complexity = self._calculate_cyclomatic_complexity(function)
        parameters_count = len(function.parameters) if hasattr(function, 'parameters') else 0
        return_statements_count = len(function.return_statements) if hasattr(function, 'return_statements') else 0
        call_sites_count = len(function.call_sites) if hasattr(function, 'call_sites') else 0
        function_calls_count = len(function.function_calls) if hasattr(function, 'function_calls') else 0
        
        # Advanced metrics
        is_recursive = self._detect_recursion(function)
        is_async = self._is_async_function(function)
        is_generator = self._is_generator_function(function)
        nesting_depth = self._calculate_nesting_depth(function)
        cognitive_complexity = self._calculate_cognitive_complexity(function)
        maintainability_index = self._calculate_maintainability_index(
            lines_of_code, cyclomatic_complexity, function
        )
        
        metrics = FunctionMetrics(
            name=function.name,
            qualified_name=function.qualified_name,
            lines_of_code=lines_of_code,
            cyclomatic_complexity=cyclomatic_complexity,
            parameters_count=parameters_count,
            return_statements_count=return_statements_count,
            call_sites_count=call_sites_count,
            function_calls_count=function_calls_count,
            is_recursive=is_recursive,
            is_async=is_async,
            is_generator=is_generator,
            nesting_depth=nesting_depth,
            cognitive_complexity=cognitive_complexity,
            maintainability_index=maintainability_index
        )
        
        self._function_cache[function.qualified_name] = metrics
        return metrics
    
    def analyze_class(self, class_def: Class) -> ClassMetrics:
        """
        Analyze a class and return comprehensive metrics.
        
        Based on graph-sitter.com class analysis patterns.
        """
        if class_def.qualified_name in self._class_cache:
            return self._class_cache[class_def.qualified_name]
        
        # Basic metrics from graph-sitter API
        methods_count = len(class_def.methods) if hasattr(class_def, 'methods') else 0
        attributes_count = len(class_def.attributes) if hasattr(class_def, 'attributes') else 0
        inheritance_depth = self._calculate_inheritance_depth(class_def)
        parent_classes = self._get_parent_class_names(class_def)
        child_classes = self._get_child_class_names(class_def)
        is_abstract = self._is_abstract_class(class_def)
        
        # Advanced metrics
        lines_of_code = self._calculate_class_loc(class_def)
        public_methods, private_methods = self._count_method_visibility(class_def)
        complexity_score = self._calculate_class_complexity(class_def)
        cohesion_score = self._calculate_class_cohesion(class_def)
        coupling_score = self._calculate_class_coupling(class_def)
        
        metrics = ClassMetrics(
            name=class_def.name,
            qualified_name=class_def.qualified_name,
            methods_count=methods_count,
            attributes_count=attributes_count,
            inheritance_depth=inheritance_depth,
            parent_classes=parent_classes,
            child_classes=child_classes,
            is_abstract=is_abstract,
            lines_of_code=lines_of_code,
            public_methods=public_methods,
            private_methods=private_methods,
            complexity_score=complexity_score,
            cohesion_score=cohesion_score,
            coupling_score=coupling_score
        )
        
        self._class_cache[class_def.qualified_name] = metrics
        return metrics
    
    def analyze_file(self, file: SourceFile) -> FileMetrics:
        """Analyze a file and return comprehensive metrics."""
        lines_of_code = self._calculate_file_loc(file)
        functions_count = len(list(file.functions)) if hasattr(file, 'functions') else 0
        classes_count = len(list(file.classes)) if hasattr(file, 'classes') else 0
        imports_count = len(list(file.imports)) if hasattr(file, 'imports') else 0
        
        complexity_score = self._calculate_file_complexity(file)
        maintainability_index = self._calculate_file_maintainability(file)
        test_coverage_estimate = self._estimate_test_coverage(file)
        documentation_coverage = self._calculate_documentation_coverage(file)
        
        return FileMetrics(
            filepath=file.filepath,
            filename=file.name,
            lines_of_code=lines_of_code,
            functions_count=functions_count,
            classes_count=classes_count,
            imports_count=imports_count,
            complexity_score=complexity_score,
            maintainability_index=maintainability_index,
            test_coverage_estimate=test_coverage_estimate,
            documentation_coverage=documentation_coverage
        )
    
    def get_codebase_summary(self) -> Dict[str, Any]:
        """Get comprehensive codebase-level metrics."""
        files = list(self.codebase.files)
        functions = list(self.codebase.functions)
        classes = list(self.codebase.classes)
        
        total_loc = sum(self._calculate_file_loc(f) for f in files)
        avg_complexity = sum(self.analyze_function(f).cyclomatic_complexity for f in functions) / len(functions) if functions else 0
        
        # Dead code analysis
        dead_functions = self.find_dead_code()
        recursive_functions = self.find_recursive_functions()
        complex_functions = self.find_complex_functions()
        
        return {
            'total_files': len(files),
            'total_functions': len(functions),
            'total_classes': len(classes),
            'total_lines_of_code': total_loc,
            'average_function_complexity': avg_complexity,
            'dead_functions_count': len(dead_functions),
            'recursive_functions_count': len(recursive_functions),
            'complex_functions_count': len(complex_functions),
            'maintainability_score': self._calculate_codebase_maintainability(),
            'technical_debt_ratio': self._calculate_technical_debt_ratio()
        }
    
    def find_dead_code(self) -> List[Function]:
        """Find functions with no call sites (potential dead code)."""
        dead_functions = []
        for function in self.codebase.functions:
            if hasattr(function, 'call_sites') and len(function.call_sites) == 0:
                # Additional checks to avoid false positives
                if not self._is_entry_point(function) and not self._is_test_function(function):
                    dead_functions.append(function)
        return dead_functions
    
    def find_recursive_functions(self) -> List[Function]:
        """Find recursive functions in the codebase."""
        recursive_functions = []
        for function in self.codebase.functions:
            if self._detect_recursion(function):
                recursive_functions.append(function)
        return recursive_functions
    
    def find_complex_functions(self, min_complexity: int = 10) -> List[Function]:
        """Find functions with high cyclomatic complexity."""
        complex_functions = []
        for function in self.codebase.functions:
            complexity = self._calculate_cyclomatic_complexity(function)
            if complexity >= min_complexity:
                complex_functions.append(function)
        return complex_functions
    
    # Private helper methods
    
    def _calculate_function_loc(self, function: Function) -> int:
        """Calculate lines of code for a function."""
        if hasattr(function, 'start_point') and hasattr(function, 'end_point'):
            return function.end_point[0] - function.start_point[0] + 1
        return 0
    
    def _calculate_cyclomatic_complexity(self, function: Function) -> int:
        """Calculate cyclomatic complexity for a function."""
        complexity = 1  # Base complexity
        
        # Count decision points in the function source
        if hasattr(function, 'source'):
            source = function.source
            # Count if statements
            complexity += len(re.findall(r'\\bif\\b', source))
            # Count elif statements
            complexity += len(re.findall(r'\\belif\\b', source))
            # Count for loops
            complexity += len(re.findall(r'\\bfor\\b', source))
            # Count while loops
            complexity += len(re.findall(r'\\bwhile\\b', source))
            # Count except clauses
            complexity += len(re.findall(r'\\bexcept\\b', source))
            # Count and/or operators
            complexity += len(re.findall(r'\\band\\b|\\bor\\b', source))
            # Count ternary operators
            complexity += len(re.findall(r'\\bif\\b.*\\belse\\b', source))
        
        return complexity
    
    def _detect_recursion(self, function: Function) -> bool:
        """Detect if a function is recursive."""
        if hasattr(function, 'function_calls'):
            for call in function.function_calls:
                if hasattr(call, 'name') and call.name == function.name:
                    return True
                if hasattr(call, 'function_definition'):
                    called_func = call.function_definition
                    if hasattr(called_func, 'name') and called_func.name == function.name:
                        return True
        return False
    
    def _is_async_function(self, function: Function) -> bool:
        """Check if function is async."""
        if hasattr(function, 'is_async'):
            return function.is_async
        if hasattr(function, 'source'):
            return 'async def' in function.source
        return False
    
    def _is_generator_function(self, function: Function) -> bool:
        """Check if function is a generator."""
        if hasattr(function, 'source'):
            return 'yield' in function.source
        return False
    
    def _calculate_nesting_depth(self, function: Function) -> int:
        """Calculate maximum nesting depth in function."""
        if not hasattr(function, 'source'):
            return 0
        
        max_depth = 0
        current_depth = 0
        
        for line in function.source.split('\\n'):
            stripped = line.strip()
            if any(stripped.startswith(keyword) for keyword in ['if', 'for', 'while', 'try', 'with']):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif stripped in ['else:', 'elif', 'except:', 'finally:']:
                continue
            elif stripped == '' or stripped.startswith('#'):
                continue
            else:
                # Check for dedentation
                indent_level = len(line) - len(line.lstrip())
                if indent_level == 0:
                    current_depth = 0
        
        return max_depth
    
    def _calculate_cognitive_complexity(self, function: Function) -> int:
        """Calculate cognitive complexity (similar to cyclomatic but with nesting weights)."""
        if not hasattr(function, 'source'):
            return 1
        
        complexity = 0
        nesting_level = 0
        
        for line in function.source.split('\\n'):
            stripped = line.strip()
            
            # Increment for control structures
            if any(stripped.startswith(keyword) for keyword in ['if', 'elif', 'for', 'while']):
                complexity += 1 + nesting_level
                nesting_level += 1
            elif stripped.startswith('try'):
                nesting_level += 1
            elif stripped.startswith('except'):
                complexity += 1 + nesting_level
            elif any(op in stripped for op in ['and', 'or']):
                complexity += 1
            
            # Handle dedentation
            if stripped.endswith(':') and any(stripped.startswith(kw) for kw in ['if', 'for', 'while', 'try']):
                continue
            elif stripped == '' or stripped.startswith('#'):
                continue
            else:
                indent_level = len(line) - len(line.lstrip())
                if indent_level == 0:
                    nesting_level = 0
        
        return max(complexity, 1)
    
    def _calculate_maintainability_index(self, loc: int, complexity: int, function: Function) -> float:
        """Calculate maintainability index for a function."""
        # Simplified maintainability index calculation
        # MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic Complexity) - 16.2 * ln(Lines of Code)
        
        import math
        
        # Estimate Halstead volume (simplified)
        halstead_volume = max(loc * 2, 1)  # Simplified estimation
        
        mi = 171 - 5.2 * math.log(halstead_volume) - 0.23 * complexity - 16.2 * math.log(max(loc, 1))
        
        # Normalize to 0-100 scale
        return max(0, min(100, mi))
    
    def _calculate_inheritance_depth(self, class_def: Class) -> int:
        """Calculate inheritance depth for a class."""
        if hasattr(class_def, 'superclasses'):
            return len(class_def.superclasses)
        return 0
    
    def _get_parent_class_names(self, class_def: Class) -> List[str]:
        """Get parent class names."""
        if hasattr(class_def, 'parent_class_names'):
            return [str(name) for name in class_def.parent_class_names]
        return []
    
    def _get_child_class_names(self, class_def: Class) -> List[str]:
        """Get child class names."""
        if hasattr(class_def, 'subclasses'):
            return [cls.name for cls in class_def.subclasses]
        return []
    
    def _is_abstract_class(self, class_def: Class) -> bool:
        """Check if class is abstract."""
        if hasattr(class_def, 'source'):
            return 'ABC' in class_def.source or '@abstractmethod' in class_def.source
        return False
    
    def _calculate_class_loc(self, class_def: Class) -> int:
        """Calculate lines of code for a class."""
        if hasattr(class_def, 'start_point') and hasattr(class_def, 'end_point'):
            return class_def.end_point[0] - class_def.start_point[0] + 1
        return 0
    
    def _count_method_visibility(self, class_def: Class) -> tuple[int, int]:
        """Count public and private methods."""
        public_count = 0
        private_count = 0
        
        if hasattr(class_def, 'methods'):
            for method in class_def.methods:
                if method.name.startswith('_'):
                    private_count += 1
                else:
                    public_count += 1
        
        return public_count, private_count
    
    def _calculate_class_complexity(self, class_def: Class) -> float:
        """Calculate overall complexity score for a class."""
        if not hasattr(class_def, 'methods'):
            return 0.0
        
        total_complexity = 0
        method_count = 0
        
        for method in class_def.methods:
            total_complexity += self._calculate_cyclomatic_complexity(method)
            method_count += 1
        
        return total_complexity / max(method_count, 1)
    
    def _calculate_class_cohesion(self, class_def: Class) -> float:
        """Calculate class cohesion score (simplified LCOM metric)."""
        # Simplified cohesion calculation
        # Higher score means better cohesion
        if not hasattr(class_def, 'methods') or not hasattr(class_def, 'attributes'):
            return 0.5
        
        methods = list(class_def.methods)
        attributes = list(class_def.attributes)
        
        if not methods or not attributes:
            return 0.5
        
        # Count how many methods use each attribute
        attribute_usage = {}
        for attr in attributes:
            usage_count = 0
            for method in methods:
                if hasattr(method, 'source') and attr.name in method.source:
                    usage_count += 1
            attribute_usage[attr.name] = usage_count
        
        # Calculate cohesion as average attribute usage
        total_usage = sum(attribute_usage.values())
        max_possible_usage = len(methods) * len(attributes)
        
        return total_usage / max(max_possible_usage, 1)
    
    def _calculate_class_coupling(self, class_def: Class) -> float:
        """Calculate class coupling score."""
        # Simplified coupling calculation based on dependencies
        if hasattr(class_def, 'dependencies'):
            return min(len(class_def.dependencies) / 10.0, 1.0)  # Normalize to 0-1
        return 0.0
    
    def _calculate_file_loc(self, file: SourceFile) -> int:
        """Calculate lines of code for a file."""
        if hasattr(file, 'source'):
            return len([line for line in file.source.split('\\n') if line.strip() and not line.strip().startswith('#')])
        return 0
    
    def _calculate_file_complexity(self, file: SourceFile) -> float:
        """Calculate overall complexity score for a file."""
        if not hasattr(file, 'functions'):
            return 0.0
        
        functions = list(file.functions)
        if not functions:
            return 0.0
        
        total_complexity = sum(self._calculate_cyclomatic_complexity(f) for f in functions)
        return total_complexity / len(functions)
    
    def _calculate_file_maintainability(self, file: SourceFile) -> float:
        """Calculate maintainability index for a file."""
        if not hasattr(file, 'functions'):
            return 50.0
        
        functions = list(file.functions)
        if not functions:
            return 50.0
        
        total_mi = sum(self.analyze_function(f).maintainability_index for f in functions)
        return total_mi / len(functions)
    
    def _estimate_test_coverage(self, file: SourceFile) -> float:
        """Estimate test coverage based on file patterns."""
        # Simple heuristic: check if there's a corresponding test file
        if 'test' in file.name.lower() or file.name.startswith('test_'):
            return 100.0  # Test files are considered 100% covered
        
        # Look for test files in the codebase
        test_files = [f for f in self.codebase.files if 'test' in f.name.lower()]
        if any(file.name.replace('.py', '') in tf.name for tf in test_files):
            return 80.0  # Has corresponding test file
        
        return 20.0  # No obvious test coverage
    
    def _calculate_documentation_coverage(self, file: SourceFile) -> float:
        """Calculate documentation coverage for a file."""
        if not hasattr(file, 'functions') and not hasattr(file, 'classes'):
            return 100.0
        
        documented_count = 0
        total_count = 0
        
        # Check function documentation
        if hasattr(file, 'functions'):
            for func in file.functions:
                total_count += 1
                if hasattr(func, 'docstring') and func.docstring:
                    documented_count += 1
        
        # Check class documentation
        if hasattr(file, 'classes'):
            for cls in file.classes:
                total_count += 1
                if hasattr(cls, 'docstring') and cls.docstring:
                    documented_count += 1
        
        return (documented_count / max(total_count, 1)) * 100
    
    def _is_entry_point(self, function: Function) -> bool:
        """Check if function is an entry point (main, etc.)."""
        return function.name in ['main', '__main__', 'run', 'start', 'execute']
    
    def _is_test_function(self, function: Function) -> bool:
        """Check if function is a test function."""
        return (function.name.startswith('test_') or 
                function.name.endswith('_test') or
                'test' in function.name.lower())
    
    def _calculate_codebase_maintainability(self) -> float:
        """Calculate overall codebase maintainability score."""
        files = list(self.codebase.files)
        if not files:
            return 50.0
        
        total_score = sum(self.analyze_file(f).maintainability_index for f in files)
        return total_score / len(files)
    
    def _calculate_technical_debt_ratio(self) -> float:
        """Calculate technical debt ratio for the codebase."""
        functions = list(self.codebase.functions)
        if not functions:
            return 0.0
        
        high_complexity_count = len(self.find_complex_functions(min_complexity=10))
        dead_code_count = len(self.find_dead_code())
        
        debt_indicators = high_complexity_count + dead_code_count
        return (debt_indicators / len(functions)) * 100


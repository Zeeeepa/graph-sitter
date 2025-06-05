"""Comprehensive code quality metrics following graph-sitter.com patterns."""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.symbol import Symbol

logger = logging.getLogger(__name__)


@dataclass
class FunctionMetrics:
    """Comprehensive function-level metrics."""
    name: str
    filepath: str
    line_count: int
    parameter_count: int
    return_statement_count: int
    call_site_count: int
    function_call_count: int
    cyclomatic_complexity: int
    maintainability_index: float
    documentation_coverage: float
    test_coverage_estimate: float
    is_async: bool
    has_decorators: bool
    has_docstring: bool
    has_type_annotations: bool
    dependency_count: int
    usage_count: int
    impact_score: float


@dataclass
class ClassMetrics:
    """Comprehensive class-level metrics."""
    name: str
    filepath: str
    method_count: int
    attribute_count: int
    inheritance_depth: int
    subclass_count: int
    cohesion_score: float
    coupling_score: float
    documentation_coverage: float
    test_coverage_estimate: float
    has_constructor: bool
    has_docstring: bool
    abstract_method_count: int
    public_method_count: int
    private_method_count: int
    magic_method_count: int


@dataclass
class FileMetrics:
    """Comprehensive file-level metrics."""
    filepath: str
    line_count: int
    function_count: int
    class_count: int
    import_count: int
    symbol_count: int
    complexity_score: float
    maintainability_index: float
    documentation_coverage: float
    test_coverage_estimate: float
    is_test_file: bool
    language: str


@dataclass
class CodebaseMetrics:
    """Overall codebase metrics."""
    total_files: int
    total_functions: int
    total_classes: int
    total_symbols: int
    total_imports: int
    total_lines: int
    average_complexity: float
    average_maintainability: float
    documentation_coverage: float
    test_coverage_estimate: float
    dead_code_percentage: float
    technical_debt_score: float
    health_score: float
    # Enhanced database-specific fields
    complexity_score: Optional[float] = None
    maintainability_index: Optional[float] = None
    technical_debt_ratio: Optional[float] = None
    test_coverage: Optional[float] = None
    languages: Optional[Dict[str, int]] = None
    created_at: Optional[datetime] = None


@dataclass
class EnhancedCodebaseMetrics:
    """Enhanced codebase metrics with database integration support."""
    # Core metrics
    total_files: int
    total_functions: int
    total_classes: int
    total_lines: int
    complexity_score: float
    maintainability_index: float
    technical_debt_ratio: float
    test_coverage: float
    languages: Dict[str, int]
    
    # Additional analysis metrics
    total_symbols: Optional[int] = None
    total_imports: Optional[int] = None
    average_complexity: Optional[float] = None
    average_maintainability: Optional[float] = None
    documentation_coverage: Optional[float] = None
    test_coverage_estimate: Optional[float] = None
    dead_code_percentage: Optional[float] = None
    technical_debt_score: Optional[float] = None
    health_score: Optional[float] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format for database storage."""
        return {
            'total_files': self.total_files,
            'total_functions': self.total_functions,
            'total_classes': self.total_classes,
            'total_lines': self.total_lines,
            'complexity_score': self.complexity_score,
            'maintainability_index': self.maintainability_index,
            'technical_debt_ratio': self.technical_debt_ratio,
            'test_coverage': self.test_coverage,
            'languages': self.languages,
            'total_symbols': self.total_symbols,
            'total_imports': self.total_imports,
            'average_complexity': self.average_complexity,
            'average_maintainability': self.average_maintainability,
            'documentation_coverage': self.documentation_coverage,
            'test_coverage_estimate': self.test_coverage_estimate,
            'dead_code_percentage': self.dead_code_percentage,
            'technical_debt_score': self.technical_debt_score,
            'health_score': self.health_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedCodebaseMetrics':
        """Create metrics from dictionary format (e.g., from database)."""
        created_at = None
        if data.get('created_at'):
            if isinstance(data['created_at'], str):
                created_at = datetime.fromisoformat(data['created_at'])
            else:
                created_at = data['created_at']
        
        return cls(
            total_files=data['total_files'],
            total_functions=data['total_functions'],
            total_classes=data['total_classes'],
            total_lines=data['total_lines'],
            complexity_score=data['complexity_score'],
            maintainability_index=data['maintainability_index'],
            technical_debt_ratio=data['technical_debt_ratio'],
            test_coverage=data['test_coverage'],
            languages=data.get('languages', {}),
            total_symbols=data.get('total_symbols'),
            total_imports=data.get('total_imports'),
            average_complexity=data.get('average_complexity'),
            average_maintainability=data.get('average_maintainability'),
            documentation_coverage=data.get('documentation_coverage'),
            test_coverage_estimate=data.get('test_coverage_estimate'),
            dead_code_percentage=data.get('dead_code_percentage'),
            technical_debt_score=data.get('technical_debt_score'),
            health_score=data.get('health_score'),
            created_at=created_at
        )


class MetricsCalculator:
    """Calculator for comprehensive code metrics."""
    
    def __init__(self, codebase: Codebase):
        self.codebase = codebase
        self._function_metrics_cache: Dict[str, FunctionMetrics] = {}
        self._class_metrics_cache: Dict[str, ClassMetrics] = {}
        self._file_metrics_cache: Dict[str, FileMetrics] = {}
    
    def calculate_cyclomatic_complexity(self, function: Function) -> int:
        """Calculate cyclomatic complexity for a function."""
        try:
            source = getattr(function, 'source', '')
            if not source:
                return 1
            
            # Count decision points
            complexity = 1  # Base complexity
            
            # Keywords that add complexity
            complexity_keywords = [
                'if ', 'elif ', 'else:', 'for ', 'while ', 'except:', 'and ', 'or ',
                'try:', 'with ', 'assert ', '?', 'case ', 'match '
            ]
            
            for keyword in complexity_keywords:
                complexity += source.count(keyword)
            
            # Count lambda expressions
            complexity += source.count('lambda ')
            
            # Count list/dict comprehensions
            complexity += source.count(' for ') - source.count('for ')  # Comprehensions only
            
            return max(1, complexity)
        except Exception as e:
            logger.warning(f"Error calculating complexity for {function.name}: {e}")
            return 1
    
    def calculate_maintainability_index(self, function: Function) -> float:
        """Calculate maintainability index (0-100 scale)."""
        try:
            source = getattr(function, 'source', '')
            if not source:
                return 50.0
            
            # Halstead metrics approximation
            lines = len(source.split('\n'))
            complexity = self.calculate_cyclomatic_complexity(function)
            
            # Simplified maintainability index
            # MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
            # Where HV = Halstead Volume, CC = Cyclomatic Complexity, LOC = Lines of Code
            
            if lines <= 0:
                return 50.0
            
            # Approximate Halstead volume based on line count and complexity
            halstead_volume = lines * complexity * 0.5
            
            if halstead_volume <= 0:
                halstead_volume = 1
            
            mi = 171 - 5.2 * math.log(halstead_volume) - 0.23 * complexity - 16.2 * math.log(lines)
            
            # Normalize to 0-100 scale
            return max(0.0, min(100.0, mi))
        except Exception as e:
            logger.warning(f"Error calculating maintainability for {function.name}: {e}")
            return 50.0
    
    def calculate_documentation_coverage(self, symbol: Symbol) -> float:
        """Calculate documentation coverage for a symbol."""
        try:
            has_docstring = bool(getattr(symbol, 'docstring', None))
            
            if isinstance(symbol, Function):
                # Check parameters have type annotations
                parameters = getattr(symbol, 'parameters', [])
                typed_params = sum(1 for p in parameters if getattr(p, 'type_annotation', None))
                param_coverage = typed_params / len(parameters) if parameters else 1.0
                
                # Check return type annotation
                has_return_type = bool(getattr(symbol, 'return_type', None))
                
                # Combine scores
                doc_score = 0.5 if has_docstring else 0.0
                type_score = (param_coverage + (0.2 if has_return_type else 0.0)) * 0.5
                
                return min(1.0, doc_score + type_score)
            
            elif isinstance(symbol, Class):
                # Check class docstring and method documentation
                class_doc = 0.3 if has_docstring else 0.0
                
                methods = getattr(symbol, 'methods', [])
                if methods:
                    method_doc_score = sum(
                        0.1 if getattr(method, 'docstring', None) else 0.0
                        for method in methods
                    ) / len(methods)
                else:
                    method_doc_score = 0.0
                
                return min(1.0, class_doc + method_doc_score * 0.7)
            
            else:
                return 1.0 if has_docstring else 0.0
                
        except Exception as e:
            logger.warning(f"Error calculating documentation coverage for {symbol.name}: {e}")
            return 0.0
    
    def estimate_test_coverage(self, symbol: Symbol) -> float:
        """Estimate test coverage for a symbol."""
        try:
            symbol_name = symbol.name.lower()
            
            # Look for test functions that might test this symbol
            test_functions = [
                f for f in self.codebase.functions
                if f.name.startswith('test_') and symbol_name in f.name.lower()
            ]
            
            # Look for test classes
            test_classes = [
                c for c in self.codebase.classes
                if c.name.startswith('Test') and symbol_name in c.name.lower()
            ]
            
            # Simple heuristic: if there are tests mentioning this symbol
            test_score = 0.0
            if test_functions:
                test_score += min(0.6, len(test_functions) * 0.2)
            if test_classes:
                test_score += min(0.4, len(test_classes) * 0.2)
            
            return min(1.0, test_score)
        except Exception as e:
            logger.warning(f"Error estimating test coverage for {symbol.name}: {e}")
            return 0.0
    
    def analyze_function_metrics(self, function: Function) -> FunctionMetrics:
        """Comprehensive function analysis."""
        if function.name in self._function_metrics_cache:
            return self._function_metrics_cache[function.name]
        
        try:
            source = getattr(function, 'source', '')
            parameters = getattr(function, 'parameters', [])
            return_statements = getattr(function, 'return_statements', [])
            call_sites = getattr(function, 'call_sites', [])
            function_calls = getattr(function, 'function_calls', [])
            decorators = getattr(function, 'decorators', [])
            dependencies = getattr(function, 'dependencies', [])
            usages = getattr(function, 'usages', [])
            
            # Calculate metrics
            line_count = len(source.split('\n')) if source else 0
            cyclomatic_complexity = self.calculate_cyclomatic_complexity(function)
            maintainability_index = self.calculate_maintainability_index(function)
            documentation_coverage = self.calculate_documentation_coverage(function)
            test_coverage = self.estimate_test_coverage(function)
            
            # Type annotation coverage
            typed_params = sum(1 for p in parameters if getattr(p, 'type_annotation', None))
            has_type_annotations = (typed_params / len(parameters)) > 0.5 if parameters else True
            
            # Impact score based on usage
            impact_score = len(call_sites) + len(usages) * 0.5
            
            metrics = FunctionMetrics(
                name=function.name,
                filepath=getattr(function, 'filepath', 'unknown'),
                line_count=line_count,
                parameter_count=len(parameters),
                return_statement_count=len(return_statements),
                call_site_count=len(call_sites),
                function_call_count=len(function_calls),
                cyclomatic_complexity=cyclomatic_complexity,
                maintainability_index=maintainability_index,
                documentation_coverage=documentation_coverage,
                test_coverage_estimate=test_coverage,
                is_async=getattr(function, 'is_async', False),
                has_decorators=len(decorators) > 0,
                has_docstring=bool(getattr(function, 'docstring', None)),
                has_type_annotations=has_type_annotations,
                dependency_count=len(dependencies),
                usage_count=len(usages),
                impact_score=impact_score
            )
            
            self._function_metrics_cache[function.name] = metrics
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing function {function.name}: {e}")
            return FunctionMetrics(
                name=function.name,
                filepath=getattr(function, 'filepath', 'unknown'),
                line_count=0, parameter_count=0, return_statement_count=0,
                call_site_count=0, function_call_count=0, cyclomatic_complexity=1,
                maintainability_index=50.0, documentation_coverage=0.0,
                test_coverage_estimate=0.0, is_async=False, has_decorators=False,
                has_docstring=False, has_type_annotations=False,
                dependency_count=0, usage_count=0, impact_score=0.0
            )
    
    def analyze_class_cohesion(self, class_def: Class) -> float:
        """Calculate class cohesion using LCOM (Lack of Cohesion of Methods)."""
        try:
            methods = getattr(class_def, 'methods', [])
            attributes = getattr(class_def, 'attributes', [])
            
            if len(methods) <= 1:
                return 1.0  # Perfect cohesion for single method
            
            # Count method pairs that share attributes
            shared_pairs = 0
            total_pairs = 0
            
            for i, method1 in enumerate(methods):
                for method2 in methods[i+1:]:
                    total_pairs += 1
                    
                    # Check if methods share attributes
                    method1_attrs = self._get_method_attributes(method1)
                    method2_attrs = self._get_method_attributes(method2)
                    
                    if method1_attrs & method2_attrs:  # Intersection
                        shared_pairs += 1
            
            if total_pairs == 0:
                return 1.0
            
            # Cohesion = shared pairs / total pairs
            return shared_pairs / total_pairs
            
        except Exception as e:
            logger.warning(f"Error calculating cohesion for {getattr(class_def, 'name', None) or 'unknown_class'}: {e}")
            return 0.5
    
    def analyze_class_coupling(self, class_def: Class) -> float:
        """Calculate class coupling based on dependencies."""
        try:
            dependencies = getattr(class_def, 'dependencies', [])
            usages = getattr(class_def, 'usages', [])
            
            # Count external dependencies (coupling)
            external_deps = len([d for d in dependencies if not self._is_internal_dependency(d)])
            external_usages = len([u for u in usages if not self._is_internal_dependency(u)])
            
            # Normalize coupling score (lower is better)
            coupling_score = (external_deps + external_usages) / 10.0
            return max(0.0, min(1.0, 1.0 - coupling_score))
            
        except Exception as e:
            logger.warning(f"Error calculating coupling for {getattr(class_def, 'name', None) or 'unknown_class'}: {e}")
            return 0.5
    
    def analyze_class_metrics(self, class_def: Class) -> ClassMetrics:
        """Comprehensive class analysis."""
        # Safe name handling for cache operations
        class_name = getattr(class_def, 'name', None) or 'unknown_class'
        
        if class_name in self._class_metrics_cache:
            return self._class_metrics_cache[class_name]
        
        try:
            methods = getattr(class_def, 'methods', [])
            attributes = getattr(class_def, 'attributes', [])
            superclasses = getattr(class_def, 'superclasses', [])
            
            # Calculate inheritance depth
            inheritance_depth = len(superclasses)
            
            # Categorize methods
            public_methods = []
            private_methods = []
            magic_methods = []
            abstract_methods = []
            
            for method in methods:
                method_name = getattr(method, 'name', None) or ''
                if method_name.startswith('__') and method_name.endswith('__'):
                    magic_methods.append(method)
                elif method_name.startswith('_'):
                    private_methods.append(method)
                else:
                    public_methods.append(method)
                
                if self._is_abstract_method(method):
                    abstract_methods.append(method)
            
            # Calculate cohesion (LCOM)
            cohesion_score = self._calculate_lcom_cohesion(methods, attributes)
            
            # Calculate coupling
            coupling_score = self._calculate_class_coupling(class_def)
            
            metrics = ClassMetrics(
                name=class_name,
                filepath=getattr(class_def, 'filepath', 'unknown'),
                method_count=len(methods),
                attribute_count=len(attributes),
                inheritance_depth=inheritance_depth,
                cohesion_score=cohesion_score,
                coupling_score=coupling_score,
                has_docstring=bool(getattr(class_def, 'docstring', None)),
                abstract_method_count=len(abstract_methods),
                public_method_count=len(public_methods),
                private_method_count=len(private_methods),
                magic_method_count=len(magic_methods)
            )
            
            self._class_metrics_cache[class_name] = metrics
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing class {class_name}: {e}")
            return ClassMetrics(
                name=class_name,
                filepath=getattr(class_def, 'filepath', 'unknown'),
                method_count=0, attribute_count=0, inheritance_depth=0,
                cohesion_score=0.0, coupling_score=0.0, has_docstring=False,
                abstract_method_count=0, public_method_count=0,
                private_method_count=0, magic_method_count=0
            )
    
    def analyze_file_metrics(self, file: SourceFile) -> FileMetrics:
        """Comprehensive file analysis."""
        if file.filepath in self._file_metrics_cache:
            return self._file_metrics_cache[file.filepath]
        
        try:
            source = getattr(file, 'source', '')
            functions = getattr(file, 'functions', [])
            classes = getattr(file, 'classes', [])
            imports = getattr(file, 'imports', [])
            symbols = getattr(file, 'symbols', [])
            
            # Calculate complexity as average of function complexities
            if functions:
                complexity_scores = [
                    self.calculate_cyclomatic_complexity(f) for f in functions
                ]
                complexity_score = sum(complexity_scores) / len(complexity_scores)
            else:
                complexity_score = 1.0
            
            # Calculate maintainability as average of function maintainability
            if functions:
                maintainability_scores = [
                    self.calculate_maintainability_index(f) for f in functions
                ]
                maintainability_index = sum(maintainability_scores) / len(maintainability_scores)
            else:
                maintainability_index = 50.0
            
            # Documentation coverage
            documented_symbols = sum(
                1 for symbol in (functions + classes)
                if getattr(symbol, 'docstring', None)
            )
            doc_coverage = documented_symbols / len(functions + classes) if (functions + classes) else 1.0
            
            # Test coverage estimation
            is_test_file = (
                file.filepath.startswith('test_') or
                '/test' in file.filepath or
                file.filepath.endswith('_test.py')
            )
            
            test_coverage = 1.0 if is_test_file else self._estimate_file_test_coverage(file)
            
            metrics = FileMetrics(
                filepath=file.filepath,
                line_count=len(source.split('\n')) if source else 0,
                function_count=len(functions),
                class_count=len(classes),
                import_count=len(imports),
                symbol_count=len(symbols),
                complexity_score=complexity_score,
                maintainability_index=maintainability_index,
                documentation_coverage=doc_coverage,
                test_coverage_estimate=test_coverage,
                is_test_file=is_test_file,
                language=getattr(file, 'language', 'python')
            )
            
            self._file_metrics_cache[file.filepath] = metrics
            return metrics
            
        except Exception as e:
            logger.error(f"Error analyzing file {file.filepath}: {e}")
            return FileMetrics(
                filepath=file.filepath,
                line_count=0, function_count=0, class_count=0,
                import_count=0, symbol_count=0, complexity_score=1.0,
                maintainability_index=50.0, documentation_coverage=0.0,
                test_coverage_estimate=0.0, is_test_file=False,
                language='python'
            )
    
    def get_codebase_summary(self) -> CodebaseMetrics:
        """Overall codebase metrics."""
        try:
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            symbols = list(self.codebase.symbols)
            imports = list(self.codebase.imports)
            
            # Calculate file metrics
            file_metrics = [self.analyze_file_metrics(f) for f in files]
            
            # Calculate function metrics
            function_metrics = [self.analyze_function_metrics(f) for f in functions]
            
            # Aggregate metrics
            total_lines = sum(fm.line_count for fm in file_metrics)
            
            if function_metrics:
                avg_complexity = sum(fm.cyclomatic_complexity for fm in function_metrics) / len(function_metrics)
                avg_maintainability = sum(fm.maintainability_index for fm in function_metrics) / len(function_metrics)
                doc_coverage = sum(fm.documentation_coverage for fm in function_metrics) / len(function_metrics)
                test_coverage = sum(fm.test_coverage_estimate for fm in function_metrics) / len(function_metrics)
            else:
                avg_complexity = 1.0
                avg_maintainability = 50.0
                doc_coverage = 0.0
                test_coverage = 0.0
            
            # Dead code percentage
            unused_functions = [f for f in functions if not getattr(f, 'usages', []) and not getattr(f, 'call_sites', [])]
            dead_code_percentage = len(unused_functions) / len(functions) if functions else 0.0
            
            # Technical debt score (inverse of maintainability)
            technical_debt_score = max(0.0, (100.0 - avg_maintainability) / 100.0)
            
            # Health score (composite metric)
            health_score = (
                (avg_maintainability / 100.0) * 0.3 +
                doc_coverage * 0.2 +
                test_coverage * 0.2 +
                (1.0 - dead_code_percentage) * 0.15 +
                (1.0 - technical_debt_score) * 0.15
            )
            
            return CodebaseMetrics(
                total_files=len(files),
                total_functions=len(functions),
                total_classes=len(classes),
                total_symbols=len(symbols),
                total_imports=len(imports),
                total_lines=total_lines,
                average_complexity=avg_complexity,
                average_maintainability=avg_maintainability,
                documentation_coverage=doc_coverage,
                test_coverage_estimate=test_coverage,
                dead_code_percentage=dead_code_percentage,
                technical_debt_score=technical_debt_score,
                health_score=health_score
            )
            
        except Exception as e:
            logger.error(f"Error calculating codebase summary: {e}")
            return CodebaseMetrics(
                total_files=0, total_functions=0, total_classes=0,
                total_symbols=0, total_imports=0, total_lines=0,
                average_complexity=1.0, average_maintainability=50.0,
                documentation_coverage=0.0, test_coverage_estimate=0.0,
                dead_code_percentage=0.0, technical_debt_score=0.0,
                health_score=0.0
            )
    
    def _get_method_attributes(self, method: Function) -> Set[str]:
        """Get attributes accessed by a method."""
        try:
            source = getattr(method, 'source', '')
            # Simple heuristic: look for self.attribute patterns
            import re
            attributes = set()
            for match in re.finditer(r'self\.(\w+)', source):
                attributes.add(match.group(1))
            return attributes
        except Exception:
            return set()
    
    def _is_internal_dependency(self, dependency) -> bool:
        """Check if dependency is internal to the project."""
        try:
            dep_filepath = getattr(dependency, 'filepath', '')
            return not dep_filepath.startswith('/') and not dep_filepath.startswith('site-packages')
        except Exception:
            return True
    
    def _is_abstract_method(self, method: Function) -> bool:
        """Check if method is abstract."""
        try:
            decorators = getattr(method, 'decorators', [])
            return any('abstractmethod' in str(d) for d in decorators)
        except Exception:
            return False
    
    def _estimate_file_test_coverage(self, file: SourceFile) -> float:
        """Estimate test coverage for a file."""
        try:
            # Look for corresponding test files
            filepath = file.filepath
            test_patterns = [
                f"test_{filepath}",
                f"tests/test_{filepath.split('/')[-1]}",
                f"{filepath.replace('.py', '_test.py')}"
            ]
            
            for pattern in test_patterns:
                if self.codebase.has_file(pattern):
                    return 0.8  # High coverage if test file exists
            
            return 0.2  # Low coverage if no test file found
        except Exception:
            return 0.0
    
    def _calculate_lcom_cohesion(self, methods, attributes):
        """Calculate LCOM (Lack of Cohesion of Methods) for a class."""
        if not methods:
            return 1.0
        
        # Count method pairs that share attributes
        shared_pairs = 0
        total_pairs = 0
        
        for i, method1 in enumerate(methods):
            for method2 in methods[i+1:]:
                total_pairs += 1
                
                # Check if methods share attributes
                method1_attrs = self._get_method_attributes(method1)
                method2_attrs = self._get_method_attributes(method2)
                
                if method1_attrs & method2_attrs:  # Intersection
                    shared_pairs += 1
        
        if total_pairs == 0:
            return 1.0
        
        # Cohesion = shared pairs / total pairs
        return shared_pairs / total_pairs
    
    def _calculate_class_coupling(self, class_def: Class) -> float:
        """Calculate class coupling based on dependencies."""
        try:
            dependencies = getattr(class_def, 'dependencies', [])
            usages = getattr(class_def, 'usages', [])
            
            # Count external dependencies (coupling)
            external_deps = len([d for d in dependencies if not self._is_internal_dependency(d)])
            external_usages = len([u for u in usages if not self._is_internal_dependency(u)])
            
            # Normalize coupling score (lower is better)
            coupling_score = (external_deps + external_usages) / 10.0
            return max(0.0, min(1.0, 1.0 - coupling_score))
            
        except Exception as e:
            logger.warning(f"Error calculating coupling for {getattr(class_def, 'name', None) or 'unknown_class'}: {e}")
            return 0.5


# Convenience functions
def calculate_cyclomatic_complexity(function: Function) -> int:
    """Calculate cyclomatic complexity for a function."""
    calculator = MetricsCalculator(function.codebase if hasattr(function, 'codebase') else None)
    return calculator.calculate_cyclomatic_complexity(function)


def calculate_maintainability_index(function: Function) -> float:
    """Calculate maintainability index for a function."""
    calculator = MetricsCalculator(function.codebase if hasattr(function, 'codebase') else None)
    return calculator.calculate_maintainability_index(function)


def analyze_function_metrics(function: Function) -> FunctionMetrics:
    """Comprehensive function analysis."""
    calculator = MetricsCalculator(function.codebase if hasattr(function, 'codebase') else None)
    return calculator.analyze_function_metrics(function)


def analyze_class_metrics(class_def: Class) -> ClassMetrics:
    """Comprehensive class analysis."""
    calculator = MetricsCalculator(class_def.codebase if hasattr(class_def, 'codebase') else None)
    return calculator.analyze_class_metrics(class_def)


def analyze_file_metrics(file: SourceFile) -> FileMetrics:
    """Comprehensive file analysis."""
    calculator = MetricsCalculator(file.codebase if hasattr(file, 'codebase') else None)
    return calculator.analyze_file_metrics(file)


def get_codebase_summary(codebase: Codebase) -> CodebaseMetrics:
    """Overall codebase metrics."""
    calculator = MetricsCalculator(codebase)
    return calculator.get_codebase_summary()

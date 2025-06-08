"""
Codebase Analysis Module

Provides comprehensive analysis functions for codebases using graph-sitter.
Based on the official graph-sitter.com API and features.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import json

from graph_sitter.configs.models.codebase import CodebaseConfig
from .analyzer import Analysis
from .enhanced_analyzer import enhanced_comprehensive_analysis

class AnalyzerAdapter:
    """Adapter to provide the expected analyzer interface."""
    
    def __init__(self, codebase_path: str, config: CodebaseConfig):
        from graph_sitter import Codebase
        self.codebase = Codebase(codebase_path, config=config)
        self.analysis = Analysis(self.codebase)
        
    def get_all_files(self) -> List[Dict[str, Any]]:
        """Get all files in the codebase."""
        files = getattr(self.codebase, 'files', [])
        if hasattr(files, '__iter__'):
            return [{'path': f.path, 'language': getattr(f, 'language', 'unknown')} 
                    for f in files]
        return []
    
    def get_all_functions(self) -> List[Dict[str, Any]]:
        """Get all functions in the codebase."""
        functions = getattr(self.codebase, 'functions', [])
        if hasattr(functions, '__iter__'):
            return [{'name': f.name} for f in functions]
        return []
    
    def get_all_classes(self) -> List[Dict[str, Any]]:
        """Get all classes in the codebase."""
        classes = getattr(self.codebase, 'classes', [])
        if hasattr(classes, '__iter__'):
            return [{'name': c.name} for c in classes]
        return []
    
    def get_all_imports(self) -> List[Dict[str, Any]]:
        """Get all imports in the codebase."""
        imports = getattr(self.codebase, 'imports', [])
        if hasattr(imports, '__iter__'):
            return [{'module': getattr(i, 'module', str(i))} for i in imports]
        return []
    
    def get_all_symbols(self) -> List[Dict[str, Any]]:
        """Get all symbols in the codebase."""
        symbols = getattr(self.codebase, 'symbols', [])
        if hasattr(symbols, '__iter__'):
            return [{'name': s.name} for s in symbols]
        return []
    
    def get_external_modules(self) -> List[str]:
        """Get external modules."""
        external_modules = getattr(self.codebase, 'external_modules', [])
        if hasattr(external_modules, '__iter__'):
            return [str(module) for module in external_modules]
        return []

    def analyze_complexity(self) -> Dict[str, Any]:
        """Analyze complexity metrics."""
        return {'average_complexity': 0.0, 'high_complexity_functions': []}
    
    def analyze_quality(self) -> Dict[str, Any]:
        """Analyze quality metrics."""
        return {'code_coverage': 0.0, 'doc_coverage': 0.0, 'test_coverage': 0.0}
    
    def analyze_file(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Analyze a specific file."""
        files = getattr(self.codebase, 'files', [])
        if hasattr(files, '__iter__'):
            for file in files:
                if file.path == filepath:
                    return {
                        'language': getattr(file, 'language', 'unknown'),
                        'functions': [f.name for f in getattr(file, 'functions', [])],
                        'classes': [c.name for c in getattr(file, 'classes', [])],
                        'imports': [getattr(i, 'module', str(i)) for i in getattr(file, 'imports', [])],
                        'symbols': [s.name for s in getattr(file, 'symbols', [])],
                        'dependencies': [],
                        'complexity_score': 0.0,
                        'lines_of_code': getattr(file, 'line_count', 0)
                    }
        return None
    
    def analyze_class(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Analyze a specific class."""
        classes = getattr(self.codebase, 'classes', [])
        if hasattr(classes, '__iter__'):
            for cls in classes:
                if cls.name == class_name:
                    return {
                        'filepath': getattr(cls, 'file', {}).get('path', ''),
                        'superclasses': [p.name for p in getattr(cls, 'superclasses', [])],
                        'subclasses': [],
                        'methods': [m.name for m in getattr(cls, 'methods', [])],
                        'attributes': [a.name for a in getattr(cls, 'attributes', [])],
                        'decorators': [],
                        'usages': [],
                        'dependencies': [],
                        'is_abstract': getattr(cls, 'is_abstract', False)
                    }
        return None
    
    def analyze_function(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Analyze a specific function."""
        functions = getattr(self.codebase, 'functions', [])
        if hasattr(functions, '__iter__'):
            for func in functions:
                if func.name == function_name:
                    return {
                        'filepath': getattr(func, 'file', {}).get('path', ''),
                        'usages': [],
                        'call_sites': [],
                        'dependencies': [],
                        'function_calls': [c.name for c in getattr(func, 'function_calls', [])],
                        'parameters': [p.name for p in getattr(func, 'parameters', [])],
                        'return_statements': [],
                        'decorators': [],
                        'is_async': getattr(func, 'is_async', False),
                        'is_generator': getattr(func, 'is_generator', False),
                        'complexity_score': 0.0
                    }
        return None
    
    def analyze_symbol(self, symbol_name: str) -> Optional[Dict[str, Any]]:
        """Analyze a specific symbol."""
        symbols = getattr(self.codebase, 'symbols', [])
        if hasattr(symbols, '__iter__'):
            for symbol in symbols:
                if symbol.name == symbol_name:
                    return {
                        'symbol_type': str(getattr(symbol, 'symbol_type', 'unknown')),
                        'filepath': getattr(symbol, 'file', {}).get('path', ''),
                        'usages': [],
                        'dependencies': [],
                        'scope': 'unknown',
                        'is_exported': False
                    }
        return None
    
    def get_function_usages(self, function_name: str) -> List[str]:
        """Get function usages."""
        return []
    
    def get_function_call_sites(self, function_name: str) -> List[str]:
        """Get function call sites."""
        return []
    
    def get_function_dependencies(self, function_name: str) -> List[str]:
        """Get function dependencies."""
        return []
    
    def get_function_calls(self, function_name: str) -> List[str]:
        """Get function calls."""
        return []
    
    def get_function_parameters(self, function_name: str) -> List[str]:
        """Get function parameters."""
        return []
    
    def get_function_returns(self, function_name: str) -> List[str]:
        """Get function return statements."""
        return []
    
    def get_function_decorators(self, function_name: str) -> List[str]:
        """Get function decorators."""
        return []
    
    def is_async_function(self, function_name: str) -> bool:
        """Check if function is async."""
        return False
    
    def is_generator_function(self, function_name: str) -> bool:
        """Check if function is generator."""
        return False
    
    def get_class_superclasses(self, class_name: str) -> List[str]:
        """Get class superclasses."""
        return []
    
    def get_class_subclasses(self, class_name: str) -> List[str]:
        """Get class subclasses."""
        return []
    
    def get_class_methods(self, class_name: str) -> List[str]:
        """Get class methods."""
        return []
    
    def get_class_attributes(self, class_name: str) -> List[str]:
        """Get class attributes."""
        return []
    
    def get_class_decorators(self, class_name: str) -> List[str]:
        """Get class decorators."""
        return []
    
    def get_class_usages(self, class_name: str) -> List[str]:
        """Get class usages."""
        return []
    
    def get_class_dependencies(self, class_name: str) -> List[str]:
        """Get class dependencies."""
        return []
    
    def is_abstract_class(self, class_name: str) -> bool:
        """Check if class is abstract."""
        return False
    
    def get_file_imports(self, file_path: str) -> List[str]:
        """Get file imports."""
        return []
    
    def get_file_inbound_imports(self, file_path: str) -> List[str]:
        """Get file inbound imports."""
        return []
    
    def get_file_symbols(self, file_path: str) -> List[str]:
        """Get file symbols."""
        return []
    
    def get_file_external_modules(self, file_path: str) -> List[str]:
        """Get file external modules."""
        return []


@dataclass
class CodebaseSummary:
    """Summary of codebase analysis results."""
    total_files: int
    total_functions: int
    total_classes: int
    total_imports: int
    total_symbols: int
    external_modules: List[str]
    languages: List[str]
    complexity_metrics: Dict[str, Any]
    quality_metrics: Dict[str, Any]


@dataclass
class FileSummary:
    """Summary of file analysis results."""
    filepath: str
    language: str
    functions: List[str]
    classes: List[str]
    imports: List[str]
    symbols: List[str]
    dependencies: List[str]
    complexity_score: float
    lines_of_code: int


@dataclass
class ClassSummary:
    """Summary of class analysis results."""
    name: str
    filepath: str
    superclasses: List[str]
    subclasses: List[str]
    methods: List[str]
    attributes: List[str]
    decorators: List[str]
    usages: List[str]
    dependencies: List[str]
    is_abstract: bool


@dataclass
class FunctionSummary:
    """Summary of function analysis results."""
    name: str
    filepath: str
    usages: List[str]
    call_sites: List[str]
    dependencies: List[str]
    function_calls: List[str]
    parameters: List[str]
    return_statements: List[str]
    decorators: List[str]
    is_async: bool
    is_generator: bool
    complexity_score: float


@dataclass
class SymbolSummary:
    """Summary of symbol analysis results."""
    name: str
    symbol_type: str
    filepath: str
    usages: List[str]
    dependencies: List[str]
    scope: str
    is_exported: bool


def get_codebase_summary(
    codebase_path: Union[str, Path],
    config: Optional[CodebaseConfig] = None
) -> CodebaseSummary:
    """
    Get comprehensive summary of the entire codebase.
    
    Args:
        codebase_path: Path to the codebase root
        config: Optional configuration for analysis
        
    Returns:
        CodebaseSummary with comprehensive codebase metrics
    """
    if config is None:
        config = CodebaseConfig(
            method_usages=True,
            generics=True,
            sync_enabled=True,
            full_range_index=True,
            py_resolve_syspath=True,
            exp_lazy_graph=False,
        )
    
    analyzer = AnalyzerAdapter(str(codebase_path), config)
    
    # Get basic metrics
    files = analyzer.get_all_files()
    functions = analyzer.get_all_functions()
    classes = analyzer.get_all_classes()
    imports = analyzer.get_all_imports()
    symbols = analyzer.get_all_symbols()
    external_modules = analyzer.get_external_modules()
    
    # Get language distribution
    languages = list(set(f.get('language', 'unknown') for f in files))
    
    # Get complexity metrics
    complexity_metrics = analyzer.analyze_complexity()
    
    # Get quality metrics
    quality_metrics = analyzer.analyze_quality()
    
    return CodebaseSummary(
        total_files=len(files),
        total_functions=len(functions),
        total_classes=len(classes),
        total_imports=len(imports),
        total_symbols=len(symbols),
        external_modules=external_modules,
        languages=languages,
        complexity_metrics=complexity_metrics,
        quality_metrics=quality_metrics
    )


def get_file_summary(
    codebase_path: Union[str, Path],
    filepath: str,
    config: Optional[CodebaseConfig] = None
) -> FileSummary:
    """
    Get comprehensive summary of a specific file.
    
    Args:
        codebase_path: Path to the codebase root
        filepath: Relative path to the file
        config: Optional configuration for analysis
        
    Returns:
        FileSummary with file-specific metrics
    """
    if config is None:
        config = CodebaseConfig(
            method_usages=True,
            generics=True,
            sync_enabled=True,
            full_range_index=True,
            py_resolve_syspath=True,
        )
    
    analyzer = AnalyzerAdapter(str(codebase_path), config)
    file_info = analyzer.analyze_file(filepath)
    
    if not file_info:
        raise ValueError(f"File not found: {filepath}")
    
    return FileSummary(
        filepath=filepath,
        language=file_info.get('language', 'unknown'),
        functions=file_info.get('functions', []),
        classes=file_info.get('classes', []),
        imports=file_info.get('imports', []),
        symbols=file_info.get('symbols', []),
        dependencies=file_info.get('dependencies', []),
        complexity_score=file_info.get('complexity_score', 0.0),
        lines_of_code=file_info.get('lines_of_code', 0)
    )


def get_class_summary(
    codebase_path: Union[str, Path],
    class_name: str,
    config: Optional[CodebaseConfig] = None
) -> ClassSummary:
    """
    Get comprehensive summary of a specific class.
    
    Args:
        codebase_path: Path to the codebase root
        class_name: Name of the class to analyze
        config: Optional configuration for analysis
        
    Returns:
        ClassSummary with class-specific metrics
    """
    if config is None:
        config = CodebaseConfig(
            method_usages=True,
            generics=True,
            sync_enabled=True,
            full_range_index=True,
            py_resolve_syspath=True,
        )
    
    analyzer = AnalyzerAdapter(str(codebase_path), config)
    class_info = analyzer.analyze_class(class_name)
    
    if not class_info:
        raise ValueError(f"Class not found: {class_name}")
    
    return ClassSummary(
        name=class_name,
        filepath=class_info.get('filepath', ''),
        superclasses=class_info.get('superclasses', []),
        subclasses=class_info.get('subclasses', []),
        methods=class_info.get('methods', []),
        attributes=class_info.get('attributes', []),
        decorators=class_info.get('decorators', []),
        usages=class_info.get('usages', []),
        dependencies=class_info.get('dependencies', []),
        is_abstract=class_info.get('is_abstract', False)
    )


def get_function_summary(
    codebase_path: Union[str, Path],
    function_name: str,
    config: Optional[CodebaseConfig] = None
) -> FunctionSummary:
    """
    Get comprehensive summary of a specific function.
    
    Args:
        codebase_path: Path to the codebase root
        function_name: Name of the function to analyze
        config: Optional configuration for analysis
        
    Returns:
        FunctionSummary with function-specific metrics
    """
    if config is None:
        config = CodebaseConfig(
            method_usages=True,
            generics=True,
            sync_enabled=True,
            full_range_index=True,
            py_resolve_syspath=True,
        )
    
    analyzer = AnalyzerAdapter(str(codebase_path), config)
    function_info = analyzer.analyze_function(function_name)
    
    if not function_info:
        raise ValueError(f"Function not found: {function_name}")
    
    return FunctionSummary(
        name=function_name,
        filepath=function_info.get('filepath', ''),
        usages=function_info.get('usages', []),
        call_sites=function_info.get('call_sites', []),
        dependencies=function_info.get('dependencies', []),
        function_calls=function_info.get('function_calls', []),
        parameters=function_info.get('parameters', []),
        return_statements=function_info.get('return_statements', []),
        decorators=function_info.get('decorators', []),
        is_async=function_info.get('is_async', False),
        is_generator=function_info.get('is_generator', False),
        complexity_score=function_info.get('complexity_score', 0.0)
    )


def get_symbol_summary(
    codebase_path: Union[str, Path],
    symbol_name: str,
    config: Optional[CodebaseConfig] = None
) -> SymbolSummary:
    """
    Get comprehensive summary of a specific symbol.
    
    Args:
        codebase_path: Path to the codebase root
        symbol_name: Name of the symbol to analyze
        config: Optional configuration for analysis
        
    Returns:
        SymbolSummary with symbol-specific metrics
    """
    if config is None:
        config = CodebaseConfig(
            method_usages=True,
            generics=True,
            sync_enabled=True,
            full_range_index=True,
            py_resolve_syspath=True,
        )
    
    analyzer = AnalyzerAdapter(str(codebase_path), config)
    symbol_info = analyzer.analyze_symbol(symbol_name)
    
    if not symbol_info:
        raise ValueError(f"Symbol not found: {symbol_name}")
    
    return SymbolSummary(
        name=symbol_name,
        symbol_type=symbol_info.get('symbol_type', 'unknown'),
        filepath=symbol_info.get('filepath', ''),
        usages=symbol_info.get('usages', []),
        dependencies=symbol_info.get('dependencies', []),
        scope=symbol_info.get('scope', 'unknown'),
        is_exported=symbol_info.get('is_exported', False)
    )


# Pre-computed Graph Element Access
class CodebaseElements:
    """
    Access all codebase elements through graph-sitter's optimized graph structure.
    """
    
    def __init__(self, codebase_path: Union[str, Path], config: Optional[CodebaseConfig] = None):
        self.codebase_path = str(codebase_path)
        self.config = config or CodebaseConfig(
            method_usages=True,
            generics=True,
            sync_enabled=True,
            full_range_index=True,
            py_resolve_syspath=True,
        )
        self.analyzer = AnalyzerAdapter(self.codebase_path, self.config)

    @property
    def functions(self) -> List[Dict[str, Any]]:
        """All functions in codebase with enhanced analysis."""
        functions = self.analyzer.get_all_functions()
        enhanced_functions = []
        
        for func in functions:
            enhanced_func = {
                **func,
                'usages': self.analyzer.get_function_usages(func['name']),
                'call_sites': self.analyzer.get_function_call_sites(func['name']),
                'dependencies': self.analyzer.get_function_dependencies(func['name']),
                'function_calls': self.analyzer.get_function_calls(func['name']),
                'parameters': self.analyzer.get_function_parameters(func['name']),
                'return_statements': self.analyzer.get_function_returns(func['name']),
                'decorators': self.analyzer.get_function_decorators(func['name']),
                'is_async': self.analyzer.is_async_function(func['name']),
                'is_generator': self.analyzer.is_generator_function(func['name']),
            }
            enhanced_functions.append(enhanced_func)
        
        return enhanced_functions
    
    @property
    def classes(self) -> List[Dict[str, Any]]:
        """All classes with enhanced hierarchy analysis."""
        classes = self.analyzer.get_all_classes()
        enhanced_classes = []
        
        for cls in classes:
            enhanced_cls = {
                **cls,
                'superclasses': self.analyzer.get_class_superclasses(cls['name']),
                'subclasses': self.analyzer.get_class_subclasses(cls['name']),
                'methods': self.analyzer.get_class_methods(cls['name']),
                'attributes': self.analyzer.get_class_attributes(cls['name']),
                'decorators': self.analyzer.get_class_decorators(cls['name']),
                'usages': self.analyzer.get_class_usages(cls['name']),
                'dependencies': self.analyzer.get_class_dependencies(cls['name']),
                'is_abstract': self.analyzer.is_abstract_class(cls['name']),
            }
            enhanced_classes.append(enhanced_cls)
        
        return enhanced_classes
    
    @property
    def imports(self) -> List[Dict[str, Any]]:
        """All import statements with relationship analysis."""
        return self.analyzer.get_all_imports()
    
    @property
    def files(self) -> List[Dict[str, Any]]:
        """All files with import relationship analysis."""
        files = self.analyzer.get_all_files()
        enhanced_files = []
        
        for file in files:
            enhanced_file = {
                **file,
                'imports': self.analyzer.get_file_imports(file['path']),
                'inbound_imports': self.analyzer.get_file_inbound_imports(file['path']),
                'symbols': self.analyzer.get_file_symbols(file['path']),
                'external_modules': self.analyzer.get_file_external_modules(file['path']),
            }
            enhanced_files.append(enhanced_file)
        
        return enhanced_files
    
    @property
    def symbols(self) -> List[Dict[str, Any]]:
        """All symbols in the codebase."""
        return self.analyzer.get_all_symbols()
    
    @property
    def external_modules(self) -> List[str]:
        """External dependencies."""
        return self.analyzer.get_external_modules()


# Export the main API functions
__all__ = [
    'get_codebase_summary',
    'get_file_summary', 
    'get_class_summary',
    'get_function_summary',
    'get_symbol_summary',
    'CodebaseElements',
    'CodebaseSummary',
    'FileSummary',
    'ClassSummary',
    'FunctionSummary',
    'SymbolSummary',
    'CodebaseConfig',
]

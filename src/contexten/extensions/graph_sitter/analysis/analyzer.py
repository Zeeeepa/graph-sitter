"""
Analysis class for graph-sitter codebase analysis

This module provides the Analysis class that wraps the existing graph-sitter
Codebase functionality to provide the exact API shown in the documentation.
"""

from graph_sitter import Codebase
from graph_sitter.configs.models.codebase import CodebaseConfig
from typing import Dict, Any, Optional


class Analysis:
    """
    Analysis class providing pre-computed graph element access and advanced analysis.
    
    Usage example from documentation:
    
    config = CodebaseConfig(
        # Performance optimizations
        method_usages=True,          # Enable method usage resolution
        generics=True,               # Enable generic type resolution
        sync_enabled=True,           # Enable graph sync during commits
        
        # Advanced analysis
        full_range_index=True,       # Full range-to-node mapping
        py_resolve_syspath=True,     # Resolve sys.path imports
        
        # Experimental features
        exp_lazy_graph=False,        # Lazy graph construction
    )
    
    codebase = Codebase("path/to/repo", config=config)
    analysis = Analysis(codebase)
    
    # Access pre-computed graph elements
    analysis.functions    # All functions in codebase
    analysis.classes      # All classes
    analysis.imports      # All import statements
    analysis.files        # All files
    analysis.symbols      # All symbols
    analysis.external_modules  # External dependencies
    """
    
    def __init__(self, codebase: Codebase):
        """Initialize Analysis with a Codebase instance."""
        self.codebase = codebase
    
    @property
    def functions(self):
        """
        All functions in codebase with enhanced analysis.
        
        Each function provides:
        - function.usages           # All usage sites
        - function.call_sites       # All call locations
        - function.dependencies     # Function dependencies
        - function.function_calls   # Functions this function calls
        - function.parameters       # Function parameters
        - function.return_statements # Return statements
        - function.decorators       # Function decorators
        - function.is_async         # Async function detection
        - function.is_generator     # Generator function detection
        """
        return self.codebase.functions
    
    @property
    def classes(self):
        """
        All classes in codebase with comprehensive analysis.
        
        Each class provides:
        - cls.superclasses         # Parent classes
        - cls.subclasses          # Child classes
        - cls.methods             # Class methods
        - cls.attributes          # Class attributes
        - cls.decorators          # Class decorators
        - cls.usages              # Class usage sites
        - cls.dependencies        # Class dependencies
        - cls.is_abstract         # Abstract class detection
        """
        return self.codebase.classes
    
    @property
    def imports(self):
        """All import statements in the codebase."""
        return self.codebase.imports
    
    @property
    def files(self):
        """
        All files in the codebase with import analysis.
        
        Each file provides:
        - file.imports            # Outbound imports
        - file.inbound_imports    # Files that import this file
        - file.symbols            # Symbols defined in file
        - file.external_modules   # External dependencies
        """
        return self.codebase.files
    
    @property
    def symbols(self):
        """All symbols (functions, classes, variables) in the codebase."""
        return self.codebase.symbols
    
    @property
    def external_modules(self):
        """External dependencies imported by the codebase."""
        return self.codebase.external_modules
    
    def get_function_analysis(self, function_name: str) -> Dict[str, Any]:
        """Get detailed analysis for a specific function."""
        functions_attr = getattr(self.codebase, 'functions', [])
        functions = list(functions_attr) if hasattr(functions_attr, '__iter__') else []
        
        for func in functions:
            if func.name == function_name:
                code_block = getattr(func, 'code_block', None)
                line_count = 0
                if code_block:
                    lines = getattr(code_block, 'lines', [])
                    line_count = len(lines) if hasattr(lines, '__len__') else 0
                
                return {
                    'name': func.name,
                    'parameters': [p.name for p in func.parameters],
                    'return_type': getattr(func, 'return_type', None),
                    'decorators': [d.name for d in func.decorators],
                    'is_async': func.is_async,
                    'is_generator': getattr(func, 'is_generator', False),
                    'complexity': getattr(func, 'complexity', 0),
                    'line_count': line_count,
                    'usages': len(func.usages) if hasattr(func, 'usages') else 0
                }
        return {}
    
    def get_class_analysis(self, class_name: str) -> Dict[str, Any]:
        """Get detailed analysis for a specific class."""
        classes_attr = getattr(self.codebase, 'classes', [])
        classes = list(classes_attr) if hasattr(classes_attr, '__iter__') else []
        
        for cls in classes:
            if cls.name == class_name:
                methods = getattr(cls, 'methods', [])
                methods_list = list(methods) if hasattr(methods, '__iter__') else []
                return {
                    'name': cls.name,
                    'methods': len(methods_list),
                    'attributes': len(getattr(cls, 'attributes', [])),
                    'superclasses': [sc.name for sc in getattr(cls, 'superclasses', [])],
                    'subclasses': [sc.name for sc in getattr(cls, 'subclasses', [])],
                    'decorators': [d.name for d in getattr(cls, 'decorators', [])],
                    'is_abstract': getattr(cls, 'is_abstract', False)
                }
        return {}
    
    def get_import_analysis(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Get import analysis for a file or entire codebase."""
        if file_path:
            file = self.codebase.get_file(file_path)
            if not file:
                return {"error": f"File not found: {file_path}"}
            
            return {
                "file": file.path,
                "imports": len(getattr(file, 'imports', [])),
                "external_imports": len([imp for imp in getattr(file, 'imports', []) if getattr(imp, 'is_external', False)])
            }
        else:
            files_attr = getattr(self.codebase, 'files', [])
            files = list(files_attr) if hasattr(files_attr, '__iter__') else []
            total_imports = sum(len(getattr(f, 'imports', [])) for f in files)
            return {
                "total_files": len(files),
                "total_imports": total_imports,
                "average_imports_per_file": total_imports / len(files) if files else 0
            }

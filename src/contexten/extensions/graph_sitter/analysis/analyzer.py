"""
Analysis class for graph-sitter codebase analysis

This module provides the Analysis class that wraps the existing graph-sitter
Codebase functionality to provide the exact API shown in the documentation.
"""

from graph_sitter import Codebase
from graph_sitter.configs.models.codebase import CodebaseConfig


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
    
    def get_function_analysis(self, function_name: str):
        """Get detailed analysis for a specific function."""
        func = self.codebase.get_function(function_name)
        if not func:
            return None
            
        return {
            'name': func.name,
            'usages': len(func.usages),
            'call_sites': len(func.call_sites),
            'dependencies': len(func.dependencies),
            'function_calls': len(func.function_calls),
            'parameters': len(func.parameters),
            'return_statements': len(func.return_statements),
            'decorators': len(func.decorators),
            'is_async': func.is_async,
            'is_generator': func.is_generator
        }
    
    def get_class_analysis(self, class_name: str):
        """Get detailed analysis for a specific class."""
        cls = self.codebase.get_class(class_name)
        if not cls:
            return None
            
        return {
            'name': cls.name,
            'superclasses': cls.parent_class_names,
            'methods': len(cls.methods),
            'attributes': len(cls.attributes),
            'decorators': len(cls.decorators),
            'usages': len(cls.usages),
            'dependencies': len(cls.dependencies)
        }
    
    def get_import_analysis(self, file_path: str = None):
        """Get import relationship analysis for a file or entire codebase."""
        if file_path:
            file = self.codebase.get_file(file_path)
            if not file:
                return None
            return {
                'file': file.name,
                'imports': len(file.imports),
                'symbols': len(file.symbols),
                'external_modules': len([imp for imp in file.imports if imp.imported_symbol and hasattr(imp.imported_symbol, 'is_external')])
            }
        else:
            # Codebase-wide import analysis
            return {
                'total_imports': len(self.imports),
                'total_external_modules': len(self.external_modules),
                'files_with_imports': len([f for f in self.files if f.imports])
            }


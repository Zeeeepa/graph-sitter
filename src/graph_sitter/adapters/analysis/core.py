"""
🔍 Core Analysis Engine

Comprehensive codebase analysis functionality including:
- Function context gathering and dependency analysis
- Dead code detection and import relationship mapping
- Symbol usage analysis and dependency tracking
- Training data generation for ML models
- Class hierarchy exploration and analysis

Based on patterns from README.md and existing codebase_analysis.py
"""

import json
import traceback
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set, Union
from pathlib import Path

try:
    from graph_sitter.core.class_definition import Class
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.external_module import ExternalModule
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.function import Function
    from graph_sitter.core.import_resolution import Import
    from graph_sitter.core.symbol import Symbol
    from graph_sitter.enums import EdgeType, SymbolType
except ImportError:
    # Fallback for when graph_sitter modules are not available
    print("Warning: Graph-sitter modules not available. Some functionality may be limited.")
    Class = object
    Codebase = object
    ExternalModule = object
    SourceFile = object
    Function = object
    Import = object
    Symbol = object
    EdgeType = None
    SymbolType = None


@dataclass
class AnalysisResult:
    """Container for analysis results"""
    codebase_summary: str = ""
    file_summaries: Dict[str, str] = field(default_factory=dict)
    class_summaries: Dict[str, str] = field(default_factory=dict)
    function_summaries: Dict[str, str] = field(default_factory=dict)
    symbol_summaries: Dict[str, str] = field(default_factory=dict)
    dead_code: List[str] = field(default_factory=list)
    recursive_functions: List[str] = field(default_factory=list)
    test_analysis: Dict[str, Any] = field(default_factory=dict)
    import_relationships: Dict[str, List[str]] = field(default_factory=dict)
    class_hierarchies: Dict[str, List[str]] = field(default_factory=dict)
    training_data: Dict[str, Any] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)


class AnalysisEngine:
    """
    Core analysis engine that provides comprehensive codebase analysis
    """
    
    def __init__(self, codebase: Optional[Codebase] = None, config: Optional[Dict] = None):
        self.codebase = codebase
        self.config = config or {}
        self.results = AnalysisResult()
    
    def analyze(self, codebase: Optional[Codebase] = None) -> AnalysisResult:
        """
        Perform comprehensive codebase analysis
        """
        if codebase:
            self.codebase = codebase
        
        if not self.codebase:
            raise ValueError("No codebase provided for analysis")
        
        try:
            # Core analysis components
            self._analyze_codebase_structure()
            self._analyze_files()
            self._analyze_classes()
            self._analyze_functions()
            self._analyze_symbols()
            self._detect_dead_code()
            self._analyze_recursive_functions()
            self._analyze_tests()
            self._analyze_import_relationships()
            self._analyze_class_hierarchies()
            self._generate_training_data()
            self._detect_issues()
            
            return self.results
            
        except Exception as e:
            print(f"Error during analysis: {e}")
            traceback.print_exc()
            return self.results
    
    def _analyze_codebase_structure(self):
        """Analyze overall codebase structure"""
        self.results.codebase_summary = get_codebase_summary(self.codebase)
    
    def _analyze_files(self):
        """Analyze individual files"""
        for file in self.codebase.files:
            try:
                self.results.file_summaries[file.name] = get_file_summary(file)
            except Exception as e:
                print(f"Error analyzing file {file.name}: {e}")
    
    def _analyze_classes(self):
        """Analyze classes"""
        for cls in self.codebase.classes:
            try:
                self.results.class_summaries[cls.name] = get_class_summary(cls)
            except Exception as e:
                print(f"Error analyzing class {cls.name}: {e}")
    
    def _analyze_functions(self):
        """Analyze functions"""
        for func in self.codebase.functions:
            try:
                self.results.function_summaries[func.name] = get_function_summary(func)
            except Exception as e:
                print(f"Error analyzing function {func.name}: {e}")
    
    def _analyze_symbols(self):
        """Analyze symbols"""
        for symbol in self.codebase.symbols:
            try:
                self.results.symbol_summaries[symbol.name] = get_symbol_summary(symbol)
            except Exception as e:
                print(f"Error analyzing symbol {symbol.name}: {e}")
    
    def _detect_dead_code(self):
        """Detect dead code (unused functions)"""
        for func in self.codebase.functions:
            try:
                if hasattr(func, 'usages') and len(func.usages) == 0:
                    self.results.dead_code.append(func.name)
            except Exception as e:
                print(f"Error checking dead code for {func.name}: {e}")
    
    def _analyze_recursive_functions(self):
        """Find recursive functions"""
        for func in self.codebase.functions:
            try:
                if hasattr(func, 'function_calls'):
                    if any(call.name == func.name for call in func.function_calls):
                        self.results.recursive_functions.append(func.name)
            except Exception as e:
                print(f"Error checking recursion for {func.name}: {e}")
    
    def _analyze_tests(self):
        """Analyze test functions and classes"""
        test_functions = [x for x in self.codebase.functions if x.name.startswith('test_')]
        test_classes = [x for x in self.codebase.classes if x.name.startswith('Test')]
        
        self.results.test_analysis = {
            "total_test_functions": len(test_functions),
            "total_test_classes": len(test_classes),
            "tests_per_file": len(test_functions) / len(list(self.codebase.files)) if self.codebase.files else 0,
            "test_functions": [f.name for f in test_functions],
            "test_classes": [c.name for c in test_classes]
        }
        
        # Find files with the most tests
        file_test_counts = Counter([x.file for x in test_classes if hasattr(x, 'file')])
        self.results.test_analysis["top_test_files"] = dict(file_test_counts.most_common(5))
    
    def _analyze_import_relationships(self):
        """Analyze import relationships"""
        for file in self.codebase.files:
            try:
                imports = []
                if hasattr(file, 'imports'):
                    for import_stmt in file.imports:
                        if hasattr(import_stmt, 'resolved_symbol') and import_stmt.resolved_symbol:
                            if hasattr(import_stmt.resolved_symbol, 'file'):
                                imports.append(import_stmt.resolved_symbol.file.path)
                
                self.results.import_relationships[file.name] = imports
            except Exception as e:
                print(f"Error analyzing imports for {file.name}: {e}")
    
    def _analyze_class_hierarchies(self):
        """Analyze class inheritance hierarchies"""
        for cls in self.codebase.classes:
            try:
                hierarchy = []
                if hasattr(cls, 'subclasses'):
                    hierarchy = [subclass.name for subclass in cls.subclasses]
                    # Go deeper in the inheritance tree
                    for subclass in cls.subclasses:
                        if hasattr(subclass, 'subclasses'):
                            hierarchy.extend([sub_sub.name for sub_sub in subclass.subclasses])
                
                self.results.class_hierarchies[cls.name] = hierarchy
            except Exception as e:
                print(f"Error analyzing hierarchy for {cls.name}: {e}")
    
    def _generate_training_data(self):
        """Generate training data for ML models"""
        training_data = {
            "functions": [],
            "metadata": {
                "total_functions": len(list(self.codebase.functions)),
                "total_processed": 0,
                "avg_dependencies": 0,
                "avg_usages": 0,
            },
        }
        
        # Process each function in the codebase
        for function in self.codebase.functions:
            try:
                # Skip if function is too small
                if hasattr(function, 'source') and len(function.source.split("\n")) < 2:
                    continue
                
                # Get function context
                context = get_function_context(function)
                
                # Only keep functions with enough context
                if len(context["dependencies"]) + len(context["usages"]) > 0:
                    training_data["functions"].append(context)
            except Exception as e:
                print(f"Error generating training data for {function.name}: {e}")
        
        # Update metadata
        training_data["metadata"]["total_processed"] = len(training_data["functions"])
        if training_data["functions"]:
            training_data["metadata"]["avg_dependencies"] = sum(
                len(f["dependencies"]) for f in training_data["functions"]
            ) / len(training_data["functions"])
            training_data["metadata"]["avg_usages"] = sum(
                len(f["usages"]) for f in training_data["functions"]
            ) / len(training_data["functions"])
        
        self.results.training_data = training_data
    
    def _detect_issues(self):
        """Detect common code issues"""
        issues = []
        
        for function in self.codebase.functions:
            try:
                # Check documentation
                if hasattr(function, 'docstring') and not function.docstring:
                    issues.append({
                        "type": "missing_docstring",
                        "severity": "warning",
                        "message": f"Function '{function.name}' missing docstring",
                        "location": getattr(function, 'filepath', 'unknown'),
                        "function": function.name
                    })
                
                # Check error handling for async functions
                if hasattr(function, 'is_async') and function.is_async:
                    if hasattr(function, 'has_try_catch') and not function.has_try_catch:
                        issues.append({
                            "type": "missing_error_handling",
                            "severity": "error",
                            "message": f"Async function '{function.name}' missing error handling",
                            "location": getattr(function, 'filepath', 'unknown'),
                            "function": function.name
                        })
            except Exception as e:
                print(f"Error detecting issues for {function.name}: {e}")
        
        self.results.issues = issues


class CodebaseAnalyzer:
    """
    High-level analyzer that orchestrates different analysis components
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.engine = AnalysisEngine(config=self.config)
    
    def analyze_repository(self, repo_path: str) -> AnalysisResult:
        """Analyze a repository from path"""
        try:
            codebase = Codebase.from_repo(repo_path)
            return self.engine.analyze(codebase)
        except Exception as e:
            print(f"Error analyzing repository {repo_path}: {e}")
            return AnalysisResult()
    
    def analyze_codebase(self, codebase: Codebase) -> AnalysisResult:
        """Analyze an existing codebase object"""
        return self.engine.analyze(codebase)
    
    def export_results(self, results: AnalysisResult, output_path: str, format: str = "json"):
        """Export analysis results to file"""
        try:
            if format.lower() == "json":
                with open(output_path, 'w') as f:
                    json.dump(results.__dict__, f, indent=2, default=str)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            print(f"Error exporting results: {e}")


# Core analysis functions (from README.md examples)

def get_codebase_summary(codebase: Codebase) -> str:
    """Get comprehensive codebase summary"""
    try:
        node_summary = f"""Contains {len(codebase.ctx.get_nodes())} nodes
- {len(list(codebase.files))} files
- {len(list(codebase.imports))} imports
- {len(list(codebase.external_modules))} external_modules
- {len(list(codebase.symbols))} symbols
\t- {len(list(codebase.classes))} classes
\t- {len(list(codebase.functions))} functions
\t- {len(list(codebase.global_vars))} global_vars
\t- {len(list(codebase.interfaces))} interfaces
"""
        edge_summary = f"""Contains {len(codebase.ctx.edges)} edges
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.SYMBOL_USAGE])} symbol -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION])} import -> used symbol
- {len([x for x in codebase.ctx.edges if x[2].type == EdgeType.EXPORT])} export -> exported symbol
    """
        return f"{node_summary}\n{edge_summary}"
    except Exception as e:
        return f"Error generating codebase summary: {e}"


def get_file_summary(file: SourceFile) -> str:
    """Get file analysis summary"""
    try:
        return f"""==== [ `{file.name}` (SourceFile) Dependency Summary ] ====
- {len(file.imports)} imports
- {len(file.symbols)} symbol references
\t- {len(file.classes)} classes
\t- {len(file.functions)} functions
\t- {len(file.global_vars)} global variables
\t- {len(file.interfaces)} interfaces

==== [ `{file.name}` Usage Summary ] ====
- {len(file.imports)} importers
"""
    except Exception as e:
        return f"Error generating file summary for {file.name}: {e}"


def get_class_summary(cls: Class) -> str:
    """Get class analysis summary"""
    try:
        return f"""==== [ `{cls.name}` (Class) Dependency Summary ] ====
- parent classes: {cls.parent_class_names}
- {len(cls.methods)} methods
- {len(cls.attributes)} attributes
- {len(cls.decorators)} decorators
- {len(cls.dependencies)} dependencies

{get_symbol_summary(cls)}
    """
    except Exception as e:
        return f"Error generating class summary for {cls.name}: {e}"


def get_function_summary(func: Function) -> str:
    """Get function analysis summary"""
    try:
        return f"""==== [ `{func.name}` (Function) Dependency Summary ] ====
- {len(func.return_statements)} return statements
- {len(func.parameters)} parameters
- {len(func.function_calls)} function calls
- {len(func.call_sites)} call sites
- {len(func.decorators)} decorators
- {len(func.dependencies)} dependencies

{get_symbol_summary(func)}
        """
    except Exception as e:
        return f"Error generating function summary for {func.name}: {e}"


def get_symbol_summary(symbol: Symbol) -> str:
    """Get symbol usage summary"""
    try:
        usages = symbol.symbol_usages
        imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]

        return f"""==== [ `{symbol.name}` ({type(symbol).__name__}) Usage Summary ] ====
- {len(usages)} usages
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t- {len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t- {len(imported_symbols)} imports
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function])} functions
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class])} classes
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar])} global variables
\t\t- {len([x for x in imported_symbols if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface])} interfaces
\t\t- {len([x for x in imported_symbols if isinstance(x, ExternalModule)])} external modules
\t\t- {len([x for x in imported_symbols if isinstance(x, SourceFile)])} files
    """
    except Exception as e:
        return f"Error generating symbol summary for {symbol.name}: {e}"


def get_function_context(function: Function) -> Dict[str, Any]:
    """Get the implementation, dependencies, and usages of a function."""
    try:
        context = {
            "implementation": {
                "source": getattr(function, 'source', ''),
                "filepath": getattr(function, 'filepath', '')
            },
            "dependencies": [],
            "usages": [],
        }

        # Add dependencies
        if hasattr(function, 'dependencies'):
            for dep in function.dependencies:
                # Hop through imports to find the root symbol source
                if isinstance(dep, Import):
                    dep = hop_through_imports(dep)

                context["dependencies"].append({
                    "source": getattr(dep, 'source', ''),
                    "filepath": getattr(dep, 'filepath', '')
                })

        # Add usages
        if hasattr(function, 'usages'):
            for usage in function.usages:
                if hasattr(usage, 'usage_symbol'):
                    context["usages"].append({
                        "source": getattr(usage.usage_symbol, 'source', ''),
                        "filepath": getattr(usage.usage_symbol, 'filepath', ''),
                    })

        return context
    except Exception as e:
        print(f"Error getting function context for {function.name}: {e}")
        return {
            "implementation": {"source": "", "filepath": ""},
            "dependencies": [],
            "usages": [],
        }


def hop_through_imports(imp: Import) -> Union[Symbol, ExternalModule]:
    """Finds the root symbol for an import."""
    try:
        if hasattr(imp, 'imported_symbol') and isinstance(imp.imported_symbol, Import):
            return hop_through_imports(imp.imported_symbol)
        return imp.imported_symbol
    except Exception as e:
        print(f"Error hopping through imports: {e}")
        return imp


def analyze_codebase(codebase: Codebase) -> List[Dict[str, Any]]:
    """Analyze codebase for common issues and flag them"""
    issues = []
    
    try:
        for function in codebase.functions:
            # Check documentation
            if hasattr(function, 'docstring') and not function.docstring:
                issues.append({
                    "type": "missing_docstring",
                    "message": "Missing docstring",
                    "function": function.name,
                    "location": getattr(function, 'filepath', 'unknown')
                })
                
            # Check error handling
            if hasattr(function, 'is_async') and function.is_async:
                if hasattr(function, 'has_try_catch') and not function.has_try_catch:
                    issues.append({
                        "type": "missing_error_handling",
                        "message": "Async function missing error handling",
                        "function": function.name,
                        "location": getattr(function, 'filepath', 'unknown')
                    })
    except Exception as e:
        print(f"Error during codebase analysis: {e}")
    
    return issues


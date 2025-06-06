"""
Core Analysis Engine

Provides the fundamental analysis capabilities for codebase examination.
Consolidates functionality from existing analysis modules.
"""

import logging
import math
import time
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path

from graph_sitter.core.class_definition import Class
from graph_sitter.core.codebase import Codebase
from graph_sitter.core.external_module import ExternalModule
from graph_sitter.core.file import SourceFile
from graph_sitter.core.function import Function
from graph_sitter.core.import_resolution import Import
from graph_sitter.core.symbol import Symbol
from graph_sitter.enums import EdgeType, SymbolType

from ..config.analysis_config import AnalysisConfig


@dataclass
class AnalysisResult:
    """Container for analysis results."""
    
    codebase_summary: Dict[str, Any] = field(default_factory=dict)
    file_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    class_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    function_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    symbol_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    dead_code: List[Dict[str, Any]] = field(default_factory=list)
    test_analysis: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: str = ""


class AnalysisEngine:
    """
    Core analysis engine that provides comprehensive codebase analysis.
    
    Consolidates functionality from existing analysis modules and provides
    a unified interface for all analysis operations.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """Initialize the analysis engine with configuration."""
        self.config = config or AnalysisConfig()
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging based on configuration."""
        level = logging.DEBUG if self.config.graph_sitter.debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def analyze_codebase(self, codebase: Codebase) -> AnalysisResult:
        """
        Perform comprehensive codebase analysis.
        
        Args:
            codebase: The codebase to analyze
            
        Returns:
            AnalysisResult containing all analysis data
        """
        start_time = time.time()
        self.logger.info("Starting comprehensive codebase analysis")
        
        result = AnalysisResult()
        result.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Core analysis
            result.codebase_summary = self._analyze_codebase_summary(codebase)
            
            if self.config.enable_dependency_analysis:
                result.dependencies = self._analyze_dependencies(codebase)
            
            # File-level analysis
            if self.config.enable_metrics_collection:
                result.file_summaries = self._analyze_files(codebase)
                result.class_summaries = self._analyze_classes(codebase)
                result.function_summaries = self._analyze_functions(codebase)
                result.symbol_summaries = self._analyze_symbols(codebase)
            
            # Specialized analysis
            if self.config.enable_dead_code_detection:
                result.dead_code = self._detect_dead_code(codebase)
            
            if self.config.enable_test_analysis:
                result.test_analysis = self._analyze_tests(codebase)
            
            # Metrics collection
            if self.config.enable_metrics_collection:
                result.metrics = self._collect_metrics(codebase, result)
            
            # Issue detection
            result.issues = self._detect_issues(codebase, result)
        
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            result.issues.append({
                "type": "analysis_error",
                "message": str(e),
                "severity": "critical"
            })
        
        result.execution_time = time.time() - start_time
        self.logger.info(f"Analysis completed in {result.execution_time:.2f} seconds")
        
        return result
    
    def _analyze_codebase_summary(self, codebase: Codebase) -> Dict[str, Any]:
        """Generate comprehensive codebase summary."""
        try:
            nodes = codebase.ctx.get_nodes()
            edges = codebase.ctx.edges
            
            # Node statistics
            node_stats = {
                "total_nodes": len(nodes),
                "files": len(list(codebase.files)),
                "imports": len(list(codebase.imports)),
                "external_modules": len(list(codebase.external_modules)),
                "symbols": len(list(codebase.symbols)),
                "classes": len(list(codebase.classes)),
                "functions": len(list(codebase.functions)),
                "global_vars": len(list(codebase.global_vars)),
                "interfaces": len(list(codebase.interfaces))
            }
            
            # Edge statistics
            edge_stats = {
                "total_edges": len(edges),
                "symbol_usages": len([x for x in edges if x[2].type == EdgeType.SYMBOL_USAGE]),
                "import_resolutions": len([x for x in edges if x[2].type == EdgeType.IMPORT_SYMBOL_RESOLUTION]),
                "exports": len([x for x in edges if x[2].type == EdgeType.EXPORT])
            }
            
            return {
                "nodes": node_stats,
                "edges": edge_stats,
                "complexity_score": self._calculate_complexity_score(node_stats, edge_stats)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to analyze codebase summary: {e}")
            return {"error": str(e)}
    
    def _analyze_files(self, codebase: Codebase) -> Dict[str, Dict[str, Any]]:
        """Analyze all files in the codebase."""
        file_summaries = {}
        
        for file in codebase.files:
            try:
                summary = {
                    "name": file.name,
                    "path": str(file.filepath) if hasattr(file, 'filepath') else file.name,
                    "imports": len(file.imports),
                    "symbols": len(file.symbols),
                    "classes": len(file.classes),
                    "functions": len(file.functions),
                    "global_vars": len(file.global_vars),
                    "interfaces": len(file.interfaces),
                    "lines_of_code": self._count_lines_of_code(file),
                    "complexity": self._calculate_file_complexity(file)
                }
                file_summaries[file.name] = summary
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze file {file.name}: {e}")
                file_summaries[file.name] = {"error": str(e)}
        
        return file_summaries
    
    def _analyze_classes(self, codebase: Codebase) -> Dict[str, Dict[str, Any]]:
        """Analyze all classes in the codebase."""
        class_summaries = {}
        
        for cls in codebase.classes:
            try:
                summary = {
                    "name": cls.name,
                    "parent_classes": cls.parent_class_names,
                    "methods": len(cls.methods),
                    "attributes": len(cls.attributes),
                    "decorators": len(cls.decorators),
                    "dependencies": len(cls.dependencies),
                    "usages": len(cls.symbol_usages),
                    "inheritance_depth": len(cls.parent_class_names),
                    "complexity": self._calculate_class_complexity(cls)
                }
                class_summaries[cls.name] = summary
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze class {cls.name}: {e}")
                class_summaries[cls.name] = {"error": str(e)}
        
        return class_summaries
    
    def _analyze_functions(self, codebase: Codebase) -> Dict[str, Dict[str, Any]]:
        """Analyze all functions in the codebase."""
        function_summaries = {}
        
        for func in codebase.functions:
            try:
                summary = {
                    "name": func.name,
                    "return_statements": len(func.return_statements),
                    "parameters": len(func.parameters),
                    "function_calls": len(func.function_calls),
                    "call_sites": len(func.call_sites),
                    "decorators": len(func.decorators),
                    "dependencies": len(func.dependencies),
                    "usages": len(func.symbol_usages),
                    "is_recursive": self._is_recursive_function(func),
                    "complexity": self._calculate_function_complexity(func)
                }
                function_summaries[func.name] = summary
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze function {func.name}: {e}")
                function_summaries[func.name] = {"error": str(e)}
        
        return function_summaries
    
    def _analyze_symbols(self, codebase: Codebase) -> Dict[str, Dict[str, Any]]:
        """Analyze all symbols in the codebase."""
        symbol_summaries = {}
        
        for symbol in codebase.symbols:
            try:
                usages = symbol.symbol_usages
                imported_symbols = [x.imported_symbol for x in usages if isinstance(x, Import)]
                
                summary = {
                    "name": symbol.name,
                    "type": symbol.symbol_type.name if hasattr(symbol, 'symbol_type') else "unknown",
                    "total_usages": len(usages),
                    "function_usages": len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Function]),
                    "class_usages": len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Class]),
                    "global_var_usages": len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.GlobalVar]),
                    "interface_usages": len([x for x in usages if isinstance(x, Symbol) and x.symbol_type == SymbolType.Interface]),
                    "imported_symbols": len(imported_symbols),
                    "external_modules": len([x for x in imported_symbols if isinstance(x, ExternalModule)]),
                    "files": len([x for x in imported_symbols if isinstance(x, SourceFile)])
                }
                symbol_summaries[symbol.name] = summary
                
            except Exception as e:
                self.logger.warning(f"Failed to analyze symbol {symbol.name}: {e}")
                symbol_summaries[symbol.name] = {"error": str(e)}
        
        return symbol_summaries
    
    def _analyze_dependencies(self, codebase: Codebase) -> Dict[str, List[str]]:
        """Analyze dependency relationships."""
        dependencies = {}
        
        try:
            for file in codebase.files:
                file_deps = []
                for import_stmt in file.imports:
                    if hasattr(import_stmt, 'resolved_symbol') and import_stmt.resolved_symbol:
                        if hasattr(import_stmt.resolved_symbol, 'file'):
                            file_deps.append(str(import_stmt.resolved_symbol.file.filepath))
                dependencies[file.name] = file_deps
                
        except Exception as e:
            self.logger.error(f"Failed to analyze dependencies: {e}")
        
        return dependencies
    
    def _detect_dead_code(self, codebase: Codebase) -> List[Dict[str, Any]]:
        """Detect potentially dead code."""
        dead_code = []
        
        try:
            # Find functions with no usages
            for func in codebase.functions:
                if len(func.usages) == 0:
                    dead_code.append({
                        "type": "unused_function",
                        "name": func.name,
                        "location": str(func.file.filepath) if hasattr(func, 'file') else "unknown",
                        "severity": "warning"
                    })
            
            # Find classes with no usages
            for cls in codebase.classes:
                if len(cls.symbol_usages) == 0:
                    dead_code.append({
                        "type": "unused_class",
                        "name": cls.name,
                        "location": str(cls.file.filepath) if hasattr(cls, 'file') else "unknown",
                        "severity": "warning"
                    })
                    
        except Exception as e:
            self.logger.error(f"Failed to detect dead code: {e}")
        
        return dead_code
    
    def _analyze_tests(self, codebase: Codebase) -> Dict[str, Any]:
        """Analyze test-related code."""
        test_analysis = {
            "test_functions": [],
            "test_classes": [],
            "test_files": [],
            "coverage_estimate": 0.0
        }
        
        try:
            # Find test functions
            test_functions = [f for f in codebase.functions if f.name.startswith('test_')]
            test_analysis["test_functions"] = [f.name for f in test_functions]
            
            # Find test classes
            test_classes = [c for c in codebase.classes if c.name.startswith('Test')]
            test_analysis["test_classes"] = [c.name for c in test_classes]
            
            # Find test files
            test_files = [f for f in codebase.files if 'test' in f.name.lower()]
            test_analysis["test_files"] = [f.name for f in test_files]
            
            # Estimate coverage
            total_functions = len(list(codebase.functions))
            if total_functions > 0:
                test_analysis["coverage_estimate"] = len(test_functions) / total_functions
                
        except Exception as e:
            self.logger.error(f"Failed to analyze tests: {e}")
        
        return test_analysis
    
    def _collect_metrics(self, codebase: Codebase, result: AnalysisResult) -> Dict[str, Any]:
        """Collect comprehensive metrics."""
        metrics = {
            "maintainability_index": 0.0,
            "technical_debt_ratio": 0.0,
            "code_quality_score": 0.0,
            "complexity_distribution": {},
            "size_metrics": {},
            "quality_metrics": {}
        }
        
        try:
            # Size metrics
            metrics["size_metrics"] = {
                "total_files": len(result.file_summaries),
                "total_classes": len(result.class_summaries),
                "total_functions": len(result.function_summaries),
                "total_lines": sum(f.get("lines_of_code", 0) for f in result.file_summaries.values()),
                "average_file_size": sum(f.get("lines_of_code", 0) for f in result.file_summaries.values()) / max(len(result.file_summaries), 1)
            }
            
            # Quality metrics
            metrics["quality_metrics"] = {
                "dead_code_count": len(result.dead_code),
                "test_coverage_estimate": result.test_analysis.get("coverage_estimate", 0.0),
                "dependency_count": sum(len(deps) for deps in result.dependencies.values()),
                "issue_count": len(result.issues)
            }
            
            # Calculate composite scores
            metrics["maintainability_index"] = self._calculate_maintainability_index(metrics)
            metrics["code_quality_score"] = self._calculate_quality_score(metrics)
            
        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
        
        return metrics
    
    def _detect_issues(self, codebase: Codebase, result: AnalysisResult) -> List[Dict[str, Any]]:
        """Detect code quality issues."""
        issues = []
        
        try:
            # Check for missing documentation
            for func_name, func_data in result.function_summaries.items():
                if func_data.get("complexity", 0) > 10:
                    issues.append({
                        "type": "high_complexity",
                        "target": func_name,
                        "message": f"Function {func_name} has high complexity",
                        "severity": "warning"
                    })
            
            # Check for large classes
            for class_name, class_data in result.class_summaries.items():
                if class_data.get("methods", 0) > 20:
                    issues.append({
                        "type": "large_class",
                        "target": class_name,
                        "message": f"Class {class_name} has too many methods",
                        "severity": "warning"
                    })
            
            # Check for large files
            for file_name, file_data in result.file_summaries.items():
                if file_data.get("lines_of_code", 0) > 1000:
                    issues.append({
                        "type": "large_file",
                        "target": file_name,
                        "message": f"File {file_name} is very large",
                        "severity": "info"
                    })
                    
        except Exception as e:
            self.logger.error(f"Failed to detect issues: {e}")
        
        return issues
    
    # Helper methods for calculations
    def _calculate_complexity_score(self, node_stats: Dict, edge_stats: Dict) -> float:
        """Calculate overall complexity score."""
        try:
            nodes = node_stats.get("total_nodes", 0)
            edges = edge_stats.get("total_edges", 0)
            return (edges / max(nodes, 1)) * 100
        except:
            return 0.0
    
    def _count_lines_of_code(self, file: SourceFile) -> int:
        """Count lines of code in a file."""
        try:
            if hasattr(file, 'source') and file.source:
                return len(file.source.split('\n'))
            return 0
        except:
            return 0
    
    def _calculate_file_complexity(self, file: SourceFile) -> float:
        """Calculate file complexity."""
        try:
            return len(file.functions) + len(file.classes) * 2
        except:
            return 0.0
    
    def _calculate_class_complexity(self, cls: Class) -> float:
        """Calculate class complexity."""
        try:
            return len(cls.methods) + len(cls.attributes) * 0.5
        except:
            return 0.0
    
    def _calculate_function_complexity(self, func: Function) -> float:
        """Calculate function complexity."""
        try:
            return len(func.function_calls) + len(func.parameters) * 0.5
        except:
            return 0.0
    
    def _is_recursive_function(self, func: Function) -> bool:
        """Check if function is recursive."""
        try:
            return any(call.name == func.name for call in func.function_calls)
        except:
            return False
    
    def _calculate_maintainability_index(self, metrics: Dict) -> float:
        """Calculate maintainability index."""
        try:
            size = metrics["size_metrics"]["total_lines"]
            complexity = metrics["quality_metrics"]["dependency_count"]
            return max(0, 171 - 5.2 * math.log(size) - 0.23 * complexity)
        except:
            return 0.0
    
    def _calculate_quality_score(self, metrics: Dict) -> float:
        """Calculate overall quality score."""
        try:
            coverage = metrics["quality_metrics"]["test_coverage_estimate"]
            dead_code_ratio = metrics["quality_metrics"]["dead_code_count"] / max(metrics["size_metrics"]["total_functions"], 1)
            return (coverage * 50) + ((1 - dead_code_ratio) * 50)
        except:
            return 0.0

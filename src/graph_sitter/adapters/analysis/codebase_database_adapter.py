"""
Unified Codebase Database Adapter

This adapter provides seamless integration between the existing 
graph_sitter codebase analysis functionality and the new unified 
analysis framework with comprehensive database support.
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import json
import logging

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.file import SourceFile
from graph_sitter.core.class_definition import Class
from graph_sitter.core.function import Function
from graph_sitter.core.symbol import Symbol
from graph_sitter.enums import EdgeType, SymbolType   

# Import unified analysis framework
from .base import BaseAnalyzer, AnalysisType, AnalysisResult, AnalysisIssue, AnalysisMetric, IssueSeverity
from .database_adapter import UnifiedAnalysisDatabase

# Import legacy codebase analysis functions if available
try:
    from graph_sitter.codebase.codebase_analysis import (
        get_codebase_summary,
        get_file_summary,
        get_class_summary,
        get_function_summary,
        get_symbol_summary,
        analyze_dependencies,
        analyze_complexity
    )
    LEGACY_ANALYSIS_AVAILABLE = True
except ImportError:
    LEGACY_ANALYSIS_AVAILABLE = False
    get_codebase_summary = None
    get_file_summary = None
    get_class_summary = None
    get_function_summary = None
    get_symbol_summary = None
    analyze_dependencies = None
    analyze_complexity = None

logger = logging.getLogger(__name__)


@dataclass
class CodebaseAnalysisConfig:
    """Configuration for codebase database analysis."""
    include_files: bool = True
    include_functions: bool = True
    include_classes: bool = True
    include_symbols: bool = True
    include_dependencies: bool = True
    include_complexity: bool = True
    include_relationships: bool = True
    max_depth: int = 10
    store_raw_data: bool = True


class CodebaseDatabaseAnalyzer(BaseAnalyzer):
    """
    Analyzer that integrates codebase structure analysis with database storage.
    
    This analyzer extracts comprehensive information about the codebase structure
    and stores it in the unified analysis database.
    """
    
    def __init__(
        self, 
        codebase: Codebase, 
        config: Optional[Dict[str, Any]] = None,
        db_path: Optional[str] = None
    ):
        """
        Initialize the codebase database analyzer.
        
        Args:
            codebase: Codebase to analyze
            config: Analysis configuration
            db_path: Path to the database file
        """
        super().__init__(codebase, config)
        self.analysis_config = CodebaseAnalysisConfig(**config) if config else CodebaseAnalysisConfig()
        self.database = UnifiedAnalysisDatabase(db_path or "codebase_analysis.db")
        self.codebase_id = None
        self.session_id = None
    
    def _get_analysis_type(self) -> AnalysisType:
        """Return the analysis type for this analyzer."""
        return AnalysisType.METRICS
    
    def analyze(self) -> AnalysisResult:
        """
        Perform comprehensive codebase analysis and store in database.
        
        Returns:
            AnalysisResult containing codebase structure analysis
        """
        try:
            start_time = datetime.now()
            
            # Store codebase in database
            self.codebase_id = self.database.store_codebase(self.codebase)
            
            # Create analysis session
            self.session_id = self.database.create_analysis_session(
                self.codebase_id,
                "codebase_structure",
                asdict(self.analysis_config)
            )
            
            # Perform analysis
            issues = []
            metrics = []
            raw_data = {}
            recommendations = []
            
            # Analyze codebase structure
            structure_data = self._analyze_codebase_structure()
            raw_data['structure'] = structure_data
            
            # Extract metrics from structure
            structure_metrics = self._extract_structure_metrics(structure_data)
            metrics.extend(structure_metrics)
            
            # Analyze files
            if self.analysis_config.include_files:
                file_data = self._analyze_files()
                raw_data['files'] = file_data
                
                file_metrics = self._extract_file_metrics(file_data)
                metrics.extend(file_metrics)
                
                file_issues = self._extract_file_issues(file_data)
                issues.extend(file_issues)
            
            # Analyze functions
            if self.analysis_config.include_functions:
                function_data = self._analyze_functions()
                raw_data['functions'] = function_data
                
                function_metrics = self._extract_function_metrics(function_data)
                metrics.extend(function_metrics)
                
                function_issues = self._extract_function_issues(function_data)
                issues.extend(function_issues)
            
            # Analyze classes
            if self.analysis_config.include_classes:
                class_data = self._analyze_classes()
                raw_data['classes'] = class_data
                
                class_metrics = self._extract_class_metrics(class_data)
                metrics.extend(class_metrics)
            
            # Analyze dependencies
            if self.analysis_config.include_dependencies:
                dependency_data = self._analyze_dependencies()
                raw_data['dependencies'] = dependency_data
                
                dependency_metrics = self._extract_dependency_metrics(dependency_data)
                metrics.extend(dependency_metrics)
                
                dependency_issues = self._extract_dependency_issues(dependency_data)
                issues.extend(dependency_issues)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(raw_data, issues, metrics)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Create result
            result = self.create_result(
                issues=issues,
                metrics=metrics,
                raw_data=raw_data,
                recommendations=recommendations,
                execution_time=execution_time,
                success=True
            )
            
            # Store result in database
            self.database.store_analysis_result(
                self.session_id,
                "codebase_database_analyzer",
                result
            )
            
            # Complete session
            self.database.complete_analysis_session(self.session_id, "completed")
            
            return result
            
        except Exception as e:
            logger.error(f"Codebase database analysis failed: {e}")
            
            # Mark session as failed if it was created
            if self.session_id:
                self.database.complete_analysis_session(self.session_id, "failed")
            
            return self.create_result(
                issues=[self.create_issue(
                    "analysis_error",
                    IssueSeverity.ERROR,
                    f"Codebase analysis failed: {str(e)}"
                )],
                metrics=[],
                raw_data={'error': str(e)},
                recommendations=["Check codebase structure and permissions"],
                execution_time=None,
                success=False,
                error_message=str(e)
            )
    
    def _analyze_codebase_structure(self) -> Dict[str, Any]:
        """Analyze overall codebase structure."""
        structure = {
            'root_path': str(self.codebase.root_path),
            'total_files': len(self.codebase.files),
            'total_functions': sum(len(f.functions) for f in self.codebase.files),
            'total_classes': sum(len(f.classes) for f in self.codebase.files),
            'total_symbols': sum(len(f.symbols) for f in self.codebase.files),
            'languages': list(set(f.language for f in self.codebase.files if f.language)),
            'file_extensions': list(set(f.path.suffix for f in self.codebase.files)),
        }
        
        # Use legacy analysis if available
        if LEGACY_ANALYSIS_AVAILABLE and get_codebase_summary:
            try:
                legacy_summary = get_codebase_summary(self.codebase)
                structure['legacy_summary'] = legacy_summary
            except Exception as e:
                logger.warning(f"Legacy codebase summary failed: {e}")
        
        return structure
    
    def _analyze_files(self) -> Dict[str, Any]:
        """Analyze individual files."""
        files_data = {}
        
        for file in self.codebase.files:
            file_info = {
                'path': str(file.path),
                'language': file.language,
                'size_bytes': file.path.stat().st_size if file.path.exists() else 0,
                'function_count': len(file.functions),
                'class_count': len(file.classes),
                'symbol_count': len(file.symbols),
                'import_count': len(file.imports) if hasattr(file, 'imports') else 0,
            }
            
            # Use legacy analysis if available
            if LEGACY_ANALYSIS_AVAILABLE and get_file_summary:
                try:
                    legacy_summary = get_file_summary(file)
                    file_info['legacy_summary'] = legacy_summary
                except Exception as e:
                    logger.warning(f"Legacy file summary failed for {file.path}: {e}")
            
            files_data[str(file.path)] = file_info
        
        return files_data
    
    def _analyze_functions(self) -> Dict[str, Any]:
        """Analyze functions across the codebase."""
        functions_data = {}
        
        for file in self.codebase.files:
            for function in file.functions:
                function_key = f"{file.path}::{function.name}"
                
                function_info = {
                    'name': function.name,
                    'file': str(file.path),
                    'line_start': function.line_start,
                    'line_end': function.line_end,
                    'parameter_count': len(function.parameters) if hasattr(function, 'parameters') else 0,
                    'is_async': getattr(function, 'is_async', False),
                    'is_method': getattr(function, 'is_method', False),
                    'docstring': getattr(function, 'docstring', None),
                }
                
                # Use legacy analysis if available
                if LEGACY_ANALYSIS_AVAILABLE and get_function_summary:
                    try:
                        legacy_summary = get_function_summary(function)
                        function_info['legacy_summary'] = legacy_summary
                    except Exception as e:
                        logger.warning(f"Legacy function summary failed for {function.name}: {e}")
                
                functions_data[function_key] = function_info
        
        return functions_data
    
    def _analyze_classes(self) -> Dict[str, Any]:
        """Analyze classes across the codebase."""
        classes_data = {}
        
        for file in self.codebase.files:
            for cls in file.classes:
                class_key = f"{file.path}::{cls.name}"
                
                class_info = {
                    'name': cls.name,
                    'file': str(file.path),
                    'line_start': cls.line_start,
                    'line_end': cls.line_end,
                    'method_count': len(cls.methods) if hasattr(cls, 'methods') else 0,
                    'property_count': len(cls.properties) if hasattr(cls, 'properties') else 0,
                    'base_classes': getattr(cls, 'base_classes', []),
                    'docstring': getattr(cls, 'docstring', None),
                }
                
                # Use legacy analysis if available
                if LEGACY_ANALYSIS_AVAILABLE and get_class_summary:
                    try:
                        legacy_summary = get_class_summary(cls)
                        class_info['legacy_summary'] = legacy_summary
                    except Exception as e:
                        logger.warning(f"Legacy class summary failed for {cls.name}: {e}")
                
                classes_data[class_key] = class_info
        
        return classes_data
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze dependencies and imports."""
        dependencies_data = {
            'internal_dependencies': {},
            'external_dependencies': {},
            'import_graph': {},
        }
        
        # Analyze imports for each file
        for file in self.codebase.files:
            file_deps = {
                'imports': [],
                'exports': [],
                'internal_refs': [],
                'external_refs': []
            }
            
            # Extract import information if available
            if hasattr(file, 'imports'):
                for imp in file.imports:
                    import_info = {
                        'module': imp.module if hasattr(imp, 'module') else str(imp),
                        'names': imp.names if hasattr(imp, 'names') else [],
                        'is_relative': getattr(imp, 'is_relative', False),
                        'line': getattr(imp, 'line', None)
                    }
                    file_deps['imports'].append(import_info)
            
            dependencies_data['import_graph'][str(file.path)] = file_deps
        
        # Use legacy dependency analysis if available
        if LEGACY_ANALYSIS_AVAILABLE and analyze_dependencies:
            try:
                legacy_deps = analyze_dependencies(self.codebase)
                dependencies_data['legacy_analysis'] = legacy_deps
            except Exception as e:
                logger.warning(f"Legacy dependency analysis failed: {e}")
        
        return dependencies_data
    
    def _extract_structure_metrics(self, structure_data: Dict[str, Any]) -> List[AnalysisMetric]:
        """Extract metrics from structure analysis."""
        metrics = []
        
        metrics.append(self.create_metric(
            "total_files", structure_data['total_files'],
            unit="count", description="Total number of files in codebase"
        ))
        
        metrics.append(self.create_metric(
            "total_functions", structure_data['total_functions'],
            unit="count", description="Total number of functions in codebase"
        ))
        
        metrics.append(self.create_metric(
            "total_classes", structure_data['total_classes'],
            unit="count", description="Total number of classes in codebase"
        ))
        
        metrics.append(self.create_metric(
            "total_symbols", structure_data['total_symbols'],
            unit="count", description="Total number of symbols in codebase"
        ))
        
        metrics.append(self.create_metric(
            "language_count", len(structure_data['languages']),
            unit="count", description="Number of programming languages used"
        ))
        
        return metrics
    
    def _extract_file_metrics(self, file_data: Dict[str, Any]) -> List[AnalysisMetric]:
        """Extract metrics from file analysis."""
        metrics = []
        
        total_size = sum(f['size_bytes'] for f in file_data.values())
        avg_size = total_size / len(file_data) if file_data else 0
        
        metrics.append(self.create_metric(
            "total_codebase_size", total_size,
            unit="bytes", description="Total size of all files"
        ))
        
        metrics.append(self.create_metric(
            "average_file_size", avg_size,
            unit="bytes", description="Average file size"
        ))
        
        # Find largest files
        if file_data:
            largest_file = max(file_data.values(), key=lambda x: x['size_bytes'])
            metrics.append(self.create_metric(
                "largest_file_size", largest_file['size_bytes'],
                unit="bytes", description=f"Size of largest file: {largest_file['path']}"
            ))
        
        return metrics
    
    def _extract_function_metrics(self, function_data: Dict[str, Any]) -> List[AnalysisMetric]:
        """Extract metrics from function analysis."""
        metrics = []
        
        if not function_data:
            return metrics
        
        # Calculate function length distribution
        function_lengths = []
        async_count = 0
        method_count = 0
        
        for func_info in function_data.values():
            length = func_info['line_end'] - func_info['line_start'] + 1
            function_lengths.append(length)
            
            if func_info['is_async']:
                async_count += 1
            if func_info['is_method']:
                method_count += 1
        
        avg_length = sum(function_lengths) / len(function_lengths)
        max_length = max(function_lengths)
        
        metrics.append(self.create_metric(
            "average_function_length", avg_length,
            unit="lines", description="Average function length in lines"
        ))
        
        metrics.append(self.create_metric(
            "max_function_length", max_length,
            unit="lines", description="Maximum function length in lines"
        ))
        
        metrics.append(self.create_metric(
            "async_function_count", async_count,
            unit="count", description="Number of async functions"
        ))
        
        metrics.append(self.create_metric(
            "method_count", method_count,
            unit="count", description="Number of class methods"
        ))
        
        return metrics
    
    def _extract_class_metrics(self, class_data: Dict[str, Any]) -> List[AnalysisMetric]:
        """Extract metrics from class analysis."""
        metrics = []
        
        if not class_data:
            return metrics
        
        # Calculate class size distribution
        class_sizes = []
        total_methods = 0
        
        for class_info in class_data.values():
            size = class_info['line_end'] - class_info['line_start'] + 1
            class_sizes.append(size)
            total_methods += class_info['method_count']
        
        avg_size = sum(class_sizes) / len(class_sizes)
        avg_methods = total_methods / len(class_data)
        
        metrics.append(self.create_metric(
            "average_class_size", avg_size,
            unit="lines", description="Average class size in lines"
        ))
        
        metrics.append(self.create_metric(
            "average_methods_per_class", avg_methods,
            unit="count", description="Average number of methods per class"
        ))
        
        return metrics
    
    def _extract_dependency_metrics(self, dependency_data: Dict[str, Any]) -> List[AnalysisMetric]:
        """Extract metrics from dependency analysis."""
        metrics = []
        
        import_graph = dependency_data.get('import_graph', {})
        
        if import_graph:
            total_imports = sum(len(file_deps['imports']) for file_deps in import_graph.values())
            avg_imports = total_imports / len(import_graph)
            
            metrics.append(self.create_metric(
                "total_imports", total_imports,
                unit="count", description="Total number of imports"
            ))
            
            metrics.append(self.create_metric(
                "average_imports_per_file", avg_imports,
                unit="count", description="Average imports per file"
            ))
        
        return metrics
    
    def _extract_file_issues(self, file_data: Dict[str, Any]) -> List[AnalysisIssue]:
        """Extract issues from file analysis."""
        issues = []
        
        for file_path, file_info in file_data.items():
            # Check for large files
            if file_info['size_bytes'] > 10000:  # 10KB threshold
                issues.append(self.create_issue(
                    "large_file",
                    IssueSeverity.WARNING,
                    f"File {file_path} is large ({file_info['size_bytes']} bytes)",
                    file=file_path,
                    suggestion="Consider breaking down large files into smaller modules"
                ))
            
            # Check for files with many functions
            if file_info['function_count'] > 20:
                issues.append(self.create_issue(
                    "many_functions",
                    IssueSeverity.INFO,
                    f"File {file_path} has many functions ({file_info['function_count']})",
                    file=file_path,
                    suggestion="Consider organizing functions into classes or separate modules"
                ))
        
        return issues
    
    def _extract_function_issues(self, function_data: Dict[str, Any]) -> List[AnalysisIssue]:
        """Extract issues from function analysis."""
        issues = []
        
        for func_key, func_info in function_data.items():
            func_length = func_info['line_end'] - func_info['line_start'] + 1
            
            # Check for long functions
            if func_length > 50:
                issues.append(self.create_issue(
                    "long_function",
                    IssueSeverity.WARNING,
                    f"Function {func_info['name']} is long ({func_length} lines)",
                    file=func_info['file'],
                    line_number=func_info['line_start'],
                    suggestion="Consider breaking down long functions into smaller ones"
                ))
            
            # Check for missing docstrings
            if not func_info.get('docstring'):
                issues.append(self.create_issue(
                    "missing_docstring",
                    IssueSeverity.INFO,
                    f"Function {func_info['name']} lacks documentation",
                    file=func_info['file'],
                    line_number=func_info['line_start'],
                    suggestion="Add docstring to document function purpose and parameters"
                ))
        
        return issues
    
    def _extract_dependency_issues(self, dependency_data: Dict[str, Any]) -> List[AnalysisIssue]:
        """Extract issues from dependency analysis."""
        issues = []
        
        import_graph = dependency_data.get('import_graph', {})
        
        for file_path, file_deps in import_graph.items():
            # Check for too many imports
            if len(file_deps['imports']) > 15:
                issues.append(self.create_issue(
                    "many_imports",
                    IssueSeverity.WARNING,
                    f"File {file_path} has many imports ({len(file_deps['imports'])})",
                    file=file_path,
                    suggestion="Consider reducing dependencies or organizing imports"
                ))
        
        return issues
    
    def _generate_recommendations(
        self, 
        raw_data: Dict[str, Any], 
        issues: List[AnalysisIssue], 
        metrics: List[AnalysisMetric]
    ) -> List[str]:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        # Analyze metrics for recommendations
        total_files = next((m.value for m in metrics if m.name == "total_files"), 0)
        total_functions = next((m.value for m in metrics if m.name == "total_functions"), 0)
        
        if total_files > 100:
            recommendations.append("Consider organizing large codebase into modules or packages")
        
        if total_functions > 500:
            recommendations.append("Large number of functions detected - consider code organization review")
        
        # Analyze issues for recommendations
        error_count = sum(1 for issue in issues if issue.severity == IssueSeverity.ERROR)
        warning_count = sum(1 for issue in issues if issue.severity == IssueSeverity.WARNING)
        
        if error_count > 0:
            recommendations.append(f"Address {error_count} critical issues found in codebase")
        
        if warning_count > 10:
            recommendations.append(f"Consider addressing {warning_count} warnings to improve code quality")
        
        # Add general recommendations
        recommendations.extend([
            "Regular code reviews can help maintain code quality",
            "Consider adding automated testing if not present",
            "Documentation updates should be part of development workflow"
        ])
        
        return recommendations
    
    def get_database_session_id(self) -> Optional[str]:
        """Get the database session ID for this analysis."""
        return self.session_id
    
    def get_database_codebase_id(self) -> Optional[str]:
        """Get the database codebase ID for this analysis."""
        return self.codebase_id


# Export for use in other modules
__all__ = [
    "CodebaseDatabaseAnalyzer",
    "CodebaseAnalysisConfig"
]


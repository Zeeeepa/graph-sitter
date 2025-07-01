"""Main metrics engine for calculating and managing code metrics."""

from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING, Dict, List, Optional, Any, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .metrics_registry import MetricsRegistry, get_global_registry
from ..models.metrics_data import (
    MetricsData,
    FunctionMetrics,
    ClassMetrics,
    FileMetrics,
    CodebaseMetrics,
)

if TYPE_CHECKING:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import Class
    from .base_calculator import BaseMetricsCalculator

logger = logging.getLogger(__name__)

class MetricsEngine:
    """Main engine for calculating comprehensive code metrics.
    
    The MetricsEngine orchestrates the calculation of various code metrics
    using registered calculators and provides a unified interface for
    metrics computation across functions, classes, files, and codebases.
    """
    
    def __init__(
        self,
        registry: Optional[MetricsRegistry] = None,
        config: Optional[Dict[str, Any]] = None,
        parallel: bool = True,
        max_workers: Optional[int] = None
    ):
        """Initialize the metrics engine.
        
        Args:
            registry: Metrics registry to use (defaults to global registry).
            config: Configuration options for the engine.
            parallel: Whether to enable parallel processing.
            max_workers: Maximum number of worker threads for parallel processing.
        """
        self.registry = registry or get_global_registry()
        self.config = config or {}
        self.parallel = parallel
        self.max_workers = max_workers
        
        # Tracking
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.calculation_stats: Dict[str, Any] = {}
        
        # Configuration
        self.enabled_calculators: Set[str] = set(self.config.get("enabled_calculators", []))
        self.disabled_calculators: Set[str] = set(self.config.get("disabled_calculators", []))
        self.language_filters: Set[str] = set(self.config.get("language_filters", []))
        
        logger.info(f"Initialized MetricsEngine with {len(self.registry.get_all_calculators())} calculators")
    
    def reset_errors(self) -> None:
        """Reset error and warning lists."""
        self.errors.clear()
        self.warnings.clear()
        self.calculation_stats.clear()
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        logger.error(message)
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
        logger.warning(message)
    
    def _get_active_calculators(self, language: Optional[str] = None) -> List[BaseMetricsCalculator]:
        """Get list of active calculators based on configuration and language.
        
        Args:
            language: Programming language to filter calculators for.
            
        Returns:
            List of active calculators.
        """
        all_calculators = self.registry.get_all_calculators()
        active_calculators = []
        
        for calculator in all_calculators:
            # Check if calculator is explicitly disabled
            if calculator.name in self.disabled_calculators:
                continue
            
            # Check if only specific calculators are enabled
            if self.enabled_calculators and calculator.name not in self.enabled_calculators:
                continue
            
            # Check language support
            if language and not calculator.supports_language(language):
                continue
            
            # Check language filters
            if self.language_filters and language and language not in self.language_filters:
                continue
            
            active_calculators.append(calculator)
        
        return active_calculators
    
    def calculate_function_metrics(
        self, 
        function: Function,
        language: Optional[str] = None
    ) -> FunctionMetrics:
        """Calculate metrics for a single function.
        
        Args:
            function: The function to analyze.
            language: Programming language of the function.
            
        Returns:
            FunctionMetrics object with calculated metrics.
        """
        start_time = time.time()
        
        # Initialize metrics object
        metrics = FunctionMetrics(
            name=function.name,
            file_path=str(function.file.path) if function.file else "",
            start_line=function.start_line if hasattr(function, 'start_line') else 0,
            end_line=function.end_line if hasattr(function, 'end_line') else 0,
        )
        
        # Get active calculators
        calculators = self._get_active_calculators(language)
        
        # Calculate metrics using each calculator
        for calculator in calculators:
            try:
                calculator.reset_errors()
                updated_metrics = calculator.calculate_function_metrics(function, metrics)
                if updated_metrics:
                    metrics = updated_metrics
                
                # Collect errors and warnings
                self.errors.extend(calculator.errors)
                self.warnings.extend(calculator.warnings)
                
            except Exception as e:
                error_msg = f"Error in calculator {calculator.name} for function {function.name}: {str(e)}"
                self.add_error(error_msg)
        
        # Record calculation time
        calculation_time = time.time() - start_time
        self.calculation_stats[f"function_{function.name}"] = calculation_time
        
        return metrics
    
    def calculate_class_metrics(
        self, 
        class_def: Class,
        language: Optional[str] = None
    ) -> ClassMetrics:
        """Calculate metrics for a single class.
        
        Args:
            class_def: The class to analyze.
            language: Programming language of the class.
            
        Returns:
            ClassMetrics object with calculated metrics.
        """
        start_time = time.time()
        
        # Initialize metrics object
        metrics = ClassMetrics(
            name=class_def.name,
            file_path=str(class_def.file.path) if class_def.file else "",
            start_line=class_def.start_line if hasattr(class_def, 'start_line') else 0,
            end_line=class_def.end_line if hasattr(class_def, 'end_line') else 0,
        )
        
        # Calculate metrics for class methods first
        if hasattr(class_def, 'methods'):
            for method in class_def.methods:
                method_metrics = self.calculate_function_metrics(method, language)
                metrics.function_metrics.append(method_metrics)
        
        # Get active calculators
        calculators = self._get_active_calculators(language)
        
        # Calculate metrics using each calculator
        for calculator in calculators:
            try:
                calculator.reset_errors()
                updated_metrics = calculator.calculate_class_metrics(class_def, metrics)
                if updated_metrics:
                    metrics = updated_metrics
                
                # Collect errors and warnings
                self.errors.extend(calculator.errors)
                self.warnings.extend(calculator.warnings)
                
            except Exception as e:
                error_msg = f"Error in calculator {calculator.name} for class {class_def.name}: {str(e)}"
                self.add_error(error_msg)
        
        # Record calculation time
        calculation_time = time.time() - start_time
        self.calculation_stats[f"class_{class_def.name}"] = calculation_time
        
        return metrics
    
    def calculate_file_metrics(
        self, 
        file: SourceFile,
        language: Optional[str] = None
    ) -> FileMetrics:
        """Calculate metrics for a single file.
        
        Args:
            file: The file to analyze.
            language: Programming language of the file.
            
        Returns:
            FileMetrics object with calculated metrics.
        """
        start_time = time.time()
        
        # Determine language if not provided
        if not language:
            language = self._detect_language(file)
        
        # Initialize metrics object
        metrics = FileMetrics(
            file_path=str(file.path),
            language=language or "unknown",
        )
        
        # Calculate metrics for functions and classes in the file
        if hasattr(file, 'functions'):
            for function in file.functions:
                func_metrics = self.calculate_function_metrics(function, language)
                metrics.function_metrics.append(func_metrics)
        
        if hasattr(file, 'classes'):
            for class_def in file.classes:
                class_metrics = self.calculate_class_metrics(class_def, language)
                metrics.class_metrics.append(class_metrics)
        
        # Get active calculators
        calculators = self._get_active_calculators(language)
        
        # Calculate metrics using each calculator
        for calculator in calculators:
            try:
                calculator.reset_errors()
                updated_metrics = calculator.calculate_file_metrics(file, metrics)
                if updated_metrics:
                    metrics = updated_metrics
                
                # Collect errors and warnings
                self.errors.extend(calculator.errors)
                self.warnings.extend(calculator.warnings)
                
            except Exception as e:
                error_msg = f"Error in calculator {calculator.name} for file {file.path}: {str(e)}"
                self.add_error(error_msg)
        
        # Record calculation time
        calculation_time = time.time() - start_time
        self.calculation_stats[f"file_{file.path}"] = calculation_time
        
        return metrics
    
    def calculate_codebase_metrics(self, codebase: Codebase) -> MetricsData:
        """Calculate comprehensive metrics for an entire codebase.
        
        Args:
            codebase: The codebase to analyze.
            
        Returns:
            MetricsData object with all calculated metrics.
        """
        start_time = time.time()
        self.reset_errors()
        
        logger.info(f"Starting metrics calculation for codebase with {len(list(codebase.files))} files")
        
        # Initialize codebase metrics
        codebase_metrics = CodebaseMetrics(
            project_name=getattr(codebase, 'name', 'Unknown'),
            total_files=len(list(codebase.files))
        )
        
        # Initialize containers
        file_metrics_dict: Dict[str, FileMetrics] = {}
        class_metrics_dict: Dict[str, List[ClassMetrics]] = {}
        function_metrics_dict: Dict[str, List[FunctionMetrics]] = {}
        
        # Process files
        files = list(codebase.files)
        
        if self.parallel and len(files) > 1:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(self.calculate_file_metrics, file): file 
                    for file in files
                }
                
                for future in as_completed(future_to_file):
                    file = future_to_file[future]
                    try:
                        file_metrics = future.result()
                        file_path = str(file.path)
                        
                        file_metrics_dict[file_path] = file_metrics
                        
                        if file_metrics.class_metrics:
                            class_metrics_dict[file_path] = file_metrics.class_metrics
                        
                        if file_metrics.function_metrics:
                            function_metrics_dict[file_path] = file_metrics.function_metrics
                        
                    except Exception as e:
                        self.add_error(f"Error processing file {file.path}: {str(e)}")
        else:
            # Sequential processing
            for file in files:
                try:
                    file_metrics = self.calculate_file_metrics(file)
                    file_path = str(file.path)
                    
                    file_metrics_dict[file_path] = file_metrics
                    
                    if file_metrics.class_metrics:
                        class_metrics_dict[file_path] = file_metrics.class_metrics
                    
                    if file_metrics.function_metrics:
                        function_metrics_dict[file_path] = file_metrics.function_metrics
                    
                except Exception as e:
                    self.add_error(f"Error processing file {file.path}: {str(e)}")
        
        # Calculate codebase-level metrics using calculators
        calculators = self._get_active_calculators()
        for calculator in calculators:
            try:
                calculator.reset_errors()
                updated_metrics = calculator.calculate_codebase_metrics(codebase, codebase_metrics)
                if updated_metrics:
                    codebase_metrics = updated_metrics
                
                # Collect errors and warnings
                self.errors.extend(calculator.errors)
                self.warnings.extend(calculator.warnings)
                
            except Exception as e:
                error_msg = f"Error in calculator {calculator.name} for codebase: {str(e)}"
                self.add_error(error_msg)
        
        # Aggregate metrics from files
        self._aggregate_codebase_metrics(codebase_metrics, file_metrics_dict)
        
        # Create final metrics data
        calculation_duration = time.time() - start_time
        
        metrics_data = MetricsData(
            codebase_metrics=codebase_metrics,
            file_metrics=file_metrics_dict,
            class_metrics=class_metrics_dict,
            function_metrics=function_metrics_dict,
            calculation_duration=calculation_duration,
            errors=self.errors.copy(),
            warnings=self.warnings.copy()
        )
        
        logger.info(f"Completed metrics calculation in {calculation_duration:.2f} seconds")
        logger.info(f"Processed {len(file_metrics_dict)} files with {len(self.errors)} errors and {len(self.warnings)} warnings")
        
        return metrics_data
    
    def _detect_language(self, file: SourceFile) -> Optional[str]:
        """Detect the programming language of a file.
        
        Args:
            file: The file to analyze.
            
        Returns:
            Detected language name or None.
        """
        if not hasattr(file, 'path'):
            return None
        
        file_path = Path(file.path)
        extension = file_path.suffix.lower()
        
        # Simple extension-based detection
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
        }
        
        return extension_map.get(extension)
    
    def _aggregate_codebase_metrics(
        self, 
        codebase_metrics: CodebaseMetrics, 
        file_metrics_dict: Dict[str, FileMetrics]
    ) -> None:
        """Aggregate metrics from files to codebase level.
        
        Args:
            codebase_metrics: Codebase metrics object to update.
            file_metrics_dict: Dictionary of file metrics.
        """
        total_complexity = 0
        total_volume = 0.0
        total_maintainability = 0.0
        maintainability_count = 0
        
        for file_metrics in file_metrics_dict.values():
            # Aggregate basic metrics
            codebase_metrics.total_lines += file_metrics.total_lines
            codebase_metrics.total_logical_lines += file_metrics.logical_lines
            codebase_metrics.total_source_lines += file_metrics.source_lines
            codebase_metrics.total_comment_lines += file_metrics.comment_lines
            codebase_metrics.total_blank_lines += file_metrics.blank_lines
            
            # Aggregate counts
            codebase_metrics.total_classes += file_metrics.class_count
            codebase_metrics.total_functions += file_metrics.function_count
            codebase_metrics.total_imports += file_metrics.import_count
            codebase_metrics.total_global_vars += file_metrics.global_var_count
            codebase_metrics.total_interfaces += file_metrics.interface_count
            
            # Aggregate complexity metrics
            total_complexity += file_metrics.cyclomatic_complexity
            total_volume += file_metrics.halstead.volume
            
            if file_metrics.maintainability_index > 0:
                total_maintainability += file_metrics.maintainability_index
                maintainability_count += 1
            
            # Language distribution
            language = file_metrics.language
            if language in codebase_metrics.language_distribution:
                codebase_metrics.language_distribution[language] += 1
            else:
                codebase_metrics.language_distribution[language] = 1
            
            # Quality metrics
            if file_metrics.has_dead_code:
                codebase_metrics.dead_code_files += 1
            
            if file_metrics.is_test_file:
                codebase_metrics.test_files += 1
        
        # Calculate averages
        if file_metrics_dict:
            codebase_metrics.total_cyclomatic_complexity = total_complexity
            codebase_metrics.average_cyclomatic_complexity = total_complexity / len(file_metrics_dict)
            codebase_metrics.total_halstead_volume = total_volume
            
            if maintainability_count > 0:
                codebase_metrics.average_maintainability_index = total_maintainability / maintainability_count
    
    def get_calculation_stats(self) -> Dict[str, Any]:
        """Get statistics about the last calculation.
        
        Returns:
            Dictionary with calculation statistics.
        """
        return {
            "calculation_stats": self.calculation_stats.copy(),
            "total_errors": len(self.errors),
            "total_warnings": len(self.warnings),
            "active_calculators": len(self._get_active_calculators()),
            "registry_info": self.registry.get_registry_info()
        }

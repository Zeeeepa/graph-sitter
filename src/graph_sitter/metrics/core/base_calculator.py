"""Base class for all metrics calculators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from graph_sitter.core.codebase import Codebase
    from graph_sitter.core.file import SourceFile
    from graph_sitter.core.function import Function
    from graph_sitter.core.class_definition import Class
    from graph_sitter.metrics.models.metrics_data import (
        FunctionMetrics,
        ClassMetrics,
        FileMetrics,
        CodebaseMetrics,
    )


class BaseMetricsCalculator(ABC):
    """Base class for all metrics calculators.
    
    This abstract class defines the interface that all metrics calculators
    must implement. Each calculator is responsible for computing specific
    metrics for functions, classes, files, or the entire codebase.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the calculator with optional configuration.
        
        Args:
            config: Optional configuration dictionary for the calculator.
        """
        self.config = config or {}
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the metrics calculator."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this calculator computes."""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """Version of the calculator implementation."""
        pass
    
    def reset_errors(self) -> None:
        """Reset error and warning lists."""
        self.errors.clear()
        self.warnings.clear()
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def calculate_function_metrics(
        self, 
        function: Function, 
        existing_metrics: Optional[FunctionMetrics] = None
    ) -> Optional[FunctionMetrics]:
        """Calculate metrics for a function.
        
        Args:
            function: The function to analyze.
            existing_metrics: Existing metrics to update (optional).
            
        Returns:
            Updated or new FunctionMetrics object, or None if calculation failed.
        """
        try:
            return self._calculate_function_metrics(function, existing_metrics)
        except Exception as e:
            self.add_error(f"Error calculating function metrics for {function.name}: {str(e)}")
            return existing_metrics
    
    def calculate_class_metrics(
        self, 
        class_def: Class, 
        existing_metrics: Optional[ClassMetrics] = None
    ) -> Optional[ClassMetrics]:
        """Calculate metrics for a class.
        
        Args:
            class_def: The class to analyze.
            existing_metrics: Existing metrics to update (optional).
            
        Returns:
            Updated or new ClassMetrics object, or None if calculation failed.
        """
        try:
            return self._calculate_class_metrics(class_def, existing_metrics)
        except Exception as e:
            self.add_error(f"Error calculating class metrics for {class_def.name}: {str(e)}")
            return existing_metrics
    
    def calculate_file_metrics(
        self, 
        file: SourceFile, 
        existing_metrics: Optional[FileMetrics] = None
    ) -> Optional[FileMetrics]:
        """Calculate metrics for a file.
        
        Args:
            file: The file to analyze.
            existing_metrics: Existing metrics to update (optional).
            
        Returns:
            Updated or new FileMetrics object, or None if calculation failed.
        """
        try:
            return self._calculate_file_metrics(file, existing_metrics)
        except Exception as e:
            self.add_error(f"Error calculating file metrics for {file.name}: {str(e)}")
            return existing_metrics
    
    def calculate_codebase_metrics(
        self, 
        codebase: Codebase, 
        existing_metrics: Optional[CodebaseMetrics] = None
    ) -> Optional[CodebaseMetrics]:
        """Calculate metrics for the entire codebase.
        
        Args:
            codebase: The codebase to analyze.
            existing_metrics: Existing metrics to update (optional).
            
        Returns:
            Updated or new CodebaseMetrics object, or None if calculation failed.
        """
        try:
            return self._calculate_codebase_metrics(codebase, existing_metrics)
        except Exception as e:
            self.add_error(f"Error calculating codebase metrics: {str(e)}")
            return existing_metrics
    
    @abstractmethod
    def _calculate_function_metrics(
        self, 
        function: Function, 
        existing_metrics: Optional[FunctionMetrics] = None
    ) -> Optional[FunctionMetrics]:
        """Internal implementation for function metrics calculation."""
        pass
    
    @abstractmethod
    def _calculate_class_metrics(
        self, 
        class_def: Class, 
        existing_metrics: Optional[ClassMetrics] = None
    ) -> Optional[ClassMetrics]:
        """Internal implementation for class metrics calculation."""
        pass
    
    @abstractmethod
    def _calculate_file_metrics(
        self, 
        file: SourceFile, 
        existing_metrics: Optional[FileMetrics] = None
    ) -> Optional[FileMetrics]:
        """Internal implementation for file metrics calculation."""
        pass
    
    @abstractmethod
    def _calculate_codebase_metrics(
        self, 
        codebase: Codebase, 
        existing_metrics: Optional[CodebaseMetrics] = None
    ) -> Optional[CodebaseMetrics]:
        """Internal implementation for codebase metrics calculation."""
        pass
    
    def supports_language(self, language: str) -> bool:
        """Check if this calculator supports the given language.
        
        Args:
            language: Programming language name (e.g., 'python', 'javascript').
            
        Returns:
            True if the language is supported, False otherwise.
        """
        # Default implementation supports all languages
        return True
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for this calculator.
        
        Returns:
            Dictionary describing the configuration options.
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True
        }


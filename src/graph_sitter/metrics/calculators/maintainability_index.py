"""Maintainability Index Calculator.

Calculates the Maintainability Index (MI) which is a composite metric that
combines Halstead Volume, Cyclomatic Complexity, and Lines of Code to
provide an overall assessment of code maintainability.

Formula: MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(SLOC)

Where:
- HV = Halstead Volume
- CC = Cyclomatic Complexity  
- SLOC = Source Lines of Code

The result is typically normalized to a 0-100 scale where:
- 85-100: Highly maintainable
- 65-84: Moderately maintainable
- 0-64: Difficult to maintain
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional, Dict, Any

from ..core.base_calculator import BaseMetricsCalculator

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


class MaintainabilityIndexCalculator(BaseMetricsCalculator):
    """Calculator for Maintainability Index metrics."""
    
    @property
    def name(self) -> str:
        return "maintainability_index"
    
    @property
    def description(self) -> str:
        return "Calculates Maintainability Index based on Halstead Volume, Cyclomatic Complexity, and SLOC"
    
    @property
    def version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration options
        self.normalize_to_100 = self.config.get("normalize_to_100", True)
        self.use_comment_ratio = self.config.get("use_comment_ratio", True)
        self.min_sloc_threshold = self.config.get("min_sloc_threshold", 1)
        self.min_halstead_threshold = self.config.get("min_halstead_threshold", 1.0)
        
        # Coefficients for the MI formula (can be customized)
        self.base_value = self.config.get("base_value", 171)
        self.halstead_coefficient = self.config.get("halstead_coefficient", 5.2)
        self.complexity_coefficient = self.config.get("complexity_coefficient", 0.23)
        self.sloc_coefficient = self.config.get("sloc_coefficient", 16.2)
        self.comment_coefficient = self.config.get("comment_coefficient", 50.0)
    
    def _calculate_maintainability_index(
        self,
        halstead_volume: float,
        cyclomatic_complexity: int,
        source_lines: int,
        comment_ratio: float = 0.0
    ) -> float:
        """Calculate the Maintainability Index.
        
        Args:
            halstead_volume: Halstead volume metric.
            cyclomatic_complexity: Cyclomatic complexity metric.
            source_lines: Source lines of code.
            comment_ratio: Ratio of comment lines to total lines.
            
        Returns:
            Maintainability Index value.
        """
        # Handle edge cases
        if source_lines < self.min_sloc_threshold:
            return 100.0  # Very small code is considered highly maintainable
        
        if halstead_volume < self.min_halstead_threshold:
            halstead_volume = self.min_halstead_threshold
        
        if cyclomatic_complexity < 1:
            cyclomatic_complexity = 1
        
        try:
            # Calculate the basic MI formula
            mi = (self.base_value 
                  - self.halstead_coefficient * math.log(halstead_volume)
                  - self.complexity_coefficient * cyclomatic_complexity
                  - self.sloc_coefficient * math.log(source_lines))
            
            # Add comment ratio bonus if enabled
            if self.use_comment_ratio and comment_ratio > 0:
                comment_bonus = self.comment_coefficient * comment_ratio
                mi += comment_bonus
            
            # Normalize to 0-100 scale if enabled
            if self.normalize_to_100:
                # The original MI can be negative or exceed 100
                # Normalize using a sigmoid-like function
                if mi < 0:
                    mi = 0.0
                elif mi > 100:
                    mi = 100.0
            
            return mi
            
        except (ValueError, OverflowError) as e:
            self.add_warning(f"Error calculating maintainability index: {str(e)}")
            return 0.0
    
    def _get_metrics_values(self, metrics) -> tuple[float, int, int, float]:
        """Extract required values from metrics object.
        
        Args:
            metrics: Metrics object (Function, Class, or File metrics).
            
        Returns:
            Tuple of (halstead_volume, cyclomatic_complexity, source_lines, comment_ratio).
        """
        halstead_volume = getattr(metrics.halstead, 'volume', 0.0) if hasattr(metrics, 'halstead') else 0.0
        cyclomatic_complexity = getattr(metrics, 'cyclomatic_complexity', 0)
        source_lines = getattr(metrics, 'source_lines', 0)
        
        # Calculate comment ratio
        total_lines = getattr(metrics, 'total_lines', 0)
        comment_lines = getattr(metrics, 'comment_lines', 0)
        comment_ratio = comment_lines / total_lines if total_lines > 0 else 0.0
        
        return halstead_volume, cyclomatic_complexity, source_lines, comment_ratio
    
    def _calculate_function_metrics(
        self, 
        function: Function, 
        existing_metrics: Optional[FunctionMetrics] = None
    ) -> Optional[FunctionMetrics]:
        """Calculate Maintainability Index for a function."""
        if existing_metrics is None:
            return None
        
        try:
            # Get required values from existing metrics
            halstead_volume, cyclomatic_complexity, source_lines, comment_ratio = self._get_metrics_values(existing_metrics)
            
            # Calculate maintainability index
            mi = self._calculate_maintainability_index(
                halstead_volume, 
                cyclomatic_complexity, 
                source_lines, 
                comment_ratio
            )
            
            existing_metrics.maintainability_index = mi
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating maintainability index for function {function.name}: {str(e)}")
            return existing_metrics
    
    def _calculate_class_metrics(
        self, 
        class_def: Class, 
        existing_metrics: Optional[ClassMetrics] = None
    ) -> Optional[ClassMetrics]:
        """Calculate Maintainability Index for a class."""
        if existing_metrics is None:
            return None
        
        try:
            # Get required values from existing metrics
            halstead_volume, cyclomatic_complexity, source_lines, comment_ratio = self._get_metrics_values(existing_metrics)
            
            # Calculate maintainability index
            mi = self._calculate_maintainability_index(
                halstead_volume, 
                cyclomatic_complexity, 
                source_lines, 
                comment_ratio
            )
            
            existing_metrics.maintainability_index = mi
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating maintainability index for class {class_def.name}: {str(e)}")
            return existing_metrics
    
    def _calculate_file_metrics(
        self, 
        file: SourceFile, 
        existing_metrics: Optional[FileMetrics] = None
    ) -> Optional[FileMetrics]:
        """Calculate Maintainability Index for a file."""
        if existing_metrics is None:
            return None
        
        try:
            # Get required values from existing metrics
            halstead_volume, cyclomatic_complexity, source_lines, comment_ratio = self._get_metrics_values(existing_metrics)
            
            # Calculate maintainability index
            mi = self._calculate_maintainability_index(
                halstead_volume, 
                cyclomatic_complexity, 
                source_lines, 
                comment_ratio
            )
            
            existing_metrics.maintainability_index = mi
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating maintainability index for file {getattr(file, 'path', 'unknown')}: {str(e)}")
            return existing_metrics
    
    def _calculate_codebase_metrics(
        self, 
        codebase: Codebase, 
        existing_metrics: Optional[CodebaseMetrics] = None
    ) -> Optional[CodebaseMetrics]:
        """Calculate Maintainability Index for the entire codebase."""
        if existing_metrics is None:
            return None
        
        try:
            # For codebase-level MI, we'll use aggregated values
            halstead_volume = getattr(existing_metrics, 'total_halstead_volume', 0.0)
            cyclomatic_complexity = getattr(existing_metrics, 'total_cyclomatic_complexity', 0)
            source_lines = getattr(existing_metrics, 'total_source_lines', 0)
            
            # Calculate comment ratio
            total_lines = getattr(existing_metrics, 'total_lines', 0)
            comment_lines = getattr(existing_metrics, 'total_comment_lines', 0)
            comment_ratio = comment_lines / total_lines if total_lines > 0 else 0.0
            
            # Calculate maintainability index
            mi = self._calculate_maintainability_index(
                halstead_volume, 
                cyclomatic_complexity, 
                source_lines, 
                comment_ratio
            )
            
            existing_metrics.average_maintainability_index = mi
            
            return existing_metrics
            
        except Exception as e:
            self.add_error(f"Error calculating maintainability index for codebase: {str(e)}")
            return existing_metrics
    
    def get_maintainability_rating(self, mi_value: float) -> str:
        """Get a human-readable rating for a Maintainability Index value.
        
        Args:
            mi_value: Maintainability Index value.
            
        Returns:
            String rating (e.g., "Highly Maintainable", "Moderate", "Difficult").
        """
        if mi_value >= 85:
            return "Highly Maintainable"
        elif mi_value >= 65:
            return "Moderately Maintainable"
        elif mi_value >= 45:
            return "Somewhat Maintainable"
        elif mi_value >= 25:
            return "Difficult to Maintain"
        else:
            return "Very Difficult to Maintain"
    
    def get_maintainability_color(self, mi_value: float) -> str:
        """Get a color code for visualizing Maintainability Index.
        
        Args:
            mi_value: Maintainability Index value.
            
        Returns:
            Color code (e.g., "green", "yellow", "red").
        """
        if mi_value >= 85:
            return "green"
        elif mi_value >= 65:
            return "yellow"
        elif mi_value >= 45:
            return "orange"
        else:
            return "red"
    
    def analyze_maintainability_trends(self, metrics_history: list) -> Dict[str, Any]:
        """Analyze maintainability trends over time.
        
        Args:
            metrics_history: List of historical metrics data.
            
        Returns:
            Dictionary with trend analysis results.
        """
        if len(metrics_history) < 2:
            return {"trend": "insufficient_data", "change": 0.0}
        
        # Calculate trend
        mi_values = [m.maintainability_index for m in metrics_history if hasattr(m, 'maintainability_index')]
        
        if len(mi_values) < 2:
            return {"trend": "insufficient_data", "change": 0.0}
        
        # Simple linear trend calculation
        first_value = mi_values[0]
        last_value = mi_values[-1]
        change = last_value - first_value
        
        if abs(change) < 1.0:
            trend = "stable"
        elif change > 0:
            trend = "improving"
        else:
            trend = "declining"
        
        # Calculate average change per period
        periods = len(mi_values) - 1
        avg_change = change / periods if periods > 0 else 0.0
        
        return {
            "trend": trend,
            "change": change,
            "average_change_per_period": avg_change,
            "first_value": first_value,
            "last_value": last_value,
            "data_points": len(mi_values)
        }
    
    def get_configuration_schema(self) -> Dict[str, Any]:
        """Get the configuration schema for this calculator."""
        return {
            "type": "object",
            "properties": {
                "normalize_to_100": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to normalize MI values to 0-100 scale"
                },
                "use_comment_ratio": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include comment ratio bonus in MI calculation"
                },
                "min_sloc_threshold": {
                    "type": "integer",
                    "default": 1,
                    "description": "Minimum SLOC threshold for MI calculation"
                },
                "min_halstead_threshold": {
                    "type": "number",
                    "default": 1.0,
                    "description": "Minimum Halstead volume threshold for MI calculation"
                },
                "base_value": {
                    "type": "number",
                    "default": 171,
                    "description": "Base value in MI formula"
                },
                "halstead_coefficient": {
                    "type": "number",
                    "default": 5.2,
                    "description": "Halstead coefficient in MI formula"
                },
                "complexity_coefficient": {
                    "type": "number",
                    "default": 0.23,
                    "description": "Complexity coefficient in MI formula"
                },
                "sloc_coefficient": {
                    "type": "number",
                    "default": 16.2,
                    "description": "SLOC coefficient in MI formula"
                },
                "comment_coefficient": {
                    "type": "number",
                    "default": 50.0,
                    "description": "Comment ratio bonus coefficient"
                }
            },
            "additionalProperties": False
        }


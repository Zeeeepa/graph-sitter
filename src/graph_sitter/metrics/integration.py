"""Integration module for advanced metrics with existing graph_sitter functionality.

from typing import TYPE_CHECKING, Dict, List, Optional, Any
import logging

from .calculators.cyclomatic_complexity import CyclomaticComplexityCalculator
from .calculators.depth_of_inheritance import DepthOfInheritanceCalculator
from .calculators.halstead_volume import HalsteadVolumeCalculator
from .calculators.lines_of_code import LinesOfCodeCalculator
from .calculators.maintainability_index import MaintainabilityIndexCalculator
from .core.metrics_engine import MetricsEngine
from .core.metrics_registry import get_global_registry, register_calculator
from .storage.metrics_database import MetricsDatabase

from __future__ import annotations
from graph_sitter.codebase.codebase_analysis import get_codebase_summary
from graph_sitter.core.codebase import Codebase
from graph_sitter.metrics.models.metrics_data import MetricsData

This module provides integration points to extend the existing codebase analysis
with advanced metrics capabilities while maintaining backward compatibility.
"""

if TYPE_CHECKING:

logger = logging.getLogger(__name__)

class AdvancedMetricsIntegration:
    """Integration class for advanced metrics functionality."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the advanced metrics integration.
        
        Args:
            config: Configuration options for metrics calculation and storage.
        """
        self.config = config or {}
        self.metrics_engine = None
        self.database = None
        
        # Initialize components
        self._initialize_calculators()
        self._initialize_engine()
        self._initialize_database()
    
    def _initialize_calculators(self) -> None:
        """Register all available metrics calculators."""
        try:
            # Register core calculators
            register_calculator(CyclomaticComplexityCalculator, "complexity")
            register_calculator(HalsteadVolumeCalculator, "complexity")
            register_calculator(MaintainabilityIndexCalculator, "maintainability")
            register_calculator(LinesOfCodeCalculator, "size")
            register_calculator(DepthOfInheritanceCalculator, "inheritance")
            
            logger.info("Registered all core metrics calculators")
            
        except Exception as e:
            logger.error(f"Failed to register calculators: {str(e)}")
            raise
    
    def _initialize_engine(self) -> None:
        """Initialize the metrics engine."""
        try:
            engine_config = self.config.get("engine", {})
            self.metrics_engine = MetricsEngine(
                registry=get_global_registry(),
                config=engine_config,
                parallel=engine_config.get("parallel", True),
                max_workers=engine_config.get("max_workers")
            )
            
            logger.info("Initialized metrics engine")
            
        except Exception as e:
            logger.error(f"Failed to initialize metrics engine: {str(e)}")
            raise
    
    def _initialize_database(self) -> None:
        """Initialize the database connection if configured."""
        try:
            db_config = self.config.get("database")
            if db_config:
                connection_string = db_config.get("connection_string")
                self.database = MetricsDatabase(connection_string, db_config)
                
                # Initialize schema if requested
                if db_config.get("initialize_schema", False):
                    self.database.initialize_schema()
                
                logger.info("Initialized metrics database")
            else:
                logger.info("No database configuration provided, metrics will not be persisted")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            # Don't raise here - database is optional
    
    def calculate_advanced_metrics(self, codebase: Codebase) -> MetricsData:
        """Calculate advanced metrics for a codebase.
        
        Args:
            codebase: The codebase to analyze.
            
        Returns:
            Complete metrics data.
        """
        if not self.metrics_engine:
            raise RuntimeError("Metrics engine not initialized")
        
        logger.info(f"Starting advanced metrics calculation for codebase")
        
        try:
            # Calculate comprehensive metrics
            metrics_data = self.metrics_engine.calculate_codebase_metrics(codebase)
            
            # Store in database if available
            if self.database:
                try:
                    codebase_id = self.database.store_metrics_data(metrics_data)
                    logger.info(f"Stored metrics data in database with ID: {codebase_id}")
                except Exception as e:
                    logger.error(f"Failed to store metrics in database: {str(e)}")
                    # Continue without database storage
            
            return metrics_data
            
        except Exception as e:
            logger.error(f"Failed to calculate advanced metrics: {str(e)}")
            raise
    
    def get_metrics_summary(self, metrics_data: MetricsData) -> Dict[str, Any]:
        """Get a summary of metrics data.
        
        Args:
            metrics_data: Complete metrics data.
            
        Returns:
            Summary dictionary with key metrics and insights.
        """
        codebase = metrics_data.codebase_metrics
        
        summary = {
            "project_name": codebase.project_name,
            "calculated_at": codebase.calculated_at.isoformat(),
            "calculation_duration": metrics_data.calculation_duration,
            
            # Size metrics
            "size": {
                "total_files": codebase.total_files,
                "total_lines": codebase.total_lines,
                "source_lines": codebase.total_source_lines,
                "comment_lines": codebase.total_comment_lines,
                "comment_ratio": codebase.comment_ratio,
            },
            
            # Complexity metrics
            "complexity": {
                "total_cyclomatic_complexity": codebase.total_cyclomatic_complexity,
                "average_cyclomatic_complexity": codebase.average_cyclomatic_complexity,
                "total_halstead_volume": codebase.total_halstead_volume,
            },
            
            # Quality metrics
            "quality": {
                "average_maintainability_index": codebase.average_maintainability_index,
                "dead_code_files": codebase.dead_code_files,
                "test_files": codebase.test_files,
                "test_file_ratio": codebase.test_file_ratio,
                "average_test_coverage": codebase.average_test_coverage,
            },
            
            # Structure metrics
            "structure": {
                "total_classes": codebase.total_classes,
                "total_functions": codebase.total_functions,
                "total_imports": codebase.total_imports,
                "language_distribution": codebase.language_distribution,
            },
            
            # Quality ratings
            "ratings": self._calculate_quality_ratings(codebase),
            
            # Issues and warnings
            "issues": {
                "errors": len(metrics_data.errors),
                "warnings": len(metrics_data.warnings),
                "error_details": metrics_data.errors[:5],  # First 5 errors
                "warning_details": metrics_data.warnings[:5],  # First 5 warnings
            }
        }
        
        return summary
    
    def _calculate_quality_ratings(self, codebase_metrics) -> Dict[str, str]:
        """Calculate quality ratings based on metrics.
        
        Args:
            codebase_metrics: Codebase metrics object.
            
        Returns:
            Dictionary with quality ratings.
        """
        ratings = {}
        
        # Maintainability rating
        mi = codebase_metrics.average_maintainability_index
        if mi >= 85:
            ratings["maintainability"] = "Excellent"
        elif mi >= 65:
            ratings["maintainability"] = "Good"
        elif mi >= 45:
            ratings["maintainability"] = "Moderate"
        else:
            ratings["maintainability"] = "Poor"
        
        # Complexity rating
        cc = codebase_metrics.average_cyclomatic_complexity
        if cc <= 5:
            ratings["complexity"] = "Low"
        elif cc <= 10:
            ratings["complexity"] = "Moderate"
        elif cc <= 20:
            ratings["complexity"] = "High"
        else:
            ratings["complexity"] = "Very High"
        
        # Documentation rating
        comment_ratio = codebase_metrics.comment_ratio
        if comment_ratio >= 0.2:
            ratings["documentation"] = "Good"
        elif comment_ratio >= 0.1:
            ratings["documentation"] = "Moderate"
        else:
            ratings["documentation"] = "Poor"
        
        # Test coverage rating
        test_coverage = codebase_metrics.average_test_coverage
        if test_coverage >= 80:
            ratings["test_coverage"] = "Excellent"
        elif test_coverage >= 60:
            ratings["test_coverage"] = "Good"
        elif test_coverage >= 40:
            ratings["test_coverage"] = "Moderate"
        else:
            ratings["test_coverage"] = "Poor"
        
        return ratings
    
    def get_file_metrics_analysis(self, metrics_data: MetricsData, file_path: str) -> Optional[Dict[str, Any]]:
        """Get detailed analysis for a specific file.
        
        Args:
            metrics_data: Complete metrics data.
            file_path: Path to the file to analyze.
            
        Returns:
            Detailed file analysis or None if file not found.
        """
        file_metrics = metrics_data.get_file_metrics(file_path)
        if not file_metrics:
            return None
        
        analysis = {
            "file_path": file_path,
            "language": file_metrics.language,
            "calculated_at": file_metrics.calculated_at.isoformat(),
            
            # Basic metrics
            "metrics": {
                "cyclomatic_complexity": file_metrics.cyclomatic_complexity,
                "maintainability_index": file_metrics.maintainability_index,
                "halstead_volume": file_metrics.halstead.volume,
                "total_lines": file_metrics.total_lines,
                "source_lines": file_metrics.source_lines,
                "comment_ratio": file_metrics.comment_ratio,
            },
            
            # Structure
            "structure": {
                "class_count": file_metrics.class_count,
                "function_count": file_metrics.function_count,
                "import_count": file_metrics.import_count,
            },
            
            # Quality indicators
            "quality": {
                "has_dead_code": file_metrics.has_dead_code,
                "is_test_file": file_metrics.is_test_file,
                "test_coverage": file_metrics.test_coverage,
            },
            
            # Classes and functions
            "classes": [
                {
                    "name": cm.name,
                    "complexity": cm.cyclomatic_complexity,
                    "maintainability": cm.maintainability_index,
                    "lines": cm.total_lines,
                    "methods": len(cm.function_metrics),
                }
                for cm in file_metrics.class_metrics
            ],
            
            "functions": [
                {
                    "name": fm.name,
                    "complexity": fm.cyclomatic_complexity,
                    "maintainability": fm.maintainability_index,
                    "lines": fm.total_lines,
                    "parameters": fm.parameter_count,
                }
                for fm in file_metrics.function_metrics
            ],
        }
        
        return analysis
    
    def get_quality_hotspots(self, metrics_data: MetricsData, limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """Identify quality hotspots in the codebase.
        
        Args:
            metrics_data: Complete metrics data.
            limit: Maximum number of hotspots to return per category.
            
        Returns:
            Dictionary with different categories of quality hotspots.
        """
        hotspots = {
            "high_complexity_functions": [],
            "low_maintainability_files": [],
            "large_classes": [],
            "deep_inheritance": [],
            "dead_code": [],
        }
        
        # Collect all functions across all files
        all_functions = []
        for file_path, file_metrics in metrics_data.file_metrics.items():
            for func_metrics in file_metrics.function_metrics:
                all_functions.append({
                    "file_path": file_path,
                    "function_name": func_metrics.name,
                    "complexity": func_metrics.cyclomatic_complexity,
                    "maintainability": func_metrics.maintainability_index,
                    "lines": func_metrics.total_lines,
                })
        
        # High complexity functions
        high_complexity = sorted(all_functions, key=lambda x: x["complexity"], reverse=True)[:limit]
        hotspots["high_complexity_functions"] = high_complexity
        
        # Low maintainability files
        low_maintainability = sorted(
            [
                {
                    "file_path": file_path,
                    "maintainability": fm.maintainability_index,
                    "complexity": fm.cyclomatic_complexity,
                    "lines": fm.total_lines,
                }
                for file_path, fm in metrics_data.file_metrics.items()
            ],
            key=lambda x: x["maintainability"]
        )[:limit]
        hotspots["low_maintainability_files"] = low_maintainability
        
        # Large classes
        all_classes = []
        for file_path, file_metrics in metrics_data.file_metrics.items():
            for class_metrics in file_metrics.class_metrics:
                all_classes.append({
                    "file_path": file_path,
                    "class_name": class_metrics.name,
                    "lines": class_metrics.total_lines,
                    "methods": class_metrics.method_count,
                    "complexity": class_metrics.cyclomatic_complexity,
                })
        
        large_classes = sorted(all_classes, key=lambda x: x["lines"], reverse=True)[:limit]
        hotspots["large_classes"] = large_classes
        
        # Deep inheritance
        deep_inheritance = sorted(all_classes, key=lambda x: x.get("depth_of_inheritance", 0), reverse=True)[:limit]
        hotspots["deep_inheritance"] = deep_inheritance
        
        # Dead code
        dead_code_files = [
            {
                "file_path": file_path,
                "has_dead_code": fm.has_dead_code,
                "lines": fm.total_lines,
            }
            for file_path, fm in metrics_data.file_metrics.items()
            if fm.has_dead_code
        ][:limit]
        hotspots["dead_code"] = dead_code_files
        
        return hotspots
    
    def close(self) -> None:
        """Clean up resources."""
        if self.database:
            self.database.close()

# Convenience functions for integration with existing codebase analysis

def enhance_codebase_analysis(codebase: Codebase, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Enhance existing codebase analysis with advanced metrics.
    
    This function can be used to extend the existing get_codebase_summary function
    with advanced metrics capabilities.
    
    Args:
        codebase: The codebase to analyze.
        config: Configuration for advanced metrics.
        
    Returns:
        Enhanced analysis results.
    """
    # Import the existing analysis function
    
    # Get basic analysis
    basic_summary = get_codebase_summary(codebase)
    
    # Calculate advanced metrics
    integration = AdvancedMetricsIntegration(config)
    try:
        metrics_data = integration.calculate_advanced_metrics(codebase)
        advanced_summary = integration.get_metrics_summary(metrics_data)
        hotspots = integration.get_quality_hotspots(metrics_data)
        
        # Combine results
        enhanced_analysis = {
            "basic_analysis": basic_summary,
            "advanced_metrics": advanced_summary,
            "quality_hotspots": hotspots,
            "calculation_stats": integration.metrics_engine.get_calculation_stats() if integration.metrics_engine else {},
        }
        
        return enhanced_analysis
        
    finally:
        integration.close()

def get_advanced_file_analysis(codebase: Codebase, file_path: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Get advanced analysis for a specific file.
    
    Args:
        codebase: The codebase containing the file.
        file_path: Path to the file to analyze.
        config: Configuration for advanced metrics.
        
    Returns:
        Advanced file analysis results.
    """
    integration = AdvancedMetricsIntegration(config)
    try:
        metrics_data = integration.calculate_advanced_metrics(codebase)
        file_analysis = integration.get_file_metrics_analysis(metrics_data, file_path)
        
        return file_analysis or {"error": f"File not found: {file_path}"}
        
    finally:
        integration.close()

# Registry access for external use
def get_metrics_registry():
    """Get the global metrics registry for external access."""
    return get_global_registry()

def register_custom_calculator(calculator_class, category: str = "custom", config: Optional[Dict[str, Any]] = None):
    """Register a custom metrics calculator.
    
    Args:
        calculator_class: Custom calculator class.
        category: Category for the calculator.
        config: Configuration for the calculator.
    """
    register_calculator(calculator_class, category, config)

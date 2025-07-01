"""Examples demonstrating the Advanced Code Metrics and Analysis Engine.

This module provides comprehensive examples of how to use the advanced metrics
system for various analysis scenarios.
"""

from __future__ import annotations

import json
from typing import Dict, Any, Optional
from pathlib import Path

from .integration import AdvancedMetricsIntegration, enhance_codebase_analysis
from .core.metrics_registry import get_global_registry
from .storage.metrics_database import MetricsDatabase


def basic_metrics_example(codebase) -> Dict[str, Any]:
    """Basic example of calculating metrics for a codebase.
    
    Args:
        codebase: The codebase to analyze.
        
    Returns:
        Dictionary with metrics results.
    """
    print("🔍 Basic Metrics Analysis Example")
    print("=" * 50)
    
    # Initialize the metrics integration
    integration = AdvancedMetricsIntegration()
    
    try:
        # Calculate comprehensive metrics
        print("Calculating advanced metrics...")
        metrics_data = integration.calculate_advanced_metrics(codebase)
        
        # Get summary
        summary = integration.get_metrics_summary(metrics_data)
        
        # Print key results
        print(f"\n📊 Results for {summary['project_name']}:")
        print(f"   Files analyzed: {summary['size']['total_files']}")
        print(f"   Total lines: {summary['size']['total_lines']:,}")
        print(f"   Average complexity: {summary['complexity']['average_cyclomatic_complexity']:.2f}")
        print(f"   Maintainability: {summary['quality']['average_maintainability_index']:.1f}")
        print(f"   Comment ratio: {summary['size']['comment_ratio']:.1%}")
        
        # Quality ratings
        print(f"\n🏆 Quality Ratings:")
        for metric, rating in summary['ratings'].items():
            print(f"   {metric.title()}: {rating}")
        
        return summary
        
    finally:
        integration.close()


def detailed_analysis_example(codebase) -> Dict[str, Any]:
    """Detailed analysis example with quality hotspots.
    
    Args:
        codebase: The codebase to analyze.
        
    Returns:
        Dictionary with detailed analysis results.
    """
    print("\n🔬 Detailed Analysis Example")
    print("=" * 50)
    
    # Configuration for detailed analysis
    config = {
        "engine": {
            "parallel": True,
            "max_workers": 4,
            "enabled_calculators": [
                "cyclomatic_complexity",
                "halstead_volume", 
                "maintainability_index",
                "lines_of_code",
                "depth_of_inheritance"
            ]
        }
    }
    
    integration = AdvancedMetricsIntegration(config)
    
    try:
        # Calculate metrics
        metrics_data = integration.calculate_advanced_metrics(codebase)
        
        # Get quality hotspots
        hotspots = integration.get_quality_hotspots(metrics_data, limit=5)
        
        print("🔥 Quality Hotspots:")
        
        # High complexity functions
        if hotspots["high_complexity_functions"]:
            print("\n   Most Complex Functions:")
            for func in hotspots["high_complexity_functions"][:3]:
                print(f"     • {func['function_name']} (complexity: {func['complexity']}) in {func['file_path']}")
        
        # Low maintainability files
        if hotspots["low_maintainability_files"]:
            print("\n   Least Maintainable Files:")
            for file_info in hotspots["low_maintainability_files"][:3]:
                print(f"     • {file_info['file_path']} (MI: {file_info['maintainability']:.1f})")
        
        # Large classes
        if hotspots["large_classes"]:
            print("\n   Largest Classes:")
            for class_info in hotspots["large_classes"][:3]:
                print(f"     • {class_info['class_name']} ({class_info['lines']} lines) in {class_info['file_path']}")
        
        return {
            "metrics_summary": integration.get_metrics_summary(metrics_data),
            "quality_hotspots": hotspots,
            "calculation_stats": integration.metrics_engine.get_calculation_stats()
        }
        
    finally:
        integration.close()


def database_integration_example(codebase) -> Dict[str, Any]:
    """Example of using database integration for metrics storage.
    
    Args:
        codebase: The codebase to analyze.
        
    Returns:
        Dictionary with database integration results.
    """
    print("\n💾 Database Integration Example")
    print("=" * 50)
    
    # Configuration with database
    config = {
        "database": {
            "db_type": "sqlite",
            "database": "metrics_example.db",
            "initialize_schema": True
        }
    }
    
    integration = AdvancedMetricsIntegration(config)
    
    try:
        # Calculate and store metrics
        print("Calculating metrics and storing in database...")
        metrics_data = integration.calculate_advanced_metrics(codebase)
        
        if integration.database:
            # Get latest metrics from database
            project_name = metrics_data.codebase_metrics.project_name
            latest_metrics = integration.database.get_latest_metrics(project_name)
            
            print(f"✅ Metrics stored successfully!")
            print(f"   Database record ID: {latest_metrics.get('id') if latest_metrics else 'N/A'}")
            print(f"   Stored at: {latest_metrics.get('calculated_at') if latest_metrics else 'N/A'}")
            
            # Get metrics history (if any)
            history = integration.database.get_metrics_history(project_name, days=30)
            print(f"   Historical records: {len(history)}")
            
            return {
                "latest_metrics": latest_metrics,
                "history_count": len(history),
                "database_type": config["database"]["db_type"]
            }
        else:
            print("❌ Database not available")
            return {"error": "Database not initialized"}
        
    finally:
        integration.close()


def custom_calculator_example(codebase) -> Dict[str, Any]:
    """Example of creating and using a custom metrics calculator.
    
    Args:
        codebase: The codebase to analyze.
        
    Returns:
        Dictionary with custom calculator results.
    """
    print("\n🛠️ Custom Calculator Example")
    print("=" * 50)
    
    from .core.base_calculator import BaseMetricsCalculator
    from .core.metrics_registry import register_calculator
    
    # Define a custom calculator
    class CustomComplexityCalculator(BaseMetricsCalculator):
        """Example custom calculator that measures TODO comments."""
        
        @property
        def name(self) -> str:
            return "todo_complexity"
        
        @property
        def description(self) -> str:
            return "Counts TODO comments as a complexity indicator"
        
        @property
        def version(self) -> str:
            return "1.0.0"
        
        def _calculate_file_metrics(self, file, existing_metrics=None):
            if existing_metrics is None:
                return None
            
            try:
                # Get file content
                content = self._get_file_content(file)
                if content:
                    # Count TODO comments
                    todo_count = content.upper().count("TODO")
                    # Store in a custom field (would need to extend metrics model)
                    print(f"     Found {todo_count} TODO comments in {getattr(file, 'path', 'unknown')}")
                
                return existing_metrics
            except Exception as e:
                self.add_error(f"Error in custom calculator: {str(e)}")
                return existing_metrics
        
        def _get_file_content(self, file):
            """Get file content."""
            try:
                if hasattr(file, 'content'):
                    return file.content
                elif hasattr(file, 'path'):
                    with open(file.path, 'r', encoding='utf-8') as f:
                        return f.read()
                return ""
            except:
                return ""
        
        # Required abstract methods (minimal implementation)
        def _calculate_function_metrics(self, function, existing_metrics=None):
            return existing_metrics
        
        def _calculate_class_metrics(self, class_def, existing_metrics=None):
            return existing_metrics
        
        def _calculate_codebase_metrics(self, codebase, existing_metrics=None):
            return existing_metrics
    
    # Register the custom calculator
    register_calculator(CustomComplexityCalculator, "custom")
    
    # Use it in analysis
    config = {
        "engine": {
            "enabled_calculators": [
                "cyclomatic_complexity",
                "lines_of_code",
                "todo_complexity"  # Our custom calculator
            ]
        }
    }
    
    integration = AdvancedMetricsIntegration(config)
    
    try:
        print("Running analysis with custom calculator...")
        metrics_data = integration.calculate_advanced_metrics(codebase)
        
        # Get registry info to show our custom calculator
        registry_info = get_global_registry().get_registry_info()
        custom_calculators = registry_info["categories"].get("custom", {})
        
        print(f"✅ Custom calculator registered and executed!")
        print(f"   Custom calculators: {custom_calculators.get('count', 0)}")
        
        return {
            "custom_calculators": custom_calculators,
            "registry_info": registry_info
        }
        
    finally:
        integration.close()


def performance_analysis_example(codebase) -> Dict[str, Any]:
    """Example of performance analysis and optimization.
    
    Args:
        codebase: The codebase to analyze.
        
    Returns:
        Dictionary with performance analysis results.
    """
    print("\n⚡ Performance Analysis Example")
    print("=" * 50)
    
    # Test different configurations
    configs = [
        {"name": "Sequential", "config": {"engine": {"parallel": False}}},
        {"name": "Parallel", "config": {"engine": {"parallel": True, "max_workers": 2}}},
        {"name": "Parallel (4 workers)", "config": {"engine": {"parallel": True, "max_workers": 4}}},
    ]
    
    results = []
    
    for test_config in configs:
        print(f"\n   Testing {test_config['name']} processing...")
        
        integration = AdvancedMetricsIntegration(test_config["config"])
        
        try:
            metrics_data = integration.calculate_advanced_metrics(codebase)
            stats = integration.metrics_engine.get_calculation_stats()
            
            result = {
                "name": test_config["name"],
                "duration": metrics_data.calculation_duration,
                "files_processed": metrics_data.codebase_metrics.total_files,
                "errors": len(metrics_data.errors),
                "warnings": len(metrics_data.warnings),
                "active_calculators": stats.get("active_calculators", 0)
            }
            
            results.append(result)
            
            print(f"     Duration: {result['duration']:.2f}s")
            print(f"     Files: {result['files_processed']}")
            print(f"     Errors: {result['errors']}")
            
        finally:
            integration.close()
    
    # Find best performance
    best_result = min(results, key=lambda x: x["duration"])
    print(f"\n🏆 Best performance: {best_result['name']} ({best_result['duration']:.2f}s)")
    
    return {
        "performance_results": results,
        "best_configuration": best_result
    }


def export_metrics_example(codebase, output_file: str = "metrics_export.json") -> Dict[str, Any]:
    """Example of exporting metrics data to various formats.
    
    Args:
        codebase: The codebase to analyze.
        output_file: Output file path.
        
    Returns:
        Dictionary with export results.
    """
    print("\n📤 Metrics Export Example")
    print("=" * 50)
    
    integration = AdvancedMetricsIntegration()
    
    try:
        # Calculate metrics
        metrics_data = integration.calculate_advanced_metrics(codebase)
        
        # Export to JSON
        export_data = metrics_data.to_dict()
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✅ Metrics exported to {output_file}")
        print(f"   File size: {Path(output_file).stat().st_size:,} bytes")
        
        # Create summary report
        summary = integration.get_metrics_summary(metrics_data)
        summary_file = output_file.replace('.json', '_summary.json')
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        print(f"   Summary exported to {summary_file}")
        
        return {
            "export_file": output_file,
            "summary_file": summary_file,
            "data_size": len(export_data),
            "summary_size": len(summary)
        }
        
    finally:
        integration.close()


def comprehensive_example(codebase) -> Dict[str, Any]:
    """Comprehensive example combining all features.
    
    Args:
        codebase: The codebase to analyze.
        
    Returns:
        Dictionary with comprehensive analysis results.
    """
    print("\n🎯 Comprehensive Analysis Example")
    print("=" * 50)
    
    # Run all examples
    results = {}
    
    try:
        results["basic"] = basic_metrics_example(codebase)
        results["detailed"] = detailed_analysis_example(codebase)
        results["database"] = database_integration_example(codebase)
        results["custom"] = custom_calculator_example(codebase)
        results["performance"] = performance_analysis_example(codebase)
        results["export"] = export_metrics_example(codebase)
        
        print("\n🎉 All examples completed successfully!")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error in comprehensive example: {str(e)}")
        return {"error": str(e), "partial_results": results}


# Utility function for easy testing
def run_example(codebase, example_name: str = "basic") -> Dict[str, Any]:
    """Run a specific example.
    
    Args:
        codebase: The codebase to analyze.
        example_name: Name of the example to run.
        
    Returns:
        Example results.
    """
    examples = {
        "basic": basic_metrics_example,
        "detailed": detailed_analysis_example,
        "database": database_integration_example,
        "custom": custom_calculator_example,
        "performance": performance_analysis_example,
        "export": export_metrics_example,
        "comprehensive": comprehensive_example,
    }
    
    if example_name not in examples:
        available = ", ".join(examples.keys())
        raise ValueError(f"Unknown example '{example_name}'. Available: {available}")
    
    return examples[example_name](codebase)


if __name__ == "__main__":
    print("Advanced Code Metrics and Analysis Engine - Examples")
    print("=" * 60)
    print("This module contains examples for using the metrics system.")
    print("Import this module and call run_example(codebase, 'example_name')")
    print(f"Available examples: {', '.join(['basic', 'detailed', 'database', 'custom', 'performance', 'export', 'comprehensive'])}")


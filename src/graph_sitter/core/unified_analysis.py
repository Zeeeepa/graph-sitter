"""
Unified Analysis System

This module consolidates analysis functionality from:
- analysis/deep_analysis.py (comprehensive metrics and insights)
- codebase/codebase_analysis.py (basic summaries and analysis)

Provides a unified interface with configurable analysis depth.
"""

from typing import Dict, List, Any, Optional, Set, Tuple, Union
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from enum import Enum

from graph_sitter.shared.logging.get_logger import get_logger

# Import existing analysis modules
from ..analysis.deep_analysis import DeepCodebaseAnalyzer
from ..codebase.codebase_analysis import (
    get_codebase_summary, get_file_summary, get_class_summary
)

logger = get_logger(__name__)


class AnalysisDepth(Enum):
    """Analysis depth levels."""
    BASIC = "basic"           # Quick summaries and counts
    STANDARD = "standard"     # Standard analysis with metrics
    COMPREHENSIVE = "comprehensive"  # Deep analysis with all features
    CUSTOM = "custom"         # Custom analysis configuration


class AnalysisStrategy:
    """Base class for analysis strategies."""
    
    def __init__(self, codebase):
        self.codebase = codebase
    
    def analyze(self) -> Dict[str, Any]:
        """Perform analysis and return results."""
        raise NotImplementedError


class BasicAnalysisStrategy(AnalysisStrategy):
    """Basic analysis strategy - quick summaries and counts."""
    
    def analyze(self) -> Dict[str, Any]:
        """Perform basic analysis."""
        try:
            # Use existing codebase analysis functions
            summary = get_codebase_summary(self.codebase)
            
            # Basic counts
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            symbols = list(self.codebase.symbols)
            
            return {
                "analysis_type": "basic",
                "timestamp": datetime.now().isoformat(),
                "summary": summary,
                "counts": {
                    "files": len(files),
                    "functions": len(functions),
                    "classes": len(classes),
                    "symbols": len(symbols),
                    "imports": len(list(self.codebase.imports)),
                    "external_modules": len(list(self.codebase.external_modules))
                },
                "file_breakdown": [
                    {
                        "name": file.name,
                        "path": getattr(file, 'filepath', 'Unknown'),
                        "classes": len(file.classes),
                        "functions": len(file.functions),
                        "imports": len(file.imports)
                    }
                    for file in files[:10]  # Limit to first 10 files for basic analysis
                ]
            }
            
        except Exception as e:
            logger.error(f"Error in basic analysis: {e}")
            return {
                "analysis_type": "basic",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "counts": {"files": 0, "functions": 0, "classes": 0, "symbols": 0}
            }


class StandardAnalysisStrategy(AnalysisStrategy):
    """Standard analysis strategy - includes metrics and relationships."""
    
    def analyze(self) -> Dict[str, Any]:
        """Perform standard analysis."""
        try:
            # Start with basic analysis
            basic_strategy = BasicAnalysisStrategy(self.codebase)
            result = basic_strategy.analyze()
            result["analysis_type"] = "standard"
            
            # Add standard metrics
            files = list(self.codebase.files)
            functions = list(self.codebase.functions)
            classes = list(self.codebase.classes)
            
            # File type analysis
            file_types = defaultdict(int)
            for file in files:
                if hasattr(file, 'name'):
                    ext = Path(file.name).suffix.lower()
                    file_types[ext] = file_types.get(ext, 0) + 1
            
            # Function complexity analysis (basic)
            function_sizes = []
            for func in functions:
                if hasattr(func, 'source'):
                    lines = len(func.source.split('\n'))
                    function_sizes.append(lines)
            
            # Class analysis
            class_sizes = []
            for cls in classes:
                method_count = len(getattr(cls, 'methods', []))
                class_sizes.append(method_count)
            
            # Add metrics to result
            result["metrics"] = {
                "file_types": dict(file_types),
                "function_stats": {
                    "total": len(function_sizes),
                    "avg_lines": sum(function_sizes) / len(function_sizes) if function_sizes else 0,
                    "max_lines": max(function_sizes) if function_sizes else 0,
                    "min_lines": min(function_sizes) if function_sizes else 0
                },
                "class_stats": {
                    "total": len(class_sizes),
                    "avg_methods": sum(class_sizes) / len(class_sizes) if class_sizes else 0,
                    "max_methods": max(class_sizes) if class_sizes else 0,
                    "min_methods": min(class_sizes) if class_sizes else 0
                }
            }
            
            # Dependency analysis (basic)
            import_counts = defaultdict(int)
            for file in files:
                for imp in file.imports:
                    if hasattr(imp, 'module_name'):
                        import_counts[imp.module_name] += 1
            
            result["dependencies"] = {
                "most_imported": dict(Counter(import_counts).most_common(10)),
                "total_unique_imports": len(import_counts)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in standard analysis: {e}")
            # Fallback to basic analysis
            basic_strategy = BasicAnalysisStrategy(self.codebase)
            result = basic_strategy.analyze()
            result["error"] = f"Standard analysis failed, using basic: {e}"
            return result


class ComprehensiveAnalysisStrategy(AnalysisStrategy):
    """Comprehensive analysis strategy - uses deep analysis capabilities."""
    
    def analyze(self) -> Dict[str, Any]:
        """Perform comprehensive analysis."""
        try:
            # Start with standard analysis
            standard_strategy = StandardAnalysisStrategy(self.codebase)
            result = standard_strategy.analyze()
            result["analysis_type"] = "comprehensive"
            
            # Use deep analysis capabilities
            deep_analyzer = DeepCodebaseAnalyzer(self.codebase)
            
            # Get comprehensive metrics
            try:
                comprehensive_metrics = deep_analyzer.analyze_comprehensive_metrics()
                result["comprehensive_metrics"] = comprehensive_metrics
            except Exception as e:
                logger.warning(f"Failed to get comprehensive metrics: {e}")
                result["comprehensive_metrics"] = {"error": str(e)}
            
            # Get dependency analysis
            try:
                dependency_analysis = deep_analyzer.analyze_dependencies()
                result["dependency_analysis"] = dependency_analysis
            except Exception as e:
                logger.warning(f"Failed to get dependency analysis: {e}")
                result["dependency_analysis"] = {"error": str(e)}
            
            # Get complexity analysis
            try:
                complexity_analysis = deep_analyzer.analyze_complexity()
                result["complexity_analysis"] = complexity_analysis
            except Exception as e:
                logger.warning(f"Failed to get complexity analysis: {e}")
                result["complexity_analysis"] = {"error": str(e)}
            
            # Get code quality metrics
            try:
                quality_metrics = deep_analyzer.analyze_code_quality()
                result["quality_metrics"] = quality_metrics
            except Exception as e:
                logger.warning(f"Failed to get quality metrics: {e}")
                result["quality_metrics"] = {"error": str(e)}
            
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            # Fallback to standard analysis
            standard_strategy = StandardAnalysisStrategy(self.codebase)
            result = standard_strategy.analyze()
            result["error"] = f"Comprehensive analysis failed, using standard: {e}"
            return result


class CustomAnalysisStrategy(AnalysisStrategy):
    """Custom analysis strategy with configurable options."""
    
    def __init__(self, codebase, config: Dict[str, Any]):
        super().__init__(codebase)
        self.config = config
    
    def analyze(self) -> Dict[str, Any]:
        """Perform custom analysis based on configuration."""
        try:
            result = {
                "analysis_type": "custom",
                "timestamp": datetime.now().isoformat(),
                "config": self.config
            }
            
            # Basic analysis if requested
            if self.config.get("include_basic", True):
                basic_strategy = BasicAnalysisStrategy(self.codebase)
                basic_result = basic_strategy.analyze()
                result.update(basic_result)
            
            # Metrics if requested
            if self.config.get("include_metrics", False):
                standard_strategy = StandardAnalysisStrategy(self.codebase)
                standard_result = standard_strategy.analyze()
                result["metrics"] = standard_result.get("metrics", {})
                result["dependencies"] = standard_result.get("dependencies", {})
            
            # Deep analysis components if requested
            if self.config.get("include_deep", False):
                deep_analyzer = DeepCodebaseAnalyzer(self.codebase)
                
                if self.config.get("include_comprehensive_metrics", False):
                    try:
                        result["comprehensive_metrics"] = deep_analyzer.analyze_comprehensive_metrics()
                    except Exception as e:
                        result["comprehensive_metrics"] = {"error": str(e)}
                
                if self.config.get("include_dependency_analysis", False):
                    try:
                        result["dependency_analysis"] = deep_analyzer.analyze_dependencies()
                    except Exception as e:
                        result["dependency_analysis"] = {"error": str(e)}
                
                if self.config.get("include_complexity", False):
                    try:
                        result["complexity_analysis"] = deep_analyzer.analyze_complexity()
                    except Exception as e:
                        result["complexity_analysis"] = {"error": str(e)}
            
            return result
            
        except Exception as e:
            logger.error(f"Error in custom analysis: {e}")
            return {
                "analysis_type": "custom",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "config": self.config
            }


class UnifiedAnalyzer:
    """
    Unified analyzer that provides a single interface for all analysis operations.
    
    This class consolidates functionality from:
    - analysis/deep_analysis.py
    - codebase/codebase_analysis.py
    
    And provides configurable analysis depth and custom analysis options.
    """
    
    def __init__(self, codebase):
        self.codebase = codebase
        self._strategies = {
            AnalysisDepth.BASIC: BasicAnalysisStrategy,
            AnalysisDepth.STANDARD: StandardAnalysisStrategy,
            AnalysisDepth.COMPREHENSIVE: ComprehensiveAnalysisStrategy,
            AnalysisDepth.CUSTOM: CustomAnalysisStrategy
        }
    
    def analyze(self, depth: AnalysisDepth = AnalysisDepth.STANDARD, 
                config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Perform analysis with specified depth.
        
        Args:
            depth: Analysis depth level
            config: Custom configuration for CUSTOM depth
            
        Returns:
            Dict containing analysis results
        """
        try:
            if depth == AnalysisDepth.CUSTOM:
                if config is None:
                    config = {"include_basic": True, "include_metrics": True}
                strategy = self._strategies[depth](self.codebase, config)
            else:
                strategy = self._strategies[depth](self.codebase)
            
            return strategy.analyze()
            
        except Exception as e:
            logger.error(f"Error in unified analysis: {e}")
            return {
                "analysis_type": depth.value,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def get_file_summary(self, file_path: str) -> str:
        """Get summary for a specific file."""
        try:
            # Find the file in the codebase
            for file in self.codebase.files:
                if hasattr(file, 'filepath') and file.filepath == file_path:
                    return get_file_summary(file)
                elif hasattr(file, 'name') and file.name == Path(file_path).name:
                    return get_file_summary(file)
            
            return f"File not found: {file_path}"
            
        except Exception as e:
            logger.error(f"Error getting file summary: {e}")
            return f"Error getting file summary: {e}"
    
    def get_class_summary(self, class_name: str) -> str:
        """Get summary for a specific class."""
        try:
            # Find the class in the codebase
            for cls in self.codebase.classes:
                if hasattr(cls, 'name') and cls.name == class_name:
                    return get_class_summary(cls)
            
            return f"Class not found: {class_name}"
            
        except Exception as e:
            logger.error(f"Error getting class summary: {e}")
            return f"Error getting class summary: {e}"
    
    def get_quick_stats(self) -> Dict[str, int]:
        """Get quick statistics about the codebase."""
        try:
            return {
                "files": len(list(self.codebase.files)),
                "functions": len(list(self.codebase.functions)),
                "classes": len(list(self.codebase.classes)),
                "symbols": len(list(self.codebase.symbols)),
                "imports": len(list(self.codebase.imports)),
                "external_modules": len(list(self.codebase.external_modules))
            }
        except Exception as e:
            logger.error(f"Error getting quick stats: {e}")
            return {"error": str(e)}
    
    def compare_analyses(self, depth1: AnalysisDepth, depth2: AnalysisDepth) -> Dict[str, Any]:
        """Compare results from different analysis depths."""
        try:
            result1 = self.analyze(depth1)
            result2 = self.analyze(depth2)
            
            return {
                "comparison_timestamp": datetime.now().isoformat(),
                "depth1": depth1.value,
                "depth2": depth2.value,
                "result1": result1,
                "result2": result2,
                "differences": self._find_differences(result1, result2)
            }
            
        except Exception as e:
            logger.error(f"Error comparing analyses: {e}")
            return {"error": str(e)}
    
    def _find_differences(self, result1: Dict[str, Any], result2: Dict[str, Any]) -> Dict[str, Any]:
        """Find differences between two analysis results."""
        differences = {}
        
        # Compare counts if both have them
        if "counts" in result1 and "counts" in result2:
            count_diffs = {}
            for key in result1["counts"]:
                if key in result2["counts"]:
                    if result1["counts"][key] != result2["counts"][key]:
                        count_diffs[key] = {
                            "result1": result1["counts"][key],
                            "result2": result2["counts"][key]
                        }
            if count_diffs:
                differences["counts"] = count_diffs
        
        # Compare metrics if both have them
        if "metrics" in result1 and "metrics" in result2:
            differences["metrics_available"] = {
                "result1": list(result1["metrics"].keys()),
                "result2": list(result2["metrics"].keys())
            }
        
        return differences

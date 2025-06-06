#!/usr/bin/env python3
"""
Unified Analyzer Class

This module provides a comprehensive analyzer that combines functionality from all
three original analysis files, providing a single interface for all analysis operations.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import asdict

# Import core components with fallback for standalone usage
try:
    from ..core.models import (
        ComprehensiveAnalysisResult, AnalysisOptions, AnalysisContext,
        create_default_analysis_options
    )
    from ..core.analysis_engine import (
        analyze_codebase_directory, generate_summary_statistics
    )
    from ..core.graph_enhancements import (
        detect_import_loops, analyze_graph_structure, detect_dead_code,
        generate_training_data, get_codebase_summary_enhanced,
        analyze_function_enhanced, analyze_class_enhanced,
        generate_import_loop_recommendations, generate_dead_code_recommendations,
        generate_graph_insights, generate_graph_recommendations
    )
except ImportError:
    # Fallback to absolute imports for standalone usage
    try:
        from core.models import (
            ComprehensiveAnalysisResult, AnalysisOptions, AnalysisContext,
            create_default_analysis_options
        )
        from core.analysis_engine import (
            analyze_codebase_directory, generate_summary_statistics
        )
        from core.graph_enhancements import (
            detect_import_loops, analyze_graph_structure, detect_dead_code,
            generate_training_data, get_codebase_summary_enhanced,
            analyze_function_enhanced, analyze_class_enhanced,
            generate_import_loop_recommendations, generate_dead_code_recommendations,
            generate_graph_insights, generate_graph_recommendations
        )
    except ImportError as e:
        # Create minimal fallbacks for testing
        print(f"Warning: Could not import core components: {e}")
        
        class ComprehensiveAnalysisResult:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        class AnalysisOptions:
            def __init__(self, **kwargs):
                for k, v in kwargs.items():
                    setattr(self, k, v)
        
        def create_default_analysis_options():
            return AnalysisOptions(
                extensions=['.py'], max_complexity=10, min_maintainability=20,
                include_dead_code=False, include_import_loops=False,
                include_training_data=False, include_enhanced_metrics=False,
                include_graph_analysis=False, use_graph_sitter=True
            )
        
        def analyze_codebase_directory(path, options):
            return ComprehensiveAnalysisResult(
                total_files=0, total_functions=0, total_classes=0,
                total_lines=0, issues=[], analysis_time=0.0
            )
        
        def generate_summary_statistics(result):
            return {"overview": {"total_files": 0}}
        
        # Create dummy functions for graph enhancements
        def detect_import_loops(codebase): return []
        def analyze_graph_structure(codebase): return {}
        def detect_dead_code(codebase): return []
        def generate_training_data(codebase): return []
        def get_codebase_summary_enhanced(codebase): return {}
        def analyze_function_enhanced(function): return {}
        def analyze_class_enhanced(cls): return {}
        def generate_import_loop_recommendations(loops): return []
        def generate_dead_code_recommendations(items): return []
        def generate_graph_insights(analysis): return []
        def generate_graph_recommendations(analysis): return []

logger = logging.getLogger(__name__)

try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False


class UnifiedCodebaseAnalyzer:
    """
    Unified codebase analyzer that combines all analysis capabilities.
    
    This class consolidates functionality from:
    - analyze_codebase_enhanced.py (CLI tool and comprehensive analysis)
    - enhanced_analyzer.py (class-based analyzer with advanced features)
    - graph_sitter_enhancements.py (core enhancement functions)
    """
    
    def __init__(self, use_graph_sitter: bool = True, use_advanced_config: bool = False):
        """
        Initialize the unified analyzer.
        
        Args:
            use_graph_sitter: Whether to use graph-sitter enhanced analysis
            use_advanced_config: Whether to use advanced CodebaseConfig options
        """
        self.use_graph_sitter = use_graph_sitter and GRAPH_SITTER_AVAILABLE
        self.use_advanced_config = use_advanced_config
        self.config = self._create_config() if use_advanced_config else None
        
        if not self.use_graph_sitter:
            logger.info("Using AST-based analysis (graph-sitter not available or disabled)")
        else:
            logger.info("Using graph-sitter enhanced analysis")
    
    def _create_config(self) -> Optional['CodebaseConfig']:
        """Create advanced CodebaseConfig with enhanced features."""
        if not GRAPH_SITTER_AVAILABLE:
            return None
        
        try:
            return CodebaseConfig(
                # Performance optimizations
                method_usages=True,          # Enable method usage resolution
                generics=True,               # Enable generic type resolution
                sync_enabled=True,           # Enable graph sync during commits
                
                # Advanced analysis
                full_range_index=True,       # Full range-to-node mapping
                py_resolve_syspath=True,     # Resolve sys.path imports
                
                # Debugging (can be enabled for troubleshooting)
                debug=False,                 # Verbose logging
                verify_graph=False,          # Graph state validation
                track_graph=False,           # Keep original graph copy
                
                # Experimental features
                exp_lazy_graph=False,        # Lazy graph construction
            )
        except Exception as e:
            logger.warning(f"Could not create advanced config: {e}")
            return None
    
    # ========================================================================
    # MAIN ANALYSIS METHODS
    # ========================================================================
    
    def analyze_codebase(self, path: str, extensions: Optional[List[str]] = None) -> ComprehensiveAnalysisResult:
        """
        Perform comprehensive codebase analysis.
        
        Args:
            path: Path to analyze
            extensions: File extensions to include
            
        Returns:
            ComprehensiveAnalysisResult containing all analysis data
        """
        options = create_default_analysis_options()
        options.use_graph_sitter = self.use_graph_sitter
        options.extensions = extensions or ['.py']
        
        if self.use_graph_sitter and GRAPH_SITTER_AVAILABLE:
            return self._analyze_with_graph_sitter(path, options)
        else:
            return analyze_codebase_directory(path, options)
    
    def _analyze_with_graph_sitter(self, path: str, options: AnalysisOptions) -> ComprehensiveAnalysisResult:
        """Perform analysis using graph-sitter enhanced features."""
        try:
            # Initialize codebase with optional advanced config
            if self.config:
                codebase = Codebase(path, config=self.config)
                logger.info("Using advanced CodebaseConfig")
            else:
                codebase = Codebase(path)
                logger.info("Using default configuration")
            
            # Start with basic analysis
            result = analyze_codebase_directory(path, options)
            
            # Enhance with graph-sitter features
            if hasattr(options, 'include_dead_code') and options.include_dead_code:
                result.dead_code_items.extend(detect_dead_code(codebase))
            
            return result
            
        except Exception as e:
            logger.error(f"Error in graph-sitter analysis: {e}")
            # Fallback to AST-based analysis
            return analyze_codebase_directory(path, options)
    
    # ========================================================================
    # SPECIALIZED ANALYSIS METHODS
    # ========================================================================
    
    def analyze_enhanced_metrics(self, path: str) -> Dict[str, Any]:
        """Generate enhanced function and class metrics."""
        if not GRAPH_SITTER_AVAILABLE:
            return {"error": "Graph-sitter not available"}
        
        try:
            codebase = Codebase(path, config=self.config)
            
            # Analyze functions with enhanced metrics
            enhanced_functions = []
            for function in codebase.functions:
                enhanced_metric = analyze_function_enhanced(function)
                enhanced_functions.append(asdict(enhanced_metric))
            
            # Analyze classes with enhanced metrics
            enhanced_classes = []
            for cls in codebase.classes:
                enhanced_metric = analyze_class_enhanced(cls)
                enhanced_classes.append(asdict(enhanced_metric))
            
            return {
                "enhanced_functions": enhanced_functions,
                "enhanced_classes": enhanced_classes,
                "summary": {
                    "total_functions_analyzed": len(enhanced_functions),
                    "total_classes_analyzed": len(enhanced_classes),
                    "functions_with_dependencies": len([f for f in enhanced_functions if f.get("dependencies", [])]),
                    "functions_with_usages": len([f for f in enhanced_functions if f.get("usages", [])]),
                    "classes_with_inheritance": len([c for c in enhanced_classes if c.get("parent_classes", [])]),
                    "async_functions": len([f for f in enhanced_functions if f.get("is_async", False)]),
                    "generator_functions": len([f for f in enhanced_functions if f.get("is_generator", False)]),
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing enhanced metrics: {e}")
            return {"error": str(e)}
    
    def analyze_training_data(self, path: str) -> Dict[str, Any]:
        """Generate training data for LLMs."""
        if not GRAPH_SITTER_AVAILABLE:
            return {"error": "Graph-sitter not available"}
        
        try:
            codebase = Codebase(path, config=self.config)
            training_data = generate_training_data(codebase)
            
            # Calculate metadata
            total_functions = len(list(codebase.functions))
            processed_functions = len(training_data)
            
            avg_dependencies = sum(len(item.dependencies) for item in training_data) / len(training_data) if training_data else 0
            avg_usages = sum(len(item.usages) for item in training_data) / len(training_data) if training_data else 0
            
            return {
                "training_data": [asdict(item) for item in training_data],
                "metadata": {
                    "total_functions": total_functions,
                    "processed_functions": processed_functions,
                    "coverage_percentage": (processed_functions / total_functions * 100) if total_functions > 0 else 0,
                    "avg_dependencies_per_function": avg_dependencies,
                    "avg_usages_per_function": avg_usages,
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating training data: {e}")
            return {"error": str(e)}
    
    def analyze_import_loops(self, path: str) -> Dict[str, Any]:
        """Detect and analyze circular import dependencies."""
        if not GRAPH_SITTER_AVAILABLE:
            return {"error": "Graph-sitter not available"}
        
        try:
            codebase = Codebase(path, config=self.config)
            import_loops = detect_import_loops(codebase)
            
            # Categorize by severity
            critical_loops = [loop for loop in import_loops if loop.severity == "critical"]
            warning_loops = [loop for loop in import_loops if loop.severity == "warning"]
            info_loops = [loop for loop in import_loops if loop.severity == "info"]
            
            return {
                "import_loops": [asdict(loop) for loop in import_loops],
                "summary": {
                    "total_loops": len(import_loops),
                    "critical_loops": len(critical_loops),
                    "warning_loops": len(warning_loops),
                    "info_loops": len(info_loops),
                },
                "recommendations": generate_import_loop_recommendations(import_loops)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing import loops: {e}")
            return {"error": str(e)}
    
    def analyze_dead_code(self, path: str) -> Dict[str, Any]:
        """Detect unused functions, classes, and variables."""
        if not GRAPH_SITTER_AVAILABLE:
            return {"error": "Graph-sitter not available"}
        
        try:
            codebase = Codebase(path, config=self.config)
            dead_code_items = detect_dead_code(codebase)
            
            # Categorize by type
            dead_functions = [item for item in dead_code_items if item.type == "function"]
            dead_classes = [item for item in dead_code_items if item.type == "class"]
            dead_variables = [item for item in dead_code_items if item.type == "variable"]
            
            return {
                "dead_code_items": [asdict(item) for item in dead_code_items],
                "summary": {
                    "total_dead_code_items": len(dead_code_items),
                    "dead_functions": len(dead_functions),
                    "dead_classes": len(dead_classes),
                    "dead_variables": len(dead_variables),
                },
                "recommendations": generate_dead_code_recommendations(dead_code_items)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing dead code: {e}")
            return {"error": str(e)}
    
    def analyze_graph_structure(self, path: str) -> Dict[str, Any]:
        """Perform comprehensive graph structure analysis."""
        if not GRAPH_SITTER_AVAILABLE:
            return {"error": "Graph-sitter not available"}
        
        try:
            codebase = Codebase(path, config=self.config)
            graph_analysis = analyze_graph_structure(codebase)
            
            return {
                "graph_analysis": asdict(graph_analysis),
                "insights": generate_graph_insights(graph_analysis),
                "recommendations": generate_graph_recommendations(graph_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing graph structure: {e}")
            return {"error": str(e)}
    
    def get_enhanced_summary(self, path: str) -> Dict[str, Any]:
        """Get enhanced codebase summary using graph-sitter features."""
        if not GRAPH_SITTER_AVAILABLE:
            return {"error": "Graph-sitter not available"}
        
        try:
            codebase = Codebase(path, config=self.config)
            return get_codebase_summary_enhanced(codebase)
        except Exception as e:
            logger.error(f"Error getting enhanced summary: {e}")
            return {"error": str(e)}
    
    # ========================================================================
    # COMPREHENSIVE ANALYSIS METHODS
    # ========================================================================
    
    def analyze_comprehensive(self, path: str, options: Optional[AnalysisOptions] = None) -> Dict[str, Any]:
        """
        Perform comprehensive analysis with all available features.
        
        Args:
            path: Path to analyze
            options: Analysis options (uses defaults if not provided)
            
        Returns:
            Dictionary containing all analysis results
        """
        if options is None:
            options = create_default_analysis_options()
            options.include_dead_code = True
            options.include_import_loops = True
            options.include_training_data = True
            options.include_enhanced_metrics = True
            options.include_graph_analysis = True
        
        start_time = time.time()
        results = {
            "analysis_metadata": {
                "analyzer_type": "unified",
                "graph_sitter_enabled": self.use_graph_sitter,
                "advanced_config": self.use_advanced_config,
                "start_time": start_time
            }
        }
        
        # Core analysis
        logger.info("Starting comprehensive codebase analysis...")
        core_result = self.analyze_codebase(path, getattr(options, 'extensions', ['.py']))
        results["core_analysis"] = asdict(core_result)
        results["summary_statistics"] = generate_summary_statistics(core_result)
        
        # Enhanced analyses (if graph-sitter is available)
        if self.use_graph_sitter and GRAPH_SITTER_AVAILABLE:
            logger.info("Running enhanced graph-sitter analyses...")
            
            if getattr(options, 'include_enhanced_metrics', False):
                results["enhanced_metrics"] = self.analyze_enhanced_metrics(path)
            
            if getattr(options, 'include_training_data', False):
                results["training_data"] = self.analyze_training_data(path)
            
            if getattr(options, 'include_import_loops', False):
                results["import_loops"] = self.analyze_import_loops(path)
            
            if getattr(options, 'include_dead_code', False):
                results["dead_code"] = self.analyze_dead_code(path)
            
            if getattr(options, 'include_graph_analysis', False):
                results["graph_analysis"] = self.analyze_graph_structure(path)
            
            results["enhanced_summary"] = self.get_enhanced_summary(path)
        
        # Finalize results
        analysis_time = time.time() - start_time
        results["analysis_metadata"]["total_time"] = analysis_time
        results["analysis_metadata"]["completed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        logger.info(f"Comprehensive analysis completed in {analysis_time:.2f} seconds")
        
        return results
    
    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================
    
    def quick_analyze(self, path: str) -> Dict[str, Any]:
        """Perform a quick analysis with basic metrics only."""
        options = create_default_analysis_options()
        options.include_dead_code = False
        options.include_import_loops = False
        options.include_training_data = False
        options.include_enhanced_metrics = False
        options.include_graph_analysis = False
        
        result = self.analyze_codebase(path, getattr(options, 'extensions', ['.py']))
        return {
            "summary": generate_summary_statistics(result),
            "issues": [asdict(issue) for issue in result.issues],
            "analysis_time": result.analysis_time
        }
    
    def analyze_for_ml_training(self, path: str) -> Dict[str, Any]:
        """Analyze codebase specifically for ML training data generation."""
        if not self.use_graph_sitter:
            return {"error": "Graph-sitter required for ML training data generation"}
        
        return self.analyze_training_data(path)
    
    def analyze_for_refactoring(self, path: str) -> Dict[str, Any]:
        """Analyze codebase to identify refactoring opportunities."""
        results = {}
        
        # Core analysis for complexity issues
        core_result = self.analyze_codebase(path)
        results["complexity_issues"] = [
            asdict(issue) for issue in core_result.issues 
            if issue.type in ["complexity", "maintainability"]
        ]
        
        if self.use_graph_sitter:
            # Dead code analysis
            dead_code_result = self.analyze_dead_code(path)
            results["dead_code"] = dead_code_result
            
            # Import loop analysis
            import_loop_result = self.analyze_import_loops(path)
            results["import_loops"] = import_loop_result
            
            # Graph structure analysis
            graph_result = self.analyze_graph_structure(path)
            results["graph_structure"] = graph_result
        
        return results


# ============================================================================
# CONVENIENCE FUNCTIONS FOR BACKWARD COMPATIBILITY
# ============================================================================

def analyze_codebase(path: str, use_graph_sitter: bool = True) -> ComprehensiveAnalysisResult:
    """Convenience function for programmatic use."""
    analyzer = UnifiedCodebaseAnalyzer(use_graph_sitter=use_graph_sitter)
    return analyzer.analyze_codebase(path)


def analyze_from_repo(repo_url: str) -> ComprehensiveAnalysisResult:
    """Analyze a remote repository."""
    if not GRAPH_SITTER_AVAILABLE:
        raise ImportError("Graph-sitter is required for remote repository analysis")
    
    codebase = Codebase.from_repo(repo_url)
    analyzer = UnifiedCodebaseAnalyzer(use_graph_sitter=True)
    return analyzer.analyze_codebase(codebase.path)


def create_analyzer(use_graph_sitter: bool = True, use_advanced_config: bool = False) -> UnifiedCodebaseAnalyzer:
    """Create a configured analyzer instance."""
    return UnifiedCodebaseAnalyzer(
        use_graph_sitter=use_graph_sitter,
        use_advanced_config=use_advanced_config
    )


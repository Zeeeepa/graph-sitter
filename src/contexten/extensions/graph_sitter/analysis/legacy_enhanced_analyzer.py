#!/usr/bin/env python3
"""
Enhanced Codebase Analyzer with Graph-Sitter Integration

This module provides an enhanced analyzer that leverages graph-sitter's
pre-computed graph elements and advanced features.
"""

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import asdict

logger = logging.getLogger(__name__)

try:
    from graph_sitter import Codebase
    from graph_sitter.configs.models.codebase import CodebaseConfig
    from contexten.extensions.graph_sitter.graph_sitter_enhancements import (
        detect_import_loops, analyze_graph_structure, detect_dead_code,
        generate_training_data, get_codebase_summary_enhanced,
        analyze_function_enhanced, analyze_class_enhanced,
        ImportLoop, TrainingDataItem, DeadCodeItem, GraphAnalysisResult,
        EnhancedFunctionMetrics, EnhancedClassMetrics
    )
    GRAPH_SITTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Graph-sitter not available: {e}")
    GRAPH_SITTER_AVAILABLE = False


class EnhancedCodebaseAnalyzer:
    """Enhanced codebase analyzer with graph-sitter integration."""
    
    def __init__(self, use_advanced_config: bool = False):
        """Initialize the enhanced analyzer.
        
        Args:
            use_advanced_config: Whether to use advanced CodebaseConfig options
        """
        self.use_advanced_config = use_advanced_config
        self.config = self._create_config() if use_advanced_config else None
    
    def _create_config(self) -> Optional[CodebaseConfig]:
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
    
    def analyze_codebase_enhanced(self, path: str, extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """Perform enhanced codebase analysis using graph-sitter features.
        
        Args:
            path: Path to analyze
            extensions: File extensions to include
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        if not GRAPH_SITTER_AVAILABLE:
            return {"error": "Graph-sitter not available"}
        
        start_time = time.time()
        
        try:
            # Initialize codebase with optional advanced config
            if self.config:
                codebase = Codebase(path, config=self.config)
                logger.info("Using advanced CodebaseConfig")
            else:
                codebase = Codebase(path)
                logger.info("Using default configuration")
            
            # Get enhanced codebase summary
            summary = get_codebase_summary_enhanced(codebase)
            
            # Perform various analyses
            results = {
                "codebase_summary": summary,
                "analysis_time": time.time() - start_time,
                "config_used": "advanced" if self.config else "default"
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error in enhanced codebase analysis: {e}")
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
                "recommendations": self._generate_import_loop_recommendations(import_loops)
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
                "recommendations": self._generate_dead_code_recommendations(dead_code_items)
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
                "insights": self._generate_graph_insights(graph_analysis),
                "recommendations": self._generate_graph_recommendations(graph_analysis)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing graph structure: {e}")
            return {"error": str(e)}
    
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
                    "functions_with_dependencies": len([f for f in enhanced_functions if f["dependencies"]]),
                    "functions_with_usages": len([f for f in enhanced_functions if f["usages"]]),
                    "classes_with_inheritance": len([c for c in enhanced_classes if c["parent_classes"]]),
                    "async_functions": len([f for f in enhanced_functions if f["is_async"]]),
                    "generator_functions": len([f for f in enhanced_functions if f["is_generator"]]),
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing enhanced metrics: {e}")
            return {"error": str(e)}
    
    def _generate_import_loop_recommendations(self, import_loops: List[ImportLoop]) -> List[str]:
        """Generate recommendations for fixing import loops."""
        recommendations = []
        
        critical_loops = [loop for loop in import_loops if loop.severity == "critical"]
        if critical_loops:
            recommendations.append("🚨 Critical: Fix mixed static/dynamic import loops immediately")
            recommendations.append("Consider using dependency injection or factory patterns")
        
        if len(import_loops) > 5:
            recommendations.append("📊 High number of import loops detected - consider architectural refactoring")
        
        if import_loops:
            recommendations.append("💡 Consider moving shared code to separate modules")
            recommendations.append("🔄 Use lazy imports where appropriate")
        
        return recommendations
    
    def _generate_dead_code_recommendations(self, dead_code_items: List[DeadCodeItem]) -> List[str]:
        """Generate recommendations for handling dead code."""
        recommendations = []
        
        high_confidence_items = [item for item in dead_code_items if item.confidence > 0.7]
        if high_confidence_items:
            recommendations.append(f"🗑️ {len(high_confidence_items)} high-confidence dead code items can be safely removed")
        
        if len(dead_code_items) > 10:
            recommendations.append("📈 Consider implementing automated dead code removal in CI/CD")
        
        if dead_code_items:
            recommendations.append("🔍 Review dead code items before removal - some may be used dynamically")
            recommendations.append("📝 Update documentation to reflect removed functionality")
        
        return recommendations
    
    def _generate_graph_insights(self, graph_analysis: GraphAnalysisResult) -> List[str]:
        """Generate insights from graph analysis."""
        insights = []
        
        if graph_analysis.total_nodes > 1000:
            insights.append(f"📊 Large codebase with {graph_analysis.total_nodes:,} nodes")
        
        edge_ratio = graph_analysis.total_edges / graph_analysis.total_nodes if graph_analysis.total_nodes > 0 else 0
        if edge_ratio > 3:
            insights.append(f"🔗 High connectivity (edge ratio: {edge_ratio:.1f}) - well-connected codebase")
        elif edge_ratio < 1:
            insights.append(f"🔗 Low connectivity (edge ratio: {edge_ratio:.1f}) - loosely coupled modules")
        
        if graph_analysis.import_loops:
            insights.append(f"🔄 {len(graph_analysis.import_loops)} import loops detected")
        
        return insights
    
    def _generate_graph_recommendations(self, graph_analysis: GraphAnalysisResult) -> List[str]:
        """Generate recommendations from graph analysis."""
        recommendations = []
        
        if graph_analysis.strongly_connected_components:
            recommendations.append("🔄 Consider breaking up strongly connected components")
        
        if graph_analysis.symbol_usage_edges < graph_analysis.total_edges * 0.3:
            recommendations.append("📊 Low symbol usage ratio - consider code organization review")
        
        return recommendations


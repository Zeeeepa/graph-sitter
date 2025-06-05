"""
Legacy Unified Analyzer - Refactored for New Analysis Framework

This module provides backward compatibility for the existing unified analyzer
while integrating with the new standardized analysis framework.
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from graph_sitter.core.codebase import Codebase

# Import unified analysis framework
from .base import BaseAnalyzer, AnalysisType, AnalysisResult, AnalysisIssue, AnalysisMetric, IssueSeverity
from .registry import get_registry, register_analyzer

# Import existing analysis components
try:
    from .enhanced_analysis import EnhancedAnalyzer
except ImportError:
    EnhancedAnalyzer = None

try:
    from .metrics import CodebaseMetrics, calculate_codebase_metrics
except ImportError:
    CodebaseMetrics = None
    calculate_codebase_metrics = None

try:
    from .dependency_analyzer import DependencyAnalyzer
except ImportError:
    DependencyAnalyzer = None

try:
    from .call_graph import CallGraphAnalyzer
except ImportError:
    CallGraphAnalyzer = None

try:
    from .dead_code import DeadCodeAnalyzer
except ImportError:
    DeadCodeAnalyzer = None

try:
    from .function_context import FunctionContext, get_function_context
except ImportError:
    FunctionContext = None
    get_function_context = None

# Import visualization components
try:
    from ..visualizations.react_visualizations import create_react_visualizations
    from ..visualizations.codebase_visualization import create_comprehensive_visualization
except ImportError:
    create_react_visualizations = None
    create_comprehensive_visualization = None

logger = logging.getLogger(__name__)


@dataclass
class LegacyAnalysisResult:
    """Legacy analysis result format for backward compatibility."""
    codebase_id: str
    timestamp: str
    enhanced_analysis: Optional[Dict[str, Any]] = None
    metrics: Optional[Dict[str, Any]] = None
    dependencies: Optional[Dict[str, Any]] = None
    call_graph: Optional[Dict[str, Any]] = None
    dead_code: Optional[Dict[str, Any]] = None
    function_contexts: Optional[Dict[str, Any]] = None
    visualizations: Optional[Dict[str, Any]] = None
    
    def to_unified_result(self) -> Dict[str, AnalysisResult]:
        """Convert legacy result to new unified format."""
        results = {}
        
        if self.enhanced_analysis:
            results['enhanced_analysis'] = self._convert_to_analysis_result(
                AnalysisType.METRICS, self.enhanced_analysis
            )
        
        if self.metrics:
            results['metrics'] = self._convert_to_analysis_result(
                AnalysisType.METRICS, self.metrics
            )
        
        if self.dependencies:
            results['dependencies'] = self._convert_to_analysis_result(
                AnalysisType.DEPENDENCIES, self.dependencies
            )
        
        if self.call_graph:
            results['call_graph'] = self._convert_to_analysis_result(
                AnalysisType.CALL_GRAPH, self.call_graph
            )
        
        if self.dead_code:
            results['dead_code'] = self._convert_to_analysis_result(
                AnalysisType.DEAD_CODE, self.dead_code
            )
        
        if self.function_contexts:
            results['function_context'] = self._convert_to_analysis_result(
                AnalysisType.FUNCTION_CONTEXT, self.function_contexts
            )
        
        return results
    
    def _convert_to_analysis_result(self, analysis_type: AnalysisType, data: Dict[str, Any]) -> AnalysisResult:
        """Convert legacy data to new AnalysisResult format."""
        # Extract issues from legacy format
        issues = []
        if 'issues' in data:
            for issue_data in data['issues']:
                issue = AnalysisIssue(
                    type=issue_data.get('type', 'unknown'),
                    severity=IssueSeverity(issue_data.get('severity', 'info')),
                    description=issue_data.get('description', ''),
                    file=issue_data.get('file'),
                    location=issue_data.get('location'),
                    line_number=issue_data.get('line_number'),
                    column_number=issue_data.get('column_number'),
                    rule_id=issue_data.get('rule_id'),
                    suggestion=issue_data.get('suggestion'),
                    metadata=issue_data.get('metadata', {})
                )
                issues.append(issue)
        
        # Extract metrics from legacy format
        metrics = []
        if 'metrics' in data:
            for metric_name, metric_value in data['metrics'].items():
                metric = AnalysisMetric(
                    name=metric_name,
                    value=metric_value,
                    category=analysis_type.value
                )
                metrics.append(metric)
        
        # Extract recommendations
        recommendations = data.get('recommendations', [])
        
        return AnalysisResult(
            analysis_type=analysis_type,
            timestamp=datetime.fromisoformat(self.timestamp),
            issues=issues,
            metrics=metrics,
            raw_data=data,
            recommendations=recommendations,
            success=True
        )


class LegacyUnifiedAnalyzer(BaseAnalyzer):
    """
    Legacy unified analyzer adapted to work with the new analysis framework.
    
    This class provides backward compatibility while leveraging the new
    standardized analysis interfaces.
    """
    
    def __init__(self, codebase: Codebase, config: Optional[Dict[str, Any]] = None):
        """Initialize the legacy unified analyzer."""
        super().__init__(codebase, config)
        self.registry = get_registry()
        self._legacy_results: Optional[LegacyAnalysisResult] = None
    
    def _get_analysis_type(self) -> AnalysisType:
        """Return the analysis type for this analyzer."""
        return AnalysisType.METRICS  # Default to metrics for legacy compatibility
    
    def analyze(self) -> AnalysisResult:
        """
        Perform comprehensive analysis using legacy components.
        
        Returns:
            AnalysisResult containing aggregated results from all legacy analyzers
        """
        try:
            # Run legacy comprehensive analysis
            legacy_result = self.run_comprehensive_analysis_legacy()
            
            # Convert to new format
            unified_results = legacy_result.to_unified_result()
            
            # Aggregate all results into a single comprehensive result
            all_issues = []
            all_metrics = []
            all_recommendations = []
            raw_data = {}
            
            for analyzer_name, result in unified_results.items():
                all_issues.extend(result.issues)
                all_metrics.extend(result.metrics)
                all_recommendations.extend(result.recommendations)
                raw_data[analyzer_name] = result.raw_data
            
            return self.create_result(
                issues=all_issues,
                metrics=all_metrics,
                raw_data=raw_data,
                recommendations=all_recommendations,
                execution_time=None,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Legacy unified analysis failed: {e}")
            return self.create_result(
                issues=[self.create_issue(
                    "analysis_error",
                    IssueSeverity.ERROR,
                    f"Legacy analysis failed: {str(e)}"
                )],
                metrics=[],
                raw_data={'error': str(e)},
                recommendations=["Check legacy analyzer configuration"],
                execution_time=None,
                success=False,
                error_message=str(e)
            )
    
    def run_comprehensive_analysis_legacy(self) -> LegacyAnalysisResult:
        """
        Run comprehensive analysis using legacy analyzers.
        
        Returns:
            LegacyAnalysisResult with all analysis components
        """
        codebase_id = str(hash(str(self.codebase.root_path)))
        timestamp = datetime.now().isoformat()
        
        result = LegacyAnalysisResult(
            codebase_id=codebase_id,
            timestamp=timestamp
        )
        
        # Run enhanced analysis if available
        if EnhancedAnalyzer:
            try:
                enhanced_analyzer = EnhancedAnalyzer(self.codebase)
                enhanced_result = enhanced_analyzer.analyze_codebase_enhanced()
                result.enhanced_analysis = asdict(enhanced_result) if enhanced_result else None
            except Exception as e:
                logger.warning(f"Enhanced analysis failed: {e}")
        
        # Run metrics analysis if available
        if CodebaseMetrics:
            try:
                metrics_analyzer = CodebaseMetrics(self.codebase)
                metrics_result = calculate_codebase_metrics(self.codebase)
                result.metrics = asdict(metrics_result) if metrics_result else None
            except Exception as e:
                logger.warning(f"Metrics analysis failed: {e}")
        
        # Run dependency analysis if available
        if DependencyAnalyzer:
            try:
                dep_analyzer = DependencyAnalyzer(self.codebase)
                dep_result = dep_analyzer.analyze_dependencies()
                result.dependencies = asdict(dep_result) if dep_result else None
            except Exception as e:
                logger.warning(f"Dependency analysis failed: {e}")
        
        # Run call graph analysis if available
        if CallGraphAnalyzer:
            try:
                call_analyzer = CallGraphAnalyzer(self.codebase)
                call_result = call_analyzer.generate_call_graph()
                result.call_graph = asdict(call_result) if call_result else None
            except Exception as e:
                logger.warning(f"Call graph analysis failed: {e}")
        
        # Run dead code analysis if available
        if DeadCodeAnalyzer:
            try:
                dead_analyzer = DeadCodeAnalyzer(self.codebase)
                dead_result = dead_analyzer.find_dead_code()
                result.dead_code = asdict(dead_result) if dead_result else None
            except Exception as e:
                logger.warning(f"Dead code analysis failed: {e}")
        
        # Run function context analysis if available
        if get_function_context:
            try:
                function_contexts = {}
                for file in self.codebase.files:
                    for func in file.functions:
                        context = get_function_context(func, self.codebase)
                        if context:
                            function_contexts[f"{file.path}::{func.name}"] = asdict(context)
                result.function_contexts = function_contexts
            except Exception as e:
                logger.warning(f"Function context analysis failed: {e}")
        
        # Generate visualizations if available
        if create_comprehensive_visualization:
            try:
                viz_data = create_comprehensive_visualization(self.codebase)
                result.visualizations = viz_data
            except Exception as e:
                logger.warning(f"Visualization generation failed: {e}")
        
        self._legacy_results = result
        return result
    
    def get_legacy_results(self) -> Optional[LegacyAnalysisResult]:
        """Get the legacy analysis results."""
        return self._legacy_results
    
    def export_legacy_format(self, output_path: str) -> None:
        """Export results in legacy format for backward compatibility."""
        if not self._legacy_results:
            raise ValueError("No legacy results available. Run analysis first.")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(self._legacy_results), f, indent=2, default=str)
        
        logger.info(f"Legacy results exported to {output_file}")


# Register the legacy analyzer with the registry
def register_legacy_analyzer():
    """Register the legacy unified analyzer with the global registry."""
    try:
        register_analyzer(
            name="legacy_unified",
            analyzer_class=LegacyUnifiedAnalyzer,
            analysis_type=AnalysisType.METRICS,
            description="Legacy unified analyzer for backward compatibility",
            supported_languages=["python", "typescript", "javascript"],
            dependencies=["enhanced_analysis", "metrics", "dependencies", "call_graph", "dead_code"],
            enabled=True
        )
        logger.info("Legacy unified analyzer registered successfully")
    except Exception as e:
        logger.warning(f"Failed to register legacy unified analyzer: {e}")


# Auto-register when module is imported
register_legacy_analyzer()


# Convenience function for backward compatibility
def run_comprehensive_analysis(codebase: Codebase, config: Optional[Dict[str, Any]] = None) -> LegacyAnalysisResult:
    """
    Run comprehensive analysis using legacy format.
    
    Args:
        codebase: Codebase to analyze
        config: Optional configuration
        
    Returns:
        LegacyAnalysisResult with all analysis components
    """
    analyzer = LegacyUnifiedAnalyzer(codebase, config)
    analyzer.analyze()  # This populates the legacy results
    return analyzer.get_legacy_results()


# Export for backward compatibility
__all__ = [
    "LegacyUnifiedAnalyzer",
    "LegacyAnalysisResult", 
    "run_comprehensive_analysis",
    "register_legacy_analyzer"
]


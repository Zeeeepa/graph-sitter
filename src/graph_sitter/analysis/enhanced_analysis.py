"""Enhanced codebase analysis integrating all graph-sitter.com capabilities."""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.function import Function
from graph_sitter.core.symbol import Symbol

from .call_graph import CallGraphAnalyzer
from .dead_code import DeadCodeDetector
from .dependency_analyzer import DependencyAnalyzer
from .metrics import MetricsCalculator

logger = logging.getLogger(__name__)


@dataclass
class AnalysisReport:
    """Comprehensive analysis report."""
    codebase_id: str
    timestamp: str
    summary: Dict[str, Any]
    metrics: Dict[str, Any]
    call_graph_analysis: Dict[str, Any]
    dependency_analysis: Dict[str, Any]
    dead_code_analysis: Dict[str, Any]
    function_analysis: List[Dict[str, Any]]
    class_analysis: List[Dict[str, Any]]
    file_analysis: List[Dict[str, Any]]
    issues: List[Dict[str, Any]]
    recommendations: List[str]
    health_score: float
    # Optional visualization data for dashboard rendering
    visualization_data: Optional[Dict[str, Any]] = None


class EnhancedCodebaseAnalyzer:
    """Comprehensive codebase analyzer integrating all capabilities."""
    
    def __init__(self, codebase: Codebase, codebase_id: str = "default"):
        self.codebase = codebase
        self.codebase_id = codebase_id
        
        # Initialize analyzers
        self.metrics_calculator = MetricsCalculator(codebase)
        self.call_graph_analyzer = CallGraphAnalyzer(codebase)
        self.dependency_analyzer = DependencyAnalyzer(codebase)
        self.dead_code_detector = DeadCodeDetector(codebase)
    
    def run_full_analysis(self) -> AnalysisReport:
        """Run comprehensive analysis of the codebase."""
        try:
            logger.info(f"Starting full analysis for codebase: {self.codebase_id}")
            
            # Get basic metrics
            codebase_metrics = self.metrics_calculator.get_codebase_summary()
            
            # Analyze call graph
            call_graph_analysis = self._analyze_call_graph()
            
            # Analyze dependencies
            dependency_analysis = self._analyze_dependencies()
            
            # Detect dead code
            dead_code_analysis = self._analyze_dead_code()
            
            # Analyze functions
            function_analysis = self._analyze_functions()
            
            # Analyze classes
            class_analysis = self._analyze_classes()
            
            # Analyze files
            file_analysis = self._analyze_files()
            
            # Detect issues
            issues = self._detect_issues()
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                codebase_metrics, call_graph_analysis, dependency_analysis, dead_code_analysis
            )
            
            # Calculate health score
            health_score = self._calculate_health_score(
                codebase_metrics, call_graph_analysis, dependency_analysis, dead_code_analysis
            )
            
            report = AnalysisReport(
                codebase_id=self.codebase_id,
                timestamp=datetime.now().isoformat(),
                summary=asdict(codebase_metrics),
                metrics={
                    'codebase': asdict(codebase_metrics),
                    'call_graph': call_graph_analysis,
                    'dependencies': dependency_analysis,
                    'dead_code': dead_code_analysis
                },
                call_graph_analysis=call_graph_analysis,
                dependency_analysis=dependency_analysis,
                dead_code_analysis=dead_code_analysis,
                function_analysis=function_analysis,
                class_analysis=class_analysis,
                file_analysis=file_analysis,
                issues=issues,
                recommendations=recommendations,
                health_score=health_score,
                visualization_data=None
            )
            
            logger.info(f"Analysis completed. Health score: {health_score:.2f}")
            return report
            
        except Exception as e:
            logger.error(f"Error during full analysis: {e}")
            raise
    
    def get_function_context_analysis(self, function_name: str) -> Dict[str, Any]:
        """Get comprehensive context analysis for a function."""
        try:
            # Find the function
            function = None
            for func in self.codebase.functions:
                if func.name == function_name:
                    function = func
                    break
            
            if not function:
                return {'error': f'Function {function_name} not found'}
            
            # Get function metrics
            function_metrics = self.metrics_calculator.analyze_function_metrics(function)
            
            # Get call graph context
            call_depth = self.call_graph_analyzer.get_function_call_depth(function_name)
            
            # Get dependency context
            dependency_context = self.dependency_analyzer.analyze_symbol_dependencies(function)
            
            # Check if function is dead code
            dead_code_items = self.dead_code_detector.find_dead_code()
            is_dead_code = any(
                item.symbol.name == function_name and item.type == 'function'
                for item in dead_code_items
            )
            
            return {
                'function_name': function_name,
                'metrics': asdict(function_metrics),
                'call_graph': {
                    'depth': call_depth,
                    'incoming_calls': len(getattr(function, 'call_sites', [])),
                    'outgoing_calls': len(getattr(function, 'function_calls', []))
                },
                'dependencies': dependency_context,
                'is_dead_code': is_dead_code,
                'implementation': {
                    'source': getattr(function, 'source', ''),
                    'filepath': getattr(function, 'filepath', 'unknown'),
                    'line_start': getattr(function, 'line_start', None),
                    'line_end': getattr(function, 'line_end', None)
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing function context: {e}")
            return {'error': str(e)}
    
    def get_codebase_health_score(self) -> Dict[str, Any]:
        """Calculate comprehensive codebase health assessment."""
        try:
            # Get metrics
            metrics = self.metrics_calculator.get_codebase_summary()
            
            # Calculate component scores
            maintainability_score = metrics.average_maintainability / 100.0
            documentation_score = metrics.documentation_coverage
            test_coverage_score = metrics.test_coverage_estimate
            dead_code_score = 1.0 - metrics.dead_code_percentage
            complexity_score = max(0.0, 1.0 - (metrics.average_complexity - 1.0) / 10.0)
            
            # Get additional scores
            call_graph_score = self._calculate_call_graph_health()
            dependency_score = self._calculate_dependency_health()
            
            # Weighted health score
            health_score = (
                maintainability_score * 0.25 +
                documentation_score * 0.15 +
                test_coverage_score * 0.15 +
                dead_code_score * 0.15 +
                complexity_score * 0.15 +
                call_graph_score * 0.10 +
                dependency_score * 0.05
            )
            
            return {
                'overall_health_score': health_score,
                'component_scores': {
                    'maintainability': maintainability_score,
                    'documentation': documentation_score,
                    'test_coverage': test_coverage_score,
                    'dead_code': dead_code_score,
                    'complexity': complexity_score,
                    'call_graph': call_graph_score,
                    'dependencies': dependency_score
                },
                'grade': self._score_to_grade(health_score),
                'recommendations': self._health_recommendations(health_score)
            }
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return {'error': str(e)}
    
    async def query_analysis_data(self, query: str) -> Dict[str, Any]:
        """Query analysis data using natural language."""
        try:
            # This would integrate with the enhanced AI system
            if hasattr(self.codebase, 'ai'):
                # Prepare context about the codebase
                context = {
                    'codebase_summary': asdict(self.metrics_calculator.get_codebase_summary()),
                    'call_graph_patterns': self.call_graph_analyzer.analyze_call_patterns(),
                    'dependency_analysis': self.dependency_analyzer.analyze_imports(),
                    'dead_code_count': len(self.dead_code_detector.find_dead_code())
                }
                
                prompt = f"""
                Analyze this codebase query: "{query}"
                
                Codebase Context:
                {json.dumps(context, indent=2, default=str)}
                
                Please provide a detailed analysis addressing the query.
                """
                
                result = await self.codebase.ai(prompt)
                return {
                    'query': query,
                    'analysis': result.content if hasattr(result, 'content') else str(result),
                    'context': context
                }
            else:
                return {'error': 'AI analysis not available'}
        except Exception as e:
            logger.error(f"Error querying analysis data: {e}")
            return {'error': str(e)}
    
    def generate_analysis_report(self, format: str = 'json') -> str:
        """Generate comprehensive analysis report."""
        try:
            report = self.run_full_analysis()
            
            if format == 'json':
                return json.dumps(asdict(report), indent=2, default=str)
            elif format == 'markdown':
                return self._generate_markdown_report(report)
            else:
                raise ValueError(f"Unsupported format: {format}")
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}"
    
    def _analyze_call_graph(self) -> Dict[str, Any]:
        """Analyze call graph patterns."""
        try:
            patterns = self.call_graph_analyzer.analyze_call_patterns()
            
            # Find specific patterns
            most_called = self.call_graph_analyzer.find_most_called_function()
            most_calling = self.call_graph_analyzer.find_most_calling_function()
            unused_functions = self.call_graph_analyzer.find_unused_functions()
            recursive_functions = self.call_graph_analyzer.find_recursive_functions()
            
            return {
                'patterns': patterns,
                'most_called_function': most_called.name if most_called else None,
                'most_calling_function': most_calling.name if most_calling else None,
                'unused_functions': [f.name for f in unused_functions],
                'recursive_functions': [f.name for f in recursive_functions],
                'call_chains': self.call_graph_analyzer.analyze_call_chains()
            }
        except Exception as e:
            logger.error(f"Error analyzing call graph: {e}")
            return {}
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze dependency patterns."""
        try:
            import_analysis = self.dependency_analyzer.analyze_imports()
            circular_deps = self.dependency_analyzer.find_circular_dependencies()
            
            return {
                'import_analysis': asdict(import_analysis),
                'circular_dependencies': [
                    {
                        'symbols': [s.name for s in cd.symbols],
                        'severity': cd.severity,
                        'description': cd.description
                    }
                    for cd in circular_deps
                ],
                'optimization_suggestions': self.dependency_analyzer.optimize_import_structure()
            }
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
            return {}
    
    def _analyze_dead_code(self) -> Dict[str, Any]:
        """Analyze dead code."""
        try:
            dead_code_items = self.dead_code_detector.find_dead_code()
            cleanup_impact = self.dead_code_detector.estimate_cleanup_impact(dead_code_items)
            removal_plan = self.dead_code_detector.get_removal_plan(dead_code_items)
            
            return {
                'dead_code_items': [
                    {
                        'name': item.symbol.name,
                        'type': item.type,
                        'filepath': item.filepath,
                        'reason': item.reason,
                        'confidence': item.confidence,
                        'safe_to_remove': item.safe_to_remove
                    }
                    for item in dead_code_items
                ],
                'cleanup_impact': cleanup_impact,
                'removal_plan': {
                    'items_count': len(removal_plan.items),
                    'estimated_lines_saved': removal_plan.estimated_lines_saved,
                    'risk_assessment': removal_plan.risk_assessment,
                    'warnings': removal_plan.warnings
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing dead code: {e}")
            return {}
    
    def _analyze_functions(self) -> List[Dict[str, Any]]:
        """Analyze all functions."""
        try:
            function_analyses = []
            for function in list(self.codebase.functions)[:50]:  # Limit for performance
                try:
                    metrics = self.metrics_calculator.analyze_function_metrics(function)
                    function_analyses.append(asdict(metrics))
                except Exception as e:
                    logger.warning(f"Error analyzing function {function.name}: {e}")
            
            return function_analyses
        except Exception as e:
            logger.error(f"Error analyzing functions: {e}")
            return []
    
    def _analyze_classes(self) -> List[Dict[str, Any]]:
        """Analyze all classes."""
        try:
            class_analyses = []
            for class_def in list(self.codebase.classes)[:50]:  # Limit for performance
                try:
                    metrics = self.metrics_calculator.analyze_class_metrics(class_def)
                    class_analyses.append(asdict(metrics))
                except Exception as e:
                    logger.warning(f"Error analyzing class {getattr(class_def, 'name', None) or 'unknown_class'}: {e}")
            
            return class_analyses
        except Exception as e:
            logger.error(f"Error analyzing classes: {e}")
            return []
    
    def _analyze_files(self) -> List[Dict[str, Any]]:
        """Analyze all files."""
        try:
            file_analyses = []
            for file in list(self.codebase.files)[:50]:  # Limit for performance
                try:
                    metrics = self.metrics_calculator.analyze_file_metrics(file)
                    file_analyses.append(asdict(metrics))
                except Exception as e:
                    logger.warning(f"Error analyzing file {file.filepath}: {e}")
            
            return file_analyses
        except Exception as e:
            logger.error(f"Error analyzing files: {e}")
            return []
    
    def _detect_issues(self) -> List[Dict[str, Any]]:
        """Detect various code issues."""
        try:
            issues = []
            
            # Get metrics for issue detection
            codebase_metrics = self.metrics_calculator.get_codebase_summary()
            
            # High complexity functions
            for function in self.codebase.functions:
                try:
                    complexity = self.metrics_calculator.calculate_cyclomatic_complexity(function)
                    if complexity > 10:
                        issues.append({
                            'type': 'high_complexity',
                            'severity': 'medium',
                            'symbol': function.name,
                            'description': f'Function has high cyclomatic complexity: {complexity}',
                            'suggestion': 'Consider breaking this function into smaller functions'
                        })
                except Exception:
                    continue
            
            # Poor documentation
            if codebase_metrics.documentation_coverage < 0.5:
                issues.append({
                    'type': 'poor_documentation',
                    'severity': 'medium',
                    'symbol': 'codebase',
                    'description': f'Low documentation coverage: {codebase_metrics.documentation_coverage:.1%}',
                    'suggestion': 'Add docstrings to functions and classes'
                })
            
            # High dead code percentage
            if codebase_metrics.dead_code_percentage > 0.2:
                issues.append({
                    'type': 'dead_code',
                    'severity': 'low',
                    'symbol': 'codebase',
                    'description': f'High dead code percentage: {codebase_metrics.dead_code_percentage:.1%}',
                    'suggestion': 'Remove unused functions and classes'
                })
            
            # Circular dependencies
            circular_deps = self.dependency_analyzer.find_circular_dependencies()
            for cd in circular_deps:
                if cd.severity in ['medium', 'high']:
                    issues.append({
                        'type': 'circular_dependency',
                        'severity': cd.severity,
                        'symbol': ', '.join([s.name for s in cd.symbols]),
                        'description': cd.description,
                        'suggestion': 'Refactor to break circular dependencies'
                    })
            
            return issues
        except Exception as e:
            logger.error(f"Error detecting issues: {e}")
            return []
    
    def _generate_recommendations(self, codebase_metrics, call_graph_analysis, 
                                dependency_analysis, dead_code_analysis) -> List[str]:
        """Generate improvement recommendations."""
        try:
            recommendations = []
            
            # Maintainability recommendations
            if codebase_metrics.average_maintainability < 60:
                recommendations.append(
                    "Improve code maintainability by reducing complexity and adding documentation"
                )
            
            # Documentation recommendations
            if codebase_metrics.documentation_coverage < 0.7:
                recommendations.append(
                    "Increase documentation coverage by adding docstrings to functions and classes"
                )
            
            # Test coverage recommendations
            if codebase_metrics.test_coverage_estimate < 0.6:
                recommendations.append(
                    "Improve test coverage by adding unit tests for critical functions"
                )
            
            # Dead code recommendations
            dead_code_count = len(dead_code_analysis.get('dead_code_items', []))
            if dead_code_count > 0:
                recommendations.append(
                    f"Remove {dead_code_count} dead code items to improve codebase cleanliness"
                )
            
            # Call graph recommendations
            unused_functions = call_graph_analysis.get('unused_functions', [])
            if len(unused_functions) > 5:
                recommendations.append(
                    f"Review {len(unused_functions)} unused functions for potential removal"
                )
            
            # Dependency recommendations
            circular_deps = dependency_analysis.get('circular_dependencies', [])
            if circular_deps:
                recommendations.append(
                    f"Resolve {len(circular_deps)} circular dependencies to improve architecture"
                )
            
            return recommendations
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []
    
    def _calculate_health_score(self, codebase_metrics, call_graph_analysis,
                              dependency_analysis, dead_code_analysis) -> float:
        """Calculate overall codebase health score."""
        try:
            # Component scores
            maintainability = codebase_metrics.average_maintainability / 100.0
            documentation = codebase_metrics.documentation_coverage
            test_coverage = codebase_metrics.test_coverage_estimate
            dead_code_penalty = codebase_metrics.dead_code_percentage
            
            # Call graph health
            patterns = call_graph_analysis.get('patterns', {})
            call_graph_health = min(1.0, patterns.get('average_calls_per_function', 0) / 5.0)
            
            # Dependency health
            import_analysis = dependency_analysis.get('import_analysis', {})
            dependency_health = 1.0 - import_analysis.get('import_complexity_score', 0)
            
            # Weighted score
            health_score = (
                maintainability * 0.3 +
                documentation * 0.2 +
                test_coverage * 0.2 +
                (1.0 - dead_code_penalty) * 0.15 +
                call_graph_health * 0.1 +
                dependency_health * 0.05
            )
            
            return max(0.0, min(1.0, health_score))
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.5
    
    def _calculate_call_graph_health(self) -> float:
        """Calculate call graph health score."""
        try:
            patterns = self.call_graph_analyzer.analyze_call_patterns()
            
            # Ideal metrics
            ideal_avg_calls = 3.0
            ideal_max_depth = 10
            
            avg_calls = patterns.get('average_calls_per_function', 0)
            max_depth = patterns.get('max_call_depth', 0)
            
            # Score based on how close to ideal
            calls_score = 1.0 - abs(avg_calls - ideal_avg_calls) / ideal_avg_calls
            depth_score = 1.0 - max(0, max_depth - ideal_max_depth) / ideal_max_depth
            
            return (calls_score + depth_score) / 2.0
        except Exception:
            return 0.5
    
    def _calculate_dependency_health(self) -> float:
        """Calculate dependency health score."""
        try:
            import_analysis = self.dependency_analyzer.analyze_imports()
            
            # Penalties for issues
            penalty = 0.0
            
            if import_analysis.total_imports > 0:
                unused_ratio = import_analysis.unused_imports / import_analysis.total_imports
                circular_ratio = import_analysis.circular_imports / import_analysis.total_imports
                
                penalty += unused_ratio * 0.3
                penalty += circular_ratio * 0.5
                penalty += import_analysis.import_complexity_score * 0.2
            
            return max(0.0, 1.0 - penalty)
        except Exception:
            return 0.5
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 0.9:
            return 'A'
        elif score >= 0.8:
            return 'B'
        elif score >= 0.7:
            return 'C'
        elif score >= 0.6:
            return 'D'
        else:
            return 'F'
    
    def _health_recommendations(self, score: float) -> List[str]:
        """Generate health-based recommendations."""
        if score >= 0.9:
            return ["Excellent codebase health! Continue current practices."]
        elif score >= 0.8:
            return ["Good codebase health. Focus on minor improvements."]
        elif score >= 0.7:
            return ["Moderate health. Address documentation and test coverage."]
        elif score >= 0.6:
            return ["Below average health. Focus on reducing complexity and dead code."]
        else:
            return ["Poor health. Comprehensive refactoring recommended."]
    
    def _generate_markdown_report(self, report: AnalysisReport) -> str:
        """Generate markdown format report."""
        try:
            md = f"""# Codebase Analysis Report

**Codebase ID:** {report.codebase_id}
**Generated:** {report.timestamp}
**Health Score:** {report.health_score:.2f} ({self._score_to_grade(report.health_score)})

## Summary

- **Total Files:** {report.summary['total_files']}
- **Total Functions:** {report.summary['total_functions']}
- **Total Classes:** {report.summary['total_classes']}
- **Total Lines:** {report.summary['total_lines']}
- **Average Complexity:** {report.summary['average_complexity']:.1f}
- **Documentation Coverage:** {report.summary['documentation_coverage']:.1%}
- **Test Coverage:** {report.summary['test_coverage_estimate']:.1%}

## Issues Found

"""
            for issue in report.issues:
                md += f"- **{issue['severity'].upper()}:** {issue['description']}\n"
                md += f"  - *Suggestion:* {issue['suggestion']}\n\n"
            
            md += "## Recommendations\n\n"
            for rec in report.recommendations:
                md += f"- {rec}\n"
            
            return md
        except Exception as e:
            logger.error(f"Error generating markdown report: {e}")
            return f"Error generating report: {e}"


# Convenience functions
def run_full_analysis(codebase: Codebase, codebase_id: str = "default") -> AnalysisReport:
    """Run comprehensive analysis."""
    analyzer = EnhancedCodebaseAnalyzer(codebase, codebase_id)
    return analyzer.run_full_analysis()


def get_function_context_analysis(codebase: Codebase, function_name: str) -> Dict[str, Any]:
    """Get function context analysis."""
    analyzer = EnhancedCodebaseAnalyzer(codebase)
    return analyzer.get_function_context_analysis(function_name)


def get_codebase_health_score(codebase: Codebase) -> Dict[str, Any]:
    """Get health assessment."""
    analyzer = EnhancedCodebaseAnalyzer(codebase)
    return analyzer.get_codebase_health_score()


async def query_analysis_data(codebase: Codebase, query: str) -> Dict[str, Any]:
    """Query analysis data."""
    analyzer = EnhancedCodebaseAnalyzer(codebase)
    return await analyzer.query_analysis_data(query)


def generate_analysis_report(codebase: Codebase, format: str = 'json') -> str:
    """Generate analysis report."""
    analyzer = EnhancedCodebaseAnalyzer(codebase)
    return analyzer.generate_analysis_report(format)

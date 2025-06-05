"""
Unified Analysis class for comprehensive codebase analysis.

This module provides the main Analysis class that orchestrates all analysis components
and provides a clean API for users to perform comprehensive code analysis.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from datetime import datetime

from graph_sitter.core.codebase import Codebase
from graph_sitter.adapters.analysis.registry import AnalysisRegistry
from graph_sitter.adapters.reports.html_generator import HTMLReportGenerator
from graph_sitter.adapters.visualizations.dashboard import InteractiveDashboard


@dataclass
class AnalysisResult:
    """Container for analysis results."""
    
    analysis_type: str
    timestamp: datetime
    results: Dict[str, Any]
    issues: List[Dict[str, Any]]
    metrics: Dict[str, float]
    recommendations: List[str]


@dataclass
class AnalysisConfig:
    """Configuration for analysis execution."""
    
    include_dead_code: bool = True
    include_dependencies: bool = True
    include_call_graph: bool = True
    include_metrics: bool = True
    include_function_context: bool = True
    generate_html_report: bool = True
    generate_interactive_dashboard: bool = True
    output_dir: Optional[str] = None
    report_title: Optional[str] = None


class Analysis:
    """
    Unified Analysis class that orchestrates comprehensive codebase analysis.
    
    This class provides a high-level interface for performing various types of
    code analysis including structural analysis, quality metrics, dependency
    analysis, and issue detection.
    """
    
    def __init__(self, codebase: Codebase, config: Optional[AnalysisConfig] = None):
        """
        Initialize the Analysis instance.
        
        Args:
            codebase: The Codebase instance to analyze
            config: Configuration for analysis execution
        """
        self.codebase = codebase
        self.config = config or AnalysisConfig()
        self.registry = AnalysisRegistry()
        self.results: List[AnalysisResult] = []
        self._html_generator = None
        self._dashboard = None
    
    @classmethod
    def from_repo(
        cls, 
        repo_full_name: str, 
        config: Optional[AnalysisConfig] = None,
        **kwargs
    ) -> "Analysis":
        """
        Create Analysis instance from a GitHub repository.
        
        Args:
            repo_full_name: Repository name in format "owner/repo"
            config: Analysis configuration
            **kwargs: Additional arguments passed to Codebase.from_repo
            
        Returns:
            Analysis instance ready for comprehensive analysis
        """
        codebase = Codebase.from_repo(repo_full_name, **kwargs)
        return cls(codebase, config)
    
    @classmethod
    def from_path(
        cls, 
        path: Union[str, Path], 
        config: Optional[AnalysisConfig] = None,
        **kwargs
    ) -> "Analysis":
        """
        Create Analysis instance from a local repository path.
        
        Args:
            path: Path to the local repository
            config: Analysis configuration
            **kwargs: Additional arguments passed to Codebase constructor
            
        Returns:
            Analysis instance ready for comprehensive analysis
        """
        codebase = Codebase(str(path), **kwargs)
        return cls(codebase, config)
    
    def run_comprehensive_analysis(self) -> Dict[str, AnalysisResult]:
        """
        Run comprehensive analysis including all enabled analysis types.
        
        Returns:
            Dictionary mapping analysis type names to their results
        """
        results = {}
        
        print("🔍 Starting comprehensive codebase analysis...")
        
        # Run structural analysis
        if self.config.include_call_graph:
            print("  📊 Analyzing call graph...")
            results['call_graph'] = self._run_call_graph_analysis()
        
        # Run dead code analysis
        if self.config.include_dead_code:
            print("  🧹 Detecting dead code...")
            results['dead_code'] = self._run_dead_code_analysis()
        
        # Run dependency analysis
        if self.config.include_dependencies:
            print("  🔗 Analyzing dependencies...")
            results['dependencies'] = self._run_dependency_analysis()
        
        # Run metrics analysis
        if self.config.include_metrics:
            print("  📈 Computing metrics...")
            results['metrics'] = self._run_metrics_analysis()
        
        # Run function context analysis
        if self.config.include_function_context:
            print("  🎯 Analyzing function contexts...")
            results['function_context'] = self._run_function_context_analysis()
        
        # Store results
        self.results.extend(results.values())
        
        # Generate reports if requested
        if self.config.generate_html_report:
            print("  📄 Generating HTML report...")
            self._generate_html_report(results)
        
        if self.config.generate_interactive_dashboard:
            print("  🎛️ Creating interactive dashboard...")
            self._generate_dashboard(results)
        
        print("✅ Comprehensive analysis completed!")
        return results
    
    def _run_call_graph_analysis(self) -> AnalysisResult:
        """Run call graph analysis."""
        from graph_sitter.adapters.analysis.call_graph import CallGraphAnalyzer
        
        analyzer = CallGraphAnalyzer(self.codebase)
        call_graph = analyzer.build_call_graph()
        
        # Detect issues in call graph
        issues = []
        if hasattr(analyzer, 'detect_circular_dependencies'):
            circular_deps = analyzer.detect_circular_dependencies()
            for dep in circular_deps:
                issues.append({
                    'type': 'circular_dependency',
                    'severity': 'warning',
                    'description': f"Circular dependency detected: {dep}",
                    'location': dep
                })
        
        return AnalysisResult(
            analysis_type='call_graph',
            timestamp=datetime.now(),
            results={'call_graph': call_graph},
            issues=issues,
            metrics={'total_nodes': len(call_graph.nodes) if hasattr(call_graph, 'nodes') else 0},
            recommendations=self._generate_call_graph_recommendations(call_graph, issues)
        )
    
    def _run_dead_code_analysis(self) -> AnalysisResult:
        """Run dead code analysis."""
        from graph_sitter.adapters.analysis.dead_code import DeadCodeAnalyzer
        
        analyzer = DeadCodeAnalyzer(self.codebase)
        dead_code_results = analyzer.find_dead_code()
        
        # Convert dead code findings to issues
        issues = []
        for item in dead_code_results.get('dead_functions', []):
            issues.append({
                'type': 'dead_function',
                'severity': 'info',
                'description': f"Unused function: {item.get('name', 'unknown')}",
                'location': item.get('location', 'unknown'),
                'file': item.get('file', 'unknown')
            })
        
        for item in dead_code_results.get('dead_classes', []):
            issues.append({
                'type': 'dead_class',
                'severity': 'info', 
                'description': f"Unused class: {item.get('name', 'unknown')}",
                'location': item.get('location', 'unknown'),
                'file': item.get('file', 'unknown')
            })
        
        return AnalysisResult(
            analysis_type='dead_code',
            timestamp=datetime.now(),
            results=dead_code_results,
            issues=issues,
            metrics={
                'dead_functions_count': len(dead_code_results.get('dead_functions', [])),
                'dead_classes_count': len(dead_code_results.get('dead_classes', []))
            },
            recommendations=self._generate_dead_code_recommendations(dead_code_results)
        )
    
    def _run_dependency_analysis(self) -> AnalysisResult:
        """Run dependency analysis."""
        from graph_sitter.adapters.analysis.dependency_analyzer import DependencyAnalyzer
        
        analyzer = DependencyAnalyzer(self.codebase)
        dependency_results = analyzer.analyze_dependencies()
        
        # Detect dependency issues
        issues = []
        if 'circular_imports' in dependency_results:
            for circular in dependency_results['circular_imports']:
                issues.append({
                    'type': 'circular_import',
                    'severity': 'error',
                    'description': f"Circular import detected: {circular}",
                    'location': circular
                })
        
        if 'unused_imports' in dependency_results:
            for unused in dependency_results['unused_imports']:
                issues.append({
                    'type': 'unused_import',
                    'severity': 'warning',
                    'description': f"Unused import: {unused}",
                    'location': unused
                })
        
        return AnalysisResult(
            analysis_type='dependencies',
            timestamp=datetime.now(),
            results=dependency_results,
            issues=issues,
            metrics={
                'total_dependencies': len(dependency_results.get('dependencies', [])),
                'circular_imports': len(dependency_results.get('circular_imports', [])),
                'unused_imports': len(dependency_results.get('unused_imports', []))
            },
            recommendations=self._generate_dependency_recommendations(dependency_results)
        )
    
    def _run_metrics_analysis(self) -> AnalysisResult:
        """Run code metrics analysis."""
        from graph_sitter.adapters.analysis.metrics import CodebaseMetrics
        
        metrics_analyzer = CodebaseMetrics(self.codebase)
        metrics_results = metrics_analyzer.calculate_all_metrics()
        
        # Detect metric-based issues
        issues = []
        
        # Check for high complexity functions
        if 'function_metrics' in metrics_results:
            for func_metric in metrics_results['function_metrics']:
                complexity = func_metric.get('cyclomatic_complexity', 0)
                if complexity > 10:  # Threshold for high complexity
                    issues.append({
                        'type': 'high_complexity',
                        'severity': 'warning',
                        'description': f"High cyclomatic complexity ({complexity}) in function: {func_metric.get('name', 'unknown')}",
                        'location': func_metric.get('location', 'unknown'),
                        'file': func_metric.get('file', 'unknown')
                    })
        
        # Check for large classes
        if 'class_metrics' in metrics_results:
            for class_metric in metrics_results['class_metrics']:
                lines_of_code = class_metric.get('lines_of_code', 0)
                if lines_of_code > 500:  # Threshold for large classes
                    issues.append({
                        'type': 'large_class',
                        'severity': 'info',
                        'description': f"Large class ({lines_of_code} LOC): {class_metric.get('name', 'unknown')}",
                        'location': class_metric.get('location', 'unknown'),
                        'file': class_metric.get('file', 'unknown')
                    })
        
        return AnalysisResult(
            analysis_type='metrics',
            timestamp=datetime.now(),
            results=metrics_results,
            issues=issues,
            metrics=metrics_results.get('summary_metrics', {}),
            recommendations=self._generate_metrics_recommendations(metrics_results, issues)
        )
    
    def _run_function_context_analysis(self) -> AnalysisResult:
        """Run function context analysis."""
        from graph_sitter.adapters.analysis.function_context import FunctionContextAnalyzer
        
        analyzer = FunctionContextAnalyzer(self.codebase)
        context_results = analyzer.analyze_function_contexts()
        
        # Detect context-related issues
        issues = []
        
        # Check for functions with missing documentation
        if 'functions' in context_results:
            for func in context_results['functions']:
                if not func.get('has_docstring', False):
                    issues.append({
                        'type': 'missing_documentation',
                        'severity': 'info',
                        'description': f"Function missing documentation: {func.get('name', 'unknown')}",
                        'location': func.get('location', 'unknown'),
                        'file': func.get('file', 'unknown')
                    })
        
        return AnalysisResult(
            analysis_type='function_context',
            timestamp=datetime.now(),
            results=context_results,
            issues=issues,
            metrics={
                'total_functions': len(context_results.get('functions', [])),
                'documented_functions': len([f for f in context_results.get('functions', []) if f.get('has_docstring', False)])
            },
            recommendations=self._generate_function_context_recommendations(context_results)
        )
    
    def _generate_html_report(self, results: Dict[str, AnalysisResult]) -> str:
        """Generate HTML report from analysis results."""
        if not self._html_generator:
            self._html_generator = HTMLReportGenerator(self.config)
        
        output_dir = self.config.output_dir or tempfile.mkdtemp(prefix="graph_sitter_analysis_")
        report_path = self._html_generator.generate_report(results, output_dir)
        
        print(f"📄 HTML report generated: {report_path}")
        return report_path
    
    def _generate_dashboard(self, results: Dict[str, AnalysisResult]) -> str:
        """Generate interactive dashboard from analysis results."""
        if not self._dashboard:
            self._dashboard = InteractiveDashboard(self.config)
        
        output_dir = self.config.output_dir or tempfile.mkdtemp(prefix="graph_sitter_dashboard_")
        dashboard_path = self._dashboard.create_dashboard(results, output_dir)
        
        print(f"🎛️ Interactive dashboard created: {dashboard_path}")
        return dashboard_path
    
    def _generate_call_graph_recommendations(self, call_graph, issues: List[Dict]) -> List[str]:
        """Generate recommendations based on call graph analysis."""
        recommendations = []
        
        if issues:
            recommendations.append("Consider refactoring circular dependencies to improve code maintainability")
        
        # Add more call graph specific recommendations
        recommendations.append("Review function call patterns for optimization opportunities")
        
        return recommendations
    
    def _generate_dead_code_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on dead code analysis."""
        recommendations = []
        
        dead_functions = len(results.get('dead_functions', []))
        dead_classes = len(results.get('dead_classes', []))
        
        if dead_functions > 0:
            recommendations.append(f"Consider removing {dead_functions} unused functions to reduce codebase size")
        
        if dead_classes > 0:
            recommendations.append(f"Consider removing {dead_classes} unused classes to improve maintainability")
        
        return recommendations
    
    def _generate_dependency_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on dependency analysis."""
        recommendations = []
        
        circular_imports = len(results.get('circular_imports', []))
        unused_imports = len(results.get('unused_imports', []))
        
        if circular_imports > 0:
            recommendations.append("Resolve circular imports to improve code structure")
        
        if unused_imports > 0:
            recommendations.append("Remove unused imports to clean up the codebase")
        
        return recommendations
    
    def _generate_metrics_recommendations(self, results: Dict, issues: List[Dict]) -> List[str]:
        """Generate recommendations based on metrics analysis."""
        recommendations = []
        
        high_complexity_count = len([i for i in issues if i['type'] == 'high_complexity'])
        large_class_count = len([i for i in issues if i['type'] == 'large_class'])
        
        if high_complexity_count > 0:
            recommendations.append(f"Consider refactoring {high_complexity_count} high-complexity functions")
        
        if large_class_count > 0:
            recommendations.append(f"Consider breaking down {large_class_count} large classes")
        
        return recommendations
    
    def _generate_function_context_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations based on function context analysis."""
        recommendations = []
        
        functions = results.get('functions', [])
        undocumented = len([f for f in functions if not f.get('has_docstring', False)])
        
        if undocumented > 0:
            recommendations.append(f"Add documentation to {undocumented} functions")
        
        return recommendations
    
    def get_all_issues(self) -> List[Dict[str, Any]]:
        """Get all issues found across all analysis types."""
        all_issues = []
        for result in self.results:
            all_issues.extend(result.issues)
        return all_issues
    
    def get_summary_metrics(self) -> Dict[str, Any]:
        """Get summary metrics across all analysis types."""
        summary = {
            'total_issues': len(self.get_all_issues()),
            'analysis_types_run': len(self.results),
            'timestamp': datetime.now().isoformat()
        }
        
        # Aggregate metrics from all results
        for result in self.results:
            for key, value in result.metrics.items():
                summary[f"{result.analysis_type}_{key}"] = value
        
        return summary
    
    def get_recommendations(self) -> List[str]:
        """Get all recommendations from all analysis types."""
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)
        return all_recommendations


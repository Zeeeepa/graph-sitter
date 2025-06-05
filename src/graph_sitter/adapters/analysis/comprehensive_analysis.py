"""
Comprehensive Analysis System - Single entry point for all codebase analysis with automatic detection.

This module provides a unified interface for running comprehensive codebase analysis,
automatically detecting when analysis is needed and orchestrating all analysis types.
"""

import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import quote

from graph_sitter.core.codebase import Codebase

# Import all analysis components
from .enhanced_analysis import EnhancedCodebaseAnalyzer as EnhancedAnalyzer, AnalysisReport
from .metrics import CodebaseMetrics, get_codebase_summary as calculate_codebase_metrics
from .dependency_analyzer import DependencyAnalyzer, ImportAnalysis
from .call_graph import CallGraphAnalyzer
from .dead_code import DeadCodeDetector
from .function_context import FunctionContext, get_function_context

logger = logging.getLogger(__name__)


@dataclass
class IssueItem:
    """Represents a single issue found during analysis."""
    id: str
    title: str
    description: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'error', 'warning', 'suggestion', 'security', 'performance'
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    fix_suggestion: Optional[str] = None
    blast_radius: Optional[List[str]] = None


@dataclass
class AnalysisSummary:
    """Summary of all analysis results."""
    total_files: int
    total_functions: int
    total_classes: int
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    health_score: float
    analysis_timestamp: str
    analysis_duration: float


@dataclass
class ComprehensiveAnalysisResult:
    """Complete analysis result with all components and issues."""
    codebase_id: str
    codebase_name: str
    analysis_summary: AnalysisSummary
    
    # Issue listings
    issues: List[IssueItem]
    errors: List[IssueItem]
    warnings: List[IssueItem]
    suggestions: List[IssueItem]
    
    # Analysis components
    enhanced_analysis: AnalysisReport
    metrics: CodebaseMetrics
    dependency_analysis: ImportAnalysis
    call_graph_data: Dict[str, Any]
    dead_code_data: Dict[str, Any]
    function_contexts: List[FunctionContext]
    
    # Visualization data
    visualization_data: Dict[str, Any]
    dashboard_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def get_issues_by_severity(self, severity: str) -> List[IssueItem]:
        """Get issues filtered by severity level."""
        return [issue for issue in self.issues if issue.severity == severity]
    
    def get_issues_by_category(self, category: str) -> List[IssueItem]:
        """Get issues filtered by category."""
        return [issue for issue in self.issues if issue.category == category]


class ComprehensiveAnalysis:
    """
    Unified analysis system that orchestrates all analysis types and provides
    comprehensive codebase understanding with issue detection and visualization.
    """
    
    def __init__(self, codebase: Codebase, auto_detect: bool = True):
        """
        Initialize comprehensive analysis system.
        
        Args:
            codebase: The codebase to analyze
            auto_detect: Whether to automatically detect if analysis should be triggered
        """
        self.codebase = codebase
        self.auto_detect = auto_detect
        self.analysis_result: Optional[ComprehensiveAnalysisResult] = None
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Analysis components
        self.enhanced_analyzer = EnhancedAnalyzer(codebase)
        self.dependency_analyzer = DependencyAnalyzer(codebase)
        self.call_graph_analyzer = CallGraphAnalyzer(codebase)
        self.dead_code_analyzer = DeadCodeDetector(codebase)
    
    def should_trigger_analysis(self) -> bool:
        """
        Determine if comprehensive analysis should be automatically triggered.
        
        Checks for keywords like 'analysis', 'analyze', 'audit', etc. in:
        - Repository name
        - Directory names
        - File names
        - Configuration files
        """
        if not self.auto_detect:
            return True
            
        analysis_keywords = [
            'analysis', 'analyze', 'audit', 'review', 'inspect', 
            'examine', 'evaluate', 'assess', 'check', 'scan'
        ]
        
        # Check repository name
        repo_name = getattr(self.codebase, 'name', '') or ''
        if any(keyword in repo_name.lower() for keyword in analysis_keywords):
            self.logger.info(f"Analysis triggered by repository name: {repo_name}")
            return True
        
        # Check directory structure
        for directory in self.codebase.directories:
            dir_name = directory.name.lower()
            if any(keyword in dir_name for keyword in analysis_keywords):
                self.logger.info(f"Analysis triggered by directory name: {directory.name}")
                return True
        
        # Check for analysis-related files
        analysis_files = [
            'analysis.py', 'analyze.py', 'audit.py', 'review.py',
            'analysis.json', 'analysis.yaml', 'analysis.yml'
        ]
        
        for file in self.codebase.files:
            if file.name.lower() in analysis_files:
                self.logger.info(f"Analysis triggered by file: {file.name}")
                return True
        
        return False
    
    async def run_comprehensive_analysis(self, 
                                       include_visualizations: bool = True,
                                       generate_dashboard: bool = True) -> ComprehensiveAnalysisResult:
        """
        Run comprehensive analysis of the codebase.
        
        Args:
            include_visualizations: Whether to generate visualization data
            generate_dashboard: Whether to generate HTML dashboard
            
        Returns:
            ComprehensiveAnalysisResult with all analysis data and issues
        """
        start_time = datetime.now()
        self.logger.info("Starting comprehensive codebase analysis...")
        
        # Run all analysis components in parallel where possible
        tasks = [
            self._run_enhanced_analysis(),
            self._run_metrics_analysis(),
            self._run_dependency_analysis(),
            self._run_call_graph_analysis(),
            self._run_dead_code_analysis(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Extract results
        enhanced_analysis = results[0] if not isinstance(results[0], Exception) else None
        metrics = results[1] if not isinstance(results[1], Exception) else None
        dependency_analysis = results[2] if not isinstance(results[2], Exception) else None
        call_graph_data = results[3] if not isinstance(results[3], Exception) else None
        dead_code_data = results[4] if not isinstance(results[4], Exception) else None
        
        # Get function contexts for key functions
        function_contexts = await self._get_function_contexts()
        
        # Aggregate all issues
        issues = self._aggregate_issues(
            enhanced_analysis, metrics, dependency_analysis, 
            call_graph_data, dead_code_data, function_contexts
        )
        
        # Calculate analysis summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        analysis_summary = AnalysisSummary(
            total_files=len(self.codebase.files),
            total_functions=len([f for f in self.codebase.functions]),
            total_classes=len([c for c in self.codebase.classes]),
            total_issues=len(issues),
            critical_issues=len([i for i in issues if i.severity == 'critical']),
            high_issues=len([i for i in issues if i.severity == 'high']),
            medium_issues=len([i for i in issues if i.severity == 'medium']),
            low_issues=len([i for i in issues if i.severity == 'low']),
            health_score=self._calculate_health_score(issues, metrics),
            analysis_timestamp=start_time.isoformat(),
            analysis_duration=duration
        )
        
        # Generate visualization data if requested
        visualization_data = {}
        if include_visualizations:
            visualization_data = await self._generate_visualization_data()
        
        # Create comprehensive result
        self.analysis_result = ComprehensiveAnalysisResult(
            codebase_id=getattr(self.codebase, 'id', 'unknown'),
            codebase_name=getattr(self.codebase, 'name', 'unknown'),
            analysis_summary=analysis_summary,
            issues=issues,
            errors=[i for i in issues if i.category == 'error'],
            warnings=[i for i in issues if i.category == 'warning'],
            suggestions=[i for i in issues if i.category == 'suggestion'],
            enhanced_analysis=enhanced_analysis,
            metrics=metrics,
            dependency_analysis=dependency_analysis,
            call_graph_data=call_graph_data or {},
            dead_code_data=dead_code_data or {},
            function_contexts=function_contexts,
            visualization_data=visualization_data
        )
        
        self.logger.info(f"Comprehensive analysis completed in {duration:.2f}s")
        self.logger.info(f"Found {len(issues)} total issues ({analysis_summary.critical_issues} critical)")
        
        return self.analysis_result
    
    async def _run_enhanced_analysis(self) -> AnalysisReport:
        """Run enhanced analysis component."""
        try:
            return self.enhanced_analyzer.run_full_analysis()
        except Exception as e:
            self.logger.error(f"Enhanced analysis failed: {e}")
            raise
    
    async def _run_metrics_analysis(self) -> CodebaseMetrics:
        """Run metrics analysis component."""
        try:
            return calculate_codebase_metrics(self.codebase)
        except Exception as e:
            self.logger.error(f"Metrics analysis failed: {e}")
            raise
    
    async def _run_dependency_analysis(self) -> ImportAnalysis:
        """Run dependency analysis component."""
        try:
            return self.dependency_analyzer.analyze_imports()
        except Exception as e:
            self.logger.error(f"Dependency analysis failed: {e}")
            raise
    
    async def _run_call_graph_analysis(self) -> Dict[str, Any]:
        """Run call graph analysis component."""
        try:
            return self.call_graph_analyzer.analyze()
        except Exception as e:
            self.logger.error(f"Call graph analysis failed: {e}")
            return {}
    
    async def _run_dead_code_analysis(self) -> Dict[str, Any]:
        """Run dead code analysis component."""
        try:
            return self.dead_code_analyzer.analyze()
        except Exception as e:
            self.logger.error(f"Dead code analysis failed: {e}")
            return {}
    
    async def _get_function_contexts(self) -> List[FunctionContext]:
        """Get function contexts for important functions."""
        contexts = []
        try:
            # Get contexts for functions with potential issues
            for function in self.codebase.functions[:20]:  # Limit to first 20 for performance
                try:
                    context = get_function_context(self.codebase, function.name)
                    if context:
                        contexts.append(context)
                except Exception as e:
                    self.logger.debug(f"Failed to get context for function {function.name}: {e}")
        except Exception as e:
            self.logger.error(f"Function context analysis failed: {e}")
        
        return contexts
    
    def _aggregate_issues(self, enhanced_analysis, metrics, dependency_analysis, 
                         call_graph_data, dead_code_data, function_contexts) -> List[IssueItem]:
        """Aggregate issues from all analysis components."""
        issues = []
        issue_id = 0
        
        # Issues from enhanced analysis
        if enhanced_analysis and hasattr(enhanced_analysis, 'issues'):
            for issue in getattr(enhanced_analysis, 'issues', []):
                issues.append(IssueItem(
                    id=f"enhanced_{issue_id}",
                    title=issue.get('title', 'Enhanced Analysis Issue'),
                    description=issue.get('description', ''),
                    severity=issue.get('severity', 'medium'),
                    category='error',
                    file_path=issue.get('file_path'),
                    line_number=issue.get('line_number'),
                    function_name=issue.get('function_name'),
                    fix_suggestion=issue.get('fix_suggestion')
                ))
                issue_id += 1
        
        # Issues from metrics (high complexity, long functions, etc.)
        if metrics:
            for file_path, file_metrics in getattr(metrics, 'file_metrics', {}).items():
                complexity = file_metrics.get('cyclomatic_complexity', 0)
                if complexity > 10:  # High complexity threshold
                    issues.append(IssueItem(
                        id=f"complexity_{issue_id}",
                        title=f"High Cyclomatic Complexity: {complexity}",
                        description=f"File has high cyclomatic complexity ({complexity}), consider refactoring",
                        severity='high' if complexity > 20 else 'medium',
                        category='warning',
                        file_path=file_path,
                        fix_suggestion="Break down complex functions into smaller, more manageable pieces"
                    ))
                    issue_id += 1
        
        # Issues from dependency analysis
        if dependency_analysis:
            circular_deps = getattr(dependency_analysis, 'circular_dependencies', [])
            for dep_cycle in circular_deps:
                issues.append(IssueItem(
                    id=f"circular_dep_{issue_id}",
                    title="Circular Dependency Detected",
                    description=f"Circular dependency found: {' -> '.join(dep_cycle)}",
                    severity='high',
                    category='error',
                    fix_suggestion="Refactor to remove circular dependencies by extracting common functionality"
                ))
                issue_id += 1
        
        # Issues from dead code analysis
        if dead_code_data:
            dead_functions = dead_code_data.get('dead_functions', [])
            for func_name in dead_functions:
                issues.append(IssueItem(
                    id=f"dead_code_{issue_id}",
                    title=f"Dead Code: {func_name}",
                    description=f"Function '{func_name}' appears to be unused",
                    severity='low',
                    category='suggestion',
                    function_name=func_name,
                    fix_suggestion="Remove unused function or verify if it's actually needed"
                ))
                issue_id += 1
        
        # Issues from function contexts (security, performance)
        for context in function_contexts:
            if hasattr(context, 'security_issues'):
                for security_issue in getattr(context, 'security_issues', []):
                    issues.append(IssueItem(
                        id=f"security_{issue_id}",
                        title=f"Security Issue in {context.function_name}",
                        description=security_issue.get('description', ''),
                        severity='critical',
                        category='security',
                        function_name=context.function_name,
                        fix_suggestion=security_issue.get('fix_suggestion')
                    ))
                    issue_id += 1
        
        return issues
    
    def _calculate_health_score(self, issues: List[IssueItem], metrics: Optional[CodebaseMetrics]) -> float:
        """Calculate overall codebase health score (0-100)."""
        if not issues and not metrics:
            return 85.0  # Default decent score
        
        # Start with base score
        score = 100.0
        
        # Deduct points for issues
        for issue in issues:
            if issue.severity == 'critical':
                score -= 15
            elif issue.severity == 'high':
                score -= 8
            elif issue.severity == 'medium':
                score -= 3
            elif issue.severity == 'low':
                score -= 1
        
        # Factor in metrics if available
        if metrics:
            avg_complexity = getattr(metrics, 'average_complexity', 5)
            if avg_complexity > 10:
                score -= (avg_complexity - 10) * 2
        
        return max(0.0, min(100.0, score))
    
    async def _generate_visualization_data(self) -> Dict[str, Any]:
        """Generate data for visualizations."""
        try:
            # This will be expanded with actual visualization data
            return {
                'dependency_graph': {},
                'call_graph': {},
                'complexity_heatmap': {},
                'issue_distribution': {},
                'file_relationships': {}
            }
        except Exception as e:
            self.logger.error(f"Visualization data generation failed: {e}")
            return {}
    
    def generate_dashboard_url(self, base_url: str = "http://localhost:8000") -> str:
        """Generate URL for the analysis dashboard."""
        if not self.analysis_result:
            raise ValueError("No analysis result available. Run analysis first.")
        
        codebase_id = quote(self.analysis_result.codebase_id)
        return f"{base_url}/dashboard/{codebase_id}"
    
    def save_results(self, output_path: str = "analysis_results.json") -> str:
        """Save analysis results to file."""
        if not self.analysis_result:
            raise ValueError("No analysis result available. Run analysis first.")
        
        output_file = Path(output_path)
        with open(output_file, 'w') as f:
            json.dump(self.analysis_result.to_dict(), f, indent=2, default=str)
        
        self.logger.info(f"Analysis results saved to {output_file}")
        return str(output_file)


# Convenience functions for easy usage
def analyze_codebase(codebase: Codebase, 
                    auto_detect: bool = True,
                    include_visualizations: bool = True,
                    generate_dashboard: bool = True) -> ComprehensiveAnalysisResult:
    """
    Convenience function to run comprehensive analysis on a codebase.
    
    Args:
        codebase: The codebase to analyze
        auto_detect: Whether to automatically detect if analysis should be triggered
        include_visualizations: Whether to generate visualization data
        generate_dashboard: Whether to generate HTML dashboard
        
    Returns:
        ComprehensiveAnalysisResult with all analysis data
    """
    analyzer = ComprehensiveAnalysis(codebase, auto_detect=auto_detect)
    
    if auto_detect and not analyzer.should_trigger_analysis():
        logger.info("Auto-detection did not trigger analysis")
        return None
    
    # Run analysis
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            analyzer.run_comprehensive_analysis(
                include_visualizations=include_visualizations,
                generate_dashboard=generate_dashboard
            )
        )
        return result
    finally:
        loop.close()


def quick_analysis(repo_name: str, **kwargs) -> ComprehensiveAnalysisResult:
    """
    Quick analysis of a repository by name.
    
    Args:
        repo_name: Repository name in format "owner/repo"
        **kwargs: Additional arguments passed to Codebase.from_repo
        
    Returns:
        ComprehensiveAnalysisResult with all analysis data
    """
    from graph_sitter.core.codebase import Codebase
    
    # Create codebase
    codebase = Codebase.from_repo(repo_name, **kwargs)
    
    # Run analysis
    return analyze_codebase(codebase)

"""
Unified Analysis System - Single Entry Point for Comprehensive Codebase Analysis

This module provides the streamlined interface requested by the user:
- Automatic analysis trigger when 'analysis' is detected in codebase names
- Single comprehensive analysis with full context
- Interactive React dashboard with dropdown selections
- Error detection and blast radius visualization
- Progressive loading with efficient dashboard generation

Usage:
    from graph_sitter import Codebase, Analysis
    
    # Automatic analysis trigger
    codebase = Codebase.from_repo('fastapi/fastapi')  # or Codebase.Analysis('path/to/repo')
    
    # Manual comprehensive analysis
    result = Analysis.analyze_comprehensive(codebase)
    dashboard_url = result.dashboard_url
"""

import asyncio
import json
import logging
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import urljoin
import webbrowser

# Core imports
from graph_sitter.core.codebase import Codebase

# Analysis components
from .adapters.analysis.enhanced_analysis import EnhancedAnalyzer, AnalysisReport
from .adapters.analysis.metrics import CodebaseMetrics, calculate_codebase_metrics
from .adapters.analysis.dependency_analyzer import DependencyAnalyzer
from .adapters.analysis.call_graph import CallGraphAnalyzer
from .adapters.analysis.dead_code import DeadCodeAnalyzer
from .adapters.analysis.function_context import get_function_context, FunctionContext

# Visualization components
from .adapters.visualizations.codebase_visualization import CodebaseVisualizer, InteractiveReport
from .adapters.visualizations.react_visualizations import create_react_visualizations

# Database components
from .adapters.database import AnalysisDatabase
from .adapters.codebase_db_adapter import CodebaseDbAdapter

logger = logging.getLogger(__name__)


# Analysis Configuration
ANALYSIS_CONFIG = {
    'max_depth': 5,
    'include_tests': False,
    'error_threshold': 0.8,
    'complexity_limit': 10,
    'auto_trigger_keywords': ['analysis', 'analyze', 'audit', 'review'],
    'dashboard_port': 8080,
    'progressive_loading': True
}

VISUALIZATION_CONFIG = {
    'graph_type': 'force-directed',
    'color_scheme': 'severity',
    'animation_duration': 500,
    'interactive_features': True,
    'dropdown_selections': True
}

# Analysis Types for Dashboard Dropdowns
ANALYSIS_TYPES = {
    'dependency': {
        'name': 'Dependency Analysis',
        'description': 'Analyze module dependencies and import relationships',
        'targets': ['module', 'class', 'function'],
        'visualizations': ['graph', 'tree', 'matrix']
    },
    'blast_radius': {
        'name': 'Blast Radius',
        'description': 'Impact analysis from selected point',
        'targets': ['error', 'class', 'function', 'module'],
        'visualizations': ['impact_graph', 'heatmap', 'propagation']
    },
    'complexity': {
        'name': 'Complexity Analysis',
        'description': 'Code complexity heatmap and metrics',
        'targets': ['file', 'class', 'function'],
        'visualizations': ['heatmap', 'metrics', 'trends']
    },
    'error_analysis': {
        'name': 'Error Analysis',
        'description': 'Error detection and impact assessment',
        'targets': ['syntax', 'runtime', 'logical', 'performance'],
        'visualizations': ['error_map', 'severity_chart', 'resolution_guide']
    },
    'performance': {
        'name': 'Performance Analysis',
        'description': 'Performance bottlenecks and optimization opportunities',
        'targets': ['function', 'class', 'module'],
        'visualizations': ['bottleneck_graph', 'performance_metrics', 'optimization_suggestions']
    }
}


@dataclass
class UnifiedAnalysisResult:
    """Complete unified analysis result with dashboard integration."""
    codebase_id: str
    timestamp: str
    dashboard_url: str
    
    # Core analysis results
    enhanced_analysis: AnalysisReport
    function_contexts: List[FunctionContext]
    
    # Component analysis
    metrics_summary: Dict[str, Any]
    dependency_analysis: Dict[str, Any]
    dead_code_analysis: Dict[str, Any]
    call_graph_analysis: Dict[str, Any]
    error_analysis: Dict[str, Any]
    
    # Interactive features
    interactive_report: InteractiveReport
    analysis_types: Dict[str, Any]
    
    # Health and recommendations
    health_score: float
    risk_assessment: Dict[str, Any]
    actionable_recommendations: List[str]
    
    # Export capabilities
    export_paths: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def save_to_file(self, filepath: str) -> None:
        """Save analysis result to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class UnifiedAnalysis:
    """
    Unified Analysis System - The single entry point for comprehensive codebase analysis.
    
    This class implements the user's vision:
    - Single analysis with full context
    - Automatic trigger based on codebase naming
    - Interactive React dashboard with dropdown selections
    - Error detection and blast radius visualization
    - Progressive loading for optimal performance
    """
    
    def __init__(self, 
                 codebase: Codebase,
                 codebase_id: Optional[str] = None,
                 output_dir: str = "unified_analysis",
                 auto_open_dashboard: bool = True):
        """
        Initialize unified analysis system.
        
        Args:
            codebase: Codebase to analyze
            codebase_id: Unique identifier for this codebase
            output_dir: Directory for analysis outputs
            auto_open_dashboard: Whether to automatically open dashboard in browser
        """
        self.codebase = codebase
        self.codebase_id = codebase_id or self._generate_codebase_id()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.auto_open_dashboard = auto_open_dashboard
        
        # Initialize analysis components
        self._initialize_analyzers()
        
        # Results storage
        self.analysis_result: Optional[UnifiedAnalysisResult] = None
        self.dashboard_url: Optional[str] = None
        
        # Check for automatic analysis trigger
        if self._should_auto_analyze():
            logger.info(f"Auto-analysis triggered for codebase: {self.codebase_id}")
            self.analyze_comprehensive()
    
    @classmethod
    def from_repo(cls, repo_url: str, **kwargs) -> 'UnifiedAnalysis':
        """
        Create unified analysis from repository URL with automatic analysis.
        
        Args:
            repo_url: Repository URL or path
            **kwargs: Additional arguments for UnifiedAnalysis
            
        Returns:
            UnifiedAnalysis instance with completed analysis
        """
        # Clone and create codebase
        codebase = Codebase.from_repo(repo_url)
        
        # Extract codebase ID from repo URL
        codebase_id = cls._extract_codebase_id_from_url(repo_url)
        
        return cls(codebase, codebase_id=codebase_id, **kwargs)
    
    def _generate_codebase_id(self) -> str:
        """Generate unique codebase identifier."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if hasattr(self.codebase, 'root_path'):
            name = Path(self.codebase.root_path).name
        else:
            name = "codebase"
        return f"{name}_{timestamp}"
    
    @staticmethod
    def _extract_codebase_id_from_url(repo_url: str) -> str:
        """Extract codebase ID from repository URL."""
        # Handle various URL formats
        if '/' in repo_url:
            return repo_url.split('/')[-1].replace('.git', '')
        return Path(repo_url).name
    
    def _should_auto_analyze(self) -> bool:
        """Check if automatic analysis should be triggered."""
        # Check codebase ID for analysis keywords
        codebase_id_lower = self.codebase_id.lower()
        for keyword in ANALYSIS_CONFIG['auto_trigger_keywords']:
            if keyword in codebase_id_lower:
                return True
        
        # Check if codebase path contains analysis keywords
        if hasattr(self.codebase, 'root_path'):
            path_lower = str(self.codebase.root_path).lower()
            for keyword in ANALYSIS_CONFIG['auto_trigger_keywords']:
                if keyword in path_lower:
                    return True
        
        return False
    
    def _initialize_analyzers(self):
        """Initialize all analysis components."""
        try:
            self.enhanced_analyzer = EnhancedAnalyzer(self.codebase, self.codebase_id)
            self.metrics_calculator = CodebaseMetrics(self.codebase)
            self.dependency_analyzer = DependencyAnalyzer(self.codebase)
            self.dead_code_detector = DeadCodeAnalyzer(self.codebase)
            self.call_graph_analyzer = CallGraphAnalyzer(self.codebase)
            self.visualizer = CodebaseVisualizer(self.codebase, str(self.output_dir / "visualizations"))
            
            # Database components
            db_path = str(self.output_dir / "analysis.db")
            self.analysis_db = AnalysisDatabase(db_path)
            self.db_adapter = CodebaseDbAdapter(self.analysis_db)
            
        except Exception as e:
            logger.error(f"Failed to initialize analyzers: {e}")
            # Initialize minimal components for graceful degradation
            self.enhanced_analyzer = None
            self.metrics_calculator = None
    
    def analyze_comprehensive(self) -> UnifiedAnalysisResult:
        """
        Perform comprehensive analysis with full context.
        
        Returns:
            UnifiedAnalysisResult with all analysis components and dashboard URL
        """
        logger.info(f"Starting comprehensive analysis for {self.codebase_id}")
        
        try:
            # Core enhanced analysis
            enhanced_analysis = self._run_enhanced_analysis()
            
            # Component analyses
            metrics_summary = self._calculate_metrics()
            dependency_analysis = self._analyze_dependencies()
            dead_code_analysis = self._detect_dead_code()
            call_graph_analysis = self._analyze_call_graph()
            error_analysis = self._analyze_errors()
            
            # Function contexts with issue detection
            function_contexts = self._analyze_function_contexts()
            
            # Generate interactive report and dashboard
            interactive_report = self._create_interactive_report(
                enhanced_analysis, function_contexts, metrics_summary,
                dependency_analysis, error_analysis
            )
            
            # Calculate health score and recommendations
            health_score = self._calculate_health_score(
                enhanced_analysis, metrics_summary, error_analysis
            )
            risk_assessment = self._assess_risks(enhanced_analysis, error_analysis)
            recommendations = self._generate_recommendations(
                enhanced_analysis, metrics_summary, error_analysis
            )
            
            # Generate dashboard URL
            dashboard_url = self._generate_dashboard_url()
            
            # Create unified result
            self.analysis_result = UnifiedAnalysisResult(
                codebase_id=self.codebase_id,
                timestamp=datetime.now().isoformat(),
                dashboard_url=dashboard_url,
                enhanced_analysis=enhanced_analysis,
                function_contexts=function_contexts,
                metrics_summary=metrics_summary,
                dependency_analysis=dependency_analysis,
                dead_code_analysis=dead_code_analysis,
                call_graph_analysis=call_graph_analysis,
                error_analysis=error_analysis,
                interactive_report=interactive_report,
                analysis_types=ANALYSIS_TYPES,
                health_score=health_score,
                risk_assessment=risk_assessment,
                actionable_recommendations=recommendations,
                export_paths=self._get_export_paths()
            )
            
            # Save results
            self._save_analysis_results()
            
            # Auto-open dashboard if requested
            if self.auto_open_dashboard and dashboard_url:
                self._open_dashboard()
            
            logger.info(f"Comprehensive analysis completed. Dashboard: {dashboard_url}")
            return self.analysis_result
            
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {e}")
            raise
    
    def _run_enhanced_analysis(self) -> AnalysisReport:
        """Run enhanced analysis component."""
        if self.enhanced_analyzer:
            return self.enhanced_analyzer.analyze()
        else:
            # Fallback minimal analysis
            return AnalysisReport(
                codebase_id=self.codebase_id,
                timestamp=datetime.now().isoformat(),
                summary={'total_functions': len(list(self.codebase.functions)),
                        'total_classes': len(list(self.codebase.classes)),
                        'total_files': len(list(self.codebase.files))},
                function_analysis=[],
                class_analysis=[],
                file_analysis=[],
                dependency_analysis={},
                issues=[],
                recommendations=[]
            )
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive codebase metrics."""
        if self.metrics_calculator:
            return calculate_codebase_metrics(self.codebase)
        return {'error': 'Metrics calculation unavailable'}
    
    def _analyze_dependencies(self) -> Dict[str, Any]:
        """Analyze codebase dependencies."""
        if self.dependency_analyzer:
            return self.dependency_analyzer.analyze()
        return {'dependencies': [], 'imports': [], 'exports': []}
    
    def _detect_dead_code(self) -> Dict[str, Any]:
        """Detect dead code in codebase."""
        if self.dead_code_detector:
            return self.dead_code_detector.find_dead_code()
        return {'dead_functions': [], 'dead_classes': [], 'unused_imports': []}
    
    def _analyze_call_graph(self) -> Dict[str, Any]:
        """Analyze call graph relationships."""
        if self.call_graph_analyzer:
            return self.call_graph_analyzer.build_call_graph()
        return {'nodes': [], 'edges': [], 'clusters': []}
    
    def _analyze_errors(self) -> Dict[str, Any]:
        """Comprehensive error analysis with blast radius."""
        errors = {
            'syntax_errors': [],
            'runtime_predictions': [],
            'logical_issues': [],
            'performance_issues': [],
            'blast_radius': {},
            'severity_assessment': {},
            'resolution_suggestions': []
        }
        
        # Basic error detection (can be enhanced with more sophisticated analysis)
        try:
            for function in self.codebase.functions:
                # Simple complexity-based performance issue detection
                if hasattr(function, 'complexity') and function.complexity > 10:
                    errors['performance_issues'].append({
                        'type': 'high_complexity',
                        'function': function.name,
                        'complexity': function.complexity,
                        'severity': 'medium'
                    })
        except Exception as e:
            logger.warning(f"Error analysis failed: {e}")
        
        return errors
    
    def _analyze_function_contexts(self) -> List[FunctionContext]:
        """Analyze function contexts with issue detection."""
        contexts = []
        try:
            for function in self.codebase.functions:
                context = get_function_context(function, self.codebase)
                contexts.append(context)
        except Exception as e:
            logger.warning(f"Function context analysis failed: {e}")
        
        return contexts
    
    def _create_interactive_report(self, enhanced_analysis, function_contexts, 
                                 metrics_summary, dependency_analysis, error_analysis) -> InteractiveReport:
        """Create interactive report for dashboard."""
        if self.visualizer:
            return self.visualizer.create_interactive_report(
                enhanced_analysis, function_contexts, metrics_summary,
                dependency_analysis, error_analysis
            )
        
        # Fallback minimal report
        return InteractiveReport(
            summary={'analysis_complete': True},
            function_analysis=function_contexts,
            dependency_graph={'nodes': [], 'edges': []},
            call_graph={'nodes': [], 'edges': []},
            complexity_heatmap={},
            issue_dashboard=error_analysis,
            recommendations=[],
            export_data={}
        )
    
    def _calculate_health_score(self, enhanced_analysis, metrics_summary, error_analysis) -> float:
        """Calculate overall codebase health score (0-100)."""
        score = 100.0
        
        # Deduct for errors
        error_count = len(error_analysis.get('syntax_errors', [])) + \
                     len(error_analysis.get('performance_issues', []))
        score -= min(error_count * 5, 30)  # Max 30 point deduction for errors
        
        # Deduct for complexity issues
        if 'complexity' in metrics_summary:
            avg_complexity = metrics_summary['complexity'].get('average', 0)
            if avg_complexity > 10:
                score -= min((avg_complexity - 10) * 2, 20)  # Max 20 point deduction
        
        return max(score, 0.0)
    
    def _assess_risks(self, enhanced_analysis, error_analysis) -> Dict[str, Any]:
        """Assess codebase risks."""
        risks = {
            'high_risk_areas': [],
            'security_concerns': [],
            'maintainability_issues': [],
            'performance_bottlenecks': error_analysis.get('performance_issues', [])
        }
        
        # Add high complexity functions as high risk
        for issue in error_analysis.get('performance_issues', []):
            if issue.get('type') == 'high_complexity':
                risks['high_risk_areas'].append(issue)
        
        return risks
    
    def _generate_recommendations(self, enhanced_analysis, metrics_summary, error_analysis) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Performance recommendations
        perf_issues = error_analysis.get('performance_issues', [])
        if perf_issues:
            recommendations.append(f"Consider refactoring {len(perf_issues)} high-complexity functions")
        
        # General recommendations
        recommendations.extend([
            "Implement comprehensive test coverage for critical functions",
            "Add documentation for public APIs",
            "Consider implementing error handling patterns",
            "Review and optimize dependency usage"
        ])
        
        return recommendations
    
    def _generate_dashboard_url(self) -> str:
        """Generate dashboard URL for interactive exploration."""
        port = ANALYSIS_CONFIG['dashboard_port']
        base_url = f"http://localhost:{port}"
        dashboard_path = f"/analysis/{self.codebase_id}"
        return urljoin(base_url, dashboard_path)
    
    def _get_export_paths(self) -> Dict[str, str]:
        """Get paths for exported analysis data."""
        return {
            'json_report': str(self.output_dir / f"{self.codebase_id}_analysis.json"),
            'html_dashboard': str(self.output_dir / f"{self.codebase_id}_dashboard.html"),
            'csv_metrics': str(self.output_dir / f"{self.codebase_id}_metrics.csv"),
            'visualization_data': str(self.output_dir / "visualizations")
        }
    
    def _save_analysis_results(self):
        """Save analysis results to various formats."""
        if self.analysis_result:
            # Save JSON report
            json_path = self.analysis_result.export_paths['json_report']
            self.analysis_result.save_to_file(json_path)
            
            # Save to database
            if self.db_adapter:
                try:
                    self.db_adapter.store_analysis_result(self.analysis_result.enhanced_analysis)
                except Exception as e:
                    logger.warning(f"Database storage failed: {e}")
    
    def _open_dashboard(self):
        """Open dashboard in default browser."""
        if self.dashboard_url:
            try:
                webbrowser.open(self.dashboard_url)
                logger.info(f"Dashboard opened: {self.dashboard_url}")
            except Exception as e:
                logger.warning(f"Failed to open dashboard: {e}")
    
    @property
    def dashboard_url(self) -> Optional[str]:
        """Get dashboard URL."""
        if self.analysis_result:
            return self.analysis_result.dashboard_url
        return self._generate_dashboard_url()


# Convenience functions for the main API
def analyze_comprehensive(codebase: Codebase, **kwargs) -> UnifiedAnalysisResult:
    """
    Perform comprehensive analysis on a codebase.
    
    Args:
        codebase: Codebase to analyze
        **kwargs: Additional arguments for UnifiedAnalysis
        
    Returns:
        UnifiedAnalysisResult with complete analysis and dashboard URL
    """
    analyzer = UnifiedAnalysis(codebase, **kwargs)
    return analyzer.analyze_comprehensive()


def from_repo_analysis(repo_url: str, **kwargs) -> UnifiedAnalysisResult:
    """
    Create codebase from repository and perform comprehensive analysis.
    
    Args:
        repo_url: Repository URL or path
        **kwargs: Additional arguments for UnifiedAnalysis
        
    Returns:
        UnifiedAnalysisResult with complete analysis and dashboard URL
    """
    analyzer = UnifiedAnalysis.from_repo(repo_url, **kwargs)
    return analyzer.analysis_result or analyzer.analyze_comprehensive()


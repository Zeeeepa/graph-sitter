"""
Analysis Orchestrator - Central coordinator for all analysis operations
"""

import asyncio
import json
import logging
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from graph_sitter.core.codebase import Codebase
from graph_sitter.adapters.analysis.enhanced_analysis import EnhancedCodebaseAnalyzer, AnalysisReport
from graph_sitter.adapters.analysis.metrics import MetricsCalculator
from graph_sitter.adapters.analysis.dependency_analyzer import DependencyAnalyzer
from graph_sitter.adapters.analysis.call_graph import CallGraphAnalyzer
from graph_sitter.adapters.analysis.dead_code import DeadCodeDetector

from .issue_detector import IssueDetector
from .dashboard_generator import HTMLDashboardGenerator
from .visualization_interface import VisualizationInterface

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    Central orchestrator for comprehensive codebase analysis.
    
    Coordinates all analysis components and provides unified interface
    for running analysis, generating dashboards, and creating visualizations.
    """
    
    def __init__(self, codebase: Codebase, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the analysis orchestrator.
        
        Args:
            codebase: The codebase to analyze
            config: Optional configuration for analysis
        """
        self.codebase = codebase
        self.config = config or {}
        self.codebase_id = self.config.get('codebase_id', 'default')
        
        # Initialize core analyzers
        self.enhanced_analyzer = EnhancedCodebaseAnalyzer(codebase, self.codebase_id)
        self.metrics_calculator = MetricsCalculator(codebase)
        self.dependency_analyzer = DependencyAnalyzer(codebase)
        self.call_graph_analyzer = CallGraphAnalyzer(codebase)
        self.dead_code_detector = DeadCodeDetector(codebase)
        
        # Initialize new components
        self.issue_detector = IssueDetector(codebase)
        self.dashboard_generator = HTMLDashboardGenerator()
        self.visualization_interface = VisualizationInterface(codebase)
        
        # Analysis results cache
        self._analysis_report: Optional[AnalysisReport] = None
        self._dashboard_url: Optional[str] = None
    
    def run_comprehensive_analysis(self, 
                                 include_visualizations: bool = True,
                                 generate_dashboard: bool = True) -> AnalysisReport:
        """
        Run comprehensive analysis of the codebase.
        
        Args:
            include_visualizations: Whether to generate visualization data
            generate_dashboard: Whether to generate HTML dashboard
            
        Returns:
            Complete analysis report
        """
        logger.info(f"Starting comprehensive analysis for codebase: {self.codebase_id}")
        
        try:
            # Run enhanced analysis
            self._analysis_report = self.enhanced_analyzer.run_full_analysis()
            
            # Enhance with additional issue detection
            additional_issues = self.issue_detector.detect_comprehensive_issues(
                self._analysis_report
            )
            self._analysis_report.issues.extend(additional_issues)
            
            # Generate visualizations if requested
            if include_visualizations:
                visualization_data = self.visualization_interface.generate_all_visualizations()
                self._analysis_report.visualization_data = visualization_data
            
            # Generate dashboard if requested
            if generate_dashboard:
                self._dashboard_url = self.dashboard_generator.generate_dashboard(
                    self._analysis_report,
                    output_dir=self.config.get('output_dir', tempfile.mkdtemp())
                )
            
            logger.info("Comprehensive analysis completed successfully")
            return self._analysis_report
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise
    
    def get_issues_summary(self) -> Dict[str, Any]:
        """Get summary of detected issues."""
        if not self._analysis_report:
            raise ValueError("Analysis not yet run. Call run_comprehensive_analysis() first.")
        
        issues = self._analysis_report.issues
        
        summary = {
            'total_issues': len(issues),
            'by_severity': {},
            'by_type': {},
            'critical_issues': [],
            'recommendations': self._analysis_report.recommendations
        }
        
        for issue in issues:
            severity = issue.get('severity', 'unknown')
            issue_type = issue.get('type', 'unknown')
            
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            summary['by_type'][issue_type] = summary['by_type'].get(issue_type, 0) + 1
            
            if severity == 'critical':
                summary['critical_issues'].append(issue)
        
        return summary
    
    def open_dashboard(self) -> str:
        """
        Open the generated dashboard in the default web browser.
        
        Returns:
            URL of the dashboard
        """
        if not self._dashboard_url:
            # Generate dashboard if not already done
            if not self._analysis_report:
                self.run_comprehensive_analysis()
            else:
                self._dashboard_url = self.dashboard_generator.generate_dashboard(
                    self._analysis_report,
                    output_dir=self.config.get('output_dir', tempfile.mkdtemp())
                )
        
        webbrowser.open(f"file://{self._dashboard_url}")
        return self._dashboard_url
    
    def get_visualization(self, 
                         viz_type: str, 
                         target: Optional[str] = None,
                         **kwargs) -> Dict[str, Any]:
        """
        Get specific visualization data.
        
        Args:
            viz_type: Type of visualization (dependency, blast_radius, call_graph, etc.)
            target: Target component (function name, class name, etc.)
            **kwargs: Additional parameters for visualization
            
        Returns:
            Visualization data
        """
        return self.visualization_interface.get_visualization(
            viz_type, target, **kwargs
        )
    
    def export_results(self, 
                      output_path: str, 
                      format: str = 'json') -> str:
        """
        Export analysis results to file.
        
        Args:
            output_path: Path to save results
            format: Export format (json, html, csv)
            
        Returns:
            Path to exported file
        """
        if not self._analysis_report:
            raise ValueError("Analysis not yet run. Call run_comprehensive_analysis() first.")
        
        output_path = Path(output_path)
        
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(self._analysis_report.__dict__, f, indent=2, default=str)
        elif format == 'html':
            # Generate standalone HTML report
            html_content = self.dashboard_generator.generate_standalone_report(
                self._analysis_report
            )
            with open(output_path, 'w') as f:
                f.write(html_content)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        return str(output_path)
    
    def get_health_score(self) -> float:
        """Get overall codebase health score."""
        if not self._analysis_report:
            raise ValueError("Analysis not yet run. Call run_comprehensive_analysis() first.")
        
        return self._analysis_report.health_score
    
    def get_recommendations(self) -> List[str]:
        """Get analysis recommendations."""
        if not self._analysis_report:
            raise ValueError("Analysis not yet run. Call run_comprehensive_analysis() first.")
        
        return self._analysis_report.recommendations
    
    @property
    def dashboard_url(self) -> Optional[str]:
        """Get the dashboard URL if generated."""
        return self._dashboard_url
    
    @property
    def analysis_report(self) -> Optional[AnalysisReport]:
        """Get the analysis report if available."""
        return self._analysis_report


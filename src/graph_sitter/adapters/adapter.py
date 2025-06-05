"""
Unified Adapter for Graph-Sitter.

This module provides a unified interface to all graph-sitter adapters including
analysis, visualization, codemod, and reporting capabilities. It serves as the
main entry point for all adapter functionality.
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# Import analysis components
from graph_sitter.adapters.analysis import (
    BaseAnalyzer,
    AnalysisRegistry,
    AnalysisType,
    AnalysisResult,
    get_registry,
    run_analysis,
    list_analyzers,
    
    # Specific analyzers
    CallGraphAnalyzer,
    DeadCodeAnalyzer,
    DependencyAnalyzer,
    CodebaseMetrics,
    FunctionContextAnalyzer,
    EnhancedAnalyzer,
)

# Import visualization components
try:
    from graph_sitter.adapters.visualizations import (
        CodebaseVisualizer,
        CallGraphVisualizer,
        DependencyVisualizer,
        MetricsVisualizer,
    )
except ImportError:
    # Fallback if visualization modules don't exist yet
    CodebaseVisualizer = None
    CallGraphVisualizer = None
    DependencyVisualizer = None
    MetricsVisualizer = None

# Import reporting components
from graph_sitter.adapters.reports import HTMLReportGenerator

# Import codemod components (if available)
try:
    from graph_sitter.adapters.codemods import (
        CodemodEngine,
        BaseCodemod,
    )
except ImportError:
    CodemodEngine = None
    BaseCodemod = None

# Import database components (if available)
try:
    from graph_sitter.adapters.database import CodebaseDBAdapter
except ImportError:
    CodebaseDBAdapter = None

from graph_sitter.core.codebase import Codebase
from graph_sitter.core.analysis import Analysis, AnalysisConfig


class UnifiedAnalyzer:
    """
    Unified analyzer that orchestrates all analysis, visualization, and reporting.
    
    This class provides a high-level interface for performing comprehensive
    codebase analysis with integrated reporting and visualization capabilities.
    """
    
    def __init__(self, codebase: Codebase, config: Optional[AnalysisConfig] = None):
        """
        Initialize the unified analyzer.
        
        Args:
            codebase: The codebase to analyze
            config: Configuration for analysis
        """
        self.codebase = codebase
        self.config = config or AnalysisConfig()
        self.registry = get_registry()
        self.results: Dict[str, AnalysisResult] = {}
        
        # Initialize components
        self._html_generator = None
        self._visualizer = None
        self._db_adapter = None
    
    def run_comprehensive_analysis(self) -> Dict[str, AnalysisResult]:
        """
        Run comprehensive analysis using all available analyzers.
        
        Returns:
            Dictionary mapping analyzer names to their results
        """
        print("🔍 Starting comprehensive analysis...")
        
        # Get all enabled analyzers
        analyzers = self.registry.list_analyzers(enabled_only=True)
        
        results = {}
        for analyzer_info in analyzers:
            print(f"  📊 Running {analyzer_info.name} analysis...")
            
            try:
                result = self.registry.run_analysis(
                    analyzer_info.name,
                    self.codebase,
                    self.config.__dict__
                )
                
                if result:
                    results[analyzer_info.name] = result
                    print(f"    ✅ {analyzer_info.name} completed")
                else:
                    print(f"    ❌ {analyzer_info.name} failed")
                    
            except Exception as e:
                print(f"    ❌ {analyzer_info.name} error: {e}")
        
        self.results = results
        print(f"✅ Comprehensive analysis completed! ({len(results)} analyzers)")
        return results
    
    def run_specific_analysis(
        self,
        analysis_types: List[Union[str, AnalysisType]]
    ) -> Dict[str, AnalysisResult]:
        """
        Run specific types of analysis.
        
        Args:
            analysis_types: List of analysis types to run
            
        Returns:
            Dictionary mapping analyzer names to their results
        """
        results = {}
        
        for analysis_type in analysis_types:
            if isinstance(analysis_type, str):
                # Find analyzer by name
                analyzer_info = self.registry.get_analyzer(analysis_type)
                if analyzer_info:
                    result = self.registry.run_analysis(
                        analysis_type,
                        self.codebase,
                        self.config.__dict__
                    )
                    if result:
                        results[analysis_type] = result
            else:
                # Find analyzers by type
                analyzers = self.registry.list_analyzers(
                    analysis_type=analysis_type,
                    enabled_only=True
                )
                
                for analyzer_info in analyzers:
                    result = self.registry.run_analysis(
                        analyzer_info.name,
                        self.codebase,
                        self.config.__dict__
                    )
                    if result:
                        results[analyzer_info.name] = result
        
        self.results.update(results)
        return results
    
    def generate_html_report(
        self,
        output_dir: str,
        title: Optional[str] = None
    ) -> str:
        """
        Generate HTML report from analysis results.
        
        Args:
            output_dir: Directory to save the report
            title: Custom title for the report
            
        Returns:
            Path to the generated HTML report
        """
        if not self._html_generator:
            self._html_generator = HTMLReportGenerator(self.config)
        
        return self._html_generator.generate_report(
            self.results,
            output_dir,
            title
        )
    
    def create_visualizations(
        self,
        output_dir: str,
        visualization_types: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Create visualizations from analysis results.
        
        Args:
            output_dir: Directory to save visualizations
            visualization_types: Types of visualizations to create
            
        Returns:
            Dictionary mapping visualization types to file paths
        """
        if not CodebaseVisualizer:
            print("⚠️ Visualization components not available")
            return {}
        
        if not self._visualizer:
            self._visualizer = CodebaseVisualizer(self.codebase)
        
        visualizations = {}
        
        # Default visualization types if none specified
        if not visualization_types:
            visualization_types = [
                'call_graph',
                'dependency_graph',
                'metrics_dashboard',
                'issue_heatmap'
            ]
        
        for viz_type in visualization_types:
            try:
                viz_path = self._visualizer.create_visualization(
                    viz_type,
                    self.results,
                    output_dir
                )
                visualizations[viz_type] = viz_path
                print(f"📊 Created {viz_type} visualization: {viz_path}")
            except Exception as e:
                print(f"❌ Failed to create {viz_type} visualization: {e}")
        
        return visualizations
    
    def save_to_database(
        self,
        db_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save analysis results to database.
        
        Args:
            db_config: Database configuration
            
        Returns:
            True if successful, False otherwise
        """
        if not CodebaseDBAdapter:
            print("⚠️ Database adapter not available")
            return False
        
        if not self._db_adapter:
            self._db_adapter = CodebaseDBAdapter(db_config)
        
        try:
            self._db_adapter.save_analysis_results(
                self.codebase,
                self.results
            )
            print("💾 Analysis results saved to database")
            return True
        except Exception as e:
            print(f"❌ Failed to save to database: {e}")
            return False
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of analysis results.
        
        Returns:
            Summary dictionary with key metrics and statistics
        """
        if not self.results:
            return {'message': 'No analysis results available'}
        
        total_issues = 0
        issues_by_severity = {'error': 0, 'warning': 0, 'info': 0}
        total_metrics = {}
        all_recommendations = []
        
        for analyzer_name, result in self.results.items():
            # Count issues
            total_issues += len(result.issues)
            
            for issue in result.issues:
                severity = issue.severity.value
                if severity in issues_by_severity:
                    issues_by_severity[severity] += 1
            
            # Collect metrics
            for metric in result.metrics:
                total_metrics[f"{analyzer_name}_{metric.name}"] = metric.value
            
            # Collect recommendations
            all_recommendations.extend(result.recommendations)
        
        return {
            'analyzers_run': len(self.results),
            'total_issues': total_issues,
            'issues_by_severity': issues_by_severity,
            'total_metrics': len(total_metrics),
            'metrics': total_metrics,
            'total_recommendations': len(all_recommendations),
            'recommendations': all_recommendations[:10],  # Top 10
            'analysis_types': [result.analysis_type.value for result in self.results.values()]
        }


class InteractiveDashboard:
    """
    Interactive dashboard for exploring analysis results.
    
    This class provides an interactive web-based dashboard for exploring
    codebase analysis results with filtering, sorting, and drill-down capabilities.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the interactive dashboard.
        
        Args:
            config: Configuration for the dashboard
        """
        self.config = config or AnalysisConfig()
    
    def create_dashboard(
        self,
        results: Dict[str, AnalysisResult],
        output_dir: str
    ) -> str:
        """
        Create an interactive dashboard from analysis results.
        
        Args:
            results: Analysis results to visualize
            output_dir: Directory to save the dashboard
            
        Returns:
            Path to the dashboard HTML file
        """
        import os
        import json
        from datetime import datetime
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare dashboard data
        dashboard_data = self._prepare_dashboard_data(results)
        
        # Generate dashboard HTML
        dashboard_html = self._generate_dashboard_html(dashboard_data)
        
        # Save dashboard
        dashboard_path = os.path.join(output_dir, "interactive_dashboard.html")
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        
        # Save data file
        data_path = os.path.join(output_dir, "dashboard_data.json")
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, indent=2, default=str)
        
        print(f"🎛️ Interactive dashboard created: {dashboard_path}")
        return dashboard_path
    
    def _prepare_dashboard_data(self, results: Dict[str, AnalysisResult]) -> Dict[str, Any]:
        """Prepare data for the dashboard."""
        # This would contain the logic to transform analysis results
        # into a format suitable for interactive visualization
        return {
            'timestamp': datetime.now().isoformat(),
            'results': {name: result.to_dict() for name, result in results.items()},
            'summary': {
                'total_analyzers': len(results),
                'total_issues': sum(len(r.issues) for r in results.values()),
                'analysis_types': list(set(r.analysis_type.value for r in results.values()))
            }
        }
    
    def _generate_dashboard_html(self, data: Dict[str, Any]) -> str:
        """Generate the dashboard HTML."""
        # This would contain the HTML template for the interactive dashboard
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Graph-Sitter Interactive Dashboard</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
        /* Dashboard styles would go here */
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
        .dashboard {{ max-width: 1200px; margin: 0 auto; }}
        .controls {{ background: #f5f5f5; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .visualization {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
    </style>
</head>
<body>
    <div id="app" class="dashboard">
        <h1>🎛️ Graph-Sitter Interactive Dashboard</h1>
        
        <div class="controls">
            <h3>Analysis Controls</h3>
            <label>Analysis Type:</label>
            <select v-model="selectedAnalysisType" @change="updateVisualization">
                <option value="all">All Types</option>
                <option v-for="type in analysisTypes" :value="type">{{{{ type }}}}</option>
            </select>
            
            <label>Visualization:</label>
            <select v-model="selectedVisualization" @change="updateVisualization">
                <option value="issues_overview">Issues Overview</option>
                <option value="metrics_dashboard">Metrics Dashboard</option>
                <option value="dependency_graph">Dependency Graph</option>
                <option value="call_graph">Call Graph</option>
            </select>
        </div>
        
        <div class="visualization">
            <div id="main-chart"></div>
        </div>
        
        <div class="visualization">
            <h3>Analysis Summary</h3>
            <p>Total Analyzers: {{{{ summary.total_analyzers }}}}</p>
            <p>Total Issues: {{{{ summary.total_issues }}}}</p>
            <p>Analysis Types: {{{{ summary.analysis_types.join(', ') }}}}</p>
        </div>
    </div>
    
    <script>
        const {{ createApp }} = Vue;
        
        createApp({{
            data() {{
                return {{
                    dashboardData: {json.dumps(data)},
                    selectedAnalysisType: 'all',
                    selectedVisualization: 'issues_overview'
                }};
            }},
            computed: {{
                analysisTypes() {{
                    return this.dashboardData.summary.analysis_types;
                }},
                summary() {{
                    return this.dashboardData.summary;
                }}
            }},
            methods: {{
                updateVisualization() {{
                    // Update the main chart based on selections
                    this.renderChart();
                }},
                renderChart() {{
                    // Sample chart rendering
                    const data = [{{
                        x: ['Errors', 'Warnings', 'Info'],
                        y: [5, 12, 8],
                        type: 'bar',
                        marker: {{ color: ['#e74c3c', '#f39c12', '#2ecc71'] }}
                    }}];
                    
                    const layout = {{
                        title: 'Issues by Severity',
                        xaxis: {{ title: 'Severity' }},
                        yaxis: {{ title: 'Count' }}
                    }};
                    
                    Plotly.newPlot('main-chart', data, layout, {{responsive: true}});
                }}
            }},
            mounted() {{
                this.renderChart();
            }}
        }}).mount('#app');
    </script>
</body>
</html>
        """


# Convenience functions for common operations
def analyze_codebase(
    codebase: Codebase,
    analysis_types: Optional[List[Union[str, AnalysisType]]] = None,
    config: Optional[AnalysisConfig] = None
) -> Dict[str, AnalysisResult]:
    """
    Convenience function to analyze a codebase.
    
    Args:
        codebase: Codebase to analyze
        analysis_types: Specific analysis types to run
        config: Analysis configuration
        
    Returns:
        Dictionary of analysis results
    """
    analyzer = UnifiedAnalyzer(codebase, config)
    
    if analysis_types:
        return analyzer.run_specific_analysis(analysis_types)
    else:
        return analyzer.run_comprehensive_analysis()


def generate_analysis_report(
    codebase: Codebase,
    output_dir: str,
    title: Optional[str] = None,
    include_dashboard: bool = True,
    config: Optional[AnalysisConfig] = None
) -> Dict[str, str]:
    """
    Generate comprehensive analysis report with visualizations.
    
    Args:
        codebase: Codebase to analyze
        output_dir: Output directory for reports
        title: Custom report title
        include_dashboard: Whether to include interactive dashboard
        config: Analysis configuration
        
    Returns:
        Dictionary with paths to generated files
    """
    analyzer = UnifiedAnalyzer(codebase, config)
    
    # Run comprehensive analysis
    results = analyzer.run_comprehensive_analysis()
    
    # Generate HTML report
    report_path = analyzer.generate_html_report(output_dir, title)
    
    generated_files = {
        'html_report': report_path,
        'analysis_results': results
    }
    
    # Generate interactive dashboard if requested
    if include_dashboard:
        dashboard = InteractiveDashboard(config)
        dashboard_path = dashboard.create_dashboard(results, output_dir)
        generated_files['interactive_dashboard'] = dashboard_path
    
    return generated_files


# Export all components
__all__ = [
    # Main classes
    "UnifiedAnalyzer",
    "InteractiveDashboard",
    
    # Convenience functions
    "analyze_codebase",
    "generate_analysis_report",
    
    # Re-exported components
    "HTMLReportGenerator",
    "AnalysisRegistry",
    "BaseAnalyzer",
    "AnalysisType",
    "AnalysisResult",
    
    # Specific analyzers (if available)
    "CallGraphAnalyzer",
    "DeadCodeAnalyzer",
    "DependencyAnalyzer", 
    "CodebaseMetrics",
    "FunctionContextAnalyzer",
    "EnhancedAnalyzer",
    
    # Visualization components (if available)
    "CodebaseVisualizer",
    "CallGraphVisualizer",
    "DependencyVisualizer",
    "MetricsVisualizer",
    
    # Database adapter (if available)
    "CodebaseDBAdapter",
    
    # Codemod components (if available)
    "CodemodEngine",
    "BaseCodemod",
]


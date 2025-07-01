"""Unified codebase analyzer integrating all analysis components for comprehensive understanding."""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from graph_sitter.core.codebase import Codebase

# Import all analysis components
from .analysis.enhanced_analysis import EnhancedAnalyzer
from .analysis.metrics import CodebaseMetrics, calculate_codebase_metrics
from .analysis.dependency_analyzer import DependencyAnalyzer
from .analysis.call_graph import CallGraphAnalyzer
from .analysis.dead_code import DeadCodeAnalyzer
from .analysis.function_context import FunctionContext, get_function_context
from .visualizations.react_visualizations import create_react_visualizations
from .visualizations.codebase_visualization import create_comprehensive_visualization

logger = logging.getLogger(__name__)


@dataclass
class ComprehensiveAnalysisResult:
    """Complete analysis result with all components."""
    codebase_id: str
    timestamp: str
    
    # Core analysis
    enhanced_analysis: AnalysisReport
    function_contexts: List[FunctionContext]
    training_data: TrainingData
    
    # Visualizations
    interactive_report: InteractiveReport
    
    # Component results
    metrics_summary: Dict[str, Any]
    dependency_analysis: Dict[str, Any]
    dead_code_analysis: Dict[str, Any]
    call_graph_analysis: Dict[str, Any]
    
    # Aggregated insights
    health_score: float
    risk_assessment: Dict[str, Any]
    actionable_recommendations: List[str]
    
    # Export data
    export_paths: Dict[str, str]


class UnifiedCodebaseAnalyzer:
    """
    Unified analyzer that orchestrates all analysis components for comprehensive codebase understanding.
    
    This class integrates:
    - Enhanced analysis (metrics, dependencies, dead code, call graphs)
    - Function context analysis with issue detection
    - Interactive visualization and reporting
    - Training data generation for ML applications
    - Database storage and querying
    """
    
    def __init__(self, 
                 codebase: Codebase, 
                 codebase_id: str = None,
                 output_dir: str = "comprehensive_analysis",
                 db_path: str = "analysis.db"):
        """
        Initialize unified analyzer.
        
        Args:
            codebase: Codebase to analyze
            codebase_id: Unique identifier for this codebase
            output_dir: Directory for output files
            db_path: Database path for storing results
        """
        self.codebase = codebase
        self.codebase_id = codebase_id or f"codebase_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize all analyzers
        self.enhanced_analyzer = EnhancedAnalyzer(codebase, self.codebase_id)
        self.metrics_calculator = CodebaseMetrics(codebase)
        self.dependency_analyzer = DependencyAnalyzer(codebase)
        self.dead_code_detector = DeadCodeAnalyzer(codebase)
        self.call_graph_analyzer = CallGraphAnalyzer(codebase)
        self.visualizer = CodebaseVisualizer(codebase, str(self.output_dir / "visualizations"))
        
        # Database components
        self.analysis_db = AnalysisDatabase(db_path)
        self.db_adapter = CodebaseDbAdapter(self.analysis_db)
        
        # Results storage
        self.analysis_results: Optional[ComprehensiveAnalysisResult] = None
    
    def run_comprehensive_analysis(self, 
                                 save_to_db: bool = True,
                                 generate_training_data: bool = True,
                                 create_visualizations: bool = True) -> ComprehensiveAnalysisResult:
        """
        Run comprehensive analysis with all components.
        
        Args:
            save_to_db: Whether to save results to database
            generate_training_data: Whether to generate ML training data
            create_visualizations: Whether to create interactive visualizations
            
        Returns:
            Comprehensive analysis results
        """
        logger.info(f"Starting comprehensive analysis for codebase: {self.codebase_id}")
        start_time = datetime.now()
        
        try:
            # 1. Run enhanced analysis (core metrics, dependencies, dead code, call graphs)
            logger.info("Running enhanced analysis...")
            enhanced_analysis = self.enhanced_analyzer.run_full_analysis()
            
            # 2. Analyze function contexts with issue detection
            logger.info("Analyzing function contexts...")
            function_contexts = self._analyze_all_function_contexts()
            
            # 3. Generate training data for ML applications
            training_data = None
            if generate_training_data:
                logger.info("Generating training data...")
                training_data = self._generate_training_data()
            
            # 4. Create interactive visualizations
            interactive_report = None
            if create_visualizations:
                logger.info("Creating interactive visualizations...")
                interactive_report = self.visualizer.generate_comprehensive_report()
            
            # 5. Get component-specific results
            logger.info("Gathering component results...")
            metrics_summary = self._get_metrics_summary()
            dependency_analysis = self._get_dependency_analysis()
            dead_code_analysis = self._get_dead_code_analysis()
            call_graph_analysis = self._get_call_graph_analysis()
            
            # 6. Calculate aggregated insights
            logger.info("Calculating aggregated insights...")
            health_score = self._calculate_overall_health_score(enhanced_analysis, function_contexts)
            risk_assessment = self._assess_overall_risk(function_contexts)
            recommendations = self._generate_actionable_recommendations(
                enhanced_analysis, function_contexts, dependency_analysis, dead_code_analysis
            )
            
            # 7. Save results and create exports
            logger.info("Saving results...")
            export_paths = self._save_all_results(
                enhanced_analysis, function_contexts, training_data, interactive_report
            )
            
            # 8. Create comprehensive result
            self.analysis_results = ComprehensiveAnalysisResult(
                codebase_id=self.codebase_id,
                timestamp=datetime.now().isoformat(),
                enhanced_analysis=enhanced_analysis,
                function_contexts=function_contexts,
                training_data=training_data,
                interactive_report=interactive_report,
                metrics_summary=metrics_summary,
                dependency_analysis=dependency_analysis,
                dead_code_analysis=dead_code_analysis,
                call_graph_analysis=call_graph_analysis,
                health_score=health_score,
                risk_assessment=risk_assessment,
                actionable_recommendations=recommendations,
                export_paths=export_paths
            )
            
            # 9. Save to database if requested
            if save_to_db:
                logger.info("Saving to database...")
                self._save_to_database()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger.info(f"Comprehensive analysis completed in {duration:.2f} seconds")
            
            return self.analysis_results
            
        except Exception as e:
            logger.error(f"Error during comprehensive analysis: {e}")
            raise
    
    def _analyze_all_function_contexts(self) -> List[FunctionContext]:
        """Analyze all functions for enhanced context."""
        function_contexts = []
        
        for function in self.codebase.functions:
            try:
                context = get_function_context(function)
                function_contexts.append(context)
            except Exception as e:
                logger.warning(f"Error analyzing function {function.name}: {e}")
        
        return function_contexts
    
    def _generate_training_data(self) -> TrainingData:
        """Generate training data for ML applications."""
        from .analysis.function_context import run
        return run(self.codebase)
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        try:
            return calculate_codebase_metrics(self.codebase)
        except Exception as e:
            logger.warning(f"Error getting metrics summary: {e}")
            return {}
    
    def _get_dependency_analysis(self) -> Dict[str, Any]:
        """Get dependency analysis results."""
        try:
            import_analysis = self.dependency_analyzer.analyze_imports()
            circular_deps = self.dependency_analyzer.find_circular_dependencies()
            
            return {
                "import_analysis": asdict(import_analysis),
                "circular_dependencies": [asdict(cd) for cd in circular_deps],
                "dependency_graph": self.dependency_analyzer.get_dependency_graph()
            }
        except Exception as e:
            logger.warning(f"Error getting dependency analysis: {e}")
            return {}
    
    def _get_dead_code_analysis(self) -> Dict[str, Any]:
        """Get dead code analysis results."""
        try:
            dead_code_items = self.dead_code_detector.find_dead_code()
            cleanup_plan = self.dead_code_detector.get_removal_plan(dead_code_items)
            
            return {
                "dead_code_items": [asdict(item) for item in dead_code_items],
                "cleanup_plan": asdict(cleanup_plan),
                "impact_estimate": self.dead_code_detector.estimate_cleanup_impact(dead_code_items)
            }
        except Exception as e:
            logger.warning(f"Error getting dead code analysis: {e}")
            return {}
    
    def _get_call_graph_analysis(self) -> Dict[str, Any]:
        """Get call graph analysis results."""
        try:
            call_patterns = self.call_graph_analyzer.analyze_call_patterns()
            call_chains = self.call_graph_analyzer.analyze_call_chains()
            
            return {
                "call_patterns": call_patterns,
                "call_chains": call_chains,
                "graph_metrics": self.call_graph_analyzer.get_graph_metrics()
            }
        except Exception as e:
            logger.warning(f"Error getting call graph analysis: {e}")
            return {}
    
    def _calculate_overall_health_score(self, 
                                      enhanced_analysis: AnalysisReport,
                                      function_contexts: List[FunctionContext]) -> float:
        """Calculate overall codebase health score."""
        try:
            # Base score from enhanced analysis
            base_score = enhanced_analysis.health_score
            
            # Adjust based on function context analysis
            total_functions = len(function_contexts)
            if total_functions == 0:
                return base_score
            
            # Calculate issue penalty
            total_issues = sum(len(fc.issues) for fc in function_contexts)
            issue_penalty = min(total_issues / total_functions * 0.1, 0.3)
            
            # Calculate risk penalty
            high_risk_functions = len([fc for fc in function_contexts if fc.risk_level == "high"])
            risk_penalty = min(high_risk_functions / total_functions * 0.2, 0.4)
            
            # Calculate complexity penalty
            high_complexity_functions = len([fc for fc in function_contexts 
                                           if fc.complexity_metrics.get("complexity_estimate", 0) > 15])
            complexity_penalty = min(high_complexity_functions / total_functions * 0.15, 0.25)
            
            # Apply penalties
            adjusted_score = base_score - issue_penalty - risk_penalty - complexity_penalty
            
            return max(0.0, min(1.0, adjusted_score))
            
        except Exception as e:
            logger.warning(f"Error calculating health score: {e}")
            return enhanced_analysis.health_score if enhanced_analysis else 0.5
    
    def _assess_overall_risk(self, function_contexts: List[FunctionContext]) -> Dict[str, Any]:
        """Assess overall codebase risk."""
        if not function_contexts:
            return {"level": "unknown", "factors": []}
        
        risk_counts = {"high": 0, "medium": 0, "low": 0, "minimal": 0}
        risk_factors = []
        
        for fc in function_contexts:
            risk_counts[fc.risk_level] += 1
        
        total_functions = len(function_contexts)
        high_risk_ratio = risk_counts["high"] / total_functions
        medium_risk_ratio = risk_counts["medium"] / total_functions
        
        # Determine overall risk level
        if high_risk_ratio > 0.2:
            overall_risk = "high"
            risk_factors.append(f"{risk_counts['high']} high-risk functions ({high_risk_ratio:.1%})")
        elif high_risk_ratio > 0.1 or medium_risk_ratio > 0.3:
            overall_risk = "medium"
            risk_factors.append(f"{risk_counts['high']} high-risk and {risk_counts['medium']} medium-risk functions")
        elif medium_risk_ratio > 0.1:
            overall_risk = "low"
            risk_factors.append(f"{risk_counts['medium']} medium-risk functions")
        else:
            overall_risk = "minimal"
        
        # Add specific risk factors
        total_issues = sum(len(fc.issues) for fc in function_contexts)
        if total_issues > total_functions * 2:
            risk_factors.append(f"High issue density: {total_issues} issues across {total_functions} functions")
        
        return {
            "level": overall_risk,
            "distribution": risk_counts,
            "factors": risk_factors,
            "metrics": {
                "high_risk_ratio": high_risk_ratio,
                "medium_risk_ratio": medium_risk_ratio,
                "total_issues": total_issues,
                "avg_issues_per_function": total_issues / total_functions
            }
        }
    
    def _generate_actionable_recommendations(self,
                                           enhanced_analysis: AnalysisReport,
                                           function_contexts: List[FunctionContext],
                                           dependency_analysis: Dict[str, Any],
                                           dead_code_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on all analysis results."""
        recommendations = set()
        
        # Add enhanced analysis recommendations
        if enhanced_analysis and enhanced_analysis.recommendations:
            recommendations.update(enhanced_analysis.recommendations)
        
        # Add function-specific recommendations
        for fc in function_contexts:
            recommendations.update(fc.recommendations)
        
        # Add dependency-based recommendations
        if dependency_analysis.get("circular_dependencies"):
            recommendations.add("Resolve circular dependencies to improve maintainability")
        
        # Add dead code recommendations
        dead_code_items = dead_code_analysis.get("dead_code_items", [])
        if len(dead_code_items) > 5:
            recommendations.add(f"Remove {len(dead_code_items)} dead code items to reduce codebase size")
        
        # Add system-level recommendations
        high_complexity_functions = [fc for fc in function_contexts 
                                   if fc.complexity_metrics.get("complexity_estimate", 0) > 15]
        if len(high_complexity_functions) > 3:
            recommendations.add("Implement complexity monitoring and refactoring for high-complexity functions")
        
        # Prioritize recommendations
        prioritized = list(recommendations)
        prioritized.sort(key=lambda x: (
            "high" in x.lower() or "critical" in x.lower(),
            "remove" in x.lower() or "resolve" in x.lower(),
            len(x)
        ), reverse=True)
        
        return prioritized[:15]  # Return top 15 recommendations
    
    def _save_all_results(self,
                         enhanced_analysis: AnalysisReport,
                         function_contexts: List[FunctionContext],
                         training_data: Optional[TrainingData],
                         interactive_report: Optional[InteractiveReport]) -> Dict[str, str]:
        """Save all analysis results to files."""
        export_paths = {}
        
        # Save enhanced analysis
        enhanced_path = self.output_dir / "enhanced_analysis.json"
        with open(enhanced_path, "w") as f:
            json.dump(asdict(enhanced_analysis), f, indent=2, default=str)
        export_paths["enhanced_analysis"] = str(enhanced_path)
        
        # Save function contexts
        contexts_path = self.output_dir / "function_contexts.json"
        with open(contexts_path, "w") as f:
            json.dump([asdict(fc) for fc in function_contexts], f, indent=2, default=str)
        export_paths["function_contexts"] = str(contexts_path)
        
        # Save training data
        if training_data:
            training_path = self.output_dir / "training_data.json"
            with open(training_path, "w") as f:
                json.dump(asdict(training_data), f, indent=2, default=str)
            export_paths["training_data"] = str(training_path)
        
        # Interactive report is saved by the visualizer
        if interactive_report:
            export_paths["interactive_report"] = str(self.output_dir / "visualizations" / "interactive_report.html")
        
        return export_paths
    
    def _save_to_database(self):
        """Save analysis results to database."""
        if not self.analysis_results:
            return
        
        try:
            # Save to database using the adapter
            self.db_adapter.store_analysis_result(self.analysis_results.enhanced_analysis)
            logger.info("Analysis results saved to database")
        except Exception as e:
            logger.warning(f"Error saving to database: {e}")
    
    def get_function_analysis(self, function_name: str) -> Optional[FunctionContext]:
        """Get analysis for a specific function."""
        if not self.analysis_results:
            logger.warning("No analysis results available. Run comprehensive analysis first.")
            return None
        
        for fc in self.analysis_results.function_contexts:
            if fc.name == function_name:
                return fc
        
        return None
    
    def get_functions_with_issues(self, severity: str = None) -> List[FunctionContext]:
        """Get functions that have issues, optionally filtered by severity."""
        if not self.analysis_results:
            return []
        
        functions_with_issues = []
        for fc in self.analysis_results.function_contexts:
            if fc.issues:
                if severity:
                    matching_issues = [issue for issue in fc.issues if issue.get("severity") == severity]
                    if matching_issues:
                        functions_with_issues.append(fc)
                else:
                    functions_with_issues.append(fc)
        
        return functions_with_issues
    
    def export_summary_report(self, output_file: str = None) -> str:
        """Export a summary report in markdown format."""
        if not self.analysis_results:
            raise ValueError("No analysis results available. Run comprehensive analysis first.")
        
        if not output_file:
            output_file = str(self.output_dir / "summary_report.md")
        
        result = self.analysis_results
        
        markdown_content = f"""# Comprehensive Codebase Analysis Report

**Codebase ID:** {result.codebase_id}  
**Analysis Date:** {result.timestamp}  
**Health Score:** {result.health_score:.2f}/1.0

## 📊 Summary

- **Total Functions:** {len(result.function_contexts)}
- **Total Issues:** {sum(len(fc.issues) for fc in result.function_contexts)}
- **Risk Level:** {result.risk_assessment['level'].title()}
- **Functions with Issues:** {len([fc for fc in result.function_contexts if fc.issues])}

## ⚠️ Risk Assessment

**Overall Risk Level:** {result.risk_assessment['level'].title()}

**Risk Distribution:**
{chr(10).join(f"- {level.title()}: {count} functions" for level, count in result.risk_assessment['distribution'].items())}

**Risk Factors:**
{chr(10).join(f"- {factor}" for factor in result.risk_assessment['factors'])}

## 🎯 Top Recommendations

{chr(10).join(f"{i+1}. {rec}" for i, rec in enumerate(result.actionable_recommendations[:10]))}

## 🔥 High-Risk Functions

{chr(10).join(f"- **{fc.name}** ({fc.filepath}) - {len(fc.issues)} issues, complexity: {fc.complexity_metrics.get('complexity_estimate', 0)}" 
             for fc in result.function_contexts if fc.risk_level == 'high')[:10]}

## 📈 Metrics Summary

- **Average Complexity:** {sum(fc.complexity_metrics.get('complexity_estimate', 0) for fc in result.function_contexts) / len(result.function_contexts):.1f}
- **Functions with High Complexity (>10):** {len([fc for fc in result.function_contexts if fc.complexity_metrics.get('complexity_estimate', 0) > 10])}
- **Unused Functions:** {len([fc for fc in result.function_contexts if fc.complexity_metrics.get('usage_count', 0) == 0])}

## 📁 Export Files

{chr(10).join(f"- **{name.replace('_', ' ').title()}:** `{path}`" for name, path in result.export_paths.items())}

---
*Generated by Unified Codebase Analyzer*
"""
        
        with open(output_file, "w") as f:
            f.write(markdown_content)
        
        return output_file
    
    def generate_interactive_report(self, output_path: str = "analysis_report.html") -> str:
        """
        Generate an interactive HTML report with all analysis results.
        
        Args:
            output_path: Path where the HTML report will be saved
            
        Returns:
            Path to the generated HTML report
        """
        # Generate interactive report
        report_path = self.output_dir / "visualizations" / "interactive_report.html"
        if not report_path.exists():
            report_path = create_interactive_report(
                codebase=self.codebase,
                output_path=output_path
            )
        
        return str(report_path)
    
    def generate_react_visualizations(self, output_dir: str = "react_visualizations",
                                    visualization_types: List[str] = None) -> Dict[str, Any]:
        """
        Generate comprehensive React visualizations for the analyzed codebase.
        
        Args:
            output_dir: Directory to save React components and data
            visualization_types: List of visualization types to generate
            
        Returns:
            Dictionary containing visualization data and component information
        """
        if not self.codebase:
            raise ValueError("No codebase loaded. Call analyze_codebase() first.")
        
        # Generate React visualizations
        result = create_react_visualizations(
            codebase=self.codebase,
            visualization_types=visualization_types
        )
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # Save visualization data and components
        for viz_type, component_data in result['components'].items():
            # Save JSON data
            json_file = output_path / f"{viz_type}_data.json"
            with open(json_file, 'w') as f:
                json.dump(component_data['data'], f, indent=2, default=str)
            
            # Save React component
            component_file = output_path / f"{viz_type.title().replace('_', '')}Visualization.jsx"
            with open(component_file, 'w') as f:
                f.write(component_data['component_code'])
        
        # Save dashboard component
        dashboard_file = output_path / "CodebaseDashboard.jsx"
        with open(dashboard_file, 'w') as f:
            f.write(result['dashboard_component'])
        
        # Save metadata
        metadata_file = output_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(result['metadata'], f, indent=2, default=str)
        
        # Generate package.json for easy setup
        package_json = {
            "name": "codebase-visualizations",
            "version": "1.0.0",
            "description": "React visualizations for codebase analysis",
            "main": "CodebaseDashboard.jsx",
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0",
                "vis-network": "^9.0.0"
            },
            "scripts": {
                "start": "react-scripts start",
                "build": "react-scripts build"
            }
        }
        
        package_file = output_path / "package.json"
        with open(package_file, 'w') as f:
            json.dump(package_json, f, indent=2)
        
        logger.info(f"Generated React visualizations in {output_path}")
        
        return {
            **result,
            'output_path': str(output_path),
            'files_generated': [
                str(f.relative_to(output_path)) for f in output_path.iterdir()
            ]
        }


# Convenience functions for external use
def analyze_codebase_comprehensive(codebase: Codebase, 
                                 codebase_id: str = None,
                                 output_dir: str = "comprehensive_analysis") -> ComprehensiveAnalysisResult:
    """
    Run comprehensive codebase analysis with all components.
    
    Args:
        codebase: Codebase to analyze
        codebase_id: Unique identifier
        output_dir: Output directory
        
    Returns:
        Comprehensive analysis results
    """
    analyzer = UnifiedCodebaseAnalyzer(codebase, codebase_id, output_dir)
    return analyzer.run_comprehensive_analysis()


def quick_function_analysis(codebase: Codebase, function_name: str) -> Optional[FunctionContext]:
    """
    Quick analysis of a specific function.
    
    Args:
        codebase: Codebase containing the function
        function_name: Name of function to analyze
        
    Returns:
        Function context with analysis
    """
    from .codebase_visualization import analyze_function_with_context
    return analyze_function_with_context(codebase, function_name)


if __name__ == "__main__":
    print("Unified Codebase Analyzer")
    print("=" * 50)
    print("Comprehensive codebase analysis integrating all components:")
    print("- Enhanced analysis (metrics, dependencies, dead code, call graphs)")
    print("- Function context analysis with issue detection")
    print("- Interactive visualization and reporting")
    print("- Training data generation for ML applications")
    print("- Database storage and querying")
    print("\nUse analyze_codebase_comprehensive() for full analysis.")

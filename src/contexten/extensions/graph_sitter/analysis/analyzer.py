"""
Main Analysis Interface

Unified interface for all codebase analysis operations using official tree-sitter patterns.
This module has been updated to use the new consolidated analysis system.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

from .config.analysis_config import AnalysisConfig
from .unified_analyzer import UnifiedAnalyzer, AnalysisResult as UnifiedAnalysisResult, CodebaseAnalysisResult
from .core.tree_sitter_core import get_tree_sitter_core

# Legacy imports for backward compatibility
from .core.analysis_engine import AnalysisResult
from .visualization.html_reporter import HTMLReporter


class CodebaseAnalyzer:
    """
    Main interface for comprehensive codebase analysis.
    
    This is the primary entry point for all analysis operations,
    now using the unified tree-sitter-based analysis system.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the codebase analyzer.
        
        Args:
            config: Analysis configuration. If None, uses default configuration.
        """
        self.config = config or AnalysisConfig()
        self.tree_sitter_core = get_tree_sitter_core()
        self.unified_analyzer = UnifiedAnalyzer(self.tree_sitter_core)
        self.html_reporter = HTMLReporter()
        self.logger = logging.getLogger(__name__)
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging based on configuration."""
        level = logging.DEBUG if self.config.graph_sitter.debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def analyze(
        self, 
        codebase_path: Union[str, Path],
        output_dir: Optional[str] = None,
        **kwargs
    ) -> CodebaseAnalysisResult:
        """
        Perform comprehensive codebase analysis using unified tree-sitter system.
        
        Args:
            codebase_path: Path to the codebase to analyze
            output_dir: Directory to save analysis outputs
            **kwargs: Additional configuration overrides
            
        Returns:
            CodebaseAnalysisResult containing all analysis data
        """
        self.logger.info(f"Starting unified analysis of codebase: {codebase_path}")
        
        # Extract analysis options from kwargs
        include_patterns = kwargs.get('include_patterns')
        exclude_patterns = kwargs.get('exclude_patterns')
        
        # Perform analysis using unified analyzer
        result = self.unified_analyzer.analyze_codebase(
            codebase_path, 
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )
        
        # Generate outputs if output directory specified
        if output_dir:
            self._generate_outputs(result, output_dir)
        
        self.logger.info("Unified analysis completed successfully")
        return result
    
    def quick_analyze(
        self, 
        codebase_path: Union[str, Path],
        output_file: Optional[str] = None
    ) -> CodebaseAnalysisResult:
        """
        Perform quick analysis with minimal features using unified system.
        
        Args:
            codebase_path: Path to the codebase to analyze
            output_file: Optional file to save results
            
        Returns:
            CodebaseAnalysisResult with basic analysis data
        """
        self.logger.info(f"Starting quick unified analysis of codebase: {codebase_path}")
        
        # For quick analysis, limit to common file types
        include_patterns = ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx']
        exclude_patterns = [
            '*test*', '*spec*', '*__pycache__*', '*node_modules*', 
            '*.min.js', '*build*', '*dist*'
        ]
        
        result = self.unified_analyzer.analyze_codebase(
            codebase_path,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )
        
        if output_file:
            self._save_result(result, output_file)
        
        return result
    
    def comprehensive_analyze(
        self, 
        codebase_path: Union[str, Path],
        output_dir: str
    ) -> CodebaseAnalysisResult:
        """
        Perform comprehensive analysis with all features enabled.
        
        Args:
            codebase_path: Path to the codebase to analyze
            output_dir: Directory to save comprehensive outputs
            
        Returns:
            CodebaseAnalysisResult with comprehensive analysis data
        """
        self.logger.info(f"Starting comprehensive analysis of codebase: {codebase_path}")
        
        result = self.unified_analyzer.analyze_codebase(codebase_path)
        
        # Generate comprehensive outputs
        self._generate_comprehensive_outputs(result, output_dir)
        
        return result
    
    def analyze_with_tree_sitter(
        self, 
        codebase_path: Union[str, Path],
        output_dir: str,
        languages: Optional[List[str]] = None
    ) -> CodebaseAnalysisResult:
        """
        Perform analysis with tree-sitter integration enabled.
        
        Args:
            codebase_path: Path to the codebase to analyze
            output_dir: Directory to save outputs
            languages: List of languages to analyze with tree-sitter
            
        Returns:
            CodebaseAnalysisResult with tree-sitter analysis data
        """
        # Enable tree-sitter features
        config = AnalysisConfig()
        config.enable_tree_sitter = True
        config.enable_visualization = True
        config.export_visualizations = True
        
        # Create analyzer with tree-sitter config
        analyzer = CodebaseAnalyzer(config)
        
        self.logger.info(f"Starting tree-sitter analysis of codebase: {codebase_path}")
        
        result = analyzer.analyze(codebase_path)
        
        # Generate tree-sitter specific outputs
        self._generate_tree_sitter_outputs(result, output_dir, languages)
        
        return result
    
    def export_html(
        self, 
        codebase_path: Union[str, Path],
        output_file: str,
        title: Optional[str] = None,
        include_source: bool = False
    ) -> bool:
        """
        Analyze codebase and export HTML report.
        
        Args:
            codebase_path: Path to the codebase to analyze
            output_file: Path for the HTML report
            title: Custom title for the report
            include_source: Whether to include source code snippets
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Perform analysis
            result = self.analyzer.analyze(codebase_path)
            
            # Generate HTML report
            return self.html_reporter.generate_report(
                result, 
                output_file, 
                title,
                include_source
            )
            
        except Exception as e:
            self.logger.error(f"Failed to export HTML: {e}")
            return False
    
    def export_json(
        self, 
        codebase_path: Union[str, Path],
        output_file: str
    ) -> bool:
        """
        Analyze codebase and export JSON data.
        
        Args:
            codebase_path: Path to the codebase to analyze
            output_file: Path for the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Perform analysis
            result = self.analyzer.analyze(codebase_path)
            
            # Export JSON data
            return self.html_reporter.export_json_data(result, output_file)
            
        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
            return False
    
    def get_summary(self, codebase_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get a quick summary of the codebase.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            Dictionary containing summary information
        """
        try:
            summary = self.analyzer.get_codebase_summary(codebase_path)
            return summary
        except Exception as e:
            self.logger.error(f"Failed to get summary: {e}")
            return {"error": str(e)}
    
    def detect_issues(self, codebase_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """
        Detect code quality issues in the codebase.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            List of detected issues
        """
        try:
            result = self.analyzer.analyze(codebase_path)
            return result.issues + [
                {
                    "type": "dead_code",
                    "target": item.get("name", "unknown"),
                    "message": f"Unused {item.get('type', 'code')}: {item.get('name', 'unknown')}",
                    "severity": "warning"
                }
                for item in result.dead_code
            ]
        except Exception as e:
            self.logger.error(f"Failed to detect issues: {e}")
            return [{"type": "analysis_error", "message": str(e), "severity": "critical"}]
    
    def _generate_outputs(self, result: CodebaseAnalysisResult, output_dir: str):
        """Generate standard analysis outputs."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate HTML report
        if 'html' in self.config.output_formats:
            html_file = output_path / "analysis_report.html"
            self.html_reporter.generate_report(result, str(html_file))
        
        # Generate JSON data
        if 'json' in self.config.output_formats:
            json_file = output_path / "analysis_data.json"
            self.html_reporter.export_json_data(result, str(json_file))
        
        # Generate summary report
        summary_file = output_path / "summary.html"
        self.html_reporter.generate_summary_report(result, str(summary_file))
    
    def _generate_comprehensive_outputs(self, result: CodebaseAnalysisResult, output_dir: str):
        """Generate comprehensive analysis outputs."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate all standard outputs
        self._generate_outputs(result, output_dir)
        
        # Generate detailed reports
        if self.config.detailed_metrics:
            # Generate detailed metrics report
            metrics_file = output_path / "detailed_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(result.metrics, f, indent=2)
            
            # Generate dependency analysis
            deps_file = output_path / "dependencies.json"
            with open(deps_file, 'w') as f:
                json.dump(result.dependencies, f, indent=2)
            
            # Generate issues report
            issues_file = output_path / "issues.json"
            with open(issues_file, 'w') as f:
                json.dump(result.issues, f, indent=2)
    
    def _generate_tree_sitter_outputs(
        self, 
        result: CodebaseAnalysisResult, 
        output_dir: str,
        languages: Optional[List[str]]
    ):
        """Generate tree-sitter specific outputs."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate standard outputs
        self._generate_outputs(result, output_dir)
        
        # Generate tree-sitter specific visualizations
        if self.config.enable_visualization:
            # This would include syntax tree visualizations,
            # pattern matching results, etc.
            pass
    
    def _save_result(self, result: CodebaseAnalysisResult, output_file: str):
        """Save analysis result to file."""
        output_path = Path(output_file)
        
        if output_path.suffix.lower() == '.json':
            self.html_reporter.export_json_data(result, output_file)
        elif output_path.suffix.lower() in ['.html', '.htm']:
            self.html_reporter.generate_report(result, output_file)
        else:
            # Default to JSON
            self.html_reporter.export_json_data(result, output_file + '.json')

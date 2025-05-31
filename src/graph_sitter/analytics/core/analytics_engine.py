"""
Core Analytics Engine for Graph-Sitter

Orchestrates all analysis operations and provides a unified interface
for comprehensive codebase analysis.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Type, Union, Any
from pathlib import Path

from graph_sitter.core.codebase import Codebase
from graph_sitter.shared.logging.logger import get_logger
from graph_sitter.shared.performance.stopwatch_utils import stopwatch

from .analysis_result import AnalysisResult, AnalysisReport, AnalysisMetrics
from .base_analyzer import BaseAnalyzer
from ..analyzers.complexity_analyzer import ComplexityAnalyzer
from ..analyzers.performance_analyzer import PerformanceAnalyzer
from ..analyzers.security_analyzer import SecurityAnalyzer
from ..analyzers.dead_code_analyzer import DeadCodeAnalyzer
from ..analyzers.dependency_analyzer import DependencyAnalyzer

logger = get_logger(__name__)


@dataclass
class AnalysisConfig:
    """Configuration for analytics engine execution."""
    
    # Analysis types to run
    enable_complexity: bool = True
    enable_performance: bool = True
    enable_security: bool = True
    enable_dead_code: bool = True
    enable_dependency: bool = True
    
    # Performance settings
    max_workers: int = 4
    timeout_seconds: int = 300  # 5 minutes
    incremental: bool = True
    cache_results: bool = True
    
    # Language filters
    languages: Optional[Set[str]] = None  # None = all supported languages
    
    # File filters
    include_patterns: List[str] = field(default_factory=lambda: ["**/*.py", "**/*.ts", "**/*.js", "**/*.java", "**/*.cpp", "**/*.rs", "**/*.go"])
    exclude_patterns: List[str] = field(default_factory=lambda: ["**/node_modules/**", "**/venv/**", "**/__pycache__/**", "**/build/**", "**/dist/**"])
    
    # Analysis depth
    deep_analysis: bool = False  # Enable more thorough but slower analysis
    
    # Output settings
    generate_reports: bool = True
    export_format: str = "json"  # json, html, markdown


class AnalyticsEngine:
    """
    Main analytics engine that orchestrates all codebase analysis operations.
    
    Provides high-performance analysis with parallel processing, caching,
    and incremental analysis capabilities.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        self.config = config or AnalysisConfig()
        self.analyzers: Dict[str, BaseAnalyzer] = {}
        self._setup_analyzers()
        self._cache: Dict[str, AnalysisResult] = {}
        
    def _setup_analyzers(self):
        """Initialize all available analyzers based on configuration."""
        if self.config.enable_complexity:
            self.analyzers["complexity"] = ComplexityAnalyzer()
            
        if self.config.enable_performance:
            self.analyzers["performance"] = PerformanceAnalyzer()
            
        if self.config.enable_security:
            self.analyzers["security"] = SecurityAnalyzer()
            
        if self.config.enable_dead_code:
            self.analyzers["dead_code"] = DeadCodeAnalyzer()
            
        if self.config.enable_dependency:
            self.analyzers["dependency"] = DependencyAnalyzer()
    
    @stopwatch("analytics_engine.analyze_codebase")
    def analyze_codebase(self, codebase: Codebase) -> AnalysisReport:
        """
        Perform comprehensive analysis of a codebase.
        
        Args:
            codebase: The codebase to analyze
            
        Returns:
            Complete analysis report with all enabled analysis results
        """
        logger.info(f"Starting comprehensive analysis of codebase with {len(list(codebase.files))} files")
        start_time = time.time()
        
        try:
            # Filter files based on configuration
            filtered_files = self._filter_files(codebase)
            logger.info(f"Analyzing {len(filtered_files)} files after filtering")
            
            # Run all analyzers in parallel
            analysis_results = self._run_parallel_analysis(codebase, filtered_files)
            
            # Aggregate results
            report = self._create_analysis_report(codebase, analysis_results, start_time)
            
            # Cache results if enabled
            if self.config.cache_results:
                self._cache_results(report)
            
            logger.info(f"Analysis completed in {report.execution_time:.2f} seconds")
            return report
            
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            raise
    
    def _filter_files(self, codebase: Codebase) -> List:
        """Filter files based on configuration patterns and language support."""
        from fnmatch import fnmatch
        
        filtered_files = []
        
        for file in codebase.files:
            file_path = str(file.filepath)
            
            # Check include patterns
            if not any(fnmatch(file_path, pattern) for pattern in self.config.include_patterns):
                continue
                
            # Check exclude patterns
            if any(fnmatch(file_path, pattern) for pattern in self.config.exclude_patterns):
                continue
                
            # Check language filter
            if self.config.languages:
                file_ext = Path(file_path).suffix.lower()
                lang_map = {
                    ".py": "python",
                    ".ts": "typescript", 
                    ".tsx": "typescript",
                    ".js": "javascript",
                    ".jsx": "javascript",
                    ".java": "java",
                    ".cpp": "cpp",
                    ".cc": "cpp",
                    ".cxx": "cpp",
                    ".rs": "rust",
                    ".go": "go"
                }
                
                if lang_map.get(file_ext) not in self.config.languages:
                    continue
            
            filtered_files.append(file)
        
        return filtered_files
    
    def _run_parallel_analysis(self, codebase: Codebase, files: List) -> Dict[str, AnalysisResult]:
        """Run all enabled analyzers in parallel for optimal performance."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all analyzer tasks
            future_to_analyzer = {}
            
            for analyzer_name, analyzer in self.analyzers.items():
                future = executor.submit(self._run_analyzer_safely, analyzer, codebase, files)
                future_to_analyzer[future] = analyzer_name
            
            # Collect results as they complete
            for future in as_completed(future_to_analyzer, timeout=self.config.timeout_seconds):
                analyzer_name = future_to_analyzer[future]
                try:
                    result = future.result()
                    results[analyzer_name] = result
                    logger.info(f"Completed {analyzer_name} analysis")
                except Exception as e:
                    logger.error(f"Analyzer {analyzer_name} failed: {str(e)}")
                    # Create error result
                    results[analyzer_name] = AnalysisResult(
                        analyzer_name=analyzer_name,
                        status="error",
                        error_message=str(e),
                        metrics=AnalysisMetrics()
                    )
        
        return results
    
    def _run_analyzer_safely(self, analyzer: BaseAnalyzer, codebase: Codebase, files: List) -> AnalysisResult:
        """Run a single analyzer with error handling."""
        try:
            return analyzer.analyze(codebase, files)
        except Exception as e:
            logger.error(f"Analyzer {analyzer.__class__.__name__} failed: {str(e)}")
            raise
    
    def _create_analysis_report(self, codebase: Codebase, results: Dict[str, AnalysisResult], start_time: float) -> AnalysisReport:
        """Create comprehensive analysis report from individual results."""
        execution_time = time.time() - start_time
        
        # Calculate overall metrics
        total_files = len(list(codebase.files))
        total_lines = sum(len(file.content.splitlines()) if hasattr(file, 'content') else 0 for file in codebase.files)
        
        # Aggregate findings
        all_findings = []
        for result in results.values():
            all_findings.extend(result.findings)
        
        # Calculate quality score (0-100)
        quality_score = self._calculate_quality_score(results)
        
        return AnalysisReport(
            codebase_name=getattr(codebase, 'name', 'Unknown'),
            analysis_results=results,
            execution_time=execution_time,
            total_files_analyzed=total_files,
            total_lines_analyzed=total_lines,
            overall_quality_score=quality_score,
            summary_findings=all_findings[:10],  # Top 10 most critical findings
            recommendations=self._generate_recommendations(results),
            timestamp=time.time()
        )
    
    def _calculate_quality_score(self, results: Dict[str, AnalysisResult]) -> float:
        """Calculate overall codebase quality score based on analysis results."""
        scores = []
        weights = {
            "complexity": 0.25,
            "security": 0.30,
            "dead_code": 0.20,
            "performance": 0.15,
            "dependency": 0.10
        }
        
        for analyzer_name, result in results.items():
            if result.status == "completed" and result.metrics.quality_score is not None:
                weight = weights.get(analyzer_name, 0.1)
                scores.append(result.metrics.quality_score * weight)
        
        return sum(scores) if scores else 0.0
    
    def _generate_recommendations(self, results: Dict[str, AnalysisResult]) -> List[str]:
        """Generate actionable recommendations based on analysis results."""
        recommendations = []
        
        for analyzer_name, result in results.items():
            if result.status == "completed":
                # Add analyzer-specific recommendations
                if hasattr(result, 'recommendations'):
                    recommendations.extend(result.recommendations)
                
                # Generate general recommendations based on metrics
                if result.metrics.critical_issues > 0:
                    recommendations.append(f"Address {result.metrics.critical_issues} critical issues found by {analyzer_name} analysis")
                
                if result.metrics.quality_score < 70:
                    recommendations.append(f"Improve code quality in areas identified by {analyzer_name} analysis (score: {result.metrics.quality_score:.1f}/100)")
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _cache_results(self, report: AnalysisReport):
        """Cache analysis results for incremental analysis."""
        cache_key = f"{report.codebase_name}_{report.timestamp}"
        self._cache[cache_key] = report
        
        # Limit cache size
        if len(self._cache) > 100:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k].timestamp)
            del self._cache[oldest_key]
    
    def get_analyzer(self, name: str) -> Optional[BaseAnalyzer]:
        """Get a specific analyzer by name."""
        return self.analyzers.get(name)
    
    def add_analyzer(self, name: str, analyzer: BaseAnalyzer):
        """Add a custom analyzer to the engine."""
        self.analyzers[name] = analyzer
    
    def remove_analyzer(self, name: str):
        """Remove an analyzer from the engine."""
        if name in self.analyzers:
            del self.analyzers[name]


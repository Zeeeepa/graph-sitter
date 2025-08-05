"""
Comprehensive Serena Analysis for Graph-Sitter

This module provides comprehensive codebase analysis using the enhanced Serena LSP bridge,
integrating static analysis, runtime error collection, and advanced Serena capabilities.
"""

import asyncio
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from collections import defaultdict
from urllib.parse import urlparse

from graph_sitter.shared.logging.get_logger import get_logger
from .serena_bridge import (
    SerenaLSPBridge, 
    SerenaErrorInfo, 
    ErrorInfo,  # Backward compatibility
    RuntimeErrorCollector,
    RuntimeError,
    RuntimeContext,
    TransactionAwareLSPManager,
    create_serena_bridge,
    get_enhanced_diagnostics,
    get_comprehensive_analysis,
    start_runtime_error_collection,
    stop_runtime_error_collection,
    get_lsp_manager,
    shutdown_all_lsp_managers
)

logger = get_logger(__name__)


@dataclass
class RepositoryInfo:
    """Information about a repository being analyzed."""
    url: Optional[str] = None
    name: str = ""
    owner: str = ""
    local_path: str = ""
    branch: str = "main"
    clone_depth: Optional[int] = None
    
    @classmethod
    def from_url(cls, url: str, local_path: str) -> 'RepositoryInfo':
        """Create RepositoryInfo from GitHub URL."""
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {url}")
        
        owner = path_parts[0]
        name = path_parts[1].replace('.git', '')
        
        return cls(
            url=url,
            name=name,
            owner=owner,
            local_path=local_path,
            branch="main"
        )
    
    @classmethod
    def from_local_path(cls, local_path: str) -> 'RepositoryInfo':
        """Create RepositoryInfo from local path."""
        path = Path(local_path)
        return cls(
            name=path.name,
            local_path=str(path.resolve())
        )


@dataclass
class AnalysisMetrics:
    """Comprehensive analysis metrics."""
    total_files: int = 0
    total_lines: int = 0
    total_diagnostics: int = 0
    static_errors: int = 0
    runtime_errors: int = 0
    serena_insights: int = 0
    
    # Performance metrics
    analysis_duration: float = 0.0
    lsp_response_time: float = 0.0
    runtime_collection_time: float = 0.0
    serena_analysis_time: float = 0.0
    
    # Quality metrics
    error_density: float = 0.0  # errors per 1000 lines
    maintainability_index: float = 0.0
    technical_debt_score: float = 0.0
    
    def calculate_derived_metrics(self):
        """Calculate derived metrics."""
        if self.total_lines > 0:
            self.error_density = (self.total_diagnostics / self.total_lines) * 1000
            
            # Simple maintainability index calculation
            self.maintainability_index = max(0, 100 - (self.static_errors * 5) - (self.runtime_errors * 10))
            
            # Technical debt score (higher is worse)
            self.technical_debt_score = (self.static_errors * 2) + (self.runtime_errors * 5)


@dataclass
class ComprehensiveAnalysisResult:
    """Result of comprehensive codebase analysis."""
    repository: RepositoryInfo
    metrics: AnalysisMetrics
    diagnostics: List[SerenaErrorInfo] = field(default_factory=list)
    runtime_errors: List[RuntimeError] = field(default_factory=list)
    serena_insights: Dict[str, Any] = field(default_factory=dict)
    
    # Analysis breakdown
    errors_by_file: Dict[str, List[SerenaErrorInfo]] = field(default_factory=dict)
    errors_by_type: Dict[str, List[SerenaErrorInfo]] = field(default_factory=dict)
    errors_by_severity: Dict[str, List[SerenaErrorInfo]] = field(default_factory=dict)
    
    # Quality assessment
    hotspots: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Calculate analysis breakdown after initialization."""
        self._calculate_breakdown()
        self._generate_recommendations()
    
    def _calculate_breakdown(self):
        """Calculate error breakdown by various dimensions."""
        # Group by file
        for diagnostic in self.diagnostics:
            if diagnostic.file_path not in self.errors_by_file:
                self.errors_by_file[diagnostic.file_path] = []
            self.errors_by_file[diagnostic.file_path].append(diagnostic)
        
        # Group by type
        for diagnostic in self.diagnostics:
            if diagnostic.error_type not in self.errors_by_type:
                self.errors_by_type[diagnostic.error_type] = []
            self.errors_by_type[diagnostic.error_type].append(diagnostic)
        
        # Group by severity
        for diagnostic in self.diagnostics:
            severity_name = diagnostic.severity.name
            if severity_name not in self.errors_by_severity:
                self.errors_by_severity[severity_name] = []
            self.errors_by_severity[severity_name].append(diagnostic)
        
        # Calculate hotspots (files with most errors)
        file_error_counts = [(file, len(errors)) for file, errors in self.errors_by_file.items()]
        file_error_counts.sort(key=lambda x: x[1], reverse=True)
        
        self.hotspots = [
            {
                'file_path': file_path,
                'error_count': error_count,
                'error_types': list(set(e.error_type for e in self.errors_by_file[file_path])),
                'severity_breakdown': {
                    severity: len([e for e in self.errors_by_file[file_path] if e.severity.name == severity])
                    for severity in ['ERROR', 'WARNING', 'INFORMATION', 'HINT']
                }
            }
            for file_path, error_count in file_error_counts[:10]
        ]
    
    def _generate_recommendations(self):
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Error-based recommendations
        error_count = len([d for d in self.diagnostics if d.is_error])
        if error_count > 0:
            recommendations.append(f"🔴 CRITICAL: Fix {error_count} errors found in the codebase")
        
        warning_count = len([d for d in self.diagnostics if d.is_warning])
        if warning_count > 50:
            recommendations.append(f"🟡 HIGH: Address {warning_count} warnings to improve code quality")
        
        # Runtime error recommendations
        if len(self.runtime_errors) > 0:
            recommendations.append(f"⚡ RUNTIME: Investigate {len(self.runtime_errors)} runtime errors")
        
        # Quality recommendations
        if self.metrics.maintainability_index < 70:
            recommendations.append(f"📊 QUALITY: Improve maintainability index (currently {self.metrics.maintainability_index:.1f}/100)")
        
        if self.metrics.technical_debt_score > 100:
            recommendations.append(f"💳 DEBT: Reduce technical debt (score: {self.metrics.technical_debt_score})")
        
        # File-specific recommendations
        if self.hotspots:
            top_hotspot = self.hotspots[0]
            if top_hotspot['error_count'] > 10:
                recommendations.append(f"🔥 HOTSPOT: Focus on {top_hotspot['file_path']} ({top_hotspot['error_count']} errors)")
        
        # Type-specific recommendations
        if 'runtime' in self.errors_by_type and len(self.errors_by_type['runtime']) > 5:
            recommendations.append("🐛 RUNTIME: Add comprehensive error handling and input validation")
        
        if 'static' in self.errors_by_type and len(self.errors_by_type['static']) > 20:
            recommendations.append("🔍 STATIC: Run linters and static analysis tools regularly")
        
        self.recommendations = recommendations[:8]  # Limit to top 8 recommendations
    
    def get_summary(self) -> Dict[str, Any]:
        """Get analysis summary."""
        return {
            'repository': {
                'name': self.repository.name,
                'path': self.repository.local_path,
                'url': self.repository.url
            },
            'metrics': {
                'total_files': self.metrics.total_files,
                'total_lines': self.metrics.total_lines,
                'total_diagnostics': self.metrics.total_diagnostics,
                'error_density': self.metrics.error_density,
                'maintainability_index': self.metrics.maintainability_index,
                'technical_debt_score': self.metrics.technical_debt_score,
                'analysis_duration': self.metrics.analysis_duration
            },
            'breakdown': {
                'by_type': {k: len(v) for k, v in self.errors_by_type.items()},
                'by_severity': {k: len(v) for k, v in self.errors_by_severity.items()},
                'files_with_errors': len(self.errors_by_file)
            },
            'top_hotspots': self.hotspots[:5],
            'recommendations': self.recommendations
        }


class SerenaCodebaseAnalyzer:
    """
    Comprehensive codebase analyzer using enhanced Serena LSP integration.
    
    Features:
    - Static analysis via LSP servers
    - Runtime error collection and analysis
    - Serena-powered insights and recommendations
    - Repository cloning and analysis
    - Performance monitoring and caching
    """
    
    def __init__(self, work_dir: Optional[str] = None):
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self.work_dir.mkdir(exist_ok=True)
        
        # Analysis cache
        self.analysis_cache: Dict[str, ComprehensiveAnalysisResult] = {}
        
        # Performance tracking
        self.performance_stats = {
            'analyses_performed': 0,
            'total_analysis_time': 0.0,
            'average_analysis_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        logger.info(f"Serena codebase analyzer initialized with work_dir: {self.work_dir}")
    
    async def analyze_codebase(
        self,
        repo_path: str,
        enable_runtime_collection: bool = True,
        enable_serena_integration: bool = True,
        use_cache: bool = True
    ) -> ComprehensiveAnalysisResult:
        """
        Analyze a local codebase comprehensively.
        
        Args:
            repo_path: Path to the repository
            enable_runtime_collection: Whether to collect runtime errors
            enable_serena_integration: Whether to use Serena integration
            use_cache: Whether to use cached results
            
        Returns:
            Comprehensive analysis result
        """
        start_time = time.time()
        
        try:
            repo_info = RepositoryInfo.from_local_path(repo_path)
            
            # Check cache
            cache_key = f"local:{repo_path}"
            if use_cache and cache_key in self.analysis_cache:
                self.performance_stats['cache_hits'] += 1
                logger.info(f"Using cached analysis for {repo_path}")
                return self.analysis_cache[cache_key]
            
            self.performance_stats['cache_misses'] += 1
            
            # Create enhanced LSP bridge
            bridge = SerenaLSPBridge(
                repo_path,
                enable_runtime_collection=enable_runtime_collection,
                enable_serena_integration=enable_serena_integration
            )
            
            try:
                # Start runtime collection if enabled
                if enable_runtime_collection:
                    bridge.start_runtime_collection()
                
                # Perform comprehensive analysis
                result = await self._perform_comprehensive_analysis(bridge, repo_info)
                
                # Cache result
                self.analysis_cache[cache_key] = result
                
                # Update performance stats
                analysis_duration = time.time() - start_time
                self.performance_stats['analyses_performed'] += 1
                self.performance_stats['total_analysis_time'] += analysis_duration
                self.performance_stats['average_analysis_time'] = (
                    self.performance_stats['total_analysis_time'] / 
                    self.performance_stats['analyses_performed']
                )
                
                result.metrics.analysis_duration = analysis_duration
                result.metrics.calculate_derived_metrics()
                
                logger.info(f"Analysis completed in {analysis_duration:.2f}s: "
                           f"{result.metrics.total_diagnostics} diagnostics found")
                
                return result
                
            finally:
                # Stop runtime collection and shutdown bridge
                if enable_runtime_collection:
                    bridge.stop_runtime_collection()
                bridge.shutdown()
                
        except Exception as e:
            logger.error(f"Error analyzing codebase {repo_path}: {e}")
            # Return minimal result with error information
            return ComprehensiveAnalysisResult(
                repository=RepositoryInfo.from_local_path(repo_path),
                metrics=AnalysisMetrics(analysis_duration=time.time() - start_time)
            )
    
    async def analyze_github_repository(
        self,
        repo_url: str,
        branch: str = "main",
        clone_depth: Optional[int] = 1,
        enable_runtime_collection: bool = True,
        enable_serena_integration: bool = True,
        use_cache: bool = True
    ) -> ComprehensiveAnalysisResult:
        """
        Analyze a GitHub repository by URL.
        
        Args:
            repo_url: GitHub repository URL
            branch: Branch to analyze
            clone_depth: Clone depth for shallow clone
            enable_runtime_collection: Whether to collect runtime errors
            enable_serena_integration: Whether to use Serena integration
            use_cache: Whether to use cached results
            
        Returns:
            Comprehensive analysis result
        """
        start_time = time.time()
        
        try:
            # Create repository info
            local_path = self.work_dir / f"repo_{int(time.time())}"
            repo_info = RepositoryInfo.from_url(repo_url, str(local_path))
            repo_info.branch = branch
            repo_info.clone_depth = clone_depth
            
            # Check cache
            cache_key = f"{repo_url}:{branch}"
            if use_cache and cache_key in self.analysis_cache:
                self.performance_stats['cache_hits'] += 1
                logger.info(f"Using cached analysis for {repo_url}")
                return self.analysis_cache[cache_key]
            
            self.performance_stats['cache_misses'] += 1
            
            # Clone repository
            logger.info(f"Cloning repository: {repo_url}")
            await self._clone_repository(repo_info)
            
            # Analyze the cloned repository
            result = await self.analyze_codebase(
                str(local_path),
                enable_runtime_collection=enable_runtime_collection,
                enable_serena_integration=enable_serena_integration,
                use_cache=False  # Don't double-cache
            )
            
            # Update repository info in result
            result.repository = repo_info
            
            # Cache result
            self.analysis_cache[cache_key] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing GitHub repository {repo_url}: {e}")
            # Return minimal result with error information
            return ComprehensiveAnalysisResult(
                repository=RepositoryInfo.from_url(repo_url, ""),
                metrics=AnalysisMetrics(analysis_duration=time.time() - start_time)
            )
    
    async def _clone_repository(self, repo_info: RepositoryInfo):
        """Clone a GitHub repository."""
        try:
            cmd = ["git", "clone"]
            
            if repo_info.clone_depth:
                cmd.extend(["--depth", str(repo_info.clone_depth)])
            
            if repo_info.branch != "main":
                cmd.extend(["--branch", repo_info.branch])
            
            cmd.extend([repo_info.url, repo_info.local_path])
            
            # Run git clone
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"Git clone failed: {stderr.decode()}")
            
            logger.info(f"Successfully cloned {repo_info.url} to {repo_info.local_path}")
            
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            raise
    
    async def _perform_comprehensive_analysis(
        self,
        bridge: SerenaLSPBridge,
        repo_info: RepositoryInfo
    ) -> ComprehensiveAnalysisResult:
        """Perform comprehensive analysis using the LSP bridge."""
        try:
            # Get comprehensive analysis from bridge
            analysis_data = await bridge.get_comprehensive_analysis()
            
            # Extract diagnostics
            diagnostics_data = analysis_data.get('diagnostics', {})
            diagnostics = []
            
            for diag_dict in diagnostics_data.get('diagnostics', []):
                # Convert dict back to SerenaErrorInfo
                diagnostic = SerenaErrorInfo(
                    file_path=diag_dict['file_path'],
                    line=diag_dict['line'],
                    character=diag_dict['character'],
                    message=diag_dict['message'],
                    severity=getattr(bridge.DiagnosticSeverity, diag_dict['severity']),
                    source=diag_dict.get('source'),
                    code=diag_dict.get('code'),
                    end_line=diag_dict.get('end_line'),
                    end_character=diag_dict.get('end_character'),
                    error_type=diag_dict.get('error_type', 'static'),
                    context=diag_dict.get('context', {}),
                    suggestions=diag_dict.get('suggestions', []),
                    related_symbols=diag_dict.get('related_symbols', []),
                    fix_actions=diag_dict.get('fix_actions', [])
                )
                diagnostics.append(diagnostic)
            
            # Get runtime errors
            runtime_errors = bridge.get_runtime_errors()
            
            # Calculate metrics
            metrics = AnalysisMetrics()
            metrics.total_diagnostics = len(diagnostics)
            metrics.static_errors = len([d for d in diagnostics if d.error_type == 'static' and d.is_error])
            metrics.runtime_errors = len(runtime_errors)
            metrics.serena_insights = len(analysis_data.get('serena_analysis', {}))
            
            # Calculate file and line counts
            repo_path = Path(repo_info.local_path)
            for py_file in repo_path.rglob("*.py"):
                if not any(part.startswith('.') for part in py_file.parts):
                    metrics.total_files += 1
                    try:
                        with open(py_file, 'r', encoding='utf-8') as f:
                            metrics.total_lines += len(f.readlines())
                    except Exception:
                        pass
            
            # Get performance stats
            perf_stats = analysis_data.get('performance_stats', {})
            metrics.lsp_response_time = perf_stats.get('average_response_time', 0.0)
            
            # Create result
            result = ComprehensiveAnalysisResult(
                repository=repo_info,
                metrics=metrics,
                diagnostics=diagnostics,
                runtime_errors=runtime_errors,
                serena_insights=analysis_data.get('serena_analysis', {})
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing comprehensive analysis: {e}")
            return ComprehensiveAnalysisResult(
                repository=repo_info,
                metrics=AnalysisMetrics()
            )
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get summary of all analyses performed."""
        total_diagnostics = 0
        total_files = 0
        
        for result in self.analysis_cache.values():
            total_diagnostics += result.metrics.total_diagnostics
            total_files += result.metrics.total_files
        
        return {
            'analyses_performed': len(self.analysis_cache),
            'total_diagnostics': total_diagnostics,
            'total_files_analyzed': total_files,
            'performance_stats': self.performance_stats.copy(),
            'cache_size': len(self.analysis_cache)
        }
    
    def clear_cache(self, repo_identifier: Optional[str] = None):
        """Clear analysis cache."""
        if repo_identifier:
            # Clear specific repository
            keys_to_remove = [key for key in self.analysis_cache.keys() if repo_identifier in key]
            for key in keys_to_remove:
                self.analysis_cache.pop(key, None)
        else:
            # Clear all cache
            self.analysis_cache.clear()
        
        logger.info(f"Cache cleared for {repo_identifier or 'all repositories'}")


# Convenience functions
async def analyze_codebase_comprehensive(
    repo_path: str,
    **kwargs
) -> ComprehensiveAnalysisResult:
    """Analyze a local codebase comprehensively."""
    analyzer = SerenaCodebaseAnalyzer()
    return await analyzer.analyze_codebase(repo_path, **kwargs)


async def analyze_github_repository_comprehensive(
    repo_url: str,
    **kwargs
) -> ComprehensiveAnalysisResult:
    """Analyze a GitHub repository comprehensively."""
    analyzer = SerenaCodebaseAnalyzer()
    return await analyzer.analyze_github_repository(repo_url, **kwargs)


async def get_repository_quality_report(
    repo_path_or_url: str,
    **kwargs
) -> Dict[str, Any]:
    """Get a quality report for a repository."""
    if repo_path_or_url.startswith(('http://', 'https://')):
        result = await analyze_github_repository_comprehensive(repo_path_or_url, **kwargs)
    else:
        result = await analyze_codebase_comprehensive(repo_path_or_url, **kwargs)
    
    return result.get_summary()

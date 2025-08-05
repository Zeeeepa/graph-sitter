"""
Comprehensive GitHub Repository Error Analysis using Serena LSP Integration

This module provides a complete solution for analyzing GitHub repositories and
retrieving comprehensive error information organized by severity, with support
for real-time monitoring, filtering, and detailed context analysis using
official Serena and SolidLSP components.
"""

import asyncio
import logging
import tempfile
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable, Union, AsyncGenerator
from dataclasses import dataclass, field
from collections import defaultdict
from urllib.parse import urlparse

from graph_sitter.shared.logging.get_logger import get_logger
from .serena_bridge import SerenaLSPBridge, SerenaErrorInfo

# Import official solidlsp types
try:
    from solidlsp.ls_types import (
        DiagnosticSeverity, 
        Diagnostic, 
        Position, 
        Range, 
        MarkupContent,
        Location, 
        MarkupKind, 
        CompletionItemKind, 
        CompletionItem, 
        UnifiedSymbolInformation, 
        SymbolKind, 
        SymbolTag
    )
    from solidlsp.ls_utils import TextUtils, PathUtils, FileUtils, PlatformId, SymbolUtils
    from solidlsp.ls_request import LanguageServerRequest
    from solidlsp.ls_logger import LanguageServerLogger, LogLine
    from solidlsp.ls_handler import SolidLanguageServerHandler, Request, LanguageServerTerminatedException
    from solidlsp.ls import SolidLanguageServer, LSPFileBuffer
    SOLIDLSP_AVAILABLE = True
except ImportError as e:
    logger.warning(f"SolidLSP not available: {e}")
    SOLIDLSP_AVAILABLE = False

# Import official Serena components
try:
    from serena.symbol import (
        LanguageServerSymbolRetriever, 
        ReferenceInLanguageServerSymbol, 
        LanguageServerSymbol, 
        Symbol, 
        PositionInFile, 
        LanguageServerSymbolLocation
    )
    from serena.text_utils import MatchedConsecutiveLines, TextLine, LineType
    from serena.project import Project
    from serena.gui_log_viewer import GuiLogViewer, LogLevel, GuiLogViewerHandler
    from serena.code_editor import CodeEditor
    from serena.cli import (
        PromptCommands, ToolCommands, ProjectCommands, SerenaConfigCommands, 
        ContextCommands, ModeCommands, TopLevelCommands, AutoRegisteringGroup, ProjectType
    )
    SERENA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Serena components not available: {e}")
    SERENA_AVAILABLE = False

logger = get_logger(__name__)


# ============================================================================
# GITHUB REPOSITORY ANALYZER
# ============================================================================

@dataclass
class RepositoryInfo:
    """Information about a GitHub repository."""
    url: str
    name: str
    owner: str
    local_path: str
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
            local_path=local_path
        )


@dataclass
class AnalysisResult:
    """Result of repository analysis."""
    repository: RepositoryInfo
    errors: List[SerenaErrorInfo]
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_errors_by_severity(self) -> Dict[str, List[SerenaErrorInfo]]:
        """Get errors grouped by severity."""
        errors_by_severity = {
            'error': [e for e in self.errors if e.severity == DiagnosticSeverity.ERROR],
            'warning': [e for e in self.errors if e.severity == DiagnosticSeverity.WARNING],
            'info': [e for e in self.errors if e.severity == DiagnosticSeverity.INFORMATION],
            'hint': [e for e in self.errors if e.severity == DiagnosticSeverity.HINT]
        }
        return errors_by_severity
    
    def get_summary_by_severity(self) -> Dict[str, Dict[str, Any]]:
        """Get summary statistics by severity."""
        errors_by_severity = self.get_errors_by_severity()
        
        summary = {}
        for severity, errors in errors_by_severity.items():
            # Group by file
            file_counts = defaultdict(int)
            
            for error in errors:
                file_counts[error.file_path] += 1
            
            summary[severity] = {
                'count': len(errors),
                'files_affected': len(file_counts),
                'top_files': sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        
        return summary


class GitHubRepositoryAnalyzer:
    """
    Comprehensive GitHub repository error analyzer with Serena LSP integration.
    
    Features:
    - Repository cloning and management
    - Serena LSP server integration
    - Comprehensive error analysis by severity
    - Real-time error monitoring
    - Context-aware error reporting
    - Performance metrics and caching
    """
    
    def __init__(self, work_dir: Optional[str] = None, enable_runtime_collection: bool = True):
        self.work_dir = Path(work_dir) if work_dir else Path(tempfile.mkdtemp())
        self.work_dir.mkdir(exist_ok=True)
        
        self.enable_runtime_collection = enable_runtime_collection
        self.repositories: Dict[str, RepositoryInfo] = {}
        self.lsp_bridges: Dict[str, SerenaLSPBridge] = {}
        self.analysis_cache: Dict[str, AnalysisResult] = {}
        
        # Performance tracking
        self.performance_stats = {
            'repositories_analyzed': 0,
            'total_analysis_time': 0.0,
            'average_analysis_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }
        
        logger.info(f"GitHub Repository Analyzer initialized with work_dir: {self.work_dir}")
    
    async def analyze_repository_by_url(
        self,
        repo_url: str,
        branch: str = "main",
        clone_depth: Optional[int] = 1,
        use_cache: bool = True,
        severity_filter: Optional[List[DiagnosticSeverity]] = None
    ) -> AnalysisResult:
        """
        Analyze a GitHub repository by URL and return comprehensive error analysis.
        
        Args:
            repo_url: GitHub repository URL
            branch: Branch to analyze (default: main)
            clone_depth: Clone depth for shallow clone (default: 1)
            use_cache: Whether to use cached results
            severity_filter: Filter errors by severity levels
            
        Returns:
            AnalysisResult with comprehensive error information
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
                cached_result = self.analysis_cache[cache_key]
                logger.info(f"Using cached analysis for {repo_url}")
                return cached_result
            
            self.performance_stats['cache_misses'] += 1
            
            # Clone repository
            logger.info(f"Cloning repository: {repo_url}")
            await self._clone_repository(repo_info)
            
            # Initialize Serena LSP bridge
            logger.info(f"Initializing Serena LSP analysis for: {repo_info.name}")
            lsp_bridge = await self._initialize_lsp_bridge(repo_info)
            
            # Perform comprehensive analysis
            logger.info(f"Performing comprehensive error analysis...")
            errors = await self._analyze_repository_errors(
                lsp_bridge, 
                repo_info,
                severity_filter
            )
            
            # Create analysis result
            analysis_duration = time.time() - start_time
            
            result = AnalysisResult(
                repository=repo_info,
                errors=errors,
                analysis_metadata={
                    'analysis_time': analysis_duration,
                    'lsp_enabled': lsp_bridge.is_initialized,
                    'runtime_collection_enabled': self.enable_runtime_collection,
                    'files_analyzed': len(set(e.file_path for e in errors)),
                    'branch': branch,
                    'clone_depth': clone_depth,
                    'serena_available': SERENA_AVAILABLE,
                    'solidlsp_available': SOLIDLSP_AVAILABLE
                }
            )
            
            # Cache result
            self.analysis_cache[cache_key] = result
            self.repositories[cache_key] = repo_info
            self.lsp_bridges[cache_key] = lsp_bridge
            
            # Update performance stats
            self.performance_stats['repositories_analyzed'] += 1
            self.performance_stats['total_analysis_time'] += analysis_duration
            self.performance_stats['average_analysis_time'] = (
                self.performance_stats['total_analysis_time'] / 
                self.performance_stats['repositories_analyzed']
            )
            
            logger.info(f"Analysis completed in {analysis_duration:.2f}s: "
                       f"{len(errors)} total errors found")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing repository {repo_url}: {e}")
            # Return empty result with error information
            return AnalysisResult(
                repository=RepositoryInfo.from_url(repo_url, ""),
                errors=[],
                analysis_metadata={
                    'error': str(e),
                    'analysis_time': time.time() - start_time
                }
            )
    
    async def get_file_errors(
        self,
        repo_url: str,
        file_path: str,
        branch: str = "main"
    ) -> List[SerenaErrorInfo]:
        """Get errors for a specific file in a repository."""
        try:
            cache_key = f"{repo_url}:{branch}"
            
            # Ensure repository is analyzed
            if cache_key not in self.lsp_bridges:
                await self.analyze_repository_by_url(repo_url, branch)
            
            lsp_bridge = self.lsp_bridges.get(cache_key)
            if not lsp_bridge:
                return []
            
            # Get file-specific errors
            file_errors = lsp_bridge.get_file_diagnostics(file_path)
            return file_errors
            
        except Exception as e:
            logger.error(f"Error getting file errors: {e}")
            return []
    
    async def get_real_time_errors(
        self,
        repo_url: str,
        branch: str = "main",
        poll_interval: float = 5.0
    ) -> AsyncGenerator[List[SerenaErrorInfo], None]:
        """Get real-time error updates for a repository."""
        try:
            cache_key = f"{repo_url}:{branch}"
            
            # Ensure repository is analyzed
            if cache_key not in self.lsp_bridges:
                await self.analyze_repository_by_url(repo_url, branch)
            
            lsp_bridge = self.lsp_bridges.get(cache_key)
            if not lsp_bridge:
                return
            
            last_error_count = 0
            
            while True:
                try:
                    # Get current errors
                    current_errors = lsp_bridge.get_diagnostics(include_runtime=True, include_serena=True)
                    
                    # Yield if there are changes
                    if len(current_errors) != last_error_count:
                        last_error_count = len(current_errors)
                        yield current_errors
                    
                    await asyncio.sleep(poll_interval)
                    
                except Exception as e:
                    logger.error(f"Error in real-time monitoring: {e}")
                    await asyncio.sleep(poll_interval)
                    
        except Exception as e:
            logger.error(f"Error setting up real-time monitoring: {e}")
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get comprehensive analysis summary."""
        total_errors = 0
        total_files = 0
        severity_breakdown = defaultdict(int)
        
        for result in self.analysis_cache.values():
            total_errors += len(result.errors)
            total_files += len(set(e.file_path for e in result.errors))
            
            for error in result.errors:
                if error.severity == DiagnosticSeverity.ERROR:
                    severity_breakdown['error'] += 1
                elif error.severity == DiagnosticSeverity.WARNING:
                    severity_breakdown['warning'] += 1
                elif error.severity == DiagnosticSeverity.INFORMATION:
                    severity_breakdown['info'] += 1
                elif error.severity == DiagnosticSeverity.HINT:
                    severity_breakdown['hint'] += 1
        
        return {
            'repositories_analyzed': len(self.analysis_cache),
            'total_errors': total_errors,
            'total_files_analyzed': total_files,
            'severity_breakdown': dict(severity_breakdown),
            'performance_stats': self.performance_stats.copy(),
            'cache_size': len(self.analysis_cache),
            'serena_available': SERENA_AVAILABLE,
            'solidlsp_available': SOLIDLSP_AVAILABLE
        }
    
    def clear_cache(self, repo_url: Optional[str] = None):
        """Clear analysis cache."""
        if repo_url:
            cache_keys_to_remove = [key for key in self.analysis_cache.keys() if repo_url in key]
            for key in cache_keys_to_remove:
                self.analysis_cache.pop(key, None)
                self.repositories.pop(key, None)
                if key in self.lsp_bridges:
                    self.lsp_bridges[key].shutdown()
                    self.lsp_bridges.pop(key, None)
        else:
            # Clear all caches
            for lsp_bridge in self.lsp_bridges.values():
                lsp_bridge.shutdown()
            
            self.analysis_cache.clear()
            self.repositories.clear()
            self.lsp_bridges.clear()
        
        logger.info(f"Cache cleared for {repo_url or 'all repositories'}")
    
    async def shutdown(self):
        """Shutdown the analyzer and clean up resources."""
        try:
            # Shutdown all LSP bridges
            for lsp_bridge in self.lsp_bridges.values():
                lsp_bridge.shutdown()
            
            # Clear all caches
            self.analysis_cache.clear()
            self.repositories.clear()
            self.lsp_bridges.clear()
            
            logger.info("GitHub Repository Analyzer shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
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
    
    async def _initialize_lsp_bridge(self, repo_info: RepositoryInfo) -> SerenaLSPBridge:
        """Initialize Serena LSP bridge for repository analysis."""
        try:
            lsp_bridge = SerenaLSPBridge(
                repo_info.local_path,
                enable_runtime_collection=self.enable_runtime_collection
            )
            
            # Wait a moment for initialization
            await asyncio.sleep(1.0)
            
            return lsp_bridge
            
        except Exception as e:
            logger.error(f"Error initializing LSP bridge: {e}")
            # Return a minimal bridge for basic functionality
            return SerenaLSPBridge(repo_info.local_path, enable_runtime_collection=False)
    
    async def _analyze_repository_errors(
        self,
        lsp_bridge: SerenaLSPBridge,
        repo_info: RepositoryInfo,
        severity_filter: Optional[List[DiagnosticSeverity]] = None
    ) -> List[SerenaErrorInfo]:
        """Perform comprehensive error analysis on repository."""
        try:
            # Get all diagnostics from Serena LSP bridge
            all_errors = lsp_bridge.get_diagnostics(include_runtime=True, include_serena=True)
            
            # Apply severity filter
            if severity_filter:
                filtered_errors = []
                for error in all_errors:
                    if error.severity in severity_filter:
                        filtered_errors.append(error)
                return filtered_errors
            
            return all_errors
            
        except Exception as e:
            logger.error(f"Error analyzing repository errors: {e}")
            return []


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def analyze_github_repository(
    repo_url: str,
    branch: str = "main",
    severity_filter: Optional[List[str]] = None,
    work_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to analyze a GitHub repository and get errors by severity.
    
    Args:
        repo_url: GitHub repository URL
        branch: Branch to analyze
        severity_filter: List of severity levels to include ('error', 'warning', 'info', 'hint')
        work_dir: Working directory for cloning
        
    Returns:
        Dictionary with comprehensive error analysis
    """
    analyzer = GitHubRepositoryAnalyzer(work_dir=work_dir)
    
    try:
        # Convert string severity filter to DiagnosticSeverity enum
        severity_enum_filter = None
        if severity_filter and SOLIDLSP_AVAILABLE:
            severity_map = {
                'error': DiagnosticSeverity.ERROR,
                'warning': DiagnosticSeverity.WARNING,
                'info': DiagnosticSeverity.INFORMATION,
                'hint': DiagnosticSeverity.HINT
            }
            severity_enum_filter = [severity_map[s] for s in severity_filter if s in severity_map]
        
        # Analyze repository
        result = await analyzer.analyze_repository_by_url(
            repo_url=repo_url,
            branch=branch,
            severity_filter=severity_enum_filter
        )
        
        # Format results
        errors_by_severity = result.get_errors_by_severity()
        summary_by_severity = result.get_summary_by_severity()
        
        return {
            'repository': {
                'url': result.repository.url,
                'name': result.repository.name,
                'owner': result.repository.owner,
                'branch': result.repository.branch
            },
            'analysis': {
                'total_errors': len(result.errors),
                'critical_errors': len([e for e in result.errors if e.severity == DiagnosticSeverity.ERROR]),
                'warnings': len([e for e in result.errors if e.severity == DiagnosticSeverity.WARNING]),
                'info_hints': len([e for e in result.errors if e.severity in [DiagnosticSeverity.INFORMATION, DiagnosticSeverity.HINT]]),
                'files_analyzed': len(set(e.file_path for e in result.errors)),
                'analysis_duration': result.analysis_metadata.get('analysis_time', 0)
            },
            'errors_by_severity': {
                severity: [error.to_dict() for error in errors]
                for severity, errors in errors_by_severity.items()
            },
            'summary_by_severity': summary_by_severity,
            'metadata': result.analysis_metadata
        }
        
    finally:
        await analyzer.shutdown()


async def get_repository_error_summary(
    repo_url: str,
    branch: str = "main",
    work_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get a quick error summary for a GitHub repository.
    
    Args:
        repo_url: GitHub repository URL
        branch: Branch to analyze
        work_dir: Working directory for cloning
        
    Returns:
        Dictionary with error summary statistics
    """
    result = await analyze_github_repository(repo_url, branch, work_dir=work_dir)
    
    return {
        'repository': result['repository'],
        'summary': result['analysis'],
        'severity_breakdown': {
            severity: summary['count']
            for severity, summary in result['summary_by_severity'].items()
        },
        'most_problematic_files': result['summary_by_severity'].get('error', {}).get('top_files', [])
    }


async def analyze_multiple_repositories(
    repo_urls: List[str],
    branch: str = "main",
    max_concurrent: int = 3,
    work_dir: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze multiple GitHub repositories concurrently.
    
    Args:
        repo_urls: List of GitHub repository URLs
        branch: Branch to analyze
        max_concurrent: Maximum concurrent analyses
        work_dir: Working directory for cloning
        
    Returns:
        Dictionary mapping repo URLs to analysis results
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def analyze_single_repo(url: str) -> tuple[str, Dict[str, Any]]:
        async with semaphore:
            try:
                result = await analyze_github_repository(url, branch, work_dir=work_dir)
                return url, result
            except Exception as e:
                logger.error(f"Error analyzing {url}: {e}")
                return url, {'error': str(e)}
    
    # Run analyses concurrently
    tasks = [analyze_single_repo(url) for url in repo_urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Format results
    analysis_results = {}
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Analysis failed: {result}")
            continue
        
        url, analysis = result
        analysis_results[url] = analysis
    
    return analysis_results


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze GitHub repository for errors using Serena LSP")
    parser.add_argument("repo_url", help="GitHub repository URL")
    parser.add_argument("--branch", default="main", help="Branch to analyze")
    parser.add_argument("--severity", nargs="+", choices=["error", "warning", "info", "hint"],
                       help="Severity levels to include")
    parser.add_argument("--work-dir", help="Working directory for cloning")
    parser.add_argument("--output", choices=["summary", "full"], default="summary",
                       help="Output format")
    
    args = parser.parse_args()
    
    try:
        if args.output == "summary":
            result = await get_repository_error_summary(
                args.repo_url,
                args.branch,
                args.work_dir
            )
        else:
            result = await analyze_github_repository(
                args.repo_url,
                args.branch,
                args.severity,
                args.work_dir
            )
        
        import json
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))


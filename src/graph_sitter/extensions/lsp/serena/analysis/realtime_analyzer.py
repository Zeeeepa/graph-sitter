"""
Real-time Analysis Engine

Provides continuous code analysis and quality monitoring.
"""

import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed

from graph_sitter.shared.logging.get_logger import get_logger
from graph_sitter.core.codebase import Codebase
from graph_sitter.extensions.lsp.serena_bridge import SerenaLSPBridge

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    """Result of real-time analysis."""
    file_path: str
    timestamp: float
    issues: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    suggestions: List[str]
    complexity_score: float
    maintainability_score: float


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis."""
    issue_type: str
    severity: str  # error, warning, info
    message: str
    file_path: str
    line_number: int
    column_number: int
    suggestion: Optional[str] = None


class RealtimeAnalyzer:
    """
    Real-time code analysis engine.
    
    Continuously monitors code changes and provides instant feedback
    on code quality, potential issues, and improvement suggestions.
    """
    
    def __init__(self, codebase: Codebase, lsp_bridge: SerenaLSPBridge, config: Optional[Dict[str, Any]] = None):
        self.codebase = codebase
        self.lsp_bridge = lsp_bridge
        self.config = config or {}
        
        # Analysis state
        self._analysis_cache: Dict[str, AnalysisResult] = {}
        self._file_watchers: Dict[str, float] = {}  # file_path -> last_modified
        self._analysis_queue: Set[str] = set()
        
        # Threading
        self._analysis_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="RealtimeAnalysis")
        
        # Configuration
        self.analysis_interval = self.config.get('analysis_interval', 1.0)  # seconds
        self.max_file_size = self.config.get('max_file_size', 1024 * 1024)  # 1MB
        self.enabled_checks = self.config.get('enabled_checks', [
            'syntax_errors',
            'unused_imports',
            'undefined_variables',
            'complexity_analysis',
            'style_violations'
        ])
        
        logger.info("Real-time analyzer initialized")
    
    def start(self) -> None:
        """Start the real-time analysis engine."""
        if self._analysis_thread and self._analysis_thread.is_alive():
            logger.warning("Real-time analyzer is already running")
            return
        
        self._stop_event.clear()
        self._analysis_thread = threading.Thread(
            target=self._analysis_loop,
            name="RealtimeAnalysisLoop",
            daemon=True
        )
        self._analysis_thread.start()
        
        logger.info("Real-time analyzer started")
    
    def stop(self) -> None:
        """Stop the real-time analysis engine."""
        if not self._analysis_thread or not self._analysis_thread.is_alive():
            return
        
        self._stop_event.set()
        self._analysis_thread.join(timeout=5.0)
        self._executor.shutdown(wait=True)
        
        logger.info("Real-time analyzer stopped")
    
    def analyze_file(self, file_path: str, force: bool = False) -> Optional[AnalysisResult]:
        """
        Analyze a specific file.
        
        Args:
            file_path: Path to the file to analyze
            force: Force analysis even if file hasn't changed
        
        Returns:
            Analysis result or None if analysis failed
        """
        try:
            # Check if file exists and is analyzable
            if not self._should_analyze_file(file_path, force):
                return self._analysis_cache.get(file_path)
            
            # Get file from codebase
            file_obj = self.codebase.get_file(file_path, optional=True)
            if not file_obj:
                return None
            
            # Perform analysis
            start_time = time.time()
            
            # Collect issues from various checks
            issues = []
            metrics = {}
            suggestions = []
            
            # Syntax errors from LSP
            if 'syntax_errors' in self.enabled_checks:
                syntax_issues = self._check_syntax_errors(file_path)
                issues.extend(syntax_issues)
            
            # Unused imports
            if 'unused_imports' in self.enabled_checks:
                unused_imports = self._check_unused_imports(file_obj)
                issues.extend(unused_imports)
                if unused_imports:
                    suggestions.append("Remove unused imports to improve code clarity")
            
            # Undefined variables
            if 'undefined_variables' in self.enabled_checks:
                undefined_vars = self._check_undefined_variables(file_obj)
                issues.extend(undefined_vars)
            
            # Complexity analysis
            if 'complexity_analysis' in self.enabled_checks:
                complexity_metrics = self._analyze_complexity(file_obj)
                metrics.update(complexity_metrics)
                
                if complexity_metrics.get('cyclomatic_complexity', 0) > 10:
                    suggestions.append("Consider breaking down complex functions")
            
            # Style violations
            if 'style_violations' in self.enabled_checks:
                style_issues = self._check_style_violations(file_obj)
                issues.extend(style_issues)
            
            # Calculate scores
            complexity_score = self._calculate_complexity_score(metrics)
            maintainability_score = self._calculate_maintainability_score(issues, metrics)
            
            # Create analysis result
            result = AnalysisResult(
                file_path=file_path,
                timestamp=time.time(),
                issues=[issue.__dict__ for issue in issues],
                metrics=metrics,
                suggestions=suggestions,
                complexity_score=complexity_score,
                maintainability_score=maintainability_score
            )
            
            # Cache result
            self._analysis_cache[file_path] = result
            self._file_watchers[file_path] = start_time
            
            elapsed = time.time() - start_time
            logger.debug(f"Analyzed {file_path} in {elapsed:.3f}s - {len(issues)} issues found")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return None
    
    def get_analysis_results(self, file_paths: Optional[List[str]] = None) -> Dict[str, AnalysisResult]:
        """Get analysis results for specified files or all analyzed files."""
        if file_paths is None:
            return self._analysis_cache.copy()
        
        return {
            path: result for path, result in self._analysis_cache.items()
            if path in file_paths
        }
    
    def queue_analysis(self, file_path: str) -> None:
        """Queue a file for analysis."""
        self._analysis_queue.add(file_path)
    
    def get_status(self) -> Dict[str, Any]:
        """Get analyzer status."""
        return {
            'running': self._analysis_thread and self._analysis_thread.is_alive(),
            'analyzed_files': len(self._analysis_cache),
            'queued_files': len(self._analysis_queue),
            'enabled_checks': self.enabled_checks,
            'analysis_interval': self.analysis_interval
        }
    
    def _analysis_loop(self) -> None:
        """Main analysis loop running in background thread."""
        logger.info("Real-time analysis loop started")
        
        while not self._stop_event.is_set():
            try:
                # Process queued files
                files_to_analyze = list(self._analysis_queue)
                self._analysis_queue.clear()
                
                # Analyze files concurrently
                if files_to_analyze:
                    futures = []
                    for file_path in files_to_analyze:
                        future = self._executor.submit(self.analyze_file, file_path)
                        futures.append((file_path, future))
                    
                    # Collect results
                    for file_path, future in futures:
                        try:
                            future.result(timeout=10.0)
                        except Exception as e:
                            logger.error(f"Error analyzing {file_path}: {e}")
                
                # Sleep until next iteration
                self._stop_event.wait(self.analysis_interval)
                
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}")
                self._stop_event.wait(1.0)
        
        logger.info("Real-time analysis loop stopped")
    
    def _should_analyze_file(self, file_path: str, force: bool) -> bool:
        """Check if file should be analyzed."""
        if force:
            return True
        
        # Check file size
        try:
            file_size = Path(file_path).stat().st_size
            if file_size > self.max_file_size:
                return False
        except Exception:
            return False
        
        # Check if file has been modified
        try:
            last_modified = Path(file_path).stat().st_mtime
            cached_time = self._file_watchers.get(file_path, 0)
            return last_modified > cached_time
        except Exception:
            return True
    
    def _check_syntax_errors(self, file_path: str) -> List[CodeIssue]:
        """Check for syntax errors using LSP diagnostics."""
        issues = []
        
        try:
            diagnostics = self.lsp_bridge.get_file_diagnostics(file_path)
            for diagnostic in diagnostics:
                if diagnostic.is_error:
                    issues.append(CodeIssue(
                        issue_type="syntax_error",
                        severity="error",
                        message=diagnostic.message,
                        file_path=file_path,
                        line_number=diagnostic.line,
                        column_number=diagnostic.character
                    ))
        except Exception as e:
            logger.debug(f"Error checking syntax errors: {e}")
        
        return issues
    
    def _check_unused_imports(self, file_obj) -> List[CodeIssue]:
        """Check for unused imports."""
        issues = []
        
        try:
            # Get all imports in the file
            imports = getattr(file_obj, 'imports', [])
            
            for import_obj in imports:
                # Simple heuristic: check if import name appears in file content
                import_name = getattr(import_obj, 'name', '')
                if import_name:
                    file_content = str(file_obj.content)
                    # Count occurrences (import statement + usage)
                    occurrences = file_content.count(import_name)
                    
                    # If only appears once (the import itself), it's likely unused
                    if occurrences <= 1:
                        issues.append(CodeIssue(
                            issue_type="unused_import",
                            severity="warning",
                            message=f"Unused import: {import_name}",
                            file_path=file_obj.filepath,
                            line_number=getattr(import_obj, 'line_number', 0),
                            column_number=0,
                            suggestion=f"Remove unused import: {import_name}"
                        ))
        except Exception as e:
            logger.debug(f"Error checking unused imports: {e}")
        
        return issues
    
    def _check_undefined_variables(self, file_obj) -> List[CodeIssue]:
        """Check for undefined variables."""
        issues = []
        
        try:
            # This would require more sophisticated analysis
            # For now, return empty list as placeholder
            pass
        except Exception as e:
            logger.debug(f"Error checking undefined variables: {e}")
        
        return issues
    
    def _analyze_complexity(self, file_obj) -> Dict[str, Any]:
        """Analyze code complexity metrics."""
        metrics = {
            'cyclomatic_complexity': 0,
            'lines_of_code': 0,
            'function_count': 0,
            'class_count': 0
        }
        
        try:
            # Count lines of code
            content = str(file_obj.content)
            lines = [line.strip() for line in content.split('\n')]
            metrics['lines_of_code'] = len([line for line in lines if line and not line.startswith('#')])
            
            # Count functions and classes
            symbols = getattr(file_obj, 'symbols', [])
            for symbol in symbols:
                if hasattr(symbol, 'symbol_type'):
                    symbol_type = str(symbol.symbol_type).lower()
                    if 'function' in symbol_type:
                        metrics['function_count'] += 1
                    elif 'class' in symbol_type:
                        metrics['class_count'] += 1
            
            # Simple cyclomatic complexity (count decision points)
            decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with']
            for keyword in decision_keywords:
                metrics['cyclomatic_complexity'] += content.count(f' {keyword} ')
                metrics['cyclomatic_complexity'] += content.count(f'\n{keyword} ')
            
        except Exception as e:
            logger.debug(f"Error analyzing complexity: {e}")
        
        return metrics
    
    def _check_style_violations(self, file_obj) -> List[CodeIssue]:
        """Check for style violations."""
        issues = []
        
        try:
            content = str(file_obj.content)
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                line_num = i + 1
                
                # Check line length
                if len(line) > 100:
                    issues.append(CodeIssue(
                        issue_type="line_too_long",
                        severity="info",
                        message=f"Line too long ({len(line)} > 100 characters)",
                        file_path=file_obj.filepath,
                        line_number=line_num,
                        column_number=100,
                        suggestion="Break long line into multiple lines"
                    ))
                
                # Check trailing whitespace
                if line.endswith(' ') or line.endswith('\t'):
                    issues.append(CodeIssue(
                        issue_type="trailing_whitespace",
                        severity="info",
                        message="Trailing whitespace",
                        file_path=file_obj.filepath,
                        line_number=line_num,
                        column_number=len(line.rstrip()),
                        suggestion="Remove trailing whitespace"
                    ))
        
        except Exception as e:
            logger.debug(f"Error checking style violations: {e}")
        
        return issues
    
    def _calculate_complexity_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate complexity score (0-1, lower is better)."""
        try:
            complexity = metrics.get('cyclomatic_complexity', 0)
            loc = metrics.get('lines_of_code', 1)
            
            # Normalize complexity by lines of code
            normalized_complexity = complexity / max(loc, 1)
            
            # Convert to 0-1 score (capped at 1.0)
            return min(normalized_complexity * 10, 1.0)
        except Exception:
            return 0.5
    
    def _calculate_maintainability_score(self, issues: List[CodeIssue], metrics: Dict[str, Any]) -> float:
        """Calculate maintainability score (0-1, higher is better)."""
        try:
            # Start with perfect score
            score = 1.0
            
            # Deduct points for issues
            error_count = len([issue for issue in issues if issue.severity == 'error'])
            warning_count = len([issue for issue in issues if issue.severity == 'warning'])
            info_count = len([issue for issue in issues if issue.severity == 'info'])
            
            score -= error_count * 0.1
            score -= warning_count * 0.05
            score -= info_count * 0.01
            
            # Deduct points for complexity
            complexity_score = self._calculate_complexity_score(metrics)
            score -= complexity_score * 0.2
            
            return max(score, 0.0)
        except Exception:
            return 0.5


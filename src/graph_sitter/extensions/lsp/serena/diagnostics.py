"""
Consolidated Diagnostics for Serena Integration

This module consolidates error analysis, diagnostics processing, and 
comprehensive error detection from multiple source files.
"""

import ast
import inspect
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import traceback

from .types import ErrorSeverity, ErrorCategory, CodeError, DiagnosticStats

try:
    from graph_sitter.shared.logging.get_logger import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class ErrorContext:
    """Comprehensive error context information."""
    error: CodeError
    calling_functions: List[Dict[str, Any]] = field(default_factory=list)
    called_functions: List[Dict[str, Any]] = field(default_factory=list)
    parameter_issues: List[Dict[str, Any]] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    related_symbols: List[Dict[str, Any]] = field(default_factory=list)
    code_context: Optional[str] = None
    fix_suggestions: List[str] = field(default_factory=list)


@dataclass
class ParameterIssue:
    """Parameter usage issue."""
    issue_type: str  # unused, wrong_type, missing, invalid_value
    parameter_name: str
    function_name: str
    file_path: str
    line_number: int
    expected_type: Optional[str] = None
    actual_type: Optional[str] = None
    description: str = ""


@dataclass
class ErrorCluster:
    """Group of related errors."""
    cluster_id: str
    primary_error: CodeError
    related_errors: List[CodeError]
    common_cause: str
    fix_priority: int  # 1-10, higher is more urgent
    estimated_fix_time: str  # "5 minutes", "1 hour", etc.


@dataclass
class ErrorVisualization:
    """Error visualization data."""
    error_hotspots: List[Dict[str, Any]]
    error_trends: List[Dict[str, Any]]
    dependency_graph: Dict[str, Any]
    complexity_metrics: Dict[str, float]


class DiagnosticProcessor:
    """
    Processes and analyzes diagnostic information.
    Consolidated from lsp/diagnostics.py.
    """
    
    def __init__(self):
        self.diagnostics: List[CodeError] = []
        self.error_contexts: Dict[str, ErrorContext] = {}
        self.clusters: List[ErrorCluster] = []
        
    def add_diagnostic(self, diagnostic: CodeError) -> None:
        """Add a diagnostic to the processor."""
        self.diagnostics.append(diagnostic)
        
    def add_diagnostics(self, diagnostics: List[CodeError]) -> None:
        """Add multiple diagnostics."""
        self.diagnostics.extend(diagnostics)
        
    def get_diagnostics_by_severity(self, severity: ErrorSeverity) -> List[CodeError]:
        """Get diagnostics by severity level."""
        return [d for d in self.diagnostics if d.severity == severity]
        
    def get_diagnostics_by_file(self, file_path: str) -> List[CodeError]:
        """Get diagnostics for a specific file."""
        return [d for d in self.diagnostics if d.file_path == file_path]
        
    def get_diagnostics_by_category(self, category: ErrorCategory) -> List[CodeError]:
        """Get diagnostics by category."""
        return [d for d in self.diagnostics if d.category == category]
        
    def get_error_hotspots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get files with the most errors."""
        file_error_counts = defaultdict(int)
        for diag in self.diagnostics:
            if diag.severity == ErrorSeverity.ERROR:
                file_error_counts[diag.file_path] += 1
                
        hotspots = []
        for file_path, count in sorted(file_error_counts.items(), key=lambda x: x[1], reverse=True)[:limit]:
            hotspots.append({
                'file_path': file_path,
                'error_count': count,
                'errors': self.get_diagnostics_by_file(file_path)
            })
            
        return hotspots
        
    def cluster_related_errors(self) -> List[ErrorCluster]:
        """Group related errors into clusters."""
        clusters = []
        processed_errors = set()
        
        for i, error in enumerate(self.diagnostics):
            if i in processed_errors:
                continue
                
            # Find related errors (same file, similar message, etc.)
            related = []
            for j, other_error in enumerate(self.diagnostics[i+1:], i+1):
                if j in processed_errors:
                    continue
                    
                if self._are_errors_related(error, other_error):
                    related.append(other_error)
                    processed_errors.add(j)
                    
            if related:
                cluster = ErrorCluster(
                    cluster_id=f"cluster_{len(clusters)}",
                    primary_error=error,
                    related_errors=related,
                    common_cause=self._determine_common_cause(error, related),
                    fix_priority=self._calculate_fix_priority(error, related),
                    estimated_fix_time=self._estimate_fix_time(error, related)
                )
                clusters.append(cluster)
                processed_errors.add(i)
                
        self.clusters = clusters
        return clusters
        
    def _are_errors_related(self, error1: CodeError, error2: CodeError) -> bool:
        """Determine if two errors are related."""
        # Same file
        if error1.file_path == error2.file_path:
            # Close line numbers
            if abs(error1.line - error2.line) <= 5:
                return True
            # Similar messages
            if self._message_similarity(error1.message, error2.message) > 0.7:
                return True
                
        # Same error code
        if error1.code and error2.code and error1.code == error2.code:
            return True
            
        return False
        
    def _message_similarity(self, msg1: str, msg2: str) -> float:
        """Calculate similarity between error messages."""
        words1 = set(msg1.lower().split())
        words2 = set(msg2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
        
    def _determine_common_cause(self, primary: CodeError, related: List[CodeError]) -> str:
        """Determine the common cause of related errors."""
        # Simple heuristics - could be improved
        if primary.category == ErrorCategory.IMPORT:
            return "Import issues"
        elif primary.category == ErrorCategory.TYPE:
            return "Type annotation problems"
        elif primary.category == ErrorCategory.SYNTAX:
            return "Syntax errors"
        else:
            return "Related code issues"
            
    def _calculate_fix_priority(self, primary: CodeError, related: List[CodeError]) -> int:
        """Calculate fix priority (1-10)."""
        priority = 5  # Base priority
        
        # Higher priority for errors vs warnings
        if primary.severity == ErrorSeverity.ERROR:
            priority += 3
        elif primary.severity == ErrorSeverity.WARNING:
            priority += 1
            
        # Higher priority for more related errors
        priority += min(len(related), 3)
        
        return min(priority, 10)
        
    def _estimate_fix_time(self, primary: CodeError, related: List[CodeError]) -> str:
        """Estimate time to fix the error cluster."""
        total_errors = 1 + len(related)
        
        if total_errors == 1:
            return "5 minutes"
        elif total_errors <= 3:
            return "15 minutes"
        elif total_errors <= 10:
            return "1 hour"
        else:
            return "2+ hours"


class DiagnosticFilter:
    """
    Filters diagnostics based on various criteria.
    Consolidated from lsp/diagnostics.py.
    """
    
    def __init__(self):
        self.severity_filter: Optional[Set[ErrorSeverity]] = None
        self.category_filter: Optional[Set[ErrorCategory]] = None
        self.file_pattern_filter: Optional[str] = None
        self.exclude_patterns: List[str] = []
        
    def set_severity_filter(self, severities: List[ErrorSeverity]) -> None:
        """Set severity filter."""
        self.severity_filter = set(severities)
        
    def set_category_filter(self, categories: List[ErrorCategory]) -> None:
        """Set category filter."""
        self.category_filter = set(categories)
        
    def set_file_pattern_filter(self, pattern: str) -> None:
        """Set file pattern filter."""
        self.file_pattern_filter = pattern
        
    def add_exclude_pattern(self, pattern: str) -> None:
        """Add pattern to exclude."""
        self.exclude_patterns.append(pattern)
        
    def filter_diagnostics(self, diagnostics: List[CodeError]) -> List[CodeError]:
        """Apply all filters to diagnostics."""
        filtered = diagnostics
        
        # Apply severity filter
        if self.severity_filter:
            filtered = [d for d in filtered if d.severity in self.severity_filter]
            
        # Apply category filter
        if self.category_filter:
            filtered = [d for d in filtered if d.category in self.category_filter]
            
        # Apply file pattern filter
        if self.file_pattern_filter:
            import fnmatch
            filtered = [d for d in filtered if fnmatch.fnmatch(d.file_path, self.file_pattern_filter)]
            
        # Apply exclude patterns
        for pattern in self.exclude_patterns:
            import fnmatch
            filtered = [d for d in filtered if not fnmatch.fnmatch(d.file_path, pattern)]
            
        return filtered


class DiagnosticAggregator:
    """
    Aggregates diagnostic statistics and trends.
    Consolidated from lsp/diagnostics.py.
    """
    
    def __init__(self):
        self._stats_history: deque = deque(maxlen=100)
        self._current_stats = DiagnosticStats()
        
    def update_stats(self, diagnostics: List[CodeError]) -> None:
        """Update statistics with new diagnostics."""
        stats = DiagnosticStats()
        
        # Count by severity
        for diag in diagnostics:
            if diag.severity == ErrorSeverity.ERROR:
                stats.total_errors += 1
            elif diag.severity == ErrorSeverity.WARNING:
                stats.total_warnings += 1
            elif diag.severity == ErrorSeverity.INFO:
                stats.total_info += 1
            elif diag.severity == ErrorSeverity.HINT:
                stats.total_hints += 1
                
        # Count files with errors
        files_with_errors = set()
        for diag in diagnostics:
            if diag.severity == ErrorSeverity.ERROR:
                files_with_errors.add(diag.file_path)
        stats.files_with_errors = len(files_with_errors)
        
        # Find most common errors
        error_messages = defaultdict(int)
        for diag in diagnostics:
            if diag.severity == ErrorSeverity.ERROR:
                # Normalize message for counting
                normalized = diag.message.split(':')[0].strip()
                error_messages[normalized] += 1
                
        stats.most_common_errors = [
            msg for msg, count in sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        self._current_stats = stats
        self._stats_history.append(stats)
        
    def get_current_stats(self) -> DiagnosticStats:
        """Get current diagnostic statistics."""
        return self._current_stats
        
    def get_historical_stats(self, count: int = 10) -> List[DiagnosticStats]:
        """Get historical statistics."""
        return list(self._stats_history)[-count:]
        
    def get_trends(self) -> Dict[str, Any]:
        """Get diagnostic trends over time."""
        if len(self._stats_history) < 2:
            return {}
            
        current = self._stats_history[-1]
        previous = self._stats_history[-2]
        
        return {
            'error_trend': current.total_errors - previous.total_errors,
            'warning_trend': current.total_warnings - previous.total_warnings,
            'files_trend': current.files_with_errors - previous.files_with_errors,
            'improvement': (previous.total_errors - current.total_errors) > 0
        }


class ComprehensiveErrorAnalyzer:
    """
    Comprehensive error analysis system.
    Consolidated from error_analysis.py and advanced_error_viewer.py.
    """
    
    def __init__(self, codebase=None):
        self.codebase = codebase
        self.processor = DiagnosticProcessor()
        self.filter = DiagnosticFilter()
        self.aggregator = DiagnosticAggregator()
        self.error_contexts: Dict[str, ErrorContext] = {}
        
    def analyze_errors(self, diagnostics: List[CodeError]) -> Dict[str, Any]:
        """Perform comprehensive error analysis."""
        # Process diagnostics
        self.processor.add_diagnostics(diagnostics)
        self.aggregator.update_stats(diagnostics)
        
        # Cluster related errors
        clusters = self.processor.cluster_related_errors()
        
        # Get error hotspots
        hotspots = self.processor.get_error_hotspots()
        
        # Generate error contexts
        self._generate_error_contexts(diagnostics)
        
        # Create analysis report
        return {
            'total_diagnostics': len(diagnostics),
            'stats': self.aggregator.get_current_stats(),
            'trends': self.aggregator.get_trends(),
            'clusters': clusters,
            'hotspots': hotspots,
            'contexts': self.error_contexts,
            'recommendations': self._generate_recommendations(diagnostics, clusters)
        }
        
    def _generate_error_contexts(self, diagnostics: List[CodeError]) -> None:
        """Generate detailed context for each error."""
        for diag in diagnostics:
            if diag.severity == ErrorSeverity.ERROR:
                context = ErrorContext(error=diag)
                
                # Add code context if available
                if self.codebase:
                    context.code_context = self._get_code_context(diag)
                    context.related_symbols = self._find_related_symbols(diag)
                    context.dependency_chain = self._trace_dependencies(diag)
                    
                # Generate fix suggestions
                context.fix_suggestions = self._generate_fix_suggestions(diag)
                
                self.error_contexts[f"{diag.file_path}:{diag.line}"] = context
                
    def _get_code_context(self, error: CodeError) -> Optional[str]:
        """Get code context around the error."""
        try:
            file_path = Path(error.file_path)
            if file_path.exists():
                lines = file_path.read_text().splitlines()
                start = max(0, error.line - 3)
                end = min(len(lines), error.line + 3)
                context_lines = lines[start:end]
                return '\n'.join(f"{i+start+1:4d}: {line}" for i, line in enumerate(context_lines))
        except Exception as e:
            logger.warning(f"Could not get code context: {e}")
        return None
        
    def _find_related_symbols(self, error: CodeError) -> List[Dict[str, Any]]:
        """Find symbols related to the error."""
        # This would use the codebase to find related symbols
        # Simplified implementation
        return []
        
    def _trace_dependencies(self, error: CodeError) -> List[str]:
        """Trace dependency chain for the error."""
        # This would trace import dependencies
        # Simplified implementation
        return []
        
    def _generate_fix_suggestions(self, error: CodeError) -> List[str]:
        """Generate fix suggestions for the error."""
        suggestions = []
        
        # Common fix patterns based on error message
        message_lower = error.message.lower()
        
        if "undefined" in message_lower or "not defined" in message_lower:
            suggestions.append("Check if the variable/function is properly imported")
            suggestions.append("Verify the spelling of the identifier")
            suggestions.append("Ensure the identifier is in scope")
            
        elif "type" in message_lower and "expected" in message_lower:
            suggestions.append("Check the type annotation")
            suggestions.append("Verify the function signature")
            suggestions.append("Consider type casting if appropriate")
            
        elif "import" in message_lower:
            suggestions.append("Check if the module is installed")
            suggestions.append("Verify the import path")
            suggestions.append("Check for circular imports")
            
        elif "syntax" in message_lower:
            suggestions.append("Check for missing parentheses or brackets")
            suggestions.append("Verify indentation")
            suggestions.append("Look for missing colons or commas")
            
        return suggestions
        
    def _generate_recommendations(self, diagnostics: List[CodeError], clusters: List[ErrorCluster]) -> List[str]:
        """Generate overall recommendations."""
        recommendations = []
        
        error_count = len([d for d in diagnostics if d.severity == ErrorSeverity.ERROR])
        warning_count = len([d for d in diagnostics if d.severity == ErrorSeverity.WARNING])
        
        if error_count > 0:
            recommendations.append(f"🔴 CRITICAL: Fix {error_count} errors to improve code stability")
            
        if warning_count > 50:
            recommendations.append(f"🟡 HIGH: Address {warning_count} warnings to improve code quality")
            
        if clusters:
            high_priority_clusters = [c for c in clusters if c.fix_priority >= 8]
            if high_priority_clusters:
                recommendations.append(f"🔥 URGENT: Focus on {len(high_priority_clusters)} high-priority error clusters")
                
        # Category-specific recommendations
        category_counts = defaultdict(int)
        for diag in diagnostics:
            if diag.severity == ErrorSeverity.ERROR:
                category_counts[diag.category] += 1
                
        for category, count in category_counts.items():
            if count > 10:
                if category == ErrorCategory.TYPE:
                    recommendations.append("📝 Consider improving type annotations")
                elif category == ErrorCategory.IMPORT:
                    recommendations.append("📦 Review import structure and dependencies")
                elif category == ErrorCategory.UNUSED:
                    recommendations.append("🧹 Clean up unused code and imports")
                    
        return recommendations


class RealTimeDiagnostics:
    """
    Real-time diagnostic monitoring and processing.
    Consolidated from lsp/diagnostics.py.
    """
    
    def __init__(self):
        self.analyzer = ComprehensiveErrorAnalyzer()
        self.active = False
        self._stats_handlers: List = []
        
    def start_monitoring(self) -> None:
        """Start real-time monitoring."""
        self.active = True
        logger.info("Real-time diagnostics monitoring started")
        
    def stop_monitoring(self) -> None:
        """Stop real-time monitoring."""
        self.active = False
        logger.info("Real-time diagnostics monitoring stopped")
        
    def process_diagnostics(self, diagnostics: List[CodeError]) -> Dict[str, Any]:
        """Process new diagnostics in real-time."""
        if not self.active:
            return {}
            
        # Analyze diagnostics
        analysis = self.analyzer.analyze_errors(diagnostics)
        
        # Notify handlers
        stats = analysis.get('stats')
        if stats:
            for handler in self._stats_handlers:
                try:
                    handler(stats)
                except Exception as e:
                    logger.error(f"Error in stats handler: {e}")
                    
        return analysis
        
    def add_stats_handler(self, handler) -> None:
        """Add a statistics handler."""
        self._stats_handlers.append(handler)
        
    def get_current_stats(self) -> DiagnosticStats:
        """Get current diagnostic statistics."""
        return self.analyzer.aggregator.get_current_stats()


# Utility functions
def create_error_from_lsp_diagnostic(diagnostic: Dict[str, Any], file_path: str) -> CodeError:
    """Create CodeError from LSP diagnostic."""
    severity_map = {1: ErrorSeverity.ERROR, 2: ErrorSeverity.WARNING, 3: ErrorSeverity.INFO, 4: ErrorSeverity.HINT}
    severity = severity_map.get(diagnostic.get("severity", 1), ErrorSeverity.ERROR)
    
    # Determine category from message/source
    category = ErrorCategory.SYNTAX  # Default
    message = diagnostic.get("message", "").lower()
    source = diagnostic.get("source", "").lower()
    
    if "import" in message or "module" in message:
        category = ErrorCategory.IMPORT
    elif "type" in message or source == "mypy":
        category = ErrorCategory.TYPE
    elif "undefined" in message or "not defined" in message:
        category = ErrorCategory.UNDEFINED
    elif "unused" in message:
        category = ErrorCategory.UNUSED
    elif source in ["pycodestyle", "flake8"]:
        category = ErrorCategory.STYLE
        
    return CodeError(
        file_path=file_path,
        line=diagnostic["range"]["start"]["line"] + 1,
        character=diagnostic["range"]["start"]["character"],
        severity=severity,
        category=category,
        message=diagnostic.get("message", ""),
        code=str(diagnostic.get("code", "")),
        source=diagnostic.get("source", "lsp"),
        range_start=diagnostic["range"]["start"],
        range_end=diagnostic["range"]["end"]
    )


def analyze_codebase_health(diagnostics: List[CodeError]) -> Dict[str, Any]:
    """Analyze overall codebase health from diagnostics."""
    analyzer = ComprehensiveErrorAnalyzer()
    return analyzer.analyze_errors(diagnostics)

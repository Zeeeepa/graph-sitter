"""
Real-time Diagnostics Processing for Serena LSP Integration

This module provides comprehensive diagnostic processing capabilities,
including real-time error monitoring, filtering, aggregation, and analysis.
"""

import asyncio
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Callable, Deque
import logging

from .error_retrieval import CodeError, ErrorSeverity, ErrorCategory, ComprehensiveErrorList

logger = logging.getLogger(__name__)


class DiagnosticEvent(Enum):
    """Diagnostic event types."""
    ERROR_ADDED = "error_added"
    ERROR_REMOVED = "error_removed"
    ERROR_UPDATED = "error_updated"
    BATCH_PROCESSED = "batch_processed"
    ANALYSIS_COMPLETE = "analysis_complete"


@dataclass
class DiagnosticFilter:
    """Filter configuration for diagnostics."""
    severities: Optional[Set[ErrorSeverity]] = None
    categories: Optional[Set[ErrorCategory]] = None
    file_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    min_line: Optional[int] = None
    max_line: Optional[int] = None
    sources: Optional[Set[str]] = None
    
    def matches(self, error: CodeError) -> bool:
        """Check if error matches filter criteria."""
        # Check severity
        if self.severities and error.severity not in self.severities:
            return False
        
        # Check category
        if self.categories and error.category not in self.categories:
            return False
        
        # Check file patterns
        if self.file_patterns:
            import fnmatch
            file_path = error.location.file_path
            if not any(fnmatch.fnmatch(file_path, pattern) for pattern in self.file_patterns):
                return False
        
        # Check exclude patterns
        if self.exclude_patterns:
            import fnmatch
            file_path = error.location.file_path
            if any(fnmatch.fnmatch(file_path, pattern) for pattern in self.exclude_patterns):
                return False
        
        # Check line range
        if self.min_line is not None and error.location.line < self.min_line:
            return False
        if self.max_line is not None and error.location.line > self.max_line:
            return False
        
        # Check sources
        if self.sources and error.source not in self.sources:
            return False
        
        return True


@dataclass
class DiagnosticStats:
    """Diagnostic statistics."""
    total_errors: int = 0
    critical_errors: int = 0
    warnings: int = 0
    info_hints: int = 0
    files_with_errors: int = 0
    categories: Dict[str, int] = field(default_factory=dict)
    sources: Dict[str, int] = field(default_factory=dict)
    error_rate: float = 0.0  # errors per minute
    last_updated: float = field(default_factory=time.time)
    
    def update_from_errors(self, errors: List[CodeError]):
        """Update statistics from error list."""
        self.total_errors = len(errors)
        self.critical_errors = sum(1 for e in errors if e.severity == ErrorSeverity.ERROR)
        self.warnings = sum(1 for e in errors if e.severity == ErrorSeverity.WARNING)
        self.info_hints = sum(1 for e in errors if e.severity in [ErrorSeverity.INFO, ErrorSeverity.HINT])
        
        # Count files with errors
        files = set(e.location.file_path for e in errors)
        self.files_with_errors = len(files)
        
        # Count by category
        self.categories = {}
        for error in errors:
            category = error.category.value
            self.categories[category] = self.categories.get(category, 0) + 1
        
        # Count by source
        self.sources = {}
        for error in errors:
            source = error.source
            self.sources[source] = self.sources.get(source, 0) + 1
        
        self.last_updated = time.time()


class DiagnosticAggregator:
    """
    Aggregates and analyzes diagnostic data over time.
    
    Features:
    - Time-based aggregation
    - Trend analysis
    - Error rate calculation
    - Historical data tracking
    """
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self._error_history: Deque[CodeError] = deque(maxlen=history_size)
        self._stats_history: Deque[DiagnosticStats] = deque(maxlen=100)
        self._current_stats = DiagnosticStats()
        
        # Time-based tracking
        self._error_timestamps: Deque[float] = deque(maxlen=history_size)
        self._last_aggregation = time.time()
    
    def add_error(self, error: CodeError):
        """Add a single error to aggregation."""
        self._error_history.append(error)
        self._error_timestamps.append(time.time())
        self._update_current_stats()
    
    def add_errors(self, errors: List[CodeError]):
        """Add multiple errors to aggregation."""
        current_time = time.time()
        for error in errors:
            self._error_history.append(error)
            self._error_timestamps.append(current_time)
        
        self._update_current_stats()
    
    def get_current_stats(self) -> DiagnosticStats:
        """Get current diagnostic statistics."""
        return self._current_stats
    
    def get_error_rate(self, time_window: float = 300.0) -> float:
        """
        Get error rate (errors per minute) over time window.
        
        Args:
            time_window: Time window in seconds (default: 5 minutes)
            
        Returns:
            Error rate per minute
        """
        current_time = time.time()
        cutoff_time = current_time - time_window
        
        # Count errors in time window
        recent_errors = sum(1 for ts in self._error_timestamps if ts >= cutoff_time)
        
        # Calculate rate per minute
        time_window_minutes = time_window / 60.0
        return recent_errors / time_window_minutes if time_window_minutes > 0 else 0.0
    
    def get_trend_analysis(self, time_window: float = 3600.0) -> Dict[str, Any]:
        """
        Get trend analysis over time window.
        
        Args:
            time_window: Time window in seconds (default: 1 hour)
            
        Returns:
            Trend analysis data
        """
        current_time = time.time()
        cutoff_time = current_time - time_window
        
        # Filter recent errors
        recent_errors = [
            error for error, ts in zip(self._error_history, self._error_timestamps)
            if ts >= cutoff_time
        ]
        
        if not recent_errors:
            return {
                'total_errors': 0,
                'error_rate': 0.0,
                'trending_categories': [],
                'trending_files': [],
                'severity_distribution': {}
            }
        
        # Analyze trends
        category_counts = defaultdict(int)
        file_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for error in recent_errors:
            category_counts[error.category.value] += 1
            file_counts[error.location.file_path] += 1
            severity_counts[error.severity.value] += 1
        
        # Sort by frequency
        trending_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        trending_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'total_errors': len(recent_errors),
            'error_rate': self.get_error_rate(time_window),
            'trending_categories': trending_categories[:10],
            'trending_files': trending_files[:10],
            'severity_distribution': dict(severity_counts),
            'time_window': time_window
        }
    
    def get_historical_stats(self, count: int = 10) -> List[DiagnosticStats]:
        """Get historical statistics."""
        return list(self._stats_history)[-count:]
    
    def clear_history(self):
        """Clear historical data."""
        self._error_history.clear()
        self._error_timestamps.clear()
        self._stats_history.clear()
        self._current_stats = DiagnosticStats()
    
    def _update_current_stats(self):
        """Update current statistics."""
        current_errors = list(self._error_history)
        self._current_stats.update_from_errors(current_errors)
        self._current_stats.error_rate = self.get_error_rate()
        
        # Add to history if significant change
        if (not self._stats_history or 
            time.time() - self._last_aggregation > 60):  # Every minute
            
            self._stats_history.append(DiagnosticStats(
                total_errors=self._current_stats.total_errors,
                critical_errors=self._current_stats.critical_errors,
                warnings=self._current_stats.warnings,
                info_hints=self._current_stats.info_hints,
                files_with_errors=self._current_stats.files_with_errors,
                categories=self._current_stats.categories.copy(),
                sources=self._current_stats.sources.copy(),
                error_rate=self._current_stats.error_rate,
                last_updated=time.time()
            ))
            
            self._last_aggregation = time.time()


class DiagnosticProcessor:
    """
    Main diagnostic processor for real-time error analysis.
    
    Features:
    - Real-time error processing
    - Filtering and categorization
    - Event-driven notifications
    - Batch processing
    - Performance monitoring
    """
    
    def __init__(self):
        self._filters: List[DiagnosticFilter] = []
        self._event_listeners: Dict[DiagnosticEvent, List[Callable]] = defaultdict(list)
        self._aggregator = DiagnosticAggregator()
        
        # Processing state
        self._active_errors: Dict[str, CodeError] = {}
        self._processing_queue: asyncio.Queue = asyncio.Queue()
        self._batch_size = 50
        self._batch_timeout = 5.0
        
        # Performance tracking
        self._processing_stats = {
            'total_processed': 0,
            'processing_time': 0.0,
            'average_processing_time': 0.0,
            'last_batch_time': 0.0
        }
        
        # Start processing loop
        self._processing_task: Optional[asyncio.Task] = None
        self._start_processing()
    
    def add_filter(self, filter_config: DiagnosticFilter):
        """Add diagnostic filter."""
        self._filters.append(filter_config)
    
    def remove_filter(self, filter_config: DiagnosticFilter):
        """Remove diagnostic filter."""
        if filter_config in self._filters:
            self._filters.remove(filter_config)
    
    def add_event_listener(self, event: DiagnosticEvent, listener: Callable):
        """Add event listener."""
        self._event_listeners[event].append(listener)
    
    def remove_event_listener(self, event: DiagnosticEvent, listener: Callable):
        """Remove event listener."""
        if listener in self._event_listeners[event]:
            self._event_listeners[event].remove(listener)
    
    async def process_errors(self, errors: List[CodeError]):
        """
        Process a list of errors.
        
        Args:
            errors: List of errors to process
        """
        for error in errors:
            await self._processing_queue.put(('add', error))
    
    async def process_error_update(self, error: CodeError):
        """Process a single error update."""
        await self._processing_queue.put(('update', error))
    
    async def process_error_removal(self, error_id: str):
        """Process error removal."""
        await self._processing_queue.put(('remove', error_id))
    
    def get_filtered_errors(self, additional_filter: Optional[DiagnosticFilter] = None) -> List[CodeError]:
        """
        Get errors filtered by current filters.
        
        Args:
            additional_filter: Additional filter to apply
            
        Returns:
            Filtered list of errors
        """
        errors = list(self._active_errors.values())
        
        # Apply all filters
        all_filters = self._filters.copy()
        if additional_filter:
            all_filters.append(additional_filter)
        
        for filter_config in all_filters:
            errors = [error for error in errors if filter_config.matches(error)]
        
        return errors
    
    def get_aggregated_stats(self) -> DiagnosticStats:
        """Get aggregated diagnostic statistics."""
        return self._aggregator.get_current_stats()
    
    def get_trend_analysis(self, **kwargs) -> Dict[str, Any]:
        """Get trend analysis."""
        return self._aggregator.get_trend_analysis(**kwargs)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing performance statistics."""
        return self._processing_stats.copy()
    
    def _start_processing(self):
        """Start the processing loop."""
        if not self._processing_task or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._processing_loop())
    
    async def _processing_loop(self):
        """Main processing loop."""
        batch = []
        last_batch_time = time.time()
        
        try:
            while True:
                try:
                    # Wait for items with timeout for batch processing
                    timeout = self._batch_timeout - (time.time() - last_batch_time)
                    timeout = max(0.1, timeout)
                    
                    item = await asyncio.wait_for(
                        self._processing_queue.get(),
                        timeout=timeout
                    )
                    
                    batch.append(item)
                    
                    # Process batch if full or timeout reached
                    if (len(batch) >= self._batch_size or 
                        time.time() - last_batch_time >= self._batch_timeout):
                        
                        await self._process_batch(batch)
                        batch = []
                        last_batch_time = time.time()
                        
                except asyncio.TimeoutError:
                    # Process partial batch on timeout
                    if batch:
                        await self._process_batch(batch)
                        batch = []
                        last_batch_time = time.time()
                        
        except asyncio.CancelledError:
            # Process remaining batch before exit
            if batch:
                await self._process_batch(batch)
            raise
        except Exception as e:
            logger.error(f"Error in diagnostic processing loop: {e}")
    
    async def _process_batch(self, batch: List[tuple]):
        """Process a batch of diagnostic operations."""
        start_time = time.time()
        
        added_errors = []
        updated_errors = []
        removed_errors = []
        
        try:
            for operation, data in batch:
                if operation == 'add':
                    error = data
                    self._active_errors[error.id] = error
                    self._aggregator.add_error(error)
                    added_errors.append(error)
                    
                elif operation == 'update':
                    error = data
                    if error.id in self._active_errors:
                        old_error = self._active_errors[error.id]
                        self._active_errors[error.id] = error
                        updated_errors.append((old_error, error))
                    else:
                        # Treat as new error
                        self._active_errors[error.id] = error
                        self._aggregator.add_error(error)
                        added_errors.append(error)
                        
                elif operation == 'remove':
                    error_id = data
                    if error_id in self._active_errors:
                        removed_error = self._active_errors.pop(error_id)
                        removed_errors.append(removed_error)
            
            # Update processing stats
            processing_time = time.time() - start_time
            self._processing_stats['total_processed'] += len(batch)
            self._processing_stats['processing_time'] += processing_time
            self._processing_stats['average_processing_time'] = (
                self._processing_stats['processing_time'] / 
                self._processing_stats['total_processed']
            )
            self._processing_stats['last_batch_time'] = processing_time
            
            # Emit events
            for error in added_errors:
                await self._emit_event(DiagnosticEvent.ERROR_ADDED, error)
            
            for old_error, new_error in updated_errors:
                await self._emit_event(DiagnosticEvent.ERROR_UPDATED, (old_error, new_error))
            
            for error in removed_errors:
                await self._emit_event(DiagnosticEvent.ERROR_REMOVED, error)
            
            if batch:
                await self._emit_event(DiagnosticEvent.BATCH_PROCESSED, {
                    'batch_size': len(batch),
                    'added': len(added_errors),
                    'updated': len(updated_errors),
                    'removed': len(removed_errors),
                    'processing_time': processing_time
                })
            
        except Exception as e:
            logger.error(f"Error processing diagnostic batch: {e}")
    
    async def _emit_event(self, event: DiagnosticEvent, data: Any):
        """Emit diagnostic event to listeners."""
        listeners = self._event_listeners.get(event, [])
        
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(data)
                else:
                    listener(data)
            except Exception as e:
                logger.error(f"Error in diagnostic event listener: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        if self._processing_task:
            self._processing_task.cancel()
            try:
                await self._processing_task
            except asyncio.CancelledError:
                pass
        
        self._active_errors.clear()
        self._event_listeners.clear()
        self._aggregator.clear_history()


class RealTimeDiagnostics:
    """
    Real-time diagnostics system combining all diagnostic components.
    
    Features:
    - Real-time error monitoring
    - Comprehensive filtering and analysis
    - Event-driven architecture
    - Performance monitoring
    - Historical tracking
    """
    
    def __init__(self):
        self.processor = DiagnosticProcessor()
        self.aggregator = self.processor._aggregator
        
        # High-level event handlers
        self._error_handlers: List[Callable[[CodeError], None]] = []
        self._stats_handlers: List[Callable[[DiagnosticStats], None]] = []
        
        # Setup internal event handling
        self.processor.add_event_listener(
            DiagnosticEvent.ERROR_ADDED,
            self._handle_error_added
        )
        
        self.processor.add_event_listener(
            DiagnosticEvent.BATCH_PROCESSED,
            self._handle_batch_processed
        )
    
    async def start_monitoring(self, error_source: Callable[[], List[CodeError]],
                             poll_interval: float = 5.0):
        """
        Start real-time monitoring of errors from a source.
        
        Args:
            error_source: Function that returns current errors
            poll_interval: Polling interval in seconds
        """
        async def monitor_loop():
            try:
                while True:
                    try:
                        errors = error_source()
                        await self.processor.process_errors(errors)
                        await asyncio.sleep(poll_interval)
                    except Exception as e:
                        logger.error(f"Error in monitoring loop: {e}")
                        await asyncio.sleep(poll_interval)
            except asyncio.CancelledError:
                pass
        
        # Start monitoring task
        asyncio.create_task(monitor_loop())
    
    def add_error_handler(self, handler: Callable[[CodeError], None]):
        """Add handler for new errors."""
        self._error_handlers.append(handler)
    
    def add_stats_handler(self, handler: Callable[[DiagnosticStats], None]):
        """Add handler for statistics updates."""
        self._stats_handlers.append(handler)
    
    def add_filter(self, filter_config: DiagnosticFilter):
        """Add diagnostic filter."""
        self.processor.add_filter(filter_config)
    
    def get_current_errors(self, filter_config: Optional[DiagnosticFilter] = None) -> List[CodeError]:
        """Get current filtered errors."""
        return self.processor.get_filtered_errors(filter_config)
    
    def get_current_stats(self) -> DiagnosticStats:
        """Get current statistics."""
        return self.processor.get_aggregated_stats()
    
    def get_trend_analysis(self, **kwargs) -> Dict[str, Any]:
        """Get trend analysis."""
        return self.processor.get_trend_analysis(**kwargs)
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive diagnostic report."""
        stats = self.get_current_stats()
        trends = self.get_trend_analysis()
        processing_stats = self.processor.get_processing_stats()
        
        return {
            'current_stats': {
                'total_errors': stats.total_errors,
                'critical_errors': stats.critical_errors,
                'warnings': stats.warnings,
                'info_hints': stats.info_hints,
                'files_with_errors': stats.files_with_errors,
                'error_rate': stats.error_rate,
                'last_updated': stats.last_updated
            },
            'category_breakdown': stats.categories,
            'source_breakdown': stats.sources,
            'trends': trends,
            'processing_performance': processing_stats
        }
    
    async def _handle_error_added(self, error: CodeError):
        """Handle new error event."""
        for handler in self._error_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(error)
                else:
                    handler(error)
            except Exception as e:
                logger.error(f"Error in error handler: {e}")
    
    async def _handle_batch_processed(self, batch_info: Dict[str, Any]):
        """Handle batch processed event."""
        # Update stats handlers
        current_stats = self.get_current_stats()
        
        for handler in self._stats_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(current_stats)
                else:
                    handler(current_stats)
            except Exception as e:
                logger.error(f"Error in stats handler: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        await self.processor.cleanup()
        self._error_handlers.clear()
        self._stats_handlers.clear()


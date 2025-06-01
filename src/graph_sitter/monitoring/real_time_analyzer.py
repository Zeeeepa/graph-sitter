"""
Real-time Code Analysis System

Provides real-time analysis of code changes with file watching,
incremental analysis, and quality delta tracking.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Callable
import hashlib
import json

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = None

from graph_sitter import Codebase
from graph_sitter.analysis import EnhancedCodebaseAnalyzer, FunctionMetrics, ClassMetrics

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Types of file changes."""
    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    RENAMED = "renamed"


class AnalysisScope(Enum):
    """Scope of analysis to perform."""
    FILE_ONLY = "file_only"
    FILE_AND_DEPENDENCIES = "file_and_dependencies"
    FULL_CODEBASE = "full_codebase"


@dataclass
class FileChangeEvent:
    """File change event information."""
    file_path: str
    change_type: ChangeType
    timestamp: datetime
    file_size: Optional[int] = None
    file_hash: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_path': self.file_path,
            'change_type': self.change_type.value,
            'timestamp': self.timestamp.isoformat(),
            'file_size': self.file_size,
            'file_hash': self.file_hash
        }


@dataclass
class QualityDelta:
    """Quality change information."""
    metric_name: str
    old_value: float
    new_value: float
    change: float
    change_percentage: float
    
    @property
    def is_improvement(self) -> bool:
        """Check if change is an improvement."""
        # For most metrics, higher is better
        if self.metric_name in ['health_score', 'maintainability_index', 'documentation_coverage']:
            return self.change > 0
        # For some metrics, lower is better
        elif self.metric_name in ['cyclomatic_complexity', 'technical_debt_score']:
            return self.change < 0
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'metric_name': self.metric_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'change': self.change,
            'change_percentage': self.change_percentage,
            'is_improvement': self.is_improvement
        }


@dataclass
class AnalysisResult:
    """Result of real-time analysis."""
    file_path: str
    timestamp: datetime
    analysis_scope: AnalysisScope
    analysis_duration: float
    
    # Quality metrics
    function_metrics: List[FunctionMetrics] = field(default_factory=list)
    class_metrics: List[ClassMetrics] = field(default_factory=list)
    quality_deltas: List[QualityDelta] = field(default_factory=list)
    
    # Issues found
    new_issues: List[Dict[str, Any]] = field(default_factory=list)
    resolved_issues: List[Dict[str, Any]] = field(default_factory=list)
    
    # Summary
    overall_quality_change: float = 0.0
    impact_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'file_path': self.file_path,
            'timestamp': self.timestamp.isoformat(),
            'analysis_scope': self.analysis_scope.value,
            'analysis_duration': self.analysis_duration,
            'function_metrics': [m.__dict__ for m in self.function_metrics],
            'class_metrics': [m.__dict__ for m in self.class_metrics],
            'quality_deltas': [d.to_dict() for d in self.quality_deltas],
            'new_issues': self.new_issues,
            'resolved_issues': self.resolved_issues,
            'overall_quality_change': self.overall_quality_change,
            'impact_score': self.impact_score
        }


class CodeFileWatcher(FileSystemEventHandler):
    """File system event handler for code changes."""
    
    def __init__(self, analyzer: 'RealTimeAnalyzer'):
        self.analyzer = analyzer
        self.supported_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp'}
    
    def on_modified(self, event):
        """Handle file modification."""
        if not event.is_directory and self._is_code_file(event.src_path):
            change_event = FileChangeEvent(
                file_path=event.src_path,
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now()
            )
            asyncio.create_task(self.analyzer._handle_file_change(change_event))
    
    def on_created(self, event):
        """Handle file creation."""
        if not event.is_directory and self._is_code_file(event.src_path):
            change_event = FileChangeEvent(
                file_path=event.src_path,
                change_type=ChangeType.CREATED,
                timestamp=datetime.now()
            )
            asyncio.create_task(self.analyzer._handle_file_change(change_event))
    
    def on_deleted(self, event):
        """Handle file deletion."""
        if not event.is_directory and self._is_code_file(event.src_path):
            change_event = FileChangeEvent(
                file_path=event.src_path,
                change_type=ChangeType.DELETED,
                timestamp=datetime.now()
            )
            asyncio.create_task(self.analyzer._handle_file_change(change_event))
    
    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file."""
        return Path(file_path).suffix.lower() in self.supported_extensions


class RealTimeAnalyzer:
    """Real-time code analysis system."""
    
    def __init__(self, codebase: Codebase, watch_path: Optional[str] = None):
        self.codebase = codebase
        self.watch_path = watch_path or str(Path.cwd())
        self.analyzer = EnhancedCodebaseAnalyzer(codebase, "real-time-analyzer")
        
        # State
        self.is_watching = False
        self.file_observer: Optional[Observer] = None
        self.file_watcher: Optional[CodeFileWatcher] = None
        
        # Analysis state
        self.file_hashes: Dict[str, str] = {}
        self.last_analysis_results: Dict[str, AnalysisResult] = {}
        self.analysis_queue: asyncio.Queue = asyncio.Queue()
        self.analysis_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.analysis_scope = AnalysisScope.FILE_AND_DEPENDENCIES
        self.debounce_delay = 2.0  # seconds
        self.max_queue_size = 100
        
        # Callbacks
        self.change_callbacks: List[Callable[[FileChangeEvent], None]] = []
        self.analysis_callbacks: List[Callable[[AnalysisResult], None]] = []
        
        # Debouncing
        self.pending_changes: Dict[str, FileChangeEvent] = {}
        self.debounce_tasks: Dict[str, asyncio.Task] = {}
    
    async def start_watching(self):
        """Start watching for file changes."""
        if not WATCHDOG_AVAILABLE:
            logger.error("Watchdog library not available. Install with: pip install watchdog")
            return
        
        if self.is_watching:
            logger.warning("Already watching for changes")
            return
        
        logger.info(f"Starting real-time analysis watching: {self.watch_path}")
        
        # Initialize file hashes
        await self._initialize_file_hashes()
        
        # Start file watcher
        self.file_watcher = CodeFileWatcher(self)
        self.file_observer = Observer()
        self.file_observer.schedule(self.file_watcher, self.watch_path, recursive=True)
        self.file_observer.start()
        
        # Start analysis task
        self.analysis_task = asyncio.create_task(self._analysis_worker())
        
        self.is_watching = True
        logger.info("Real-time analysis started")
    
    async def stop_watching(self):
        """Stop watching for file changes."""
        if not self.is_watching:
            return
        
        logger.info("Stopping real-time analysis")
        self.is_watching = False
        
        # Stop file observer
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join()
        
        # Cancel analysis task
        if self.analysis_task:
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass
        
        # Cancel debounce tasks
        for task in self.debounce_tasks.values():
            task.cancel()
        self.debounce_tasks.clear()
        
        logger.info("Real-time analysis stopped")
    
    async def _initialize_file_hashes(self):
        """Initialize file hashes for change detection."""
        try:
            watch_path = Path(self.watch_path)
            for file_path in watch_path.rglob("*.py"):  # Start with Python files
                if file_path.is_file():
                    file_hash = await self._calculate_file_hash(str(file_path))
                    self.file_hashes[str(file_path)] = file_hash
            
            logger.info(f"Initialized hashes for {len(self.file_hashes)} files")
            
        except Exception as e:
            logger.error(f"Error initializing file hashes: {e}")
    
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.warning(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    async def _handle_file_change(self, change_event: FileChangeEvent):
        """Handle file change event with debouncing."""
        try:
            file_path = change_event.file_path
            
            # Cancel existing debounce task
            if file_path in self.debounce_tasks:
                self.debounce_tasks[file_path].cancel()
            
            # Store pending change
            self.pending_changes[file_path] = change_event
            
            # Create new debounce task
            self.debounce_tasks[file_path] = asyncio.create_task(
                self._debounced_analysis(file_path)
            )
            
        except Exception as e:
            logger.error(f"Error handling file change: {e}")
    
    async def _debounced_analysis(self, file_path: str):
        """Perform debounced analysis after delay."""
        try:
            await asyncio.sleep(self.debounce_delay)
            
            # Get pending change
            if file_path not in self.pending_changes:
                return
            
            change_event = self.pending_changes.pop(file_path)
            
            # Check if file actually changed
            if change_event.change_type == ChangeType.MODIFIED:
                current_hash = await self._calculate_file_hash(file_path)
                old_hash = self.file_hashes.get(file_path, "")
                
                if current_hash == old_hash:
                    logger.debug(f"File {file_path} not actually changed, skipping analysis")
                    return
                
                self.file_hashes[file_path] = current_hash
                change_event.file_hash = current_hash
            
            # Add file size
            try:
                change_event.file_size = Path(file_path).stat().st_size
            except:
                pass
            
            # Notify change callbacks
            for callback in self.change_callbacks:
                try:
                    callback(change_event)
                except Exception as e:
                    logger.error(f"Error in change callback: {e}")
            
            # Queue for analysis
            if self.analysis_queue.qsize() < self.max_queue_size:
                await self.analysis_queue.put(change_event)
            else:
                logger.warning(f"Analysis queue full, dropping change event for {file_path}")
            
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in debounced analysis: {e}")
        finally:
            # Clean up
            if file_path in self.debounce_tasks:
                del self.debounce_tasks[file_path]
    
    async def _analysis_worker(self):
        """Worker task for processing analysis queue."""
        while self.is_watching:
            try:
                # Get change event from queue
                change_event = await asyncio.wait_for(
                    self.analysis_queue.get(), timeout=1.0
                )
                
                # Perform analysis
                result = await self._analyze_change(change_event)
                
                if result:
                    # Store result
                    self.last_analysis_results[change_event.file_path] = result
                    
                    # Notify callbacks
                    for callback in self.analysis_callbacks:
                        try:
                            callback(result)
                        except Exception as e:
                            logger.error(f"Error in analysis callback: {e}")
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analysis worker: {e}")
    
    async def _analyze_change(self, change_event: FileChangeEvent) -> Optional[AnalysisResult]:
        """Analyze file change."""
        start_time = time.time()
        
        try:
            logger.debug(f"Analyzing change: {change_event.file_path} ({change_event.change_type.value})")
            
            # Handle deleted files
            if change_event.change_type == ChangeType.DELETED:
                return self._create_deletion_result(change_event, time.time() - start_time)
            
            # Check if file exists
            file_path = Path(change_event.file_path)
            if not file_path.exists():
                logger.warning(f"File not found: {change_event.file_path}")
                return None
            
            # Determine analysis scope
            scope = self._determine_analysis_scope(change_event)
            
            # Perform analysis based on scope
            if scope == AnalysisScope.FILE_ONLY:
                result = await self._analyze_file_only(change_event)
            elif scope == AnalysisScope.FILE_AND_DEPENDENCIES:
                result = await self._analyze_file_and_dependencies(change_event)
            else:  # FULL_CODEBASE
                result = await self._analyze_full_codebase(change_event)
            
            if result:
                result.analysis_duration = time.time() - start_time
                result.analysis_scope = scope
                
                # Calculate quality deltas
                await self._calculate_quality_deltas(result, change_event)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing change {change_event.file_path}: {e}")
            return None
    
    def _determine_analysis_scope(self, change_event: FileChangeEvent) -> AnalysisScope:
        """Determine appropriate analysis scope."""
        # For now, use configured scope
        # Could be made smarter based on file type, size, etc.
        return self.analysis_scope
    
    async def _analyze_file_only(self, change_event: FileChangeEvent) -> Optional[AnalysisResult]:
        """Analyze single file only."""
        try:
            file_path = change_event.file_path
            
            # Get file from codebase
            # This is a simplified approach - in practice, you'd need to
            # reload the specific file in the codebase
            
            result = AnalysisResult(
                file_path=file_path,
                timestamp=change_event.timestamp
            )
            
            # Analyze functions and classes in the file
            # This would require integration with the codebase to get
            # specific file analysis
            
            return result
            
        except Exception as e:
            logger.error(f"Error in file-only analysis: {e}")
            return None
    
    async def _analyze_file_and_dependencies(self, change_event: FileChangeEvent) -> Optional[AnalysisResult]:
        """Analyze file and its dependencies."""
        try:
            # This would analyze the changed file plus any files that depend on it
            # or that it depends on
            
            result = AnalysisResult(
                file_path=change_event.file_path,
                timestamp=change_event.timestamp
            )
            
            # Implementation would involve:
            # 1. Finding dependencies of the changed file
            # 2. Finding files that depend on the changed file
            # 3. Running analysis on this subset
            
            return result
            
        except Exception as e:
            logger.error(f"Error in file and dependencies analysis: {e}")
            return None
    
    async def _analyze_full_codebase(self, change_event: FileChangeEvent) -> Optional[AnalysisResult]:
        """Analyze full codebase."""
        try:
            # Run full codebase analysis
            # This is expensive but gives complete picture
            
            report = self.analyzer.run_full_analysis()
            
            result = AnalysisResult(
                file_path=change_event.file_path,
                timestamp=change_event.timestamp
            )
            
            # Extract relevant metrics
            function_analysis = report.get('function_analysis', [])
            class_analysis = report.get('class_analysis', [])
            
            # Convert to metrics objects (simplified)
            # In practice, you'd need proper conversion
            
            return result
            
        except Exception as e:
            logger.error(f"Error in full codebase analysis: {e}")
            return None
    
    def _create_deletion_result(self, change_event: FileChangeEvent, duration: float) -> AnalysisResult:
        """Create result for file deletion."""
        return AnalysisResult(
            file_path=change_event.file_path,
            timestamp=change_event.timestamp,
            analysis_scope=AnalysisScope.FILE_ONLY,
            analysis_duration=duration,
            overall_quality_change=0.0,  # Could be positive if removing bad code
            impact_score=0.1  # Low impact for deletion
        )
    
    async def _calculate_quality_deltas(self, result: AnalysisResult, change_event: FileChangeEvent):
        """Calculate quality changes."""
        try:
            # Get previous analysis result
            previous_result = self.last_analysis_results.get(change_event.file_path)
            if not previous_result:
                return
            
            # Calculate deltas for various metrics
            # This is a simplified example
            
            deltas = []
            
            # Example: Compare function complexity
            if result.function_metrics and previous_result.function_metrics:
                for new_metric in result.function_metrics:
                    # Find corresponding previous metric
                    old_metric = next(
                        (m for m in previous_result.function_metrics if m.name == new_metric.name),
                        None
                    )
                    
                    if old_metric:
                        complexity_delta = QualityDelta(
                            metric_name="cyclomatic_complexity",
                            old_value=old_metric.cyclomatic_complexity,
                            new_value=new_metric.cyclomatic_complexity,
                            change=new_metric.cyclomatic_complexity - old_metric.cyclomatic_complexity,
                            change_percentage=((new_metric.cyclomatic_complexity - old_metric.cyclomatic_complexity) 
                                             / max(old_metric.cyclomatic_complexity, 1)) * 100
                        )
                        deltas.append(complexity_delta)
            
            result.quality_deltas = deltas
            
            # Calculate overall quality change
            if deltas:
                improvements = sum(1 for d in deltas if d.is_improvement)
                result.overall_quality_change = (improvements / len(deltas)) * 2 - 1  # -1 to 1 scale
            
        except Exception as e:
            logger.error(f"Error calculating quality deltas: {e}")
    
    def add_change_callback(self, callback: Callable[[FileChangeEvent], None]):
        """Add callback for file changes."""
        self.change_callbacks.append(callback)
    
    def add_analysis_callback(self, callback: Callable[[AnalysisResult], None]):
        """Add callback for analysis results."""
        self.analysis_callbacks.append(callback)
    
    def get_recent_results(self, hours: int = 1) -> List[AnalysisResult]:
        """Get recent analysis results."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [r for r in self.last_analysis_results.values() if r.timestamp > cutoff]
    
    def set_analysis_scope(self, scope: AnalysisScope):
        """Set analysis scope."""
        self.analysis_scope = scope
        logger.info(f"Analysis scope set to: {scope.value}")
    
    def set_debounce_delay(self, delay: float):
        """Set debounce delay in seconds."""
        self.debounce_delay = delay
        logger.info(f"Debounce delay set to: {delay}s")
    
    async def analyze_file_now(self, file_path: str) -> Optional[AnalysisResult]:
        """Force immediate analysis of specific file."""
        change_event = FileChangeEvent(
            file_path=file_path,
            change_type=ChangeType.MODIFIED,
            timestamp=datetime.now()
        )
        
        return await self._analyze_change(change_event)


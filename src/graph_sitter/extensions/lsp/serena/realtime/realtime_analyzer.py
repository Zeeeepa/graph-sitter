"""
Real-time Analyzer

Provides file watching and incremental analysis capabilities.
"""

import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent, FileDeletedEvent

logger = logging.getLogger(__name__)


class RealtimeAnalyzer:
    """
    Provides real-time analysis capabilities.
    
    Features:
    - File system monitoring
    - Incremental analysis on file changes
    - Debounced change processing
    - Background analysis tasks
    - Integration with symbol intelligence and diagnostics
    """
    
    def __init__(self, codebase_path: str, serena_core: Any):
        self.codebase_path = Path(codebase_path)
        self.serena_core = serena_core
        
        # File monitoring
        self._observer: Optional[Observer] = None
        self._event_handler: Optional[FileSystemEventHandler] = None
        self._monitoring = False
        
        # Change tracking
        self._pending_changes: Dict[str, float] = {}  # file_path -> timestamp
        self._change_debounce_time = 0.5  # seconds
        self._last_analysis_time: Dict[str, float] = {}
        
        # Analysis state
        self._analysis_queue: asyncio.Queue = asyncio.Queue()
        self._analysis_tasks: List[asyncio.Task] = []
        self._analysis_results: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self._watch_patterns = ['*.py', '*.js', '*.ts', '*.jsx', '*.tsx']
        self._ignore_patterns = ['__pycache__', '.git', '.venv', 'node_modules']
        
        logger.debug("RealtimeAnalyzer initialized")
    
    async def initialize(self) -> None:
        """Initialize real-time analyzer."""
        logger.info("Initializing real-time analyzer...")
        
        # Start file monitoring
        await self.start_monitoring()
        
        # Start analysis workers
        await self._start_analysis_workers()
        
        logger.info("✅ Real-time analyzer initialized")
    
    async def shutdown(self) -> None:
        """Shutdown real-time analyzer."""
        logger.info("Shutting down real-time analyzer...")
        
        # Stop monitoring
        await self.stop_monitoring()
        
        # Cancel analysis tasks
        for task in self._analysis_tasks:
            task.cancel()
        
        if self._analysis_tasks:
            await asyncio.gather(*self._analysis_tasks, return_exceptions=True)
        
        self._analysis_tasks.clear()
        self._analysis_results.clear()
        self._pending_changes.clear()
        
        logger.info("✅ Real-time analyzer shutdown")
    
    async def start_monitoring(self) -> None:
        """Start real-time file monitoring."""
        if self._monitoring:
            return
        
        try:
            # Create event handler
            self._event_handler = RealtimeFileHandler(self)
            
            # Create observer
            self._observer = Observer()
            self._observer.schedule(
                self._event_handler,
                str(self.codebase_path),
                recursive=True
            )
            
            # Start observer
            self._observer.start()
            self._monitoring = True
            
            logger.info(f"Started file monitoring for: {self.codebase_path}")
            
            # Emit monitoring started event
            if self.serena_core:
                await self.serena_core._emit_event("realtime.monitoring_started", {
                    'codebase_path': str(self.codebase_path),
                    'watch_patterns': self._watch_patterns
                })
            
        except Exception as e:
            logger.error(f"Error starting file monitoring: {e}")
            self._monitoring = False
    
    async def stop_monitoring(self) -> None:
        """Stop real-time file monitoring."""
        if not self._monitoring:
            return
        
        try:
            if self._observer:
                self._observer.stop()
                self._observer.join(timeout=5.0)
                self._observer = None
            
            self._event_handler = None
            self._monitoring = False
            
            logger.info("Stopped file monitoring")
            
            # Emit monitoring stopped event
            if self.serena_core:
                await self.serena_core._emit_event("realtime.monitoring_stopped", {})
            
        except Exception as e:
            logger.error(f"Error stopping file monitoring: {e}")
    
    async def enable_analysis(
        self,
        watch_patterns: List[str],
        auto_refresh: bool = True
    ) -> bool:
        """Enable real-time analysis with file watching."""
        try:
            self._watch_patterns = watch_patterns
            
            # Restart monitoring with new patterns if already running
            if self._monitoring:
                await self.stop_monitoring()
                await self.start_monitoring()
            
            logger.info(f"Enabled real-time analysis with patterns: {watch_patterns}")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling real-time analysis: {e}")
            return False
    
    async def disable_analysis(self) -> bool:
        """Disable real-time analysis."""
        try:
            await self.stop_monitoring()
            logger.info("Disabled real-time analysis")
            return True
            
        except Exception as e:
            logger.error(f"Error disabling real-time analysis: {e}")
            return False
    
    async def analyze_file(self, file_path: str, force: bool = False) -> Dict[str, Any]:
        """Analyze a specific file."""
        try:
            file_path = str(Path(file_path).resolve())
            
            # Check if analysis is needed
            if not force:
                last_analysis = self._last_analysis_time.get(file_path, 0)
                file_mtime = Path(file_path).stat().st_mtime
                
                if last_analysis >= file_mtime:
                    # Return cached result if available
                    if file_path in self._analysis_results:
                        return self._analysis_results[file_path]
            
            # Perform analysis
            analysis_result = await self._perform_file_analysis(file_path)
            
            # Cache result
            self._analysis_results[file_path] = analysis_result
            self._last_analysis_time[file_path] = time.time()
            
            # Emit analysis completed event
            if self.serena_core:
                await self.serena_core._emit_event("realtime.file_analyzed", {
                    'file_path': file_path,
                    'analysis_result': analysis_result
                })
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return {
                'file_path': file_path,
                'error': str(e),
                'analysis_time': time.time()
            }
    
    async def get_analysis_result(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get cached analysis result for a file."""
        file_path = str(Path(file_path).resolve())
        return self._analysis_results.get(file_path)
    
    async def queue_file_for_analysis(self, file_path: str) -> None:
        """Queue a file for analysis."""
        try:
            await self._analysis_queue.put({
                'file_path': file_path,
                'timestamp': time.time(),
                'priority': 'normal'
            })
            
            logger.debug(f"Queued file for analysis: {file_path}")
            
        except Exception as e:
            logger.error(f"Error queuing file for analysis: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get real-time analyzer status."""
        return {
            'initialized': True,
            'monitoring': self._monitoring,
            'codebase_path': str(self.codebase_path),
            'watch_patterns': self._watch_patterns,
            'ignore_patterns': self._ignore_patterns,
            'pending_changes': len(self._pending_changes),
            'analysis_queue_size': self._analysis_queue.qsize(),
            'active_analysis_tasks': len([t for t in self._analysis_tasks if not t.done()]),
            'analyzed_files': len(self._analysis_results),
            'last_analysis_times': len(self._last_analysis_time)
        }
    
    async def _handle_file_change(self, file_path: str, event_type: str) -> None:
        """Handle file change event."""
        try:
            # Check if file should be monitored
            if not self._should_monitor_file(file_path):
                return
            
            # Add to pending changes with debounce
            current_time = time.time()
            self._pending_changes[file_path] = current_time
            
            # Schedule debounced analysis
            await asyncio.sleep(self._change_debounce_time)
            
            # Check if this is still the latest change
            if (file_path in self._pending_changes and 
                self._pending_changes[file_path] == current_time):
                
                # Remove from pending and queue for analysis
                del self._pending_changes[file_path]
                await self.queue_file_for_analysis(file_path)
                
                logger.debug(f"File change processed: {file_path} ({event_type})")
            
        except Exception as e:
            logger.error(f"Error handling file change for {file_path}: {e}")
    
    def _should_monitor_file(self, file_path: str) -> bool:
        """Check if a file should be monitored."""
        file_path_obj = Path(file_path)
        
        # Check ignore patterns
        for ignore_pattern in self._ignore_patterns:
            if ignore_pattern in str(file_path_obj):
                return False
        
        # Check watch patterns
        for watch_pattern in self._watch_patterns:
            if file_path_obj.match(watch_pattern):
                return True
        
        return False
    
    async def _start_analysis_workers(self) -> None:
        """Start background analysis worker tasks."""
        # Start multiple workers for parallel analysis
        num_workers = 2
        
        for i in range(num_workers):
            task = asyncio.create_task(self._analysis_worker(f"worker-{i}"))
            self._analysis_tasks.append(task)
        
        logger.debug(f"Started {num_workers} analysis workers")
    
    async def _analysis_worker(self, worker_name: str) -> None:
        """Background worker for processing analysis queue."""
        logger.debug(f"Analysis worker {worker_name} started")
        
        try:
            while True:
                try:
                    # Get next analysis task
                    analysis_task = await asyncio.wait_for(
                        self._analysis_queue.get(),
                        timeout=1.0
                    )
                    
                    file_path = analysis_task['file_path']
                    
                    # Perform analysis
                    await self.analyze_file(file_path)
                    
                    # Mark task as done
                    self._analysis_queue.task_done()
                    
                except asyncio.TimeoutError:
                    # No tasks in queue, continue
                    continue
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in analysis worker {worker_name}: {e}")
                    
        except asyncio.CancelledError:
            pass
        finally:
            logger.debug(f"Analysis worker {worker_name} stopped")
    
    async def _perform_file_analysis(self, file_path: str) -> Dict[str, Any]:
        """Perform comprehensive analysis of a file."""
        analysis_start = time.time()
        
        try:
            analysis_result = {
                'file_path': file_path,
                'analysis_time': analysis_start,
                'file_size': 0,
                'line_count': 0,
                'symbols': [],
                'imports': [],
                'diagnostics': [],
                'metrics': {}
            }
            
            # Check if file exists
            file_path_obj = Path(file_path)
            if not file_path_obj.exists():
                analysis_result['error'] = 'File does not exist'
                return analysis_result
            
            # Get file stats
            stat = file_path_obj.stat()
            analysis_result['file_size'] = stat.st_size
            analysis_result['last_modified'] = stat.st_mtime
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    analysis_result['line_count'] = len(lines)
            except Exception as e:
                analysis_result['error'] = f'Could not read file: {str(e)}'
                return analysis_result
            
            # Analyze symbols if symbol intelligence is available
            if (self.serena_core and 
                self.serena_core.is_capability_enabled(self.serena_core.config.enabled_capabilities[0])):
                
                try:
                    # Refresh symbol index for this file
                    symbol_intelligence = self.serena_core.get_capability('symbol_intelligence')
                    if symbol_intelligence:
                        await symbol_intelligence.refresh_symbol_index([file_path])
                        
                        # Get symbols in this file
                        symbols = await symbol_intelligence.search_symbols(
                            query='',
                            file_pattern=file_path,
                            limit=100
                        )
                        
                        analysis_result['symbols'] = [
                            {
                                'name': symbol.name,
                                'type': symbol.symbol_type,
                                'line': symbol.line_number,
                                'character': symbol.character
                            }
                            for symbol in symbols
                        ]
                        
                except Exception as e:
                    logger.warning(f"Error analyzing symbols in {file_path}: {e}")
            
            # Analyze imports
            analysis_result['imports'] = self._analyze_imports(content)
            
            # Basic code metrics
            analysis_result['metrics'] = self._calculate_code_metrics(content, lines)
            
            # Calculate analysis duration
            analysis_result['analysis_duration'] = time.time() - analysis_start
            
            logger.debug(f"Analyzed file {file_path} in {analysis_result['analysis_duration']:.3f}s")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error performing file analysis for {file_path}: {e}")
            return {
                'file_path': file_path,
                'analysis_time': analysis_start,
                'error': str(e),
                'analysis_duration': time.time() - analysis_start
            }
    
    def _analyze_imports(self, content: str) -> List[Dict[str, Any]]:
        """Analyze import statements in file content."""
        imports = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append({
                    'line': i + 1,
                    'statement': line,
                    'type': 'import' if line.startswith('import ') else 'from_import'
                })
        
        return imports
    
    def _calculate_code_metrics(self, content: str, lines: List[str]) -> Dict[str, Any]:
        """Calculate basic code metrics."""
        metrics = {
            'total_lines': len(lines),
            'code_lines': 0,
            'comment_lines': 0,
            'blank_lines': 0,
            'function_count': 0,
            'class_count': 0,
            'complexity_estimate': 0
        }
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                metrics['blank_lines'] += 1
            elif stripped.startswith('#'):
                metrics['comment_lines'] += 1
            else:
                metrics['code_lines'] += 1
                
                # Count functions and classes
                if stripped.startswith('def '):
                    metrics['function_count'] += 1
                elif stripped.startswith('class '):
                    metrics['class_count'] += 1
                
                # Simple complexity estimate
                complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'with']
                for keyword in complexity_keywords:
                    if f' {keyword} ' in f' {stripped} ' or stripped.startswith(f'{keyword} '):
                        metrics['complexity_estimate'] += 1
        
        return metrics


class RealtimeFileHandler(FileSystemEventHandler):
    """File system event handler for real-time monitoring."""
    
    def __init__(self, analyzer: RealtimeAnalyzer):
        self.analyzer = analyzer
        super().__init__()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            asyncio.create_task(
                self.analyzer._handle_file_change(event.src_path, 'modified')
            )
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            asyncio.create_task(
                self.analyzer._handle_file_change(event.src_path, 'created')
            )
    
    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory:
            # Remove from analysis results
            file_path = str(Path(event.src_path).resolve())
            if file_path in self.analyzer._analysis_results:
                del self.analyzer._analysis_results[file_path]
            if file_path in self.analyzer._last_analysis_time:
                del self.analyzer._last_analysis_time[file_path]
            
            logger.debug(f"File deleted: {event.src_path}")
    
    def on_moved(self, event):
        """Handle file move events."""
        if not event.is_directory:
            # Handle as delete + create
            old_path = str(Path(event.src_path).resolve())
            if old_path in self.analyzer._analysis_results:
                del self.analyzer._analysis_results[old_path]
            if old_path in self.analyzer._last_analysis_time:
                del self.analyzer._last_analysis_time[old_path]
            
            asyncio.create_task(
                self.analyzer._handle_file_change(event.dest_path, 'moved')
            )
            
            logger.debug(f"File moved: {event.src_path} -> {event.dest_path}")

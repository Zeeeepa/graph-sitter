"""
Strands Watcher

File system and event watching capabilities for Strands agents.
Based on: https://github.com/strands-agents/sdk-python/blob/main/src/strands/tools/watcher.py
"""

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    # Create dummy classes for when watchdog is not available
    class FileSystemEventHandler:
        pass
    
    class FileSystemEvent:
        def __init__(self):
            self.src_path = ""
            self.is_directory = False
    
    class Observer:
        def schedule(self, *args, **kwargs):
            pass
        def start(self):
            pass
        def stop(self):
            pass
        def join(self):
            pass

logger = logging.getLogger(__name__)


class WatchEventType(Enum):
    """Types of watch events."""
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_MOVED = "file_moved"
    DIRECTORY_CREATED = "directory_created"
    DIRECTORY_MODIFIED = "directory_modified"
    DIRECTORY_DELETED = "directory_deleted"
    DIRECTORY_MOVED = "directory_moved"


@dataclass
class WatchEvent:
    """Represents a file system watch event."""
    event_type: WatchEventType
    path: str
    timestamp: float
    is_directory: bool = False
    src_path: Optional[str] = None  # For move events
    dest_path: Optional[str] = None  # For move events
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WatchConfig:
    """Configuration for file system watching."""
    recursive: bool = True
    ignore_patterns: Set[str] = field(default_factory=lambda: {
        "*.pyc", "*.pyo", "__pycache__", ".git", ".svn", ".hg",
        "*.tmp", "*.swp", "*.log", ".DS_Store"
    })
    include_patterns: Optional[Set[str]] = None
    debounce_delay: float = 0.5  # Delay to debounce rapid events
    max_events_per_second: int = 100
    enable_content_hashing: bool = False


class StrandsFileSystemEventHandler(FileSystemEventHandler):
    """Custom file system event handler for Strands."""
    
    def __init__(self, watcher: 'Watcher'):
        """Initialize the event handler.
        
        Args:
            watcher: Parent watcher instance
        """
        super().__init__()
        self.watcher = watcher
    
    def on_created(self, event: FileSystemEvent):
        """Handle file/directory creation."""
        if event.is_directory:
            watch_event = WatchEvent(
                event_type=WatchEventType.DIRECTORY_CREATED,
                path=event.src_path,
                timestamp=time.time(),
                is_directory=True
            )
        else:
            watch_event = WatchEvent(
                event_type=WatchEventType.FILE_CREATED,
                path=event.src_path,
                timestamp=time.time(),
                is_directory=False
            )
        
        self.watcher._queue_event(watch_event)
    
    def on_modified(self, event: FileSystemEvent):
        """Handle file/directory modification."""
        if event.is_directory:
            watch_event = WatchEvent(
                event_type=WatchEventType.DIRECTORY_MODIFIED,
                path=event.src_path,
                timestamp=time.time(),
                is_directory=True
            )
        else:
            watch_event = WatchEvent(
                event_type=WatchEventType.FILE_MODIFIED,
                path=event.src_path,
                timestamp=time.time(),
                is_directory=False
            )
        
        self.watcher._queue_event(watch_event)
    
    def on_deleted(self, event: FileSystemEvent):
        """Handle file/directory deletion."""
        if event.is_directory:
            watch_event = WatchEvent(
                event_type=WatchEventType.DIRECTORY_DELETED,
                path=event.src_path,
                timestamp=time.time(),
                is_directory=True
            )
        else:
            watch_event = WatchEvent(
                event_type=WatchEventType.FILE_DELETED,
                path=event.src_path,
                timestamp=time.time(),
                is_directory=False
            )
        
        self.watcher._queue_event(watch_event)
    
    def on_moved(self, event: FileSystemEvent):
        """Handle file/directory move."""
        if event.is_directory:
            watch_event = WatchEvent(
                event_type=WatchEventType.DIRECTORY_MOVED,
                path=event.dest_path,
                timestamp=time.time(),
                is_directory=True,
                src_path=event.src_path,
                dest_path=event.dest_path
            )
        else:
            watch_event = WatchEvent(
                event_type=WatchEventType.FILE_MOVED,
                path=event.dest_path,
                timestamp=time.time(),
                is_directory=False,
                src_path=event.src_path,
                dest_path=event.dest_path
            )
        
        self.watcher._queue_event(watch_event)


class Watcher:
    """Advanced file system watcher with debouncing and filtering."""
    
    def __init__(self, config: Optional[WatchConfig] = None):
        """Initialize the watcher.
        
        Args:
            config: Optional watcher configuration
        """
        self.config = config or WatchConfig()
        self.observers: Dict[str, Observer] = {}
        self.event_handlers: List[Callable[[WatchEvent], None]] = []
        
        # Event processing
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.debounce_cache: Dict[str, float] = {}
        self.event_counts: Dict[float, int] = {}  # Events per second tracking
        
        # Statistics
        self.stats = {
            "events_processed": 0,
            "events_debounced": 0,
            "events_filtered": 0,
            "watches_active": 0
        }
        
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        
        logger.info("Initialized Strands watcher")
    
    async def start(self):
        """Start the watcher."""
        if self._running:
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        
        logger.info("Started Strands watcher")
    
    async def stop(self):
        """Stop the watcher."""
        if not self._running:
            return
        
        self._running = False
        
        # Stop all observers
        for path, observer in self.observers.items():
            observer.stop()
            observer.join()
            logger.debug(f"Stopped watching: {path}")
        
        self.observers.clear()
        
        # Stop event processor
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped Strands watcher")
    
    def watch_path(self, path: str) -> bool:
        """Start watching a path.
        
        Args:
            path: Path to watch
            
        Returns:
            True if watching started successfully
        """
        if not WATCHDOG_AVAILABLE:
            logger.warning("Watchdog not available, file watching disabled")
            return False
        
        path = os.path.abspath(path)
        
        if not os.path.exists(path):
            logger.error(f"Path does not exist: {path}")
            return False
        
        if path in self.observers:
            logger.warning(f"Already watching path: {path}")
            return True
        
        try:
            observer = Observer()
            event_handler = StrandsFileSystemEventHandler(self)
            
            observer.schedule(
                event_handler,
                path,
                recursive=self.config.recursive
            )
            
            observer.start()
            self.observers[path] = observer
            self.stats["watches_active"] = len(self.observers)
            
            logger.info(f"Started watching path: {path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to watch path {path}: {e}")
            return False
    
    def unwatch_path(self, path: str):
        """Stop watching a path.
        
        Args:
            path: Path to stop watching
        """
        path = os.path.abspath(path)
        
        if path not in self.observers:
            logger.warning(f"Not watching path: {path}")
            return
        
        observer = self.observers[path]
        observer.stop()
        observer.join()
        
        del self.observers[path]
        self.stats["watches_active"] = len(self.observers)
        
        logger.info(f"Stopped watching path: {path}")
    
    def add_event_handler(self, handler: Callable[[WatchEvent], None]):
        """Add an event handler.
        
        Args:
            handler: Function to handle watch events
        """
        self.event_handlers.append(handler)
        logger.info("Added watch event handler")
    
    def remove_event_handler(self, handler: Callable[[WatchEvent], None]):
        """Remove an event handler.
        
        Args:
            handler: Handler to remove
        """
        if handler in self.event_handlers:
            self.event_handlers.remove(handler)
            logger.info("Removed watch event handler")
    
    def _queue_event(self, event: WatchEvent):
        """Queue an event for processing.
        
        Args:
            event: Event to queue
        """
        # Check rate limiting
        current_second = int(time.time())
        if current_second not in self.event_counts:
            self.event_counts[current_second] = 0
        
        self.event_counts[current_second] += 1
        
        if self.event_counts[current_second] > self.config.max_events_per_second:
            logger.warning(f"Rate limit exceeded, dropping event: {event.path}")
            return
        
        # Clean old event counts
        old_seconds = [s for s in self.event_counts.keys() if s < current_second - 5]
        for s in old_seconds:
            del self.event_counts[s]
        
        # Queue the event
        try:
            self.event_queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Event queue full, dropping event")
    
    async def _process_events(self):
        """Process queued events."""
        logger.debug("Starting event processing loop")
        
        while self._running:
            try:
                # Get event with timeout
                try:
                    event = await asyncio.wait_for(
                        self.event_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Apply filters
                if not self._should_process_event(event):
                    self.stats["events_filtered"] += 1
                    continue
                
                # Apply debouncing
                if self._is_debounced(event):
                    self.stats["events_debounced"] += 1
                    continue
                
                # Process event
                await self._handle_event(event)
                self.stats["events_processed"] += 1
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
                await asyncio.sleep(0.1)
    
    def _should_process_event(self, event: WatchEvent) -> bool:
        """Check if event should be processed based on filters.
        
        Args:
            event: Event to check
            
        Returns:
            True if event should be processed
        """
        path = Path(event.path)
        
        # Check ignore patterns
        for pattern in self.config.ignore_patterns:
            if path.match(pattern):
                return False
        
        # Check include patterns (if specified)
        if self.config.include_patterns:
            for pattern in self.config.include_patterns:
                if path.match(pattern):
                    return True
            return False
        
        return True
    
    def _is_debounced(self, event: WatchEvent) -> bool:
        """Check if event should be debounced.
        
        Args:
            event: Event to check
            
        Returns:
            True if event should be debounced
        """
        cache_key = f"{event.event_type.value}:{event.path}"
        current_time = time.time()
        
        if cache_key in self.debounce_cache:
            last_time = self.debounce_cache[cache_key]
            if current_time - last_time < self.config.debounce_delay:
                return True
        
        self.debounce_cache[cache_key] = current_time
        
        # Clean old entries
        old_keys = [
            key for key, timestamp in self.debounce_cache.items()
            if current_time - timestamp > self.config.debounce_delay * 2
        ]
        for key in old_keys:
            del self.debounce_cache[key]
        
        return False
    
    async def _handle_event(self, event: WatchEvent):
        """Handle a processed event.
        
        Args:
            event: Event to handle
        """
        # Add metadata if enabled
        if self.config.enable_content_hashing and not event.is_directory:
            try:
                if os.path.exists(event.path):
                    import hashlib
                    with open(event.path, 'rb') as f:
                        content_hash = hashlib.md5(f.read()).hexdigest()
                    event.metadata['content_hash'] = content_hash
            except Exception as e:
                logger.debug(f"Failed to hash file {event.path}: {e}")
        
        # Call event handlers
        for handler in self.event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get watcher status.
        
        Returns:
            Status information
        """
        return {
            "running": self._running,
            "watched_paths": list(self.observers.keys()),
            "event_handlers": len(self.event_handlers),
            "queue_size": self.event_queue.qsize(),
            "debounce_cache_size": len(self.debounce_cache),
            "stats": self.stats.copy(),
            "config": {
                "recursive": self.config.recursive,
                "debounce_delay": self.config.debounce_delay,
                "max_events_per_second": self.config.max_events_per_second,
                "ignore_patterns": list(self.config.ignore_patterns)
            }
        }

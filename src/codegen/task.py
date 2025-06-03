"""
Enhanced Task class for representing Codegen agent tasks with comprehensive monitoring.
"""

import time
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Callable
from datetime import datetime, timezone

from .exceptions import TaskError, TimeoutError

if TYPE_CHECKING:
    from .agent import Agent

logger = logging.getLogger(__name__)


class Task:
    """
    Enhanced Task class representing a task executed by a Codegen agent.
    
    Includes comprehensive monitoring, artifact management, and event handling.
    """
    
    def __init__(self, task_id: str, agent: 'Agent', task_info: Optional[Dict[str, Any]] = None):
        """
        Initialize a Task.
        
        Args:
            task_id: Unique task identifier
            agent: The agent instance that created this task
            task_info: Initial task data from the API
        """
        self.task_id = task_id
        self.agent = agent
        self._task_info = task_info or {}
        self._last_refresh_time: Optional[float] = None
        self._artifacts_cache: Optional[List[Dict[str, Any]]] = None
        self._logs_cache: Optional[List[str]] = None
        self._status_callbacks: List[Callable[[str, str], None]] = []
        
        # Monitoring
        self._refresh_count = 0
        self._creation_time = time.time()
        
        logger.info(f"Task {task_id} initialized with status: {self.status}")
    
    @property
    def status(self) -> str:
        """Current task status."""
        return self._task_info.get("status", "unknown")
    
    @property
    def result(self) -> Optional[str]:
        """Task result (if completed)."""
        return self._task_info.get("result")
    
    @property
    def error(self) -> Optional[str]:
        """Error message (if failed)."""
        return self._task_info.get("error")
    
    @property
    def progress(self) -> Optional[Dict[str, Any]]:
        """Progress information."""
        return self._task_info.get("progress", {})
    
    @property
    def created_at(self) -> Optional[str]:
        """Creation timestamp."""
        return self._task_info.get("created_at")
    
    @property
    def updated_at(self) -> Optional[str]:
        """Last update timestamp."""
        return self._task_info.get("updated_at")
    
    @property
    def prompt(self) -> Optional[str]:
        """Original prompt."""
        return self._task_info.get("prompt")
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """Additional metadata."""
        return self._task_info.get("metadata", {})
    
    @property
    def logs(self) -> List[str]:
        """Execution logs."""
        if self._logs_cache is None:
            self._logs_cache = self._task_info.get("logs", [])
        return self._logs_cache or []  # Return empty list if None
    
    @property
    def is_terminal(self) -> bool:
        """Check if task is in a terminal state."""
        return self.status in ["completed", "failed", "cancelled"]
    
    @property
    def is_running(self) -> bool:
        """Check if task is currently running."""
        return self.status in ["pending", "running", "in_progress"]
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.created_at and self.updated_at:
            try:
                created = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
                updated = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
                return (updated - created).total_seconds()
            except (ValueError, AttributeError):
                pass
        return None
    
    def add_status_callback(self, callback: Callable[[str, str], None]):
        """
        Add a callback to be called when status changes.
        
        Args:
            callback: Function that takes (old_status, new_status) as arguments
        """
        self._status_callbacks.append(callback)
    
    def refresh(self) -> None:
        """Refresh task data from the API with enhanced error handling."""
        try:
            old_status = self.status
            self._task_info = self.agent._get_task(self.task_id)
            new_status = self.status
            
            # Clear caches
            self._artifacts_cache = None
            self._logs_cache = None
            
            # Update monitoring
            self._refresh_count += 1
            self._last_refresh_time = time.time()
            
            # Call status callbacks if status changed
            if old_status != new_status:
                logger.info(f"Task {self.task_id} status changed: {old_status} -> {new_status}")
                for callback in self._status_callbacks:
                    try:
                        callback(old_status, new_status)
                    except Exception as e:
                        logger.warning(f"Status callback failed: {e}")
            
        except Exception as e:
            logger.error(f"Failed to refresh task {self.task_id}: {e}")
            raise TaskError(f"Failed to refresh task {self.task_id}: {str(e)}", task_id=self.task_id)
    
    def wait_for_completion(
        self, 
        timeout: int = 300, 
        poll_interval: int = 5,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> None:
        """
        Wait for task completion with enhanced monitoring.
        
        Args:
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            progress_callback: Optional callback for progress updates
            
        Raises:
            TaskError: If task fails or is cancelled
            TimeoutError: If task times out
        """
        start_time = time.time()
        last_progress = None
        
        logger.info(f"Waiting for task {self.task_id} completion (timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            self.refresh()
            
            # Call progress callback if progress changed
            if progress_callback and self.progress != last_progress:
                try:
                    progress_data = self.progress or {}  # Ensure we have a dict
                    progress_callback(progress_data)
                    last_progress = self.progress.copy() if self.progress else None
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")
            
            if self.is_terminal:
                if self.status == "failed":
                    raise TaskError(
                        f"Task failed: {self.error}", 
                        task_id=self.task_id, 
                        task_status=self.status
                    )
                elif self.status == "cancelled":
                    raise TaskError(
                        "Task was cancelled", 
                        task_id=self.task_id, 
                        task_status=self.status
                    )
                
                logger.info(f"Task {self.task_id} completed successfully")
                return  # Completed successfully
            
            time.sleep(poll_interval)
        
        elapsed = time.time() - start_time
        raise TimeoutError(
            f"Task timed out after {elapsed:.1f} seconds", 
            timeout_duration=elapsed
        )
    
    def cancel(self) -> None:
        """Cancel the task with enhanced error handling."""
        try:
            logger.info(f"Cancelling task {self.task_id}")
            result = self.agent._cancel_task(self.task_id)
            self._task_info.update(result)
            logger.info(f"Task {self.task_id} cancelled successfully")
        except Exception as e:
            logger.error(f"Failed to cancel task {self.task_id}: {e}")
            raise TaskError(f"Failed to cancel task {self.task_id}: {str(e)}", task_id=self.task_id)
    
    def get_artifacts(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get task artifacts with caching.
        
        Args:
            force_refresh: Force refresh of artifacts cache
            
        Returns:
            List of artifact dictionaries
        """
        if self._artifacts_cache is None or force_refresh:
            try:
                self._artifacts_cache = self.agent._get_task_artifacts(self.task_id)
                logger.debug(f"Retrieved {len(self._artifacts_cache)} artifacts for task {self.task_id}")
            except Exception as e:
                logger.warning(f"Failed to get artifacts for task {self.task_id}: {e}")
                self._artifacts_cache = []
        
        return self._artifacts_cache or []  # Return empty list if None
    
    def get_logs(self, force_refresh: bool = False) -> List[str]:
        """
        Get task logs with caching.
        
        Args:
            force_refresh: Force refresh of logs cache
            
        Returns:
            List of log messages
        """
        if self._logs_cache is None or force_refresh:
            try:
                logs_data = self.agent._get_task_logs(self.task_id)
                self._logs_cache = logs_data.get("logs", [])
                logger.debug(f"Retrieved {len(self._logs_cache)} log entries for task {self.task_id}")
            except Exception as e:
                logger.warning(f"Failed to get logs for task {self.task_id}: {e}")
                self._logs_cache = []
        
        return self._logs_cache or []  # Return empty list if None
    
    def get_monitoring_info(self) -> Dict[str, Any]:
        """Get comprehensive monitoring information."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "creation_time": self._creation_time,
            "refresh_count": self._refresh_count,
            "last_refresh_time": self._last_refresh_time,
            "duration": self.duration,
            "is_terminal": self.is_terminal,
            "is_running": self.is_running,
            "artifacts_count": len(self.get_artifacts()),
            "logs_count": len(self.get_logs()),
            "progress": self.progress
        }
    
    def __str__(self) -> str:
        """String representation of the task."""
        return f"Task({self.task_id}, status={self.status})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the task."""
        return f"Task(id={self.task_id}, status={self.status}, refreshes={self._refresh_count})"

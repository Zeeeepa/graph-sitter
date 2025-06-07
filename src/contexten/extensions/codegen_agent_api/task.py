"""
Enhanced Task class for representing Codegen agent tasks with comprehensive monitoring.

Migrated from src/codegen/task.py with contexten extension integration.
"""

import time
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Callable
from datetime import datetime, timezone

from .types import TaskStatus, TaskProgress, TaskMetrics, StatusCallback, ProgressCallback
from .exceptions import TaskError, TimeoutError

if TYPE_CHECKING:
    from .agent import Agent

logger = logging.getLogger(__name__)


class Task:
    """
    Enhanced Task class representing a task executed by a Codegen agent.
    
    Includes comprehensive monitoring, artifact management, and event handling
    with contexten extension integration.
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
        self._status_callbacks: List[StatusCallback] = []
        self._progress_callbacks: List[ProgressCallback] = []
        
        # Enhanced monitoring with metrics
        self._metrics = TaskMetrics(
            creation_time=time.time(),
            start_time=time.time() if self.status in ["running", "in_progress"] else None
        )
        
        logger.info(f"Task {task_id} initialized with status: {self.status} (contexten extension)")
    
    @property
    def status(self) -> str:
        """Current task status."""
        return self._task_info.get("status", "unknown")
    
    @property
    def status_enum(self) -> TaskStatus:
        """Current task status as enum."""
        try:
            return TaskStatus(self.status)
        except ValueError:
            return TaskStatus.PENDING  # Default fallback
    
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
    def progress_obj(self) -> Optional[TaskProgress]:
        """Progress information as TaskProgress object."""
        progress_data = self.progress
        if not progress_data:
            return None
        
        return TaskProgress(
            current_step=progress_data.get("current_step", ""),
            total_steps=progress_data.get("total_steps", 0),
            completed_steps=progress_data.get("completed_steps", 0),
            percentage=progress_data.get("percentage", 0.0),
            estimated_remaining_seconds=progress_data.get("estimated_remaining_seconds"),
            details=progress_data.get("details")
        )
    
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
        return self.status in ["completed", "failed", "cancelled", "timeout"]
    
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
    
    @property
    def metrics(self) -> TaskMetrics:
        """Get task metrics."""
        # Update end time if task is terminal
        if self.is_terminal and self._metrics.end_time is None:
            self._metrics.end_time = time.time()
        
        return self._metrics
    
    def add_status_callback(self, callback: StatusCallback) -> None:
        """
        Add a callback to be called when status changes.
        
        Args:
            callback: Function that takes (old_status, new_status) as arguments
        """
        self._status_callbacks.append(callback)
    
    def add_progress_callback(self, callback: ProgressCallback) -> None:
        """
        Add a callback to be called when progress changes.
        
        Args:
            callback: Function that takes TaskProgress as argument
        """
        self._progress_callbacks.append(callback)
    
    def remove_status_callback(self, callback: StatusCallback) -> None:
        """Remove a status callback."""
        if callback in self._status_callbacks:
            self._status_callbacks.remove(callback)
    
    def remove_progress_callback(self, callback: ProgressCallback) -> None:
        """Remove a progress callback."""
        if callback in self._progress_callbacks:
            self._progress_callbacks.remove(callback)
    
    def refresh(self) -> None:
        """Refresh task data from the API with enhanced error handling."""
        try:
            old_status = self.status
            old_progress = self.progress_obj
            
            self._task_info = self.agent._get_task(self.task_id)
            new_status = self.status
            new_progress = self.progress_obj
            
            # Clear caches
            self._artifacts_cache = None
            self._logs_cache = None
            
            # Update monitoring
            self._metrics.refresh_count += 1
            self._metrics.last_refresh_time = time.time()
            self._last_refresh_time = time.time()
            
            # Update start time if task started running
            if old_status in ["pending"] and new_status in ["running", "in_progress"]:
                self._metrics.start_time = time.time()
            
            # Call status callbacks if status changed
            if old_status != new_status:
                logger.info(f"Task {self.task_id} status changed: {old_status} -> {new_status}")
                for callback in self._status_callbacks:
                    try:
                        callback(old_status, new_status)
                    except Exception as e:
                        logger.warning(f"Status callback failed: {e}")
            
            # Call progress callbacks if progress changed
            if new_progress and (not old_progress or old_progress.percentage != new_progress.percentage):
                for callback in self._progress_callbacks:
                    try:
                        callback(new_progress)
                    except Exception as e:
                        logger.warning(f"Progress callback failed: {e}")
            
        except Exception as e:
            logger.error(f"Failed to refresh task {self.task_id}: {e}")
            raise TaskError(f"Failed to refresh task {self.task_id}: {str(e)}", task_id=self.task_id)
    
    def wait_for_completion(
        self, 
        timeout: int = 300, 
        poll_interval: int = 5,
        progress_callback: Optional[ProgressCallback] = None
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
        
        # Add temporary progress callback if provided
        if progress_callback:
            self.add_progress_callback(progress_callback)
        
        logger.info(f"Waiting for task {self.task_id} completion (timeout: {timeout}s)")
        
        try:
            while time.time() - start_time < timeout:
                self.refresh()
                
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
                    elif self.status == "timeout":
                        raise TaskError(
                            "Task timed out", 
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
        
        finally:
            # Remove temporary progress callback
            if progress_callback:
                self.remove_progress_callback(progress_callback)
    
    def cancel(self) -> None:
        """Cancel the task with enhanced error handling."""
        try:
            logger.info(f"Cancelling task {self.task_id}")
            result = self.agent._cancel_task(self.task_id)
            self._task_info.update(result)
            
            # Update metrics
            if self._metrics.end_time is None:
                self._metrics.end_time = time.time()
            
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
            "status_enum": self.status_enum.value,
            "creation_time": self._metrics.creation_time,
            "start_time": self._metrics.start_time,
            "end_time": self._metrics.end_time,
            "refresh_count": self._metrics.refresh_count,
            "last_refresh_time": self._metrics.last_refresh_time,
            "duration": self.duration,
            "metrics_duration": self._metrics.duration,
            "total_lifetime": self._metrics.total_lifetime,
            "is_terminal": self.is_terminal,
            "is_running": self.is_running,
            "artifacts_count": len(self.get_artifacts()),
            "logs_count": len(self.get_logs()),
            "progress": self.progress,
            "progress_obj": self.progress_obj.to_dict() if self.progress_obj else None,
            "callbacks": {
                "status_callbacks": len(self._status_callbacks),
                "progress_callbacks": len(self._progress_callbacks)
            }
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary representation."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "result": self.result,
            "error": self.error,
            "progress": self.progress,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "prompt": self.prompt,
            "metadata": self.metadata,
            "is_terminal": self.is_terminal,
            "is_running": self.is_running,
            "duration": self.duration,
            "monitoring_info": self.get_monitoring_info()
        }
    
    def __str__(self) -> str:
        """String representation of the task."""
        return f"Task({self.task_id}, status={self.status})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the task."""
        return f"Task(id={self.task_id}, status={self.status}, refreshes={self._metrics.refresh_count})"
    
    def __eq__(self, other) -> bool:
        """Check equality based on task ID."""
        if isinstance(other, Task):
            return self.task_id == other.task_id
        return False
    
    def __hash__(self) -> int:
        """Hash based on task ID."""
        return hash(self.task_id)


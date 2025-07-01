"""
Task class for representing Codegen agent tasks.
"""

import time
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .exceptions import TaskError

if TYPE_CHECKING:
    from .agent import Agent


class Task:
    """Represents a task executed by a Codegen agent."""
    
    def __init__(self, task_id: str, agent: "Agent", task_data: Dict[str, Any]):
        """
        Initialize a Task.
        
        Args:
            task_id: Unique task identifier
            agent: The agent instance that created this task
            task_data: Initial task data from the API
        """
        self.task_id = task_id
        self.agent = agent
        self._data = task_data
    
    @property
    def status(self) -> str:
        """Current task status."""
        return self._data.get("status", "unknown")
    
    @property
    def result(self) -> Optional[str]:
        """Task result (if completed)."""
        return self._data.get("result")
    
    @property
    def error(self) -> Optional[str]:
        """Error message (if failed)."""
        return self._data.get("error")
    
    @property
    def progress(self) -> Optional[Dict[str, Any]]:
        """Progress information."""
        return self._data.get("progress")
    
    @property
    def created_at(self) -> Optional[str]:
        """Creation timestamp."""
        return self._data.get("created_at")
    
    @property
    def updated_at(self) -> Optional[str]:
        """Last update timestamp."""
        return self._data.get("updated_at")
    
    @property
    def prompt(self) -> Optional[str]:
        """Original prompt."""
        return self._data.get("prompt")
    
    @property
    def metadata(self) -> Optional[Dict[str, Any]]:
        """Additional metadata."""
        return self._data.get("metadata", {})
    
    @property
    def logs(self) -> List[str]:
        """Execution logs."""
        return self._data.get("logs", [])
    
    def refresh(self) -> None:
        """Refresh task data from the API."""
        try:
            self._data = self.agent._get_task(self.task_id)
        except Exception as e:
            raise TaskError(f"Failed to refresh task {self.task_id}: {str(e)}")
    
    def wait_for_completion(self, timeout: int = 300, poll_interval: int = 5) -> None:
        """
        Wait for task completion.
        
        Args:
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Raises:
            TaskError: If task fails or times out
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            self.refresh()
            
            if self.status in ["completed", "failed", "cancelled"]:
                if self.status == "failed":
                    raise TaskError(f"Task failed: {self.error}")
                elif self.status == "cancelled":
                    raise TaskError("Task was cancelled")
                return  # Completed successfully
            
            time.sleep(poll_interval)
        
        raise TaskError(f"Task timed out after {timeout} seconds")
    
    def cancel(self) -> None:
        """Cancel the task."""
        try:
            self._data = self.agent._cancel_task(self.task_id)
        except Exception as e:
            raise TaskError(f"Failed to cancel task {self.task_id}: {str(e)}")
    
    def get_artifacts(self) -> List[Dict[str, Any]]:
        """Get task artifacts."""
        try:
            return self.agent._get_task_artifacts(self.task_id)
        except Exception as e:
            raise TaskError(f"Failed to get artifacts for task {self.task_id}: {str(e)}")
    
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
            "logs": self.logs
        }
    
    def __str__(self) -> str:
        """String representation of the task."""
        return f"Task({self.task_id}, status={self.status})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the task."""
        return f"Task(task_id={self.task_id}, status={self.status}, created_at={self.created_at})"


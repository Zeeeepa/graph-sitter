"""
Task execution logging system
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID


class TaskLogger:
    """
    Comprehensive task execution logging
    
    Features:
    - Structured logging for task events
    - Performance tracking
    - Error logging and analysis
    - Audit trail for task operations
    """
    
    def __init__(self, 
                 logger_name: str = "task_management",
                 log_level: int = logging.INFO,
                 log_format: Optional[str] = None):
        
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(log_level)
        
        # Create formatter
        if log_format is None:
            log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        formatter = logging.Formatter(log_format)
        
        # Create console handler if no handlers exist
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
    
    def log_task_created(self, task_id: UUID, task_name: str, created_by: str, metadata: Dict[str, Any] = None) -> None:
        """Log task creation"""
        self._log_structured("INFO", "task_created", {
            "task_id": str(task_id),
            "task_name": task_name,
            "created_by": created_by,
            "metadata": metadata or {}
        })
    
    def log_task_started(self, task_id: UUID, executor_id: str, execution_id: UUID) -> None:
        """Log task execution start"""
        self._log_structured("INFO", "task_started", {
            "task_id": str(task_id),
            "executor_id": executor_id,
            "execution_id": str(execution_id)
        })
    
    def log_task_completed(self, task_id: UUID, execution_id: UUID, duration_seconds: float, result: Dict[str, Any] = None) -> None:
        """Log task completion"""
        self._log_structured("INFO", "task_completed", {
            "task_id": str(task_id),
            "execution_id": str(execution_id),
            "duration_seconds": duration_seconds,
            "result_summary": self._summarize_result(result)
        })
    
    def log_task_failed(self, task_id: UUID, execution_id: UUID, error_message: str, error_details: Dict[str, Any] = None) -> None:
        """Log task failure"""
        self._log_structured("ERROR", "task_failed", {
            "task_id": str(task_id),
            "execution_id": str(execution_id),
            "error_message": error_message,
            "error_details": error_details or {}
        })
    
    def log_task_cancelled(self, task_id: UUID, execution_id: UUID, reason: str) -> None:
        """Log task cancellation"""
        self._log_structured("WARNING", "task_cancelled", {
            "task_id": str(task_id),
            "execution_id": str(execution_id),
            "reason": reason
        })
    
    def log_task_retried(self, task_id: UUID, retry_count: int, max_retries: int, reason: str) -> None:
        """Log task retry"""
        self._log_structured("WARNING", "task_retried", {
            "task_id": str(task_id),
            "retry_count": retry_count,
            "max_retries": max_retries,
            "reason": reason
        })
    
    def log_workflow_started(self, workflow_id: UUID, workflow_name: str, step_count: int) -> None:
        """Log workflow start"""
        self._log_structured("INFO", "workflow_started", {
            "workflow_id": str(workflow_id),
            "workflow_name": workflow_name,
            "step_count": step_count
        })
    
    def log_workflow_completed(self, workflow_id: UUID, duration_seconds: float, completed_steps: int, failed_steps: int) -> None:
        """Log workflow completion"""
        self._log_structured("INFO", "workflow_completed", {
            "workflow_id": str(workflow_id),
            "duration_seconds": duration_seconds,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps
        })
    
    def log_workflow_failed(self, workflow_id: UUID, error_message: str, completed_steps: int, failed_steps: int) -> None:
        """Log workflow failure"""
        self._log_structured("ERROR", "workflow_failed", {
            "workflow_id": str(workflow_id),
            "error_message": error_message,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps
        })
    
    def log_dependency_resolved(self, task_id: UUID, dependency_chain: list) -> None:
        """Log dependency resolution"""
        self._log_structured("DEBUG", "dependency_resolved", {
            "task_id": str(task_id),
            "dependency_chain": [str(dep_id) for dep_id in dependency_chain]
        })
    
    def log_circular_dependency(self, task_ids: list, cycle_path: list) -> None:
        """Log circular dependency detection"""
        self._log_structured("ERROR", "circular_dependency", {
            "task_ids": [str(task_id) for task_id in task_ids],
            "cycle_path": [str(task_id) for task_id in cycle_path]
        })
    
    def log_resource_usage(self, execution_id: UUID, cpu_percent: float, memory_mb: float, additional_metrics: Dict[str, float] = None) -> None:
        """Log resource usage"""
        self._log_structured("DEBUG", "resource_usage", {
            "execution_id": str(execution_id),
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "additional_metrics": additional_metrics or {}
        })
    
    def log_agent_registered(self, agent_id: str, agent_type: str, capabilities: list) -> None:
        """Log agent registration"""
        self._log_structured("INFO", "agent_registered", {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "capabilities": capabilities
        })
    
    def log_agent_unregistered(self, agent_id: str) -> None:
        """Log agent unregistration"""
        self._log_structured("INFO", "agent_unregistered", {
            "agent_id": agent_id
        })
    
    def log_scheduler_stats(self, stats: Dict[str, Any]) -> None:
        """Log scheduler statistics"""
        self._log_structured("INFO", "scheduler_stats", stats)
    
    def log_performance_alert(self, alert_type: str, message: str, metrics: Dict[str, Any]) -> None:
        """Log performance alerts"""
        self._log_structured("WARNING", "performance_alert", {
            "alert_type": alert_type,
            "message": message,
            "metrics": metrics
        })
    
    def log_info(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log general info message"""
        self._log_structured("INFO", "general", {
            "message": message,
            "context": context or {}
        })
    
    def log_warning(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log warning message"""
        self._log_structured("WARNING", "general", {
            "message": message,
            "context": context or {}
        })
    
    def log_error(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log error message"""
        self._log_structured("ERROR", "general", {
            "message": message,
            "context": context or {}
        })
    
    def log_debug(self, message: str, context: Dict[str, Any] = None) -> None:
        """Log debug message"""
        self._log_structured("DEBUG", "general", {
            "message": message,
            "context": context or {}
        })
    
    def _log_structured(self, level: str, event_type: str, data: Dict[str, Any]) -> None:
        """Log structured event"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "level": level,
            **data
        }
        
        # Convert to JSON string for structured logging
        log_message = json.dumps(log_entry, default=str)
        
        # Log at appropriate level
        if level == "DEBUG":
            self.logger.debug(log_message)
        elif level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)
    
    def _summarize_result(self, result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary of task result for logging"""
        if not result:
            return {}
        
        summary = {}
        
        # Include basic result info
        if "status" in result:
            summary["status"] = result["status"]
        
        if "message" in result:
            summary["message"] = result["message"][:200]  # Truncate long messages
        
        # Include result size info
        summary["result_keys"] = list(result.keys())
        summary["result_size"] = len(str(result))
        
        return summary
    
    def add_file_handler(self, log_file_path: str, log_level: int = logging.INFO) -> None:
        """Add file handler for logging to file"""
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
    
    def set_log_level(self, log_level: int) -> None:
        """Set logging level"""
        self.logger.setLevel(log_level)
    
    def get_logger(self) -> logging.Logger:
        """Get underlying logger instance"""
        return self.logger


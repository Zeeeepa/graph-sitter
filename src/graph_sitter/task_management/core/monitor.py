"""
Task Monitoring and Metrics Collection

Provides comprehensive monitoring capabilities for task execution,
performance tracking, and system health metrics.
"""

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Deque
import statistics

from .task import Task, TaskStatus, TaskType, TaskPriority


logger = logging.getLogger(__name__)


@dataclass
class TaskMetrics:
    """Metrics for individual task execution."""
    task_id: str
    task_type: TaskType
    priority: TaskPriority
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    status: TaskStatus = TaskStatus.RUNNING
    error_message: Optional[str] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringMetrics:
    """Aggregated monitoring metrics for the task management system."""
    
    # Task execution metrics
    total_tasks_created: int = 0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    total_tasks_cancelled: int = 0
    
    # Performance metrics
    average_execution_time: float = 0.0
    median_execution_time: float = 0.0
    min_execution_time: float = 0.0
    max_execution_time: float = 0.0
    
    # Throughput metrics
    tasks_per_minute: float = 0.0
    tasks_per_hour: float = 0.0
    
    # Error metrics
    error_rate: float = 0.0
    timeout_rate: float = 0.0
    retry_rate: float = 0.0
    
    # Resource metrics
    average_cpu_usage: float = 0.0
    average_memory_usage: float = 0.0
    peak_concurrent_tasks: int = 0
    
    # Queue metrics
    average_queue_time: float = 0.0
    current_queue_size: int = 0
    
    # Type-specific metrics
    metrics_by_type: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metrics_by_priority: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Time-based metrics
    last_updated: datetime = field(default_factory=datetime.utcnow)
    monitoring_period_hours: float = 24.0


class TaskMonitor:
    """
    Comprehensive task monitoring and metrics collection system.
    
    Tracks task execution, performance metrics, resource usage,
    and provides analytics for system optimization.
    """
    
    def __init__(self, history_size: int = 10000, metrics_window_hours: float = 24.0):
        """Initialize the task monitor."""
        self.history_size = history_size
        self.metrics_window_hours = metrics_window_hours
        
        # Task tracking
        self._task_metrics: Dict[str, TaskMetrics] = {}
        self._completed_metrics: Deque[TaskMetrics] = deque(maxlen=history_size)
        self._active_tasks: Dict[str, TaskMetrics] = {}
        
        # Performance tracking
        self._execution_times: Deque[float] = deque(maxlen=history_size)
        self._queue_times: Deque[float] = deque(maxlen=history_size)
        self._throughput_samples: Deque[tuple] = deque(maxlen=1440)  # 24 hours of minute samples
        
        # Error tracking
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._timeout_count: int = 0
        self._retry_count: int = 0
        
        # Resource tracking
        self._resource_samples: Deque[Dict[str, Any]] = deque(maxlen=1440)
        self._peak_concurrent: int = 0
        
        # Synchronization
        self._lock = threading.RLock()
        
        # Background monitoring
        self._monitoring_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._start_monitoring()
        
        logger.info(f"TaskMonitor initialized with history size {history_size}")
    
    def _start_monitoring(self) -> None:
        """Start background monitoring thread."""
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_worker,
            daemon=True,
            name="TaskMonitor"
        )
        self._monitoring_thread.start()
    
    def _monitoring_worker(self) -> None:
        """Background worker for periodic monitoring tasks."""
        while not self._shutdown_event.is_set():
            try:
                self._collect_system_metrics()
                self._update_throughput_metrics()
                self._cleanup_old_metrics()
            except Exception as e:
                logger.error(f"Error in monitoring worker: {e}")
            
            # Wait for next collection interval (1 minute)
            self._shutdown_event.wait(60)
    
    def task_created(self, task: Task) -> None:
        """Record that a task was created."""
        with self._lock:
            metrics = TaskMetrics(
                task_id=task.id,
                task_type=task.task_type,
                priority=task.priority,
                start_time=task.created_at,
                status=task.status
            )
            self._task_metrics[task.id] = metrics
            
            logger.debug(f"Recorded task creation: {task.id}")
    
    def task_started(self, task: Task) -> None:
        """Record that a task started execution."""
        with self._lock:
            if task.id in self._task_metrics:
                metrics = self._task_metrics[task.id]
                metrics.start_time = task.started_at or datetime.utcnow()
                metrics.status = TaskStatus.RUNNING
                self._active_tasks[task.id] = metrics
                
                # Update peak concurrent tasks
                current_concurrent = len(self._active_tasks)
                if current_concurrent > self._peak_concurrent:
                    self._peak_concurrent = current_concurrent
                
                # Calculate queue time
                if task.created_at:
                    queue_time = (metrics.start_time - task.created_at).total_seconds()
                    self._queue_times.append(queue_time)
                
                logger.debug(f"Recorded task start: {task.id}")
    
    def task_completed(self, task: Task) -> None:
        """Record that a task completed successfully."""
        with self._lock:
            if task.id in self._task_metrics:
                metrics = self._task_metrics[task.id]
                metrics.end_time = task.completed_at or datetime.utcnow()
                metrics.status = TaskStatus.COMPLETED
                
                # Calculate duration
                if task.started_at:
                    duration = (metrics.end_time - task.started_at).total_seconds()
                    metrics.duration_seconds = duration
                    self._execution_times.append(duration)
                
                # Move to completed metrics
                self._completed_metrics.append(metrics)
                self._active_tasks.pop(task.id, None)
                
                logger.debug(f"Recorded task completion: {task.id}")
    
    def task_failed(self, task: Task, error: Exception) -> None:
        """Record that a task failed."""
        with self._lock:
            if task.id in self._task_metrics:
                metrics = self._task_metrics[task.id]
                metrics.end_time = task.completed_at or datetime.utcnow()
                metrics.status = TaskStatus.FAILED
                metrics.error_message = str(error)
                
                # Calculate duration if started
                if task.started_at:
                    duration = (metrics.end_time - task.started_at).total_seconds()
                    metrics.duration_seconds = duration
                
                # Track error type
                error_type = type(error).__name__
                self._error_counts[error_type] += 1
                
                # Check if it was a timeout
                if "timeout" in str(error).lower():
                    self._timeout_count += 1
                
                # Move to completed metrics
                self._completed_metrics.append(metrics)
                self._active_tasks.pop(task.id, None)
                
                logger.debug(f"Recorded task failure: {task.id}, error: {error}")
    
    def task_cancelled(self, task: Task) -> None:
        """Record that a task was cancelled."""
        with self._lock:
            if task.id in self._task_metrics:
                metrics = self._task_metrics[task.id]
                metrics.end_time = task.completed_at or datetime.utcnow()
                metrics.status = TaskStatus.CANCELLED
                
                # Move to completed metrics
                self._completed_metrics.append(metrics)
                self._active_tasks.pop(task.id, None)
                
                logger.debug(f"Recorded task cancellation: {task.id}")
    
    def task_retried(self, task: Task) -> None:
        """Record that a task was retried."""
        with self._lock:
            self._retry_count += 1
            logger.debug(f"Recorded task retry: {task.id}")
    
    def record_resource_usage(self, task_id: str, resource_data: Dict[str, Any]) -> None:
        """Record resource usage for a task."""
        with self._lock:
            if task_id in self._task_metrics:
                self._task_metrics[task_id].resource_usage.update(resource_data)
    
    def record_custom_metric(self, task_id: str, metric_name: str, value: Any) -> None:
        """Record a custom metric for a task."""
        with self._lock:
            if task_id in self._task_metrics:
                self._task_metrics[task_id].custom_metrics[metric_name] = value
    
    def get_metrics(self) -> MonitoringMetrics:
        """Get comprehensive monitoring metrics."""
        with self._lock:
            return self._calculate_metrics()
    
    def _calculate_metrics(self) -> MonitoringMetrics:
        """Calculate aggregated metrics from collected data."""
        # Get recent metrics within the window
        cutoff_time = datetime.utcnow() - timedelta(hours=self.metrics_window_hours)
        recent_metrics = [
            m for m in self._completed_metrics
            if m.end_time and m.end_time >= cutoff_time
        ]
        
        # Basic counts
        total_created = len(self._task_metrics)
        total_completed = len([m for m in recent_metrics if m.status == TaskStatus.COMPLETED])
        total_failed = len([m for m in recent_metrics if m.status == TaskStatus.FAILED])
        total_cancelled = len([m for m in recent_metrics if m.status == TaskStatus.CANCELLED])
        
        # Execution time statistics
        execution_times = [m.duration_seconds for m in recent_metrics 
                          if m.duration_seconds is not None]
        
        avg_exec_time = statistics.mean(execution_times) if execution_times else 0.0
        median_exec_time = statistics.median(execution_times) if execution_times else 0.0
        min_exec_time = min(execution_times) if execution_times else 0.0
        max_exec_time = max(execution_times) if execution_times else 0.0
        
        # Throughput calculations
        total_recent = len(recent_metrics)
        tasks_per_minute = total_recent / (self.metrics_window_hours * 60) if total_recent > 0 else 0.0
        tasks_per_hour = total_recent / self.metrics_window_hours if total_recent > 0 else 0.0
        
        # Error rates
        total_finished = total_completed + total_failed + total_cancelled
        error_rate = (total_failed / total_finished) if total_finished > 0 else 0.0
        timeout_rate = (self._timeout_count / total_finished) if total_finished > 0 else 0.0
        retry_rate = (self._retry_count / total_created) if total_created > 0 else 0.0
        
        # Queue time statistics
        avg_queue_time = statistics.mean(self._queue_times) if self._queue_times else 0.0
        
        # Type-specific metrics
        metrics_by_type = self._calculate_type_metrics(recent_metrics)
        metrics_by_priority = self._calculate_priority_metrics(recent_metrics)
        
        # Resource metrics (simplified)
        avg_cpu = 0.0
        avg_memory = 0.0
        if self._resource_samples:
            cpu_samples = [s.get('cpu_usage', 0) for s in self._resource_samples]
            memory_samples = [s.get('memory_usage', 0) for s in self._resource_samples]
            avg_cpu = statistics.mean(cpu_samples) if cpu_samples else 0.0
            avg_memory = statistics.mean(memory_samples) if memory_samples else 0.0
        
        return MonitoringMetrics(
            total_tasks_created=total_created,
            total_tasks_completed=total_completed,
            total_tasks_failed=total_failed,
            total_tasks_cancelled=total_cancelled,
            average_execution_time=avg_exec_time,
            median_execution_time=median_exec_time,
            min_execution_time=min_exec_time,
            max_execution_time=max_exec_time,
            tasks_per_minute=tasks_per_minute,
            tasks_per_hour=tasks_per_hour,
            error_rate=error_rate,
            timeout_rate=timeout_rate,
            retry_rate=retry_rate,
            average_cpu_usage=avg_cpu,
            average_memory_usage=avg_memory,
            peak_concurrent_tasks=self._peak_concurrent,
            average_queue_time=avg_queue_time,
            current_queue_size=0,  # This would be provided by the scheduler
            metrics_by_type=metrics_by_type,
            metrics_by_priority=metrics_by_priority,
            monitoring_period_hours=self.metrics_window_hours
        )
    
    def _calculate_type_metrics(self, metrics: List[TaskMetrics]) -> Dict[str, Dict[str, Any]]:
        """Calculate metrics grouped by task type."""
        type_groups = defaultdict(list)
        for metric in metrics:
            type_groups[metric.task_type.value].append(metric)
        
        type_metrics = {}
        for task_type, type_metrics_list in type_groups.items():
            completed = [m for m in type_metrics_list if m.status == TaskStatus.COMPLETED]
            failed = [m for m in type_metrics_list if m.status == TaskStatus.FAILED]
            
            execution_times = [m.duration_seconds for m in completed 
                             if m.duration_seconds is not None]
            
            type_metrics[task_type] = {
                "total_tasks": len(type_metrics_list),
                "completed_tasks": len(completed),
                "failed_tasks": len(failed),
                "success_rate": len(completed) / len(type_metrics_list) if type_metrics_list else 0.0,
                "average_execution_time": statistics.mean(execution_times) if execution_times else 0.0,
            }
        
        return type_metrics
    
    def _calculate_priority_metrics(self, metrics: List[TaskMetrics]) -> Dict[str, Dict[str, Any]]:
        """Calculate metrics grouped by task priority."""
        priority_groups = defaultdict(list)
        for metric in metrics:
            priority_groups[metric.priority.value].append(metric)
        
        priority_metrics = {}
        for priority, priority_metrics_list in priority_groups.items():
            completed = [m for m in priority_metrics_list if m.status == TaskStatus.COMPLETED]
            
            execution_times = [m.duration_seconds for m in completed 
                             if m.duration_seconds is not None]
            
            priority_metrics[str(priority)] = {
                "total_tasks": len(priority_metrics_list),
                "completed_tasks": len(completed),
                "average_execution_time": statistics.mean(execution_times) if execution_times else 0.0,
            }
        
        return priority_metrics
    
    def _collect_system_metrics(self) -> None:
        """Collect system-level metrics."""
        try:
            import psutil
            
            # CPU and memory usage
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            resource_sample = {
                "timestamp": datetime.utcnow(),
                "cpu_usage": cpu_usage,
                "memory_usage": memory.percent,
                "memory_available_mb": memory.available // (1024 * 1024),
                "active_tasks": len(self._active_tasks),
            }
            
            with self._lock:
                self._resource_samples.append(resource_sample)
                
        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
    
    def _update_throughput_metrics(self) -> None:
        """Update throughput tracking."""
        current_time = datetime.utcnow()
        completed_last_minute = len([
            m for m in self._completed_metrics
            if m.end_time and (current_time - m.end_time).total_seconds() <= 60
        ])
        
        with self._lock:
            self._throughput_samples.append((current_time, completed_last_minute))
    
    def _cleanup_old_metrics(self) -> None:
        """Clean up old metrics to prevent memory leaks."""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.metrics_window_hours * 2)
        
        with self._lock:
            # Clean up old task metrics
            old_task_ids = [
                task_id for task_id, metrics in self._task_metrics.items()
                if metrics.end_time and metrics.end_time < cutoff_time
            ]
            
            for task_id in old_task_ids:
                self._task_metrics.pop(task_id, None)
    
    def get_task_metrics(self, task_id: str) -> Optional[TaskMetrics]:
        """Get metrics for a specific task."""
        with self._lock:
            return self._task_metrics.get(task_id)
    
    def get_active_task_count(self) -> int:
        """Get the number of currently active tasks."""
        with self._lock:
            return len(self._active_tasks)
    
    def get_error_summary(self) -> Dict[str, int]:
        """Get a summary of error types and counts."""
        with self._lock:
            return dict(self._error_counts)
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        with self._lock:
            self._task_metrics.clear()
            self._completed_metrics.clear()
            self._active_tasks.clear()
            self._execution_times.clear()
            self._queue_times.clear()
            self._throughput_samples.clear()
            self._error_counts.clear()
            self._timeout_count = 0
            self._retry_count = 0
            self._resource_samples.clear()
            self._peak_concurrent = 0
            
            logger.info("Task monitoring metrics reset")
    
    def shutdown(self) -> None:
        """Shutdown the monitoring system."""
        logger.info("Shutting down TaskMonitor...")
        self._shutdown_event.set()
        
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)
        
        logger.info("TaskMonitor shutdown complete")


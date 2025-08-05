"""
Task performance metrics and analytics
"""

import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID


class TaskMetrics:
    """
    Real-time task performance monitoring and analytics
    
    Features:
    - Real-time execution metrics
    - Performance analytics
    - Resource usage tracking
    - SLA monitoring
    - Trend analysis
    """
    
    def __init__(self, 
                 metrics_retention_hours: int = 24,
                 sample_window_minutes: int = 5):
        
        self.metrics_retention_hours = metrics_retention_hours
        self.sample_window_minutes = sample_window_minutes
        
        # Task execution metrics
        self.task_start_times: Dict[UUID, float] = {}
        self.task_completion_times: Dict[UUID, float] = {}
        self.task_durations: deque = deque()  # (timestamp, duration)
        self.task_failures: deque = deque()  # (timestamp, task_id, reason)
        self.task_cancellations: deque = deque()  # (timestamp, task_id, reason)
        
        # Agent performance metrics
        self.agent_task_counts: Dict[str, int] = defaultdict(int)
        self.agent_success_counts: Dict[str, int] = defaultdict(int)
        self.agent_failure_counts: Dict[str, int] = defaultdict(int)
        self.agent_avg_durations: Dict[str, float] = defaultdict(float)
        
        # Resource usage metrics
        self.resource_samples: deque = deque()  # (timestamp, cpu, memory, etc.)
        
        # Workflow metrics
        self.workflow_durations: deque = deque()  # (timestamp, workflow_id, duration)
        self.workflow_step_counts: Dict[UUID, int] = {}
        
        # System metrics
        self.concurrent_tasks: int = 0
        self.peak_concurrent_tasks: int = 0
        self.total_tasks_processed: int = 0
        
        # SLA metrics
        self.sla_violations: deque = deque()  # (timestamp, task_id, expected_duration, actual_duration)
        
        # Throughput metrics
        self.throughput_samples: deque = deque()  # (timestamp, tasks_completed_in_window)
    
    def record_task_started(self, task_id: UUID, agent_id: str) -> None:
        """Record task start"""
        current_time = time.time()
        self.task_start_times[task_id] = current_time
        
        # Update concurrent task count
        self.concurrent_tasks += 1
        self.peak_concurrent_tasks = max(self.peak_concurrent_tasks, self.concurrent_tasks)
        
        # Update agent metrics
        self.agent_task_counts[agent_id] += 1
    
    def record_task_completed(self, task_id: UUID, duration_seconds: float) -> None:
        """Record task completion"""
        current_time = time.time()
        self.task_completion_times[task_id] = current_time
        
        # Record duration
        self.task_durations.append((current_time, duration_seconds))
        
        # Update concurrent task count
        self.concurrent_tasks = max(0, self.concurrent_tasks - 1)
        
        # Update total processed
        self.total_tasks_processed += 1
        
        # Update agent success metrics
        if task_id in self.task_start_times:
            del self.task_start_times[task_id]
        
        # Clean old data
        self._cleanup_old_data()
    
    def record_task_failed(self, task_id: UUID, reason: str) -> None:
        """Record task failure"""
        current_time = time.time()
        self.task_failures.append((current_time, str(task_id), reason))
        
        # Update concurrent task count
        self.concurrent_tasks = max(0, self.concurrent_tasks - 1)
        
        # Clean up start time
        if task_id in self.task_start_times:
            del self.task_start_times[task_id]
        
        # Clean old data
        self._cleanup_old_data()
    
    def record_task_cancelled(self, task_id: UUID) -> None:
        """Record task cancellation"""
        current_time = time.time()
        self.task_cancellations.append((current_time, str(task_id), "cancelled"))
        
        # Update concurrent task count
        self.concurrent_tasks = max(0, self.concurrent_tasks - 1)
        
        # Clean up start time
        if task_id in self.task_start_times:
            del self.task_start_times[task_id]
    
    def record_agent_success(self, agent_id: str, duration_seconds: float) -> None:
        """Record agent success"""
        self.agent_success_counts[agent_id] += 1
        
        # Update average duration
        current_avg = self.agent_avg_durations[agent_id]
        total_tasks = self.agent_success_counts[agent_id]
        self.agent_avg_durations[agent_id] = (
            (current_avg * (total_tasks - 1) + duration_seconds) / total_tasks
        )
    
    def record_agent_failure(self, agent_id: str) -> None:
        """Record agent failure"""
        self.agent_failure_counts[agent_id] += 1
    
    def record_resource_usage(self, cpu_percent: float, memory_mb: float, additional_metrics: Dict[str, float] = None) -> None:
        """Record resource usage sample"""
        current_time = time.time()
        
        sample = {
            "timestamp": current_time,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
        }
        
        if additional_metrics:
            sample.update(additional_metrics)
        
        self.resource_samples.append(sample)
        
        # Clean old samples
        cutoff_time = current_time - (self.metrics_retention_hours * 3600)
        while self.resource_samples and self.resource_samples[0]["timestamp"] < cutoff_time:
            self.resource_samples.popleft()
    
    def record_workflow_completed(self, workflow_id: UUID, duration_seconds: float, step_count: int) -> None:
        """Record workflow completion"""
        current_time = time.time()
        self.workflow_durations.append((current_time, str(workflow_id), duration_seconds))
        self.workflow_step_counts[workflow_id] = step_count
    
    def record_sla_violation(self, task_id: UUID, expected_duration: float, actual_duration: float) -> None:
        """Record SLA violation"""
        current_time = time.time()
        self.sla_violations.append((current_time, str(task_id), expected_duration, actual_duration))
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        current_time = time.time()
        
        # Calculate recent metrics (last hour)
        hour_ago = current_time - 3600
        
        # Recent task durations
        recent_durations = [
            duration for timestamp, duration in self.task_durations
            if timestamp > hour_ago
        ]
        
        # Recent failures
        recent_failures = [
            failure for timestamp, task_id, reason in self.task_failures
            if timestamp > hour_ago
        ]
        
        # Calculate throughput (tasks per minute)
        minute_ago = current_time - 60
        recent_completions = sum(
            1 for timestamp, _ in self.task_durations
            if timestamp > minute_ago
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "concurrent_tasks": self.concurrent_tasks,
            "peak_concurrent_tasks": self.peak_concurrent_tasks,
            "total_tasks_processed": self.total_tasks_processed,
            "tasks_per_minute": recent_completions,
            "average_duration_seconds": sum(recent_durations) / len(recent_durations) if recent_durations else 0,
            "failure_rate_percent": (len(recent_failures) / max(len(recent_durations) + len(recent_failures), 1)) * 100,
            "active_agents": len([agent for agent, count in self.agent_task_counts.items() if count > 0]),
            "sla_violations_last_hour": len([v for timestamp, _, _, _ in self.sla_violations if timestamp > hour_ago]),
        }
    
    def get_agent_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get per-agent metrics"""
        agent_metrics = {}
        
        for agent_id in set(list(self.agent_task_counts.keys()) + list(self.agent_success_counts.keys())):
            total_tasks = self.agent_task_counts[agent_id]
            successful_tasks = self.agent_success_counts[agent_id]
            failed_tasks = self.agent_failure_counts[agent_id]
            
            success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            agent_metrics[agent_id] = {
                "total_tasks": total_tasks,
                "successful_tasks": successful_tasks,
                "failed_tasks": failed_tasks,
                "success_rate_percent": round(success_rate, 2),
                "average_duration_seconds": round(self.agent_avg_durations[agent_id], 2),
            }
        
        return agent_metrics
    
    def get_resource_metrics(self) -> Dict[str, Any]:
        """Get resource usage metrics"""
        if not self.resource_samples:
            return {}
        
        # Calculate averages and peaks
        cpu_values = [sample["cpu_percent"] for sample in self.resource_samples]
        memory_values = [sample["memory_mb"] for sample in self.resource_samples]
        
        return {
            "average_cpu_percent": round(sum(cpu_values) / len(cpu_values), 2),
            "peak_cpu_percent": round(max(cpu_values), 2),
            "average_memory_mb": round(sum(memory_values) / len(memory_values), 2),
            "peak_memory_mb": round(max(memory_values), 2),
            "sample_count": len(self.resource_samples),
        }
    
    def get_workflow_metrics(self) -> Dict[str, Any]:
        """Get workflow metrics"""
        if not self.workflow_durations:
            return {}
        
        durations = [duration for _, _, duration in self.workflow_durations]
        step_counts = list(self.workflow_step_counts.values())
        
        return {
            "total_workflows": len(self.workflow_durations),
            "average_duration_seconds": round(sum(durations) / len(durations), 2),
            "average_step_count": round(sum(step_counts) / len(step_counts), 2) if step_counts else 0,
            "longest_workflow_seconds": max(durations),
            "shortest_workflow_seconds": min(durations),
        }
    
    def get_performance_trends(self, hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """Get performance trends over time"""
        current_time = time.time()
        cutoff_time = current_time - (hours * 3600)
        
        # Group data by hour
        hourly_data = defaultdict(lambda: {
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_duration": 0,
            "task_count": 0
        })
        
        # Process task completions
        for timestamp, duration in self.task_durations:
            if timestamp > cutoff_time:
                hour_key = int(timestamp // 3600) * 3600
                hourly_data[hour_key]["completed_tasks"] += 1
                hourly_data[hour_key]["total_duration"] += duration
                hourly_data[hour_key]["task_count"] += 1
        
        # Process failures
        for timestamp, _, _ in self.task_failures:
            if timestamp > cutoff_time:
                hour_key = int(timestamp // 3600) * 3600
                hourly_data[hour_key]["failed_tasks"] += 1
        
        # Convert to trend data
        trends = []
        for hour_timestamp in sorted(hourly_data.keys()):
            data = hourly_data[hour_timestamp]
            avg_duration = data["total_duration"] / data["task_count"] if data["task_count"] > 0 else 0
            
            trends.append({
                "timestamp": datetime.fromtimestamp(hour_timestamp).isoformat(),
                "completed_tasks": data["completed_tasks"],
                "failed_tasks": data["failed_tasks"],
                "average_duration_seconds": round(avg_duration, 2),
                "success_rate_percent": round(
                    (data["completed_tasks"] / max(data["completed_tasks"] + data["failed_tasks"], 1)) * 100, 2
                )
            })
        
        return {"hourly_trends": trends}
    
    def get_sla_metrics(self) -> Dict[str, Any]:
        """Get SLA compliance metrics"""
        current_time = time.time()
        hour_ago = current_time - 3600
        day_ago = current_time - 86400
        
        recent_violations = [
            v for timestamp, _, _, _ in self.sla_violations
            if timestamp > hour_ago
        ]
        
        daily_violations = [
            v for timestamp, _, _, _ in self.sla_violations
            if timestamp > day_ago
        ]
        
        return {
            "sla_violations_last_hour": len(recent_violations),
            "sla_violations_last_24h": len(daily_violations),
            "sla_compliance_rate_24h": round(
                max(0, 100 - (len(daily_violations) / max(self.total_tasks_processed, 1) * 100)), 2
            )
        }
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "current_metrics": self.get_current_metrics(),
            "agent_metrics": self.get_agent_metrics(),
            "resource_metrics": self.get_resource_metrics(),
            "workflow_metrics": self.get_workflow_metrics(),
            "sla_metrics": self.get_sla_metrics(),
            "performance_trends": self.get_performance_trends(),
        }
    
    def _cleanup_old_data(self) -> None:
        """Clean up old metric data"""
        current_time = time.time()
        cutoff_time = current_time - (self.metrics_retention_hours * 3600)
        
        # Clean task durations
        while self.task_durations and self.task_durations[0][0] < cutoff_time:
            self.task_durations.popleft()
        
        # Clean failures
        while self.task_failures and self.task_failures[0][0] < cutoff_time:
            self.task_failures.popleft()
        
        # Clean cancellations
        while self.task_cancellations and self.task_cancellations[0][0] < cutoff_time:
            self.task_cancellations.popleft()
        
        # Clean workflow durations
        while self.workflow_durations and self.workflow_durations[0][0] < cutoff_time:
            self.workflow_durations.popleft()
        
        # Clean SLA violations
        while self.sla_violations and self.sla_violations[0][0] < cutoff_time:
            self.sla_violations.popleft()
    
    def reset_metrics(self) -> None:
        """Reset all metrics (useful for testing)"""
        self.task_start_times.clear()
        self.task_completion_times.clear()
        self.task_durations.clear()
        self.task_failures.clear()
        self.task_cancellations.clear()
        self.agent_task_counts.clear()
        self.agent_success_counts.clear()
        self.agent_failure_counts.clear()
        self.agent_avg_durations.clear()
        self.resource_samples.clear()
        self.workflow_durations.clear()
        self.workflow_step_counts.clear()
        self.sla_violations.clear()
        self.throughput_samples.clear()
        
        self.concurrent_tasks = 0
        self.peak_concurrent_tasks = 0
        self.total_tasks_processed = 0


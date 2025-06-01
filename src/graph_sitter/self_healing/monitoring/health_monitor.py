"""
Health Monitor

Comprehensive system health monitoring and status reporting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from collections import defaultdict, deque

from ..models.events import HealthMetric, ErrorEvent, RecoveryAction
from ..models.enums import HealthStatus, RecoveryStatus
from ..error_detection.monitors import CPUMonitor, MemoryMonitor, NetworkMonitor, DiskMonitor
from .effectiveness_tracker import EffectivenessTracker


class HealthMonitor:
    """
    Comprehensive system health monitoring and reporting.
    
    Tracks system health metrics, recovery effectiveness, and provides
    real-time status updates with learning capabilities.
    """
    
    def __init__(self, update_interval: int = 30):
        """
        Initialize the health monitor.
        
        Args:
            update_interval: Health check interval in seconds
        """
        self.update_interval = update_interval
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self._stop_event = asyncio.Event()
        
        # Initialize monitors
        self.monitors = {
            "cpu": CPUMonitor(),
            "memory": MemoryMonitor(),
            "network": NetworkMonitor(),
            "disk": DiskMonitor(),
        }
        
        # Health tracking
        self.current_health: Dict[str, HealthMetric] = {}
        self.health_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # System status
        self.overall_status = HealthStatus.UNKNOWN
        self.last_health_check = None
        
        # Recovery tracking
        self.active_recoveries: Dict[str, RecoveryAction] = {}
        self.recovery_history: List[RecoveryAction] = []
        
        # Effectiveness tracking
        self.effectiveness_tracker = EffectivenessTracker()
        
        # Event handlers
        self.health_handlers: List[Callable[[Dict[str, HealthMetric]], None]] = []
        self.status_handlers: List[Callable[[HealthStatus], None]] = []
        
        # Performance metrics
        self.performance_metrics = {
            "uptime_start": datetime.utcnow(),
            "total_errors": 0,
            "resolved_errors": 0,
            "mean_time_to_detection": 0.0,
            "mean_time_to_recovery": 0.0,
        }
    
    def add_health_handler(self, handler: Callable[[Dict[str, HealthMetric]], None]) -> None:
        """Add a handler for health metric updates."""
        self.health_handlers.append(handler)
    
    def add_status_handler(self, handler: Callable[[HealthStatus], None]) -> None:
        """Add a handler for overall status changes."""
        self.status_handlers.append(handler)
    
    async def start(self) -> None:
        """Start the health monitoring service."""
        if self.is_running:
            self.logger.warning("Health monitor is already running")
            return
        
        self.logger.info("Starting health monitor")
        self.is_running = True
        self._stop_event.clear()
        
        # Start monitoring task
        asyncio.create_task(self._monitoring_loop())
    
    async def stop(self) -> None:
        """Stop the health monitoring service."""
        if not self.is_running:
            return
        
        self.logger.info("Stopping health monitor")
        self.is_running = False
        self._stop_event.set()
    
    async def check_system_health(self) -> Dict[str, HealthMetric]:
        """
        Perform comprehensive system health check.
        
        Returns:
            Dictionary of current health metrics
        """
        try:
            current_metrics = {}
            
            # Collect metrics from all monitors
            for name, monitor in self.monitors.items():
                try:
                    metric = await monitor.get_metric()
                    if metric:
                        current_metrics[name] = metric
                        
                        # Store in history
                        self.health_history[name].append(metric)
                        
                except Exception as e:
                    self.logger.error(f"Error getting metric from {name} monitor: {e}")
            
            # Update current health state
            self.current_health.update(current_metrics)
            self.last_health_check = datetime.utcnow()
            
            # Calculate overall status
            new_status = self._calculate_overall_status(current_metrics)
            if new_status != self.overall_status:
                old_status = self.overall_status
                self.overall_status = new_status
                self.logger.info(f"Overall health status changed: {old_status.value} -> {new_status.value}")
                
                # Notify status handlers
                for handler in self.status_handlers:
                    try:
                        handler(new_status)
                    except Exception as e:
                        self.logger.error(f"Error in status handler: {e}")
            
            # Notify health handlers
            for handler in self.health_handlers:
                try:
                    handler(current_metrics)
                except Exception as e:
                    self.logger.error(f"Error in health handler: {e}")
            
            return current_metrics
            
        except Exception as e:
            self.logger.error(f"Error checking system health: {e}")
            return {}
    
    async def track_recovery_effectiveness(self, recovery_id: str, 
                                         recovery_action: RecoveryAction) -> float:
        """
        Track and measure recovery effectiveness.
        
        Args:
            recovery_id: ID of the recovery action
            recovery_action: The recovery action to track
            
        Returns:
            Effectiveness score (0.0 to 1.0)
        """
        try:
            # Add to active recoveries if in progress
            if recovery_action.status == RecoveryStatus.IN_PROGRESS:
                self.active_recoveries[recovery_id] = recovery_action
                return 0.0  # No score yet for in-progress actions
            
            # Remove from active recoveries if completed
            self.active_recoveries.pop(recovery_id, None)
            
            # Add to history
            self.recovery_history.append(recovery_action)
            
            # Calculate effectiveness score
            effectiveness_score = await self.effectiveness_tracker.calculate_effectiveness(recovery_action)
            
            # Update performance metrics
            self._update_performance_metrics(recovery_action, effectiveness_score)
            
            self.logger.info(f"Recovery {recovery_id} effectiveness: {effectiveness_score:.2f}")
            return effectiveness_score
            
        except Exception as e:
            self.logger.error(f"Error tracking recovery effectiveness for {recovery_id}: {e}")
            return 0.0
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status report.
        
        Returns:
            System status information
        """
        try:
            uptime = datetime.utcnow() - self.performance_metrics["uptime_start"]
            
            # Calculate availability
            total_errors = self.performance_metrics["total_errors"]
            resolved_errors = self.performance_metrics["resolved_errors"]
            error_rate = (total_errors / max(uptime.total_seconds() / 3600, 1)) if uptime.total_seconds() > 0 else 0
            
            # Calculate success rates
            recovery_success_rate = 0.0
            if self.recovery_history:
                successful_recoveries = sum(1 for r in self.recovery_history if r.status == RecoveryStatus.COMPLETED)
                recovery_success_rate = (successful_recoveries / len(self.recovery_history)) * 100
            
            return {
                "overall_status": self.overall_status.value,
                "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
                "uptime_hours": round(uptime.total_seconds() / 3600, 2),
                "current_metrics": {name: metric.to_dict() for name, metric in self.current_health.items()},
                "performance": {
                    "total_errors": total_errors,
                    "resolved_errors": resolved_errors,
                    "error_rate_per_hour": round(error_rate, 2),
                    "recovery_success_rate": round(recovery_success_rate, 2),
                    "mean_time_to_detection": round(self.performance_metrics["mean_time_to_detection"], 2),
                    "mean_time_to_recovery": round(self.performance_metrics["mean_time_to_recovery"], 2),
                },
                "active_recoveries": len(self.active_recoveries),
                "total_recoveries": len(self.recovery_history),
                "monitoring_status": "active" if self.is_running else "stopped",
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                "overall_status": "error",
                "error": str(e),
            }
    
    def get_health_trends(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get health trends for a specific metric.
        
        Args:
            metric_name: Name of the metric
            hours: Number of hours of history to return
            
        Returns:
            List of metric data points
        """
        try:
            if metric_name not in self.health_history:
                return []
            
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            trends = []
            for metric in self.health_history[metric_name]:
                if metric.measured_at and metric.measured_at > cutoff_time:
                    trends.append({
                        "timestamp": metric.measured_at.isoformat(),
                        "value": metric.current_value,
                        "status": metric.status.value,
                    })
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error getting health trends for {metric_name}: {e}")
            return []
    
    def record_error_event(self, error_event: ErrorEvent) -> None:
        """Record an error event for tracking."""
        try:
            self.performance_metrics["total_errors"] += 1
            
            # Calculate time to detection if we have context
            if error_event.context and "detection_delay" in error_event.context:
                detection_time = error_event.context["detection_delay"]
                current_mttd = self.performance_metrics["mean_time_to_detection"]
                total_errors = self.performance_metrics["total_errors"]
                
                # Update running average
                self.performance_metrics["mean_time_to_detection"] = (
                    (current_mttd * (total_errors - 1) + detection_time) / total_errors
                )
            
        except Exception as e:
            self.logger.error(f"Error recording error event: {e}")
    
    def record_error_resolution(self, error_event: ErrorEvent, resolution_time: float) -> None:
        """Record error resolution for tracking."""
        try:
            self.performance_metrics["resolved_errors"] += 1
            
            # Update mean time to recovery
            current_mttr = self.performance_metrics["mean_time_to_recovery"]
            resolved_errors = self.performance_metrics["resolved_errors"]
            
            self.performance_metrics["mean_time_to_recovery"] = (
                (current_mttr * (resolved_errors - 1) + resolution_time) / resolved_errors
            )
            
        except Exception as e:
            self.logger.error(f"Error recording error resolution: {e}")
    
    def _calculate_overall_status(self, metrics: Dict[str, HealthMetric]) -> HealthStatus:
        """Calculate overall system health status."""
        if not metrics:
            return HealthStatus.UNKNOWN
        
        # Count status levels
        status_counts = defaultdict(int)
        for metric in metrics.values():
            status_counts[metric.status] += 1
        
        total_metrics = len(metrics)
        
        # Determine overall status based on worst status
        if status_counts[HealthStatus.CRITICAL] > 0:
            return HealthStatus.CRITICAL
        elif status_counts[HealthStatus.WARNING] > total_metrics * 0.3:  # More than 30% warnings
            return HealthStatus.WARNING
        elif status_counts[HealthStatus.HEALTHY] == total_metrics:
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.WARNING
    
    def _update_performance_metrics(self, recovery_action: RecoveryAction, 
                                  effectiveness_score: float) -> None:
        """Update performance metrics based on recovery action."""
        try:
            # Calculate recovery time if we have timestamps
            if recovery_action.started_at and recovery_action.completed_at:
                recovery_time = (recovery_action.completed_at - recovery_action.started_at).total_seconds()
                
                # Update mean time to recovery
                current_mttr = self.performance_metrics["mean_time_to_recovery"]
                total_recoveries = len(self.recovery_history)
                
                if total_recoveries > 0:
                    self.performance_metrics["mean_time_to_recovery"] = (
                        (current_mttr * (total_recoveries - 1) + recovery_time) / total_recoveries
                    )
                else:
                    self.performance_metrics["mean_time_to_recovery"] = recovery_time
            
        except Exception as e:
            self.logger.error(f"Error updating performance metrics: {e}")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_running and not self._stop_event.is_set():
            try:
                # Perform health check
                await self.check_system_health()
                
                # Wait for next check
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retrying


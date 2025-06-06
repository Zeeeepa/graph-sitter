"""
Monitoring Service - System health monitoring and alerting.
Provides comprehensive system monitoring and health checks.
"""

import asyncio
import logging
import psutil
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from ..consolidated_models import SystemHealthResponse, ServiceStatus, ServiceStatusResponse

logger = logging.getLogger(__name__)


class MonitoringService:
    """
    Service for system monitoring, health checks, and alerting.
    Monitors system resources, service health, and workflow status.
    """
    
    def __init__(self):
        """Initialize the Monitoring service."""
        self.health_history: List[Dict[str, Any]] = []
        self.alerts: List[Dict[str, Any]] = []
        self.monitoring_enabled = True
        self.alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "error_rate": 5.0,
            "response_time": 5000  # milliseconds
        }
        
        # Service health cache
        self.service_health_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 30  # seconds
        
        # Start background monitoring
        self._start_background_monitoring()
    
    async def get_system_health(self) -> SystemHealthResponse:
        """Get comprehensive system health status."""
        try:
            # Get system metrics
            system_metrics = await self._get_system_metrics()
            
            # Get service statuses
            services = await self._get_all_service_statuses()
            
            # Count active workflows and tasks
            workflow_stats = await self._get_workflow_statistics()
            
            # Calculate overall status
            overall_status = self._calculate_overall_status(system_metrics, services)
            
            # Get recent error count
            error_count = await self._get_recent_error_count()
            
            health_response = SystemHealthResponse(
                status=overall_status,
                timestamp=datetime.now().isoformat(),
                services=services,
                system_metrics=system_metrics,
                active_workflows=workflow_stats["active_workflows"],
                active_tasks=workflow_stats["active_tasks"],
                error_count=error_count
            )
            
            # Store in history
            self._store_health_history(health_response.dict())
            
            return health_response
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return SystemHealthResponse(
                status="error",
                timestamp=datetime.now().isoformat(),
                services=ServiceStatusResponse(
                    github=ServiceStatus.UNKNOWN,
                    linear=ServiceStatus.UNKNOWN,
                    slack=ServiceStatus.UNKNOWN,
                    codegen=ServiceStatus.UNKNOWN,
                    database=ServiceStatus.UNKNOWN
                ),
                system_metrics={"error": str(e)},
                active_workflows=0,
                active_tasks=0,
                error_count=1
            )
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics."""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Process metrics
            process_count = len(psutil.pids())
            
            # Load average (Unix-like systems)
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                load_avg = [0, 0, 0]  # Windows doesn't have load average
            
            metrics = {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "frequency_mhz": cpu_freq.current if cpu_freq else 0
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "usage_percent": memory.percent
                },
                "swap": {
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "usage_percent": swap.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 2)
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "system": {
                    "process_count": process_count,
                    "load_average": {
                        "1min": round(load_avg[0], 2),
                        "5min": round(load_avg[1], 2),
                        "15min": round(load_avg[2], 2)
                    },
                    "uptime_seconds": time.time() - psutil.boot_time()
                }
            }
            
            # Check for alerts
            await self._check_system_alerts(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}
    
    async def _get_all_service_statuses(self) -> ServiceStatusResponse:
        """Get status of all services with caching."""
        try:
            now = datetime.now()
            
            # Check cache first
            if self._is_cache_valid("services", now):
                cached = self.service_health_cache["services"]
                return ServiceStatusResponse(**cached["data"])
            
            # Get fresh service statuses
            services = ServiceStatusResponse(
                github=await self._check_service_health("github"),
                linear=await self._check_service_health("linear"),
                slack=await self._check_service_health("slack"),
                codegen=await self._check_service_health("codegen"),
                database=await self._check_service_health("database"),
                strands_workflow=await self._check_service_health("strands_workflow"),
                strands_mcp=await self._check_service_health("strands_mcp"),
                controlflow=await self._check_service_health("controlflow"),
                prefect=await self._check_service_health("prefect")
            )
            
            # Cache the result
            self.service_health_cache["services"] = {
                "timestamp": now,
                "data": services.dict()
            }
            
            return services
            
        except Exception as e:
            logger.error(f"Failed to get service statuses: {e}")
            return ServiceStatusResponse(
                github=ServiceStatus.ERROR,
                linear=ServiceStatus.ERROR,
                slack=ServiceStatus.ERROR,
                codegen=ServiceStatus.ERROR,
                database=ServiceStatus.ERROR
            )
    
    async def _check_service_health(self, service_name: str) -> ServiceStatus:
        """Check health of a specific service."""
        try:
            # This would integrate with actual service health checks
            # For now, simulate health checks
            
            if service_name == "github":
                # Check GitHub API connectivity
                return await self._check_github_health()
            elif service_name == "linear":
                # Check Linear API connectivity
                return await self._check_linear_health()
            elif service_name == "slack":
                # Check Slack API connectivity
                return await self._check_slack_health()
            elif service_name == "codegen":
                # Check Codegen SDK connectivity
                return await self._check_codegen_health()
            elif service_name == "database":
                # Check database connectivity
                return await self._check_database_health()
            elif service_name in ["strands_workflow", "strands_mcp", "controlflow", "prefect"]:
                # Check orchestration services
                return await self._check_orchestration_health(service_name)
            else:
                return ServiceStatus.UNKNOWN
                
        except Exception as e:
            logger.error(f"Health check failed for {service_name}: {e}")
            return ServiceStatus.ERROR
    
    async def _check_github_health(self) -> ServiceStatus:
        """Check GitHub service health."""
        try:
            # This would make an actual API call to GitHub
            # For now, simulate based on environment variables
            import os
            if os.getenv("GITHUB_ACCESS_TOKEN"):
                return ServiceStatus.CONNECTED
            else:
                return ServiceStatus.DISCONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_linear_health(self) -> ServiceStatus:
        """Check Linear service health."""
        try:
            import os
            if os.getenv("LINEAR_ACCESS_TOKEN"):
                return ServiceStatus.CONNECTED
            else:
                return ServiceStatus.DISCONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_slack_health(self) -> ServiceStatus:
        """Check Slack service health."""
        try:
            import os
            if os.getenv("SLACK_BOT_TOKEN"):
                return ServiceStatus.CONNECTED
            else:
                return ServiceStatus.DISCONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_codegen_health(self) -> ServiceStatus:
        """Check Codegen SDK health."""
        try:
            import os
            if os.getenv("CODEGEN_ORG_ID") and os.getenv("CODEGEN_TOKEN"):
                return ServiceStatus.CONNECTED
            else:
                return ServiceStatus.DISCONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_database_health(self) -> ServiceStatus:
        """Check database health."""
        try:
            # This would check actual database connectivity
            # For now, assume connected
            return ServiceStatus.CONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def _check_orchestration_health(self, service_name: str) -> ServiceStatus:
        """Check orchestration service health."""
        try:
            # This would check actual orchestration service health
            # For now, simulate based on service availability
            if service_name == "strands_workflow":
                try:
                    # Check if strands_tools is available
                    import strands_tools
                    return ServiceStatus.CONNECTED
                except ImportError:
                    return ServiceStatus.DISCONNECTED
            elif service_name == "strands_mcp":
                try:
                    # Check if strands MCP client is available
                    from strands.tools.mcp.mcp_client import MCPClient
                    return ServiceStatus.CONNECTED
                except ImportError:
                    return ServiceStatus.DISCONNECTED
            elif service_name == "controlflow":
                try:
                    import controlflow
                    return ServiceStatus.CONNECTED
                except ImportError:
                    return ServiceStatus.DISCONNECTED
            elif service_name == "prefect":
                try:
                    import prefect
                    return ServiceStatus.CONNECTED
                except ImportError:
                    return ServiceStatus.DISCONNECTED
            else:
                return ServiceStatus.UNKNOWN
        except Exception:
            return ServiceStatus.ERROR
    
    async def _get_workflow_statistics(self) -> Dict[str, int]:
        """Get workflow and task statistics."""
        try:
            # This would query actual workflow and task counts
            # For now, return mock statistics
            return {
                "active_workflows": 3,
                "active_tasks": 12,
                "completed_workflows": 45,
                "failed_workflows": 2,
                "pending_tasks": 8,
                "running_tasks": 4
            }
        except Exception as e:
            logger.error(f"Failed to get workflow statistics: {e}")
            return {
                "active_workflows": 0,
                "active_tasks": 0,
                "completed_workflows": 0,
                "failed_workflows": 0,
                "pending_tasks": 0,
                "running_tasks": 0
            }
    
    async def _get_recent_error_count(self) -> int:
        """Get count of recent errors."""
        try:
            # This would query actual error logs
            # For now, return mock count
            return len([alert for alert in self.alerts if alert.get("level") == "error"])
        except Exception:
            return 0
    
    def _calculate_overall_status(self, system_metrics: Dict[str, Any], services: ServiceStatusResponse) -> str:
        """Calculate overall system status."""
        try:
            # Check for critical issues
            if "error" in system_metrics:
                return "error"
            
            # Check system resource usage
            cpu_usage = system_metrics.get("cpu", {}).get("usage_percent", 0)
            memory_usage = system_metrics.get("memory", {}).get("usage_percent", 0)
            disk_usage = system_metrics.get("disk", {}).get("usage_percent", 0)
            
            if cpu_usage > 90 or memory_usage > 95 or disk_usage > 95:
                return "critical"
            
            # Check service statuses
            critical_services = [services.codegen, services.database]
            if any(status == ServiceStatus.ERROR for status in critical_services):
                return "degraded"
            
            # Check for warnings
            if cpu_usage > 80 or memory_usage > 85 or disk_usage > 90:
                return "warning"
            
            if any(status == ServiceStatus.DISCONNECTED for status in [services.github, services.linear, services.slack]):
                return "warning"
            
            return "healthy"
            
        except Exception as e:
            logger.error(f"Failed to calculate overall status: {e}")
            return "unknown"
    
    async def _check_system_alerts(self, metrics: Dict[str, Any]):
        """Check system metrics against alert thresholds."""
        try:
            now = datetime.now()
            
            # CPU usage alert
            cpu_usage = metrics.get("cpu", {}).get("usage_percent", 0)
            if cpu_usage > self.alert_thresholds["cpu_usage"]:
                await self._create_alert(
                    "high_cpu_usage",
                    f"High CPU usage: {cpu_usage:.1f}%",
                    "warning",
                    {"cpu_usage": cpu_usage}
                )
            
            # Memory usage alert
            memory_usage = metrics.get("memory", {}).get("usage_percent", 0)
            if memory_usage > self.alert_thresholds["memory_usage"]:
                await self._create_alert(
                    "high_memory_usage",
                    f"High memory usage: {memory_usage:.1f}%",
                    "warning",
                    {"memory_usage": memory_usage}
                )
            
            # Disk usage alert
            disk_usage = metrics.get("disk", {}).get("usage_percent", 0)
            if disk_usage > self.alert_thresholds["disk_usage"]:
                await self._create_alert(
                    "high_disk_usage",
                    f"High disk usage: {disk_usage:.1f}%",
                    "critical",
                    {"disk_usage": disk_usage}
                )
            
        except Exception as e:
            logger.error(f"Failed to check system alerts: {e}")
    
    async def _create_alert(self, alert_type: str, message: str, level: str, data: Dict[str, Any]):
        """Create a new alert."""
        alert = {
            "id": f"{alert_type}_{int(time.time())}",
            "type": alert_type,
            "message": message,
            "level": level,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "acknowledged": False
        }
        
        # Check if similar alert already exists (avoid spam)
        recent_alerts = [
            a for a in self.alerts 
            if a["type"] == alert_type and 
            datetime.fromisoformat(a["timestamp"]) > datetime.now() - timedelta(minutes=5)
        ]
        
        if not recent_alerts:
            self.alerts.append(alert)
            logger.warning(f"Alert created: {message}")
            
            # Keep only last 100 alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
    
    def _is_cache_valid(self, cache_key: str, now: datetime) -> bool:
        """Check if cache entry is still valid."""
        if cache_key not in self.service_health_cache:
            return False
        
        cache_entry = self.service_health_cache[cache_key]
        cache_time = cache_entry["timestamp"]
        
        return (now - cache_time).total_seconds() < self.cache_ttl
    
    def _store_health_history(self, health_data: Dict[str, Any]):
        """Store health data in history."""
        self.health_history.append(health_data)
        
        # Keep only last 100 entries
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]
    
    def _start_background_monitoring(self):
        """Start background monitoring tasks."""
        if self.monitoring_enabled:
            asyncio.create_task(self._background_health_monitor())
    
    async def _background_health_monitor(self):
        """Background task for continuous health monitoring."""
        while self.monitoring_enabled:
            try:
                # Get system health (this will trigger alerts if needed)
                await self.get_system_health()
                
                # Wait before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Background health monitor error: {e}")
                await asyncio.sleep(120)  # Wait longer on error
    
    async def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent alerts."""
        return self.alerts[-limit:] if limit else self.alerts
    
    async def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert["id"] == alert_id:
                alert["acknowledged"] = True
                alert["acknowledged_at"] = datetime.now().isoformat()
                logger.info(f"Alert acknowledged: {alert_id}")
                return True
        return False
    
    async def get_health_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get health history for the specified number of hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            entry for entry in self.health_history
            if datetime.fromisoformat(entry["timestamp"]) > cutoff_time
        ]
    
    async def update_alert_thresholds(self, thresholds: Dict[str, float]):
        """Update alert thresholds."""
        self.alert_thresholds.update(thresholds)
        logger.info(f"Updated alert thresholds: {thresholds}")
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.monitoring_enabled = False
        logger.info("Monitoring stopped")


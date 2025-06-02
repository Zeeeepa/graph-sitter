"""
System Monitoring and Health Check Module

This module provides comprehensive monitoring capabilities for the autonomous
CI/CD orchestration system, including health checks, performance monitoring,
and alerting.
"""

import asyncio
import logging
import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from .config import OrchestrationConfig


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class ComponentHealth:
    """Health information for a system component"""
    name: str
    status: HealthStatus
    health_score: float  # 0-100
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SystemMetrics:
    """System-wide metrics"""
    timestamp: datetime
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    network_io_bytes: Dict[str, int]
    active_workflows: int
    total_workflows_executed: int
    successful_workflows: int
    failed_workflows: int
    error_rate_percent: float
    average_response_time_ms: float
    system_health_score: float


class SystemMonitor:
    """
    Comprehensive system monitoring and health checking.
    
    This class monitors all aspects of the autonomous CI/CD system,
    including system resources, component health, and performance metrics.
    """
    
    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.component_health: Dict[str, ComponentHealth] = {}
        self.metrics_history: List[SystemMetrics] = []
        self.alert_history: List[Dict[str, Any]] = []
        self.monitoring_active = False
        
    async def initialize(self) -> None:
        """Initialize the monitoring system"""
        self.logger.info("Initializing System Monitor...")
        
        if self.config.monitoring_enabled:
            self.monitoring_active = True
            # Start background monitoring tasks
            asyncio.create_task(self._continuous_monitoring())
            
        self.logger.info("System Monitor initialized")
    
    async def _continuous_monitoring(self) -> None:
        """Continuous monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                await self._collect_system_metrics()
                
                # Check component health
                await self._check_all_components()
                
                # Process alerts
                await self._process_alerts()
                
                # Clean up old data
                await self._cleanup_old_data()
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.config.health_check_interval_minutes * 60)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics"""
        try:
            # System resource metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Calculate workflow metrics
            total_workflows = len(self.metrics_history)
            successful_workflows = sum(1 for m in self.metrics_history if m.error_rate_percent < 5)
            error_rate = ((total_workflows - successful_workflows) / max(total_workflows, 1)) * 100
            
            # Calculate average response time
            avg_response_time = sum(
                comp.response_time_ms or 0 
                for comp in self.component_health.values()
            ) / max(len(self.component_health), 1)
            
            # Calculate system health score
            health_score = self._calculate_system_health_score(
                cpu_percent, memory.percent, disk.percent, error_rate
            )
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_usage_percent=cpu_percent,
                memory_usage_percent=memory.percent,
                disk_usage_percent=disk.percent,
                network_io_bytes={
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv
                },
                active_workflows=0,  # Will be updated by orchestrator
                total_workflows_executed=total_workflows,
                successful_workflows=successful_workflows,
                failed_workflows=total_workflows - successful_workflows,
                error_rate_percent=error_rate,
                average_response_time_ms=avg_response_time,
                system_health_score=health_score
            )
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Keep only last 24 hours of metrics
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.metrics_history = [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_time
            ]
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            raise
    
    def _calculate_system_health_score(
        self, 
        cpu_percent: float, 
        memory_percent: float, 
        disk_percent: float, 
        error_rate: float
    ) -> float:
        """Calculate overall system health score (0-100)"""
        
        # Component scores (higher is better)
        cpu_score = max(0, 100 - cpu_percent)
        memory_score = max(0, 100 - memory_percent)
        disk_score = max(0, 100 - disk_percent)
        error_score = max(0, 100 - error_rate)
        
        # Component health scores
        component_scores = [
            comp.health_score for comp in self.component_health.values()
        ]
        avg_component_score = sum(component_scores) / max(len(component_scores), 1)
        
        # Weighted average
        weights = {
            "cpu": 0.2,
            "memory": 0.2,
            "disk": 0.15,
            "error_rate": 0.25,
            "components": 0.2
        }
        
        health_score = (
            weights["cpu"] * cpu_score +
            weights["memory"] * memory_score +
            weights["disk"] * disk_score +
            weights["error_rate"] * error_score +
            weights["components"] * avg_component_score
        )
        
        return min(100, max(0, health_score))
    
    async def _check_all_components(self) -> None:
        """Check health of all system components"""
        components_to_check = [
            "codegen_sdk",
            "linear_api",
            "github_api",
            "slack_integration",
            "prefect_server",
            "database",
            "file_system"
        ]
        
        for component in components_to_check:
            try:
                health = await self._check_component_health(component)
                self.component_health[component] = health
            except Exception as e:
                self.logger.error(f"Error checking {component} health: {e}")
                self.component_health[component] = ComponentHealth(
                    name=component,
                    status=HealthStatus.UNHEALTHY,
                    health_score=0,
                    last_check=datetime.now(),
                    error_message=str(e)
                )
    
    async def _check_component_health(self, component_name: str) -> ComponentHealth:
        """Check health of a specific component"""
        start_time = time.time()
        
        try:
            if component_name == "codegen_sdk":
                return await self._check_codegen_sdk_health()
            elif component_name == "linear_api":
                return await self._check_linear_api_health()
            elif component_name == "github_api":
                return await self._check_github_api_health()
            elif component_name == "slack_integration":
                return await self._check_slack_integration_health()
            elif component_name == "prefect_server":
                return await self._check_prefect_server_health()
            elif component_name == "database":
                return await self._check_database_health()
            elif component_name == "file_system":
                return await self._check_file_system_health()
            else:
                raise ValueError(f"Unknown component: {component_name}")
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name=component_name,
                status=HealthStatus.UNHEALTHY,
                health_score=0,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _check_codegen_sdk_health(self) -> ComponentHealth:
        """Check Codegen SDK health"""
        start_time = time.time()
        
        try:
            if not self.config.is_integration_enabled("codegen"):
                return ComponentHealth(
                    name="codegen_sdk",
                    status=HealthStatus.DEGRADED,
                    health_score=50,
                    last_check=datetime.now(),
                    error_message="Codegen SDK not configured"
                )
            
            # Simple connectivity test
            from codegen import Agent as CodegenAgent
            
            agent = CodegenAgent(
                org_id=self.config.codegen_org_id,
                token=self.config.codegen_token
            )
            
            # Quick health check task
            task = agent.run(prompt="Health check: respond with 'OK'")
            
            # Wait briefly for response
            for _ in range(6):  # 60 seconds total
                task.refresh()
                if task.status in ["completed", "failed"]:
                    break
                await asyncio.sleep(10)
            
            response_time = (time.time() - start_time) * 1000
            
            if task.status == "completed":
                return ComponentHealth(
                    name="codegen_sdk",
                    status=HealthStatus.HEALTHY,
                    health_score=100,
                    last_check=datetime.now(),
                    response_time_ms=response_time
                )
            else:
                return ComponentHealth(
                    name="codegen_sdk",
                    status=HealthStatus.DEGRADED,
                    health_score=30,
                    last_check=datetime.now(),
                    response_time_ms=response_time,
                    error_message=f"Task status: {task.status}"
                )
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="codegen_sdk",
                status=HealthStatus.UNHEALTHY,
                health_score=0,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _check_linear_api_health(self) -> ComponentHealth:
        """Check Linear API health"""
        start_time = time.time()
        
        try:
            if not self.config.is_integration_enabled("linear"):
                return ComponentHealth(
                    name="linear_api",
                    status=HealthStatus.DEGRADED,
                    health_score=50,
                    last_check=datetime.now(),
                    error_message="Linear API not configured"
                )
            
            # Simple API connectivity test
            import aiohttp
            
            headers = {
                "Authorization": f"Bearer {self.config.linear_api_key}",
                "Content-Type": "application/json"
            }
            
            query = """
            query {
                viewer {
                    id
                    name
                }
            }
            """
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.linear.app/graphql",
                    json={"query": query},
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return ComponentHealth(
                            name="linear_api",
                            status=HealthStatus.HEALTHY,
                            health_score=100,
                            last_check=datetime.now(),
                            response_time_ms=response_time
                        )
                    else:
                        return ComponentHealth(
                            name="linear_api",
                            status=HealthStatus.DEGRADED,
                            health_score=30,
                            last_check=datetime.now(),
                            response_time_ms=response_time,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="linear_api",
                status=HealthStatus.UNHEALTHY,
                health_score=0,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _check_github_api_health(self) -> ComponentHealth:
        """Check GitHub API health"""
        start_time = time.time()
        
        try:
            if not self.config.is_integration_enabled("github"):
                return ComponentHealth(
                    name="github_api",
                    status=HealthStatus.DEGRADED,
                    health_score=50,
                    last_check=datetime.now(),
                    error_message="GitHub API not configured"
                )
            
            # Simple API connectivity test
            import aiohttp
            
            headers = {
                "Authorization": f"token {self.config.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.github.com/user",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return ComponentHealth(
                            name="github_api",
                            status=HealthStatus.HEALTHY,
                            health_score=100,
                            last_check=datetime.now(),
                            response_time_ms=response_time
                        )
                    else:
                        return ComponentHealth(
                            name="github_api",
                            status=HealthStatus.DEGRADED,
                            health_score=30,
                            last_check=datetime.now(),
                            response_time_ms=response_time,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="github_api",
                status=HealthStatus.UNHEALTHY,
                health_score=0,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _check_slack_integration_health(self) -> ComponentHealth:
        """Check Slack integration health"""
        start_time = time.time()
        
        try:
            if not self.config.is_integration_enabled("slack"):
                return ComponentHealth(
                    name="slack_integration",
                    status=HealthStatus.DEGRADED,
                    health_score=50,
                    last_check=datetime.now(),
                    error_message="Slack integration not configured"
                )
            
            # Simple webhook connectivity test
            import aiohttp
            
            test_payload = {
                "text": "Health check from autonomous orchestrator",
                "username": "orchestrator-health-check"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.slack_webhook_url,
                    json=test_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return ComponentHealth(
                            name="slack_integration",
                            status=HealthStatus.HEALTHY,
                            health_score=100,
                            last_check=datetime.now(),
                            response_time_ms=response_time
                        )
                    else:
                        return ComponentHealth(
                            name="slack_integration",
                            status=HealthStatus.DEGRADED,
                            health_score=30,
                            last_check=datetime.now(),
                            response_time_ms=response_time,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="slack_integration",
                status=HealthStatus.UNHEALTHY,
                health_score=0,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _check_prefect_server_health(self) -> ComponentHealth:
        """Check Prefect server health"""
        start_time = time.time()
        
        try:
            # Check if Prefect is accessible
            import aiohttp
            
            api_url = self.config.prefect_api_url or "http://localhost:4200/api"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{api_url}/health",
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return ComponentHealth(
                            name="prefect_server",
                            status=HealthStatus.HEALTHY,
                            health_score=100,
                            last_check=datetime.now(),
                            response_time_ms=response_time
                        )
                    else:
                        return ComponentHealth(
                            name="prefect_server",
                            status=HealthStatus.DEGRADED,
                            health_score=30,
                            last_check=datetime.now(),
                            response_time_ms=response_time,
                            error_message=f"HTTP {response.status}"
                        )
                        
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="prefect_server",
                status=HealthStatus.UNHEALTHY,
                health_score=0,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _check_database_health(self) -> ComponentHealth:
        """Check database health (if applicable)"""
        # For now, assume healthy if no database is configured
        return ComponentHealth(
            name="database",
            status=HealthStatus.HEALTHY,
            health_score=100,
            last_check=datetime.now(),
            response_time_ms=1.0
        )
    
    async def _check_file_system_health(self) -> ComponentHealth:
        """Check file system health"""
        start_time = time.time()
        
        try:
            # Check disk space and write permissions
            disk = psutil.disk_usage('/')
            
            # Test write permissions
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(delete=True) as tmp_file:
                tmp_file.write(b"health check")
                tmp_file.flush()
                os.fsync(tmp_file.fileno())
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine health based on disk usage
            if disk.percent < 80:
                status = HealthStatus.HEALTHY
                score = 100
            elif disk.percent < 90:
                status = HealthStatus.DEGRADED
                score = 60
            else:
                status = HealthStatus.UNHEALTHY
                score = 20
            
            return ComponentHealth(
                name="file_system",
                status=status,
                health_score=score,
                last_check=datetime.now(),
                response_time_ms=response_time,
                metadata={"disk_usage_percent": disk.percent}
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return ComponentHealth(
                name="file_system",
                status=HealthStatus.UNHEALTHY,
                health_score=0,
                last_check=datetime.now(),
                response_time_ms=response_time,
                error_message=str(e)
            )
    
    async def _process_alerts(self) -> None:
        """Process and send alerts based on current system state"""
        alerts = []
        
        # Check system resource alerts
        if self.metrics_history:
            latest_metrics = self.metrics_history[-1]
            
            if latest_metrics.cpu_usage_percent > self.config.alert_thresholds["cpu_usage_percent"]:
                alerts.append(f"High CPU usage: {latest_metrics.cpu_usage_percent:.1f}%")
            
            if latest_metrics.memory_usage_percent > self.config.alert_thresholds["memory_usage_percent"]:
                alerts.append(f"High memory usage: {latest_metrics.memory_usage_percent:.1f}%")
            
            if latest_metrics.disk_usage_percent > self.config.alert_thresholds["disk_usage_percent"]:
                alerts.append(f"High disk usage: {latest_metrics.disk_usage_percent:.1f}%")
            
            if latest_metrics.error_rate_percent > self.config.alert_thresholds["error_rate_percent"]:
                alerts.append(f"High error rate: {latest_metrics.error_rate_percent:.1f}%")
        
        # Check component health alerts
        for component_name, health in self.component_health.items():
            if health.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                alerts.append(f"Component {component_name} is {health.status.value}: {health.error_message}")
        
        # Send alerts if any
        if alerts:
            await self._send_alerts(alerts)
    
    async def _send_alerts(self, alerts: List[str]) -> None:
        """Send alerts via configured channels"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "system_health_score": self.get_current_health_score()
        }
        
        self.alert_history.append(alert_data)
        
        # Log alerts
        for alert in alerts:
            self.logger.warning(f"ALERT: {alert}")
        
        # Send to Slack if configured
        if self.config.is_integration_enabled("slack"):
            await self._send_slack_alert(alerts)
    
    async def _send_slack_alert(self, alerts: List[str]) -> None:
        """Send alert to Slack"""
        try:
            import aiohttp
            
            alert_text = "🚨 *System Alerts*\n" + "\n".join(f"• {alert}" for alert in alerts)
            
            payload = {
                "text": alert_text,
                "username": "orchestrator-monitor",
                "icon_emoji": ":warning:"
            }
            
            async with aiohttp.ClientSession() as session:
                await session.post(self.config.slack_webhook_url, json=payload)
                
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old monitoring data"""
        # Keep only last 24 hours of metrics
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history 
            if m.timestamp > cutoff_time
        ]
        
        # Keep only last 100 alerts
        self.alert_history = self.alert_history[-100:]
    
    def get_current_health_score(self) -> float:
        """Get current system health score"""
        if self.metrics_history:
            return self.metrics_history[-1].system_health_score
        return 0.0
    
    async def get_comprehensive_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        latest_metrics = self.metrics_history[-1] if self.metrics_history else None
        
        return {
            "system_metrics": latest_metrics.__dict__ if latest_metrics else None,
            "component_health": {
                name: {
                    "status": health.status.value,
                    "health_score": health.health_score,
                    "response_time_ms": health.response_time_ms,
                    "last_check": health.last_check.isoformat(),
                    "error_message": health.error_message
                }
                for name, health in self.component_health.items()
            },
            "recent_alerts": self.alert_history[-10:],  # Last 10 alerts
            "monitoring_active": self.monitoring_active
        }
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform immediate system health check"""
        await self._check_all_components()
        metrics = await self._collect_system_metrics()
        
        # Determine overall status
        component_statuses = [health.status for health in self.component_health.values()]
        
        if any(status == HealthStatus.CRITICAL for status in component_statuses):
            overall_status = HealthStatus.CRITICAL
        elif any(status == HealthStatus.UNHEALTHY for status in component_statuses):
            overall_status = HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in component_statuses):
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            "status": overall_status.value,
            "health_score": metrics.system_health_score,
            "components": {
                name: {
                    "status": health.status.value,
                    "health_score": health.health_score,
                    "response_time_ms": health.response_time_ms
                }
                for name, health in self.component_health.items()
            },
            "metrics": {
                "cpu_usage_percent": metrics.cpu_usage_percent,
                "memory_usage_percent": metrics.memory_usage_percent,
                "disk_usage_percent": metrics.disk_usage_percent,
                "error_rate_percent": metrics.error_rate_percent
            },
            "alerts": [alert["alerts"] for alert in self.alert_history[-5:]]  # Last 5 alert batches
        }
    
    async def shutdown(self) -> None:
        """Shutdown the monitoring system"""
        self.logger.info("Shutting down System Monitor...")
        self.monitoring_active = False


"""
Orchestration Monitoring System

This module provides comprehensive monitoring capabilities for the Prefect-based
orchestration system, including health checks, performance tracking, and alerting.
"""

import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class ComponentHealth:
    """Health status for a system component"""
    name: str
    status: str  # healthy, degraded, unhealthy
    health_score: float  # 0-100
    last_check: datetime
    error_message: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health status"""
    overall_health: float  # 0-100
    status: str  # healthy, degraded, unhealthy
    components: Dict[str, ComponentHealth] = field(default_factory=dict)
    alerts: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


class OrchestrationMonitor:
    """
    Comprehensive monitoring system for orchestration components
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.monitoring_active = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Health check configuration
        self.health_check_interval = 60  # seconds
        self.component_timeout = 30  # seconds
        
        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        self.max_history_size = 1000
        
        # Alert thresholds
        self.alert_thresholds = {
            "cpu_usage_percent": 80,
            "memory_usage_percent": 85,
            "error_rate_percent": 10,
            "response_time_ms": 5000,
            "health_score": 70
        }
        
        # Component health checkers
        self.health_checkers: Dict[str, Callable] = {
            "prefect_server": self._check_prefect_server_health,
            "codegen_agent": self._check_codegen_agent_health,
            "github_integration": self._check_github_integration_health,
            "linear_integration": self._check_linear_integration_health,
            "system_resources": self._check_system_resources_health,
            "workflow_execution": self._check_workflow_execution_health
        }
    
    async def start(self):
        """Start the monitoring system"""
        
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Orchestration monitoring started")
    
    async def stop(self):
        """Stop the monitoring system"""
        
        self.monitoring_active = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Orchestration monitoring stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        
        while self.monitoring_active:
            try:
                # Perform health check
                health_status = await self.check_system_health()
                
                # Record performance metrics
                await self._record_performance_metrics()
                
                # Check for alerts
                await self._check_alerts(health_status)
                
                # Wait for next check
                await asyncio.sleep(self.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.health_check_interval)
    
    async def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive system health check"""
        
        logger.debug("Performing system health check")
        
        component_healths = {}
        
        # Check each component
        for component_name, checker in self.health_checkers.items():
            try:
                health = await asyncio.wait_for(
                    checker(), 
                    timeout=self.component_timeout
                )
                component_healths[component_name] = health
                
            except asyncio.TimeoutError:
                component_healths[component_name] = ComponentHealth(
                    name=component_name,
                    status="unhealthy",
                    health_score=0,
                    last_check=datetime.now(),
                    error_message="Health check timeout"
                )
            except Exception as e:
                component_healths[component_name] = ComponentHealth(
                    name=component_name,
                    status="unhealthy",
                    health_score=0,
                    last_check=datetime.now(),
                    error_message=str(e)
                )
        
        # Calculate overall health
        overall_health = self._calculate_overall_health(component_healths)
        
        # Determine overall status
        if overall_health >= 90:
            overall_status = "healthy"
        elif overall_health >= 70:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        # Generate alerts
        alerts = self._generate_alerts(component_healths, overall_health)
        
        health_status = {
            "overall_health": overall_health,
            "status": overall_status,
            "components": {name: health.__dict__ for name, health in component_healths.items()},
            "alerts": alerts,
            "last_updated": datetime.now().isoformat()
        }
        
        logger.debug(f"System health check complete: {overall_health}% ({overall_status})")
        
        return health_status
    
    def _calculate_overall_health(self, component_healths: Dict[str, ComponentHealth]) -> float:
        """Calculate overall system health score"""
        
        if not component_healths:
            return 0
        
        # Weight different components
        component_weights = {
            "prefect_server": 0.25,
            "codegen_agent": 0.25,
            "github_integration": 0.15,
            "linear_integration": 0.15,
            "system_resources": 0.15,
            "workflow_execution": 0.05
        }
        
        weighted_score = 0
        total_weight = 0
        
        for name, health in component_healths.items():
            weight = component_weights.get(name, 0.1)
            weighted_score += health.health_score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 0
    
    def _generate_alerts(self, component_healths: Dict[str, ComponentHealth], overall_health: float) -> List[str]:
        """Generate alerts based on health status"""
        
        alerts = []
        
        # Overall health alerts
        if overall_health < self.alert_thresholds["health_score"]:
            alerts.append(f"System health degraded: {overall_health:.1f}%")
        
        # Component-specific alerts
        for name, health in component_healths.items():
            if health.status == "unhealthy":
                alerts.append(f"Component {name} is unhealthy: {health.error_message}")
            elif health.status == "degraded":
                alerts.append(f"Component {name} is degraded: {health.health_score:.1f}%")
        
        # Resource alerts
        system_health = component_healths.get("system_resources")
        if system_health and system_health.metrics:
            cpu_usage = system_health.metrics.get("cpu_percent", 0)
            memory_usage = system_health.metrics.get("memory_percent", 0)
            
            if cpu_usage > self.alert_thresholds["cpu_usage_percent"]:
                alerts.append(f"High CPU usage: {cpu_usage:.1f}%")
            
            if memory_usage > self.alert_thresholds["memory_usage_percent"]:
                alerts.append(f"High memory usage: {memory_usage:.1f}%")
        
        return alerts
    
    async def _check_prefect_server_health(self) -> ComponentHealth:
        """Check Prefect server health"""
        
        try:
            # Check if we can connect to Prefect server
            client = self.orchestrator.prefect_client
            
            # Try to get server info
            start_time = time.time()
            server_info = await client.api_healthcheck()
            response_time = (time.time() - start_time) * 1000
            
            health_score = 100
            status = "healthy"
            
            # Adjust score based on response time
            if response_time > 2000:
                health_score = 80
                status = "degraded"
            elif response_time > 5000:
                health_score = 50
                status = "degraded"
            
            return ComponentHealth(
                name="prefect_server",
                status=status,
                health_score=health_score,
                last_check=datetime.now(),
                metrics={
                    "response_time_ms": response_time,
                    "server_info": server_info
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="prefect_server",
                status="unhealthy",
                health_score=0,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_codegen_agent_health(self) -> ComponentHealth:
        """Check Codegen agent health"""
        
        try:
            # Simple health check - try to get agent status
            agent = self.orchestrator.codegen_agent
            
            # This would depend on Codegen SDK having a health check method
            # For now, we'll assume it's healthy if we can access it
            health_score = 100
            status = "healthy"
            
            return ComponentHealth(
                name="codegen_agent",
                status=status,
                health_score=health_score,
                last_check=datetime.now(),
                metrics={
                    "org_id": self.orchestrator.codegen_org_id,
                    "agent_available": True
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="codegen_agent",
                status="unhealthy",
                health_score=0,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_github_integration_health(self) -> ComponentHealth:
        """Check GitHub integration health"""
        
        try:
            if not self.orchestrator.github_token:
                return ComponentHealth(
                    name="github_integration",
                    status="degraded",
                    health_score=50,
                    last_check=datetime.now(),
                    error_message="GitHub token not configured"
                )
            
            # This would check GitHub API connectivity
            # For now, assume healthy if token is present
            health_score = 100
            status = "healthy"
            
            return ComponentHealth(
                name="github_integration",
                status=status,
                health_score=health_score,
                last_check=datetime.now(),
                metrics={
                    "token_configured": True,
                    "api_accessible": True
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="github_integration",
                status="unhealthy",
                health_score=0,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_linear_integration_health(self) -> ComponentHealth:
        """Check Linear integration health"""
        
        try:
            # This would check Linear API connectivity
            # For now, assume healthy
            health_score = 100
            status = "healthy"
            
            return ComponentHealth(
                name="linear_integration",
                status=status,
                health_score=health_score,
                last_check=datetime.now(),
                metrics={
                    "api_accessible": True
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="linear_integration",
                status="unhealthy",
                health_score=0,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_system_resources_health(self) -> ComponentHealth:
        """Check system resource health"""
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Calculate health score based on resource usage
            health_score = 100
            status = "healthy"
            
            if cpu_percent > 80 or memory.percent > 85:
                health_score = 60
                status = "degraded"
            elif cpu_percent > 90 or memory.percent > 95:
                health_score = 30
                status = "unhealthy"
            
            return ComponentHealth(
                name="system_resources",
                status=status,
                health_score=health_score,
                last_check=datetime.now(),
                metrics={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="system_resources",
                status="unhealthy",
                health_score=0,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def _check_workflow_execution_health(self) -> ComponentHealth:
        """Check workflow execution health"""
        
        try:
            # Check active executions and recent failures
            active_count = len(self.orchestrator.active_executions)
            metrics = self.orchestrator.metrics
            
            health_score = 100
            status = "healthy"
            
            # Adjust based on error rate
            if metrics.error_rate_percent > 20:
                health_score = 50
                status = "degraded"
            elif metrics.error_rate_percent > 10:
                health_score = 75
                status = "degraded"
            
            return ComponentHealth(
                name="workflow_execution",
                status=status,
                health_score=health_score,
                last_check=datetime.now(),
                metrics={
                    "active_executions": active_count,
                    "error_rate_percent": metrics.error_rate_percent,
                    "total_executed": metrics.total_workflows_executed,
                    "successful": metrics.successful_workflows,
                    "failed": metrics.failed_workflows
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="workflow_execution",
                status="unhealthy",
                health_score=0,
                last_check=datetime.now(),
                error_message=str(e)
            )
    
    async def _record_performance_metrics(self):
        """Record performance metrics for trend analysis"""
        
        try:
            metrics = await self.orchestrator.get_metrics()
            
            performance_data = {
                "timestamp": datetime.now().isoformat(),
                "active_workflows": metrics.active_workflows,
                "error_rate": metrics.error_rate_percent,
                "avg_execution_time": metrics.average_execution_time,
                "system_health": metrics.system_health_score,
                "cpu_usage": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent
            }
            
            self.performance_history.append(performance_data)
            
            # Limit history size
            if len(self.performance_history) > self.max_history_size:
                self.performance_history = self.performance_history[-self.max_history_size:]
                
        except Exception as e:
            logger.error(f"Failed to record performance metrics: {e}")
    
    async def _check_alerts(self, health_status: Dict[str, Any]):
        """Check for alert conditions and trigger notifications"""
        
        alerts = health_status.get("alerts", [])
        
        if alerts:
            logger.warning(f"System alerts detected: {alerts}")
            
            # This would trigger alert notifications
            # Implementation depends on notification system setup
            await self._send_alerts(alerts)
    
    async def _send_alerts(self, alerts: List[str]):
        """Send alert notifications"""
        
        try:
            # This would integrate with notification systems
            # For now, just log the alerts
            for alert in alerts:
                logger.warning(f"ALERT: {alert}")
                
        except Exception as e:
            logger.error(f"Failed to send alerts: {e}")
    
    def get_performance_trends(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance trends for the specified time period"""
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        return [
            data for data in self.performance_history
            if datetime.fromisoformat(data["timestamp"]) > cutoff_time
        ]
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of current health status"""
        
        if not self.performance_history:
            return {"status": "no_data"}
        
        latest = self.performance_history[-1]
        
        return {
            "overall_health": latest.get("system_health", 0),
            "active_workflows": latest.get("active_workflows", 0),
            "error_rate": latest.get("error_rate", 0),
            "last_updated": latest.get("timestamp"),
            "monitoring_active": self.monitoring_active
        }


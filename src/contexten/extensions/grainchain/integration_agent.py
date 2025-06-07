"""
Main integration agent for Grainchain extension.

This module provides the central orchestrator that coordinates all Grainchain
components and integrates with the Contexten ecosystem.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

from .types import (
    GrainchainEvent, GrainchainEventType, IntegrationStatus,
    SandboxProvider, QualityGateType
)
from .config import GrainchainIntegrationConfig, get_grainchain_config
from .grainchain_client import GrainchainClient
from .sandbox_manager import SandboxManager
from .quality_gates import QualityGateManager
from .snapshot_manager import SnapshotManager
from .provider_manager import ProviderManager


logger = logging.getLogger(__name__)


@dataclass
class IntegrationHealth:
    """Health status of the integration."""
    status: IntegrationStatus
    components: Dict[str, str]
    issues: List[str]
    last_check: datetime
    uptime: float


class GrainchainIntegrationAgent:
    """
    Main integration agent for Grainchain.
    
    Orchestrates all Grainchain components and provides the main interface
    for integration with the Contexten ecosystem.
    """
    
    def __init__(self, config: Optional[GrainchainIntegrationConfig] = None):
        """Initialize the integration agent."""
        self.config = config or get_grainchain_config()
        
        # Core components
        self.client = GrainchainClient(self.config)
        self.sandbox_manager = SandboxManager(self.config)
        self.quality_gate_manager = QualityGateManager(self.config)
        self.snapshot_manager = SnapshotManager(self.config)
        self.provider_manager = ProviderManager(self.config)
        
        # Event handling
        self._event_handlers = {}
        self._background_tasks = []
        
        # Health monitoring
        self._health_status = IntegrationHealth(
            status=IntegrationStatus.HEALTHY,
            components={},
            issues=[],
            last_check=datetime.utcnow(),
            uptime=0.0
        )
        
        # Integration state
        self._started_at = None
        self._is_running = False
        
        # Setup event handlers
        self._setup_event_handlers()
    
    async def start(self):
        """Start the integration agent."""
        if self._is_running:
            return
        
        logger.info("Starting Grainchain integration agent")
        
        self._started_at = datetime.utcnow()
        self._is_running = True
        
        # Validate configuration
        config_issues = self.config.validate()
        if config_issues:
            logger.warning(f"Configuration issues: {config_issues}")
        
        # Start background tasks
        if self.config.monitoring.enabled:
            self._background_tasks.append(
                asyncio.create_task(self._health_monitoring_loop())
            )
        
        if self.config.cost_optimization:
            self._background_tasks.append(
                asyncio.create_task(self._cost_optimization_loop())
            )
        
        if self.config.performance_benchmarking:
            self._background_tasks.append(
                asyncio.create_task(self._performance_monitoring_loop())
            )
        
        # Setup event handlers with components
        self.client.add_event_handler(self._handle_grainchain_event)
        
        logger.info("Grainchain integration agent started successfully")
    
    async def stop(self):
        """Stop the integration agent."""
        if not self._is_running:
            return
        
        logger.info("Stopping Grainchain integration agent")
        
        self._is_running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Shutdown components
        await self.sandbox_manager.shutdown()
        
        logger.info("Grainchain integration agent stopped")
    
    def _setup_event_handlers(self):
        """Setup default event handlers."""
        self.on_event(GrainchainEventType.SANDBOX_CREATED)(self._handle_sandbox_created)
        self.on_event(GrainchainEventType.QUALITY_GATE_FAILED)(self._handle_quality_gate_failed)
        self.on_event(GrainchainEventType.COST_THRESHOLD_EXCEEDED)(self._handle_cost_threshold_exceeded)
        self.on_event(GrainchainEventType.PERFORMANCE_DEGRADED)(self._handle_performance_degraded)
    
    def on_event(self, event_type: GrainchainEventType):
        """Decorator for registering event handlers."""
        def decorator(handler: Callable[[GrainchainEvent], None]):
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)
            return handler
        return decorator
    
    async def _handle_grainchain_event(self, event: GrainchainEvent):
        """Handle Grainchain events."""
        handlers = self._event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler failed for {event.event_type.value}: {e}")
    
    async def _handle_sandbox_created(self, event: GrainchainEvent):
        """Handle sandbox creation events."""
        logger.info(f"Sandbox created: {event.data.get('sandbox_id')} on {event.data.get('provider')}")
    
    async def _handle_quality_gate_failed(self, event: GrainchainEvent):
        """Handle quality gate failure events."""
        logger.warning(f"Quality gate failed: {event.data}")
        
        # Could trigger notifications, create debug snapshots, etc.
        if self.config.ci_integration.notification_channels:
            await self._send_notification(
                f"Quality gate failed for execution {event.data.get('execution_id')}",
                event.data
            )
    
    async def _handle_cost_threshold_exceeded(self, event: GrainchainEvent):
        """Handle cost threshold exceeded events."""
        logger.warning(f"Cost threshold exceeded: {event.data}")
        
        # Trigger cost optimization
        if self.config.cost_optimization:
            await self._trigger_cost_optimization()
    
    async def _handle_performance_degraded(self, event: GrainchainEvent):
        """Handle performance degradation events."""
        logger.warning(f"Performance degraded: {event.data}")
        
        # Could trigger provider switching, scaling, etc.
    
    async def _health_monitoring_loop(self):
        """Background health monitoring loop."""
        while self._is_running:
            try:
                await self._update_health_status()
                await asyncio.sleep(self.config.monitoring.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute
    
    async def _cost_optimization_loop(self):
        """Background cost optimization loop."""
        while self._is_running:
            try:
                await self._run_cost_optimization()
                await asyncio.sleep(3600)  # Run every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cost optimization error: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    async def _performance_monitoring_loop(self):
        """Background performance monitoring loop."""
        while self._is_running:
            try:
                await self._run_performance_monitoring()
                await asyncio.sleep(1800)  # Run every 30 minutes
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(300)  # Retry in 5 minutes
    
    async def _update_health_status(self):
        """Update the health status of all components."""
        components = {}
        issues = []
        
        try:
            # Check sandbox manager
            sandbox_health = await self.sandbox_manager.get_health_status()
            components["sandbox_manager"] = sandbox_health["status"]
            if sandbox_health.get("issues"):
                issues.extend(sandbox_health["issues"])
            
            # Check provider manager
            provider_health = await self.provider_manager.get_health_status()
            components["provider_manager"] = provider_health["status"]
            if provider_health.get("issues"):
                issues.extend(provider_health["issues"])
            
            # Check quality gate manager
            components["quality_gate_manager"] = "healthy"  # Simplified
            
            # Check snapshot manager
            components["snapshot_manager"] = "healthy"  # Simplified
            
            # Determine overall status
            if any(status == "unhealthy" for status in components.values()):
                overall_status = IntegrationStatus.UNHEALTHY
            elif any(status == "degraded" for status in components.values()):
                overall_status = IntegrationStatus.DEGRADED
            else:
                overall_status = IntegrationStatus.HEALTHY
            
            # Calculate uptime
            uptime = 0.0
            if self._started_at:
                uptime = (datetime.utcnow() - self._started_at).total_seconds()
            
            self._health_status = IntegrationHealth(
                status=overall_status,
                components=components,
                issues=issues,
                last_check=datetime.utcnow(),
                uptime=uptime
            )
            
        except Exception as e:
            logger.error(f"Health status update failed: {e}")
            self._health_status.status = IntegrationStatus.UNHEALTHY
            self._health_status.issues.append(f"Health check failed: {e}")
    
    async def _run_cost_optimization(self):
        """Run cost optimization analysis."""
        try:
            optimization_result = await self.sandbox_manager.optimize_resources()
            
            if optimization_result["potential_monthly_savings"] > 100:  # $100 threshold
                logger.info(f"Cost optimization opportunity: ${optimization_result['potential_monthly_savings']:.2f}/month")
                
                # Could automatically implement optimizations
                for recommendation in optimization_result["recommendations"]:
                    logger.info(f"Recommendation: {recommendation['description']}")
        
        except Exception as e:
            logger.error(f"Cost optimization failed: {e}")
    
    async def _run_performance_monitoring(self):
        """Run performance monitoring and benchmarking."""
        try:
            # Run benchmarks
            benchmark_results = await self.client.benchmark_providers(
                test_suite="performance_monitoring"
            )
            
            # Analyze results for degradation
            for provider, results in benchmark_results.items():
                if "error" in results:
                    continue
                
                startup_time = results.get("startup_time", 0)
                if startup_time > 30:  # 30 second threshold
                    await self._emit_event(GrainchainEventType.PERFORMANCE_DEGRADED, {
                        "provider": provider.value,
                        "metric": "startup_time",
                        "value": startup_time,
                        "threshold": 30
                    })
        
        except Exception as e:
            logger.error(f"Performance monitoring failed: {e}")
    
    async def _trigger_cost_optimization(self):
        """Trigger immediate cost optimization."""
        logger.info("Triggering cost optimization")
        await self._run_cost_optimization()
    
    async def _send_notification(self, message: str, data: Dict[str, Any]):
        """Send notification to configured channels."""
        # This would integrate with notification systems
        logger.info(f"Notification: {message}")
    
    async def _emit_event(self, event_type: GrainchainEventType, data: Dict[str, Any]):
        """Emit an event."""
        event = GrainchainEvent(
            event_type=event_type,
            timestamp=datetime.utcnow(),
            source="integration_agent",
            data=data
        )
        
        await self._handle_grainchain_event(event)
    
    # Public API methods
    
    async def get_health_status(self) -> IntegrationHealth:
        """Get current health status."""
        return self._health_status
    
    async def run_quality_gates(
        self,
        pr_number: Optional[int] = None,
        commit_sha: Optional[str] = None,
        gates: Optional[List[QualityGateType]] = None
    ):
        """Run quality gates."""
        return await self.quality_gate_manager.run_quality_gates(
            pr_number=pr_number,
            commit_sha=commit_sha,
            gates=gates
        )
    
    async def create_pr_environment(
        self,
        pr_number: int,
        commit_sha: str,
        provider: Optional[SandboxProvider] = None
    ):
        """Create a PR environment."""
        # This would be implemented in pr_automation.py
        pass
    
    async def get_metrics(self):
        """Get comprehensive metrics."""
        return {
            "health": self._health_status,
            "sandbox_metrics": await self.client.get_metrics(),
            "provider_metrics": await self.provider_manager.get_metrics(),
            "uptime": self._health_status.uptime
        }


def create_grainchain_integration_agent(
    config: Optional[GrainchainIntegrationConfig] = None
) -> GrainchainIntegrationAgent:
    """
    Factory function to create a Grainchain integration agent.
    
    Args:
        config: Optional configuration (will load from environment if not provided)
        
    Returns:
        Configured GrainchainIntegrationAgent
    """
    return GrainchainIntegrationAgent(config)


# Placeholder classes for components not yet implemented

class SnapshotManager:
    """Placeholder for snapshot manager."""
    
    def __init__(self, config):
        self.config = config
    
    async def create_snapshot(self, name: str, metadata: Dict[str, Any] = None):
        """Create a snapshot."""
        pass
    
    async def restore_snapshot(self, snapshot_id: str):
        """Restore a snapshot."""
        pass
    
    async def list_snapshots(self):
        """List snapshots."""
        return []


class ProviderManager:
    """Placeholder for provider manager."""
    
    def __init__(self, config):
        self.config = config
    
    async def get_health_status(self):
        """Get provider health status."""
        return {"status": "healthy", "issues": []}
    
    async def get_metrics(self):
        """Get provider metrics."""
        return {}
    
    async def recommend_provider(self, **kwargs):
        """Recommend optimal provider."""
        return {"provider": SandboxProvider.E2B, "estimated_cost": 1.0}


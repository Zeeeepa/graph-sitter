"""Main integration agent for Grainchain extension.

This module provides the central orchestrator that coordinates all Grainchain
components and integrates with the Contexten ecosystem.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Callable

from .config import GrainchainIntegrationConfig, get_grainchain_config
from .grainchain_types import (
    GrainchainEvent,
    GrainchainEventType,
    IntegrationStatus,
    QualityGateType,
    QualityGateStatus,
    QualityGateResult,
    SandboxProvider
)
from .quality_gates import QualityGateManager, QualityGateExecution
from .sandbox_manager import SandboxManager

if TYPE_CHECKING:
    from .grainchain_client import GrainchainClient
    from .quality_gates import QualityGateManager
    from .sandbox_manager import SandboxManager

logger = logging.getLogger(__name__)


@dataclass
class IntegrationHealth:
    """Health status of the integration."""
    status: IntegrationStatus
    components: Dict[str, bool]
    issues: List[str]
    last_check: datetime
    uptime: float


class GrainchainIntegrationAgent:
    """Integration agent for Grainchain."""

    def __init__(self, config: Optional[GrainchainIntegrationConfig] = None):
        """Initialize the integration agent.

        Args:
            config: Integration configuration
        """
        self.config = config or get_grainchain_config()
        self._event_handlers: Dict[GrainchainEventType, List[Callable[..., Any]]] = {}
        self._quality_gate_manager = QualityGateManager(self.config)
        self._sandbox_manager = SandboxManager(self.config)
        self._is_running = False
        self._started_at: Optional[datetime] = None
        self._health_status = IntegrationHealth(
            status=IntegrationStatus.HEALTHY,
            components={},
            issues=[],
            last_check=datetime.now(UTC),
            uptime=0.0
        )

        # Register event handlers
        self.on_event(GrainchainEventType.SANDBOX_CREATED)(self._handle_sandbox_created)
        self.on_event(GrainchainEventType.SANDBOX_DESTROYED)(self._handle_sandbox_destroyed)
        self.on_event(GrainchainEventType.QUALITY_GATE_FAILED)(self._handle_quality_gate_failed)
        self.on_event(GrainchainEventType.COST_THRESHOLD_EXCEEDED)(self._handle_cost_threshold_exceeded)
        self.on_event(GrainchainEventType.PERFORMANCE_DEGRADED)(self._handle_performance_degraded)

    async def _handle_grainchain_event(self, event: GrainchainEvent) -> None:
        """Handle a Grainchain event.

        Args:
            event: The event to handle
        """
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.exception(f"Event handler failed: {e}")

    def on_event(self, event_type: GrainchainEventType) -> Callable:
        """Decorator for registering event handlers."""
        def decorator(handler: Callable[[GrainchainEvent], None]):
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)
            return handler
        return decorator

    async def _handle_sandbox_created(self, event: GrainchainEvent) -> None:
        """Handle sandbox creation event."""
        logger.info(f"Sandbox created: {event.data}")

    async def _handle_sandbox_destroyed(self, event: GrainchainEvent) -> None:
        """Handle sandbox destruction event."""
        logger.info(f"Sandbox destroyed: {event.data}")

    async def _handle_quality_gate_failed(self, event: GrainchainEvent) -> None:
        """Handle quality gate failure event."""
        logger.warning(f"Quality gate failed: {event.data}")

    async def _handle_cost_threshold_exceeded(self, event: GrainchainEvent) -> None:
        """Handle cost threshold exceeded event."""
        logger.warning(f"Cost threshold exceeded: {event.data}")

    async def _handle_performance_degraded(self, event: GrainchainEvent) -> None:
        """Handle performance degradation event."""
        logger.warning(f"Performance degraded: {event.data}")

    async def _health_monitoring_loop(self) -> None:
        """Background health monitoring loop."""
        while True:
            try:
                await self._check_health()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.exception(f"Health monitoring error: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute

    async def _check_health(self) -> None:
        """Check the health of all components."""
        try:
            # Check provider health
            providers = await self._sandbox_manager._grainchain_client.get_available_providers()
            healthy_providers = len(providers)
            total_providers = len(SandboxProvider)
            health_ratio = healthy_providers / total_providers

            # Check resource utilization
            utilization = await self._sandbox_manager.get_resource_utilization()

            # Identify issues
            issues = []

            if health_ratio < 0.5:
                issues.append("More than half of providers are unavailable")

            if utilization['total_active_sandboxes'] > self._sandbox_manager._resource_limits['max_concurrent_sessions']:
                issues.append("Session limit exceeded")

            # Update health status
            status = IntegrationStatus.HEALTHY if health_ratio >= 0.8 and not issues else IntegrationStatus.DEGRADED

            self._health_status = IntegrationHealth(
                status=status,
                components={
                    'providers': health_ratio >= 0.8,
                    'sandbox_manager': True,
                    'quality_gates': True
                },
                issues=issues,
                last_check=datetime.now(UTC),
                uptime=self._get_uptime()
            )

        except Exception as e:
            logger.exception(f"Health check failed: {e}")
            self._health_status = IntegrationHealth(
                status=IntegrationStatus.DEGRADED,
                components={},
                issues=[str(e)],
                last_check=datetime.now(UTC),
                uptime=self._get_uptime()
            )

    def _get_uptime(self) -> float:
        """Get uptime in seconds."""
        if not self._started_at:
            return 0.0
        return (datetime.now(UTC) - self._started_at).total_seconds()

    async def _run_cost_optimization(self) -> None:
        """Run cost optimization analysis."""
        try:
            # Get current resource utilization
            utilization = await self._sandbox_manager.get_resource_utilization()

            # Check for cost optimization opportunities
            if utilization['total_active_sandboxes'] > 0:
                # Get optimization recommendations
                recommendations = await self._sandbox_manager.optimize_resources()

                # Log recommendations
                for recommendation in recommendations['recommendations']:
                    logger.info(f"Cost optimization recommendation: {recommendation}")

                # Trigger cost threshold exceeded event if needed
                if recommendations['potential_savings'] > 100.0:  # $100 threshold
                    await self._handle_grainchain_event(GrainchainEvent(
                        event_type=GrainchainEventType.COST_THRESHOLD_EXCEEDED,
                        data={
                            'potential_savings': recommendations['potential_savings'],
                            'recommendations': recommendations['recommendations']
                        },
                        timestamp=datetime.now(UTC),
                        source='cost_optimization'
                    ))

        except Exception as e:
            logger.exception(f"Cost optimization failed: {e}")

    async def _run_performance_monitoring(self) -> None:
        """Run performance monitoring analysis."""
        try:
            # Get current metrics
            utilization = await self._sandbox_manager.get_resource_utilization()

            # Check for performance issues
            for provider, metrics in utilization['provider_breakdown'].items():
                if metrics.get('success_rate', 1.0) < 0.8:
                    await self._handle_grainchain_event(GrainchainEvent(
                        event_type=GrainchainEventType.PERFORMANCE_DEGRADED,
                        data={
                            'provider': provider,
                            'success_rate': metrics['success_rate'],
                            'error_count': metrics.get('error_count', 0)
                        },
                        timestamp=datetime.now(UTC),
                        source='performance_monitoring'
                    ))

        except Exception as e:
            logger.exception(f"Performance monitoring failed: {e}")

    async def _trigger_cost_optimization(self) -> None:
        """Trigger immediate cost optimization."""
        logger.info("Triggering cost optimization")
        await self._run_cost_optimization()

    async def _trigger_performance_monitoring(self) -> None:
        """Trigger immediate performance monitoring."""
        logger.info("Triggering performance monitoring")
        await self._run_performance_monitoring()

    async def _trigger_health_check(self) -> None:
        """Trigger immediate health check."""
        logger.info("Triggering health check")
        await self._check_health()

    async def _send_notification(self, message: str, data: dict[str, Any]) -> None:
        """Send notification to configured channels.

        Args:
            message: Notification message
            data: Additional data to include
        """
        # Log notification
        logger.info(f"Notification: {message}")

    async def _emit_event(self, event_type: GrainchainEventType, data: dict[str, Any]) -> None:
        """Emit an event."""
        event = GrainchainEvent(
            event_type=event_type,
            data=data,
            timestamp=datetime.now(UTC),
            source="integration_agent"
        )
        await self._handle_grainchain_event(event)

    # Public API methods

    async def get_health_status(self) -> IntegrationHealth:
        """Get current health status."""
        return self._health_status

    async def run_quality_gates(
        self,
        execution: QualityGateExecution
    ) -> None:
        """Run quality gates for a given execution.

        Args:
            execution: The quality gate execution
        """
        try:
            # Run quality gates with default settings
            await self._quality_gate_manager.run_quality_gates(execution.pr_number)
        except Exception as e:
            logger.exception(f"Failed to run quality gates: {e}")
            execution.error = str(e)
            execution.status = "error"

    async def create_pr_environment(
        self,
        pr_number: int,
        commit_sha: str,
        provider: SandboxProvider | None = None
    ):
        """Create a PR environment."""
        # This would be implemented in pr_automation.py
        pass

    async def get_metrics(self):
        """Get comprehensive metrics."""
        return {
            "status": self._health_status.status.value,
            "components": self._health_status.components,
            "issues": self._health_status.issues,
            "health": self._health_status,
            "sandbox_metrics": await self.client.get_metrics(),
            "provider_metrics": await self.provider_manager.get_metrics(),
            "uptime": self._health_status.uptime
        }


def create_grainchain_integration_agent(
    config: GrainchainIntegrationConfig | None = None
) -> GrainchainIntegrationAgent:
    """Factory function to create a Grainchain integration agent.

    Args:
        config: Optional configuration (will load from environment if not provided)

    Returns:
        Configured GrainchainIntegrationAgent
    """
    return GrainchainIntegrationAgent(config)

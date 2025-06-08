"""Integration agent for Grainchain.

This module provides the main orchestrator for Grainchain integration,
coordinating sandbox management, quality gates, and event handling.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, cast

from .config import GrainchainIntegrationConfig, get_grainchain_config
from .grainchain_types import GrainchainEvent, GrainchainEventType, IntegrationStatus, QualityGateType, SandboxProvider

if TYPE_CHECKING:
    from .grainchain_client import GrainchainClient
    from .quality_gates import QualityGateManager
    from .sandbox_manager import SandboxManager

logger = logging.getLogger(__name__)


@dataclass
class IntegrationHealth:
    """Health status of the integration."""
    status: IntegrationStatus
    components: dict[str, str]
    issues: list[str]
    last_check: datetime
    uptime: float


class GrainchainIntegrationAgent:
    """Main orchestrator for Grainchain integration."""

    def __init__(self, config: Optional[GrainchainIntegrationConfig] = None) -> None:
        """Initialize the integration agent."""
        from .config import get_grainchain_config

        self.config = config or get_grainchain_config()
        self._quality_gate_manager = QualityGateManager(self.config)
        self._event_handlers: Dict[GrainchainEventType, List[Callable[[GrainchainEvent], Any]]] = {}

    async def _handle_grainchain_event(self, event: GrainchainEvent) -> None:
        """Handle a Grainchain event."""
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.exception(f"Event handler failed: {e}")

    async def run_quality_gates(self, *args: Any, **kwargs: Any) -> List[QualityGateResult]:
        """Run quality gates."""
        return await self._quality_gate_manager.run_quality_gates(*args, **kwargs)

    def on_event(self, event_type: GrainchainEventType):
        """Decorator for registering event handlers."""
        def decorator(handler: Callable[[GrainchainEvent], None]):
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)
            return handler
        return decorator

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
                uptime = (datetime.now(UTC) - self._started_at).total_seconds()

            self._health_status = IntegrationHealth(
                status=overall_status,
                components=components,
                issues=issues,
                last_check=datetime.now(UTC),
                uptime=uptime
            )

        except Exception as e:
            logger.exception(f"Health status update failed: {e}")
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
            logger.exception(f"Cost optimization failed: {e}")

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
            logger.exception(f"Performance monitoring failed: {e}")

    async def _trigger_cost_optimization(self):
        """Trigger immediate cost optimization."""
        logger.info("Triggering cost optimization")
        await self._run_cost_optimization()

    async def _send_notification(self, message: str, data: dict[str, Any]):
        """Send notification to configured channels."""
        # This would integrate with notification systems
        logger.info(f"Notification: {message}")

    async def _emit_event(self, event_type: GrainchainEventType, data: dict[str, Any]):
        """Emit an event."""
        event = GrainchainEvent(
            event_type=event_type,
            timestamp=datetime.now(UTC),
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
        pr_number: int | None = None,
        commit_sha: str | None = None,
        gates: list[QualityGateType] | None = None
    ):
        """Run quality gates."""
        return await self._quality_gate_manager.run_quality_gates(
            pr_number=pr_number,
            commit_sha=commit_sha,
            gates=gates
        )

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

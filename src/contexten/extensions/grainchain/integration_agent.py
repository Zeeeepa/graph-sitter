"""Integration agent for Grainchain.

This module provides the main orchestrator for Grainchain integration,
coordinating sandbox management, quality gates, and event handling.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, TypeVar, cast

from .config import GrainchainIntegrationConfig
from .grainchain_types import (
    GrainchainEvent,
    GrainchainEventType,
    IntegrationStatus,
    QualityGateResult,
    QualityGateType,
    SandboxProvider,
)
from .quality_gates import QualityGateManager

if TYPE_CHECKING:
    from .grainchain_client import GrainchainClient
    from .sandbox_manager import SandboxManager

logger = logging.getLogger(__name__)

T = TypeVar('T')

class NotificationChannel(Enum):
    """Supported notification channels."""
    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK = "webhook"
    TEAMS = "teams"
    DISCORD = "discord"

@dataclass
class IntegrationHealth:
    """Health status of the integration."""
    status: IntegrationStatus
    components: Dict[str, str]
    issues: List[str]
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
        self._notification_channels: Dict[NotificationChannel, bool] = {
            channel: False for channel in NotificationChannel
        }
        self._metrics: Dict[str, float] = {
            "total_executions": 0,
            "success_rate": 0.0,
            "average_duration": 0.0,
            "error_rate": 0.0
        }

    async def _handle_grainchain_event(self, event: GrainchainEvent) -> None:
        """Handle a Grainchain event."""
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.exception(f"Event handler failed: {e}")

    async def run_quality_gates(
        self,
        gates: Optional[List[QualityGateType]] = None,
        parallel: bool = True,
        fail_fast: bool = True
    ) -> List[QualityGateResult]:
        """Run quality gates."""
        results = await self._quality_gate_manager.run_quality_gates(
            gates=gates,
            parallel=parallel,
            fail_fast=fail_fast
        )
        self._update_metrics(results)
        return cast(List[QualityGateResult], results)

    def on_event(self, event_type: GrainchainEventType) -> Callable[[Callable[[GrainchainEvent], T]], Callable[[GrainchainEvent], T]]:
        """Decorator for registering event handlers."""
        def decorator(handler: Callable[[GrainchainEvent], T]) -> Callable[[GrainchainEvent], T]:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(cast(Callable[[GrainchainEvent], Any], handler))
            return handler
        return decorator

    def enable_notification_channel(self, channel: NotificationChannel) -> None:
        """Enable a notification channel."""
        self._notification_channels[channel] = True

    def disable_notification_channel(self, channel: NotificationChannel) -> None:
        """Disable a notification channel."""
        self._notification_channels[channel] = False

    def get_enabled_channels(self) -> List[NotificationChannel]:
        """Get list of enabled notification channels."""
        return [
            channel for channel, enabled in self._notification_channels.items()
            if enabled
        ]

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the integration agent."""
        try:
            # Get component health
            quality_gates_health = await self._quality_gate_manager.get_health_status()

            # Calculate overall health
            issues = []
            if quality_gates_health["status"] != IntegrationStatus.HEALTHY:
                issues.extend(quality_gates_health["issues"])

            status = IntegrationStatus.HEALTHY if not issues else IntegrationStatus.DEGRADED

            return {
                "status": status,
                "components": {
                    "quality_gates": quality_gates_health
                },
                "issues": issues,
                "last_check": datetime.now(UTC),
                "metrics": self._metrics.copy(),
                "notification_channels": {
                    channel.value: enabled
                    for channel, enabled in self._notification_channels.items()
                }
            }

        except Exception as e:
            logger.exception("Failed to get health status")
            return {
                "status": IntegrationStatus.ERROR,
                "error": str(e),
                "issues": ["Failed to get health status"]
            }

    def _update_metrics(self, results: List[QualityGateResult]) -> None:
        """Update integration metrics."""
        if not results:
            return

        self._metrics["total_executions"] += 1
        success_count = sum(1 for result in results if result.passed)
        total_duration = sum(result.duration for result in results)

        # Update success rate
        self._metrics["success_rate"] = (
            (self._metrics["total_executions"] * self._metrics["success_rate"] + success_count) /
            (self._metrics["total_executions"] + 1)
        )

        # Update average duration
        self._metrics["average_duration"] = (
            (self._metrics["average_duration"] * self._metrics["total_executions"] + total_duration) /
            (self._metrics["total_executions"] + 1)
        )

        # Update error rate
        error_count = len([r for r in results if r.error_message])
        self._metrics["error_rate"] = (
            (self._metrics["error_rate"] * self._metrics["total_executions"] + error_count) /
            (self._metrics["total_executions"] + 1)
        )


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

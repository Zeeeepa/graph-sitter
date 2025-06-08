"""Integration agent for Grainchain.

This module provides the main orchestrator for Grainchain integration,
coordinating sandbox management, quality gates, and event handling.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set, TypeVar, cast

from .config import GrainchainIntegrationConfig, get_grainchain_config
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

    async def run_quality_gates(
        self,
        gates: Optional[List[QualityGateType]] = None,
        parallel: bool = True,
        fail_fast: bool = True
    ) -> List[QualityGateResult]:
        """Run quality gates."""
        return await self._quality_gate_manager.run_quality_gates(
            gates=gates,
            parallel=parallel,
            fail_fast=fail_fast
        )

    def on_event(self, event_type: GrainchainEventType) -> Callable[[Callable[[GrainchainEvent], T]], Callable[[GrainchainEvent], T]]:
        """Decorator for registering event handlers."""
        def decorator(handler: Callable[[GrainchainEvent], T]) -> Callable[[GrainchainEvent], T]:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []
            self._event_handlers[event_type].append(handler)
            return handler
        return decorator

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
                "last_check": datetime.now(UTC)
            }

        except Exception as e:
            logger.exception("Failed to get health status")
            return {
                "status": IntegrationStatus.ERROR,
                "error": str(e),
                "issues": ["Failed to get health status"]
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

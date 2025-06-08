"""High-level sandbox management for Grainchain integration.

This module provides advanced sandbox lifecycle management, session handling,
and resource optimization for the Grainchain integration system.
"""

import asyncio
import logging
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List, Optional, AsyncIterator, TypeVar
from dataclasses import dataclass, field

from .config import GrainchainIntegrationConfig
from .grainchain_client import GrainchainClient, SandboxSession
from .grainchain_types import (
    ExecutionResult,
    IntegrationStatus,
    SandboxConfig,
    SandboxMetrics,
    SandboxProvider
)

logger = logging.getLogger(__name__)


class ProviderUnavailableError(Exception):
    """Exception raised when a provider is not available."""
    pass


@dataclass
class SandboxManagerConfig:
    """Configuration for the sandbox manager."""
    max_concurrent_sandboxes: int = 10
    max_sandbox_lifetime: int = 3600  # 1 hour
    cleanup_interval: int = 300  # 5 minutes
    snapshots: Dict[str, Any] = field(default_factory=dict)


class TrackedSandboxSession:
    """Wrapper around SandboxSession that tracks metrics."""

    def __init__(self, session: SandboxSession, session_id: str, manager: 'SandboxManager'):
        """Initialize the tracked sandbox session.

        Args:
            session: The sandbox session to track
            session_id: ID of the session
            manager: The sandbox manager
        """
        self.session = session
        self.session_id = session_id
        self.manager = manager

    async def execute(self, command: str, timeout: Optional[int] = None) -> ExecutionResult:
        """Execute a command in the sandbox.

        Args:
            command: Command to execute
            timeout: Optional timeout in seconds

        Returns:
            ExecutionResult: Result of the command execution
        """
        result = await self.session.execute(self.session_id, command, timeout)

        # Update metrics
        session_info = self.manager._active_sandboxes.get(self.session_id)
        if session_info:
            session_info['metrics']['commands_executed'] += 1

        return result

    async def _cleanup_session(self) -> None:
        """Clean up the sandbox session."""
        try:
            await self.manager._grainchain_client.create_sandbox(None, None).__aexit__(None, None, None)
        except Exception as e:
            logger.exception(f"Failed to cleanup session {self.session_id}: {e}")


class SandboxManager:
    """Manages sandbox lifecycle and resources."""

    def __init__(self, config: GrainchainIntegrationConfig):
        """Initialize the sandbox manager.

        Args:
            config: Sandbox manager configuration
        """
        self.config = config
        self._grainchain_client = GrainchainClient(config)

        # Session management
        self._active_sandboxes: Dict[str, Any] = {}
        self._session_metrics: Dict[str, SandboxMetrics] = {}
        self._cleanup_task = None

        # Resource management
        self._resource_limits: Dict[str, Any] = {
            'max_concurrent_sessions': getattr(config, 'max_concurrent_sandboxes', 10),
            'session_timeout': getattr(config, 'max_sandbox_lifetime', 3600),
            'cleanup_interval': getattr(config, 'cleanup_interval', 300)
        }

        # Auto-cleanup
        async def cleanup_loop():
            while True:
                try:
                    await self._cleanup_expired_sessions()
                    await asyncio.sleep(self._resource_limits['cleanup_interval'])
                except Exception as e:
                    logger.exception(f"Cleanup task error: {e}")
                    await asyncio.sleep(300)  # Retry in 5 minutes

        self._cleanup_task = asyncio.create_task(cleanup_loop())

    @asynccontextmanager
    async def create_session(
        self,
        config: Optional[SandboxConfig] = None,
        provider_name: Optional[str] = None,
        auto_cleanup: bool = True
    ) -> AsyncIterator[SandboxSession]:
        """Create a new sandbox session.

        Args:
            config: Optional sandbox configuration
            provider_name: Optional provider name
            auto_cleanup: Whether to automatically clean up the session

        Returns:
            AsyncIterator[SandboxSession]: The sandbox session
        """
        session = None
        try:
            session = await self._create_session(config, provider_name)
            yield session
        finally:
            if session and auto_cleanup:
                await self._cleanup_expired_sessions()

    async def _create_session(self, config: Optional[SandboxConfig], provider_name: Optional[str]) -> SandboxSession:
        """Create a new sandbox session.

        Args:
            config: Optional sandbox configuration
            provider_name: Optional provider name

        Returns:
            SandboxSession: The sandbox session
        """
        if config is None:
            config = SandboxConfig()

        # Select optimal provider
        provider = await self._select_optimal_provider(config)
        config.provider = provider

        # Create sandbox session
        session = await self._grainchain_client.create_sandbox(config, provider).__aenter__()
        return session

    async def _select_optimal_provider(self, config: SandboxConfig) -> SandboxProvider:
        """Select the optimal provider based on current load and requirements.

        Args:
            config: Sandbox configuration

        Returns:
            SandboxProvider: The selected provider
        """
        # Get available providers
        available_providers = await self._grainchain_client.get_available_providers()

        if not available_providers:
            raise ProviderUnavailableError("No providers available")

        # If a specific provider is requested, use it if available
        if config.provider and config.provider in available_providers:
            return config.provider

        # Get provider metrics
        provider_metrics = {}
        for provider in available_providers:
            try:
                metrics = await self._grainchain_client.get_metrics(provider.value)
                provider_metrics[provider] = metrics
            except Exception as e:
                logger.exception(f"Failed to get metrics for {provider.value}: {e}")

        # Score providers based on metrics and requirements
        provider_scores = {}
        for provider, metrics in provider_metrics.items():
            try:
                # Calculate score based on various factors
                score = 0.0

                # Resource availability
                if metrics.total_sandboxes_created > 0:
                    score += (1 - metrics.active_sandboxes / metrics.total_sandboxes_created) * 0.3

                # Performance
                if metrics.average_startup_time > 0:
                    score += (1 / metrics.average_startup_time) * 0.2

                # Reliability
                score += metrics.success_rate * 0.3

                # Cost efficiency
                if metrics.cost_per_hour > 0:
                    score += (1 / metrics.cost_per_hour) * 0.2

                provider_scores[provider] = score
            except Exception as e:
                logger.exception(f"Failed to calculate score for {provider.value}: {e}")
                provider_scores[provider] = 0.0

        # Select provider with highest score
        if not provider_scores:
            # If no scores available, use first available provider
            return available_providers[0]

        return max(provider_scores.items(), key=lambda x: x[1])[0]

    async def get_session_metrics(self, session_id: str) -> dict[str, Any] | None:
        """Get metrics for a specific session."""
        session_info = self._active_sandboxes.get(session_id)
        if not session_info:
            return None

        return {
            'session_id': session_id,
            'provider': session_info['session'].provider.value,
            'created_at': session_info['created_at'],
            'duration': (datetime.now(UTC) - session_info['created_at']).total_seconds(),
            'metrics': session_info['metrics']
        }

    async def list_active_sessions(self) -> list[dict[str, Any]]:
        """List all active sessions."""
        sessions = []

        for session_id, session_info in self._active_sandboxes.items():
            sessions.append({
                'session_id': session_id,
                'provider': session_info['session'].provider.value,
                'sandbox_id': session_info['session'].sandbox_id,
                'created_at': session_info['created_at'],
                'duration': (datetime.now(UTC) - session_info['created_at']).total_seconds(),
                'metrics': session_info['metrics']
            })

        return sessions

    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a specific session."""
        session_info = self._active_sandboxes.get(session_id)
        if not session_info:
            return False

        try:
            # The session will be cleaned up automatically when the context exits
            # For now, we just remove it from tracking
            self._active_sandboxes.pop(session_id, None)
            return True
        except Exception as e:
            logger.exception(f"Failed to terminate session {session_id}: {e}")
            return False

    async def get_resource_utilization(self) -> dict[str, Any]:
        """Get current resource utilization.

        Returns:
            dict[str, Any]: Resource utilization metrics
        """
        utilization: dict[str, Any] = {
            'total_active_sandboxes': 0,
            'total_sessions': len(self._active_sandboxes),
            'total_cost': 0.0,
            'provider_breakdown': {}
        }

        # Get metrics for each provider
        for provider in SandboxProvider:
            try:
                metrics = await self._grainchain_client.get_metrics(provider.value)
                utilization['provider_breakdown'][provider.value] = {
                    'active_sandboxes': metrics.active_sandboxes,
                    'total_execution_time': metrics.total_execution_time,
                    'success_rate': metrics.success_rate,
                    'cost_total': metrics.cost_total,
                    'cost_per_hour': metrics.cost_per_hour,
                    'resource_utilization': metrics.resource_utilization,
                    'error_count': metrics.error_count
                }

                # Update totals
                utilization['total_active_sandboxes'] += int(metrics.active_sandboxes)
                utilization['total_cost'] += float(metrics.cost_total)
            except Exception as e:
                logger.exception(f"Failed to get metrics for {provider.value}: {e}")
                utilization['provider_breakdown'][provider.value] = {
                    'error': str(e)
                }

        return utilization

    async def optimize_resources(self) -> dict[str, Any]:
        """Optimize resource allocation.

        Returns:
            dict[str, Any]: Optimization results
        """
        optimization_results: dict[str, Any] = {
            'recommendations': [],
            'potential_savings': 0.0
        }

        # Get current metrics
        for provider in SandboxProvider:
            try:
                metrics = await self._grainchain_client.get_metrics(provider.value)

                # Check for underutilized resources
                if metrics.active_sandboxes < metrics.total_sandboxes_created * 0.3:
                    optimization_results['recommendations'].append({
                        'provider': provider.value,
                        'action': 'scale_down',
                        'reason': 'Low utilization',
                        'potential_savings': metrics.cost_per_hour * 0.7
                    })
                    optimization_results['potential_savings'] += metrics.cost_per_hour * 0.7

                # Check for performance issues
                if metrics.success_rate < 0.8:
                    optimization_results['recommendations'].append({
                        'provider': provider.value,
                        'action': 'investigate',
                        'reason': 'Low success rate',
                        'metrics': {
                            'success_rate': metrics.success_rate,
                            'error_count': metrics.error_count
                        }
                    })

            except Exception as e:
                logger.exception(f"Failed to optimize resources for {provider.value}: {e}")

        return optimization_results

    async def _cleanup_expired_sessions(self):
        """Clean up expired resources and sessions."""
        now = datetime.now(UTC)

        # Clean up long-running sessions if configured
        if hasattr(self.config, 'max_sandbox_lifetime'):
            max_duration = timedelta(seconds=self.config.max_sandbox_lifetime)

            expired_sessions = [
                session_id for session_id, info in self._active_sandboxes.items()
                if now - info['created_at'] > max_duration
            ]

            for session_id in expired_sessions:
                logger.info(f"Cleaning up expired session: {session_id}")
                await self.terminate_session(session_id)

    async def get_health_status(self) -> dict[str, Any]:
        """Get health status of the sandbox manager.

        Returns:
            dict[str, Any]: Health status information
        """
        now = datetime.now(UTC)

        try:
            # Check provider health
            providers = await self._grainchain_client.get_available_providers()
            healthy_providers = len(providers)
            total_providers = len(SandboxProvider)
            health_ratio = healthy_providers / total_providers

            # Check for issues
            issues = []

            if health_ratio < 0.5:
                issues.append("More than half of providers are unavailable")

            if len(self._active_sandboxes) > self._resource_limits['max_concurrent_sessions']:
                issues.append("Session limit exceeded")

            # Determine status
            status = IntegrationStatus.HEALTHY if health_ratio >= 0.8 and not issues else IntegrationStatus.DEGRADED

            return {
                'status': status.value,
                'healthy_providers': healthy_providers,
                'total_providers': total_providers,
                'active_sessions': len(self._active_sandboxes),
                'issues': issues,
                'last_check': now
            }

        except Exception as e:
            logger.exception(f"Health status check failed: {e}")
            return {
                'status': IntegrationStatus.DEGRADED.value,
                'error': str(e),
                'last_check': now
            }

    async def shutdown(self):
        """Shutdown the sandbox manager and cleanup resources."""
        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        # Terminate all active sessions
        session_ids = list(self._active_sandboxes.keys())
        for session_id in session_ids:
            await self.terminate_session(session_id)

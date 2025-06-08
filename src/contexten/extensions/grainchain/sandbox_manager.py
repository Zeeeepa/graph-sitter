"""High-level sandbox management for Grainchain integration.

This module provides advanced sandbox lifecycle management, session handling,
and resource optimization for the Grainchain integration system.
"""

import asyncio
import logging
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

from .config import GrainchainIntegrationConfig
from .grainchain_client import GrainchainClient, SandboxSession
from .grainchain_types import IntegrationStatus, SandboxConfig, SandboxMetrics, SandboxProvider

logger = logging.getLogger(__name__)


class SandboxManager:
    """High-level sandbox management with advanced features.

    Provides session management, resource optimization, auto-scaling,
    and intelligent provider selection for sandbox operations.
    """

    def __init__(self, config: GrainchainIntegrationConfig):
        """Initialize the sandbox manager."""
        self.config = config
        self._grainchain_client = GrainchainClient(config)

        # Session management
        self._active_sessions: dict[str, dict[str, Any]] = {}
        self._session_metrics: dict[str, SandboxMetrics] = {}
        self._cleanup_tasks: list[asyncio.Task] = []

        # Resource management
        self._resource_limits: dict[str, Any] = {
            'max_concurrent_sessions': config.max_concurrent_sandboxes,
            'session_timeout': config.sandbox_timeout,
            'cleanup_interval': 300  # 5 minutes
        }

        # Auto-cleanup
        if self.config.snapshots.cleanup_enabled:
            self._start_cleanup_task()

    def _start_cleanup_task(self):
        """Start the automatic cleanup task."""
        async def cleanup_loop():
            while True:
                try:
                    await self._cleanup_expired_resources()
                    await asyncio.sleep(3600)  # Run every hour
                except Exception as e:
                    logger.exception(f"Cleanup task error: {e}")
                    await asyncio.sleep(300)  # Retry in 5 minutes

        self._cleanup_tasks.append(asyncio.create_task(cleanup_loop()))

    @asynccontextmanager
    async def create_session(
        self,
        config: SandboxConfig | None = None,
        session_id: str | None = None,
        auto_cleanup: bool = True
    ) -> AbstractAsyncContextManager[SandboxSession]:
        """Create a managed sandbox session.

        Args:
            config: Sandbox configuration
            session_id: Optional session identifier for tracking
            auto_cleanup: Whether to automatically cleanup on exit

        Returns:
            Managed sandbox session
        """
        if config is None:
            config = SandboxConfig()

        session_id = session_id or f"session_{datetime.now(UTC).timestamp()}"

        # Select optimal provider
        provider = await self._select_optimal_provider(config)
        config.provider = provider

        # Create sandbox session
        async with self._grainchain_client.create_sandbox(config, provider) as session:
            # Track session
            self._active_sessions[session_id] = {
                'session': session,
                'created_at': datetime.now(UTC),
                'config': config,
                'metrics': {
                    'commands_executed': 0,
                    'files_uploaded': 0,
                    'files_downloaded': 0,
                    'snapshots_created': 0
                }
            }

            # Wrap session with tracking
            tracked_session = TrackedSandboxSession(
                session=session,
                session_id=session_id,
                manager=self
            )

            try:
                yield tracked_session
            finally:
                # Cleanup session tracking
                self._active_sessions.pop(session_id, None)

    async def _select_optimal_provider(self, config: SandboxConfig) -> SandboxProvider:
        """Select the optimal provider based on current load and requirements."""
        available_providers = await self._grainchain_client.get_available_providers()

        if not available_providers:
            msg = "No providers available"
            raise Exception(msg)

        # If provider is specified and available, use it
        if config.provider and config.provider in available_providers:
            return config.provider

        # Get current metrics for load balancing
        provider_metrics = await self._grainchain_client.get_metrics()

        # Score providers based on various factors
        provider_scores = {}

        for provider in available_providers:
            score = 0
            metrics = provider_metrics.get(provider)

            if metrics:
                # Factor in current load (lower is better)
                load_factor = metrics.active_sandboxes / max(1, metrics.total_sandboxes_created)
                score += (1 - load_factor) * 30

                # Factor in success rate (higher is better)
                score += metrics.success_rate * 25

                # Factor in performance (faster startup is better)
                startup_score = max(0, 10 - metrics.average_startup_time)
                score += startup_score * 20

                # Factor in cost (lower is better)
                cost_score = max(0, 10 - metrics.cost_per_hour)
                score += cost_score * 15

                # Factor in resource utilization (moderate is better)
                cpu_util = metrics.resource_utilization.get('cpu', 0.5)
                memory_util = metrics.resource_utilization.get('memory', 0.5)
                util_score = 10 - abs(0.7 - (cpu_util + memory_util) / 2) * 20
                score += util_score * 10

            provider_scores[provider] = score

        # Select provider with highest score
        best_provider = max(provider_scores.keys(), key=lambda p: provider_scores[p])

        logger.info(f"Selected provider {best_provider.value} with score {provider_scores[best_provider]}")
        return best_provider

    async def get_session_metrics(self, session_id: str) -> dict[str, Any] | None:
        """Get metrics for a specific session."""
        session_info = self._active_sessions.get(session_id)
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

        for session_id, session_info in self._active_sessions.items():
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
        session_info = self._active_sessions.get(session_id)
        if not session_info:
            return False

        try:
            # The session will be cleaned up automatically when the context exits
            # For now, we just remove it from tracking
            self._active_sessions.pop(session_id, None)
            return True
        except Exception as e:
            logger.exception(f"Failed to terminate session {session_id}: {e}")
            return False

    async def get_resource_utilization(self) -> dict[str, Any]:
        """Get current resource utilization across all providers."""
        provider_metrics = await self._grainchain_client.get_metrics()

        total_active = sum(m.active_sandboxes for m in provider_metrics.values())
        total_cost = sum(m.cost_total for m in provider_metrics.values())

        utilization = {
            'total_active_sandboxes': total_active,
            'total_sessions': len(self._active_sessions),
            'total_cost': total_cost,
            'provider_breakdown': {}
        }

        for provider, metrics in provider_metrics.items():
            utilization['provider_breakdown'][provider.value] = {
                'active_sandboxes': metrics.active_sandboxes,
                'success_rate': metrics.success_rate,
                'cost_per_hour': metrics.cost_per_hour,
                'resource_utilization': metrics.resource_utilization
            }

        return utilization

    async def optimize_resources(self) -> dict[str, Any]:
        """Analyze and optimize resource usage."""
        utilization = await self.get_resource_utilization()
        provider_metrics = await self._grainchain_client.get_metrics()

        recommendations = []
        potential_savings = 0

        # Analyze provider efficiency
        for provider, metrics in provider_metrics.items():
            if metrics.active_sandboxes == 0 and metrics.cost_per_hour > 0:
                recommendations.append({
                    'type': 'idle_provider',
                    'provider': provider.value,
                    'description': f"Provider {provider.value} has no active sandboxes but incurs costs",
                    'potential_savings': metrics.cost_per_hour * 24 * 30  # Monthly savings
                })
                potential_savings += metrics.cost_per_hour * 24 * 30

        # Analyze session patterns
        long_running_sessions = [
            session_id for session_id, info in self._active_sessions.items()
            if (datetime.now(UTC) - info['created_at']).total_seconds() > 3600  # 1 hour
        ]

        if long_running_sessions:
            recommendations.append({
                'type': 'long_running_sessions',
                'count': len(long_running_sessions),
                'description': f"{len(long_running_sessions)} sessions running for over 1 hour",
                'action': 'Review and consider terminating if no longer needed'
            })

        return {
            'current_utilization': utilization,
            'recommendations': recommendations,
            'potential_monthly_savings': potential_savings
        }

    async def _cleanup_expired_resources(self):
        """Clean up expired resources and sessions."""
        now = datetime.now(UTC)

        # Clean up long-running sessions if configured
        if hasattr(self.config, 'max_session_duration'):
            max_duration = timedelta(seconds=self.config.max_session_duration)

            expired_sessions = [
                session_id for session_id, info in self._active_sessions.items()
                if now - info['created_at'] > max_duration
            ]

            for session_id in expired_sessions:
                logger.info(f"Cleaning up expired session: {session_id}")
                await self.terminate_session(session_id)

    async def get_health_status(self) -> dict[str, Any]:
        """Get health status of the sandbox management system."""
        try:
            available_providers = await self._grainchain_client.get_available_providers()
            provider_metrics = await self._grainchain_client.get_metrics()

            # Calculate overall health
            total_providers = len(self.config.get_enabled_providers())
            healthy_providers = len(available_providers)
            health_ratio = healthy_providers / total_providers if total_providers > 0 else 0

            issues = []
            if health_ratio < 0.5:
                issues.append("More than half of providers are unavailable")

            if len(self._active_sessions) > self._resource_limits['max_concurrent_sessions']:
                issues.append("Session limit exceeded")

            status = IntegrationStatus.HEALTHY if health_ratio >= 0.8 and not issues else IntegrationStatus.DEGRADED
            if health_ratio < 0.5:
                status = IntegrationStatus.UNHEALTHY

            now = datetime.now(UTC)
            return {
                'status': status.value,
                'healthy_providers': healthy_providers,
                'total_providers': total_providers,
                'active_sessions': len(self._active_sessions),
                'issues': issues,
                'last_check': now
            }

        except Exception as e:
            logger.exception(f"Health check failed: {e}")
            now = datetime.now(UTC)
            return {
                'status': IntegrationStatus.UNHEALTHY.value,
                'error': str(e),
                'last_check': now
            }

    async def shutdown(self):
        """Shutdown the sandbox manager and cleanup resources."""
        # Cancel cleanup tasks
        for task in self._cleanup_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Terminate all active sessions
        session_ids = list(self._active_sessions.keys())
        for session_id in session_ids:
            await self.terminate_session(session_id)


class TrackedSandboxSession:
    """A wrapper around SandboxSession that tracks usage metrics."""

    def __init__(self, session: SandboxSession, session_id: str, manager: SandboxManager):
        self.session = session
        self.session_id = session_id
        self.manager = manager

    def __getattr__(self, name):
        """Delegate attribute access to the wrapped session."""
        return getattr(self.session, name)

    async def execute(self, command: str, timeout: int | None = None):
        """Execute command with metrics tracking."""
        result = await self.session.execute(command, timeout)

        # Update metrics
        session_info = self.manager._active_sessions.get(self.session_id)
        if session_info:
            session_info['metrics']['commands_executed'] += 1

        return result

    async def upload_file(self, path: str, content: str):
        """Upload file with metrics tracking."""
        await self.session.upload_file(path, content)

        # Update metrics
        session_info = self.manager._active_sessions.get(self.session_id)
        if session_info:
            session_info['metrics']['files_uploaded'] += 1

    async def download_file(self, path: str) -> str:
        """Download file with metrics tracking."""
        content = await self.session.download_file(path)

        # Update metrics
        session_info = self.manager._active_sessions.get(self.session_id)
        if session_info:
            session_info['metrics']['files_downloaded'] += 1

        return content

    async def create_snapshot(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        """Create snapshot with metrics tracking."""
        snapshot_id = await self.session.create_snapshot(name, metadata)

        # Update metrics
        session_info = self.manager._active_sessions.get(self.session_id)
        if session_info:
            session_info['metrics']['snapshots_created'] += 1

        return snapshot_id

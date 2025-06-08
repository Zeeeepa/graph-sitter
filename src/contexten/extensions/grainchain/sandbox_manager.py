"""Sandbox management for Grainchain integration.

This module provides high-level sandbox management functionality
including session handling, resource optimization, and metrics.
"""

import asyncio
import logging
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional, Set, cast

from .config import GrainchainIntegrationConfig
from .error_handling import (
    CircuitBreakerConfig,
    ErrorCategory,
    ErrorContext,
    ErrorHandler,
    ErrorSeverity,
    RetryConfig,
    RetryableError,
    with_retry,
)
from .grainchain_client import GrainchainClient, SandboxSession
from .grainchain_types import (
    IntegrationStatus,
    SandboxConfig,
    SandboxMetrics,
    SandboxProvider,
)

logger = logging.getLogger(__name__)

class SandboxError(Exception, RetryableError):
    """Base exception for sandbox errors."""
    pass

class ResourceLimitError(SandboxError):
    """Raised when resource limits are exceeded."""
    pass

class SandboxManager:
    """High-level sandbox management.

    Handles sandbox lifecycle, resource optimization, and metrics
    across multiple providers.
    """

    def __init__(self, config: Optional[GrainchainIntegrationConfig] = None) -> None:
        """Initialize the sandbox manager."""
        from .config import get_grainchain_config

        self.config = config or get_grainchain_config()
        self._client = GrainchainClient(self.config)
        self._active_sessions: Dict[str, SandboxSession] = {}
        self._session_metrics: Dict[str, Dict[str, Any]] = {}
        self._resource_limits: Dict[str, Any] = {
            "max_concurrent_sandboxes": getattr(self.config, "max_concurrent_sandboxes", 10),
            "sandbox_timeout": getattr(self.config, "sandbox_timeout", 3600),
            "memory_limit": "4GB",
            "cpu_limit": 2.0
        }
        self._error_handler = ErrorHandler()
        self._setup_error_handling()

    def _setup_error_handling(self) -> None:
        """Set up error handling and circuit breakers."""
        # Create circuit breaker for resource management
        self._error_handler.create_circuit_breaker(
            "resource_management",
            CircuitBreakerConfig(
                failure_threshold=5,
                reset_timeout=300.0,  # 5 minutes
                half_open_timeout=60.0
            )
        )

        # Register error handlers
        self._error_handler.register_error_handler(
            ErrorCategory.RESOURCE,
            self._handle_resource_error
        )

        # Register recovery procedures
        self._error_handler.register_recovery_procedure(
            ErrorCategory.RESOURCE,
            self._recover_resources
        )

    def _handle_resource_error(self, context: ErrorContext) -> None:
        """Handle resource-related errors."""
        logger.error(
            f"Resource error in sandbox operation: {context.error}",
            extra={
                "operation": context.operation,
                "resource_id": context.resource_id,
                "provider": context.provider
            }
        )

    def _recover_resources(self) -> None:
        """Attempt to recover from resource errors."""
        asyncio.create_task(self.optimize_resources())

    @with_retry(
        retry_config=RetryConfig(max_attempts=3),
        retryable_errors=[SandboxError, ResourceLimitError]
    )
    @asynccontextmanager
    async def create_session(
        self,
        config: Optional[SandboxConfig] = None,
        provider_id: Optional[str] = None,
        auto_cleanup: bool = True
    ) -> AsyncIterator[SandboxSession]:
        """Create a new sandbox session.

        Args:
            config: Optional sandbox configuration
            provider_id: Optional specific provider to use
            auto_cleanup: Whether to automatically cleanup the sandbox

        Returns:
            SandboxSession context manager
        """
        if len(self._active_sessions) >= self._resource_limits["max_concurrent_sandboxes"]:
            try:
                await self.optimize_resources()
            except Exception as e:
                context = ErrorContext(
                    error=e,
                    severity=ErrorSeverity.ERROR,
                    category=ErrorCategory.RESOURCE,
                    operation="optimize_resources"
                )
                self._error_handler.handle_error(e, context)
                raise ResourceLimitError("Failed to optimize resources") from e

        # Select optimal provider
        try:
            selected_provider = await self._select_optimal_provider(
                provider_id=provider_id,
                config=config
            )
        except Exception as e:
            context = ErrorContext(
                error=e,
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.PROVIDER,
                operation="select_provider"
            )
            self._error_handler.handle_error(e, context)
            raise SandboxError("Failed to select provider") from e

        # Create sandbox session
        try:
            async with self._client.create_sandbox(config, selected_provider) as session:
                session_id = session.sandbox_id
                self._active_sessions[session_id] = session
                self._session_metrics[session_id] = {
                    "created_at": datetime.now(UTC),
                    "provider": selected_provider,
                    "config": config.__dict__ if config else {},
                    "metrics": {}
                }

                try:
                    yield session
                finally:
                    if auto_cleanup:
                        try:
                            await self._cleanup_session(session_id)
                        except Exception as e:
                            context = ErrorContext(
                                error=e,
                                severity=ErrorSeverity.WARNING,
                                category=ErrorCategory.RESOURCE,
                                operation="cleanup_session",
                                resource_id=session_id
                            )
                            self._error_handler.handle_error(e, context)

        except Exception as e:
            context = ErrorContext(
                error=e,
                severity=ErrorSeverity.ERROR,
                category=ErrorCategory.PROVIDER,
                provider=selected_provider.value,
                operation="create_sandbox"
            )
            self._error_handler.handle_error(e, context)
            raise SandboxError("Failed to create sandbox session") from e

    async def _cleanup_session(self, session_id: str) -> None:
        """Clean up a sandbox session."""
        self._active_sessions.pop(session_id, None)
        self._session_metrics.pop(session_id, None)

    async def _select_optimal_provider(
        self,
        provider_id: Optional[str] = None,
        config: Optional[SandboxConfig] = None
    ) -> SandboxProvider:
        """Select the optimal provider based on current conditions."""
        if provider_id:
            return SandboxProvider(provider_id)

        # Get provider metrics
        metrics = await self._client.get_metrics()

        # Calculate provider scores
        scores: Dict[SandboxProvider, float] = {}

        for provider, provider_metrics in metrics.items():
            # Base score
            score: float = 100.0

            # Adjust for resource utilization
            utilization = provider_metrics.resource_utilization.get("cpu", 0.0)
            score -= utilization * 20  # Penalize high utilization

            # Adjust for error rate
            error_rate = float(provider_metrics.error_count) / max(provider_metrics.total_sandboxes_created, 1)
            score -= error_rate * 30  # Penalize high error rates

            # Adjust for cost
            if provider_metrics.cost_per_hour:
                score -= provider_metrics.cost_per_hour * 10  # Penalize high cost

            # Adjust for startup time
            if provider_metrics.average_startup_time:
                score -= provider_metrics.average_startup_time  # Penalize slow startup

            # Adjust for success rate
            score += provider_metrics.success_rate * 20  # Reward high success rate

            scores[provider] = score

        # Select provider with highest score
        if not scores:
            return self.config.default_provider

        return max(scores.items(), key=lambda x: x[1])[0]

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get information about all active sessions."""
        sessions = []

        for session_id, session in self._active_sessions.items():
            metrics = self._session_metrics[session_id]
            sessions.append({
                "session_id": session_id,
                "provider": metrics["provider"],
                "created_at": metrics["created_at"],
                "config": metrics["config"],
                "metrics": metrics["metrics"]
            })

        return sessions

    async def get_resource_utilization(self) -> Dict[str, Any]:
        """Get current resource utilization metrics."""
        utilization: Dict[str, Any] = {
            "active_sessions": len(self._active_sessions),
            "providers": {},
            "total_memory": 0.0,
            "total_cpu": 0.0
        }

        # Get provider metrics
        metrics = await self._client.get_metrics()

        for provider, provider_metrics in metrics.items():
            provider_util = provider_metrics.resource_utilization
            utilization["providers"][provider.value] = provider_util
            utilization["total_memory"] += float(provider_util.get("memory", 0.0))
            utilization["total_cpu"] += float(provider_util.get("cpu", 0.0))

        return utilization

    async def optimize_resources(self) -> None:
        """Optimize resource usage across providers."""
        # Get current utilization
        utilization = await self.get_resource_utilization()

        # Check if we need to optimize
        if utilization["active_sessions"] < self._resource_limits["max_concurrent_sandboxes"]:
            return

        # Get session metrics
        sessions = await self.get_active_sessions()

        # Sort by age and resource usage
        sorted_sessions = sorted(
            sessions,
            key=lambda x: (
                x["created_at"],
                float(x["metrics"].get("memory", 0.0)),
                float(x["metrics"].get("cpu", 0.0))
            )
        )

        # Clean up oldest sessions until we're under limits
        while utilization["active_sessions"] >= self._resource_limits["max_concurrent_sandboxes"]:
            if not sorted_sessions:
                break

            oldest_session = sorted_sessions.pop(0)
            session_id = oldest_session["session_id"]

            if session_id in self._active_sessions:
                self._active_sessions.pop(session_id, None)
                self._session_metrics.pop(session_id, None)
                utilization["active_sessions"] -= 1

    async def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the sandbox management system."""
        try:
            available_providers = await self._client.get_available_providers()
            provider_metrics = await self._client.get_metrics()

            # Calculate overall health
            total_providers = len(self.config.get_enabled_providers())
            available_count = len(available_providers)
            health_ratio = available_count / total_providers

            issues = []

            if health_ratio < 0.5:
                issues.append("More than half of providers are unavailable")

            if len(self._active_sessions) > self._resource_limits["max_concurrent_sandboxes"]:
                issues.append("Session limit exceeded")

            status = IntegrationStatus.HEALTHY if health_ratio >= 0.8 and not issues else IntegrationStatus.DEGRADED

            return {
                "status": status,
                "available_providers": [p.value for p in available_providers],
                "total_providers": total_providers,
                "active_sessions": len(self._active_sessions),
                "issues": issues,
                "provider_metrics": {
                    p.value: {
                        "active_sandboxes": m.active_sandboxes,
                        "success_rate": m.success_rate,
                        "error_count": m.error_count
                    } for p, m in provider_metrics.items()
                }
            }

        except Exception as e:
            logger.exception("Failed to get health status")
            return {
                "status": IntegrationStatus.ERROR,
                "error": str(e),
                "issues": ["Failed to get health status"]
            }

    async def shutdown(self) -> None:
        """Shutdown the sandbox manager."""
        # Clean up active sessions
        for session_id in list(self._active_sessions.keys()):
            try:
                await self._client.destroy_sandbox(session_id)
            except Exception as e:
                logger.exception(f"Failed to destroy sandbox {session_id}: {e}")

        self._active_sessions.clear()
        self._session_metrics.clear()

    async def cleanup_inactive_sessions(self, max_age: int = 3600) -> None:
        """Clean up inactive sessions older than max_age seconds."""
        now = datetime.now(UTC)
        sessions = await self.get_active_sessions()

        for session in sessions:
            age = (now - session["created_at"]).total_seconds()
            if age > max_age:
                session_id = session["session_id"]
                if session_id in self._active_sessions:
                    try:
                        await self._client.destroy_sandbox(session_id)
                    except Exception as e:
                        logger.exception(f"Failed to destroy sandbox {session_id}: {e}")
                    self._active_sessions.pop(session_id, None)
                    self._session_metrics.pop(session_id, None)

    async def terminate_session(self, session_id: str) -> bool:
        """Terminate a specific session."""
        if session_id not in self._active_sessions:
            return False

        try:
            await self._client.destroy_sandbox(session_id)
            self._active_sessions.pop(session_id, None)
            self._session_metrics.pop(session_id, None)
            return True
        except Exception as e:
            logger.exception(f"Failed to terminate session {session_id}: {e}")
            return False


class TrackedSandboxSession:
    """Sandbox session with tracking."""

    def __init__(
        self,
        session: SandboxSession,
        session_id: str,
        manager: "SandboxManager"
    ) -> None:
        """Initialize the tracked session."""
        self.session = session
        self.session_id = session_id
        self._manager = manager

    async def execute(self, command: str, timeout: Optional[int] = None) -> Dict[str, Any]:
        """Execute a command in the sandbox."""
        result = await self.session.execute(command, timeout)
        self._manager._session_metrics[self.session_id]["metrics"]["commands_executed"] = (
            self._manager._session_metrics[self.session_id]["metrics"].get("commands_executed", 0) + 1
        )
        return cast(Dict[str, Any], result)

    async def upload_file(self, local_path: str, remote_path: str) -> None:
        """Upload a file to the sandbox."""
        await self.session.upload_file(local_path, remote_path)
        self._manager._session_metrics[self.session_id]["metrics"]["files_uploaded"] = (
            self._manager._session_metrics[self.session_id]["metrics"].get("files_uploaded", 0) + 1
        )

    async def download_file(self, remote_path: str, local_path: str) -> None:
        """Download a file from the sandbox."""
        await self.session.download_file(remote_path, local_path)
        self._manager._session_metrics[self.session_id]["metrics"]["files_downloaded"] = (
            self._manager._session_metrics[self.session_id]["metrics"].get("files_downloaded", 0) + 1
        )

    async def create_snapshot(self, name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create a snapshot of the sandbox."""
        snapshot_id = await self.session.create_snapshot(name, metadata)
        self._manager._session_metrics[self.session_id]["metrics"]["snapshots_created"] = (
            self._manager._session_metrics[self.session_id]["metrics"].get("snapshots_created", 0) + 1
        )
        return cast(str, snapshot_id)

    async def restore_snapshot(self, snapshot_id: str) -> None:
        """Restore a snapshot in the sandbox."""
        await self.session.restore_snapshot(snapshot_id)
        self._manager._session_metrics[self.session_id]["metrics"]["snapshots_restored"] = (
            self._manager._session_metrics[self.session_id]["metrics"].get("snapshots_restored", 0) + 1
        )

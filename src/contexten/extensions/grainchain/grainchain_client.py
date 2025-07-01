"""Grainchain client for unified sandbox management.

This module provides a high-level client interface to the Grainchain
sandbox system with provider abstraction and automatic fallback.
"""

import logging
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from .config import GrainchainIntegrationConfig
from .grainchain_types import ExecutionResult, GrainchainEvent, GrainchainEventType, SandboxConfig, SandboxMetrics, SandboxProvider, SnapshotInfo

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class GrainchainClientError(Exception):
    """Base exception for Grainchain client errors."""
    pass


class ProviderUnavailableError(GrainchainClientError):
    """Raised when no providers are available."""
    pass


class SandboxCreationError(GrainchainClientError):
    """Raised when sandbox creation fails."""
    pass


class GrainchainClient:
    """High-level client for Grainchain sandbox operations.

    Provides a unified interface to multiple sandbox providers with
    automatic fallback, load balancing, and error handling.
    """

    def __init__(self, config: GrainchainIntegrationConfig | None = None):
        """Initialize the Grainchain client."""
        from .config import get_grainchain_config

        self.config = config or get_grainchain_config()
        self._provider_clients: dict[SandboxProvider, Any] = {}
        self._active_sandboxes: dict[str, dict[str, Any]] = {}
        self._metrics: dict[SandboxProvider, SandboxMetrics] = {}
        self._event_handlers: list[Callable] = []

        # Initialize provider clients
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize clients for enabled providers."""
        for provider in self.config.get_enabled_providers():
            try:
                client = self._create_provider_client(provider)
                self._provider_clients[provider] = client
                logger.info(f"Initialized {provider.value} provider client")
            except Exception as e:
                logger.exception(f"Failed to initialize {provider.value} provider: {e}")

    def _create_provider_client(self, provider: SandboxProvider):
        """Create a client for the specified provider."""
        # This would import and create the actual provider clients
        # For now, we'll create mock clients

        if provider == SandboxProvider.LOCAL:
            return MockLocalClient(self.config.get_provider_config(provider))
        elif provider == SandboxProvider.E2B:
            return MockE2BClient(self.config.get_provider_config(provider))
        elif provider == SandboxProvider.DAYTONA:
            return MockDaytonaClient(self.config.get_provider_config(provider))
        elif provider == SandboxProvider.MORPH:
            return MockMorphClient(self.config.get_provider_config(provider))
        else:
            msg = f"Unsupported provider: {provider}"
            raise ValueError(msg)

    async def get_available_providers(self) -> list[SandboxProvider]:
        """Get list of currently available providers."""
        available = []

        for provider, client in self._provider_clients.items():
            try:
                if await client.health_check():
                    available.append(provider)
            except Exception as e:
                logger.warning(f"Health check failed for {provider.value}: {e}")

        return available

    async def select_provider(
        self,
        preferred_provider: SandboxProvider | None = None,
        requirements: dict[str, Any] | None = None
    ) -> SandboxProvider:
        """Select the best available provider based on preferences and requirements."""
        available_providers = await self.get_available_providers()

        if not available_providers:
            msg = "No providers are currently available"
            raise ProviderUnavailableError(msg)

        # Try preferred provider first
        if preferred_provider and preferred_provider in available_providers:
            return preferred_provider

        # Try default provider
        if self.config.default_provider in available_providers:
            return self.config.default_provider

        # Use first available fallback provider
        for fallback in self.config.fallback_providers:
            if fallback in available_providers:
                return fallback

        # Use any available provider
        return available_providers[0]

    @asynccontextmanager
    async def create_sandbox(
        self,
        config: SandboxConfig | None = None,
        provider: SandboxProvider | None = None
    ) -> AbstractAsyncContextManager['SandboxSession']:
        """Create a sandbox session with automatic cleanup.

        Args:
            config: Sandbox configuration
            provider: Preferred provider (will auto-select if None)

        Returns:
            SandboxSession context manager
        """
        if config is None:
            config = SandboxConfig()

        # Select provider
        selected_provider = await self.select_provider(
            preferred_provider=provider or config.provider
        )

        # Get provider client
        client = self._provider_clients.get(selected_provider)
        if not client:
            msg = f"Provider {selected_provider.value} not available"
            raise ProviderUnavailableError(msg)

        # Create sandbox
        try:
            sandbox_id = await client.create_sandbox(config)
            session = SandboxSession(
                sandbox_id=sandbox_id,
                provider=selected_provider,
                client=client,
                grainchain_client=self
            )

            # Track active sandbox
            self._active_sandboxes[sandbox_id] = {
                'provider': selected_provider,
                'created_at': datetime.now(UTC),
                'config': config
            }

            # Emit event
            event = GrainchainEvent(
                event_type=GrainchainEventType.SANDBOX_CREATED,
                timestamp=datetime.now(UTC),
                source="grainchain_client",
                data={
                    'sandbox_id': sandbox_id,
                    'provider': selected_provider.value,
                    'config': config.__dict__
                }
            )

            for handler in self._event_handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.exception(f"Event handler failed: {e}")

            try:
                yield session
            finally:
                # Cleanup sandbox
                try:
                    await client.destroy_sandbox(sandbox_id)

                    # Remove from tracking
                    self._active_sandboxes.pop(sandbox_id, None)

                    # Emit event
                    event = GrainchainEvent(
                        event_type=GrainchainEventType.SANDBOX_DESTROYED,
                        timestamp=datetime.now(UTC),
                        source="grainchain_client",
                        data={
                            'sandbox_id': sandbox_id,
                            'provider': selected_provider.value
                        }
                    )

                    for handler in self._event_handlers:
                        try:
                            await handler(event)
                        except Exception as e:
                            logger.exception(f"Event handler failed: {e}")

                except Exception as e:
                    logger.exception(f"Failed to cleanup sandbox {sandbox_id}: {e}")

        except Exception as e:
            logger.exception(f"Failed to create sandbox with {selected_provider.value}: {e}")
            msg = f"Sandbox creation failed: {e}"
            raise SandboxCreationError(msg)

    async def list_snapshots(
        self,
        provider: SandboxProvider | None = None
    ) -> list[SnapshotInfo]:
        """List available snapshots."""
        snapshots = []

        providers_to_check = [provider] if provider else self._provider_clients.keys()

        for prov in providers_to_check:
            client = self._provider_clients.get(prov)
            if client:
                try:
                    provider_snapshots = await client.list_snapshots()
                    snapshots.extend(provider_snapshots)
                except Exception as e:
                    logger.exception(f"Failed to list snapshots for {prov.value}: {e}")

        return snapshots

    async def get_metrics(self) -> dict[SandboxProvider, SandboxMetrics]:
        """Get metrics for all providers."""
        metrics = {}

        for provider, client in self._provider_clients.items():
            try:
                provider_metrics = await client.get_metrics()
                metrics[provider] = provider_metrics
            except Exception as e:
                logger.exception(f"Failed to get metrics for {provider.value}: {e}")

        return metrics

    async def benchmark_providers(
        self,
        test_suite: str = "standard",
        providers: list[SandboxProvider] | None = None
    ) -> dict[SandboxProvider, dict[str, float]]:
        """Run performance benchmarks across providers."""
        if providers is None:
            providers = list(self._provider_clients.keys())

        results = {}

        for provider in providers:
            client = self._provider_clients.get(provider)
            if not client:
                continue

            try:
                benchmark_result = await client.run_benchmark(test_suite)
                results[provider] = benchmark_result
            except Exception as e:
                logger.exception(f"Benchmark failed for {provider.value}: {e}")
                results[provider] = {'error': str(e)}

        return results

    def add_event_handler(self, handler):
        """Add an event handler for Grainchain events."""
        self._event_handlers.append(handler)

    async def _emit_event(self, event_type: GrainchainEventType, data: dict[str, Any]):
        """Emit an event to all registered handlers."""
        event = GrainchainEvent(
            event_type=event_type,
            timestamp=datetime.now(UTC),
            source="grainchain_client",
            data=data
        )

        for handler in self._event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.exception(f"Event handler failed: {e}")


class SandboxSession:
    """A session representing an active sandbox.

    Provides methods for executing commands, managing files,
    and creating snapshots within the sandbox.
    """

    def __init__(
        self,
        sandbox_id: str,
        provider: SandboxProvider,
        client,
        grainchain_client: GrainchainClient
    ):
        self.sandbox_id = sandbox_id
        self.provider = provider
        self._client = client
        self._grainchain_client = grainchain_client

    async def execute(self, command: str, timeout: int | None = None) -> ExecutionResult:
        """Execute a command in the sandbox."""
        return await self._client.execute(self.sandbox_id, command, timeout)

    async def upload_file(self, path: str, content: str) -> None:
        """Upload a file to the sandbox."""
        await self._client.upload_file(self.sandbox_id, path, content)

    async def download_file(self, path: str) -> str:
        """Download a file from the sandbox."""
        return await self._client.download_file(self.sandbox_id, path)

    async def list_files(self, path: str = "/") -> list[dict[str, Any]]:
        """List files in the sandbox."""
        return await self._client.list_files(self.sandbox_id, path)

    async def create_snapshot(self, name: str, metadata: dict[str, Any] | None = None) -> str:
        """Create a snapshot of the current sandbox state."""
        snapshot_id = await self._client.create_snapshot(self.sandbox_id, name, metadata)

        # Emit event
        event = GrainchainEvent(
            event_type=GrainchainEventType.SNAPSHOT_CREATED,
            timestamp=datetime.now(UTC),
            source="grainchain_client",
            data={
                'sandbox_id': self.sandbox_id,
                'snapshot_id': snapshot_id,
                'name': name,
                'provider': self.provider.value
            }
        )

        for handler in self._grainchain_client._event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.exception(f"Event handler failed: {e}")

        return snapshot_id

    async def restore_snapshot(self, snapshot_id: str) -> None:
        """Restore the sandbox to a previous snapshot."""
        await self._client.restore_snapshot(self.sandbox_id, snapshot_id)

        # Emit event
        event = GrainchainEvent(
            event_type=GrainchainEventType.SNAPSHOT_RESTORED,
            timestamp=datetime.now(UTC),
            source="grainchain_client",
            data={
                'sandbox_id': self.sandbox_id,
                'snapshot_id': snapshot_id,
                'provider': self.provider.value
            }
        )

        for handler in self._grainchain_client._event_handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.exception(f"Event handler failed: {e}")


# Mock provider clients for demonstration
# In a real implementation, these would be actual Grainchain provider clients

class MockProviderClient:
    """Base mock provider client."""

    def __init__(self, config):
        self.config = config

    async def health_check(self) -> bool:
        return True

    async def create_sandbox(self, config: SandboxConfig) -> str:
        return f"sandbox_{self.__class__.__name__}_{datetime.now(UTC).timestamp()}"

    async def destroy_sandbox(self, sandbox_id: str) -> None:
        pass

    async def execute(self, sandbox_id: str, command: str, timeout: int | None = None) -> ExecutionResult:
        return ExecutionResult(
            command=command,
            exit_code=0,
            stdout="Mock output",
            stderr="",
            duration=1.0,
            timestamp=datetime.now(UTC),
            sandbox_id=sandbox_id,
            provider=SandboxProvider.LOCAL
        )

    async def upload_file(self, sandbox_id: str, path: str, content: str) -> None:
        pass

    async def download_file(self, sandbox_id: str, path: str) -> str:
        return "Mock file content"

    async def list_files(self, sandbox_id: str, path: str) -> list[dict[str, Any]]:
        return [{"name": "mock_file.txt", "size": 100, "type": "file"}]

    async def create_snapshot(self, sandbox_id: str, name: str, metadata: dict[str, Any] | None = None) -> str:
        return f"snapshot_{name}_{datetime.now(UTC).timestamp()}"

    async def restore_snapshot(self, sandbox_id: str, snapshot_id: str) -> None:
        pass

    async def list_snapshots(self) -> list[SnapshotInfo]:
        return []

    async def get_metrics(self) -> SandboxMetrics:
        return SandboxMetrics(
            provider=SandboxProvider.LOCAL,
            total_sandboxes_created=10,
            active_sandboxes=2,
            total_execution_time=3600.0,
            average_startup_time=5.0,
            success_rate=0.95,
            cost_total=10.0,
            cost_per_hour=1.0,
            resource_utilization={"cpu": 0.5, "memory": 0.6},
            error_count=1,
            last_updated=datetime.now(UTC)
        )

    async def run_benchmark(self, test_suite: str) -> dict[str, float]:
        return {
            "startup_time": 5.0,
            "execution_time": 10.0,
            "memory_usage": 512.0,
            "cpu_usage": 50.0
        }


class MockLocalClient(MockProviderClient):
    """Mock local provider client."""
    pass


class MockE2BClient(MockProviderClient):
    """Mock E2B provider client."""
    pass


class MockDaytonaClient(MockProviderClient):
    """Mock Daytona provider client."""
    pass


class MockMorphClient(MockProviderClient):
    """Mock Morph provider client."""
    pass

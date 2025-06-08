"""Grainchain client for unified sandbox management.

This module provides a high-level client interface to the Grainchain
sandbox system with provider abstraction and automatic fallback.
"""

import logging
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, AsyncIterator, Optional, Dict

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
        self._provider_clients: dict[SandboxProvider, MockProviderClient] = {}
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

    def _create_provider_client(self, provider: SandboxProvider) -> MockProviderClient:
        """Create a provider client.

        Args:
            provider: The provider to create a client for

        Returns:
            MockProviderClient: The provider client
        """
        if provider not in self._provider_clients:
            client = {
                SandboxProvider.LOCAL: MockLocalClient,
                SandboxProvider.E2B: MockE2BClient,
                SandboxProvider.DAYTONA: MockDaytonaClient,
                SandboxProvider.MORPH: MockMorphClient
            }[provider]()
            self._provider_clients[provider] = client
        return self._provider_clients[provider]

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
        config: Optional[SandboxConfig] = None,
        provider: Optional[SandboxProvider] = None,
    ) -> AsyncIterator[SandboxSession]:
        """Create a new sandbox session.

        Args:
            config: Optional sandbox configuration
            provider: Optional sandbox provider

        Returns:
            AsyncIterator[SandboxSession]: The sandbox session
        """
        session = None
        try:
            session = await self._create_sandbox_session(config, provider)
            yield session
        finally:
            if session:
                await self._cleanup_sandbox_session(session)

    async def _create_sandbox_session(
        self,
        config: Optional[SandboxConfig] = None,
        provider: Optional[SandboxProvider] = None,
    ) -> SandboxSession:
        """Create a new sandbox session."""
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

            return session

        except Exception as e:
            logger.exception(f"Failed to create sandbox with {selected_provider.value}: {e}")
            msg = f"Sandbox creation failed: {e}"
            raise SandboxCreationError(msg)

    async def list_snapshots(
        self,
        sandbox_id: str
    ) -> list[SnapshotInfo]:
        """List snapshots for a sandbox.

        Args:
            sandbox_id: ID of the sandbox

        Returns:
            list[SnapshotInfo]: List of snapshot information
        """
        client = self._get_provider_client(sandbox_id)
        return await client.list_snapshots(sandbox_id)

    async def get_metrics(self, sandbox_id: str) -> SandboxMetrics:
        """Get metrics for a sandbox.

        Args:
            sandbox_id: ID of the sandbox

        Returns:
            SandboxMetrics: Sandbox metrics
        """
        client = self._get_provider_client(sandbox_id)
        return await client.get_metrics(sandbox_id)

    async def benchmark_providers(
        self,
        test_suite: str = "standard",
        providers: list[SandboxProvider] | None = None
    ) -> dict[str, float]:
        """Run benchmarks on all providers.

        Returns:
            dict[str, float]: Benchmark results
        """
        if providers is None:
            providers = list(self._provider_clients.keys())

        results: dict[str, float] = {}

        for provider in providers:
            client = self._create_provider_client(provider)
            try:
                benchmark_results = await client.run_benchmark(test_suite)
                results[provider.value] = benchmark_results.get("score", 0.0)
            except Exception as e:
                logger.exception(f"Failed to benchmark {provider.value}: {e}")
                results[provider.value] = 0.0

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

    async def _cleanup_sandbox_session(self, session: SandboxSession) -> None:
        """Clean up a sandbox session.

        Args:
            session: The sandbox session to clean up
        """
        try:
            # Get the provider client
            client = self._provider_clients.get(session.provider)
            if not client:
                raise ProviderUnavailableError(f"Provider {session.provider.value} not available")

            # Cleanup sandbox
            await client.destroy_sandbox(session.sandbox_id)

            # Emit event
            event = GrainchainEvent(
                event_type=GrainchainEventType.SANDBOX_DESTROYED,
                timestamp=datetime.now(UTC),
                source="grainchain_client",
                data={
                    'sandbox_id': session.sandbox_id,
                    'provider': session.provider.value
                }
            )

            for handler in self._event_handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.exception(f"Event handler failed: {e}")

        except Exception as e:
            logger.exception(f"Failed to cleanup sandbox {session.sandbox_id}: {e}")

    def _get_provider_client(self, sandbox_id: str) -> MockProviderClient:
        """Get the provider client for a sandbox.

        Args:
            sandbox_id: ID of the sandbox

        Returns:
            MockProviderClient: The provider client

        Raises:
            ProviderUnavailableError: If the provider is not available
        """
        # Get the sandbox info from active sandboxes
        sandbox_info = self._active_sandboxes.get(sandbox_id)
        if not sandbox_info:
            raise ProviderUnavailableError(f"Sandbox {sandbox_id} not found")

        # Get the provider client
        provider = sandbox_info['provider']
        client = self._provider_clients.get(provider)
        if not client:
            raise ProviderUnavailableError(f"Provider {provider.value} not available")

        return client


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

    async def execute(self, sandbox_id: str, command: str, timeout: int | None = None) -> ExecutionResult:
        """Execute a command in a sandbox.

        Args:
            sandbox_id: ID of the sandbox
            command: Command to execute
            timeout: Optional timeout in seconds

        Returns:
            ExecutionResult: Result of the command execution
        """
        return ExecutionResult(
            command=command,
            exit_code=0,
            stdout="Mock stdout",
            stderr="",
            duration=0.1,
            timestamp=datetime.now(UTC),
            sandbox_id=sandbox_id,
            provider=SandboxProvider.LOCAL
        )

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

    def __init__(self):
        """Initialize the mock provider client."""
        self._sandboxes: Dict[str, Any] = {}

    async def health_check(self) -> bool:
        return True

    async def create_sandbox(self, config: SandboxConfig) -> str:
        sandbox_id = f"sandbox_{self.__class__.__name__}_{datetime.now(UTC).timestamp()}"
        self._sandboxes[sandbox_id] = config
        return sandbox_id

    async def destroy_sandbox(self, sandbox_id: str) -> None:
        """Destroy a sandbox.

        Args:
            sandbox_id: ID of the sandbox to destroy
        """
        try:
            self._sandboxes.pop(sandbox_id, None)
        except Exception as e:
            logger.exception(f"Failed to destroy sandbox {sandbox_id}: {e}")
            raise

    async def execute(self, sandbox_id: str, command: str, timeout: int | None = None) -> ExecutionResult:
        return ExecutionResult(
            command=command,
            exit_code=0,
            stdout="Mock stdout",
            stderr="",
            duration=0.1,
            timestamp=datetime.now(UTC),
            sandbox_id=sandbox_id,
            provider=SandboxProvider.LOCAL
        )

    async def upload_file(self, sandbox_id: str, path: str, content: str) -> None:
        pass

    async def download_file(self, sandbox_id: str, path: str) -> str:
        return "Mock file content"

    async def create_snapshot(self, sandbox_id: str, name: str, metadata: dict[str, Any] | None = None) -> str:
        return f"snapshot_{sandbox_id}_{name}"

    async def restore_snapshot(self, sandbox_id: str, snapshot_id: str) -> None:
        pass

    async def list_snapshots(self, sandbox_id: str) -> list[SnapshotInfo]:
        return []

    async def get_metrics(self, sandbox_id: str) -> SandboxMetrics:
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

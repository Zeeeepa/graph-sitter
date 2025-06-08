"""Quality gate management for Grainchain integration.

This module provides quality gate automation with snapshot-based
testing and comprehensive reporting.
"""

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional, Set

from .config import GrainchainIntegrationConfig, get_grainchain_config
from .grainchain_types import (
    GrainchainEvent,
    GrainchainEventType,
    QualityGateResult,
    QualityGateStatus,
    QualityGateType,
    SandboxConfig,
    SandboxProvider,
    SandboxSession,
)
from .sandbox_manager import SandboxManager

logger = logging.getLogger(__name__)


@dataclass
class QualityGateDefinition:
    """Definition of a quality gate."""

    gate_type: QualityGateType
    name: str
    description: str
    provider: Optional[SandboxProvider] = None
    timeout: int = 1800
    parallel: bool = True
    dependencies: List[QualityGateType] = field(default_factory=list)
    thresholds: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize default values."""
        if self.dependencies is None:
            self.dependencies = []
        if self.thresholds is None:
            self.thresholds = {}


class QualityGateManager:
    """Quality gate management with parallel execution and reporting."""

    def __init__(self, config: Optional[GrainchainIntegrationConfig] = None) -> None:
        """Initialize the quality gate manager."""
        from .config import get_grainchain_config

        self.config = config or get_grainchain_config()
        self._sandbox_manager = SandboxManager(self.config)
        self._gate_definitions: Dict[QualityGateType, QualityGateDefinition] = {}
        self._custom_gates: Dict[str, Callable[[SandboxSession], Any]] = {}
        self._initialize_gates()

    def _initialize_gates(self) -> None:
        """Initialize default quality gates."""
        # Initialize standard gates
        for gate_type in QualityGateType:
            self._gate_definitions[gate_type] = QualityGateDefinition(
                gate_type=gate_type,
                name=gate_type.value,
                description=f"Standard {gate_type.value} gate"
            )

        # Set up dependencies
        self._gate_definitions[QualityGateType.INTEGRATION_TESTS].dependencies = [
            QualityGateType.UNIT_TESTS
        ]
        self._gate_definitions[QualityGateType.DEPLOYMENT_TEST].dependencies = [
            QualityGateType.INTEGRATION_TESTS,
            QualityGateType.SECURITY_SCAN
        ]

    def register_custom_gate(
        self,
        name: str,
        gate_func: Callable[[SandboxSession], Any]
    ) -> None:
        """Register a custom quality gate."""
        self._custom_gates[name] = gate_func

    async def run_quality_gates(
        self,
        gates: Optional[List[QualityGateType]] = None,
        parallel: bool = True,
        fail_fast: bool = True
    ) -> List[QualityGateResult]:
        """Run quality gates with dependency resolution."""
        if gates is None:
            gates = list(QualityGateType)

        # Build dependency graph
        dependency_graph = self._build_dependency_graph(gates)

        # Track execution state
        results: List[QualityGateResult] = []
        failed_gates: Set[QualityGateType] = set()

        if parallel:
            # Execute gates in parallel with dependency resolution
            results = await self._execute_gates_parallel(
                gates=gates,
                dependency_graph=dependency_graph,
                fail_fast=fail_fast
            )
        else:
            # Execute gates sequentially
            for gate in gates:
                # Check dependencies
                dependencies = dependency_graph.get(gate, [])
                if any(dep in failed_gates for dep in dependencies):
                    logger.warning(f"Skipping {gate} due to failed dependencies")
                    continue

                result = await self._execute_single_gate(gate)
                results.append(result)

                if not result.passed and fail_fast:
                    break

                if not result.passed:
                    failed_gates.add(gate)

        return results

    async def _execute_gates_parallel(
        self,
        gates: List[QualityGateType],
        dependency_graph: Dict[QualityGateType, List[QualityGateType]],
        fail_fast: bool = True
    ) -> List[QualityGateResult]:
        """Execute gates in parallel with dependency resolution."""
        results: List[QualityGateResult] = []
        completed_gates: Set[QualityGateType] = set()
        failed_gates: Set[QualityGateType] = set()

        # Create tasks for gates without dependencies
        pending_tasks: Dict[QualityGateType, asyncio.Task[QualityGateResult]] = {}
        for gate in gates:
            if not dependency_graph.get(gate, []):
                task = asyncio.create_task(self._execute_single_gate(gate))
                pending_tasks[gate] = task

        while pending_tasks:
            # Wait for any task to complete
            done, _ = await asyncio.wait(
                pending_tasks.values(),
                return_when=asyncio.FIRST_COMPLETED
            )

            # Process completed tasks
            for task in done:
                result = await task
                completed_gate = next(
                    gate for gate, t in pending_tasks.items()
                    if t == task
                )
                completed_gates.add(completed_gate)
                results.append(result)

                if not result.passed:
                    failed_gates.add(completed_gate)
                    if fail_fast:
                        # Cancel remaining tasks
                        for t in pending_tasks.values():
                            if not t.done():
                                t.cancel()
                        return results

                # Remove completed task
                pending_tasks.pop(completed_gate)

            # Schedule new tasks whose dependencies are met
            for gate in gates:
                if (
                    gate not in completed_gates
                    and gate not in pending_tasks
                    and all(dep in completed_gates for dep in dependency_graph.get(gate, []))
                    and not any(dep in failed_gates for dep in dependency_graph.get(gate, []))
                ):
                    task = asyncio.create_task(self._execute_single_gate(gate))
                    pending_tasks[gate] = task

        return results

    async def _execute_single_gate(self, gate: QualityGateType) -> QualityGateResult:
        """Execute a single quality gate."""
        logger.info(f"Executing quality gate: {gate}")
        start_time = datetime.now(UTC)

        try:
            # Get gate definition
            gate_def = self._gate_definitions.get(gate)
            if not gate_def:
                msg = f"No definition found for gate: {gate}"
                raise ValueError(msg)

            # Create sandbox for gate execution
            config = SandboxConfig(
                provider=gate_def.provider,
                timeout=gate_def.timeout
            )

            async with self._sandbox_manager.create_session(config=config) as session:
                # Execute gate logic
                result = await self._execute_gate_logic(gate, session)
                return result

        except Exception as e:
            logger.exception(f"Failed to execute gate {gate}: {e}")
            return QualityGateResult(
                gate=gate,
                passed=False,
                error=str(e),
                duration=(datetime.now(UTC) - start_time).total_seconds(),
                metrics={}
            )

    async def _execute_gate_logic(
        self,
        gate: QualityGateType,
        session: SandboxSession
    ) -> QualityGateResult:
        """Execute the specific logic for a quality gate."""
        start_time = datetime.now(UTC)

        try:
            # Execute gate-specific logic
            if gate == QualityGateType.CODE_QUALITY:
                result = await self._execute_code_quality_gate(session)
            elif gate == QualityGateType.UNIT_TESTS:
                result = await self._execute_unit_tests_gate(session)
            elif gate == QualityGateType.INTEGRATION_TESTS:
                result = await self._execute_integration_tests_gate(session)
            elif gate == QualityGateType.SECURITY_SCAN:
                result = await self._execute_security_scan_gate(session)
            elif gate == QualityGateType.PERFORMANCE_TEST:
                result = await self._execute_performance_test_gate(session)
            elif gate == QualityGateType.DEPLOYMENT_TEST:
                result = await self._execute_deployment_test_gate(session)
            else:
                # Try custom gate
                gate_name = str(gate)
                if gate_name in self._custom_gates:
                    result = await self._custom_gates[gate_name](session)
                else:
                    msg = f"Unsupported gate type: {gate}"
                    raise ValueError(msg)

            return QualityGateResult(
                gate=gate,
                passed=result.get("passed", False),
                metrics=result.get("metrics", {}),
                duration=(datetime.now(UTC) - start_time).total_seconds(),
                error=result.get("error")
            )

        except Exception as e:
            logger.exception(f"Failed to execute gate logic for {gate}: {e}")
            return QualityGateResult(
                gate=gate,
                passed=False,
                error=str(e),
                duration=(datetime.now(UTC) - start_time).total_seconds(),
                metrics={}
            )

    def _build_dependency_graph(
        self,
        gates: List[QualityGateType]
    ) -> Dict[QualityGateType, List[QualityGateType]]:
        """Build a dependency graph for the specified gates."""
        graph: Dict[QualityGateType, List[QualityGateType]] = {}

        for gate in gates:
            gate_def = self._gate_definitions.get(gate)
            if gate_def:
                # Only include dependencies that are in the requested gates
                graph[gate] = [
                    dep for dep in gate_def.dependencies
                    if dep in gates
                ]

        return graph

    async def _execute_code_quality_gate(self, session: SandboxSession) -> Dict[str, Any]:
        """Execute code quality gate."""
        result = await session.execute("ruff check . --output-format=json")
        return {
            "passed": result.exit_code == 0,
            "metrics": {
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }

    async def _execute_unit_tests_gate(self, session: SandboxSession) -> Dict[str, Any]:
        """Execute unit tests gate."""
        result = await session.execute("python -m pytest tests/unit/ -v")
        return {
            "passed": result.exit_code == 0,
            "metrics": {
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }

    async def _execute_integration_tests_gate(self, session: SandboxSession) -> Dict[str, Any]:
        """Execute integration tests gate."""
        result = await session.execute("python -m pytest tests/integration/ -v")
        return {
            "passed": result.exit_code == 0,
            "metrics": {
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }

    async def _execute_security_scan_gate(self, session: SandboxSession) -> Dict[str, Any]:
        """Execute security scan gate."""
        result = await session.execute("bandit -r . -f json")
        return {
            "passed": result.exit_code == 0,
            "metrics": {
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }

    async def _execute_performance_test_gate(self, session: SandboxSession) -> Dict[str, Any]:
        """Execute performance test gate."""
        result = await session.execute("python -m pytest tests/performance/ -v")
        return {
            "passed": result.exit_code == 0,
            "metrics": {
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }

    async def _execute_deployment_test_gate(self, session: SandboxSession) -> Dict[str, Any]:
        """Execute deployment test gate."""
        result = await session.execute("python -m pytest tests/deployment/ -v")
        return {
            "passed": result.exit_code == 0,
            "metrics": {
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        }

    def _topological_sort(self, gates: list[QualityGateType]) -> list[QualityGateType]:
        """Sort gates topologically based on dependencies."""
        graph = self._build_dependency_graph(gates)
        visited = set()
        result = []

        def visit(gate):
            if gate in visited:
                return
            visited.add(gate)

            for dep in graph.get(gate, []):
                visit(dep)

            result.append(gate)

        for gate in gates:
            visit(gate)

        return result

    async def _emit_event(self, event_type: GrainchainEventType, data: dict[str, Any]):
        """Emit a quality gate event."""
        # This would integrate with the event system
        pass


@dataclass
class QualityGateExecution:
    """Represents a quality gate execution."""
    execution_id: str
    pr_number: int | None
    commit_sha: str | None
    base_snapshot: str | None
    gates: list[QualityGateType]
    fail_fast: bool
    started_at: datetime
    completed_at: datetime | None = None
    status: str = "running"
    results: dict[QualityGateType, QualityGateResult] = None
    error_message: str | None = None

    def __post_init__(self):
        if self.results is None:
            self.results = {}

    @property
    def duration(self) -> float:
        """Get execution duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (datetime.now(UTC) - self.started_at).total_seconds()

    @property
    def all_passed(self) -> bool:
        """Check if all gates passed."""
        return all(result.passed for result in self.results.values())

    @property
    def failed_gates(self) -> list[QualityGateType]:
        """Get list of failed gates."""
        return [gate for gate, result in self.results.items() if not result.passed]

    @property
    def passed_gates(self) -> list[QualityGateType]:
        """Get list of passed gates."""
        return [gate for gate, result in self.results.items() if result.passed]

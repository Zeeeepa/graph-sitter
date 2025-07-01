from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

from .config import GrainchainIntegrationConfig
from .grainchain_types import (
    GrainchainEventType,
    QualityGateResult,
    QualityGateStatus,
    QualityGateType,
    SandboxConfig,
    SandboxProvider
)
from .sandbox_manager import SandboxManager

import asyncio
import logging
import uuid

logger = logging.getLogger(__name__)


@dataclass
class QualityGateDefinition:
    """Definition of a quality gate."""

    name: str
    description: str
    gate_types: List[QualityGateType] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 300  # 5 minutes
    retries: int = 3
    retry_delay: int = 60  # 1 minute
    required: bool = True
    enabled: bool = True
    order: int = 0

    def __post_init__(self):
        """Initialize default values."""
        if not self.gate_types:
            self.gate_types = []
        if not self.parameters:
            self.parameters = {}

    def validate(self) -> List[str]:
        """Validate the quality gate definition.

        Returns:
            List[str]: List of validation errors
        """
        errors = []

        if not self.name:
            errors.append("Name is required")

        if not self.description:
            errors.append("Description is required")

        if not self.gate_types:
            errors.append("At least one gate type is required")

        if self.timeout <= 0:
            errors.append("Timeout must be positive")

        if self.retries < 0:
            errors.append("Retries cannot be negative")

        if self.retry_delay <= 0:
            errors.append("Retry delay must be positive")

        return errors


@dataclass
class QualityGateExecution:
    """Quality gate execution details."""

    pr_number: Optional[int] = None
    commit_sha: Optional[str] = None
    base_snapshot: Optional[str] = None
    gates: List[QualityGateType] = field(default_factory=list)
    fail_fast: bool = True
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    error: Optional[str] = None
    results: List[QualityGateResult] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Get execution duration in seconds."""
        if not self.started_at or not self.completed_at:
            return 0.0
        return (self.completed_at - self.started_at).total_seconds()

    @property
    def all_passed(self) -> bool:
        """Check if all gates passed."""
        return all(result.passed for result in self.results)

    @property
    def failed_gates(self) -> List[QualityGateType]:
        """Get list of failed gates."""
        return [result.gate_type for result in self.results if not result.passed]

    @property
    def passed_gates(self) -> List[QualityGateType]:
        """Get list of passed gates."""
        return [result.gate_type for result in self.results if result.passed]


class QualityGateManager:
    """Manages quality gates and their execution."""

    def __init__(self, config: GrainchainIntegrationConfig):
        """Initialize the quality gate manager.

        Args:
            config: Integration configuration
        """
        self.config = config
        self._gates: List[QualityGateDefinition] = []
        self._executions: Dict[str, QualityGateExecution] = {}
        self._sandbox_manager = SandboxManager(config)
        self._gate_definitions: Dict[QualityGateType, QualityGateDefinition] = {}
        self._custom_gates: Dict[QualityGateType, Dict[str, Any]] = {}

        # Initialize default gates
        self._gates.extend(self._create_default_gates())

    def _create_default_gates(self) -> List[QualityGateDefinition]:
        """Create default quality gates.

        Returns:
            List[QualityGateDefinition]: List of default quality gates
        """
        return [
            QualityGateDefinition(
                name="Code Quality",
                description="Run code quality checks",
                gate_types=[QualityGateType.CODE_QUALITY],
                parameters={
                    'tools': ['flake8', 'pylint'],
                    'config_files': ['.flake8', '.pylintrc']
                }
            ),
            QualityGateDefinition(
                name="Unit Tests",
                description="Run unit tests",
                gate_types=[QualityGateType.UNIT_TESTS],
                parameters={
                    'test_runner': 'pytest',
                    'test_dir': 'tests/unit'
                }
            ),
            QualityGateDefinition(
                name="Integration Tests",
                description="Run integration tests",
                gate_types=[QualityGateType.INTEGRATION_TESTS],
                parameters={
                    'test_runner': 'pytest',
                    'test_dir': 'tests/integration'
                }
            ),
            QualityGateDefinition(
                name="Security Scan",
                description="Run security scan",
                gate_types=[QualityGateType.SECURITY_SCAN],
                parameters={
                    'scanner': 'bandit',
                    'config_file': '.bandit'
                }
            ),
            QualityGateDefinition(
                name="Performance Tests",
                description="Run performance tests",
                gate_types=[QualityGateType.PERFORMANCE_TEST],
                parameters={
                    'test_runner': 'locust',
                    'test_file': 'locustfile.py'
                }
            )
        ]

    def register_custom_gate(self, gate: QualityGateDefinition) -> None:
        """Register a custom quality gate.

        Args:
            gate: Quality gate definition
        """
        self._gates.append(gate)

    async def run_quality_gates(self, pr_number: Optional[int] = None) -> None:
        """Run quality gates.

        Args:
            pr_number: Optional PR number
        """
        execution = QualityGateExecution(
            pr_number=pr_number,
            started_at=datetime.now(UTC)
        )

        try:
            # Run each gate
            for gate in self._gates:
                if not gate.enabled:
                    continue

                result = await self._run_gate(gate, execution)
                execution.results.append(result)

                if result.status == QualityGateStatus.FAILED and gate.required:
                    execution.status = "failed"
                    execution.error = f"Required gate {gate.name} failed"
                    break

            if execution.status != "failed":
                execution.status = "passed"

        except Exception as e:
            logger.exception(f"Failed to run quality gates: {e}")
            execution.status = "error"
            execution.error = str(e)

        finally:
            execution.completed_at = datetime.now(UTC)

    async def _run_gate(self, gate: QualityGateDefinition, execution: QualityGateExecution) -> QualityGateResult:
        """Run a single quality gate."""
        start_time = datetime.now(UTC)

        try:
            # Create sandbox configuration
            sandbox_config = SandboxConfig(
                provider=SandboxProvider.LOCAL,
                cpu_limit=2.0,
                memory_limit="4096MB",  # 4GB in MB
                environment_vars={
                    "CI": "true",
                    "QUALITY_GATE": gate.name,
                    "PR_NUMBER": str(execution.pr_number) if execution.pr_number else "",
                    "COMMIT_SHA": execution.commit_sha or ""
                }
            )

            # Create sandbox session
            async with self._sandbox_manager.create_session(sandbox_config) as session:
                # Restore base snapshot if provided
                if execution.base_snapshot:
                    await session.restore_snapshot(execution.base_snapshot)

                # Execute gate-specific logic
                result = await self._execute_gate_logic(session, gate)

                # Create snapshot of gate execution
                snapshot_id = await session.create_snapshot(
                    name=f"gate_{gate.name}_{execution.pr_number}",
                    metadata={
                        "gate_name": gate.name,
                        "pr_number": execution.pr_number,
                        "status": result.status,
                        "passed": result.passed
                    }
                )

                return result

        except Exception as e:
            duration = (datetime.now(UTC) - start_time).total_seconds()
            return QualityGateResult(
                gate_type=gate.gate_types[0],
                status=QualityGateStatus.ERROR,
                passed=False,
                duration=duration,
                timestamp=datetime.now(UTC),
                sandbox_id="",
                error_message=str(e)
            )

    async def _execute_gate_logic(self, session: Any, gate: QualityGateDefinition) -> QualityGateResult:
        """Execute gate-specific logic.

        Args:
            session: Sandbox session
            gate: Quality gate definition

        Returns:
            QualityGateResult: Result of the gate execution
        """
        start_time = datetime.now(UTC)

        try:
            # Execute gate-specific commands
            result = await session.execute(
                f"python -m pytest {gate.parameters.get('test_dir', 'tests')} -v",
                timeout=gate.timeout
            )

            # Check if tests passed
            passed = result.exit_code == 0

            return QualityGateResult(
                gate_type=gate.gate_types[0],
                status=QualityGateStatus.PASSED if passed else QualityGateStatus.FAILED,
                passed=passed,
                duration=(datetime.now(UTC) - start_time).total_seconds(),
                timestamp=datetime.now(UTC),
                sandbox_id=session.session_id,
                results={"test_output": result.stdout}
            )

        except Exception as e:
            duration = (datetime.now(UTC) - start_time).total_seconds()
            return QualityGateResult(
                gate_type=gate.gate_types[0],
                status=QualityGateStatus.ERROR,
                passed=False,
                duration=duration,
                timestamp=datetime.now(UTC),
                sandbox_id=session.session_id,
                error_message=str(e)
            )


"""
Quality gates implementation for Grainchain integration.

This module provides comprehensive quality gate automation with snapshot-based
reproducible environments and parallel execution capabilities.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass

from .types import (
    QualityGateType, QualityGateStatus, QualityGateResult,
    SandboxProvider, SandboxConfig, GrainchainEvent, GrainchainEventType
)
from .config import GrainchainIntegrationConfig
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
    dependencies: List[QualityGateType] = None
    config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.config is None:
            self.config = {}


class QualityGateManager:
    """
    Manages quality gate execution with snapshot-based reproducible environments.
    
    Provides automated quality gate execution, parallel processing,
    and comprehensive reporting for CI/CD integration.
    """
    
    def __init__(self, config: Optional[GrainchainIntegrationConfig] = None):
        """Initialize the quality gate manager."""
        from .config import get_grainchain_config
        
        self.config = config or get_grainchain_config()
        self.sandbox_manager = SandboxManager(self.config)
        
        # Gate definitions
        self._gate_definitions = self._create_default_gates()
        self._custom_gates = {}
        
        # Execution tracking
        self._active_executions = {}
        self._execution_history = []
    
    def _create_default_gates(self) -> Dict[QualityGateType, QualityGateDefinition]:
        """Create default quality gate definitions."""
        return {
            QualityGateType.CODE_QUALITY: QualityGateDefinition(
                gate_type=QualityGateType.CODE_QUALITY,
                name="Code Quality",
                description="Static code analysis, linting, and complexity checks",
                provider=SandboxProvider.LOCAL,  # Fast for static analysis
                timeout=600,
                parallel=True,
                config={
                    "tools": ["ruff", "mypy", "bandit", "radon"],
                    "thresholds": {
                        "complexity": 10,
                        "coverage": 80,
                        "security_issues": 0
                    }
                }
            ),
            
            QualityGateType.UNIT_TESTS: QualityGateDefinition(
                gate_type=QualityGateType.UNIT_TESTS,
                name="Unit Tests",
                description="Fast unit test execution with coverage analysis",
                provider=SandboxProvider.LOCAL,  # Fast for unit tests
                timeout=900,
                parallel=True,
                config={
                    "test_command": "python -m pytest tests/unit/ -v --cov=. --cov-report=json",
                    "coverage_threshold": 80
                }
            ),
            
            QualityGateType.INTEGRATION_TESTS: QualityGateDefinition(
                gate_type=QualityGateType.INTEGRATION_TESTS,
                name="Integration Tests",
                description="Integration tests with external services",
                provider=SandboxProvider.E2B,  # Cloud for integration
                timeout=1800,
                parallel=True,
                dependencies=[QualityGateType.UNIT_TESTS],
                config={
                    "test_command": "python -m pytest tests/integration/ -v",
                    "services": ["postgres", "redis"],
                    "setup_script": "docker-compose up -d"
                }
            ),
            
            QualityGateType.SECURITY_SCAN: QualityGateDefinition(
                gate_type=QualityGateType.SECURITY_SCAN,
                name="Security Scan",
                description="Comprehensive security analysis",
                provider=SandboxProvider.DAYTONA,  # Isolated for security
                timeout=2400,
                parallel=True,
                config={
                    "tools": ["semgrep", "safety", "trivy", "checkov"],
                    "thresholds": {
                        "critical_issues": 0,
                        "high_issues": 2
                    }
                }
            ),
            
            QualityGateType.PERFORMANCE_TEST: QualityGateDefinition(
                gate_type=QualityGateType.PERFORMANCE_TEST,
                name="Performance Tests",
                description="Performance and load testing",
                provider=SandboxProvider.MORPH,  # Fast startup for perf tests
                timeout=3600,
                parallel=False,  # Resource intensive
                dependencies=[QualityGateType.INTEGRATION_TESTS],
                config={
                    "load_test_command": "locust -f locustfile.py --headless -u 50 -r 10 -t 60s",
                    "benchmark_command": "python -m pytest tests/performance/ --benchmark-json=results.json",
                    "thresholds": {
                        "response_time_p95": 500,  # ms
                        "error_rate": 0.01  # 1%
                    }
                }
            ),
            
            QualityGateType.DEPLOYMENT_TEST: QualityGateDefinition(
                gate_type=QualityGateType.DEPLOYMENT_TEST,
                name="Deployment Test",
                description="End-to-end deployment validation",
                provider=SandboxProvider.E2B,
                timeout=1800,
                parallel=False,
                dependencies=[QualityGateType.INTEGRATION_TESTS],
                config={
                    "deploy_command": "./deploy-test.sh",
                    "health_check_url": "http://localhost:8000/health",
                    "smoke_tests": "python -m pytest tests/smoke/ -v"
                }
            )
        }
    
    def register_custom_gate(
        self,
        gate_type: QualityGateType,
        executor: Callable,
        definition: QualityGateDefinition
    ):
        """Register a custom quality gate."""
        self._custom_gates[gate_type] = {
            'definition': definition,
            'executor': executor
        }
    
    async def run_quality_gates(
        self,
        pr_number: Optional[int] = None,
        commit_sha: Optional[str] = None,
        base_snapshot: Optional[str] = None,
        gates: Optional[List[QualityGateType]] = None,
        fail_fast: bool = None
    ) -> 'QualityGateExecution':
        """
        Run quality gates with snapshot-based isolation.
        
        Args:
            pr_number: PR number for tracking
            commit_sha: Commit SHA for tracking
            base_snapshot: Base snapshot to restore from
            gates: Specific gates to run (defaults to configured gates)
            fail_fast: Stop on first failure (defaults to config)
            
        Returns:
            QualityGateExecution with results
        """
        if gates is None:
            gates = self.config.quality_gates.gates
        
        if fail_fast is None:
            fail_fast = self.config.quality_gates.fail_fast
        
        execution_id = f"qg_{datetime.utcnow().timestamp()}"
        
        execution = QualityGateExecution(
            execution_id=execution_id,
            pr_number=pr_number,
            commit_sha=commit_sha,
            base_snapshot=base_snapshot,
            gates=gates,
            fail_fast=fail_fast,
            started_at=datetime.utcnow()
        )
        
        # Track execution
        self._active_executions[execution_id] = execution
        
        try:
            # Emit start event
            await self._emit_event(GrainchainEventType.QUALITY_GATE_STARTED, {
                'execution_id': execution_id,
                'pr_number': pr_number,
                'commit_sha': commit_sha,
                'gates': [g.value for g in gates]
            })
            
            # Execute gates
            if self.config.quality_gates.parallel_execution:
                await self._execute_gates_parallel(execution)
            else:
                await self._execute_gates_sequential(execution)
            
            execution.completed_at = datetime.utcnow()
            execution.status = "completed"
            
            # Emit completion event
            await self._emit_event(GrainchainEventType.QUALITY_GATE_COMPLETED, {
                'execution_id': execution_id,
                'status': execution.status,
                'passed': execution.all_passed,
                'duration': execution.duration
            })
            
            return execution
            
        except Exception as e:
            execution.status = "error"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            
            logger.error(f"Quality gate execution failed: {e}")
            
            # Emit failure event
            await self._emit_event(GrainchainEventType.QUALITY_GATE_FAILED, {
                'execution_id': execution_id,
                'error': str(e)
            })
            
            raise
            
        finally:
            # Move to history
            self._execution_history.append(execution)
            self._active_executions.pop(execution_id, None)
    
    async def _execute_gates_parallel(self, execution: 'QualityGateExecution'):
        """Execute gates in parallel with dependency management."""
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(execution.gates)
        
        # Execute in waves based on dependencies
        completed_gates = set()
        
        while len(completed_gates) < len(execution.gates):
            # Find gates that can run (dependencies satisfied)
            ready_gates = [
                gate for gate in execution.gates
                if gate not in completed_gates and
                all(dep in completed_gates for dep in dependency_graph.get(gate, []))
            ]
            
            if not ready_gates:
                raise Exception("Circular dependency detected in quality gates")
            
            # Execute ready gates in parallel
            tasks = []
            for gate in ready_gates:
                task = asyncio.create_task(self._execute_single_gate(execution, gate))
                tasks.append((gate, task))
            
            # Wait for completion
            for gate, task in tasks:
                try:
                    result = await task
                    execution.results[gate] = result
                    completed_gates.add(gate)
                    
                    # Check for fail-fast
                    if execution.fail_fast and not result.passed:
                        # Cancel remaining tasks
                        for _, remaining_task in tasks:
                            if not remaining_task.done():
                                remaining_task.cancel()
                        return
                        
                except Exception as e:
                    logger.error(f"Gate {gate.value} failed: {e}")
                    execution.results[gate] = QualityGateResult(
                        gate_type=gate,
                        status=QualityGateStatus.ERROR,
                        passed=False,
                        duration=0,
                        timestamp=datetime.utcnow(),
                        sandbox_id="",
                        error_message=str(e)
                    )
                    completed_gates.add(gate)
                    
                    if execution.fail_fast:
                        return
    
    async def _execute_gates_sequential(self, execution: 'QualityGateExecution'):
        """Execute gates sequentially."""
        # Sort gates by dependencies
        sorted_gates = self._topological_sort(execution.gates)
        
        for gate in sorted_gates:
            try:
                result = await self._execute_single_gate(execution, gate)
                execution.results[gate] = result
                
                # Check for fail-fast
                if execution.fail_fast and not result.passed:
                    return
                    
            except Exception as e:
                logger.error(f"Gate {gate.value} failed: {e}")
                execution.results[gate] = QualityGateResult(
                    gate_type=gate,
                    status=QualityGateStatus.ERROR,
                    passed=False,
                    duration=0,
                    timestamp=datetime.utcnow(),
                    sandbox_id="",
                    error_message=str(e)
                )
                
                if execution.fail_fast:
                    return
    
    async def _execute_single_gate(
        self,
        execution: 'QualityGateExecution',
        gate_type: QualityGateType
    ) -> QualityGateResult:
        """Execute a single quality gate."""
        start_time = datetime.utcnow()
        
        # Get gate definition
        definition = self._gate_definitions.get(gate_type)
        if not definition:
            raise ValueError(f"Unknown gate type: {gate_type}")
        
        # Check for custom executor
        if gate_type in self._custom_gates:
            custom_gate = self._custom_gates[gate_type]
            return await custom_gate['executor'](execution, definition)
        
        # Create sandbox configuration
        sandbox_config = SandboxConfig(
            provider=definition.provider,
            timeout=definition.timeout,
            memory_limit="4GB",
            environment_vars={
                "CI": "true",
                "QUALITY_GATE": gate_type.value,
                "PR_NUMBER": str(execution.pr_number) if execution.pr_number else "",
                "COMMIT_SHA": execution.commit_sha or ""
            }
        )
        
        # Execute gate in sandbox
        async with self.sandbox_manager.create_session(sandbox_config) as session:
            try:
                # Restore base snapshot if provided
                if execution.base_snapshot:
                    await session.restore_snapshot(execution.base_snapshot)
                
                # Execute gate-specific logic
                result = await self._execute_gate_logic(session, gate_type, definition)
                
                # Create snapshot of gate execution
                snapshot_id = await session.create_snapshot(
                    name=f"gate_{gate_type.value}_{execution.execution_id}",
                    metadata={
                        "gate_type": gate_type.value,
                        "execution_id": execution.execution_id,
                        "status": result.status.value,
                        "passed": result.passed
                    }
                )
                result.snapshot_id = snapshot_id
                
                return result
                
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                return QualityGateResult(
                    gate_type=gate_type,
                    status=QualityGateStatus.ERROR,
                    passed=False,
                    duration=duration,
                    timestamp=start_time,
                    sandbox_id=session.sandbox_id,
                    error_message=str(e)
                )
    
    async def _execute_gate_logic(
        self,
        session,
        gate_type: QualityGateType,
        definition: QualityGateDefinition
    ) -> QualityGateResult:
        """Execute the specific logic for a gate type."""
        start_time = datetime.utcnow()
        
        if gate_type == QualityGateType.CODE_QUALITY:
            return await self._execute_code_quality_gate(session, definition)
        elif gate_type == QualityGateType.UNIT_TESTS:
            return await self._execute_unit_tests_gate(session, definition)
        elif gate_type == QualityGateType.INTEGRATION_TESTS:
            return await self._execute_integration_tests_gate(session, definition)
        elif gate_type == QualityGateType.SECURITY_SCAN:
            return await self._execute_security_scan_gate(session, definition)
        elif gate_type == QualityGateType.PERFORMANCE_TEST:
            return await self._execute_performance_test_gate(session, definition)
        elif gate_type == QualityGateType.DEPLOYMENT_TEST:
            return await self._execute_deployment_test_gate(session, definition)
        else:
            raise ValueError(f"Unsupported gate type: {gate_type}")
    
    async def _execute_code_quality_gate(self, session, definition) -> QualityGateResult:
        """Execute code quality checks."""
        start_time = datetime.utcnow()
        results = {}
        
        # Run linting
        lint_result = await session.execute("ruff check . --output-format=json")
        results["lint"] = lint_result
        
        # Run type checking
        type_result = await session.execute("mypy . --json-report")
        results["types"] = type_result
        
        # Run security linting
        security_result = await session.execute("bandit -r . -f json")
        results["security"] = security_result
        
        # Run complexity analysis
        complexity_result = await session.execute("radon cc . --json")
        results["complexity"] = complexity_result
        
        # Evaluate results
        passed = (
            lint_result.exit_code == 0 and
            type_result.exit_code == 0 and
            security_result.exit_code == 0
        )
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return QualityGateResult(
            gate_type=QualityGateType.CODE_QUALITY,
            status=QualityGateStatus.PASSED if passed else QualityGateStatus.FAILED,
            passed=passed,
            duration=duration,
            timestamp=start_time,
            sandbox_id=session.sandbox_id,
            results=results
        )
    
    async def _execute_unit_tests_gate(self, session, definition) -> QualityGateResult:
        """Execute unit tests."""
        start_time = datetime.utcnow()
        
        test_command = definition.config.get("test_command", "python -m pytest tests/unit/ -v")
        test_result = await session.execute(test_command)
        
        passed = test_result.exit_code == 0
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return QualityGateResult(
            gate_type=QualityGateType.UNIT_TESTS,
            status=QualityGateStatus.PASSED if passed else QualityGateStatus.FAILED,
            passed=passed,
            duration=duration,
            timestamp=start_time,
            sandbox_id=session.sandbox_id,
            results={"test_output": test_result.stdout}
        )
    
    # Additional gate implementations would follow similar patterns...
    
    def _build_dependency_graph(self, gates: List[QualityGateType]) -> Dict[QualityGateType, List[QualityGateType]]:
        """Build dependency graph for gates."""
        graph = {}
        
        for gate in gates:
            definition = self._gate_definitions.get(gate)
            if definition:
                graph[gate] = [dep for dep in definition.dependencies if dep in gates]
            else:
                graph[gate] = []
        
        return graph
    
    def _topological_sort(self, gates: List[QualityGateType]) -> List[QualityGateType]:
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
    
    async def _emit_event(self, event_type: GrainchainEventType, data: Dict[str, Any]):
        """Emit a quality gate event."""
        # This would integrate with the event system
        pass


@dataclass
class QualityGateExecution:
    """Represents a quality gate execution."""
    execution_id: str
    pr_number: Optional[int]
    commit_sha: Optional[str]
    base_snapshot: Optional[str]
    gates: List[QualityGateType]
    fail_fast: bool
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"
    results: Dict[QualityGateType, QualityGateResult] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}
    
    @property
    def duration(self) -> float:
        """Get execution duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return (datetime.utcnow() - self.started_at).total_seconds()
    
    @property
    def all_passed(self) -> bool:
        """Check if all gates passed."""
        return all(result.passed for result in self.results.values())
    
    @property
    def failed_gates(self) -> List[QualityGateType]:
        """Get list of failed gates."""
        return [gate for gate, result in self.results.items() if not result.passed]
    
    @property
    def passed_gates(self) -> List[QualityGateType]:
        """Get list of passed gates."""
        return [gate for gate, result in self.results.items() if result.passed]


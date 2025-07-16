"""
Autonomous CI/CD - Self-healing CI/CD pipeline management with intelligent error detection
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import yaml
import os


class PipelineStage(Enum):
    """CI/CD pipeline stages"""
    SETUP = "setup"
    BUILD = "build"
    TEST = "test"
    SECURITY_SCAN = "security_scan"
    DEPLOY = "deploy"
    MONITOR = "monitor"
    CLEANUP = "cleanup"


class PipelineStatus(Enum):
    """Pipeline execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


@dataclass
class PipelineStep:
    """Represents a single pipeline step"""
    name: str
    stage: PipelineStage
    command: str
    timeout: int = 300
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    working_directory: Optional[str] = None
    continue_on_error: bool = False


@dataclass
class PipelineExecution:
    """Represents a pipeline execution"""
    id: str
    pipeline_name: str
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    steps: List[PipelineStep] = field(default_factory=list)
    current_step: Optional[str] = None
    error_message: Optional[str] = None
    logs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AutonomousCICD:
    """
    Autonomous CI/CD Pipeline Management System
    
    Features:
    - Automated pipeline management
    - Intelligent error detection and resolution
    - Self-healing architecture implementation
    - Continuous optimization
    - Real-time monitoring and alerting
    """
    
    def __init__(
        self,
        enabled: bool = True,
        auto_healing: bool = True,
        continuous_optimization: bool = True,
        config_path: str = "contexten_cicd_config.yaml"
    ):
        """Initialize the Autonomous CI/CD system"""
        self.enabled = enabled
        self.auto_healing = auto_healing
        self.continuous_optimization = continuous_optimization
        self.config_path = config_path
        
        self.logger = logging.getLogger(__name__)
        
        # Pipeline definitions
        self._pipelines: Dict[str, List[PipelineStep]] = {}
        self._load_default_pipelines()
        
        # Active executions
        self._executions: Dict[str, PipelineExecution] = {}
        
        # Error patterns and fixes
        self._error_patterns: Dict[str, Dict[str, Any]] = {}
        self._load_error_patterns()
        
        # Statistics
        self._stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "auto_fixes_applied": 0,
            "optimizations_performed": 0,
            "last_execution": None,
            "average_execution_time": 0.0
        }
        
        # Monitoring task
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
    
    def _load_default_pipelines(self):
        """Load default CI/CD pipeline definitions"""
        # Default build pipeline
        build_pipeline = [
            PipelineStep(
                name="checkout",
                stage=PipelineStage.SETUP,
                command="git checkout {branch}",
                timeout=60
            ),
            PipelineStep(
                name="install_dependencies",
                stage=PipelineStage.SETUP,
                command="pip install -r requirements.txt",
                timeout=300,
                dependencies=["checkout"]
            ),
            PipelineStep(
                name="lint",
                stage=PipelineStage.BUILD,
                command="ruff check .",
                timeout=120,
                dependencies=["install_dependencies"]
            ),
            PipelineStep(
                name="type_check",
                stage=PipelineStage.BUILD,
                command="mypy .",
                timeout=180,
                dependencies=["install_dependencies"]
            ),
            PipelineStep(
                name="unit_tests",
                stage=PipelineStage.TEST,
                command="pytest tests/unit/",
                timeout=600,
                dependencies=["lint", "type_check"]
            ),
            PipelineStep(
                name="integration_tests",
                stage=PipelineStage.TEST,
                command="pytest tests/integration/",
                timeout=900,
                dependencies=["unit_tests"]
            ),
            PipelineStep(
                name="security_scan",
                stage=PipelineStage.SECURITY_SCAN,
                command="bandit -r src/",
                timeout=300,
                dependencies=["unit_tests"]
            ),
            PipelineStep(
                name="build_package",
                stage=PipelineStage.BUILD,
                command="python -m build",
                timeout=300,
                dependencies=["integration_tests", "security_scan"]
            )
        ]
        
        # Default deployment pipeline
        deploy_pipeline = [
            PipelineStep(
                name="validate_environment",
                stage=PipelineStage.SETUP,
                command="echo 'Validating deployment environment'",
                timeout=60
            ),
            PipelineStep(
                name="backup_current",
                stage=PipelineStage.SETUP,
                command="echo 'Creating backup of current deployment'",
                timeout=120,
                dependencies=["validate_environment"]
            ),
            PipelineStep(
                name="deploy_application",
                stage=PipelineStage.DEPLOY,
                command="echo 'Deploying application'",
                timeout=600,
                dependencies=["backup_current"]
            ),
            PipelineStep(
                name="health_check",
                stage=PipelineStage.MONITOR,
                command="echo 'Performing health check'",
                timeout=300,
                dependencies=["deploy_application"]
            ),
            PipelineStep(
                name="smoke_tests",
                stage=PipelineStage.TEST,
                command="echo 'Running smoke tests'",
                timeout=300,
                dependencies=["health_check"]
            )
        ]
        
        self._pipelines["build"] = build_pipeline
        self._pipelines["deploy"] = deploy_pipeline
    
    def _load_error_patterns(self):
        """Load error patterns and their fixes"""
        self._error_patterns = {
            "dependency_conflict": {
                "pattern": ["conflict", "incompatible", "version"],
                "fix_commands": [
                    "pip install --upgrade pip",
                    "pip install --force-reinstall -r requirements.txt"
                ],
                "description": "Dependency version conflict detected"
            },
            "import_error": {
                "pattern": ["ImportError", "ModuleNotFoundError", "No module named"],
                "fix_commands": [
                    "pip install --upgrade -r requirements.txt",
                    "pip install -e ."
                ],
                "description": "Missing module or import error"
            },
            "test_failure": {
                "pattern": ["FAILED", "AssertionError", "test failed"],
                "fix_commands": [
                    "pytest --lf",  # Run last failed tests
                    "pytest -x"     # Stop on first failure
                ],
                "description": "Test failure detected"
            },
            "lint_error": {
                "pattern": ["ruff", "lint", "style"],
                "fix_commands": [
                    "ruff check --fix .",
                    "ruff format ."
                ],
                "description": "Code style/lint issues"
            },
            "type_error": {
                "pattern": ["mypy", "type", "typing"],
                "fix_commands": [
                    "mypy --install-types --non-interactive"
                ],
                "description": "Type checking errors"
            },
            "permission_error": {
                "pattern": ["Permission denied", "PermissionError"],
                "fix_commands": [
                    "chmod +x scripts/*",
                    "sudo chown -R $USER:$USER ."
                ],
                "description": "File permission issues"
            }
        }
    
    async def start(self):
        """Start the Autonomous CI/CD system"""
        self.logger.info("Starting Autonomous CI/CD system...")
        
        if not self.enabled:
            self.logger.info("Autonomous CI/CD is disabled")
            return
        
        self._running = True
        
        # Load configuration if exists
        await self._load_configuration()
        
        # Start monitoring task
        if self.continuous_optimization:
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        
        self.logger.info("Autonomous CI/CD system started successfully")
    
    async def stop(self):
        """Stop the Autonomous CI/CD system"""
        self.logger.info("Stopping Autonomous CI/CD system...")
        
        self._running = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # Cancel active executions
        for execution in self._executions.values():
            if execution.status == PipelineStatus.RUNNING:
                execution.status = PipelineStatus.CANCELLED
        
        self.logger.info("Autonomous CI/CD system stopped successfully")
    
    async def _load_configuration(self):
        """Load CI/CD configuration from file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                
                # Load custom pipelines
                if "pipelines" in config:
                    for name, steps_config in config["pipelines"].items():
                        steps = []
                        for step_config in steps_config:
                            step = PipelineStep(**step_config)
                            steps.append(step)
                        self._pipelines[name] = steps
                
                # Load custom error patterns
                if "error_patterns" in config:
                    self._error_patterns.update(config["error_patterns"])
                
                self.logger.info(f"Loaded configuration from {self.config_path}")
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
    
    async def execute_pipeline(
        self,
        pipeline_name: str,
        execution_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute a CI/CD pipeline
        
        Args:
            pipeline_name: Name of the pipeline to execute
            execution_id: Optional execution ID
            parameters: Pipeline parameters
            
        Returns:
            Execution ID
        """
        if pipeline_name not in self._pipelines:
            raise ValueError(f"Pipeline '{pipeline_name}' not found")
        
        execution_id = execution_id or f"{pipeline_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        parameters = parameters or {}
        
        # Create execution
        execution = PipelineExecution(
            id=execution_id,
            pipeline_name=pipeline_name,
            status=PipelineStatus.PENDING,
            start_time=datetime.now(),
            steps=self._pipelines[pipeline_name].copy(),
            metadata=parameters
        )
        
        self._executions[execution_id] = execution
        
        # Start execution task
        asyncio.create_task(self._execute_pipeline_internal(execution))
        
        self.logger.info(f"Started pipeline execution: {execution_id}")
        return execution_id
    
    async def _execute_pipeline_internal(self, execution: PipelineExecution):
        """Internal pipeline execution logic"""
        try:
            execution.status = PipelineStatus.RUNNING
            self.logger.info(f"Executing pipeline {execution.pipeline_name} ({execution.id})")
            
            # Execute steps in dependency order
            completed_steps = set()
            
            while len(completed_steps) < len(execution.steps):
                # Find next executable steps
                executable_steps = []
                for step in execution.steps:
                    if step.name not in completed_steps:
                        # Check if all dependencies are completed
                        if all(dep in completed_steps for dep in step.dependencies):
                            executable_steps.append(step)
                
                if not executable_steps:
                    # No more executable steps - check for circular dependencies
                    remaining_steps = [s.name for s in execution.steps if s.name not in completed_steps]
                    raise RuntimeError(f"Circular dependency or missing dependencies: {remaining_steps}")
                
                # Execute steps in parallel
                tasks = []
                for step in executable_steps:
                    task = asyncio.create_task(self._execute_step(execution, step))
                    tasks.append((step, task))
                
                # Wait for all steps to complete
                for step, task in tasks:
                    try:
                        success = await task
                        if success:
                            completed_steps.add(step.name)
                        elif not step.continue_on_error:
                            raise RuntimeError(f"Step '{step.name}' failed and continue_on_error is False")
                    except Exception as e:
                        if not step.continue_on_error:
                            raise RuntimeError(f"Step '{step.name}' failed: {e}")
                        else:
                            self.logger.warning(f"Step '{step.name}' failed but continuing: {e}")
                            completed_steps.add(step.name)
            
            # Pipeline completed successfully
            execution.status = PipelineStatus.SUCCESS
            execution.end_time = datetime.now()
            
            self._stats["successful_executions"] += 1
            self.logger.info(f"Pipeline {execution.id} completed successfully")
            
        except Exception as e:
            execution.status = PipelineStatus.FAILED
            execution.end_time = datetime.now()
            execution.error_message = str(e)
            
            self._stats["failed_executions"] += 1
            self.logger.error(f"Pipeline {execution.id} failed: {e}")
            
            # Attempt auto-healing if enabled
            if self.auto_healing:
                await self._attempt_auto_healing(execution, str(e))
        
        finally:
            self._stats["total_executions"] += 1
            self._stats["last_execution"] = execution.end_time.isoformat() if execution.end_time else None
            
            # Update average execution time
            if execution.end_time:
                duration = (execution.end_time - execution.start_time).total_seconds()
                if self._stats["average_execution_time"] == 0:
                    self._stats["average_execution_time"] = duration
                else:
                    self._stats["average_execution_time"] = (
                        self._stats["average_execution_time"] * 0.9 + duration * 0.1
                    )
    
    async def _execute_step(self, execution: PipelineExecution, step: PipelineStep) -> bool:
        """Execute a single pipeline step"""
        try:
            execution.current_step = step.name
            execution.logs.append(f"Starting step: {step.name}")
            
            self.logger.debug(f"Executing step {step.name} in pipeline {execution.id}")
            
            # Prepare environment
            env = os.environ.copy()
            env.update(step.environment)
            
            # Format command with execution metadata
            command = step.command.format(**execution.metadata)
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=step.working_directory
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=step.timeout
                )
                
                # Log output
                if stdout:
                    execution.logs.append(f"STDOUT: {stdout.decode()}")
                if stderr:
                    execution.logs.append(f"STDERR: {stderr.decode()}")
                
                if process.returncode == 0:
                    execution.logs.append(f"Step {step.name} completed successfully")
                    return True
                else:
                    error_msg = f"Step {step.name} failed with return code {process.returncode}"
                    execution.logs.append(error_msg)
                    
                    # Attempt retry if configured
                    if step.retry_count < step.max_retries:
                        step.retry_count += 1
                        execution.logs.append(f"Retrying step {step.name} (attempt {step.retry_count})")
                        await asyncio.sleep(2 ** step.retry_count)  # Exponential backoff
                        return await self._execute_step(execution, step)
                    
                    return False
                    
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                execution.logs.append(f"Step {step.name} timed out after {step.timeout} seconds")
                return False
                
        except Exception as e:
            execution.logs.append(f"Step {step.name} failed with exception: {e}")
            return False
    
    async def _attempt_auto_healing(self, execution: PipelineExecution, error_message: str):
        """Attempt to automatically fix pipeline errors"""
        try:
            self.logger.info(f"Attempting auto-healing for pipeline {execution.id}")
            
            # Analyze error message
            fix_applied = False
            
            for pattern_name, pattern_info in self._error_patterns.items():
                if any(keyword.lower() in error_message.lower() for keyword in pattern_info["pattern"]):
                    self.logger.info(f"Detected error pattern: {pattern_name}")
                    
                    # Apply fix commands
                    for fix_command in pattern_info["fix_commands"]:
                        try:
                            process = await asyncio.create_subprocess_shell(
                                fix_command,
                                stdout=asyncio.subprocess.PIPE,
                                stderr=asyncio.subprocess.PIPE
                            )
                            
                            stdout, stderr = await process.communicate()
                            
                            if process.returncode == 0:
                                execution.logs.append(f"Auto-fix applied: {fix_command}")
                                fix_applied = True
                            else:
                                execution.logs.append(f"Auto-fix failed: {fix_command} - {stderr.decode()}")
                                
                        except Exception as e:
                            execution.logs.append(f"Auto-fix error: {fix_command} - {e}")
                    
                    break
            
            if fix_applied:
                self._stats["auto_fixes_applied"] += 1
                execution.logs.append("Auto-healing completed, retrying pipeline...")
                
                # Retry the pipeline
                new_execution_id = f"{execution.id}_retry_{datetime.now().strftime('%H%M%S')}"
                await self.execute_pipeline(
                    execution.pipeline_name,
                    new_execution_id,
                    execution.metadata
                )
            else:
                execution.logs.append("No auto-healing pattern matched")
                
        except Exception as e:
            self.logger.error(f"Auto-healing failed: {e}")
            execution.logs.append(f"Auto-healing failed: {e}")
    
    async def _monitoring_loop(self):
        """Background monitoring and optimization loop"""
        while self._running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._perform_optimization()
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
    
    async def _perform_optimization(self):
        """Perform continuous optimization"""
        try:
            self.logger.debug("Performing CI/CD optimization...")
            
            # Analyze recent executions
            recent_executions = [
                exec for exec in self._executions.values()
                if exec.end_time and exec.end_time > datetime.now() - timedelta(hours=24)
            ]
            
            if not recent_executions:
                return
            
            # Identify frequently failing steps
            step_failures = {}
            for execution in recent_executions:
                if execution.status == PipelineStatus.FAILED:
                    for step in execution.steps:
                        if step.retry_count > 0:
                            step_failures[step.name] = step_failures.get(step.name, 0) + 1
            
            # Optimize frequently failing steps
            for step_name, failure_count in step_failures.items():
                if failure_count >= 3:  # Failed 3+ times in 24 hours
                    await self._optimize_step(step_name)
            
            # Clean up old executions
            await self._cleanup_old_executions()
            
            self._stats["optimizations_performed"] += 1
            
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
    
    async def _optimize_step(self, step_name: str):
        """Optimize a specific pipeline step"""
        self.logger.info(f"Optimizing frequently failing step: {step_name}")
        
        # Find the step in all pipelines
        for pipeline_name, steps in self._pipelines.items():
            for step in steps:
                if step.name == step_name:
                    # Increase timeout and max retries
                    step.timeout = min(step.timeout * 1.5, 1800)  # Max 30 minutes
                    step.max_retries = min(step.max_retries + 1, 5)  # Max 5 retries
                    
                    self.logger.info(
                        f"Optimized step {step_name}: timeout={step.timeout}, max_retries={step.max_retries}"
                    )
    
    async def _cleanup_old_executions(self):
        """Clean up old execution records"""
        cutoff_date = datetime.now() - timedelta(days=7)  # Keep 7 days of history
        
        old_executions = [
            exec_id for exec_id, execution in self._executions.items()
            if execution.end_time and execution.end_time < cutoff_date
        ]
        
        for exec_id in old_executions:
            del self._executions[exec_id]
        
        if old_executions:
            self.logger.info(f"Cleaned up {len(old_executions)} old execution records")
    
    async def get_execution_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a pipeline execution"""
        if execution_id not in self._executions:
            return None
        
        execution = self._executions[execution_id]
        
        return {
            "id": execution.id,
            "pipeline_name": execution.pipeline_name,
            "status": execution.status.value,
            "start_time": execution.start_time.isoformat(),
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "current_step": execution.current_step,
            "error_message": execution.error_message,
            "steps_total": len(execution.steps),
            "metadata": execution.metadata
        }
    
    async def get_execution_logs(self, execution_id: str) -> List[str]:
        """Get logs for a pipeline execution"""
        if execution_id not in self._executions:
            return []
        
        return self._executions[execution_id].logs
    
    async def list_pipelines(self) -> List[str]:
        """List available pipelines"""
        return list(self._pipelines.keys())
    
    async def list_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent pipeline executions"""
        executions = sorted(
            self._executions.values(),
            key=lambda x: x.start_time,
            reverse=True
        )
        
        return [
            {
                "id": exec.id,
                "pipeline_name": exec.pipeline_name,
                "status": exec.status.value,
                "start_time": exec.start_time.isoformat(),
                "end_time": exec.end_time.isoformat() if exec.end_time else None,
                "error_message": exec.error_message
            }
            for exec in executions[:limit]
        ]
    
    async def optimize(self) -> Dict[str, Any]:
        """Trigger manual optimization"""
        await self._perform_optimization()
        
        return {
            "optimization_completed": True,
            "timestamp": datetime.now().isoformat(),
            "optimizations_performed": self._stats["optimizations_performed"]
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get CI/CD system status"""
        active_executions = sum(
            1 for exec in self._executions.values()
            if exec.status == PipelineStatus.RUNNING
        )
        
        return {
            "enabled": self.enabled,
            "auto_healing": self.auto_healing,
            "continuous_optimization": self.continuous_optimization,
            "running": self._running,
            "active_executions": active_executions,
            "total_pipelines": len(self._pipelines),
            "error_patterns": len(self._error_patterns),
            **self._stats
        }
    
    def is_healthy(self) -> bool:
        """Check if CI/CD system is healthy"""
        if not self.enabled:
            return True
        
        return (
            self._running and
            len(self._executions) < 1000 and  # Not too many executions
            self._stats["failed_executions"] < self._stats["total_executions"] * 0.5  # Less than 50% failure rate
        )


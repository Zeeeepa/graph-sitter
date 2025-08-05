"""
Task Orchestrator

Provides intelligent task management with automated requirement analysis,
task decomposition, priority assignment, and dynamic orchestration.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

from ..models.pipeline_models import PipelineExecution, PipelineStatus


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskType(Enum):
    """Types of tasks in the pipeline."""
    SETUP = "setup"
    BUILD = "build"
    TEST = "test"
    LINT = "lint"
    SECURITY_SCAN = "security_scan"
    DEPLOY = "deploy"
    CLEANUP = "cleanup"
    NOTIFICATION = "notification"


class Task(BaseModel):
    """Individual task definition."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    task_type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    
    # Dependencies and scheduling
    dependencies: List[str] = Field(default_factory=list)
    estimated_duration: int = 60  # seconds
    timeout: int = 300  # seconds
    retry_count: int = 0
    max_retries: int = 3
    
    # Execution details
    command: Optional[str] = None
    environment: Dict[str, str] = Field(default_factory=dict)
    working_directory: Optional[str] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    exit_code: Optional[int] = None
    output: Optional[str] = None
    error_output: Optional[str] = None
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TaskGraph(BaseModel):
    """Task dependency graph."""
    tasks: Dict[str, Task] = Field(default_factory=dict)
    edges: List[Tuple[str, str]] = Field(default_factory=list)  # (from_task, to_task)
    
    def add_task(self, task: Task) -> None:
        """Add a task to the graph."""
        self.tasks[task.id] = task
    
    def add_dependency(self, from_task_id: str, to_task_id: str) -> None:
        """Add a dependency between tasks."""
        if from_task_id in self.tasks and to_task_id in self.tasks:
            self.edges.append((from_task_id, to_task_id))
            if to_task_id not in self.tasks[from_task_id].dependencies:
                self.tasks[from_task_id].dependencies.append(to_task_id)
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute."""
        ready_tasks = []
        
        for task in self.tasks.values():
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                dependencies_completed = all(
                    self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                    if dep_id in self.tasks
                )
                
                if dependencies_completed:
                    task.status = TaskStatus.READY
                    ready_tasks.append(task)
        
        return ready_tasks
    
    def get_blocked_tasks(self) -> List[Task]:
        """Get tasks that are blocked by failed dependencies."""
        blocked_tasks = []
        
        for task in self.tasks.values():
            if task.status in [TaskStatus.PENDING, TaskStatus.READY]:
                # Check if any dependency failed
                has_failed_dependency = any(
                    self.tasks[dep_id].status == TaskStatus.FAILED
                    for dep_id in task.dependencies
                    if dep_id in self.tasks
                )
                
                if has_failed_dependency:
                    task.status = TaskStatus.BLOCKED
                    blocked_tasks.append(task)
        
        return blocked_tasks


class ResourcePool(BaseModel):
    """Resource pool for task execution."""
    max_concurrent_tasks: int = 4
    available_workers: int = 4
    cpu_limit: float = 2.0
    memory_limit: float = 4.0  # GB
    
    # Current usage
    active_tasks: Set[str] = Field(default_factory=set)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    def can_execute_task(self, task: Task) -> bool:
        """Check if resources are available to execute a task."""
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            return False
        
        # Estimate resource requirements
        estimated_cpu = 0.5  # Default CPU requirement
        estimated_memory = 0.5  # Default memory requirement
        
        if task.task_type == TaskType.BUILD:
            estimated_cpu = 1.0
            estimated_memory = 1.0
        elif task.task_type == TaskType.TEST:
            estimated_cpu = 0.8
            estimated_memory = 0.8
        
        return (
            self.cpu_usage + estimated_cpu <= self.cpu_limit and
            self.memory_usage + estimated_memory <= self.memory_limit
        )
    
    def allocate_resources(self, task: Task) -> bool:
        """Allocate resources for a task."""
        if self.can_execute_task(task):
            self.active_tasks.add(task.id)
            # Update resource usage (simplified)
            self.cpu_usage += 0.5
            self.memory_usage += 0.5
            return True
        return False
    
    def release_resources(self, task: Task) -> None:
        """Release resources after task completion."""
        if task.id in self.active_tasks:
            self.active_tasks.remove(task.id)
            self.cpu_usage = max(0, self.cpu_usage - 0.5)
            self.memory_usage = max(0, self.memory_usage - 0.5)


class TaskOrchestrator:
    """
    Intelligent task orchestrator that manages pipeline execution
    with dynamic scheduling, resource optimization, and failure handling.
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 4,
        enable_dynamic_scheduling: bool = True,
        enable_resource_optimization: bool = True
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.enable_dynamic_scheduling = enable_dynamic_scheduling
        self.enable_resource_optimization = enable_resource_optimization
        
        self.logger = logging.getLogger(__name__)
        
        # Resource management
        self.resource_pool = ResourcePool(max_concurrent_tasks=max_concurrent_tasks)
        
        # Task tracking
        self.active_orchestrations: Dict[str, TaskGraph] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Performance metrics
        self.task_performance_history: Dict[TaskType, List[float]] = {}
        self.optimization_cache: Dict[str, Any] = {}

    async def orchestrate_pipeline(
        self,
        pipeline_execution: PipelineExecution,
        requirements: Optional[Dict[str, Any]] = None
    ) -> TaskGraph:
        """
        Orchestrate pipeline execution with intelligent task management.
        
        Args:
            pipeline_execution: Pipeline execution instance
            requirements: Additional requirements and constraints
            
        Returns:
            Task graph for the pipeline
        """
        self.logger.info(f"Starting orchestration for pipeline: {pipeline_execution.id}")
        
        # Analyze requirements
        analyzed_requirements = await self._analyze_requirements(
            pipeline_execution, requirements
        )
        
        # Decompose into tasks
        task_graph = await self._decompose_into_tasks(
            pipeline_execution, analyzed_requirements
        )
        
        # Optimize task execution order
        if self.enable_dynamic_scheduling:
            task_graph = await self._optimize_task_scheduling(task_graph)
        
        # Store active orchestration
        self.active_orchestrations[pipeline_execution.id] = task_graph
        
        # Start execution
        execution_result = await self._execute_task_graph(
            pipeline_execution.id, task_graph
        )
        
        # Record execution history
        self.execution_history.append({
            "pipeline_id": pipeline_execution.id,
            "task_count": len(task_graph.tasks),
            "execution_time": execution_result.get("total_time", 0),
            "success_rate": execution_result.get("success_rate", 0),
            "timestamp": datetime.now().isoformat()
        })
        
        return task_graph

    async def _analyze_requirements(
        self,
        pipeline_execution: PipelineExecution,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze and parse pipeline requirements."""
        analyzed = {
            "project_type": pipeline_execution.project_type.value,
            "stages": pipeline_execution.config.stages,
            "tools": pipeline_execution.config.tools,
            "quality_gates": pipeline_execution.config.quality_gates,
            "resource_limits": pipeline_execution.config.resource_limits,
            "timeout": pipeline_execution.config.timeout_minutes * 60,
            "parallel_jobs": pipeline_execution.config.parallel_jobs
        }
        
        # Add custom requirements
        if requirements:
            analyzed.update(requirements)
        
        # Analyze project complexity
        complexity_metrics = await self._analyze_project_complexity(
            pipeline_execution.project_path
        )
        analyzed["complexity"] = complexity_metrics
        
        # Determine critical path requirements
        critical_tasks = await self._identify_critical_tasks(analyzed)
        analyzed["critical_tasks"] = critical_tasks
        
        return analyzed

    async def _analyze_project_complexity(self, project_path) -> Dict[str, Any]:
        """Analyze project complexity for task planning."""
        # This would analyze the project structure, dependencies, etc.
        # For now, return basic metrics
        return {
            "estimated_build_time": 300,  # seconds
            "estimated_test_time": 600,
            "dependency_complexity": "medium",
            "test_coverage_required": 80.0
        }

    async def _identify_critical_tasks(self, requirements: Dict[str, Any]) -> List[str]:
        """Identify tasks that are critical for pipeline success."""
        critical_tasks = []
        
        # Always critical
        critical_tasks.extend(["setup", "build"])
        
        # Conditional criticality
        if requirements.get("quality_gates", {}).get("test_coverage", 0) > 0:
            critical_tasks.append("test")
        
        if requirements.get("quality_gates", {}).get("security_scan", False):
            critical_tasks.append("security_scan")
        
        return critical_tasks

    async def _decompose_into_tasks(
        self,
        pipeline_execution: PipelineExecution,
        requirements: Dict[str, Any]
    ) -> TaskGraph:
        """Decompose pipeline into individual tasks."""
        task_graph = TaskGraph()
        
        # Create tasks based on pipeline configuration
        tasks = []
        
        # Setup task (always first)
        setup_task = Task(
            name="Setup Environment",
            description="Setup build environment and dependencies",
            task_type=TaskType.SETUP,
            priority=TaskPriority.CRITICAL,
            estimated_duration=120,
            command=self._generate_setup_command(pipeline_execution)
        )
        tasks.append(setup_task)
        
        # Build task
        if "build" in requirements.get("stages", []):
            build_task = Task(
                name="Build Project",
                description="Compile and build the project",
                task_type=TaskType.BUILD,
                priority=TaskPriority.HIGH,
                dependencies=[setup_task.id],
                estimated_duration=requirements.get("complexity", {}).get("estimated_build_time", 300),
                command=self._generate_build_command(pipeline_execution)
            )
            tasks.append(build_task)
        
        # Lint task (can run in parallel with build)
        if "lint" in requirements.get("stages", []):
            lint_task = Task(
                name="Code Linting",
                description="Run code quality checks",
                task_type=TaskType.LINT,
                priority=TaskPriority.MEDIUM,
                dependencies=[setup_task.id],
                estimated_duration=60,
                command=self._generate_lint_command(pipeline_execution)
            )
            tasks.append(lint_task)
        
        # Test task
        if "test" in requirements.get("stages", []):
            test_dependencies = [setup_task.id]
            if any(t.task_type == TaskType.BUILD for t in tasks):
                build_task_id = next(t.id for t in tasks if t.task_type == TaskType.BUILD)
                test_dependencies.append(build_task_id)
            
            test_task = Task(
                name="Run Tests",
                description="Execute test suite",
                task_type=TaskType.TEST,
                priority=TaskPriority.HIGH,
                dependencies=test_dependencies,
                estimated_duration=requirements.get("complexity", {}).get("estimated_test_time", 600),
                command=self._generate_test_command(pipeline_execution)
            )
            tasks.append(test_task)
        
        # Security scan task
        if requirements.get("quality_gates", {}).get("security_scan", False):
            security_dependencies = [setup_task.id]
            if any(t.task_type == TaskType.BUILD for t in tasks):
                build_task_id = next(t.id for t in tasks if t.task_type == TaskType.BUILD)
                security_dependencies.append(build_task_id)
            
            security_task = Task(
                name="Security Scan",
                description="Run security vulnerability scan",
                task_type=TaskType.SECURITY_SCAN,
                priority=TaskPriority.HIGH,
                dependencies=security_dependencies,
                estimated_duration=180,
                command=self._generate_security_command(pipeline_execution)
            )
            tasks.append(security_task)
        
        # Deploy task (if specified)
        if "deploy" in requirements.get("stages", []):
            deploy_dependencies = [t.id for t in tasks if t.task_type in [TaskType.BUILD, TaskType.TEST]]
            
            deploy_task = Task(
                name="Deploy",
                description="Deploy the application",
                task_type=TaskType.DEPLOY,
                priority=TaskPriority.CRITICAL,
                dependencies=deploy_dependencies,
                estimated_duration=300,
                command=self._generate_deploy_command(pipeline_execution)
            )
            tasks.append(deploy_task)
        
        # Add tasks to graph
        for task in tasks:
            task_graph.add_task(task)
        
        # Add explicit dependencies
        for task in tasks:
            for dep_id in task.dependencies:
                task_graph.add_dependency(task.id, dep_id)
        
        return task_graph

    def _generate_setup_command(self, pipeline_execution: PipelineExecution) -> str:
        """Generate setup command based on project type."""
        project_type = pipeline_execution.project_type.value
        
        if project_type == "python":
            return "uv sync && uv run pip install -e ."
        elif project_type in ["typescript", "javascript"]:
            return "npm ci"
        else:
            return "echo 'Setup completed'"

    def _generate_build_command(self, pipeline_execution: PipelineExecution) -> str:
        """Generate build command based on project type."""
        project_type = pipeline_execution.project_type.value
        
        if project_type == "python":
            return "uv run python -m build"
        elif project_type in ["typescript", "javascript"]:
            return "npm run build"
        else:
            return "echo 'Build completed'"

    def _generate_lint_command(self, pipeline_execution: PipelineExecution) -> str:
        """Generate lint command based on project type."""
        project_type = pipeline_execution.project_type.value
        
        if project_type == "python":
            return "uv run ruff check . && uv run mypy ."
        elif project_type in ["typescript", "javascript"]:
            return "npm run lint"
        else:
            return "echo 'Linting completed'"

    def _generate_test_command(self, pipeline_execution: PipelineExecution) -> str:
        """Generate test command based on project type."""
        project_type = pipeline_execution.project_type.value
        
        if project_type == "python":
            return "uv run pytest --cov=src --cov-report=xml"
        elif project_type in ["typescript", "javascript"]:
            return "npm test"
        else:
            return "echo 'Tests completed'"

    def _generate_security_command(self, pipeline_execution: PipelineExecution) -> str:
        """Generate security scan command based on project type."""
        project_type = pipeline_execution.project_type.value
        
        if project_type == "python":
            return "uv run bandit -r src/"
        elif project_type in ["typescript", "javascript"]:
            return "npm audit"
        else:
            return "echo 'Security scan completed'"

    def _generate_deploy_command(self, pipeline_execution: PipelineExecution) -> str:
        """Generate deploy command."""
        return "echo 'Deployment completed'"

    async def _optimize_task_scheduling(self, task_graph: TaskGraph) -> TaskGraph:
        """Optimize task execution order for better performance."""
        if not self.enable_dynamic_scheduling:
            return task_graph
        
        # Analyze task dependencies and critical path
        critical_path = self._calculate_critical_path(task_graph)
        
        # Adjust priorities based on critical path
        for task_id in critical_path:
            if task_id in task_graph.tasks:
                task = task_graph.tasks[task_id]
                if task.priority != TaskPriority.CRITICAL:
                    task.priority = TaskPriority.HIGH
        
        # Optimize for parallel execution
        parallel_groups = self._identify_parallel_groups(task_graph)
        
        # Apply historical performance data
        await self._apply_performance_optimizations(task_graph)
        
        return task_graph

    def _calculate_critical_path(self, task_graph: TaskGraph) -> List[str]:
        """Calculate the critical path through the task graph."""
        # Simplified critical path calculation
        # In a real implementation, this would use proper CPM algorithm
        
        # Find tasks with no dependencies (start nodes)
        start_tasks = [
            task.id for task in task_graph.tasks.values()
            if not task.dependencies
        ]
        
        # Find tasks with no dependents (end nodes)
        all_dependencies = set()
        for task in task_graph.tasks.values():
            all_dependencies.update(task.dependencies)
        
        end_tasks = [
            task.id for task in task_graph.tasks.values()
            if task.id not in all_dependencies
        ]
        
        # For now, return the longest path (simplified)
        longest_path = []
        max_duration = 0
        
        for start_task in start_tasks:
            path = self._find_longest_path(task_graph, start_task, end_tasks)
            path_duration = sum(
                task_graph.tasks[task_id].estimated_duration
                for task_id in path
                if task_id in task_graph.tasks
            )
            
            if path_duration > max_duration:
                max_duration = path_duration
                longest_path = path
        
        return longest_path

    def _find_longest_path(
        self, task_graph: TaskGraph, start_task: str, end_tasks: List[str]
    ) -> List[str]:
        """Find the longest path from start task to any end task."""
        # Simplified path finding - in reality would use proper graph algorithms
        visited = set()
        path = []
        
        def dfs(task_id: str, current_path: List[str]) -> List[str]:
            if task_id in visited:
                return current_path
            
            visited.add(task_id)
            current_path.append(task_id)
            
            if task_id in end_tasks:
                return current_path.copy()
            
            longest = current_path.copy()
            
            # Find tasks that depend on this task
            dependents = [
                task.id for task in task_graph.tasks.values()
                if task_id in task.dependencies
            ]
            
            for dependent in dependents:
                candidate_path = dfs(dependent, current_path.copy())
                if len(candidate_path) > len(longest):
                    longest = candidate_path
            
            return longest
        
        return dfs(start_task, [])

    def _identify_parallel_groups(self, task_graph: TaskGraph) -> List[List[str]]:
        """Identify groups of tasks that can run in parallel."""
        parallel_groups = []
        
        # Group tasks by their dependency level
        levels = {}
        
        def calculate_level(task_id: str) -> int:
            if task_id in levels:
                return levels[task_id]
            
            task = task_graph.tasks[task_id]
            if not task.dependencies:
                levels[task_id] = 0
                return 0
            
            max_dep_level = max(
                calculate_level(dep_id) for dep_id in task.dependencies
                if dep_id in task_graph.tasks
            )
            levels[task_id] = max_dep_level + 1
            return levels[task_id]
        
        # Calculate levels for all tasks
        for task_id in task_graph.tasks:
            calculate_level(task_id)
        
        # Group tasks by level
        level_groups = {}
        for task_id, level in levels.items():
            if level not in level_groups:
                level_groups[level] = []
            level_groups[level].append(task_id)
        
        # Convert to list of parallel groups
        for level in sorted(level_groups.keys()):
            if len(level_groups[level]) > 1:
                parallel_groups.append(level_groups[level])
        
        return parallel_groups

    async def _apply_performance_optimizations(self, task_graph: TaskGraph) -> None:
        """Apply performance optimizations based on historical data."""
        for task in task_graph.tasks.values():
            task_type = task.task_type
            
            # Get historical performance data
            if task_type in self.task_performance_history:
                history = self.task_performance_history[task_type]
                if history:
                    # Use average of recent executions
                    recent_history = history[-10:]  # Last 10 executions
                    avg_duration = sum(recent_history) / len(recent_history)
                    
                    # Adjust estimated duration
                    task.estimated_duration = int(avg_duration * 1.1)  # Add 10% buffer

    async def _execute_task_graph(
        self, pipeline_id: str, task_graph: TaskGraph
    ) -> Dict[str, Any]:
        """Execute the task graph with intelligent scheduling."""
        start_time = datetime.now()
        completed_tasks = 0
        failed_tasks = 0
        
        self.logger.info(f"Starting execution of {len(task_graph.tasks)} tasks")
        
        # Main execution loop
        while True:
            # Get ready tasks
            ready_tasks = task_graph.get_ready_tasks()
            
            # Check for blocked tasks
            blocked_tasks = task_graph.get_blocked_tasks()
            if blocked_tasks:
                self.logger.warning(f"Found {len(blocked_tasks)} blocked tasks")
                for task in blocked_tasks:
                    task.status = TaskStatus.CANCELLED
                    failed_tasks += 1
            
            # Check if we're done
            if not ready_tasks:
                remaining_tasks = [
                    task for task in task_graph.tasks.values()
                    if task.status in [TaskStatus.PENDING, TaskStatus.READY, TaskStatus.RUNNING]
                ]
                if not remaining_tasks:
                    break
                
                # Wait a bit for running tasks to complete
                await asyncio.sleep(1)
                continue
            
            # Execute ready tasks (up to resource limits)
            execution_tasks = []
            for task in ready_tasks:
                if self.resource_pool.can_execute_task(task):
                    if self.resource_pool.allocate_resources(task):
                        execution_tasks.append(self._execute_task(task))
                        task.status = TaskStatus.RUNNING
                        task.started_at = datetime.now()
            
            # Wait for at least one task to complete
            if execution_tasks:
                done, pending = await asyncio.wait(
                    execution_tasks, return_when=asyncio.FIRST_COMPLETED
                )
                
                # Process completed tasks
                for task_future in done:
                    task_result = await task_future
                    task = task_result["task"]
                    
                    # Release resources
                    self.resource_pool.release_resources(task)
                    
                    # Update task status
                    task.completed_at = datetime.now()
                    if task_result["success"]:
                        task.status = TaskStatus.COMPLETED
                        completed_tasks += 1
                        
                        # Record performance data
                        execution_time = (task.completed_at - task.started_at).total_seconds()
                        if task.task_type not in self.task_performance_history:
                            self.task_performance_history[task.task_type] = []
                        self.task_performance_history[task.task_type].append(execution_time)
                    else:
                        task.status = TaskStatus.FAILED
                        failed_tasks += 1
                        task.error_output = task_result.get("error", "Unknown error")
                
                # Continue with pending tasks
                for task_future in pending:
                    task_future.cancel()
            
            # Small delay to prevent busy waiting
            await asyncio.sleep(0.1)
        
        # Calculate results
        total_time = (datetime.now() - start_time).total_seconds()
        total_tasks = len(task_graph.tasks)
        success_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        
        self.logger.info(
            f"Task execution completed: {completed_tasks}/{total_tasks} successful "
            f"in {total_time:.2f} seconds"
        )
        
        return {
            "total_time": total_time,
            "completed_tasks": completed_tasks,
            "failed_tasks": failed_tasks,
            "success_rate": success_rate,
            "total_tasks": total_tasks
        }

    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task."""
        self.logger.info(f"Executing task: {task.name}")
        
        try:
            # Simulate task execution
            if task.command:
                # In a real implementation, this would execute the actual command
                await asyncio.sleep(min(task.estimated_duration / 10, 5))  # Simulate work
                
                # Simulate success/failure based on task type
                success_probability = 0.9  # 90% success rate
                if task.task_type == TaskType.TEST:
                    success_probability = 0.85  # Tests are more likely to fail
                
                import random
                success = random.random() < success_probability
                
                task.exit_code = 0 if success else 1
                task.output = f"Task {task.name} completed successfully" if success else None
                
                return {
                    "task": task,
                    "success": success,
                    "error": None if success else f"Task {task.name} failed"
                }
            else:
                # No command to execute
                task.exit_code = 0
                task.output = f"Task {task.name} completed (no command)"
                return {"task": task, "success": True, "error": None}
        
        except Exception as e:
            task.exit_code = 1
            task.error_output = str(e)
            return {"task": task, "success": False, "error": str(e)}

    def get_orchestration_status(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of pipeline orchestration."""
        if pipeline_id not in self.active_orchestrations:
            return None
        
        task_graph = self.active_orchestrations[pipeline_id]
        
        status_counts = {}
        for status in TaskStatus:
            status_counts[status.value] = sum(
                1 for task in task_graph.tasks.values()
                if task.status == status
            )
        
        return {
            "pipeline_id": pipeline_id,
            "total_tasks": len(task_graph.tasks),
            "status_breakdown": status_counts,
            "resource_usage": {
                "active_tasks": len(self.resource_pool.active_tasks),
                "cpu_usage": self.resource_pool.cpu_usage,
                "memory_usage": self.resource_pool.memory_usage
            }
        }

    def get_orchestration_statistics(self) -> Dict[str, Any]:
        """Get comprehensive orchestration statistics."""
        total_executions = len(self.execution_history)
        
        if total_executions == 0:
            return {
                "total_executions": 0,
                "average_execution_time": 0,
                "average_success_rate": 0,
                "task_type_performance": {}
            }
        
        # Calculate averages
        avg_execution_time = sum(
            exec["execution_time"] for exec in self.execution_history
        ) / total_executions
        
        avg_success_rate = sum(
            exec["success_rate"] for exec in self.execution_history
        ) / total_executions
        
        # Task type performance
        task_type_performance = {}
        for task_type, durations in self.task_performance_history.items():
            if durations:
                task_type_performance[task_type.value] = {
                    "average_duration": sum(durations) / len(durations),
                    "execution_count": len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations)
                }
        
        return {
            "total_executions": total_executions,
            "average_execution_time": avg_execution_time,
            "average_success_rate": avg_success_rate,
            "task_type_performance": task_type_performance,
            "active_orchestrations": len(self.active_orchestrations)
        }


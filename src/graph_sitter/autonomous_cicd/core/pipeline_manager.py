"""
Autonomous Pipeline Manager

Handles automated pipeline creation, configuration, and optimization
with dynamic adaptation based on project type and requirements.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import yaml
from pydantic import BaseModel, Field

from ..models.pipeline_models import (
    PipelineConfig,
    PipelineExecution,
    PipelineOptimization,
    PipelineStatus,
    ProjectType,
)
from ..utils.performance_analyzer import PerformanceAnalyzer
from ..utils.resource_optimizer import ResourceOptimizer


class PipelineStrategy(Enum):
    """Pipeline execution strategies."""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


@dataclass
class PipelineMetrics:
    """Pipeline execution metrics."""
    execution_time: float
    success_rate: float
    resource_usage: Dict[str, float]
    bottlenecks: List[str]
    optimization_opportunities: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class AutonomousPipelineManager:
    """
    Manages autonomous CI/CD pipeline operations with intelligent
    optimization and dynamic adaptation capabilities.
    """

    def __init__(
        self,
        config_path: Optional[Path] = None,
        enable_optimization: bool = True,
        enable_parallel_processing: bool = True,
    ):
        self.config_path = config_path or Path(".github/workflows")
        self.enable_optimization = enable_optimization
        self.enable_parallel_processing = enable_parallel_processing
        
        self.logger = logging.getLogger(__name__)
        self.performance_analyzer = PerformanceAnalyzer()
        self.resource_optimizer = ResourceOptimizer()
        
        # Pipeline state tracking
        self.active_pipelines: Dict[str, PipelineExecution] = {}
        self.pipeline_history: List[PipelineExecution] = []
        self.optimization_cache: Dict[str, PipelineOptimization] = {}
        
        # Configuration
        self.default_config = self._load_default_config()
        self.project_configs: Dict[ProjectType, PipelineConfig] = {}
        
        # Initialize project type detection
        self._initialize_project_detection()

    def _load_default_config(self) -> PipelineConfig:
        """Load default pipeline configuration."""
        return PipelineConfig(
            name="default",
            strategy=PipelineStrategy.ADAPTIVE,
            timeout_minutes=30,
            retry_attempts=3,
            parallel_jobs=4,
            resource_limits={
                "cpu": "2",
                "memory": "4Gi",
                "disk": "10Gi"
            },
            quality_gates={
                "test_coverage": 80.0,
                "code_quality": "A",
                "security_scan": True,
                "performance_benchmark": True
            }
        )

    def _initialize_project_detection(self) -> None:
        """Initialize project type detection patterns."""
        self.project_configs = {
            ProjectType.PYTHON: PipelineConfig(
                name="python_project",
                strategy=PipelineStrategy.PARALLEL,
                stages=[
                    "setup_python",
                    "install_dependencies", 
                    "lint_code",
                    "run_tests",
                    "security_scan",
                    "build_package",
                    "deploy"
                ],
                tools=["pytest", "mypy", "ruff", "bandit", "coverage"],
                timeout_minutes=25
            ),
            ProjectType.TYPESCRIPT: PipelineConfig(
                name="typescript_project",
                strategy=PipelineStrategy.PARALLEL,
                stages=[
                    "setup_node",
                    "install_dependencies",
                    "lint_code", 
                    "type_check",
                    "run_tests",
                    "build_project",
                    "deploy"
                ],
                tools=["eslint", "typescript", "jest", "webpack"],
                timeout_minutes=20
            ),
            ProjectType.MIXED: PipelineConfig(
                name="mixed_project",
                strategy=PipelineStrategy.HYBRID,
                stages=[
                    "detect_languages",
                    "setup_environments",
                    "install_all_dependencies",
                    "parallel_linting",
                    "parallel_testing",
                    "integration_tests",
                    "build_all",
                    "deploy"
                ],
                timeout_minutes=40
            )
        }

    async def create_pipeline(
        self,
        project_path: Path,
        config_override: Optional[Dict[str, Any]] = None
    ) -> PipelineExecution:
        """
        Create an optimized pipeline configuration for the project.
        
        Args:
            project_path: Path to the project directory
            config_override: Optional configuration overrides
            
        Returns:
            PipelineExecution instance
        """
        self.logger.info(f"Creating pipeline for project: {project_path}")
        
        # Detect project type
        project_type = await self._detect_project_type(project_path)
        self.logger.info(f"Detected project type: {project_type}")
        
        # Get base configuration
        base_config = self.project_configs.get(project_type, self.default_config)
        
        # Apply optimizations if enabled
        if self.enable_optimization:
            optimized_config = await self._optimize_pipeline_config(
                base_config, project_path
            )
        else:
            optimized_config = base_config
            
        # Apply overrides
        if config_override:
            optimized_config = self._apply_config_overrides(
                optimized_config, config_override
            )
        
        # Create pipeline execution
        pipeline_execution = PipelineExecution(
            id=f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            config=optimized_config,
            project_path=project_path,
            project_type=project_type,
            status=PipelineStatus.CREATED,
            created_at=datetime.now()
        )
        
        # Store in active pipelines
        self.active_pipelines[pipeline_execution.id] = pipeline_execution
        
        # Generate workflow files
        await self._generate_workflow_files(pipeline_execution)
        
        self.logger.info(f"Pipeline created: {pipeline_execution.id}")
        return pipeline_execution

    async def _detect_project_type(self, project_path: Path) -> ProjectType:
        """Detect the project type based on files and structure."""
        files = list(project_path.rglob("*"))
        file_names = {f.name for f in files if f.is_file()}
        
        has_python = any(
            f in file_names for f in ["pyproject.toml", "setup.py", "requirements.txt"]
        ) or any(f.suffix == ".py" for f in files)
        
        has_typescript = any(
            f in file_names for f in ["tsconfig.json", "package.json"]
        ) or any(f.suffix in [".ts", ".tsx"] for f in files)
        
        has_javascript = any(
            f in file_names for f in ["package.json", "yarn.lock"]
        ) or any(f.suffix in [".js", ".jsx"] for f in files)
        
        if has_python and (has_typescript or has_javascript):
            return ProjectType.MIXED
        elif has_python:
            return ProjectType.PYTHON
        elif has_typescript:
            return ProjectType.TYPESCRIPT
        elif has_javascript:
            return ProjectType.JAVASCRIPT
        else:
            return ProjectType.GENERIC

    async def _optimize_pipeline_config(
        self, base_config: PipelineConfig, project_path: Path
    ) -> PipelineConfig:
        """Optimize pipeline configuration based on project analysis."""
        self.logger.info("Optimizing pipeline configuration")
        
        # Analyze project complexity
        complexity_metrics = await self._analyze_project_complexity(project_path)
        
        # Optimize based on historical data
        historical_optimization = self._get_historical_optimization(base_config.name)
        
        # Resource optimization
        optimized_resources = await self.resource_optimizer.optimize_resources(
            base_config.resource_limits, complexity_metrics
        )
        
        # Create optimized config
        optimized_config = base_config.copy()
        optimized_config.resource_limits = optimized_resources
        
        # Adjust timeout based on complexity
        if complexity_metrics.get("high_complexity", False):
            optimized_config.timeout_minutes = int(base_config.timeout_minutes * 1.5)
        
        # Optimize parallel jobs
        if self.enable_parallel_processing:
            optimal_jobs = self._calculate_optimal_parallel_jobs(complexity_metrics)
            optimized_config.parallel_jobs = optimal_jobs
        
        # Apply historical optimizations
        if historical_optimization:
            optimized_config = self._apply_historical_optimization(
                optimized_config, historical_optimization
            )
        
        return optimized_config

    async def _analyze_project_complexity(self, project_path: Path) -> Dict[str, Any]:
        """Analyze project complexity metrics."""
        metrics = {}
        
        # Count files and lines of code
        total_files = 0
        total_lines = 0
        
        for file_path in project_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".py", ".ts", ".js", ".tsx", ".jsx"]:
                total_files += 1
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        total_lines += len(f.readlines())
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        metrics["total_files"] = total_files
        metrics["total_lines"] = total_lines
        metrics["high_complexity"] = total_files > 100 or total_lines > 10000
        
        # Analyze dependencies
        dependencies = await self._analyze_dependencies(project_path)
        metrics["dependency_count"] = len(dependencies)
        metrics["has_heavy_dependencies"] = any(
            dep in dependencies for dep in ["tensorflow", "pytorch", "pandas", "numpy"]
        )
        
        return metrics

    async def _analyze_dependencies(self, project_path: Path) -> List[str]:
        """Analyze project dependencies."""
        dependencies = []
        
        # Python dependencies
        pyproject_path = project_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomllib
                with open(pyproject_path, 'rb') as f:
                    data = tomllib.load(f)
                    deps = data.get("project", {}).get("dependencies", [])
                    dependencies.extend([dep.split("==")[0].split(">=")[0] for dep in deps])
            except Exception:
                pass
        
        # Node.js dependencies
        package_json_path = project_path / "package.json"
        if package_json_path.exists():
            try:
                import json
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = data.get("dependencies", {})
                    dev_deps = data.get("devDependencies", {})
                    dependencies.extend(list(deps.keys()) + list(dev_deps.keys()))
            except Exception:
                pass
        
        return dependencies

    def _calculate_optimal_parallel_jobs(self, complexity_metrics: Dict[str, Any]) -> int:
        """Calculate optimal number of parallel jobs."""
        base_jobs = 4
        
        if complexity_metrics.get("high_complexity", False):
            return min(base_jobs + 2, 8)
        elif complexity_metrics.get("has_heavy_dependencies", False):
            return min(base_jobs + 1, 6)
        else:
            return base_jobs

    def _get_historical_optimization(self, config_name: str) -> Optional[PipelineOptimization]:
        """Get historical optimization data for configuration."""
        return self.optimization_cache.get(config_name)

    def _apply_historical_optimization(
        self, config: PipelineConfig, optimization: PipelineOptimization
    ) -> PipelineConfig:
        """Apply historical optimization to configuration."""
        optimized_config = config.copy()
        
        # Apply successful optimizations
        if optimization.successful_optimizations:
            for opt in optimization.successful_optimizations:
                if opt["type"] == "timeout_adjustment":
                    optimized_config.timeout_minutes = opt["value"]
                elif opt["type"] == "parallel_jobs":
                    optimized_config.parallel_jobs = opt["value"]
                elif opt["type"] == "resource_limits":
                    optimized_config.resource_limits.update(opt["value"])
        
        return optimized_config

    def _apply_config_overrides(
        self, config: PipelineConfig, overrides: Dict[str, Any]
    ) -> PipelineConfig:
        """Apply configuration overrides."""
        config_dict = config.dict()
        config_dict.update(overrides)
        return PipelineConfig(**config_dict)

    async def _generate_workflow_files(self, pipeline_execution: PipelineExecution) -> None:
        """Generate GitHub Actions workflow files."""
        workflow_content = self._create_workflow_yaml(pipeline_execution)
        
        # Ensure workflows directory exists
        workflows_dir = self.config_path
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # Write workflow file
        workflow_file = workflows_dir / f"autonomous_{pipeline_execution.id}.yml"
        with open(workflow_file, 'w') as f:
            f.write(workflow_content)
        
        self.logger.info(f"Generated workflow file: {workflow_file}")

    def _create_workflow_yaml(self, pipeline_execution: PipelineExecution) -> str:
        """Create GitHub Actions workflow YAML content."""
        config = pipeline_execution.config
        
        workflow = {
            "name": f"Autonomous Pipeline - {config.name}",
            "on": {
                "push": {"branches": ["develop", "main"]},
                "pull_request": {"branches": ["develop", "main"]},
                "workflow_dispatch": {}
            },
            "jobs": {
                "autonomous_pipeline": {
                    "runs-on": "ubuntu-latest",
                    "timeout-minutes": config.timeout_minutes,
                    "strategy": {
                        "matrix": {
                            "group": list(range(1, config.parallel_jobs + 1))
                        }
                    } if config.parallel_jobs > 1 else None,
                    "steps": self._create_workflow_steps(pipeline_execution)
                }
            }
        }
        
        # Remove None values
        if workflow["jobs"]["autonomous_pipeline"]["strategy"] is None:
            del workflow["jobs"]["autonomous_pipeline"]["strategy"]
        
        return yaml.dump(workflow, default_flow_style=False, sort_keys=False)

    def _create_workflow_steps(self, pipeline_execution: PipelineExecution) -> List[Dict[str, Any]]:
        """Create workflow steps based on pipeline configuration."""
        config = pipeline_execution.config
        steps = []
        
        # Checkout step
        steps.append({
            "name": "Checkout code",
            "uses": "actions/checkout@v4",
            "with": {"fetch-depth": 0}
        })
        
        # Setup steps based on project type
        if pipeline_execution.project_type == ProjectType.PYTHON:
            steps.extend(self._create_python_steps(config))
        elif pipeline_execution.project_type == ProjectType.TYPESCRIPT:
            steps.extend(self._create_typescript_steps(config))
        elif pipeline_execution.project_type == ProjectType.MIXED:
            steps.extend(self._create_mixed_steps(config))
        
        # Quality assurance steps
        steps.extend(self._create_qa_steps(config))
        
        # Monitoring and reporting steps
        steps.extend(self._create_monitoring_steps(pipeline_execution))
        
        return steps

    def _create_python_steps(self, config: PipelineConfig) -> List[Dict[str, Any]]:
        """Create Python-specific workflow steps."""
        return [
            {
                "name": "Setup Python",
                "uses": "actions/setup-python@v4",
                "with": {"python-version": "3.12"}
            },
            {
                "name": "Install UV",
                "run": "pip install uv"
            },
            {
                "name": "Install dependencies",
                "run": "uv sync"
            },
            {
                "name": "Run linting",
                "run": "uv run ruff check ."
            },
            {
                "name": "Run type checking",
                "run": "uv run mypy ."
            },
            {
                "name": "Run tests",
                "run": "uv run pytest --cov=src --cov-report=xml"
            }
        ]

    def _create_typescript_steps(self, config: PipelineConfig) -> List[Dict[str, Any]]:
        """Create TypeScript-specific workflow steps."""
        return [
            {
                "name": "Setup Node.js",
                "uses": "actions/setup-node@v4",
                "with": {"node-version": "18"}
            },
            {
                "name": "Install dependencies",
                "run": "npm ci"
            },
            {
                "name": "Run linting",
                "run": "npm run lint"
            },
            {
                "name": "Run type checking",
                "run": "npm run type-check"
            },
            {
                "name": "Run tests",
                "run": "npm run test"
            },
            {
                "name": "Build project",
                "run": "npm run build"
            }
        ]

    def _create_mixed_steps(self, config: PipelineConfig) -> List[Dict[str, Any]]:
        """Create steps for mixed-language projects."""
        steps = []
        steps.extend(self._create_python_steps(config))
        steps.extend(self._create_typescript_steps(config))
        
        # Add integration test step
        steps.append({
            "name": "Run integration tests",
            "run": "uv run pytest tests/integration/"
        })
        
        return steps

    def _create_qa_steps(self, config: PipelineConfig) -> List[Dict[str, Any]]:
        """Create quality assurance steps."""
        steps = []
        
        if config.quality_gates.get("security_scan", False):
            steps.append({
                "name": "Security scan",
                "run": "uv run bandit -r src/"
            })
        
        if config.quality_gates.get("performance_benchmark", False):
            steps.append({
                "name": "Performance benchmark",
                "run": "uv run pytest tests/performance/ --benchmark-only"
            })
        
        return steps

    def _create_monitoring_steps(self, pipeline_execution: PipelineExecution) -> List[Dict[str, Any]]:
        """Create monitoring and reporting steps."""
        return [
            {
                "name": "Upload coverage reports",
                "uses": "codecov/codecov-action@v3",
                "with": {"file": "./coverage.xml"}
            },
            {
                "name": "Report pipeline metrics",
                "run": f"echo 'Pipeline {pipeline_execution.id} completed'"
            }
        ]

    async def execute_pipeline(self, pipeline_id: str) -> PipelineExecution:
        """Execute a pipeline and monitor its progress."""
        if pipeline_id not in self.active_pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        pipeline = self.active_pipelines[pipeline_id]
        pipeline.status = PipelineStatus.RUNNING
        pipeline.started_at = datetime.now()
        
        self.logger.info(f"Executing pipeline: {pipeline_id}")
        
        try:
            # Monitor pipeline execution
            await self._monitor_pipeline_execution(pipeline)
            
            pipeline.status = PipelineStatus.SUCCESS
            pipeline.completed_at = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            pipeline.status = PipelineStatus.FAILED
            pipeline.error_message = str(e)
            pipeline.completed_at = datetime.now()
        
        # Move to history
        self.pipeline_history.append(pipeline)
        del self.active_pipelines[pipeline_id]
        
        # Update optimization cache
        await self._update_optimization_cache(pipeline)
        
        return pipeline

    async def _monitor_pipeline_execution(self, pipeline: PipelineExecution) -> None:
        """Monitor pipeline execution and collect metrics."""
        start_time = datetime.now()
        
        # Simulate pipeline monitoring
        # In real implementation, this would integrate with GitHub Actions API
        await asyncio.sleep(1)  # Placeholder for actual monitoring
        
        # Collect metrics
        execution_time = (datetime.now() - start_time).total_seconds()
        metrics = PipelineMetrics(
            execution_time=execution_time,
            success_rate=1.0,  # Would be calculated from actual results
            resource_usage={"cpu": 0.5, "memory": 0.3},
            bottlenecks=[],
            optimization_opportunities=[]
        )
        
        pipeline.metrics = metrics

    async def _update_optimization_cache(self, pipeline: PipelineExecution) -> None:
        """Update optimization cache with pipeline results."""
        config_name = pipeline.config.name
        
        if config_name not in self.optimization_cache:
            self.optimization_cache[config_name] = PipelineOptimization(
                config_name=config_name,
                successful_optimizations=[],
                failed_optimizations=[],
                performance_history=[]
            )
        
        optimization = self.optimization_cache[config_name]
        
        # Add performance data
        if pipeline.metrics:
            optimization.performance_history.append({
                "timestamp": pipeline.completed_at.isoformat(),
                "execution_time": pipeline.metrics.execution_time,
                "success_rate": pipeline.metrics.success_rate,
                "resource_usage": pipeline.metrics.resource_usage
            })
        
        # Analyze for optimization opportunities
        if pipeline.status == PipelineStatus.SUCCESS and pipeline.metrics:
            await self._analyze_optimization_opportunities(pipeline, optimization)

    async def _analyze_optimization_opportunities(
        self, pipeline: PipelineExecution, optimization: PipelineOptimization
    ) -> None:
        """Analyze pipeline for optimization opportunities."""
        if not pipeline.metrics:
            return
        
        metrics = pipeline.metrics
        
        # Check for timeout optimization
        if metrics.execution_time < pipeline.config.timeout_minutes * 60 * 0.5:
            optimization.successful_optimizations.append({
                "type": "timeout_adjustment",
                "value": int(pipeline.config.timeout_minutes * 0.8),
                "reason": "Pipeline completed well under timeout"
            })
        
        # Check for resource optimization
        if metrics.resource_usage.get("cpu", 0) < 0.3:
            optimization.successful_optimizations.append({
                "type": "resource_limits",
                "value": {"cpu": "1"},
                "reason": "Low CPU utilization detected"
            })

    def get_pipeline_status(self, pipeline_id: str) -> Optional[PipelineStatus]:
        """Get the current status of a pipeline."""
        if pipeline_id in self.active_pipelines:
            return self.active_pipelines[pipeline_id].status
        
        # Check history
        for pipeline in self.pipeline_history:
            if pipeline.id == pipeline_id:
                return pipeline.status
        
        return None

    def get_active_pipelines(self) -> List[PipelineExecution]:
        """Get all currently active pipelines."""
        return list(self.active_pipelines.values())

    def get_pipeline_metrics(self, pipeline_id: str) -> Optional[PipelineMetrics]:
        """Get metrics for a specific pipeline."""
        if pipeline_id in self.active_pipelines:
            return self.active_pipelines[pipeline_id].metrics
        
        for pipeline in self.pipeline_history:
            if pipeline.id == pipeline_id:
                return pipeline.metrics
        
        return None

    async def optimize_existing_pipelines(self) -> Dict[str, Any]:
        """Optimize all existing pipeline configurations."""
        optimization_results = {}
        
        for config_name, optimization in self.optimization_cache.items():
            if optimization.performance_history:
                # Analyze performance trends
                recent_performance = optimization.performance_history[-10:]
                avg_execution_time = sum(
                    p["execution_time"] for p in recent_performance
                ) / len(recent_performance)
                
                optimization_results[config_name] = {
                    "avg_execution_time": avg_execution_time,
                    "optimization_count": len(optimization.successful_optimizations),
                    "recommendations": optimization.successful_optimizations[-5:]
                }
        
        return optimization_results


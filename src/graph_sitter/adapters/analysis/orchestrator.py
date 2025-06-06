"""
Analysis Orchestrator

Coordinates and orchestrates all analysis operations.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from .config.analysis_config import AnalysisConfig
from .core.analysis_engine import AnalysisEngine, AnalysisResult


@dataclass
class AnalysisTask:
    """Represents an analysis task."""
    
    name: str
    function: Callable
    args: tuple
    kwargs: dict
    priority: int = 0
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class AnalysisOrchestrator:
    """
    Orchestrates complex analysis operations across multiple modules.
    
    Provides task scheduling, dependency management, and parallel execution
    for comprehensive codebase analysis.
    """
    
    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize the analysis orchestrator.
        
        Args:
            config: Analysis configuration
        """
        self.config = config or AnalysisConfig()
        self.logger = logging.getLogger(__name__)
        self.tasks = {}
        self.results = {}
        self.completed_tasks = set()
        
        # Setup thread pool for parallel execution
        max_workers = self.config.performance.max_worker_threads
        if max_workers is None:
            max_workers = min(32, (Path().cwd().stat().st_size or 4) + 4)
        
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    def add_task(
        self, 
        name: str, 
        function: Callable, 
        args: tuple = (), 
        kwargs: dict = None,
        priority: int = 0,
        dependencies: List[str] = None
    ):
        """
        Add an analysis task to the orchestrator.
        
        Args:
            name: Unique name for the task
            function: Function to execute
            args: Arguments for the function
            kwargs: Keyword arguments for the function
            priority: Task priority (higher = executed first)
            dependencies: List of task names this task depends on
        """
        if kwargs is None:
            kwargs = {}
        
        task = AnalysisTask(
            name=name,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            dependencies=dependencies or []
        )
        
        self.tasks[name] = task
        self.logger.debug(f"Added task: {name}")
    
    def execute_tasks(self) -> Dict[str, Any]:
        """
        Execute all tasks in dependency order with parallel execution.
        
        Returns:
            Dictionary of task results
        """
        self.logger.info("Starting task execution")
        
        # Validate dependencies
        self._validate_dependencies()
        
        # Execute tasks in dependency order
        while len(self.completed_tasks) < len(self.tasks):
            # Find ready tasks (dependencies satisfied)
            ready_tasks = self._get_ready_tasks()
            
            if not ready_tasks:
                remaining = set(self.tasks.keys()) - self.completed_tasks
                raise RuntimeError(f"Circular dependency detected in tasks: {remaining}")
            
            # Execute ready tasks in parallel
            self._execute_parallel_tasks(ready_tasks)
        
        self.logger.info("All tasks completed")
        return self.results
    
    def execute_analysis_pipeline(self, codebase_path: str) -> AnalysisResult:
        """
        Execute a complete analysis pipeline.
        
        Args:
            codebase_path: Path to the codebase to analyze
            
        Returns:
            Comprehensive analysis result
        """
        self.logger.info(f"Starting analysis pipeline for: {codebase_path}")
        
        # Setup analysis pipeline tasks
        self._setup_analysis_pipeline(codebase_path)
        
        # Execute all tasks
        task_results = self.execute_tasks()
        
        # Combine results into final analysis result
        final_result = self._combine_results(task_results)
        
        self.logger.info("Analysis pipeline completed")
        return final_result
    
    def _validate_dependencies(self):
        """Validate that all task dependencies exist."""
        for task_name, task in self.tasks.items():
            for dep in task.dependencies:
                if dep not in self.tasks:
                    raise ValueError(f"Task '{task_name}' depends on non-existent task '{dep}'")
    
    def _get_ready_tasks(self) -> List[str]:
        """Get tasks that are ready to execute (dependencies satisfied)."""
        ready = []
        
        for task_name, task in self.tasks.items():
            if task_name in self.completed_tasks:
                continue
            
            # Check if all dependencies are completed
            if all(dep in self.completed_tasks for dep in task.dependencies):
                ready.append(task_name)
        
        # Sort by priority (higher priority first)
        ready.sort(key=lambda name: self.tasks[name].priority, reverse=True)
        return ready
    
    def _execute_parallel_tasks(self, task_names: List[str]):
        """Execute multiple tasks in parallel."""
        if not task_names:
            return
        
        # Submit tasks to thread pool
        future_to_task = {}
        for task_name in task_names:
            task = self.tasks[task_name]
            future = self.executor.submit(self._execute_task, task_name, task)
            future_to_task[future] = task_name
        
        # Wait for completion
        for future in as_completed(future_to_task):
            task_name = future_to_task[future]
            try:
                result = future.result()
                self.results[task_name] = result
                self.completed_tasks.add(task_name)
                self.logger.debug(f"Task completed: {task_name}")
            except Exception as e:
                self.logger.error(f"Task failed: {task_name} - {e}")
                self.results[task_name] = {"error": str(e)}
                self.completed_tasks.add(task_name)  # Mark as completed to avoid blocking
    
    def _execute_task(self, task_name: str, task: AnalysisTask) -> Any:
        """Execute a single task."""
        try:
            self.logger.debug(f"Executing task: {task_name}")
            
            # Inject dependency results into kwargs if needed
            if 'dependency_results' in task.function.__code__.co_varnames:
                dep_results = {dep: self.results.get(dep) for dep in task.dependencies}
                task.kwargs['dependency_results'] = dep_results
            
            result = task.function(*task.args, **task.kwargs)
            return result
            
        except Exception as e:
            self.logger.error(f"Task execution failed: {task_name} - {e}")
            raise
    
    def _setup_analysis_pipeline(self, codebase_path: str):
        """Setup the complete analysis pipeline."""
        from graph_sitter.core.codebase import Codebase
        from codegen.configs import CodebaseConfig
        
        # Create codebase loading task
        self.add_task(
            "load_codebase",
            self._load_codebase,
            args=(codebase_path,),
            priority=100
        )
        
        # Core analysis tasks
        self.add_task(
            "codebase_summary",
            self._analyze_codebase_summary,
            dependencies=["load_codebase"],
            priority=90
        )
        
        self.add_task(
            "file_analysis",
            self._analyze_files,
            dependencies=["load_codebase"],
            priority=80
        )
        
        self.add_task(
            "class_analysis",
            self._analyze_classes,
            dependencies=["load_codebase"],
            priority=80
        )
        
        self.add_task(
            "function_analysis",
            self._analyze_functions,
            dependencies=["load_codebase"],
            priority=80
        )
        
        # Dependency analysis
        if self.config.enable_dependency_analysis:
            self.add_task(
                "dependency_analysis",
                self._analyze_dependencies,
                dependencies=["load_codebase"],
                priority=70
            )
        
        # Dead code detection
        if self.config.enable_dead_code_detection:
            self.add_task(
                "dead_code_detection",
                self._detect_dead_code,
                dependencies=["load_codebase"],
                priority=60
            )
        
        # Test analysis
        if self.config.enable_test_analysis:
            self.add_task(
                "test_analysis",
                self._analyze_tests,
                dependencies=["load_codebase"],
                priority=60
            )
        
        # Metrics collection (depends on other analyses)
        if self.config.enable_metrics_collection:
            self.add_task(
                "metrics_collection",
                self._collect_metrics,
                dependencies=[
                    "codebase_summary", "file_analysis", 
                    "class_analysis", "function_analysis"
                ],
                priority=50
            )
        
        # Issue detection (depends on all analyses)
        self.add_task(
            "issue_detection",
            self._detect_issues,
            dependencies=[
                "codebase_summary", "file_analysis", 
                "class_analysis", "function_analysis"
            ],
            priority=40
        )
    
    def _combine_results(self, task_results: Dict[str, Any]) -> AnalysisResult:
        """Combine task results into a final analysis result."""
        result = AnalysisResult()
        
        # Extract results from tasks
        result.codebase_summary = task_results.get("codebase_summary", {})
        result.file_summaries = task_results.get("file_analysis", {})
        result.class_summaries = task_results.get("class_analysis", {})
        result.function_summaries = task_results.get("function_analysis", {})
        result.dependencies = task_results.get("dependency_analysis", {})
        result.dead_code = task_results.get("dead_code_detection", [])
        result.test_analysis = task_results.get("test_analysis", {})
        result.metrics = task_results.get("metrics_collection", {})
        result.issues = task_results.get("issue_detection", [])
        
        # Set metadata
        import time
        result.timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        result.execution_time = 0.0  # Would be calculated from task timings
        
        return result
    
    # Task implementation methods
    def _load_codebase(self, codebase_path: str):
        """Load codebase task."""
        from graph_sitter.core.codebase import Codebase
        from codegen.configs import CodebaseConfig
        
        gs_config = CodebaseConfig(**self.config.graph_sitter.to_dict())
        codebase = Codebase(codebase_path, config=gs_config)
        return codebase
    
    def _analyze_codebase_summary(self, dependency_results: Dict[str, Any]):
        """Analyze codebase summary task."""
        codebase = dependency_results["load_codebase"]
        engine = AnalysisEngine(self.config)
        return engine._analyze_codebase_summary(codebase)
    
    def _analyze_files(self, dependency_results: Dict[str, Any]):
        """Analyze files task."""
        codebase = dependency_results["load_codebase"]
        engine = AnalysisEngine(self.config)
        return engine._analyze_files(codebase)
    
    def _analyze_classes(self, dependency_results: Dict[str, Any]):
        """Analyze classes task."""
        codebase = dependency_results["load_codebase"]
        engine = AnalysisEngine(self.config)
        return engine._analyze_classes(codebase)
    
    def _analyze_functions(self, dependency_results: Dict[str, Any]):
        """Analyze functions task."""
        codebase = dependency_results["load_codebase"]
        engine = AnalysisEngine(self.config)
        return engine._analyze_functions(codebase)
    
    def _analyze_dependencies(self, dependency_results: Dict[str, Any]):
        """Analyze dependencies task."""
        codebase = dependency_results["load_codebase"]
        engine = AnalysisEngine(self.config)
        return engine._analyze_dependencies(codebase)
    
    def _detect_dead_code(self, dependency_results: Dict[str, Any]):
        """Detect dead code task."""
        codebase = dependency_results["load_codebase"]
        engine = AnalysisEngine(self.config)
        return engine._detect_dead_code(codebase)
    
    def _analyze_tests(self, dependency_results: Dict[str, Any]):
        """Analyze tests task."""
        codebase = dependency_results["load_codebase"]
        engine = AnalysisEngine(self.config)
        return engine._analyze_tests(codebase)
    
    def _collect_metrics(self, dependency_results: Dict[str, Any]):
        """Collect metrics task."""
        # Create a mock result with the dependency data
        from .core.analysis_engine import AnalysisResult
        mock_result = AnalysisResult()
        mock_result.file_summaries = dependency_results.get("file_analysis", {})
        mock_result.class_summaries = dependency_results.get("class_analysis", {})
        mock_result.function_summaries = dependency_results.get("function_analysis", {})
        mock_result.dependencies = dependency_results.get("dependency_analysis", {})
        mock_result.dead_code = dependency_results.get("dead_code_detection", [])
        mock_result.test_analysis = dependency_results.get("test_analysis", {})
        
        codebase = dependency_results["load_codebase"]
        engine = AnalysisEngine(self.config)
        return engine._collect_metrics(codebase, mock_result)
    
    def _detect_issues(self, dependency_results: Dict[str, Any]):
        """Detect issues task."""
        # Create a mock result with the dependency data
        from .core.analysis_engine import AnalysisResult
        mock_result = AnalysisResult()
        mock_result.file_summaries = dependency_results.get("file_analysis", {})
        mock_result.class_summaries = dependency_results.get("class_analysis", {})
        mock_result.function_summaries = dependency_results.get("function_analysis", {})
        
        codebase = dependency_results["load_codebase"]
        engine = AnalysisEngine(self.config)
        return engine._detect_issues(codebase, mock_result)
    
    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)


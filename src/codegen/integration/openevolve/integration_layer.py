"""
OpenEvolve Integration Layer

Main integration class that coordinates between OpenEvolve agents and the graph-sitter
evaluation system.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import importlib.util
import sys

from .config import OpenEvolveConfig
from .agent_adapters import EvaluatorAgentAdapter, DatabaseAgentAdapter, ControllerAgentAdapter
from ..database.overlay import DatabaseOverlay
from ..evaluation.engine import EffectivenessEvaluator


@dataclass
class EvaluationResult:
    """Result of a component evaluation."""
    component_type: str
    component_name: str
    effectiveness_score: float
    performance_metrics: Dict[str, Any]
    execution_time_ms: int
    success: bool
    error_message: Optional[str] = None
    step_results: List[Dict[str, Any]] = None


class OpenEvolveIntegrator:
    """
    Main integration layer between OpenEvolve framework and graph-sitter evaluation system.
    
    This class orchestrates the evaluation of evaluator.py, database.py, and controller.py
    components using OpenEvolve agents for effectiveness analysis.
    """
    
    def __init__(self, config: Optional[OpenEvolveConfig] = None):
        """Initialize the OpenEvolve integrator."""
        self.config = config or OpenEvolveConfig.from_env()
        self.config.validate()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, self.config.log_level))
        
        # Initialize components
        self.database_overlay: Optional[DatabaseOverlay] = None
        self.effectiveness_evaluator: Optional[EffectivenessEvaluator] = None
        
        # Agent adapters
        self.evaluator_adapter: Optional[EvaluatorAgentAdapter] = None
        self.database_adapter: Optional[DatabaseAgentAdapter] = None
        self.controller_adapter: Optional[ControllerAgentAdapter] = None
        
        # State tracking
        self.current_session_id: Optional[str] = None
        self.is_initialized = False
        self.evaluation_cache: Dict[str, EvaluationResult] = {}
        
        self.logger.info("OpenEvolveIntegrator initialized with config: %s", self.config.to_dict())
    
    async def initialize(self) -> None:
        """Initialize the integration layer and all components."""
        if self.is_initialized:
            self.logger.warning("OpenEvolveIntegrator already initialized")
            return
        
        try:
            # Initialize database overlay
            self.database_overlay = DatabaseOverlay(
                database_url=self.config.database_url,
                schema_path=self.config.schema_path
            )
            await self.database_overlay.initialize()
            
            # Initialize effectiveness evaluator
            self.effectiveness_evaluator = EffectivenessEvaluator(
                database_overlay=self.database_overlay,
                config=self.config
            )
            
            # Initialize agent adapters
            await self._initialize_agent_adapters()
            
            # Create evaluation session
            self.current_session_id = await self.database_overlay.create_session(
                session_name=f"openevolve_integration_{int(time.time())}",
                description="OpenEvolve integration evaluation session"
            )
            
            self.is_initialized = True
            self.logger.info("OpenEvolveIntegrator successfully initialized with session: %s", 
                           self.current_session_id)
            
        except Exception as e:
            self.logger.error("Failed to initialize OpenEvolveIntegrator: %s", str(e))
            raise
    
    async def _initialize_agent_adapters(self) -> None:
        """Initialize OpenEvolve agent adapters."""
        try:
            # Load OpenEvolve agents dynamically if repo path is provided
            if self.config.openevolve_repo_path:
                await self._load_openevolve_agents()
            
            # Initialize adapters
            self.evaluator_adapter = EvaluatorAgentAdapter(self.config)
            self.database_adapter = DatabaseAgentAdapter(self.config)
            self.controller_adapter = ControllerAgentAdapter(self.config)
            
            await self.evaluator_adapter.initialize()
            await self.database_adapter.initialize()
            await self.controller_adapter.initialize()
            
            self.logger.info("Agent adapters initialized successfully")
            
        except Exception as e:
            self.logger.error("Failed to initialize agent adapters: %s", str(e))
            raise
    
    async def _load_openevolve_agents(self) -> None:
        """Dynamically load OpenEvolve agents from repository path."""
        if not self.config.openevolve_repo_path:
            return
        
        repo_path = Path(self.config.openevolve_repo_path)
        if not repo_path.exists():
            raise FileNotFoundError(f"OpenEvolve repository not found: {repo_path}")
        
        # Add OpenEvolve repo to Python path
        if str(repo_path) not in sys.path:
            sys.path.insert(0, str(repo_path))
        
        self.logger.info("Loaded OpenEvolve repository from: %s", repo_path)
    
    async def evaluate_component(
        self, 
        component_type: str, 
        component_name: str,
        component_instance: Any,
        evaluation_context: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate a specific component using OpenEvolve agents.
        
        Args:
            component_type: Type of component ('evaluator', 'database', 'controller')
            component_name: Name/identifier of the component
            component_instance: The actual component instance to evaluate
            evaluation_context: Additional context for evaluation
            
        Returns:
            EvaluationResult with effectiveness score and metrics
        """
        if not self.is_initialized:
            await self.initialize()
        
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"{component_type}:{component_name}"
            if self.config.enable_caching and cache_key in self.evaluation_cache:
                cached_result = self.evaluation_cache[cache_key]
                if time.time() - cached_result.performance_metrics.get('timestamp', 0) < self.config.cache_ttl_seconds:
                    self.logger.debug("Returning cached evaluation result for %s", cache_key)
                    return cached_result
            
            # Select appropriate adapter
            adapter = self._get_adapter_for_component(component_type)
            if not adapter:
                raise ValueError(f"No adapter available for component type: {component_type}")
            
            # Perform evaluation
            self.logger.info("Starting evaluation of %s component: %s", component_type, component_name)
            
            evaluation_result = await adapter.evaluate_component(
                component_instance=component_instance,
                component_name=component_name,
                context=evaluation_context or {}
            )
            
            execution_time_ms = int((time.time() - start_time) * 1000)
            
            # Create result object
            result = EvaluationResult(
                component_type=component_type,
                component_name=component_name,
                effectiveness_score=evaluation_result.get('effectiveness_score', 0.0),
                performance_metrics=evaluation_result.get('performance_metrics', {}),
                execution_time_ms=execution_time_ms,
                success=evaluation_result.get('success', False),
                error_message=evaluation_result.get('error_message'),
                step_results=evaluation_result.get('step_results', [])
            )
            
            # Store in database
            await self._store_evaluation_result(result)
            
            # Cache result
            if self.config.enable_caching:
                result.performance_metrics['timestamp'] = time.time()
                self.evaluation_cache[cache_key] = result
            
            self.logger.info("Completed evaluation of %s: effectiveness=%.4f, time=%dms", 
                           component_name, result.effectiveness_score, result.execution_time_ms)
            
            return result
            
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            error_result = EvaluationResult(
                component_type=component_type,
                component_name=component_name,
                effectiveness_score=0.0,
                performance_metrics={'error': str(e)},
                execution_time_ms=execution_time_ms,
                success=False,
                error_message=str(e)
            )
            
            await self._store_evaluation_result(error_result)
            self.logger.error("Evaluation failed for %s: %s", component_name, str(e))
            return error_result
    
    async def evaluate_all_components(
        self,
        components: Dict[str, Dict[str, Any]],
        evaluation_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, EvaluationResult]:
        """
        Evaluate multiple components concurrently.
        
        Args:
            components: Dict mapping component_type to {name: instance} mappings
            evaluation_context: Additional context for evaluation
            
        Returns:
            Dict mapping component names to evaluation results
        """
        if not self.is_initialized:
            await self.initialize()
        
        tasks = []
        component_names = []
        
        for component_type, component_instances in components.items():
            for component_name, component_instance in component_instances.items():
                task = self.evaluate_component(
                    component_type=component_type,
                    component_name=component_name,
                    component_instance=component_instance,
                    evaluation_context=evaluation_context
                )
                tasks.append(task)
                component_names.append(component_name)
        
        # Limit concurrent evaluations
        semaphore = asyncio.Semaphore(self.config.max_concurrent_evaluations)
        
        async def limited_evaluate(task):
            async with semaphore:
                return await task
        
        limited_tasks = [limited_evaluate(task) for task in tasks]
        results = await asyncio.gather(*limited_tasks, return_exceptions=True)
        
        # Process results
        evaluation_results = {}
        for component_name, result in zip(component_names, results):
            if isinstance(result, Exception):
                self.logger.error("Evaluation failed for %s: %s", component_name, str(result))
                evaluation_results[component_name] = EvaluationResult(
                    component_type="unknown",
                    component_name=component_name,
                    effectiveness_score=0.0,
                    performance_metrics={'error': str(result)},
                    execution_time_ms=0,
                    success=False,
                    error_message=str(result)
                )
            else:
                evaluation_results[component_name] = result
        
        return evaluation_results
    
    def _get_adapter_for_component(self, component_type: str) -> Optional[Any]:
        """Get the appropriate adapter for a component type."""
        adapter_map = {
            'evaluator': self.evaluator_adapter,
            'database': self.database_adapter,
            'controller': self.controller_adapter
        }
        return adapter_map.get(component_type)
    
    async def _store_evaluation_result(self, result: EvaluationResult) -> None:
        """Store evaluation result in database."""
        if not self.database_overlay or not self.current_session_id:
            return
        
        try:
            await self.database_overlay.store_component_evaluation(
                session_id=self.current_session_id,
                component_type=result.component_type,
                component_name=result.component_name,
                effectiveness_score=result.effectiveness_score,
                performance_metrics=result.performance_metrics,
                execution_time_ms=result.execution_time_ms,
                success_rate=1.0 if result.success else 0.0,
                error_count=0 if result.success else 1
            )
            
            # Store step results if available
            if result.step_results:
                for i, step_result in enumerate(result.step_results):
                    await self.database_overlay.store_evaluation_step(
                        component_evaluation_id=None,  # Will be set by database overlay
                        step_number=i + 1,
                        step_name=step_result.get('name', f'Step {i+1}'),
                        step_description=step_result.get('description', ''),
                        duration_ms=step_result.get('duration_ms', 0),
                        status=step_result.get('status', 'completed'),
                        input_data=step_result.get('input_data', {}),
                        output_data=step_result.get('output_data', {}),
                        error_message=step_result.get('error_message'),
                        effectiveness_contribution=step_result.get('effectiveness_contribution', 0.0)
                    )
            
        except Exception as e:
            self.logger.error("Failed to store evaluation result: %s", str(e))
    
    async def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current evaluation session."""
        if not self.database_overlay or not self.current_session_id:
            return {}
        
        return await self.database_overlay.get_session_summary(self.current_session_id)
    
    async def cleanup(self) -> None:
        """Cleanup resources and close connections."""
        try:
            if self.database_overlay:
                await self.database_overlay.cleanup()
            
            # Clear cache
            self.evaluation_cache.clear()
            
            self.is_initialized = False
            self.logger.info("OpenEvolveIntegrator cleanup completed")
            
        except Exception as e:
            self.logger.error("Error during cleanup: %s", str(e))
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()


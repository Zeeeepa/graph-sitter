"""
OpenEvolve Integration Adapter for Graph-Sitter Task Management System

This module provides the integration layer between Graph-Sitter's task management
system and OpenEvolve's evaluation framework for step-by-step effectiveness analysis.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import asyncpg
from pydantic import BaseModel, Field

from graph_sitter.configs.models.base_config import BaseConfig

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Result of an OpenEvolve evaluation"""
    
    task_id: str
    program_id: str
    scores: Dict[str, float] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    # Evolution tracking
    generation: int = 0
    parent_program_id: Optional[str] = None
    iteration_found: int = 0
    
    # Performance data
    evaluation_duration_ms: int = 0
    complexity_score: float = 0.0
    diversity_score: float = 0.0
    quality_score: float = 0.0
    
    # Status
    status: str = "completed"
    error_message: Optional[str] = None


@dataclass
class Program:
    """OpenEvolve Program representation"""
    
    id: str
    code: str
    language: str = "python"
    
    # Evolution information
    parent_id: Optional[str] = None
    generation: int = 0
    timestamp: float = field(default_factory=time.time)
    iteration_found: int = 0
    
    # Performance metrics
    metrics: Dict[str, float] = field(default_factory=dict)
    complexity: float = 0.0
    diversity: float = 0.0
    fitness_score: float = 0.0
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


class EvolutionConfig(BaseModel):
    """Configuration for OpenEvolve evolution process"""
    
    max_generations: int = Field(default=50, ge=1, le=1000)
    population_size: int = Field(default=10, ge=1, le=100)
    mutation_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    crossover_rate: float = Field(default=0.8, ge=0.0, le=1.0)
    selection_pressure: float = Field(default=2.0, ge=1.0, le=10.0)
    
    # Evaluation configuration
    evaluation_timeout_ms: int = Field(default=30000, ge=1000)
    parallel_evaluations: int = Field(default=4, ge=1, le=16)
    
    # Convergence criteria
    convergence_threshold: float = Field(default=0.001, ge=0.0)
    stagnation_generations: int = Field(default=10, ge=1)
    
    # Additional parameters
    elitism_rate: float = Field(default=0.1, ge=0.0, le=0.5)
    diversity_weight: float = Field(default=0.2, ge=0.0, le=1.0)


class OpenEvolveAdapter:
    """
    Adapter for integrating OpenEvolve evaluation system with Graph-Sitter
    
    This class provides the main interface for:
    - Task implementation evaluation
    - Program evolution tracking
    - Metrics synchronization
    - Workflow orchestration
    """
    
    def __init__(
        self,
        config: BaseConfig,
        database_url: str,
        openevolve_base_url: Optional[str] = None
    ):
        self.config = config
        self.database_url = database_url
        self.openevolve_base_url = openevolve_base_url or "http://localhost:8000"
        
        # Connection pools
        self.db_pool: Optional[asyncpg.Pool] = None
        self.http_session: Optional[aiohttp.ClientSession] = None
        
        # Caches
        self._program_cache: Dict[str, Program] = {}
        self._evaluation_cache: Dict[str, EvaluationResult] = {}
        
        logger.info(f"Initialized OpenEvolve adapter with base URL: {self.openevolve_base_url}")
    
    async def initialize(self) -> None:
        """Initialize database and HTTP connections"""
        try:
            # Initialize database pool
            self.db_pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20,
                command_timeout=60
            )
            
            # Initialize HTTP session
            timeout = aiohttp.ClientTimeout(total=300)
            self.http_session = aiohttp.ClientSession(timeout=timeout)
            
            logger.info("OpenEvolve adapter initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenEvolve adapter: {e}")
            raise
    
    async def close(self) -> None:
        """Close connections and cleanup resources"""
        if self.db_pool:
            await self.db_pool.close()
        
        if self.http_session:
            await self.http_session.close()
        
        logger.info("OpenEvolve adapter closed")
    
    async def evaluate_task_implementation(
        self,
        task_id: str,
        implementation_code: str,
        evaluation_criteria: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """
        Evaluate a task implementation using OpenEvolve's evaluation system
        
        Args:
            task_id: Unique identifier for the task
            implementation_code: Code to be evaluated
            evaluation_criteria: Specific criteria for evaluation
            context: Additional context for evaluation
            
        Returns:
            EvaluationResult with scores, metrics, and recommendations
        """
        start_time = time.time()
        program_id = str(uuid.uuid4())
        
        try:
            # Create program record
            program = Program(
                id=program_id,
                code=implementation_code,
                metadata=context or {}
            )
            
            # Store program in cache and database
            self._program_cache[program_id] = program
            await self._store_program_evolution(task_id, program)
            
            # Perform evaluation via OpenEvolve API
            evaluation_data = {
                "program_id": program_id,
                "code": implementation_code,
                "criteria": evaluation_criteria,
                "context": context or {}
            }
            
            async with self.http_session.post(
                f"{self.openevolve_base_url}/api/v1/evaluate",
                json=evaluation_data
            ) as response:
                if response.status == 200:
                    result_data = await response.json()
                    
                    # Create evaluation result
                    result = EvaluationResult(
                        task_id=task_id,
                        program_id=program_id,
                        scores=result_data.get("scores", {}),
                        metrics=result_data.get("metrics", {}),
                        recommendations=result_data.get("recommendations", []),
                        complexity_score=result_data.get("complexity_score", 0.0),
                        diversity_score=result_data.get("diversity_score", 0.0),
                        quality_score=result_data.get("quality_score", 0.0),
                        evaluation_duration_ms=int((time.time() - start_time) * 1000)
                    )
                    
                else:
                    error_msg = f"OpenEvolve API error: {response.status}"
                    result = EvaluationResult(
                        task_id=task_id,
                        program_id=program_id,
                        status="failed",
                        error_message=error_msg,
                        evaluation_duration_ms=int((time.time() - start_time) * 1000)
                    )
            
            # Store evaluation result
            await self._store_evaluation_result(result)
            self._evaluation_cache[program_id] = result
            
            return result
            
        except Exception as e:
            logger.error(f"Evaluation failed for task {task_id}: {e}")
            
            # Return error result
            result = EvaluationResult(
                task_id=task_id,
                program_id=program_id,
                status="failed",
                error_message=str(e),
                evaluation_duration_ms=int((time.time() - start_time) * 1000)
            )
            
            await self._store_evaluation_result(result)
            return result
    
    async def evaluate_multiple_implementations(
        self,
        implementations: List[Tuple[str, str, Dict[str, Any]]]  # (task_id, code, criteria)
    ) -> List[EvaluationResult]:
        """Batch evaluation of multiple implementations"""
        
        tasks = [
            self.evaluate_task_implementation(task_id, code, criteria)
            for task_id, code, criteria in implementations
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                task_id, _, _ = implementations[i]
                error_result = EvaluationResult(
                    task_id=task_id,
                    program_id=str(uuid.uuid4()),
                    status="failed",
                    error_message=str(result)
                )
                final_results.append(error_result)
            else:
                final_results.append(result)
        
        return final_results
    
    async def orchestrate_task_evolution(
        self,
        task_id: str,
        initial_implementation: str,
        evolution_config: EvolutionConfig
    ) -> Dict[str, Any]:
        """
        Orchestrate task implementation evolution using OpenEvolve
        
        Args:
            task_id: Task identifier
            initial_implementation: Starting implementation
            evolution_config: Evolution parameters
            
        Returns:
            Evolution results with best implementation and metrics
        """
        start_time = time.time()
        
        try:
            # Prepare evolution request
            evolution_data = {
                "task_id": task_id,
                "initial_code": initial_implementation,
                "config": evolution_config.dict()
            }
            
            # Start evolution process
            async with self.http_session.post(
                f"{self.openevolve_base_url}/api/v1/evolve",
                json=evolution_data
            ) as response:
                if response.status == 200:
                    evolution_result = await response.json()
                    
                    # Store evolution results
                    await self._store_evolution_results(task_id, evolution_result)
                    
                    return {
                        "status": "completed",
                        "task_id": task_id,
                        "best_implementation": evolution_result.get("best_code"),
                        "best_score": evolution_result.get("best_score"),
                        "generations": evolution_result.get("generations"),
                        "total_evaluations": evolution_result.get("total_evaluations"),
                        "convergence_achieved": evolution_result.get("converged", False),
                        "duration_ms": int((time.time() - start_time) * 1000),
                        "evolution_history": evolution_result.get("history", [])
                    }
                else:
                    error_msg = f"Evolution failed: HTTP {response.status}"
                    logger.error(error_msg)
                    return {
                        "status": "failed",
                        "task_id": task_id,
                        "error": error_msg,
                        "duration_ms": int((time.time() - start_time) * 1000)
                    }
                    
        except Exception as e:
            logger.error(f"Evolution orchestration failed for task {task_id}: {e}")
            return {
                "status": "failed",
                "task_id": task_id,
                "error": str(e),
                "duration_ms": int((time.time() - start_time) * 1000)
            }
    
    async def get_evolution_history(self, task_id: str) -> List[Program]:
        """Retrieve evolution history for a task"""
        
        if not self.db_pool:
            raise RuntimeError("Database pool not initialized")
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT 
                    program_id,
                    code,
                    language,
                    parent_id,
                    generation,
                    timestamp,
                    iteration_found,
                    metrics,
                    complexity,
                    diversity,
                    fitness_score,
                    metadata
                FROM program_evolution
                WHERE task_id = $1
                ORDER BY generation, iteration_found
            """, task_id)
            
            programs = []
            for row in rows:
                program = Program(
                    id=row['program_id'],
                    code=row['code'],
                    language=row['language'],
                    parent_id=row['parent_id'],
                    generation=row['generation'],
                    timestamp=row['timestamp'].timestamp() if row['timestamp'] else time.time(),
                    iteration_found=row['iteration_found'],
                    metrics=row['metrics'] or {},
                    complexity=float(row['complexity']) if row['complexity'] else 0.0,
                    diversity=float(row['diversity']) if row['diversity'] else 0.0,
                    fitness_score=float(row['fitness_score']) if row['fitness_score'] else 0.0,
                    metadata=row['metadata'] or {}
                )
                programs.append(program)
            
            return programs
    
    async def sync_metrics(
        self,
        task_id: str,
        graph_sitter_metrics: Dict[str, Any],
        openevolve_metrics: Dict[str, Any]
    ) -> None:
        """Synchronize metrics between Graph-Sitter and OpenEvolve systems"""
        
        if not self.db_pool:
            raise RuntimeError("Database pool not initialized")
        
        # Merge metrics
        combined_metrics = {
            "graph_sitter": graph_sitter_metrics,
            "openevolve": openevolve_metrics,
            "sync_timestamp": time.time(),
            "correlation_analysis": self._analyze_metric_correlation(
                graph_sitter_metrics, 
                openevolve_metrics
            )
        }
        
        # Store synchronized metrics
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO task_metrics (
                    task_id,
                    period_start,
                    period_end,
                    detailed_metrics
                ) VALUES ($1, $2, $3, $4)
                ON CONFLICT (task_id, period_start, period_end)
                DO UPDATE SET detailed_metrics = $4
            """, 
            task_id,
            time.time(),
            time.time(),
            json.dumps(combined_metrics)
            )
    
    async def track_best_implementation(
        self,
        task_id: str,
        implementation: str,
        metrics: Dict[str, float]
    ) -> None:
        """Track the best implementation across evolution steps"""
        
        if not self.db_pool:
            raise RuntimeError("Database pool not initialized")
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(metrics)
        
        async with self.db_pool.acquire() as conn:
            # Check if this is better than current best
            current_best = await conn.fetchrow("""
                SELECT fitness_score
                FROM program_evolution
                WHERE task_id = $1
                ORDER BY fitness_score DESC
                LIMIT 1
            """, task_id)
            
            if not current_best or overall_score > current_best['fitness_score']:
                # Store new best implementation
                program_id = str(uuid.uuid4())
                
                await conn.execute("""
                    INSERT INTO program_evolution (
                        task_id,
                        program_id,
                        code,
                        metrics,
                        fitness_score,
                        metadata
                    ) VALUES ($1, $2, $3, $4, $5, $6)
                """,
                task_id,
                program_id,
                implementation,
                json.dumps(metrics),
                overall_score,
                json.dumps({"is_best": True, "tracked_at": time.time()})
                )
                
                logger.info(f"New best implementation tracked for task {task_id}: score {overall_score}")
    
    # Private helper methods
    
    async def _store_program_evolution(self, task_id: str, program: Program) -> None:
        """Store program evolution data in database"""
        
        if not self.db_pool:
            return
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO program_evolution (
                    task_id,
                    program_id,
                    code,
                    language,
                    parent_id,
                    generation,
                    timestamp,
                    iteration_found,
                    metrics,
                    complexity,
                    diversity,
                    fitness_score,
                    metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (task_id, program_id) DO UPDATE SET
                    code = $3,
                    metrics = $9,
                    complexity = $10,
                    diversity = $11,
                    fitness_score = $12,
                    metadata = $13
            """,
            task_id,
            program.id,
            program.code,
            program.language,
            program.parent_id,
            program.generation,
            program.timestamp,
            program.iteration_found,
            json.dumps(program.metrics),
            program.complexity,
            program.diversity,
            program.fitness_score,
            json.dumps(program.metadata)
            )
    
    async def _store_evaluation_result(self, result: EvaluationResult) -> None:
        """Store evaluation result in database"""
        
        if not self.db_pool:
            return
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO openevolve_evaluations (
                    task_id,
                    program_id,
                    evaluation_type,
                    scores,
                    metrics,
                    recommendations,
                    generation,
                    parent_program_id,
                    iteration_found,
                    evaluation_duration_ms,
                    complexity_score,
                    diversity_score,
                    quality_score,
                    status,
                    completed_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            """,
            result.task_id,
            result.program_id,
            "implementation",
            json.dumps(result.scores),
            json.dumps(result.metrics),
            json.dumps(result.recommendations),
            result.generation,
            result.parent_program_id,
            result.iteration_found,
            result.evaluation_duration_ms,
            result.complexity_score,
            result.diversity_score,
            result.quality_score,
            result.status,
            time.time()
            )
    
    async def _store_evolution_results(self, task_id: str, evolution_result: Dict[str, Any]) -> None:
        """Store evolution results in database"""
        
        if not self.db_pool:
            return
        
        # Store each generation's programs
        history = evolution_result.get("history", [])
        
        async with self.db_pool.acquire() as conn:
            for generation_data in history:
                for program_data in generation_data.get("programs", []):
                    program = Program(
                        id=program_data["id"],
                        code=program_data["code"],
                        generation=generation_data["generation"],
                        metrics=program_data.get("metrics", {}),
                        fitness_score=program_data.get("fitness_score", 0.0)
                    )
                    
                    await self._store_program_evolution(task_id, program)
    
    def _analyze_metric_correlation(
        self, 
        gs_metrics: Dict[str, Any], 
        oe_metrics: Dict[str, Any]
    ) -> Dict[str, float]:
        """Analyze correlation between Graph-Sitter and OpenEvolve metrics"""
        
        correlations = {}
        
        # Simple correlation analysis (in real implementation, use statistical methods)
        for gs_key, gs_value in gs_metrics.items():
            if isinstance(gs_value, (int, float)):
                for oe_key, oe_value in oe_metrics.items():
                    if isinstance(oe_value, (int, float)):
                        # Simplified correlation calculation
                        correlation_key = f"{gs_key}_vs_{oe_key}"
                        correlations[correlation_key] = abs(gs_value - oe_value) / max(abs(gs_value), abs(oe_value), 1)
        
        return correlations
    
    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall score from metrics"""
        
        if not metrics:
            return 0.0
        
        # Weighted average of metrics
        weights = {
            "quality": 0.4,
            "performance": 0.3,
            "maintainability": 0.2,
            "complexity": -0.1  # Lower complexity is better
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for metric, value in metrics.items():
            weight = weights.get(metric, 0.1)  # Default weight
            total_score += value * weight
            total_weight += abs(weight)
        
        return total_score / total_weight if total_weight > 0 else 0.0


# Factory function for creating adapter instances
async def create_openevolve_adapter(
    config: BaseConfig,
    database_url: str,
    openevolve_base_url: Optional[str] = None
) -> OpenEvolveAdapter:
    """Create and initialize an OpenEvolve adapter instance"""
    
    adapter = OpenEvolveAdapter(config, database_url, openevolve_base_url)
    await adapter.initialize()
    return adapter


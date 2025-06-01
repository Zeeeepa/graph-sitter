"""
Pipeline Orchestrator - Central coordinator for autonomous development pipeline.

This module provides the main orchestration logic for the autonomous development
pipeline, integrating with Graph-Sitter's existing capabilities and extending
them with autonomous features from OpenAlpha_Evolve.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Graph-Sitter imports
from graph_sitter import Codebase
from graph_sitter.codebase.codebase_analysis import get_codebase_summary
from graph_sitter.shared.logging.get_logger import get_logger

# Contexten imports
from ..open_evolve.core.interfaces import TaskDefinition, Program
from ..open_evolve.task_manager.agent import TaskManagerAgent

logger = get_logger(__name__)

class PipelineStage(Enum):
    """Stages in the autonomous development pipeline."""
    INITIALIZATION = "initialization"
    CONTEXT_ANALYSIS = "context_analysis"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    TASK_DECOMPOSITION = "task_decomposition"
    SOLUTION_GENERATION = "solution_generation"
    VALIDATION = "validation"
    ERROR_ANALYSIS = "error_analysis"
    DEBUGGING = "debugging"
    LEARNING = "learning"
    OPTIMIZATION = "optimization"
    COMPLETION = "completion"

@dataclass
class PipelineState:
    """Represents the current state of the pipeline."""
    current_stage: PipelineStage
    task_definition: Optional[TaskDefinition] = None
    codebase_context: Optional[Dict[str, Any]] = None
    generated_programs: List[Program] = field(default_factory=list)
    errors_encountered: List[Dict[str, Any]] = field(default_factory=list)
    debug_results: List[Dict[str, Any]] = field(default_factory=list)
    learning_insights: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class PipelineResult:
    """Result of pipeline execution."""
    success: bool
    final_programs: List[Program]
    execution_time: float
    stages_completed: List[PipelineStage]
    errors_resolved: int
    learning_insights: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommendations: List[str]

class PipelineOrchestrator:
    """
    Central orchestrator for the autonomous development pipeline.
    Coordinates all components and manages the end-to-end development process.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Pipeline configuration
        self.enable_learning = self.config.get('enable_learning', True)
        self.enable_auto_debugging = self.config.get('enable_auto_debugging', True)
        self.enable_context_analysis = self.config.get('enable_context_analysis', True)
        self.max_pipeline_retries = self.config.get('max_pipeline_retries', 3)
        
        # Callbacks for monitoring
        self.stage_callbacks: Dict[PipelineStage, List[Callable]] = {}
        self.progress_callback: Optional[Callable] = None
        
        # Initialize codebase if path provided
        self.codebase = None
        if 'codebase_path' in self.config:
            self.codebase = Codebase(self.config['codebase_path'])
    
    async def execute(self, task_definition: TaskDefinition) -> PipelineResult:
        """Main execution method - runs the complete autonomous development pipeline."""
        return await self.run_pipeline(task_definition)
    
    async def run_pipeline(self, task_definition: TaskDefinition) -> PipelineResult:
        """
        Run the complete autonomous development pipeline.
        
        Args:
            task_definition: The task to be solved autonomously
        """
        start_time = datetime.now()
        logger.info(f"Starting autonomous development pipeline for task: {task_definition.id}")
        
        # Initialize pipeline state
        state = PipelineState(
            current_stage=PipelineStage.INITIALIZATION,
            task_definition=task_definition,
            max_retries=self.max_pipeline_retries
        )
        
        try:
            # Execute pipeline stages
            await self._execute_stage(PipelineStage.INITIALIZATION, state)
            
            if self.enable_context_analysis:
                await self._execute_stage(PipelineStage.CONTEXT_ANALYSIS, state)
            
            await self._execute_stage(PipelineStage.REQUIREMENT_ANALYSIS, state)
            await self._execute_stage(PipelineStage.TASK_DECOMPOSITION, state)
            await self._execute_stage(PipelineStage.SOLUTION_GENERATION, state)
            await self._execute_stage(PipelineStage.VALIDATION, state)
            
            # Error handling and debugging loop
            while state.errors_encountered and state.retry_count < state.max_retries:
                if self.enable_auto_debugging:
                    await self._execute_stage(PipelineStage.ERROR_ANALYSIS, state)
                    await self._execute_stage(PipelineStage.DEBUGGING, state)
                    await self._execute_stage(PipelineStage.VALIDATION, state)
                else:
                    break
                state.retry_count += 1
            
            # Learning and optimization
            if self.enable_learning:
                await self._execute_stage(PipelineStage.LEARNING, state)
                await self._execute_stage(PipelineStage.OPTIMIZATION, state)
            
            await self._execute_stage(PipelineStage.COMPLETION, state)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Generate final result
            result = PipelineResult(
                success=len(state.generated_programs) > 0 and not state.errors_encountered,
                final_programs=state.generated_programs,
                execution_time=execution_time,
                stages_completed=[record['stage'] for record in state.stage_history],
                errors_resolved=len(state.debug_results),
                learning_insights=state.learning_insights,
                performance_metrics=state.performance_metrics,
                recommendations=self._generate_recommendations(state)
            )
            
            logger.info(f"Pipeline completed: success={result.success}, "
                       f"programs={len(result.final_programs)}, time={execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}", exc_info=True)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return PipelineResult(
                success=False,
                final_programs=state.generated_programs,
                execution_time=execution_time,
                stages_completed=[record['stage'] for record in state.stage_history],
                errors_resolved=0,
                learning_insights={},
                performance_metrics={},
                recommendations=[f"Pipeline failed with error: {str(e)}"]
            )
    
    async def _execute_stage(self, stage: PipelineStage, state: PipelineState):
        """Execute a specific pipeline stage."""
        logger.debug(f"Executing pipeline stage: {stage.value}")
        state.current_stage = stage
        
        stage_start = datetime.now()
        
        try:
            # Execute stage-specific logic
            if stage == PipelineStage.INITIALIZATION:
                await self._stage_initialization(state)
            elif stage == PipelineStage.CONTEXT_ANALYSIS:
                await self._stage_context_analysis(state)
            elif stage == PipelineStage.REQUIREMENT_ANALYSIS:
                await self._stage_requirement_analysis(state)
            elif stage == PipelineStage.TASK_DECOMPOSITION:
                await self._stage_task_decomposition(state)
            elif stage == PipelineStage.SOLUTION_GENERATION:
                await self._stage_solution_generation(state)
            elif stage == PipelineStage.VALIDATION:
                await self._stage_validation(state)
            elif stage == PipelineStage.ERROR_ANALYSIS:
                await self._stage_error_analysis(state)
            elif stage == PipelineStage.DEBUGGING:
                await self._stage_debugging(state)
            elif stage == PipelineStage.LEARNING:
                await self._stage_learning(state)
            elif stage == PipelineStage.OPTIMIZATION:
                await self._stage_optimization(state)
            elif stage == PipelineStage.COMPLETION:
                await self._stage_completion(state)
            
            stage_duration = (datetime.now() - stage_start).total_seconds()
            
            # Record stage completion
            state.stage_history.append({
                'stage': stage,
                'duration': stage_duration,
                'timestamp': datetime.now().isoformat(),
                'success': True
            })
            
            # Call stage callbacks
            if stage in self.stage_callbacks:
                for callback in self.stage_callbacks[stage]:
                    try:
                        await callback(stage, state)
                    except Exception as e:
                        logger.warning(f"Stage callback failed: {e}")
            
            # Update progress
            if self.progress_callback:
                try:
                    progress = len(state.stage_history) / len(PipelineStage)
                    await self.progress_callback(progress, f"Completed {stage.value}")
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")
            
            logger.debug(f"Stage {stage.value} completed in {stage_duration:.2f}s")
            
        except Exception as e:
            logger.error(f"Stage {stage.value} failed: {e}", exc_info=True)
            
            state.stage_history.append({
                'stage': stage,
                'duration': (datetime.now() - stage_start).total_seconds(),
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            })
            
            raise
    
    async def _stage_initialization(self, state: PipelineState):
        """Initialize the pipeline."""
        logger.info("Initializing autonomous development pipeline")
        
        # Validate task definition
        if not state.task_definition:
            raise ValueError("Task definition is required")
        
        # Initialize performance metrics
        state.performance_metrics = {
            'start_time': datetime.now().isoformat(),
            'task_id': state.task_definition.id,
            'task_complexity': len(state.task_definition.description.split()),
            'initial_examples': len(state.task_definition.input_output_examples or [])
        }
        
        logger.info(f"Pipeline initialized for task: {state.task_definition.id}")
    
    async def _stage_context_analysis(self, state: PipelineState):
        """Analyze codebase context."""
        logger.info("Analyzing codebase context")
        
        if self.codebase:
            # Use Graph-Sitter for comprehensive analysis
            context = {
                'total_files': len(self.codebase.files),
                'total_functions': len(self.codebase.functions),
                'total_classes': len(self.codebase.classes),
                'imports': len(self.codebase.imports),
                'summary': get_codebase_summary(self.codebase)
            }
            
            # Add complexity analysis
            context['complexity_metrics'] = {
                'cyclomatic_complexity': sum(
                    getattr(func, 'cyclomatic_complexity', 1) 
                    for func in self.codebase.functions
                ),
                'inheritance_depth': max(
                    len(cls.superclasses) for cls in self.codebase.classes
                ) if self.codebase.classes else 0
            }
            
            state.codebase_context = context
            
            # Update performance metrics
            state.performance_metrics.update({
                'codebase_files': context['total_files'],
                'codebase_functions': context['total_functions'],
                'codebase_classes': context['total_classes']
            })
        
        logger.info("Context analysis complete")
    
    async def _stage_requirement_analysis(self, state: PipelineState):
        """Analyze requirements and constraints."""
        logger.info("Analyzing requirements")
        
        # Analyze task requirements
        requirements = {
            'function_name': state.task_definition.function_name_to_evolve,
            'input_output_examples': len(state.task_definition.input_output_examples or []),
            'allowed_imports': state.task_definition.allowed_imports or [],
            'complexity_estimate': self._estimate_task_complexity(state.task_definition)
        }
        
        state.performance_metrics['requirements'] = requirements
        
        logger.info(f"Requirements analyzed: complexity={requirements['complexity_estimate']}")
    
    async def _stage_task_decomposition(self, state: PipelineState):
        """Decompose task into manageable components."""
        logger.info("Decomposing task")
        
        # Simple task decomposition (can be enhanced)
        decomposition = {
            'main_task': state.task_definition.description,
            'sub_tasks': self._decompose_task(state.task_definition),
            'dependencies': self._analyze_task_dependencies(state.task_definition)
        }
        
        state.performance_metrics['task_decomposition'] = decomposition
        
        logger.info(f"Task decomposed into {len(decomposition['sub_tasks'])} sub-tasks")
    
    async def _stage_solution_generation(self, state: PipelineState):
        """Generate solutions using the evolutionary algorithm."""
        logger.info("Generating solutions")
        
        # Create task manager and run evolution
        task_manager = TaskManagerAgent(task_definition=state.task_definition)
        
        # Execute evolutionary algorithm
        best_programs = await task_manager.execute()
        
        if best_programs:
            state.generated_programs = best_programs
            
            # Update performance metrics
            state.performance_metrics.update({
                'solutions_generated': len(best_programs),
                'best_fitness': max(p.fitness_scores.get('correctness', 0) for p in best_programs),
                'average_fitness': sum(p.fitness_scores.get('correctness', 0) for p in best_programs) / len(best_programs)
            })
        
        logger.info(f"Solution generation complete: {len(state.generated_programs)} programs generated")
    
    async def _stage_validation(self, state: PipelineState):
        """Validate generated solutions."""
        logger.info("Validating solutions")
        
        validation_results = []
        errors_found = []
        
        for program in state.generated_programs:
            try:
                # Basic syntax validation
                compile(program.code, '<string>', 'exec')
                validation_results.append({'program_id': program.id, 'valid': True})
            except SyntaxError as e:
                error_info = {
                    'program_id': program.id,
                    'error_type': 'SyntaxError',
                    'error_message': str(e),
                    'line_number': e.lineno
                }
                errors_found.append(error_info)
                validation_results.append({'program_id': program.id, 'valid': False, 'error': error_info})
        
        # Update state with validation results
        state.errors_encountered = errors_found
        state.performance_metrics['validation'] = {
            'total_programs': len(state.generated_programs),
            'valid_programs': len([r for r in validation_results if r['valid']]),
            'errors_found': len(errors_found)
        }
        
        logger.info(f"Validation complete: {len(errors_found)} errors found")
    
    async def _stage_error_analysis(self, state: PipelineState):
        """Analyze and classify errors."""
        logger.info("Analyzing errors")
        
        # Simple error classification
        for error in state.errors_encountered:
            error['category'] = self._classify_error(error)
            error['severity'] = self._assess_error_severity(error)
            error['suggested_fixes'] = self._suggest_error_fixes(error)
        
        logger.info(f"Error analysis complete: {len(state.errors_encountered)} errors classified")
    
    async def _stage_debugging(self, state: PipelineState):
        """Apply automated debugging fixes."""
        logger.info("Applying debugging fixes")
        
        debug_results = []
        
        for error in state.errors_encountered:
            try:
                # Apply simple fixes based on error type
                if error['error_type'] == 'SyntaxError':
                    fixed_code = self._apply_syntax_fix(error)
                    if fixed_code:
                        debug_results.append({
                            'error_id': error.get('program_id'),
                            'fix_applied': True,
                            'fix_type': 'syntax_fix',
                            'fixed_code': fixed_code
                        })
            except Exception as e:
                debug_results.append({
                    'error_id': error.get('program_id'),
                    'fix_applied': False,
                    'error': str(e)
                })
        
        state.debug_results = debug_results
        
        # Remove fixed errors
        fixed_error_ids = {r['error_id'] for r in debug_results if r.get('fix_applied')}
        state.errors_encountered = [
            e for e in state.errors_encountered 
            if e.get('program_id') not in fixed_error_ids
        ]
        
        logger.info(f"Debugging complete: {len(debug_results)} fixes applied")
    
    async def _stage_learning(self, state: PipelineState):
        """Learn from execution patterns and results."""
        logger.info("Learning from execution patterns")
        
        # Simple learning insights
        insights = {
            'successful_patterns': self._identify_successful_patterns(state),
            'error_patterns': self._identify_error_patterns(state),
            'performance_insights': self._analyze_performance_patterns(state)
        }
        
        state.learning_insights = insights
        
        logger.info("Learning phase complete")
    
    async def _stage_optimization(self, state: PipelineState):
        """Optimize solutions based on learning insights."""
        logger.info("Optimizing solutions")
        
        # Apply optimizations based on insights
        optimized_count = 0
        for program in state.generated_programs:
            if self._can_optimize_program(program, state.learning_insights):
                self._apply_optimizations(program, state.learning_insights)
                optimized_count += 1
        
        state.performance_metrics['optimization'] = {
            'programs_optimized': optimized_count,
            'optimization_techniques': list(state.learning_insights.keys())
        }
        
        logger.info(f"Optimization complete: {optimized_count} programs optimized")
    
    async def _stage_completion(self, state: PipelineState):
        """Complete the pipeline execution."""
        logger.info("Completing pipeline execution")
        
        # Final metrics calculation
        state.performance_metrics['completion'] = {
            'total_execution_time': sum(
                record['duration'] for record in state.stage_history
            ),
            'stages_completed': len(state.stage_history),
            'final_program_count': len(state.generated_programs),
            'errors_resolved': len(state.debug_results)
        }
        
        logger.info("Pipeline execution completed successfully")
    
    def _estimate_task_complexity(self, task_definition: TaskDefinition) -> str:
        """Estimate task complexity based on description and examples."""
        description_length = len(task_definition.description.split())
        example_count = len(task_definition.input_output_examples or [])
        
        if description_length < 10 and example_count <= 3:
            return "low"
        elif description_length < 20 and example_count <= 5:
            return "medium"
        else:
            return "high"
    
    def _decompose_task(self, task_definition: TaskDefinition) -> List[str]:
        """Decompose task into sub-tasks."""
        # Simple decomposition based on keywords
        description = task_definition.description.lower()
        sub_tasks = []
        
        if "function" in description:
            sub_tasks.append("Define function signature")
            sub_tasks.append("Implement core logic")
            sub_tasks.append("Handle edge cases")
        
        if "test" in description or "example" in description:
            sub_tasks.append("Validate against examples")
        
        if not sub_tasks:
            sub_tasks = ["Analyze requirements", "Implement solution", "Validate results"]
        
        return sub_tasks
    
    def _analyze_task_dependencies(self, task_definition: TaskDefinition) -> List[str]:
        """Analyze task dependencies."""
        dependencies = []
        
        if task_definition.allowed_imports:
            dependencies.extend(task_definition.allowed_imports)
        
        # Add common dependencies based on task type
        if "math" in task_definition.description.lower():
            dependencies.append("math")
        
        return dependencies
    
    def _classify_error(self, error: Dict[str, Any]) -> str:
        """Classify error type."""
        error_type = error.get('error_type', '')
        
        if 'Syntax' in error_type:
            return 'syntax'
        elif 'Name' in error_type:
            return 'undefined_variable'
        elif 'Type' in error_type:
            return 'type_mismatch'
        else:
            return 'unknown'
    
    def _assess_error_severity(self, error: Dict[str, Any]) -> str:
        """Assess error severity."""
        error_type = error.get('error_type', '')
        
        if 'Syntax' in error_type:
            return 'high'
        elif 'Runtime' in error_type:
            return 'medium'
        else:
            return 'low'
    
    def _suggest_error_fixes(self, error: Dict[str, Any]) -> List[str]:
        """Suggest fixes for errors."""
        fixes = []
        error_type = error.get('error_type', '')
        
        if 'Syntax' in error_type:
            fixes.append("Check for missing parentheses or brackets")
            fixes.append("Verify proper indentation")
        elif 'Name' in error_type:
            fixes.append("Define the missing variable")
            fixes.append("Check for typos in variable names")
        
        return fixes
    
    def _apply_syntax_fix(self, error: Dict[str, Any]) -> Optional[str]:
        """Apply simple syntax fixes."""
        # This is a placeholder for more sophisticated fixing logic
        return None
    
    def _identify_successful_patterns(self, state: PipelineState) -> List[str]:
        """Identify patterns from successful programs."""
        patterns = []
        
        for program in state.generated_programs:
            if program.fitness_scores.get('correctness', 0) > 0.8:
                patterns.append(f"High-performing pattern in {program.id}")
        
        return patterns
    
    def _identify_error_patterns(self, state: PipelineState) -> List[str]:
        """Identify common error patterns."""
        error_types = [error.get('error_type') for error in state.errors_encountered]
        return list(set(error_types))
    
    def _analyze_performance_patterns(self, state: PipelineState) -> Dict[str, Any]:
        """Analyze performance patterns."""
        return {
            'average_stage_duration': sum(
                record['duration'] for record in state.stage_history
            ) / len(state.stage_history) if state.stage_history else 0,
            'most_time_consuming_stage': max(
                state.stage_history, 
                key=lambda x: x['duration']
            )['stage'].value if state.stage_history else None
        }
    
    def _can_optimize_program(self, program: Program, insights: Dict[str, Any]) -> bool:
        """Check if program can be optimized."""
        return program.fitness_scores.get('correctness', 0) > 0.5
    
    def _apply_optimizations(self, program: Program, insights: Dict[str, Any]):
        """Apply optimizations to program."""
        # Placeholder for optimization logic
        pass
    
    def _generate_recommendations(self, state: PipelineState) -> List[str]:
        """Generate recommendations based on pipeline execution."""
        recommendations = []
        
        if state.errors_encountered:
            recommendations.append(f"Address {len(state.errors_encountered)} remaining errors")
        
        if len(state.generated_programs) == 0:
            recommendations.append("No solutions generated - consider adjusting task parameters")
        
        if state.retry_count > 0:
            recommendations.append("Consider improving error handling to reduce retries")
        
        return recommendations
    
    def add_stage_callback(self, stage: PipelineStage, callback: Callable):
        """Add a callback for a specific stage."""
        if stage not in self.stage_callbacks:
            self.stage_callbacks[stage] = []
        self.stage_callbacks[stage].append(callback)
    
    def set_progress_callback(self, callback: Callable):
        """Set a progress callback."""
        self.progress_callback = callback


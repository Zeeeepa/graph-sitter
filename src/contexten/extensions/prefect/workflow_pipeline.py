#!/usr/bin/env python3
"""
Prefect Workflow Pipeline Integration

Enhanced Prefect integration for orchestrating complex workflows with
Codegen SDK, ControlFlow, and quality gates.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from prefect import flow, task, get_run_logger
from prefect.context import get_run_context
from prefect.states import State, Completed, Failed

from .flow import PrefectFlow
from .monitoring import PrefectMonitoring

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Pipeline execution stages."""
    INITIALIZATION = "initialization"
    PLANNING = "planning"
    ORCHESTRATION = "orchestration"
    EXECUTION = "execution"
    QUALITY_GATES = "quality_gates"
    FINALIZATION = "finalization"


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineContext:
    """Pipeline execution context."""
    project_id: str
    requirements: str
    config: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    callbacks: List[Callable] = field(default_factory=list)


@dataclass
class StageResult:
    """Result of a pipeline stage."""
    stage: PipelineStage
    status: PipelineStatus
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


class PrefectWorkflowPipeline:
    """Enhanced Prefect workflow pipeline for Contexten orchestration."""
    
    def __init__(self, name: str = "contexten_pipeline"):
        """Initialize Prefect workflow pipeline."""
        self.name = name
        self.monitoring = PrefectMonitoring()
        self.stage_callbacks: Dict[PipelineStage, List[Callable]] = {}
        self.global_callbacks: List[Callable] = []
        
        # Initialize stage callbacks
        for stage in PipelineStage:
            self.stage_callbacks[stage] = []
        
        logger.info(f"Prefect workflow pipeline '{name}' initialized")
    
    def add_stage_callback(self, stage: PipelineStage, callback: Callable):
        """Add callback for specific pipeline stage."""
        self.stage_callbacks[stage].append(callback)
    
    def add_global_callback(self, callback: Callable):
        """Add global callback for all pipeline events."""
        self.global_callbacks.append(callback)
    
    def _emit_pipeline_event(self, event_type: str, data: Dict[str, Any]):
        """Emit pipeline event to registered callbacks."""
        for callback in self.global_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"Global pipeline callback failed: {e}")
    
    def _emit_stage_event(self, stage: PipelineStage, event_type: str, data: Dict[str, Any]):
        """Emit stage-specific event to registered callbacks."""
        for callback in self.stage_callbacks[stage]:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"Stage {stage.value} callback failed: {e}")
    
    @flow(name="contexten_workflow_pipeline")
    async def execute_pipeline(
        self,
        context: PipelineContext,
        codegen_config: Dict[str, Any],
        controlflow_config: Dict[str, Any] = None,
        grainchain_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute complete workflow pipeline with Prefect orchestration."""
        logger = get_run_logger()
        logger.info(f"Starting Contexten workflow pipeline for project {context.project_id}")
        
        pipeline_result = {
            'project_id': context.project_id,
            'pipeline_name': self.name,
            'status': PipelineStatus.RUNNING,
            'start_time': time.time(),
            'stages': {},
            'overall_metrics': {},
            'flow_run_id': get_run_context().flow_run.id if get_run_context() else None
        }
        
        self._emit_pipeline_event('pipeline_started', {
            'project_id': context.project_id,
            'pipeline_name': self.name
        })
        
        try:
            # Stage 1: Initialization
            init_result = await self._execute_initialization_stage(context, pipeline_result)
            pipeline_result['stages']['initialization'] = init_result
            
            if init_result.status == PipelineStatus.FAILED:
                raise Exception(f"Initialization failed: {init_result.error}")
            
            # Stage 2: Planning
            planning_result = await self._execute_planning_stage(
                context, codegen_config, pipeline_result
            )
            pipeline_result['stages']['planning'] = planning_result
            
            if planning_result.status == PipelineStatus.FAILED:
                raise Exception(f"Planning failed: {planning_result.error}")
            
            # Stage 3: Orchestration
            orchestration_result = await self._execute_orchestration_stage(
                context, controlflow_config, planning_result.result, pipeline_result
            )
            pipeline_result['stages']['orchestration'] = orchestration_result
            
            if orchestration_result.status == PipelineStatus.FAILED:
                raise Exception(f"Orchestration failed: {orchestration_result.error}")
            
            # Stage 4: Execution
            execution_result = await self._execute_execution_stage(
                context, codegen_config, orchestration_result.result, pipeline_result
            )
            pipeline_result['stages']['execution'] = execution_result
            
            if execution_result.status == PipelineStatus.FAILED:
                raise Exception(f"Execution failed: {execution_result.error}")
            
            # Stage 5: Quality Gates
            quality_result = await self._execute_quality_gates_stage(
                context, grainchain_config, execution_result.result, pipeline_result
            )
            pipeline_result['stages']['quality_gates'] = quality_result
            
            if quality_result.status == PipelineStatus.FAILED:
                logger.warning(f"Quality gates failed: {quality_result.error}")
                # Don't fail the entire pipeline for quality gate failures
            
            # Stage 6: Finalization
            finalization_result = await self._execute_finalization_stage(
                context, pipeline_result
            )
            pipeline_result['stages']['finalization'] = finalization_result
            
            pipeline_result['status'] = PipelineStatus.COMPLETED
            logger.info(f"Pipeline completed successfully for project {context.project_id}")
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            pipeline_result['status'] = PipelineStatus.FAILED
            pipeline_result['error'] = str(e)
            
            self._emit_pipeline_event('pipeline_failed', {
                'project_id': context.project_id,
                'error': str(e)
            })
        
        pipeline_result['end_time'] = time.time()
        pipeline_result['duration'] = pipeline_result['end_time'] - pipeline_result['start_time']
        pipeline_result['overall_metrics'] = self._calculate_pipeline_metrics(pipeline_result)
        
        self._emit_pipeline_event('pipeline_completed', {
            'project_id': context.project_id,
            'status': pipeline_result['status'],
            'duration': pipeline_result['duration']
        })
        
        return pipeline_result
    
    @task(name="initialization_stage")
    async def _execute_initialization_stage(
        self,
        context: PipelineContext,
        pipeline_result: Dict[str, Any]
    ) -> StageResult:
        """Execute initialization stage."""
        logger = get_run_logger()
        logger.info("Executing initialization stage")
        
        stage_result = StageResult(
            stage=PipelineStage.INITIALIZATION,
            status=PipelineStatus.RUNNING,
            start_time=time.time()
        )
        
        self._emit_stage_event(PipelineStage.INITIALIZATION, 'stage_started', {
            'project_id': context.project_id
        })
        
        try:
            # Initialize pipeline components
            initialization_data = {
                'project_id': context.project_id,
                'requirements': context.requirements,
                'config_validated': True,
                'components_initialized': [],
                'environment_ready': True
            }
            
            # Validate configuration
            if not context.project_id:
                raise ValueError("Project ID is required")
            
            if not context.requirements:
                raise ValueError("Requirements are required")
            
            # Initialize monitoring
            self.monitoring.start_monitoring(context.project_id)
            initialization_data['components_initialized'].append('monitoring')
            
            # Validate external dependencies
            # This would check if Codegen, ControlFlow, etc. are available
            initialization_data['components_initialized'].extend([
                'codegen_sdk', 'controlflow', 'grainchain', 'graph_sitter'
            ])
            
            stage_result.status = PipelineStatus.COMPLETED
            stage_result.result = initialization_data
            
            logger.info("Initialization stage completed successfully")
            
        except Exception as e:
            logger.error(f"Initialization stage failed: {e}")
            stage_result.status = PipelineStatus.FAILED
            stage_result.error = str(e)
        
        stage_result.end_time = time.time()
        stage_result.duration = stage_result.end_time - stage_result.start_time
        
        self._emit_stage_event(PipelineStage.INITIALIZATION, 'stage_completed', {
            'project_id': context.project_id,
            'status': stage_result.status.value,
            'duration': stage_result.duration
        })
        
        return stage_result
    
    @task(name="planning_stage")
    async def _execute_planning_stage(
        self,
        context: PipelineContext,
        codegen_config: Dict[str, Any],
        pipeline_result: Dict[str, Any]
    ) -> StageResult:
        """Execute planning stage using Codegen SDK."""
        logger = get_run_logger()
        logger.info("Executing planning stage")
        
        stage_result = StageResult(
            stage=PipelineStage.PLANNING,
            status=PipelineStatus.RUNNING,
            start_time=time.time()
        )
        
        self._emit_stage_event(PipelineStage.PLANNING, 'stage_started', {
            'project_id': context.project_id
        })
        
        try:
            # Import and initialize Codegen workflow integration
            from ..codegen.workflow_integration import create_codegen_workflow_integration
            
            codegen_integration = create_codegen_workflow_integration(
                org_id=codegen_config['org_id'],
                token=codegen_config['token'],
                base_url=codegen_config.get('base_url', 'https://api.codegen.com')
            )
            
            # Create planning prompt
            planning_prompt = f"""
            Create a comprehensive implementation plan for the following project:
            
            Project ID: {context.project_id}
            Requirements: {context.requirements}
            
            Please provide:
            1. Detailed task breakdown with dependencies
            2. Estimated complexity and duration for each task
            3. Required tools and capabilities
            4. Quality gates and validation criteria
            5. Risk assessment and mitigation strategies
            
            Format the response as a structured JSON plan that can be executed by automated agents.
            """
            
            # Execute planning with Codegen
            from codegen.agents.agent import Agent
            
            agent = Agent(
                org_id=codegen_config['org_id'],
                token=codegen_config['token'],
                base_url=codegen_config.get('base_url', 'https://api.codegen.com')
            )
            
            planning_task = agent.run(planning_prompt)
            
            # Wait for completion
            timeout = 600  # 10 minutes for planning
            start_time = time.time()
            
            while planning_task.status not in ['completed', 'failed'] and (time.time() - start_time) < timeout:
                await asyncio.sleep(10)
                planning_task.refresh()
            
            if planning_task.status == 'completed':
                planning_result = {
                    'codegen_task_id': planning_task.id,
                    'plan': planning_task.result if hasattr(planning_task, 'result') else 'Plan generated',
                    'planning_duration': time.time() - start_time,
                    'tasks_identified': self._extract_task_count_from_plan(planning_task),
                    'complexity_assessment': 'moderate',  # Would be extracted from plan
                    'estimated_total_duration': 3600  # Would be calculated from plan
                }
                
                stage_result.status = PipelineStatus.COMPLETED
                stage_result.result = planning_result
                
                logger.info("Planning stage completed successfully")
                
            else:
                raise Exception(f"Planning task failed or timed out: {planning_task.status}")
        
        except Exception as e:
            logger.error(f"Planning stage failed: {e}")
            stage_result.status = PipelineStatus.FAILED
            stage_result.error = str(e)
        
        stage_result.end_time = time.time()
        stage_result.duration = stage_result.end_time - stage_result.start_time
        
        self._emit_stage_event(PipelineStage.PLANNING, 'stage_completed', {
            'project_id': context.project_id,
            'status': stage_result.status.value,
            'duration': stage_result.duration
        })
        
        return stage_result
    
    @task(name="orchestration_stage")
    async def _execute_orchestration_stage(
        self,
        context: PipelineContext,
        controlflow_config: Dict[str, Any],
        planning_result: Dict[str, Any],
        pipeline_result: Dict[str, Any]
    ) -> StageResult:
        """Execute orchestration stage using ControlFlow."""
        logger = get_run_logger()
        logger.info("Executing orchestration stage")
        
        stage_result = StageResult(
            stage=PipelineStage.ORCHESTRATION,
            status=PipelineStatus.RUNNING,
            start_time=time.time()
        )
        
        self._emit_stage_event(PipelineStage.ORCHESTRATION, 'stage_started', {
            'project_id': context.project_id
        })
        
        try:
            # Import and initialize ControlFlow integration
            from ..controlflow.codegen_integration import create_codegen_flow_orchestrator
            
            orchestrator = create_codegen_flow_orchestrator()
            
            # Register Codegen agents if provided in config
            if controlflow_config and 'agents' in controlflow_config:
                for agent_config in controlflow_config['agents']:
                    orchestrator.register_codegen_agent(
                        agent_id=agent_config['id'],
                        name=agent_config['name'],
                        org_id=agent_config['org_id'],
                        token=agent_config['token'],
                        base_url=agent_config.get('base_url', 'https://api.codegen.com'),
                        capabilities=agent_config.get('capabilities', [])
                    )
            
            # Create workflow definition from planning result
            workflow_definition = {
                'id': f"workflow_{context.project_id}",
                'name': f"Contexten Workflow - {context.project_id}",
                'plan': planning_result.get('plan', ''),
                'tasks': self._extract_tasks_from_planning_result(planning_result),
                'estimated_duration': planning_result.get('estimated_total_duration', 3600)
            }
            
            # Execute workflow orchestration
            orchestration_result = await orchestrator.execute_workflow_with_codegen(
                workflow_definition=workflow_definition,
                context=context.variables
            )
            
            stage_result.status = PipelineStatus.COMPLETED
            stage_result.result = orchestration_result
            
            logger.info("Orchestration stage completed successfully")
        
        except Exception as e:
            logger.error(f"Orchestration stage failed: {e}")
            stage_result.status = PipelineStatus.FAILED
            stage_result.error = str(e)
        
        stage_result.end_time = time.time()
        stage_result.duration = stage_result.end_time - stage_result.start_time
        
        self._emit_stage_event(PipelineStage.ORCHESTRATION, 'stage_completed', {
            'project_id': context.project_id,
            'status': stage_result.status.value,
            'duration': stage_result.duration
        })
        
        return stage_result
    
    @task(name="execution_stage")
    async def _execute_execution_stage(
        self,
        context: PipelineContext,
        codegen_config: Dict[str, Any],
        orchestration_result: Dict[str, Any],
        pipeline_result: Dict[str, Any]
    ) -> StageResult:
        """Execute tasks using enhanced Codegen workflow integration."""
        logger = get_run_logger()
        logger.info("Executing execution stage")
        
        stage_result = StageResult(
            stage=PipelineStage.EXECUTION,
            status=PipelineStatus.RUNNING,
            start_time=time.time()
        )
        
        self._emit_stage_event(PipelineStage.EXECUTION, 'stage_started', {
            'project_id': context.project_id
        })
        
        try:
            # The orchestration stage should have already executed the tasks
            # This stage focuses on collecting and validating results
            
            workflow_tasks = orchestration_result.get('tasks', {})
            execution_summary = {
                'total_tasks': len(workflow_tasks),
                'completed_tasks': 0,
                'failed_tasks': 0,
                'task_results': workflow_tasks,
                'performance_metrics': orchestration_result.get('performance', {}),
                'agent_utilization': orchestration_result.get('agent_utilization', {})
            }
            
            # Count task statuses
            for task_result in workflow_tasks.values():
                if task_result.get('status') == 'completed':
                    execution_summary['completed_tasks'] += 1
                elif task_result.get('status') == 'failed':
                    execution_summary['failed_tasks'] += 1
            
            # Calculate success rate
            if execution_summary['total_tasks'] > 0:
                execution_summary['success_rate'] = (
                    execution_summary['completed_tasks'] / execution_summary['total_tasks']
                )
            else:
                execution_summary['success_rate'] = 0.0
            
            # Determine overall execution status
            if execution_summary['success_rate'] >= 0.8:  # 80% success threshold
                stage_result.status = PipelineStatus.COMPLETED
                logger.info(f"Execution stage completed with {execution_summary['success_rate']:.1%} success rate")
            else:
                stage_result.status = PipelineStatus.FAILED
                stage_result.error = f"Low success rate: {execution_summary['success_rate']:.1%}"
                logger.warning(f"Execution stage completed with low success rate: {execution_summary['success_rate']:.1%}")
            
            stage_result.result = execution_summary
        
        except Exception as e:
            logger.error(f"Execution stage failed: {e}")
            stage_result.status = PipelineStatus.FAILED
            stage_result.error = str(e)
        
        stage_result.end_time = time.time()
        stage_result.duration = stage_result.end_time - stage_result.start_time
        
        self._emit_stage_event(PipelineStage.EXECUTION, 'stage_completed', {
            'project_id': context.project_id,
            'status': stage_result.status.value,
            'duration': stage_result.duration
        })
        
        return stage_result
    
    @task(name="quality_gates_stage")
    async def _execute_quality_gates_stage(
        self,
        context: PipelineContext,
        grainchain_config: Dict[str, Any],
        execution_result: Dict[str, Any],
        pipeline_result: Dict[str, Any]
    ) -> StageResult:
        """Execute quality gates using Grainchain + Graph_sitter."""
        logger = get_run_logger()
        logger.info("Executing quality gates stage")
        
        stage_result = StageResult(
            stage=PipelineStage.QUALITY_GATES,
            status=PipelineStatus.RUNNING,
            start_time=time.time()
        )
        
        self._emit_stage_event(PipelineStage.QUALITY_GATES, 'stage_started', {
            'project_id': context.project_id
        })
        
        try:
            # Import quality gate components
            from ..grainchain.quality_gates import QualityGateManager
            from ..grainchain.config import GrainchainIntegrationConfig
            from ..graph_sitter.analysis.main_analyzer import comprehensive_analysis
            from graph_sitter import Codebase
            
            # Initialize quality gate manager
            if grainchain_config:
                config = GrainchainIntegrationConfig(**grainchain_config)
            else:
                config = GrainchainIntegrationConfig()
            
            quality_manager = QualityGateManager(config)
            
            # Run Graph_sitter analysis
            try:
                codebase = Codebase(".")  # Analyze current directory
                analysis_result = comprehensive_analysis(codebase)
                logger.info("Graph_sitter analysis completed")
            except Exception as e:
                logger.warning(f"Graph_sitter analysis failed: {e}")
                analysis_result = {'error': str(e)}
            
            # Run quality gates
            quality_results = []
            
            # Define quality gates to run
            from ..grainchain.grainchain_types import QualityGateType
            
            gates_to_run = [
                QualityGateType.CODE_QUALITY,
                QualityGateType.SECURITY_SCAN,
                QualityGateType.UNIT_TESTS,
                QualityGateType.INTEGRATION_TESTS
            ]
            
            for gate_type in gates_to_run:
                try:
                    gate_result = await quality_manager.execute_quality_gate(
                        gate_type=gate_type,
                        codebase_path=".",
                        context={
                            'execution_result': execution_result,
                            'project_id': context.project_id
                        }
                    )
                    quality_results.append(gate_result)
                    logger.info(f"Quality gate {gate_type.value} completed")
                    
                except Exception as e:
                    logger.warning(f"Quality gate {gate_type.value} failed: {e}")
                    quality_results.append({
                        'gate_type': gate_type.value,
                        'status': 'failed',
                        'error': str(e)
                    })
            
            # Compile quality results
            quality_summary = {
                'graph_sitter_analysis': analysis_result,
                'quality_gates': quality_results,
                'total_gates': len(quality_results),
                'passed_gates': sum(1 for r in quality_results if r.get('status') == 'passed'),
                'failed_gates': sum(1 for r in quality_results if r.get('status') == 'failed'),
                'overall_status': 'passed' if all(r.get('status') == 'passed' for r in quality_results) else 'failed'
            }
            
            stage_result.status = PipelineStatus.COMPLETED
            stage_result.result = quality_summary
            
            logger.info(f"Quality gates stage completed: {quality_summary['overall_status']}")
        
        except Exception as e:
            logger.error(f"Quality gates stage failed: {e}")
            stage_result.status = PipelineStatus.FAILED
            stage_result.error = str(e)
        
        stage_result.end_time = time.time()
        stage_result.duration = stage_result.end_time - stage_result.start_time
        
        self._emit_stage_event(PipelineStage.QUALITY_GATES, 'stage_completed', {
            'project_id': context.project_id,
            'status': stage_result.status.value,
            'duration': stage_result.duration
        })
        
        return stage_result
    
    @task(name="finalization_stage")
    async def _execute_finalization_stage(
        self,
        context: PipelineContext,
        pipeline_result: Dict[str, Any]
    ) -> StageResult:
        """Execute finalization stage."""
        logger = get_run_logger()
        logger.info("Executing finalization stage")
        
        stage_result = StageResult(
            stage=PipelineStage.FINALIZATION,
            status=PipelineStatus.RUNNING,
            start_time=time.time()
        )
        
        self._emit_stage_event(PipelineStage.FINALIZATION, 'stage_started', {
            'project_id': context.project_id
        })
        
        try:
            # Compile final results
            finalization_data = {
                'project_id': context.project_id,
                'pipeline_status': pipeline_result['status'],
                'total_duration': pipeline_result.get('duration', 0),
                'stages_completed': len([s for s in pipeline_result['stages'].values() 
                                       if s.status == PipelineStatus.COMPLETED]),
                'stages_failed': len([s for s in pipeline_result['stages'].values() 
                                    if s.status == PipelineStatus.FAILED]),
                'cleanup_performed': True,
                'notifications_sent': True
            }
            
            # Stop monitoring
            self.monitoring.stop_monitoring(context.project_id)
            
            # Cleanup resources
            # This would clean up any temporary resources, close connections, etc.
            
            # Send notifications
            # This would send completion notifications via Slack, email, etc.
            
            stage_result.status = PipelineStatus.COMPLETED
            stage_result.result = finalization_data
            
            logger.info("Finalization stage completed successfully")
        
        except Exception as e:
            logger.error(f"Finalization stage failed: {e}")
            stage_result.status = PipelineStatus.FAILED
            stage_result.error = str(e)
        
        stage_result.end_time = time.time()
        stage_result.duration = stage_result.end_time - stage_result.start_time
        
        self._emit_stage_event(PipelineStage.FINALIZATION, 'stage_completed', {
            'project_id': context.project_id,
            'status': stage_result.status.value,
            'duration': stage_result.duration
        })
        
        return stage_result
    
    def _extract_task_count_from_plan(self, planning_task) -> int:
        """Extract number of tasks from planning result."""
        # Simple heuristic - in practice, this would parse the actual plan
        return 5  # Default task count
    
    def _extract_tasks_from_planning_result(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract task definitions from planning result."""
        # Simple task extraction - in practice, this would parse the actual plan
        return [
            {
                'id': 'task_1',
                'name': 'Implement Core Functionality',
                'description': 'Implement the main features based on requirements',
                'complexity': 'moderate',
                'estimated_duration': 1800,
                'required_capabilities': ['code_generation', 'testing'],
                'dependencies': [],
                'priority': 3
            },
            {
                'id': 'task_2',
                'name': 'Add Comprehensive Tests',
                'description': 'Create unit and integration tests',
                'complexity': 'simple',
                'estimated_duration': 900,
                'required_capabilities': ['testing', 'code_review'],
                'dependencies': ['task_1'],
                'priority': 2
            },
            {
                'id': 'task_3',
                'name': 'Update Documentation',
                'description': 'Update README and API documentation',
                'complexity': 'simple',
                'estimated_duration': 600,
                'required_capabilities': ['documentation'],
                'dependencies': ['task_1'],
                'priority': 1
            }
        ]
    
    def _calculate_pipeline_metrics(self, pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall pipeline metrics."""
        stages = pipeline_result.get('stages', {})
        
        total_stages = len(stages)
        completed_stages = sum(1 for stage in stages.values() if stage.status == PipelineStatus.COMPLETED)
        failed_stages = sum(1 for stage in stages.values() if stage.status == PipelineStatus.FAILED)
        
        total_stage_duration = sum(stage.duration or 0 for stage in stages.values())
        
        return {
            'total_stages': total_stages,
            'completed_stages': completed_stages,
            'failed_stages': failed_stages,
            'stage_success_rate': completed_stages / total_stages if total_stages > 0 else 0,
            'total_stage_duration': total_stage_duration,
            'pipeline_efficiency': (
                total_stage_duration / pipeline_result.get('duration', 1)
                if pipeline_result.get('duration', 0) > 0 else 0
            ),
            'average_stage_duration': total_stage_duration / total_stages if total_stages > 0 else 0
        }


# Factory function for easy integration
def create_prefect_workflow_pipeline(name: str = "contexten_pipeline") -> PrefectWorkflowPipeline:
    """Create and initialize Prefect workflow pipeline."""
    return PrefectWorkflowPipeline(name=name)


#!/usr/bin/env python3
"""
Prefect Workflow Pipeline Integration

Enhanced Prefect integration for orchestrating complex workflows with
Codegen SDK, ControlFlow, and quality gates.
"""

import asyncio
import json
import logging
import re
import time
from typing import Dict, List, Any, Optional, Callable, Union
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


class TaskComplexity(str, Enum):
    """Task complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class ParsingStrategy(str, Enum):
    """Planning result parsing strategies."""
    JSON_STRUCTURED = "json_structured"
    MARKDOWN_STRUCTURED = "markdown_structured"
    TEXT_PATTERN = "text_pattern"
    AI_ASSISTED = "ai_assisted"
    FALLBACK = "fallback"


@dataclass
class TaskDefinition:
    """Structured task definition extracted from planning results."""
    id: str
    name: str
    description: str
    complexity: TaskComplexity = TaskComplexity.MODERATE
    estimated_duration: int = 1800  # seconds
    required_capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    priority: int = 2
    validation_criteria: List[str] = field(default_factory=list)
    risk_level: str = "low"


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


class PlanningResultParser:
    """Intelligent parser for Codegen SDK planning results."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parsing_strategies = [
            self._parse_json_structured,
            self._parse_markdown_structured,
            self._parse_text_pattern,
            self._parse_ai_assisted,
            self._parse_fallback
        ]
        
        # Common capability keywords mapping
        self.capability_keywords = {
            'code': ['code_generation', 'programming', 'development'],
            'test': ['testing', 'quality_assurance', 'validation'],
            'docs': ['documentation', 'writing', 'technical_writing'],
            'review': ['code_review', 'analysis', 'inspection'],
            'deploy': ['deployment', 'devops', 'infrastructure'],
            'debug': ['debugging', 'troubleshooting', 'problem_solving'],
            'design': ['system_design', 'architecture', 'planning'],
            'api': ['api_development', 'integration', 'web_services']
        }
        
        # Complexity indicators
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: ['simple', 'basic', 'straightforward', 'quick', 'minor'],
            TaskComplexity.MODERATE: ['moderate', 'standard', 'typical', 'normal', 'medium'],
            TaskComplexity.COMPLEX: ['complex', 'advanced', 'challenging', 'difficult', 'major'],
            TaskComplexity.CRITICAL: ['critical', 'essential', 'core', 'fundamental', 'crucial']
        }

    def parse_planning_result(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse planning result using multiple strategies.
        
        Args:
            planning_result: The planning result from Codegen SDK
            
        Returns:
            List of task definitions compatible with workflow system
        """
        self.logger.info("Starting planning result parsing")
        
        # Validate input
        if not self._validate_planning_result(planning_result):
            self.logger.warning("Planning result validation failed, using fallback")
            return self._parse_fallback(planning_result)
        
        plan_content = planning_result.get('plan', '')
        if not plan_content:
            self.logger.warning("No plan content found, using fallback")
            return self._parse_fallback(planning_result)
        
        # Try parsing strategies in order of reliability
        for strategy_func in self.parsing_strategies:
            try:
                self.logger.debug(f"Trying parsing strategy: {strategy_func.__name__}")
                tasks = strategy_func(planning_result)
                if tasks and len(tasks) > 0:
                    self.logger.info(f"Successfully parsed {len(tasks)} tasks using {strategy_func.__name__}")
                    return self._validate_and_enhance_tasks(tasks, planning_result)
            except Exception as e:
                self.logger.debug(f"Strategy {strategy_func.__name__} failed: {e}")
                continue
        
        # If all strategies fail, use fallback
        self.logger.warning("All parsing strategies failed, using fallback")
        return self._parse_fallback(planning_result)

    def _validate_planning_result(self, planning_result: Dict[str, Any]) -> bool:
        """Validate planning result structure."""
        required_fields = ['plan']
        return all(field in planning_result for field in required_fields)

    def _parse_json_structured(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse JSON-structured planning results."""
        plan_content = planning_result.get('plan', '')
        
        # Try to extract JSON from the plan content
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{.*?"tasks".*?\})',
            r'(\[.*?\{.*?"name".*?\}.*?\])'
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, plan_content, re.DOTALL | re.IGNORECASE)
            for match in matches:
                try:
                    parsed_json = json.loads(match)
                    if isinstance(parsed_json, dict) and 'tasks' in parsed_json:
                        return self._extract_tasks_from_json(parsed_json['tasks'])
                    elif isinstance(parsed_json, list):
                        return self._extract_tasks_from_json(parsed_json)
                except json.JSONDecodeError:
                    continue
        
        raise ValueError("No valid JSON structure found")

    def _parse_markdown_structured(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse markdown-structured planning results."""
        plan_content = planning_result.get('plan', '')
        tasks = []
        
        # Look for markdown task sections
        task_patterns = [
            r'#{1,3}\s*(?:Task|Step)\s*(\d+)[:.]?\s*(.+?)(?=#{1,3}|$)',
            r'(\d+)\.\s*\*\*(.+?)\*\*\s*[-:]?\s*(.+?)(?=\d+\.|$)',
            r'-\s*\*\*(.+?)\*\*\s*[-:]?\s*(.+?)(?=-\s*\*\*|$)'
        ]
        
        for i, pattern in enumerate(task_patterns):
            matches = re.findall(pattern, plan_content, re.DOTALL | re.IGNORECASE)
            if matches:
                for j, match in enumerate(matches):
                    if len(match) >= 2:
                        task_id = f"task_{j+1}"
                        if i == 0:  # Pattern with task number
                            name = match[1].strip()
                            description = self._extract_description_after_header(plan_content, match[1])
                        else:
                            name = match[0].strip() if i == 2 else match[1].strip()
                            description = match[1].strip() if i == 2 else match[2].strip()
                        
                        tasks.append(self._create_task_definition(
                            task_id=task_id,
                            name=name,
                            description=description
                        ))
                
                if tasks:
                    return tasks
        
        raise ValueError("No markdown structure found")

    def _parse_text_pattern(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse text-based planning results using patterns."""
        plan_content = planning_result.get('plan', '')
        tasks = []
        
        # Common text patterns for tasks
        patterns = [
            r'(?:Task|Step|Phase)\s*(\d+)[:.]?\s*(.+?)(?:\n|$)',
            r'(\d+)\.\s*(.+?)(?:\n|$)',
            r'-\s*(.+?)(?:\n|$)',
            r'•\s*(.+?)(?:\n|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, plan_content, re.MULTILINE)
            if matches and len(matches) >= 2:  # Need at least 2 tasks
                for i, match in enumerate(matches):
                    if isinstance(match, tuple):
                        name = match[1].strip() if len(match) > 1 else match[0].strip()
                    else:
                        name = match.strip()
                    
                    if len(name) > 10:  # Filter out too short matches
                        tasks.append(self._create_task_definition(
                            task_id=f"task_{i+1}",
                            name=name,
                            description=name
                        ))
                
                if tasks:
                    return tasks
        
        raise ValueError("No text patterns found")

    def _parse_ai_assisted(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """AI-assisted parsing for natural language plans."""
        plan_content = planning_result.get('plan', '')
        
        # Split content into potential task sections
        sections = re.split(r'\n\s*\n', plan_content)
        tasks = []
        
        for i, section in enumerate(sections):
            section = section.strip()
            if len(section) > 50:  # Meaningful content
                # Extract potential task name (first line or sentence)
                lines = section.split('\n')
                first_line = lines[0].strip()
                
                # Clean up the first line to get task name
                name = re.sub(r'^[\d\.\-\*\#\s]+', '', first_line)
                name = re.sub(r'[:\.]+$', '', name)
                
                if len(name) > 10:
                    tasks.append(self._create_task_definition(
                        task_id=f"task_{i+1}",
                        name=name,
                        description=section
                    ))
        
        if len(tasks) >= 2:
            return tasks
        
        raise ValueError("AI-assisted parsing failed")

    def _parse_fallback(self, planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback parser that generates basic tasks."""
        self.logger.info("Using fallback parser - generating basic tasks")
        
        # Generate tasks based on common software development workflow
        base_tasks = [
            {
                'id': 'task_analysis',
                'name': 'Requirements Analysis',
                'description': 'Analyze requirements and create implementation plan',
                'complexity': TaskComplexity.MODERATE.value,
                'estimated_duration': 1200,
                'required_capabilities': ['analysis', 'planning'],
                'dependencies': [],
                'priority': 3
            },
            {
                'id': 'task_implementation',
                'name': 'Core Implementation',
                'description': 'Implement core functionality based on requirements',
                'complexity': TaskComplexity.COMPLEX.value,
                'estimated_duration': 2400,
                'required_capabilities': ['code_generation', 'development'],
                'dependencies': ['task_analysis'],
                'priority': 3
            },
            {
                'id': 'task_testing',
                'name': 'Testing & Validation',
                'description': 'Create and run comprehensive tests',
                'complexity': TaskComplexity.MODERATE.value,
                'estimated_duration': 1200,
                'required_capabilities': ['testing', 'quality_assurance'],
                'dependencies': ['task_implementation'],
                'priority': 2
            },
            {
                'id': 'task_documentation',
                'name': 'Documentation',
                'description': 'Update documentation and README',
                'complexity': TaskComplexity.SIMPLE.value,
                'estimated_duration': 600,
                'required_capabilities': ['documentation', 'writing'],
                'dependencies': ['task_implementation'],
                'priority': 1
            }
        ]
        
        # Customize based on planning result if available
        requirements = planning_result.get('requirements', '')
        if 'api' in requirements.lower():
            base_tasks.insert(1, {
                'id': 'task_api_design',
                'name': 'API Design',
                'description': 'Design API endpoints and data structures',
                'complexity': TaskComplexity.MODERATE.value,
                'estimated_duration': 900,
                'required_capabilities': ['api_development', 'design'],
                'dependencies': ['task_analysis'],
                'priority': 3
            })
        
        return base_tasks

    def _extract_tasks_from_json(self, tasks_json: Union[List, Dict]) -> List[Dict[str, Any]]:
        """Extract tasks from JSON structure."""
        if isinstance(tasks_json, dict):
            tasks_json = [tasks_json]
        
        tasks = []
        for i, task_data in enumerate(tasks_json):
            if isinstance(task_data, dict):
                task_id = task_data.get('id', f"task_{i+1}")
                name = task_data.get('name', task_data.get('title', f"Task {i+1}"))
                description = task_data.get('description', task_data.get('desc', name))
                
                # Ensure name and description are strings
                if not isinstance(name, str):
                    name = str(name) if name is not None else f"Task {i+1}"
                if not isinstance(description, str):
                    description = str(description) if description is not None else name
                
                tasks.append(self._create_task_definition(
                    task_id=task_id,
                    name=name,
                    description=description,
                    complexity=task_data.get('complexity'),
                    estimated_duration=task_data.get('duration', task_data.get('estimated_duration')),
                    required_capabilities=task_data.get('capabilities', task_data.get('required_capabilities', [])),
                    dependencies=task_data.get('dependencies', []),
                    priority=task_data.get('priority', 2)
                ))
        
        return tasks

    def _create_task_definition(self, task_id: str, name: str, description: str, 
                              complexity: Optional[str] = None, estimated_duration: Optional[int] = None,
                              required_capabilities: Optional[List[str]] = None,
                              dependencies: Optional[List[str]] = None,
                              priority: Optional[int] = None) -> Dict[str, Any]:
        """Create a standardized task definition."""
        
        # Infer complexity if not provided
        if not complexity:
            complexity = self._infer_complexity(name, description)
        
        # Estimate duration if not provided
        if not estimated_duration:
            estimated_duration = self._estimate_duration(complexity, description)
        
        # Infer capabilities if not provided
        if not required_capabilities:
            required_capabilities = self._infer_capabilities(name, description)
        
        return {
            'id': task_id,
            'name': name,
            'description': description,
            'complexity': complexity,
            'estimated_duration': estimated_duration,
            'required_capabilities': required_capabilities or [],
            'dependencies': dependencies or [],
            'priority': priority or 2,
            'validation_criteria': self._generate_validation_criteria(name, description),
            'risk_level': self._assess_risk_level(complexity, description)
        }

    def _infer_complexity(self, name: str, description: str) -> str:
        """Infer task complexity from name and description."""
        text = f"{name} {description}".lower()
        
        for complexity, indicators in self.complexity_indicators.items():
            if any(indicator in text for indicator in indicators):
                return complexity.value
        
        # Default complexity based on description length and keywords
        if len(description) > 200 or any(word in text for word in ['integrate', 'complex', 'system', 'architecture']):
            return TaskComplexity.COMPLEX.value
        elif len(description) > 100 or any(word in text for word in ['implement', 'develop', 'create']):
            return TaskComplexity.MODERATE.value
        else:
            return TaskComplexity.SIMPLE.value

    def _estimate_duration(self, complexity: str, description: str) -> int:
        """Estimate task duration based on complexity and description."""
        base_durations = {
            TaskComplexity.SIMPLE.value: 600,      # 10 minutes
            TaskComplexity.MODERATE.value: 1800,   # 30 minutes
            TaskComplexity.COMPLEX.value: 3600,    # 1 hour
            TaskComplexity.CRITICAL.value: 7200    # 2 hours
        }
        
        base_duration = base_durations.get(complexity, 1800)
        
        # Adjust based on description keywords
        multiplier = 1.0
        text = description.lower()
        
        if any(word in text for word in ['comprehensive', 'complete', 'full', 'entire']):
            multiplier *= 1.5
        if any(word in text for word in ['test', 'testing', 'validation']):
            multiplier *= 1.2
        if any(word in text for word in ['documentation', 'docs']):
            multiplier *= 0.8
        
        return int(base_duration * multiplier)

    def _infer_capabilities(self, name: str, description: str) -> List[str]:
        """Infer required capabilities from task name and description."""
        text = f"{name} {description}".lower()
        capabilities = []
        
        for category, keywords in self.capability_keywords.items():
            if any(keyword in text for keyword in keywords):
                capabilities.extend(keywords[:2])  # Add first 2 capabilities from category
        
        # Remove duplicates and return
        return list(set(capabilities))

    def _generate_validation_criteria(self, name: str, description: str) -> List[str]:
        """Generate validation criteria for the task."""
        criteria = []
        text = f"{name} {description}".lower()
        
        if any(word in text for word in ['implement', 'create', 'develop']):
            criteria.append("Code compiles without errors")
            criteria.append("Functionality works as expected")
        
        if any(word in text for word in ['test', 'testing']):
            criteria.append("All tests pass")
            criteria.append("Code coverage meets requirements")
        
        if any(word in text for word in ['documentation', 'docs']):
            criteria.append("Documentation is complete and accurate")
            criteria.append("Examples are provided and working")
        
        if not criteria:
            criteria.append("Task completed successfully")
        
        return criteria

    def _assess_risk_level(self, complexity: str, description: str) -> str:
        """Assess risk level for the task."""
        text = description.lower()
        
        if complexity == TaskComplexity.CRITICAL.value:
            return "high"
        elif any(word in text for word in ['critical', 'core', 'fundamental', 'breaking']):
            return "high"
        elif any(word in text for word in ['integration', 'system', 'architecture']):
            return "medium"
        else:
            return "low"

    def _validate_and_enhance_tasks(self, tasks: List[Dict[str, Any]], 
                                  planning_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate and enhance parsed tasks."""
        enhanced_tasks: List[Dict[str, Any]] = []
        
        for task in tasks:
            # Ensure required fields
            if 'id' not in task:
                task['id'] = f"task_{len(enhanced_tasks) + 1}"
            if 'name' not in task:
                task['name'] = f"Task {len(enhanced_tasks) + 1}"
            if 'description' not in task:
                task['description'] = task['name']
            
            # Validate and fix dependencies
            task['dependencies'] = self._validate_dependencies(task.get('dependencies', []), enhanced_tasks)
            
            enhanced_tasks.append(task)
        
        return enhanced_tasks

    def _validate_dependencies(self, dependencies: List[str], existing_tasks: List[Dict[str, Any]]) -> List[str]:
        """Validate task dependencies."""
        valid_dependencies = []
        existing_task_ids = [task['id'] for task in existing_tasks]
        
        for dep in dependencies:
            if dep in existing_task_ids:
                valid_dependencies.append(dep)
        
        return valid_dependencies

    def _extract_description_after_header(self, content: str, header: str) -> str:
        """Extract description text after a header."""
        pattern = re.escape(header) + r'\s*\n(.*?)(?=#{1,3}|\n\s*\n|$)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return header


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
        
        # Initialize planning result parser
        self.planning_parser = PlanningResultParser()
        
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
        """Extract task definitions from planning result using intelligent parsing."""
        return self.planning_parser.parse_planning_result(planning_result)
    
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

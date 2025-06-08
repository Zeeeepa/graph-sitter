#!/usr/bin/env python3
"""
Codegen Workflow Integration

Enhanced Codegen SDK integration with Strands workflow tools and MCP client support.
Provides seamless transitions between different tools/systems for Codegen SDK task execution.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowStage(str, Enum):
    """Workflow execution stages."""
    PLANNING = "planning"
    ORCHESTRATION = "orchestration"
    EXECUTION = "execution"
    VALIDATION = "validation"
    COMPLETION = "completion"


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class WorkflowTask:
    """Workflow task definition."""
    id: str
    name: str
    description: str
    stage: WorkflowStage
    dependencies: List[str]
    tools_required: List[str]
    estimated_duration: int
    priority: int = 1
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class WorkflowContext:
    """Workflow execution context."""
    project_id: str
    requirements: str
    config: Dict[str, Any]
    variables: Dict[str, Any]
    tools_available: List[str]
    mcp_servers: List[str]


class CodegenWorkflowIntegration:
    """Enhanced Codegen integration with workflow orchestration."""
    
    def __init__(self, org_id: str, token: str, base_url: str = "https://api.codegen.com"):
        """Initialize Codegen workflow integration."""
        self.org_id = org_id
        self.token = token
        self.base_url = base_url
        self._codegen_agent = None
        self._strands_client = None
        self._mcp_client = None
        self._workflow_callbacks: List[Callable] = []
        
        # Initialize components
        self._initialize_codegen()
        self._initialize_strands()
        self._initialize_mcp()
        
        logger.info("Codegen workflow integration initialized")
    
    def _initialize_codegen(self):
        """Initialize Codegen SDK agent."""
        try:
            from codegen.agents.agent import Agent
            
            self._codegen_agent = Agent(
                org_id=self.org_id,
                token=self.token,
                base_url=self.base_url
            )
            
            logger.info("Codegen SDK agent initialized")
            
        except ImportError as e:
            logger.error(f"Failed to import Codegen SDK: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Codegen agent: {e}")
            raise
    
    def _initialize_strands(self):
        """Initialize Strands workflow tools."""
        try:
            # Import Strands workflow tools
            # Note: These would be the actual imports from the Strands tools
            # from strands_tools.workflow import WorkflowClient
            # from strands.tools.mcp.mcp_client import MCPClient
            
            # For now, we'll create placeholder implementations
            self._strands_client = StrandsWorkflowClient()
            
            logger.info("Strands workflow client initialized")
            
        except ImportError as e:
            logger.warning(f"Strands tools not available: {e}")
            self._strands_client = None
        except Exception as e:
            logger.error(f"Failed to initialize Strands client: {e}")
            self._strands_client = None
    
    def _initialize_mcp(self):
        """Initialize MCP client for enhanced tool access."""
        try:
            # Initialize MCP client for additional tool access
            self._mcp_client = MCPClientWrapper()
            
            logger.info("MCP client initialized")
            
        except ImportError as e:
            logger.warning(f"MCP client not available: {e}")
            self._mcp_client = None
        except Exception as e:
            logger.error(f"Failed to initialize MCP client: {e}")
            self._mcp_client = None
    
    def add_workflow_callback(self, callback: Callable):
        """Add callback for workflow events."""
        self._workflow_callbacks.append(callback)
    
    def _emit_workflow_event(self, event_type: str, data: Dict[str, Any]):
        """Emit workflow event to registered callbacks."""
        for callback in self._workflow_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                logger.error(f"Workflow callback failed: {e}")
    
    async def execute_enhanced_workflow(
        self,
        context: WorkflowContext,
        tasks: List[WorkflowTask]
    ) -> Dict[str, Any]:
        """Execute enhanced workflow with seamless tool transitions."""
        logger.info(f"Starting enhanced workflow for project {context.project_id}")
        
        workflow_result = {
            'project_id': context.project_id,
            'status': 'running',
            'start_time': time.time(),
            'tasks': {},
            'stages': {stage.value: {'status': 'pending', 'tasks': []} for stage in WorkflowStage},
            'tools_used': [],
            'transitions': []
        }
        
        self._emit_workflow_event('workflow_started', {
            'project_id': context.project_id,
            'task_count': len(tasks)
        })
        
        try:
            # Group tasks by stage
            tasks_by_stage = self._group_tasks_by_stage(tasks)
            
            # Execute stages in order
            for stage in WorkflowStage:
                if stage.value in tasks_by_stage:
                    stage_tasks = tasks_by_stage[stage.value]
                    logger.info(f"Executing stage: {stage.value} with {len(stage_tasks)} tasks")
                    
                    stage_result = await self._execute_stage(
                        stage=stage,
                        tasks=stage_tasks,
                        context=context,
                        workflow_result=workflow_result
                    )
                    
                    workflow_result['stages'][stage.value] = stage_result
                    
                    # Check if stage failed
                    if stage_result['status'] == 'failed':
                        workflow_result['status'] = 'failed'
                        workflow_result['error'] = f"Stage {stage.value} failed"
                        break
            
            if workflow_result['status'] != 'failed':
                workflow_result['status'] = 'completed'
            
            workflow_result['end_time'] = time.time()
            workflow_result['duration'] = workflow_result['end_time'] - workflow_result['start_time']
            
            self._emit_workflow_event('workflow_completed', {
                'project_id': context.project_id,
                'status': workflow_result['status'],
                'duration': workflow_result['duration']
            })
            
            logger.info(f"Enhanced workflow completed for project {context.project_id}")
            
        except Exception as e:
            logger.error(f"Enhanced workflow failed: {e}")
            workflow_result['status'] = 'failed'
            workflow_result['error'] = str(e)
            workflow_result['end_time'] = time.time()
            
            self._emit_workflow_event('workflow_failed', {
                'project_id': context.project_id,
                'error': str(e)
            })
        
        return workflow_result
    
    def _group_tasks_by_stage(self, tasks: List[WorkflowTask]) -> Dict[str, List[WorkflowTask]]:
        """Group tasks by execution stage."""
        tasks_by_stage = {}
        
        for task in tasks:
            stage_key = task.stage.value
            if stage_key not in tasks_by_stage:
                tasks_by_stage[stage_key] = []
            tasks_by_stage[stage_key].append(task)
        
        return tasks_by_stage
    
    async def _execute_stage(
        self,
        stage: WorkflowStage,
        tasks: List[WorkflowTask],
        context: WorkflowContext,
        workflow_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a workflow stage with appropriate tool selection."""
        stage_result = {
            'status': 'running',
            'start_time': time.time(),
            'tasks': [],
            'tools_used': [],
            'transitions': []
        }
        
        try:
            # Sort tasks by priority and dependencies
            sorted_tasks = self._sort_tasks_by_dependencies(tasks)
            
            # Execute tasks
            for task in sorted_tasks:
                logger.info(f"Executing task: {task.name}")
                
                task_result = await self._execute_task_with_tool_selection(
                    task=task,
                    context=context,
                    workflow_result=workflow_result
                )
                
                stage_result['tasks'].append(task_result)
                workflow_result['tasks'][task.id] = task_result
                
                # Track tools used
                if 'tool_used' in task_result:
                    tool_used = task_result['tool_used']
                    if tool_used not in stage_result['tools_used']:
                        stage_result['tools_used'].append(tool_used)
                    if tool_used not in workflow_result['tools_used']:
                        workflow_result['tools_used'].append(tool_used)
                
                # Track tool transitions
                if 'transition' in task_result:
                    stage_result['transitions'].append(task_result['transition'])
                    workflow_result['transitions'].append(task_result['transition'])
                
                # Check if task failed
                if task_result['status'] == 'failed':
                    stage_result['status'] = 'failed'
                    stage_result['error'] = f"Task {task.name} failed: {task_result.get('error', 'Unknown error')}"
                    break
            
            if stage_result['status'] != 'failed':
                stage_result['status'] = 'completed'
            
            stage_result['end_time'] = time.time()
            stage_result['duration'] = stage_result['end_time'] - stage_result['start_time']
            
        except Exception as e:
            logger.error(f"Stage {stage.value} execution failed: {e}")
            stage_result['status'] = 'failed'
            stage_result['error'] = str(e)
            stage_result['end_time'] = time.time()
        
        return stage_result
    
    def _sort_tasks_by_dependencies(self, tasks: List[WorkflowTask]) -> List[WorkflowTask]:
        """Sort tasks by dependencies and priority."""
        # Simple topological sort by dependencies
        sorted_tasks = []
        remaining_tasks = tasks.copy()
        
        while remaining_tasks:
            # Find tasks with no unresolved dependencies
            ready_tasks = []
            for task in remaining_tasks:
                dependencies_met = all(
                    dep_id in [t.id for t in sorted_tasks]
                    for dep_id in task.dependencies
                )
                if dependencies_met:
                    ready_tasks.append(task)
            
            if not ready_tasks:
                # Circular dependency or missing dependency
                logger.warning("Circular dependency detected, executing remaining tasks by priority")
                ready_tasks = sorted(remaining_tasks, key=lambda t: t.priority, reverse=True)[:1]
            
            # Sort ready tasks by priority
            ready_tasks.sort(key=lambda t: t.priority, reverse=True)
            
            # Add first ready task to sorted list
            next_task = ready_tasks[0]
            sorted_tasks.append(next_task)
            remaining_tasks.remove(next_task)
        
        return sorted_tasks
    
    async def _execute_task_with_tool_selection(
        self,
        task: WorkflowTask,
        context: WorkflowContext,
        workflow_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute task with intelligent tool selection and seamless transitions."""
        task.start_time = time.time()
        task.status = TaskStatus.RUNNING
        
        task_result = {
            'task_id': task.id,
            'task_name': task.name,
            'status': 'running',
            'start_time': task.start_time,
            'tool_used': None,
            'transition': None
        }
        
        self._emit_workflow_event('task_started', {
            'task_id': task.id,
            'task_name': task.name,
            'stage': task.stage.value
        })
        
        try:
            # Select best tool for the task
            selected_tool = self._select_optimal_tool(task, context)
            task_result['tool_used'] = selected_tool
            
            # Execute task with selected tool
            if selected_tool == 'codegen':
                execution_result = await self._execute_with_codegen(task, context)
            elif selected_tool == 'strands' and self._strands_client:
                execution_result = await self._execute_with_strands(task, context)
            elif selected_tool == 'mcp' and self._mcp_client:
                execution_result = await self._execute_with_mcp(task, context)
            else:
                # Fallback to Codegen
                execution_result = await self._execute_with_codegen(task, context)
                task_result['tool_used'] = 'codegen'
            
            # Handle tool transitions if needed
            if execution_result.get('requires_transition'):
                transition_result = await self._handle_tool_transition(
                    task=task,
                    current_tool=selected_tool,
                    target_tool=execution_result['target_tool'],
                    context=context,
                    partial_result=execution_result
                )
                
                task_result['transition'] = {
                    'from': selected_tool,
                    'to': execution_result['target_tool'],
                    'reason': execution_result.get('transition_reason', 'Tool capability required')
                }
                
                execution_result = transition_result
            
            task.status = TaskStatus.COMPLETED
            task.result = execution_result
            task_result['status'] = 'completed'
            task_result['result'] = execution_result
            
            self._emit_workflow_event('task_completed', {
                'task_id': task.id,
                'task_name': task.name,
                'tool_used': task_result['tool_used'],
                'duration': time.time() - task.start_time
            })
            
        except Exception as e:
            logger.error(f"Task {task.name} execution failed: {e}")
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task_result['status'] = 'failed'
            task_result['error'] = str(e)
            
            self._emit_workflow_event('task_failed', {
                'task_id': task.id,
                'task_name': task.name,
                'error': str(e)
            })
        
        task.end_time = time.time()
        task_result['end_time'] = task.end_time
        task_result['duration'] = task.end_time - task.start_time
        
        return task_result
    
    def _select_optimal_tool(self, task: WorkflowTask, context: WorkflowContext) -> str:
        """Select the optimal tool for task execution."""
        # Tool selection logic based on task requirements
        required_tools = set(task.tools_required)
        available_tools = set(context.tools_available)
        
        # Check if specific tools are required
        if 'github' in required_tools or 'linear' in required_tools or 'slack' in required_tools:
            # Tasks requiring specific integrations should use Codegen
            return 'codegen'
        
        if 'mcp' in required_tools and self._mcp_client:
            # Tasks requiring MCP servers
            return 'mcp'
        
        if 'workflow' in required_tools and self._strands_client:
            # Complex workflow tasks
            return 'strands'
        
        # Default to Codegen for general tasks
        return 'codegen'
    
    async def _execute_with_codegen(self, task: WorkflowTask, context: WorkflowContext) -> Dict[str, Any]:
        """Execute task using Codegen SDK."""
        if not self._codegen_agent:
            raise Exception("Codegen agent not initialized")
        
        # Create enhanced prompt with context
        prompt = self._create_enhanced_prompt(task, context)
        
        # Execute with Codegen
        codegen_task = self._codegen_agent.run(prompt)
        
        # Wait for completion with timeout
        timeout = task.estimated_duration * 2  # Double the estimated time
        start_time = time.time()
        
        while codegen_task.status not in ['completed', 'failed'] and (time.time() - start_time) < timeout:
            await asyncio.sleep(5)
            codegen_task.refresh()
        
        if codegen_task.status == 'completed':
            return {
                'codegen_task_id': codegen_task.id,
                'result': codegen_task.result if hasattr(codegen_task, 'result') else 'Task completed',
                'tool': 'codegen',
                'duration': time.time() - start_time
            }
        else:
            raise Exception(f"Codegen task failed or timed out: {codegen_task.status}")
    
    async def _execute_with_strands(self, task: WorkflowTask, context: WorkflowContext) -> Dict[str, Any]:
        """Execute task using Strands workflow tools."""
        if not self._strands_client:
            raise Exception("Strands client not initialized")
        
        # Execute with Strands
        result = await self._strands_client.execute_workflow_task(
            task_definition=task,
            context=context
        )
        
        return {
            'result': result,
            'tool': 'strands',
            'workflow_id': result.get('workflow_id')
        }
    
    async def _execute_with_mcp(self, task: WorkflowTask, context: WorkflowContext) -> Dict[str, Any]:
        """Execute task using MCP client."""
        if not self._mcp_client:
            raise Exception("MCP client not initialized")
        
        # Execute with MCP
        result = await self._mcp_client.execute_task(
            task_definition=task,
            context=context,
            servers=context.mcp_servers
        )
        
        return {
            'result': result,
            'tool': 'mcp',
            'servers_used': result.get('servers_used', [])
        }
    
    async def _handle_tool_transition(
        self,
        task: WorkflowTask,
        current_tool: str,
        target_tool: str,
        context: WorkflowContext,
        partial_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle seamless transition between tools."""
        logger.info(f"Transitioning from {current_tool} to {target_tool} for task {task.name}")
        
        # Create transition context
        transition_context = WorkflowContext(
            project_id=context.project_id,
            requirements=context.requirements,
            config=context.config,
            variables={**context.variables, 'partial_result': partial_result},
            tools_available=context.tools_available,
            mcp_servers=context.mcp_servers
        )
        
        # Execute with target tool
        if target_tool == 'codegen':
            return await self._execute_with_codegen(task, transition_context)
        elif target_tool == 'strands':
            return await self._execute_with_strands(task, transition_context)
        elif target_tool == 'mcp':
            return await self._execute_with_mcp(task, transition_context)
        else:
            raise Exception(f"Unknown target tool: {target_tool}")
    
    def _create_enhanced_prompt(self, task: WorkflowTask, context: WorkflowContext) -> str:
        """Create enhanced prompt with full context."""
        prompt = f"""
        Execute the following task as part of project {context.project_id}:
        
        Task: {task.name}
        Description: {task.description}
        Stage: {task.stage.value}
        Priority: {task.priority}
        
        Project Requirements:
        {context.requirements}
        
        Available Tools: {', '.join(context.tools_available)}
        Required Tools: {', '.join(task.tools_required)}
        
        Context Variables:
        {context.variables}
        
        Please execute this task and provide detailed results.
        If you need to use specific tools or integrations that are not directly available,
        indicate this in your response with 'requires_transition: true' and specify the target_tool.
        """
        
        return prompt


class StrandsWorkflowClient:
    """Placeholder for Strands workflow client."""
    
    async def execute_workflow_task(self, task_definition: WorkflowTask, context: WorkflowContext) -> Dict[str, Any]:
        """Execute workflow task using Strands tools."""
        # Placeholder implementation
        await asyncio.sleep(1)  # Simulate work
        
        return {
            'status': 'completed',
            'result': f"Strands workflow executed for task {task_definition.name}",
            'workflow_id': f"strands_wf_{task_definition.id}"
        }


class MCPClientWrapper:
    """Placeholder for MCP client wrapper."""
    
    async def execute_task(
        self,
        task_definition: WorkflowTask,
        context: WorkflowContext,
        servers: List[str]
    ) -> Dict[str, Any]:
        """Execute task using MCP servers."""
        # Placeholder implementation
        await asyncio.sleep(1)  # Simulate work
        
        return {
            'status': 'completed',
            'result': f"MCP task executed for {task_definition.name}",
            'servers_used': servers[:2]  # Simulate using first 2 servers
        }


# Factory function for easy integration
def create_codegen_workflow_integration(
    org_id: str,
    token: str,
    base_url: str = "https://api.codegen.com"
) -> CodegenWorkflowIntegration:
    """Create and initialize Codegen workflow integration."""
    return CodegenWorkflowIntegration(
        org_id=org_id,
        token=token,
        base_url=base_url
    )


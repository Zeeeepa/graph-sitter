"""
Strands Orchestrator - Multi-layer workflow coordination.
Coordinates Strands Workflow, MCP, ControlFlow, and Prefect layers.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..consolidated_models import (
    Flow, Task, FlowStatus, TaskStatus, ServiceStatus
)

logger = logging.getLogger(__name__)


class StrandsOrchestrator:
    """
    Multi-layer orchestrator that coordinates:
    - Top Layer: Prefect flows for high-level workflow management
    - Middle Layer: ControlFlow system for task orchestration  
    - Bottom Layer: MCP-based agentic flows for granular execution
    - Integration Layer: Strands Workflow for unified management
    """
    
    def __init__(self):
        """Initialize the Strands Orchestrator."""
        self.active_workflows: Dict[str, Flow] = {}
        self.workflow_managers = {}
        
        # Initialize layer managers
        self._init_layer_managers()
    
    def _init_layer_managers(self):
        """Initialize all layer managers with fallbacks."""
        try:
            # Try to import actual Strands tools
            from strands_tools.workflow import WorkflowManager
            self.workflow_managers['strands'] = WorkflowManager()
        except ImportError:
            logger.warning("Strands tools not available, using mock implementation")
            self.workflow_managers['strands'] = MockStrandsWorkflowManager()
        
        try:
            # Try to import actual MCP client
            from strands.tools.mcp.mcp_client import MCPClient
            self.workflow_managers['mcp'] = MCPClient()
        except ImportError:
            logger.warning("Strands MCP client not available, using mock implementation")
            self.workflow_managers['mcp'] = MockMCPManager()
        
        try:
            # Try to import ControlFlow
            import controlflow
            self.workflow_managers['controlflow'] = ControlFlowManager()
        except ImportError:
            logger.warning("ControlFlow not available, using mock implementation")
            self.workflow_managers['controlflow'] = MockControlFlowManager()
        
        try:
            # Try to import Prefect
            import prefect
            self.workflow_managers['prefect'] = PrefectManager()
        except ImportError:
            logger.warning("Prefect not available, using mock implementation")
            self.workflow_managers['prefect'] = MockPrefectManager()
    
    async def start_workflow(
        self,
        project_id: str,
        requirements: str,
        flow_name: Optional[str] = None,
        auto_execute: bool = True
    ) -> Flow:
        """Start a multi-layer workflow orchestration."""
        flow_id = str(uuid.uuid4())
        flow_name = flow_name or f"Workflow for {project_id}"
        
        # Create flow object
        flow = Flow(
            id=flow_id,
            project_id=project_id,
            name=flow_name,
            description=f"Multi-layer orchestration for: {requirements}",
            status=FlowStatus.PLANNING,
            original_requirements=requirements
        )
        
        self.active_workflows[flow_id] = flow
        
        try:
            # Step 1: Initialize Strands Workflow layer
            strands_workflow_id = await self._init_strands_workflow(flow)
            flow.strands_workflow_id = strands_workflow_id
            
            # Step 2: Create Prefect flow for high-level orchestration
            prefect_flow_id = await self._create_prefect_flow(flow)
            flow.prefect_flow_run_id = prefect_flow_id
            
            # Step 3: Setup ControlFlow for task management
            controlflow_flow_id = await self._setup_controlflow(flow)
            flow.controlflow_flow_id = controlflow_flow_id
            
            # Step 4: Generate plan and tasks
            await self._generate_workflow_plan(flow)
            
            # Step 5: Start execution if auto_execute is True
            if auto_execute:
                flow.status = FlowStatus.RUNNING
                flow.started_at = datetime.now()
                await self._execute_workflow(flow)
            else:
                flow.status = FlowStatus.IDLE
            
            return flow
            
        except Exception as e:
            logger.error(f"Failed to start workflow {flow_id}: {e}")
            flow.status = FlowStatus.FAILED
            flow.error_message = str(e)
            raise
    
    async def _init_strands_workflow(self, flow: Flow) -> str:
        """Initialize Strands Workflow layer."""
        try:
            strands_manager = self.workflow_managers['strands']
            workflow_id = await strands_manager.create_workflow(
                name=flow.name,
                description=flow.description,
                project_id=flow.project_id
            )
            logger.info(f"Initialized Strands workflow: {workflow_id}")
            return workflow_id
        except Exception as e:
            logger.error(f"Failed to initialize Strands workflow: {e}")
            raise
    
    async def _create_prefect_flow(self, flow: Flow) -> str:
        """Create Prefect flow for high-level orchestration."""
        try:
            prefect_manager = self.workflow_managers['prefect']
            flow_run_id = await prefect_manager.create_flow_run(
                flow_name=f"orchestration_{flow.id}",
                parameters={
                    "project_id": flow.project_id,
                    "requirements": flow.original_requirements,
                    "flow_id": flow.id
                }
            )
            logger.info(f"Created Prefect flow run: {flow_run_id}")
            return flow_run_id
        except Exception as e:
            logger.error(f"Failed to create Prefect flow: {e}")
            raise
    
    async def _setup_controlflow(self, flow: Flow) -> str:
        """Setup ControlFlow for task management."""
        try:
            controlflow_manager = self.workflow_managers['controlflow']
            flow_id = await controlflow_manager.create_flow(
                name=flow.name,
                description=flow.description,
                project_context={
                    "project_id": flow.project_id,
                    "requirements": flow.original_requirements
                }
            )
            logger.info(f"Setup ControlFlow: {flow_id}")
            return flow_id
        except Exception as e:
            logger.error(f"Failed to setup ControlFlow: {e}")
            raise
    
    async def _generate_workflow_plan(self, flow: Flow):
        """Generate workflow plan and tasks."""
        try:
            # Use Strands workflow to generate plan
            strands_manager = self.workflow_managers['strands']
            plan = await strands_manager.generate_plan(
                workflow_id=flow.strands_workflow_id,
                requirements=flow.original_requirements
            )
            
            flow.generated_plan = plan
            
            # Create tasks based on plan
            tasks = []
            for i, step in enumerate(plan.get('steps', [])):
                task = Task(
                    id=str(uuid.uuid4()),
                    flow_id=flow.id,
                    project_id=flow.project_id,
                    title=step.get('title', f'Task {i+1}'),
                    description=step.get('description', ''),
                    task_type=step.get('type', 'general'),
                    dependencies=step.get('dependencies', [])
                )
                tasks.append(task)
            
            flow.tasks = tasks
            logger.info(f"Generated {len(tasks)} tasks for workflow {flow.id}")
            
        except Exception as e:
            logger.error(f"Failed to generate workflow plan: {e}")
            raise
    
    async def _execute_workflow(self, flow: Flow):
        """Execute the workflow across all layers."""
        try:
            # Start Prefect flow execution
            prefect_manager = self.workflow_managers['prefect']
            await prefect_manager.start_flow_run(flow.prefect_flow_run_id)
            
            # Execute tasks through ControlFlow
            controlflow_manager = self.workflow_managers['controlflow']
            for task in flow.tasks:
                # Create ControlFlow task
                cf_task_id = await controlflow_manager.create_task(
                    flow_id=flow.controlflow_flow_id,
                    name=task.title,
                    description=task.description,
                    task_type=task.task_type
                )
                task.controlflow_task_id = cf_task_id
                
                # Execute task through MCP if needed
                if task.task_type in ['codegen', 'analysis', 'validation']:
                    mcp_manager = self.workflow_managers['mcp']
                    mcp_task_id = await mcp_manager.execute_task(
                        task_description=task.description,
                        context={
                            "project_id": flow.project_id,
                            "flow_id": flow.id,
                            "task_id": task.id
                        }
                    )
                    task.mcp_task_id = mcp_task_id
            
            logger.info(f"Started execution for workflow {flow.id}")
            
        except Exception as e:
            logger.error(f"Failed to execute workflow: {e}")
            flow.status = FlowStatus.FAILED
            flow.error_message = str(e)
            raise
    
    async def get_workflow(self, flow_id: str) -> Optional[Flow]:
        """Get workflow by ID."""
        return self.active_workflows.get(flow_id)
    
    async def pause_workflow(self, flow_id: str) -> Optional[Flow]:
        """Pause a running workflow."""
        flow = self.active_workflows.get(flow_id)
        if not flow:
            return None
        
        try:
            # Pause across all layers
            if flow.prefect_flow_run_id:
                prefect_manager = self.workflow_managers['prefect']
                await prefect_manager.pause_flow_run(flow.prefect_flow_run_id)
            
            if flow.controlflow_flow_id:
                controlflow_manager = self.workflow_managers['controlflow']
                await controlflow_manager.pause_flow(flow.controlflow_flow_id)
            
            flow.status = FlowStatus.PAUSED
            logger.info(f"Paused workflow {flow_id}")
            return flow
            
        except Exception as e:
            logger.error(f"Failed to pause workflow {flow_id}: {e}")
            raise
    
    async def resume_workflow(self, flow_id: str) -> Optional[Flow]:
        """Resume a paused workflow."""
        flow = self.active_workflows.get(flow_id)
        if not flow:
            return None
        
        try:
            # Resume across all layers
            if flow.prefect_flow_run_id:
                prefect_manager = self.workflow_managers['prefect']
                await prefect_manager.resume_flow_run(flow.prefect_flow_run_id)
            
            if flow.controlflow_flow_id:
                controlflow_manager = self.workflow_managers['controlflow']
                await controlflow_manager.resume_flow(flow.controlflow_flow_id)
            
            flow.status = FlowStatus.RUNNING
            logger.info(f"Resumed workflow {flow_id}")
            return flow
            
        except Exception as e:
            logger.error(f"Failed to resume workflow {flow_id}: {e}")
            raise
    
    async def stop_workflow(self, flow_id: str) -> Optional[Flow]:
        """Stop a running workflow."""
        flow = self.active_workflows.get(flow_id)
        if not flow:
            return None
        
        try:
            # Stop across all layers
            if flow.prefect_flow_run_id:
                prefect_manager = self.workflow_managers['prefect']
                await prefect_manager.cancel_flow_run(flow.prefect_flow_run_id)
            
            if flow.controlflow_flow_id:
                controlflow_manager = self.workflow_managers['controlflow']
                await controlflow_manager.cancel_flow(flow.controlflow_flow_id)
            
            # Update task statuses
            for task in flow.tasks:
                if task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS]:
                    task.status = TaskStatus.CANCELLED
            
            flow.status = FlowStatus.CANCELLED
            flow.completed_at = datetime.now()
            logger.info(f"Stopped workflow {flow_id}")
            return flow
            
        except Exception as e:
            logger.error(f"Failed to stop workflow {flow_id}: {e}")
            raise
    
    async def monitor_workflow_execution(self, flow_id: str):
        """Monitor workflow execution and update status."""
        flow = self.active_workflows.get(flow_id)
        if not flow:
            return
        
        try:
            while flow.status == FlowStatus.RUNNING:
                # Check status across all layers
                await self._update_workflow_status(flow)
                await asyncio.sleep(10)  # Check every 10 seconds
                
        except Exception as e:
            logger.error(f"Workflow monitoring failed for {flow_id}: {e}")
    
    async def _update_workflow_status(self, flow: Flow):
        """Update workflow status based on layer statuses."""
        try:
            # Check Prefect status
            if flow.prefect_flow_run_id:
                prefect_manager = self.workflow_managers['prefect']
                prefect_status = await prefect_manager.get_flow_run_status(flow.prefect_flow_run_id)
                
                if prefect_status == "COMPLETED":
                    flow.status = FlowStatus.COMPLETED
                    flow.completed_at = datetime.now()
                elif prefect_status == "FAILED":
                    flow.status = FlowStatus.FAILED
                    flow.completed_at = datetime.now()
            
            # Update task statuses
            for task in flow.tasks:
                if task.controlflow_task_id:
                    controlflow_manager = self.workflow_managers['controlflow']
                    cf_status = await controlflow_manager.get_task_status(task.controlflow_task_id)
                    
                    if cf_status == "completed":
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.now()
                    elif cf_status == "failed":
                        task.status = TaskStatus.FAILED
                        task.completed_at = datetime.now()
                    elif cf_status == "running":
                        task.status = TaskStatus.IN_PROGRESS
                        if not task.started_at:
                            task.started_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Failed to update workflow status: {e}")
    
    # Status check methods for API
    async def check_workflow_status(self) -> ServiceStatus:
        """Check Strands Workflow status."""
        try:
            strands_manager = self.workflow_managers['strands']
            if hasattr(strands_manager, 'check_health'):
                health = await strands_manager.check_health()
                return ServiceStatus.CONNECTED if health else ServiceStatus.ERROR
            return ServiceStatus.CONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def check_mcp_status(self) -> ServiceStatus:
        """Check MCP status."""
        try:
            mcp_manager = self.workflow_managers['mcp']
            if hasattr(mcp_manager, 'check_health'):
                health = await mcp_manager.check_health()
                return ServiceStatus.CONNECTED if health else ServiceStatus.ERROR
            return ServiceStatus.CONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def check_controlflow_status(self) -> ServiceStatus:
        """Check ControlFlow status."""
        try:
            controlflow_manager = self.workflow_managers['controlflow']
            if hasattr(controlflow_manager, 'check_health'):
                health = await controlflow_manager.check_health()
                return ServiceStatus.CONNECTED if health else ServiceStatus.ERROR
            return ServiceStatus.CONNECTED
        except Exception:
            return ServiceStatus.ERROR
    
    async def check_prefect_status(self) -> ServiceStatus:
        """Check Prefect status."""
        try:
            prefect_manager = self.workflow_managers['prefect']
            if hasattr(prefect_manager, 'check_health'):
                health = await prefect_manager.check_health()
                return ServiceStatus.CONNECTED if health else ServiceStatus.ERROR
            return ServiceStatus.CONNECTED
        except Exception:
            return ServiceStatus.ERROR


# Mock implementations for development
class MockStrandsWorkflowManager:
    """Mock Strands Workflow Manager for development."""
    
    async def create_workflow(self, name: str, description: str, project_id: str) -> str:
        workflow_id = f"strands_workflow_{uuid.uuid4().hex[:8]}"
        logger.info(f"Mock: Created Strands workflow {workflow_id}")
        return workflow_id
    
    async def generate_plan(self, workflow_id: str, requirements: str) -> Dict[str, Any]:
        return {
            "workflow_id": workflow_id,
            "steps": [
                {
                    "title": "Analyze Requirements",
                    "description": f"Analyze the requirements: {requirements}",
                    "type": "analysis",
                    "dependencies": []
                },
                {
                    "title": "Generate Code",
                    "description": "Generate code based on analysis",
                    "type": "codegen",
                    "dependencies": ["step_1"]
                },
                {
                    "title": "Validate Quality",
                    "description": "Validate code quality and run tests",
                    "type": "validation",
                    "dependencies": ["step_2"]
                }
            ]
        }
    
    async def check_health(self) -> bool:
        return True


class MockMCPManager:
    """Mock MCP Manager for development."""
    
    async def execute_task(self, task_description: str, context: Dict[str, Any]) -> str:
        task_id = f"mcp_task_{uuid.uuid4().hex[:8]}"
        logger.info(f"Mock: Executing MCP task {task_id}: {task_description}")
        return task_id
    
    async def check_health(self) -> bool:
        return True


class MockControlFlowManager:
    """Mock ControlFlow Manager for development."""
    
    async def create_flow(self, name: str, description: str, project_context: Dict[str, Any]) -> str:
        flow_id = f"cf_flow_{uuid.uuid4().hex[:8]}"
        logger.info(f"Mock: Created ControlFlow {flow_id}")
        return flow_id
    
    async def create_task(self, flow_id: str, name: str, description: str, task_type: str) -> str:
        task_id = f"cf_task_{uuid.uuid4().hex[:8]}"
        logger.info(f"Mock: Created ControlFlow task {task_id}")
        return task_id
    
    async def pause_flow(self, flow_id: str):
        logger.info(f"Mock: Paused ControlFlow {flow_id}")
    
    async def resume_flow(self, flow_id: str):
        logger.info(f"Mock: Resumed ControlFlow {flow_id}")
    
    async def cancel_flow(self, flow_id: str):
        logger.info(f"Mock: Cancelled ControlFlow {flow_id}")
    
    async def get_task_status(self, task_id: str) -> str:
        return "completed"  # Mock status
    
    async def check_health(self) -> bool:
        return True


class MockPrefectManager:
    """Mock Prefect Manager for development."""
    
    async def create_flow_run(self, flow_name: str, parameters: Dict[str, Any]) -> str:
        flow_run_id = f"prefect_run_{uuid.uuid4().hex[:8]}"
        logger.info(f"Mock: Created Prefect flow run {flow_run_id}")
        return flow_run_id
    
    async def start_flow_run(self, flow_run_id: str):
        logger.info(f"Mock: Started Prefect flow run {flow_run_id}")
    
    async def pause_flow_run(self, flow_run_id: str):
        logger.info(f"Mock: Paused Prefect flow run {flow_run_id}")
    
    async def resume_flow_run(self, flow_run_id: str):
        logger.info(f"Mock: Resumed Prefect flow run {flow_run_id}")
    
    async def cancel_flow_run(self, flow_run_id: str):
        logger.info(f"Mock: Cancelled Prefect flow run {flow_run_id}")
    
    async def get_flow_run_status(self, flow_run_id: str) -> str:
        return "COMPLETED"  # Mock status
    
    async def check_health(self) -> bool:
        return True


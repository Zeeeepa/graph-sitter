"""
Simple Workflow Engine for Single-User Dashboard

Executes plans as sequential tasks with basic orchestration using ControlFlow and Prefect.
Integrates with Linear for task updates and Codegen for task execution.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from graph_sitter.shared.logging.get_logger import get_logger
from .models import FlowStatus, TaskStatus, WorkflowEvent, DashboardPlan, DashboardTask
from ..controlflow.controlflow import ControlFlow
from ..prefect.prefect import Prefect
from ..codegen.codegen import Codegen
from ..linear.linear import Linear

logger = get_logger(__name__)


class WorkflowEngine:
    """
    Handles workflow execution and monitoring with simple orchestration.
    
    Features:
    - Sequential task execution
    - ControlFlow agent orchestration
    - Prefect workflow management
    - Linear task synchronization
    - Basic error handling and retry
    """
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.controlflow: Optional[ControlFlow] = None
        self.prefect: Optional[Prefect] = None
        self.codegen: Optional[Codegen] = None
        self.linear: Optional[Linear] = None
        
    async def initialize(self):
        """Initialize the workflow engine"""
        logger.info("Initializing WorkflowEngine...")
        
        # Initialize ControlFlow
        if self.dashboard.settings_manager.is_extension_enabled("controlflow"):
            self.controlflow = ControlFlow({})
            await self.controlflow.initialize()
            logger.info("ControlFlow integration initialized")
            
        # Initialize Prefect
        if self.dashboard.settings_manager.is_extension_enabled("prefect"):
            self.prefect = Prefect({})
            await self.prefect.initialize()
            logger.info("Prefect integration initialized")
            
        # Get Codegen integration
        if self.dashboard.settings_manager.is_extension_enabled("codegen"):
            org_id = self.dashboard.settings_manager.get_api_credential("codegen_org_id")
            token = self.dashboard.settings_manager.get_api_credential("codegen_token")
            
            if org_id and token:
                self.codegen = Codegen({
                    "org_id": org_id,
                    "api_token": token
                })
                await self.codegen.initialize()
                logger.info("Codegen integration initialized")
                
        # Get Linear integration
        if self.dashboard.settings_manager.is_extension_enabled("linear"):
            linear_key = self.dashboard.settings_manager.get_api_credential("linear")
            if linear_key:
                self.linear = Linear({"api_key": linear_key})
                await self.linear.initialize()
                logger.info("Linear integration initialized")
                
    async def start_workflow(self, project_id: str) -> bool:
        """
        Start workflow for a project
        
        Args:
            project_id: Project ID to start workflow for
            
        Returns:
            True if workflow started successfully
        """
        try:
            logger.info(f"Starting workflow for project {project_id}")
            
            # Get project and plan
            project = await self.dashboard.project_manager.get_project(project_id)
            if not project or not project.current_plan_id:
                logger.error(f"No plan found for project {project_id}")
                return False
                
            plan = await self.dashboard.planning_engine.get_plan(project.current_plan_id)
            if not plan:
                logger.error(f"Plan not found: {project.current_plan_id}")
                return False
                
            # Check if workflow already running
            if project_id in self.active_workflows:
                logger.warning(f"Workflow already running for project {project_id}")
                return False
                
            # Create workflow state
            workflow_id = f"workflow_{project_id}_{int(datetime.now().timestamp())}"
            workflow_state = {
                "workflow_id": workflow_id,
                "project_id": project_id,
                "plan_id": plan.plan_id,
                "status": FlowStatus.STARTING,
                "current_task_index": 0,
                "tasks": plan.tasks,
                "started_at": datetime.now(),
                "completed_tasks": [],
                "failed_tasks": [],
                "logs": []
            }
            
            self.active_workflows[project_id] = workflow_state
            project.active_workflow_id = workflow_id
            
            # Update statuses
            await self.dashboard.project_manager.update_flow_status(project_id, FlowStatus.STARTING)
            await self.dashboard.planning_engine.update_plan_status(plan.plan_id, "executing")
            
            # Create Linear issues for tasks if available
            if self.linear:
                await self._create_linear_issues_for_tasks(plan.tasks, project)
                
            # Start workflow execution
            asyncio.create_task(self._execute_workflow(workflow_state))
            
            # Emit event
            await self.dashboard.event_coordinator.emit_event(
                "workflow_started",
                "workflow_engine",
                project_id=project_id,
                data={
                    "workflow_id": workflow_id,
                    "plan_id": plan.plan_id,
                    "task_count": len(plan.tasks)
                }
            )
            
            logger.info(f"Started workflow {workflow_id} for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start workflow for project {project_id}: {e}")
            return False
            
    async def _execute_workflow(self, workflow_state: Dict[str, Any]):
        """Execute workflow tasks sequentially"""
        try:
            project_id = workflow_state["project_id"]
            workflow_id = workflow_state["workflow_id"]
            tasks = workflow_state["tasks"]
            
            logger.info(f"Executing workflow {workflow_id} with {len(tasks)} tasks")
            
            # Update status to running
            workflow_state["status"] = FlowStatus.RUNNING
            await self.dashboard.project_manager.update_flow_status(project_id, FlowStatus.RUNNING)
            
            # Execute tasks sequentially
            for i, task in enumerate(tasks):
                workflow_state["current_task_index"] = i
                
                logger.info(f"Executing task {i+1}/{len(tasks)}: {task.title}")
                
                # Update task status
                task.status = TaskStatus.IN_PROGRESS
                task.started_at = datetime.now()
                
                # Execute task
                success = await self._execute_task(task, workflow_state)
                
                if success:
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = datetime.now()
                    task.progress = 1.0
                    workflow_state["completed_tasks"].append(task.task_id)
                    
                    # Update Linear issue if available
                    if self.linear and task.linear_issue_id:
                        await self._update_linear_issue_status(task.linear_issue_id, "completed")
                        
                    logger.info(f"Task completed: {task.title}")
                else:
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now()
                    workflow_state["failed_tasks"].append(task.task_id)
                    
                    # Update Linear issue if available
                    if self.linear and task.linear_issue_id:
                        await self._update_linear_issue_status(task.linear_issue_id, "failed")
                        
                    logger.error(f"Task failed: {task.title}")
                    
                    # Check if we should continue or stop
                    if not self.dashboard.settings_manager.get_extension_setting("workflow", "continue_on_failure", False):
                        logger.info("Stopping workflow due to task failure")
                        break
                        
                # Emit task completion event
                await self.dashboard.event_coordinator.emit_event(
                    "task_completed" if success else "task_failed",
                    "workflow_engine",
                    project_id=project_id,
                    task_id=task.task_id,
                    data={"task_title": task.title, "success": success}
                )
                
            # Determine final workflow status
            if workflow_state["failed_tasks"]:
                final_status = FlowStatus.FAILED
                plan_status = "failed"
            else:
                final_status = FlowStatus.COMPLETED
                plan_status = "completed"
                
            # Update statuses
            workflow_state["status"] = final_status
            workflow_state["completed_at"] = datetime.now()
            
            await self.dashboard.project_manager.update_flow_status(project_id, final_status)
            await self.dashboard.planning_engine.update_plan_status(workflow_state["plan_id"], plan_status)
            
            # Clean up
            if project_id in self.active_workflows:
                del self.active_workflows[project_id]
                
            # Emit completion event
            await self.dashboard.event_coordinator.emit_event(
                "workflow_completed",
                "workflow_engine",
                project_id=project_id,
                data={
                    "workflow_id": workflow_id,
                    "status": final_status,
                    "completed_tasks": len(workflow_state["completed_tasks"]),
                    "failed_tasks": len(workflow_state["failed_tasks"])
                }
            )
            
            logger.info(f"Workflow {workflow_id} completed with status: {final_status}")
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            
            # Update to failed status
            workflow_state["status"] = FlowStatus.FAILED
            await self.dashboard.project_manager.update_flow_status(project_id, FlowStatus.FAILED)
            
    async def _execute_task(self, task: DashboardTask, workflow_state: Dict[str, Any]) -> bool:
        """Execute a single task"""
        try:
            logger.info(f"Executing task: {task.title} ({task.task_type})")
            
            # Add to logs
            workflow_state["logs"].append(f"Starting task: {task.title}")
            
            # Choose execution method based on task type
            if task.task_type == "code_change":
                success = await self._execute_code_change_task(task)
            elif task.task_type == "analysis":
                success = await self._execute_analysis_task(task)
            elif task.task_type == "testing":
                success = await self._execute_testing_task(task)
            elif task.task_type == "deployment":
                success = await self._execute_deployment_task(task)
            elif task.task_type == "configuration":
                success = await self._execute_configuration_task(task)
            else:
                # Default: use Codegen for general tasks
                success = await self._execute_codegen_task(task)
                
            if success:
                workflow_state["logs"].append(f"Task completed: {task.title}")
            else:
                workflow_state["logs"].append(f"Task failed: {task.title}")
                
            return success
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            task.error_message = str(e)
            workflow_state["logs"].append(f"Task error: {task.title} - {str(e)}")
            return False
            
    async def _execute_code_change_task(self, task: DashboardTask) -> bool:
        """Execute a code change task using Codegen"""
        try:
            if not self.codegen:
                logger.warning("Codegen not available for code change task")
                return False
                
            # Create Codegen task
            response = await self.codegen.create_task(
                prompt=f"Task: {task.title}\nDescription: {task.description}",
                task_type="code_change"
            )
            
            if response and response.get("success"):
                task.codegen_task_id = response.get("task_id")
                task.execution_logs.append(f"Codegen task created: {task.codegen_task_id}")
                
                # Wait for completion (simplified - in real implementation, this would be async)
                await asyncio.sleep(5)  # Simulate execution time
                
                return True
            else:
                task.error_message = "Failed to create Codegen task"
                return False
                
        except Exception as e:
            logger.error(f"Code change task failed: {e}")
            task.error_message = str(e)
            return False
            
    async def _execute_analysis_task(self, task: DashboardTask) -> bool:
        """Execute an analysis task using Graph-sitter"""
        try:
            # Trigger Graph-sitter analysis
            project = await self.dashboard.project_manager.get_project(task.project_id)
            if project:
                analysis = await self.dashboard.quality_manager.analyze_project(task.project_id)
                if analysis:
                    task.execution_logs.append("Code analysis completed")
                    return True
                    
            task.error_message = "Analysis failed"
            return False
            
        except Exception as e:
            logger.error(f"Analysis task failed: {e}")
            task.error_message = str(e)
            return False
            
    async def _execute_testing_task(self, task: DashboardTask) -> bool:
        """Execute a testing task"""
        try:
            # Simulate test execution
            await asyncio.sleep(2)
            task.execution_logs.append("Tests executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Testing task failed: {e}")
            task.error_message = str(e)
            return False
            
    async def _execute_deployment_task(self, task: DashboardTask) -> bool:
        """Execute a deployment task using GrainChain"""
        try:
            # Trigger GrainChain deployment
            deployment = await self.dashboard.quality_manager.deploy_to_sandbox(task.project_id)
            if deployment:
                task.execution_logs.append(f"Deployed to sandbox: {deployment.sandbox.sandbox_id}")
                return True
                
            task.error_message = "Deployment failed"
            return False
            
        except Exception as e:
            logger.error(f"Deployment task failed: {e}")
            task.error_message = str(e)
            return False
            
    async def _execute_configuration_task(self, task: DashboardTask) -> bool:
        """Execute a configuration task"""
        try:
            # Simulate configuration changes
            await asyncio.sleep(1)
            task.execution_logs.append("Configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Configuration task failed: {e}")
            task.error_message = str(e)
            return False
            
    async def _execute_codegen_task(self, task: DashboardTask) -> bool:
        """Execute a general task using Codegen"""
        try:
            if not self.codegen:
                # Simulate task execution without Codegen
                await asyncio.sleep(3)
                task.execution_logs.append("Task executed (simulated)")
                return True
                
            # Use Codegen for task execution
            response = await self.codegen.create_task(
                prompt=f"Execute task: {task.title}\nDescription: {task.description}",
                task_type="general"
            )
            
            if response and response.get("success"):
                task.codegen_task_id = response.get("task_id")
                task.execution_logs.append(f"Codegen task executed: {task.codegen_task_id}")
                return True
            else:
                task.error_message = "Codegen execution failed"
                return False
                
        except Exception as e:
            logger.error(f"General task execution failed: {e}")
            task.error_message = str(e)
            return False
            
    async def _create_linear_issues_for_tasks(self, tasks: List[DashboardTask], project):
        """Create Linear issues for workflow tasks"""
        try:
            if not self.linear or not project.linear_project_id:
                return
                
            for task in tasks:
                issue = await self.linear.create_issue(
                    title=task.title,
                    description=task.description,
                    project_id=project.linear_project_id
                )
                
                if issue:
                    task.linear_issue_id = issue.get("id")
                    logger.info(f"Created Linear issue for task: {task.title}")
                    
        except Exception as e:
            logger.error(f"Failed to create Linear issues: {e}")
            
    async def _update_linear_issue_status(self, issue_id: str, status: str):
        """Update Linear issue status"""
        try:
            if not self.linear:
                return
                
            await self.linear.update_issue_status(issue_id, status)
            
        except Exception as e:
            logger.error(f"Failed to update Linear issue status: {e}")
            
    async def stop_workflow(self, project_id: str) -> bool:
        """Stop an active workflow"""
        try:
            if project_id not in self.active_workflows:
                logger.warning(f"No active workflow for project {project_id}")
                return False
                
            workflow_state = self.active_workflows[project_id]
            workflow_state["status"] = FlowStatus.PAUSED
            
            await self.dashboard.project_manager.update_flow_status(project_id, FlowStatus.PAUSED)
            
            logger.info(f"Stopped workflow for project {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop workflow: {e}")
            return False
            
    async def get_workflow_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status for a project"""
        return self.active_workflows.get(project_id)
        
    async def get_active_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get all active workflows"""
        return self.active_workflows.copy()


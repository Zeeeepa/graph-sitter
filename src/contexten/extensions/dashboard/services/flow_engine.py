"""Flow engine for orchestrating development workflows."""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..models import Flow, Task, FlowStatus, TaskStatus
from .codegen_service import CodegenService


class FlowEngine:
    """Engine for managing and executing development flows."""
    
    def __init__(self):
        """Initialize the flow engine."""
        self._flows: Dict[str, Flow] = {}
        self._running_flows: Dict[str, asyncio.Task] = {}
        self.codegen_service = CodegenService()
    
    async def start_flow(self, project_id: str, requirements: str) -> Flow:
        """Start a new development flow for a project."""
        try:
            # Create new flow
            flow = Flow(
                id=str(uuid.uuid4()),
                project_id=project_id,
                name=f"Development Flow - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                status=FlowStatus.PLANNING,
                created_at=datetime.now()
            )
            
            self._flows[flow.id] = flow
            
            # Start flow execution in background
            execution_task = asyncio.create_task(
                self._execute_flow(flow, requirements)
            )
            self._running_flows[flow.id] = execution_task
            
            return flow
            
        except Exception as e:
            raise Exception(f"Failed to start flow: {str(e)}")
    
    async def get_flow(self, flow_id: str) -> Optional[Flow]:
        """Get a flow by ID."""
        return self._flows.get(flow_id)
    
    async def pause_flow(self, flow_id: str) -> Optional[Flow]:
        """Pause a running flow."""
        flow = self._flows.get(flow_id)
        if not flow:
            return None
        
        if flow.status == FlowStatus.RUNNING:
            flow.status = FlowStatus.PAUSED
            
            # Cancel the running task
            if flow_id in self._running_flows:
                self._running_flows[flow_id].cancel()
                del self._running_flows[flow_id]
        
        return flow
    
    async def resume_flow(self, flow_id: str) -> Optional[Flow]:
        """Resume a paused flow."""
        flow = self._flows.get(flow_id)
        if not flow:
            return None
        
        if flow.status == FlowStatus.PAUSED:
            flow.status = FlowStatus.RUNNING
            
            # Resume execution
            execution_task = asyncio.create_task(
                self._resume_flow_execution(flow)
            )
            self._running_flows[flow_id] = execution_task
        
        return flow
    
    async def stop_flow(self, flow_id: str) -> Optional[Flow]:
        """Stop a running flow."""
        flow = self._flows.get(flow_id)
        if not flow:
            return None
        
        if flow.status in [FlowStatus.RUNNING, FlowStatus.PAUSED]:
            flow.status = FlowStatus.FAILED
            flow.completed_at = datetime.now()
            flow.error_message = "Flow stopped by user"
            
            # Cancel the running task
            if flow_id in self._running_flows:
                self._running_flows[flow_id].cancel()
                del self._running_flows[flow_id]
        
        return flow
    
    async def get_flow_tasks(self, flow_id: str) -> List[Task]:
        """Get all tasks for a flow."""
        flow = self._flows.get(flow_id)
        if not flow:
            return []
        
        return flow.tasks
    
    async def get_active_flows(self) -> List[Flow]:
        """Get all active (running or paused) flows."""
        return [
            flow for flow in self._flows.values()
            if flow.status in [FlowStatus.RUNNING, FlowStatus.PAUSED, FlowStatus.PLANNING]
        ]
    
    async def _execute_flow(self, flow: Flow, requirements: str):
        """Execute a flow from start to finish."""
        try:
            # Phase 1: Planning
            await self._planning_phase(flow, requirements)
            
            # Phase 2: Execution
            await self._execution_phase(flow)
            
            # Phase 3: Completion
            await self._completion_phase(flow)
            
        except asyncio.CancelledError:
            flow.status = FlowStatus.PAUSED
            raise
        except Exception as e:
            flow.status = FlowStatus.FAILED
            flow.error_message = str(e)
            flow.completed_at = datetime.now()
            print(f"Flow {flow.id} failed: {e}")
    
    async def _planning_phase(self, flow: Flow, requirements: str):
        """Planning phase: Generate tasks using Codegen SDK."""
        try:
            flow.status = FlowStatus.PLANNING
            flow.started_at = datetime.now()
            
            # Generate plan using Codegen SDK
            plan = await self.codegen_service.generate_plan(flow.project_id, requirements)
            
            # Convert plan tasks to Flow tasks
            tasks = []
            for i, plan_task in enumerate(plan.get("tasks", [])):
                task = Task(
                    id=str(uuid.uuid4()),
                    flow_id=flow.id,
                    title=plan_task.get("title", f"Task {i+1}"),
                    description=plan_task.get("description", ""),
                    status=TaskStatus.PENDING,
                    dependencies=plan_task.get("dependencies", []),
                    created_at=datetime.now()
                )
                tasks.append(task)
            
            flow.tasks = tasks
            
            # Add quality gate tasks
            quality_gates = plan.get("quality_gates", [])
            for gate in quality_gates:
                quality_task = Task(
                    id=str(uuid.uuid4()),
                    flow_id=flow.id,
                    title=f"Quality Gate: {gate}",
                    description=f"Validate: {gate}",
                    status=TaskStatus.PENDING,
                    dependencies=[task.id for task in tasks],  # Depends on all main tasks
                    created_at=datetime.now()
                )
                flow.tasks.append(quality_task)
            
            print(f"Planning completed for flow {flow.id}: {len(flow.tasks)} tasks created")
            
        except Exception as e:
            raise Exception(f"Planning phase failed: {str(e)}")
    
    async def _execution_phase(self, flow: Flow):
        """Execution phase: Execute tasks in dependency order."""
        try:
            flow.status = FlowStatus.RUNNING
            
            # Execute tasks in dependency order
            completed_tasks = set()
            
            while len(completed_tasks) < len(flow.tasks):
                # Find tasks that can be executed (dependencies met)
                ready_tasks = [
                    task for task in flow.tasks
                    if (task.status == TaskStatus.PENDING and
                        all(dep_id in completed_tasks for dep_id in task.dependencies))
                ]
                
                if not ready_tasks:
                    # Check if we're stuck (no ready tasks but not all completed)
                    pending_tasks = [t for t in flow.tasks if t.status == TaskStatus.PENDING]
                    if pending_tasks:
                        raise Exception("Circular dependency or missing dependency detected")
                    break
                
                # Execute ready tasks (can be done in parallel)
                execution_tasks = []
                for task in ready_tasks:
                    execution_tasks.append(self._execute_task(task))
                
                # Wait for all ready tasks to complete
                results = await asyncio.gather(*execution_tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    task = ready_tasks[i]
                    if isinstance(result, Exception):
                        task.status = TaskStatus.FAILED
                        task.error_message = str(result)
                        task.completed_at = datetime.now()
                        raise Exception(f"Task {task.title} failed: {result}")
                    else:
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                        task.completed_at = datetime.now()
                        completed_tasks.add(task.id)
                        
                        # Generate follow-up tasks if needed
                        followup_tasks = await self._generate_followup_tasks(task, result)
                        if followup_tasks:
                            flow.tasks.extend(followup_tasks)
                
                # Small delay to prevent tight loop
                await asyncio.sleep(1)
            
            print(f"Execution completed for flow {flow.id}")
            
        except Exception as e:
            raise Exception(f"Execution phase failed: {str(e)}")
    
    async def _completion_phase(self, flow: Flow):
        """Completion phase: Finalize flow and cleanup."""
        try:
            # Check if all tasks completed successfully
            failed_tasks = [task for task in flow.tasks if task.status == TaskStatus.FAILED]
            
            if failed_tasks:
                flow.status = FlowStatus.FAILED
                flow.error_message = f"{len(failed_tasks)} tasks failed"
            else:
                flow.status = FlowStatus.COMPLETED
            
            flow.completed_at = datetime.now()
            
            # Cleanup
            if flow.id in self._running_flows:
                del self._running_flows[flow.id]
            
            print(f"Flow {flow.id} completed with status: {flow.status}")
            
        except Exception as e:
            flow.status = FlowStatus.FAILED
            flow.error_message = f"Completion phase failed: {str(e)}"
            flow.completed_at = datetime.now()
    
    async def _execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task."""
        try:
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            
            # Create context for task execution
            context = {
                "flow_id": task.flow_id,
                "task_id": task.id,
                "dependencies": task.dependencies
            }
            
            # Execute task using Codegen service
            result = await self.codegen_service.execute_task(
                task_description=f"{task.title}: {task.description}",
                context=context
            )
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            raise e
    
    async def _generate_followup_tasks(self, completed_task: Task, result: Dict[str, Any]) -> List[Task]:
        """Generate follow-up tasks based on completed task results."""
        try:
            # Use Codegen service to generate follow-up tasks
            followup_suggestions = await self.codegen_service.create_followup_tasks(
                completed_task, result
            )
            
            followup_tasks = []
            for suggestion in followup_suggestions:
                followup_task = Task(
                    id=str(uuid.uuid4()),
                    flow_id=completed_task.flow_id,
                    title=suggestion.get("title", "Follow-up Task"),
                    description=suggestion.get("description", ""),
                    status=TaskStatus.PENDING,
                    dependencies=[completed_task.id],
                    created_at=datetime.now()
                )
                followup_tasks.append(followup_task)
            
            return followup_tasks
            
        except Exception as e:
            print(f"Failed to generate follow-up tasks: {e}")
            return []
    
    async def _resume_flow_execution(self, flow: Flow):
        """Resume execution of a paused flow."""
        try:
            # Find the next tasks to execute
            completed_task_ids = {
                task.id for task in flow.tasks 
                if task.status == TaskStatus.COMPLETED
            }
            
            # Continue with execution phase
            await self._execution_phase(flow)
            
            # Complete the flow
            await self._completion_phase(flow)
            
        except asyncio.CancelledError:
            flow.status = FlowStatus.PAUSED
            raise
        except Exception as e:
            flow.status = FlowStatus.FAILED
            flow.error_message = str(e)
            flow.completed_at = datetime.now()
    
    async def get_flow_statistics(self) -> Dict[str, Any]:
        """Get flow execution statistics."""
        all_flows = list(self._flows.values())
        
        # Count flows by status
        status_counts = {}
        for status in FlowStatus:
            status_counts[status.value] = len([
                f for f in all_flows if f.status == status
            ])
        
        # Calculate average execution time for completed flows
        completed_flows = [f for f in all_flows if f.status == FlowStatus.COMPLETED]
        avg_execution_time = 0
        if completed_flows:
            total_time = sum([
                (f.completed_at - f.started_at).total_seconds()
                for f in completed_flows
                if f.started_at and f.completed_at
            ])
            avg_execution_time = total_time / len(completed_flows)
        
        return {
            "total_flows": len(all_flows),
            "active_flows": len(self._running_flows),
            "status_breakdown": status_counts,
            "average_execution_time_seconds": avg_execution_time,
            "success_rate": len(completed_flows) / len(all_flows) if all_flows else 0
        }


"""
Enhanced Flow Scheduler

Provides intelligent scheduling capabilities with:
- Priority-based scheduling
- Resource-aware scheduling
- Dependency management
- Load balancing
- Scheduling optimization
"""

from typing import Dict, List, Any, Optional, Set, Tuple
import asyncio
import logging
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import heapq

from .strands import StrandAgent, StrandWorkflow

logger = logging.getLogger(__name__)


class SchedulingStrategy(Enum):
    """Scheduling strategy options."""
    FIFO = "fifo"  # First In, First Out
    PRIORITY = "priority"  # Priority-based
    RESOURCE_AWARE = "resource_aware"  # Consider resource availability
    LOAD_BALANCED = "load_balanced"  # Balance load across agents
    DEADLINE_AWARE = "deadline_aware"  # Consider deadlines


@dataclass
class ScheduledFlow:
    """Represents a scheduled flow with metadata."""
    flow_id: str
    workflow: StrandWorkflow
    workflow_def: Dict[str, Any]
    priority: int = 1
    scheduled_time: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    required_agents: List[str] = field(default_factory=list)
    estimated_duration: Optional[timedelta] = None
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    
    def __lt__(self, other):
        """Comparison for priority queue (higher priority = lower number)."""
        return self.priority < other.priority


class ResourceTracker:
    """Tracks resource usage and availability."""
    
    def __init__(self):
        self.agent_usage = {}  # agent_id -> current_load
        self.agent_capacity = {}  # agent_id -> max_capacity
        self.total_capacity = 0
        self.current_load = 0
        
    def register_agent(self, agent_id: str, capacity: int = 1):
        """Register an agent with its capacity."""
        self.agent_usage[agent_id] = 0
        self.agent_capacity[agent_id] = capacity
        self.total_capacity += capacity
        
    def allocate_resources(self, agent_id: str, load: int = 1) -> bool:
        """Attempt to allocate resources for an agent."""
        if agent_id not in self.agent_usage:
            return False
            
        if self.agent_usage[agent_id] + load <= self.agent_capacity[agent_id]:
            self.agent_usage[agent_id] += load
            self.current_load += load
            return True
        return False
        
    def release_resources(self, agent_id: str, load: int = 1):
        """Release resources for an agent."""
        if agent_id in self.agent_usage:
            self.agent_usage[agent_id] = max(0, self.agent_usage[agent_id] - load)
            self.current_load = max(0, self.current_load - load)
            
    def get_available_capacity(self, agent_id: str) -> int:
        """Get available capacity for an agent."""
        if agent_id not in self.agent_usage:
            return 0
        return self.agent_capacity[agent_id] - self.agent_usage[agent_id]
        
    def get_system_load(self) -> float:
        """Get overall system load percentage."""
        if self.total_capacity == 0:
            return 0.0
        return (self.current_load / self.total_capacity) * 100
        
    def get_least_loaded_agent(self) -> Optional[str]:
        """Get the agent with the least load."""
        if not self.agent_usage:
            return None
            
        min_load_ratio = float('inf')
        best_agent = None
        
        for agent_id in self.agent_usage:
            capacity = self.agent_capacity[agent_id]
            if capacity > 0:
                load_ratio = self.agent_usage[agent_id] / capacity
                if load_ratio < min_load_ratio:
                    min_load_ratio = load_ratio
                    best_agent = agent_id
                    
        return best_agent


class DependencyGraph:
    """Manages flow dependencies."""
    
    def __init__(self):
        self.dependencies = {}  # flow_id -> set of dependency flow_ids
        self.dependents = {}    # flow_id -> set of dependent flow_ids
        self.completed = set()  # completed flow_ids
        
    def add_dependency(self, flow_id: str, dependency_id: str):
        """Add a dependency relationship."""
        if flow_id not in self.dependencies:
            self.dependencies[flow_id] = set()
        if dependency_id not in self.dependents:
            self.dependents[dependency_id] = set()
            
        self.dependencies[flow_id].add(dependency_id)
        self.dependents[dependency_id].add(flow_id)
        
    def mark_completed(self, flow_id: str):
        """Mark a flow as completed."""
        self.completed.add(flow_id)
        
    def get_ready_flows(self, flow_ids: List[str]) -> List[str]:
        """Get flows that are ready to execute (all dependencies completed)."""
        ready = []
        for flow_id in flow_ids:
            dependencies = self.dependencies.get(flow_id, set())
            if dependencies.issubset(self.completed):
                ready.append(flow_id)
        return ready
        
    def has_circular_dependency(self, flow_id: str, visited: Optional[Set[str]] = None) -> bool:
        """Check for circular dependencies."""
        if visited is None:
            visited = set()
            
        if flow_id in visited:
            return True
            
        visited.add(flow_id)
        
        for dependency in self.dependencies.get(flow_id, set()):
            if self.has_circular_dependency(dependency, visited.copy()):
                return True
                
        return False


class FlowScheduler:
    """
    Enhanced flow scheduler with intelligent scheduling capabilities.
    
    Features:
    - Multiple scheduling strategies
    - Resource-aware scheduling
    - Dependency management
    - Load balancing
    - Deadline awareness
    - Performance optimization
    """
    
    def __init__(
        self,
        agents: Optional[List[StrandAgent]] = None,
        strategy: SchedulingStrategy = SchedulingStrategy.PRIORITY,
        max_concurrent_flows: int = 10,
        enable_load_balancing: bool = True,
        **kwargs
    ):
        """
        Initialize the flow scheduler.
        
        Args:
            agents: Available agents
            strategy: Scheduling strategy
            max_concurrent_flows: Maximum concurrent flows
            enable_load_balancing: Whether to enable load balancing
            **kwargs: Additional configuration
        """
        self.agents = agents or []
        self.strategy = strategy
        self.max_concurrent_flows = max_concurrent_flows
        self.enable_load_balancing = enable_load_balancing
        
        # Scheduling queues
        self.pending_flows = []  # Priority queue of ScheduledFlow objects
        self.running_flows = {}  # flow_id -> ScheduledFlow
        self.completed_flows = []  # History of completed flows
        
        # Resource management
        self.resource_tracker = ResourceTracker()
        for i, agent in enumerate(self.agents):
            self.resource_tracker.register_agent(f"agent_{i}", capacity=1)
            
        # Dependency management
        self.dependency_graph = DependencyGraph()
        
        # Scheduling metrics
        self.metrics = {
            "total_scheduled": 0,
            "total_completed": 0,
            "total_failed": 0,
            "average_wait_time": 0.0,
            "average_execution_time": 0.0,
            "current_queue_size": 0
        }
        
        # Background scheduler task
        self._scheduler_task = None
        self._running = False
        
    async def start(self):
        """Start the scheduler."""
        if not self._running:
            self._running = True
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())
            logger.info(f"Flow scheduler started with strategy: {self.strategy.value}")
            
    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Flow scheduler stopped")
        
    async def schedule_flow(
        self,
        workflow: StrandWorkflow,
        workflow_def: Dict[str, Any],
        priority: int = 1,
        deadline: Optional[datetime] = None,
        dependencies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Schedule a flow for execution.
        
        Args:
            workflow: Workflow to schedule
            workflow_def: Workflow definition
            priority: Execution priority (lower = higher priority)
            deadline: Optional deadline
            dependencies: Optional list of dependency flow IDs
            
        Returns:
            Dict containing scheduling result
        """
        flow_id = workflow_def.get("id", f"flow_{datetime.now().isoformat()}")
        
        try:
            # Validate dependencies
            if dependencies:
                for dep_id in dependencies:
                    if self.dependency_graph.has_circular_dependency(dep_id):
                        return {
                            "status": "failed",
                            "error": f"Circular dependency detected with {dep_id}",
                            "flow_id": flow_id
                        }
                    self.dependency_graph.add_dependency(flow_id, dep_id)
                    
            # Estimate duration
            estimated_duration = self._estimate_flow_duration(workflow_def)
            
            # Create scheduled flow
            scheduled_flow = ScheduledFlow(
                flow_id=flow_id,
                workflow=workflow,
                workflow_def=workflow_def,
                priority=priority,
                deadline=deadline,
                estimated_duration=estimated_duration,
                dependencies=dependencies or []
            )
            
            # Add to pending queue
            heapq.heappush(self.pending_flows, scheduled_flow)
            
            # Update metrics
            self.metrics["total_scheduled"] += 1
            self.metrics["current_queue_size"] = len(self.pending_flows)
            
            logger.info(f"Scheduled flow {flow_id} with priority {priority}")
            
            return {
                "status": "success",
                "flow_id": flow_id,
                "priority": priority,
                "estimated_duration": estimated_duration.total_seconds() if estimated_duration else None,
                "queue_position": len(self.pending_flows)
            }
            
        except Exception as e:
            logger.error(f"Failed to schedule flow {flow_id}: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "flow_id": flow_id
            }
            
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._schedule_next_flows()
                await asyncio.sleep(0.1)  # Brief pause between scheduling cycles
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(1)
                
    async def _schedule_next_flows(self):
        """Schedule next available flows based on strategy."""
        if not self.pending_flows:
            return
            
        # Check if we can schedule more flows
        if len(self.running_flows) >= self.max_concurrent_flows:
            return
            
        # Get flows ready for execution (dependencies satisfied)
        ready_flow_ids = self.dependency_graph.get_ready_flows(
            [flow.flow_id for flow in self.pending_flows]
        )
        
        # Select flows to schedule based on strategy
        flows_to_schedule = self._select_flows_for_scheduling(ready_flow_ids)
        
        # Schedule selected flows
        for flow in flows_to_schedule:
            if len(self.running_flows) >= self.max_concurrent_flows:
                break
                
            # Remove from pending queue
            self.pending_flows.remove(flow)
            heapq.heapify(self.pending_flows)  # Re-heapify after removal
            
            # Start execution
            await self._start_flow_execution(flow)
            
        # Update metrics
        self.metrics["current_queue_size"] = len(self.pending_flows)
        
    def _select_flows_for_scheduling(self, ready_flow_ids: List[str]) -> List[ScheduledFlow]:
        """Select flows for scheduling based on current strategy."""
        ready_flows = [
            flow for flow in self.pending_flows 
            if flow.flow_id in ready_flow_ids
        ]
        
        if not ready_flows:
            return []
            
        if self.strategy == SchedulingStrategy.FIFO:
            return sorted(ready_flows, key=lambda f: f.scheduled_time)[:self.max_concurrent_flows - len(self.running_flows)]
            
        elif self.strategy == SchedulingStrategy.PRIORITY:
            return sorted(ready_flows, key=lambda f: f.priority)[:self.max_concurrent_flows - len(self.running_flows)]
            
        elif self.strategy == SchedulingStrategy.DEADLINE_AWARE:
            # Sort by deadline, then priority
            now = datetime.now()
            return sorted(
                ready_flows,
                key=lambda f: (
                    f.deadline if f.deadline else now + timedelta(days=365),
                    f.priority
                )
            )[:self.max_concurrent_flows - len(self.running_flows)]
            
        elif self.strategy == SchedulingStrategy.RESOURCE_AWARE:
            return self._select_resource_aware_flows(ready_flows)
            
        elif self.strategy == SchedulingStrategy.LOAD_BALANCED:
            return self._select_load_balanced_flows(ready_flows)
            
        else:
            return ready_flows[:self.max_concurrent_flows - len(self.running_flows)]
            
    def _select_resource_aware_flows(self, ready_flows: List[ScheduledFlow]) -> List[ScheduledFlow]:
        """Select flows based on resource availability."""
        selected = []
        available_slots = self.max_concurrent_flows - len(self.running_flows)
        
        # Sort by priority first
        sorted_flows = sorted(ready_flows, key=lambda f: f.priority)
        
        for flow in sorted_flows:
            if len(selected) >= available_slots:
                break
                
            # Check if we have resources for this flow
            required_agents = self._get_required_agents(flow.workflow_def)
            if self._can_allocate_resources(required_agents):
                selected.append(flow)
                
        return selected
        
    def _select_load_balanced_flows(self, ready_flows: List[ScheduledFlow]) -> List[ScheduledFlow]:
        """Select flows to balance load across agents."""
        selected = []
        available_slots = self.max_concurrent_flows - len(self.running_flows)
        
        # Sort by priority
        sorted_flows = sorted(ready_flows, key=lambda f: f.priority)
        
        for flow in sorted_flows:
            if len(selected) >= available_slots:
                break
                
            # Select flow if it helps balance load
            if self._improves_load_balance(flow):
                selected.append(flow)
                
        return selected
        
    async def _start_flow_execution(self, scheduled_flow: ScheduledFlow):
        """Start execution of a scheduled flow."""
        flow_id = scheduled_flow.flow_id
        
        try:
            # Allocate resources
            required_agents = self._get_required_agents(scheduled_flow.workflow_def)
            allocated_agents = self._allocate_flow_resources(required_agents)
            
            # Add to running flows
            self.running_flows[flow_id] = scheduled_flow
            
            # Start execution task
            execution_task = asyncio.create_task(
                self._execute_flow_with_monitoring(scheduled_flow, allocated_agents)
            )
            
            # Store task reference for cleanup
            scheduled_flow.execution_task = execution_task
            
            logger.info(f"Started execution of flow {flow_id}")
            
        except Exception as e:
            logger.error(f"Failed to start flow {flow_id}: {e}")
            # Return flow to pending queue
            heapq.heappush(self.pending_flows, scheduled_flow)
            
    async def _execute_flow_with_monitoring(
        self,
        scheduled_flow: ScheduledFlow,
        allocated_agents: List[str]
    ):
        """Execute flow with monitoring and cleanup."""
        flow_id = scheduled_flow.flow_id
        start_time = datetime.now()
        
        try:
            # Execute the workflow
            result = await scheduled_flow.workflow.execute(scheduled_flow.workflow_def)
            
            # Mark as completed
            self.dependency_graph.mark_completed(flow_id)
            
            # Update metrics
            execution_time = (datetime.now() - start_time).total_seconds()
            self._update_completion_metrics(execution_time, True)
            
            logger.info(f"Flow {flow_id} completed successfully in {execution_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Flow {flow_id} failed: {e}")
            
            # Handle retry logic
            if scheduled_flow.retry_count < scheduled_flow.max_retries:
                scheduled_flow.retry_count += 1
                logger.info(f"Retrying flow {flow_id} (attempt {scheduled_flow.retry_count})")
                
                # Re-queue for retry
                heapq.heappush(self.pending_flows, scheduled_flow)
            else:
                # Mark as failed
                execution_time = (datetime.now() - start_time).total_seconds()
                self._update_completion_metrics(execution_time, False)
                
        finally:
            # Cleanup resources
            self._release_flow_resources(allocated_agents)
            
            # Remove from running flows
            if flow_id in self.running_flows:
                completed_flow = self.running_flows.pop(flow_id)
                self.completed_flows.append(completed_flow)
                
    def _estimate_flow_duration(self, workflow_def: Dict[str, Any]) -> Optional[timedelta]:
        """Estimate flow execution duration."""
        # Simple estimation based on number of stages and tasks
        stages = workflow_def.get("stages", [])
        total_tasks = sum(len(stage.get("tasks", [])) for stage in stages)
        
        # Base estimation: 30 seconds per task
        estimated_seconds = total_tasks * 30
        
        # Adjust based on complexity
        complexity = workflow_def.get("complexity", 1)
        estimated_seconds *= complexity
        
        return timedelta(seconds=estimated_seconds)
        
    def _get_required_agents(self, workflow_def: Dict[str, Any]) -> List[str]:
        """Get list of required agent types for a workflow."""
        required_agents = []
        stages = workflow_def.get("stages", [])
        
        for stage in stages:
            for task in stage.get("tasks", []):
                required_tools = task.get("required_tools", [])
                # Map tools to agent types (simplified)
                if required_tools:
                    required_agents.append("general_agent")
                    
        return required_agents or ["general_agent"]
        
    def _can_allocate_resources(self, required_agents: List[str]) -> bool:
        """Check if resources can be allocated for required agents."""
        # Simplified check - just verify we have available capacity
        return self.resource_tracker.get_system_load() < 80  # 80% threshold
        
    def _allocate_flow_resources(self, required_agents: List[str]) -> List[str]:
        """Allocate resources for a flow."""
        allocated = []
        for agent_type in required_agents:
            # Find least loaded agent
            agent_id = self.resource_tracker.get_least_loaded_agent()
            if agent_id and self.resource_tracker.allocate_resources(agent_id):
                allocated.append(agent_id)
        return allocated
        
    def _release_flow_resources(self, allocated_agents: List[str]):
        """Release resources for a flow."""
        for agent_id in allocated_agents:
            self.resource_tracker.release_resources(agent_id)
            
    def _improves_load_balance(self, flow: ScheduledFlow) -> bool:
        """Check if scheduling this flow improves load balance."""
        # Simplified check - schedule if system load is reasonable
        return self.resource_tracker.get_system_load() < 70  # 70% threshold
        
    def _update_completion_metrics(self, execution_time: float, success: bool):
        """Update completion metrics."""
        if success:
            self.metrics["total_completed"] += 1
        else:
            self.metrics["total_failed"] += 1
            
        # Update average execution time
        total_completed = self.metrics["total_completed"] + self.metrics["total_failed"]
        current_avg = self.metrics["average_execution_time"]
        self.metrics["average_execution_time"] = (
            (current_avg * (total_completed - 1) + execution_time) / total_completed
        )
        
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status and metrics."""
        return {
            "strategy": self.strategy.value,
            "running": self._running,
            "pending_flows": len(self.pending_flows),
            "running_flows": len(self.running_flows),
            "completed_flows": len(self.completed_flows),
            "system_load": self.resource_tracker.get_system_load(),
            "metrics": self.metrics.copy()
        }


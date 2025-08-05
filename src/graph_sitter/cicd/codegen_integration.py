"""
Codegen SDK Integration for Graph-Sitter CI/CD

Provides comprehensive integration with Codegen SDK:
- Agent management and configuration
- Task execution and monitoring
- Cost tracking and optimization
- Performance analytics
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Codegen agent types"""
    GENERAL = "general"
    REVIEWER = "reviewer"
    TESTER = "tester"
    DEPLOYER = "deployer"
    ANALYZER = "analyzer"
    OPTIMIZER = "optimizer"


class AgentTaskStatus(Enum):
    """Agent task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class CodegenAgent:
    """Codegen agent configuration and capabilities"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str = ""
    name: str = ""
    description: str = ""
    agent_type: AgentType = AgentType.GENERAL
    configuration: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    is_active: bool = True
    
    # Usage tracking
    last_used_at: Optional[datetime] = None
    usage_stats: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def add_capability(self, capability: str) -> None:
        """Add a capability to the agent"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)
    
    def remove_capability(self, capability: str) -> None:
        """Remove a capability from the agent"""
        if capability in self.capabilities:
            self.capabilities.remove(capability)
    
    def has_capability(self, capability: str) -> bool:
        """Check if agent has a specific capability"""
        return capability in self.capabilities
    
    def update_usage_stats(self, execution_time: float, tokens_used: int, cost: float) -> None:
        """Update agent usage statistics"""
        self.last_used_at = datetime.now(timezone.utc)
        
        if "total_executions" not in self.usage_stats:
            self.usage_stats["total_executions"] = 0
        if "total_execution_time" not in self.usage_stats:
            self.usage_stats["total_execution_time"] = 0.0
        if "total_tokens_used" not in self.usage_stats:
            self.usage_stats["total_tokens_used"] = 0
        if "total_cost" not in self.usage_stats:
            self.usage_stats["total_cost"] = 0.0
        
        self.usage_stats["total_executions"] += 1
        self.usage_stats["total_execution_time"] += execution_time
        self.usage_stats["total_tokens_used"] += tokens_used
        self.usage_stats["total_cost"] += cost
        
        # Calculate averages
        executions = self.usage_stats["total_executions"]
        self.usage_stats["avg_execution_time"] = self.usage_stats["total_execution_time"] / executions
        self.usage_stats["avg_tokens_per_execution"] = self.usage_stats["total_tokens_used"] / executions
        self.usage_stats["avg_cost_per_execution"] = self.usage_stats["total_cost"] / executions


@dataclass
class AgentTask:
    """Codegen agent task execution"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    task_id: Optional[str] = None
    codegen_task_id: Optional[str] = None
    
    # Task definition
    prompt: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 3  # 1=highest, 5=lowest
    
    # Execution tracking
    status: AgentTaskStatus = AgentTaskStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    result: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    
    # Metrics
    tokens_used: int = 0
    cost_estimate: float = 0.0
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def start_execution(self) -> None:
        """Mark task execution as started"""
        self.status = AgentTaskStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)
    
    def complete_execution(self, result: Dict[str, Any], tokens_used: int = 0, cost: float = 0.0) -> None:
        """Mark task execution as completed"""
        self.status = AgentTaskStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.result = result
        self.tokens_used = tokens_used
        self.cost_estimate = cost
    
    def fail_execution(self, error_message: str) -> None:
        """Mark task execution as failed"""
        self.status = AgentTaskStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error_message
    
    def get_execution_time(self) -> Optional[float]:
        """Get execution time in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class CodegenClient:
    """
    Comprehensive Codegen SDK client with:
    - Agent management and task execution
    - Performance monitoring and optimization
    - Cost tracking and budget management
    - Integration with CI/CD pipelines
    """
    
    def __init__(self, organization_id: str, org_id: str, token: str, database_connection=None):
        self.organization_id = organization_id
        self.org_id = org_id
        self.token = token
        self.db = database_connection
        
        # In-memory storage (would be replaced with database in production)
        self.agents: Dict[str, CodegenAgent] = {}
        self.agent_tasks: Dict[str, AgentTask] = {}
        
        # Configuration
        self.default_timeout = 300  # 5 minutes
        self.max_retries = 3
        self.cost_budget_limit = 1000.0  # Daily budget limit
        self.current_daily_cost = 0.0
        
        # Performance tracking
        self.performance_metrics: Dict[str, Any] = {
            "total_tasks_executed": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "avg_execution_time": 0.0
        }
    
    async def create_agent(self, agent: CodegenAgent) -> str:
        """Create a new Codegen agent"""
        agent.organization_id = self.organization_id
        self.agents[agent.id] = agent
        
        # Store in database if available
        if self.db:
            await self._store_agent_in_db(agent)
        
        logger.info(f"Created Codegen agent {agent.id}: {agent.name}")
        return agent.id
    
    async def get_agent(self, agent_id: str) -> Optional[CodegenAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    async def list_agents(self, agent_type: Optional[AgentType] = None, active_only: bool = True) -> List[CodegenAgent]:
        """List agents with optional filters"""
        agents = list(self.agents.values())
        
        if active_only:
            agents = [a for a in agents if a.is_active]
        if agent_type:
            agents = [a for a in agents if a.agent_type == agent_type]
        
        return agents
    
    async def execute_agent_task(self, agent_id: str, prompt: str, context: Dict[str, Any] = None, priority: int = 3) -> AgentTask:
        """Execute a task using a Codegen agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        if not agent.is_active:
            raise ValueError(f"Agent {agent_id} is not active")
        
        # Check budget limit
        if self.current_daily_cost >= self.cost_budget_limit:
            raise ValueError("Daily cost budget limit exceeded")
        
        # Create agent task
        agent_task = AgentTask(
            agent_id=agent_id,
            prompt=prompt,
            context=context or {},
            priority=priority
        )
        self.agent_tasks[agent_task.id] = agent_task
        
        # Start execution
        agent_task.start_execution()
        logger.info(f"Starting agent task {agent_task.id} for agent {agent_id}")
        
        try:
            # Execute task with Codegen SDK
            result = await self._execute_codegen_task(agent, agent_task)
            
            # Complete task
            tokens_used = result.get("tokens_used", 0)
            cost = result.get("cost", 0.0)
            agent_task.complete_execution(result, tokens_used, cost)
            
            # Update agent usage stats
            execution_time = agent_task.get_execution_time() or 0.0
            agent.update_usage_stats(execution_time, tokens_used, cost)
            
            # Update global metrics
            self._update_performance_metrics(agent_task, True)
            
            logger.info(f"Completed agent task {agent_task.id}")
            
        except Exception as e:
            agent_task.fail_execution(str(e))
            self._update_performance_metrics(agent_task, False)
            logger.error(f"Failed to execute agent task {agent_task.id}: {e}")
            
        finally:
            # Store task in database
            if self.db:
                await self._store_agent_task_in_db(agent_task)
        
        return agent_task
    
    async def execute_batch_tasks(self, tasks: List[Dict[str, Any]], max_concurrent: int = 5) -> List[AgentTask]:
        """Execute multiple tasks concurrently"""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def execute_single_task(task_data: Dict[str, Any]) -> AgentTask:
            async with semaphore:
                return await self.execute_agent_task(
                    agent_id=task_data["agent_id"],
                    prompt=task_data["prompt"],
                    context=task_data.get("context", {}),
                    priority=task_data.get("priority", 3)
                )
        
        # Execute tasks concurrently
        task_coroutines = [execute_single_task(task_data) for task_data in tasks]
        results = await asyncio.gather(*task_coroutines, return_exceptions=True)
        
        # Filter out exceptions and return successful tasks
        successful_tasks = [r for r in results if isinstance(r, AgentTask)]
        return successful_tasks
    
    async def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for an agent"""
        agent = self.agents.get(agent_id)
        if not agent:
            return {}
        
        # Get agent tasks
        agent_tasks = [t for t in self.agent_tasks.values() if t.agent_id == agent_id]
        
        if not agent_tasks:
            return {"agent_id": agent_id, "task_count": 0}
        
        # Calculate metrics
        total_tasks = len(agent_tasks)
        successful_tasks = len([t for t in agent_tasks if t.status == AgentTaskStatus.COMPLETED])
        failed_tasks = len([t for t in agent_tasks if t.status == AgentTaskStatus.FAILED])
        
        # Calculate average execution time
        completed_tasks = [t for t in agent_tasks if t.get_execution_time() is not None]
        avg_execution_time = 0.0
        if completed_tasks:
            total_time = sum(t.get_execution_time() for t in completed_tasks)
            avg_execution_time = total_time / len(completed_tasks)
        
        # Calculate cost metrics
        total_cost = sum(t.cost_estimate for t in agent_tasks)
        total_tokens = sum(t.tokens_used for t in agent_tasks)
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "task_count": total_tasks,
            "success_rate": successful_tasks / total_tasks if total_tasks > 0 else 0,
            "failure_rate": failed_tasks / total_tasks if total_tasks > 0 else 0,
            "avg_execution_time_seconds": avg_execution_time,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "avg_cost_per_task": total_cost / total_tasks if total_tasks > 0 else 0,
            "avg_tokens_per_task": total_tokens / total_tasks if total_tasks > 0 else 0,
            "last_used": agent.last_used_at.isoformat() if agent.last_used_at else None
        }
    
    async def get_cost_analysis(self, time_period_days: int = 30) -> Dict[str, Any]:
        """Get cost analysis for the specified time period"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=time_period_days)
        recent_tasks = [
            t for t in self.agent_tasks.values() 
            if t.created_at >= cutoff_date
        ]
        
        if not recent_tasks:
            return {"period_days": time_period_days, "total_cost": 0.0, "task_count": 0}
        
        # Calculate cost metrics
        total_cost = sum(t.cost_estimate for t in recent_tasks)
        total_tokens = sum(t.tokens_used for t in recent_tasks)
        
        # Group by agent
        agent_costs = {}
        for task in recent_tasks:
            agent_id = task.agent_id
            if agent_id not in agent_costs:
                agent_costs[agent_id] = {"cost": 0.0, "tokens": 0, "tasks": 0}
            agent_costs[agent_id]["cost"] += task.cost_estimate
            agent_costs[agent_id]["tokens"] += task.tokens_used
            agent_costs[agent_id]["tasks"] += 1
        
        # Group by day
        daily_costs = {}
        for task in recent_tasks:
            day = task.created_at.date().isoformat()
            if day not in daily_costs:
                daily_costs[day] = 0.0
            daily_costs[day] += task.cost_estimate
        
        return {
            "period_days": time_period_days,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "task_count": len(recent_tasks),
            "avg_cost_per_task": total_cost / len(recent_tasks),
            "avg_tokens_per_task": total_tokens / len(recent_tasks),
            "agent_breakdown": agent_costs,
            "daily_costs": daily_costs,
            "budget_utilization": (self.current_daily_cost / self.cost_budget_limit) * 100
        }
    
    async def optimize_agent_allocation(self) -> Dict[str, Any]:
        """Analyze and suggest agent allocation optimizations"""
        agents = list(self.agents.values())
        if not agents:
            return {"recommendations": []}
        
        recommendations = []
        
        # Analyze agent performance
        for agent in agents:
            performance = await self.get_agent_performance(agent.id)
            
            # Check for underutilized agents
            if performance["task_count"] == 0:
                recommendations.append({
                    "type": "underutilized",
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "message": "Agent has no task executions",
                    "suggestion": "Consider deactivating or reassigning capabilities"
                })
            
            # Check for high failure rates
            elif performance["failure_rate"] > 0.2:  # 20% failure rate
                recommendations.append({
                    "type": "high_failure_rate",
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "failure_rate": performance["failure_rate"],
                    "message": f"High failure rate: {performance['failure_rate']:.1%}",
                    "suggestion": "Review agent configuration and capabilities"
                })
            
            # Check for high costs
            elif performance["avg_cost_per_task"] > 10.0:  # $10 per task
                recommendations.append({
                    "type": "high_cost",
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "avg_cost": performance["avg_cost_per_task"],
                    "message": f"High average cost per task: ${performance['avg_cost_per_task']:.2f}",
                    "suggestion": "Consider optimizing prompts or using different model"
                })
        
        return {
            "recommendations": recommendations,
            "total_agents": len(agents),
            "active_agents": len([a for a in agents if a.is_active]),
            "analysis_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _execute_codegen_task(self, agent: CodegenAgent, agent_task: AgentTask) -> Dict[str, Any]:
        """Execute task using Codegen SDK (mock implementation)"""
        # In real implementation, this would use the actual Codegen SDK
        await asyncio.sleep(0.5)  # Simulate API call
        
        # Mock response based on agent capabilities
        if agent.has_capability("code_generation"):
            result = {
                "status": "completed",
                "generated_code": "# Generated code would be here",
                "explanation": "Code generated successfully",
                "tokens_used": 150,
                "cost": 0.05
            }
        elif agent.has_capability("code_analysis"):
            result = {
                "status": "completed",
                "analysis_results": {
                    "complexity_score": 7.5,
                    "issues_found": 2,
                    "suggestions": ["Improve error handling", "Add unit tests"]
                },
                "tokens_used": 100,
                "cost": 0.03
            }
        else:
            result = {
                "status": "completed",
                "message": "Task completed successfully",
                "tokens_used": 75,
                "cost": 0.02
            }
        
        # Update daily cost tracking
        self.current_daily_cost += result.get("cost", 0.0)
        
        return result
    
    def _update_performance_metrics(self, agent_task: AgentTask, success: bool) -> None:
        """Update global performance metrics"""
        self.performance_metrics["total_tasks_executed"] += 1
        
        if success:
            self.performance_metrics["successful_tasks"] += 1
        else:
            self.performance_metrics["failed_tasks"] += 1
        
        self.performance_metrics["total_cost"] += agent_task.cost_estimate
        self.performance_metrics["total_tokens"] += agent_task.tokens_used
        
        # Update average execution time
        execution_time = agent_task.get_execution_time()
        if execution_time:
            total_tasks = self.performance_metrics["total_tasks_executed"]
            current_avg = self.performance_metrics["avg_execution_time"]
            self.performance_metrics["avg_execution_time"] = (
                (current_avg * (total_tasks - 1) + execution_time) / total_tasks
            )
    
    async def _store_agent_in_db(self, agent: CodegenAgent) -> None:
        """Store agent in database"""
        # Implementation would depend on database connection
        pass
    
    async def _store_agent_task_in_db(self, agent_task: AgentTask) -> None:
        """Store agent task in database"""
        # Implementation would depend on database connection
        pass


# Utility functions
def create_agent_from_dict(data: Dict[str, Any]) -> CodegenAgent:
    """Create a CodegenAgent object from dictionary data"""
    agent = CodegenAgent()
    for key, value in data.items():
        if key == "agent_type" and isinstance(value, str):
            agent.agent_type = AgentType(value)
        elif hasattr(agent, key):
            setattr(agent, key, value)
    return agent


from datetime import timedelta


"""
Enhanced Orchestrator - Core orchestration engine integrating SDK-Python and Strands-Agents
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

from .memory import MemoryManager
from .events import EventEvaluator
from .cicd import AutonomousCICD
from .integrations.sdk_python import SDKPythonIntegration
from .integrations.strands_agents import StrandsAgentsIntegration


@dataclass
class OrchestratorConfig:
    """Configuration for the Enhanced Orchestrator"""
    
    # Memory configuration
    memory_backend: str = "persistent"
    memory_retention_days: int = 30
    memory_optimization_enabled: bool = True
    
    # Event evaluation configuration
    event_monitoring_enabled: bool = True
    event_classification_threshold: float = 0.8
    real_time_processing: bool = True
    
    # CI/CD configuration
    autonomous_cicd_enabled: bool = True
    pipeline_auto_healing: bool = True
    continuous_optimization: bool = True
    
    # Integration configuration
    sdk_python_enabled: bool = True
    strands_agents_enabled: bool = True
    
    # Processing configuration
    max_parallel_tasks: int = 10
    task_timeout_seconds: int = 300
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


class EnhancedOrchestrator:
    """
    Enhanced Orchestrator with SDK-Python and Strands-Agents Integration
    
    Provides comprehensive orchestration capabilities including:
    - Model-driven agent building via SDK-Python
    - Advanced tool integration via Strands-Agents
    - Extended memory management
    - System-level event evaluation
    - Autonomous CI/CD capabilities
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        """Initialize the Enhanced Orchestrator"""
        self.config = config or OrchestratorConfig()
        self._setup_logging()
        
        # Initialize core components
        self.memory_manager = MemoryManager(
            backend=self.config.memory_backend,
            retention_days=self.config.memory_retention_days,
            optimization_enabled=self.config.memory_optimization_enabled
        )
        
        self.event_evaluator = EventEvaluator(
            monitoring_enabled=self.config.event_monitoring_enabled,
            classification_threshold=self.config.event_classification_threshold,
            real_time_processing=self.config.real_time_processing
        )
        
        self.autonomous_cicd = AutonomousCICD(
            enabled=self.config.autonomous_cicd_enabled,
            auto_healing=self.config.pipeline_auto_healing,
            continuous_optimization=self.config.continuous_optimization
        )
        
        # Initialize integrations
        self.sdk_python = None
        self.strands_agents = None
        
        if self.config.sdk_python_enabled:
            self.sdk_python = SDKPythonIntegration()
            
        if self.config.strands_agents_enabled:
            self.strands_agents = StrandsAgentsIntegration()
        
        # Task management
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._task_results: Dict[str, Any] = {}
        
        self.logger.info("Enhanced Orchestrator initialized successfully")
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level),
            format=self.config.log_format
        )
        self.logger = logging.getLogger(__name__)
    
    async def start(self):
        """Start the orchestrator and all its components"""
        self.logger.info("Starting Enhanced Orchestrator...")
        
        # Start core components
        await self.memory_manager.start()
        await self.event_evaluator.start()
        await self.autonomous_cicd.start()
        
        # Start integrations
        if self.sdk_python:
            await self.sdk_python.start()
            
        if self.strands_agents:
            await self.strands_agents.start()
        
        self.logger.info("Enhanced Orchestrator started successfully")
    
    async def stop(self):
        """Stop the orchestrator and cleanup resources"""
        self.logger.info("Stopping Enhanced Orchestrator...")
        
        # Cancel active tasks
        for task_id, task in self._active_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Stop components
        if self.strands_agents:
            await self.strands_agents.stop()
            
        if self.sdk_python:
            await self.sdk_python.stop()
            
        await self.autonomous_cicd.stop()
        await self.event_evaluator.stop()
        await self.memory_manager.stop()
        
        self.logger.info("Enhanced Orchestrator stopped successfully")
    
    async def create_agent(
        self,
        agent_config: Dict[str, Any],
        tools: Optional[List[str]] = None,
        memory_context: Optional[str] = None
    ) -> str:
        """
        Create a new agent using SDK-Python integration
        
        Args:
            agent_config: Configuration for the agent
            tools: List of tools to enable for the agent
            memory_context: Memory context identifier
            
        Returns:
            Agent ID
        """
        if not self.sdk_python:
            raise RuntimeError("SDK-Python integration not enabled")
        
        # Store agent context in memory
        if memory_context:
            await self.memory_manager.store_context(
                context_id=memory_context,
                data=agent_config,
                metadata={"type": "agent_config", "timestamp": datetime.now().isoformat()}
            )
        
        # Create agent via SDK-Python
        agent_id = await self.sdk_python.create_agent(agent_config, tools)
        
        self.logger.info(f"Created agent {agent_id} with tools: {tools}")
        return agent_id
    
    async def execute_task(
        self,
        task_id: str,
        task_config: Dict[str, Any],
        agent_id: Optional[str] = None,
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a task using the orchestrator
        
        Args:
            task_id: Unique task identifier
            task_config: Task configuration
            agent_id: Agent to use for execution
            use_memory: Whether to use memory for context
            
        Returns:
            Task execution result
        """
        self.logger.info(f"Executing task {task_id}")
        
        # Retrieve memory context if enabled
        context = {}
        if use_memory:
            context = await self.memory_manager.retrieve_context(
                context_id=task_id,
                relevance_threshold=0.7
            )
        
        # Create execution task
        execution_task = asyncio.create_task(
            self._execute_task_internal(task_id, task_config, agent_id, context)
        )
        
        self._active_tasks[task_id] = execution_task
        
        try:
            result = await asyncio.wait_for(
                execution_task,
                timeout=self.config.task_timeout_seconds
            )
            
            # Store result in memory
            if use_memory:
                await self.memory_manager.store_context(
                    context_id=f"{task_id}_result",
                    data=result,
                    metadata={"type": "task_result", "task_id": task_id}
                )
            
            self._task_results[task_id] = result
            return result
            
        except asyncio.TimeoutError:
            self.logger.error(f"Task {task_id} timed out")
            execution_task.cancel()
            raise
        
        finally:
            self._active_tasks.pop(task_id, None)
    
    async def _execute_task_internal(
        self,
        task_id: str,
        task_config: Dict[str, Any],
        agent_id: Optional[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Internal task execution logic"""
        
        # Evaluate task as system event
        event_data = {
            "type": "task_execution",
            "task_id": task_id,
            "config": task_config,
            "context": context
        }
        
        await self.event_evaluator.evaluate_event(event_data)
        
        # Execute based on available integrations
        if agent_id and self.sdk_python:
            # Use SDK-Python agent
            result = await self.sdk_python.execute_with_agent(
                agent_id, task_config, context
            )
        elif self.strands_agents:
            # Use Strands-Agents tools
            result = await self.strands_agents.execute_task(
                task_config, context
            )
        else:
            # Fallback execution
            result = await self._fallback_execution(task_config, context)
        
        return {
            "task_id": task_id,
            "status": "completed",
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "context_used": bool(context)
        }
    
    async def _fallback_execution(
        self,
        task_config: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fallback execution when integrations are not available"""
        self.logger.warning("Using fallback execution - integrations not available")
        
        return {
            "message": "Task executed with fallback method",
            "config": task_config,
            "context_keys": list(context.keys()) if context else []
        }
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a task"""
        if task_id in self._active_tasks:
            task = self._active_tasks[task_id]
            return {
                "task_id": task_id,
                "status": "running" if not task.done() else "completed",
                "done": task.done()
            }
        elif task_id in self._task_results:
            return {
                "task_id": task_id,
                "status": "completed",
                "result": self._task_results[task_id]
            }
        else:
            return {
                "task_id": task_id,
                "status": "not_found"
            }
    
    async def list_active_tasks(self) -> List[str]:
        """List all active task IDs"""
        return list(self._active_tasks.keys())
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory management statistics"""
        return await self.memory_manager.get_stats()
    
    async def get_event_stats(self) -> Dict[str, Any]:
        """Get event evaluation statistics"""
        return await self.event_evaluator.get_stats()
    
    async def get_cicd_status(self) -> Dict[str, Any]:
        """Get CI/CD system status"""
        return await self.autonomous_cicd.get_status()
    
    async def optimize_system(self) -> Dict[str, Any]:
        """Trigger system optimization"""
        self.logger.info("Starting system optimization...")
        
        optimization_results = {}
        
        # Optimize memory
        memory_optimization = await self.memory_manager.optimize()
        optimization_results["memory"] = memory_optimization
        
        # Optimize CI/CD
        if self.autonomous_cicd:
            cicd_optimization = await self.autonomous_cicd.optimize()
            optimization_results["cicd"] = cicd_optimization
        
        # Optimize integrations
        if self.sdk_python:
            sdk_optimization = await self.sdk_python.optimize()
            optimization_results["sdk_python"] = sdk_optimization
            
        if self.strands_agents:
            strands_optimization = await self.strands_agents.optimize()
            optimization_results["strands_agents"] = strands_optimization
        
        self.logger.info("System optimization completed")
        return optimization_results
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        return {
            "orchestrator": "healthy",
            "memory_manager": self.memory_manager.is_healthy(),
            "event_evaluator": self.event_evaluator.is_healthy(),
            "autonomous_cicd": self.autonomous_cicd.is_healthy(),
            "sdk_python": self.sdk_python.is_healthy() if self.sdk_python else "disabled",
            "strands_agents": self.strands_agents.is_healthy() if self.strands_agents else "disabled",
            "active_tasks": len(self._active_tasks),
            "timestamp": datetime.now().isoformat()
        }


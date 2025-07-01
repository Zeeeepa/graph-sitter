"""
Contexten Core Orchestrator

Main orchestrator with Codegen SDK integration and system-watcher capabilities.
This module serves as the central coordination point for all CI/CD operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import os
from pathlib import Path

# Import Codegen SDK integration
from ..codegen.autogenlib import (
    CodegenClient, TaskManager, BatchProcessor,
    TaskConfig, WorkflowDefinition, BatchConfig
)

# Import existing codebase analysis
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)

# Import platform integrations
from .extensions.github.enhanced_integration import GitHubIntegration
from .extensions.linear.enhanced_automation import LinearIntegration  
from .extensions.slack.enhanced_communication import SlackIntegration

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """System status enumeration."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class SystemConfig:
    """Configuration for the Contexten system."""
    # Codegen SDK configuration
    codegen_org_id: str
    codegen_token: str
    codegen_base_url: Optional[str] = None
    
    # System settings
    max_concurrent_tasks: int = 10
    health_check_interval: int = 30
    log_level: str = "INFO"
    
    # Platform integrations
    github_enabled: bool = True
    linear_enabled: bool = True
    slack_enabled: bool = True
    
    # Database configuration
    database_url: Optional[str] = None
    
    # Learning system
    learning_enabled: bool = True
    pattern_recognition_enabled: bool = True
    
    # Monitoring
    metrics_enabled: bool = True
    performance_tracking: bool = True


@dataclass
class SystemMetrics:
    """System performance and health metrics."""
    uptime_seconds: float = 0
    total_tasks_processed: int = 0
    active_tasks: int = 0
    failed_tasks: int = 0
    success_rate: float = 0.0
    average_task_duration: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


class ContextenOrchestrator:
    """
    Main orchestrator for the Contexten CI/CD system.
    
    This class coordinates all system components including:
    - Codegen SDK integration
    - Platform integrations (GitHub, Linear, Slack)
    - Task management and workflow orchestration
    - System monitoring and health checks
    - Continuous learning and adaptation
    """
    
    def __init__(self, config: SystemConfig):
        """
        Initialize the Contexten orchestrator.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.status = SystemStatus.INITIALIZING
        self.start_time = datetime.now()
        self.metrics = SystemMetrics()
        
        # Core components
        self.codegen_client: Optional[CodegenClient] = None
        self.task_manager: Optional[TaskManager] = None
        self.batch_processor: Optional[BatchProcessor] = None
        
        # Platform integrations
        self.github_integration: Optional[GitHubIntegration] = None
        self.linear_integration: Optional[LinearIntegration] = None
        self.slack_integration: Optional[SlackIntegration] = None
        
        # System state
        self.active_workflows: Dict[str, Any] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.health_check_task: Optional[asyncio.Task] = None
        self.shutdown_event = asyncio.Event()
        
        # Setup logging
        logging.basicConfig(level=getattr(logging, config.log_level))
        logger.info("Contexten Orchestrator initialized")
    
    async def start(self):
        """Start the orchestrator and all subsystems."""
        try:
            logger.info("Starting Contexten Orchestrator...")
            self.status = SystemStatus.INITIALIZING
            
            # Initialize Codegen SDK
            await self._initialize_codegen_sdk()
            
            # Initialize platform integrations
            await self._initialize_platform_integrations()
            
            # Start system monitoring
            await self._start_monitoring()
            
            # Start task manager
            if self.task_manager:
                await self.task_manager.start()
            
            self.status = SystemStatus.ACTIVE
            logger.info("Contexten Orchestrator started successfully")
            
            # Emit startup event
            await self._emit_event("system_started", {"timestamp": datetime.now()})
            
        except Exception as e:
            self.status = SystemStatus.ERROR
            logger.error(f"Failed to start Contexten Orchestrator: {e}")
            raise
    
    async def stop(self):
        """Stop the orchestrator and all subsystems."""
        logger.info("Stopping Contexten Orchestrator...")
        self.status = SystemStatus.SHUTDOWN
        self.shutdown_event.set()
        
        # Stop monitoring
        if self.health_check_task:
            self.health_check_task.cancel()
        
        # Stop task manager
        if self.task_manager:
            await self.task_manager.stop()
        
        # Close platform integrations
        if self.github_integration:
            await self.github_integration.close()
        if self.linear_integration:
            await self.linear_integration.close()
        if self.slack_integration:
            await self.slack_integration.close()
        
        # Close Codegen client
        if self.codegen_client:
            await self.codegen_client.__aexit__(None, None, None)
        
        logger.info("Contexten Orchestrator stopped")
    
    async def _initialize_codegen_sdk(self):
        """Initialize the Codegen SDK components."""
        logger.info("Initializing Codegen SDK...")
        
        # Create Codegen client
        self.codegen_client = CodegenClient(
            org_id=self.config.codegen_org_id,
            token=self.config.codegen_token,
            base_url=self.config.codegen_base_url
        )
        
        # Initialize client session
        await self.codegen_client.__aenter__()
        
        # Create task manager
        self.task_manager = TaskManager(
            codegen_client=self.codegen_client,
            max_concurrent_tasks=self.config.max_concurrent_tasks
        )
        
        # Create batch processor
        self.batch_processor = BatchProcessor(self.codegen_client)
        
        # Setup task event handlers
        self.task_manager.add_event_handler('task_completed', self._on_task_completed)
        self.task_manager.add_event_handler('task_failed', self._on_task_failed)
        
        logger.info("Codegen SDK initialized successfully")
    
    async def _initialize_platform_integrations(self):
        """Initialize platform integrations."""
        logger.info("Initializing platform integrations...")
        
        # Initialize GitHub integration
        if self.config.github_enabled:
            try:
                self.github_integration = GitHubIntegration(self)
                await self.github_integration.initialize()
                logger.info("GitHub integration initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize GitHub integration: {e}")
        
        # Initialize Linear integration
        if self.config.linear_enabled:
            try:
                self.linear_integration = LinearIntegration(self)
                await self.linear_integration.initialize()
                logger.info("Linear integration initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Linear integration: {e}")
        
        # Initialize Slack integration
        if self.config.slack_enabled:
            try:
                self.slack_integration = SlackIntegration(self)
                await self.slack_integration.initialize()
                logger.info("Slack integration initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Slack integration: {e}")
    
    async def _start_monitoring(self):
        """Start system monitoring and health checks."""
        if self.config.metrics_enabled:
            self.health_check_task = asyncio.create_task(self._health_check_loop())
            logger.info("System monitoring started")
    
    async def _health_check_loop(self):
        """Continuous health check loop."""
        while not self.shutdown_event.is_set():
            try:
                await self._update_metrics()
                await self._check_system_health()
                await asyncio.sleep(self.config.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(5)
    
    async def _update_metrics(self):
        """Update system metrics."""
        current_time = datetime.now()
        self.metrics.uptime_seconds = (current_time - self.start_time).total_seconds()
        self.metrics.last_updated = current_time
        
        # Update task metrics
        if self.task_manager:
            status_summary = self.task_manager.get_status_summary()
            self.metrics.active_tasks = status_summary.get("running_tasks", 0)
            self.metrics.total_tasks_processed = status_summary.get("total_tasks", 0)
        
        # Update performance metrics
        if self.batch_processor:
            perf_metrics = self.batch_processor.get_performance_metrics()
            self.metrics.success_rate = perf_metrics.get("success_rate", 0.0)
            self.metrics.average_task_duration = perf_metrics.get("average_batch_duration", 0.0)
        
        # System resource metrics (simplified)
        import psutil
        process = psutil.Process()
        self.metrics.memory_usage_mb = process.memory_info().rss / 1024 / 1024
        self.metrics.cpu_usage_percent = process.cpu_percent()
    
    async def _check_system_health(self):
        """Check system health and update status."""
        try:
            # Check if critical components are responsive
            if self.codegen_client:
                client_info = self.codegen_client.get_client_info()
                if not client_info:
                    self.status = SystemStatus.DEGRADED
                    return
            
            # Check resource usage
            if self.metrics.memory_usage_mb > 1000:  # 1GB threshold
                logger.warning(f"High memory usage: {self.metrics.memory_usage_mb:.1f}MB")
            
            if self.metrics.cpu_usage_percent > 80:
                logger.warning(f"High CPU usage: {self.metrics.cpu_usage_percent:.1f}%")
            
            # Check error rates
            if self.metrics.success_rate < 0.8:  # 80% threshold
                logger.warning(f"Low success rate: {self.metrics.success_rate:.1%}")
                self.status = SystemStatus.DEGRADED
            else:
                self.status = SystemStatus.ACTIVE
                
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            self.status = SystemStatus.ERROR
    
    async def execute_codebase_analysis(self, 
                                      repository_url: str,
                                      analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """
        Execute codebase analysis using integrated tools.
        
        Args:
            repository_url: URL of repository to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis results
        """
        logger.info(f"Starting {analysis_type} analysis of {repository_url}")
        
        try:
            # Create analysis task
            task_config = TaskConfig(
                prompt=f"Perform {analysis_type} analysis of repository {repository_url}",
                context={
                    "repository_url": repository_url,
                    "analysis_type": analysis_type,
                    "use_existing_functions": True,
                    "functions_available": [
                        "get_codebase_summary",
                        "get_file_summary",
                        "get_class_summary", 
                        "get_function_summary",
                        "get_symbol_summary"
                    ]
                },
                priority=5
            )
            
            # Execute task
            if self.codegen_client:
                result = await self.codegen_client.run_task(task_config)
                
                # Enhance with local analysis if available
                enhanced_result = await self._enhance_with_local_analysis(result, repository_url)
                
                return {
                    "status": "completed",
                    "repository_url": repository_url,
                    "analysis_type": analysis_type,
                    "result": enhanced_result,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise Exception("Codegen client not initialized")
                
        except Exception as e:
            logger.error(f"Analysis failed for {repository_url}: {e}")
            return {
                "status": "failed",
                "repository_url": repository_url,
                "analysis_type": analysis_type,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _enhance_with_local_analysis(self, 
                                         codegen_result: Any,
                                         repository_url: str) -> Dict[str, Any]:
        """Enhance Codegen results with local codebase analysis."""
        enhanced = {
            "codegen_result": codegen_result.result if hasattr(codegen_result, 'result') else codegen_result,
            "local_analysis": {}
        }
        
        try:
            # This would integrate with actual codebase analysis
            # For now, we'll add placeholder analysis
            enhanced["local_analysis"] = {
                "analysis_available": True,
                "functions_used": [
                    "get_codebase_summary",
                    "get_file_summary",
                    "get_class_summary",
                    "get_function_summary", 
                    "get_symbol_summary"
                ],
                "repository_url": repository_url,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.warning(f"Could not enhance with local analysis: {e}")
            enhanced["local_analysis"] = {"error": str(e)}
        
        return enhanced
    
    async def create_workflow(self, workflow_def: WorkflowDefinition) -> List[str]:
        """Create and execute a workflow."""
        if not self.task_manager:
            raise Exception("Task manager not initialized")
        
        logger.info(f"Creating workflow: {workflow_def.name}")
        task_ids = self.task_manager.add_workflow(workflow_def)
        
        self.active_workflows[workflow_def.id] = {
            "definition": workflow_def,
            "task_ids": task_ids,
            "created_at": datetime.now(),
            "status": "active"
        }
        
        await self._emit_event("workflow_created", {
            "workflow_id": workflow_def.id,
            "task_count": len(task_ids)
        })
        
        return task_ids
    
    async def _on_task_completed(self, task):
        """Handle task completion events."""
        self.metrics.total_tasks_processed += 1
        await self._emit_event("task_completed", {"task_id": task.id})
        
        # Check if this completes any workflows
        await self._check_workflow_completion(task)
    
    async def _on_task_failed(self, task):
        """Handle task failure events."""
        self.metrics.failed_tasks += 1
        await self._emit_event("task_failed", {
            "task_id": task.id,
            "error": task.error_history[-1] if task.error_history else "Unknown error"
        })
    
    async def _check_workflow_completion(self, completed_task):
        """Check if any workflows are completed."""
        for workflow_id, workflow_info in self.active_workflows.items():
            if completed_task.id in workflow_info["task_ids"]:
                # Check if all tasks in workflow are completed
                all_completed = True
                for task_id in workflow_info["task_ids"]:
                    task = self.task_manager.get_task(task_id)
                    if not task or task.status.value != "completed":
                        all_completed = False
                        break
                
                if all_completed:
                    workflow_info["status"] = "completed"
                    workflow_info["completed_at"] = datetime.now()
                    await self._emit_event("workflow_completed", {"workflow_id": workflow_id})
    
    async def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """Emit system events to registered handlers."""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, data)
                else:
                    handler(event_type, data)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
    
    def add_event_handler(self, event_type: str, handler: Callable):
        """Add an event handler for system events."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "status": self.status.value,
            "uptime_seconds": self.metrics.uptime_seconds,
            "metrics": {
                "total_tasks_processed": self.metrics.total_tasks_processed,
                "active_tasks": self.metrics.active_tasks,
                "failed_tasks": self.metrics.failed_tasks,
                "success_rate": self.metrics.success_rate,
                "memory_usage_mb": self.metrics.memory_usage_mb,
                "cpu_usage_percent": self.metrics.cpu_usage_percent
            },
            "components": {
                "codegen_client": bool(self.codegen_client),
                "task_manager": bool(self.task_manager),
                "batch_processor": bool(self.batch_processor),
                "github_integration": bool(self.github_integration),
                "linear_integration": bool(self.linear_integration),
                "slack_integration": bool(self.slack_integration)
            },
            "active_workflows": len(self.active_workflows),
            "last_updated": self.metrics.last_updated.isoformat()
        }


# Factory function for easy initialization
def create_orchestrator(config_dict: Dict[str, Any]) -> ContextenOrchestrator:
    """
    Create a Contexten orchestrator from configuration dictionary.
    
    Args:
        config_dict: Configuration parameters
        
    Returns:
        Configured ContextenOrchestrator instance
    """
    config = SystemConfig(**config_dict)
    return ContextenOrchestrator(config)


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the Contexten orchestrator."""
        config = SystemConfig(
            codegen_org_id="example-org",
            codegen_token="example-token",
            max_concurrent_tasks=5,
            github_enabled=True,
            linear_enabled=True,
            slack_enabled=True
        )
        
        orchestrator = ContextenOrchestrator(config)
        
        try:
            # Start the orchestrator
            await orchestrator.start()
            
            # Execute a codebase analysis
            result = await orchestrator.execute_codebase_analysis(
                "https://github.com/example/repo",
                "comprehensive"
            )
            print(f"Analysis result: {result}")
            
            # Get system status
            status = orchestrator.get_system_status()
            print(f"System status: {status}")
            
            # Wait a bit
            await asyncio.sleep(10)
            
        finally:
            # Stop the orchestrator
            await orchestrator.stop()
    
    asyncio.run(example_usage())


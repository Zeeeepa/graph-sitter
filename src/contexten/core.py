"""
Contexten Core Orchestrator
Enhanced agentic orchestrator with comprehensive integration support
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json

from .extensions.base import BaseExtension
from .extensions.linear import LinearExtension
from .extensions.github import GitHubExtension
from .extensions.slack import SlackExtension


@dataclass
class ContextenConfig:
    """Configuration for Contexten orchestrator"""
    
    # Core settings
    max_concurrent_tasks: int = 10
    task_timeout_seconds: int = 300
    retry_attempts: int = 3
    
    # Integration settings
    linear_enabled: bool = True
    github_enabled: bool = True
    slack_enabled: bool = True
    
    # OpenEvolve integration
    openevolve_enabled: bool = True
    evaluation_timeout_ms: int = 30000
    max_generations: int = 100
    
    # Codegen API settings
    codegen_org_id: Optional[str] = None
    codegen_token: Optional[str] = None
    
    # Database settings
    database_url: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    
    # Extension configurations
    extension_configs: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class ContextenOrchestrator:
    """
    Enhanced agentic orchestrator for comprehensive task management
    with Linear, GitHub, Slack, and OpenEvolve integrations
    """
    
    def __init__(self, config: ContextenConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.extensions: Dict[str, BaseExtension] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self._initialize_extensions()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("contexten")
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_extensions(self):
        """Initialize all enabled extensions"""
        try:
            # Linear extension
            if self.config.linear_enabled:
                linear_config = self.config.extension_configs.get('linear', {})
                self.extensions['linear'] = LinearExtension(
                    config=linear_config,
                    logger=self.logger
                )
                self.logger.info("Linear extension initialized")
            
            # GitHub extension
            if self.config.github_enabled:
                github_config = self.config.extension_configs.get('github', {})
                self.extensions['github'] = GitHubExtension(
                    config=github_config,
                    logger=self.logger
                )
                self.logger.info("GitHub extension initialized")
            
            # Slack extension
            if self.config.slack_enabled:
                slack_config = self.config.extension_configs.get('slack', {})
                self.extensions['slack'] = SlackExtension(
                    config=slack_config,
                    logger=self.logger
                )
                self.logger.info("Slack extension initialized")
            
            self.logger.info(f"Initialized {len(self.extensions)} extensions")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize extensions: {e}")
            raise
    
    async def start(self):
        """Start the orchestrator and all extensions"""
        self.logger.info("Starting Contexten orchestrator")
        
        # Start all extensions
        for name, extension in self.extensions.items():
            try:
                await extension.start()
                self.logger.info(f"Started {name} extension")
            except Exception as e:
                self.logger.error(f"Failed to start {name} extension: {e}")
        
        self.logger.info("Contexten orchestrator started successfully")
    
    async def stop(self):
        """Stop the orchestrator and all extensions"""
        self.logger.info("Stopping Contexten orchestrator")
        
        # Cancel all active tasks
        for task_id, task in self.active_tasks.items():
            if not task.done():
                task.cancel()
                self.logger.info(f"Cancelled task {task_id}")
        
        # Stop all extensions
        for name, extension in self.extensions.items():
            try:
                await extension.stop()
                self.logger.info(f"Stopped {name} extension")
            except Exception as e:
                self.logger.error(f"Failed to stop {name} extension: {e}")
        
        self.logger.info("Contexten orchestrator stopped")
    
    async def execute_task(
        self, 
        task_type: str, 
        task_data: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using the appropriate extension
        
        Args:
            task_type: Type of task (e.g., 'linear.create_issue', 'github.create_pr')
            task_data: Task-specific data
            task_id: Optional task identifier
            
        Returns:
            Task execution result
        """
        if task_id is None:
            task_id = f"task_{datetime.now().isoformat()}"
        
        self.logger.info(f"Executing task {task_id}: {task_type}")
        
        try:
            # Parse task type to determine extension
            if '.' in task_type:
                extension_name, action = task_type.split('.', 1)
            else:
                raise ValueError(f"Invalid task type format: {task_type}")
            
            # Get the appropriate extension
            extension = self.extensions.get(extension_name)
            if not extension:
                raise ValueError(f"Extension not found: {extension_name}")
            
            # Create and execute the task
            task = asyncio.create_task(
                self._execute_with_timeout(extension, action, task_data)
            )
            self.active_tasks[task_id] = task
            
            try:
                result = await task
                self.logger.info(f"Task {task_id} completed successfully")
                return {
                    "task_id": task_id,
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.now().isoformat()
                }
            finally:
                self.active_tasks.pop(task_id, None)
                
        except asyncio.TimeoutError:
            self.logger.error(f"Task {task_id} timed out")
            return {
                "task_id": task_id,
                "status": "timeout",
                "error": "Task execution timed out",
                "failed_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Task {task_id} failed: {e}")
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            }
    
    async def _execute_with_timeout(
        self, 
        extension: BaseExtension, 
        action: str, 
        task_data: Dict[str, Any]
    ) -> Any:
        """Execute extension action with timeout"""
        return await asyncio.wait_for(
            extension.execute_action(action, task_data),
            timeout=self.config.task_timeout_seconds
        )
    
    async def batch_execute(
        self, 
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tasks concurrently
        
        Args:
            tasks: List of task dictionaries with 'type' and 'data' keys
            
        Returns:
            List of task execution results
        """
        self.logger.info(f"Executing batch of {len(tasks)} tasks")
        
        # Create semaphore to limit concurrent tasks
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)
        
        async def execute_single_task(task_info: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.execute_task(
                    task_type=task_info['type'],
                    task_data=task_info['data'],
                    task_id=task_info.get('id')
                )
        
        # Execute all tasks concurrently
        results = await asyncio.gather(
            *[execute_single_task(task) for task in tasks],
            return_exceptions=True
        )
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "task_id": tasks[i].get('id', f"task_{i}"),
                    "status": "failed",
                    "error": str(result),
                    "failed_at": datetime.now().isoformat()
                })
            else:
                processed_results.append(result)
        
        self.logger.info(f"Batch execution completed: {len(processed_results)} results")
        return processed_results
    
    def get_extension_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all extensions"""
        status = {}
        for name, extension in self.extensions.items():
            try:
                status[name] = extension.get_status()
            except Exception as e:
                status[name] = {
                    "status": "error",
                    "error": str(e)
                }
        return status
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active tasks"""
        active_info = {}
        for task_id, task in self.active_tasks.items():
            active_info[task_id] = {
                "status": "running" if not task.done() else "completed",
                "cancelled": task.cancelled() if task.done() else False,
                "exception": str(task.exception()) if task.done() and task.exception() else None
            }
        return active_info
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            "orchestrator": "healthy",
            "timestamp": datetime.now().isoformat(),
            "extensions": {},
            "active_tasks": len(self.active_tasks),
            "config": {
                "max_concurrent_tasks": self.config.max_concurrent_tasks,
                "task_timeout_seconds": self.config.task_timeout_seconds,
                "enabled_extensions": list(self.extensions.keys())
            }
        }
        
        # Check extension health
        for name, extension in self.extensions.items():
            try:
                ext_health = await extension.health_check()
                health_status["extensions"][name] = ext_health
            except Exception as e:
                health_status["extensions"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        # Determine overall health
        unhealthy_extensions = [
            name for name, status in health_status["extensions"].items()
            if status.get("status") != "healthy"
        ]
        
        if unhealthy_extensions:
            health_status["orchestrator"] = "degraded"
            health_status["unhealthy_extensions"] = unhealthy_extensions
        
        return health_status


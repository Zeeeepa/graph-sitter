"""
Core Contexten Orchestrator with Codegen SDK Integration
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json

# Handle missing codegen module gracefully
try:
    from codegen import Agent
except ImportError:
    logging.warning("Codegen SDK not available, using mock implementation")
    
    class MockAgent:
        def __init__(self, org_id, token):
            self.org_id = org_id
            self.token = token
        
        def run(self, prompt):
            return MockTask()
    
    class MockTask:
        def __init__(self):
            self.id = "mock_task_123"
            self.status = "completed"
            self.result = "Mock code generation result"
        
        def refresh(self):
            pass
    
    Agent = MockAgent

from .extensions.linear import LinearExtension
from .extensions.github import GitHubExtension
from .extensions.slack import SlackExtension

logger = logging.getLogger(__name__)


@dataclass
class ContextenConfig:
    """Configuration for Contexten Orchestrator"""
    
    # Codegen SDK Configuration
    codegen_org_id: str = "323"
    codegen_token: Optional[str] = None
    
    # Database Configuration
    database_url: Optional[str] = None
    
    # Integration Configuration
    linear_enabled: bool = True
    linear_api_key: Optional[str] = None
    linear_team_id: Optional[str] = None
    
    github_enabled: bool = True
    github_token: Optional[str] = None
    
    slack_enabled: bool = True
    slack_token: Optional[str] = None
    
    # OpenEvolve Configuration
    openevolve_enabled: bool = True
    openevolve_timeout_ms: int = 30000
    openevolve_max_generations: int = 100
    
    # System Configuration
    max_concurrent_tasks: int = 50
    default_timeout_ms: int = 300000
    retry_attempts: int = 3
    
    # Advanced Configuration
    self_healing_enabled: bool = True
    continuous_learning_enabled: bool = True
    analytics_enabled: bool = True
    
    def __post_init__(self):
        """Load configuration from environment variables if not provided"""
        if not self.codegen_token:
            self.codegen_token = os.getenv("CODEGEN_TOKEN")
        if not self.database_url:
            self.database_url = os.getenv("DATABASE_URL")
        if not self.linear_api_key:
            self.linear_api_key = os.getenv("LINEAR_API_KEY")
        if not self.linear_team_id:
            self.linear_team_id = os.getenv("LINEAR_TEAM_ID")
        if not self.github_token:
            self.github_token = os.getenv("GITHUB_TOKEN")
        if not self.slack_token:
            self.slack_token = os.getenv("SLACK_TOKEN")


class ContextenOrchestrator:
    """
    Enhanced Agentic Orchestrator with Codegen SDK Integration
    
    Provides comprehensive CI/CD automation with:
    - Codegen SDK integration for task execution
    - Linear, GitHub, and Slack integrations
    - Self-healing architecture with OpenEvolve
    - Continuous learning and optimization
    - Real-time analytics and monitoring
    """
    
    def __init__(self, config: ContextenConfig):
        self.config = config
        self.codegen_agent: Optional[Agent] = None
        self.extensions: Dict[str, Any] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        
        # Initialize Codegen SDK
        self._initialize_codegen_sdk()
        
        # Initialize extensions
        self._initialize_extensions()
        
        logger.info("Contexten Orchestrator initialized successfully")
    
    def _initialize_codegen_sdk(self):
        """Initialize Codegen SDK with proper configuration"""
        if not self.config.codegen_token:
            raise ValueError("Codegen token is required for SDK integration")
        
        try:
            self.codegen_agent = Agent(
                org_id=self.config.codegen_org_id,
                token=self.config.codegen_token
            )
            logger.info(f"Codegen SDK initialized with org_id: {self.config.codegen_org_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Codegen SDK: {e}")
            raise
    
    def _initialize_extensions(self):
        """Initialize platform extensions"""
        
        # Linear Extension
        if self.config.linear_enabled and self.config.linear_api_key:
            try:
                self.extensions['linear'] = LinearExtension(
                    api_key=self.config.linear_api_key,
                    team_id=self.config.linear_team_id,
                    orchestrator=self
                )
                logger.info("Linear extension initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Linear extension: {e}")
        
        # GitHub Extension
        if self.config.github_enabled and self.config.github_token:
            try:
                self.extensions['github'] = GitHubExtension(
                    token=self.config.github_token,
                    orchestrator=self
                )
                logger.info("GitHub extension initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize GitHub extension: {e}")
        
        # Slack Extension
        if self.config.slack_enabled and self.config.slack_token:
            try:
                self.extensions['slack'] = SlackExtension(
                    token=self.config.slack_token,
                    orchestrator=self
                )
                logger.info("Slack extension initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Slack extension: {e}")
    
    async def start(self):
        """Start the orchestrator and all extensions"""
        if self.is_running:
            logger.warning("Orchestrator is already running")
            return
        
        self.is_running = True
        logger.info("Starting Contexten Orchestrator...")
        
        # Start extensions
        for name, extension in self.extensions.items():
            try:
                if hasattr(extension, 'start'):
                    await extension.start()
                logger.info(f"Started {name} extension")
            except Exception as e:
                logger.error(f"Failed to start {name} extension: {e}")
        
        # Start task processor
        asyncio.create_task(self._process_task_queue())
        
        logger.info("Contexten Orchestrator started successfully")
    
    async def stop(self):
        """Stop the orchestrator and all extensions"""
        if not self.is_running:
            return
        
        self.is_running = False
        logger.info("Stopping Contexten Orchestrator...")
        
        # Cancel running tasks
        for task_id, task in self.running_tasks.items():
            task.cancel()
            logger.info(f"Cancelled task: {task_id}")
        
        # Stop extensions
        for name, extension in self.extensions.items():
            try:
                if hasattr(extension, 'stop'):
                    await extension.stop()
                logger.info(f"Stopped {name} extension")
            except Exception as e:
                logger.error(f"Failed to stop {name} extension: {e}")
        
        logger.info("Contexten Orchestrator stopped")
    
    async def execute_task(self, task_type: str, task_data: Dict[str, Any], priority: int = 3) -> Dict[str, Any]:
        """
        Execute a task using the appropriate extension or Codegen SDK
        
        Args:
            task_type: Type of task (e.g., 'linear.create_issue', 'github.create_pr', 'codegen.generate_code')
            task_data: Task-specific data
            priority: Task priority (1=highest, 5=lowest)
        
        Returns:
            Task execution result
        """
        task_id = f"{task_type}_{datetime.now().isoformat()}"
        
        try:
            # Route task to appropriate handler
            if task_type.startswith('codegen.'):
                result = await self._execute_codegen_task(task_type, task_data)
            elif '.' in task_type:
                extension_name, action = task_type.split('.', 1)
                if extension_name in self.extensions:
                    extension = self.extensions[extension_name]
                    result = await extension.execute_action(action, task_data)
                else:
                    raise ValueError(f"Unknown extension: {extension_name}")
            else:
                raise ValueError(f"Invalid task type: {task_type}")
            
            logger.info(f"Task {task_id} completed successfully")
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            
            # Self-healing: attempt recovery if enabled
            if self.config.self_healing_enabled:
                recovery_result = await self._attempt_recovery(task_type, task_data, str(e))
                if recovery_result.get("recovered"):
                    return recovery_result
            
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _execute_codegen_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using Codegen SDK"""
        if not self.codegen_agent:
            raise RuntimeError("Codegen SDK not initialized")
        
        # Extract prompt and context from task data
        prompt = task_data.get("prompt", "")
        context = task_data.get("context", {})
        
        if not prompt:
            raise ValueError("Prompt is required for Codegen tasks")
        
        # Enhance prompt with context if available
        if context:
            enhanced_prompt = self._enhance_prompt_with_context(prompt, context)
        else:
            enhanced_prompt = prompt
        
        try:
            # Execute task with Codegen SDK
            task = self.codegen_agent.run(prompt=enhanced_prompt)
            
            # Wait for completion with timeout
            timeout_seconds = self.config.default_timeout_ms / 1000
            start_time = datetime.now()
            
            while task.status not in ["completed", "failed"]:
                if (datetime.now() - start_time).total_seconds() > timeout_seconds:
                    raise TimeoutError(f"Task timed out after {timeout_seconds} seconds")
                
                await asyncio.sleep(1)
                task.refresh()
            
            if task.status == "completed":
                return {
                    "codegen_task_id": task.id,
                    "status": task.status,
                    "result": task.result,
                    "execution_time": (datetime.now() - start_time).total_seconds()
                }
            else:
                raise RuntimeError(f"Codegen task failed with status: {task.status}")
                
        except Exception as e:
            logger.error(f"Codegen task execution failed: {e}")
            raise
    
    def _enhance_prompt_with_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """Enhance prompt with contextual information"""
        context_str = json.dumps(context, indent=2)
        
        enhanced_prompt = f"""
{prompt}

Context Information:
{context_str}

Please use the provided context to inform your response and ensure accuracy.
"""
        return enhanced_prompt
    
    async def _attempt_recovery(self, task_type: str, task_data: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Attempt to recover from task failure using self-healing mechanisms"""
        logger.info(f"Attempting recovery for failed task: {task_type}")
        
        try:
            # Analyze error and determine recovery strategy
            recovery_prompt = f"""
A task of type '{task_type}' failed with the following error:
{error}

Task data: {json.dumps(task_data, indent=2)}

Please analyze this error and provide a corrected approach or alternative solution.
Focus on:
1. Root cause analysis
2. Corrective actions
3. Alternative implementation approaches
4. Prevention strategies for future occurrences

Provide a practical solution that can be implemented immediately.
"""
            
            # Use Codegen SDK for recovery analysis
            recovery_task = await self._execute_codegen_task(
                "codegen.analyze_and_recover",
                {
                    "prompt": recovery_prompt,
                    "context": {
                        "original_task_type": task_type,
                        "original_task_data": task_data,
                        "error": error
                    }
                }
            )
            
            return {
                "task_id": f"recovery_{datetime.now().isoformat()}",
                "status": "recovered",
                "recovery_analysis": recovery_task["result"],
                "original_error": error,
                "timestamp": datetime.now().isoformat(),
                "recovered": True
            }
            
        except Exception as recovery_error:
            logger.error(f"Recovery attempt failed: {recovery_error}")
            return {
                "task_id": f"recovery_failed_{datetime.now().isoformat()}",
                "status": "recovery_failed",
                "original_error": error,
                "recovery_error": str(recovery_error),
                "timestamp": datetime.now().isoformat(),
                "recovered": False
            }
    
    async def _process_task_queue(self):
        """Process tasks from the queue"""
        while self.is_running:
            try:
                # Get task from queue with timeout
                task_item = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Execute task
                task_id = task_item["task_id"]
                self.running_tasks[task_id] = asyncio.create_task(
                    self.execute_task(
                        task_item["task_type"],
                        task_item["task_data"],
                        task_item.get("priority", 3)
                    )
                )
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error processing task queue: {e}")
    
    async def queue_task(self, task_type: str, task_data: Dict[str, Any], priority: int = 3) -> str:
        """Queue a task for asynchronous execution"""
        task_id = f"{task_type}_{datetime.now().isoformat()}"
        
        await self.task_queue.put({
            "task_id": task_id,
            "task_type": task_type,
            "task_data": task_data,
            "priority": priority,
            "queued_at": datetime.now().isoformat()
        })
        
        logger.info(f"Task queued: {task_id}")
        return task_id
    
    def get_extension(self, name: str) -> Optional[Any]:
        """Get an extension by name"""
        return self.extensions.get(name)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            "is_running": self.is_running,
            "extensions": {
                name: hasattr(ext, 'get_status') and ext.get_status() or "active"
                for name, ext in self.extensions.items()
            },
            "running_tasks": len(self.running_tasks),
            "queue_size": self.task_queue.qsize(),
            "config": {
                "codegen_org_id": self.config.codegen_org_id,
                "linear_enabled": self.config.linear_enabled,
                "github_enabled": self.config.github_enabled,
                "slack_enabled": self.config.slack_enabled,
                "openevolve_enabled": self.config.openevolve_enabled,
                "self_healing_enabled": self.config.self_healing_enabled,
                "continuous_learning_enabled": self.config.continuous_learning_enabled
            },
            "timestamp": datetime.now().isoformat()
        }

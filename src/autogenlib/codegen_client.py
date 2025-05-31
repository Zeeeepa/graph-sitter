"""
Codegen API Client
Effective implementation with org_id and token for automated code generation
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import json

try:
    from codegen import Agent
except ImportError:
    # Fallback for development/testing
    class Agent:
        def __init__(self, org_id: str, token: str):
            self.org_id = org_id
            self.token = token
        
        def run(self, prompt: str):
            return MockTask(prompt)

class MockTask:
    def __init__(self, prompt: str):
        self.prompt = prompt
        self.status = "pending"
        self.result = None
    
    def refresh(self):
        self.status = "completed"
        self.result = f"Mock result for: {self.prompt}"


@dataclass
class CodegenConfig:
    """Configuration for Codegen API client"""
    org_id: str
    token: str
    base_url: Optional[str] = None
    timeout_seconds: int = 300
    max_retries: int = 3
    retry_delay_seconds: int = 5


class CodegenClient:
    """
    Enhanced Codegen API client with comprehensive task management
    and error handling for automated code generation
    """
    
    def __init__(self, config: CodegenConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.agent = None
        self.active_tasks: Dict[str, Any] = {}
        self._initialize_agent()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("autogenlib.codegen")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_agent(self):
        """Initialize Codegen agent with credentials"""
        try:
            # Get credentials from config or environment
            org_id = self.config.org_id or os.getenv('CODEGEN_ORG_ID')
            token = self.config.token or os.getenv('CODEGEN_TOKEN')
            
            if not org_id or not token:
                raise ValueError(
                    "Codegen credentials not provided. Set CODEGEN_ORG_ID and CODEGEN_TOKEN "
                    "environment variables or provide them in config."
                )
            
            self.agent = Agent(org_id=org_id, token=token)
            self.logger.info(f"Codegen agent initialized for org: {org_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Codegen agent: {e}")
            raise
    
    async def generate_code(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate code using Codegen API
        
        Args:
            prompt: Code generation prompt
            context: Additional context for generation
            task_id: Optional task identifier
            
        Returns:
            Generation result with status and code
        """
        if task_id is None:
            task_id = f"codegen_{datetime.now().isoformat()}"
        
        self.logger.info(f"Starting code generation task {task_id}")
        
        try:
            # Enhance prompt with context if provided
            enhanced_prompt = self._enhance_prompt(prompt, context)
            
            # Submit task to Codegen
            task = self.agent.run(enhanced_prompt)
            self.active_tasks[task_id] = {
                "task": task,
                "prompt": enhanced_prompt,
                "started_at": datetime.now(),
                "context": context or {}
            }
            
            # Wait for completion with timeout
            result = await self._wait_for_completion(task, task_id)
            
            # Clean up active task
            self.active_tasks.pop(task_id, None)
            
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "prompt": enhanced_prompt,
                "completed_at": datetime.now().isoformat()
            }
            
        except asyncio.TimeoutError:
            self.logger.error(f"Code generation task {task_id} timed out")
            self.active_tasks.pop(task_id, None)
            return {
                "task_id": task_id,
                "status": "timeout",
                "error": "Code generation timed out",
                "failed_at": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Code generation task {task_id} failed: {e}")
            self.active_tasks.pop(task_id, None)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            }
    
    def _enhance_prompt(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Enhance prompt with additional context"""
        if not context:
            return prompt
        
        enhanced_parts = [prompt]
        
        # Add codebase context
        if "codebase_info" in context:
            enhanced_parts.append(f"\nCodebase Context:\n{context['codebase_info']}")
        
        # Add file context
        if "file_context" in context:
            enhanced_parts.append(f"\nFile Context:\n{context['file_context']}")
        
        # Add requirements
        if "requirements" in context:
            enhanced_parts.append(f"\nRequirements:\n{context['requirements']}")
        
        # Add constraints
        if "constraints" in context:
            enhanced_parts.append(f"\nConstraints:\n{context['constraints']}")
        
        return "\n".join(enhanced_parts)
    
    async def _wait_for_completion(self, task: Any, task_id: str) -> str:
        """Wait for task completion with polling"""
        start_time = datetime.now()
        timeout = self.config.timeout_seconds
        
        while True:
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                raise asyncio.TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
            
            # Refresh task status
            try:
                task.refresh()
                
                if task.status == "completed":
                    self.logger.info(f"Task {task_id} completed successfully")
                    return task.result
                elif task.status == "failed":
                    raise Exception(f"Task failed: {getattr(task, 'error', 'Unknown error')}")
                
                # Wait before next poll
                await asyncio.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error polling task {task_id}: {e}")
                raise
    
    async def batch_generate(
        self, 
        prompts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Generate code for multiple prompts concurrently
        
        Args:
            prompts: List of prompt dictionaries with 'prompt' and optional 'context'
            
        Returns:
            List of generation results
        """
        self.logger.info(f"Starting batch code generation for {len(prompts)} prompts")
        
        # Create tasks for all prompts
        tasks = []
        for i, prompt_info in enumerate(prompts):
            task_id = prompt_info.get('id', f"batch_{i}")
            task = self.generate_code(
                prompt=prompt_info['prompt'],
                context=prompt_info.get('context'),
                task_id=task_id
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "task_id": prompts[i].get('id', f"batch_{i}"),
                    "status": "failed",
                    "error": str(result),
                    "failed_at": datetime.now().isoformat()
                })
            else:
                processed_results.append(result)
        
        self.logger.info(f"Batch generation completed: {len(processed_results)} results")
        return processed_results
    
    def get_active_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get information about active code generation tasks"""
        active_info = {}
        for task_id, task_info in self.active_tasks.items():
            active_info[task_id] = {
                "prompt": task_info["prompt"][:100] + "..." if len(task_info["prompt"]) > 100 else task_info["prompt"],
                "started_at": task_info["started_at"].isoformat(),
                "elapsed_seconds": (datetime.now() - task_info["started_at"]).total_seconds(),
                "context_keys": list(task_info["context"].keys())
            }
        return active_info
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel an active code generation task
        
        Args:
            task_id: Task identifier to cancel
            
        Returns:
            True if task was cancelled, False if not found
        """
        if task_id not in self.active_tasks:
            return False
        
        try:
            # Note: Codegen API doesn't support cancellation directly
            # We remove from our tracking and log the cancellation
            task_info = self.active_tasks.pop(task_id)
            self.logger.info(f"Cancelled task {task_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get client status and statistics"""
        return {
            "status": "healthy" if self.agent else "unhealthy",
            "org_id": self.config.org_id,
            "active_tasks": len(self.active_tasks),
            "config": {
                "timeout_seconds": self.config.timeout_seconds,
                "max_retries": self.config.max_retries,
                "retry_delay_seconds": self.config.retry_delay_seconds
            },
            "timestamp": datetime.now().isoformat()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of Codegen client"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "agent_initialized": self.agent is not None,
            "active_tasks": len(self.active_tasks),
            "config_valid": bool(self.config.org_id and self.config.token)
        }
        
        # Test basic connectivity (if possible)
        try:
            if self.agent:
                # Simple test to verify agent is working
                test_task = self.agent.run("# Test connectivity")
                health_status["connectivity"] = "ok"
            else:
                health_status["status"] = "unhealthy"
                health_status["error"] = "Agent not initialized"
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["connectivity_error"] = str(e)
        
        return health_status


"""
Enhanced Codegen Client with Effective SDK Integration
"""

import asyncio
import logging
import os
import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import time

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

logger = logging.getLogger(__name__)


@dataclass
class CodegenConfig:
    """Configuration for Codegen Client"""
    
    # Required Codegen SDK Configuration
    org_id: str = "323"
    token: Optional[str] = None
    
    # Performance Configuration
    max_concurrent_tasks: int = 10
    default_timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    
    # Caching Configuration
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    
    # Context Enhancement
    enable_context_enhancement: bool = True
    max_context_length: int = 10000
    
    # Cost Management
    enable_cost_tracking: bool = True
    max_daily_cost: float = 100.0
    
    def __post_init__(self):
        """Load configuration from environment variables if not provided"""
        if not self.token:
            self.token = os.getenv("CODEGEN_TOKEN")
        
        # Override with environment variables if available
        if os.getenv("CODEGEN_ORG_ID"):
            self.org_id = os.getenv("CODEGEN_ORG_ID")


class CodegenClient:
    """
    Enhanced Codegen SDK Client with comprehensive features
    
    Provides:
    - Effective org_id and token configuration
    - Batch processing capabilities
    - Context enhancement
    - Caching and optimization
    - Cost tracking and management
    - Error handling and retry logic
    - Performance monitoring
    """
    
    def __init__(self, config: CodegenConfig):
        self.config = config
        self.agent: Optional[Agent] = None
        self.task_cache: Dict[str, Dict[str, Any]] = {}
        self.cost_tracker: Dict[str, float] = {"daily_cost": 0.0, "last_reset": time.time()}
        self.performance_metrics: Dict[str, Any] = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_duration": 0.0,
            "cache_hits": 0
        }
        
        # Initialize Codegen SDK
        self._initialize_sdk()
        
        logger.info(f"Codegen client initialized with org_id: {self.config.org_id}")
    
    def _initialize_sdk(self):
        """Initialize Codegen SDK with proper configuration"""
        if not self.config.token:
            raise ValueError("Codegen token is required. Set CODEGEN_TOKEN environment variable or provide in config.")
        
        try:
            self.agent = Agent(
                org_id=self.config.org_id,
                token=self.config.token
            )
            logger.info("Codegen SDK initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Codegen SDK: {e}")
            raise
    
    async def generate_code(
        self, 
        prompt: str, 
        context: Optional[Dict[str, Any]] = None,
        timeout_seconds: Optional[int] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Generate code using Codegen SDK
        
        Args:
            prompt: The prompt for code generation
            context: Optional context to enhance the prompt
            timeout_seconds: Custom timeout (uses default if not provided)
            use_cache: Whether to use caching for this request
        
        Returns:
            Generation result with metadata
        """
        start_time = time.time()
        
        try:
            # Check daily cost limit
            if self.config.enable_cost_tracking:
                self._check_cost_limit()
            
            # Enhance prompt with context if enabled
            enhanced_prompt = prompt
            if self.config.enable_context_enhancement and context:
                enhanced_prompt = self._enhance_prompt_with_context(prompt, context)
            
            # Check cache if enabled
            cache_key = None
            if use_cache and self.config.enable_caching:
                cache_key = self._generate_cache_key(enhanced_prompt, context)
                cached_result = self._get_cached_result(cache_key)
                if cached_result:
                    self.performance_metrics["cache_hits"] += 1
                    logger.info("Returning cached result")
                    return cached_result
            
            # Execute with Codegen SDK
            result = await self._execute_with_retry(
                enhanced_prompt, 
                timeout_seconds or self.config.default_timeout_seconds
            )
            
            # Update metrics
            duration = time.time() - start_time
            self._update_performance_metrics(duration, True)
            
            # Cache result if enabled
            if cache_key and self.config.enable_caching:
                self._cache_result(cache_key, result)
            
            # Track cost if enabled
            if self.config.enable_cost_tracking:
                self._track_cost(result)
            
            logger.info(f"Code generation completed in {duration:.2f}s")
            
            return {
                "status": "success",
                "result": result,
                "metadata": {
                    "duration_seconds": duration,
                    "prompt_length": len(prompt),
                    "enhanced_prompt_length": len(enhanced_prompt),
                    "context_provided": context is not None,
                    "cache_used": False,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            duration = time.time() - start_time
            self._update_performance_metrics(duration, False)
            
            logger.error(f"Code generation failed after {duration:.2f}s: {e}")
            
            return {
                "status": "failed",
                "error": str(e),
                "metadata": {
                    "duration_seconds": duration,
                    "prompt_length": len(prompt),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _execute_with_retry(self, prompt: str, timeout_seconds: int) -> Any:
        """Execute Codegen task with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                # Create and execute task
                task = self.agent.run(prompt=prompt)
                
                # Wait for completion with timeout
                start_time = time.time()
                while task.status not in ["completed", "failed"]:
                    if time.time() - start_time > timeout_seconds:
                        raise TimeoutError(f"Task timed out after {timeout_seconds} seconds")
                    
                    await asyncio.sleep(1)
                    task.refresh()
                
                if task.status == "completed":
                    return task.result
                else:
                    raise RuntimeError(f"Task failed with status: {task.status}")
                    
            except Exception as e:
                last_exception = e
                if attempt < self.config.retry_attempts - 1:
                    delay = self.config.retry_delay_seconds * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"All {self.config.retry_attempts} attempts failed")
        
        raise last_exception
    
    def _enhance_prompt_with_context(self, prompt: str, context: Dict[str, Any]) -> str:
        """Enhance prompt with contextual information"""
        if not context:
            return prompt
        
        # Convert context to string representation
        context_str = json.dumps(context, indent=2, default=str)
        
        # Truncate if too long
        if len(context_str) > self.config.max_context_length:
            context_str = context_str[:self.config.max_context_length] + "... [truncated]"
        
        enhanced_prompt = f"""
{prompt}

## Context Information:
```json
{context_str}
```

Please use the provided context to inform your response and ensure accuracy. Consider the context when generating code, making decisions, and providing explanations.
"""
        return enhanced_prompt
    
    def _generate_cache_key(self, prompt: str, context: Optional[Dict[str, Any]]) -> str:
        """Generate a cache key for the request"""
        content = prompt
        if context:
            content += json.dumps(context, sort_keys=True, default=str)
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if available and not expired"""
        if cache_key not in self.task_cache:
            return None
        
        cached_item = self.task_cache[cache_key]
        
        # Check if expired
        if time.time() - cached_item["timestamp"] > self.config.cache_ttl_seconds:
            del self.task_cache[cache_key]
            return None
        
        return cached_item["result"]
    
    def _cache_result(self, cache_key: str, result: Any):
        """Cache the result"""
        self.task_cache[cache_key] = {
            "result": {
                "status": "success",
                "result": result,
                "metadata": {
                    "cached": True,
                    "timestamp": datetime.now().isoformat()
                }
            },
            "timestamp": time.time()
        }
    
    def _check_cost_limit(self):
        """Check if daily cost limit is exceeded"""
        current_time = time.time()
        
        # Reset daily cost if it's a new day
        if current_time - self.cost_tracker["last_reset"] > 86400:  # 24 hours
            self.cost_tracker["daily_cost"] = 0.0
            self.cost_tracker["last_reset"] = current_time
        
        if self.cost_tracker["daily_cost"] >= self.config.max_daily_cost:
            raise RuntimeError(f"Daily cost limit of ${self.config.max_daily_cost} exceeded")
    
    def _track_cost(self, result: Any):
        """Track cost of the operation"""
        # This is a simplified cost estimation
        # In a real implementation, you would get actual cost from the API response
        estimated_cost = 0.01  # $0.01 per request as example
        
        self.cost_tracker["daily_cost"] += estimated_cost
        logger.debug(f"Estimated cost: ${estimated_cost}, Daily total: ${self.cost_tracker['daily_cost']}")
    
    def _update_performance_metrics(self, duration: float, success: bool):
        """Update performance metrics"""
        self.performance_metrics["total_tasks"] += 1
        
        if success:
            self.performance_metrics["successful_tasks"] += 1
        else:
            self.performance_metrics["failed_tasks"] += 1
        
        # Update average duration
        total_tasks = self.performance_metrics["total_tasks"]
        current_avg = self.performance_metrics["average_duration"]
        self.performance_metrics["average_duration"] = (
            (current_avg * (total_tasks - 1) + duration) / total_tasks
        )
    
    async def batch_generate(
        self, 
        requests: List[Dict[str, Any]], 
        max_concurrent: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate code for multiple requests concurrently
        
        Args:
            requests: List of request dictionaries with 'prompt' and optional 'context'
            max_concurrent: Maximum concurrent requests (uses config default if not provided)
        
        Returns:
            List of results in the same order as requests
        """
        max_concurrent = max_concurrent or self.config.max_concurrent_tasks
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_request(request: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self.generate_code(
                    prompt=request["prompt"],
                    context=request.get("context"),
                    timeout_seconds=request.get("timeout_seconds"),
                    use_cache=request.get("use_cache", True)
                )
        
        # Execute all requests concurrently
        tasks = [process_request(request) for request in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "status": "failed",
                    "error": str(result),
                    "request_index": i,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                processed_results.append(result)
        
        logger.info(f"Batch generation completed: {len(requests)} requests")
        return processed_results
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        success_rate = 0.0
        if self.performance_metrics["total_tasks"] > 0:
            success_rate = (
                self.performance_metrics["successful_tasks"] / 
                self.performance_metrics["total_tasks"]
            )
        
        return {
            **self.performance_metrics,
            "success_rate": success_rate,
            "cache_hit_rate": (
                self.performance_metrics["cache_hits"] / 
                max(self.performance_metrics["total_tasks"], 1)
            ),
            "daily_cost": self.cost_tracker["daily_cost"],
            "cache_size": len(self.task_cache),
            "timestamp": datetime.now().isoformat()
        }
    
    def clear_cache(self):
        """Clear the task cache"""
        self.task_cache.clear()
        logger.info("Task cache cleared")
    
    def reset_metrics(self):
        """Reset performance metrics"""
        self.performance_metrics = {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "average_duration": 0.0,
            "cache_hits": 0
        }
        logger.info("Performance metrics reset")

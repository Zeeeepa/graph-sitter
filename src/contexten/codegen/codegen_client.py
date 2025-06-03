"""
Enhanced Codegen SDK Client with Context Integration.

This module provides the main interface for integrating the Codegen SDK with
the contexten orchestrator, including context enhancement, performance optimization,
and seamless integration with existing graph_sitter analysis functions.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx

# Import from existing Codegen SDK
from codegen.agents.agent import Agent, AgentTask

# Import from graph_sitter analysis functions
from graph_sitter.codebase.codebase_analysis import (
    get_codebase_summary,
    get_file_summary,
    get_class_summary,
    get_function_summary,
    get_symbol_summary
)
from graph_sitter.core.codebase import Codebase

# Import local configuration and components
from .config import CodegenConfig
from .config.auth_config import AuthConfig, AuthCredentials
from .performance.rate_limiter import RateLimiter
from .performance.connection_pool import ConnectionPool
from .context.context_pipeline import ContextPipeline
from .monitoring.metrics_collector import MetricsCollector


logger = logging.getLogger(__name__)


@dataclass
class CodegenRequest:
    """Container for code generation requests with context."""
    prompt: str
    context: Optional[Dict[str, Any]] = None
    priority: int = 1  # 1 = highest, 5 = lowest
    timeout: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None


@dataclass
class CodegenResponse:
    """Container for code generation responses with metadata."""
    request_id: str
    task_id: str
    status: str
    result: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class CodegenSDKAdapter:
    """
    Enhanced Codegen SDK adapter with context integration and performance optimization.
    
    This adapter provides a high-level interface for the Codegen SDK with:
    - Intelligent context enhancement using graph_sitter analysis
    - Performance optimization with connection pooling and rate limiting
    - Async/await support for concurrent operations
    - Comprehensive monitoring and metrics collection
    - Seamless integration with contexten orchestrator
    """
    
    def __init__(self, config: CodegenConfig):
        """
        Initialize the Codegen SDK adapter.
        
        Args:
            config: Configuration for the adapter
        """
        self.config = config
        self._agent: Optional[Agent] = None
        self._auth_config: Optional[AuthConfig] = None
        self._rate_limiter: Optional[RateLimiter] = None
        self._connection_pool: Optional[ConnectionPool] = None
        self._context_pipeline: Optional[ContextPipeline] = None
        self._metrics_collector: Optional[MetricsCollector] = None
        self._active_tasks: Dict[str, AgentTask] = {}
        self._initialized = False
        
        # Validate configuration
        config.validate()
    
    async def initialize(self) -> None:
        """
        Initialize the adapter and all its components.
        
        Raises:
            ValueError: If initialization fails
        """
        if self._initialized:
            return
        
        try:
            # Initialize authentication
            await self._initialize_auth()
            
            # Initialize performance components
            await self._initialize_performance()
            
            # Initialize context pipeline
            await self._initialize_context()
            
            # Initialize monitoring
            await self._initialize_monitoring()
            
            # Initialize Codegen SDK agent
            await self._initialize_agent()
            
            self._initialized = True
            logger.info("CodegenSDKAdapter initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize CodegenSDKAdapter: {e}")
            raise ValueError(f"Initialization failed: {e}")
    
    async def generate_code(self, 
                          request: Union[str, CodegenRequest],
                          codebase: Optional[Codebase] = None,
                          enhance_context: bool = True) -> CodegenResponse:
        """
        Generate code using the Codegen SDK with optional context enhancement.
        
        Args:
            request: Code generation request (prompt string or CodegenRequest object)
            codebase: Optional codebase for context enhancement
            enhance_context: Whether to enhance the prompt with codebase context
            
        Returns:
            CodegenResponse with generation results
            
        Raises:
            ValueError: If request is invalid
            RuntimeError: If generation fails
        """
        await self._ensure_initialized()
        
        # Convert string prompt to CodegenRequest
        if isinstance(request, str):
            request = CodegenRequest(prompt=request)
        
        # Generate unique request ID if not provided
        if not request.request_id:
            request.request_id = f"req_{int(time.time() * 1000)}"
        
        start_time = time.time()
        
        try:
            # Enhance prompt with context if requested
            enhanced_prompt = request.prompt
            if enhance_context and codebase and self._context_pipeline:
                enhanced_prompt = await self._context_pipeline.enhance_prompt(
                    request.prompt, codebase, request.context
                )
                logger.debug(f"Enhanced prompt for request {request.request_id}")
            
            # Apply rate limiting
            if self._rate_limiter:
                await self._rate_limiter.acquire()
            
            # Submit task to Codegen SDK
            task = self._agent.run(enhanced_prompt)
            self._active_tasks[request.request_id] = task
            
            # Create initial response
            response = CodegenResponse(
                request_id=request.request_id,
                task_id=task.id,
                status=task.status,
                metadata={
                    "original_prompt": request.prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "context_enhanced": enhance_context and codebase is not None,
                    "priority": request.priority
                }
            )
            
            # Record metrics
            if self._metrics_collector:
                await self._metrics_collector.record_request(request, response)
            
            logger.info(f"Started code generation task {task.id} for request {request.request_id}")
            return response
            
        except Exception as e:
            error_msg = f"Failed to generate code: {e}"
            logger.error(error_msg)
            
            # Record error metrics
            if self._metrics_collector:
                await self._metrics_collector.record_error(request.request_id, str(e))
            
            return CodegenResponse(
                request_id=request.request_id,
                task_id="",
                status="failed",
                error=error_msg,
                metadata={"error_time": time.time() - start_time}
            )
    
    async def get_task_status(self, request_id: str) -> Optional[CodegenResponse]:
        """
        Get the status of a code generation task.
        
        Args:
            request_id: Request ID to check status for
            
        Returns:
            CodegenResponse with current status, None if not found
        """
        await self._ensure_initialized()
        
        task = self._active_tasks.get(request_id)
        if not task:
            logger.warning(f"Task not found for request {request_id}")
            return None
        
        try:
            # Refresh task status
            task.refresh()
            
            response = CodegenResponse(
                request_id=request_id,
                task_id=task.id,
                status=task.status,
                result=task.result if task.status == "completed" else None,
                metadata={
                    "web_url": getattr(task, "web_url", None),
                    "last_updated": datetime.utcnow().isoformat()
                }
            )
            
            # If task is completed or failed, remove from active tasks
            if task.status in ["completed", "failed"]:
                response.completed_at = datetime.utcnow()
                del self._active_tasks[request_id]
                
                # Record completion metrics
                if self._metrics_collector:
                    await self._metrics_collector.record_completion(request_id, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to get task status for {request_id}: {e}")
            return CodegenResponse(
                request_id=request_id,
                task_id=task.id,
                status="error",
                error=str(e)
            )
    
    async def wait_for_completion(self, 
                                request_id: str, 
                                timeout: float = 300.0,
                                poll_interval: float = 2.0) -> CodegenResponse:
        """
        Wait for a code generation task to complete.
        
        Args:
            request_id: Request ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check status in seconds
            
        Returns:
            CodegenResponse with final results
            
        Raises:
            TimeoutError: If task doesn't complete within timeout
        """
        await self._ensure_initialized()
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = await self.get_task_status(request_id)
            
            if not response:
                raise ValueError(f"Task not found: {request_id}")
            
            if response.status in ["completed", "failed", "error"]:
                return response
            
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Task {request_id} did not complete within {timeout} seconds")
    
    async def batch_generate(self, 
                           requests: List[Union[str, CodegenRequest]],
                           codebase: Optional[Codebase] = None,
                           max_concurrent: Optional[int] = None) -> List[CodegenResponse]:
        """
        Generate code for multiple requests concurrently.
        
        Args:
            requests: List of code generation requests
            codebase: Optional codebase for context enhancement
            max_concurrent: Maximum concurrent requests (uses config default if None)
            
        Returns:
            List of CodegenResponse objects
        """
        await self._ensure_initialized()
        
        if not requests:
            return []
        
        max_concurrent = max_concurrent or self.config.max_concurrent_requests
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def generate_with_semaphore(request):
            async with semaphore:
                return await self.generate_code(request, codebase)
        
        # Execute requests concurrently
        tasks = [generate_with_semaphore(req) for req in requests]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error responses
        final_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                req_id = f"batch_req_{i}"
                if isinstance(requests[i], CodegenRequest) and requests[i].request_id:
                    req_id = requests[i].request_id
                
                final_responses.append(CodegenResponse(
                    request_id=req_id,
                    task_id="",
                    status="failed",
                    error=str(response)
                ))
            else:
                final_responses.append(response)
        
        logger.info(f"Completed batch generation for {len(requests)} requests")
        return final_responses
    
    async def get_codebase_context(self, codebase: Codebase) -> Dict[str, Any]:
        """
        Get enhanced codebase context using graph_sitter analysis functions.
        
        Args:
            codebase: Codebase to analyze
            
        Returns:
            Dictionary containing codebase context information
        """
        await self._ensure_initialized()
        
        if not self._context_pipeline:
            # Fallback to basic analysis if context pipeline not available
            return {
                "summary": get_codebase_summary(codebase),
                "file_count": len(list(codebase.files)),
                "function_count": len(list(codebase.functions)),
                "class_count": len(list(codebase.classes))
            }
        
        return await self._context_pipeline.get_codebase_context(codebase)
    
    async def shutdown(self) -> None:
        """Shutdown the adapter and cleanup resources."""
        logger.info("Shutting down CodegenSDKAdapter")
        
        # Wait for active tasks to complete (with timeout)
        if self._active_tasks:
            logger.info(f"Waiting for {len(self._active_tasks)} active tasks to complete")
            try:
                await asyncio.wait_for(
                    self._wait_for_active_tasks(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not complete during shutdown")
        
        # Shutdown components
        if self._connection_pool:
            await self._connection_pool.close()
        
        if self._metrics_collector:
            await self._metrics_collector.shutdown()
        
        self._initialized = False
        logger.info("CodegenSDKAdapter shutdown complete")
    
    # Private methods
    
    async def _ensure_initialized(self) -> None:
        """Ensure the adapter is initialized."""
        if not self._initialized:
            await self.initialize()
    
    async def _initialize_auth(self) -> None:
        """Initialize authentication configuration."""
        self._auth_config = AuthConfig()
        
        # Load credentials
        credentials = self._auth_config.load_credentials(self.config.environment.value)
        if not credentials:
            # Create credentials from config
            credentials = AuthCredentials(
                org_id=self.config.org_id,
                token=self.config.token,
                created_at=datetime.utcnow()
            )
        
        # Validate credentials
        is_valid, error_msg = self._auth_config.validate_credentials(credentials)
        if not is_valid:
            raise ValueError(f"Invalid credentials: {error_msg}")
        
        logger.info("Authentication initialized successfully")
    
    async def _initialize_performance(self) -> None:
        """Initialize performance optimization components."""
        # Initialize rate limiter
        self._rate_limiter = RateLimiter(
            requests_per_second=self.config.requests_per_second,
            burst_limit=self.config.burst_limit
        )
        
        # Initialize connection pool
        self._connection_pool = ConnectionPool(
            max_connections=self.config.connection_pool_size,
            timeout=self.config.request_timeout
        )
        
        logger.info("Performance components initialized")
    
    async def _initialize_context(self) -> None:
        """Initialize context enhancement pipeline."""
        if self.config.is_feature_enabled("enhanced_context"):
            self._context_pipeline = ContextPipeline(
                max_tokens=self.config.max_context_tokens,
                cache_ttl=self.config.context_cache_ttl,
                enable_caching=self.config.enable_context_caching
            )
            await self._context_pipeline.initialize()
            logger.info("Context pipeline initialized")
    
    async def _initialize_monitoring(self) -> None:
        """Initialize monitoring and metrics collection."""
        if self.config.enable_metrics:
            self._metrics_collector = MetricsCollector(
                enable_cost_tracking=self.config.enable_cost_tracking,
                export_interval=self.config.metrics_export_interval
            )
            await self._metrics_collector.initialize()
            logger.info("Metrics collection initialized")
    
    async def _initialize_agent(self) -> None:
        """Initialize the Codegen SDK agent."""
        self._agent = Agent(
            token=self.config.token,
            org_id=int(self.config.org_id),
            base_url=self.config.base_url
        )
        logger.info("Codegen SDK agent initialized")
    
    async def _wait_for_active_tasks(self) -> None:
        """Wait for all active tasks to complete."""
        while self._active_tasks:
            completed_tasks = []
            
            for request_id, task in self._active_tasks.items():
                try:
                    task.refresh()
                    if task.status in ["completed", "failed"]:
                        completed_tasks.append(request_id)
                except Exception as e:
                    logger.error(f"Error checking task {request_id}: {e}")
                    completed_tasks.append(request_id)
            
            # Remove completed tasks
            for request_id in completed_tasks:
                del self._active_tasks[request_id]
            
            if self._active_tasks:
                await asyncio.sleep(1.0)
    
    def get_metrics(self) -> Optional[Dict[str, Any]]:
        """Get current metrics if metrics collection is enabled."""
        if self._metrics_collector:
            return self._metrics_collector.get_current_metrics()
        return None
    
    def get_active_task_count(self) -> int:
        """Get the number of currently active tasks."""
        return len(self._active_tasks)
    
    def is_healthy(self) -> bool:
        """Check if the adapter is healthy and operational."""
        return (
            self._initialized and
            self._agent is not None and
            (not self._rate_limiter or self._rate_limiter.is_healthy()) and
            (not self._connection_pool or self._connection_pool.is_healthy())
        )


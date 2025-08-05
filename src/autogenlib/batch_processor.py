"""
Batch Processor for Autogenlib
Concurrent code generation for multiple requests
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

from .codegen_client import CodegenClient
from .task_manager import TaskManager, TaskPriority

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """Batch processing status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchRequest:
    """Individual request in a batch"""
    id: str
    prompt: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchJob:
    """Batch processing job"""
    id: str
    name: str
    requests: List[BatchRequest]
    status: BatchStatus = BatchStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    errors: Dict[str, str] = field(default_factory=dict)
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class BatchProcessor:
    """
    Advanced batch processing system for concurrent code generation
    
    Provides:
    - Concurrent processing of multiple requests
    - Progress tracking and monitoring
    - Error handling and retry logic
    - Resource management and throttling
    - Result aggregation and reporting
    - Batch job scheduling
    """
    
    def __init__(
        self,
        codegen_client: CodegenClient,
        task_manager: Optional[TaskManager] = None,
        max_concurrent_batches: int = 5,
        max_concurrent_requests: int = 20
    ):
        self.codegen_client = codegen_client
        self.task_manager = task_manager
        self.max_concurrent_batches = max_concurrent_batches
        self.max_concurrent_requests = max_concurrent_requests
        
        self.batch_jobs: Dict[str, BatchJob] = {}
        self.running_batches: Dict[str, asyncio.Task] = {}
        self.batch_queue: asyncio.Queue = asyncio.Queue()
        self.is_running = False
        
        # Performance metrics
        self.metrics = {
            "total_batches": 0,
            "completed_batches": 0,
            "failed_batches": 0,
            "total_requests": 0,
            "completed_requests": 0,
            "failed_requests": 0,
            "average_batch_time": 0.0,
            "average_request_time": 0.0
        }
        
        logger.info("Batch Processor initialized")
    
    async def start(self):
        """Start the batch processor"""
        if self.is_running:
            logger.warning("Batch Processor is already running")
            return
        
        self.is_running = True
        
        # Start batch queue processor
        asyncio.create_task(self._process_batch_queue())
        
        logger.info("Batch Processor started")
    
    async def stop(self):
        """Stop the batch processor"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Cancel running batches
        for batch_id, task in self.running_batches.items():
            task.cancel()
            logger.info(f"Cancelled batch: {batch_id}")
        
        self.running_batches.clear()
        
        logger.info("Batch Processor stopped")
    
    def create_batch_job(
        self,
        name: str,
        requests: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new batch job
        
        Args:
            name: Batch job name
            requests: List of request dictionaries
            metadata: Optional batch metadata
        
        Returns:
            Batch job ID
        """
        # Convert request dictionaries to BatchRequest objects
        batch_requests = []
        for i, req in enumerate(requests):
            batch_request = BatchRequest(
                id=f"{name}_{i}",
                prompt=req["prompt"],
                context=req.get("context", {}),
                priority=TaskPriority(req.get("priority", TaskPriority.NORMAL.value)),
                timeout_seconds=req.get("timeout_seconds", 300),
                metadata=req.get("metadata", {})
            )
            batch_requests.append(batch_request)
        
        # Create batch job
        batch_job = BatchJob(
            id=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.batch_jobs)}",
            name=name,
            requests=batch_requests,
            metadata=metadata or {}
        )
        
        self.batch_jobs[batch_job.id] = batch_job
        self.metrics["total_batches"] += 1
        self.metrics["total_requests"] += len(batch_requests)
        
        logger.info(f"Created batch job: {batch_job.id} with {len(batch_requests)} requests")
        return batch_job.id
    
    async def submit_batch(self, batch_id: str) -> bool:
        """
        Submit a batch job for processing
        
        Args:
            batch_id: Batch job ID to submit
        
        Returns:
            True if batch was submitted successfully
        """
        if batch_id not in self.batch_jobs:
            logger.error(f"Batch job not found: {batch_id}")
            return False
        
        # Add to queue
        await self.batch_queue.put(batch_id)
        
        logger.info(f"Submitted batch to queue: {batch_id}")
        return True
    
    async def execute_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Execute a batch job immediately (bypassing queue)
        
        Args:
            batch_id: Batch job ID to execute
        
        Returns:
            Batch execution result
        """
        if batch_id not in self.batch_jobs:
            raise ValueError(f"Batch job not found: {batch_id}")
        
        return await self._execute_single_batch(self.batch_jobs[batch_id])
    
    async def wait_for_batch(self, batch_id: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Wait for a batch job to complete
        
        Args:
            batch_id: Batch job ID to wait for
            timeout: Optional timeout in seconds
        
        Returns:
            Batch results
        """
        if batch_id not in self.batch_jobs:
            raise ValueError(f"Batch job not found: {batch_id}")
        
        batch_job = self.batch_jobs[batch_id]
        start_time = datetime.now()
        
        while batch_job.status not in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]:
            if timeout and (datetime.now() - start_time).total_seconds() > timeout:
                raise TimeoutError(f"Batch {batch_id} timed out after {timeout} seconds")
            
            await asyncio.sleep(0.5)
        
        return self.get_batch_results(batch_id)
    
    async def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancel a batch job
        
        Args:
            batch_id: Batch job ID to cancel
        
        Returns:
            True if batch was cancelled successfully
        """
        if batch_id not in self.batch_jobs:
            logger.error(f"Batch job not found: {batch_id}")
            return False
        
        batch_job = self.batch_jobs[batch_id]
        
        # Cancel if running
        if batch_id in self.running_batches:
            self.running_batches[batch_id].cancel()
            del self.running_batches[batch_id]
        
        # Update batch status
        batch_job.status = BatchStatus.CANCELLED
        batch_job.completed_at = datetime.now()
        
        logger.info(f"Cancelled batch: {batch_id}")
        return True
    
    def get_batch_status(self, batch_id: str) -> Optional[BatchStatus]:
        """Get batch job status"""
        if batch_id not in self.batch_jobs:
            return None
        return self.batch_jobs[batch_id].status
    
    def get_batch_progress(self, batch_id: str) -> Optional[float]:
        """Get batch job progress (0.0 to 1.0)"""
        if batch_id not in self.batch_jobs:
            return None
        return self.batch_jobs[batch_id].progress
    
    def get_batch_results(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get batch job results"""
        if batch_id not in self.batch_jobs:
            return None
        
        batch_job = self.batch_jobs[batch_id]
        
        return {
            "batch_id": batch_id,
            "name": batch_job.name,
            "status": batch_job.status.value,
            "progress": batch_job.progress,
            "total_requests": len(batch_job.requests),
            "completed_requests": len(batch_job.results),
            "failed_requests": len(batch_job.errors),
            "created_at": batch_job.created_at.isoformat(),
            "started_at": batch_job.started_at.isoformat() if batch_job.started_at else None,
            "completed_at": batch_job.completed_at.isoformat() if batch_job.completed_at else None,
            "results": batch_job.results,
            "errors": batch_job.errors,
            "metadata": batch_job.metadata
        }
    
    def list_batch_jobs(
        self,
        status: Optional[BatchStatus] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List batch jobs with optional filtering
        
        Args:
            status: Filter by batch status
            limit: Maximum number of jobs to return
        
        Returns:
            List of batch job information
        """
        filtered_jobs = []
        
        for batch_job in self.batch_jobs.values():
            # Filter by status
            if status and batch_job.status != status:
                continue
            
            job_info = {
                "id": batch_job.id,
                "name": batch_job.name,
                "status": batch_job.status.value,
                "progress": batch_job.progress,
                "total_requests": len(batch_job.requests),
                "completed_requests": len(batch_job.results),
                "failed_requests": len(batch_job.errors),
                "created_at": batch_job.created_at.isoformat(),
                "started_at": batch_job.started_at.isoformat() if batch_job.started_at else None,
                "completed_at": batch_job.completed_at.isoformat() if batch_job.completed_at else None
            }
            
            filtered_jobs.append(job_info)
        
        # Sort by creation time (newest first)
        filtered_jobs.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply limit
        if limit:
            filtered_jobs = filtered_jobs[:limit]
        
        return filtered_jobs
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get batch processor metrics"""
        return {
            **self.metrics,
            "queue_size": self.batch_queue.qsize(),
            "running_batches": len(self.running_batches),
            "total_batches_in_system": len(self.batch_jobs),
            "batch_success_rate": (
                self.metrics["completed_batches"] / max(self.metrics["total_batches"], 1)
            ) * 100,
            "request_success_rate": (
                self.metrics["completed_requests"] / max(self.metrics["total_requests"], 1)
            ) * 100,
            "timestamp": datetime.now().isoformat()
        }
    
    async def create_and_submit_batch(
        self,
        name: str,
        requests: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create and immediately submit a batch job"""
        batch_id = self.create_batch_job(name, requests, metadata)
        await self.submit_batch(batch_id)
        return batch_id
    
    async def _process_batch_queue(self):
        """Process batch jobs from the queue"""
        while self.is_running:
            try:
                # Wait for available slot
                while len(self.running_batches) >= self.max_concurrent_batches:
                    await asyncio.sleep(0.1)
                
                # Get next batch from queue
                try:
                    batch_id = await asyncio.wait_for(self.batch_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                
                # Execute batch
                if batch_id in self.batch_jobs:
                    batch_job = self.batch_jobs[batch_id]
                    self.running_batches[batch_id] = asyncio.create_task(
                        self._execute_single_batch(batch_job)
                    )
                
            except Exception as e:
                logger.error(f"Error in batch queue processor: {e}")
    
    async def _execute_single_batch(self, batch_job: BatchJob) -> Dict[str, Any]:
        """Execute a single batch job"""
        try:
            # Update batch status
            batch_job.status = BatchStatus.RUNNING
            batch_job.started_at = datetime.now()
            
            logger.info(f"Executing batch: {batch_job.id} with {len(batch_job.requests)} requests")
            
            # Create semaphore for concurrent request limiting
            semaphore = asyncio.Semaphore(self.max_concurrent_requests)
            
            async def process_request(request: BatchRequest) -> tuple[str, Dict[str, Any]]:
                async with semaphore:
                    try:
                        result = await self.codegen_client.generate_code(
                            prompt=request.prompt,
                            context=request.context,
                            timeout_seconds=request.timeout_seconds
                        )
                        return request.id, result
                    except Exception as e:
                        logger.error(f"Request {request.id} failed: {e}")
                        return request.id, {
                            "status": "failed",
                            "error": str(e),
                            "request_id": request.id
                        }
            
            # Execute all requests concurrently
            tasks = [process_request(request) for request in batch_job.requests]
            
            # Process results as they complete
            completed_count = 0
            for coro in asyncio.as_completed(tasks):
                request_id, result = await coro
                
                if result.get("status") == "success":
                    batch_job.results[request_id] = result
                    self.metrics["completed_requests"] += 1
                else:
                    batch_job.errors[request_id] = result.get("error", "Unknown error")
                    self.metrics["failed_requests"] += 1
                
                # Update progress
                completed_count += 1
                batch_job.progress = completed_count / len(batch_job.requests)
                
                logger.debug(f"Batch {batch_job.id} progress: {batch_job.progress:.2%}")
            
            # Update batch status
            batch_job.status = BatchStatus.COMPLETED
            batch_job.completed_at = datetime.now()
            
            # Update metrics
            self.metrics["completed_batches"] += 1
            
            execution_time = (batch_job.completed_at - batch_job.started_at).total_seconds()
            self.metrics["average_batch_time"] = (
                (self.metrics["average_batch_time"] * (self.metrics["completed_batches"] - 1) + execution_time) /
                self.metrics["completed_batches"]
            )
            
            logger.info(f"Batch completed: {batch_job.id} in {execution_time:.2f}s")
            
            return self.get_batch_results(batch_job.id)
            
        except Exception as e:
            # Handle batch failure
            batch_job.status = BatchStatus.FAILED
            batch_job.completed_at = datetime.now()
            
            # Update metrics
            self.metrics["failed_batches"] += 1
            
            logger.error(f"Batch failed: {batch_job.id} - {e}")
            
            return {
                "status": "failed",
                "error": str(e),
                "batch_id": batch_job.id
            }
        
        finally:
            # Remove from running batches
            if batch_job.id in self.running_batches:
                del self.running_batches[batch_job.id]
    
    async def execute_template_batch(
        self,
        template_name: str,
        template_variations: List[Dict[str, Any]],
        batch_name: Optional[str] = None
    ) -> str:
        """
        Execute a batch of requests using the same template with different variables
        
        Args:
            template_name: Name of the template to use
            template_variations: List of template variable sets
            batch_name: Optional batch name
        
        Returns:
            Batch job ID
        """
        batch_name = batch_name or f"template_batch_{template_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create requests from template variations
        requests = []
        for i, variables in enumerate(template_variations):
            request = {
                "prompt": f"Use template '{template_name}' with variables: {json.dumps(variables)}",
                "context": {
                    "template_name": template_name,
                    "template_variables": variables,
                    "variation_index": i
                },
                "metadata": {
                    "template_name": template_name,
                    "variation_index": i
                }
            }
            requests.append(request)
        
        # Create and submit batch
        return await self.create_and_submit_batch(batch_name, requests, {
            "template_name": template_name,
            "total_variations": len(template_variations)
        })
    
    async def retry_failed_requests(self, batch_id: str) -> str:
        """
        Retry failed requests from a batch job
        
        Args:
            batch_id: Original batch job ID
        
        Returns:
            New batch job ID for retry
        """
        if batch_id not in self.batch_jobs:
            raise ValueError(f"Batch job not found: {batch_id}")
        
        original_batch = self.batch_jobs[batch_id]
        
        # Find failed requests
        failed_requests = []
        for request in original_batch.requests:
            if request.id in original_batch.errors:
                failed_requests.append({
                    "prompt": request.prompt,
                    "context": request.context,
                    "priority": request.priority.value,
                    "timeout_seconds": request.timeout_seconds,
                    "metadata": {**request.metadata, "retry_of": request.id}
                })
        
        if not failed_requests:
            raise ValueError(f"No failed requests found in batch: {batch_id}")
        
        # Create retry batch
        retry_batch_name = f"{original_batch.name}_retry"
        return await self.create_and_submit_batch(
            retry_batch_name,
            failed_requests,
            {
                "original_batch_id": batch_id,
                "retry_count": original_batch.metadata.get("retry_count", 0) + 1
            }
        )


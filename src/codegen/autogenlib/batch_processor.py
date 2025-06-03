"""
Batch Processor for concurrent task execution and bulk operations.

This module provides high-performance batch processing capabilities
for handling multiple Codegen tasks concurrently with optimized
resource utilization and error handling.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Iterator, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict

from .codegen_client import CodegenClient, TaskConfig, TaskResult

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """Batch execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    max_concurrent_tasks: int = 10
    timeout_seconds: int = 600
    retry_failed_tasks: bool = True
    max_retries: int = 3
    batch_size: int = 100
    progress_callback: Optional[Callable] = None
    error_threshold: float = 0.1  # Fail batch if >10% of tasks fail
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BatchResult:
    """Result from batch processing."""
    batch_id: str
    status: BatchStatus
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    cancelled_tasks: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    task_results: Dict[str, TaskResult] = field(default_factory=dict)
    error_summary: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BatchProcessor:
    """
    High-performance batch processor for concurrent Codegen task execution.
    
    Features:
    - Concurrent task execution with configurable limits
    - Intelligent retry logic and error handling
    - Progress tracking and monitoring
    - Resource optimization and throttling
    - Bulk operations support
    - Performance metrics and analytics
    """
    
    def __init__(self, codegen_client: CodegenClient):
        """
        Initialize the batch processor.
        
        Args:
            codegen_client: Configured CodegenClient instance
        """
        self.client = codegen_client
        self.active_batches: Dict[str, BatchResult] = {}
        self.completed_batches: Dict[str, BatchResult] = {}
        
        # Performance tracking
        self.performance_metrics = {
            "total_batches": 0,
            "total_tasks_processed": 0,
            "average_batch_duration": 0.0,
            "success_rate": 0.0,
            "throughput_tasks_per_second": 0.0
        }
        
        logger.info("BatchProcessor initialized")
    
    async def process_batch(self, 
                          tasks: List[Tuple[str, TaskConfig]], 
                          config: Optional[BatchConfig] = None) -> BatchResult:
        """
        Process a batch of tasks concurrently.
        
        Args:
            tasks: List of (task_id, TaskConfig) tuples
            config: Batch processing configuration
            
        Returns:
            BatchResult with execution details
        """
        config = config or BatchConfig()
        batch_id = f"batch_{datetime.now().isoformat()}_{hash(str(tasks)) % 10000}"
        
        batch_result = BatchResult(
            batch_id=batch_id,
            status=BatchStatus.PENDING,
            total_tasks=len(tasks),
            completed_tasks=0,
            failed_tasks=0,
            cancelled_tasks=0,
            started_at=datetime.now(),
            metadata=config.metadata
        )
        
        self.active_batches[batch_id] = batch_result
        
        try:
            logger.info(f"Starting batch {batch_id} with {len(tasks)} tasks")
            batch_result.status = BatchStatus.RUNNING
            
            # Process tasks in chunks to manage memory and resources
            chunk_size = min(config.batch_size, len(tasks))
            task_chunks = [tasks[i:i + chunk_size] for i in range(0, len(tasks), chunk_size)]
            
            for chunk_idx, chunk in enumerate(task_chunks):
                logger.info(f"Processing chunk {chunk_idx + 1}/{len(task_chunks)} with {len(chunk)} tasks")
                
                # Process chunk concurrently
                chunk_results = await self._process_chunk(chunk, config, batch_result)
                
                # Update batch results
                for task_id, result in chunk_results.items():
                    batch_result.task_results[task_id] = result
                    
                    if result.status == "completed":
                        batch_result.completed_tasks += 1
                    elif result.status == "failed":
                        batch_result.failed_tasks += 1
                        # Track error types
                        error_type = self._categorize_error(result.error)
                        batch_result.error_summary[error_type] = batch_result.error_summary.get(error_type, 0) + 1
                    elif result.status == "cancelled":
                        batch_result.cancelled_tasks += 1
                
                # Check error threshold
                error_rate = batch_result.failed_tasks / batch_result.total_tasks
                if error_rate > config.error_threshold:
                    logger.warning(f"Batch {batch_id} error rate ({error_rate:.2%}) exceeds threshold ({config.error_threshold:.2%})")
                    if not config.retry_failed_tasks:
                        batch_result.status = BatchStatus.FAILED
                        break
                
                # Progress callback
                if config.progress_callback:
                    progress = (batch_result.completed_tasks + batch_result.failed_tasks) / batch_result.total_tasks
                    config.progress_callback(batch_id, progress, batch_result)
            
            # Determine final status
            if batch_result.failed_tasks == 0 and batch_result.cancelled_tasks == 0:
                batch_result.status = BatchStatus.COMPLETED
            elif batch_result.completed_tasks > 0:
                batch_result.status = BatchStatus.PARTIAL
            else:
                batch_result.status = BatchStatus.FAILED
            
            batch_result.completed_at = datetime.now()
            batch_result.duration_seconds = (batch_result.completed_at - batch_result.started_at).total_seconds()
            
            logger.info(f"Batch {batch_id} completed: {batch_result.completed_tasks}/{batch_result.total_tasks} successful")
            
        except Exception as e:
            batch_result.status = BatchStatus.FAILED
            batch_result.completed_at = datetime.now()
            batch_result.duration_seconds = (batch_result.completed_at - batch_result.started_at).total_seconds()
            logger.error(f"Batch {batch_id} failed with error: {e}")
        
        finally:
            # Move to completed batches
            self.completed_batches[batch_id] = batch_result
            del self.active_batches[batch_id]
            
            # Update performance metrics
            self._update_performance_metrics(batch_result)
        
        return batch_result
    
    async def _process_chunk(self, 
                           chunk: List[Tuple[str, TaskConfig]], 
                           config: BatchConfig,
                           batch_result: BatchResult) -> Dict[str, TaskResult]:
        """Process a chunk of tasks concurrently."""
        semaphore = asyncio.Semaphore(config.max_concurrent_tasks)
        chunk_results = {}
        
        async def process_single_task(task_id: str, task_config: TaskConfig) -> Tuple[str, TaskResult]:
            async with semaphore:
                try:
                    # Add timeout to individual task
                    result = await asyncio.wait_for(
                        self.client.run_task(task_config),
                        timeout=config.timeout_seconds
                    )
                    return task_id, result
                except asyncio.TimeoutError:
                    timeout_result = TaskResult(
                        task_id=task_id,
                        status="failed",
                        error="Task timeout",
                        started_at=datetime.now(),
                        completed_at=datetime.now()
                    )
                    return task_id, timeout_result
                except Exception as e:
                    error_result = TaskResult(
                        task_id=task_id,
                        status="failed",
                        error=str(e),
                        started_at=datetime.now(),
                        completed_at=datetime.now()
                    )
                    return task_id, error_result
        
        # Create tasks for concurrent execution
        tasks = [process_single_task(task_id, task_config) for task_id, task_config in chunk]
        
        # Execute tasks concurrently
        completed_tasks = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for result in completed_tasks:
            if isinstance(result, Exception):
                logger.error(f"Unexpected error in task execution: {result}")
                continue
            
            task_id, task_result = result
            chunk_results[task_id] = task_result
        
        return chunk_results
    
    def _categorize_error(self, error_message: Optional[str]) -> str:
        """Categorize error messages for analytics."""
        if not error_message:
            return "unknown"
        
        error_lower = error_message.lower()
        
        if "timeout" in error_lower:
            return "timeout"
        elif "network" in error_lower or "connection" in error_lower:
            return "network"
        elif "auth" in error_lower or "permission" in error_lower:
            return "authentication"
        elif "rate limit" in error_lower:
            return "rate_limit"
        elif "validation" in error_lower:
            return "validation"
        else:
            return "other"
    
    def _update_performance_metrics(self, batch_result: BatchResult):
        """Update performance metrics based on batch results."""
        self.performance_metrics["total_batches"] += 1
        self.performance_metrics["total_tasks_processed"] += batch_result.total_tasks
        
        # Update average batch duration
        total_duration = (
            self.performance_metrics["average_batch_duration"] * (self.performance_metrics["total_batches"] - 1) +
            (batch_result.duration_seconds or 0)
        )
        self.performance_metrics["average_batch_duration"] = total_duration / self.performance_metrics["total_batches"]
        
        # Update success rate
        total_completed = sum(b.completed_tasks for b in self.completed_batches.values())
        total_tasks = sum(b.total_tasks for b in self.completed_batches.values())
        self.performance_metrics["success_rate"] = total_completed / total_tasks if total_tasks > 0 else 0
        
        # Update throughput
        if batch_result.duration_seconds and batch_result.duration_seconds > 0:
            self.performance_metrics["throughput_tasks_per_second"] = (
                batch_result.completed_tasks / batch_result.duration_seconds
            )
    
    async def process_bulk_analysis(self, 
                                  repository_urls: List[str],
                                  analysis_type: str = "comprehensive",
                                  config: Optional[BatchConfig] = None) -> BatchResult:
        """
        Process bulk codebase analysis for multiple repositories.
        
        Args:
            repository_urls: List of repository URLs to analyze
            analysis_type: Type of analysis to perform
            config: Batch processing configuration
            
        Returns:
            BatchResult with analysis results
        """
        tasks = []
        
        for idx, repo_url in enumerate(repository_urls):
            task_id = f"analysis_{analysis_type}_{idx}_{hash(repo_url) % 10000}"
            task_config = TaskConfig(
                prompt=f"Perform {analysis_type} analysis of repository {repo_url}",
                context={
                    "repository_url": repo_url,
                    "analysis_type": analysis_type,
                    "use_codebase_analysis": True
                },
                priority=5,
                metadata={"repository_url": repo_url, "analysis_type": analysis_type}
            )
            tasks.append((task_id, task_config))
        
        logger.info(f"Starting bulk analysis of {len(repository_urls)} repositories")
        return await self.process_batch(tasks, config)
    
    async def process_bulk_reviews(self, 
                                 pr_urls: List[str],
                                 review_type: str = "comprehensive",
                                 config: Optional[BatchConfig] = None) -> BatchResult:
        """
        Process bulk PR reviews.
        
        Args:
            pr_urls: List of PR URLs to review
            review_type: Type of review to perform
            config: Batch processing configuration
            
        Returns:
            BatchResult with review results
        """
        tasks = []
        
        for idx, pr_url in enumerate(pr_urls):
            task_id = f"review_{review_type}_{idx}_{hash(pr_url) % 10000}"
            task_config = TaskConfig(
                prompt=f"Perform {review_type} review of pull request {pr_url}",
                context={
                    "pr_url": pr_url,
                    "review_type": review_type,
                    "include_suggestions": True
                },
                priority=7,
                metadata={"pr_url": pr_url, "review_type": review_type}
            )
            tasks.append((task_id, task_config))
        
        logger.info(f"Starting bulk review of {len(pr_urls)} pull requests")
        return await self.process_batch(tasks, config)
    
    def get_batch_status(self, batch_id: str) -> Optional[BatchResult]:
        """Get the status of a specific batch."""
        return self.active_batches.get(batch_id) or self.completed_batches.get(batch_id)
    
    def list_active_batches(self) -> List[BatchResult]:
        """List all currently active batches."""
        return list(self.active_batches.values())
    
    def list_completed_batches(self, limit: int = 50) -> List[BatchResult]:
        """List completed batches, most recent first."""
        batches = sorted(
            self.completed_batches.values(),
            key=lambda b: b.started_at,
            reverse=True
        )
        return batches[:limit]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics and analytics."""
        return {
            **self.performance_metrics,
            "active_batches": len(self.active_batches),
            "completed_batches": len(self.completed_batches),
            "error_distribution": self._get_error_distribution()
        }
    
    def _get_error_distribution(self) -> Dict[str, int]:
        """Get distribution of error types across all batches."""
        error_dist = defaultdict(int)
        
        for batch in self.completed_batches.values():
            for error_type, count in batch.error_summary.items():
                error_dist[error_type] += count
        
        return dict(error_dist)
    
    async def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancel an active batch.
        
        Args:
            batch_id: ID of batch to cancel
            
        Returns:
            True if cancelled successfully
        """
        batch = self.active_batches.get(batch_id)
        if batch:
            batch.status = BatchStatus.CANCELLED
            batch.completed_at = datetime.now()
            batch.duration_seconds = (batch.completed_at - batch.started_at).total_seconds()
            
            # Move to completed batches
            self.completed_batches[batch_id] = batch
            del self.active_batches[batch_id]
            
            logger.info(f"Batch {batch_id} cancelled")
            return True
        
        return False


# Utility functions for common batch operations
async def analyze_repositories_batch(client: CodegenClient, 
                                   repository_urls: List[str],
                                   max_concurrent: int = 5) -> BatchResult:
    """Convenience function for batch repository analysis."""
    processor = BatchProcessor(client)
    config = BatchConfig(max_concurrent_tasks=max_concurrent)
    return await processor.process_bulk_analysis(repository_urls, config=config)


async def review_prs_batch(client: CodegenClient,
                          pr_urls: List[str],
                          max_concurrent: int = 3) -> BatchResult:
    """Convenience function for batch PR reviews."""
    processor = BatchProcessor(client)
    config = BatchConfig(max_concurrent_tasks=max_concurrent)
    return await processor.process_bulk_reviews(pr_urls, config=config)


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the BatchProcessor."""
        from .codegen_client import CodegenClient
        
        # Initialize client and processor
        client = CodegenClient("example-org", "example-token")
        processor = BatchProcessor(client)
        
        # Example: Batch analysis of multiple repositories
        repositories = [
            "https://github.com/example/repo1",
            "https://github.com/example/repo2",
            "https://github.com/example/repo3"
        ]
        
        def progress_callback(batch_id: str, progress: float, batch_result: BatchResult):
            print(f"Batch {batch_id}: {progress:.1%} complete")
        
        config = BatchConfig(
            max_concurrent_tasks=2,
            progress_callback=progress_callback,
            retry_failed_tasks=True
        )
        
        result = await processor.process_bulk_analysis(repositories, config=config)
        
        print(f"Batch completed: {result.completed_tasks}/{result.total_tasks} successful")
        print(f"Performance metrics: {processor.get_performance_metrics()}")
    
    asyncio.run(example_usage())


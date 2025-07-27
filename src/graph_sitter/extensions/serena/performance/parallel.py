"""
Parallel Processing System for Serena Analysis

This module provides parallel processing capabilities to speed up analysis
operations across multiple files and large codebases.
"""

import asyncio
import concurrent.futures
import multiprocessing
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from queue import Queue, Empty

from ..serena_types import SerenaConfig


@dataclass
class AnalysisTask:
    """Represents a single analysis task."""
    task_id: str
    operation: str
    file_path: str
    parameters: Dict[str, Any]
    priority: int = 0
    
    def __lt__(self, other):
        return self.priority > other.priority  # Higher priority first


@dataclass 
class AnalysisResult:
    """Represents the result of an analysis task."""
    task_id: str
    operation: str
    file_path: str
    result: Any
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: float = 0.0


class ParallelAnalyzer:
    """
    High-performance parallel analyzer for Serena operations.
    
    Features:
    - Thread-based and process-based parallelism
    - Task prioritization and queuing
    - Progress tracking and monitoring
    - Error handling and recovery
    - Resource management
    """
    
    def __init__(self,
                 max_workers: Optional[int] = None,
                 use_processes: bool = False,
                 queue_size: int = 1000):
        self.max_workers = max_workers or min(32, (multiprocessing.cpu_count() or 1) + 4)
        self.use_processes = use_processes
        self.queue_size = queue_size
        
        self._executor: Optional[Union[ThreadPoolExecutor, ProcessPoolExecutor]] = None
        self._task_queue: Queue = Queue(maxsize=queue_size)
        self._results: Dict[str, AnalysisResult] = {}
        self._active_tasks: Dict[str, concurrent.futures.Future] = {}
        self._stats = {
            'submitted': 0,
            'completed': 0,
            'failed': 0,
            'total_duration': 0.0
        }
        self._lock = threading.RLock()
        self._shutdown = False
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
    
    def start(self):
        """Start the parallel analyzer."""
        if self._executor is not None:
            return
        
        if self.use_processes:
            self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        self._shutdown = False
    
    def shutdown(self, wait: bool = True):
        """Shutdown the parallel analyzer."""
        self._shutdown = True
        
        if self._executor is not None:
            self._executor.shutdown(wait=wait)
            self._executor = None
        
        # Cancel any remaining active tasks
        with self._lock:
            for future in self._active_tasks.values():
                future.cancel()
            self._active_tasks.clear()
    
    def submit_task(self, task: AnalysisTask, 
                   analysis_func: Callable) -> str:
        """Submit an analysis task for parallel execution."""
        if self._shutdown or self._executor is None:
            raise RuntimeError("Analyzer is not running")
        
        start_time = time.time()
        
        def wrapped_analysis():
            try:
                result = analysis_func(task.file_path, **task.parameters)
                duration = time.time() - start_time
                
                analysis_result = AnalysisResult(
                    task_id=task.task_id,
                    operation=task.operation,
                    file_path=task.file_path,
                    result=result,
                    duration=duration,
                    timestamp=time.time()
                )
                
                with self._lock:
                    self._results[task.task_id] = analysis_result
                    self._stats['completed'] += 1
                    self._stats['total_duration'] += duration
                    if task.task_id in self._active_tasks:
                        del self._active_tasks[task.task_id]
                
                return analysis_result
                
            except Exception as e:
                duration = time.time() - start_time
                
                error_result = AnalysisResult(
                    task_id=task.task_id,
                    operation=task.operation,
                    file_path=task.file_path,
                    result=None,
                    error=str(e),
                    duration=duration,
                    timestamp=time.time()
                )
                
                with self._lock:
                    self._results[task.task_id] = error_result
                    self._stats['failed'] += 1
                    self._stats['total_duration'] += duration
                    if task.task_id in self._active_tasks:
                        del self._active_tasks[task.task_id]
                
                return error_result
        
        future = self._executor.submit(wrapped_analysis)
        
        with self._lock:
            self._active_tasks[task.task_id] = future
            self._stats['submitted'] += 1
        
        return task.task_id
    
    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[AnalysisResult]:
        """Get the result of a specific task."""
        # Check if result is already available
        with self._lock:
            if task_id in self._results:
                return self._results[task_id]
            
            if task_id not in self._active_tasks:
                return None
            
            future = self._active_tasks[task_id]
        
        try:
            # Wait for the future to complete
            result = future.result(timeout=timeout)
            return result
        except concurrent.futures.TimeoutError:
            return None
        except Exception:
            return None
    
    def get_all_results(self, timeout: Optional[float] = None) -> List[AnalysisResult]:
        """Get all completed results."""
        with self._lock:
            results = list(self._results.values())
            
            # Wait for any remaining active tasks
            if self._active_tasks and timeout is not None:
                remaining_futures = list(self._active_tasks.values())
                
                try:
                    concurrent.futures.wait(
                        remaining_futures, 
                        timeout=timeout,
                        return_when=concurrent.futures.ALL_COMPLETED
                    )
                except Exception:
                    pass
                
                # Collect any new results
                results = list(self._results.values())
        
        return results
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all submitted tasks to complete."""
        with self._lock:
            if not self._active_tasks:
                return True
            
            futures = list(self._active_tasks.values())
        
        try:
            done, not_done = concurrent.futures.wait(
                futures,
                timeout=timeout,
                return_when=concurrent.futures.ALL_COMPLETED
            )
            return len(not_done) == 0
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._lock:
            avg_duration = (
                self._stats['total_duration'] / self._stats['completed']
                if self._stats['completed'] > 0 else 0
            )
            
            return {
                'submitted': self._stats['submitted'],
                'completed': self._stats['completed'],
                'failed': self._stats['failed'],
                'active': len(self._active_tasks),
                'success_rate': (
                    self._stats['completed'] / 
                    (self._stats['completed'] + self._stats['failed'])
                    if (self._stats['completed'] + self._stats['failed']) > 0 else 0
                ),
                'average_duration': avg_duration,
                'total_duration': self._stats['total_duration'],
                'max_workers': self.max_workers,
                'use_processes': self.use_processes
            }


def parallel_analysis(operation: str, 
                     analysis_func: Callable,
                     file_paths: List[str],
                     parameters: Optional[Dict[str, Any]] = None,
                     max_workers: Optional[int] = None,
                     use_processes: bool = False,
                     timeout: Optional[float] = None) -> List[AnalysisResult]:
    """
    Perform parallel analysis on multiple files.
    
    Args:
        operation: Name of the analysis operation
        analysis_func: Function to perform analysis
        file_paths: List of file paths to analyze
        parameters: Common parameters for all analyses
        max_workers: Maximum number of parallel workers
        use_processes: Whether to use process-based parallelism
        timeout: Timeout for all operations
    
    Returns:
        List of analysis results
    """
    parameters = parameters or {}
    
    with ParallelAnalyzer(max_workers=max_workers, use_processes=use_processes) as analyzer:
        # Submit all tasks
        task_ids = []
        for i, file_path in enumerate(file_paths):
            task = AnalysisTask(
                task_id=f"{operation}_{i}",
                operation=operation,
                file_path=file_path,
                parameters=parameters
            )
            task_id = analyzer.submit_task(task, analysis_func)
            task_ids.append(task_id)
        
        # Wait for completion
        analyzer.wait_for_completion(timeout=timeout)
        
        # Collect results
        results = []
        for task_id in task_ids:
            result = analyzer.get_result(task_id)
            if result:
                results.append(result)
        
        return results


def batch_analyze_files(analysis_functions: Dict[str, Callable],
                       file_paths: List[str],
                       parameters: Optional[Dict[str, Dict[str, Any]]] = None,
                       max_workers: Optional[int] = None,
                       use_processes: bool = False,
                       timeout: Optional[float] = None) -> Dict[str, List[AnalysisResult]]:
    """
    Perform multiple types of analysis on multiple files in parallel.
    
    Args:
        analysis_functions: Dict mapping operation names to analysis functions
        file_paths: List of file paths to analyze
        parameters: Dict mapping operation names to their parameters
        max_workers: Maximum number of parallel workers
        use_processes: Whether to use process-based parallelism
        timeout: Timeout for all operations
    
    Returns:
        Dict mapping operation names to their results
    """
    parameters = parameters or {}
    results = {}
    
    with ParallelAnalyzer(max_workers=max_workers, use_processes=use_processes) as analyzer:
        # Submit all tasks
        task_mapping = {}  # Maps task_id to (operation, file_index)
        
        for operation, analysis_func in analysis_functions.items():
            operation_params = parameters.get(operation, {})
            
            for i, file_path in enumerate(file_paths):
                task = AnalysisTask(
                    task_id=f"{operation}_{i}",
                    operation=operation,
                    file_path=file_path,
                    parameters=operation_params
                )
                task_id = analyzer.submit_task(task, analysis_func)
                task_mapping[task_id] = (operation, i)
        
        # Wait for completion
        analyzer.wait_for_completion(timeout=timeout)
        
        # Organize results by operation
        for operation in analysis_functions.keys():
            results[operation] = []
        
        for task_id, (operation, file_index) in task_mapping.items():
            result = analyzer.get_result(task_id)
            if result:
                results[operation].append(result)
        
        # Sort results by file index to maintain order
        for operation in results:
            results[operation].sort(key=lambda r: file_paths.index(r.file_path))
    
    return results


class AsyncAnalyzer:
    """
    Async-based analyzer for I/O intensive operations.
    Complements the parallel analyzer for different use cases.
    """
    
    def __init__(self, max_concurrent: int = 50):
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._stats = {
            'submitted': 0,
            'completed': 0,
            'failed': 0
        }
    
    async def analyze_file(self, 
                          operation: str,
                          file_path: str,
                          analysis_func: Callable,
                          **kwargs) -> AnalysisResult:
        """Analyze a single file asynchronously."""
        async with self._semaphore:
            start_time = time.time()
            task_id = f"{operation}_{hash(file_path)}"
            
            try:
                self._stats['submitted'] += 1
                
                # Run the analysis function
                if asyncio.iscoroutinefunction(analysis_func):
                    result = await analysis_func(file_path, **kwargs)
                else:
                    # Run sync function in thread pool
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, lambda: analysis_func(file_path, **kwargs)
                    )
                
                duration = time.time() - start_time
                self._stats['completed'] += 1
                
                return AnalysisResult(
                    task_id=task_id,
                    operation=operation,
                    file_path=file_path,
                    result=result,
                    duration=duration,
                    timestamp=time.time()
                )
                
            except Exception as e:
                duration = time.time() - start_time
                self._stats['failed'] += 1
                
                return AnalysisResult(
                    task_id=task_id,
                    operation=operation,
                    file_path=file_path,
                    result=None,
                    error=str(e),
                    duration=duration,
                    timestamp=time.time()
                )
    
    async def analyze_files(self,
                           operation: str,
                           file_paths: List[str],
                           analysis_func: Callable,
                           **kwargs) -> List[AnalysisResult]:
        """Analyze multiple files asynchronously."""
        tasks = [
            self.analyze_file(operation, file_path, analysis_func, **kwargs)
            for file_path in file_paths
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=False)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get async analyzer statistics."""
        return {
            'max_concurrent': self.max_concurrent,
            'submitted': self._stats['submitted'],
            'completed': self._stats['completed'],
            'failed': self._stats['failed'],
            'success_rate': (
                self._stats['completed'] / 
                (self._stats['completed'] + self._stats['failed'])
                if (self._stats['completed'] + self._stats['failed']) > 0 else 0
            )
        }


"""
Memory Optimization System for Serena Analysis

This module provides memory optimization techniques to handle large codebases
efficiently while maintaining analysis quality and performance.
"""

import gc
import psutil
import sys
import weakref
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional, Set, Union
import threading
import time
from pathlib import Path

from ..serena_types import SerenaConfig


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    process_memory_mb: float
    memory_percent: float
    gc_collections: Dict[int, int]
    timestamp: float


class MemoryOptimizer:
    """
    Memory optimization system for Serena analysis operations.
    
    Features:
    - Memory usage monitoring and alerts
    - Automatic garbage collection optimization
    - Memory-efficient data structures
    - Streaming analysis for large files
    - Memory pressure detection and response
    """
    
    def __init__(self,
                 memory_limit_mb: Optional[float] = None,
                 gc_threshold_mb: float = 100.0,
                 enable_monitoring: bool = True):
        self.memory_limit_mb = memory_limit_mb or (psutil.virtual_memory().total / (1024**2) * 0.8)
        self.gc_threshold_mb = gc_threshold_mb
        self.enable_monitoring = enable_monitoring
        
        self._process = psutil.Process()
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_active = False
        self._memory_alerts: List[Dict[str, Any]] = []
        self._weak_refs: Set[weakref.ref] = set()
        self._lock = threading.RLock()
        
        # Configure garbage collection
        self._configure_gc()
    
    def _configure_gc(self):
        """Configure garbage collection for optimal performance."""
        # Adjust GC thresholds for better performance
        gc.set_threshold(700, 10, 10)  # More aggressive collection
        
        # Enable automatic garbage collection
        if not gc.isenabled():
            gc.enable()
    
    def start_monitoring(self, interval: float = 5.0):
        """Start memory monitoring in background thread."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitor_memory,
            args=(interval,),
            daemon=True
        )
        self._monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=1.0)
            self._monitoring_thread = None
    
    def _monitor_memory(self, interval: float):
        """Background memory monitoring loop."""
        while self._monitoring_active:
            try:
                stats = self.get_memory_stats()
                
                # Check for memory pressure
                if stats.process_memory_mb > self.memory_limit_mb * 0.9:
                    self._handle_memory_pressure(stats)
                
                # Trigger GC if needed
                if stats.process_memory_mb > self.gc_threshold_mb:
                    self._trigger_gc()
                
                time.sleep(interval)
                
            except Exception as e:
                # Log error but continue monitoring
                print(f"Memory monitoring error: {e}")
                time.sleep(interval)
    
    def _handle_memory_pressure(self, stats: MemoryStats):
        """Handle high memory usage situations."""
        with self._lock:
            alert = {
                'timestamp': time.time(),
                'memory_mb': stats.process_memory_mb,
                'limit_mb': self.memory_limit_mb,
                'action': 'memory_pressure_detected'
            }
            self._memory_alerts.append(alert)
            
            # Keep only recent alerts
            cutoff_time = time.time() - 3600  # 1 hour
            self._memory_alerts = [
                a for a in self._memory_alerts 
                if a['timestamp'] > cutoff_time
            ]
        
        # Trigger aggressive cleanup
        self._trigger_gc()
        self._cleanup_weak_refs()
    
    def _trigger_gc(self):
        """Trigger garbage collection."""
        collected = gc.collect()
        return collected
    
    def _cleanup_weak_refs(self):
        """Clean up dead weak references."""
        with self._lock:
            dead_refs = {ref for ref in self._weak_refs if ref() is None}
            self._weak_refs -= dead_refs
    
    def get_memory_stats(self) -> MemoryStats:
        """Get current memory usage statistics."""
        # System memory
        vm = psutil.virtual_memory()
        
        # Process memory
        process_info = self._process.memory_info()
        
        # GC stats
        gc_stats = {}
        for i in range(3):
            gc_stats[i] = gc.get_count()[i]
        
        return MemoryStats(
            total_memory_mb=vm.total / (1024**2),
            available_memory_mb=vm.available / (1024**2),
            used_memory_mb=vm.used / (1024**2),
            process_memory_mb=process_info.rss / (1024**2),
            memory_percent=vm.percent,
            gc_collections=gc_stats,
            timestamp=time.time()
        )
    
    def register_object(self, obj: Any) -> weakref.ref:
        """Register an object for memory tracking."""
        def cleanup_callback(ref):
            with self._lock:
                self._weak_refs.discard(ref)
        
        weak_ref = weakref.ref(obj, cleanup_callback)
        
        with self._lock:
            self._weak_refs.add(weak_ref)
        
        return weak_ref
    
    def get_tracked_objects_count(self) -> int:
        """Get count of tracked objects."""
        with self._lock:
            # Clean up dead references first
            self._cleanup_weak_refs()
            return len(self._weak_refs)
    
    def get_memory_alerts(self) -> List[Dict[str, Any]]:
        """Get recent memory alerts."""
        with self._lock:
            return list(self._memory_alerts)
    
    def clear_alerts(self):
        """Clear memory alerts."""
        with self._lock:
            self._memory_alerts.clear()


# Global memory optimizer instance
_global_optimizer: Optional[MemoryOptimizer] = None
_optimizer_lock = threading.RLock()


def get_memory_optimizer() -> MemoryOptimizer:
    """Get or create the global memory optimizer."""
    global _global_optimizer
    
    with _optimizer_lock:
        if _global_optimizer is None:
            _global_optimizer = MemoryOptimizer()
            _global_optimizer.start_monitoring()
        return _global_optimizer


def get_memory_stats() -> MemoryStats:
    """Get current memory statistics."""
    optimizer = get_memory_optimizer()
    return optimizer.get_memory_stats()


@contextmanager
def memory_efficient_analysis(enable_gc: bool = True,
                            gc_frequency: int = 100) -> Generator[Any, None, None]:
    """
    Context manager for memory-efficient analysis operations.
    
    Args:
        enable_gc: Whether to enable automatic garbage collection
        gc_frequency: How often to trigger GC (every N operations)
    
    Usage:
        with memory_efficient_analysis() as optimizer:
            for file in large_file_list:
                analyze_file(file)
    """
    optimizer = get_memory_optimizer()
    initial_stats = optimizer.get_memory_stats()
    
    operation_count = 0
    
    class MemoryContext:
        def __init__(self, opt: MemoryOptimizer):
            self.optimizer = opt
            self.operation_count = 0
        
        def checkpoint(self):
            """Manual checkpoint for memory optimization."""
            nonlocal operation_count
            operation_count += 1
            
            if enable_gc and operation_count % gc_frequency == 0:
                collected = gc.collect()
                if collected > 0:
                    print(f"GC collected {collected} objects")
        
        def get_stats(self) -> MemoryStats:
            return self.optimizer.get_memory_stats()
    
    context = MemoryContext(optimizer)
    
    try:
        yield context
    finally:
        # Final cleanup
        if enable_gc:
            gc.collect()
        
        final_stats = optimizer.get_memory_stats()
        memory_delta = final_stats.process_memory_mb - initial_stats.process_memory_mb
        
        if abs(memory_delta) > 10:  # Significant memory change
            print(f"Memory usage changed by {memory_delta:.1f} MB")


def optimize_memory_usage(target_mb: Optional[float] = None) -> Dict[str, Any]:
    """
    Optimize current memory usage.
    
    Args:
        target_mb: Target memory usage in MB (optional)
    
    Returns:
        Dict with optimization results
    """
    initial_stats = get_memory_stats()
    
    # Trigger garbage collection
    collected_objects = gc.collect()
    
    # Clean up optimizer weak references
    optimizer = get_memory_optimizer()
    optimizer._cleanup_weak_refs()
    
    final_stats = get_memory_stats()
    
    memory_freed = initial_stats.process_memory_mb - final_stats.process_memory_mb
    
    result = {
        'initial_memory_mb': initial_stats.process_memory_mb,
        'final_memory_mb': final_stats.process_memory_mb,
        'memory_freed_mb': memory_freed,
        'objects_collected': collected_objects,
        'target_achieved': True
    }
    
    if target_mb is not None:
        result['target_achieved'] = final_stats.process_memory_mb <= target_mb
        result['target_mb'] = target_mb
    
    return result


class StreamingAnalyzer:
    """
    Memory-efficient streaming analyzer for large files.
    Processes files in chunks to minimize memory usage.
    """
    
    def __init__(self, chunk_size: int = 8192, max_memory_mb: float = 50.0):
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb
        self._optimizer = get_memory_optimizer()
    
    def analyze_file_streaming(self, 
                             file_path: Union[str, Path],
                             analysis_func: callable,
                             **kwargs) -> Generator[Any, None, None]:
        """
        Analyze a file in streaming fashion.
        
        Args:
            file_path: Path to the file to analyze
            analysis_func: Function to analyze each chunk
            **kwargs: Additional arguments for analysis function
        
        Yields:
            Analysis results for each chunk
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            chunk_num = 0
            
            while True:
                # Check memory usage
                stats = self._optimizer.get_memory_stats()
                if stats.process_memory_mb > self.max_memory_mb:
                    gc.collect()
                
                # Read chunk
                chunk = f.read(self.chunk_size)
                if not chunk:
                    break
                
                try:
                    # Analyze chunk
                    result = analysis_func(
                        chunk=chunk,
                        chunk_num=chunk_num,
                        file_path=str(file_path),
                        **kwargs
                    )
                    
                    yield result
                    
                except Exception as e:
                    yield {
                        'error': str(e),
                        'chunk_num': chunk_num,
                        'file_path': str(file_path)
                    }
                
                chunk_num += 1
                
                # Periodic cleanup
                if chunk_num % 100 == 0:
                    gc.collect()
    
    def analyze_files_streaming(self,
                              file_paths: List[Union[str, Path]],
                              analysis_func: callable,
                              **kwargs) -> Generator[Any, None, None]:
        """
        Analyze multiple files in streaming fashion.
        
        Args:
            file_paths: List of file paths to analyze
            analysis_func: Function to analyze each chunk
            **kwargs: Additional arguments for analysis function
        
        Yields:
            Analysis results for each chunk from all files
        """
        for file_path in file_paths:
            yield from self.analyze_file_streaming(file_path, analysis_func, **kwargs)


def memory_efficient_batch_analysis(file_paths: List[str],
                                   analysis_func: callable,
                                   batch_size: int = 10,
                                   memory_limit_mb: float = 200.0,
                                   **kwargs) -> List[Any]:
    """
    Perform batch analysis with memory efficiency.
    
    Args:
        file_paths: List of file paths to analyze
        analysis_func: Analysis function to apply
        batch_size: Number of files to process in each batch
        memory_limit_mb: Memory limit for the operation
        **kwargs: Additional arguments for analysis function
    
    Returns:
        List of analysis results
    """
    results = []
    optimizer = get_memory_optimizer()
    
    # Process files in batches
    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i + batch_size]
        
        # Check memory before processing batch
        stats = optimizer.get_memory_stats()
        if stats.process_memory_mb > memory_limit_mb * 0.8:
            # Trigger cleanup before processing
            optimize_memory_usage()
        
        # Process batch
        batch_results = []
        for file_path in batch:
            try:
                result = analysis_func(file_path, **kwargs)
                batch_results.append(result)
            except Exception as e:
                batch_results.append({
                    'error': str(e),
                    'file_path': file_path
                })
        
        results.extend(batch_results)
        
        # Cleanup after batch
        if i % (batch_size * 5) == 0:  # Every 5 batches
            gc.collect()
    
    return results

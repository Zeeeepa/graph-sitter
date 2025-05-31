"""
Advanced Profiler

Comprehensive profiling system for performance analysis and optimization insights.
"""

import cProfile
import io
import json
import pstats
import sys
import threading
import time
import tracemalloc
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class ProfilerType(Enum):
    """Types of profiling"""
    CPU = auto()
    MEMORY = auto()
    IO = auto()
    NETWORK = auto()
    CUSTOM = auto()


class ProfilerMode(Enum):
    """Profiling modes"""
    SAMPLING = auto()      # Sample-based profiling
    DETERMINISTIC = auto() # Deterministic profiling
    STATISTICAL = auto()   # Statistical profiling


@dataclass
class ProfilerConfig:
    """Configuration for profiler"""
    enable_cpu_profiling: bool = True
    enable_memory_profiling: bool = True
    enable_io_profiling: bool = False
    enable_network_profiling: bool = False
    profiler_mode: ProfilerMode = ProfilerMode.SAMPLING
    sampling_interval: float = 0.01  # 10ms
    max_stack_depth: int = 50
    output_directory: str = "./profiles"
    auto_save: bool = True
    save_interval_seconds: float = 300.0  # 5 minutes
    max_profile_size_mb: int = 100
    enable_line_profiling: bool = False
    enable_function_profiling: bool = True


@dataclass
class ProfileData:
    """Profile data container"""
    profiler_type: ProfilerType
    start_time: float
    end_time: float
    duration: float
    function_name: str
    filename: str
    line_number: int
    call_count: int = 0
    total_time: float = 0.0
    cumulative_time: float = 0.0
    memory_usage: int = 0
    peak_memory: int = 0
    io_operations: int = 0
    network_operations: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class MemorySnapshot:
    """Memory usage snapshot"""
    timestamp: float
    current_memory: int
    peak_memory: int
    memory_percent: float
    tracemalloc_snapshot: Optional[Any] = None
    
    @classmethod
    def take_snapshot(cls) -> 'MemorySnapshot':
        """Take current memory snapshot"""
        current_memory = 0
        peak_memory = 0
        memory_percent = 0.0
        
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            memory_info = process.memory_info()
            current_memory = memory_info.rss
            peak_memory = memory_info.peak_wss if hasattr(memory_info, 'peak_wss') else memory_info.rss
            memory_percent = process.memory_percent()
        
        tracemalloc_snapshot = None
        if tracemalloc.is_tracing():
            tracemalloc_snapshot = tracemalloc.take_snapshot()
        
        return cls(
            timestamp=time.time(),
            current_memory=current_memory,
            peak_memory=peak_memory,
            memory_percent=memory_percent,
            tracemalloc_snapshot=tracemalloc_snapshot
        )


class CPUProfiler:
    """CPU profiling implementation"""
    
    def __init__(self, config: ProfilerConfig):
        self.config = config
        self.profiler: Optional[cProfile.Profile] = None
        self.is_profiling = False
        self._lock = threading.RLock()
    
    def start_profiling(self) -> None:
        """Start CPU profiling"""
        with self._lock:
            if not self.is_profiling:
                self.profiler = cProfile.Profile()
                self.profiler.enable()
                self.is_profiling = True
                logger.debug("CPU profiling started")
    
    def stop_profiling(self) -> Optional[pstats.Stats]:
        """Stop CPU profiling and return stats"""
        with self._lock:
            if self.is_profiling and self.profiler:
                self.profiler.disable()
                self.is_profiling = False
                
                # Create stats object
                stats_stream = io.StringIO()
                stats = pstats.Stats(self.profiler, stream=stats_stream)
                logger.debug("CPU profiling stopped")
                return stats
            return None
    
    @contextmanager
    def profile_context(self):
        """Context manager for CPU profiling"""
        self.start_profiling()
        try:
            yield
        finally:
            stats = self.stop_profiling()
            if stats and self.config.auto_save:
                self._save_cpu_profile(stats)
    
    def _save_cpu_profile(self, stats: pstats.Stats) -> None:
        """Save CPU profile to file"""
        try:
            output_dir = Path(self.config.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(time.time())
            filename = output_dir / f"cpu_profile_{timestamp}.prof"
            
            stats.dump_stats(str(filename))
            logger.info(f"CPU profile saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save CPU profile: {e}")


class MemoryProfiler:
    """Memory profiling implementation"""
    
    def __init__(self, config: ProfilerConfig):
        self.config = config
        self.snapshots: deque = deque(maxlen=1000)
        self.is_profiling = False
        self._lock = threading.RLock()
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start_profiling(self) -> None:
        """Start memory profiling"""
        with self._lock:
            if not self.is_profiling:
                # Start tracemalloc if not already started
                if not tracemalloc.is_tracing():
                    tracemalloc.start(self.config.max_stack_depth)
                
                self.is_profiling = True
                self._start_monitoring()
                logger.debug("Memory profiling started")
    
    def stop_profiling(self) -> List[MemorySnapshot]:
        """Stop memory profiling and return snapshots"""
        with self._lock:
            if self.is_profiling:
                self.is_profiling = False
                self._stop_monitoring()
                
                if self.config.auto_save:
                    self._save_memory_profile()
                
                logger.debug("Memory profiling stopped")
                return list(self.snapshots)
            return []
    
    def _start_monitoring(self) -> None:
        """Start background memory monitoring"""
        def monitor_loop():
            while self.is_profiling:
                try:
                    snapshot = MemorySnapshot.take_snapshot()
                    self.snapshots.append(snapshot)
                    time.sleep(self.config.sampling_interval)
                except Exception as e:
                    logger.error(f"Error in memory monitoring: {e}")
                    time.sleep(1)
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
    
    def _stop_monitoring(self) -> None:
        """Stop background memory monitoring"""
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
    
    def _save_memory_profile(self) -> None:
        """Save memory profile to file"""
        try:
            output_dir = Path(self.config.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(time.time())
            filename = output_dir / f"memory_profile_{timestamp}.json"
            
            # Convert snapshots to serializable format
            data = {
                'snapshots': [
                    {
                        'timestamp': snapshot.timestamp,
                        'current_memory': snapshot.current_memory,
                        'peak_memory': snapshot.peak_memory,
                        'memory_percent': snapshot.memory_percent
                    }
                    for snapshot in self.snapshots
                ],
                'summary': self._generate_memory_summary()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Memory profile saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save memory profile: {e}")
    
    def _generate_memory_summary(self) -> Dict[str, Any]:
        """Generate memory usage summary"""
        if not self.snapshots:
            return {}
        
        memory_values = [s.current_memory for s in self.snapshots]
        
        return {
            'min_memory': min(memory_values),
            'max_memory': max(memory_values),
            'avg_memory': sum(memory_values) / len(memory_values),
            'peak_memory': max(s.peak_memory for s in self.snapshots),
            'sample_count': len(self.snapshots)
        }
    
    @contextmanager
    def profile_context(self):
        """Context manager for memory profiling"""
        self.start_profiling()
        try:
            yield
        finally:
            self.stop_profiling()


class FunctionProfiler:
    """Function-level profiling"""
    
    def __init__(self, config: ProfilerConfig):
        self.config = config
        self.function_stats: Dict[str, ProfileData] = {}
        self.call_stack: deque = deque()
        self._lock = threading.RLock()
    
    def profile_function(self, 
                        name: str = None,
                        track_memory: bool = True,
                        track_io: bool = False) -> Callable[[F], F]:
        """Decorator to profile individual functions"""
        
        def decorator(func: F) -> F:
            func_name = name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self._execute_with_profiling(
                    func, func_name, track_memory, track_io, args, kwargs
                )
            
            return wrapper
        
        return decorator
    
    def _execute_with_profiling(self, 
                               func: Callable,
                               func_name: str,
                               track_memory: bool,
                               track_io: bool,
                               args: tuple,
                               kwargs: dict) -> Any:
        """Execute function with profiling"""
        start_time = time.perf_counter()
        start_memory = None
        
        if track_memory:
            start_memory = MemorySnapshot.take_snapshot()
        
        # Track call stack
        with self._lock:
            self.call_stack.append(func_name)
        
        try:
            result = func(*args, **kwargs)
            return result
            
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            end_memory = None
            if track_memory:
                end_memory = MemorySnapshot.take_snapshot()
            
            # Update function statistics
            with self._lock:
                self.call_stack.pop()
                self._update_function_stats(
                    func_name, duration, start_memory, end_memory, func
                )
    
    def _update_function_stats(self, 
                              func_name: str,
                              duration: float,
                              start_memory: Optional[MemorySnapshot],
                              end_memory: Optional[MemorySnapshot],
                              func: Callable) -> None:
        """Update function statistics"""
        if func_name not in self.function_stats:
            self.function_stats[func_name] = ProfileData(
                profiler_type=ProfilerType.CUSTOM,
                start_time=time.time(),
                end_time=time.time(),
                duration=0.0,
                function_name=func_name,
                filename=func.__code__.co_filename if hasattr(func, '__code__') else '',
                line_number=func.__code__.co_firstlineno if hasattr(func, '__code__') else 0
            )
        
        stats = self.function_stats[func_name]
        stats.call_count += 1
        stats.total_time += duration
        stats.cumulative_time += duration
        stats.end_time = time.time()
        
        if start_memory and end_memory:
            memory_delta = end_memory.current_memory - start_memory.current_memory
            stats.memory_usage += memory_delta
            stats.peak_memory = max(stats.peak_memory, end_memory.peak_memory)
    
    def get_function_stats(self) -> Dict[str, ProfileData]:
        """Get function profiling statistics"""
        with self._lock:
            return dict(self.function_stats)
    
    def get_top_functions(self, 
                         metric: str = "total_time",
                         limit: int = 10) -> List[ProfileData]:
        """Get top functions by specified metric"""
        with self._lock:
            sorted_functions = sorted(
                self.function_stats.values(),
                key=lambda x: getattr(x, metric, 0),
                reverse=True
            )
            return sorted_functions[:limit]
    
    def reset_stats(self) -> None:
        """Reset function statistics"""
        with self._lock:
            self.function_stats.clear()
            self.call_stack.clear()


class AdvancedProfiler:
    """Main advanced profiler coordinating all profiling types"""
    
    def __init__(self, config: ProfilerConfig = None):
        self.config = config or ProfilerConfig()
        
        self.cpu_profiler = CPUProfiler(self.config) if self.config.enable_cpu_profiling else None
        self.memory_profiler = MemoryProfiler(self.config) if self.config.enable_memory_profiling else None
        self.function_profiler = FunctionProfiler(self.config) if self.config.enable_function_profiling else None
        
        self.is_profiling = False
        self._auto_save_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
    
    def start_profiling(self, 
                       profile_types: List[ProfilerType] = None) -> None:
        """Start profiling with specified types"""
        with self._lock:
            if self.is_profiling:
                return
            
            types_to_profile = profile_types or [ProfilerType.CPU, ProfilerType.MEMORY]
            
            if ProfilerType.CPU in types_to_profile and self.cpu_profiler:
                self.cpu_profiler.start_profiling()
            
            if ProfilerType.MEMORY in types_to_profile and self.memory_profiler:
                self.memory_profiler.start_profiling()
            
            self.is_profiling = True
            
            if self.config.auto_save:
                self._start_auto_save()
            
            logger.info(f"Advanced profiling started with types: {[t.name for t in types_to_profile]}")
    
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop all profiling and return results"""
        with self._lock:
            if not self.is_profiling:
                return {}
            
            results = {}
            
            if self.cpu_profiler:
                cpu_stats = self.cpu_profiler.stop_profiling()
                if cpu_stats:
                    results['cpu'] = self._format_cpu_stats(cpu_stats)
            
            if self.memory_profiler:
                memory_snapshots = self.memory_profiler.stop_profiling()
                results['memory'] = self._format_memory_stats(memory_snapshots)
            
            if self.function_profiler:
                function_stats = self.function_profiler.get_function_stats()
                results['functions'] = {name: stats.to_dict() for name, stats in function_stats.items()}
            
            self.is_profiling = False
            self._stop_auto_save()
            
            logger.info("Advanced profiling stopped")
            return results
    
    def profile_function(self, 
                        name: str = None,
                        track_memory: bool = True,
                        track_io: bool = False) -> Callable[[F], F]:
        """Decorator for function profiling"""
        if self.function_profiler:
            return self.function_profiler.profile_function(name, track_memory, track_io)
        else:
            # Return no-op decorator if function profiling is disabled
            def no_op_decorator(func: F) -> F:
                return func
            return no_op_decorator
    
    @contextmanager
    def profile_context(self, profile_types: List[ProfilerType] = None):
        """Context manager for profiling"""
        self.start_profiling(profile_types)
        try:
            yield
        finally:
            results = self.stop_profiling()
            return results
    
    def _format_cpu_stats(self, stats: pstats.Stats) -> Dict[str, Any]:
        """Format CPU profiling statistics"""
        # Get top functions by cumulative time
        stats.sort_stats('cumulative')
        
        # Capture stats output
        output = io.StringIO()
        stats.print_stats(20, file=output)  # Top 20 functions
        
        return {
            'total_calls': stats.total_calls,
            'total_time': stats.total_tt,
            'top_functions': output.getvalue()
        }
    
    def _format_memory_stats(self, snapshots: List[MemorySnapshot]) -> Dict[str, Any]:
        """Format memory profiling statistics"""
        if not snapshots:
            return {}
        
        memory_values = [s.current_memory for s in snapshots]
        
        return {
            'min_memory': min(memory_values),
            'max_memory': max(memory_values),
            'avg_memory': sum(memory_values) / len(memory_values),
            'peak_memory': max(s.peak_memory for s in snapshots),
            'sample_count': len(snapshots),
            'memory_trend': self._calculate_memory_trend(memory_values)
        }
    
    def _calculate_memory_trend(self, memory_values: List[int]) -> str:
        """Calculate memory usage trend"""
        if len(memory_values) < 2:
            return "stable"
        
        start_avg = sum(memory_values[:len(memory_values)//4]) / (len(memory_values)//4)
        end_avg = sum(memory_values[-len(memory_values)//4:]) / (len(memory_values)//4)
        
        change_percent = ((end_avg - start_avg) / start_avg) * 100
        
        if change_percent > 10:
            return "increasing"
        elif change_percent < -10:
            return "decreasing"
        else:
            return "stable"
    
    def _start_auto_save(self) -> None:
        """Start auto-save thread"""
        def auto_save_loop():
            while self.is_profiling:
                time.sleep(self.config.save_interval_seconds)
                if self.is_profiling:
                    self._save_intermediate_results()
        
        self._auto_save_thread = threading.Thread(target=auto_save_loop, daemon=True)
        self._auto_save_thread.start()
    
    def _stop_auto_save(self) -> None:
        """Stop auto-save thread"""
        if self._auto_save_thread:
            self._auto_save_thread.join(timeout=5)
    
    def _save_intermediate_results(self) -> None:
        """Save intermediate profiling results"""
        try:
            output_dir = Path(self.config.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = int(time.time())
            
            # Save function stats
            if self.function_profiler:
                function_stats = self.function_profiler.get_function_stats()
                filename = output_dir / f"function_stats_{timestamp}.json"
                
                with open(filename, 'w') as f:
                    json.dump(
                        {name: stats.to_dict() for name, stats in function_stats.items()},
                        f, indent=2
                    )
            
            logger.debug(f"Intermediate profiling results saved at {timestamp}")
            
        except Exception as e:
            logger.error(f"Failed to save intermediate results: {e}")
    
    def get_profiling_summary(self) -> Dict[str, Any]:
        """Get comprehensive profiling summary"""
        summary = {
            'is_profiling': self.is_profiling,
            'config': {
                'cpu_profiling': self.config.enable_cpu_profiling,
                'memory_profiling': self.config.enable_memory_profiling,
                'function_profiling': self.config.enable_function_profiling,
                'sampling_interval': self.config.sampling_interval,
                'auto_save': self.config.auto_save
            }
        }
        
        if self.function_profiler:
            function_stats = self.function_profiler.get_function_stats()
            summary['function_count'] = len(function_stats)
            summary['top_functions'] = [
                stats.to_dict() for stats in 
                self.function_profiler.get_top_functions(limit=5)
            ]
        
        return summary


# Global profiler instance
_global_profiler: Optional[AdvancedProfiler] = None


def get_profiler(config: ProfilerConfig = None) -> AdvancedProfiler:
    """Get global profiler instance"""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = AdvancedProfiler(config)
    return _global_profiler


def profile_function(name: str = None,
                    track_memory: bool = True,
                    track_io: bool = False) -> Callable[[F], F]:
    """Global function profiling decorator"""
    profiler = get_profiler()
    return profiler.profile_function(name, track_memory, track_io)


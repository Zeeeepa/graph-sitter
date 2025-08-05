"""
Profiling utilities for graph-sitter operations.

Provides detailed profiling capabilities for identifying performance
bottlenecks and optimization opportunities in codebase operations.
"""

import cProfile
import pstats
import io
import time
import threading
from typing import Dict, Any, Optional, List, Callable, TypeVar
from dataclasses import dataclass
from contextlib import contextmanager
from functools import wraps
import logging

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


@dataclass
class ProfileResult:
    """Results from a profiling session."""
    operation_name: str
    duration: float
    function_stats: Dict[str, Any]
    top_functions: List[Dict[str, Any]]
    memory_profile: Optional[Dict[str, Any]] = None
    
    def get_summary(self) -> str:
        """Get a human-readable summary of the profile."""
        lines = [
            f"Profile Summary for: {self.operation_name}",
            f"Total Duration: {self.duration:.3f}s",
            f"Top Functions by Time:",
        ]
        
        for i, func in enumerate(self.top_functions[:10], 1):
            lines.append(
                f"  {i:2d}. {func['function']} - {func['cumulative_time']:.3f}s "
                f"({func['calls']} calls)"
            )
        
        return "\n".join(lines)


class CodebaseProfiler:
    """
    Profiler for graph-sitter codebase operations.
    
    Provides both statistical profiling and memory profiling
    capabilities with support for operation-specific analysis.
    """
    
    def __init__(self, enable_memory_profiling: bool = False):
        self.enable_memory_profiling = enable_memory_profiling
        self._profiles: Dict[str, List[ProfileResult]] = {}
        self._lock = threading.Lock()
        
        # Try to import memory profiler if enabled
        self._memory_profiler = None
        if enable_memory_profiling:
            try:
                import memory_profiler
                self._memory_profiler = memory_profiler
            except ImportError:
                logger.warning("memory_profiler not available, memory profiling disabled")
                self.enable_memory_profiling = False
    
    @contextmanager
    def profile_operation(self, operation_name: str):
        """Context manager for profiling an operation."""
        profiler = cProfile.Profile()
        start_time = time.time()
        
        # Start memory profiling if enabled
        memory_usage_before = None
        if self.enable_memory_profiling and self._memory_profiler:
            memory_usage_before = self._memory_profiler.memory_usage()[0]
        
        try:
            profiler.enable()
            yield
        finally:
            profiler.disable()
            end_time = time.time()
            
            # Get memory usage after
            memory_profile = None
            if self.enable_memory_profiling and self._memory_profiler and memory_usage_before:
                memory_usage_after = self._memory_profiler.memory_usage()[0]
                memory_profile = {
                    'before': memory_usage_before,
                    'after': memory_usage_after,
                    'delta': memory_usage_after - memory_usage_before,
                }
            
            # Process profiling results
            result = self._process_profile_results(
                operation_name,
                profiler,
                end_time - start_time,
                memory_profile
            )
            
            # Store results
            with self._lock:
                if operation_name not in self._profiles:
                    self._profiles[operation_name] = []
                self._profiles[operation_name].append(result)
    
    def _process_profile_results(self, 
                                operation_name: str,
                                profiler: cProfile.Profile,
                                duration: float,
                                memory_profile: Optional[Dict[str, Any]]) -> ProfileResult:
        """Process cProfile results into structured data."""
        # Capture stats
        stats_stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stats_stream)
        stats.sort_stats('cumulative')
        
        # Extract function statistics
        function_stats = {}
        top_functions = []
        
        for func_key, (cc, nc, tt, ct, callers) in stats.stats.items():
            filename, line_num, func_name = func_key
            
            func_info = {
                'function': f"{filename}:{line_num}({func_name})",
                'calls': nc,
                'total_time': tt,
                'cumulative_time': ct,
                'per_call': ct / nc if nc > 0 else 0,
            }
            
            function_stats[func_info['function']] = func_info
            top_functions.append(func_info)
        
        # Sort by cumulative time
        top_functions.sort(key=lambda x: x['cumulative_time'], reverse=True)
        
        return ProfileResult(
            operation_name=operation_name,
            duration=duration,
            function_stats=function_stats,
            top_functions=top_functions,
            memory_profile=memory_profile
        )
    
    def get_profile_results(self, operation_name: Optional[str] = None) -> List[ProfileResult]:
        """Get profile results, optionally filtered by operation name."""
        with self._lock:
            if operation_name:
                return self._profiles.get(operation_name, []).copy()
            
            all_results = []
            for results in self._profiles.values():
                all_results.extend(results)
            return all_results
    
    def get_aggregated_stats(self, operation_name: str) -> Optional[Dict[str, Any]]:
        """Get aggregated statistics for an operation."""
        with self._lock:
            results = self._profiles.get(operation_name, [])
            if not results:
                return None
            
            durations = [r.duration for r in results]
            
            # Aggregate function statistics
            all_functions = {}
            for result in results:
                for func_name, stats in result.function_stats.items():
                    if func_name not in all_functions:
                        all_functions[func_name] = {
                            'total_calls': 0,
                            'total_time': 0,
                            'total_cumulative_time': 0,
                            'appearances': 0,
                        }
                    
                    all_functions[func_name]['total_calls'] += stats['calls']
                    all_functions[func_name]['total_time'] += stats['total_time']
                    all_functions[func_name]['total_cumulative_time'] += stats['cumulative_time']
                    all_functions[func_name]['appearances'] += 1
            
            # Calculate averages
            for func_stats in all_functions.values():
                appearances = func_stats['appearances']
                func_stats['avg_calls'] = func_stats['total_calls'] / appearances
                func_stats['avg_time'] = func_stats['total_time'] / appearances
                func_stats['avg_cumulative_time'] = func_stats['total_cumulative_time'] / appearances
            
            # Sort by average cumulative time
            top_functions = sorted(
                all_functions.items(),
                key=lambda x: x[1]['avg_cumulative_time'],
                reverse=True
            )[:20]
            
            return {
                'operation_name': operation_name,
                'total_runs': len(results),
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'top_functions': [
                    {
                        'function': func_name,
                        **stats
                    }
                    for func_name, stats in top_functions
                ],
            }
    
    def clear_profiles(self, operation_name: Optional[str] = None) -> None:
        """Clear profile results."""
        with self._lock:
            if operation_name:
                self._profiles.pop(operation_name, None)
            else:
                self._profiles.clear()
    
    def export_profile_data(self) -> Dict[str, Any]:
        """Export all profile data for analysis."""
        with self._lock:
            export_data = {}
            
            for operation_name, results in self._profiles.items():
                export_data[operation_name] = []
                
                for result in results:
                    export_data[operation_name].append({
                        'duration': result.duration,
                        'top_functions': result.top_functions[:10],  # Limit for size
                        'memory_profile': result.memory_profile,
                    })
            
            return export_data


def profile_operation(operation_name: Optional[str] = None,
                     enable_memory: bool = False) -> Callable[[F], F]:
    """
    Decorator for profiling function execution.
    
    Args:
        operation_name: Name for the operation (defaults to function name)
        enable_memory: Whether to enable memory profiling
    
    Returns:
        Decorated function with profiling
    """
    def decorator(func: F) -> F:
        name = operation_name or func.__name__
        profiler = CodebaseProfiler(enable_memory_profiling=enable_memory)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with profiler.profile_operation(name):
                return func(*args, **kwargs)
        
        # Attach profiler to function for access to results
        wrapper._profiler = profiler
        
        return wrapper
    
    return decorator


class PerformanceAnalyzer:
    """
    Analyzer for identifying performance bottlenecks and optimization opportunities.
    """
    
    def __init__(self, profiler: CodebaseProfiler):
        self.profiler = profiler
    
    def analyze_bottlenecks(self, operation_name: str) -> Dict[str, Any]:
        """Analyze performance bottlenecks for an operation."""
        stats = self.profiler.get_aggregated_stats(operation_name)
        if not stats:
            return {'error': f'No profile data for operation: {operation_name}'}
        
        bottlenecks = []
        recommendations = []
        
        # Identify functions taking significant time
        total_time = stats['avg_duration']
        for func_data in stats['top_functions'][:10]:
            func_time = func_data['avg_cumulative_time']
            percentage = (func_time / total_time) * 100 if total_time > 0 else 0
            
            if percentage > 10:  # Functions taking >10% of total time
                bottlenecks.append({
                    'function': func_data['function'],
                    'time_percentage': percentage,
                    'avg_time': func_time,
                    'avg_calls': func_data['avg_calls'],
                })
                
                # Generate recommendations
                if func_data['avg_calls'] > 100:
                    recommendations.append(
                        f"Consider caching results for {func_data['function']} "
                        f"(called {func_data['avg_calls']:.0f} times on average)"
                    )
                
                if percentage > 25:
                    recommendations.append(
                        f"High impact optimization opportunity: {func_data['function']} "
                        f"takes {percentage:.1f}% of total time"
                    )
        
        return {
            'operation_name': operation_name,
            'total_runs': stats['total_runs'],
            'avg_duration': stats['avg_duration'],
            'bottlenecks': bottlenecks,
            'recommendations': recommendations,
        }
    
    def compare_operations(self, operation_names: List[str]) -> Dict[str, Any]:
        """Compare performance across multiple operations."""
        comparison = {}
        
        for name in operation_names:
            stats = self.profiler.get_aggregated_stats(name)
            if stats:
                comparison[name] = {
                    'avg_duration': stats['avg_duration'],
                    'min_duration': stats['min_duration'],
                    'max_duration': stats['max_duration'],
                    'total_runs': stats['total_runs'],
                }
        
        # Find fastest and slowest operations
        if comparison:
            fastest = min(comparison.items(), key=lambda x: x[1]['avg_duration'])
            slowest = max(comparison.items(), key=lambda x: x[1]['avg_duration'])
            
            return {
                'operations': comparison,
                'fastest': fastest[0],
                'slowest': slowest[0],
                'performance_ratio': slowest[1]['avg_duration'] / fastest[1]['avg_duration'],
            }
        
        return {'operations': {}}


# Global profiler instance
_global_profiler = CodebaseProfiler()


def get_global_profiler() -> CodebaseProfiler:
    """Get the global profiler instance."""
    return _global_profiler


def analyze_performance(operation_name: str) -> Dict[str, Any]:
    """Analyze performance for a specific operation using the global profiler."""
    analyzer = PerformanceAnalyzer(_global_profiler)
    return analyzer.analyze_bottlenecks(operation_name)


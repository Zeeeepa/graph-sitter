"""
Performance Integration Layer

Integration layer for applying performance optimizations to existing graph-sitter components.
"""

import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from graph_sitter.shared.logging.get_logger import get_logger

from .cache_manager import CacheStrategy, get_cache_manager
from .memory_manager import MemoryStrategy, get_memory_manager
from .monitoring import get_performance_monitor
from .optimization_engine import OptimizationStrategy, get_optimization_engine
from .profiler import get_profiler
from .scalability import get_scalability_manager

logger = get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class PerformanceIntegration:
    """Main integration class for applying performance optimizations"""
    
    def __init__(self):
        self.optimization_engine = get_optimization_engine()
        self.cache_manager = get_cache_manager()
        self.memory_manager = get_memory_manager()
        self.performance_monitor = get_performance_monitor()
        self.profiler = get_profiler()
        self.scalability_manager = get_scalability_manager()
        
        # Track optimized functions
        self.optimized_functions: Dict[str, Dict[str, Any]] = {}
    
    def optimize_codebase_operations(self) -> None:
        """Apply optimizations to core codebase operations"""
        logger.info("Applying performance optimizations to graph-sitter codebase")
        
        # Setup caching for common operations
        self._setup_caching()
        
        # Setup monitoring for critical functions
        self._setup_monitoring()
        
        # Setup memory optimization
        self._setup_memory_optimization()
        
        logger.info("Performance optimizations applied successfully")
    
    def _setup_caching(self) -> None:
        """Setup caching for frequently used operations"""
        # Create specialized caches
        self.cache_manager.create_cache(
            "file_parsing", 
            CacheStrategy.LRU, 
            max_size=5000,
            ttl=3600  # 1 hour
        )
        
        self.cache_manager.create_cache(
            "type_resolution", 
            CacheStrategy.LFU, 
            max_size=10000,
            ttl=1800  # 30 minutes
        )
        
        self.cache_manager.create_cache(
            "import_analysis", 
            CacheStrategy.WEAK_REF, 
            max_size=2000
        )
        
        logger.debug("Specialized caches created")
    
    def _setup_monitoring(self) -> None:
        """Setup monitoring for critical operations"""
        # Add performance alerts
        self.performance_monitor.add_alert(
            "high_memory_usage",
            "memory_usage_bytes",
            threshold=1024 * 1024 * 1024,  # 1GB
            comparison="greater_than"
        )
        
        self.performance_monitor.add_alert(
            "slow_function_execution",
            "function_duration_seconds",
            threshold=5.0,  # 5 seconds
            comparison="greater_than"
        )
        
        logger.debug("Performance monitoring alerts configured")
    
    def _setup_memory_optimization(self) -> None:
        """Setup memory optimization strategies"""
        # Create object pools for expensive objects
        self.memory_manager.create_object_pool(
            "ast_nodes",
            factory=lambda: {},  # Placeholder factory
            max_size=1000
        )
        
        self.memory_manager.create_object_pool(
            "symbol_tables",
            factory=lambda: {},  # Placeholder factory
            max_size=500
        )
        
        logger.debug("Memory optimization pools created")
    
    def optimize_file_operations(self) -> Callable[[F], F]:
        """Decorator for optimizing file I/O operations"""
        def decorator(func: F) -> F:
            # Apply multiple optimizations
            optimized_func = self.optimization_engine.optimize(
                OptimizationStrategy.IO_OPTIMIZED,
                cache_key="file_parsing"
            )(func)
            
            optimized_func = self.memory_manager.optimize_memory(
                MemoryStrategy.BALANCED
            )(optimized_func)
            
            optimized_func = self.performance_monitor.monitor_function(
                f"file_ops.{func.__name__}"
            )(optimized_func)
            
            self._track_optimization(func.__name__, "file_operations")
            return optimized_func
        
        return decorator
    
    def optimize_parsing_operations(self) -> Callable[[F], F]:
        """Decorator for optimizing parsing operations"""
        def decorator(func: F) -> F:
            # Apply CPU and memory optimizations
            optimized_func = self.optimization_engine.optimize(
                OptimizationStrategy.CPU_OPTIMIZED,
                cache_key="file_parsing"
            )(func)
            
            optimized_func = self.memory_manager.optimize_memory(
                MemoryStrategy.AGGRESSIVE
            )(optimized_func)
            
            optimized_func = self.performance_monitor.monitor_function(
                f"parsing.{func.__name__}"
            )(optimized_func)
            
            self._track_optimization(func.__name__, "parsing_operations")
            return optimized_func
        
        return decorator
    
    def optimize_type_resolution(self) -> Callable[[F], F]:
        """Decorator for optimizing type resolution operations"""
        def decorator(func: F) -> F:
            # Apply caching and CPU optimizations
            optimized_func = self.cache_manager.cached(
                cache_name="type_resolution",
                ttl=1800
            )(func)
            
            optimized_func = self.optimization_engine.optimize(
                OptimizationStrategy.LATENCY_OPTIMIZED
            )(optimized_func)
            
            optimized_func = self.performance_monitor.monitor_function(
                f"type_resolution.{func.__name__}"
            )(optimized_func)
            
            self._track_optimization(func.__name__, "type_resolution")
            return optimized_func
        
        return decorator
    
    def optimize_import_analysis(self) -> Callable[[F], F]:
        """Decorator for optimizing import analysis operations"""
        def decorator(func: F) -> F:
            # Apply weak reference caching and memory optimization
            optimized_func = self.cache_manager.cached(
                cache_name="import_analysis"
            )(func)
            
            optimized_func = self.memory_manager.optimize_memory(
                MemoryStrategy.STREAMING
            )(optimized_func)
            
            optimized_func = self.performance_monitor.monitor_function(
                f"import_analysis.{func.__name__}"
            )(optimized_func)
            
            self._track_optimization(func.__name__, "import_analysis")
            return optimized_func
        
        return decorator
    
    def optimize_graph_operations(self) -> Callable[[F], F]:
        """Decorator for optimizing graph operations"""
        def decorator(func: F) -> F:
            # Apply distributed execution for large graphs
            optimized_func = self.scalability_manager.distributed_execution()(func)
            
            optimized_func = self.optimization_engine.optimize(
                OptimizationStrategy.THROUGHPUT_OPTIMIZED
            )(optimized_func)
            
            optimized_func = self.performance_monitor.monitor_function(
                f"graph_ops.{func.__name__}"
            )(optimized_func)
            
            self._track_optimization(func.__name__, "graph_operations")
            return optimized_func
        
        return decorator
    
    def optimize_database_operations(self) -> Callable[[F], F]:
        """Decorator for optimizing database operations"""
        def decorator(func: F) -> F:
            # Apply connection pooling and caching
            optimized_func = self.cache_manager.cached(
                cache_name="database_queries",
                ttl=300  # 5 minutes
            )(func)
            
            optimized_func = self.optimization_engine.optimize(
                OptimizationStrategy.IO_OPTIMIZED
            )(optimized_func)
            
            optimized_func = self.performance_monitor.monitor_function(
                f"database.{func.__name__}"
            )(optimized_func)
            
            self._track_optimization(func.__name__, "database_operations")
            return optimized_func
        
        return decorator
    
    def _track_optimization(self, function_name: str, category: str) -> None:
        """Track applied optimizations"""
        if category not in self.optimized_functions:
            self.optimized_functions[category] = {}
        
        self.optimized_functions[category][function_name] = {
            'optimized_at': time.time(),
            'category': category
        }
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Get comprehensive optimization report"""
        return {
            'optimized_functions': self.optimized_functions,
            'cache_stats': self.cache_manager.get_all_stats(),
            'memory_stats': self.memory_manager.get_global_stats(),
            'performance_summary': self.performance_monitor.get_performance_summary(),
            'scalability_stats': self.scalability_manager.get_global_stats(),
            'profiling_summary': self.profiler.get_profiling_summary()
        }
    
    def start_comprehensive_monitoring(self) -> None:
        """Start comprehensive performance monitoring"""
        # Start profiling
        self.profiler.start_profiling()
        
        # Start scalability monitoring
        self.scalability_manager.auto_scaler.start_monitoring()
        
        logger.info("Comprehensive performance monitoring started")
    
    def stop_comprehensive_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return final report"""
        # Stop profiling and get results
        profiling_results = self.profiler.stop_profiling()
        
        # Stop scalability monitoring
        self.scalability_manager.auto_scaler.stop_monitoring()
        
        # Generate final report
        final_report = self.get_optimization_report()
        final_report['profiling_results'] = profiling_results
        
        logger.info("Comprehensive performance monitoring stopped")
        return final_report


# Global integration instance
_global_integration: Optional[PerformanceIntegration] = None


def get_performance_integration() -> PerformanceIntegration:
    """Get global performance integration instance"""
    global _global_integration
    if _global_integration is None:
        _global_integration = PerformanceIntegration()
    return _global_integration


# Convenience decorators for common optimizations
def optimize_file_ops(func: F) -> F:
    """Optimize file operations"""
    integration = get_performance_integration()
    return integration.optimize_file_operations()(func)


def optimize_parsing(func: F) -> F:
    """Optimize parsing operations"""
    integration = get_performance_integration()
    return integration.optimize_parsing_operations()(func)


def optimize_types(func: F) -> F:
    """Optimize type resolution"""
    integration = get_performance_integration()
    return integration.optimize_type_resolution()(func)


def optimize_imports(func: F) -> F:
    """Optimize import analysis"""
    integration = get_performance_integration()
    return integration.optimize_import_analysis()(func)


def optimize_graph(func: F) -> F:
    """Optimize graph operations"""
    integration = get_performance_integration()
    return integration.optimize_graph_operations()(func)


def optimize_database(func: F) -> F:
    """Optimize database operations"""
    integration = get_performance_integration()
    return integration.optimize_database_operations()(func)


# Auto-apply optimizations to existing codebase
def apply_performance_optimizations() -> None:
    """Apply performance optimizations to the entire codebase"""
    integration = get_performance_integration()
    integration.optimize_codebase_operations()
    integration.start_comprehensive_monitoring()
    
    logger.info("🚀 Performance optimization system fully activated!")


# Initialize optimizations when module is imported
try:
    apply_performance_optimizations()
except Exception as e:
    logger.warning(f"Failed to auto-apply performance optimizations: {e}")
    logger.info("Performance optimizations can be manually applied using apply_performance_optimizations()")


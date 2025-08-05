"""
Scalability Management and Load Balancing

Advanced scalability system for horizontal and vertical scaling with load balancing.
"""

import asyncio
import hashlib
import random
import threading
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar, Union
from weakref import WeakSet

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

F = TypeVar('F', bound=Callable[..., Any])


class LoadBalancingStrategy(Enum):
    """Load balancing strategies"""
    ROUND_ROBIN = auto()
    LEAST_CONNECTIONS = auto()
    WEIGHTED_ROUND_ROBIN = auto()
    RANDOM = auto()
    HASH_BASED = auto()
    LEAST_RESPONSE_TIME = auto()


class ScalingStrategy(Enum):
    """Scaling strategies"""
    MANUAL = auto()
    AUTO_CPU = auto()
    AUTO_MEMORY = auto()
    AUTO_QUEUE_LENGTH = auto()
    AUTO_RESPONSE_TIME = auto()
    PREDICTIVE = auto()


@dataclass
class WorkerNode:
    """Worker node for distributed processing"""
    id: str
    weight: float = 1.0
    max_connections: int = 100
    current_connections: int = 0
    total_requests: int = 0
    total_response_time: float = 0.0
    last_request_time: float = 0.0
    is_healthy: bool = True
    created_at: float = field(default_factory=time.time)
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time"""
        if self.total_requests == 0:
            return 0.0
        return self.total_response_time / self.total_requests
    
    @property
    def load_factor(self) -> float:
        """Calculate current load factor (0.0 to 1.0)"""
        if self.max_connections == 0:
            return 0.0
        return self.current_connections / self.max_connections
    
    def can_accept_request(self) -> bool:
        """Check if worker can accept new request"""
        return self.is_healthy and self.current_connections < self.max_connections
    
    def start_request(self) -> None:
        """Mark start of request processing"""
        self.current_connections += 1
        self.last_request_time = time.time()
    
    def finish_request(self, response_time: float) -> None:
        """Mark completion of request processing"""
        self.current_connections = max(0, self.current_connections - 1)
        self.total_requests += 1
        self.total_response_time += response_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'weight': self.weight,
            'max_connections': self.max_connections,
            'current_connections': self.current_connections,
            'total_requests': self.total_requests,
            'average_response_time': self.average_response_time,
            'load_factor': self.load_factor,
            'is_healthy': self.is_healthy,
            'created_at': self.created_at
        }


@dataclass
class ScalingConfig:
    """Configuration for scalability management"""
    min_workers: int = 1
    max_workers: int = 10
    target_cpu_utilization: float = 0.7
    target_memory_utilization: float = 0.8
    target_queue_length: int = 100
    target_response_time_ms: float = 1000.0
    scale_up_threshold: float = 0.8
    scale_down_threshold: float = 0.3
    scale_up_cooldown_seconds: float = 300.0
    scale_down_cooldown_seconds: float = 600.0
    health_check_interval_seconds: float = 30.0
    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS
    scaling_strategy: ScalingStrategy = ScalingStrategy.AUTO_CPU


class LoadBalancer:
    """Advanced load balancer with multiple strategies"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_CONNECTIONS):
        self.strategy = strategy
        self.workers: Dict[str, WorkerNode] = {}
        self.round_robin_index = 0
        self._lock = threading.RLock()
        
    def add_worker(self, worker: WorkerNode) -> None:
        """Add worker node"""
        with self._lock:
            self.workers[worker.id] = worker
            logger.info(f"Added worker {worker.id} to load balancer")
    
    def remove_worker(self, worker_id: str) -> bool:
        """Remove worker node"""
        with self._lock:
            if worker_id in self.workers:
                del self.workers[worker_id]
                logger.info(f"Removed worker {worker_id} from load balancer")
                return True
            return False
    
    def get_worker(self, request_key: str = None) -> Optional[WorkerNode]:
        """Get worker based on load balancing strategy"""
        with self._lock:
            available_workers = [
                worker for worker in self.workers.values()
                if worker.can_accept_request()
            ]
            
            if not available_workers:
                return None
            
            if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return self._round_robin_selection(available_workers)
            elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return self._least_connections_selection(available_workers)
            elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return self._weighted_round_robin_selection(available_workers)
            elif self.strategy == LoadBalancingStrategy.RANDOM:
                return self._random_selection(available_workers)
            elif self.strategy == LoadBalancingStrategy.HASH_BASED:
                return self._hash_based_selection(available_workers, request_key)
            elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                return self._least_response_time_selection(available_workers)
            else:
                return available_workers[0]  # Fallback
    
    def _round_robin_selection(self, workers: List[WorkerNode]) -> WorkerNode:
        """Round robin worker selection"""
        worker = workers[self.round_robin_index % len(workers)]
        self.round_robin_index += 1
        return worker
    
    def _least_connections_selection(self, workers: List[WorkerNode]) -> WorkerNode:
        """Select worker with least connections"""
        return min(workers, key=lambda w: w.current_connections)
    
    def _weighted_round_robin_selection(self, workers: List[WorkerNode]) -> WorkerNode:
        """Weighted round robin selection"""
        total_weight = sum(w.weight for w in workers)
        if total_weight == 0:
            return workers[0]
        
        # Simple weighted selection
        weights = [w.weight / total_weight for w in workers]
        cumulative_weights = []
        cumulative = 0
        for weight in weights:
            cumulative += weight
            cumulative_weights.append(cumulative)
        
        rand = random.random()
        for i, cumulative_weight in enumerate(cumulative_weights):
            if rand <= cumulative_weight:
                return workers[i]
        
        return workers[-1]  # Fallback
    
    def _random_selection(self, workers: List[WorkerNode]) -> WorkerNode:
        """Random worker selection"""
        return random.choice(workers)
    
    def _hash_based_selection(self, workers: List[WorkerNode], request_key: str) -> WorkerNode:
        """Hash-based worker selection for session affinity"""
        if not request_key:
            return self._least_connections_selection(workers)
        
        hash_value = int(hashlib.md5(request_key.encode()).hexdigest(), 16)
        index = hash_value % len(workers)
        return workers[index]
    
    def _least_response_time_selection(self, workers: List[WorkerNode]) -> WorkerNode:
        """Select worker with least average response time"""
        return min(workers, key=lambda w: w.average_response_time)
    
    def get_load_stats(self) -> Dict[str, Any]:
        """Get load balancer statistics"""
        with self._lock:
            total_workers = len(self.workers)
            healthy_workers = sum(1 for w in self.workers.values() if w.is_healthy)
            total_connections = sum(w.current_connections for w in self.workers.values())
            total_requests = sum(w.total_requests for w in self.workers.values())
            
            avg_response_time = 0.0
            if total_requests > 0:
                total_response_time = sum(w.total_response_time for w in self.workers.values())
                avg_response_time = total_response_time / total_requests
            
            return {
                'strategy': self.strategy.name,
                'total_workers': total_workers,
                'healthy_workers': healthy_workers,
                'total_connections': total_connections,
                'total_requests': total_requests,
                'average_response_time': avg_response_time,
                'workers': [w.to_dict() for w in self.workers.values()]
            }


class WorkerPool:
    """Pool of worker threads/processes for parallel execution"""
    
    def __init__(self, 
                 initial_size: int = 4,
                 max_size: int = 16,
                 worker_factory: Callable = None):
        self.initial_size = initial_size
        self.max_size = max_size
        self.worker_factory = worker_factory or self._default_worker_factory
        
        self.executor = ThreadPoolExecutor(max_workers=initial_size)
        self.current_size = initial_size
        self.pending_tasks = deque()
        self.active_tasks: Set[Any] = set()
        self._lock = threading.RLock()
        
    def _default_worker_factory(self) -> ThreadPoolExecutor:
        """Default worker factory"""
        return ThreadPoolExecutor(max_workers=1)
    
    def submit_task(self, func: Callable, *args, **kwargs) -> Any:
        """Submit task to worker pool"""
        with self._lock:
            future = self.executor.submit(func, *args, **kwargs)
            self.active_tasks.add(future)
            
            # Add callback to remove from active tasks when done
            future.add_done_callback(lambda f: self.active_tasks.discard(f))
            
            return future
    
    def scale_up(self, target_size: int = None) -> bool:
        """Scale up worker pool"""
        with self._lock:
            target = min(target_size or (self.current_size * 2), self.max_size)
            
            if target > self.current_size:
                # Create new executor with more workers
                old_executor = self.executor
                self.executor = ThreadPoolExecutor(max_workers=target)
                
                # Shutdown old executor gracefully
                old_executor.shutdown(wait=False)
                
                self.current_size = target
                logger.info(f"Scaled up worker pool to {target} workers")
                return True
            
            return False
    
    def scale_down(self, target_size: int = None) -> bool:
        """Scale down worker pool"""
        with self._lock:
            target = max(target_size or (self.current_size // 2), self.initial_size)
            
            if target < self.current_size:
                # Create new executor with fewer workers
                old_executor = self.executor
                self.executor = ThreadPoolExecutor(max_workers=target)
                
                # Shutdown old executor gracefully
                old_executor.shutdown(wait=False)
                
                self.current_size = target
                logger.info(f"Scaled down worker pool to {target} workers")
                return True
            
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get worker pool statistics"""
        with self._lock:
            return {
                'current_size': self.current_size,
                'max_size': self.max_size,
                'active_tasks': len(self.active_tasks),
                'pending_tasks': len(self.pending_tasks),
                'utilization': len(self.active_tasks) / self.current_size if self.current_size > 0 else 0
            }
    
    def shutdown(self) -> None:
        """Shutdown worker pool"""
        self.executor.shutdown(wait=True)


class AutoScaler:
    """Automatic scaling system based on metrics"""
    
    def __init__(self, config: ScalingConfig = None):
        self.config = config or ScalingConfig()
        self.worker_pool = WorkerPool(
            initial_size=self.config.min_workers,
            max_size=self.config.max_workers
        )
        self.load_balancer = LoadBalancer(self.config.load_balancing_strategy)
        
        self.metrics_history: deque = deque(maxlen=100)
        self.last_scale_up_time = 0
        self.last_scale_down_time = 0
        self._monitoring_active = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Initialize workers
        self._initialize_workers()
    
    def _initialize_workers(self) -> None:
        """Initialize worker nodes"""
        for i in range(self.config.min_workers):
            worker = WorkerNode(
                id=f"worker_{i}",
                max_connections=50  # Default
            )
            self.load_balancer.add_worker(worker)
    
    def start_monitoring(self) -> None:
        """Start automatic scaling monitoring"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Auto-scaling monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop automatic scaling monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Auto-scaling monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop for auto-scaling"""
        while self._monitoring_active:
            try:
                # Collect current metrics
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                
                # Make scaling decisions
                if self.config.scaling_strategy != ScalingStrategy.MANUAL:
                    self._evaluate_scaling(metrics)
                
                # Health check workers
                self._health_check_workers()
                
                time.sleep(self.config.health_check_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in auto-scaling monitoring loop: {e}")
                time.sleep(5)  # Brief pause before retrying
    
    def _collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        pool_stats = self.worker_pool.get_stats()
        load_stats = self.load_balancer.get_load_stats()
        
        return {
            'cpu_utilization': pool_stats['utilization'],
            'memory_utilization': 0.0,  # Would integrate with memory manager
            'queue_length': pool_stats['pending_tasks'],
            'response_time': load_stats['average_response_time'],
            'active_connections': load_stats['total_connections'],
            'timestamp': time.time()
        }
    
    def _evaluate_scaling(self, metrics: Dict[str, float]) -> None:
        """Evaluate if scaling is needed"""
        current_time = time.time()
        
        # Check scale-up conditions
        should_scale_up = False
        if self.config.scaling_strategy == ScalingStrategy.AUTO_CPU:
            should_scale_up = metrics['cpu_utilization'] > self.config.scale_up_threshold
        elif self.config.scaling_strategy == ScalingStrategy.AUTO_MEMORY:
            should_scale_up = metrics['memory_utilization'] > self.config.scale_up_threshold
        elif self.config.scaling_strategy == ScalingStrategy.AUTO_QUEUE_LENGTH:
            should_scale_up = metrics['queue_length'] > self.config.target_queue_length
        elif self.config.scaling_strategy == ScalingStrategy.AUTO_RESPONSE_TIME:
            should_scale_up = metrics['response_time'] > self.config.target_response_time_ms
        
        # Check scale-down conditions
        should_scale_down = False
        if self.config.scaling_strategy == ScalingStrategy.AUTO_CPU:
            should_scale_down = metrics['cpu_utilization'] < self.config.scale_down_threshold
        elif self.config.scaling_strategy == ScalingStrategy.AUTO_MEMORY:
            should_scale_down = metrics['memory_utilization'] < self.config.scale_down_threshold
        elif self.config.scaling_strategy == ScalingStrategy.AUTO_QUEUE_LENGTH:
            should_scale_down = metrics['queue_length'] < (self.config.target_queue_length * 0.3)
        elif self.config.scaling_strategy == ScalingStrategy.AUTO_RESPONSE_TIME:
            should_scale_down = metrics['response_time'] < (self.config.target_response_time_ms * 0.5)
        
        # Apply cooldown periods
        if should_scale_up and (current_time - self.last_scale_up_time) > self.config.scale_up_cooldown_seconds:
            self._scale_up()
            self.last_scale_up_time = current_time
        elif should_scale_down and (current_time - self.last_scale_down_time) > self.config.scale_down_cooldown_seconds:
            self._scale_down()
            self.last_scale_down_time = current_time
    
    def _scale_up(self) -> None:
        """Scale up the system"""
        with self._lock:
            # Scale up worker pool
            if self.worker_pool.scale_up():
                # Add new worker to load balancer
                new_worker_id = f"worker_{len(self.load_balancer.workers)}"
                new_worker = WorkerNode(id=new_worker_id, max_connections=50)
                self.load_balancer.add_worker(new_worker)
                logger.info(f"Scaled up: added worker {new_worker_id}")
    
    def _scale_down(self) -> None:
        """Scale down the system"""
        with self._lock:
            # Only scale down if we have more than minimum workers
            if len(self.load_balancer.workers) > self.config.min_workers:
                # Remove least utilized worker
                workers = list(self.load_balancer.workers.values())
                least_utilized = min(workers, key=lambda w: w.current_connections)
                
                if least_utilized.current_connections == 0:  # Only remove idle workers
                    self.load_balancer.remove_worker(least_utilized.id)
                    self.worker_pool.scale_down()
                    logger.info(f"Scaled down: removed worker {least_utilized.id}")
    
    def _health_check_workers(self) -> None:
        """Perform health checks on workers"""
        current_time = time.time()
        
        for worker in self.load_balancer.workers.values():
            # Simple health check based on last activity
            if current_time - worker.last_request_time > 300:  # 5 minutes
                if worker.current_connections == 0:
                    worker.is_healthy = True
                else:
                    # Worker might be stuck
                    worker.is_healthy = False
                    logger.warning(f"Worker {worker.id} marked as unhealthy")
    
    def execute_distributed(self, 
                           func: Callable, 
                           args_list: List[tuple],
                           request_key: str = None) -> List[Any]:
        """Execute function across distributed workers"""
        results = []
        futures = []
        
        for args in args_list:
            # Get worker for load balancing
            worker = self.load_balancer.get_worker(request_key)
            if worker:
                worker.start_request()
                
                # Submit task to worker pool
                future = self.worker_pool.submit_task(func, *args)
                futures.append((future, worker))
            else:
                logger.warning("No available workers for request")
                # Execute locally as fallback
                results.append(func(*args))
        
        # Collect results
        for future, worker in futures:
            try:
                start_time = time.time()
                result = future.result(timeout=30)  # 30 second timeout
                response_time = time.time() - start_time
                
                worker.finish_request(response_time)
                results.append(result)
                
            except Exception as e:
                worker.finish_request(30.0)  # Max timeout
                logger.error(f"Error in distributed execution: {e}")
                results.append(None)
        
        return results
    
    def get_scaling_stats(self) -> Dict[str, Any]:
        """Get comprehensive scaling statistics"""
        return {
            'config': {
                'min_workers': self.config.min_workers,
                'max_workers': self.config.max_workers,
                'scaling_strategy': self.config.scaling_strategy.name,
                'load_balancing_strategy': self.config.load_balancing_strategy.name
            },
            'worker_pool': self.worker_pool.get_stats(),
            'load_balancer': self.load_balancer.get_load_stats(),
            'recent_metrics': list(self.metrics_history)[-10:] if self.metrics_history else [],
            'last_scale_up': self.last_scale_up_time,
            'last_scale_down': self.last_scale_down_time
        }
    
    def shutdown(self) -> None:
        """Shutdown auto-scaler"""
        self.stop_monitoring()
        self.worker_pool.shutdown()


class ScalabilityManager:
    """Main scalability management system"""
    
    def __init__(self, config: ScalingConfig = None):
        self.config = config or ScalingConfig()
        self.auto_scaler = AutoScaler(self.config)
        self._scalers: Dict[str, AutoScaler] = {}
        self._lock = threading.RLock()
        
        # Start monitoring
        self.auto_scaler.start_monitoring()
    
    def get_scaler(self, name: str = "default") -> AutoScaler:
        """Get or create named auto-scaler"""
        with self._lock:
            if name == "default":
                return self.auto_scaler
            
            if name not in self._scalers:
                self._scalers[name] = AutoScaler(self.config)
                self._scalers[name].start_monitoring()
            
            return self._scalers[name]
    
    def distributed_execution(self, 
                            scaler_name: str = "default") -> Callable[[F], F]:
        """Decorator for distributed function execution"""
        
        def decorator(func: F) -> F:
            scaler = self.get_scaler(scaler_name)
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # For single execution, just use the worker pool
                return scaler.worker_pool.submit_task(func, *args, **kwargs).result()
            
            return wrapper
        
        return decorator
    
    def batch_execution(self, 
                       func: Callable,
                       args_list: List[tuple],
                       scaler_name: str = "default",
                       request_key: str = None) -> List[Any]:
        """Execute function in batches across workers"""
        scaler = self.get_scaler(scaler_name)
        return scaler.execute_distributed(func, args_list, request_key)
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global scalability statistics"""
        stats = {
            'default': self.auto_scaler.get_scaling_stats(),
            'scalers': {}
        }
        
        for name, scaler in self._scalers.items():
            stats['scalers'][name] = scaler.get_scaling_stats()
        
        return stats
    
    def shutdown_all(self) -> None:
        """Shutdown all scalers"""
        self.auto_scaler.shutdown()
        for scaler in self._scalers.values():
            scaler.shutdown()
        self._scalers.clear()


# Global scalability manager instance
_global_scalability_manager: Optional[ScalabilityManager] = None


def get_scalability_manager(config: ScalingConfig = None) -> ScalabilityManager:
    """Get global scalability manager instance"""
    global _global_scalability_manager
    if _global_scalability_manager is None:
        _global_scalability_manager = ScalabilityManager(config)
    return _global_scalability_manager


def distributed(scaler_name: str = "default") -> Callable[[F], F]:
    """Global distributed execution decorator"""
    manager = get_scalability_manager()
    return manager.distributed_execution(scaler_name)


"""
Enhanced Contexten Orchestrator with Self-Healing Architecture

This module provides a comprehensive agentic orchestrator that integrates with
the Codegen SDK and provides self-healing capabilities, real-time monitoring,
and enhanced platform integrations.

Renamed from codegen_app.py to contexten_app.py as part of system integration.
"""

import asyncio
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Import existing graph_sitter capabilities
from graph_sitter.core.codebase import Codebase
from graph_sitter.codebase.codebase_analysis import get_codebase_summary
from graph_sitter.shared.logging.get_logger import get_logger

# Import enhanced autogenlib
from ..autogenlib import AutogenClient, AutogenConfig

# Import platform extensions
from .extensions.linear import EnhancedLinearExtension
from .extensions.github import EnhancedGitHubExtension  
from .extensions.slack import EnhancedSlackExtension

logger = get_logger(__name__)

@dataclass
class ContextenConfig:
    """Configuration for Contexten orchestrator"""
    
    # Codegen SDK integration
    codegen_org_id: str
    codegen_token: str
    
    # Platform integrations
    linear_enabled: bool = True
    github_enabled: bool = True
    slack_enabled: bool = True
    
    # Self-healing configuration
    self_healing_enabled: bool = True
    health_check_interval: int = 60  # seconds
    max_retry_attempts: int = 3
    circuit_breaker_threshold: int = 5
    
    # Performance settings
    max_concurrent_tasks: int = 1000
    task_timeout_seconds: int = 300
    response_time_target_ms: int = 150
    
    # Monitoring
    enable_metrics: bool = True
    metrics_retention_days: int = 30
    
    # Codebase analysis
    codebase_path: Optional[str] = None
    auto_analyze_repos: bool = True

@dataclass
class TaskRequest:
    """Request for task execution"""
    task_type: str
    task_data: Dict[str, Any]
    priority: int = 3  # 1=highest, 5=lowest
    timeout: Optional[int] = None
    retry_count: int = 0

@dataclass
class TaskResult:
    """Result of task execution"""
    task_id: str
    status: str  # 'completed', 'failed', 'timeout', 'cancelled'
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retry_count: int = 0

class HealthMonitor:
    """Health monitoring and self-healing capabilities"""
    
    def __init__(self, config: ContextenConfig):
        self.config = config
        self.health_status = {}
        self.error_counts = {}
        self.circuit_breakers = {}
        self.last_health_check = time.time()
    
    async def check_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        
        health_report = {
            'timestamp': time.time(),
            'overall_status': 'healthy',
            'components': {},
            'metrics': {}
        }
        
        # Check database connectivity
        try:
            # This would check actual database connection
            health_report['components']['database'] = 'healthy'
        except Exception as e:
            health_report['components']['database'] = f'unhealthy: {e}'
            health_report['overall_status'] = 'degraded'
        
        # Check Codegen SDK connectivity
        try:
            # This would ping Codegen SDK
            health_report['components']['codegen_sdk'] = 'healthy'
        except Exception as e:
            health_report['components']['codegen_sdk'] = f'unhealthy: {e}'
            health_report['overall_status'] = 'degraded'
        
        # Check platform integrations
        for platform in ['linear', 'github', 'slack']:
            if getattr(self.config, f'{platform}_enabled'):
                try:
                    # This would check platform connectivity
                    health_report['components'][platform] = 'healthy'
                except Exception as e:
                    health_report['components'][platform] = f'unhealthy: {e}'
                    health_report['overall_status'] = 'degraded'
        
        # Update health status
        self.health_status = health_report
        self.last_health_check = time.time()
        
        return health_report
    
    def record_error(self, component: str, error: str):
        """Record error for circuit breaker logic"""
        
        if component not in self.error_counts:
            self.error_counts[component] = 0
        
        self.error_counts[component] += 1
        
        # Trigger circuit breaker if threshold exceeded
        if self.error_counts[component] >= self.config.circuit_breaker_threshold:
            self.circuit_breakers[component] = time.time()
            logger.warning(f"Circuit breaker triggered for {component}")
    
    def is_circuit_open(self, component: str) -> bool:
        """Check if circuit breaker is open for component"""
        
        if component not in self.circuit_breakers:
            return False
        
        # Reset circuit breaker after 5 minutes
        if time.time() - self.circuit_breakers[component] > 300:
            del self.circuit_breakers[component]
            self.error_counts[component] = 0
            return False
        
        return True

class ContextenOrchestrator:
    """Enhanced agentic orchestrator with self-healing capabilities"""
    
    def __init__(self, config: ContextenConfig):
        self.config = config
        self.app = FastAPI(title="Contexten Orchestrator")
        
        # Initialize core components
        self.health_monitor = HealthMonitor(config)
        self.task_queue = asyncio.Queue(maxsize=config.max_concurrent_tasks)
        self.active_tasks = {}
        self.task_results = {}
        
        # Initialize autogenlib client
        autogen_config = AutogenConfig(
            org_id=config.codegen_org_id,
            token=config.codegen_token,
            codebase_path=config.codebase_path,
            enable_caching=True,
            enable_context_enhancement=True
        )
        self.autogen_client = AutogenClient(autogen_config)
        
        # Initialize platform extensions
        self.extensions = {}
        self._initialize_extensions()
        
        # Initialize codebase if provided
        self.codebase = None
        if config.codebase_path:
            self._initialize_codebase()
        
        # Setup routes
        self._setup_routes()
        
        # Background tasks
        self._background_tasks = []
    
    def _initialize_extensions(self):
        """Initialize platform extensions"""
        
        if self.config.linear_enabled:
            self.extensions['linear'] = EnhancedLinearExtension(self)
        
        if self.config.github_enabled:
            self.extensions['github'] = EnhancedGitHubExtension(self)
        
        if self.config.slack_enabled:
            self.extensions['slack'] = EnhancedSlackExtension(self)
    
    def _initialize_codebase(self):
        """Initialize codebase analysis"""
        
        try:
            if Path(self.config.codebase_path).is_dir():
                self.codebase = Codebase.from_path(self.config.codebase_path)
            else:
                self.codebase = Codebase.from_repo(self.config.codebase_path)
            
            logger.info(f"Codebase initialized: {get_codebase_summary(self.codebase)}")
            
        except Exception as e:
            logger.error(f"Failed to initialize codebase: {e}")
            self.codebase = None
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return await self.health_monitor.check_health()
        
        @self.app.post("/tasks")
        async def create_task(request: TaskRequest):
            """Create and execute a task"""
            return await self.execute_task(
                request.task_type,
                request.task_data,
                priority=request.priority,
                timeout=request.timeout
            )
        
        @self.app.get("/tasks/{task_id}")
        async def get_task_result(task_id: str):
            """Get task result"""
            if task_id in self.task_results:
                return self.task_results[task_id]
            elif task_id in self.active_tasks:
                return {"task_id": task_id, "status": "running"}
            else:
                raise HTTPException(status_code=404, detail="Task not found")
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get system metrics"""
            return await self.get_system_metrics()
        
        @self.app.get("/codebase/summary")
        async def get_codebase_summary_endpoint():
            """Get codebase summary"""
            if self.codebase:
                return {"summary": get_codebase_summary(self.codebase)}
            else:
                raise HTTPException(status_code=404, detail="No codebase loaded")
    
    async def start(self):
        """Start the orchestrator"""
        
        logger.info("Starting Contexten Orchestrator...")
        
        # Start background tasks
        if self.config.self_healing_enabled:
            self._background_tasks.append(
                asyncio.create_task(self._health_check_loop())
            )
        
        self._background_tasks.append(
            asyncio.create_task(self._task_processor())
        )
        
        # Initialize extensions
        for name, extension in self.extensions.items():
            try:
                await extension.initialize()
                logger.info(f"Initialized {name} extension")
            except Exception as e:
                logger.error(f"Failed to initialize {name} extension: {e}")
                self.health_monitor.record_error(name, str(e))
        
        logger.info("Contexten Orchestrator started successfully")
    
    async def stop(self):
        """Stop the orchestrator"""
        
        logger.info("Stopping Contexten Orchestrator...")
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self._background_tasks, return_exceptions=True)
        
        # Cleanup extensions
        for name, extension in self.extensions.items():
            try:
                await extension.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up {name} extension: {e}")
        
        logger.info("Contexten Orchestrator stopped")
    
    async def execute_task(self, 
                         task_type: str, 
                         task_data: Dict[str, Any],
                         priority: int = 3,
                         timeout: Optional[int] = None) -> TaskResult:
        """Execute a task with self-healing capabilities"""
        
        task_id = f"task_{int(time.time() * 1000)}"
        start_time = time.time()
        
        try:
            # Check if component is available
            component = task_type.split('.')[0] if '.' in task_type else 'core'
            
            if self.health_monitor.is_circuit_open(component):
                return TaskResult(
                    task_id=task_id,
                    status='failed',
                    error=f'Circuit breaker open for {component}',
                    execution_time=time.time() - start_time
                )
            
            # Add to active tasks
            self.active_tasks[task_id] = {
                'type': task_type,
                'data': task_data,
                'start_time': start_time,
                'priority': priority
            }
            
            # Route task to appropriate handler
            result = await self._route_task(task_type, task_data, timeout)
            
            # Create successful result
            task_result = TaskResult(
                task_id=task_id,
                status='completed',
                result=result,
                execution_time=time.time() - start_time
            )
            
        except asyncio.TimeoutError:
            task_result = TaskResult(
                task_id=task_id,
                status='timeout',
                error='Task timed out',
                execution_time=time.time() - start_time
            )
            self.health_monitor.record_error(component, 'timeout')
            
        except Exception as e:
            task_result = TaskResult(
                task_id=task_id,
                status='failed',
                error=str(e),
                execution_time=time.time() - start_time
            )
            self.health_monitor.record_error(component, str(e))
            
        finally:
            # Remove from active tasks and store result
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            
            self.task_results[task_id] = task_result
        
        return task_result
    
    async def _route_task(self, task_type: str, task_data: Dict[str, Any], timeout: Optional[int]) -> Dict[str, Any]:
        """Route task to appropriate handler"""
        
        if timeout is None:
            timeout = self.config.task_timeout_seconds
        
        # Parse task type
        if '.' in task_type:
            platform, action = task_type.split('.', 1)
        else:
            platform, action = 'core', task_type
        
        # Route to platform extension
        if platform in self.extensions:
            return await asyncio.wait_for(
                self.extensions[platform].handle_task(action, task_data),
                timeout=timeout
            )
        
        # Handle core tasks
        elif platform == 'core':
            return await self._handle_core_task(action, task_data)
        
        # Handle autogenlib tasks
        elif platform == 'autogenlib':
            return await self._handle_autogenlib_task(action, task_data)
        
        else:
            raise ValueError(f"Unknown task type: {task_type}")
    
    async def _handle_core_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle core orchestrator tasks"""
        
        if action == 'health_check':
            return await self.health_monitor.check_health()
        
        elif action == 'analyze_codebase':
            if self.codebase:
                return {"summary": get_codebase_summary(self.codebase)}
            else:
                raise ValueError("No codebase loaded")
        
        elif action == 'get_metrics':
            return await self.get_system_metrics()
        
        else:
            raise ValueError(f"Unknown core action: {action}")
    
    async def _handle_autogenlib_task(self, action: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle autogenlib code generation tasks"""
        
        if action == 'generate_code':
            result = await self.autogen_client.generate_code(
                module_path=task_data.get('module_path'),
                function_name=task_data.get('function_name'),
                **task_data.get('kwargs', {})
            )
            
            return {
                'code': result.code,
                'metadata': result.metadata,
                'generation_time': result.generation_time,
                'cache_hit': result.cache_hit
            }
        
        elif action == 'generate_batch':
            results = await self.autogen_client.generate_batch(
                task_data.get('requests', [])
            )
            
            return {
                'results': [
                    {
                        'code': r.code,
                        'metadata': r.metadata,
                        'generation_time': r.generation_time,
                        'cache_hit': r.cache_hit
                    } for r in results
                ]
            }
        
        else:
            raise ValueError(f"Unknown autogenlib action: {action}")
    
    async def _health_check_loop(self):
        """Background health check loop"""
        
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                await self.health_monitor.check_health()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check error: {e}")
    
    async def _task_processor(self):
        """Background task processor"""
        
        while True:
            try:
                # This would process queued tasks
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task processor error: {e}")
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get comprehensive system metrics"""
        
        return {
            'timestamp': time.time(),
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.task_results),
            'health_status': self.health_monitor.health_status,
            'circuit_breakers': list(self.health_monitor.circuit_breakers.keys()),
            'extensions': {
                name: ext.get_status() for name, ext in self.extensions.items()
            },
            'autogenlib_metrics': await self.autogen_client.get_performance_metrics() if self.autogen_client else {}
        }

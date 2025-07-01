"""
Unified API Interface

This module provides a unified API interface that integrates all
Contexten components and provides a single entry point for external systems.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import json

from .codebase_adapter import CodebaseAdapter, AnalysisRequest, AnalysisResult
from .database_adapter import DatabaseAdapter, DatabaseConfig
from ..learning import (
    PatternRecognitionEngine, PerformanceTracker, AdaptationEngine,
    Pattern, DataPoint, MetricPoint, MetricType
)

logger = logging.getLogger(__name__)


class APIVersion(Enum):
    """API version enumeration."""
    V1 = "v1"
    V2 = "v2"


@dataclass
class APIResponse:
    """Standard API response format."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    message: Optional[str] = None
    timestamp: datetime = None
    version: str = "v1"
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class APIRequest:
    """Standard API request format."""
    action: str
    parameters: Dict[str, Any]
    version: str = "v1"
    request_id: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.request_id is None:
            import uuid
            self.request_id = str(uuid.uuid4())[:8]


class UnifiedAPI:
    """
    Unified API interface for the Contexten CI/CD system.
    
    This API provides a single entry point for all system operations,
    integrating codebase analysis, database operations, learning systems,
    and platform integrations.
    """
    
    def __init__(self, 
                 database_config: Optional[DatabaseConfig] = None,
                 enable_learning: bool = True,
                 enable_performance_tracking: bool = True):
        """
        Initialize the unified API.
        
        Args:
            database_config: Database configuration
            enable_learning: Whether to enable learning systems
            enable_performance_tracking: Whether to enable performance tracking
        """
        self.database_config = database_config
        self.enable_learning = enable_learning
        self.enable_performance_tracking = enable_performance_tracking
        
        # Core components
        self.codebase_adapter = CodebaseAdapter()
        self.database_adapter: Optional[DatabaseAdapter] = None
        self.pattern_engine: Optional[PatternRecognitionEngine] = None
        self.performance_tracker: Optional[PerformanceTracker] = None
        self.adaptation_engine: Optional[AdaptationEngine] = None
        
        # API state
        self.initialized = False
        self.request_handlers: Dict[str, callable] = {}
        self.middleware: List[callable] = []
        
        # Setup request handlers
        self._setup_request_handlers()
        
        logger.info("Unified API initialized")
    
    async def initialize(self):
        """Initialize all API components."""
        if self.initialized:
            return
        
        logger.info("Initializing Unified API components...")
        
        # Initialize database adapter
        if self.database_config:
            self.database_adapter = DatabaseAdapter(self.database_config)
            await self.database_adapter.connect()
        
        # Initialize learning components
        if self.enable_learning:
            self.pattern_engine = PatternRecognitionEngine()
            
            if self.enable_performance_tracking:
                self.performance_tracker = PerformanceTracker()
                await self.performance_tracker.start_monitoring()
                
                self.adaptation_engine = AdaptationEngine(
                    self.pattern_engine,
                    self.performance_tracker
                )
        
        self.initialized = True
        logger.info("Unified API initialized successfully")
    
    async def shutdown(self):
        """Shutdown all API components."""
        logger.info("Shutting down Unified API...")
        
        if self.performance_tracker:
            await self.performance_tracker.stop_monitoring()
        
        if self.database_adapter:
            await self.database_adapter.disconnect()
        
        self.initialized = False
        logger.info("Unified API shutdown complete")
    
    def _setup_request_handlers(self):
        """Setup request handlers for different actions."""
        self.request_handlers = {
            # Codebase operations
            "analyze_codebase": self._handle_analyze_codebase,
            "get_analysis_status": self._handle_get_analysis_status,
            "list_analyses": self._handle_list_analyses,
            
            # Project management
            "create_project": self._handle_create_project,
            "get_project": self._handle_get_project,
            "list_projects": self._handle_list_projects,
            "get_project_metrics": self._handle_get_project_metrics,
            
            # Task management
            "create_task": self._handle_create_task,
            "update_task": self._handle_update_task,
            "get_task": self._handle_get_task,
            "list_tasks": self._handle_list_tasks,
            
            # Pipeline operations
            "create_pipeline": self._handle_create_pipeline,
            "run_pipeline": self._handle_run_pipeline,
            "get_pipeline_status": self._handle_get_pipeline_status,
            
            # Learning and adaptation
            "get_patterns": self._handle_get_patterns,
            "get_performance_metrics": self._handle_get_performance_metrics,
            "get_adaptations": self._handle_get_adaptations,
            "apply_adaptation": self._handle_apply_adaptation,
            
            # System operations
            "health_check": self._handle_health_check,
            "get_system_status": self._handle_get_system_status,
            "get_api_info": self._handle_get_api_info
        }
    
    def add_middleware(self, middleware_func: callable):
        """Add middleware function to the API."""
        self.middleware.append(middleware_func)
    
    async def process_request(self, request: Union[APIRequest, Dict[str, Any]]) -> APIResponse:
        """
        Process an API request.
        
        Args:
            request: API request object or dictionary
            
        Returns:
            API response
        """
        # Convert dict to APIRequest if needed
        if isinstance(request, dict):
            request = APIRequest(**request)
        
        logger.info(f"Processing API request: {request.action} ({request.request_id})")
        
        try:
            # Apply middleware
            for middleware in self.middleware:
                request = await middleware(request) if asyncio.iscoroutinefunction(middleware) else middleware(request)
            
            # Check if API is initialized
            if not self.initialized and request.action != "get_api_info":
                return APIResponse(
                    success=False,
                    error="API not initialized",
                    request_id=request.request_id
                )
            
            # Get handler
            handler = self.request_handlers.get(request.action)
            if not handler:
                return APIResponse(
                    success=False,
                    error=f"Unknown action: {request.action}",
                    request_id=request.request_id
                )
            
            # Execute handler
            result = await handler(request.parameters)
            
            # Record performance metrics
            if self.performance_tracker:
                self.performance_tracker.record_task_performance(
                    task_id=f"api_{request.action}_{request.request_id}",
                    duration=0.1,  # Would measure actual duration
                    success=True
                )
            
            return APIResponse(
                success=True,
                data=result,
                message=f"Successfully processed {request.action}",
                request_id=request.request_id
            )
            
        except Exception as e:
            logger.error(f"Error processing request {request.request_id}: {e}")
            
            # Record error metrics
            if self.performance_tracker:
                self.performance_tracker.record_task_performance(
                    task_id=f"api_{request.action}_{request.request_id}",
                    duration=0.1,
                    success=False,
                    error_type=type(e).__name__
                )
            
            return APIResponse(
                success=False,
                error=str(e),
                request_id=request.request_id
            )
    
    # Request handlers
    
    async def _handle_analyze_codebase(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle codebase analysis request."""
        request = AnalysisRequest(
            repository_url=params["repository_url"],
            analysis_type=params.get("analysis_type", "comprehensive"),
            target_files=params.get("target_files"),
            target_classes=params.get("target_classes"),
            target_functions=params.get("target_functions"),
            include_dependencies=params.get("include_dependencies", True),
            custom_config=params.get("custom_config")
        )
        
        result = await self.codebase_adapter.analyze_codebase(request)
        
        # Store in database if available
        if self.database_adapter and result.status == "completed":
            # This would store the analysis results
            pass
        
        return asdict(result)
    
    async def _handle_get_analysis_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get analysis status request."""
        request_id = params["request_id"]
        status = await self.codebase_adapter.get_analysis_status(request_id)
        
        return {
            "request_id": request_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_list_analyses(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list analyses request."""
        analyses = self.codebase_adapter.get_cached_analyses()
        
        return {
            "analyses": [asdict(analysis) for analysis in analyses],
            "total_count": len(analyses),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_create_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create project request."""
        if not self.database_adapter:
            raise Exception("Database not available")
        
        project_id = await self.database_adapter.create_project(
            org_id=params["organization_id"],
            name=params["name"],
            slug=params["slug"],
            description=params.get("description"),
            repository_url=params.get("repository_url")
        )
        
        return {
            "project_id": project_id,
            "name": params["name"],
            "created_at": datetime.now().isoformat()
        }
    
    async def _handle_get_project(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get project request."""
        if not self.database_adapter:
            raise Exception("Database not available")
        
        project = await self.database_adapter.get_project(params["project_id"])
        if not project:
            raise Exception("Project not found")
        
        return project
    
    async def _handle_list_projects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list projects request."""
        if not self.database_adapter:
            raise Exception("Database not available")
        
        projects = await self.database_adapter.list_projects(
            org_id=params.get("organization_id")
        )
        
        return {
            "projects": projects,
            "total_count": len(projects),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_get_project_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get project metrics request."""
        if not self.database_adapter:
            raise Exception("Database not available")
        
        metrics = await self.database_adapter.get_project_metrics(
            project_id=params["project_id"],
            days=params.get("days", 30)
        )
        
        return metrics
    
    async def _handle_create_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create task request."""
        if not self.database_adapter:
            raise Exception("Database not available")
        
        task_id = await self.database_adapter.create_task(
            project_id=params["project_id"],
            name=params["name"],
            description=params.get("description"),
            workflow_id=params.get("workflow_id"),
            task_definition_id=params.get("task_definition_id"),
            priority=params.get("priority", 5),
            config=params.get("config"),
            context=params.get("context")
        )
        
        return {
            "task_id": task_id,
            "name": params["name"],
            "created_at": datetime.now().isoformat()
        }
    
    async def _handle_update_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update task request."""
        if not self.database_adapter:
            raise Exception("Database not available")
        
        success = await self.database_adapter.update_task_status(
            task_id=params["task_id"],
            status=params["status"],
            result=params.get("result"),
            error_message=params.get("error_message")
        )
        
        return {
            "task_id": params["task_id"],
            "status": params["status"],
            "updated": success,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_get_task(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get task request."""
        if not self.database_adapter:
            raise Exception("Database not available")
        
        task = await self.database_adapter.get_task(params["task_id"])
        if not task:
            raise Exception("Task not found")
        
        return task
    
    async def _handle_list_tasks(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle list tasks request."""
        if not self.database_adapter:
            raise Exception("Database not available")
        
        tasks = await self.database_adapter.list_tasks(
            project_id=params.get("project_id"),
            status=params.get("status"),
            limit=params.get("limit", 100)
        )
        
        return {
            "tasks": tasks,
            "total_count": len(tasks),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_create_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create pipeline request."""
        if not self.database_adapter:
            raise Exception("Database not available")
        
        pipeline_id = await self.database_adapter.create_pipeline(
            project_id=params["project_id"],
            name=params["name"],
            description=params.get("description"),
            pipeline_type=params.get("pipeline_type", "ci_cd"),
            config=params.get("config")
        )
        
        return {
            "pipeline_id": pipeline_id,
            "name": params["name"],
            "created_at": datetime.now().isoformat()
        }
    
    async def _handle_run_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle run pipeline request."""
        if not self.database_adapter:
            raise Exception("Database not available")
        
        run_id = await self.database_adapter.create_pipeline_run(
            pipeline_id=params["pipeline_id"],
            trigger_event=params.get("trigger_event")
        )
        
        return {
            "run_id": run_id,
            "pipeline_id": params["pipeline_id"],
            "started_at": datetime.now().isoformat()
        }
    
    async def _handle_get_pipeline_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get pipeline status request."""
        # This would query pipeline run status from database
        return {
            "run_id": params["run_id"],
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_get_patterns(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get patterns request."""
        if not self.pattern_engine:
            raise Exception("Pattern recognition not available")
        
        pattern_type = params.get("pattern_type")
        if pattern_type:
            from ..learning.pattern_recognition import PatternType
            patterns = self.pattern_engine.get_patterns_by_type(PatternType(pattern_type))
        else:
            patterns = list(self.pattern_engine.recognized_patterns.values())
        
        return {
            "patterns": [asdict(pattern) for pattern in patterns],
            "total_count": len(patterns),
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_get_performance_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get performance metrics request."""
        if not self.performance_tracker:
            raise Exception("Performance tracking not available")
        
        summary = self.performance_tracker.get_performance_summary()
        return summary
    
    async def _handle_get_adaptations(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get adaptations request."""
        if not self.adaptation_engine:
            raise Exception("Adaptation engine not available")
        
        summary = self.adaptation_engine.get_adaptation_summary()
        return summary
    
    async def _handle_apply_adaptation(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle apply adaptation request."""
        if not self.adaptation_engine:
            raise Exception("Adaptation engine not available")
        
        adaptation_id = params["adaptation_id"]
        success = await self.adaptation_engine.apply_pending_adaptation(adaptation_id)
        
        return {
            "adaptation_id": adaptation_id,
            "applied": success,
            "timestamp": datetime.now().isoformat()
        }
    
    async def _handle_health_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle health check request."""
        health_status = {
            "api": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "codebase_adapter": "healthy",
                "database_adapter": "unknown",
                "pattern_engine": "unknown",
                "performance_tracker": "unknown",
                "adaptation_engine": "unknown"
            }
        }
        
        # Check database
        if self.database_adapter:
            db_health = await self.database_adapter.health_check()
            health_status["components"]["database_adapter"] = db_health["status"]
        
        # Check other components
        if self.pattern_engine:
            health_status["components"]["pattern_engine"] = "healthy"
        
        if self.performance_tracker:
            health_status["components"]["performance_tracker"] = "healthy"
        
        if self.adaptation_engine:
            health_status["components"]["adaptation_engine"] = "healthy"
        
        return health_status
    
    async def _handle_get_system_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get system status request."""
        status = {
            "initialized": self.initialized,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "codebase_adapter": bool(self.codebase_adapter),
                "database_adapter": bool(self.database_adapter),
                "pattern_engine": bool(self.pattern_engine),
                "performance_tracker": bool(self.performance_tracker),
                "adaptation_engine": bool(self.adaptation_engine)
            },
            "capabilities": {
                "codebase_analysis": True,
                "database_operations": bool(self.database_adapter),
                "pattern_recognition": bool(self.pattern_engine),
                "performance_tracking": bool(self.performance_tracker),
                "adaptive_learning": bool(self.adaptation_engine)
            }
        }
        
        # Add component statistics
        if self.codebase_adapter:
            status["statistics"] = self.codebase_adapter.get_adapter_stats()
        
        return status
    
    async def _handle_get_api_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get API info request."""
        return {
            "name": "Contexten Unified API",
            "version": "1.0.0",
            "description": "Unified API for the Contexten CI/CD system",
            "supported_versions": [v.value for v in APIVersion],
            "available_actions": list(self.request_handlers.keys()),
            "timestamp": datetime.now().isoformat(),
            "initialized": self.initialized
        }
    
    # Convenience methods
    
    async def quick_analyze(self, repository_url: str, analysis_type: str = "summary") -> APIResponse:
        """Quick codebase analysis."""
        request = APIRequest(
            action="analyze_codebase",
            parameters={
                "repository_url": repository_url,
                "analysis_type": analysis_type
            }
        )
        return await self.process_request(request)
    
    async def create_simple_project(self, org_id: str, name: str, repository_url: str) -> APIResponse:
        """Create a simple project."""
        request = APIRequest(
            action="create_project",
            parameters={
                "organization_id": org_id,
                "name": name,
                "slug": name.lower().replace(" ", "-"),
                "repository_url": repository_url
            }
        )
        return await self.process_request(request)
    
    def to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert object to dictionary for JSON serialization."""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                elif hasattr(value, '__dict__'):
                    result[key] = self.to_dict(value)
                elif isinstance(value, list):
                    result[key] = [self.to_dict(item) if hasattr(item, '__dict__') else item for item in value]
                else:
                    result[key] = value
            return result
        else:
            return obj


# Example usage
if __name__ == "__main__":
    async def example_usage():
        """Example usage of the unified API."""
        # Initialize API
        api = UnifiedAPI(enable_learning=True, enable_performance_tracking=True)
        await api.initialize()
        
        try:
            # Health check
            health_request = APIRequest(
                action="health_check",
                parameters={}
            )
            health_response = await api.process_request(health_request)
            print(f"Health check: {health_response.success}")
            
            # Analyze codebase
            analysis_response = await api.quick_analyze(
                "https://github.com/example/repo",
                "summary"
            )
            print(f"Analysis: {analysis_response.success}")
            
            # Get API info
            info_request = APIRequest(
                action="get_api_info",
                parameters={}
            )
            info_response = await api.process_request(info_request)
            print(f"API info: {info_response.data}")
            
        finally:
            await api.shutdown()
    
    asyncio.run(example_usage())


"""Base interface implementations for Contexten extensions."""

from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
import logging
import asyncio


logger = logging.getLogger(__name__)


class BaseExtension(ABC):
    """Base class for all Contexten extensions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the extension."""
        if self._initialized:
            return
        
        try:
            await self._initialize_impl()
            self._initialized = True
            self.logger.info(f"{self.__class__.__name__} initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize {self.__class__.__name__}: {e}")
            raise
    
    @abstractmethod
    async def _initialize_impl(self) -> None:
        """Implementation-specific initialization."""
        pass
    
    async def handle(self, payload: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
        """Handle incoming requests/events."""
        if not self._initialized:
            await self.initialize()
        
        try:
            return await self._handle_impl(payload, request)
        except Exception as e:
            self.logger.error(f"Error handling request in {self.__class__.__name__}: {e}")
            return {"error": str(e), "status": "failed"}
    
    @abstractmethod
    async def _handle_impl(self, payload: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
        """Implementation-specific request handling."""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get extension status."""
        return {
            "name": self.__class__.__name__,
            "initialized": self._initialized,
            "config": self.config,
            "status": "healthy" if self._initialized else "not_initialized"
        }


class BaseWorkflowClient(BaseExtension):
    """Base class for workflow client extensions."""
    
    @abstractmethod
    async def create_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """Create a new workflow."""
        pass
    
    @abstractmethod
    async def execute_workflow(self, workflow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow."""
        pass
    
    @abstractmethod
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution status."""
        pass


class BaseAnalysisEngine(BaseExtension):
    """Base class for analysis engine extensions."""
    
    @abstractmethod
    async def analyze_code(self, code_path: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze code at the given path."""
        pass
    
    @abstractmethod
    async def validate_pr(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a pull request."""
        pass
    
    @abstractmethod
    async def get_analysis_report(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis report."""
        pass


class BaseOrchestrator(BaseExtension):
    """Base class for orchestrator extensions."""
    
    @abstractmethod
    async def orchestrate_flow(self, flow_config: Dict[str, Any]) -> str:
        """Orchestrate a flow execution."""
        pass
    
    @abstractmethod
    async def schedule_task(self, task_config: Dict[str, Any]) -> str:
        """Schedule a task for execution."""
        pass
    
    @abstractmethod
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get flow execution status."""
        pass


class BaseQualityGate(BaseExtension):
    """Base class for quality gate extensions."""
    
    @abstractmethod
    async def validate_quality(self, validation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality gates."""
        pass
    
    @abstractmethod
    async def create_snapshot(self, snapshot_config: Dict[str, Any]) -> str:
        """Create a deployment snapshot."""
        pass
    
    @abstractmethod
    async def get_validation_results(self, validation_id: str) -> Dict[str, Any]:
        """Get validation results."""
        pass


class BaseDeploymentManager(BaseExtension):
    """Base class for deployment manager extensions."""
    
    @abstractmethod
    async def deploy(self, deployment_config: Dict[str, Any]) -> str:
        """Deploy infrastructure or application."""
        pass
    
    @abstractmethod
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status."""
        pass
    
    @abstractmethod
    async def rollback(self, deployment_id: str) -> Dict[str, Any]:
        """Rollback a deployment."""
        pass


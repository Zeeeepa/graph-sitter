"""Protocol definitions for Contexten extensions."""

from typing import Protocol, Any, Dict, List, Optional, Union
from abc import abstractmethod


class ExtensionProtocol(Protocol):
    """Base protocol for all Contexten extensions."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the extension."""
        ...
    
    @abstractmethod
    async def handle(self, payload: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
        """Handle incoming requests/events."""
        ...
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get extension status."""
        ...


class WorkflowProtocol(Protocol):
    """Protocol for workflow management extensions."""
    
    @abstractmethod
    async def create_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """Create a new workflow."""
        ...
    
    @abstractmethod
    async def execute_workflow(self, workflow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow."""
        ...
    
    @abstractmethod
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution status."""
        ...


class AnalysisProtocol(Protocol):
    """Protocol for code analysis extensions."""
    
    @abstractmethod
    async def analyze_code(self, code_path: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze code at the given path."""
        ...
    
    @abstractmethod
    async def validate_pr(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a pull request."""
        ...
    
    @abstractmethod
    async def get_analysis_report(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis report."""
        ...


class OrchestrationProtocol(Protocol):
    """Protocol for orchestration extensions."""
    
    @abstractmethod
    async def orchestrate_flow(self, flow_config: Dict[str, Any]) -> str:
        """Orchestrate a flow execution."""
        ...
    
    @abstractmethod
    async def schedule_task(self, task_config: Dict[str, Any]) -> str:
        """Schedule a task for execution."""
        ...
    
    @abstractmethod
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get flow execution status."""
        ...


class QualityGateProtocol(Protocol):
    """Protocol for quality gate extensions."""
    
    @abstractmethod
    async def validate_quality(self, validation_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality gates."""
        ...
    
    @abstractmethod
    async def create_snapshot(self, snapshot_config: Dict[str, Any]) -> str:
        """Create a deployment snapshot."""
        ...
    
    @abstractmethod
    async def get_validation_results(self, validation_id: str) -> Dict[str, Any]:
        """Get validation results."""
        ...


class DeploymentProtocol(Protocol):
    """Protocol for deployment extensions."""
    
    @abstractmethod
    async def deploy(self, deployment_config: Dict[str, Any]) -> str:
        """Deploy infrastructure or application."""
        ...
    
    @abstractmethod
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get deployment status."""
        ...
    
    @abstractmethod
    async def rollback(self, deployment_id: str) -> Dict[str, Any]:
        """Rollback a deployment."""
        ...


class EventHandlerManagerProtocol(Protocol):
    """Protocol for event handler managers."""
    
    @abstractmethod
    async def handle(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an event."""
        ...
    
    @abstractmethod
    def register_handler(self, event_type: str, handler: Any) -> None:
        """Register an event handler."""
        ...
    
    @abstractmethod
    def get_handlers(self, event_type: str) -> List[Any]:
        """Get handlers for an event type."""
        ...


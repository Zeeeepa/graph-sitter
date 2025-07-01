"""Base interfaces and protocols for Contexten extensions."""

from .protocols import (
    ExtensionProtocol,
    WorkflowProtocol,
    AnalysisProtocol,
    OrchestrationProtocol,
    QualityGateProtocol,
    DeploymentProtocol,
)

from .interfaces import (
    BaseExtension,
    BaseWorkflowClient,
    BaseAnalysisEngine,
    BaseOrchestrator,
    BaseQualityGate,
    BaseDeploymentManager,
)

__all__ = [
    # Protocols
    "ExtensionProtocol",
    "WorkflowProtocol", 
    "AnalysisProtocol",
    "OrchestrationProtocol",
    "QualityGateProtocol",
    "DeploymentProtocol",
    # Base Classes
    "BaseExtension",
    "BaseWorkflowClient",
    "BaseAnalysisEngine", 
    "BaseOrchestrator",
    "BaseQualityGate",
    "BaseDeploymentManager",
]


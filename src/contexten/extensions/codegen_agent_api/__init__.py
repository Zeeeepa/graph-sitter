"""
Codegen Agent API Extension for Contexten

Comprehensive Codegen integration providing:
- Agent and CodebaseAI interfaces with pip install overlay functionality
- Seamless integration with contexten ecosystem
- Webhook processing and event handling
- Configuration management and monitoring
- Fallback mechanisms and error handling

This extension follows the established contexten extension patterns
and provides overlay functionality to work with pip-installed codegen packages.
"""

# Core classes
from .codegen_agent_api import (
    CodegenAgentAPI,
    create_codegen_extension,
    create_agent_with_overlay,
    create_codebase_ai_with_overlay
)

# Configuration
from .config import (
    CodegenAgentAPIConfig,
    get_codegen_config,
    create_config_template,
    detect_pip_codegen,
    get_overlay_strategy
)

# Core functionality
from .agent import Agent
from .task import Task
from .codebase_ai import (
    CodebaseAI,
    initialize_codebase_ai,
    codebase_ai,
    improve_function,
    summarize_method,
    analyze_codebase,
    generate_docs,
    refactor_code,
    explain_code,
    find_bugs,
    optimize_performance,
    add_tests
)

# Overlay functionality
from .client import (
    OverlayClient,
    create_agent,
    create_codebase_ai
)

# Integration components
from .integration_agent import (
    CodegenIntegrationAgent,
    create_integration_agent
)

from .webhook_processor import (
    WebhookProcessor,
    create_task_completion_handler,
    create_task_failure_handler,
    create_progress_handler
)

# Type definitions
from .types import (
    # Enums
    TaskStatus,
    TaskPriority,
    OverlayStrategy,
    OverlayPriority,
    WebhookEventType,
    ErrorCode,
    
    # Core types
    TaskInfo,
    AgentStats,
    UsageStats,
    RepositoryInfo,
    WebhookInfo,
    ArtifactInfo,
    PipPackageInfo,
    OverlayInfo,
    
    # Request/Response types
    CreateTaskRequest,
    CreateTaskResponse,
    ListTasksRequest,
    ListTasksResponse,
    CreateWebhookRequest,
    CreateWebhookResponse,
    
    # CodebaseAI types
    CodebaseAITarget,
    CodebaseAIContext,
    CodebaseAIRequest,
    
    # Integration types
    IntegrationEvent,
    IntegrationStatus,
    ComponentStats,
    CodegenAgentAPIMetrics,
    
    # Dataclasses
    TaskProgress,
    TaskMetrics,
    AgentMetrics,
    ExtensionMetrics,
    WebhookEvent,
    
    # Callback types
    StatusCallback,
    ProgressCallback,
    WebhookCallback,
    ErrorCallback
)

# Exceptions
from .exceptions import (
    # Base exceptions
    CodegenError,
    ExtensionError,
    
    # Core exceptions
    AuthenticationError,
    APIError,
    RateLimitError,
    ValidationError,
    TaskError,
    TimeoutError,
    NetworkError,
    ConfigurationError,
    
    # Overlay exceptions
    OverlayError,
    PipPackageNotFoundError,
    PipPackageImportError,
    OverlayStrategyError,
    FallbackError,
    
    # Extension exceptions
    IntegrationError,
    WebhookError
)

__version__ = "1.0.0"
__author__ = "Contexten Team"

# Main extension class for easy access
CodegenExtension = CodegenAgentAPI

__all__ = [
    # Main extension class
    "CodegenAgentAPI",
    "CodegenExtension",  # Alias for consistency with other extensions
    
    # Factory functions
    "create_codegen_extension",
    "create_agent_with_overlay",
    "create_codebase_ai_with_overlay",
    
    # Configuration
    "CodegenAgentAPIConfig",
    "get_codegen_config",
    "create_config_template",
    "detect_pip_codegen",
    "get_overlay_strategy",
    
    # Core classes
    "Agent",
    "Task",
    "CodebaseAI",
    
    # Overlay functionality
    "OverlayClient",
    "create_agent",
    "create_codebase_ai",
    
    # Integration components
    "CodegenIntegrationAgent",
    "create_integration_agent",
    "WebhookProcessor",
    "create_task_completion_handler",
    "create_task_failure_handler",
    "create_progress_handler",
    
    # CodebaseAI global functions
    "initialize_codebase_ai",
    "codebase_ai",
    "improve_function",
    "summarize_method",
    "analyze_codebase",
    "generate_docs",
    "refactor_code",
    "explain_code",
    "find_bugs",
    "optimize_performance",
    "add_tests",
    
    # Enums
    "TaskStatus",
    "TaskPriority",
    "OverlayStrategy",
    "OverlayPriority",
    "WebhookEventType",
    "ErrorCode",
    
    # Core types
    "TaskInfo",
    "AgentStats",
    "UsageStats",
    "RepositoryInfo",
    "WebhookInfo",
    "ArtifactInfo",
    "PipPackageInfo",
    "OverlayInfo",
    
    # Request/Response types
    "CreateTaskRequest",
    "CreateTaskResponse",
    "ListTasksRequest",
    "ListTasksResponse",
    "CreateWebhookRequest",
    "CreateWebhookResponse",
    
    # CodebaseAI types
    "CodebaseAITarget",
    "CodebaseAIContext",
    "CodebaseAIRequest",
    
    # Integration types
    "IntegrationEvent",
    "IntegrationStatus",
    "ComponentStats",
    "CodegenAgentAPIMetrics",
    
    # Dataclasses
    "TaskProgress",
    "TaskMetrics",
    "AgentMetrics",
    "ExtensionMetrics",
    "WebhookEvent",
    
    # Callback types
    "StatusCallback",
    "ProgressCallback",
    "WebhookCallback",
    "ErrorCallback",
    
    # Base exceptions
    "CodegenError",
    "ExtensionError",
    
    # Core exceptions
    "AuthenticationError",
    "APIError",
    "RateLimitError",
    "ValidationError",
    "TaskError",
    "TimeoutError",
    "NetworkError",
    "ConfigurationError",
    
    # Overlay exceptions
    "OverlayError",
    "PipPackageNotFoundError",
    "PipPackageImportError",
    "OverlayStrategyError",
    "FallbackError",
    
    # Extension exceptions
    "IntegrationError",
    "WebhookError",
]


# Extension metadata for contexten
EXTENSION_INFO = {
    "name": "codegen_agent_api",
    "version": __version__,
    "description": "Codegen Agent API extension with pip install overlay functionality",
    "author": __author__,
    "main_class": "CodegenAgentAPI",
    "overlay_support": True,
    "pip_package": "codegen",
    "dependencies": ["requests", "typing_extensions"],
    "optional_dependencies": ["flask"],
    "contexten_version": ">=1.0.0"
}


def get_extension_info() -> dict:
    """Get extension metadata."""
    return EXTENSION_INFO.copy()


def get_version() -> str:
    """Get extension version."""
    return __version__


def get_overlay_status() -> dict:
    """Get current overlay status."""
    try:
        pip_info = detect_pip_codegen()
        return {
            "pip_available": pip_info is not None,
            "pip_info": pip_info,
            "local_available": True,  # Local implementation is always available
            "extension_version": __version__
        }
    except Exception as e:
        return {
            "pip_available": False,
            "pip_info": None,
            "local_available": True,
            "error": str(e),
            "extension_version": __version__
        }


# Add convenience functions to module level
def quick_start(org_id: str, token: str, **kwargs) -> CodegenAgentAPI:
    """
    Quick start function to create a configured extension instance.
    
    Args:
        org_id: Organization ID
        token: API token
        **kwargs: Additional configuration
        
    Returns:
        Configured CodegenAgentAPI instance
    """
    return create_codegen_extension(org_id=org_id, token=token, **kwargs)


def create_simple_agent(org_id: str, token: str, **kwargs):
    """
    Create a simple Agent instance with minimal configuration.
    
    Args:
        org_id: Organization ID
        token: API token
        **kwargs: Additional Agent parameters
        
    Returns:
        Agent instance
    """
    return create_agent_with_overlay(org_id=org_id, token=token, **kwargs)


def create_simple_codebase_ai(org_id: str, token: str, **kwargs):
    """
    Create a simple CodebaseAI instance with minimal configuration.
    
    Args:
        org_id: Organization ID
        token: API token
        **kwargs: Additional CodebaseAI parameters
        
    Returns:
        CodebaseAI instance
    """
    return create_codebase_ai_with_overlay(org_id=org_id, token=token, **kwargs)


# Add to __all__
__all__.extend([
    "get_extension_info",
    "get_version", 
    "get_overlay_status",
    "quick_start",
    "create_simple_agent",
    "create_simple_codebase_ai"
])


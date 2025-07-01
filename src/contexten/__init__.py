"""
Contexten - Agentic Orchestrator

An intelligent agent orchestration framework with chat capabilities, 
GitHub/Linear integrations, and workflow automation.
"""

__version__ = "0.1.0"

# Core imports for easy access - with error handling for missing dependencies
try:
    from contexten.agents.base_agent import BaseAgent
except ImportError:
    BaseAgent = None

try:
    from contexten.flows.flow_manager import FlowManager
except ImportError:
    # Create a placeholder if FlowManager is not available
    class FlowManager:
        def __init__(self, *args, **kwargs):
            raise ImportError("FlowManager requires additional dependencies. Please ensure all contexten dependencies are installed.")

__all__ = [
    "BaseAgent",
    "FlowManager",
    "__version__",
]


"""
Workflow orchestration system for the Dashboard extension.

This module provides multi-layered workflow orchestration capabilities:
- Top layer: Prefect flows for high-level workflow management
- Middle layer: ControlFlow system for task orchestration  
- Bottom layer: Granular agentic flows with MCP integration

The orchestration system manages the complete lifecycle of development workflows
from plan generation to task execution and quality validation.
"""

from .orchestrator import WorkflowOrchestrator
from .prefect_integration import PrefectFlowManager
from .controlflow_integration import ControlFlowManager
from .mcp_integration import MCPAgentManager

__all__ = [
    "WorkflowOrchestrator",
    "PrefectFlowManager", 
    "ControlFlowManager",
    "MCPAgentManager",
]


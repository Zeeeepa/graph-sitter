"""
Flow Orchestration Extension for Contexten

This extension provides comprehensive flow orchestration capabilities integrating:
- ControlFlow: Agent orchestration framework
- Prefect: Workflow monitoring and management  
- Strands: Core agent functionality with MCP integration

The flow system enables automated task execution, workflow management,
and real-time monitoring for complex multi-agent operations.
"""

from .flow_manager import FlowManager
from .orchestrator import FlowOrchestrator, FlowStatus, FlowPriority
from .executor import FlowExecutor, ExecutionContext
from .scheduler import FlowScheduler, SchedulingStrategy

# Import framework-specific components
from .controlflow import FlowOrchestrator as ControlFlowOrchestrator
from .prefect import PrefectFlow, PrefectMonitor
from .strands import StrandAgent, StrandWorkflow, MCPClient

__all__ = [
    # Core components
    'FlowManager',
    'FlowOrchestrator', 
    'FlowExecutor',
    'FlowScheduler',
    
    # Enums and utilities
    'FlowStatus',
    'FlowPriority',
    'SchedulingStrategy',
    'ExecutionContext',
    
    # Framework-specific
    'ControlFlowOrchestrator',
    'PrefectFlow',
    'PrefectMonitor',
    'StrandAgent',
    'StrandWorkflow',
    'MCPClient'
]


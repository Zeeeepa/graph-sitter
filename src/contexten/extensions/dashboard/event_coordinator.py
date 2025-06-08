"""
Event Coordinator

Central event bus for cross-extension communication.
Enhanced with sophisticated event routing and loop prevention.
"""

import logging
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime

from graph_sitter.shared.logging.get_logger import get_logger
from .models import WorkflowEvent
from .event_bus import EventBus, EventPriority, EventRule

logger = get_logger(__name__)


class EventCoordinator:
    """
    Enhanced event coordinator that uses the central event bus for 
    sophisticated cross-extension communication.
    """
    
    def __init__(self, dashboard):
        self.dashboard = dashboard
        self.event_bus = EventBus(dashboard)
        self.event_history: List[WorkflowEvent] = []
        
    async def initialize(self):
        """Initialize the event coordinator"""
        logger.info("Initializing EventCoordinator...")
        
        # Register dashboard extension with event bus
        self.event_bus.register_extension("dashboard", self.dashboard)
        
        # Setup dashboard-specific event handlers
        self._setup_dashboard_handlers()
        
        # Start the event bus
        await self.event_bus.start()
        
    def _setup_dashboard_handlers(self):
        """Setup dashboard-specific event handlers"""
        
        # Project events
        self.event_bus.subscribe("project.created", self._handle_project_created)
        self.event_bus.subscribe("project.updated", self._handle_project_updated)
        self.event_bus.subscribe("project.pinned", self._handle_project_pinned)
        
        # Plan events
        self.event_bus.subscribe("plan.generated", self._handle_plan_generated)
        self.event_bus.subscribe("plan.updated", self._handle_plan_updated)
        
        # Workflow events
        self.event_bus.subscribe("workflow.started", self._handle_workflow_started)
        self.event_bus.subscribe("workflow.stopped", self._handle_workflow_stopped)
        self.event_bus.subscribe("task.completed", self._handle_task_completed)
        
        # Quality gate events
        self.event_bus.subscribe("quality_gate.completed", self._handle_quality_gate_completed)
        
    async def _handle_project_created(self, data: Dict[str, Any], context):
        """Handle project creation events"""
        logger.info(f"Project created: {data.get('project_id')}")
        
        # Emit follow-up events
        await self.event_bus.emit(
            "project.setup_required",
            data,
            source="dashboard",
            priority=EventPriority.HIGH,
            correlation_id=context.correlation_id
        )
    
    async def _handle_project_updated(self, data: Dict[str, Any], context):
        """Handle project update events"""
        logger.info(f"Project updated: {data.get('project_id')}")
    
    async def _handle_project_pinned(self, data: Dict[str, Any], context):
        """Handle project pinning events"""
        logger.info(f"Project pinned: {data.get('project_id')}")
        
        # Trigger initial project analysis
        await self.event_bus.emit(
            "project.analyze_required",
            data,
            source="dashboard",
            priority=EventPriority.NORMAL,
            correlation_id=context.correlation_id
        )
    
    async def _handle_plan_generated(self, data: Dict[str, Any], context):
        """Handle plan generation events"""
        logger.info(f"Plan generated: {data.get('plan_id')} for project {data.get('project_id')}")
        
        # Notify relevant extensions
        await self.event_bus.emit(
            "linear.create_issues",
            data,
            source="dashboard",
            priority=EventPriority.HIGH,
            correlation_id=context.correlation_id
        )
    
    async def _handle_plan_updated(self, data: Dict[str, Any], context):
        """Handle plan update events"""
        logger.info(f"Plan updated: {data.get('plan_id')}")
    
    async def _handle_workflow_started(self, data: Dict[str, Any], context):
        """Handle workflow start events"""
        logger.info(f"Workflow started for project: {data.get('project_id')}")
        
        # Notify Slack if configured
        await self.event_bus.emit(
            "slack.notify",
            {
                **data,
                "message": f"Workflow started for project {data.get('project_name', data.get('project_id'))}"
            },
            source="dashboard",
            priority=EventPriority.NORMAL,
            correlation_id=context.correlation_id
        )
    
    async def _handle_workflow_stopped(self, data: Dict[str, Any], context):
        """Handle workflow stop events"""
        logger.info(f"Workflow stopped for project: {data.get('project_id')}")
    
    async def _handle_task_completed(self, data: Dict[str, Any], context):
        """Handle task completion events"""
        logger.info(f"Task completed: {data.get('task_id')}")
        
        # Update Linear issue status
        await self.event_bus.emit(
            "linear.update_issue",
            {
                **data,
                "status": "completed"
            },
            source="dashboard",
            priority=EventPriority.HIGH,
            correlation_id=context.correlation_id
        )
        
        # Trigger quality gates if this was a code task
        if data.get("task_type") == "code":
            await self.event_bus.emit(
                "quality_gate.run",
                data,
                source="dashboard",
                priority=EventPriority.HIGH,
                correlation_id=context.correlation_id
            )
    
    async def _handle_quality_gate_completed(self, data: Dict[str, Any], context):
        """Handle quality gate completion events"""
        logger.info(f"Quality gate completed: {data.get('gate_name')} - {data.get('status')}")
        
        if data.get("status") == "failed":
            # Notify about quality gate failure
            await self.event_bus.emit(
                "slack.notify",
                {
                    **data,
                    "message": f"Quality gate {data.get('gate_name')} failed for {data.get('project_id')}"
                },
                source="dashboard",
                priority=EventPriority.CRITICAL,
                correlation_id=context.correlation_id
            )
    
    async def handle_event(self, event_type: str, data: Dict[str, Any]):
        """Handle incoming events from external sources"""
        logger.info(f"Handling external event: {event_type}")
        
        # Route through event bus for proper coordination
        await self.event_bus.emit(
            event_type,
            data,
            source=data.get("source", "external"),
            priority=EventPriority.NORMAL
        )
    
    def register_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        self.event_bus.subscribe(event_type, handler)
    
    async def emit_event(self, event_type: str, project_id: str, message: str, 
                        source: str = "dashboard", priority: str = "normal", **kwargs):
        """Emit a new event"""
        priority_enum = getattr(EventPriority, priority.upper(), EventPriority.NORMAL)
        
        data = {
            "project_id": project_id,
            "source": source,
            "message": message,
            **kwargs
        }
        
        await self.event_bus.emit(event_type, data, source=source, priority=priority_enum)
    
    def get_recent_events(self, project_id: Optional[str] = None, limit: int = 50) -> List[WorkflowEvent]:
        """Get recent events, optionally filtered by project"""
        events = self.event_history
        
        if project_id:
            events = [e for e in events if e.project_id == project_id]
        
        # Return most recent events
        return sorted(events, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def add_routing_rule(self, rule: EventRule):
        """Add a custom event routing rule"""
        self.event_bus.add_rule(rule)
    
    def register_extension(self, name: str, extension: Any):
        """Register an extension with the event bus"""
        self.event_bus.register_extension(name, extension)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get event coordination metrics"""
        return self.event_bus.get_metrics()
    
    async def stop(self):
        """Stop the event coordinator"""
        logger.info("Stopping EventCoordinator...")
        await self.event_bus.stop()


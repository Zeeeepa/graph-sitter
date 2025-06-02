"""
Flow Management System

Comprehensive flow management with parameter configuration, progress tracking,
and template management for the contexten autonomous CI/CD system.
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

from pydantic import BaseModel, Field, validator
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class FlowStatus(Enum):
    """Flow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FlowPriority(Enum):
    """Flow execution priority."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FlowParameter:
    """Individual flow parameter definition."""
    name: str
    type: str  # string, integer, boolean, array, object
    description: str
    required: bool = True
    default: Any = None
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    options: Optional[List[Any]] = None  # For enum-like parameters


@dataclass
class FlowTemplate:
    """Flow template definition."""
    id: str
    name: str
    description: str
    category: str
    parameters: List[FlowParameter]
    workflow_type: str
    estimated_duration: int  # minutes
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class FlowExecution:
    """Flow execution instance."""
    id: str
    template_id: str
    name: str
    status: FlowStatus
    priority: FlowPriority
    parameters: Dict[str, Any]
    project_id: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0
    current_stage: Optional[str] = None
    stages: List[Dict[str, Any]] = field(default_factory=list)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    result: Optional[Dict[str, Any]] = None


class FlowParameterValidator:
    """Validates flow parameters against their definitions."""
    
    @staticmethod
    def validate_parameter(param: FlowParameter, value: Any) -> tuple[bool, Optional[str]]:
        """Validate a single parameter value."""
        try:
            # Check required
            if param.required and value is None:
                return False, f"Parameter '{param.name}' is required"
            
            if value is None:
                return True, None
            
            # Type validation
            if param.type == "string" and not isinstance(value, str):
                return False, f"Parameter '{param.name}' must be a string"
            elif param.type == "integer" and not isinstance(value, int):
                return False, f"Parameter '{param.name}' must be an integer"
            elif param.type == "boolean" and not isinstance(value, bool):
                return False, f"Parameter '{param.name}' must be a boolean"
            elif param.type == "array" and not isinstance(value, list):
                return False, f"Parameter '{param.name}' must be an array"
            elif param.type == "object" and not isinstance(value, dict):
                return False, f"Parameter '{param.name}' must be an object"
            
            # Options validation
            if param.options and value not in param.options:
                return False, f"Parameter '{param.name}' must be one of {param.options}"
            
            # Custom validation rules
            for rule_name, rule_value in param.validation_rules.items():
                if rule_name == "min_length" and len(str(value)) < rule_value:
                    return False, f"Parameter '{param.name}' must be at least {rule_value} characters"
                elif rule_name == "max_length" and len(str(value)) > rule_value:
                    return False, f"Parameter '{param.name}' must be at most {rule_value} characters"
                elif rule_name == "min_value" and isinstance(value, (int, float)) and value < rule_value:
                    return False, f"Parameter '{param.name}' must be at least {rule_value}"
                elif rule_name == "max_value" and isinstance(value, (int, float)) and value > rule_value:
                    return False, f"Parameter '{param.name}' must be at most {rule_value}"
                elif rule_name == "pattern" and isinstance(value, str):
                    import re
                    if not re.match(rule_value, value):
                        return False, f"Parameter '{param.name}' does not match required pattern"
            
            return True, None
            
        except Exception as e:
            return False, f"Validation error for parameter '{param.name}': {str(e)}"
    
    @staticmethod
    def validate_parameters(template: FlowTemplate, parameters: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate all parameters for a flow template."""
        errors = []
        
        for param in template.parameters:
            value = parameters.get(param.name)
            is_valid, error = FlowParameterValidator.validate_parameter(param, value)
            if not is_valid:
                errors.append(error)
        
        return len(errors) == 0, errors


class FlowProgressTracker:
    """Tracks and manages flow execution progress."""
    
    def __init__(self):
        self.active_flows: Dict[str, FlowExecution] = {}
        self.websocket_connections: Dict[str, List[WebSocket]] = {}
    
    async def start_flow(self, flow: FlowExecution) -> bool:
        """Start tracking a flow execution."""
        try:
            flow.status = FlowStatus.RUNNING
            flow.started_at = datetime.now()
            self.active_flows[flow.id] = flow
            
            await self._broadcast_flow_update(flow)
            logger.info(f"Started tracking flow {flow.id}: {flow.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start flow tracking: {e}")
            return False
    
    async def update_progress(self, flow_id: str, progress: float, stage: str = None, logs: List[Dict] = None):
        """Update flow progress and broadcast to connected clients."""
        if flow_id not in self.active_flows:
            logger.warning(f"Attempted to update non-existent flow: {flow_id}")
            return
        
        flow = self.active_flows[flow_id]
        flow.progress = max(0.0, min(1.0, progress))  # Clamp between 0 and 1
        
        if stage:
            flow.current_stage = stage
        
        if logs:
            flow.logs.extend(logs)
        
        await self._broadcast_flow_update(flow)
    
    async def complete_flow(self, flow_id: str, success: bool, result: Dict[str, Any] = None, error: str = None):
        """Mark a flow as completed."""
        if flow_id not in self.active_flows:
            logger.warning(f"Attempted to complete non-existent flow: {flow_id}")
            return
        
        flow = self.active_flows[flow_id]
        flow.completed_at = datetime.now()
        flow.progress = 1.0
        flow.status = FlowStatus.COMPLETED if success else FlowStatus.FAILED
        
        if result:
            flow.result = result
        
        if error:
            flow.error_message = error
        
        await self._broadcast_flow_update(flow)
        logger.info(f"Flow {flow_id} completed with status: {flow.status}")
    
    async def add_websocket_connection(self, flow_id: str, websocket: WebSocket):
        """Add a WebSocket connection for flow updates."""
        if flow_id not in self.websocket_connections:
            self.websocket_connections[flow_id] = []
        
        self.websocket_connections[flow_id].append(websocket)
        
        # Send current flow state if it exists
        if flow_id in self.active_flows:
            await self._send_flow_update(websocket, self.active_flows[flow_id])
    
    async def remove_websocket_connection(self, flow_id: str, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if flow_id in self.websocket_connections:
            try:
                self.websocket_connections[flow_id].remove(websocket)
                if not self.websocket_connections[flow_id]:
                    del self.websocket_connections[flow_id]
            except ValueError:
                pass  # Connection not in list
    
    async def _broadcast_flow_update(self, flow: FlowExecution):
        """Broadcast flow update to all connected WebSocket clients."""
        if flow.id not in self.websocket_connections:
            return
        
        connections = self.websocket_connections[flow.id].copy()
        for websocket in connections:
            try:
                await self._send_flow_update(websocket, flow)
            except WebSocketDisconnect:
                await self.remove_websocket_connection(flow.id, websocket)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                await self.remove_websocket_connection(flow.id, websocket)
    
    async def _send_flow_update(self, websocket: WebSocket, flow: FlowExecution):
        """Send flow update to a specific WebSocket connection."""
        update_data = {
            "type": "flow_update",
            "flow_id": flow.id,
            "status": flow.status.value,
            "progress": flow.progress,
            "current_stage": flow.current_stage,
            "logs": flow.logs[-10:] if flow.logs else [],  # Last 10 log entries
            "timestamp": datetime.now().isoformat()
        }
        
        await websocket.send_json(update_data)


class FlowTemplateManager:
    """Manages flow templates and their lifecycle."""
    
    def __init__(self):
        self.templates: Dict[str, FlowTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default flow templates."""
        # Feature Development Template
        feature_template = FlowTemplate(
            id="feature_development",
            name="Feature Development",
            description="Complete feature development workflow from requirements to deployment",
            category="Development",
            workflow_type="feature_development",
            estimated_duration=120,
            parameters=[
                FlowParameter(
                    name="feature_name",
                    type="string",
                    description="Name of the feature to develop",
                    validation_rules={"min_length": 3, "max_length": 100}
                ),
                FlowParameter(
                    name="requirements",
                    type="string",
                    description="Detailed feature requirements",
                    validation_rules={"min_length": 10}
                ),
                FlowParameter(
                    name="priority",
                    type="string",
                    description="Feature priority level",
                    options=["low", "normal", "high", "critical"],
                    default="normal"
                ),
                FlowParameter(
                    name="target_branch",
                    type="string",
                    description="Target branch for the feature",
                    default="develop"
                ),
                FlowParameter(
                    name="create_tests",
                    type="boolean",
                    description="Whether to create automated tests",
                    default=True
                ),
                FlowParameter(
                    name="reviewers",
                    type="array",
                    description="List of code reviewers",
                    required=False
                )
            ],
            tags=["development", "feature", "automation"]
        )
        
        # Bug Fix Template
        bug_fix_template = FlowTemplate(
            id="bug_fix",
            name="Bug Fix",
            description="Automated bug investigation and fix workflow",
            category="Maintenance",
            workflow_type="bug_fix",
            estimated_duration=60,
            parameters=[
                FlowParameter(
                    name="bug_description",
                    type="string",
                    description="Description of the bug to fix",
                    validation_rules={"min_length": 10}
                ),
                FlowParameter(
                    name="reproduction_steps",
                    type="string",
                    description="Steps to reproduce the bug",
                    required=False
                ),
                FlowParameter(
                    name="severity",
                    type="string",
                    description="Bug severity level",
                    options=["low", "medium", "high", "critical"],
                    default="medium"
                ),
                FlowParameter(
                    name="affected_components",
                    type="array",
                    description="List of affected system components",
                    required=False
                ),
                FlowParameter(
                    name="hotfix",
                    type="boolean",
                    description="Whether this is a hotfix requiring immediate deployment",
                    default=False
                )
            ],
            tags=["bugfix", "maintenance", "automation"]
        )
        
        # Code Review Template
        code_review_template = FlowTemplate(
            id="code_review",
            name="Automated Code Review",
            description="Comprehensive automated code review with AI analysis",
            category="Quality",
            workflow_type="code_review",
            estimated_duration=30,
            parameters=[
                FlowParameter(
                    name="pr_url",
                    type="string",
                    description="GitHub Pull Request URL",
                    validation_rules={"pattern": r"https://github\.com/.+/pull/\d+"}
                ),
                FlowParameter(
                    name="review_depth",
                    type="string",
                    description="Depth of code review analysis",
                    options=["basic", "standard", "comprehensive"],
                    default="standard"
                ),
                FlowParameter(
                    name="check_security",
                    type="boolean",
                    description="Include security vulnerability analysis",
                    default=True
                ),
                FlowParameter(
                    name="check_performance",
                    type="boolean",
                    description="Include performance impact analysis",
                    default=True
                ),
                FlowParameter(
                    name="auto_approve",
                    type="boolean",
                    description="Automatically approve if all checks pass",
                    default=False
                )
            ],
            tags=["review", "quality", "automation"]
        )
        
        self.templates = {
            template.id: template
            for template in [feature_template, bug_fix_template, code_review_template]
        }
    
    def get_template(self, template_id: str) -> Optional[FlowTemplate]:
        """Get a flow template by ID."""
        return self.templates.get(template_id)
    
    def list_templates(self, category: str = None) -> List[FlowTemplate]:
        """List all templates, optionally filtered by category."""
        templates = list(self.templates.values())
        if category:
            templates = [t for t in templates if t.category.lower() == category.lower()]
        return sorted(templates, key=lambda t: t.name)
    
    def create_template(self, template: FlowTemplate) -> bool:
        """Create a new flow template."""
        try:
            if template.id in self.templates:
                logger.warning(f"Template {template.id} already exists")
                return False
            
            template.created_at = datetime.now()
            template.updated_at = datetime.now()
            self.templates[template.id] = template
            
            logger.info(f"Created new template: {template.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create template: {e}")
            return False
    
    def update_template(self, template_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing flow template."""
        try:
            if template_id not in self.templates:
                logger.warning(f"Template {template_id} not found")
                return False
            
            template = self.templates[template_id]
            
            # Update allowed fields
            allowed_fields = ['name', 'description', 'category', 'parameters', 'estimated_duration', 'tags']
            for field, value in updates.items():
                if field in allowed_fields:
                    setattr(template, field, value)
            
            template.updated_at = datetime.now()
            
            logger.info(f"Updated template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update template: {e}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """Delete a flow template."""
        try:
            if template_id not in self.templates:
                logger.warning(f"Template {template_id} not found")
                return False
            
            del self.templates[template_id]
            logger.info(f"Deleted template: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete template: {e}")
            return False


class FlowManager:
    """Main flow management coordinator."""
    
    def __init__(self):
        self.template_manager = FlowTemplateManager()
        self.progress_tracker = FlowProgressTracker()
        self.executions: Dict[str, FlowExecution] = {}
    
    async def create_flow(self, template_id: str, parameters: Dict[str, Any], 
                         name: str = None, priority: FlowPriority = FlowPriority.NORMAL,
                         project_id: str = None, created_by: str = None) -> Optional[FlowExecution]:
        """Create a new flow execution."""
        try:
            template = self.template_manager.get_template(template_id)
            if not template:
                logger.error(f"Template {template_id} not found")
                return None
            
            # Validate parameters
            is_valid, errors = FlowParameterValidator.validate_parameters(template, parameters)
            if not is_valid:
                logger.error(f"Parameter validation failed: {errors}")
                return None
            
            # Fill in default values
            final_parameters = {}
            for param in template.parameters:
                if param.name in parameters:
                    final_parameters[param.name] = parameters[param.name]
                elif param.default is not None:
                    final_parameters[param.name] = param.default
            
            # Create flow execution
            flow = FlowExecution(
                id=str(uuid.uuid4()),
                template_id=template_id,
                name=name or f"{template.name} - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
                status=FlowStatus.PENDING,
                priority=priority,
                parameters=final_parameters,
                project_id=project_id,
                created_by=created_by
            )
            
            self.executions[flow.id] = flow
            logger.info(f"Created flow execution: {flow.id}")
            return flow
            
        except Exception as e:
            logger.error(f"Failed to create flow: {e}")
            return None
    
    async def start_flow(self, flow_id: str) -> bool:
        """Start a flow execution."""
        try:
            if flow_id not in self.executions:
                logger.error(f"Flow {flow_id} not found")
                return False
            
            flow = self.executions[flow_id]
            if flow.status != FlowStatus.PENDING:
                logger.error(f"Flow {flow_id} is not in pending status")
                return False
            
            await self.progress_tracker.start_flow(flow)
            logger.info(f"Started flow: {flow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start flow: {e}")
            return False
    
    async def stop_flow(self, flow_id: str) -> bool:
        """Stop a running flow."""
        try:
            if flow_id not in self.executions:
                logger.error(f"Flow {flow_id} not found")
                return False
            
            flow = self.executions[flow_id]
            if flow.status not in [FlowStatus.RUNNING, FlowStatus.PAUSED]:
                logger.error(f"Flow {flow_id} is not running")
                return False
            
            flow.status = FlowStatus.CANCELLED
            flow.completed_at = datetime.now()
            
            await self.progress_tracker._broadcast_flow_update(flow)
            logger.info(f"Stopped flow: {flow_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop flow: {e}")
            return False
    
    def get_flow(self, flow_id: str) -> Optional[FlowExecution]:
        """Get a flow execution by ID."""
        return self.executions.get(flow_id)
    
    def list_flows(self, status: FlowStatus = None, project_id: str = None) -> List[FlowExecution]:
        """List flow executions with optional filtering."""
        flows = list(self.executions.values())
        
        if status:
            flows = [f for f in flows if f.status == status]
        
        if project_id:
            flows = [f for f in flows if f.project_id == project_id]
        
        return sorted(flows, key=lambda f: f.created_at, reverse=True)
    
    async def update_flow_progress(self, flow_id: str, progress: float, stage: str = None, logs: List[Dict] = None):
        """Update flow progress."""
        await self.progress_tracker.update_progress(flow_id, progress, stage, logs)
    
    async def complete_flow(self, flow_id: str, success: bool, result: Dict[str, Any] = None, error: str = None):
        """Complete a flow execution."""
        await self.progress_tracker.complete_flow(flow_id, success, result, error)


# Global flow manager instance
flow_manager = FlowManager()


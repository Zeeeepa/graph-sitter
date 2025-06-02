"""
Linear Workflow Automation

Automated workflow management for Linear integration.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from ..types import LinearIssue, LinearProject, LinearUser, LinearIssueState, LinearIssuePriority
from ..enhanced_client import EnhancedLinearClient

logger = logging.getLogger(__name__)


class WorkflowTrigger(Enum):
    """Workflow trigger types"""
    ISSUE_CREATED = "issue_created"
    ISSUE_UPDATED = "issue_updated"
    ISSUE_COMPLETED = "issue_completed"
    ISSUE_ASSIGNED = "issue_assigned"
    PROJECT_CREATED = "project_created"
    PROJECT_COMPLETED = "project_completed"
    COMMENT_ADDED = "comment_added"
    SCHEDULE_DAILY = "schedule_daily"
    SCHEDULE_WEEKLY = "schedule_weekly"


class WorkflowAction(Enum):
    """Workflow action types"""
    CREATE_ISSUE = "create_issue"
    UPDATE_ISSUE = "update_issue"
    ASSIGN_ISSUE = "assign_issue"
    ADD_COMMENT = "add_comment"
    SEND_NOTIFICATION = "send_notification"
    CREATE_PROJECT = "create_project"
    SYNC_GITHUB = "sync_github"
    ANALYZE_CODE = "analyze_code"


@dataclass
class WorkflowRule:
    """Workflow automation rule"""
    id: str
    name: str
    description: str
    trigger: WorkflowTrigger
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    
    def matches_conditions(self, event_data: Dict[str, Any]) -> bool:
        """Check if event data matches rule conditions"""
        if not self.conditions:
            return True
        
        for condition in self.conditions:
            if not self._evaluate_condition(condition, event_data):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """Evaluate a single condition"""
        field_path = condition.get("field", "")
        operator = condition.get("operator", "equals")
        expected_value = condition.get("value")
        
        # Get actual value from event data
        actual_value = self._get_nested_value(event_data, field_path)
        
        # Evaluate based on operator
        if operator == "equals":
            return actual_value == expected_value
        elif operator == "not_equals":
            return actual_value != expected_value
        elif operator == "contains":
            return expected_value in str(actual_value) if actual_value else False
        elif operator == "starts_with":
            return str(actual_value).startswith(str(expected_value)) if actual_value else False
        elif operator == "ends_with":
            return str(actual_value).endswith(str(expected_value)) if actual_value else False
        elif operator == "greater_than":
            return float(actual_value) > float(expected_value) if actual_value else False
        elif operator == "less_than":
            return float(actual_value) < float(expected_value) if actual_value else False
        elif operator == "is_empty":
            return not actual_value
        elif operator == "is_not_empty":
            return bool(actual_value)
        
        return False
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from data using dot notation"""
        keys = field_path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value


@dataclass
class WorkflowExecution:
    """Workflow execution record"""
    id: str
    rule_id: str
    trigger_event: Dict[str, Any]
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "running"  # running, completed, failed
    actions_executed: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> Optional[timedelta]:
        """Get execution duration"""
        if self.completed_at:
            return self.completed_at - self.started_at
        return None
    
    @property
    def is_completed(self) -> bool:
        """Check if execution is completed"""
        return self.status in ["completed", "failed"]


class WorkflowAutomation:
    """Linear workflow automation engine"""
    
    def __init__(self, linear_client: EnhancedLinearClient):
        self.linear_client = linear_client
        self.rules: Dict[str, WorkflowRule] = {}
        self.executions: Dict[str, WorkflowExecution] = {}
        self.action_handlers: Dict[WorkflowAction, Callable] = {}
        self._running = False
        self._setup_default_handlers()
        
        logger.info("Workflow automation initialized")
    
    def _setup_default_handlers(self):
        """Setup default action handlers"""
        self.action_handlers = {
            WorkflowAction.CREATE_ISSUE: self._handle_create_issue,
            WorkflowAction.UPDATE_ISSUE: self._handle_update_issue,
            WorkflowAction.ASSIGN_ISSUE: self._handle_assign_issue,
            WorkflowAction.ADD_COMMENT: self._handle_add_comment,
            WorkflowAction.SEND_NOTIFICATION: self._handle_send_notification,
            WorkflowAction.CREATE_PROJECT: self._handle_create_project,
            WorkflowAction.SYNC_GITHUB: self._handle_sync_github,
            WorkflowAction.ANALYZE_CODE: self._handle_analyze_code,
        }
    
    def add_rule(self, rule: WorkflowRule):
        """Add a workflow rule"""
        self.rules[rule.id] = rule
        logger.info(f"Added workflow rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Remove a workflow rule"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed workflow rule: {rule_id}")
    
    def get_rule(self, rule_id: str) -> Optional[WorkflowRule]:
        """Get a workflow rule by ID"""
        return self.rules.get(rule_id)
    
    def list_rules(self, enabled_only: bool = False) -> List[WorkflowRule]:
        """List all workflow rules"""
        rules = list(self.rules.values())
        if enabled_only:
            rules = [rule for rule in rules if rule.enabled]
        return rules
    
    async def trigger_workflow(self, trigger: WorkflowTrigger, event_data: Dict[str, Any]) -> List[WorkflowExecution]:
        """Trigger workflows for a specific event"""
        executions = []
        
        # Find matching rules
        matching_rules = [
            rule for rule in self.rules.values()
            if rule.enabled and rule.trigger == trigger and rule.matches_conditions(event_data)
        ]
        
        logger.info(f"Found {len(matching_rules)} matching rules for trigger {trigger.value}")
        
        # Execute matching rules
        for rule in matching_rules:
            try:
                execution = await self._execute_rule(rule, event_data)
                executions.append(execution)
            except Exception as e:
                logger.error(f"Failed to execute rule {rule.id}: {e}")
        
        return executions
    
    async def _execute_rule(self, rule: WorkflowRule, event_data: Dict[str, Any]) -> WorkflowExecution:
        """Execute a workflow rule"""
        execution_id = f"exec_{rule.id}_{int(datetime.now().timestamp())}"
        execution = WorkflowExecution(
            id=execution_id,
            rule_id=rule.id,
            trigger_event=event_data,
            started_at=datetime.now()
        )
        
        self.executions[execution_id] = execution
        
        try:
            logger.info(f"Executing workflow rule: {rule.name}")
            
            # Execute actions
            for action_config in rule.actions:
                try:
                    await self._execute_action(action_config, event_data, execution)
                except Exception as e:
                    error_msg = f"Action failed: {e}"
                    execution.errors.append(error_msg)
                    logger.error(error_msg)
            
            # Update rule statistics
            rule.last_executed = datetime.now()
            rule.execution_count += 1
            
            # Mark execution as completed
            execution.completed_at = datetime.now()
            execution.status = "completed" if not execution.errors else "failed"
            
            logger.info(f"Workflow execution completed: {execution_id}")
            
        except Exception as e:
            execution.completed_at = datetime.now()
            execution.status = "failed"
            execution.errors.append(str(e))
            logger.error(f"Workflow execution failed: {e}")
        
        return execution
    
    async def _execute_action(self, action_config: Dict[str, Any], event_data: Dict[str, Any], 
                            execution: WorkflowExecution):
        """Execute a workflow action"""
        action_type_str = action_config.get("type")
        if not action_type_str:
            raise ValueError("Action type is required")
        
        try:
            action_type = WorkflowAction(action_type_str)
        except ValueError:
            raise ValueError(f"Unknown action type: {action_type_str}")
        
        handler = self.action_handlers.get(action_type)
        if not handler:
            raise ValueError(f"No handler for action type: {action_type}")
        
        # Execute action
        result = await handler(action_config, event_data)
        
        # Record action execution
        execution.actions_executed.append({
            "type": action_type_str,
            "config": action_config,
            "result": result,
            "executed_at": datetime.now().isoformat()
        })
        
        logger.debug(f"Action executed: {action_type_str}")
    
    # Action Handlers
    
    async def _handle_create_issue(self, action_config: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create issue action"""
        title = action_config.get("title", "Automated Issue")
        description = action_config.get("description", "")
        team_id = action_config.get("team_id")
        assignee_id = action_config.get("assignee_id")
        priority = action_config.get("priority")
        
        # Template substitution
        title = self._substitute_template(title, event_data)
        description = self._substitute_template(description, event_data)
        
        # Convert priority if specified
        linear_priority = None
        if priority:
            try:
                linear_priority = LinearIssuePriority(priority)
            except ValueError:
                logger.warning(f"Invalid priority value: {priority}")
        
        response = await self.linear_client.create_issue(
            title=title,
            description=description,
            team_id=team_id,
            assignee_id=assignee_id,
            priority=linear_priority
        )
        
        if not response.success:
            raise Exception(f"Failed to create issue: {', '.join(response.errors)}")
        
        return response.data
    
    async def _handle_update_issue(self, action_config: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle update issue action"""
        issue_id = action_config.get("issue_id")
        if not issue_id:
            # Try to get issue ID from event data
            issue_id = event_data.get("issue", {}).get("id")
        
        if not issue_id:
            raise ValueError("Issue ID is required for update action")
        
        # Build update parameters
        update_params = {}
        
        if "title" in action_config:
            update_params["title"] = self._substitute_template(action_config["title"], event_data)
        
        if "description" in action_config:
            update_params["description"] = self._substitute_template(action_config["description"], event_data)
        
        if "assignee_id" in action_config:
            update_params["assignee_id"] = action_config["assignee_id"]
        
        if "priority" in action_config:
            try:
                update_params["priority"] = LinearIssuePriority(action_config["priority"])
            except ValueError:
                logger.warning(f"Invalid priority value: {action_config['priority']}")
        
        response = await self.linear_client.update_issue(issue_id, **update_params)
        
        if not response.success:
            raise Exception(f"Failed to update issue: {', '.join(response.errors)}")
        
        return response.data
    
    async def _handle_assign_issue(self, action_config: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle assign issue action"""
        issue_id = action_config.get("issue_id")
        if not issue_id:
            issue_id = event_data.get("issue", {}).get("id")
        
        if not issue_id:
            raise ValueError("Issue ID is required for assign action")
        
        assignee_id = action_config.get("assignee_id")
        if not assignee_id:
            raise ValueError("Assignee ID is required for assign action")
        
        response = await self.linear_client.update_issue(issue_id, assignee_id=assignee_id)
        
        if not response.success:
            raise Exception(f"Failed to assign issue: {', '.join(response.errors)}")
        
        return response.data
    
    async def _handle_add_comment(self, action_config: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle add comment action"""
        # This would require implementing comment creation in the Linear client
        # For now, return a placeholder
        return {"status": "comment_action_not_implemented"}
    
    async def _handle_send_notification(self, action_config: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle send notification action"""
        # This would integrate with notification systems (Slack, email, etc.)
        # For now, return a placeholder
        return {"status": "notification_action_not_implemented"}
    
    async def _handle_create_project(self, action_config: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle create project action"""
        # This would require implementing project creation in the Linear client
        # For now, return a placeholder
        return {"status": "create_project_action_not_implemented"}
    
    async def _handle_sync_github(self, action_config: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GitHub sync action"""
        # This would integrate with GitHub extension
        # For now, return a placeholder
        return {"status": "github_sync_action_not_implemented"}
    
    async def _handle_analyze_code(self, action_config: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle code analysis action"""
        # This would integrate with code analysis tools
        # For now, return a placeholder
        return {"status": "code_analysis_action_not_implemented"}
    
    def _substitute_template(self, template: str, event_data: Dict[str, Any]) -> str:
        """Substitute template variables with event data"""
        if not template or not isinstance(template, str):
            return template
        
        # Simple template substitution using {key} format
        import re
        
        def replace_var(match):
            var_name = match.group(1)
            value = self._get_nested_value(event_data, var_name)
            return str(value) if value is not None else match.group(0)
        
        return re.sub(r'\\{([^}]+)\\}', replace_var, template)
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get nested value from data using dot notation"""
        keys = field_path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get workflow execution by ID"""
        return self.executions.get(execution_id)
    
    def list_executions(self, rule_id: Optional[str] = None, limit: int = 100) -> List[WorkflowExecution]:
        """List workflow executions"""
        executions = list(self.executions.values())
        
        if rule_id:
            executions = [exec for exec in executions if exec.rule_id == rule_id]
        
        # Sort by start time (newest first)
        executions.sort(key=lambda x: x.started_at, reverse=True)
        
        return executions[:limit]
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get workflow execution statistics"""
        executions = list(self.executions.values())
        
        total_executions = len(executions)
        completed_executions = len([e for e in executions if e.status == "completed"])
        failed_executions = len([e for e in executions if e.status == "failed"])
        running_executions = len([e for e in executions if e.status == "running"])
        
        return {
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "failed_executions": failed_executions,
            "running_executions": running_executions,
            "success_rate": completed_executions / total_executions if total_executions > 0 else 0,
            "total_rules": len(self.rules),
            "enabled_rules": len([r for r in self.rules.values() if r.enabled])
        }


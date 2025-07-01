"""Block Kit builder for rich interactive Slack messages and modals."""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class BlockType(Enum):
    """Block Kit block types."""
    SECTION = "section"
    DIVIDER = "divider"
    HEADER = "header"
    CONTEXT = "context"
    ACTIONS = "actions"
    IMAGE = "image"
    FILE = "file"
    RICH_TEXT = "rich_text"


class ElementType(Enum):
    """Block Kit element types."""
    BUTTON = "button"
    SELECT = "static_select"
    MULTI_SELECT = "multi_static_select"
    DATEPICKER = "datepicker"
    TIMEPICKER = "timepicker"
    PLAIN_TEXT_INPUT = "plain_text_input"
    CHECKBOXES = "checkboxes"
    RADIO_BUTTONS = "radio_buttons"
    OVERFLOW = "overflow"


class ButtonStyle(Enum):
    """Button styles."""
    DEFAULT = "default"
    PRIMARY = "primary"
    DANGER = "danger"


class NotificationTemplate(Enum):
    """Pre-defined notification templates."""
    ISSUE_ASSIGNED = "issue_assigned"
    PR_REVIEW_REQUEST = "pr_review_request"
    DEPLOYMENT_STATUS = "deployment_status"
    SYSTEM_ALERT = "system_alert"
    WORKFLOW_APPROVAL = "workflow_approval"
    TEAM_UPDATE = "team_update"


class BlockKitBuilder:
    """Builder for creating rich Block Kit messages and modals."""
    
    def __init__(self):
        self.templates = self._load_templates()
        logger.info("Block Kit builder initialized with templates")
    
    async def build_notification_blocks(
        self, 
        event_data: Dict[str, Any], 
        context: Any
    ) -> List[Dict[str, Any]]:
        """Build notification blocks based on event data and context.
        
        Args:
            event_data: The event data to display
            context: NotificationContext with routing information
            
        Returns:
            List of Block Kit blocks
        """
        try:
            # Determine template based on event type
            template = self._get_template_for_event(context.event_type)
            
            if template:
                return await self._build_from_template(template, event_data, context)
            else:
                return await self._build_generic_notification(event_data, context)
                
        except Exception as e:
            logger.exception(f"Failed to build notification blocks: {e}")
            return self._build_error_blocks(str(e))
    
    async def build_workflow_blocks(
        self, 
        workflow_context: Any
    ) -> List[Dict[str, Any]]:
        """Build interactive workflow blocks for approvals and coordination.
        
        Args:
            workflow_context: WorkflowContext with workflow information
            
        Returns:
            List of Block Kit blocks with interactive components
        """
        try:
            workflow_type = workflow_context.workflow_type
            
            if workflow_type == "approval":
                return self._build_approval_workflow(workflow_context)
            elif workflow_type == "review":
                return self._build_review_workflow(workflow_context)
            elif workflow_type == "deployment":
                return self._build_deployment_workflow(workflow_context)
            elif workflow_type == "task_assignment":
                return self._build_task_assignment_workflow(workflow_context)
            else:
                return self._build_generic_workflow(workflow_context)
                
        except Exception as e:
            logger.exception(f"Failed to build workflow blocks: {e}")
            return self._build_error_blocks(str(e))
    
    def build_modal_view(
        self, 
        title: str, 
        blocks: List[Dict[str, Any]],
        submit_text: str = "Submit",
        close_text: str = "Cancel",
        callback_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Build a modal view with the specified blocks.
        
        Args:
            title: Modal title
            blocks: List of blocks to include in modal
            submit_text: Text for submit button
            close_text: Text for close button
            callback_id: Callback ID for handling submission
            
        Returns:
            Modal view definition
        """
        return {
            "type": "modal",
            "title": self._text_object(title, "plain_text"),
            "blocks": blocks,
            "submit": self._text_object(submit_text, "plain_text"),
            "close": self._text_object(close_text, "plain_text"),
            "callback_id": callback_id or f"modal_{int(datetime.now().timestamp())}"
        }
    
    def build_home_tab_view(
        self, 
        user_id: str,
        blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build a home tab view for the user.
        
        Args:
            user_id: User ID for the home tab
            blocks: List of blocks to display
            
        Returns:
            Home tab view definition
        """
        return {
            "type": "home",
            "blocks": blocks
        }
    
    def _get_template_for_event(self, event_type: str) -> Optional[NotificationTemplate]:
        """Get the appropriate template for an event type."""
        template_map = {
            "issue_assigned": NotificationTemplate.ISSUE_ASSIGNED,
            "issue_created": NotificationTemplate.ISSUE_ASSIGNED,
            "pr_review_requested": NotificationTemplate.PR_REVIEW_REQUEST,
            "pr_opened": NotificationTemplate.PR_REVIEW_REQUEST,
            "deployment_started": NotificationTemplate.DEPLOYMENT_STATUS,
            "deployment_completed": NotificationTemplate.DEPLOYMENT_STATUS,
            "deployment_failed": NotificationTemplate.DEPLOYMENT_STATUS,
            "system_alert": NotificationTemplate.SYSTEM_ALERT,
            "workflow_approval": NotificationTemplate.WORKFLOW_APPROVAL,
            "team_update": NotificationTemplate.TEAM_UPDATE
        }
        return template_map.get(event_type)
    
    async def _build_from_template(
        self, 
        template: NotificationTemplate, 
        event_data: Dict[str, Any], 
        context: Any
    ) -> List[Dict[str, Any]]:
        """Build blocks from a predefined template."""
        if template == NotificationTemplate.ISSUE_ASSIGNED:
            return self._build_issue_notification(event_data, context)
        elif template == NotificationTemplate.PR_REVIEW_REQUEST:
            return self._build_pr_review_notification(event_data, context)
        elif template == NotificationTemplate.DEPLOYMENT_STATUS:
            return self._build_deployment_notification(event_data, context)
        elif template == NotificationTemplate.SYSTEM_ALERT:
            return self._build_system_alert_notification(event_data, context)
        elif template == NotificationTemplate.WORKFLOW_APPROVAL:
            return self._build_workflow_approval_notification(event_data, context)
        else:
            return await self._build_generic_notification(event_data, context)
    
    def _build_issue_notification(
        self, 
        event_data: Dict[str, Any], 
        context: Any
    ) -> List[Dict[str, Any]]:
        """Build notification blocks for issue events."""
        issue_title = event_data.get("title", "Issue")
        issue_url = event_data.get("url", "#")
        assignee = event_data.get("assignee", "Unknown")
        priority = context.priority if hasattr(context, 'priority') else "normal"
        
        # Priority emoji mapping
        priority_emoji = {
            "low": "🔵",
            "normal": "🟡", 
            "high": "🟠",
            "urgent": "🔴"
        }
        
        blocks = [
            {
                "type": "header",
                "text": self._text_object(f"{priority_emoji.get(priority, '🟡')} Issue Assigned", "plain_text")
            },
            {
                "type": "section",
                "text": self._text_object(f"*<{issue_url}|{issue_title}>*", "mrkdwn"),
                "fields": [
                    self._text_object(f"*Assignee:*\n<@{assignee}>", "mrkdwn"),
                    self._text_object(f"*Priority:*\n{priority.title()}", "mrkdwn")
                ]
            }
        ]
        
        # Add action buttons
        if issue_url != "#":
            blocks.append({
                "type": "actions",
                "elements": [
                    self._button_element("View Issue", issue_url, style=ButtonStyle.PRIMARY),
                    self._button_element("Comment", f"{issue_url}#comment", style=ButtonStyle.DEFAULT)
                ]
            })
        
        return blocks
    
    def _build_pr_review_notification(
        self, 
        event_data: Dict[str, Any], 
        context: Any
    ) -> List[Dict[str, Any]]:
        """Build notification blocks for PR review events."""
        pr_title = event_data.get("title", "Pull Request")
        pr_url = event_data.get("url", "#")
        author = event_data.get("author", "Unknown")
        reviewers = event_data.get("reviewers", [])
        
        blocks = [
            {
                "type": "header",
                "text": self._text_object("👀 Code Review Requested", "plain_text")
            },
            {
                "type": "section",
                "text": self._text_object(f"*<{pr_url}|{pr_title}>*", "mrkdwn"),
                "fields": [
                    self._text_object(f"*Author:*\n<@{author}>", "mrkdwn"),
                    self._text_object(f"*Reviewers:*\n{', '.join([f'<@{r}>' for r in reviewers])}", "mrkdwn")
                ]
            }
        ]
        
        # Add review action buttons
        if pr_url != "#":
            blocks.append({
                "type": "actions",
                "elements": [
                    self._button_element("Review PR", pr_url, style=ButtonStyle.PRIMARY),
                    self._button_element("Approve", f"{pr_url}/approve", style=ButtonStyle.DEFAULT),
                    self._button_element("Request Changes", f"{pr_url}/changes", style=ButtonStyle.DANGER)
                ]
            })
        
        return blocks
    
    def _build_deployment_notification(
        self, 
        event_data: Dict[str, Any], 
        context: Any
    ) -> List[Dict[str, Any]]:
        """Build notification blocks for deployment events."""
        status = event_data.get("status", "unknown")
        environment = event_data.get("environment", "production")
        version = event_data.get("version", "unknown")
        
        # Status emoji mapping
        status_emoji = {
            "started": "🚀",
            "completed": "✅",
            "failed": "❌",
            "cancelled": "⏹️"
        }
        
        blocks = [
            {
                "type": "header",
                "text": self._text_object(
                    f"{status_emoji.get(status, '🚀')} Deployment {status.title()}", 
                    "plain_text"
                )
            },
            {
                "type": "section",
                "fields": [
                    self._text_object(f"*Environment:*\n{environment}", "mrkdwn"),
                    self._text_object(f"*Version:*\n{version}", "mrkdwn"),
                    self._text_object(f"*Status:*\n{status.title()}", "mrkdwn"),
                    self._text_object(f"*Time:*\n{datetime.now().strftime('%H:%M:%S')}", "mrkdwn")
                ]
            }
        ]
        
        # Add action buttons based on status
        if status == "completed":
            blocks.append({
                "type": "actions",
                "elements": [
                    self._button_element("View Logs", "#", style=ButtonStyle.DEFAULT),
                    self._button_element("Monitor", "#", style=ButtonStyle.PRIMARY)
                ]
            })
        elif status == "failed":
            blocks.append({
                "type": "actions",
                "elements": [
                    self._button_element("View Logs", "#", style=ButtonStyle.DANGER),
                    self._button_element("Rollback", "#", style=ButtonStyle.DEFAULT),
                    self._button_element("Retry", "#", style=ButtonStyle.PRIMARY)
                ]
            })
        
        return blocks
    
    def _build_system_alert_notification(
        self, 
        event_data: Dict[str, Any], 
        context: Any
    ) -> List[Dict[str, Any]]:
        """Build notification blocks for system alerts."""
        alert_type = event_data.get("type", "unknown")
        message = event_data.get("message", "System alert")
        severity = event_data.get("severity", "warning")
        
        # Severity emoji mapping
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        blocks = [
            {
                "type": "header",
                "text": self._text_object(
                    f"{severity_emoji.get(severity, '⚠️')} System Alert", 
                    "plain_text"
                )
            },
            {
                "type": "section",
                "text": self._text_object(f"*{alert_type.title()}:* {message}", "mrkdwn"),
                "fields": [
                    self._text_object(f"*Severity:*\n{severity.title()}", "mrkdwn"),
                    self._text_object(f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "mrkdwn")
                ]
            }
        ]
        
        # Add action buttons for critical alerts
        if severity in ["error", "critical"]:
            blocks.append({
                "type": "actions",
                "elements": [
                    self._button_element("Investigate", "#", style=ButtonStyle.DANGER),
                    self._button_element("Acknowledge", "#", style=ButtonStyle.DEFAULT),
                    self._button_element("Escalate", "#", style=ButtonStyle.PRIMARY)
                ]
            })
        
        return blocks
    
    def _build_workflow_approval_notification(
        self, 
        event_data: Dict[str, Any], 
        context: Any
    ) -> List[Dict[str, Any]]:
        """Build notification blocks for workflow approval requests."""
        workflow_name = event_data.get("workflow_name", "Workflow")
        requester = event_data.get("requester", "Unknown")
        description = event_data.get("description", "Approval required")
        
        blocks = [
            {
                "type": "header",
                "text": self._text_object("📋 Approval Required", "plain_text")
            },
            {
                "type": "section",
                "text": self._text_object(f"*{workflow_name}*\n{description}", "mrkdwn"),
                "fields": [
                    self._text_object(f"*Requested by:*\n<@{requester}>", "mrkdwn"),
                    self._text_object(f"*Time:*\n{datetime.now().strftime('%H:%M:%S')}", "mrkdwn")
                ]
            },
            {
                "type": "actions",
                "elements": [
                    self._button_element("Approve", "approve", style=ButtonStyle.PRIMARY),
                    self._button_element("Reject", "reject", style=ButtonStyle.DANGER),
                    self._button_element("More Info", "info", style=ButtonStyle.DEFAULT)
                ]
            }
        ]
        
        return blocks
    
    async def _build_generic_notification(
        self, 
        event_data: Dict[str, Any], 
        context: Any
    ) -> List[Dict[str, Any]]:
        """Build generic notification blocks."""
        title = event_data.get("title", "Notification")
        message = event_data.get("message", "No message provided")
        
        return [
            {
                "type": "section",
                "text": self._text_object(f"*{title}*\n{message}", "mrkdwn")
            }
        ]
    
    def _build_approval_workflow(self, workflow_context: Any) -> List[Dict[str, Any]]:
        """Build approval workflow blocks."""
        workflow_data = workflow_context.data
        
        blocks = [
            {
                "type": "header",
                "text": self._text_object("📋 Approval Workflow", "plain_text")
            },
            {
                "type": "section",
                "text": self._text_object(
                    f"*{workflow_data.get('title', 'Approval Required')}*\n"
                    f"{workflow_data.get('description', 'Please review and approve.')}", 
                    "mrkdwn"
                )
            },
            {
                "type": "actions",
                "elements": [
                    self._button_element(
                        "Approve", 
                        f"approve_{workflow_context.workflow_id}", 
                        style=ButtonStyle.PRIMARY
                    ),
                    self._button_element(
                        "Reject", 
                        f"reject_{workflow_context.workflow_id}", 
                        style=ButtonStyle.DANGER
                    ),
                    self._button_element(
                        "Request Changes", 
                        f"changes_{workflow_context.workflow_id}", 
                        style=ButtonStyle.DEFAULT
                    )
                ]
            }
        ]
        
        return blocks
    
    def _build_review_workflow(self, workflow_context: Any) -> List[Dict[str, Any]]:
        """Build code review workflow blocks."""
        workflow_data = workflow_context.data
        
        blocks = [
            {
                "type": "header",
                "text": self._text_object("👀 Code Review", "plain_text")
            },
            {
                "type": "section",
                "text": self._text_object(
                    f"*{workflow_data.get('pr_title', 'Pull Request')}*\n"
                    f"Review requested by <@{workflow_data.get('author', 'unknown')}>", 
                    "mrkdwn"
                )
            },
            {
                "type": "actions",
                "elements": [
                    self._button_element(
                        "Start Review", 
                        f"review_{workflow_context.workflow_id}", 
                        style=ButtonStyle.PRIMARY
                    ),
                    self._button_element(
                        "Quick Approve", 
                        f"quick_approve_{workflow_context.workflow_id}", 
                        style=ButtonStyle.DEFAULT
                    )
                ]
            }
        ]
        
        return blocks
    
    def _build_deployment_workflow(self, workflow_context: Any) -> List[Dict[str, Any]]:
        """Build deployment workflow blocks."""
        workflow_data = workflow_context.data
        
        blocks = [
            {
                "type": "header",
                "text": self._text_object("🚀 Deployment Approval", "plain_text")
            },
            {
                "type": "section",
                "text": self._text_object(
                    f"*{workflow_data.get('environment', 'Production')} Deployment*\n"
                    f"Version: {workflow_data.get('version', 'unknown')}", 
                    "mrkdwn"
                )
            },
            {
                "type": "actions",
                "elements": [
                    self._button_element(
                        "Deploy", 
                        f"deploy_{workflow_context.workflow_id}", 
                        style=ButtonStyle.PRIMARY
                    ),
                    self._button_element(
                        "Schedule", 
                        f"schedule_{workflow_context.workflow_id}", 
                        style=ButtonStyle.DEFAULT
                    ),
                    self._button_element(
                        "Cancel", 
                        f"cancel_{workflow_context.workflow_id}", 
                        style=ButtonStyle.DANGER
                    )
                ]
            }
        ]
        
        return blocks
    
    def _build_task_assignment_workflow(self, workflow_context: Any) -> List[Dict[str, Any]]:
        """Build task assignment workflow blocks."""
        workflow_data = workflow_context.data
        
        blocks = [
            {
                "type": "header",
                "text": self._text_object("📝 Task Assignment", "plain_text")
            },
            {
                "type": "section",
                "text": self._text_object(
                    f"*{workflow_data.get('task_title', 'New Task')}*\n"
                    f"{workflow_data.get('description', 'Task assignment required.')}", 
                    "mrkdwn"
                )
            },
            {
                "type": "actions",
                "elements": [
                    self._button_element(
                        "Accept", 
                        f"accept_{workflow_context.workflow_id}", 
                        style=ButtonStyle.PRIMARY
                    ),
                    self._button_element(
                        "Reassign", 
                        f"reassign_{workflow_context.workflow_id}", 
                        style=ButtonStyle.DEFAULT
                    ),
                    self._button_element(
                        "Decline", 
                        f"decline_{workflow_context.workflow_id}", 
                        style=ButtonStyle.DANGER
                    )
                ]
            }
        ]
        
        return blocks
    
    def _build_generic_workflow(self, workflow_context: Any) -> List[Dict[str, Any]]:
        """Build generic workflow blocks."""
        return [
            {
                "type": "section",
                "text": self._text_object(
                    f"*{workflow_context.workflow_type.title()} Workflow*\n"
                    f"Workflow ID: {workflow_context.workflow_id}", 
                    "mrkdwn"
                )
            }
        ]
    
    def _build_error_blocks(self, error_message: str) -> List[Dict[str, Any]]:
        """Build error notification blocks."""
        return [
            {
                "type": "section",
                "text": self._text_object(f"❌ *Error:* {error_message}", "mrkdwn")
            }
        ]
    
    def _text_object(self, text: str, text_type: str = "mrkdwn") -> Dict[str, str]:
        """Create a text object for Block Kit."""
        return {
            "type": text_type,
            "text": text
        }
    
    def _button_element(
        self, 
        text: str, 
        action_id: str, 
        style: ButtonStyle = ButtonStyle.DEFAULT,
        url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a button element."""
        button = {
            "type": "button",
            "text": self._text_object(text, "plain_text"),
            "action_id": action_id
        }
        
        if style != ButtonStyle.DEFAULT:
            button["style"] = style.value
        
        if url:
            button["url"] = url
        
        return button
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load notification templates."""
        # This would load templates from configuration
        return {}


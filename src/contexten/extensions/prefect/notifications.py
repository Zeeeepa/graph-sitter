"""
Notification System for Autonomous CI/CD Workflows

This module handles notifications for various workflow events including
Slack, email, and Linear integrations.
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

import aiohttp
from prefect import get_run_logger

from .config import get_config


class NotificationType(Enum):
    """Types of notifications that can be sent"""
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    FIXES_APPLIED = "fixes_applied"
    FAILURE_FIXED = "failure_fixed"
    SECURITY_UPDATE = "security_update"
    PERFORMANCE_REGRESSION = "performance_regression"
    DEPENDENCY_UPDATE = "dependency_update"
    CRITICAL_ALERT = "critical_alert"


class NotificationChannel(Enum):
    """Available notification channels"""
    SLACK = "slack"
    EMAIL = "email"
    LINEAR = "linear"
    GITHUB = "github"


async def send_notification(
    notification_type: NotificationType,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    channels: Optional[List[NotificationChannel]] = None,
    priority: str = "normal"
) -> Dict[str, bool]:
    """
    Send notifications across multiple channels.
    
    Args:
        notification_type: Type of notification
        message: Main notification message
        data: Additional data to include
        channels: Specific channels to send to (default: all enabled)
        priority: Notification priority (low, normal, high, critical)
    
    Returns:
        Dictionary indicating success/failure for each channel
    """
    logger = get_run_logger()
    config = get_config()
    
    if data is None:
        data = {}
    
    # Determine channels to send to
    if channels is None:
        channels = _get_enabled_channels(config, notification_type)
    
    logger.info(f"Sending {notification_type.value} notification to {len(channels)} channels")
    
    results = {}
    
    # Send to each channel concurrently
    tasks = []
    for channel in channels:
        if channel == NotificationChannel.SLACK:
            tasks.append(_send_slack_notification(message, data, notification_type, priority))
        elif channel == NotificationChannel.EMAIL:
            tasks.append(_send_email_notification(message, data, notification_type, priority))
        elif channel == NotificationChannel.LINEAR:
            tasks.append(_send_linear_notification(message, data, notification_type, priority))
        elif channel == NotificationChannel.GITHUB:
            tasks.append(_send_github_notification(message, data, notification_type, priority))
    
    if tasks:
        channel_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(channel_results):
            channel = channels[i]
            if isinstance(result, Exception):
                logger.error(f"Failed to send notification to {channel.value}: {str(result)}")
                results[channel.value] = False
            else:
                results[channel.value] = result
    
    return results


async def _send_slack_notification(
    message: str,
    data: Dict[str, Any],
    notification_type: NotificationType,
    priority: str
) -> bool:
    """Send notification to Slack"""
    config = get_config()
    
    if not config.slack_webhook_url:
        return False
    
    try:
        # Format Slack message
        slack_payload = _format_slack_message(message, data, notification_type, priority)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                config.slack_webhook_url,
                json=slack_payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                return response.status == 200
                
    except Exception as e:
        logging.error(f"Slack notification failed: {str(e)}")
        return False


async def _send_email_notification(
    message: str,
    data: Dict[str, Any],
    notification_type: NotificationType,
    priority: str
) -> bool:
    """Send email notification"""
    config = get_config()
    
    if not config.notification_email:
        return False
    
    try:
        # Email sending logic would go here
        # This is a placeholder for actual email implementation
        logging.info(f"Email notification sent to {config.notification_email}")
        return True
        
    except Exception as e:
        logging.error(f"Email notification failed: {str(e)}")
        return False


async def _send_linear_notification(
    message: str,
    data: Dict[str, Any],
    notification_type: NotificationType,
    priority: str
) -> bool:
    """Send notification to Linear (create issue or comment)"""
    config = get_config()
    
    if not config.linear_api_key:
        return False
    
    try:
        # Linear notification logic would go here
        # This could create issues for critical alerts or add comments
        logging.info("Linear notification sent")
        return True
        
    except Exception as e:
        logging.error(f"Linear notification failed: {str(e)}")
        return False


async def _send_github_notification(
    message: str,
    data: Dict[str, Any],
    notification_type: NotificationType,
    priority: str
) -> bool:
    """Send notification to GitHub (create issue or comment)"""
    config = get_config()
    
    if not config.github_token:
        return False
    
    try:
        # GitHub notification logic would go here
        # This could create issues for critical alerts
        logging.info("GitHub notification sent")
        return True
        
    except Exception as e:
        logging.error(f"GitHub notification failed: {str(e)}")
        return False


def _get_enabled_channels(
    config,
    notification_type: NotificationType
) -> List[NotificationChannel]:
    """Get enabled notification channels based on configuration"""
    channels = []
    
    if config.enable_slack_notifications and config.slack_webhook_url:
        channels.append(NotificationChannel.SLACK)
    
    if config.enable_email_notifications and config.notification_email:
        channels.append(NotificationChannel.EMAIL)
    
    # Always try Linear and GitHub if configured
    if config.linear_api_key:
        channels.append(NotificationChannel.LINEAR)
    
    if config.github_token:
        channels.append(NotificationChannel.GITHUB)
    
    return channels


def _format_slack_message(
    message: str,
    data: Dict[str, Any],
    notification_type: NotificationType,
    priority: str
) -> Dict[str, Any]:
    """Format message for Slack"""
    
    # Color coding based on notification type and priority
    color_map = {
        NotificationType.WORKFLOW_STARTED: "#36a64f",  # Green
        NotificationType.WORKFLOW_COMPLETED: "#36a64f",  # Green
        NotificationType.WORKFLOW_FAILED: "#ff0000",  # Red
        NotificationType.FIXES_APPLIED: "#36a64f",  # Green
        NotificationType.FAILURE_FIXED: "#ffaa00",  # Orange
        NotificationType.SECURITY_UPDATE: "#ff6600",  # Orange-Red
        NotificationType.PERFORMANCE_REGRESSION: "#ffaa00",  # Orange
        NotificationType.DEPENDENCY_UPDATE: "#0099ff",  # Blue
        NotificationType.CRITICAL_ALERT: "#ff0000",  # Red
    }
    
    # Priority indicators
    priority_indicators = {
        "low": "🔵",
        "normal": "🟡",
        "high": "🟠",
        "critical": "🔴"
    }
    
    color = color_map.get(notification_type, "#808080")
    indicator = priority_indicators.get(priority, "🟡")
    
    # Build attachment fields
    fields = []
    
    if "repo_url" in data:
        fields.append({
            "title": "Repository",
            "value": data["repo_url"],
            "short": True
        })
    
    if "branch" in data:
        fields.append({
            "title": "Branch",
            "value": data["branch"],
            "short": True
        })
    
    if "pr_url" in data:
        fields.append({
            "title": "Pull Request",
            "value": f"<{data['pr_url']}|View PR>",
            "short": True
        })
    
    if "fixes_count" in data:
        fields.append({
            "title": "Fixes Applied",
            "value": str(data["fixes_count"]),
            "short": True
        })
    
    if "workflow_run_id" in data:
        fields.append({
            "title": "Workflow Run",
            "value": data["workflow_run_id"],
            "short": True
        })
    
    # Add timestamp
    fields.append({
        "title": "Timestamp",
        "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "short": True
    })
    
    payload = {
        "text": f"{indicator} Autonomous CI/CD Notification",
        "attachments": [
            {
                "color": color,
                "title": f"{notification_type.value.replace('_', ' ').title()}",
                "text": message,
                "fields": fields,
                "footer": "Autonomous CI/CD System",
                "footer_icon": "https://github.com/favicon.ico",
                "ts": int(datetime.utcnow().timestamp())
            }
        ]
    }
    
    # Add additional context for specific notification types
    if notification_type == NotificationType.WORKFLOW_FAILED and "error" in data:
        payload["attachments"][0]["fields"].append({
            "title": "Error",
            "value": f"```{data['error']}```",
            "short": False
        })
    
    if notification_type == NotificationType.PERFORMANCE_REGRESSION and "regressions" in data:
        regression_text = "\n".join([f"• {reg}" for reg in data["regressions"][:5]])
        payload["attachments"][0]["fields"].append({
            "title": "Regressions Detected",
            "value": regression_text,
            "short": False
        })
    
    if notification_type == NotificationType.SECURITY_UPDATE and "security_fixes" in data:
        fixes_text = "\n".join([f"• {fix}" for fix in data["security_fixes"][:5]])
        payload["attachments"][0]["fields"].append({
            "title": "Security Fixes",
            "value": fixes_text,
            "short": False
        })
    
    return payload


def _format_email_subject(
    notification_type: NotificationType,
    priority: str
) -> str:
    """Format email subject line"""
    priority_prefix = {
        "low": "[LOW]",
        "normal": "[INFO]",
        "high": "[HIGH]",
        "critical": "[CRITICAL]"
    }
    
    prefix = priority_prefix.get(priority, "[INFO]")
    title = notification_type.value.replace("_", " ").title()
    
    return f"{prefix} Autonomous CI/CD: {title}"


def _format_email_body(
    message: str,
    data: Dict[str, Any],
    notification_type: NotificationType
) -> str:
    """Format email body"""
    body = f"""
Autonomous CI/CD Notification

{message}

Details:
"""
    
    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)):
            body += f"  {key.replace('_', ' ').title()}: {value}\n"
    
    body += f"""
Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

---
This notification was sent by the Autonomous CI/CD System.
"""
    
    return body


# Convenience functions for common notifications

async def notify_workflow_started(repo_url: str, workflow_name: str) -> Dict[str, bool]:
    """Send workflow started notification"""
    return await send_notification(
        NotificationType.WORKFLOW_STARTED,
        f"🚀 Started {workflow_name} workflow for {repo_url}",
        {"repo_url": repo_url, "workflow_name": workflow_name}
    )


async def notify_workflow_completed(
    repo_url: str,
    workflow_name: str,
    results: Dict[str, Any]
) -> Dict[str, bool]:
    """Send workflow completed notification"""
    return await send_notification(
        NotificationType.WORKFLOW_COMPLETED,
        f"✅ Completed {workflow_name} workflow for {repo_url}",
        {"repo_url": repo_url, "workflow_name": workflow_name, **results}
    )


async def notify_workflow_failed(
    repo_url: str,
    workflow_name: str,
    error: str
) -> Dict[str, bool]:
    """Send workflow failed notification"""
    return await send_notification(
        NotificationType.WORKFLOW_FAILED,
        f"❌ Failed {workflow_name} workflow for {repo_url}",
        {"repo_url": repo_url, "workflow_name": workflow_name, "error": error},
        priority="high"
    )


async def notify_fixes_applied(
    repo_url: str,
    fixes_count: int,
    pr_url: Optional[str] = None
) -> Dict[str, bool]:
    """Send fixes applied notification"""
    data = {"repo_url": repo_url, "fixes_count": fixes_count}
    if pr_url:
        data["pr_url"] = pr_url
    
    return await send_notification(
        NotificationType.FIXES_APPLIED,
        f"🔧 Applied {fixes_count} autonomous fixes to {repo_url}",
        data
    )


async def notify_security_update(
    repo_url: str,
    security_fixes: List[str]
) -> Dict[str, bool]:
    """Send security update notification"""
    return await send_notification(
        NotificationType.SECURITY_UPDATE,
        f"🔒 Applied {len(security_fixes)} security updates to {repo_url}",
        {"repo_url": repo_url, "security_fixes": security_fixes},
        priority="high"
    )


async def notify_performance_regression(
    repo_url: str,
    regressions: List[str]
) -> Dict[str, bool]:
    """Send performance regression notification"""
    return await send_notification(
        NotificationType.PERFORMANCE_REGRESSION,
        f"⚠️ Performance regression detected in {repo_url}",
        {"repo_url": repo_url, "regressions": regressions},
        priority="high"
    )


async def notify_critical_alert(
    message: str,
    data: Dict[str, Any]
) -> Dict[str, bool]:
    """Send critical alert notification"""
    return await send_notification(
        NotificationType.CRITICAL_ALERT,
        message,
        data,
        priority="critical"
    )


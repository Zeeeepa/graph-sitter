"""
Enhanced Slack Integration

This module provides advanced Slack integration capabilities including
team communication, notifications, and interactive bot functionality.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class SlackConfig:
    """Configuration for Slack integration."""
    bot_token: str
    app_token: Optional[str] = None
    signing_secret: Optional[str] = None
    default_channel: str = "#general"
    notification_channels: Dict[str, str] = None
    interactive_mode: bool = True


class SlackIntegration:
    """
    Enhanced Slack integration with communication and notification capabilities.
    
    Features:
    - Team notifications and updates
    - Interactive bot commands
    - Status reporting and monitoring
    - Workflow notifications
    - Real-time communication
    """
    
    def __init__(self, orchestrator):
        """
        Initialize Slack integration.
        
        Args:
            orchestrator: Reference to the main orchestrator
        """
        self.orchestrator = orchestrator
        self.config: Optional[SlackConfig] = None
        self.command_handlers: Dict[str, Callable] = {}
        self.event_handlers: Dict[str, Callable] = {}
        
        logger.info("Slack integration initialized")
    
    async def initialize(self):
        """Initialize the Slack integration."""
        # Load configuration from environment or orchestrator config
        self.config = SlackConfig(
            bot_token="placeholder-token",  # Would load from environment
            default_channel="#ci-cd",
            notification_channels={
                "system": "#system-alerts",
                "deployments": "#deployments",
                "errors": "#errors"
            },
            interactive_mode=True
        )
        
        # Setup command and event handlers
        self._setup_command_handlers()
        self._setup_event_handlers()
        
        logger.info("Slack integration initialized successfully")
    
    async def close(self):
        """Close the Slack integration."""
        logger.info("Slack integration closed")
    
    def _setup_command_handlers(self):
        """Setup slash command handlers."""
        self.command_handlers = {
            "/analyze": self._handle_analyze_command,
            "/status": self._handle_status_command,
            "/workflow": self._handle_workflow_command,
            "/help": self._handle_help_command
        }
    
    def _setup_event_handlers(self):
        """Setup event handlers for orchestrator events."""
        if self.orchestrator:
            self.orchestrator.add_event_handler("system_started", self._on_system_started)
            self.orchestrator.add_event_handler("task_completed", self._on_task_completed)
            self.orchestrator.add_event_handler("task_failed", self._on_task_failed)
            self.orchestrator.add_event_handler("workflow_completed", self._on_workflow_completed)
    
    async def _handle_analyze_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /analyze command."""
        text = command_data.get("text", "")
        user_id = command_data.get("user_id")
        channel_id = command_data.get("channel_id")
        
        logger.info(f"Handling /analyze command from user {user_id}")
        
        if not text:
            return {
                "response_type": "ephemeral",
                "text": "Please provide a repository URL to analyze. Usage: `/analyze https://github.com/user/repo`"
            }
        
        # Extract repository URL from text
        repo_url = text.strip()
        
        # Trigger analysis
        if self.orchestrator:
            try:
                # Start analysis asynchronously
                asyncio.create_task(self._trigger_analysis_with_notification(repo_url, channel_id))
                
                return {
                    "response_type": "in_channel",
                    "text": f"🔍 Starting analysis of {repo_url}... I'll notify you when it's complete!"
                }
            except Exception as e:
                return {
                    "response_type": "ephemeral",
                    "text": f"❌ Failed to start analysis: {str(e)}"
                }
        else:
            return {
                "response_type": "ephemeral",
                "text": "❌ Orchestrator not available"
            }
    
    async def _handle_status_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /status command."""
        user_id = command_data.get("user_id")
        
        logger.info(f"Handling /status command from user {user_id}")
        
        if self.orchestrator:
            status = self.orchestrator.get_system_status()
            
            # Format status for Slack
            status_emoji = {
                "active": "🟢",
                "degraded": "🟡", 
                "error": "🔴",
                "maintenance": "🔵"
            }.get(status["status"], "⚪")
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{status_emoji} *System Status: {status['status'].title()}*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Uptime:* {status['uptime_seconds']:.0f}s"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Active Tasks:* {status['metrics']['active_tasks']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Total Processed:* {status['metrics']['total_tasks_processed']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Success Rate:* {status['metrics']['success_rate']:.1%}"
                        }
                    ]
                }
            ]
            
            return {
                "response_type": "ephemeral",
                "blocks": blocks
            }
        else:
            return {
                "response_type": "ephemeral",
                "text": "❌ Orchestrator not available"
            }
    
    async def _handle_workflow_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /workflow command."""
        text = command_data.get("text", "")
        user_id = command_data.get("user_id")
        
        logger.info(f"Handling /workflow command from user {user_id}")
        
        if not text:
            # List active workflows
            if self.orchestrator:
                workflows = await self._get_workflow_list()
                if workflows:
                    workflow_text = "\n".join([
                        f"• {w['name']} ({w['status']}) - {w['task_count']} tasks"
                        for w in workflows
                    ])
                    return {
                        "response_type": "ephemeral",
                        "text": f"📋 *Active Workflows:*\n{workflow_text}"
                    }
                else:
                    return {
                        "response_type": "ephemeral",
                        "text": "📋 No active workflows"
                    }
            else:
                return {
                    "response_type": "ephemeral",
                    "text": "❌ Orchestrator not available"
                }
        
        # Handle workflow commands (start, stop, etc.)
        parts = text.split()
        action = parts[0] if parts else ""
        
        if action == "list":
            # Same as no text case above
            pass
        elif action == "cancel" and len(parts) > 1:
            workflow_id = parts[1]
            # Cancel workflow
            if self.orchestrator:
                success = await self.orchestrator.cancel_workflow(workflow_id)
                if success:
                    return {
                        "response_type": "in_channel",
                        "text": f"🛑 Cancelled workflow {workflow_id}"
                    }
                else:
                    return {
                        "response_type": "ephemeral",
                        "text": f"❌ Failed to cancel workflow {workflow_id}"
                    }
        
        return {
            "response_type": "ephemeral",
            "text": "Usage: `/workflow [list|cancel <workflow_id>]`"
        }
    
    async def _handle_help_command(self, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle /help command."""
        help_text = """
🤖 *Contexten CI/CD Bot Commands*

• `/analyze <repo_url>` - Analyze a repository
• `/status` - Show system status
• `/workflow [list|cancel <id>]` - Manage workflows
• `/help` - Show this help message

*Examples:*
• `/analyze https://github.com/user/repo`
• `/workflow list`
• `/workflow cancel workflow_123`
        """
        
        return {
            "response_type": "ephemeral",
            "text": help_text
        }
    
    async def _trigger_analysis_with_notification(self, repo_url: str, channel_id: str):
        """Trigger analysis and send notification when complete."""
        try:
            result = await self.orchestrator.execute_codebase_analysis(repo_url)
            
            if result["status"] == "completed":
                await self.send_message(
                    channel=channel_id,
                    text=f"✅ Analysis of {repo_url} completed successfully!",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"✅ *Analysis Complete*\n📊 Repository: {repo_url}\n⏱️ Completed at: {result['timestamp']}"
                            }
                        }
                    ]
                )
            else:
                await self.send_message(
                    channel=channel_id,
                    text=f"❌ Analysis of {repo_url} failed: {result.get('error', 'Unknown error')}"
                )
        except Exception as e:
            await self.send_message(
                channel=channel_id,
                text=f"❌ Analysis of {repo_url} failed with error: {str(e)}"
            )
    
    async def _get_workflow_list(self) -> List[Dict[str, Any]]:
        """Get list of active workflows."""
        if self.orchestrator:
            return await self.orchestrator.list_workflows()
        return []
    
    async def _on_system_started(self, event_type: str, data: Dict[str, Any]):
        """Handle system started event."""
        await self.send_notification(
            "system",
            "🚀 Contexten CI/CD system started successfully!",
            data
        )
    
    async def _on_task_completed(self, event_type: str, data: Dict[str, Any]):
        """Handle task completed event."""
        task_id = data.get("task_id")
        # Only notify for important tasks to avoid spam
        # This would have more sophisticated filtering in practice
    
    async def _on_task_failed(self, event_type: str, data: Dict[str, Any]):
        """Handle task failed event."""
        task_id = data.get("task_id")
        error = data.get("error", "Unknown error")
        
        await self.send_notification(
            "errors",
            f"❌ Task {task_id} failed: {error}",
            data
        )
    
    async def _on_workflow_completed(self, event_type: str, data: Dict[str, Any]):
        """Handle workflow completed event."""
        workflow_id = data.get("workflow_id")
        
        await self.send_notification(
            "deployments",
            f"✅ Workflow {workflow_id} completed successfully!",
            data
        )
    
    async def process_command(self, command: str, command_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming slash commands."""
        handler = self.command_handlers.get(command)
        if handler:
            try:
                return await handler(command_data)
            except Exception as e:
                logger.error(f"Error processing command {command}: {e}")
                return {
                    "response_type": "ephemeral",
                    "text": f"❌ Error processing command: {str(e)}"
                }
        else:
            return {
                "response_type": "ephemeral",
                "text": f"❌ Unknown command: {command}"
            }
    
    async def send_message(self, 
                          channel: str, 
                          text: str, 
                          blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Send a message to a Slack channel."""
        logger.info(f"Sending message to {channel}: {text[:50]}...")
        
        # This would integrate with actual Slack API
        return {
            "ok": True,
            "channel": channel,
            "ts": str(datetime.now().timestamp()),
            "message": {
                "text": text,
                "blocks": blocks
            }
        }
    
    async def send_notification(self, 
                              notification_type: str, 
                              message: str, 
                              data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a notification to the appropriate channel."""
        if not self.config or not self.config.notification_channels:
            return {"ok": False, "error": "No notification channels configured"}
        
        channel = self.config.notification_channels.get(
            notification_type, 
            self.config.default_channel
        )
        
        return await self.send_message(channel, message)
    
    async def send_interactive_message(self, 
                                     channel: str, 
                                     text: str, 
                                     actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Send an interactive message with buttons."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            },
            {
                "type": "actions",
                "elements": actions
            }
        ]
        
        return await self.send_message(channel, text, blocks)
    
    async def update_message(self, 
                           channel: str, 
                           ts: str, 
                           text: str, 
                           blocks: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Update an existing message."""
        logger.info(f"Updating message in {channel} at {ts}")
        
        # This would integrate with actual Slack API
        return {
            "ok": True,
            "channel": channel,
            "ts": ts,
            "message": {
                "text": text,
                "blocks": blocks
            }
        }


"""
Enhanced Slack Extension for Contexten
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    logging.warning("slack-sdk not available, using mock implementation")
    
    class MockWebClient:
        def __init__(self, token):
            self.token = token
        
        def auth_test(self):
            return {"team": "Mock Team"}
        
        def chat_postMessage(self, **kwargs):
            return {
                "ts": "1234567890.123456",
                "channel": kwargs.get("channel", "C1234567890"),
                "text": kwargs.get("text", "")
            }
        
        def conversations_create(self, **kwargs):
            return {
                "channel": {
                    "id": "C1234567890",
                    "name": kwargs.get("name", "test-channel"),
                    "is_private": kwargs.get("is_private", False)
                }
            }
        
        def conversations_info(self, **kwargs):
            return {
                "channel": {
                    "id": kwargs.get("channel", "C1234567890"),
                    "name": "test-channel",
                    "is_private": False,
                    "is_archived": False,
                    "num_members": 5
                }
            }
        
        def chat_update(self, **kwargs):
            return {
                "ts": kwargs.get("ts", "1234567890.123456"),
                "channel": kwargs.get("channel", "C1234567890")
            }
    
    class MockSlackApiError(Exception):
        pass
    
    WebClient = MockWebClient
    SlackApiError = MockSlackApiError

logger = logging.getLogger(__name__)


class SlackExtension:
    """
    Enhanced Slack integration for Contexten orchestrator
    
    Provides comprehensive Slack functionality including:
    - Message posting and management
    - Channel management
    - User interactions
    - Workflow notifications
    - Real-time event handling
    - Bot interactions
    """
    
    def __init__(self, token: str, orchestrator=None):
        if WebClient is None:
            raise ImportError("slack-sdk is required for Slack extension. Install with: pip install slack-sdk")
        
        self.token = token
        self.orchestrator = orchestrator
        self.client = WebClient(token=token)
        self.is_active = False
        
        logger.info("Slack extension initialized")
    
    async def start(self):
        """Start the Slack extension"""
        self.is_active = True
        
        # Test connection
        try:
            response = self.client.auth_test()
            logger.info(f"Slack extension started for team: {response['team']}")
        except Exception as e:
            logger.error(f"Failed to connect to Slack: {e}")
            raise
    
    async def stop(self):
        """Stop the Slack extension"""
        self.is_active = False
        logger.info("Slack extension stopped")
    
    async def execute_action(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Slack action
        
        Args:
            action: Action to execute (e.g., 'send_message', 'create_channel', 'notify_team')
            data: Action-specific data
        
        Returns:
            Action result
        """
        if not self.is_active:
            raise RuntimeError("Slack extension is not active")
        
        try:
            if action == "send_message":
                return await self._send_message(data)
            elif action == "create_channel":
                return await self._create_channel(data)
            elif action == "notify_team":
                return await self._notify_team(data)
            elif action == "post_thread":
                return await self._post_thread(data)
            elif action == "update_message":
                return await self._update_message(data)
            elif action == "get_channel_info":
                return await self._get_channel_info(data)
            elif action == "notify_task_completion":
                return await self._notify_task_completion(data)
            elif action == "notify_error":
                return await self._notify_error(data)
            elif action == "send_daily_report":
                return await self._send_daily_report(data)
            else:
                raise ValueError(f"Unknown Slack action: {action}")
                
        except Exception as e:
            logger.error(f"Slack action '{action}' failed: {e}")
            raise
    
    async def _send_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to a Slack channel"""
        channel = data.get("channel")
        text = data.get("text")
        blocks = data.get("blocks")
        thread_ts = data.get("thread_ts")
        
        if not channel or (not text and not blocks):
            raise ValueError("Channel and either text or blocks are required")
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts
            )
            
            logger.info(f"Sent Slack message to {channel}")
            
            return {
                "action": "send_message",
                "status": "success",
                "message": {
                    "ts": response["ts"],
                    "channel": response["channel"],
                    "text": text
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to send Slack message: {e}")
            raise
    
    async def _create_channel(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Slack channel"""
        name = data.get("name")
        is_private = data.get("is_private", False)
        
        if not name:
            raise ValueError("Channel name is required")
        
        try:
            if is_private:
                response = self.client.conversations_create(
                    name=name,
                    is_private=True
                )
            else:
                response = self.client.conversations_create(name=name)
            
            channel = response["channel"]
            logger.info(f"Created Slack channel: {channel['name']}")
            
            return {
                "action": "create_channel",
                "status": "success",
                "channel": {
                    "id": channel["id"],
                    "name": channel["name"],
                    "is_private": channel.get("is_private", False)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to create Slack channel: {e}")
            raise
    
    async def _notify_team(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a notification to the team"""
        channel = data.get("channel")
        title = data.get("title")
        message = data.get("message")
        priority = data.get("priority", "normal")  # low, normal, high, urgent
        
        if not channel or not title or not message:
            raise ValueError("Channel, title, and message are required")
        
        # Create formatted notification
        priority_emoji = {
            "low": "ℹ️",
            "normal": "📢",
            "high": "⚠️",
            "urgent": "🚨"
        }
        
        emoji = priority_emoji.get(priority, "📢")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Priority: {priority.upper()} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"{title}: {message}"  # Fallback text
            )
            
            logger.info(f"Sent team notification to {channel}")
            
            return {
                "action": "notify_team",
                "status": "success",
                "notification": {
                    "ts": response["ts"],
                    "channel": response["channel"],
                    "title": title,
                    "priority": priority
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to send team notification: {e}")
            raise
    
    async def _post_thread(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Post a threaded message"""
        channel = data.get("channel")
        thread_ts = data.get("thread_ts")
        text = data.get("text")
        
        if not all([channel, thread_ts, text]):
            raise ValueError("Channel, thread_ts, and text are required")
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                thread_ts=thread_ts,
                text=text
            )
            
            logger.info(f"Posted thread message to {channel}")
            
            return {
                "action": "post_thread",
                "status": "success",
                "message": {
                    "ts": response["ts"],
                    "channel": response["channel"],
                    "thread_ts": thread_ts
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to post thread message: {e}")
            raise
    
    async def _update_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing message"""
        channel = data.get("channel")
        ts = data.get("ts")
        text = data.get("text")
        blocks = data.get("blocks")
        
        if not channel or not ts or (not text and not blocks):
            raise ValueError("Channel, ts, and either text or blocks are required")
        
        try:
            response = self.client.chat_update(
                channel=channel,
                ts=ts,
                text=text,
                blocks=blocks
            )
            
            logger.info(f"Updated Slack message in {channel}")
            
            return {
                "action": "update_message",
                "status": "success",
                "message": {
                    "ts": response["ts"],
                    "channel": response["channel"]
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to update Slack message: {e}")
            raise
    
    async def _get_channel_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get information about a channel"""
        channel = data.get("channel")
        
        if not channel:
            raise ValueError("Channel is required")
        
        try:
            response = self.client.conversations_info(channel=channel)
            channel_info = response["channel"]
            
            return {
                "action": "get_channel_info",
                "status": "success",
                "channel": {
                    "id": channel_info["id"],
                    "name": channel_info["name"],
                    "is_private": channel_info.get("is_private", False),
                    "is_archived": channel_info.get("is_archived", False),
                    "num_members": channel_info.get("num_members", 0)
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to get channel info: {e}")
            raise
    
    async def _notify_task_completion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Notify about task completion"""
        channel = data.get("channel")
        task_id = data.get("task_id")
        task_type = data.get("task_type")
        status = data.get("status")
        result = data.get("result", {})
        
        if not all([channel, task_id, task_type, status]):
            raise ValueError("Channel, task_id, task_type, and status are required")
        
        # Create status-specific notification
        status_emoji = {
            "completed": "✅",
            "failed": "❌",
            "cancelled": "⏹️"
        }
        
        emoji = status_emoji.get(status, "ℹ️")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Task {status.title()}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Task ID:*\n{task_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Type:*\n{task_type}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{status.title()}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Completed:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            }
        ]
        
        # Add result information if available
        if result and status == "completed":
            result_text = str(result)[:500]  # Limit length
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Result:*\n```{result_text}```"
                }
            })
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"Task {task_id} {status}"
            )
            
            logger.info(f"Sent task completion notification to {channel}")
            
            return {
                "action": "notify_task_completion",
                "status": "success",
                "notification": {
                    "ts": response["ts"],
                    "channel": response["channel"],
                    "task_id": task_id,
                    "task_status": status
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to send task completion notification: {e}")
            raise
    
    async def _notify_error(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Notify about system errors"""
        channel = data.get("channel")
        error_type = data.get("error_type")
        error_message = data.get("error_message")
        context = data.get("context", {})
        
        if not all([channel, error_type, error_message]):
            raise ValueError("Channel, error_type, and error_message are required")
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🚨 System Error: {error_type}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error Message:*\n```{error_message}```"
                }
            }
        ]
        
        # Add context if available
        if context:
            context_text = str(context)[:500]
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Context:*\n```{context_text}```"
                }
            })
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Occurred at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"System Error: {error_type}"
            )
            
            logger.info(f"Sent error notification to {channel}")
            
            return {
                "action": "notify_error",
                "status": "success",
                "notification": {
                    "ts": response["ts"],
                    "channel": response["channel"],
                    "error_type": error_type
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to send error notification: {e}")
            raise
    
    async def _send_daily_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send a daily system report"""
        channel = data.get("channel")
        
        if not channel:
            raise ValueError("Channel is required")
        
        # Get system status from orchestrator
        system_status = {}
        if self.orchestrator:
            system_status = self.orchestrator.get_system_status()
        
        # Generate report using Codegen SDK if available
        report_content = None
        if self.orchestrator and self.orchestrator.codegen_agent:
            report_prompt = f"""
Generate a comprehensive daily system report based on the following system status:

{system_status}

Please include:
1. System health overview
2. Task execution summary
3. Extension status
4. Performance metrics
5. Notable events or issues
6. Recommendations for improvement

Format the report in a clear, concise manner suitable for a team update.
"""
            
            try:
                report_task = await self.orchestrator._execute_codegen_task(
                    "codegen.generate_daily_report",
                    {
                        "prompt": report_prompt,
                        "context": {
                            "system_status": system_status,
                            "date": datetime.now().strftime('%Y-%m-%d')
                        }
                    }
                )
                
                report_content = report_task.get("result", "Daily report generated.")
            except Exception as e:
                logger.warning(f"Failed to generate AI report: {e}")
                report_content = "Daily report - AI generation unavailable."
        
        # Create report blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Daily System Report - {datetime.now().strftime('%Y-%m-%d')}"
                }
            }
        ]
        
        if report_content:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": report_content[:3000]  # Slack block limit
                }
            })
        
        # Add system metrics
        if system_status:
            blocks.append({
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:*\n{'🟢 Running' if system_status.get('is_running') else '🔴 Stopped'}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Running Tasks:*\n{system_status.get('running_tasks', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Queue Size:*\n{system_status.get('queue_size', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Extensions:*\n{len(system_status.get('extensions', {}))}"
                    }
                ]
            })
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"Daily System Report - {datetime.now().strftime('%Y-%m-%d')}"
            )
            
            logger.info(f"Sent daily report to {channel}")
            
            return {
                "action": "send_daily_report",
                "status": "success",
                "report": {
                    "ts": response["ts"],
                    "channel": response["channel"],
                    "date": datetime.now().strftime('%Y-%m-%d')
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to send daily report: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get extension status"""
        return {
            "active": self.is_active,
            "client_initialized": self.client is not None,
            "timestamp": datetime.now().isoformat()
        }

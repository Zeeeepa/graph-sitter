#!/usr/bin/env python3
"""
Slack Integration Module
Handles Slack API interactions, messaging, notifications, and team communication.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
import aiohttp
from datetime import datetime

from ..base.interfaces import BaseExtension

logger = logging.getLogger(__name__)


class SlackIntegration(BaseExtension):
    """Slack integration for messaging and team communication."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.slack_token = self.config.get("slack_token") if self.config else None
        self.base_url = "https://slack.com/api"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _initialize_impl(self) -> None:
        """Initialize Slack integration."""
        self.logger.info("Initializing Slack integration")
        
        if not self.slack_token:
            self.logger.warning("No Slack token provided - some features may be limited")
            
        # Initialize HTTP session
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.slack_token}" if self.slack_token else ""
        }
        
        self.session = aiohttp.ClientSession(headers=headers)
        
    async def _handle_impl(self, payload: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
        """Handle Slack integration requests."""
        action = payload.get("action")
        
        if action == "send_message":
            return await self.send_message(payload)
        elif action == "list_channels":
            return await self.list_channels()
        elif action == "get_channel":
            channel_id = payload.get("channel_id")
            if not channel_id:
                return {"error": "channel_id is required", "status": "failed"}
            return await self.get_channel(channel_id)
        elif action == "create_channel":
            return await self.create_channel(payload)
        elif action == "list_users":
            return await self.list_users()
        elif action == "get_user":
            user_id = payload.get("user_id")
            if not user_id:
                return {"error": "user_id is required", "status": "failed"}
            return await self.get_user(user_id)
        elif action == "upload_file":
            return await self.upload_file(payload)
        elif action == "get_messages":
            channel_id = payload.get("channel_id")
            if not channel_id:
                return {"error": "channel_id is required", "status": "failed"}
            return await self.get_messages(channel_id, payload.get("limit", 100))
        elif action == "update_message":
            return await self.update_message(payload)
        elif action == "delete_message":
            return await self.delete_message(payload)
        else:
            return {"error": f"Unknown action: {action}", "status": "failed"}
    
    async def send_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send a message to a Slack channel or user."""
        try:
            channel = payload.get("channel")
            text = payload.get("text")
            
            if not all([channel, text]):
                return {"error": "channel and text are required", "status": "failed"}
            
            url = f"{self.base_url}/chat.postMessage"
            data = {
                "channel": channel,
                "text": text
            }
            
            # Optional parameters
            if payload.get("username"):
                data["username"] = payload["username"]
            if payload.get("icon_emoji"):
                data["icon_emoji"] = payload["icon_emoji"]
            if payload.get("icon_url"):
                data["icon_url"] = payload["icon_url"]
            if payload.get("attachments"):
                data["attachments"] = payload["attachments"]
            if payload.get("blocks"):
                data["blocks"] = payload["blocks"]
            if payload.get("thread_ts"):
                data["thread_ts"] = payload["thread_ts"]
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        return {
                            "message": {
                                "ts": result["ts"],
                                "channel": result["channel"],
                                "text": text
                            },
                            "status": "success"
                        }
                    else:
                        return {"error": result.get("error", "Failed to send message"), "status": "failed"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def list_channels(self) -> Dict[str, Any]:
        """List all channels in the workspace."""
        try:
            url = f"{self.base_url}/conversations.list"
            params = {"types": "public_channel,private_channel"}
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        channels = result.get("channels", [])
                        return {
                            "channels": [
                                {
                                    "id": channel["id"],
                                    "name": channel["name"],
                                    "is_channel": channel.get("is_channel", False),
                                    "is_private": channel.get("is_private", False),
                                    "is_archived": channel.get("is_archived", False),
                                    "is_member": channel.get("is_member", False),
                                    "topic": channel.get("topic", {}).get("value", ""),
                                    "purpose": channel.get("purpose", {}).get("value", ""),
                                    "num_members": channel.get("num_members", 0),
                                    "created": channel.get("created")
                                }
                                for channel in channels
                            ],
                            "status": "success"
                        }
                    else:
                        return {"error": result.get("error", "Failed to list channels"), "status": "failed"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error listing channels: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def get_channel(self, channel_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific channel."""
        try:
            url = f"{self.base_url}/conversations.info"
            params = {"channel": channel_id}
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        channel = result.get("channel", {})
                        return {
                            "channel": {
                                "id": channel["id"],
                                "name": channel["name"],
                                "is_channel": channel.get("is_channel", False),
                                "is_private": channel.get("is_private", False),
                                "is_archived": channel.get("is_archived", False),
                                "is_member": channel.get("is_member", False),
                                "topic": channel.get("topic", {}).get("value", ""),
                                "purpose": channel.get("purpose", {}).get("value", ""),
                                "num_members": channel.get("num_members", 0),
                                "created": channel.get("created"),
                                "creator": channel.get("creator")
                            },
                            "status": "success"
                        }
                    else:
                        return {"error": result.get("error", "Channel not found"), "status": "failed"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error getting channel: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def create_channel(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new channel."""
        try:
            name = payload.get("name")
            if not name:
                return {"error": "name is required", "status": "failed"}
            
            url = f"{self.base_url}/conversations.create"
            data = {"name": name}
            
            if payload.get("is_private"):
                data["is_private"] = payload["is_private"]
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        channel = result.get("channel", {})
                        return {
                            "channel": {
                                "id": channel["id"],
                                "name": channel["name"],
                                "is_private": channel.get("is_private", False),
                                "created": channel.get("created")
                            },
                            "status": "success"
                        }
                    else:
                        return {"error": result.get("error", "Failed to create channel"), "status": "failed"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error creating channel: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def list_users(self) -> Dict[str, Any]:
        """List all users in the workspace."""
        try:
            url = f"{self.base_url}/users.list"
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        members = result.get("members", [])
                        return {
                            "users": [
                                {
                                    "id": member["id"],
                                    "name": member["name"],
                                    "real_name": member.get("real_name", ""),
                                    "display_name": member.get("profile", {}).get("display_name", ""),
                                    "email": member.get("profile", {}).get("email", ""),
                                    "is_bot": member.get("is_bot", False),
                                    "is_admin": member.get("is_admin", False),
                                    "is_owner": member.get("is_owner", False),
                                    "deleted": member.get("deleted", False),
                                    "tz": member.get("tz"),
                                    "profile_image": member.get("profile", {}).get("image_72")
                                }
                                for member in members
                                if not member.get("deleted", False)
                            ],
                            "status": "success"
                        }
                    else:
                        return {"error": result.get("error", "Failed to list users"), "status": "failed"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error listing users: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def get_user(self, user_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific user."""
        try:
            url = f"{self.base_url}/users.info"
            params = {"user": user_id}
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        user = result.get("user", {})
                        return {
                            "user": {
                                "id": user["id"],
                                "name": user["name"],
                                "real_name": user.get("real_name", ""),
                                "display_name": user.get("profile", {}).get("display_name", ""),
                                "email": user.get("profile", {}).get("email", ""),
                                "phone": user.get("profile", {}).get("phone", ""),
                                "title": user.get("profile", {}).get("title", ""),
                                "is_bot": user.get("is_bot", False),
                                "is_admin": user.get("is_admin", False),
                                "is_owner": user.get("is_owner", False),
                                "deleted": user.get("deleted", False),
                                "tz": user.get("tz"),
                                "profile_image": user.get("profile", {}).get("image_192")
                            },
                            "status": "success"
                        }
                    else:
                        return {"error": result.get("error", "User not found"), "status": "failed"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error getting user: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def upload_file(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a file to Slack."""
        try:
            channels = payload.get("channels")
            file_content = payload.get("content")
            filename = payload.get("filename")
            
            if not all([channels, file_content, filename]):
                return {"error": "channels, content, and filename are required", "status": "failed"}
            
            url = f"{self.base_url}/files.upload"
            data = {
                "channels": channels,
                "content": file_content,
                "filename": filename
            }
            
            if payload.get("title"):
                data["title"] = payload["title"]
            if payload.get("initial_comment"):
                data["initial_comment"] = payload["initial_comment"]
            if payload.get("filetype"):
                data["filetype"] = payload["filetype"]
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            async with self.session.post(url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        file_info = result.get("file", {})
                        return {
                            "file": {
                                "id": file_info.get("id"),
                                "name": file_info.get("name"),
                                "title": file_info.get("title"),
                                "mimetype": file_info.get("mimetype"),
                                "size": file_info.get("size"),
                                "url_private": file_info.get("url_private"),
                                "permalink": file_info.get("permalink")
                            },
                            "status": "success"
                        }
                    else:
                        return {"error": result.get("error", "Failed to upload file"), "status": "failed"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error uploading file: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def get_messages(self, channel_id: str, limit: int = 100) -> Dict[str, Any]:
        """Get messages from a channel."""
        try:
            url = f"{self.base_url}/conversations.history"
            params = {
                "channel": channel_id,
                "limit": str(min(limit, 1000))  # Slack API limit
            }
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        messages = result.get("messages", [])
                        return {
                            "messages": [
                                {
                                    "ts": message.get("ts"),
                                    "user": message.get("user"),
                                    "text": message.get("text", ""),
                                    "type": message.get("type"),
                                    "subtype": message.get("subtype"),
                                    "thread_ts": message.get("thread_ts"),
                                    "reply_count": message.get("reply_count", 0),
                                    "reactions": message.get("reactions", []),
                                    "files": message.get("files", [])
                                }
                                for message in messages
                            ],
                            "status": "success"
                        }
                    else:
                        return {"error": result.get("error", "Failed to get messages"), "status": "failed"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error getting messages: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def update_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing message."""
        try:
            channel = payload.get("channel")
            ts = payload.get("ts")
            text = payload.get("text")
            
            if not all([channel, ts, text]):
                return {"error": "channel, ts, and text are required", "status": "failed"}
            
            url = f"{self.base_url}/chat.update"
            data = {
                "channel": channel,
                "ts": ts,
                "text": text
            }
            
            if payload.get("attachments"):
                data["attachments"] = payload["attachments"]
            if payload.get("blocks"):
                data["blocks"] = payload["blocks"]
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        return {
                            "message": {
                                "ts": result.get("ts"),
                                "channel": result.get("channel"),
                                "text": text
                            },
                            "status": "success"
                        }
                    else:
                        return {"error": result.get("error", "Failed to update message"), "status": "failed"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error updating message: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def delete_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a message."""
        try:
            channel = payload.get("channel")
            ts = payload.get("ts")
            
            if not all([channel, ts]):
                return {"error": "channel and ts are required", "status": "failed"}
            
            url = f"{self.base_url}/chat.delete"
            data = {
                "channel": channel,
                "ts": ts
            }
            
            if not self.session:
                raise RuntimeError("Session not initialized")
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    if result.get("ok"):
                        return {"status": "success"}
                    else:
                        return {"error": result.get("error", "Failed to delete message"), "status": "failed"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error deleting message: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def _cleanup_impl(self) -> None:
        """Cleanup Slack integration resources."""
        if self.session:
            await self.session.close()
            self.session = None
        self.logger.info("Slack integration cleaned up")


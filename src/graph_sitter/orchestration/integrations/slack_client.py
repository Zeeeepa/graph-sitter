"""
Slack Integration Client

Integration client for Slack API and webhook handling.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePlatformIntegration


class SlackIntegration(BasePlatformIntegration):
    """
    Slack platform integration for handling Slack API operations
    and webhook events.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("slack")
        self.config = config or {}
        self.bot_token = self.config.get("bot_token")
        self.app_token = self.config.get("app_token")
        self.signing_secret = self.config.get("signing_secret")
        self.base_url = self.config.get("base_url", "https://slack.com/api")
        
        # State
        self.authenticated = False
        self.bot_info: Optional[Dict[str, Any]] = None
        
        # Event handlers
        self.event_handlers: Dict[str, List[callable]] = {}
    
    async def start(self):
        """Start the Slack integration"""
        if self.running:
            return
        
        self.logger.info("Starting Slack integration")
        self.running = True
        
        # Authenticate if token provided
        if self.bot_token:
            self.authenticated = await self.authenticate({"bot_token": self.bot_token})
        
        # Start health monitoring
        asyncio.create_task(self._periodic_health_check())
        
        self.logger.info("Slack integration started")
    
    async def stop(self):
        """Stop the Slack integration"""
        self.logger.info("Stopping Slack integration")
        self.running = False
        self.logger.info("Slack integration stopped")
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Slack API"""
        bot_token = credentials.get("bot_token")
        if not bot_token:
            return False
        
        try:
            # Test authentication by getting bot info
            response = await self._api_request("auth.test")
            if response and response.get("ok"):
                self.authenticated = True
                self.bot_info = response
                self.logger.info(f"Authenticated as Slack bot: {response.get('user')} in team {response.get('team')}")
                return True
        
        except Exception as e:
            self.logger.error(f"Slack authentication failed: {e}")
        
        return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform Slack API health check"""
        try:
            # Check API status
            response = await self._api_request("auth.test")
            
            if response and response.get("ok"):
                healthy = True
                details = {
                    "authenticated": self.authenticated,
                    "bot_user_id": response.get("user_id"),
                    "team_id": response.get("team_id"),
                    "api_responsive": True
                }
            else:
                healthy = False
                details = {
                    "authenticated": self.authenticated,
                    "api_responsive": False,
                    "error": response.get("error", "Unknown error") if response else "No response"
                }
            
            self._update_health_status(healthy, details)
            return self.health_status
        
        except Exception as e:
            self.logger.error(f"Slack health check failed: {e}")
            self._update_health_status(False, {"error": str(e)})
        
        return self.health_status
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Slack integration status"""
        return {
            "platform": self.platform_name,
            "running": self.running,
            "authenticated": self.authenticated,
            "bot_info": self.bot_info,
            "health": self.health_status,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None
        }
    
    # Slack-specific methods
    
    async def send_message(self, channel: str, text: str, 
                          blocks: List[Dict[str, Any]] = None,
                          thread_ts: str = None) -> Optional[Dict[str, Any]]:
        """Send a message to a Slack channel"""
        data = {
            "channel": channel,
            "text": text
        }
        
        if blocks:
            data["blocks"] = blocks
        if thread_ts:
            data["thread_ts"] = thread_ts
        
        return await self._api_request("chat.postMessage", data)
    
    async def update_message(self, channel: str, ts: str, text: str,
                           blocks: List[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Update a Slack message"""
        data = {
            "channel": channel,
            "ts": ts,
            "text": text
        }
        
        if blocks:
            data["blocks"] = blocks
        
        return await self._api_request("chat.update", data)
    
    async def delete_message(self, channel: str, ts: str) -> Optional[Dict[str, Any]]:
        """Delete a Slack message"""
        data = {
            "channel": channel,
            "ts": ts
        }
        
        return await self._api_request("chat.delete", data)
    
    async def add_reaction(self, channel: str, timestamp: str, 
                          name: str) -> Optional[Dict[str, Any]]:
        """Add a reaction to a message"""
        data = {
            "channel": channel,
            "timestamp": timestamp,
            "name": name
        }
        
        return await self._api_request("reactions.add", data)
    
    async def get_channel_info(self, channel: str) -> Optional[Dict[str, Any]]:
        """Get information about a channel"""
        data = {"channel": channel}
        return await self._api_request("conversations.info", data)
    
    async def list_channels(self, types: str = "public_channel,private_channel") -> List[Dict[str, Any]]:
        """List channels"""
        data = {"types": types}
        response = await self._api_request("conversations.list", data)
        
        if response and response.get("ok"):
            return response.get("channels", [])
        
        return []
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a user"""
        data = {"user": user_id}
        response = await self._api_request("users.info", data)
        
        if response and response.get("ok"):
            return response.get("user")
        
        return None
    
    async def list_users(self) -> List[Dict[str, Any]]:
        """List users in the workspace"""
        response = await self._api_request("users.list")
        
        if response and response.get("ok"):
            return response.get("members", [])
        
        return []
    
    async def create_channel(self, name: str, is_private: bool = False) -> Optional[Dict[str, Any]]:
        """Create a new channel"""
        data = {
            "name": name,
            "is_private": is_private
        }
        
        response = await self._api_request("conversations.create", data)
        
        if response and response.get("ok"):
            return response.get("channel")
        
        return None
    
    async def invite_to_channel(self, channel: str, users: List[str]) -> Optional[Dict[str, Any]]:
        """Invite users to a channel"""
        data = {
            "channel": channel,
            "users": ",".join(users)
        }
        
        return await self._api_request("conversations.invite", data)
    
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Handle Slack webhook events"""
        try:
            self.logger.info(f"Handling Slack webhook: {event_type}")
            
            # Handle URL verification challenge
            if event_type == "url_verification":
                return payload.get("challenge")
            
            # Process event callbacks
            if event_type == "event_callback":
                event = payload.get("event", {})
                event_subtype = event.get("type")
                
                if event_subtype == "message":
                    await self._handle_message_event(event)
                elif event_subtype == "reaction_added":
                    await self._handle_reaction_event(event)
                elif event_subtype == "app_mention":
                    await self._handle_mention_event(event)
            
            # Call registered event handlers
            handlers = self.event_handlers.get(event_type, [])
            for handler in handlers:
                try:
                    await handler(payload)
                except Exception as e:
                    self.logger.error(f"Event handler error: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Webhook handling failed: {e}")
            return False
    
    def register_event_handler(self, event_type: str, handler: callable):
        """Register an event handler for specific Slack events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _handle_message_event(self, event: Dict[str, Any]):
        """Handle message events"""
        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text", "")
        
        self.logger.info(f"Message in {channel} from {user}: {text[:100]}...")
    
    async def _handle_reaction_event(self, event: Dict[str, Any]):
        """Handle reaction events"""
        reaction = event.get("reaction")
        user = event.get("user")
        item = event.get("item", {})
        
        self.logger.info(f"Reaction {reaction} added by {user} to message {item.get('ts')}")
    
    async def _handle_mention_event(self, event: Dict[str, Any]):
        """Handle app mention events"""
        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text", "")
        
        self.logger.info(f"App mentioned in {channel} by {user}: {text}")
    
    async def _api_request(self, method: str, data: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make a request to the Slack API"""
        if not self.bot_token:
            self.logger.error("No Slack bot token configured")
            return None
        
        import aiohttp
        
        url = f"{self.base_url}/{method}"
        headers = {
            "Authorization": f"Bearer {self.bot_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                if data:
                    async with session.post(url, headers=headers, json=data) as response:
                        return await response.json()
                else:
                    async with session.get(url, headers=headers) as response:
                        return await response.json()
        
        except Exception as e:
            self.logger.error(f"Slack API request failed: {e}")
            return None


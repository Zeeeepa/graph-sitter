"""
Linear Webhook Handlers

This module provides event handlers for Linear webhooks.
"""

from typing import Dict, Any
import logging

from ....shared.logging.get_logger import get_logger
from ..types import LinearEvent

logger = get_logger(__name__)

class WebhookHandlers:
    """Linear webhook event handlers"""
    
    def __init__(self):
        self._handlers = {
            "Issue.create": self._handle_issue_created,
            "Issue.update": self._handle_issue_updated,
            "Issue.delete": self._handle_issue_deleted,
            "Comment.create": self._handle_comment_created,
            "Project.create": self._handle_project_created,
            "Project.update": self._handle_project_updated,
        }
    
    async def handle_event(self, event: LinearEvent) -> None:
        """Handle a Linear event"""
        event_key = f"{event.type}.{event.action}"
        
        if event_key in self._handlers:
            try:
                await self._handlers[event_key](event)
            except Exception as e:
                logger.error(f"Error handling event {event_key}: {e}")
        else:
            logger.debug(f"No handler for event: {event_key}")
    
    async def _handle_issue_created(self, event: LinearEvent) -> None:
        """Handle issue created event"""
        logger.info(f"Issue created: {event.data.get('title', 'Unknown')}")
    
    async def _handle_issue_updated(self, event: LinearEvent) -> None:
        """Handle issue updated event"""
        logger.info(f"Issue updated: {event.data.get('title', 'Unknown')}")
    
    async def _handle_issue_deleted(self, event: LinearEvent) -> None:
        """Handle issue deleted event"""
        logger.info(f"Issue deleted: {event.data.get('title', 'Unknown')}")
    
    async def _handle_comment_created(self, event: LinearEvent) -> None:
        """Handle comment created event"""
        logger.info("Comment created on issue")
    
    async def _handle_project_created(self, event: LinearEvent) -> None:
        """Handle project created event"""
        logger.info(f"Project created: {event.data.get('name', 'Unknown')}")
    
    async def _handle_project_updated(self, event: LinearEvent) -> None:
        """Handle project updated event"""
        logger.info(f"Project updated: {event.data.get('name', 'Unknown')}")


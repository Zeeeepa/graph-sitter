"""
Simple Event Bus for Single-User Dashboard

Basic event handling for real-time updates without complex routing.
Uses simple pub/sub pattern with WebSocket for real-time dashboard updates.
"""

import logging
import asyncio
import json
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
from dataclasses import asdict

from graph_sitter.shared.logging.get_logger import get_logger
from .models import WorkflowEvent

logger = get_logger(__name__)


class EventBus:
    """
    Simple event bus for dashboard events.
    
    Features:
    - Basic pub/sub pattern
    - Event filtering by type and source
    - WebSocket broadcasting for real-time updates
    - Event history for debugging
    - Simple event handlers
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[WorkflowEvent] = []
        self.websocket_connections: List[Any] = []
        self.max_history = 1000  # Keep last 1000 events
        
    async def initialize(self):
        """Initialize the event bus"""
        logger.info("Initializing EventBus...")
        
    async def publish(self, event: WorkflowEvent):
        """
        Publish an event to all subscribers
        
        Args:
            event: Event to publish
        """
        try:
            # Add to history
            self.event_history.append(event)
            
            # Trim history if needed
            if len(self.event_history) > self.max_history:
                self.event_history = self.event_history[-self.max_history:]
                
            # Notify subscribers
            await self._notify_subscribers(event)
            
            # Broadcast to WebSocket connections
            await self._broadcast_to_websockets(event)
            
            logger.debug(f"Published event: {event.event_type} from {event.source}")
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            
    async def subscribe(self, event_type: str, handler: Callable):
        """
        Subscribe to events of a specific type
        
        Args:
            event_type: Type of events to subscribe to
            handler: Async function to handle events
        """
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
            
        self.subscribers[event_type].append(handler)
        logger.info(f"Subscribed to events: {event_type}")
        
    async def unsubscribe(self, event_type: str, handler: Callable):
        """
        Unsubscribe from events
        
        Args:
            event_type: Type of events to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self.subscribers:
            try:
                self.subscribers[event_type].remove(handler)
                logger.info(f"Unsubscribed from events: {event_type}")
            except ValueError:
                logger.warning(f"Handler not found for event type: {event_type}")
                
    async def _notify_subscribers(self, event: WorkflowEvent):
        """Notify all subscribers of an event"""
        try:
            # Notify specific event type subscribers
            if event.event_type in self.subscribers:
                for handler in self.subscribers[event.event_type]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Event handler failed: {e}")
                        
            # Notify wildcard subscribers
            if "*" in self.subscribers:
                for handler in self.subscribers["*"]:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Wildcard event handler failed: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to notify subscribers: {e}")
            
    async def _broadcast_to_websockets(self, event: WorkflowEvent):
        """Broadcast event to WebSocket connections"""
        if not self.websocket_connections:
            return
            
        # Convert event to JSON
        event_data = {
            "event_id": event.event_id,
            "event_type": event.event_type,
            "source": event.source,
            "project_id": event.project_id,
            "task_id": event.task_id,
            "data": event.data,
            "timestamp": event.timestamp.isoformat()
        }
        
        message = json.dumps(event_data)
        
        # Send to all connected WebSockets
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                disconnected.append(websocket)
                
        # Remove disconnected WebSockets
        for websocket in disconnected:
            self.websocket_connections.remove(websocket)
            
    async def add_websocket(self, websocket):
        """Add a WebSocket connection for real-time updates"""
        self.websocket_connections.append(websocket)
        logger.info("Added WebSocket connection")
        
    async def remove_websocket(self, websocket):
        """Remove a WebSocket connection"""
        if websocket in self.websocket_connections:
            self.websocket_connections.remove(websocket)
            logger.info("Removed WebSocket connection")
            
    def get_recent_events(self, limit: int = 50, event_type: Optional[str] = None, 
                         project_id: Optional[str] = None) -> List[WorkflowEvent]:
        """
        Get recent events with optional filtering
        
        Args:
            limit: Maximum number of events to return
            event_type: Filter by event type
            project_id: Filter by project ID
            
        Returns:
            List of recent events
        """
        events = self.event_history.copy()
        
        # Apply filters
        if event_type:
            events = [e for e in events if e.event_type == event_type]
            
        if project_id:
            events = [e for e in events if e.project_id == project_id]
            
        # Return most recent events
        return events[-limit:] if events else []
        
    def get_event_statistics(self) -> Dict[str, Any]:
        """Get event statistics"""
        if not self.event_history:
            return {
                "total_events": 0,
                "event_types": {},
                "sources": {},
                "projects": {}
            }
            
        # Count by type
        event_types = {}
        for event in self.event_history:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
            
        # Count by source
        sources = {}
        for event in self.event_history:
            sources[event.source] = sources.get(event.source, 0) + 1
            
        # Count by project
        projects = {}
        for event in self.event_history:
            if event.project_id:
                projects[event.project_id] = projects.get(event.project_id, 0) + 1
                
        return {
            "total_events": len(self.event_history),
            "event_types": event_types,
            "sources": sources,
            "projects": projects,
            "websocket_connections": len(self.websocket_connections)
        }
        
    async def clear_history(self):
        """Clear event history"""
        self.event_history.clear()
        logger.info("Cleared event history")
        
    async def shutdown(self):
        """Shutdown the event bus"""
        logger.info("Shutting down EventBus...")
        
        # Close all WebSocket connections
        for websocket in self.websocket_connections:
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(f"Failed to close WebSocket: {e}")
                
        self.websocket_connections.clear()
        self.subscribers.clear()
        
        logger.info("EventBus shutdown complete")


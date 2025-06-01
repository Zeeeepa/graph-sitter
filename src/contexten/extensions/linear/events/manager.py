"""
Linear Event Manager

This module provides event management and processing for Linear integration.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from ....shared.logging.get_logger import get_logger

logger = get_logger(__name__)

class EventManager:
    """Linear event management system"""
    
    def __init__(self):
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._pending_events: List[Dict[str, Any]] = []
        self._running = False
    
    async def start(self) -> None:
        """Start event manager"""
        self._running = True
        logger.info("Linear event manager started")
    
    async def stop(self) -> None:
        """Stop event manager"""
        self._running = False
        logger.info("Linear event manager stopped")
    
    async def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event"""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self._pending_events.append(event)
        logger.debug(f"Emitted event: {event_type}")
    
    async def process_pending_events(self) -> None:
        """Process all pending events"""
        while self._pending_events:
            event = self._pending_events.pop(0)
            await self._process_event(event)
    
    async def _process_event(self, event: Dict[str, Any]) -> None:
        """Process a single event"""
        event_type = event.get("type")
        if event_type in self._event_handlers:
            for handler in self._event_handlers[event_type]:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
    
    def is_healthy(self) -> bool:
        """Check if event manager is healthy"""
        return self._running


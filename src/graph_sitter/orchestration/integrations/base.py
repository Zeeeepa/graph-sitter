"""
Base Platform Integration

Abstract base class for platform integrations.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime


class BasePlatformIntegration(ABC):
    """
    Abstract base class for platform integrations.
    
    All platform integrations should inherit from this class and implement
    the required methods for their specific platform.
    """
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.logger = logging.getLogger(f"{__name__}.{platform_name}")
        self.running = False
        self.last_health_check: Optional[datetime] = None
        self.health_status: Dict[str, Any] = {"healthy": True}
    
    @abstractmethod
    async def start(self):
        """Start the platform integration"""
        pass
    
    @abstractmethod
    async def stop(self):
        """Stop the platform integration"""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check for this integration
        
        Returns:
            Dictionary with health status information
        """
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of this integration
        
        Returns:
            Dictionary with status information
        """
        pass
    
    # Common methods that can be overridden by specific integrations
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """
        Authenticate with the platform
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            True if authentication successful
        """
        # Default implementation - override in subclasses
        return True
    
    async def send_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Send an event to the platform
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            True if event sent successfully
        """
        # Default implementation - override in subclasses
        self.logger.info(f"Sending {event_type} event to {self.platform_name}")
        return True
    
    async def receive_events(self) -> List[Dict[str, Any]]:
        """
        Receive events from the platform
        
        Returns:
            List of events
        """
        # Default implementation - override in subclasses
        return []
    
    def _update_health_status(self, healthy: bool, details: Dict[str, Any] = None):
        """Update the health status of this integration"""
        self.health_status = {
            "healthy": healthy,
            "last_check": datetime.now().isoformat(),
            "platform": self.platform_name,
            "details": details or {}
        }
        self.last_health_check = datetime.now()
    
    async def _periodic_health_check(self, interval: int = 300):
        """Perform periodic health checks"""
        while self.running:
            try:
                await self.health_check()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health check failed: {e}")
                self._update_health_status(False, {"error": str(e)})
                await asyncio.sleep(interval)


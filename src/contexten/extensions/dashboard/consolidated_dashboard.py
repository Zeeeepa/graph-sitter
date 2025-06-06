"""
Consolidated Dashboard Extension.
Main entry point for the comprehensive dashboard system.
"""

import logging
import os
from typing import Optional

from .consolidated_api import ConsolidatedDashboardAPI, create_dashboard_app
from .consolidated_models import UserSettings

logger = logging.getLogger(__name__)


class ConsolidatedDashboard:
    """
    Main dashboard extension class that consolidates all PR features.
    Provides a unified interface for the complete dashboard system.
    """
    
    def __init__(self, contexten_app=None):
        """Initialize the Consolidated Dashboard."""
        self.contexten_app = contexten_app
        self.api = ConsolidatedDashboardAPI(contexten_app)
        self.app = self.api.app
        
        # Configuration
        self.host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
        self.port = int(os.getenv("DASHBOARD_PORT", "8000"))
        self.debug = os.getenv("DASHBOARD_DEBUG", "false").lower() == "true"
        
        logger.info("Consolidated Dashboard initialized")
    
    async def start(self):
        """Start the dashboard server."""
        try:
            import uvicorn
            
            logger.info(f"Starting Consolidated Dashboard on {self.host}:{self.port}")
            
            config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                reload=self.debug,
                log_level="debug" if self.debug else "info"
            )
            
            server = uvicorn.Server(config)
            await server.serve()
            
        except Exception as e:
            logger.error(f"Failed to start dashboard server: {e}")
            raise
    
    def run(self):
        """Run the dashboard server (blocking)."""
        try:
            import uvicorn
            
            logger.info(f"Running Consolidated Dashboard on {self.host}:{self.port}")
            
            uvicorn.run(
                app=self.app,
                host=self.host,
                port=self.port,
                reload=self.debug,
                log_level="debug" if self.debug else "info"
            )
            
        except Exception as e:
            logger.error(f"Failed to run dashboard server: {e}")
            raise
    
    async def stop(self):
        """Stop the dashboard server."""
        try:
            # Stop background monitoring
            if hasattr(self.api, 'monitoring_service'):
                self.api.monitoring_service.stop_monitoring()
            
            logger.info("Consolidated Dashboard stopped")
            
        except Exception as e:
            logger.error(f"Error stopping dashboard: {e}")
    
    def get_health_status(self):
        """Get current health status."""
        try:
            return {
                "status": "healthy",
                "services": {
                    "api": "running",
                    "websocket": "active",
                    "monitoring": "enabled"
                },
                "active_connections": len(self.api.active_connections),
                "background_tasks": len(self.api.background_tasks)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


def create_consolidated_dashboard(contexten_app=None) -> ConsolidatedDashboard:
    """Factory function to create a consolidated dashboard instance."""
    return ConsolidatedDashboard(contexten_app)


# For direct execution
if __name__ == "__main__":
    import asyncio
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run dashboard
    dashboard = create_consolidated_dashboard()
    
    try:
        dashboard.run()
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Dashboard failed: {e}")
        raise


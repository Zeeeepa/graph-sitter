#!/usr/bin/env python3
"""
Strands Backend - Unified Entry Point
Clean, maintainable backend that coordinates all Strands tools
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Add the dashboard directory to Python path
dashboard_dir = os.path.dirname(os.path.abspath(__file__))
if dashboard_dir not in sys.path:
    sys.path.insert(0, dashboard_dir)

try:
    import uvicorn
    from strands_api import create_strands_api
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install -r requirements.txt")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class StrandsBackend:
    """
    Unified Strands backend coordinator
    """
    
    def __init__(self):
        self.app = None
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables"""
        return {
            # Server configuration
            'host': os.getenv('STRANDS_HOST', '0.0.0.0'),
            'port': int(os.getenv('STRANDS_PORT', '8000')),
            'debug': os.getenv('STRANDS_DEBUG', 'false').lower() == 'true',
            'reload': os.getenv('STRANDS_RELOAD', 'false').lower() == 'true',
            
            # Codegen SDK configuration
            'codegen_org_id': os.getenv('CODEGEN_ORG_ID'),
            'codegen_token': os.getenv('CODEGEN_TOKEN'),
            
            # Strands tools configuration
            'strands_workflow_enabled': os.getenv('STRANDS_WORKFLOW_ENABLED', 'true').lower() == 'true',
            'strands_mcp_enabled': os.getenv('STRANDS_MCP_ENABLED', 'true').lower() == 'true',
            'controlflow_enabled': os.getenv('CONTROLFLOW_ENABLED', 'true').lower() == 'true',
            'prefect_enabled': os.getenv('PREFECT_ENABLED', 'true').lower() == 'true',
            
            # System monitoring configuration
            'system_watcher_enabled': os.getenv('SYSTEM_WATCHER_ENABLED', 'true').lower() == 'true',
            'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
            
            # Logging configuration
            'log_level': os.getenv('LOG_LEVEL', 'INFO').upper(),
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config['log_level'], logging.INFO)
        
        # Configure root logger
        logging.getLogger().setLevel(log_level)
        
        # Configure specific loggers
        logging.getLogger('uvicorn').setLevel(log_level)
        logging.getLogger('fastapi').setLevel(log_level)
        logging.getLogger('strands').setLevel(log_level)
        
        logger.info(f"Logging configured at {self.config['log_level']} level")
    
    def _validate_config(self) -> bool:
        """Validate configuration"""
        issues = []
        
        # Check Codegen SDK configuration
        if not self.config['codegen_org_id']:
            issues.append("CODEGEN_ORG_ID environment variable not set")
        
        if not self.config['codegen_token']:
            issues.append("CODEGEN_TOKEN environment variable not set")
        
        # Check port availability
        port = self.config['port']
        if not (1024 <= port <= 65535):
            issues.append(f"Invalid port number: {port}")
        
        if issues:
            logger.error("Configuration validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def create_app(self):
        """Create FastAPI application"""
        try:
            logger.info("Creating Strands FastAPI application...")
            
            # Set environment variables for components
            if self.config['codegen_org_id']:
                os.environ['CODEGEN_ORG_ID'] = self.config['codegen_org_id']
            if self.config['codegen_token']:
                os.environ['CODEGEN_TOKEN'] = self.config['codegen_token']
            
            # Create the FastAPI app
            self.app = create_strands_api()
            
            logger.info("Strands FastAPI application created successfully")
            return self.app
            
        except Exception as e:
            logger.error(f"Failed to create FastAPI application: {e}")
            raise
    
    async def start_server(self):
        """Start the Strands backend server"""
        try:
            logger.info("Starting Strands Backend Server...")
            logger.info(f"Configuration: {self.config}")
            
            # Setup logging
            self._setup_logging()
            
            # Validate configuration
            if not self._validate_config():
                logger.error("Configuration validation failed. Exiting.")
                return False
            
            # Create FastAPI app
            self.create_app()
            
            # Configure uvicorn
            uvicorn_config = uvicorn.Config(
                app=self.app,
                host=self.config['host'],
                port=self.config['port'],
                log_level=self.config['log_level'].lower(),
                reload=self.config['reload'],
                access_log=True
            )
            
            # Start server
            server = uvicorn.Server(uvicorn_config)
            
            logger.info(f"Strands Backend starting on http://{self.config['host']}:{self.config['port']}")
            logger.info("Available endpoints:")
            logger.info("  - GET  /api/health - Health check")
            logger.info("  - POST /api/workflows - Create workflow")
            logger.info("  - GET  /api/workflows - List workflows")
            logger.info("  - POST /api/codegen/tasks - Create Codegen task")
            logger.info("  - GET  /api/codegen/tasks - List Codegen tasks")
            logger.info("  - GET  /api/system/health - System health")
            logger.info("  - WS   /ws - WebSocket connection")
            
            await server.serve()
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
            return True
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def run(self):
        """Run the Strands backend (synchronous entry point)"""
        try:
            return asyncio.run(self.start_server())
        except KeyboardInterrupt:
            logger.info("Strands Backend shutdown complete")
            return True
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            return False

def main():
    """Main entry point"""
    print("🚀 Strands Agent Dashboard Backend")
    print("=" * 50)
    
    backend = StrandsBackend()
    success = backend.run()
    
    if success:
        print("\n✅ Strands Backend shutdown gracefully")
        sys.exit(0)
    else:
        print("\n❌ Strands Backend encountered errors")
        sys.exit(1)

if __name__ == "__main__":
    main()


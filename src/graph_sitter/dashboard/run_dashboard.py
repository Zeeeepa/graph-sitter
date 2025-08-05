#!/usr/bin/env python3
"""
Linear & GitHub Dashboard Startup Script

This script starts the dashboard server with proper configuration and logging.
"""

import argparse
import os
import sys
import uvicorn
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from graph_sitter.dashboard.api.main import create_dashboard_app
from graph_sitter.dashboard.utils.config import DashboardConfig
from graph_sitter.dashboard.utils.logger import configure_dashboard_logging


def main():
    """Main entry point for the dashboard."""
    parser = argparse.ArgumentParser(description="Linear & GitHub Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    
    args = parser.parse_args()
    
    # Configure logging
    configure_dashboard_logging(args.log_level)
    
    # Create configuration
    config = DashboardConfig.from_env()
    config.host = args.host
    config.port = args.port
    config.debug = args.debug
    
    # Validate configuration
    missing_keys = config.get_missing_keys()
    if missing_keys:
        print(f"⚠️  Warning: Missing API keys: {', '.join(missing_keys)}")
        print("Some features may be limited. Set the following environment variables:")
        for key in missing_keys:
            env_var = key.upper().replace("_TOKEN", "_ACCESS_TOKEN")
            print(f"  - {env_var}")
        print()
    
    # Create app
    app = create_dashboard_app(config)
    
    print("🚀 Starting Linear & GitHub Dashboard")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"📚 API Docs: http://{args.host}:{args.port}/docs")
    print(f"🏥 Health Check: http://{args.host}:{args.port}/health")
    print()
    
    # Start server
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()


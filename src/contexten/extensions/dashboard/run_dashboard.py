#!/usr/bin/env python3
"""
Dashboard Startup Script

Simple script to run the Contexten Dashboard for single-user scenarios.
"""

import asyncio
import logging
import uvicorn
from pathlib import Path

from graph_sitter.shared.logging.get_logger import get_logger
from .dashboard import create_dashboard

logger = get_logger(__name__)


async def main():
    """Main startup function"""
    print("🚀 Starting Contexten Dashboard...")
    print("=" * 50)
    
    # Create dashboard
    dashboard = create_dashboard()
    
    # Initialize dashboard
    try:
        await dashboard.initialize()
        print("✅ Dashboard initialized successfully")
    except Exception as e:
        print(f"❌ Dashboard initialization failed: {e}")
        return
        
    # Print setup status
    setup_status = dashboard.settings_manager.get_setup_status()
    print("\n📋 Setup Status:")
    print(f"  GitHub: {'✅' if setup_status['credentials']['github'] else '❌'}")
    print(f"  Codegen: {'✅' if setup_status['credentials']['codegen'] else '❌'}")
    print(f"  Linear: {'✅' if setup_status['credentials']['linear'] else '❌'}")
    print(f"  Slack: {'✅' if setup_status['credentials']['slack'] else '❌'}")
    print(f"  Ready: {'✅' if setup_status['ready'] else '❌'}")
    
    if not setup_status['ready']:
        print("\n⚠️  Missing required credentials!")
        print(dashboard.settings_manager.get_configuration_help())
        
    print("\n🌐 Starting web server...")
    print("Dashboard will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    # Start the server
    config = uvicorn.Config(
        app=dashboard.app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down dashboard...")
        await dashboard.shutdown()
        print("✅ Dashboard stopped")


if __name__ == "__main__":
    asyncio.run(main())


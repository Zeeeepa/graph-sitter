#!/usr/bin/env python3
"""
Contexten Enhanced Dashboard Launcher

Launch the comprehensive contexten dashboard with all enhanced features:
- Flow management and parameter configuration
- Project pinning and requirements tracking
- Real-time progress monitoring
- Linear issue state tracking
- GitHub PR automation and validation
- Autonomous CI/CD pipeline management
- Error healing and system recovery
- WebSocket support for real-time updates

Usage:
    python launch_dashboard.py [--host HOST] [--port PORT] [--debug]
"""

import asyncio
import os
import sys
import argparse
import logging
import webbrowser
from pathlib import Path
import uvicorn

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))  # Add src directory to path

# Try importing with graceful error handling
try:
    from contexten.dashboard.app import app, config
    CONTEXTEN_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import contexten modules: {e}")
    print("Some features may be limited. Ensure the package is properly installed.")
    app = None
    config = None
    CONTEXTEN_AVAILABLE = False

# Only proceed if contexten is available
if not CONTEXTEN_AVAILABLE:
    print("Error: Contexten dashboard modules are not available.")
    print("Please ensure the contexten package is properly installed.")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if required environment variables are set"""
    required_vars = {
        "CODEGEN_ORG_ID": "Codegen organization ID",
        "CODEGEN_TOKEN": "Codegen API token"
    }
    
    optional_vars = {
        "GITHUB_TOKEN": "GitHub personal access token",
        "LINEAR_API_KEY": "Linear API key",
        "SLACK_WEBHOOK_URL": "Slack webhook URL",
        "PREFECT_API_URL": "Prefect API URL",
        "PREFECT_WORKSPACE": "Prefect workspace"
    }
    
    missing_required = []
    missing_optional = []
    
    # Check if we have any environment tokens available
    env_tokens_available = any([
        os.getenv("GITHUB_TOKEN"),
        os.getenv("LINEAR_API_KEY"),
        os.getenv("SLACK_WEBHOOK_URL")
    ])
    
    # If environment tokens are available, make Codegen tokens optional
    if env_tokens_available:
        # Move Codegen vars to optional when env tokens are present
        optional_vars.update(required_vars)
        required_vars = {}
    
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"  {var}: {description}")
    
    for var, description in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"  {var}: {description}")
    
    if missing_required:
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(var)
        print("\nPlease set these variables and try again.")
        return False
    
    if missing_optional:
        print("⚠️  Missing optional environment variables (some features may be limited):")
        for var in missing_optional:
            print(var)
        print()
    
    print("✅ Environment check passed!")
    return True


def print_banner():
    """Print the dashboard banner"""
    banner = """
╔════�������════�������════════════════════════════════════════════════════════════════════╗
║                        Contexten Enhanced Dashboard                          ║
║                                                                              ║
║  🚀 Comprehensive Flow Management & CI/CD Automation                        ║
║  📊 Real-time Project Monitoring & Analytics                                ║
║  🔗 Linear/GitHub/Slack Integration                                         ║
║  🤖 Autonomous Error Healing & Recovery                                     ║
║  ⚡ WebSocket Real-time Updates                                             ║
║                                                                              ║
╚═══════════════════���═���═���══════���═���═���═══════════════════════════════════════════╝
"""
    print(banner)


def print_features():
    """Print available features"""
    features = """
🎯 Available Features:

📋 Flow Management:
   • Create and configure autonomous flows
   • Real-time progress tracking with WebSocket updates
   • Flow parameter configuration and templates
   • Flow execution control (start/stop/monitor)

📁 Project Management:
   • Pin projects for quick access
   • Requirements tracking and management
   • Project health monitoring and analytics
   • Team collaboration features

🔗 Integration Hub:
   • Linear issue state tracking and automation
   • GitHub PR management and validation
   • Slack notifications and alerts
   • Codegen SDK integration for AI-powered tasks

🤖 Autonomous Operations:
   • Self-healing flows with intelligent error recovery
   • Automated CI/CD pipeline optimization
   • Predictive maintenance and monitoring
   • Smart notification routing

📊 Analytics & Monitoring:
   • Real-time system health monitoring
   • Flow performance analytics and trends
   • Resource utilization tracking
   • Comprehensive reporting dashboard
"""
    print(features)


def print_api_endpoints():
    """Print key API endpoints"""
    endpoints = """
🔌 Key API Endpoints:

Flow Management:
   GET    /api/flows                    - List all flows
   POST   /api/flows/create             - Create new flow
   GET    /api/flows/{id}               - Get flow details
   POST   /api/flows/{id}/start         - Start flow execution
   GET    /api/flows/{id}/progress      - Get real-time progress
   WS     /ws/flows/{id}                - Real-time flow updates

Project Management:
   GET    /api/projects/pinned          - Get pinned projects
   POST   /api/projects/{id}/pin        - Pin a project
   GET    /api/projects/{id}/dashboard  - Get project dashboard
   GET    /api/projects/{id}/requirements - Get project requirements
   WS     /ws/projects/{id}             - Real-time project updates

Linear Integration:
   GET    /api/linear/issues/{project}  - Get Linear issues with states
   GET    /api/linear/issues/{id}/state - Get detailed issue state
   POST   /api/linear/sync/{project}    - Sync Linear with flows

Templates & Configuration:
   GET    /api/flow-templates           - Get available flow templates
   GET    /api/flow-templates/{id}      - Get template details
"""
    print(endpoints)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Contexten Enhanced Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    parser.add_argument("--show-features", action="store_true", help="Show available features")
    parser.add_argument("--show-api", action="store_true", help="Show API endpoints")
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Show features if requested
    if args.show_features:
        print_features()
        return
    
    # Show API endpoints if requested
    if args.show_api:
        print_api_endpoints()
        return
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    print("✅ Environment check passed!")
    print(f"🌐 Starting dashboard on http://{args.host}:{args.port}")
    print("📱 Dashboard features:")
    print("   • Flow Management & Monitoring")
    print("   • Project Pinning & Requirements")
    print("   • Linear/GitHub Integration")
    print("   • Real-time Updates via WebSocket")
    print("   • Autonomous Error Healing")
    print()
    
    # Open browser if not disabled
    if not args.no_browser:
        dashboard_url = f"http://localhost:{args.port}"
        print(f"🚀 Opening dashboard in browser: {dashboard_url}")
        webbrowser.open(dashboard_url)
    
    # Configure uvicorn
    log_level = "debug" if args.debug else "info"
    
    config = uvicorn.Config(
        app=app,
        host=args.host,
        port=args.port,
        log_level=log_level,
        reload=args.debug,
        access_log=True
    )
    
    server = uvicorn.Server(config)
    
    try:
        print("🎉 Dashboard is ready! Press Ctrl+C to stop.")
        await server.serve()
    except KeyboardInterrupt:
        print("\n👋 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

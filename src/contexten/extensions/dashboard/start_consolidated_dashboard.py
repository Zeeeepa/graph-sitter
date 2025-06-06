#!/usr/bin/env python3
"""
Startup script for the Consolidated Strands Agent Dashboard.
Provides easy way to launch the dashboard with proper configuration.
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.contexten.extensions.dashboard.consolidated_dashboard import create_consolidated_dashboard


def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('dashboard.log')
        ]
    )
    
    # Reduce noise from some libraries
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('websockets').setLevel(logging.WARNING)


def check_environment():
    """Check required environment variables."""
    required_vars = ['CODEGEN_ORG_ID', 'CODEGEN_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Warning: Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nThe dashboard will use mock implementations for missing integrations.")
        print("Set these variables for full functionality:")
        for var in missing_vars:
            print(f"   export {var}='your-{var.lower().replace('_', '-')}'")
        print()
    
    # Check optional variables
    optional_vars = {
        'GITHUB_ACCESS_TOKEN': 'GitHub integration',
        'LINEAR_ACCESS_TOKEN': 'Linear integration', 
        'SLACK_BOT_TOKEN': 'Slack integration'
    }
    
    missing_optional = []
    for var, description in optional_vars.items():
        if not os.getenv(var):
            missing_optional.append(f"{var} ({description})")
    
    if missing_optional:
        print("ℹ️  Optional integrations not configured:")
        for var in missing_optional:
            print(f"   - {var}")
        print()


def print_banner():
    """Print startup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        🚀 Consolidated Strands Agent Dashboard 🚀           ║
║                                                              ║
║  Comprehensive dashboard for Strands tools ecosystem        ║
║  • Multi-layer orchestration (Strands + ControlFlow +       ║
║    Prefect)                                                  ║
║  • AI-powered planning with Codegen SDK                     ║
║  • Real-time monitoring and quality gates                   ║
║  • GitHub, Linear, and Slack integrations                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Start the Consolidated Strands Agent Dashboard'
    )
    parser.add_argument(
        '--host', 
        default=os.getenv('DASHBOARD_HOST', '0.0.0.0'),
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port', 
        type=int,
        default=int(os.getenv('DASHBOARD_PORT', '8000')),
        help='Port to bind to (default: 8000)'
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        default=os.getenv('DASHBOARD_DEBUG', 'false').lower() == 'true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--reload',
        action='store_true', 
        help='Enable auto-reload (development mode)'
    )
    parser.add_argument(
        '--check-env',
        action='store_true',
        help='Check environment variables and exit'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.debug)
    logger = logging.getLogger(__name__)
    
    # Print banner
    print_banner()
    
    # Check environment
    check_environment()
    
    if args.check_env:
        print("Environment check complete.")
        return
    
    try:
        # Create dashboard
        logger.info("Creating consolidated dashboard...")
        dashboard = create_consolidated_dashboard()
        
        # Configure host and port
        dashboard.host = args.host
        dashboard.port = args.port
        dashboard.debug = args.debug or args.reload
        
        # Print startup info
        print(f"🌐 Starting dashboard on http://{args.host}:{args.port}")
        print(f"📚 API documentation: http://{args.host}:{args.port}/docs")
        print(f"🔌 WebSocket endpoint: ws://{args.host}:{args.port}/ws")
        print(f"❤️  Health check: http://{args.host}:{args.port}/health")
        print()
        print("Press Ctrl+C to stop the dashboard")
        print("=" * 60)
        
        # Start dashboard
        dashboard.run()
        
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
        print("\n👋 Dashboard stopped. Goodbye!")
    except Exception as e:
        logger.error(f"Dashboard failed to start: {e}")
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


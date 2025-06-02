#!/usr/bin/env python3
"""
Contexten Unified Dashboard

A comprehensive dashboard for managing autonomous CI/CD flows, project tracking,
Linear issue management, GitHub PR automation, and full workflow orchestration.

This serves as the main entry point for the contexten system, providing:
- Flow management and parameter configuration
- Project pinning and requirements tracking
- Real-time progress monitoring
- Linear issue state tracking
- GitHub PR automation and validation
- Autonomous CI/CD pipeline management
- Error healing and system recovery
- Notification and alerting system

Usage:
    python -m src.contexten.dashboard
    # or
    python src/contexten/dashboard.py
"""

import asyncio
import os
import sys
import logging
import signal
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import uvicorn

# Add the project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import the existing dashboard app
from src.contexten.dashboard.app import app as dashboard_app
from src.contexten.dashboard.prefect_dashboard import PrefectDashboardManager
from src.contexten.dashboard.flow_manager import flow_manager, FlowStatus, FlowPriority
from src.contexten.dashboard.project_manager import project_manager, ProjectStatus, ProjectHealth
from src.contexten.dashboard.enhanced_routes import setup_enhanced_routes
from src.contexten.orchestration.autonomous_orchestrator import AutonomousOrchestrator
from src.contexten.orchestration.config import OrchestrationConfig
from src.contexten.orchestration.monitoring import SystemMonitor
from src.contexten.orchestration.workflow_types import AutonomousWorkflowType

# Import agents and extensions
try:
    from .extensions.linear.enhanced_agent import EnhancedLinearAgent
    from .extensions.github.enhanced_agent import EnhancedGitHubAgent
    from .extensions.slack.enhanced_agent import EnhancedSlackAgent
except ImportError as e:
    logger.warning(f"Failed to import enhanced agents: {e}")
    EnhancedLinearAgent = None
    EnhancedGitHubAgent = None
    EnhancedSlackAgent = None

# Import Codegen SDK
try:
    from codegen import Agent as CodegenAgent
except ImportError:
    print("Warning: Codegen SDK not available. Some features may be limited.")
    CodegenAgent = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('contexten_dashboard.log')
    ]
)
logger = logging.getLogger(__name__)


class ContextenDashboard:
    """
    Unified dashboard coordinator for the contexten system.
    
    This class orchestrates all components of the contexten system including:
    - FastAPI web dashboard
    - Prefect workflow management
    - Autonomous orchestration
    - System monitoring
    - Agent coordination
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the dashboard with configuration."""
        self.config = self._load_config(config_path)
        self.orchestrator = None
        self.monitor = None
        self.prefect_manager = None
        self.agents = {}
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Contexten Dashboard initialized")
    
    def _load_config(self, config_path: Optional[str] = None) -> OrchestrationConfig:
        """Load configuration from environment or file."""
        config = OrchestrationConfig()
        
        # Load from environment variables
        config.codegen_org_id = os.getenv('CODEGEN_ORG_ID')
        config.codegen_token = os.getenv('CODEGEN_TOKEN')
        config.github_token = os.getenv('GITHUB_TOKEN')
        config.linear_api_key = os.getenv('LINEAR_API_KEY')
        config.slack_webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        config.prefect_api_url = os.getenv('PREFECT_API_URL')
        config.prefect_workspace = os.getenv('PREFECT_WORKSPACE')
        
        return config
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    async def initialize_components(self):
        """Initialize all dashboard components."""
        logger.info("Initializing dashboard components...")
        
        try:
            # Initialize autonomous orchestrator
            self.orchestrator = AutonomousOrchestrator(self.config)
            await self.orchestrator.initialize()
            logger.info("✅ Autonomous orchestrator initialized")
            
            # Initialize system monitor
            self.monitor = SystemMonitor(self.config)
            await self.monitor.start()
            logger.info("✅ System monitor started")
            
            # Initialize Prefect dashboard manager
            self.prefect_manager = PrefectDashboardManager(self.config)
            await self.prefect_manager.initialize()
            logger.info("✅ Prefect dashboard manager initialized")
            
            # Initialize agents
            await self._initialize_agents()
            logger.info("✅ All agents initialized")
            
            # Setup dashboard routes
            self._setup_dashboard_routes()
            logger.info("✅ Dashboard routes configured")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise
    
    async def _initialize_agents(self):
        """Initialize all AI agents."""
        try:
            # Initialize chat agent
            self.agents['chat'] = ChatAgent()
            
            # Initialize code agent
            self.agents['code'] = CodeAgent()
            
            # Initialize Codegen SDK agent if available
            if CodegenAgent and self.config.codegen_org_id and self.config.codegen_token:
                self.agents['codegen'] = CodegenAgent(
                    org_id=self.config.codegen_org_id,
                    token=self.config.codegen_token
                )
                logger.info("✅ Codegen SDK agent initialized")
            
            # Initialize Linear agent if configured
            if self.config.linear_api_key:
                self.agents['linear'] = EnhancedLinearAgent(
                    api_key=self.config.linear_api_key
                )
                logger.info("✅ Linear agent initialized")
            
            # Initialize GitHub agent if configured
            if self.config.github_token:
                self.agents['github'] = EnhancedGitHubAgent(
                    token=self.config.github_token
                )
                logger.info("✅ GitHub agent initialized")
            
            # Initialize Slack agent if configured
            if self.config.slack_webhook_url:
                self.agents['slack'] = EnhancedSlackAgent(
                    webhook_url=self.config.slack_webhook_url
                )
                logger.info("✅ Slack agent initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def _setup_dashboard_routes(self):
        """Setup additional dashboard routes for flow management."""
        
        # Setup enhanced routes with all the new functionality
        setup_enhanced_routes(
            app=dashboard_app,
            agents=self.agents,
            monitor=self.monitor,
            orchestrator=self.orchestrator
        )
        
        logger.info("Enhanced dashboard routes configured")
    
    async def start_dashboard(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the dashboard server."""
        logger.info(f"Starting Contexten Dashboard on {host}:{port}")
        
        # Initialize all components
        await self.initialize_components()
        
        # Configure uvicorn
        config = uvicorn.Config(
            app=dashboard_app,
            host=host,
            port=port,
            log_level="info",
            reload=False,
            access_log=True
        )
        
        server = uvicorn.Server(config)
        self.running = True
        
        try:
            # Start background tasks
            background_tasks = [
                self._run_monitoring_loop(),
                self._run_orchestration_loop(),
                self._run_health_checks()
            ]
            
            # Start server and background tasks
            await asyncio.gather(
                server.serve(),
                *background_tasks,
                return_exceptions=True
            )
            
        except Exception as e:
            logger.error(f"Dashboard server error: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def _run_monitoring_loop(self):
        """Run continuous system monitoring."""
        while self.running:
            try:
                if self.monitor:
                    await self.monitor.collect_metrics()
                await asyncio.sleep(60)  # Monitor every minute
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _run_orchestration_loop(self):
        """Run autonomous orchestration loop."""
        while self.running:
            try:
                if self.orchestrator:
                    await self.orchestrator.process_pending_workflows()
                await asyncio.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Orchestration loop error: {e}")
                await asyncio.sleep(30)
    
    async def _run_health_checks(self):
        """Run periodic health checks."""
        while self.running:
            try:
                if self.monitor:
                    health_status = await self.monitor.perform_health_check()
                    if not health_status.get('healthy', True):
                        logger.warning(f"Health check failed: {health_status}")
                        # Trigger recovery procedures if needed
                        if self.orchestrator:
                            await self.orchestrator.trigger_recovery()
                
                await asyncio.sleep(300)  # Health check every 5 minutes
            except Exception as e:
                logger.error(f"Health check error: {e}")
                await asyncio.sleep(300)
    
    async def shutdown(self):
        """Gracefully shutdown all components."""
        logger.info("Shutting down Contexten Dashboard...")
        
        self.running = False
        
        try:
            if self.monitor:
                await self.monitor.stop()
                logger.info("✅ System monitor stopped")
            
            if self.orchestrator:
                await self.orchestrator.shutdown()
                logger.info("✅ Autonomous orchestrator stopped")
            
            if self.prefect_manager:
                await self.prefect_manager.shutdown()
                logger.info("✅ Prefect dashboard manager stopped")
            
            logger.info("✅ Dashboard shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def print_startup_banner():
    """Print startup banner with system information."""
    banner = """
    ╔════════════════════════���═════════════════════════════════════╗
    ║                    CONTEXTEN DASHBOARD                       ║
    ║                                                              ║
    ║  🚀 Autonomous CI/CD Flow Management System                  ║
    ║  📊 Real-time Project & Issue Tracking                      ║
    ║  🔄 GitHub PR Automation & Validation                       ║
    ║  🎯 Linear Issue State Management                           ║
    ║  🛠️  Intelligent Error Healing & Recovery                   ║
    ║  📈 Comprehensive System Monitoring                         ║
    ║                                                              ║
    ║  Access the dashboard at: http://localhost:8000             ║
    ╚═════════════════════════════════════════════��════════════════╝
    """
    print(banner)


def check_environment():
    """Check environment setup and provide guidance."""
    missing_vars = []
    optional_vars = []
    
    # Required environment variables
    required = {
        'CODEGEN_ORG_ID': 'Codegen organization ID',
        'CODEGEN_TOKEN': 'Codegen API token'
    }
    
    # Optional but recommended
    optional = {
        'GITHUB_TOKEN': 'GitHub personal access token',
        'LINEAR_API_KEY': 'Linear API key',
        'SLACK_WEBHOOK_URL': 'Slack webhook URL',
        'PREFECT_API_URL': 'Prefect API URL',
        'PREFECT_WORKSPACE': 'Prefect workspace name'
    }
    
    for var, desc in required.items():
        if not os.getenv(var):
            missing_vars.append(f"  ❌ {var}: {desc}")
    
    for var, desc in optional.items():
        if not os.getenv(var):
            optional_vars.append(f"  ⚠️  {var}: {desc}")
    
    if missing_vars:
        print("\n🔴 Missing required environment variables:")
        print("\n".join(missing_vars))
        print("\nPlease set these variables before starting the dashboard.")
        return False
    
    if optional_vars:
        print("\n🟡 Optional environment variables not set:")
        print("\n".join(optional_vars))
        print("\nSome features may be limited without these variables.")
    
    print("\n✅ Environment check passed!")
    return True


async def main():
    """Main entry point for the dashboard."""
    print_startup_banner()
    
    # Check environment setup
    if not check_environment():
        sys.exit(1)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='Contexten Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Create and start dashboard
    dashboard = ContextenDashboard(config_path=args.config)
    
    try:
        await dashboard.start_dashboard(host=args.host, port=args.port)
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Dashboard failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Run the dashboard
    asyncio.run(main())

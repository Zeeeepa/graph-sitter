#!/usr/bin/env python3
"""
Contexten Dashboard Launcher
Comprehensive launcher script for the enhanced dashboard
"""

import os
import sys
import argparse
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

logger = logging.getLogger(__name__)

class DashboardLauncher:
    """
    Comprehensive dashboard launcher with environment setup and validation
    """
    
    def __init__(self):
        self.project_root = project_root
        self.dashboard_dir = Path(__file__).parent
        self.env_file = self.project_root / ".env"
        
    def setup_logging(self, debug: bool = False):
        """Setup logging configuration"""
        level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.project_root / "dashboard.log")
            ]
        )
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        required_packages = [
            "fastapi",
            "uvicorn",
            "jinja2",
            "python-multipart",
            "aiofiles",
            "httpx",
            "pydantic"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            logger.error("Missing required packages:")
            for package in missing_packages:
                logger.error(f"  - {package}")
            logger.error("Install with: pip install " + " ".join(missing_packages))
            return False
        
        logger.info("✅ All required dependencies are installed")
        return True
    
    def check_environment(self) -> bool:
        """Check environment configuration"""
        logger.info("Checking environment configuration...")
        
        # Check if .env file exists
        if not self.env_file.exists():
            logger.warning(f".env file not found at {self.env_file}")
            self.create_default_env_file()
        
        # Load environment variables
        try:
            from dotenv import load_dotenv
            load_dotenv(self.env_file)
            logger.info("✅ Environment variables loaded")
        except ImportError:
            logger.warning("python-dotenv not installed, using system environment")
        
        # Check critical environment variables
        critical_vars = {
            "DASHBOARD_HOST": "0.0.0.0",
            "DASHBOARD_PORT": "8080",
            "DASHBOARD_SECRET_KEY": None
        }
        
        missing_vars = []
        for var, default in critical_vars.items():
            value = os.getenv(var, default)
            if not value:
                missing_vars.append(var)
            else:
                logger.info(f"✅ {var}: {value if var != 'DASHBOARD_SECRET_KEY' else '***'}")
        
        if missing_vars:
            logger.error("Missing critical environment variables:")
            for var in missing_vars:
                logger.error(f"  - {var}")
            return False
        
        return True
    
    def create_default_env_file(self):
        """Create a default .env file"""
        logger.info("Creating default .env file...")
        
        default_env_content = """# Contexten Dashboard Configuration
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8080
DASHBOARD_DEBUG=false
DASHBOARD_SECRET_KEY=your-secret-key-change-this

# Integration Tokens (Optional)
# GITHUB_TOKEN=your-github-token
# LINEAR_API_KEY=your-linear-api-key
# PREFECT_API_KEY=your-prefect-api-key
# SLACK_WEBHOOK_URL=your-slack-webhook

# Database Configuration (Optional)
# DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis Configuration (Optional)
# REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO
"""
        
        try:
            with open(self.env_file, 'w') as f:
                f.write(default_env_content)
            logger.info(f"✅ Default .env file created at {self.env_file}")
            logger.warning("⚠️  Please update the .env file with your actual configuration")
        except Exception as e:
            logger.error(f"Failed to create .env file: {e}")
    
    def check_templates(self) -> bool:
        """Check if dashboard templates exist"""
        templates_dir = self.dashboard_dir / "templates"
        required_templates = [
            "dashboard.html",
            "prefect_dashboard.html"
        ]
        
        if not templates_dir.exists():
            logger.error(f"Templates directory not found: {templates_dir}")
            return False
        
        missing_templates = []
        for template in required_templates:
            template_path = templates_dir / template
            if not template_path.exists():
                missing_templates.append(template)
        
        if missing_templates:
            logger.error("Missing required templates:")
            for template in missing_templates:
                logger.error(f"  - {template}")
            return False
        
        logger.info("✅ All required templates are present")
        return True
    
    def check_static_files(self) -> bool:
        """Check if static files exist"""
        static_dir = self.dashboard_dir / "static"
        required_files = [
            "css/dashboard.css",
            "js/dashboard.js"
        ]
        
        if not static_dir.exists():
            logger.warning(f"Static directory not found: {static_dir}")
            return True  # Not critical, will use CDN fallbacks
        
        missing_files = []
        for file_path in required_files:
            full_path = static_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        if missing_files:
            logger.warning("Missing static files (will use CDN fallbacks):")
            for file_path in missing_files:
                logger.warning(f"  - {file_path}")
        else:
            logger.info("✅ All static files are present")
        
        return True
    
    def validate_installation(self) -> bool:
        """Validate the complete installation"""
        logger.info("Validating dashboard installation...")
        
        checks = [
            ("Dependencies", self.check_dependencies),
            ("Environment", self.check_environment),
            ("Templates", self.check_templates),
            ("Static Files", self.check_static_files)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            logger.info(f"Checking {check_name}...")
            if not check_func():
                logger.error(f"❌ {check_name} check failed")
                all_passed = False
            else:
                logger.info(f"✅ {check_name} check passed")
        
        return all_passed
    
    def install_dependencies(self):
        """Install missing dependencies"""
        logger.info("Installing dashboard dependencies...")
        
        try:
            # Install the package in development mode
            subprocess.run([
                sys.executable, "-m", "pip", "install", "-e", "."
            ], cwd=self.project_root, check=True)
            
            logger.info("✅ Dependencies installed successfully")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            raise
    
    def launch_dashboard(
        self,
        host: str = None,
        port: int = None,
        debug: bool = False,
        reload: bool = False
    ):
        """Launch the dashboard"""
        # Get configuration
        host = host or os.getenv("DASHBOARD_HOST", "0.0.0.0")
        port = port or int(os.getenv("DASHBOARD_PORT", "8080"))
        debug = debug or os.getenv("DASHBOARD_DEBUG", "false").lower() == "true"
        
        logger.info(f"Launching Contexten Dashboard...")
        logger.info(f"Host: {host}")
        logger.info(f"Port: {port}")
        logger.info(f"Debug: {debug}")
        logger.info(f"URL: http://{host}:{port}")
        
        try:
            import uvicorn
            from contexten.dashboard.app import app
            
            # Configure uvicorn
            config = uvicorn.Config(
                app=app,
                host=host,
                port=port,
                log_level="debug" if debug else "info",
                reload=reload,
                access_log=True
            )
            
            server = uvicorn.Server(config)
            
            # Run the server
            logger.info("🚀 Starting dashboard server...")
            server.run()
            
        except ImportError as e:
            logger.error(f"Failed to import required modules: {e}")
            logger.error("Try running: pip install -e .")
            raise
        except Exception as e:
            logger.error(f"Failed to launch dashboard: {e}")
            raise
    
    def run_setup_wizard(self):
        """Interactive setup wizard"""
        print("🚀 Contexten Dashboard Setup Wizard")
        print("=" * 50)
        
        # Check if this is first run
        if not self.env_file.exists():
            print("First time setup detected!")
            
            # Ask for basic configuration
            host = input("Dashboard host (default: 0.0.0.0): ").strip() or "0.0.0.0"
            port = input("Dashboard port (default: 8080): ").strip() or "8080"
            
            # Ask for integrations
            print("\nOptional integrations:")
            github_token = input("GitHub token (optional): ").strip()
            linear_key = input("Linear API key (optional): ").strip()
            prefect_key = input("Prefect API key (optional): ").strip()
            
            # Create .env file
            env_content = f"""# Contexten Dashboard Configuration
DASHBOARD_HOST={host}
DASHBOARD_PORT={port}
DASHBOARD_DEBUG=false
DASHBOARD_SECRET_KEY=dashboard-secret-{os.urandom(16).hex()}

# Integration Tokens
"""
            
            if github_token:
                env_content += f"GITHUB_TOKEN={github_token}\n"
            if linear_key:
                env_content += f"LINEAR_API_KEY={linear_key}\n"
            if prefect_key:
                env_content += f"PREFECT_API_KEY={prefect_key}\n"
            
            with open(self.env_file, 'w') as f:
                f.write(env_content)
            
            print(f"✅ Configuration saved to {self.env_file}")
        
        # Install dependencies if needed
        if not self.check_dependencies():
            install = input("Install missing dependencies? (Y/n): ").strip().lower()
            if install != 'n':
                self.install_dependencies()
        
        print("\n🎉 Setup complete! Ready to launch dashboard.")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Contexten Dashboard Launcher")
    parser.add_argument("--host", default=None, help="Dashboard host")
    parser.add_argument("--port", type=int, default=None, help="Dashboard port")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--setup", action="store_true", help="Run setup wizard")
    parser.add_argument("--validate", action="store_true", help="Validate installation only")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies only")
    
    args = parser.parse_args()
    
    # Initialize launcher
    launcher = DashboardLauncher()
    launcher.setup_logging(args.debug)
    
    try:
        # Run setup wizard if requested
        if args.setup:
            launcher.run_setup_wizard()
            return
        
        # Install dependencies if requested
        if args.install_deps:
            launcher.install_dependencies()
            return
        
        # Validate installation
        if not launcher.validate_installation():
            logger.error("❌ Installation validation failed")
            logger.info("Run with --setup to configure the dashboard")
            sys.exit(1)
        
        # Validate only if requested
        if args.validate:
            logger.info("✅ Installation validation passed")
            return
        
        # Launch dashboard
        launcher.launch_dashboard(
            host=args.host,
            port=args.port,
            debug=args.debug,
            reload=args.reload
        )
        
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()


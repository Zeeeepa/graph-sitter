#!/usr/bin/env python3
"""
Comprehensive Dashboard Launch Script
Validates and launches the complete Contexten Dashboard system with full component connectivity.
"""

import os
import sys
import subprocess
import time
import signal
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DashboardLauncher:
    """Comprehensive dashboard launcher with full component validation."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.dashboard_dir = self.project_root / "src" / "contexten" / "extensions" / "dashboard"
        self.frontend_dir = self.dashboard_dir / "frontend"
        self.processes = {}
        self.environment_validated = False
        
    def validate_environment(self) -> bool:
        """Validate all required environment variables and dependencies."""
        logger.info("🔍 Validating environment...")
        
        # Check Python dependencies
        try:
            import fastapi
            import uvicorn
            import websockets
            import sqlalchemy
            logger.info("✅ Python dependencies available")
        except ImportError as e:
            logger.error(f"❌ Missing Python dependency: {e}")
            return False
        
        # Check Node.js and npm
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Node.js available (version {result.stdout.strip()})")
            else:
                logger.error("❌ Node.js not available")
                return False
                
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ npm available (version {result.stdout.strip()})")
            else:
                logger.error("❌ npm not available")
                return False
        except FileNotFoundError:
            logger.error("❌ Node.js/npm not found")
            return False
        
        # Check environment variables (optional but recommended)
        env_vars = {
            'GITHUB_TOKEN': 'GitHub integration',
            'LINEAR_API_KEY': 'Linear integration',
            'SLACK_BOT_TOKEN': 'Slack integration',
            'CODEGEN_ORG_ID': 'Codegen SDK',
            'CODEGEN_TOKEN': 'Codegen SDK',
            'POSTGRESQL_URL': 'Database connection',
            'CIRCLECI_TOKEN': 'CircleCI integration'
        }
        
        missing_vars = []
        for var, description in env_vars.items():
            if not os.environ.get(var):
                missing_vars.append(f"{var} ({description})")
        
        if missing_vars:
            logger.warning("⚠️  Missing environment variables (dashboard will work with limited functionality):")
            for var in missing_vars:
                logger.warning(f"   - {var}")
        else:
            logger.info("✅ All environment variables configured")
        
        self.environment_validated = True
        return True
    
    def validate_file_structure(self) -> bool:
        """Validate that all required files exist."""
        logger.info("📁 Validating file structure...")
        
        required_files = [
            self.dashboard_dir / "main.py",
            self.dashboard_dir / "api.py",
            self.dashboard_dir / "dashboard.py",
            self.frontend_dir / "package.json",
            self.frontend_dir / "src" / "App.tsx",
            self.frontend_dir / "src" / "components" / "ProjectCard.tsx",
            self.frontend_dir / "src" / "components" / "ProjectDialog.tsx",
            self.frontend_dir / "src" / "components" / "TopBar.tsx",
            self.frontend_dir / "src" / "components" / "SettingsDialog.tsx",
        ]
        
        missing_files = []
        for file_path in required_files:
            if not file_path.exists():
                missing_files.append(str(file_path))
        
        if missing_files:
            logger.error("❌ Missing required files:")
            for file in missing_files:
                logger.error(f"   - {file}")
            return False
        
        logger.info("✅ All required files present")
        return True
    
    def install_frontend_dependencies(self) -> bool:
        """Install frontend dependencies if needed."""
        node_modules = self.frontend_dir / "node_modules"
        
        if not node_modules.exists():
            logger.info("📦 Installing frontend dependencies...")
            try:
                result = subprocess.run(
                    ['npm', 'install'], 
                    cwd=self.frontend_dir, 
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info("✅ Frontend dependencies installed")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install frontend dependencies: {e}")
                logger.error(f"stdout: {e.stdout}")
                logger.error(f"stderr: {e.stderr}")
                return False
        else:
            logger.info("✅ Frontend dependencies already installed")
            return True
    
    def start_backend(self) -> Optional[subprocess.Popen]:
        """Start the FastAPI backend server."""
        logger.info("🚀 Starting backend server...")
        
        try:
            # Use the ContextenApp integration
            cmd = [
                sys.executable, "-c", 
                """
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.contexten.extensions.contexten_app.contexten_app import ContextenApp
import uvicorn

# Create ContextenApp instance
app = ContextenApp(name="Contexten Dashboard", repo="Zeeeepa/graph-sitter")

# Initialize services
import asyncio
asyncio.run(app.initialize_services())

# Run the app
uvicorn.run(app.app, host="0.0.0.0", port=8000, log_level="info")
"""
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Give backend time to start
            time.sleep(3)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info("✅ Backend server started successfully")
                return process
            else:
                logger.error("❌ Backend server failed to start")
                if process.stdout:
                    output = process.stdout.read()
                    logger.error(f"Backend output: {output}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to start backend: {e}")
            return None
    
    def start_frontend(self) -> Optional[subprocess.Popen]:
        """Start the React frontend server."""
        logger.info("🎨 Starting frontend server...")
        
        try:
            # Set environment variables for frontend
            env = os.environ.copy()
            env['PORT'] = '3001'
            env['BROWSER'] = 'none'  # Don't auto-open browser
            env['REACT_APP_API_URL'] = 'http://localhost:8000'
            
            process = subprocess.Popen(
                ['npm', 'start'],
                cwd=self.frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Give frontend time to start
            time.sleep(5)
            
            # Check if process is still running
            if process.poll() is None:
                logger.info("✅ Frontend server started successfully")
                return process
            else:
                logger.error("❌ Frontend server failed to start")
                if process.stdout:
                    output = process.stdout.read()
                    logger.error(f"Frontend output: {output}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to start frontend: {e}")
            return None
    
    def validate_connectivity(self) -> bool:
        """Validate that all components are properly connected."""
        logger.info("🔗 Validating component connectivity...")
        
        import requests
        import time
        
        # Test backend health
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Backend health check passed")
            else:
                logger.error(f"❌ Backend health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Backend connectivity failed: {e}")
            return False
        
        # Test API endpoints
        try:
            response = requests.get("http://localhost:8000/api/projects", timeout=5)
            if response.status_code == 200:
                logger.info("✅ API endpoints accessible")
            else:
                logger.error(f"❌ API endpoints failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ API connectivity failed: {e}")
            return False
        
        # Test frontend accessibility
        try:
            response = requests.get("http://localhost:3001", timeout=10)
            if response.status_code == 200:
                logger.info("✅ Frontend accessible")
            else:
                logger.error(f"❌ Frontend accessibility failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Frontend connectivity failed: {e}")
            return False
        
        logger.info("✅ All component connectivity validated")
        return True
    
    def launch(self) -> bool:
        """Launch the complete dashboard system."""
        logger.info("🎯 Launching Contexten Dashboard System")
        logger.info("=" * 50)
        
        # Step 1: Validate environment
        if not self.validate_environment():
            logger.error("❌ Environment validation failed")
            return False
        
        # Step 2: Validate file structure
        if not self.validate_file_structure():
            logger.error("❌ File structure validation failed")
            return False
        
        # Step 3: Install dependencies
        if not self.install_frontend_dependencies():
            logger.error("❌ Frontend dependency installation failed")
            return False
        
        # Step 4: Start backend
        backend_process = self.start_backend()
        if not backend_process:
            logger.error("❌ Backend startup failed")
            return False
        self.processes['backend'] = backend_process
        
        # Step 5: Start frontend
        frontend_process = self.start_frontend()
        if not frontend_process:
            logger.error("❌ Frontend startup failed")
            self.cleanup()
            return False
        self.processes['frontend'] = frontend_process
        
        # Step 6: Validate connectivity
        time.sleep(3)  # Give services time to fully initialize
        if not self.validate_connectivity():
            logger.error("❌ Component connectivity validation failed")
            self.cleanup()
            return False
        
        # Success!
        logger.info("")
        logger.info("🎉 Dashboard launched successfully!")
        logger.info("=" * 50)
        logger.info("🌐 Frontend UI: http://localhost:3001")
        logger.info("🔧 Backend API: http://localhost:8000")
        logger.info("📚 API Documentation: http://localhost:8000/docs")
        logger.info("=" * 50)
        logger.info("Press Ctrl+C to stop all services")
        logger.info("")
        
        return True
    
    def monitor_processes(self):
        """Monitor running processes and handle cleanup."""
        try:
            while True:
                time.sleep(1)
                
                # Check if processes are still running
                for name, process in self.processes.items():
                    if process.poll() is not None:
                        logger.error(f"❌ {name.title()} process stopped unexpectedly")
                        self.cleanup()
                        return
                        
        except KeyboardInterrupt:
            logger.info("\n🛑 Shutting down dashboard...")
            self.cleanup()
    
    def cleanup(self):
        """Clean up all running processes."""
        for name, process in self.processes.items():
            if process and process.poll() is None:
                logger.info(f"🛑 Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(f"⚠️  Force killing {name}...")
                    process.kill()
        
        logger.info("✅ All services stopped")

def main():
    """Main entry point."""
    launcher = DashboardLauncher()
    
    if launcher.launch():
        launcher.monitor_processes()
    else:
        logger.error("❌ Dashboard launch failed")
        sys.exit(1)

if __name__ == "__main__":
    main()


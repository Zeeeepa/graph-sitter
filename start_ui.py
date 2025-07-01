#!/usr/bin/env python3
"""
Graph-Sitter UI Launcher
Comprehensive startup script for the Graph-Sitter dashboard system.
"""

import asyncio
import subprocess
import sys
import os
import signal
import time
from pathlib import Path
from typing import Optional, List
import uvicorn
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UILauncher:
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.dashboard_server: Optional[uvicorn.Server] = None
        
    def cleanup(self):
        """Clean up all running processes"""
        print("\n🛑 Shutting down all services...")
        
        # Stop dashboard server
        if self.dashboard_server:
            try:
                self.dashboard_server.should_exit = True
            except:
                pass
                
        # Stop all subprocesses
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except:
                pass
                
        print("✅ All services stopped")

    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.cleanup()
        sys.exit(0)

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        print("🔍 Checking dependencies...")
        
        # Check Node.js/npm
        try:
            result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ npm version: {result.stdout.strip()}")
            else:
                print("❌ npm not found")
                return False
        except FileNotFoundError:
            print("❌ npm not found")
            return False
            
        # Check Python packages
        try:
            import fastapi
            import uvicorn
            print("✅ FastAPI and uvicorn available")
        except ImportError as e:
            print(f"❌ Missing Python packages: {e}")
            return False
            
        return True

    def setup_frontend(self) -> bool:
        """Set up the React frontend"""
        frontend_dir = Path("src/contexten/frontend")
        
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False
            
        print("📦 Setting up React frontend...")
        
        # Check if node_modules exists
        if not (frontend_dir / "node_modules").exists():
            print("📥 Installing npm dependencies...")
            try:
                result = subprocess.run(
                    ['npm', 'install'], 
                    cwd=frontend_dir, 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    print(f"❌ npm install failed: {result.stderr}")
                    return False
                print("✅ npm dependencies installed")
            except Exception as e:
                print(f"❌ Failed to install dependencies: {e}")
                return False
        else:
            print("✅ npm dependencies already installed")
            
        return True

    def start_backend_dashboard(self):
        """Start the dashboard backend server"""
        print("🚀 Starting dashboard backend...")
        
        try:
            # Try to import and start the dashboard
            from src.contexten.extensions.dashboard.dashboard import create_dashboard
            
            dashboard = create_dashboard()
            
            # Create uvicorn config
            config = uvicorn.Config(
                app=dashboard.app,
                host="0.0.0.0",
                port=8000,
                log_level="info"
            )
            
            self.dashboard_server = uvicorn.Server(config)
            
            print("✅ Dashboard backend started on http://localhost:8000")
            return True
            
        except Exception as e:
            print(f"❌ Failed to start dashboard backend: {e}")
            print("💡 Trying alternative backend...")
            return self.start_simple_backend()

    def start_simple_backend(self):
        """Start a simple FastAPI backend as fallback"""
        print("🔄 Starting simple backend...")
        
        # Create a simple backend script
        simple_backend = '''
import asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import uvicorn

app = FastAPI(title="Graph-Sitter Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3001", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Graph-Sitter Dashboard API", "status": "running"}

@app.get("/api/projects")
async def get_projects():
    return {"projects": [
        {
            "id": "1",
            "name": "Graph-Sitter Core",
            "description": "Code analysis framework",
            "status": "active",
            "lastUpdated": datetime.now().isoformat()
        }
    ]}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''
        
        with open("simple_backend.py", "w") as f:
            f.write(simple_backend)
            
        try:
            process = subprocess.Popen([
                sys.executable, "simple_backend.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(process)
            time.sleep(2)  # Give it time to start
            
            if process.poll() is None:
                print("✅ Simple backend started on http://localhost:8000")
                return True
            else:
                print("❌ Simple backend failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start simple backend: {e}")
            return False

    def start_frontend(self):
        """Start the React frontend"""
        print("🌐 Starting React frontend...")
        
        frontend_dir = Path("src/contexten/frontend")
        
        try:
            process = subprocess.Popen([
                'npm', 'start'
            ], cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes.append(process)
            time.sleep(3)  # Give it time to start
            
            if process.poll() is None:
                print("✅ React frontend started on http://localhost:3001")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Frontend failed to start: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return False

    async def run(self):
        """Main run method"""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("🚀 Graph-Sitter UI Launcher")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            print("❌ Dependency check failed")
            return
            
        # Setup frontend
        if not self.setup_frontend():
            print("❌ Frontend setup failed")
            return
            
        # Start backend
        backend_started = self.start_backend_dashboard()
        if not backend_started:
            print("❌ Backend startup failed")
            return
            
        # Start frontend
        frontend_started = self.start_frontend()
        if not frontend_started:
            print("❌ Frontend startup failed")
            return
            
        print("\n🎉 All services started successfully!")
        print("📍 Frontend: http://localhost:3001")
        print("📍 Backend API: http://localhost:8000")
        print("📍 API Docs: http://localhost:8000/docs")
        print("\n🛑 Press Ctrl+C to stop all services")
        print("=" * 50)
        
        # Keep running
        try:
            if self.dashboard_server:
                await self.dashboard_server.serve()
            else:
                # Just wait if using simple backend
                while True:
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    launcher = UILauncher()
    try:
        asyncio.run(launcher.run())
    except KeyboardInterrupt:
        launcher.cleanup()

if __name__ == "__main__":
    main()


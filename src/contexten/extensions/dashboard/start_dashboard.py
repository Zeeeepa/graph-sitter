#!/usr/bin/env python3
"""
Contexten Dashboard Startup Script
Launches both backend and frontend for the dashboard
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import uvicorn
        import fastapi
        print("✅ Python dependencies available")
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("Install with: pip install fastapi uvicorn")
        return False
    
    # Check if npm is available
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm available (version {result.stdout.strip()})")
        else:
            print("❌ npm not available")
            return False
    except FileNotFoundError:
        print("❌ npm not found. Please install Node.js and npm")
        return False
    
    return True

def install_frontend_deps():
    """Install frontend dependencies if needed"""
    frontend_dir = Path(__file__).parent / "frontend"
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("📦 Installing frontend dependencies...")
        try:
            subprocess.run(['npm', 'install'], cwd=frontend_dir, check=True)
            print("✅ Frontend dependencies installed")
        except subprocess.CalledProcessError:
            print("❌ Failed to install frontend dependencies")
            return False
    else:
        print("✅ Frontend dependencies already installed")
    
    return True

def start_backend():
    """Start the FastAPI backend"""
    print("🚀 Starting backend server...")
    backend_dir = Path(__file__).parent
    
    # Start uvicorn server
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "api:app", 
        "--host", "0.0.0.0", 
        "--port", "8000", 
        "--reload"
    ]
    
    return subprocess.Popen(cmd, cwd=backend_dir)

def start_frontend():
    """Start the React frontend"""
    print("🎯 Starting frontend server...")
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Set environment variables
    env = os.environ.copy()
    env['PORT'] = '3001'
    env['BROWSER'] = 'none'  # Don't auto-open browser
    
    cmd = ['npm', 'start']
    
    return subprocess.Popen(cmd, cwd=frontend_dir, env=env)

def main():
    """Main startup function"""
    print("🎯 Contexten Dashboard Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Install frontend dependencies
    if not install_frontend_deps():
        sys.exit(1)
    
    # Start processes
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend
        backend_process = start_backend()
        time.sleep(2)  # Give backend time to start
        
        # Start frontend
        frontend_process = start_frontend()
        time.sleep(3)  # Give frontend time to start
        
        print("\n🎉 Dashboard started successfully!")
        print("=" * 40)
        print("🌐 Frontend UI: http://localhost:3001")
        print("🔧 Backend API: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("=" * 40)
        print("Press Ctrl+C to stop both servers")
        
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend process stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down dashboard...")
        
    finally:
        # Clean up processes
        if backend_process:
            backend_process.terminate()
            try:
                backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                backend_process.kill()
        
        if frontend_process:
            frontend_process.terminate()
            try:
                frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                frontend_process.kill()
        
        print("✅ Dashboard stopped")

if __name__ == "__main__":
    main()


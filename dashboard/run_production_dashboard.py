#!/usr/bin/env python3
"""
PRODUCTION DASHBOARD LAUNCHER
Starts both backend and frontend for the real codebase analysis dashboard
"""

import subprocess
import sys
import time
import os
import signal
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import reflex
        import httpx
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting backend server...")
    backend_process = subprocess.Popen([
        sys.executable, "-c",
        """
import sys
sys.path.insert(0, '.')
from backend_core import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000, log_level='info')
        """
    ], cwd=Path(__file__).parent)
    
    # Wait for backend to start
    time.sleep(3)
    return backend_process

def start_frontend():
    """Start the Reflex frontend"""
    print("🎨 Starting frontend dashboard...")
    
    # Initialize reflex if needed
    try:
        subprocess.run(["reflex", "init"], cwd=Path(__file__).parent, check=False, capture_output=True)
    except:
        pass
    
    # Start frontend
    frontend_process = subprocess.Popen([
        "reflex", "run", "--frontend-port", "3000", "--backend-port", "8001"
    ], cwd=Path(__file__).parent)
    
    return frontend_process

def main():
    """Main launcher function"""
    print("=" * 60)
    print("🔍 REAL CODEBASE ANALYSIS DASHBOARD")
    print("Complete production dashboard with graph-sitter integration")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start processes
    backend_process = None
    frontend_process = None
    
    try:
        # Start backend
        backend_process = start_backend()
        print("✅ Backend started on http://localhost:8000")
        
        # Start frontend
        frontend_process = start_frontend()
        print("✅ Frontend started on http://localhost:3000")
        
        print("\n" + "=" * 60)
        print("🎉 DASHBOARD IS READY!")
        print("📊 Open your browser to: http://localhost:3000")
        print("🔧 Backend API available at: http://localhost:8000")
        print("📚 API docs at: http://localhost:8000/docs")
        print("=" * 60)
        print("\n💡 FEATURES AVAILABLE:")
        print("  • Real graph-sitter codebase analysis")
        print("  • Interactive tree structure visualization")
        print("  • Complete issue detection and context")
        print("  • Dead code analysis and removal")
        print("  • Important functions identification")
        print("  • Entry points detection")
        print("  • Comprehensive statistics")
        print("  • Auto-resolve capabilities")
        print("\n🔗 Enter any GitHub repository URL to analyze!")
        print("\nPress Ctrl+C to stop both servers...")
        
        # Wait for processes
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend process died")
                break
                
            if frontend_process.poll() is not None:
                print("❌ Frontend process died")
                break
    
    except KeyboardInterrupt:
        print("\n🛑 Shutting down dashboard...")
        
    finally:
        # Clean up processes
        if backend_process:
            try:
                backend_process.terminate()
                backend_process.wait(timeout=5)
                print("✅ Backend stopped")
            except:
                backend_process.kill()
                print("🔥 Backend force killed")
        
        if frontend_process:
            try:
                frontend_process.terminate()
                frontend_process.wait(timeout=5)
                print("✅ Frontend stopped")
            except:
                frontend_process.kill()
                print("🔥 Frontend force killed")
        
        print("👋 Dashboard shutdown complete")

if __name__ == "__main__":
    main()

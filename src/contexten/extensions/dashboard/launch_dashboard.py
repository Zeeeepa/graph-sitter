#!/usr/bin/env python3
"""
Dashboard Launch Script
Starts the Contexten Dashboard backend server with proper configuration.
"""

import os
import sys
import subprocess
import uvicorn
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import fastapi
        import uvicorn
        print("✅ Backend dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing backend dependencies: {e}")
        print("Please install with: pip install fastapi uvicorn python-multipart")
        return False

def check_frontend():
    """Check if frontend is set up."""
    frontend_dir = Path(__file__).parent / "frontend"
    node_modules = frontend_dir / "node_modules"
    
    if not node_modules.exists():
        print("⚠️  Frontend dependencies not installed")
        print(f"Please run: cd {frontend_dir} && npm install")
        return False
    
    print("✅ Frontend dependencies found")
    return True

def start_backend():
    """Start the backend server."""
    print("🚀 Starting Dashboard Backend Server...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("📍 API docs will be available at: http://localhost:8000/docs")
    print("📍 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Import the FastAPI app
        from api.enhanced_endpoints import app
        
        # Start the server
        uvicorn.run(
            "api.enhanced_endpoints:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except ImportError:
        print("❌ Could not import FastAPI app")
        print("Please ensure api/enhanced_endpoints.py exists and is properly configured")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)

def start_frontend():
    """Start the frontend development server."""
    frontend_dir = Path(__file__).parent / "frontend"
    
    print("🚀 Starting Dashboard Frontend Server...")
    print("📍 Frontend will be available at: http://localhost:3000")
    print("📍 Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        subprocess.run(
            ["npm", "start"],
            cwd=frontend_dir,
            check=True
        )
    except subprocess.CalledProcessError:
        print("❌ Failed to start frontend server")
        print("Please ensure you're in the correct directory and npm is installed")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped by user")
        sys.exit(0)

def main():
    """Main launch function."""
    print("🎯 Contexten Dashboard Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check frontend setup
    frontend_ready = check_frontend()
    
    # Get launch mode
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
    else:
        print("\nSelect launch mode:")
        print("1. Backend only")
        print("2. Frontend only") 
        print("3. Full stack (both)")
        
        choice = input("\nEnter choice (1-3) or 'backend'/'frontend'/'both': ").strip()
        
        if choice in ['1', 'backend']:
            mode = 'backend'
        elif choice in ['2', 'frontend']:
            mode = 'frontend'
        elif choice in ['3', 'both', 'full']:
            mode = 'both'
        else:
            mode = 'backend'  # default
    
    print(f"\n🚀 Launching in {mode} mode...")
    
    if mode == 'backend':
        start_backend()
    elif mode == 'frontend':
        if not frontend_ready:
            print("❌ Frontend not ready. Please install dependencies first.")
            sys.exit(1)
        start_frontend()
    elif mode == 'both':
        print("🔄 Full stack mode requires running backend and frontend separately")
        print("\nTo start both servers:")
        print("1. Terminal 1: python launch_dashboard.py backend")
        print("2. Terminal 2: python launch_dashboard.py frontend")
        print("\nOr use the individual commands:")
        print("Backend: python launch_dashboard.py backend")
        print("Frontend: cd frontend && npm start")
        
        # Default to backend for now
        start_backend()
    else:
        print(f"❌ Unknown mode: {mode}")
        print("Available modes: backend, frontend, both")
        sys.exit(1)

if __name__ == "__main__":
    main()


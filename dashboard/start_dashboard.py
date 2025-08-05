#!/usr/bin/env python3
"""
Dashboard Startup Script

Starts both the backend API server and the Reflex frontend dashboard.
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path
import threading


def start_backend():
    """Start the FastAPI backend server."""
    print("🚀 Starting Backend API Server...")
    try:
        subprocess.run([
            sys.executable, "backend_server.py"
        ], cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")


def start_frontend():
    """Start the Reflex frontend dashboard."""
    print("🎨 Starting Reflex Frontend Dashboard...")
    time.sleep(3)  # Give backend time to start
    try:
        subprocess.run([
            "reflex", "run", "--frontend-port", "3000", "--backend-port", "3001"
        ], cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n🛑 Frontend dashboard stopped")


def main():
    """Main startup function."""
    print("=" * 60)
    print("🔍 CODEBASE ANALYSIS DASHBOARD")
    print("=" * 60)
    print("Starting comprehensive codebase analysis dashboard...")
    print("Backend API: http://localhost:8000")
    print("Frontend Dashboard: http://localhost:3000")
    print("API Documentation: http://localhost:8000/docs")
    print("=" * 60)
    
    # Check if reflex is installed
    try:
        subprocess.run(["reflex", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Error: Reflex is not installed or not in PATH")
        print("Please install Reflex: pip install reflex")
        sys.exit(1)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(2)
    
    try:
        # Start frontend (this will block)
        start_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down dashboard...")
        print("👋 Thank you for using the Codebase Analysis Dashboard!")


if __name__ == "__main__":
    main()


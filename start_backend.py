#!/usr/bin/env python3
"""
Simple script to start the enhanced codebase analytics backend.
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    # Change to backend directory
    backend_dir = Path(__file__).parent / "backend"
    
    if not backend_dir.exists():
        print("❌ Backend directory not found!")
        sys.exit(1)
    
    # Check if requirements are installed
    try:
        import fastapi
        import uvicorn
        import graph_sitter
    except ImportError as e:
        print(f"❌ Missing dependencies: {e}")
        print("💡 Run: cd backend && pip install -r requirements.txt")
        sys.exit(1)
    
    print("🚀 Starting Enhanced Codebase Analytics Backend...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("📖 API docs will be available at: http://localhost:8000/docs")
    print("🔄 Press Ctrl+C to stop")
    print("-" * 50)
    
    # Start the server
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], cwd=backend_dir)
    except KeyboardInterrupt:
        print("\n👋 Backend stopped")

if __name__ == "__main__":
    main()


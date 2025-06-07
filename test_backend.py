#!/usr/bin/env python3
"""
Simple backend test to validate API functionality
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from src.contexten.extensions.dashboard.main import app
    import uvicorn
    
    print("✅ Successfully imported dashboard app")
    print("🚀 Starting test server...")
    
    if __name__ == "__main__":
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Trying alternative import...")
    
    try:
        # Alternative: Use the simple main.py
        import subprocess
        subprocess.run([sys.executable, "./src/contexten/extensions/dashboard/main.py"])
    except Exception as e2:
        print(f"❌ Alternative failed: {e2}")
        sys.exit(1)


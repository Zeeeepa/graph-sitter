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
    from contexten.extensions.contexten_app.contexten_app import ContextenApp
    import uvicorn
    
    print("✅ Successfully imported contexten app")
    print("🚀 Starting test server...")
    
    if __name__ == "__main__":
        app_instance = ContextenApp(name="Test Contexten App")
        uvicorn.run(app_instance.app, host="0.0.0.0", port=8000, log_level="info")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("❌ Failed to start test server")
    sys.exit(1)


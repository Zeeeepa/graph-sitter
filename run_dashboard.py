#!/usr/bin/env python3
"""
Simple Dashboard Runner
Quick way to start the Contexten Dashboard extension.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def main():
    """Run the dashboard"""
    try:
        from contexten.extensions.dashboard.run_dashboard import main as dashboard_main
        await dashboard_main()
    except ImportError as e:
        print(f"❌ Failed to import dashboard: {e}")
        print("💡 Make sure you're in the graph-sitter directory and dependencies are installed")
        print("💡 Try: pip install -e .")
        return 1
    except Exception as e:
        print(f"❌ Dashboard error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


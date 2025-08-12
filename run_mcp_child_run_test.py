#!/usr/bin/env python3
"""
Script to run the MCP server child run integration test.

This script sets up the environment and runs the test_child_run.py test
to verify that the MCP server can properly create and manage child runs.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Run the MCP server child run integration test."""
    # Get the root directory of the project
    root_dir = Path(__file__).parent.absolute()
    
    # Set up the Python path to include the project root
    sys.path.insert(0, str(root_dir))
    
    # Run the test
    test_path = root_dir / "tests" / "integration" / "mcp" / "test_child_run.py"
    
    print(f"Running MCP server child run integration test: {test_path}")
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "-v", str(test_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("Errors:", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
        
        print("Test completed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Test failed with exit code {e.returncode}", file=sys.stderr)
        print(e.stdout)
        print("Errors:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return e.returncode

if __name__ == "__main__":
    sys.exit(main())


#!/usr/bin/env python3
"""
MCP Bridge Usage Example

This example demonstrates how to use the Serena MCP Bridge to interact with an MCP server.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the Python path to import graph_sitter
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from graph_sitter.extensions.lsp.serena.mcp_bridge import SerenaMCPBridge


def main():
    """Main function to demonstrate MCP bridge usage."""
    # Get the repository path from command line or use current directory
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print(f"Initializing MCP bridge for repository: {repo_path}")
    
    # Initialize the MCP bridge
    bridge = SerenaMCPBridge(repo_path)
    
    try:
        # Check if the bridge is initialized
        if not bridge.is_initialized:
            print("Failed to initialize MCP bridge")
            return 1
        
        print(f"MCP bridge initialized successfully")
        
        # Get available tools
        tools = bridge.get_available_tools()
        print(f"Available tools ({len(tools)}):")
        for tool_name, tool_info in tools.items():
            print(f"  - {tool_name}: {tool_info.get('description', 'No description')}")
        
        # Check if a specific tool is available
        tool_to_check = "semantic_search" if "semantic_search" in tools else next(iter(tools.keys())) if tools else None
        
        if tool_to_check:
            print(f"\nChecking if tool '{tool_to_check}' is available: {bridge.is_tool_available(tool_to_check)}")
            
            # Call the tool
            print(f"\nCalling tool '{tool_to_check}'...")
            result = bridge.call_tool(tool_to_check, {"query": "hello world"})
            
            # Print the result
            print(f"Tool call result:")
            print(f"  Success: {result.success}")
            if result.success:
                print(f"  Content: {json.dumps(result.content, indent=2)}")
            else:
                print(f"  Error: {result.error}")
        else:
            print("\nNo tools available to call")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Shutdown the bridge
        print("\nShutting down MCP bridge...")
        bridge.shutdown()
        print("MCP bridge shutdown complete")


if __name__ == "__main__":
    sys.exit(main())


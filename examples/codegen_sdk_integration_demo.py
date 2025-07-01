#!/usr/bin/env python3
"""
Codegen SDK Integration Demo

This example demonstrates how to use the enhanced ChatAgent and CodeAgent
with Codegen SDK integration in the Contexten orchestrator.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path so we can import contexten modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph_sitter import Codebase
from contexten.agents.chat_agent import ChatAgent
from contexten.agents.code_agent import CodeAgent
from contexten.agents.codegen_config import print_codegen_status, setup_codegen_env


def demo_chat_agent():
    """Demonstrate ChatAgent with Codegen SDK integration."""
    print("\n🗣️ ChatAgent Demo")
    print("=" * 50)
    
    # Initialize codebase (you can change this to your project path)
    codebase_path = Path(__file__).parent.parent
    codebase = Codebase(codebase_path)
    
    # Create ChatAgent - it will auto-detect Codegen SDK configuration
    chat_agent = ChatAgent(codebase)
    
    # Example conversation
    prompts = [
        "What is this codebase about?",
        "Can you explain the main components of the contexten module?",
        "How does the agent orchestration work?"
    ]
    
    for prompt in prompts:
        print(f"\n👤 User: {prompt}")
        try:
            response = chat_agent.run(prompt)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")


def demo_code_agent():
    """Demonstrate CodeAgent with Codegen SDK integration."""
    print("\n💻 CodeAgent Demo")
    print("=" * 50)
    
    # Initialize codebase
    codebase_path = Path(__file__).parent.parent
    codebase = Codebase(codebase_path)
    
    # Create CodeAgent - it will auto-detect Codegen SDK configuration
    code_agent = CodeAgent(codebase)
    
    # Example coding tasks
    tasks = [
        "Analyze the structure of the contexten agents module",
        "Create a simple utility function to validate environment variables",
        "Suggest improvements to the agent configuration system"
    ]
    
    for task in tasks:
        print(f"\n👤 User: {task}")
        try:
            response = code_agent.run(task)
            print(f"🤖 Agent: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")


def demo_manual_configuration():
    """Demonstrate manual Codegen SDK configuration."""
    print("\n⚙️ Manual Configuration Demo")
    print("=" * 50)
    
    # Example of setting up Codegen SDK programmatically
    # (Replace with your actual credentials)
    org_id = "your_organization_id_here"
    token = "your_api_token_here"
    
    print("Setting up Codegen SDK configuration...")
    setup_codegen_env(org_id, token)
    
    # Now create agents that will use the SDK
    codebase_path = Path(__file__).parent.parent
    codebase = Codebase(codebase_path)
    
    # Force Codegen SDK usage
    chat_agent = ChatAgent(codebase, use_codegen_sdk=True)
    code_agent = CodeAgent(codebase, use_codegen_sdk=True)
    
    print("✅ Agents configured to use Codegen SDK")


def demo_local_only_mode():
    """Demonstrate local-only mode (no Codegen SDK)."""
    print("\n🔧 Local-Only Mode Demo")
    print("=" * 50)
    
    codebase_path = Path(__file__).parent.parent
    codebase = Codebase(codebase_path)
    
    # Force local-only mode
    chat_agent = ChatAgent(codebase, use_codegen_sdk=False)
    code_agent = CodeAgent(codebase, use_codegen_sdk=False)
    
    print("✅ Agents configured for local-only mode")
    
    # Test with a simple prompt
    response = chat_agent.run("What files are in the src/contexten/agents directory?")
    print(f"🤖 Local Agent Response: {response}")


def main():
    """Main demo function."""
    print("🚀 Contexten Codegen SDK Integration Demo")
    print("=" * 60)
    
    # Check current Codegen SDK status
    print_codegen_status()
    
    # Run demos based on available configuration
    if len(sys.argv) > 1:
        demo_type = sys.argv[1].lower()
        
        if demo_type == "chat":
            demo_chat_agent()
        elif demo_type == "code":
            demo_code_agent()
        elif demo_type == "manual":
            demo_manual_configuration()
        elif demo_type == "local":
            demo_local_only_mode()
        else:
            print(f"Unknown demo type: {demo_type}")
            print("Available demos: chat, code, manual, local")
    else:
        print("\n📋 Available Demos:")
        print("  python examples/codegen_sdk_integration_demo.py chat    # ChatAgent demo")
        print("  python examples/codegen_sdk_integration_demo.py code    # CodeAgent demo")
        print("  python examples/codegen_sdk_integration_demo.py manual  # Manual config demo")
        print("  python examples/codegen_sdk_integration_demo.py local   # Local-only demo")
        
        # Run local demo by default
        demo_local_only_mode()


if __name__ == "__main__":
    main()


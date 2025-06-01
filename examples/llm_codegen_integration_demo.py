"""
LLM Codegen SDK Integration Demo

Demonstrates how to configure and use Codegen SDK as a selectable
and default model for program-wide agentic calls.
"""

import os
import asyncio
from contexten.extensions.langchain.llm import LLM
from contexten.extensions.langchain.llm_config import (
    configure_codegen_default, 
    get_llm_config,
    create_llm_with_config
)
from contexten.extensions.langchain.llm_tools import (
    set_codegen_as_default_llm,
    set_llm_provider,
    get_llm_status,
    configure_llm_provider,
    get_llm_configuration_tools
)


def demo_basic_llm_usage():
    """Demonstrate basic LLM usage with different providers"""
    print("🤖 Basic LLM Usage Demo")
    print("=" * 40)
    
    # Method 1: Direct instantiation with specific provider
    print("\n1. Direct instantiation:")
    
    # OpenAI
    try:
        llm_openai = LLM(model_provider="openai", model_name="gpt-4")
        print(f"✅ OpenAI LLM created: {llm_openai.model_name}")
    except Exception as e:
        print(f"❌ OpenAI LLM failed: {e}")
    
    # Anthropic
    try:
        llm_anthropic = LLM(model_provider="anthropic", model_name="claude-3-5-sonnet-latest")
        print(f"✅ Anthropic LLM created: {llm_anthropic.model_name}")
    except Exception as e:
        print(f"❌ Anthropic LLM failed: {e}")
    
    # Codegen SDK (if credentials are available)
    try:
        org_id = os.getenv("CODEGEN_ORG_ID", "your-org-id")
        token = os.getenv("CODEGEN_TOKEN", "your-token")
        
        llm_codegen = LLM.with_codegen(
            org_id=org_id,
            token=token,
            model="codegen-agent"
        )
        print(f"✅ Codegen LLM created: {llm_codegen.model_name}")
    except Exception as e:
        print(f"❌ Codegen LLM failed: {e}")


def demo_configuration_system():
    """Demonstrate the configuration system"""
    print("\n🔧 Configuration System Demo")
    print("=" * 40)
    
    # Get current configuration
    config = get_llm_config()
    print(f"Current default provider: {config.default_provider}")
    print(f"Current default model: {config.default_model}")
    print(f"Available providers: {config.get_available_providers()}")
    
    # Method 2: Using global configuration
    print("\n2. Using global configuration:")
    try:
        llm_from_config = LLM.from_config()
        print(f"✅ LLM from config: {llm_from_config.model_provider} - {llm_from_config.model_name}")
    except Exception as e:
        print(f"❌ LLM from config failed: {e}")
    
    # Method 3: Configure Codegen as default
    print("\n3. Setting Codegen as default:")
    org_id = os.getenv("CODEGEN_ORG_ID")
    token = os.getenv("CODEGEN_TOKEN")
    
    if org_id and token:
        try:
            configure_codegen_default(org_id, token, "codegen-agent")
            print("✅ Codegen configured as default")
            
            # Now create LLM using the new default
            llm_default = LLM.from_config()
            print(f"✅ Default LLM now uses: {llm_default.model_provider}")
        except Exception as e:
            print(f"❌ Failed to configure Codegen: {e}")
    else:
        print("❌ CODEGEN_ORG_ID and CODEGEN_TOKEN not set in environment")


def demo_agent_function_calls():
    """Demonstrate agent function call interface"""
    print("\n🛠️ Agent Function Call Interface Demo")
    print("=" * 40)
    
    # Simulate agent function calls
    print("\n1. Get current LLM status:")
    status = configure_llm_provider("get_status")
    print(status)
    
    print("\n2. Set provider to OpenAI:")
    result = configure_llm_provider(
        action="set_provider",
        provider="openai",
        model="gpt-4",
        temperature=0.1
    )
    print(result)
    
    print("\n3. Set Codegen as default (if credentials available):")
    org_id = os.getenv("CODEGEN_ORG_ID")
    token = os.getenv("CODEGEN_TOKEN")
    
    if org_id and token:
        result = configure_llm_provider(
            action="set_codegen_default",
            org_id=org_id,
            token=token,
            model="codegen-agent"
        )
        print(result)
    else:
        print("❌ Codegen credentials not available")
    
    print("\n4. Final status:")
    final_status = configure_llm_provider("get_status")
    print(final_status)


def demo_langchain_tools():
    """Demonstrate LangChain tools for agent integration"""
    print("\n🔗 LangChain Tools Demo")
    print("=" * 40)
    
    # Get the tools
    tools = get_llm_configuration_tools()
    
    print(f"Available tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description}")
    
    # Demonstrate tool usage
    print("\n1. Using SetCodegenDefaultTool:")
    org_id = os.getenv("CODEGEN_ORG_ID", "demo-org-id")
    token = os.getenv("CODEGEN_TOKEN", "demo-token")
    
    from contexten.extensions.langchain.llm_tools import SetCodegenDefaultTool
    
    codegen_tool = SetCodegenDefaultTool()
    try:
        result = codegen_tool._run(org_id, token, "codegen-agent")
        print(result)
    except Exception as e:
        print(f"❌ Tool execution failed: {e}")
    
    print("\n2. Using GetLLMStatusTool:")
    from contexten.extensions.langchain.llm_tools import GetLLMStatusTool
    
    status_tool = GetLLMStatusTool()
    status_result = status_tool._run()
    print(status_result)


async def demo_actual_llm_calls():
    """Demonstrate actual LLM calls with different providers"""
    print("\n💬 Actual LLM Calls Demo")
    print("=" * 40)
    
    test_prompt = "Hello! Please respond with a brief greeting."
    
    # Test with different providers
    providers_to_test = ["anthropic", "openai", "codegen"]
    
    for provider in providers_to_test:
        print(f"\n🧪 Testing {provider}:")
        
        try:
            config = get_llm_config()
            if not config.is_provider_available(provider):
                print(f"❌ {provider} not available (missing credentials)")
                continue
            
            # Create LLM for this provider
            if provider == "codegen":
                org_id = os.getenv("CODEGEN_ORG_ID")
                token = os.getenv("CODEGEN_TOKEN")
                llm = LLM.with_codegen(org_id, token)
            else:
                llm = LLM(model_provider=provider)
            
            # Make a test call
            from langchain_core.messages import HumanMessage
            
            messages = [HumanMessage(content=test_prompt)]
            response = llm._generate(messages)
            
            print(f"✅ {provider} response: {response.generations[0].message.content[:100]}...")
            
        except Exception as e:
            print(f"❌ {provider} failed: {e}")


def demo_environment_configuration():
    """Demonstrate environment-based configuration"""
    print("\n🌍 Environment Configuration Demo")
    print("=" * 40)
    
    print("Environment variables for LLM configuration:")
    env_vars = [
        "LLM_DEFAULT_PROVIDER",
        "LLM_DEFAULT_MODEL", 
        "LLM_TEMPERATURE",
        "LLM_MAX_TOKENS",
        "CODEGEN_ORG_ID",
        "CODEGEN_TOKEN",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "XAI_API_KEY"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "token" in var.lower() or "key" in var.lower():
                display_value = value[:8] + "..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: Not set")
    
    print("\nTo configure Codegen as default via environment:")
    print("export LLM_DEFAULT_PROVIDER=codegen")
    print("export CODEGEN_ORG_ID=your-org-id")
    print("export CODEGEN_TOKEN=your-token")


def demo_config_file():
    """Demonstrate configuration file usage"""
    print("\n📄 Configuration File Demo")
    print("=" * 40)
    
    # Show example configuration file
    example_config = {
        "default_provider": "codegen",
        "default_model": "codegen-agent",
        "temperature": 0.1,
        "max_tokens": 4000,
        "timeout": 300,
        "codegen": {
            "model": "codegen-agent",
            "temperature": 0.1
        },
        "anthropic": {
            "model": "claude-3-5-sonnet-latest",
            "temperature": 0.0
        },
        "openai": {
            "model": "gpt-4",
            "temperature": 0.1
        }
    }
    
    print("Example llm_config.json:")
    import json
    print(json.dumps(example_config, indent=2))
    
    print("\nConfiguration file locations (in order of precedence):")
    print("1. ./llm_config.json (current directory)")
    print("2. ~/.contexten/llm_config.json (user home)")
    print("3. /etc/contexten/llm_config.json (system-wide)")
    
    # Try to save current config
    try:
        config = get_llm_config()
        config.save_to_file()
        print("\n✅ Current configuration saved to ~/.contexten/llm_config.json")
    except Exception as e:
        print(f"\n❌ Failed to save configuration: {e}")


if __name__ == "__main__":
    print("🚀 LLM Codegen SDK Integration Demo")
    print("=" * 50)
    
    # Run all demos
    demo_basic_llm_usage()
    demo_configuration_system()
    demo_agent_function_calls()
    demo_langchain_tools()
    demo_environment_configuration()
    demo_config_file()
    
    # Run async demo
    print("\n⚡ Running async LLM calls demo...")
    asyncio.run(demo_actual_llm_calls())
    
    print("\n✅ Demo completed!")
    print("\nNext steps:")
    print("1. Set your Codegen SDK credentials (CODEGEN_ORG_ID, CODEGEN_TOKEN)")
    print("2. Configure Codegen as default: configure_codegen_default(org_id, token)")
    print("3. Use LLM.from_config() to create LLM instances with global settings")
    print("4. Integrate LLM configuration tools into your agents")
    print("5. Use environment variables or config files for persistent settings")


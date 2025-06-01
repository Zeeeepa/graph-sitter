"""

from typing import Any, Dict, List, Optional

from .llm_config import get_llm_config, configure_codegen_default, create_llm_with_config
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

LLM Configuration Tools

Provides function/tool interfaces for agents to configure LLM providers,
including setting Codegen SDK as the default provider.
"""

# Handle LangChain dependencies with graceful fallback
try:
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # Create mock classes for when LangChain is not available
    LANGCHAIN_AVAILABLE = False
    
    class BaseTool:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def _run(self, *args, **kwargs):
            return "Tool execution not available without LangChain"
    
    class BaseModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    def Field(**kwargs):
        return None

class SetCodegenDefaultInput(BaseModel):
    """Input for setting Codegen SDK as default provider"""
    org_id: str = Field(description="Codegen organization ID")
    token: str = Field(description="Codegen API token")
    model: str = Field(default="codegen-agent", description="Model name to use")

class SetLLMProviderInput(BaseModel):
    """Input for setting LLM provider"""
    provider: str = Field(description="Provider name (anthropic, openai, xai, codegen)")
    model: Optional[str] = Field(default=None, description="Model name to use")
    temperature: Optional[float] = Field(default=None, description="Temperature setting")
    max_tokens: Optional[int] = Field(default=None, description="Maximum tokens")

class GetLLMStatusInput(BaseModel):
    """Input for getting LLM status (no parameters needed)"""
    pass

class SetCodegenDefaultTool(BaseTool):
    """Tool for setting Codegen SDK as the default LLM provider"""
    
    name: str = "set_codegen_default"
    description: str = """Set Codegen SDK as the default LLM provider program-wide.
    This configures the system to use Codegen SDK for all subsequent LLM operations.
    Requires organization ID and API token."""
    
    args_schema = SetCodegenDefaultInput
    
    def _run(self, org_id: str, token: str, model: str = "codegen-agent") -> str:
        """Set Codegen SDK as default provider"""
        try:
            config = configure_codegen_default(org_id, token, model)
            
            # Verify the configuration works
            test_llm = create_llm_with_config()
            
            return f"""✅ Successfully configured Codegen SDK as default LLM provider!

Configuration:
- Provider: codegen
- Model: {model}
- Organization ID: {org_id[:8]}...
- Status: Ready

The system will now use Codegen SDK for all LLM operations by default.
You can override this on a per-call basis if needed."""
            
        except Exception as e:
            return f"❌ Failed to configure Codegen SDK: {str(e)}"

class SetLLMProviderTool(BaseTool):
    """Tool for setting the default LLM provider"""
    
    name: str = "set_llm_provider"
    description: str = """Set the default LLM provider and configuration.
    Supports anthropic, openai, xai, and codegen providers."""
    
    args_schema = SetLLMProviderInput
    
    def _run(
        self, 
        provider: str, 
        model: Optional[str] = None, 
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Set LLM provider configuration"""
        try:
            config = get_llm_config()
            
            # Validate provider
            valid_providers = ["anthropic", "openai", "xai", "codegen"]
            if provider not in valid_providers:
                return f"❌ Invalid provider '{provider}'. Must be one of: {', '.join(valid_providers)}"
            
            # Check if provider is available
            if not config.is_provider_available(provider):
                missing_creds = {
                    "anthropic": "ANTHROPIC_API_KEY",
                    "openai": "OPENAI_API_KEY", 
                    "xai": "XAI_API_KEY",
                    "codegen": "CODEGEN_ORG_ID and CODEGEN_TOKEN"
                }
                return f"❌ Provider '{provider}' is not available. Missing: {missing_creds.get(provider, 'credentials')}"
            
            # Update configuration
            config.default_provider = provider
            if model:
                config.default_model = model
            if temperature is not None:
                config.temperature = temperature
            if max_tokens is not None:
                config.max_tokens = max_tokens
            
            # Test the configuration
            test_llm = create_llm_with_config()
            
            return f"""✅ Successfully configured LLM provider!

Configuration:
- Provider: {provider}
- Model: {model or config.default_model}
- Temperature: {temperature or config.temperature}
- Max Tokens: {max_tokens or config.max_tokens or 'default'}
- Status: Ready

The system will now use {provider} for LLM operations by default."""
            
        except Exception as e:
            return f"❌ Failed to configure LLM provider: {str(e)}"

class GetLLMStatusTool(BaseTool):
    """Tool for getting current LLM configuration status"""
    
    name: str = "get_llm_status"
    description: str = """Get the current LLM configuration and available providers.
    Shows which providers are configured and available."""
    
    args_schema = GetLLMStatusInput
    
    def _run(self) -> str:
        """Get LLM status and configuration"""
        try:
            config = get_llm_config()
            available_providers = config.get_available_providers()
            
            status_lines = [
                "🤖 LLM Configuration Status",
                "=" * 30,
                f"Default Provider: {config.default_provider}",
                f"Default Model: {config.default_model}",
                f"Temperature: {config.temperature}",
                f"Max Tokens: {config.max_tokens or 'default'}",
                "",
                "Available Providers:"
            ]
            
            for provider in ["anthropic", "openai", "xai", "codegen"]:
                status = "✅" if provider in available_providers else "❌"
                status_lines.append(f"  {status} {provider}")
                
                if provider == "codegen" and provider in available_providers:
                    org_id = config.codegen_org_id
                    if org_id:
                        status_lines.append(f"    Org ID: {org_id[:8]}...")
            
            if not available_providers:
                status_lines.extend([
                    "",
                    "⚠️  No providers are currently available!",
                    "Please configure at least one provider with appropriate credentials."
                ])
            
            return "\n".join(status_lines)
            
        except Exception as e:
            return f"❌ Failed to get LLM status: {str(e)}"

# Convenience functions for direct use
def set_codegen_as_default_llm(org_id: str, token: str, model: str = "codegen-agent") -> str:
    """Convenience function to set Codegen SDK as default LLM"""
    tool = SetCodegenDefaultTool()
    return tool._run(org_id, token, model)

def set_llm_provider(
    provider: str, 
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """Convenience function to set LLM provider"""
    tool = SetLLMProviderTool()
    return tool._run(provider, model, temperature, max_tokens)

def get_llm_status() -> str:
    """Convenience function to get LLM status"""
    tool = GetLLMStatusTool()
    return tool._run()

# Function definitions for agent prompt function calls
def configure_llm_provider(
    action: str,
    provider: Optional[str] = None,
    org_id: Optional[str] = None,
    token: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
) -> str:
    """
    Universal LLM configuration function for agent prompt function calls.
    
    Args:
        action: Action to perform ("set_codegen_default", "set_provider", "get_status")
        provider: LLM provider name (anthropic, openai, xai, codegen)
        org_id: Codegen organization ID (required for codegen provider)
        token: Codegen API token (required for codegen provider)
        model: Model name to use
        temperature: Temperature setting (0-1)
        max_tokens: Maximum tokens to generate
    
    Returns:
        Status message indicating success or failure
    """
    
    if action == "set_codegen_default":
        if not org_id or not token:
            return "❌ org_id and token are required for setting Codegen as default"
        return set_codegen_as_default_llm(org_id, token, model or "codegen-agent")
    
    elif action == "set_provider":
        if not provider:
            return "❌ provider is required for set_provider action"
        return set_llm_provider(provider, model, temperature, max_tokens)
    
    elif action == "get_status":
        return get_llm_status()
    
    else:
        return f"❌ Unknown action '{action}'. Valid actions: set_codegen_default, set_provider, get_status"

# Export tools for LangChain agent use
def get_llm_configuration_tools() -> List[BaseTool]:
    """Get all LLM configuration tools for use in LangChain agents"""
    return [
        SetCodegenDefaultTool(),
        SetLLMProviderTool(),
        GetLLMStatusTool()
    ]

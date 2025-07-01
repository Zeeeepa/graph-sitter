"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional
import json
import os

LLM Configuration Manager

Provides program-wide configuration for LLM providers, including
the ability to set Codegen SDK as the default provider.
"""

@dataclass
class LLMConfig:
    """Configuration for LLM providers"""
    
    # Default provider selection
    default_provider: str = "anthropic"
    default_model: str = "claude-3-5-sonnet-latest"
    
    # Provider-specific configurations
    anthropic_config: Dict[str, Any] = field(default_factory=dict)
    openai_config: Dict[str, Any] = field(default_factory=dict)
    xai_config: Dict[str, Any] = field(default_factory=dict)
    codegen_config: Dict[str, Any] = field(default_factory=dict)
    
    # Global settings
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    timeout: int = 300
    
    # Codegen SDK specific
    codegen_org_id: Optional[str] = None
    codegen_token: Optional[str] = None
    
    def __post_init__(self):
        """Load configuration from environment and config files"""
        self._load_from_env()
        self._load_from_config_file()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Default provider
        if env_provider := os.getenv("LLM_DEFAULT_PROVIDER"):
            self.default_provider = env_provider
        
        if env_model := os.getenv("LLM_DEFAULT_MODEL"):
            self.default_model = env_model
        
        # Global settings
        if env_temp := os.getenv("LLM_TEMPERATURE"):
            try:
                self.temperature = float(env_temp)
            except ValueError:
                pass
        
        if env_tokens := os.getenv("LLM_MAX_TOKENS"):
            try:
                self.max_tokens = int(env_tokens)
            except ValueError:
                pass
        
        # Codegen SDK credentials
        if env_org_id := os.getenv("CODEGEN_ORG_ID"):
            self.codegen_org_id = env_org_id
            self.codegen_config["org_id"] = env_org_id
        
        if env_token := os.getenv("CODEGEN_TOKEN"):
            self.codegen_token = env_token
            self.codegen_config["token"] = env_token
    
    def _load_from_config_file(self):
        """Load configuration from config file"""
        config_paths = [
            Path.cwd() / "llm_config.json",
            Path.home() / ".contexten" / "llm_config.json",
            Path("/etc/contexten/llm_config.json")
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config_data = json.load(f)
                    self._apply_config_data(config_data)
                    break
                except (json.JSONDecodeError, IOError):
                    continue
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data from file"""
        if "default_provider" in config_data:
            self.default_provider = config_data["default_provider"]
        
        if "default_model" in config_data:
            self.default_model = config_data["default_model"]
        
        if "temperature" in config_data:
            self.temperature = config_data["temperature"]
        
        if "max_tokens" in config_data:
            self.max_tokens = config_data["max_tokens"]
        
        if "timeout" in config_data:
            self.timeout = config_data["timeout"]
        
        # Provider-specific configs
        for provider in ["anthropic", "openai", "xai", "codegen"]:
            if provider in config_data:
                setattr(self, f"{provider}_config", config_data[provider])
        
        # Codegen SDK specific
        if "codegen_org_id" in config_data:
            self.codegen_org_id = config_data["codegen_org_id"]
        
        if "codegen_token" in config_data:
            self.codegen_token = config_data["codegen_token"]
    
    def set_codegen_as_default(self, org_id: str, token: str, model: str = "codegen-agent"):
        """Set Codegen SDK as the default provider"""
        self.default_provider = "codegen"
        self.default_model = model
        self.codegen_org_id = org_id
        self.codegen_token = token
        self.codegen_config.update({
            "org_id": org_id,
            "token": token,
            "model": model
        })
    
    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific provider"""
        base_config = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout
        }
        
        provider_config = getattr(self, f"{provider}_config", {})
        
        # Add Codegen SDK credentials if needed
        if provider == "codegen":
            if self.codegen_org_id:
                provider_config["org_id"] = self.codegen_org_id
            if self.codegen_token:
                provider_config["token"] = self.codegen_token
        
        return {**base_config, **provider_config}
    
    def save_to_file(self, config_path: Optional[Path] = None):
        """Save current configuration to file"""
        if config_path is None:
            config_dir = Path.home() / ".contexten"
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / "llm_config.json"
        
        config_data = {
            "default_provider": self.default_provider,
            "default_model": self.default_model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "anthropic": self.anthropic_config,
            "openai": self.openai_config,
            "xai": self.xai_config,
            "codegen": self.codegen_config,
        }
        
        # Only save non-sensitive config data
        if self.codegen_org_id and not self.codegen_config.get("save_credentials", False):
            config_data["codegen_org_id"] = self.codegen_org_id
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def is_provider_available(self, provider: str) -> bool:
        """Check if a provider is available (has required credentials)"""
        if provider == "anthropic":
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        elif provider == "openai":
            return bool(os.getenv("OPENAI_API_KEY"))
        elif provider == "xai":
            return bool(os.getenv("XAI_API_KEY"))
        elif provider == "codegen":
            return bool(
                (self.codegen_org_id or os.getenv("CODEGEN_ORG_ID")) and
                (self.codegen_token or os.getenv("CODEGEN_TOKEN"))
            )
        return False
    
    def get_available_providers(self) -> list[str]:
        """Get list of available providers"""
        providers = ["anthropic", "openai", "xai", "codegen"]
        return [p for p in providers if self.is_provider_available(p)]
    
    def auto_select_provider(self) -> str:
        """Automatically select the best available provider"""
        # First try the configured default
        if self.is_provider_available(self.default_provider):
            return self.default_provider
        
        # Fallback order: codegen -> anthropic -> openai -> xai
        fallback_order = ["codegen", "anthropic", "openai", "xai"]
        for provider in fallback_order:
            if self.is_provider_available(provider):
                return provider
        
        raise ValueError("No LLM providers are available. Please configure at least one provider.")

# Global configuration instance
_global_config: Optional[LLMConfig] = None

def get_llm_config() -> LLMConfig:
    """Get the global LLM configuration"""
    global _global_config
    if _global_config is None:
        _global_config = LLMConfig()
    return _global_config

def set_llm_config(config: LLMConfig):
    """Set the global LLM configuration"""
    global _global_config
    _global_config = config

def configure_codegen_default(org_id: str, token: str, model: str = "codegen-agent"):
    """Configure Codegen SDK as the default provider program-wide"""
    config = get_llm_config()
    config.set_codegen_as_default(org_id, token, model)
    return config

def create_llm_with_config(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> "LLM":
    """Create an LLM instance using global configuration"""
    from .llm import LLM
    
    config = get_llm_config()
    
    # Use provided values or fall back to config
    provider = provider or config.auto_select_provider()
    model = model or config.default_model
    
    # Get provider-specific configuration
    provider_config = config.get_provider_config(provider)
    
    # Merge with any provided kwargs
    final_kwargs = {**provider_config, **kwargs}
    
    return LLM(
        model_provider=provider,
        model_name=model,
        **final_kwargs
    )

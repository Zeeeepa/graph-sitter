"""Configuration management for AutoGenLib integration."""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class AutoGenLibConfig:
    """Configuration for AutoGenLib integration."""
    
    # Basic settings
    description: str = "Dynamic code generation library"
    enable_caching: bool = False
    enable_exception_handler: bool = True
    cache_dir: Optional[str] = None
    
    # Codegen SDK settings
    codegen_org_id: Optional[str] = None
    codegen_token: Optional[str] = None
    codegen_base_url: Optional[str] = None
    
    # Claude API settings
    claude_api_key: Optional[str] = None
    claude_model: str = "claude-3-5-sonnet-20241022"
    
    # OpenAI settings (for backward compatibility)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_base_url: Optional[str] = None
    
    # Provider preferences
    provider_order: list[str] = field(default_factory=lambda: ["codegen", "claude", "openai"])
    
    # Context settings
    max_context_functions: int = 10
    max_context_dependencies: int = 15
    max_context_usages: int = 8
    max_source_length: int = 1000
    
    # Generation settings
    generation_timeout: int = 30
    max_retries: int = 3
    temperature: float = 0.1
    
    @classmethod
    def from_environment(cls) -> "AutoGenLibConfig":
        """Create configuration from environment variables."""
        return cls(
            # Basic settings
            description=os.environ.get("AUTOGENLIB_DESCRIPTION", "Dynamic code generation library"),
            enable_caching=os.environ.get("AUTOGENLIB_ENABLE_CACHING", "false").lower() == "true",
            enable_exception_handler=os.environ.get("AUTOGENLIB_ENABLE_EXCEPTION_HANDLER", "true").lower() == "true",
            cache_dir=os.environ.get("AUTOGENLIB_CACHE_DIR"),
            
            # Codegen SDK
            codegen_org_id=os.environ.get("CODEGEN_ORG_ID"),
            codegen_token=os.environ.get("CODEGEN_TOKEN") or os.environ.get("CODEGEN_API_TOKEN"),
            codegen_base_url=os.environ.get("CODEGEN_BASE_URL"),
            
            # Claude API
            claude_api_key=os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY"),
            claude_model=os.environ.get("CLAUDE_MODEL", "claude-3-5-sonnet-20241022"),
            
            # OpenAI (backward compatibility)
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            openai_model=os.environ.get("OPENAI_MODEL", "gpt-4"),
            openai_base_url=os.environ.get("OPENAI_BASE_URL"),
            
            # Provider order
            provider_order=os.environ.get("AUTOGENLIB_PROVIDER_ORDER", "codegen,claude,openai").split(","),
            
            # Context settings
            max_context_functions=int(os.environ.get("AUTOGENLIB_MAX_CONTEXT_FUNCTIONS", "10")),
            max_context_dependencies=int(os.environ.get("AUTOGENLIB_MAX_CONTEXT_DEPENDENCIES", "15")),
            max_context_usages=int(os.environ.get("AUTOGENLIB_MAX_CONTEXT_USAGES", "8")),
            max_source_length=int(os.environ.get("AUTOGENLIB_MAX_SOURCE_LENGTH", "1000")),
            
            # Generation settings
            generation_timeout=int(os.environ.get("AUTOGENLIB_GENERATION_TIMEOUT", "30")),
            max_retries=int(os.environ.get("AUTOGENLIB_MAX_RETRIES", "3")),
            temperature=float(os.environ.get("AUTOGENLIB_TEMPERATURE", "0.1"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "description": self.description,
            "enable_caching": self.enable_caching,
            "enable_exception_handler": self.enable_exception_handler,
            "cache_dir": self.cache_dir,
            "codegen_org_id": self.codegen_org_id,
            "codegen_token": "***" if self.codegen_token else None,
            "codegen_base_url": self.codegen_base_url,
            "claude_api_key": "***" if self.claude_api_key else None,
            "claude_model": self.claude_model,
            "openai_api_key": "***" if self.openai_api_key else None,
            "openai_model": self.openai_model,
            "openai_base_url": self.openai_base_url,
            "provider_order": self.provider_order,
            "max_context_functions": self.max_context_functions,
            "max_context_dependencies": self.max_context_dependencies,
            "max_context_usages": self.max_context_usages,
            "max_source_length": self.max_source_length,
            "generation_timeout": self.generation_timeout,
            "max_retries": self.max_retries,
            "temperature": self.temperature
        }
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        # Check if at least one provider is configured
        has_provider = False
        
        if self.codegen_org_id and self.codegen_token:
            has_provider = True
        
        if self.claude_api_key:
            has_provider = True
        
        if self.openai_api_key:
            has_provider = True
        
        if not has_provider:
            issues.append("No AI providers configured. Set CODEGEN_ORG_ID+CODEGEN_TOKEN, CLAUDE_API_KEY, or OPENAI_API_KEY")
        
        # Validate numeric settings
        if self.generation_timeout <= 0:
            issues.append("generation_timeout must be positive")
        
        if self.max_retries < 0:
            issues.append("max_retries must be non-negative")
        
        if not 0 <= self.temperature <= 2:
            issues.append("temperature must be between 0 and 2")
        
        # Validate provider order
        valid_providers = {"codegen", "claude", "openai"}
        for provider in self.provider_order:
            if provider not in valid_providers:
                issues.append(f"Invalid provider in order: {provider}. Valid: {valid_providers}")
        
        return issues
    
    def get_available_providers(self) -> list[str]:
        """Get list of available providers based on configuration."""
        available = []
        
        if self.codegen_org_id and self.codegen_token:
            available.append("codegen")
        
        if self.claude_api_key:
            available.append("claude")
        
        if self.openai_api_key:
            available.append("openai")
        
        return available
    
    def log_configuration(self):
        """Log the current configuration (without sensitive data)."""
        config_dict = self.to_dict()
        available_providers = self.get_available_providers()
        
        logger.info("AutoGenLib Configuration:")
        logger.info(f"  Description: {config_dict['description']}")
        logger.info(f"  Caching: {config_dict['enable_caching']}")
        logger.info(f"  Exception Handler: {config_dict['enable_exception_handler']}")
        logger.info(f"  Available Providers: {available_providers}")
        logger.info(f"  Provider Order: {config_dict['provider_order']}")
        logger.info(f"  Generation Timeout: {config_dict['generation_timeout']}s")
        logger.info(f"  Max Context Functions: {config_dict['max_context_functions']}")
        
        # Validate and log any issues
        issues = self.validate()
        if issues:
            logger.warning("Configuration issues:")
            for issue in issues:
                logger.warning(f"  - {issue}")


def load_config() -> AutoGenLibConfig:
    """Load configuration from environment variables."""
    config = AutoGenLibConfig.from_environment()
    config.log_configuration()
    return config


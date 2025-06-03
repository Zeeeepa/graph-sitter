"""
Integration configuration for external services and APIs.
"""

from typing import Optional
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class IntegrationsConfig(BaseSettings):
    """Configuration for external integrations."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # GitHub integration
    github_token: Optional[SecretStr] = Field(
        default=None,
        description="GitHub access token"
    )
    github_webhook_secret: Optional[SecretStr] = Field(
        default=None,
        description="GitHub webhook secret"
    )
    
    # Linear integration
    linear_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Linear API key"
    )
    linear_webhook_secret: Optional[SecretStr] = Field(
        default=None,
        description="Linear webhook secret"
    )
    
    # Slack integration
    slack_bot_token: Optional[SecretStr] = Field(
        default=None,
        description="Slack bot token"
    )
    slack_signing_secret: Optional[SecretStr] = Field(
        default=None,
        description="Slack signing secret"
    )
    
    # OpenAI integration
    openai_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenAI API key"
    )
    openai_organization: Optional[str] = Field(
        default=None,
        description="OpenAI organization ID"
    )
    
    # Codegen SDK integration
    codegen_org_id: Optional[str] = Field(
        default=None,
        description="Codegen organization ID"
    )
    codegen_api_token: Optional[SecretStr] = Field(
        default=None,
        description="Codegen API token"
    )
    
    # Autogenlib integration settings
    autogenlib_enabled: bool = Field(
        default=False,
        description="Enable autogenlib integration"
    )
    autogenlib_api_url: Optional[str] = Field(
        default=None,
        description="Autogenlib API URL"
    )
    autogenlib_api_key: Optional[SecretStr] = Field(
        default=None,
        description="Autogenlib API key"
    )
    
    # OpenEvolve integration settings
    openevolve_enabled: bool = Field(
        default=False,
        description="Enable OpenEvolve continuous learning"
    )
    openevolve_api_url: Optional[str] = Field(
        default=None,
        description="OpenEvolve API URL"
    )
    openevolve_api_key: Optional[SecretStr] = Field(
        default=None,
        description="OpenEvolve API key"
    )
    
    # Integration timeouts and retries
    api_timeout_seconds: int = Field(
        default=30,
        description="Default API timeout in seconds"
    )
    api_retry_attempts: int = Field(
        default=3,
        description="Number of API retry attempts"
    )
    api_retry_delay_seconds: float = Field(
        default=1.0,
        description="Delay between API retries in seconds"
    )


# Global integrations config instance
_integrations_config: Optional[IntegrationsConfig] = None


def get_integrations_config() -> IntegrationsConfig:
    """Get the global integrations configuration instance."""
    global _integrations_config
    if _integrations_config is None:
        _integrations_config = IntegrationsConfig()
    return _integrations_config


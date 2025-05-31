"""Configuration management for the dashboard."""

import os
from typing import Dict, Optional
from pydantic import BaseModel, Field


class DashboardConfig(BaseModel):
    """Dashboard configuration model."""
    
    # API Keys
    github_token: Optional[str] = Field(default=None, description="GitHub access token")
    linear_token: Optional[str] = Field(default=None, description="Linear access token")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    codegen_api_key: Optional[str] = Field(default=None, description="Codegen API key")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Database Configuration
    database_url: Optional[str] = Field(default=None, description="Database connection URL")
    
    # Cache Configuration
    cache_ttl_default: int = Field(default=300, description="Default cache TTL in seconds")
    cache_ttl_projects: int = Field(default=300, description="Projects cache TTL")
    cache_ttl_requirements: int = Field(default=300, description="Requirements cache TTL")
    
    # GitHub Configuration
    github_organization: Optional[str] = Field(default=None, description="GitHub organization")
    github_include_forks: bool = Field(default=False, description="Include forked repositories")
    github_include_archived: bool = Field(default=False, description="Include archived repositories")
    
    # Linear Configuration
    linear_team_id: Optional[str] = Field(default=None, description="Default Linear team ID")
    
    # Webhook Configuration
    webhook_secret: Optional[str] = Field(default=None, description="Webhook secret for verification")
    webhook_base_url: str = Field(default="http://localhost:8000", description="Base URL for webhooks")
    
    # Chat Configuration
    chat_model: str = Field(default="claude-3-sonnet-20240229", description="Anthropic model to use")
    chat_max_tokens: int = Field(default=4000, description="Maximum tokens for chat responses")
    
    # Feature Flags
    enable_requirements_management: bool = Field(default=True, description="Enable requirements management")
    enable_webhook_integration: bool = Field(default=True, description="Enable webhook integration")
    enable_chat_interface: bool = Field(default=True, description="Enable chat interface")
    enable_code_analysis: bool = Field(default=True, description="Enable code analysis")
    
    # UI Configuration
    projects_per_page: int = Field(default=20, description="Projects per page in UI")
    max_pinned_projects: int = Field(default=10, description="Maximum pinned projects")
    
    class Config:
        """Pydantic configuration."""
        env_prefix = "DASHBOARD_"
        case_sensitive = False
    
    @classmethod
    def from_env(cls) -> "DashboardConfig":
        """Create configuration from environment variables.
        
        Returns:
            Dashboard configuration
        """
        return cls(
            github_token=os.getenv("GITHUB_ACCESS_TOKEN"),
            linear_token=os.getenv("LINEAR_ACCESS_TOKEN"),
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            codegen_api_key=os.getenv("CODEGEN_API_KEY"),
            host=os.getenv("DASHBOARD_HOST", "0.0.0.0"),
            port=int(os.getenv("DASHBOARD_PORT", "8000")),
            debug=os.getenv("DASHBOARD_DEBUG", "false").lower() == "true",
            database_url=os.getenv("DATABASE_URL"),
            github_organization=os.getenv("GITHUB_ORGANIZATION"),
            linear_team_id=os.getenv("LINEAR_TEAM_ID"),
            webhook_secret=os.getenv("WEBHOOK_SECRET"),
            webhook_base_url=os.getenv("WEBHOOK_BASE_URL", "http://localhost:8000"),
        )
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return self.dict()
    
    def validate_required_keys(self) -> Dict[str, bool]:
        """Validate that required API keys are present.
        
        Returns:
            Dictionary with validation results
        """
        return {
            "github_token": self.github_token is not None,
            "linear_token": self.linear_token is not None,
            "anthropic_api_key": self.anthropic_api_key is not None,
        }
    
    def get_missing_keys(self) -> list[str]:
        """Get list of missing required API keys.
        
        Returns:
            List of missing key names
        """
        validation = self.validate_required_keys()
        return [key for key, valid in validation.items() if not valid]


"""
Configuration management for the Codegen SDK.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path


class Config:
    """Configuration manager for the Codegen SDK."""
    
    def __init__(self):
        """Initialize configuration with environment variables and defaults."""
        self.org_id = os.getenv("CODEGEN_ORG_ID")
        self.token = os.getenv("CODEGEN_TOKEN")
        self.base_url = os.getenv("CODEGEN_BASE_URL", "https://api.codegen.com")
        self.timeout = int(os.getenv("CODEGEN_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("CODEGEN_MAX_RETRIES", "3"))
        self.debug = os.getenv("CODEGEN_DEBUG", "false").lower() == "true"
    
    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Config instance
        """
        config = cls()
        config_file = Path(config_path)
        
        if config_file.exists():
            # Support for .env files
            if config_path.endswith('.env'):
                config._load_env_file(config_file)
            # Support for JSON files
            elif config_path.endswith('.json'):
                import json
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    config._load_from_dict(data)
        
        return config
    
    def _load_env_file(self, env_file: Path) -> None:
        """Load configuration from a .env file."""
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        
        # Reload from environment
        self.__init__()
    
    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        """Load configuration from a dictionary."""
        self.org_id = data.get("org_id", self.org_id)
        self.token = data.get("token", self.token)
        self.base_url = data.get("base_url", self.base_url)
        self.timeout = data.get("timeout", self.timeout)
        self.max_retries = data.get("max_retries", self.max_retries)
        self.debug = data.get("debug", self.debug)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "org_id": self.org_id,
            "token": "***" if self.token else None,  # Mask token for security
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "debug": self.debug
        }
    
    def is_valid(self) -> bool:
        """Check if the configuration is valid."""
        return bool(self.org_id and self.token)


# Global configuration instance
config = Config()


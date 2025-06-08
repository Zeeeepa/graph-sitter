"""
Direct Configuration Manager for Single-User Dashboard

Handles API keys and configurations through environment variables and simple config file.
No encryption, validation layers, or complex security - just effective functionality.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from graph_sitter.shared.logging.get_logger import get_logger
from .models import DashboardConfig, ExtensionConfig

logger = get_logger(__name__)


@dataclass
class APICredentials:
    """Simple container for API credentials"""
    github_token: Optional[str] = None
    linear_api_key: Optional[str] = None
    codegen_org_id: Optional[str] = None
    codegen_token: Optional[str] = None
    slack_webhook: Optional[str] = None
    circleci_token: Optional[str] = None
    postgresql_url: Optional[str] = None


class SettingsManager:
    """
    Simple settings management for single-user dashboard.
    
    Features:
    - Environment variable configuration
    - Simple JSON config file
    - Direct API key access
    - Sensible defaults
    """
    
    def __init__(self, config_file: str = "dashboard_config.json"):
        self.config_file = Path(config_file)
        self.config = DashboardConfig()
        self.credentials = APICredentials()
        self._load_configuration()
        
    def _load_configuration(self):
        """Load configuration from environment variables and config file"""
        logger.info("Loading dashboard configuration...")
        
        # Load from environment variables first
        self._load_from_environment()
        
        # Load from config file if it exists
        if self.config_file.exists():
            self._load_from_file()
        else:
            # Create default config file
            self._create_default_config()
            
        # Validate essential credentials
        self._validate_credentials()
        
    def _load_from_environment(self):
        """Load configuration from environment variables"""
        # API Credentials
        self.credentials.github_token = os.getenv("GITHUB_TOKEN")
        self.credentials.linear_api_key = os.getenv("LINEAR_API_KEY")
        self.credentials.codegen_org_id = os.getenv("CODEGEN_ORG_ID")
        self.credentials.codegen_token = os.getenv("CODEGEN_TOKEN")
        self.credentials.slack_webhook = os.getenv("SLACK_WEBHOOK")
        self.credentials.circleci_token = os.getenv("CIRCLECI_TOKEN")
        self.credentials.postgresql_url = os.getenv("DATABASE_URL", "sqlite:///dashboard.db")
        
        # Global settings
        self.config.auto_deploy = os.getenv("AUTO_DEPLOY", "true").lower() == "true"
        self.config.auto_analyze = os.getenv("AUTO_ANALYZE", "true").lower() == "true"
        self.config.notification_level = os.getenv("NOTIFICATION_LEVEL", "normal")
        self.config.workspace_path = os.getenv("WORKSPACE_PATH", "./workspace")
        self.config.logs_path = os.getenv("LOGS_PATH", "./logs")
        
    def _load_from_file(self):
        """Load additional configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                file_config = json.load(f)
                
            # Update extension configurations
            for ext_name, ext_config in file_config.get("extensions", {}).items():
                self.config.extensions[ext_name] = ExtensionConfig(
                    extension_name=ext_name,
                    enabled=ext_config.get("enabled", True),
                    config=ext_config.get("config", {}),
                    api_keys=ext_config.get("api_keys", {})
                )
                
            logger.info(f"Loaded configuration from {self.config_file}")
            
        except Exception as e:
            logger.error(f"Failed to load config file {self.config_file}: {e}")
            
    def _create_default_config(self):
        """Create default configuration file"""
        default_config = {
            "extensions": {
                "github": {
                    "enabled": True,
                    "config": {
                        "auto_sync": True,
                        "webhook_enabled": False
                    }
                },
                "linear": {
                    "enabled": True,
                    "config": {
                        "auto_create_issues": True,
                        "default_team": None
                    }
                },
                "codegen": {
                    "enabled": True,
                    "config": {
                        "model": "claude-3-sonnet",
                        "max_tokens": 4000
                    }
                },
                "slack": {
                    "enabled": True,
                    "config": {
                        "notify_on_start": True,
                        "notify_on_complete": True,
                        "notify_on_error": True
                    }
                },
                "circleci": {
                    "enabled": True,
                    "config": {
                        "auto_trigger": True,
                        "wait_for_completion": True
                    }
                },
                "grainchain": {
                    "enabled": True,
                    "config": {
                        "sandbox_type": "development",
                        "auto_snapshot": True,
                        "cleanup_after": 24  # hours
                    }
                },
                "graph_sitter": {
                    "enabled": True,
                    "config": {
                        "analyze_on_pin": True,
                        "analyze_on_change": True,
                        "include_tests": True
                    }
                },
                "prefect": {
                    "enabled": True,
                    "config": {
                        "max_concurrent_flows": 3,
                        "retry_attempts": 2
                    }
                },
                "controlflow": {
                    "enabled": True,
                    "config": {
                        "max_agents": 5,
                        "agent_timeout": 300  # seconds
                    }
                },
                "modal": {
                    "enabled": True,
                    "config": {
                        "auto_scale": True,
                        "max_instances": 10
                    }
                },
                "contexten_app": {
                    "enabled": True,
                    "config": {
                        "port": 8000,
                        "debug": False
                    }
                }
            },
            "global_settings": {
                "auto_deploy": True,
                "auto_analyze": True,
                "notification_level": "normal",
                "workspace_path": "./workspace",
                "logs_path": "./logs"
            }
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default configuration file: {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to create default config file: {e}")
            
    def _validate_credentials(self):
        """Validate essential credentials are present"""
        missing = []
        
        if not self.credentials.github_token:
            missing.append("GITHUB_TOKEN")
        if not self.credentials.codegen_org_id:
            missing.append("CODEGEN_ORG_ID")
        if not self.credentials.codegen_token:
            missing.append("CODEGEN_TOKEN")
            
        if missing:
            logger.warning(f"Missing essential credentials: {', '.join(missing)}")
            logger.info("Set these environment variables for full functionality")
        else:
            logger.info("All essential credentials are configured")
            
    def get_extension_config(self, extension_name: str) -> ExtensionConfig:
        """Get configuration for a specific extension"""
        if extension_name not in self.config.extensions:
            # Create default config for extension
            self.config.extensions[extension_name] = ExtensionConfig(
                extension_name=extension_name,
                enabled=True
            )
        return self.config.extensions[extension_name]
        
    def get_api_credential(self, service: str) -> Optional[str]:
        """Get API credential for a service"""
        credential_map = {
            "github": self.credentials.github_token,
            "linear": self.credentials.linear_api_key,
            "codegen_org_id": self.credentials.codegen_org_id,
            "codegen_token": self.credentials.codegen_token,
            "slack": self.credentials.slack_webhook,
            "circleci": self.credentials.circleci_token,
            "database": self.credentials.postgresql_url
        }
        return credential_map.get(service)
        
    def is_extension_enabled(self, extension_name: str) -> bool:
        """Check if an extension is enabled"""
        config = self.get_extension_config(extension_name)
        return config.enabled
        
    def get_extension_setting(self, extension_name: str, setting_name: str, default=None):
        """Get a specific setting for an extension"""
        config = self.get_extension_config(extension_name)
        return config.config.get(setting_name, default)
        
    def update_extension_setting(self, extension_name: str, setting_name: str, value: Any):
        """Update a setting for an extension"""
        config = self.get_extension_config(extension_name)
        config.config[setting_name] = value
        self._save_config()
        
    def enable_extension(self, extension_name: str):
        """Enable an extension"""
        config = self.get_extension_config(extension_name)
        config.enabled = True
        self._save_config()
        logger.info(f"Enabled extension: {extension_name}")
        
    def disable_extension(self, extension_name: str):
        """Disable an extension"""
        config = self.get_extension_config(extension_name)
        config.enabled = False
        self._save_config()
        logger.info(f"Disabled extension: {extension_name}")
        
    def _save_config(self):
        """Save current configuration to file"""
        try:
            config_data = {
                "extensions": {
                    name: {
                        "enabled": config.enabled,
                        "config": config.config,
                        "api_keys": config.api_keys
                    }
                    for name, config in self.config.extensions.items()
                },
                "global_settings": {
                    "auto_deploy": self.config.auto_deploy,
                    "auto_analyze": self.config.auto_analyze,
                    "notification_level": self.config.notification_level,
                    "workspace_path": self.config.workspace_path,
                    "logs_path": self.config.logs_path
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            
    def get_setup_status(self) -> Dict[str, Any]:
        """Get setup status for all extensions"""
        status = {
            "credentials": {
                "github": bool(self.credentials.github_token),
                "linear": bool(self.credentials.linear_api_key),
                "codegen": bool(self.credentials.codegen_org_id and self.credentials.codegen_token),
                "slack": bool(self.credentials.slack_webhook),
                "circleci": bool(self.credentials.circleci_token),
                "database": bool(self.credentials.postgresql_url)
            },
            "extensions": {
                name: config.enabled
                for name, config in self.config.extensions.items()
            },
            "ready": all([
                self.credentials.github_token,
                self.credentials.codegen_org_id,
                self.credentials.codegen_token
            ])
        }
        return status
        
    def get_configuration_help(self) -> str:
        """Get help text for configuration setup"""
        return """
Dashboard Configuration Help
===========================

Required Environment Variables:
- GITHUB_TOKEN: GitHub personal access token
- CODEGEN_ORG_ID: Your Codegen organization ID
- CODEGEN_TOKEN: Your Codegen API token

Optional Environment Variables:
- LINEAR_API_KEY: Linear API key for task management
- SLACK_WEBHOOK: Slack webhook URL for notifications
- CIRCLECI_TOKEN: CircleCI API token for CI/CD monitoring
- DATABASE_URL: Database connection string (defaults to SQLite)

Configuration File:
- Edit dashboard_config.json to customize extension settings
- All extensions are enabled by default
- Settings can be modified through the dashboard UI

Setup Steps:
1. Set required environment variables
2. Run the dashboard application
3. Configure additional settings through the UI
4. Pin your first GitHub project to get started
"""


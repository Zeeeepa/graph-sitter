"""Example configuration for Contexten application.

This file shows how to configure all extensions and services.
Copy this file and modify the values according to your setup.
"""

import os
from typing import Dict, Any

def get_example_config() -> Dict[str, Any]:
    """Get example configuration for Contexten.
    
    Returns:
        Configuration dictionary
    """
    return {
        # GitHub Extension Configuration
        "github": {
            "token": os.getenv("GITHUB_TOKEN", "your_github_token_here"),
            "webhook_secret": os.getenv("GITHUB_WEBHOOK_SECRET", "your_webhook_secret"),
            "base_url": "https://api.github.com"  # For GitHub Enterprise, use your instance URL
        },

        # Linear Extension Configuration
        "linear": {
            "api_key": os.getenv("LINEAR_API_KEY", "your_linear_api_key_here"),
            "webhook_secret": os.getenv("LINEAR_WEBHOOK_SECRET", "your_webhook_secret")
        },

        # Codegen Extension Configuration
        "codegen": {
            "org_id": os.getenv("CODEGEN_ORG_ID", "your_codegen_org_id"),
            "token": os.getenv("CODEGEN_TOKEN", "your_codegen_token"),
            "base_url": "https://api.codegen.com"  # Optional: custom base URL
        },

        # Flow Orchestration Configuration
        "flows": {
            # Prefect Configuration
            "prefect": {
                "api_url": os.getenv("PREFECT_API_URL", "https://api.prefect.cloud"),
                "api_key": os.getenv("PREFECT_API_KEY", "your_prefect_api_key")
            },

            # ControlFlow Configuration
            "controlflow": {
                "api_url": os.getenv("CONTROLFLOW_API_URL", "https://api.controlflow.dev"),
                "api_key": os.getenv("CONTROLFLOW_API_KEY", "your_controlflow_api_key")
            },

            # Strands Configuration
            "strands": {
                "api_url": os.getenv("STRANDS_API_URL", "https://api.strands.dev"),
                "api_key": os.getenv("STRANDS_API_KEY", "your_strands_api_key")
            },

            # MCP Configuration
            "mcp": {
                "server_url": os.getenv("MCP_SERVER_URL", "https://mcp.example.com"),
                "auth_token": os.getenv("MCP_AUTH_TOKEN", "your_mcp_token")
            }
        },

        # Dashboard Configuration
        "dashboard": {
            "host": os.getenv("DASHBOARD_HOST", "0.0.0.0"),
            "port": int(os.getenv("DASHBOARD_PORT", "8000")),
            "frontend_path": os.getenv("DASHBOARD_FRONTEND_PATH", "./frontend/build")
        },

        # Slack Extension Configuration (Optional)
        "slack": {
            "token": os.getenv("SLACK_BOT_TOKEN", "your_slack_bot_token"),
            "signing_secret": os.getenv("SLACK_SIGNING_SECRET", "your_slack_signing_secret"),
            "app_token": os.getenv("SLACK_APP_TOKEN", "your_slack_app_token")
        },

        # CircleCI Extension Configuration (Optional)
        "circleci": {
            "token": os.getenv("CIRCLECI_TOKEN", "your_circleci_token"),
            "webhook_secret": os.getenv("CIRCLECI_WEBHOOK_SECRET", "your_webhook_secret")
        },

        # State Management Configuration
        "state": {
            "persistence_enabled": True,
            "persistence_path": os.getenv("STATE_FILE_PATH", "./contexten_state.json")
        },

        # Event Bus Configuration
        "events": {
            "queue_size": 1000,
            "worker_count": 4
        },

        # Logging Configuration
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": os.getenv("LOG_FILE", "./contexten.log")
        }
    }

def get_minimal_config() -> Dict[str, Any]:
    """Get minimal configuration for testing.
    
    Returns:
        Minimal configuration dictionary
    """
    return {
        "dashboard": {
            "host": "127.0.0.1",
            "port": 8000
        },
        "flows": {},
        "state": {
            "persistence_enabled": False
        }
    }

def get_production_config() -> Dict[str, Any]:
    """Get production configuration template.
    
    Returns:
        Production configuration dictionary
    """
    config = get_example_config()
    
    # Production-specific overrides
    config.update({
        "dashboard": {
            "host": "0.0.0.0",
            "port": 8000,
            "frontend_path": "/app/frontend/build"
        },
        "state": {
            "persistence_enabled": True,
            "persistence_path": "/data/contexten_state.json"
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": "/var/log/contexten.log"
        }
    })
    
    return config

# Environment-specific configurations
CONFIGURATIONS = {
    "development": get_example_config,
    "testing": get_minimal_config,
    "production": get_production_config
}

def get_config(environment: str = "development") -> Dict[str, Any]:
    """Get configuration for specific environment.
    
    Args:
        environment: Environment name (development, testing, production)
        
    Returns:
        Configuration dictionary
        
    Raises:
        ValueError: If environment is not supported
    """
    if environment not in CONFIGURATIONS:
        raise ValueError(f"Unsupported environment: {environment}")
    
    return CONFIGURATIONS[environment]()


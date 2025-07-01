"""
Secure secrets management for PR validation system.
Uses environment variables and GitHub Secrets for credential management.
"""

import os
from typing import Optional

class SecretManager:
    @staticmethod
    def get_required_secret(name: str) -> str:
        """Get a required secret, raising an error if not found."""
        value = os.getenv(name)
        if not value:
            raise ValueError(f"Required secret {name} not found in environment")
        return value
    
    @staticmethod
    def get_optional_secret(name: str, default: Optional[str] = None) -> Optional[str]:
        """Get an optional secret, returning default if not found."""
        return os.getenv(name, default)
    
    @staticmethod
    def validate_required_secrets() -> bool:
        """Validate that all required secrets are present."""
        required_secrets = [
            'GITHUB_TOKEN',
            'CODEGEN_ORG_ID',
            'CODEGEN_API_TOKEN'
        ]
        
        missing_secrets = []
        for secret in required_secrets:
            if not os.getenv(secret):
                missing_secrets.append(secret)
        
        if missing_secrets:
            raise ValueError(f"Missing required secrets: {', '.join(missing_secrets)}")
        
        return True


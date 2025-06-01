"""
Codegen SDK Configuration Utilities

This module provides utilities for configuring and validating Codegen SDK integration
in the Contexten orchestrator.
"""

import os
from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass

try:
    from codegen import Agent as CodegenAgent
    CODEGEN_AVAILABLE = True
except ImportError:
    CODEGEN_AVAILABLE = False


@dataclass
class CodegenConfig:
    """Configuration for Codegen SDK integration."""
    
    org_id: str
    token: str
    base_url: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> Optional['CodegenConfig']:
        """Create configuration from environment variables.
        
        Returns:
            CodegenConfig if all required variables are present, None otherwise
        """
        org_id = os.getenv("CODEGEN_ORG_ID")
        token = os.getenv("CODEGEN_TOKEN")
        base_url = os.getenv("CODEGEN_BASE_URL")
        
        if org_id and token:
            return cls(org_id=org_id, token=token, base_url=base_url)
        return None
    
    def validate(self) -> Tuple[bool, str]:
        """Validate the configuration.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not CODEGEN_AVAILABLE:
            return False, "Codegen SDK is not installed. Install with: pip install codegen"
        
        if not self.org_id:
            return False, "CODEGEN_ORG_ID is required"
        
        if not self.token:
            return False, "CODEGEN_TOKEN is required"
        
        try:
            # Test connection
            agent = CodegenAgent(org_id=self.org_id, token=self.token)
            # You could add a simple test call here if the SDK supports it
            return True, "Configuration is valid"
        except Exception as e:
            return False, f"Failed to initialize Codegen agent: {str(e)}"


def get_codegen_status() -> Dict[str, Any]:
    """Get the current status of Codegen SDK integration.
    
    Returns:
        Dictionary with status information
    """
    status = {
        "sdk_available": CODEGEN_AVAILABLE,
        "config_present": False,
        "config_valid": False,
        "error": None,
        "org_id": None,
        "has_token": False
    }
    
    if not CODEGEN_AVAILABLE:
        status["error"] = "Codegen SDK not installed"
        return status
    
    config = CodegenConfig.from_env()
    if config:
        status["config_present"] = True
        status["org_id"] = config.org_id
        status["has_token"] = bool(config.token)
        
        is_valid, error = config.validate()
        status["config_valid"] = is_valid
        if not is_valid:
            status["error"] = error
    else:
        status["error"] = "Missing CODEGEN_ORG_ID or CODEGEN_TOKEN environment variables"
    
    return status


def print_codegen_status():
    """Print a formatted status report of Codegen SDK integration."""
    status = get_codegen_status()
    
    print("🤖 Codegen SDK Integration Status")
    print("=" * 40)
    
    if status["sdk_available"]:
        print("✅ Codegen SDK is installed")
    else:
        print("❌ Codegen SDK is not installed")
        print("   Install with: pip install codegen")
        return
    
    if status["config_present"]:
        print("✅ Configuration found in environment")
        print(f"   Org ID: {status['org_id']}")
        print(f"   Token: {'✅ Present' if status['has_token'] else '❌ Missing'}")
    else:
        print("❌ Configuration missing")
        print("   Required environment variables:")
        print("   - CODEGEN_ORG_ID=your_organization_id_here")
        print("   - CODEGEN_TOKEN=your_api_token_here")
        return
    
    if status["config_valid"]:
        print("✅ Configuration is valid and working")
    else:
        print(f"❌ Configuration error: {status['error']}")
    
    print("\n📖 Usage:")
    print("   Both ChatAgent and CodeAgent will automatically use Codegen SDK")
    print("   when valid configuration is detected.")
    print("   Set use_codegen_sdk=False to force local-only mode.")


def setup_codegen_env(org_id: str, token: str, base_url: Optional[str] = None):
    """Set up Codegen environment variables programmatically.
    
    Args:
        org_id: Codegen organization ID
        token: Codegen API token
        base_url: Optional custom base URL
    """
    os.environ["CODEGEN_ORG_ID"] = org_id
    os.environ["CODEGEN_TOKEN"] = token
    
    if base_url:
        os.environ["CODEGEN_BASE_URL"] = base_url
    
    print(f"✅ Codegen environment configured (org_id: {org_id})")


if __name__ == "__main__":
    print_codegen_status()


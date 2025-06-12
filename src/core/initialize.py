"""
Core initialization module for PR validation system.
Handles setup of sandbox environment and validation tools.
"""

import os
import sys
from typing import Dict, Any
import yaml
from grainchain import Sandbox
from codegen import Agent
from graph_sitter import Codebase

class ValidationEnvironment:
    def __init__(self):
        self.sandbox = None
        self.agent = None
        self.codebase = None
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'validation.yml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
        
    async def initialize(self):
        """Initialize the validation environment."""
        # Initialize sandbox for isolated command execution
        self.sandbox = await Sandbox().create()
        
        # Initialize codegen agent for code analysis
        self.agent = Agent(
            org_id=os.getenv('CODEGEN_ORG_ID'),
            token=os.getenv('CODEGEN_API_TOKEN')
        )
        
        # Initialize codebase analysis
        self.codebase = Codebase("./")
        
        # Set up global variables from config
        if 'global_vars' in self.config:
            for key, value in self.config['global_vars'].items():
                os.environ[key] = str(value)
                
    async def cleanup(self):
        """Cleanup resources."""
        if self.sandbox:
            await self.sandbox.cleanup()

async def main():
    """Main initialization function."""
    env = ValidationEnvironment()
    try:
        await env.initialize()
        print("✅ Validation environment initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing validation environment: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await env.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


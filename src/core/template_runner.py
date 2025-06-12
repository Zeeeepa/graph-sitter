"""
Template runner for executing pre-defined command lists.
Supports global variables and command validation.
"""

import os
import sys
import yaml
from typing import List, Dict, Any
from grainchain import Sandbox
from .initialize import ValidationEnvironment

class CommandTemplate:
    def __init__(self, template: Dict[str, Any]):
        self.name = template.get('name', 'unnamed')
        self.commands = template.get('commands', [])
        self.variables = template.get('variables', {})
        self.validation = template.get('validation', {})
        
    def validate_command(self, command: str) -> bool:
        """Validate a command against security rules."""
        # Add security validation logic here
        return True
        
    def substitute_variables(self, command: str, global_vars: Dict[str, str]) -> str:
        """Substitute variables in command string."""
        result = command
        for key, value in {**self.variables, **global_vars}.items():
            result = result.replace(f"${key}", str(value))
        return result

class TemplateRunner:
    def __init__(self):
        self.env = ValidationEnvironment()
        self.templates = self._load_templates()
        
    def _load_templates(self) -> List[CommandTemplate]:
        """Load command templates from YAML file."""
        template_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'templates.yml')
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                data = yaml.safe_load(f)
                return [CommandTemplate(t) for t in data.get('templates', [])]
        return []
        
    async def run_template(self, template: CommandTemplate) -> bool:
        """Run a command template in the sandbox."""
        try:
            async with Sandbox() as sandbox:
                for cmd in template.commands:
                    if not template.validate_command(cmd):
                        print(f"❌ Command validation failed: {cmd}", file=sys.stderr)
                        return False
                        
                    # Substitute variables
                    cmd = template.substitute_variables(cmd, os.environ)
                    
                    # Execute command
                    result = await sandbox.execute(cmd)
                    if result.returncode != 0:
                        print(f"❌ Command failed: {cmd}", file=sys.stderr)
                        print(f"Error output: {result.stderr}", file=sys.stderr)
                        return False
                        
                    print(f"✅ Command succeeded: {cmd}")
                    print(f"Output: {result.stdout}")
                    
            return True
            
        except Exception as e:
            print(f"❌ Error running template {template.name}: {e}", file=sys.stderr)
            return False
            
    async def run_all(self) -> bool:
        """Run all command templates."""
        success = True
        for template in self.templates:
            print(f"Running template: {template.name}")
            if not await self.run_template(template):
                success = False
        return success

async def main():
    """Main function for template runner."""
    runner = TemplateRunner()
    success = await runner.run_all()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


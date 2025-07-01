"""
Feature validator using codegen and graph-sitter for code analysis.
"""

import os
import sys
from typing import List, Dict, Any
from codegen import Agent
from graph_sitter import Codebase
from ..core.initialize import ValidationEnvironment

class FeatureValidator:
    def __init__(self):
        self.env = ValidationEnvironment()
        self.agent = Agent(
            org_id=os.getenv('CODEGEN_ORG_ID'),
            token=os.getenv('CODEGEN_API_TOKEN')
        )
        self.codebase = Codebase("./")
        
    async def validate_changes(self) -> bool:
        """Validate code changes in the PR."""
        try:
            # Get PR information
            pr_number = os.getenv('GITHUB_PR_NUMBER')
            if not pr_number:
                print("❌ No PR number found in environment", file=sys.stderr)
                return False
                
            # Analyze code changes
            task = self.agent.run(f"Analyze PR #{pr_number} for potential issues")
            task.refresh()
            
            if task.status != "completed":
                print("❌ Code analysis failed", file=sys.stderr)
                return False
                
            # Validate code structure
            functions = self.codebase.functions
            for function in functions:
                # Check for unused functions
                if not function.usages:
                    print(f"⚠️ Warning: Unused function found: {function.name}")
                    
                # Check for complexity
                if function.complexity > 10:  # Example threshold
                    print(f"⚠️ Warning: High complexity in function: {function.name}")
                    
            # Additional validation logic here
            
            return True
            
        except Exception as e:
            print(f"❌ Error during feature validation: {e}", file=sys.stderr)
            return False
            
    async def run_tests(self) -> bool:
        """Run tests for new features."""
        try:
            # Add test execution logic here
            return True
        except Exception as e:
            print(f"❌ Error running tests: {e}", file=sys.stderr)
            return False

async def main():
    """Main function for feature validation."""
    validator = FeatureValidator()
    
    # Run validations
    changes_valid = await validator.validate_changes()
    tests_passed = await validator.run_tests()
    
    if not (changes_valid and tests_passed):
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


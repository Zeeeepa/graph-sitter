"""
Deployment synchronization module for GitHub integration.
"""

import os
import sys
import json
from typing import Dict, Any
from github import Github
from ..core.initialize import ValidationEnvironment

class DeploymentSync:
    def __init__(self):
        self.env = ValidationEnvironment()
        self.github = Github(os.getenv('GITHUB_TOKEN'))
        self.repo = self.github.get_repo(os.getenv('GITHUB_REPOSITORY'))
        
    async def update_deployment_status(self, status: str, description: str) -> bool:
        """Update deployment status on GitHub."""
        try:
            # Get PR number
            pr_number = os.getenv('GITHUB_PR_NUMBER')
            if not pr_number:
                print("❌ No PR number found in environment", file=sys.stderr)
                return False
                
            # Get PR
            pr = self.repo.get_pull(int(pr_number))
            
            # Create deployment status
            deployment = self.repo.create_deployment(
                ref=pr.head.ref,
                environment="validation",
                description=description
            )
            
            # Update status
            deployment.create_status(
                state=status,
                description=description,
                environment="validation"
            )
            
            print(f"✅ Updated deployment status: {status} - {description}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating deployment status: {e}", file=sys.stderr)
            return False
            
    async def sync_validation_results(self) -> bool:
        """Sync validation results with GitHub."""
        try:
            # Load validation results
            results_path = os.path.join(os.path.dirname(__file__), '..', 'results', 'validation.json')
            if os.path.exists(results_path):
                with open(results_path, 'r') as f:
                    results = json.load(f)
                    
                # Update status based on results
                status = "success" if results.get('success', False) else "failure"
                description = results.get('description', 'Validation completed')
                
                return await self.update_deployment_status(status, description)
            
            print("❌ No validation results found", file=sys.stderr)
            return False
            
        except Exception as e:
            print(f"❌ Error syncing validation results: {e}", file=sys.stderr)
            return False

async def main():
    """Main function for deployment sync."""
    sync = DeploymentSync()
    if not await sync.sync_validation_results():
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


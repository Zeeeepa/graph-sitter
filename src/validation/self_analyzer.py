"""
Self-analysis module for PR validation system.
Analyzes its own PRs and provides feedback.
"""

import os
import sys
from typing import Dict, Any, List
from github import Github
from codegen import Agent
from graph_sitter import Codebase
from ..core.secrets import SecretManager
from ..core.initialize import ValidationEnvironment

class SelfAnalyzer:
    def __init__(self):
        self.env = ValidationEnvironment()
        self.github = Github(SecretManager.get_required_secret('GITHUB_TOKEN'))
        self.repo = self.github.get_repo(os.getenv('GITHUB_REPOSITORY'))
        self.agent = Agent(
            org_id=SecretManager.get_required_secret('CODEGEN_ORG_ID'),
            token=SecretManager.get_required_secret('CODEGEN_API_TOKEN')
        )
        self.codebase = Codebase("./")
        
    async def analyze_self_pr(self) -> Dict[str, Any]:
        """Analyze the current PR that contains this code."""
        try:
            # Get PR number from environment
            pr_number = os.getenv('GITHUB_PR_NUMBER')
            if not pr_number:
                raise ValueError("No PR number found in environment")
            
            pr = self.repo.get_pull(int(pr_number))
            
            # Analyze changes
            analysis = await self._analyze_changes(pr)
            
            # Add PR comment with analysis
            await self._comment_on_pr(pr, analysis)
            
            return analysis
            
        except Exception as e:
            print(f"❌ Error during self-analysis: {e}", file=sys.stderr)
            return {"error": str(e)}
            
    async def _analyze_changes(self, pr) -> Dict[str, Any]:
        """Analyze PR changes using codegen and graph-sitter."""
        analysis = {
            "security_issues": [],
            "code_quality": [],
            "potential_improvements": []
        }
        
        # Check for security issues
        security_task = self.agent.run(f"Analyze PR #{pr.number} for security issues")
        security_task.refresh()
        if security_task.status == "completed":
            analysis["security_issues"] = security_task.result
            
        # Analyze code quality
        for file in self.codebase.files:
            # Check complexity
            functions = file.functions
            for func in functions:
                if func.complexity > 10:
                    analysis["code_quality"].append({
                        "file": file.path,
                        "function": func.name,
                        "issue": "High complexity",
                        "suggestion": "Consider breaking down into smaller functions"
                    })
                    
            # Check for potential improvements
            if len(file.imports) > 15:
                analysis["potential_improvements"].append({
                    "file": file.path,
                    "issue": "High number of imports",
                    "suggestion": "Consider modularizing or using facade pattern"
                })
                
        return analysis
        
    async def _comment_on_pr(self, pr, analysis: Dict[str, Any]) -> None:
        """Add analysis results as a PR comment."""
        comment = "## 🔍 Self-Analysis Results\n\n"
        
        if analysis.get("security_issues"):
            comment += "### 🔒 Security Issues\n"
            for issue in analysis["security_issues"]:
                comment += f"- {issue}\n"
                
        if analysis.get("code_quality"):
            comment += "\n### 📊 Code Quality\n"
            for issue in analysis["code_quality"]:
                comment += f"- **{issue['file']}** ({issue['function']}): {issue['issue']}\n"
                comment += f"  - Suggestion: {issue['suggestion']}\n"
                
        if analysis.get("potential_improvements"):
            comment += "\n### 💡 Potential Improvements\n"
            for improvement in analysis["potential_improvements"]:
                comment += f"- **{improvement['file']}**: {improvement['issue']}\n"
                comment += f"  - Suggestion: {improvement['suggestion']}\n"
                
        pr.create_issue_comment(comment)

async def main():
    """Main function for self-analysis."""
    try:
        SecretManager.validate_required_secrets()
        analyzer = SelfAnalyzer()
        await analyzer.analyze_self_pr()
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())


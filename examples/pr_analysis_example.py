"""
Example of using the PR static analysis system.
"""
import asyncio
import os
from typing import Dict, List

from graph_sitter.extensions.github.pr_analysis import (
    PRGitHubClient,
    GitHubWebhookHandler,
    GitHubCommentFormatter,
    PRAnalyzer
)


class MockRuleEngine:
    """Mock rule engine for demonstration purposes."""
    
    async def apply_rules(self, diff_context: Dict) -> List[Dict]:
        """Apply rules to the diff context.

        Args:
            diff_context: Diff context

        Returns:
            List of analysis results
        """
        # In a real implementation, this would analyze the diff context
        # and return a list of issues found
        return [
            {
                'rule_id': 'UNUSED_IMPORT',
                'message': 'Unused import detected',
                'severity': 'warning',
                'file': 'src/example.py',
                'line': 10,
                'code_snippet': 'import os  # This import is not used',
                'suggestion': 'Remove the unused import'
            },
            {
                'rule_id': 'SYNTAX_ERROR',
                'message': 'Syntax error detected',
                'severity': 'error',
                'file': 'src/example.py',
                'line': 15,
                'code_snippet': 'def function(:\n    pass',
                'suggestion': 'Fix the syntax error in the function definition'
            }
        ]


async def main():
    """Run the example."""
    # Get GitHub token from environment
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("GITHUB_TOKEN environment variable not set")
        return

    # Create components
    github_client = PRGitHubClient(token=github_token)
    rule_engine = MockRuleEngine()
    comment_formatter = GitHubCommentFormatter()
    pr_analyzer = PRAnalyzer(github_client, rule_engine, comment_formatter)
    
    # Create webhook handler
    webhook_secret = os.environ.get('WEBHOOK_SECRET')
    webhook_handler = GitHubWebhookHandler(pr_analyzer, webhook_secret)
    
    # Analyze a PR
    pr_number = 123  # Replace with a real PR number
    repository = 'owner/repo'  # Replace with a real repository
    
    results = await pr_analyzer.analyze_pr(pr_number, repository)
    
    # Format and print results
    pr_context = {
        'number': pr_number,
        'title': 'Example PR',
        'html_url': f'https://github.com/{repository}/pull/{pr_number}'
    }
    comment = comment_formatter.format_results(results, pr_context)
    
    print(comment)


if __name__ == '__main__':
    asyncio.run(main())


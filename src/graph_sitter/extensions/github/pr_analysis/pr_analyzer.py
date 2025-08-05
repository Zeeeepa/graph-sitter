"""
PR analyzer for GitHub integration.
"""
from typing import Dict, List, Optional, Any

from github.PullRequest import PullRequest

from graph_sitter.extensions.github.pr_analysis.pr_client import PRGitHubClient
from graph_sitter.extensions.github.pr_analysis.comment_formatter import GitHubCommentFormatter
from graph_sitter.extensions.github.types.pull_request import PullRequest as PRModel
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class PRAnalyzer:
    """Main orchestrator for PR analysis."""
    
    def __init__(self, github_client: PRGitHubClient, rule_engine: Any, comment_formatter: Optional[GitHubCommentFormatter] = None):
        """Initialize the PR analyzer.

        Args:
            github_client: GitHub client
            rule_engine: Rule engine for applying analysis rules
            comment_formatter: Formatter for GitHub comments
        """
        self.github_client = github_client
        self.rule_engine = rule_engine
        self.comment_formatter = comment_formatter or GitHubCommentFormatter()
        
    async def analyze_pr(self, pr_number: int, repository: str) -> List[Dict]:
        """Analyze a PR and return results.

        Args:
            pr_number: PR number
            repository: Repository full name

        Returns:
            List of analysis results
        """
        logger.info(f"Analyzing PR {pr_number} in {repository}")
        
        # Get PR data
        pr = self.github_client.get_pr(pr_number, repository)
        if not pr:
            logger.error(f"PR {pr_number} not found in {repository}")
            return []
        
        # Create PR context
        pr_context = self._create_pr_context(pr)
        
        # Create analysis contexts
        base_context = await self._create_analysis_context(pr_context['base'])
        head_context = await self._create_analysis_context(pr_context['head'])
        
        # Create diff context
        diff_context = await self._create_diff_context(base_context, head_context)
        
        # Apply rules
        results = await self.rule_engine.apply_rules(diff_context)
        
        logger.info(f"Analysis complete for PR {pr_number} in {repository}: {len(results)} issues found")
        
        return results
    
    def format_results(self, results: List[Dict], pr_number: int, repository: str) -> str:
        """Format analysis results as a GitHub comment.

        Args:
            results: Analysis results
            pr_number: PR number
            repository: Repository full name

        Returns:
            Formatted comment string
        """
        # Get PR data
        pr = self.github_client.get_pr(pr_number, repository)
        if not pr:
            logger.error(f"PR {pr_number} not found in {repository}")
            return "Error: PR not found"
        
        # Create PR context
        pr_context = self._create_pr_context(pr)
        
        # Format results
        return self.comment_formatter.format_results(results, pr_context)
    
    async def post_comment(self, pr_number: int, repository: str, comment: str) -> bool:
        """Post a comment on a PR.

        Args:
            pr_number: PR number
            repository: Repository full name
            comment: Comment text

        Returns:
            True if successful, False otherwise
        """
        # Get PR data
        pr = self.github_client.get_pr(pr_number, repository)
        if not pr:
            logger.error(f"PR {pr_number} not found in {repository}")
            return False
        
        # Post comment
        return self.github_client.post_comment(pr, comment)
    
    def _create_pr_context(self, pr: PullRequest) -> Dict:
        """Create a PR context from a GitHub PR object.

        Args:
            pr: GitHub PR object

        Returns:
            PR context dictionary
        """
        return {
            'number': pr.number,
            'title': pr.title,
            'body': pr.body,
            'state': pr.state,
            'base': {
                'ref': pr.base.ref,
                'sha': pr.base.sha,
                'repo_name': pr.base.repo.full_name
            },
            'head': {
                'ref': pr.head.ref,
                'sha': pr.head.sha,
                'repo_name': pr.head.repo.full_name
            },
            'user': {
                'login': pr.user.login,
                'id': pr.user.id,
                'html_url': pr.user.html_url
            },
            'html_url': pr.html_url
        }
    
    async def _create_analysis_context(self, pr_part: Dict) -> Dict:
        """Create an analysis context for a PR part (base or head).

        Args:
            pr_part: PR part context

        Returns:
            Analysis context
        """
        # This would typically involve cloning the repository at the specified ref
        # and creating a codebase context for analysis
        # For now, we'll return a placeholder
        return {
            'ref': pr_part['ref'],
            'sha': pr_part['sha'],
            'repo_name': pr_part['repo_name'],
            'codebase': None  # This would be a codebase context in a real implementation
        }
    
    async def _create_diff_context(self, base_context: Dict, head_context: Dict) -> Dict:
        """Create a diff context from base and head contexts.

        Args:
            base_context: Base branch context
            head_context: Head branch context

        Returns:
            Diff context
        """
        # This would typically involve comparing the base and head codebases
        # and creating a diff context for analysis
        # For now, we'll return a placeholder
        return {
            'base': base_context,
            'head': head_context,
            'changes': []  # This would be a list of changes in a real implementation
        }


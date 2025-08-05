"""
PR static analysis system.

This module provides the main PR static analysis functionality,
integrating with GitHub to fetch PR data, analyze it, and post results.
"""

import os
from typing import Any, Dict, List, Optional, Tuple, Union

from github.PullRequest import PullRequest
from github.Repository import Repository

from graph_sitter.git.auth.github_auth import GitHubAuth
from graph_sitter.git.clients.github_api_client import GitHubAPIClient
from graph_sitter.git.models.pr_comment import PRComment, PRReviewComment
from graph_sitter.git.models.pr_commit import PRCommit
from graph_sitter.git.models.pr_file import PRFile
from graph_sitter.git.models.pull_request_context import PullRequestContext
from graph_sitter.git.utils.comment_formatter import CommentFormatter
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class PRAnalyzer:
    """
    PR static analysis system.
    
    This class provides the main PR static analysis functionality,
    integrating with GitHub to fetch PR data, analyze it, and post results.
    """
    
    _github_client: GitHubAPIClient
    _comment_formatter: CommentFormatter
    
    def __init__(
        self,
        github_client: GitHubAPIClient,
        comment_formatter: Optional[CommentFormatter] = None
    ):
        """
        Initialize the PR analyzer.
        
        Args:
            github_client: GitHub API client
            comment_formatter: Comment formatter (optional)
        """
        self._github_client = github_client
        self._comment_formatter = comment_formatter or CommentFormatter()
    
    def analyze_pr(
        self,
        repo_full_name: str,
        pr_number: int
    ) -> Dict[str, Any]:
        """
        Analyze a pull request and post results.
        
        Args:
            repo_full_name: Full name of the repository (owner/repo)
            pr_number: Pull request number
            
        Returns:
            Analysis results
        """
        logger.info(f"Analyzing PR {repo_full_name}#{pr_number}")
        
        # Get repository and PR
        repo = self._github_client.get_repository(repo_full_name)
        if not repo:
            logger.error(f"Repository not found: {repo_full_name}")
            return {"status": "error", "message": f"Repository not found: {repo_full_name}"}
        
        pr = self._github_client.get_pull_request(repo, pr_number)
        if not pr:
            logger.error(f"Pull request not found: {pr_number}")
            return {"status": "error", "message": f"Pull request not found: {pr_number}"}
        
        # Fetch PR data
        pr_data = self._fetch_pr_data(repo, pr)
        
        # Analyze PR
        analysis_results = self._analyze_pr_data(pr_data)
        
        # Post results
        posting_results = self._post_analysis_results(repo, pr, analysis_results)
        
        return {
            "status": "success",
            "pr_data": pr_data,
            "analysis_results": analysis_results,
            "posting_results": posting_results
        }
    
    def _fetch_pr_data(
        self,
        repo: Repository,
        pr: PullRequest
    ) -> Dict[str, Any]:
        """
        Fetch data for a pull request.
        
        Args:
            repo: Repository object
            pr: Pull request object
            
        Returns:
            PR data
        """
        logger.info(f"Fetching data for PR #{pr.number}")
        
        # Convert PR to context model
        pr_context = self._github_client.convert_pr_to_context(pr)
        
        # Fetch files
        files_data = self._github_client.get_pull_request_files(pr)
        files = [PRFile.from_github_file(file_data) for file_data in files_data]
        
        # Fetch commits
        commits_data = self._github_client.get_pull_request_commits(pr)
        commits = [PRCommit.from_github_commit(commit_data) for commit_data in commits_data]
        
        # Fetch comments
        comments_data = self._github_client.get_pull_request_comments(pr)
        comments = [PRComment.from_github_comment(comment_data) for comment_data in comments_data]
        
        # Fetch review comments
        review_comments_data = self._github_client.get_pull_request_review_comments(pr)
        review_comments = [PRReviewComment.from_github_review_comment(comment_data) for comment_data in review_comments_data]
        
        return {
            "pr_context": pr_context,
            "files": files,
            "commits": commits,
            "comments": comments,
            "review_comments": review_comments
        }
    
    def _analyze_pr_data(self, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze PR data.
        
        Args:
            pr_data: PR data
            
        Returns:
            Analysis results
        """
        logger.info("Analyzing PR data")
        
        # Extract data
        pr_context = pr_data["pr_context"]
        files = pr_data["files"]
        commits = pr_data["commits"]
        
        # Initialize results
        results = {
            "issues": [],
            "stats": {
                "files_analyzed": len(files),
                "total_issues": 0,
                "issues_by_type": {}
            }
        }
        
        # Analyze each file
        for file in files:
            # Skip deleted files
            if file.status == "removed":
                continue
                
            # Analyze file
            file_issues = self._analyze_file(file)
            
            # Add issues to results
            results["issues"].extend(file_issues)
            
            # Update statistics
            results["stats"]["total_issues"] += len(file_issues)
            
            # Update issues by type
            for issue in file_issues:
                issue_type = issue.get("type", "unknown")
                if issue_type not in results["stats"]["issues_by_type"]:
                    results["stats"]["issues_by_type"][issue_type] = 0
                results["stats"]["issues_by_type"][issue_type] += 1
        
        return results
    
    def _analyze_file(self, file: PRFile) -> List[Dict[str, Any]]:
        """
        Analyze a file.
        
        Args:
            file: File to analyze
            
        Returns:
            List of issues found
        """
        # This is a placeholder for actual file analysis
        # In a real implementation, this would use static analysis tools
        # to analyze the file and find issues
        
        issues = []
        
        # Example: Check file extension
        if file.filename.endswith(".py"):
            # Python file analysis would go here
            pass
        elif file.filename.endswith(".js") or file.filename.endswith(".ts"):
            # JavaScript/TypeScript file analysis would go here
            pass
        
        return issues
    
    def _post_analysis_results(
        self,
        repo: Repository,
        pr: PullRequest,
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post analysis results to GitHub.
        
        Args:
            repo: Repository object
            pr: Pull request object
            analysis_results: Analysis results
            
        Returns:
            Posting results
        """
        logger.info(f"Posting analysis results for PR #{pr.number}")
        
        issues = analysis_results["issues"]
        stats = analysis_results["stats"]
        
        # Skip if no issues found
        if not issues:
            logger.info("No issues found, posting summary comment")
            
            # Post summary comment
            summary_comment = self._comment_formatter.format_summary_comment(
                issues_by_type={},
                files_analyzed=stats["files_analyzed"],
                total_issues=0
            )
            
            comment = self._github_client.create_pull_request_comment(pr, summary_comment)
            
            return {
                "status": "success",
                "message": "No issues found",
                "comments": [{"id": comment.id, "body": summary_comment}]
            }
        
        # Group issues by file
        issues_by_file = self._comment_formatter.group_comments_by_file(issues)
        
        # Post inline comments for each issue
        inline_comments = []
        for file_path, file_issues in issues_by_file.items():
            for issue in file_issues:
                # Get issue details
                issue_type = issue.get("type", "info")
                issue_message = issue.get("message", "")
                issue_suggestion = issue.get("suggestion")
                issue_code = issue.get("code")
                issue_location = issue.get("location", {})
                
                # Get file position
                position = issue_location.get("position")
                if not position:
                    # Skip issues without a position
                    continue
                
                # Get commit ID
                commit_id = issue.get("commit_id")
                if not commit_id:
                    # Use the latest commit
                    commit_id = pr.head.sha
                
                # Format inline comment
                comment_body = self._comment_formatter.format_inline_comment(
                    issue=issue_message,
                    suggestion=issue_suggestion,
                    code_snippet=issue_code,
                    severity=issue_type
                )
                
                # Post comment
                comment = self._github_client.create_pull_request_review_comment(
                    pr=pr,
                    body=comment_body,
                    commit_id=commit_id,
                    path=file_path,
                    position=position
                )
                
                if comment:
                    inline_comments.append({
                        "id": comment.id,
                        "body": comment_body,
                        "path": file_path,
                        "position": position
                    })
        
        # Post summary comment
        summary_comment = self._comment_formatter.format_summary_comment(
            issues_by_type=stats["issues_by_type"],
            files_analyzed=stats["files_analyzed"],
            total_issues=stats["total_issues"]
        )
        
        comment = self._github_client.create_pull_request_comment(pr, summary_comment)
        
        return {
            "status": "success",
            "message": f"Posted {len(inline_comments)} inline comments and 1 summary comment",
            "inline_comments": inline_comments,
            "summary_comment": {"id": comment.id, "body": summary_comment}
        }
    
    @classmethod
    def create_from_env(cls) -> "PRAnalyzer":
        """
        Create a PRAnalyzer instance from environment variables.
        
        Returns:
            PRAnalyzer instance
        """
        # Get GitHub token from environment
        github_auth = GitHubAuth.from_env()
        token = github_auth.token
        
        if not token:
            msg = "GitHub token not found in environment variables"
            raise ValueError(msg)
        
        # Create GitHub client
        github_client = GitHubAPIClient(token=token)
        
        # Create comment formatter
        comment_formatter = CommentFormatter()
        
        return cls(
            github_client=github_client,
            comment_formatter=comment_formatter
        )


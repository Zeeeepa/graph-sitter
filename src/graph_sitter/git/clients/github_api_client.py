"""
GitHub API client for PR static analysis.

This module provides a client for interacting with the GitHub API,
specifically for fetching PR data and posting analysis results.
"""

import time
from typing import Any, Dict, List, Optional, Tuple, Union

from github import Github, GithubException, RateLimitExceededException
from github.ContentFile import ContentFile
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest
from github.PullRequestComment import PullRequestComment
from github.Repository import Repository

from graph_sitter.git.clients.github_client import GithubClient
from graph_sitter.git.models.pull_request_context import PullRequestContext
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class GitHubAPIClient:
    """
    Enhanced GitHub client for PR static analysis.
    
    This class extends the basic GithubClient functionality with methods
    specifically designed for PR static analysis, including fetching PR data,
    handling rate limits, and posting analysis results.
    """
    
    _github_client: GithubClient
    _rate_limit_retries: int = 3
    _rate_limit_delay: int = 5  # seconds
    
    def __init__(
        self, 
        token: str, 
        base_url: str = "https://api.github.com", 
        api_version: str = "2022-11-28"
    ):
        """
        Initialize the GitHub API client.
        
        Args:
            token: GitHub API token
            base_url: GitHub API base URL (for GitHub Enterprise support)
            api_version: GitHub API version to use
        """
        self._github_client = GithubClient(token=token, base_url=base_url)
        # Set API version header
        self._github_client.client._Github__requester._Requester__authorizationHeader = (
            f"Bearer {token}"
        )
        if api_version:
            self._github_client.client._Github__requester._Requester__customHeaders = {
                "Accept": f"application/vnd.github.{api_version}+json",
                "X-GitHub-Api-Version": api_version
            }
    
    def _handle_rate_limit(self, func, *args, **kwargs) -> Any:
        """
        Handle GitHub API rate limiting with exponential backoff.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Result of the function call
            
        Raises:
            RateLimitExceededException: If rate limit is exceeded after retries
        """
        retries = self._rate_limit_retries
        delay = self._rate_limit_delay
        
        while retries > 0:
            try:
                return func(*args, **kwargs)
            except RateLimitExceededException as e:
                reset_time = self._github_client.client.rate_limiting_resettime
                current_time = int(time.time())
                wait_time = max(reset_time - current_time, 0) + 1
                
                if retries == 1 or wait_time > 300:  # 5 minutes max wait
                    logger.error(f"Rate limit exceeded: {e}")
                    raise
                
                logger.warning(f"Rate limit hit, waiting {delay}s before retry. {retries-1} retries left.")
                time.sleep(delay)
                retries -= 1
                delay *= 2  # Exponential backoff
    
    def get_repository(self, repo_full_name: str) -> Optional[Repository]:
        """
        Get a GitHub repository by full name.
        
        Args:
            repo_full_name: Full name of the repository (owner/repo)
            
        Returns:
            Repository object or None if not found
        """
        return self._handle_rate_limit(
            self._github_client.get_repo_by_full_name,
            repo_full_name
        )
    
    def get_pull_request(self, repo: Repository, pr_number: int) -> Optional[PullRequest]:
        """
        Get a pull request by number.
        
        Args:
            repo: Repository object
            pr_number: Pull request number
            
        Returns:
            PullRequest object or None if not found
        """
        try:
            return self._handle_rate_limit(repo.get_pull, pr_number)
        except GithubException as e:
            logger.error(f"Error getting PR {pr_number}: {e}")
            return None
    
    def get_pull_request_files(self, pr: PullRequest) -> List[Dict[str, Any]]:
        """
        Get files changed in a pull request.
        
        Args:
            pr: Pull request object
            
        Returns:
            List of file objects with filename, status, additions, deletions, etc.
        """
        files = self._handle_rate_limit(pr.get_files)
        return [
            {
                "filename": f.filename,
                "status": f.status,
                "additions": f.additions,
                "deletions": f.deletions,
                "changes": f.changes,
                "patch": f.patch,
                "raw_url": f.raw_url,
                "contents_url": f.contents_url,
                "sha": f.sha
            }
            for f in files
        ]
    
    def get_pull_request_commits(self, pr: PullRequest) -> List[Dict[str, Any]]:
        """
        Get commits in a pull request.
        
        Args:
            pr: Pull request object
            
        Returns:
            List of commit objects with sha, message, author, etc.
        """
        commits = self._handle_rate_limit(pr.get_commits)
        return [
            {
                "sha": c.sha,
                "message": c.commit.message,
                "author": {
                    "name": c.commit.author.name,
                    "email": c.commit.author.email,
                    "date": c.commit.author.date.isoformat() if c.commit.author.date else None
                },
                "committer": {
                    "name": c.commit.committer.name,
                    "email": c.commit.committer.email,
                    "date": c.commit.committer.date.isoformat() if c.commit.committer.date else None
                },
                "url": c.url,
                "html_url": c.html_url
            }
            for c in commits
        ]
    
    def get_pull_request_comments(self, pr: PullRequest) -> List[Dict[str, Any]]:
        """
        Get comments on a pull request.
        
        Args:
            pr: Pull request object
            
        Returns:
            List of comment objects with body, user, created_at, etc.
        """
        comments = self._handle_rate_limit(pr.get_comments)
        return [
            {
                "id": c.id,
                "body": c.body,
                "user": {
                    "login": c.user.login,
                    "id": c.user.id,
                    "type": c.user.type
                },
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None
            }
            for c in comments
        ]
    
    def get_pull_request_review_comments(self, pr: PullRequest) -> List[Dict[str, Any]]:
        """
        Get review comments on a pull request (comments on specific lines).
        
        Args:
            pr: Pull request object
            
        Returns:
            List of review comment objects with body, user, path, position, etc.
        """
        review_comments = self._handle_rate_limit(pr.get_review_comments)
        return [
            {
                "id": c.id,
                "body": c.body,
                "user": {
                    "login": c.user.login,
                    "id": c.user.id,
                    "type": c.user.type
                },
                "path": c.path,
                "position": c.position,
                "original_position": c.original_position,
                "commit_id": c.commit_id,
                "original_commit_id": c.original_commit_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None
            }
            for c in review_comments
        ]
    
    def create_pull_request_comment(
        self, 
        pr: PullRequest, 
        body: str
    ) -> Optional[PullRequestComment]:
        """
        Create a general comment on a pull request.
        
        Args:
            pr: Pull request object
            body: Comment text
            
        Returns:
            Created comment object or None if failed
        """
        try:
            return self._handle_rate_limit(pr.create_issue_comment, body)
        except GithubException as e:
            logger.error(f"Error creating PR comment: {e}")
            return None
    
    def create_pull_request_review_comment(
        self,
        pr: PullRequest,
        body: str,
        commit_id: str,
        path: str,
        position: int
    ) -> Optional[PullRequestComment]:
        """
        Create a review comment on a specific line in a pull request.
        
        Args:
            pr: Pull request object
            body: Comment text
            commit_id: Commit SHA
            path: File path
            position: Line position in the diff
            
        Returns:
            Created comment object or None if failed
        """
        try:
            return self._handle_rate_limit(
                pr.create_review_comment,
                body=body,
                commit_id=commit_id,
                path=path,
                position=position
            )
        except GithubException as e:
            logger.error(f"Error creating PR review comment: {e}")
            return None
    
    def get_file_content(
        self, 
        repo: Repository, 
        path: str, 
        ref: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the content of a file in a repository.
        
        Args:
            repo: Repository object
            path: File path
            ref: Git reference (branch, tag, commit)
            
        Returns:
            File content as string or None if not found
        """
        try:
            content_file = self._handle_rate_limit(
                repo.get_contents,
                path=path,
                ref=ref
            )
            
            # Handle directory vs file
            if isinstance(content_file, list):
                logger.warning(f"Path {path} is a directory, not a file")
                return None
                
            return content_file.decoded_content.decode('utf-8')
        except GithubException as e:
            logger.error(f"Error getting file content for {path}: {e}")
            return None
    
    def convert_pr_to_context(self, pr: PullRequest) -> PullRequestContext:
        """
        Convert a GitHub PullRequest object to a PullRequestContext model.
        
        Args:
            pr: GitHub PullRequest object
            
        Returns:
            PullRequestContext model
        """
        from graph_sitter.git.models.github_named_user_context import GithubNamedUserContext
        from graph_sitter.git.models.pr_part_context import PRPartContext
        
        return PullRequestContext(
            id=pr.id,
            url=pr.url,
            html_url=pr.html_url,
            number=pr.number,
            state=pr.state,
            title=pr.title,
            user=GithubNamedUserContext(
                login=pr.user.login,
                email=pr.user.email
            ),
            draft=pr.draft,
            head=PRPartContext(
                ref=pr.head.ref,
                sha=pr.head.sha
            ),
            base=PRPartContext(
                ref=pr.base.ref,
                sha=pr.base.sha
            ),
            body=pr.body,
            merged=pr.merged,
            merged_by={} if not pr.merged_by else {
                "login": pr.merged_by.login,
                "id": pr.merged_by.id
            },
            additions=pr.additions,
            deletions=pr.deletions,
            changed_files=pr.changed_files,
            webhook_data=None
        )


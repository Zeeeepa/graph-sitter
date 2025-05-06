from typing import List, Dict, Optional, Any, Union
import os
import logging
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from github.PullRequestFile import PullRequestFile
from github.Commit import Commit
from github.PullRequestReview import PullRequestReview
from github.GithubException import GithubException

logger = logging.getLogger(__name__)

class GitHubClient:
    """
    A client for interacting with the GitHub API for PR static analysis.
    Adapted from graph-sitter's GitHubClient class.
    """

    def __init__(self, access_token: str):
        """
        Initialize the GitHub client.

        Args:
            access_token: GitHub access token for authentication
        """
        self.client = Github(access_token)

    def get_repo(self, repo_full_name: str) -> Optional[Repository]:
        """
        Get a GitHub repository by its full name.

        Args:
            repo_full_name: Full name of the repository (owner/repo)

        Returns:
            Repository: The repository object, or None if not found
        """
        try:
            return self.client.get_repo(repo_full_name)
        except GithubException as e:
            logger.error(f"Error getting repository {repo_full_name}: {e}")
            return None

    def get_pr(self, repo: Union[str, Repository], pr_number: int) -> Optional[PullRequest]:
        """
        Get a specific PR.

        Args:
            repo: Repository object or full name string
            pr_number: Number of the PR to get

        Returns:
            PullRequest: The PR object, or None if not found
        """
        try:
            if isinstance(repo, str):
                repo = self.get_repo(repo)
                if not repo:
                    return None
            
            return repo.get_pull(pr_number)
        except GithubException as e:
            logger.error(f"Error getting PR #{pr_number}: {e}")
            return None

    def get_pr_files(self, repo: Union[str, Repository], pr_number: int) -> List[PullRequestFile]:
        """
        Get files changed in a PR.

        Args:
            repo: Repository object or full name string
            pr_number: Number of the PR

        Returns:
            List[PullRequestFile]: List of files changed in the PR
        """
        pr = self.get_pr(repo, pr_number)
        if not pr:
            return []
        
        try:
            return list(pr.get_files())
        except GithubException as e:
            logger.error(f"Error getting files for PR #{pr_number}: {e}")
            return []

    def get_pr_commits(self, repo: Union[str, Repository], pr_number: int) -> List[Commit]:
        """
        Get commits in a PR.

        Args:
            repo: Repository object or full name string
            pr_number: Number of the PR

        Returns:
            List[Commit]: List of commits in the PR
        """
        pr = self.get_pr(repo, pr_number)
        if not pr:
            return []
        
        try:
            return list(pr.get_commits())
        except GithubException as e:
            logger.error(f"Error getting commits for PR #{pr_number}: {e}")
            return []

    def get_pr_reviews(self, repo: Union[str, Repository], pr_number: int) -> List[PullRequestReview]:
        """
        Get reviews for a PR.

        Args:
            repo: Repository object or full name string
            pr_number: Number of the PR

        Returns:
            List[PullRequestReview]: List of reviews for the PR
        """
        pr = self.get_pr(repo, pr_number)
        if not pr:
            return []
        
        try:
            return list(pr.get_reviews())
        except GithubException as e:
            logger.error(f"Error getting reviews for PR #{pr_number}: {e}")
            return []

    def create_pr_comment(self, repo: Union[str, Repository], pr_number: int, body: str) -> bool:
        """
        Create a general comment on a PR.

        Args:
            repo: Repository object or full name string
            pr_number: Number of the PR
            body: Text of the comment

        Returns:
            bool: True if successful, False otherwise
        """
        pr = self.get_pr(repo, pr_number)
        if not pr:
            return False
        
        try:
            pr.create_issue_comment(body)
            return True
        except GithubException as e:
            logger.error(f"Error creating comment on PR #{pr_number}: {e}")
            return False

    def create_pr_review_comment(
        self,
        repo: Union[str, Repository],
        pr_number: int,
        body: str,
        commit_sha: str,
        path: str,
        line: int,
        position: Optional[int] = None
    ) -> bool:
        """
        Create an inline comment on a PR.

        Args:
            repo: Repository object or full name string
            pr_number: Number of the PR
            body: Text of the comment
            commit_sha: SHA of the commit to comment on
            path: Path to the file to comment on
            line: Line number to comment on
            position: Position in the diff to comment on (optional)

        Returns:
            bool: True if successful, False otherwise
        """
        pr = self.get_pr(repo, pr_number)
        if not pr:
            return False
        
        try:
            if position is not None:
                pr.create_review_comment(body, commit_sha, path, position)
            else:
                # If position is not provided, use the line number
                pr.create_review_comment(body, commit_sha, path, line)
            return True
        except GithubException as e:
            logger.error(f"Error creating review comment on PR #{pr_number}: {e}")
            return False

    def create_pr_review(
        self,
        repo: Union[str, Repository],
        pr_number: int,
        body: str,
        event: str = "COMMENT"
    ) -> bool:
        """
        Create a review on a PR.

        Args:
            repo: Repository object or full name string
            pr_number: Number of the PR
            body: Text of the review
            event: Review event type (COMMENT, APPROVE, REQUEST_CHANGES)

        Returns:
            bool: True if successful, False otherwise
        """
        pr = self.get_pr(repo, pr_number)
        if not pr:
            return False
        
        try:
            pr.create_review(body=body, event=event)
            return True
        except GithubException as e:
            logger.error(f"Error creating review on PR #{pr_number}: {e}")
            return False

    def create_status(
        self,
        repo: Union[str, Repository],
        commit_sha: str,
        state: str,
        description: str,
        context: str
    ) -> bool:
        """
        Create a status for a commit.

        Args:
            repo: Repository object or full name string
            commit_sha: SHA of the commit
            state: Status state (success, error, failure, pending)
            description: Description of the status
            context: Context for the status

        Returns:
            bool: True if successful, False otherwise
        """
        if isinstance(repo, str):
            repo = self.get_repo(repo)
            if not repo:
                return False
        
        try:
            repo.get_commit(commit_sha).create_status(
                state=state,
                description=description,
                context=context
            )
            return True
        except GithubException as e:
            logger.error(f"Error creating status for commit {commit_sha}: {e}")
            return False

    def create_check_run(
        self,
        repo: Union[str, Repository],
        commit_sha: str,
        name: str,
        status: str,
        conclusion: Optional[str] = None,
        output: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Create a check run for a commit.

        Args:
            repo: Repository object or full name string
            commit_sha: SHA of the commit
            name: Name of the check run
            status: Status of the check run (queued, in_progress, completed)
            conclusion: Conclusion of the check run (success, failure, neutral, etc.)
            output: Output for the check run (title, summary, text)

        Returns:
            bool: True if successful, False otherwise
        """
        if isinstance(repo, str):
            repo = self.get_repo(repo)
            if not repo:
                return False
        
        try:
            check_run_params = {
                "name": name,
                "head_sha": commit_sha,
                "status": status
            }
            
            if conclusion and status == "completed":
                check_run_params["conclusion"] = conclusion
            
            if output:
                check_run_params["output"] = output
            
            repo.create_check_run(**check_run_params)
            return True
        except GithubException as e:
            logger.error(f"Error creating check run for commit {commit_sha}: {e}")
            return False


"""
GitHub client for PR static analysis.
"""
from typing import List, Optional

from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository

from graph_sitter.git.clients.github_client import GithubClient
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class PRGitHubClient(GithubClient):
    """Extended GitHub client for PR static analysis."""

    def __init__(self, token: str | None = None, base_url: str = None):
        """Initialize the PR GitHub client.

        Args:
            token: GitHub API token
            base_url: GitHub API base URL
        """
        super().__init__(token, base_url)

    def get_pr(self, pr_number: int, repository: str) -> Optional[PullRequest]:
        """Get a PR by number and repository.

        Args:
            pr_number: PR number
            repository: Repository full name (e.g., "owner/repo")

        Returns:
            PullRequest object or None if not found
        """
        repo = self.get_repo_by_full_name(repository)
        if not repo:
            logger.error(f"Repository {repository} not found")
            return None

        try:
            return repo.get_pull(pr_number)
        except Exception as e:
            logger.error(f"Error getting PR {pr_number} from {repository}: {e}")
            return None

    def get_pr_files(self, pr: PullRequest) -> List[dict]:
        """Get files changed in a PR.

        Args:
            pr: PullRequest object

        Returns:
            List of file changes
        """
        try:
            return list(pr.get_files())
        except Exception as e:
            logger.error(f"Error getting files for PR {pr.number}: {e}")
            return []

    def get_pr_commits(self, pr: PullRequest) -> List[dict]:
        """Get commits in a PR.

        Args:
            pr: PullRequest object

        Returns:
            List of commits
        """
        try:
            return list(pr.get_commits())
        except Exception as e:
            logger.error(f"Error getting commits for PR {pr.number}: {e}")
            return []

    def post_comment(self, pr: PullRequest, comment: str) -> bool:
        """Post a comment on a PR.

        Args:
            pr: PullRequest object
            comment: Comment text

        Returns:
            True if successful, False otherwise
        """
        try:
            pr.create_issue_comment(comment)
            return True
        except Exception as e:
            logger.error(f"Error posting comment on PR {pr.number}: {e}")
            return False

    def post_review_comment(
        self, pr: PullRequest, comment: str, commit_id: str, path: str, position: int
    ) -> bool:
        """Post a review comment on a specific line in a PR.

        Args:
            pr: PullRequest object
            comment: Comment text
            commit_id: Commit ID
            path: File path
            position: Line position

        Returns:
            True if successful, False otherwise
        """
        try:
            pr.create_review_comment(comment, commit_id, path, position)
            return True
        except Exception as e:
            logger.error(f"Error posting review comment on PR {pr.number}: {e}")
            return False

    def get_pr_diff(self, pr: PullRequest) -> str:
        """Get the diff for a PR.

        Args:
            pr: PullRequest object

        Returns:
            PR diff as a string
        """
        try:
            return pr.get_diff()
        except Exception as e:
            logger.error(f"Error getting diff for PR {pr.number}: {e}")
            return ""

    def get_repo(self, repository: str) -> Optional[Repository]:
        """Get a repository by full name.

        Args:
            repository: Repository full name (e.g., "owner/repo")

        Returns:
            Repository object or None if not found
        """
        return self.get_repo_by_full_name(repository)


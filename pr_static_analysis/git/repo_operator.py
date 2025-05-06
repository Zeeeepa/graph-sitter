import os
import fnmatch
from typing import List, Dict, Optional, Tuple, Any
from git import Repo as GitCLI
from git import Commit as GitCommit
from git import GitCommandError, InvalidGitRepositoryError

class RepoOperator:
    """
    A class for managing Git repository operations for PR static analysis.
    Adapted from graph-sitter's RepoOperator class.
    """

    def __init__(
        self,
        repo_path: str,
        access_token: Optional[str] = None,
        clone_url: Optional[str] = None,
    ) -> None:
        """
        Initialize the RepoOperator.

        Args:
            repo_path: Path to the local repository
            access_token: GitHub access token for authenticated operations
            clone_url: URL to clone the repository from
        """
        self.repo_path = repo_path
        self.access_token = access_token
        self.clone_url = clone_url
        
        # Initialize repository if it exists
        if os.path.exists(repo_path):
            try:
                self.git_cli = GitCLI(repo_path)
            except InvalidGitRepositoryError:
                self.git_cli = None
        else:
            self.git_cli = None

    def clone_repo(self, repo_url: str, shallow: bool = True) -> bool:
        """
        Clone a repository.

        Args:
            repo_url: URL of the repository to clone
            shallow: Whether to perform a shallow clone (depth=1)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            os.makedirs(os.path.dirname(self.repo_path), exist_ok=True)
            
            # Add access token to URL if provided
            if self.access_token and repo_url.startswith("https://"):
                auth_url = repo_url.replace("https://", f"https://{self.access_token}@")
            else:
                auth_url = repo_url
            
            # Clone the repository
            if shallow:
                self.git_cli = GitCLI.clone_from(auth_url, self.repo_path, depth=1)
            else:
                self.git_cli = GitCLI.clone_from(auth_url, self.repo_path)
            
            return True
        except GitCommandError as e:
            print(f"Error cloning repository: {e}")
            return False

    def checkout_branch(self, branch_name: str) -> bool:
        """
        Checkout a branch.

        Args:
            branch_name: Name of the branch to checkout

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.git_cli:
            return False
        
        try:
            self.git_cli.git.checkout(branch_name)
            return True
        except GitCommandError as e:
            print(f"Error checking out branch {branch_name}: {e}")
            return False

    def checkout_commit(self, commit_sha: str) -> bool:
        """
        Checkout a specific commit.

        Args:
            commit_sha: SHA of the commit to checkout

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.git_cli:
            return False
        
        try:
            self.git_cli.git.checkout(commit_sha)
            return True
        except GitCommandError as e:
            print(f"Error checking out commit {commit_sha}: {e}")
            return False

    def get_file_content(self, file_path: str, ref: Optional[str] = None) -> Optional[str]:
        """
        Get content of a file at a specific ref.

        Args:
            file_path: Path to the file
            ref: Reference (branch, tag, or commit) to get the file from

        Returns:
            str: Content of the file, or None if the file doesn't exist
        """
        if not self.git_cli:
            return None
        
        try:
            if ref:
                return self.git_cli.git.show(f"{ref}:{file_path}")
            else:
                full_path = os.path.join(self.repo_path, file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        return f.read()
                return None
        except GitCommandError as e:
            print(f"Error getting file content for {file_path} at {ref}: {e}")
            return None

    def get_changed_files(self, base_ref: str, head_ref: str) -> List[str]:
        """
        Get files changed between two refs.

        Args:
            base_ref: Base reference (branch, tag, or commit)
            head_ref: Head reference (branch, tag, or commit)

        Returns:
            List[str]: List of changed file paths
        """
        if not self.git_cli:
            return []
        
        try:
            diff_output = self.git_cli.git.diff("--name-only", base_ref, head_ref)
            return diff_output.splitlines() if diff_output else []
        except GitCommandError as e:
            print(f"Error getting changed files between {base_ref} and {head_ref}: {e}")
            return []

    def get_diff(self, file_path: str, base_ref: str, head_ref: str) -> Optional[str]:
        """
        Get diff for a specific file.

        Args:
            file_path: Path to the file
            base_ref: Base reference (branch, tag, or commit)
            head_ref: Head reference (branch, tag, or commit)

        Returns:
            str: Diff of the file, or None if there's an error
        """
        if not self.git_cli:
            return None
        
        try:
            return self.git_cli.git.diff(base_ref, head_ref, "--", file_path)
        except GitCommandError as e:
            print(f"Error getting diff for {file_path} between {base_ref} and {head_ref}: {e}")
            return None

    def get_commit(self, commit_sha: str) -> Optional[GitCommit]:
        """
        Get a specific commit.

        Args:
            commit_sha: SHA of the commit to get

        Returns:
            GitCommit: The commit object, or None if there's an error
        """
        if not self.git_cli:
            return None
        
        try:
            return self.git_cli.commit(commit_sha)
        except GitCommandError as e:
            print(f"Error getting commit {commit_sha}: {e}")
            return None

    def get_commit_message(self, commit_sha: str) -> Optional[str]:
        """
        Get the message of a commit.

        Args:
            commit_sha: SHA of the commit

        Returns:
            str: Commit message, or None if there's an error
        """
        commit = self.get_commit(commit_sha)
        return commit.message if commit else None

    def get_commit_author(self, commit_sha: str) -> Optional[Dict[str, str]]:
        """
        Get the author of a commit.

        Args:
            commit_sha: SHA of the commit

        Returns:
            Dict[str, str]: Author information (name, email), or None if there's an error
        """
        commit = self.get_commit(commit_sha)
        if not commit:
            return None
        
        return {
            "name": commit.author.name,
            "email": commit.author.email
        }

    def get_default_branch(self) -> Optional[str]:
        """
        Get the default branch of the repository.

        Returns:
            str: Name of the default branch, or None if there's an error
        """
        if not self.git_cli:
            return None
        
        try:
            # Try to get the default branch from the origin remote
            for remote in self.git_cli.remotes:
                if remote.name == "origin":
                    for ref in remote.refs:
                        if ref.remote_head == "HEAD":
                            return ref.reference.name.replace("origin/", "")
            
            # Fallback to the active branch
            return self.git_cli.active_branch.name
        except GitCommandError as e:
            print(f"Error getting default branch: {e}")
            return None

    def find_files(self, pattern: str) -> List[str]:
        """
        Find files matching a pattern in the repository.

        Args:
            pattern: Glob pattern to match files

        Returns:
            List[str]: List of matching file paths
        """
        if not self.git_cli:
            return []
        
        result = []
        for root, _, files in os.walk(self.repo_path):
            for file in files:
                if fnmatch.fnmatch(file, pattern):
                    rel_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                    result.append(rel_path)
        
        return result


"""
GitHub authentication and authorization utilities.

This module provides utilities for authenticating with GitHub
and managing credentials.
"""

import base64
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import jwt
import requests

from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class GitHubAuth:
    """
    GitHub authentication manager.
    
    This class provides methods for authenticating with GitHub
    using different authentication methods (token, OAuth, GitHub App).
    """
    
    _token: Optional[str] = None
    _token_expiry: Optional[datetime] = None
    _app_id: Optional[str] = None
    _app_private_key: Optional[str] = None
    _installation_id: Optional[str] = None
    
    def __init__(
        self,
        token: Optional[str] = None,
        app_id: Optional[str] = None,
        app_private_key: Optional[str] = None,
        installation_id: Optional[str] = None
    ):
        """
        Initialize the GitHub authentication manager.
        
        Args:
            token: GitHub personal access token or OAuth token
            app_id: GitHub App ID
            app_private_key: GitHub App private key
            installation_id: GitHub App installation ID
        """
        self._token = token
        self._app_id = app_id
        self._app_private_key = app_private_key
        self._installation_id = installation_id
    
    @property
    def token(self) -> Optional[str]:
        """
        Get the current authentication token.
        
        If using GitHub App authentication and the token is expired,
        a new token will be generated automatically.
        
        Returns:
            Authentication token or None if not authenticated
        """
        # If using a static token, return it
        if self._token and not self._app_id:
            return self._token
        
        # If using GitHub App authentication, check if token is expired
        if self._app_id and self._app_private_key and self._installation_id:
            if not self._token or not self._token_expiry or datetime.now() >= self._token_expiry:
                # Generate a new token
                self._token, self._token_expiry = self._generate_installation_token()
            
            return self._token
        
        return None
    
    def _generate_jwt(self) -> str:
        """
        Generate a JWT for GitHub App authentication.
        
        Returns:
            JWT token
        
        Raises:
            ValueError: If app_id or app_private_key is not set
        """
        if not self._app_id or not self._app_private_key:
            msg = "GitHub App ID and private key are required for JWT generation"
            raise ValueError(msg)
        
        # Prepare JWT payload
        now = int(time.time())
        payload = {
            "iat": now,  # Issued at time
            "exp": now + 600,  # Expires in 10 minutes
            "iss": self._app_id  # GitHub App ID
        }
        
        # Generate JWT
        token = jwt.encode(
            payload,
            self._app_private_key,
            algorithm="RS256"
        )
        
        return token
    
    def _generate_installation_token(self) -> Tuple[str, datetime]:
        """
        Generate an installation token for GitHub App authentication.
        
        Returns:
            Tuple of (token, expiry datetime)
        
        Raises:
            ValueError: If installation_id is not set
            RuntimeError: If token generation fails
        """
        if not self._installation_id:
            msg = "GitHub App installation ID is required for token generation"
            raise ValueError(msg)
        
        # Generate JWT for API authentication
        jwt_token = self._generate_jwt()
        
        # Request installation token
        url = f"https://api.github.com/app/installations/{self._installation_id}/access_tokens"
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.post(url, headers=headers)
        
        if response.status_code != 201:
            msg = f"Failed to generate installation token: {response.status_code} {response.text}"
            raise RuntimeError(msg)
        
        data = response.json()
        token = data.get("token")
        expires_at = data.get("expires_at")
        
        if not token or not expires_at:
            msg = "Invalid response from GitHub API"
            raise RuntimeError(msg)
        
        # Parse expiry time
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        
        # Add a small buffer to avoid using a token that's about to expire
        expiry = expiry - timedelta(minutes=5)
        
        return token, expiry
    
    @classmethod
    def from_env(cls) -> "GitHubAuth":
        """
        Create a GitHubAuth instance from environment variables.
        
        The following environment variables are used:
        - GITHUB_TOKEN: GitHub personal access token or OAuth token
        - GITHUB_APP_ID: GitHub App ID
        - GITHUB_APP_PRIVATE_KEY: GitHub App private key (base64 encoded)
        - GITHUB_APP_INSTALLATION_ID: GitHub App installation ID
        
        Returns:
            GitHubAuth instance
        """
        token = os.environ.get("GITHUB_TOKEN")
        app_id = os.environ.get("GITHUB_APP_ID")
        app_private_key_base64 = os.environ.get("GITHUB_APP_PRIVATE_KEY")
        installation_id = os.environ.get("GITHUB_APP_INSTALLATION_ID")
        
        app_private_key = None
        if app_private_key_base64:
            try:
                app_private_key = base64.b64decode(app_private_key_base64).decode("utf-8")
            except Exception as e:
                logger.error(f"Failed to decode GitHub App private key: {e}")
        
        return cls(
            token=token,
            app_id=app_id,
            app_private_key=app_private_key,
            installation_id=installation_id
        )
    
    @classmethod
    def from_file(cls, file_path: str) -> "GitHubAuth":
        """
        Create a GitHubAuth instance from a JSON file.
        
        The file should contain a JSON object with the following keys:
        - token: GitHub personal access token or OAuth token
        - app_id: GitHub App ID
        - app_private_key: GitHub App private key
        - installation_id: GitHub App installation ID
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            GitHubAuth instance
        """
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            return cls(
                token=data.get("token"),
                app_id=data.get("app_id"),
                app_private_key=data.get("app_private_key"),
                installation_id=data.get("installation_id")
            )
        except Exception as e:
            logger.error(f"Failed to load GitHub auth from file: {e}")
            return cls()


class GitHubPermissions:
    """
    GitHub permissions checker.
    
    This class provides methods for checking if a user or token
    has the required permissions for certain operations.
    """
    
    @staticmethod
    def check_repo_permission(
        token: str,
        repo_owner: str,
        repo_name: str,
        permission: str = "push"
    ) -> bool:
        """
        Check if the token has the specified permission on a repository.
        
        Args:
            token: GitHub token
            repo_owner: Repository owner
            repo_name: Repository name
            permission: Permission to check (pull, push, admin)
            
        Returns:
            True if the token has the permission, False otherwise
        """
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.warning(f"Failed to check repo permission: {response.status_code} {response.text}")
            return False
        
        data = response.json()
        
        # Check if the repo is private and the token has the required permission
        if data.get("private", False):
            # For private repos, we need to check the specific permission
            permissions = data.get("permissions", {})
            
            if permission == "pull":
                return permissions.get("pull", False)
            elif permission == "push":
                return permissions.get("push", False)
            elif permission == "admin":
                return permissions.get("admin", False)
            else:
                return False
        else:
            # For public repos, anyone has pull access
            if permission == "pull":
                return True
            
            # For push and admin, we still need to check permissions
            permissions = data.get("permissions", {})
            
            if permission == "push":
                return permissions.get("push", False)
            elif permission == "admin":
                return permissions.get("admin", False)
            else:
                return False
    
    @staticmethod
    def check_user_permission(
        token: str,
        repo_owner: str,
        repo_name: str,
        username: str
    ) -> Optional[str]:
        """
        Check a user's permission level on a repository.
        
        Args:
            token: GitHub token
            repo_owner: Repository owner
            repo_name: Repository name
            username: GitHub username
            
        Returns:
            Permission level (admin, write, read, none) or None if check failed
        """
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/collaborators/{username}/permission"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            logger.warning(f"Failed to check user permission: {response.status_code} {response.text}")
            return None
        
        data = response.json()
        return data.get("permission")


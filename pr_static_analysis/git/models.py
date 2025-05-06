from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

class GitHubNamedUserContext(BaseModel):
    """
    Represents a GitHub user.
    Adapted from graph-sitter's GitHubNamedUserContext.
    """
    login: str
    name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    
    @classmethod
    def from_github_user(cls, user: Dict[str, Any]) -> "GitHubNamedUserContext":
        """
        Create a GitHubNamedUserContext from a GitHub API user object.
        
        Args:
            user: GitHub API user object
            
        Returns:
            GitHubNamedUserContext: User context object
        """
        return cls(
            login=user.get("login"),
            name=user.get("name"),
            email=user.get("email"),
            avatar_url=user.get("avatar_url")
        )
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "GitHubNamedUserContext":
        """
        Create a GitHubNamedUserContext from a webhook payload.
        
        Args:
            payload: Webhook payload containing user data
            
        Returns:
            GitHubNamedUserContext: User context object
        """
        return cls(
            login=payload.get("login"),
            name=payload.get("name"),
            email=payload.get("email"),
            avatar_url=payload.get("avatar_url")
        )

class PRPartContext(BaseModel):
    """
    Represents a part of a PR (base or head).
    Adapted from graph-sitter's PRPartContext.
    """
    ref: str
    sha: str
    repo_name: Optional[str] = None
    repo_full_name: Optional[str] = None
    repo_url: Optional[str] = None
    
    @classmethod
    def from_github_pr_part(cls, part: Dict[str, Any]) -> "PRPartContext":
        """
        Create a PRPartContext from a GitHub API PR part object.
        
        Args:
            part: GitHub API PR part object (base or head)
            
        Returns:
            PRPartContext: PR part context object
        """
        repo = part.get("repo", {})
        return cls(
            ref=part.get("ref"),
            sha=part.get("sha"),
            repo_name=repo.get("name"),
            repo_full_name=repo.get("full_name"),
            repo_url=repo.get("html_url")
        )
    
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "PRPartContext":
        """
        Create a PRPartContext from a webhook payload.
        
        Args:
            payload: Webhook payload containing PR part data
            
        Returns:
            PRPartContext: PR part context object
        """
        repo = payload.get("repo", {})
        return cls(
            ref=payload.get("ref"),
            sha=payload.get("sha"),
            repo_name=repo.get("name"),
            repo_full_name=repo.get("full_name"),
            repo_url=repo.get("html_url")
        )

class PullRequestContext(BaseModel):
    """
    Represents a GitHub pull request.
    Adapted from graph-sitter's PullRequestContext.
    """
    id: int
    url: str
    html_url: str
    number: int
    state: str
    title: str
    user: GitHubNamedUserContext
    draft: bool
    head: PRPartContext
    base: PRPartContext
    body: Optional[str] = None
    merged: Optional[bool] = None
    merged_by: Optional[Dict[str, Any]] = None
    additions: Optional[int] = None
    deletions: Optional[int] = None
    changed_files: Optional[int] = None
    labels: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    @classmethod
    def from_github_pr(cls, pr: Dict[str, Any]) -> "PullRequestContext":
        """
        Create a PullRequestContext from a GitHub API PR object.
        
        Args:
            pr: GitHub API PR object
            
        Returns:
            PullRequestContext: PR context object
        """
        return cls(
            id=pr.get("id"),
            url=pr.get("url"),
            html_url=pr.get("html_url"),
            number=pr.get("number"),
            state=pr.get("state"),
            title=pr.get("title"),
            user=GitHubNamedUserContext.from_github_user(pr.get("user", {})),
            body=pr.get("body"),
            draft=pr.get("draft", False),
            head=PRPartContext.from_github_pr_part(pr.get("head", {})),
            base=PRPartContext.from_github_pr_part(pr.get("base", {})),
            merged=pr.get("merged"),
            merged_by=pr.get("merged_by"),
            additions=pr.get("additions"),
            deletions=pr.get("deletions"),
            changed_files=pr.get("changed_files"),
            labels=pr.get("labels"),
            created_at=pr.get("created_at"),
            updated_at=pr.get("updated_at")
        )
    
    @classmethod
    def from_payload(cls, webhook_payload: Dict[str, Any]) -> "PullRequestContext":
        """
        Create a PullRequestContext from a webhook payload.
        
        Args:
            webhook_payload: Webhook payload containing PR data
            
        Returns:
            PullRequestContext: PR context object
        """
        pr_data = webhook_payload.get("pull_request", {})
        return cls(
            id=pr_data.get("id"),
            url=pr_data.get("url"),
            html_url=pr_data.get("html_url"),
            number=pr_data.get("number"),
            state=pr_data.get("state"),
            title=pr_data.get("title"),
            user=GitHubNamedUserContext.from_payload(pr_data.get("user", {})),
            body=pr_data.get("body"),
            draft=pr_data.get("draft", False),
            head=PRPartContext.from_payload(pr_data.get("head", {})),
            base=PRPartContext.from_payload(pr_data.get("base", {})),
            merged=pr_data.get("merged"),
            merged_by=pr_data.get("merged_by"),
            additions=pr_data.get("additions"),
            deletions=pr_data.get("deletions"),
            changed_files=pr_data.get("changed_files"),
            labels=pr_data.get("labels"),
            created_at=pr_data.get("created_at"),
            updated_at=pr_data.get("updated_at")
        )


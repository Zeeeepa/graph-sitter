"""
Models for representing PR commit data.
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field


class CommitAuthor(BaseModel):
    """
    Represents a commit author or committer.
    """
    
    name: str
    email: Optional[str] = None
    date: Optional[datetime] = None
    
    @classmethod
    def from_dict(cls, data: Dict) -> "CommitAuthor":
        """
        Create a CommitAuthor from dictionary data.
        
        Args:
            data: Author/committer data
            
        Returns:
            CommitAuthor instance
        """
        date_str = data.get("date")
        date = None
        if date_str:
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
                
        return cls(
            name=data.get("name", ""),
            email=data.get("email"),
            date=date
        )


class PRCommit(BaseModel):
    """
    Represents a commit in a GitHub pull request.
    """
    
    sha: str
    message: str
    author: CommitAuthor
    committer: CommitAuthor
    url: Optional[str] = None
    html_url: Optional[str] = None
    
    @classmethod
    def from_github_commit(cls, commit_data: Dict) -> "PRCommit":
        """
        Create a PRCommit from GitHub API commit data.
        
        Args:
            commit_data: Commit data from GitHub API
            
        Returns:
            PRCommit instance
        """
        return cls(
            sha=commit_data.get("sha", ""),
            message=commit_data.get("message", ""),
            author=CommitAuthor.from_dict(commit_data.get("author", {})),
            committer=CommitAuthor.from_dict(commit_data.get("committer", {})),
            url=commit_data.get("url"),
            html_url=commit_data.get("html_url")
        )
    
    @classmethod
    def from_webhook_payload(cls, commit_data: Dict) -> "PRCommit":
        """
        Create a PRCommit from webhook payload commit data.
        
        Args:
            commit_data: Commit data from webhook payload
            
        Returns:
            PRCommit instance
        """
        return cls(
            sha=commit_data.get("id", ""),
            message=commit_data.get("message", ""),
            author=CommitAuthor.from_dict(commit_data.get("author", {})),
            committer=CommitAuthor.from_dict(commit_data.get("committer", {})),
            url=commit_data.get("url"),
            html_url=commit_data.get("html_url")
        )


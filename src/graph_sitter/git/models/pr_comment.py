"""
Models for representing PR comment data.
"""

from datetime import datetime
from typing import Dict, Optional

from pydantic import BaseModel, Field

from graph_sitter.git.models.github_named_user_context import GithubNamedUserContext


class PRComment(BaseModel):
    """
    Represents a comment on a GitHub pull request.
    """
    
    id: int
    body: str
    user: GithubNamedUserContext
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_github_comment(cls, comment_data: Dict) -> "PRComment":
        """
        Create a PRComment from GitHub API comment data.
        
        Args:
            comment_data: Comment data from GitHub API
            
        Returns:
            PRComment instance
        """
        user_data = comment_data.get("user", {})
        user = GithubNamedUserContext(
            login=user_data.get("login", ""),
            email=user_data.get("email")
        )
        
        created_at_str = comment_data.get("created_at")
        updated_at_str = comment_data.get("updated_at")
        
        created_at = None
        updated_at = None
        
        if created_at_str:
            try:
                created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
                
        if updated_at_str:
            try:
                updated_at = datetime.fromisoformat(updated_at_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        
        return cls(
            id=comment_data.get("id", 0),
            body=comment_data.get("body", ""),
            user=user,
            created_at=created_at,
            updated_at=updated_at
        )
    
    @classmethod
    def from_webhook_payload(cls, comment_data: Dict) -> "PRComment":
        """
        Create a PRComment from webhook payload comment data.
        
        Args:
            comment_data: Comment data from webhook payload
            
        Returns:
            PRComment instance
        """
        return cls.from_github_comment(comment_data)


class PRReviewComment(PRComment):
    """
    Represents a review comment on a specific line in a GitHub pull request.
    """
    
    path: str
    position: Optional[int] = None
    original_position: Optional[int] = None
    commit_id: str
    original_commit_id: Optional[str] = None
    
    @classmethod
    def from_github_review_comment(cls, comment_data: Dict) -> "PRReviewComment":
        """
        Create a PRReviewComment from GitHub API review comment data.
        
        Args:
            comment_data: Review comment data from GitHub API
            
        Returns:
            PRReviewComment instance
        """
        base_comment = PRComment.from_github_comment(comment_data)
        
        return cls(
            id=base_comment.id,
            body=base_comment.body,
            user=base_comment.user,
            created_at=base_comment.created_at,
            updated_at=base_comment.updated_at,
            path=comment_data.get("path", ""),
            position=comment_data.get("position"),
            original_position=comment_data.get("original_position"),
            commit_id=comment_data.get("commit_id", ""),
            original_commit_id=comment_data.get("original_commit_id")
        )
    
    @classmethod
    def from_webhook_payload(cls, comment_data: Dict) -> "PRReviewComment":
        """
        Create a PRReviewComment from webhook payload review comment data.
        
        Args:
            comment_data: Review comment data from webhook payload
            
        Returns:
            PRReviewComment instance
        """
        return cls.from_github_review_comment(comment_data)


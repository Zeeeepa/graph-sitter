"""
Models for representing PR file data.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PRFile(BaseModel):
    """
    Represents a file in a GitHub pull request.
    """
    
    filename: str
    status: str = Field(description="Status of the file (added, modified, removed)")
    additions: int = Field(default=0, description="Number of lines added")
    deletions: int = Field(default=0, description="Number of lines deleted")
    changes: int = Field(default=0, description="Total number of changes")
    patch: Optional[str] = Field(default=None, description="Diff patch")
    raw_url: Optional[str] = Field(default=None, description="URL to raw file content")
    contents_url: Optional[str] = Field(default=None, description="URL to file contents API")
    sha: Optional[str] = Field(default=None, description="Blob SHA")
    
    @classmethod
    def from_github_file(cls, file_data: Dict) -> "PRFile":
        """
        Create a PRFile from GitHub API file data.
        
        Args:
            file_data: File data from GitHub API
            
        Returns:
            PRFile instance
        """
        return cls(
            filename=file_data.get("filename", ""),
            status=file_data.get("status", ""),
            additions=file_data.get("additions", 0),
            deletions=file_data.get("deletions", 0),
            changes=file_data.get("changes", 0),
            patch=file_data.get("patch"),
            raw_url=file_data.get("raw_url"),
            contents_url=file_data.get("contents_url"),
            sha=file_data.get("sha")
        )
    
    @classmethod
    def from_webhook_payload(cls, file_data: Dict) -> "PRFile":
        """
        Create a PRFile from webhook payload file data.
        
        Args:
            file_data: File data from webhook payload
            
        Returns:
            PRFile instance
        """
        return cls(
            filename=file_data.get("filename", ""),
            status=file_data.get("status", ""),
            additions=file_data.get("additions", 0),
            deletions=file_data.get("deletions", 0),
            changes=file_data.get("changes", 0),
            patch=file_data.get("patch"),
            raw_url=file_data.get("raw_url"),
            contents_url=file_data.get("contents_url"),
            sha=file_data.get("sha")
        )


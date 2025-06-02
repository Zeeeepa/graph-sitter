"""
GitHub Types

This module defines data types for GitHub integration.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any

@dataclass
class GitHubUser:
    """GitHub user"""
    id: int
    login: str
    name: Optional[str]
    email: Optional[str]
    avatar_url: str
    html_url: str
    type: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubUser':
        return cls(
            id=data['id'],
            login=data['login'],
            name=data.get('name'),
            email=data.get('email'),
            avatar_url=data['avatar_url'],
            html_url=data['html_url'],
            type=data['type']
        )

@dataclass
class GitHubRepository:
    """GitHub repository"""
    id: int
    name: str
    full_name: str
    description: Optional[str]
    private: bool
    html_url: str
    clone_url: str
    ssh_url: str
    default_branch: str
    language: Optional[str]
    owner: GitHubUser
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubRepository':
        return cls(
            id=data['id'],
            name=data['name'],
            full_name=data['full_name'],
            description=data.get('description'),
            private=data['private'],
            html_url=data['html_url'],
            clone_url=data['clone_url'],
            ssh_url=data['ssh_url'],
            default_branch=data['default_branch'],
            language=data.get('language'),
            owner=GitHubUser.from_dict(data['owner'])
        )

@dataclass
class GitHubIssue:
    """GitHub issue"""
    id: int
    number: int
    title: str
    body: Optional[str]
    state: str
    html_url: str
    user: GitHubUser
    assignees: List[GitHubUser]
    labels: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubIssue':
        return cls(
            id=data['id'],
            number=data['number'],
            title=data['title'],
            body=data.get('body'),
            state=data['state'],
            html_url=data['html_url'],
            user=GitHubUser.from_dict(data['user']),
            assignees=[GitHubUser.from_dict(assignee) for assignee in data.get('assignees', [])],
            labels=data.get('labels', []),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        )

@dataclass
class GitHubPullRequest:
    """GitHub pull request"""
    id: int
    number: int
    title: str
    body: Optional[str]
    state: str
    html_url: str
    user: GitHubUser
    head: Dict[str, Any]
    base: Dict[str, Any]
    draft: bool
    merged: bool
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubPullRequest':
        return cls(
            id=data['id'],
            number=data['number'],
            title=data['title'],
            body=data.get('body'),
            state=data['state'],
            html_url=data['html_url'],
            user=GitHubUser.from_dict(data['user']),
            head=data['head'],
            base=data['base'],
            draft=data.get('draft', False),
            merged=data.get('merged', False),
            created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        )


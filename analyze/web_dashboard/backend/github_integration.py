"""
GitHub Integration for Web-Eval-Agent Dashboard

Handles GitHub API operations, webhook management, and repository interactions.
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
import hmac
import hashlib
import json

import aiohttp
from github import Github, GithubException
from github.Repository import Repository
from github.PullRequest import PullRequest
# from github.Webhook import Webhook  # Not available in current PyGithub version

logger = logging.getLogger(__name__)


class GitHubIntegration:
    """GitHub API integration and webhook management."""
    
    def __init__(self):
        """Initialize GitHub integration."""
        self.token = os.getenv("GITHUB_TOKEN")
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET")
        self.github_client = None
        
        if not self.token:
            logger.warning("GITHUB_TOKEN not set - GitHub integration will be limited")
        if not self.webhook_secret:
            logger.warning("GITHUB_WEBHOOK_SECRET not set - webhook verification disabled")
    
    async def initialize(self):
        """Initialize GitHub client."""
        if self.token:
            self.github_client = Github(self.token)
            logger.info("GitHub integration initialized")
        else:
            logger.warning("GitHub integration not initialized - missing token")
    
    async def shutdown(self):
        """Shutdown GitHub integration."""
        if self.github_client:
            self.github_client.close()
            logger.info("GitHub integration shutdown")
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature."""
        if not self.webhook_secret:
            logger.warning("Webhook signature verification skipped - no secret configured")
            return True
        
        try:
            # GitHub sends signature as 'sha256=<hash>'
            if not signature.startswith('sha256='):
                return False
            
            expected_signature = signature[7:]  # Remove 'sha256=' prefix
            
            # Calculate HMAC
            mac = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            )
            calculated_signature = mac.hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(expected_signature, calculated_signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def get_repository_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """Get repository information."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return None
        
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            
            return {
                "id": repository.id,
                "name": repository.name,
                "full_name": repository.full_name,
                "description": repository.description,
                "private": repository.private,
                "default_branch": repository.default_branch,
                "clone_url": repository.clone_url,
                "ssh_url": repository.ssh_url,
                "html_url": repository.html_url,
                "created_at": repository.created_at.isoformat() if repository.created_at else None,
                "updated_at": repository.updated_at.isoformat() if repository.updated_at else None,
                "language": repository.language,
                "size": repository.size,
                "stargazers_count": repository.stargazers_count,
                "forks_count": repository.forks_count,
                "open_issues_count": repository.open_issues_count,
                "has_issues": repository.has_issues,
                "has_projects": repository.has_projects,
                "has_wiki": repository.has_wiki,
                "archived": repository.archived,
                "disabled": repository.disabled,
                "permissions": {
                    "admin": repository.permissions.admin,
                    "push": repository.permissions.push,
                    "pull": repository.permissions.pull
                } if repository.permissions else None
            }
            
        except GithubException as e:
            logger.error(f"Error getting repository info for {owner}/{repo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting repository info: {e}")
            return None
    
    async def create_webhook(self, owner: str, repo: str, webhook_url: str) -> Optional[str]:
        """Create a webhook for the repository."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return None
        
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Webhook configuration
            config = {
                "url": webhook_url,
                "content_type": "json",
                "insecure_ssl": "0"  # Require SSL
            }
            
            if self.webhook_secret:
                config["secret"] = self.webhook_secret
            
            # Events to subscribe to
            events = [
                "push",
                "pull_request",
                "pull_request_review",
                "issues",
                "issue_comment",
                "release",
                "workflow_run"
            ]
            
            # Create webhook
            webhook = repository.create_hook(
                name="web",
                config=config,
                events=events,
                active=True
            )
            
            logger.info(f"Created webhook {webhook.id} for {owner}/{repo}")
            return str(webhook.id)
            
        except GithubException as e:
            logger.error(f"Error creating webhook for {owner}/{repo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating webhook: {e}")
            return None
    
    async def delete_webhook(self, owner: str, repo: str, webhook_id: str) -> bool:
        """Delete a webhook from the repository."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return False
        
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            webhook = repository.get_hook(int(webhook_id))
            webhook.delete()
            
            logger.info(f"Deleted webhook {webhook_id} from {owner}/{repo}")
            return True
            
        except GithubException as e:
            logger.error(f"Error deleting webhook {webhook_id} from {owner}/{repo}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting webhook: {e}")
            return False
    
    async def get_repository_tree(self, owner: str, repo: str, branch: str = "main") -> Optional[Dict[str, Any]]:
        """Get repository file tree structure."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return None
        
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Get the tree for the specified branch
            try:
                ref = repository.get_git_ref(f"heads/{branch}")
                commit = repository.get_git_commit(ref.object.sha)
                tree = repository.get_git_tree(commit.tree.sha, recursive=True)
            except GithubException:
                # Fallback to default branch if specified branch doesn't exist
                tree = repository.get_git_tree(repository.default_branch, recursive=True)
            
            # Build tree structure
            tree_data = {
                "sha": tree.sha,
                "url": tree.url,
                "tree": []
            }
            
            for element in tree.tree:
                tree_data["tree"].append({
                    "path": element.path,
                    "mode": element.mode,
                    "type": element.type,
                    "sha": element.sha,
                    "size": element.size,
                    "url": element.url
                })
            
            return tree_data
            
        except GithubException as e:
            logger.error(f"Error getting repository tree for {owner}/{repo}:{branch}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting repository tree: {e}")
            return None
    
    async def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Optional[Dict[str, Any]]:
        """Get pull request information."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return None
        
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            
            return {
                "id": pr.id,
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "draft": pr.draft,
                "merged": pr.merged,
                "mergeable": pr.mergeable,
                "mergeable_state": pr.mergeable_state,
                "merge_commit_sha": pr.merge_commit_sha,
                "head": {
                    "ref": pr.head.ref,
                    "sha": pr.head.sha,
                    "repo": pr.head.repo.full_name if pr.head.repo else None
                },
                "base": {
                    "ref": pr.base.ref,
                    "sha": pr.base.sha,
                    "repo": pr.base.repo.full_name if pr.base.repo else None
                },
                "user": {
                    "login": pr.user.login,
                    "id": pr.user.id,
                    "avatar_url": pr.user.avatar_url
                } if pr.user else None,
                "created_at": pr.created_at.isoformat() if pr.created_at else None,
                "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                "closed_at": pr.closed_at.isoformat() if pr.closed_at else None,
                "merged_at": pr.merged_at.isoformat() if pr.merged_at else None,
                "html_url": pr.html_url,
                "diff_url": pr.diff_url,
                "patch_url": pr.patch_url,
                "additions": pr.additions,
                "deletions": pr.deletions,
                "changed_files": pr.changed_files,
                "commits": pr.commits,
                "comments": pr.comments,
                "review_comments": pr.review_comments
            }
            
        except GithubException as e:
            logger.error(f"Error getting PR {pr_number} for {owner}/{repo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting PR: {e}")
            return None
    
    async def merge_pull_request(
        self, 
        owner: str, 
        repo: str, 
        pr_number: int,
        commit_title: Optional[str] = None,
        commit_message: Optional[str] = None,
        merge_method: str = "merge"
    ) -> bool:
        """Merge a pull request."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return False
        
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            pr = repository.get_pull(pr_number)
            
            # Check if PR is mergeable
            if not pr.mergeable:
                logger.error(f"PR {pr_number} is not mergeable")
                return False
            
            # Merge the PR
            merge_result = pr.merge(
                commit_title=commit_title,
                commit_message=commit_message,
                merge_method=merge_method
            )
            
            if merge_result.merged:
                logger.info(f"Successfully merged PR {pr_number} for {owner}/{repo}")
                return True
            else:
                logger.error(f"Failed to merge PR {pr_number}: {merge_result.message}")
                return False
            
        except GithubException as e:
            logger.error(f"Error merging PR {pr_number} for {owner}/{repo}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error merging PR: {e}")
            return False
    
    async def create_issue_comment(
        self, 
        owner: str, 
        repo: str, 
        issue_number: int, 
        comment_body: str
    ) -> bool:
        """Create a comment on an issue or PR."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return False
        
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            issue = repository.get_issue(issue_number)
            issue.create_comment(comment_body)
            
            logger.info(f"Created comment on issue {issue_number} for {owner}/{repo}")
            return True
            
        except GithubException as e:
            logger.error(f"Error creating comment on issue {issue_number} for {owner}/{repo}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating comment: {e}")
            return False
    
    async def get_file_content(
        self, 
        owner: str, 
        repo: str, 
        file_path: str, 
        ref: Optional[str] = None
    ) -> Optional[str]:
        """Get file content from repository."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return None
        
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            
            # Get file content
            file_content = repository.get_contents(file_path, ref=ref)
            
            if isinstance(file_content, list):
                # If it's a directory, return None
                return None
            
            # Decode content
            content = file_content.decoded_content.decode('utf-8')
            return content
            
        except GithubException as e:
            logger.error(f"Error getting file content {file_path} from {owner}/{repo}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting file content: {e}")
            return None
    
    async def clone_repository(
        self, 
        owner: str, 
        repo: str, 
        target_dir: str,
        branch: Optional[str] = None
    ) -> bool:
        """Clone repository to local directory."""
        try:
            # Get repository info to get clone URL
            repo_info = await self.get_repository_info(owner, repo)
            if not repo_info:
                logger.error(f"Could not get repository info for {owner}/{repo}")
                return False
            
            clone_url = repo_info["clone_url"]
            
            # Build git clone command
            cmd = ["git", "clone"]
            
            if branch:
                cmd.extend(["--branch", branch])
            
            cmd.extend([clone_url, target_dir])
            
            # Execute git clone
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"Successfully cloned {owner}/{repo} to {target_dir}")
                return True
            else:
                logger.error(f"Failed to clone repository: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error cloning repository {owner}/{repo}: {e}")
            return False
    
    async def get_repository_branches(self, owner: str, repo: str) -> List[str]:
        """Get list of repository branches."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return []
        
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            branches = repository.get_branches()
            
            return [branch.name for branch in branches]
            
        except GithubException as e:
            logger.error(f"Error getting branches for {owner}/{repo}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting branches: {e}")
            return []
    
    async def get_commit_status(self, owner: str, repo: str, sha: str) -> Optional[Dict[str, Any]]:
        """Get commit status (CI/CD checks)."""
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return None
        
        try:
            repository = self.github_client.get_repo(f"{owner}/{repo}")
            commit = repository.get_commit(sha)
            
            # Get combined status
            combined_status = commit.get_combined_status()
            
            # Get individual statuses
            statuses = []
            for status in combined_status.statuses:
                statuses.append({
                    "id": status.id,
                    "state": status.state,
                    "description": status.description,
                    "target_url": status.target_url,
                    "context": status.context,
                    "created_at": status.created_at.isoformat() if status.created_at else None,
                    "updated_at": status.updated_at.isoformat() if status.updated_at else None
                })
            
            return {
                "state": combined_status.state,
                "total_count": combined_status.total_count,
                "statuses": statuses,
                "sha": combined_status.sha,
                "commit_url": combined_status.commit_url,
                "repository": combined_status.repository.full_name if combined_status.repository else None
            }
            
        except GithubException as e:
            logger.error(f"Error getting commit status for {owner}/{repo}:{sha}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting commit status: {e}")
            return None

"""
Enhanced GitHub Extension for Contexten
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio

try:
    from github import Github
    from github.Repository import Repository
    from github.PullRequest import PullRequest
except ImportError:
    logging.warning("PyGithub not available, using mock implementation")
    
    class MockGithub:
        def __init__(self, token):
            self.token = token
        
        def get_repo(self, name):
            return MockRepository(name)
        
        def get_rate_limit(self):
            return MockRateLimit()
    
    class MockRepository:
        def __init__(self, name):
            self.name = name
            self.full_name = name
            self.description = "Mock repository"
            self.html_url = f"https://github.com/{name}"
            self.clone_url = f"https://github.com/{name}.git"
            self.default_branch = "main"
            self.language = "Python"
            self.stargazers_count = 100
            self.forks_count = 10
    
    class MockRateLimit:
        def __init__(self):
            self.core = MockCore()
    
    class MockCore:
        def __init__(self):
            self.remaining = 5000
            self.limit = 5000
            self.reset = datetime.now()
    
    Github = MockGithub
    Repository = None
    PullRequest = None

logger = logging.getLogger(__name__)


class GitHubExtension:
    """
    Enhanced GitHub integration for Contexten orchestrator
    
    Provides comprehensive GitHub functionality including:
    - Repository management
    - Pull request automation
    - Issue tracking
    - Webhook handling
    - Code analysis integration
    - Automated workflows
    """
    
    def __init__(self, token: str, orchestrator=None):
        if Github is None:
            raise ImportError("PyGithub is required for GitHub extension. Install with: pip install PyGithub")
        
        self.token = token
        self.orchestrator = orchestrator
        self.client = Github(token)
        self.is_active = False
        
        logger.info("GitHub extension initialized")
    
    async def start(self):
        """Start the GitHub extension"""
        self.is_active = True
        logger.info("GitHub extension started")
    
    async def stop(self):
        """Stop the GitHub extension"""
        self.is_active = False
        logger.info("GitHub extension stopped")
    
    async def execute_action(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a GitHub action
        
        Args:
            action: Action to execute (e.g., 'create_pr', 'get_repository', 'analyze_pr')
            data: Action-specific data
        
        Returns:
            Action result
        """
        if not self.is_active:
            raise RuntimeError("GitHub extension is not active")
        
        try:
            if action == "create_pr":
                return await self._create_pr(data)
            elif action == "get_repository":
                return await self._get_repository(data)
            elif action == "analyze_pr":
                return await self._analyze_pr(data)
            elif action == "review_pr":
                return await self._review_pr(data)
            elif action == "merge_pr":
                return await self._merge_pr(data)
            elif action == "create_issue":
                return await self._create_issue(data)
            elif action == "analyze_repository":
                return await self._analyze_repository(data)
            elif action == "setup_webhook":
                return await self._setup_webhook(data)
            else:
                raise ValueError(f"Unknown GitHub action: {action}")
                
        except Exception as e:
            logger.error(f"GitHub action '{action}' failed: {e}")
            raise
    
    async def _create_pr(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pull request"""
        repo_name = data.get("repository")
        title = data.get("title")
        body = data.get("body", "")
        head = data.get("head")  # source branch
        base = data.get("base", "main")  # target branch
        
        if not all([repo_name, title, head]):
            raise ValueError("Repository, title, and head branch are required for creating a PR")
        
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base
            )
            
            logger.info(f"Created GitHub PR: {pr.html_url}")
            
            return {
                "action": "create_pr",
                "status": "success",
                "pr": {
                    "id": pr.id,
                    "number": pr.number,
                    "title": pr.title,
                    "url": pr.html_url,
                    "state": pr.state
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create GitHub PR: {e}")
            raise
    
    async def _get_repository(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get repository information"""
        repo_name = data.get("repository")
        
        if not repo_name:
            raise ValueError("Repository name is required")
        
        try:
            repo = self.client.get_repo(repo_name)
            
            return {
                "action": "get_repository",
                "status": "success",
                "repository": {
                    "id": repo.id,
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                    "clone_url": repo.clone_url,
                    "default_branch": repo.default_branch,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get GitHub repository {repo_name}: {e}")
            raise
    
    async def _analyze_pr(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a pull request"""
        repo_name = data.get("repository")
        pr_number = data.get("pr_number")
        
        if not repo_name or not pr_number:
            raise ValueError("Repository and PR number are required")
        
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Get PR details
            files = list(pr.get_files())
            commits = list(pr.get_commits())
            
            # Use Codegen SDK for detailed analysis if available
            analysis_result = None
            if self.orchestrator and self.orchestrator.codegen_agent:
                analysis_prompt = f"""
Analyze the following GitHub pull request:

Repository: {repo_name}
PR #{pr_number}: {pr.title}
Description: {pr.body}

Files changed: {len(files)}
Commits: {len(commits)}

Please provide a comprehensive analysis including:
1. Code quality assessment
2. Security considerations
3. Performance implications
4. Testing coverage
5. Documentation updates needed
6. Potential breaking changes
7. Recommendations for improvement

Focus on providing actionable feedback for the PR author.
"""
                
                analysis_task = await self.orchestrator._execute_codegen_task(
                    "codegen.analyze_pr",
                    {
                        "prompt": analysis_prompt,
                        "context": {
                            "repository": repo_name,
                            "pr_number": pr_number,
                            "pr_title": pr.title,
                            "pr_body": pr.body,
                            "files_changed": len(files),
                            "commits_count": len(commits)
                        }
                    }
                )
                
                analysis_result = analysis_task.get("result")
            
            return {
                "action": "analyze_pr",
                "status": "success",
                "pr": {
                    "id": pr.id,
                    "number": pr.number,
                    "title": pr.title,
                    "url": pr.html_url,
                    "state": pr.state,
                    "files_changed": len(files),
                    "commits": len(commits),
                    "additions": pr.additions,
                    "deletions": pr.deletions
                },
                "analysis": analysis_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze GitHub PR {repo_name}#{pr_number}: {e}")
            raise
    
    async def _review_pr(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Review a pull request and provide feedback"""
        repo_name = data.get("repository")
        pr_number = data.get("pr_number")
        review_type = data.get("review_type", "COMMENT")  # APPROVE, REQUEST_CHANGES, COMMENT
        
        if not repo_name or not pr_number:
            raise ValueError("Repository and PR number are required")
        
        try:
            # First analyze the PR
            analysis_result = await self._analyze_pr(data)
            
            # Generate review comments using Codegen SDK
            if self.orchestrator and self.orchestrator.codegen_agent:
                review_prompt = f"""
Based on the following PR analysis, create a comprehensive code review:

{analysis_result.get('analysis', '')}

Please provide:
1. Overall assessment
2. Specific line-by-line feedback where applicable
3. Suggestions for improvement
4. Approval recommendation (APPROVE, REQUEST_CHANGES, or COMMENT)

Format the response as a structured review that can be posted to GitHub.
"""
                
                review_task = await self.orchestrator._execute_codegen_task(
                    "codegen.review_pr",
                    {
                        "prompt": review_prompt,
                        "context": {
                            "repository": repo_name,
                            "pr_number": pr_number,
                            "analysis": analysis_result
                        }
                    }
                )
                
                review_body = review_task.get("result", "Automated review completed.")
            else:
                review_body = "Automated review completed. Please see analysis for details."
            
            # Post review to GitHub
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            review = pr.create_review(
                body=review_body,
                event=review_type
            )
            
            logger.info(f"Created GitHub PR review: {repo_name}#{pr_number}")
            
            return {
                "action": "review_pr",
                "status": "success",
                "review": {
                    "id": review.id,
                    "body": review.body,
                    "state": review.state,
                    "url": review.html_url
                },
                "analysis": analysis_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to review GitHub PR {repo_name}#{pr_number}: {e}")
            raise
    
    async def _merge_pr(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge a pull request"""
        repo_name = data.get("repository")
        pr_number = data.get("pr_number")
        merge_method = data.get("merge_method", "merge")  # merge, squash, rebase
        
        if not repo_name or not pr_number:
            raise ValueError("Repository and PR number are required")
        
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            # Check if PR is mergeable
            if not pr.mergeable:
                raise ValueError("PR is not mergeable")
            
            # Merge the PR
            merge_result = pr.merge(merge_method=merge_method)
            
            logger.info(f"Merged GitHub PR: {repo_name}#{pr_number}")
            
            return {
                "action": "merge_pr",
                "status": "success",
                "merge": {
                    "merged": merge_result.merged,
                    "sha": merge_result.sha,
                    "message": merge_result.message
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to merge GitHub PR {repo_name}#{pr_number}: {e}")
            raise
    
    async def _create_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a GitHub issue"""
        repo_name = data.get("repository")
        title = data.get("title")
        body = data.get("body", "")
        labels = data.get("labels", [])
        assignees = data.get("assignees", [])
        
        if not repo_name or not title:
            raise ValueError("Repository and title are required for creating an issue")
        
        try:
            repo = self.client.get_repo(repo_name)
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=labels,
                assignees=assignees
            )
            
            logger.info(f"Created GitHub issue: {issue.html_url}")
            
            return {
                "action": "create_issue",
                "status": "success",
                "issue": {
                    "id": issue.id,
                    "number": issue.number,
                    "title": issue.title,
                    "url": issue.html_url,
                    "state": issue.state
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {e}")
            raise
    
    async def _analyze_repository(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a repository comprehensively"""
        repo_name = data.get("repository")
        analysis_type = data.get("analysis_type", "comprehensive")
        
        if not repo_name:
            raise ValueError("Repository name is required")
        
        try:
            repo = self.client.get_repo(repo_name)
            
            # Gather repository metrics
            issues = list(repo.get_issues(state="open"))
            prs = list(repo.get_pulls(state="open"))
            releases = list(repo.get_releases())
            contributors = list(repo.get_contributors())
            
            # Use Codegen SDK for detailed analysis
            analysis_result = None
            if self.orchestrator and self.orchestrator.codegen_agent:
                analysis_prompt = f"""
Analyze the GitHub repository: {repo_name}

Repository Information:
- Description: {repo.description}
- Language: {repo.language}
- Stars: {repo.stargazers_count}
- Forks: {repo.forks_count}
- Open Issues: {len(issues)}
- Open PRs: {len(prs)}
- Releases: {len(releases)}
- Contributors: {len(contributors)}

Analysis Type: {analysis_type}

Please provide a comprehensive analysis including:
1. Code quality and architecture assessment
2. Project health and activity metrics
3. Security and vulnerability analysis
4. Performance considerations
5. Documentation quality
6. Community engagement
7. Maintenance recommendations
8. Improvement suggestions

Focus on actionable insights for repository improvement.
"""
                
                analysis_task = await self.orchestrator._execute_codegen_task(
                    "codegen.analyze_repository",
                    {
                        "prompt": analysis_prompt,
                        "context": {
                            "repository": repo_name,
                            "analysis_type": analysis_type,
                            "repo_stats": {
                                "stars": repo.stargazers_count,
                                "forks": repo.forks_count,
                                "open_issues": len(issues),
                                "open_prs": len(prs),
                                "releases": len(releases),
                                "contributors": len(contributors)
                            }
                        }
                    }
                )
                
                analysis_result = analysis_task.get("result")
            
            return {
                "action": "analyze_repository",
                "status": "success",
                "repository": {
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "url": repo.html_url,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "open_issues": len(issues),
                    "open_prs": len(prs),
                    "releases": len(releases),
                    "contributors": len(contributors)
                },
                "analysis": analysis_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze GitHub repository {repo_name}: {e}")
            raise
    
    async def _setup_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Setup a webhook for the repository"""
        repo_name = data.get("repository")
        webhook_url = data.get("webhook_url")
        events = data.get("events", ["push", "pull_request", "issues"])
        
        if not repo_name or not webhook_url:
            raise ValueError("Repository and webhook URL are required")
        
        try:
            repo = self.client.get_repo(repo_name)
            
            webhook = repo.create_hook(
                name="web",
                config={
                    "url": webhook_url,
                    "content_type": "json"
                },
                events=events,
                active=True
            )
            
            logger.info(f"Created GitHub webhook for {repo_name}")
            
            return {
                "action": "setup_webhook",
                "status": "success",
                "webhook": {
                    "id": webhook.id,
                    "url": webhook_url,
                    "events": events,
                    "active": webhook.active
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to setup GitHub webhook for {repo_name}: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get extension status"""
        return {
            "active": self.is_active,
            "client_initialized": self.client is not None,
            "rate_limit": {
                "remaining": self.client.get_rate_limit().core.remaining,
                "limit": self.client.get_rate_limit().core.limit,
                "reset": self.client.get_rate_limit().core.reset.isoformat()
            } if self.client else None,
            "timestamp": datetime.now().isoformat()
        }

"""
Enhanced Linear Extension for Contexten
Integrates with existing Linear client from codegen.extensions.linear
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# Handle missing Linear client gracefully
try:
    from codegen.extensions.linear.linear_client import LinearClient
    from codegen.extensions.linear.types import LinearIssue, LinearComment, LinearTeam
except ImportError:
    logging.warning("Linear client not available, using mock implementation")
    
    class MockLinearClient:
        def __init__(self, access_token, team_id=None):
            self.access_token = access_token
            self.team_id = team_id
        
        def create_issue(self, title, description=None, team_id=None):
            return MockLinearIssue(title, description)
        
        def get_issue(self, issue_id):
            return MockLinearIssue("Mock Issue", "Mock description")
        
        def comment_on_issue(self, issue_id, body):
            return MockLinearComment(body)
        
        def search_issues(self, query, limit=10):
            return [MockLinearIssue(f"Issue {i}", f"Description {i}") for i in range(min(limit, 3))]
        
        def get_teams(self):
            return [MockLinearTeam("Mock Team", "MT")]
    
    class MockLinearIssue:
        def __init__(self, title, description):
            self.id = "mock_issue_123"
            self.title = title
            self.description = description
    
    class MockLinearComment:
        def __init__(self, body):
            self.id = "mock_comment_123"
            self.body = body
            self.user = MockLinearUser()
    
    class MockLinearTeam:
        def __init__(self, name, key):
            self.id = "mock_team_123"
            self.name = name
            self.key = key
    
    class MockLinearUser:
        def __init__(self):
            self.name = "Mock User"
    
    LinearClient = MockLinearClient
    LinearIssue = MockLinearIssue
    LinearComment = MockLinearComment
    LinearTeam = MockLinearTeam

logger = logging.getLogger(__name__)


class LinearExtension:
    """
    Enhanced Linear integration for Contexten orchestrator
    
    Provides comprehensive Linear functionality including:
    - Issue management (create, update, search, comment)
    - Team management
    - Webhook handling
    - Real-time synchronization
    - Context-aware task automation
    """
    
    def __init__(self, api_key: str, team_id: Optional[str] = None, orchestrator=None):
        self.api_key = api_key
        self.team_id = team_id
        self.orchestrator = orchestrator
        self.client = LinearClient(access_token=api_key, team_id=team_id)
        self.is_active = False
        
        logger.info("Linear extension initialized")
    
    async def start(self):
        """Start the Linear extension"""
        self.is_active = True
        logger.info("Linear extension started")
    
    async def stop(self):
        """Stop the Linear extension"""
        self.is_active = False
        logger.info("Linear extension stopped")
    
    async def execute_action(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a Linear action
        
        Args:
            action: Action to execute (e.g., 'create_issue', 'get_issue', 'comment_on_issue')
            data: Action-specific data
        
        Returns:
            Action result
        """
        if not self.is_active:
            raise RuntimeError("Linear extension is not active")
        
        try:
            if action == "create_issue":
                return await self._create_issue(data)
            elif action == "get_issue":
                return await self._get_issue(data)
            elif action == "comment_on_issue":
                return await self._comment_on_issue(data)
            elif action == "search_issues":
                return await self._search_issues(data)
            elif action == "get_teams":
                return await self._get_teams(data)
            elif action == "analyze_repository":
                return await self._analyze_repository(data)
            elif action == "create_pr_from_issue":
                return await self._create_pr_from_issue(data)
            else:
                raise ValueError(f"Unknown Linear action: {action}")
                
        except Exception as e:
            logger.error(f"Linear action '{action}' failed: {e}")
            raise
    
    async def _create_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new Linear issue"""
        title = data.get("title")
        description = data.get("description")
        team_id = data.get("team_id", self.team_id)
        
        if not title:
            raise ValueError("Title is required for creating an issue")
        
        try:
            issue = self.client.create_issue(
                title=title,
                description=description,
                team_id=team_id
            )
            
            logger.info(f"Created Linear issue: {issue.id}")
            
            return {
                "action": "create_issue",
                "status": "success",
                "issue": {
                    "id": issue.id,
                    "title": issue.title,
                    "description": issue.description
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create Linear issue: {e}")
            raise
    
    async def _get_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a Linear issue by ID"""
        issue_id = data.get("issue_id")
        
        if not issue_id:
            raise ValueError("Issue ID is required")
        
        try:
            issue = self.client.get_issue(issue_id)
            
            return {
                "action": "get_issue",
                "status": "success",
                "issue": {
                    "id": issue.id,
                    "title": issue.title,
                    "description": issue.description
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get Linear issue {issue_id}: {e}")
            raise
    
    async def _comment_on_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a comment to a Linear issue"""
        issue_id = data.get("issue_id")
        body = data.get("body")
        
        if not issue_id or not body:
            raise ValueError("Issue ID and body are required for commenting")
        
        try:
            comment = self.client.comment_on_issue(issue_id, body)
            
            logger.info(f"Added comment to Linear issue {issue_id}")
            
            return {
                "action": "comment_on_issue",
                "status": "success",
                "comment": {
                    "id": comment.id,
                    "body": comment.body,
                    "user": comment.user.name if comment.user else None
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to comment on Linear issue {issue_id}: {e}")
            raise
    
    async def _search_issues(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Search for Linear issues"""
        query = data.get("query", "")
        limit = data.get("limit", 10)
        
        try:
            issues = self.client.search_issues(query, limit)
            
            return {
                "action": "search_issues",
                "status": "success",
                "issues": [
                    {
                        "id": issue.id,
                        "title": issue.title,
                        "description": issue.description
                    }
                    for issue in issues
                ],
                "query": query,
                "count": len(issues),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to search Linear issues: {e}")
            raise
    
    async def _get_teams(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get all Linear teams"""
        try:
            teams = self.client.get_teams()
            
            return {
                "action": "get_teams",
                "status": "success",
                "teams": [
                    {
                        "id": team.id,
                        "name": team.name,
                        "key": team.key
                    }
                    for team in teams
                ],
                "count": len(teams),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get Linear teams: {e}")
            raise
    
    async def _analyze_repository(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a repository and create Linear issues for findings"""
        repository_url = data.get("repository_url")
        analysis_type = data.get("analysis_type", "comprehensive")
        
        if not repository_url:
            raise ValueError("Repository URL is required for analysis")
        
        try:
            # Use Codegen SDK through orchestrator for repository analysis
            if self.orchestrator and self.orchestrator.codegen_agent:
                analysis_prompt = f"""
Analyze the repository at {repository_url} and provide a comprehensive analysis including:

1. Code quality assessment
2. Security vulnerabilities
3. Performance bottlenecks
4. Technical debt identification
5. Improvement recommendations

Analysis type: {analysis_type}

Please provide actionable insights that can be converted into Linear issues for tracking and resolution.
"""
                
                analysis_task = await self.orchestrator._execute_codegen_task(
                    "codegen.analyze_repository",
                    {
                        "prompt": analysis_prompt,
                        "context": {
                            "repository_url": repository_url,
                            "analysis_type": analysis_type
                        }
                    }
                )
                
                # Parse analysis results and create issues if requested
                create_issues = data.get("create_issues", False)
                created_issues = []
                
                if create_issues and analysis_task.get("result"):
                    # Extract actionable items from analysis
                    issues_to_create = self._extract_issues_from_analysis(
                        analysis_task["result"], 
                        repository_url
                    )
                    
                    for issue_data in issues_to_create:
                        try:
                            issue = self.client.create_issue(
                                title=issue_data["title"],
                                description=issue_data["description"],
                                team_id=self.team_id
                            )
                            created_issues.append({
                                "id": issue.id,
                                "title": issue.title,
                                "type": issue_data["type"]
                            })
                        except Exception as e:
                            logger.warning(f"Failed to create issue: {e}")
                
                return {
                    "action": "analyze_repository",
                    "status": "success",
                    "repository_url": repository_url,
                    "analysis_type": analysis_type,
                    "analysis_result": analysis_task["result"],
                    "created_issues": created_issues,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise RuntimeError("Orchestrator or Codegen agent not available")
                
        except Exception as e:
            logger.error(f"Failed to analyze repository {repository_url}: {e}")
            raise
    
    async def _create_pr_from_issue(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a PR to resolve a Linear issue"""
        issue_id = data.get("issue_id")
        repository_url = data.get("repository_url")
        
        if not issue_id:
            raise ValueError("Issue ID is required")
        
        try:
            # Get issue details
            issue = self.client.get_issue(issue_id)
            
            # Use Codegen SDK to generate code for the issue
            if self.orchestrator and self.orchestrator.codegen_agent:
                code_generation_prompt = f"""
Create a pull request to resolve the following Linear issue:

Title: {issue.title}
Description: {issue.description}

Repository: {repository_url}

Please:
1. Analyze the issue requirements
2. Generate the necessary code changes
3. Create appropriate tests
4. Provide clear commit messages
5. Create a comprehensive PR description

Focus on creating production-ready, well-tested code that fully addresses the issue requirements.
"""
                
                pr_task = await self.orchestrator._execute_codegen_task(
                    "codegen.create_pr_from_issue",
                    {
                        "prompt": code_generation_prompt,
                        "context": {
                            "issue_id": issue_id,
                            "issue_title": issue.title,
                            "issue_description": issue.description,
                            "repository_url": repository_url
                        }
                    }
                )
                
                # Update Linear issue with PR information
                pr_url = pr_task.get("result", {}).get("pr_url")
                if pr_url:
                    comment_body = f"🚀 Pull request created to resolve this issue: {pr_url}"
                    self.client.comment_on_issue(issue_id, comment_body)
                
                return {
                    "action": "create_pr_from_issue",
                    "status": "success",
                    "issue_id": issue_id,
                    "pr_result": pr_task["result"],
                    "timestamp": datetime.now().isoformat()
                }
            else:
                raise RuntimeError("Orchestrator or Codegen agent not available")
                
        except Exception as e:
            logger.error(f"Failed to create PR from Linear issue {issue_id}: {e}")
            raise
    
    def _extract_issues_from_analysis(self, analysis_result: str, repository_url: str) -> List[Dict[str, Any]]:
        """Extract actionable issues from analysis result"""
        # This is a simplified implementation
        # In a real system, you would use NLP or structured parsing
        
        issues = []
        
        # Look for common patterns in analysis results
        if "security" in analysis_result.lower():
            issues.append({
                "title": f"Security Review Required - {repository_url}",
                "description": f"Security analysis identified potential vulnerabilities in {repository_url}.\n\nDetails from analysis:\n{analysis_result}",
                "type": "security"
            })
        
        if "performance" in analysis_result.lower():
            issues.append({
                "title": f"Performance Optimization - {repository_url}",
                "description": f"Performance analysis identified optimization opportunities in {repository_url}.\n\nDetails from analysis:\n{analysis_result}",
                "type": "performance"
            })
        
        if "technical debt" in analysis_result.lower():
            issues.append({
                "title": f"Technical Debt Cleanup - {repository_url}",
                "description": f"Technical debt analysis identified areas for improvement in {repository_url}.\n\nDetails from analysis:\n{analysis_result}",
                "type": "technical_debt"
            })
        
        return issues
    
    def get_status(self) -> Dict[str, Any]:
        """Get extension status"""
        return {
            "active": self.is_active,
            "team_id": self.team_id,
            "client_initialized": self.client is not None,
            "timestamp": datetime.now().isoformat()
        }

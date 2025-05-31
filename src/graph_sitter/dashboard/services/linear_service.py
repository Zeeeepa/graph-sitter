"""Linear service for issue management and integration."""

import os
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp

from ..utils.cache import CacheManager
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LinearService:
    """Service for Linear API interactions and issue management."""
    
    def __init__(self, access_token: Optional[str] = None):
        """Initialize Linear service.
        
        Args:
            access_token: Linear API access token
        """
        self.access_token = access_token or os.getenv("LINEAR_ACCESS_TOKEN")
        if not self.access_token:
            raise ValueError("Linear access token is required")
            
        self.base_url = "https://api.linear.app/graphql"
        self.cache = CacheManager()
        
    async def get_teams(self) -> List[Dict]:
        """Get all teams from Linear.
        
        Returns:
            List of team objects
        """
        cache_key = "linear_teams"
        cached_teams = await self.cache.get(cache_key)
        
        if cached_teams:
            return cached_teams
            
        query = """
        query {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                    color
                    icon
                    private
                    issueCount
                    activeCycle {
                        id
                        name
                        number
                        startsAt
                        endsAt
                    }
                }
            }
        }
        """
        
        try:
            result = await self._execute_query(query)
            teams = result.get("data", {}).get("teams", {}).get("nodes", [])
            
            # Cache for 10 minutes
            await self.cache.set(cache_key, teams, ttl=600)
            return teams
            
        except Exception as e:
            logger.error(f"Error fetching Linear teams: {e}")
            return []
    
    async def get_issues(self, 
                        team_id: Optional[str] = None,
                        assignee_id: Optional[str] = None,
                        state: Optional[str] = None,
                        limit: int = 50) -> List[Dict]:
        """Get issues from Linear.
        
        Args:
            team_id: Filter by team ID
            assignee_id: Filter by assignee ID
            state: Filter by state
            limit: Maximum number of issues to return
            
        Returns:
            List of issue objects
        """
        cache_key = f"linear_issues_{team_id}_{assignee_id}_{state}_{limit}"
        cached_issues = await self.cache.get(cache_key)
        
        if cached_issues:
            return cached_issues
            
        # Build filter conditions
        filter_conditions = []
        if team_id:
            filter_conditions.append(f'team: {{ id: {{ eq: "{team_id}" }} }}')
        if assignee_id:
            filter_conditions.append(f'assignee: {{ id: {{ eq: "{assignee_id}" }} }}')
        if state:
            filter_conditions.append(f'state: {{ name: {{ eq: "{state}" }} }}')
            
        filter_str = ""
        if filter_conditions:
            filter_str = f"filter: {{ {', '.join(filter_conditions)} }}"
            
        query = f"""
        query {{
            issues({filter_str}, first: {limit}) {{
                nodes {{
                    id
                    identifier
                    title
                    description
                    priority
                    estimate
                    url
                    createdAt
                    updatedAt
                    dueDate
                    completedAt
                    archivedAt
                    state {{
                        id
                        name
                        color
                        type
                    }}
                    assignee {{
                        id
                        name
                        email
                        avatarUrl
                    }}
                    creator {{
                        id
                        name
                        email
                    }}
                    team {{
                        id
                        name
                        key
                    }}
                    project {{
                        id
                        name
                        description
                    }}
                    labels {{
                        nodes {{
                            id
                            name
                            color
                        }}
                    }}
                    comments {{
                        nodes {{
                            id
                            body
                            createdAt
                            user {{
                                id
                                name
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """
        
        try:
            result = await self._execute_query(query)
            issues = result.get("data", {}).get("issues", {}).get("nodes", [])
            
            # Cache for 2 minutes
            await self.cache.set(cache_key, issues, ttl=120)
            return issues
            
        except Exception as e:
            logger.error(f"Error fetching Linear issues: {e}")
            return []
    
    async def create_issue(self, 
                          team_id: str,
                          title: str,
                          description: Optional[str] = None,
                          assignee_id: Optional[str] = None,
                          priority: Optional[int] = None,
                          project_id: Optional[str] = None) -> Optional[Dict]:
        """Create a new issue in Linear.
        
        Args:
            team_id: Team ID to create issue in
            title: Issue title
            description: Issue description
            assignee_id: Assignee user ID
            priority: Issue priority (0-4)
            project_id: Project ID to assign to
            
        Returns:
            Created issue object or None if failed
        """
        mutation = """
        mutation IssueCreate($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                }
            }
        }
        """
        
        variables = {
            "input": {
                "teamId": team_id,
                "title": title,
            }
        }
        
        if description:
            variables["input"]["description"] = description
        if assignee_id:
            variables["input"]["assigneeId"] = assignee_id
        if priority is not None:
            variables["input"]["priority"] = priority
        if project_id:
            variables["input"]["projectId"] = project_id
            
        try:
            result = await self._execute_query(mutation, variables)
            create_result = result.get("data", {}).get("issueCreate", {})
            
            if create_result.get("success"):
                return create_result.get("issue")
            else:
                logger.error(f"Failed to create Linear issue: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Linear issue: {e}")
            return None
    
    async def update_issue(self, 
                          issue_id: str,
                          title: Optional[str] = None,
                          description: Optional[str] = None,
                          assignee_id: Optional[str] = None,
                          state_id: Optional[str] = None,
                          priority: Optional[int] = None) -> Optional[Dict]:
        """Update an existing issue in Linear.
        
        Args:
            issue_id: Issue ID to update
            title: New title
            description: New description
            assignee_id: New assignee ID
            state_id: New state ID
            priority: New priority
            
        Returns:
            Updated issue object or None if failed
        """
        mutation = """
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
            issueUpdate(id: $id, input: $input) {
                success
                issue {
                    id
                    identifier
                    title
                    url
                }
            }
        }
        """
        
        variables = {
            "id": issue_id,
            "input": {}
        }
        
        if title:
            variables["input"]["title"] = title
        if description:
            variables["input"]["description"] = description
        if assignee_id:
            variables["input"]["assigneeId"] = assignee_id
        if state_id:
            variables["input"]["stateId"] = state_id
        if priority is not None:
            variables["input"]["priority"] = priority
            
        try:
            result = await self._execute_query(mutation, variables)
            update_result = result.get("data", {}).get("issueUpdate", {})
            
            if update_result.get("success"):
                return update_result.get("issue")
            else:
                logger.error(f"Failed to update Linear issue: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating Linear issue: {e}")
            return None
    
    async def add_comment(self, issue_id: str, body: str) -> Optional[Dict]:
        """Add a comment to a Linear issue.
        
        Args:
            issue_id: Issue ID to comment on
            body: Comment body
            
        Returns:
            Created comment object or None if failed
        """
        mutation = """
        mutation CommentCreate($input: CommentCreateInput!) {
            commentCreate(input: $input) {
                success
                comment {
                    id
                    body
                    createdAt
                    user {
                        id
                        name
                    }
                }
            }
        }
        """
        
        variables = {
            "input": {
                "issueId": issue_id,
                "body": body,
            }
        }
        
        try:
            result = await self._execute_query(mutation, variables)
            create_result = result.get("data", {}).get("commentCreate", {})
            
            if create_result.get("success"):
                return create_result.get("comment")
            else:
                logger.error(f"Failed to create Linear comment: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Linear comment: {e}")
            return None
    
    async def get_projects(self, team_id: Optional[str] = None) -> List[Dict]:
        """Get projects from Linear.
        
        Args:
            team_id: Filter by team ID
            
        Returns:
            List of project objects
        """
        cache_key = f"linear_projects_{team_id}"
        cached_projects = await self.cache.get(cache_key)
        
        if cached_projects:
            return cached_projects
            
        filter_str = ""
        if team_id:
            filter_str = f'filter: {{ team: {{ id: {{ eq: "{team_id}" }} }} }}'
            
        query = f"""
        query {{
            projects({filter_str}) {{
                nodes {{
                    id
                    name
                    description
                    state
                    progress
                    url
                    createdAt
                    updatedAt
                    startedAt
                    completedAt
                    targetDate
                    lead {{
                        id
                        name
                        email
                    }}
                    teams {{
                        nodes {{
                            id
                            name
                            key
                        }}
                    }}
                    issues {{
                        nodes {{
                            id
                            identifier
                            title
                            state {{
                                name
                                type
                            }}
                        }}
                    }}
                }}
            }}
        }}
        """
        
        try:
            result = await self._execute_query(query)
            projects = result.get("data", {}).get("projects", {}).get("nodes", [])
            
            # Cache for 5 minutes
            await self.cache.set(cache_key, projects, ttl=300)
            return projects
            
        except Exception as e:
            logger.error(f"Error fetching Linear projects: {e}")
            return []
    
    async def _execute_query(self, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query against Linear API.
        
        Args:
            query: GraphQL query string
            variables: Query variables
            
        Returns:
            Query result
        """
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                json=payload,
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Linear API error {response.status}: {error_text}")


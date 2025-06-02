"""
Enhanced Linear API Client

Comprehensive Linear API client with rate limiting, error handling, and caching.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
import aiohttp
from dataclasses import asdict

from .types import (
    LinearIssue, LinearProject, LinearUser, LinearTeam, LinearComment,
    LinearAPIResponse, LinearIntegrationConfig, LinearIssueState,
    LinearIssuePriority, LinearProjectState
)

logger = logging.getLogger(__name__)


class LinearAPIError(Exception):
    """Linear API specific error"""
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_requests: int = 100, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire permission to make a request"""
        async with self._lock:
            now = datetime.now()
            # Remove old requests outside the time window
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < timedelta(seconds=self.time_window)]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
    
    async def wait_if_needed(self):
        """Wait if rate limit is exceeded"""
        while not await self.acquire():
            await asyncio.sleep(1)


class EnhancedLinearClient:
    """Enhanced Linear API client with comprehensive functionality"""
    
    BASE_URL = "https://api.linear.app/graphql"
    
    def __init__(self, config: LinearIntegrationConfig):
        self.config = config
        self.rate_limiter = RateLimiter(
            max_requests=config.rate_limit_requests,
            time_window=config.rate_limit_window
        )
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        
        # Validate configuration
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Initialize the client"""
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "Authorization": f"Bearer {self.config.api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Contexten-Linear-Client/1.0"
                }
            )
        logger.info("Linear client initialized")
    
    async def close(self):
        """Close the client and cleanup resources"""
        if self._session:
            await self._session.close()
            self._session = None
        logger.info("Linear client closed")
    
    def _get_cache_key(self, query: str, variables: Optional[Dict] = None) -> str:
        """Generate cache key for query"""
        key_data = {"query": query}
        if variables:
            key_data["variables"] = variables
        return str(hash(json.dumps(key_data, sort_keys=True)))
    
    def _is_cache_valid(self, cache_key: str, ttl_seconds: int = 300) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache_ttl:
            return False
        return datetime.now() - self._cache_ttl[cache_key] < timedelta(seconds=ttl_seconds)
    
    def _cache_response(self, cache_key: str, data: Any):
        """Cache response data"""
        self._cache[cache_key] = data
        self._cache_ttl[cache_key] = datetime.now()
    
    async def _make_request(self, query: str, variables: Optional[Dict] = None, 
                          use_cache: bool = True, cache_ttl: int = 300) -> LinearAPIResponse:
        """Make GraphQL request to Linear API"""
        if not self._session:
            await self.start()
        
        # Check cache first
        cache_key = self._get_cache_key(query, variables)
        if use_cache and self._is_cache_valid(cache_key, cache_ttl):
            logger.debug(f"Returning cached response for query")
            return LinearAPIResponse.success_response(self._cache[cache_key])
        
        # Rate limiting
        await self.rate_limiter.wait_if_needed()
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            async with self._session.post(self.BASE_URL, json=payload) as response:
                response_data = await response.json()
                
                if response.status != 200:
                    error_msg = f"HTTP {response.status}: {response_data.get('message', 'Unknown error')}"
                    raise LinearAPIError(error_msg, response.status, response_data)
                
                if "errors" in response_data:
                    errors = [error.get("message", "Unknown error") for error in response_data["errors"]]
                    return LinearAPIResponse.error_response(errors)
                
                data = response_data.get("data", {})
                
                # Cache successful response
                if use_cache:
                    self._cache_response(cache_key, data)
                
                return LinearAPIResponse.success_response(data)
                
        except aiohttp.ClientError as e:
            error_msg = f"Network error: {str(e)}"
            logger.error(error_msg)
            return LinearAPIResponse.error_response(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return LinearAPIResponse.error_response(error_msg)
    
    async def get_teams(self) -> LinearAPIResponse:
        """Get all teams"""
        query = """
        query GetTeams {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                    color
                    icon
                    private
                    archived
                    createdAt
                    updatedAt
                }
            }
        }
        """
        
        response = await self._make_request(query)
        if response.success:
            teams_data = response.data.get("teams", {}).get("nodes", [])
            teams = [self._parse_team(team_data) for team_data in teams_data]
            response.data = teams
        
        return response
    
    async def get_team_by_id(self, team_id: str) -> LinearAPIResponse:
        """Get team by ID"""
        query = """
        query GetTeam($id: String!) {
            team(id: $id) {
                id
                name
                key
                description
                color
                icon
                private
                archived
                createdAt
                updatedAt
            }
        }
        """
        
        response = await self._make_request(query, {"id": team_id})
        if response.success and response.data.get("team"):
            team = self._parse_team(response.data["team"])
            response.data = team
        
        return response
    
    async def get_issues(self, team_id: Optional[str] = None, 
                        state: Optional[LinearIssueState] = None,
                        assignee_id: Optional[str] = None,
                        limit: int = 50) -> LinearAPIResponse:
        """Get issues with optional filters"""
        
        # Build filter conditions
        filter_conditions = []
        if team_id:
            filter_conditions.append(f'team: {{id: {{eq: "{team_id}"}}}}')
        if state:
            filter_conditions.append(f'state: {{name: {{eq: "{state.value}"}}}}')
        if assignee_id:
            filter_conditions.append(f'assignee: {{id: {{eq: "{assignee_id}"}}}}')
        
        filter_str = ", ".join(filter_conditions)
        filter_clause = f"filter: {{{filter_str}}}" if filter_conditions else ""
        
        query = f"""
        query GetIssues {{
            issues({filter_clause}, first: {limit}) {{
                nodes {{
                    id
                    identifier
                    title
                    description
                    url
                    priority
                    estimate
                    createdAt
                    updatedAt
                    completedAt
                    canceledAt
                    dueDate
                    state {{
                        name
                    }}
                    creator {{
                        id
                        name
                        email
                        displayName
                        avatarUrl
                    }}
                    assignee {{
                        id
                        name
                        email
                        displayName
                        avatarUrl
                    }}
                    team {{
                        id
                        name
                        key
                    }}
                    project {{
                        id
                        name
                    }}
                    labels {{
                        nodes {{
                            id
                            name
                            color
                        }}
                    }}
                }}
            }}
        }}
        """
        
        response = await self._make_request(query, use_cache=False)  # Don't cache issue queries
        if response.success:
            issues_data = response.data.get("issues", {}).get("nodes", [])
            issues = [self._parse_issue(issue_data) for issue_data in issues_data]
            response.data = issues
        
        return response
    
    async def create_issue(self, title: str, description: Optional[str] = None,
                          team_id: Optional[str] = None, assignee_id: Optional[str] = None,
                          priority: Optional[LinearIssuePriority] = None,
                          project_id: Optional[str] = None,
                          label_ids: Optional[List[str]] = None) -> LinearAPIResponse:
        """Create a new issue"""
        
        # Use default team if not specified
        if not team_id:
            team_id = self.config.team_id
        
        if not team_id:
            return LinearAPIResponse.error_response("Team ID is required to create issue")
        
        # Build input object
        input_fields = [
            f'title: "{title}"',
            f'teamId: "{team_id}"'
        ]
        
        if description:
            # Escape description for GraphQL
            escaped_desc = description.replace('"', '\\"').replace('\n', '\\n')
            input_fields.append(f'description: "{escaped_desc}"')
        
        if assignee_id:
            input_fields.append(f'assigneeId: "{assignee_id}"')
        
        if priority:
            input_fields.append(f'priority: {priority.value}')
        
        if project_id:
            input_fields.append(f'projectId: "{project_id}"')
        
        if label_ids:
            label_ids_str = ", ".join([f'"{label_id}"' for label_id in label_ids])
            input_fields.append(f'labelIds: [{label_ids_str}]')
        
        input_str = ", ".join(input_fields)
        
        query = f"""
        mutation CreateIssue {{
            issueCreate(input: {{{input_str}}}) {{
                success
                issue {{
                    id
                    identifier
                    title
                    url
                    state {{
                        name
                    }}
                    team {{
                        name
                        key
                    }}
                }}
            }}
        }}
        """
        
        response = await self._make_request(query, use_cache=False)
        if response.success:
            create_data = response.data.get("issueCreate", {})
            if create_data.get("success"):
                issue_data = create_data.get("issue", {})
                response.data = {
                    "issue_id": issue_data.get("id"),
                    "identifier": issue_data.get("identifier"),
                    "url": issue_data.get("url"),
                    "title": issue_data.get("title")
                }
            else:
                return LinearAPIResponse.error_response("Failed to create issue")
        
        return response
    
    async def update_issue(self, issue_id: str, **kwargs) -> LinearAPIResponse:
        """Update an existing issue"""
        
        # Build update fields
        update_fields = []
        
        if "title" in kwargs:
            update_fields.append(f'title: "{kwargs["title"]}"')
        
        if "description" in kwargs:
            escaped_desc = kwargs["description"].replace('"', '\\"').replace('\n', '\\n')
            update_fields.append(f'description: "{escaped_desc}"')
        
        if "assignee_id" in kwargs:
            if kwargs["assignee_id"]:
                update_fields.append(f'assigneeId: "{kwargs["assignee_id"]}"')
            else:
                update_fields.append('assigneeId: null')
        
        if "priority" in kwargs and isinstance(kwargs["priority"], LinearIssuePriority):
            update_fields.append(f'priority: {kwargs["priority"].value}')
        
        if "state_id" in kwargs:
            update_fields.append(f'stateId: "{kwargs["state_id"]}"')
        
        if not update_fields:
            return LinearAPIResponse.error_response("No update fields provided")
        
        update_str = ", ".join(update_fields)
        
        query = f"""
        mutation UpdateIssue {{
            issueUpdate(id: "{issue_id}", input: {{{update_str}}}) {{
                success
                issue {{
                    id
                    identifier
                    title
                    url
                }}
            }}
        }}
        """
        
        response = await self._make_request(query, use_cache=False)
        if response.success:
            update_data = response.data.get("issueUpdate", {})
            if update_data.get("success"):
                issue_data = update_data.get("issue", {})
                response.data = {
                    "issue_id": issue_data.get("id"),
                    "identifier": issue_data.get("identifier"),
                    "url": issue_data.get("url"),
                    "title": issue_data.get("title")
                }
            else:
                return LinearAPIResponse.error_response("Failed to update issue")
        
        return response
    
    async def get_projects(self, team_id: Optional[str] = None) -> LinearAPIResponse:
        """Get projects"""
        filter_clause = f'filter: {{team: {{id: {{eq: "{team_id}"}}}}}}' if team_id else ""
        
        query = f"""
        query GetProjects {{
            projects({filter_clause}) {{
                nodes {{
                    id
                    name
                    description
                    state
                    progress
                    startDate
                    targetDate
                    completedAt
                    createdAt
                    updatedAt
                    creator {{
                        id
                        name
                        email
                    }}
                    lead {{
                        id
                        name
                        email
                    }}
                }}
            }}
        }}
        """
        
        response = await self._make_request(query)
        if response.success:
            projects_data = response.data.get("projects", {}).get("nodes", [])
            projects = [self._parse_project(project_data) for project_data in projects_data]
            response.data = projects
        
        return response
    
    def _parse_team(self, team_data: Dict) -> LinearTeam:
        """Parse team data from API response"""
        return LinearTeam(
            id=team_data["id"],
            name=team_data["name"],
            key=team_data["key"],
            description=team_data.get("description"),
            color=team_data.get("color"),
            icon=team_data.get("icon"),
            private=team_data.get("private", False),
            archived=team_data.get("archived", False),
            created_at=self._parse_datetime(team_data.get("createdAt")),
            updated_at=self._parse_datetime(team_data.get("updatedAt"))
        )
    
    def _parse_user(self, user_data: Dict) -> LinearUser:
        """Parse user data from API response"""
        return LinearUser(
            id=user_data["id"],
            name=user_data["name"],
            email=user_data["email"],
            display_name=user_data.get("displayName"),
            avatar_url=user_data.get("avatarUrl"),
            active=user_data.get("active", True),
            admin=user_data.get("admin", False),
            created_at=self._parse_datetime(user_data.get("createdAt")),
            updated_at=self._parse_datetime(user_data.get("updatedAt"))
        )
    
    def _parse_issue(self, issue_data: Dict) -> LinearIssue:
        """Parse issue data from API response"""
        # Parse state
        state_name = issue_data.get("state", {}).get("name", "backlog")
        try:
            state = LinearIssueState(state_name.lower())
        except ValueError:
            state = LinearIssueState.BACKLOG
        
        # Parse priority
        priority_value = issue_data.get("priority", 0)
        try:
            priority = LinearIssuePriority(priority_value)
        except ValueError:
            priority = LinearIssuePriority.NO_PRIORITY
        
        return LinearIssue(
            id=issue_data["id"],
            identifier=issue_data["identifier"],
            title=issue_data["title"],
            description=issue_data.get("description"),
            state=state,
            priority=priority,
            estimate=issue_data.get("estimate"),
            url=issue_data.get("url"),
            created_at=self._parse_datetime(issue_data.get("createdAt")),
            updated_at=self._parse_datetime(issue_data.get("updatedAt")),
            completed_at=self._parse_datetime(issue_data.get("completedAt")),
            canceled_at=self._parse_datetime(issue_data.get("canceledAt")),
            due_date=self._parse_datetime(issue_data.get("dueDate")),
            creator=self._parse_user(issue_data["creator"]) if issue_data.get("creator") else None,
            assignee=self._parse_user(issue_data["assignee"]) if issue_data.get("assignee") else None,
            team=self._parse_team(issue_data["team"]) if issue_data.get("team") else None
        )
    
    def _parse_project(self, project_data: Dict) -> LinearProject:
        """Parse project data from API response"""
        # Parse state
        state_name = project_data.get("state", "planned")
        try:
            state = LinearProjectState(state_name.lower())
        except ValueError:
            state = LinearProjectState.PLANNED
        
        return LinearProject(
            id=project_data["id"],
            name=project_data["name"],
            description=project_data.get("description"),
            state=state,
            progress=project_data.get("progress", 0.0),
            start_date=self._parse_datetime(project_data.get("startDate")),
            target_date=self._parse_datetime(project_data.get("targetDate")),
            completed_at=self._parse_datetime(project_data.get("completedAt")),
            created_at=self._parse_datetime(project_data.get("createdAt")),
            updated_at=self._parse_datetime(project_data.get("updatedAt")),
            creator=self._parse_user(project_data["creator"]) if project_data.get("creator") else None,
            lead=self._parse_user(project_data["lead"]) if project_data.get("lead") else None
        )
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string from API"""
        if not date_str:
            return None
        try:
            # Linear uses ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    async def health_check(self) -> LinearAPIResponse:
        """Check if the Linear API is accessible"""
        query = """
        query HealthCheck {
            viewer {
                id
                name
                email
            }
        }
        """
        
        response = await self._make_request(query, use_cache=False)
        if response.success:
            viewer_data = response.data.get("viewer", {})
            response.data = {
                "status": "healthy",
                "user": viewer_data
            }
        
        return response


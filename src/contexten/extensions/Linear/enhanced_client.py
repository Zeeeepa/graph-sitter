"""
Enhanced Linear GraphQL Client

Comprehensive Linear API client with advanced features including:
- Rate limiting and request throttling
- Response caching with TTL
- Retry logic with exponential backoff
- Comprehensive error handling
- Request/response logging
- Performance metrics
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .config import LinearIntegrationConfig
from .types import (
    LinearIssue, LinearComment, LinearUser, LinearTeam, LinearLabel,
    LinearProject, LinearState, ComponentStats
)
from graph_sitter.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    data: Any
    expires_at: datetime
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


@dataclass
class RateLimiter:
    """Rate limiter for API requests"""
    requests: int = 0
    window_start: datetime = field(default_factory=datetime.now)
    max_requests: int = 100
    window_seconds: int = 60
    
    def can_make_request(self) -> bool:
        now = datetime.now()
        if now - self.window_start > timedelta(seconds=self.window_seconds):
            # Reset window
            self.requests = 0
            self.window_start = now
        
        return self.requests < self.max_requests
    
    def record_request(self) -> None:
        self.requests += 1
    
    def time_until_reset(self) -> float:
        """Time in seconds until rate limit resets"""
        reset_time = self.window_start + timedelta(seconds=self.window_seconds)
        return max(0, (reset_time - datetime.now()).total_seconds())


class EnhancedLinearClient:
    """Enhanced Linear GraphQL client with comprehensive features"""
    
    def __init__(self, config: LinearIntegrationConfig):
        self.config = config
        self.api_config = config.api
        
        # Initialize session
        timeout = ClientTimeout(total=self.api_config.timeout)
        self.session: Optional[ClientSession] = None
        self.timeout = timeout
        
        # Rate limiting
        self.rate_limiter = RateLimiter(
            max_requests=self.api_config.rate_limit_requests,
            window_seconds=self.api_config.rate_limit_window
        )
        
        # Response cache
        self.cache: Dict[str, CacheEntry] = {}
        self.cache_ttl = timedelta(seconds=self.api_config.cache_ttl)
        
        # Statistics
        self.stats = ComponentStats()
        self.start_time = datetime.now()
        
        # User info cache
        self.user_info: Optional[Dict[str, Any]] = None
        
        logger.info("Enhanced Linear client initialized")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def initialize(self) -> None:
        """Initialize the client session"""
        if self.session is None:
            self.session = ClientSession(timeout=self.timeout)
            logger.info("Linear client session initialized")
    
    async def close(self) -> None:
        """Close the client session"""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Linear client session closed")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers"""
        return {
            "Content-Type": "application/json",
            "Authorization": self.api_config.api_key,
            "User-Agent": "graph-sitter-linear-client/1.0"
        }
    
    def _get_cache_key(self, query: str, variables: Optional[Dict] = None) -> str:
        """Generate cache key for query"""
        cache_data = {"query": query, "variables": variables or {}}
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Get cached response if available and not expired"""
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            if not entry.is_expired():
                self.stats.cache_hits += 1
                return entry.data
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        self.stats.cache_misses += 1
        return None
    
    def _cache_response(self, cache_key: str, data: Any) -> None:
        """Cache response with TTL"""
        expires_at = datetime.now() + self.cache_ttl
        self.cache[cache_key] = CacheEntry(data=data, expires_at=expires_at)
    
    async def _wait_for_rate_limit(self) -> None:
        """Wait if rate limit is exceeded"""
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.time_until_reset()
            logger.warning(f"Rate limit exceeded, waiting {wait_time:.2f} seconds")
            await asyncio.sleep(wait_time)
    
    async def _execute_query(
        self, 
        query: str, 
        variables: Optional[Dict] = None,
        use_cache: bool = True,
        retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query with comprehensive error handling"""
        
        if not self.session:
            await self.initialize()
        
        # Check cache first
        cache_key = self._get_cache_key(query, variables) if use_cache else None
        if cache_key and use_cache:
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
        
        # Rate limiting
        await self._wait_for_rate_limit()
        self.rate_limiter.record_request()
        
        # Prepare request
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        headers = self._get_headers()
        max_retries = retries if retries is not None else self.api_config.max_retries
        
        # Execute with retries
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                self.stats.requests_made += 1
                self.stats.last_request = datetime.now()
                
                async with self.session.post(
                    self.api_config.base_url,
                    json=payload,
                    headers=headers
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check for GraphQL errors
                        if "errors" in data:
                            error_msg = "; ".join([err.get("message", "Unknown error") for err in data["errors"]])
                            raise Exception(f"GraphQL errors: {error_msg}")
                        
                        # Cache successful response
                        if cache_key and use_cache:
                            self._cache_response(cache_key, data)
                        
                        self.stats.requests_successful += 1
                        return data
                    
                    elif response.status == 429:
                        # Rate limited by server
                        retry_after = int(response.headers.get("Retry-After", "60"))
                        logger.warning(f"Server rate limit hit, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
            
            except (ClientError, asyncio.TimeoutError) as e:
                last_exception = e
                if attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}/{max_retries + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {max_retries + 1} attempts: {e}")
            
            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error in request: {e}")
                break
        
        # All retries failed
        self.stats.requests_failed += 1
        self.stats.last_error = str(last_exception)
        raise Exception(f"Request failed after {max_retries + 1} attempts: {last_exception}")
    
    async def authenticate(self, api_key: str) -> bool:
        """Authenticate with Linear API and get user info"""
        try:
            query = """
                query {
                    viewer {
                        id
                        name
                        email
                        avatarUrl
                        active
                    }
                }
            """
            
            response = await self._execute_query(query, use_cache=False)
            self.user_info = response["data"]["viewer"]
            
            logger.info(f"Authenticated as Linear user: {self.user_info.get('name')} ({self.user_info.get('email')})")
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def get_issue(self, issue_id: str) -> Optional[LinearIssue]:
        """Get issue by ID with comprehensive data"""
        try:
            query = """
                query getIssue($issueId: String!) {
                    issue(id: $issueId) {
                        id
                        title
                        description
                        number
                        url
                        priority
                        estimate
                        createdAt
                        updatedAt
                        completedAt
                        dueDate
                        assignee {
                            id
                            name
                            email
                            avatarUrl
                            active
                        }
                        creator {
                            id
                            name
                            email
                            avatarUrl
                            active
                        }
                        team {
                            id
                            name
                            key
                            description
                            private
                        }
                        state {
                            id
                            name
                            type
                            color
                            position
                        }
                        labels {
                            nodes {
                                id
                                name
                                color
                                description
                            }
                        }
                        project {
                            id
                            name
                            description
                            url
                        }
                    }
                }
            """
            
            variables = {"issueId": issue_id}
            response = await self._execute_query(query, variables)
            
            issue_data = response["data"]["issue"]
            if not issue_data:
                return None
            
            # Parse labels
            labels = []
            if issue_data.get("labels", {}).get("nodes"):
                labels = [
                    LinearLabel(**label) 
                    for label in issue_data["labels"]["nodes"]
                ]
            
            # Parse other nested objects
            assignee = LinearUser(**issue_data["assignee"]) if issue_data.get("assignee") else None
            creator = LinearUser(**issue_data["creator"]) if issue_data.get("creator") else None
            team = LinearTeam(**issue_data["team"]) if issue_data.get("team") else None
            state = LinearState(**issue_data["state"]) if issue_data.get("state") else None
            project = LinearProject(**issue_data["project"]) if issue_data.get("project") else None
            
            return LinearIssue(
                id=issue_data["id"],
                title=issue_data["title"],
                description=issue_data.get("description"),
                number=issue_data.get("number"),
                url=issue_data.get("url"),
                assignee=assignee,
                assignee_id=issue_data.get("assignee", {}).get("id") if issue_data.get("assignee") else None,
                creator=creator,
                team=team,
                state=state,
                labels=labels,
                project=project,
                priority=issue_data.get("priority"),
                estimate=issue_data.get("estimate"),
                created_at=datetime.fromisoformat(issue_data["createdAt"].replace("Z", "+00:00")) if issue_data.get("createdAt") else None,
                updated_at=datetime.fromisoformat(issue_data["updatedAt"].replace("Z", "+00:00")) if issue_data.get("updatedAt") else None,
                completed_at=datetime.fromisoformat(issue_data["completedAt"].replace("Z", "+00:00")) if issue_data.get("completedAt") else None,
                due_date=datetime.fromisoformat(issue_data["dueDate"].replace("Z", "+00:00")) if issue_data.get("dueDate") else None
            )
            
        except Exception as e:
            logger.error(f"Error getting issue {issue_id}: {e}")
            return None
    
    async def get_user_assigned_issues(
        self, 
        user_id: str, 
        limit: int = 50,
        include_completed: bool = False
    ) -> List[LinearIssue]:
        """Get issues assigned to a specific user"""
        try:
            state_filter = "" if include_completed else 'filter: { state: { type: { neq: "completed" } } }'
            
            query = f"""
                query getUserAssignedIssues($userId: String!, $limit: Int!) {{
                    user(id: $userId) {{
                        assignedIssues(first: $limit, {state_filter}) {{
                            nodes {{
                                id
                                title
                                description
                                number
                                url
                                priority
                                estimate
                                createdAt
                                updatedAt
                                assignee {{
                                    id
                                    name
                                }}
                                team {{
                                    id
                                    name
                                    key
                                }}
                                state {{
                                    id
                                    name
                                    type
                                }}
                            }}
                        }}
                    }}
                }}
            """
            
            variables = {"userId": user_id, "limit": limit}
            response = await self._execute_query(query, variables)
            
            user_data = response["data"]["user"]
            if not user_data or not user_data.get("assignedIssues", {}).get("nodes"):
                return []
            
            issues = []
            for issue_data in user_data["assignedIssues"]["nodes"]:
                # Create simplified issue objects for listing
                assignee = LinearUser(id=issue_data["assignee"]["id"], name=issue_data["assignee"]["name"]) if issue_data.get("assignee") else None
                team = LinearTeam(id=issue_data["team"]["id"], name=issue_data["team"]["name"], key=issue_data["team"]["key"]) if issue_data.get("team") else None
                state = LinearState(
                    id=issue_data["state"]["id"], 
                    name=issue_data["state"]["name"], 
                    type=issue_data["state"]["type"],
                    color="",  # Not included in this query
                    position=0.0  # Not included in this query
                ) if issue_data.get("state") else None
                
                issue = LinearIssue(
                    id=issue_data["id"],
                    title=issue_data["title"],
                    description=issue_data.get("description"),
                    number=issue_data.get("number"),
                    url=issue_data.get("url"),
                    assignee=assignee,
                    assignee_id=issue_data.get("assignee", {}).get("id") if issue_data.get("assignee") else None,
                    team=team,
                    state=state,
                    priority=issue_data.get("priority"),
                    estimate=issue_data.get("estimate"),
                    created_at=datetime.fromisoformat(issue_data["createdAt"].replace("Z", "+00:00")) if issue_data.get("createdAt") else None,
                    updated_at=datetime.fromisoformat(issue_data["updatedAt"].replace("Z", "+00:00")) if issue_data.get("updatedAt") else None
                )
                issues.append(issue)
            
            return issues
            
        except Exception as e:
            logger.error(f"Error getting assigned issues for user {user_id}: {e}")
            return []
    
    async def update_issue(
        self, 
        issue_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update an issue with the provided changes"""
        try:
            # Build the mutation dynamically based on updates
            update_fields = []
            variables = {"issueId": issue_id}
            
            if "title" in updates:
                update_fields.append("title: $title")
                variables["title"] = updates["title"]
            
            if "description" in updates:
                update_fields.append("description: $description")
                variables["description"] = updates["description"]
            
            if "assignee_id" in updates:
                update_fields.append("assigneeId: $assigneeId")
                variables["assigneeId"] = updates["assignee_id"]
            
            if "state_id" in updates:
                update_fields.append("stateId: $stateId")
                variables["stateId"] = updates["state_id"]
            
            if "priority" in updates:
                update_fields.append("priority: $priority")
                variables["priority"] = updates["priority"]
            
            if not update_fields:
                logger.warning("No valid update fields provided")
                return False
            
            mutation = f"""
                mutation updateIssue($issueId: String!, {', '.join(f'${k}: {self._get_graphql_type(k, v)}' for k, v in variables.items() if k != 'issueId')}) {{
                    issueUpdate(id: $issueId, input: {{ {', '.join(update_fields)} }}) {{
                        success
                        issue {{
                            id
                            title
                        }}
                    }}
                }}
            """
            
            response = await self._execute_query(mutation, variables, use_cache=False)
            
            result = response["data"]["issueUpdate"]
            if result["success"]:
                logger.info(f"Successfully updated issue {issue_id}")
                return True
            else:
                logger.error(f"Failed to update issue {issue_id}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating issue {issue_id}: {e}")
            return False
    
    def _get_graphql_type(self, field: str, value: Any) -> str:
        """Get GraphQL type for a field"""
        type_mapping = {
            "title": "String",
            "description": "String", 
            "assigneeId": "String",
            "stateId": "String",
            "priority": "Int"
        }
        return type_mapping.get(field, "String")
    
    async def create_comment(self, issue_id: str, body: str) -> Optional[str]:
        """Create a comment on an issue"""
        try:
            mutation = """
                mutation createComment($issueId: String!, $body: String!) {
                    commentCreate(input: {issueId: $issueId, body: $body}) {
                        success
                        comment {
                            id
                            body
                            url
                        }
                    }
                }
            """
            
            variables = {"issueId": issue_id, "body": body}
            response = await self._execute_query(mutation, variables, use_cache=False)
            
            result = response["data"]["commentCreate"]
            if result["success"]:
                comment_id = result["comment"]["id"]
                logger.info(f"Created comment {comment_id} on issue {issue_id}")
                return comment_id
            else:
                logger.error(f"Failed to create comment on issue {issue_id}")
                return None
            
        except Exception as e:
            logger.error(f"Error creating comment on issue {issue_id}: {e}")
            return None
    
    def get_stats(self) -> ComponentStats:
        """Get client statistics"""
        self.stats.uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        return self.stats
    
    def clear_cache(self) -> None:
        """Clear the response cache"""
        self.cache.clear()
        logger.info("Response cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired_entries,
            "active_entries": total_entries - expired_entries,
            "cache_hit_rate": self.stats.cache_hits / (self.stats.cache_hits + self.stats.cache_misses) if (self.stats.cache_hits + self.stats.cache_misses) > 0 else 0.0
        }


"""
Enhanced Linear GraphQL Client

This module provides a comprehensive GraphQL client for Linear API with
advanced features like connection pooling, retry logic, and caching.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import asyncio
import hashlib
import json
import logging
import time

import aiohttp

from ...shared.logging.get_logger import get_logger
from .mutations import LINEAR_MUTATIONS
from .queries import LINEAR_QUERIES
from .types import LinearIssue, LinearProject, LinearTeam, LinearUser, LinearComment

logger = get_logger(__name__)

@dataclass
class CacheEntry:
    """Cache entry for GraphQL responses"""
    data: Any
    timestamp: datetime
    ttl: int  # Time to live in seconds
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.timestamp + timedelta(seconds=self.ttl)

class EnhancedLinearClient:
    """
    Enhanced Linear GraphQL Client with advanced features:
    - Connection pooling
    - Automatic retries with exponential backoff
    - Response caching
    - Rate limiting
    - Error handling and recovery
    """
    
    BASE_URL = "https://api.linear.app/graphql"
    
    def __init__(
        self,
        api_key: str,
        max_retries: int = 3,
        timeout: int = 30,
        cache_ttl: int = 300,  # 5 minutes
        rate_limit_per_minute: int = 1000
    ):
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.rate_limit_per_minute = rate_limit_per_minute
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, CacheEntry] = {}
        self._rate_limiter = asyncio.Semaphore(rate_limit_per_minute)
        self._last_request_time = 0
        
        # Headers for GraphQL requests
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Contexten-Linear-Client/1.0"
        }
    
    async def initialize(self) -> None:
        """Initialize the HTTP session"""
        if not self._session:
            connector = aiohttp.TCPConnector(
                limit=100,  # Connection pool size
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=self._headers
            )
            
            logger.info("Linear GraphQL client initialized")
    
    async def close(self) -> None:
        """Close the HTTP session"""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("Linear GraphQL client closed")
    
    def _get_cache_key(self, query: str, variables: Optional[Dict] = None) -> str:
        """Generate cache key for query and variables"""
        content = f"{query}:{json.dumps(variables or {}, sort_keys=True)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Get cached response if available and not expired"""
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                logger.debug(f"Cache hit for key: {cache_key}")
                return entry.data
            else:
                # Remove expired entry
                del self._cache[cache_key]
        return None
    
    def _cache_response(self, cache_key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Cache response data"""
        ttl = ttl or self.cache_ttl
        self._cache[cache_key] = CacheEntry(
            data=data,
            timestamp=datetime.utcnow(),
            ttl=ttl
        )
        logger.debug(f"Cached response for key: {cache_key}")
    
    async def _rate_limit(self) -> None:
        """Apply rate limiting"""
        async with self._rate_limiter:
            current_time = time.time()
            time_since_last = current_time - self._last_request_time
            min_interval = 60.0 / self.rate_limit_per_minute
            
            if time_since_last < min_interval:
                await asyncio.sleep(min_interval - time_since_last)
            
            self._last_request_time = time.time()
    
    async def _execute_query(
        self,
        query: str,
        variables: Optional[Dict] = None,
        use_cache: bool = True,
        cache_ttl: Optional[int] = None
    ) -> Dict[str, Any]:
        """Execute GraphQL query with retries and caching"""
        if not self._session:
            await self.initialize()
        
        # Check cache first
        cache_key = self._get_cache_key(query, variables) if use_cache else None
        if cache_key:
            cached_response = self._get_cached_response(cache_key)
            if cached_response:
                return cached_response
        
        # Apply rate limiting
        await self._rate_limit()
        
        payload = {
            "query": query,
            "variables": variables or {}
        }
        
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self._session.post(self.BASE_URL, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "errors" in data:
                            error_msg = "; ".join([err.get("message", "Unknown error") for err in data["errors"]])
                            raise Exception(f"GraphQL errors: {error_msg}")
                        
                        # Cache successful response
                        if cache_key and "data" in data:
                            self._cache_response(cache_key, data, cache_ttl)
                        
                        return data
                    
                    elif response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue
                    
                    else:
                        error_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {error_text}")
            
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Request failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Request failed after {self.max_retries + 1} attempts: {e}")
        
        raise last_exception
    
    # Issue Operations
    async def get_issue(self, issue_id: str) -> Optional[LinearIssue]:
        """Get a Linear issue by ID"""
        try:
            response = await self._execute_query(
                LINEAR_QUERIES["GET_ISSUE"],
                {"id": issue_id}
            )
            
            issue_data = response.get("data", {}).get("issue")
            if issue_data:
                return LinearIssue.from_dict(issue_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting issue {issue_id}: {e}")
            return None
    
    async def search_issues(
        self,
        query: Optional[str] = None,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50
    ) -> List[LinearIssue]:
        """Search for Linear issues"""
        try:
            variables = {
                "first": limit,
                "filter": {}
            }
            
            # Build filter
            if team_id:
                variables["filter"]["team"] = {"id": {"eq": team_id}}
            if project_id:
                variables["filter"]["project"] = {"id": {"eq": project_id}}
            if assignee_id:
                variables["filter"]["assignee"] = {"id": {"eq": assignee_id}}
            if state:
                variables["filter"]["state"] = {"name": {"eq": state}}
            if query:
                variables["filter"]["title"] = {"containsIgnoreCase": query}
            
            response = await self._execute_query(
                LINEAR_QUERIES["SEARCH_ISSUES"],
                variables
            )
            
            issues_data = response.get("data", {}).get("issues", {}).get("nodes", [])
            return [LinearIssue.from_dict(issue) for issue in issues_data]
            
        except Exception as e:
            logger.error(f"Error searching issues: {e}")
            return []
    
    async def create_issue(
        self,
        title: str,
        description: Optional[str] = None,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[int] = None,
        labels: Optional[List[str]] = None,
        parent_id: Optional[str] = None
    ) -> LinearIssue:
        """Create a new Linear issue"""
        try:
            variables = {
                "input": {
                    "title": title
                }
            }
            
            if description:
                variables["input"]["description"] = description
            if team_id:
                variables["input"]["teamId"] = team_id
            if project_id:
                variables["input"]["projectId"] = project_id
            if assignee_id:
                variables["input"]["assigneeId"] = assignee_id
            if priority is not None:
                variables["input"]["priority"] = priority
            if labels:
                variables["input"]["labelIds"] = labels
            if parent_id:
                variables["input"]["parentId"] = parent_id
            
            response = await self._execute_query(
                LINEAR_MUTATIONS["CREATE_ISSUE"],
                variables,
                use_cache=False
            )
            
            issue_data = response.get("data", {}).get("issueCreate", {}).get("issue")
            if issue_data:
                return LinearIssue.from_dict(issue_data)
            else:
                raise Exception("Failed to create issue")
                
        except Exception as e:
            logger.error(f"Error creating issue: {e}")
            raise
    
    async def update_issue(self, issue_id: str, **updates) -> LinearIssue:
        """Update an existing Linear issue"""
        try:
            variables = {
                "id": issue_id,
                "input": updates
            }
            
            response = await self._execute_query(
                LINEAR_MUTATIONS["UPDATE_ISSUE"],
                variables,
                use_cache=False
            )
            
            issue_data = response.get("data", {}).get("issueUpdate", {}).get("issue")
            if issue_data:
                return LinearIssue.from_dict(issue_data)
            else:
                raise Exception("Failed to update issue")
                
        except Exception as e:
            logger.error(f"Error updating issue {issue_id}: {e}")
            raise
    
    async def add_comment(self, issue_id: str, body: str) -> LinearComment:
        """Add a comment to an issue"""
        try:
            variables = {
                "input": {
                    "issueId": issue_id,
                    "body": body
                }
            }
            
            response = await self._execute_query(
                LINEAR_MUTATIONS["CREATE_COMMENT"],
                variables,
                use_cache=False
            )
            
            comment_data = response.get("data", {}).get("commentCreate", {}).get("comment")
            if comment_data:
                return LinearComment.from_dict(comment_data)
            else:
                raise Exception("Failed to create comment")
                
        except Exception as e:
            logger.error(f"Error adding comment to issue {issue_id}: {e}")
            raise
    
    # Project Operations
    async def get_projects(self, team_id: Optional[str] = None) -> List[LinearProject]:
        """Get Linear projects"""
        try:
            variables = {"first": 100}
            if team_id:
                variables["filter"] = {"team": {"id": {"eq": team_id}}}
            
            response = await self._execute_query(
                LINEAR_QUERIES["GET_PROJECTS"],
                variables
            )
            
            projects_data = response.get("data", {}).get("projects", {}).get("nodes", [])
            return [LinearProject.from_dict(project) for project in projects_data]
            
        except Exception as e:
            logger.error(f"Error getting projects: {e}")
            return []
    
    async def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        team_id: Optional[str] = None,
        lead_id: Optional[str] = None,
        target_date: Optional[datetime] = None
    ) -> LinearProject:
        """Create a new Linear project"""
        try:
            variables = {
                "input": {
                    "name": name
                }
            }
            
            if description:
                variables["input"]["description"] = description
            if team_id:
                variables["input"]["teamId"] = team_id
            if lead_id:
                variables["input"]["leadId"] = lead_id
            if target_date:
                variables["input"]["targetDate"] = target_date.isoformat()
            
            response = await self._execute_query(
                LINEAR_MUTATIONS["CREATE_PROJECT"],
                variables,
                use_cache=False
            )
            
            project_data = response.get("data", {}).get("projectCreate", {}).get("project")
            if project_data:
                return LinearProject.from_dict(project_data)
            else:
                raise Exception("Failed to create project")
                
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    # Team Operations
    async def get_teams(self) -> List[LinearTeam]:
        """Get Linear teams"""
        try:
            response = await self._execute_query(
                LINEAR_QUERIES["GET_TEAMS"],
                {"first": 100}
            )
            
            teams_data = response.get("data", {}).get("teams", {}).get("nodes", [])
            return [LinearTeam.from_dict(team) for team in teams_data]
            
        except Exception as e:
            logger.error(f"Error getting teams: {e}")
            return []
    
    async def get_team_members(self, team_id: str) -> List[LinearUser]:
        """Get members of a Linear team"""
        try:
            response = await self._execute_query(
                LINEAR_QUERIES["GET_TEAM_MEMBERS"],
                {"teamId": team_id, "first": 100}
            )
            
            members_data = response.get("data", {}).get("team", {}).get("members", {}).get("nodes", [])
            return [LinearUser.from_dict(member) for member in members_data]
            
        except Exception as e:
            logger.error(f"Error getting team members for {team_id}: {e}")
            return []
    
    # User Operations
    async def get_current_user(self) -> Optional[LinearUser]:
        """Get current authenticated user"""
        try:
            response = await self._execute_query(
                LINEAR_QUERIES["GET_CURRENT_USER"]
            )
            
            user_data = response.get("data", {}).get("viewer")
            if user_data:
                return LinearUser.from_dict(user_data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    # Health Check
    async def health_check(self) -> bool:
        """Perform health check"""
        try:
            await self.get_current_user()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    # Cache Management
    def clear_cache(self) -> None:
        """Clear all cached responses"""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_hit_ratio": getattr(self, "_cache_hits", 0) / max(getattr(self, "_cache_requests", 1), 1)
        }


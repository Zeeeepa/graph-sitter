"""
Linear Integration Client

Integration client for Linear API and webhook handling.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base import BasePlatformIntegration


class LinearIntegration(BasePlatformIntegration):
    """
    Linear platform integration for handling Linear API operations
    and webhook events.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("linear")
        self.config = config or {}
        self.api_token = self.config.get("api_token")
        self.webhook_secret = self.config.get("webhook_secret")
        self.base_url = self.config.get("base_url", "https://api.linear.app/graphql")
        
        # State
        self.authenticated = False
        self.team_id = self.config.get("team_id")
        
        # Event handlers
        self.event_handlers: Dict[str, List[callable]] = {}
    
    async def start(self):
        """Start the Linear integration"""
        if self.running:
            return
        
        self.logger.info("Starting Linear integration")
        self.running = True
        
        # Authenticate if token provided
        if self.api_token:
            self.authenticated = await self.authenticate({"token": self.api_token})
        
        # Start health monitoring
        asyncio.create_task(self._periodic_health_check())
        
        self.logger.info("Linear integration started")
    
    async def stop(self):
        """Stop the Linear integration"""
        self.logger.info("Stopping Linear integration")
        self.running = False
        self.logger.info("Linear integration stopped")
    
    async def authenticate(self, credentials: Dict[str, Any]) -> bool:
        """Authenticate with Linear API"""
        token = credentials.get("token")
        if not token:
            return False
        
        try:
            # Test authentication by getting viewer info
            query = """
            query {
                viewer {
                    id
                    name
                    email
                }
            }
            """
            
            response = await self._graphql_request(query)
            if response and "data" in response and "viewer" in response["data"]:
                self.authenticated = True
                viewer = response["data"]["viewer"]
                self.logger.info(f"Authenticated as Linear user: {viewer.get('name')} ({viewer.get('email')})")
                return True
        
        except Exception as e:
            self.logger.error(f"Linear authentication failed: {e}")
        
        return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform Linear API health check"""
        try:
            # Simple query to check API health
            query = """
            query {
                viewer {
                    id
                }
            }
            """
            
            response = await self._graphql_request(query)
            
            if response and "data" in response:
                healthy = True
                details = {
                    "authenticated": self.authenticated,
                    "api_responsive": True
                }
            else:
                healthy = False
                details = {
                    "authenticated": self.authenticated,
                    "api_responsive": False,
                    "error": "API not responding correctly"
                }
            
            self._update_health_status(healthy, details)
            return self.health_status
        
        except Exception as e:
            self.logger.error(f"Linear health check failed: {e}")
            self._update_health_status(False, {"error": str(e)})
        
        return self.health_status
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Linear integration status"""
        return {
            "platform": self.platform_name,
            "running": self.running,
            "authenticated": self.authenticated,
            "team_id": self.team_id,
            "health": self.health_status,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None
        }
    
    # Linear-specific methods
    
    async def create_issue(self, title: str, description: str = "", 
                          team_id: str = None, assignee_id: str = None,
                          priority: int = None, labels: List[str] = None) -> Optional[Dict[str, Any]]:
        """Create a Linear issue"""
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
        
        input_data = {
            "title": title,
            "description": description,
            "teamId": team_id or self.team_id
        }
        
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if priority is not None:
            input_data["priority"] = priority
        if labels:
            input_data["labelIds"] = labels
        
        variables = {"input": input_data}
        response = await self._graphql_request(mutation, variables)
        
        if response and "data" in response and "issueCreate" in response["data"]:
            return response["data"]["issueCreate"]["issue"]
        
        return None
    
    async def update_issue(self, issue_id: str, title: str = None, 
                          description: str = None, state_id: str = None,
                          assignee_id: str = None, priority: int = None) -> Optional[Dict[str, Any]]:
        """Update a Linear issue"""
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
        
        input_data = {}
        if title is not None:
            input_data["title"] = title
        if description is not None:
            input_data["description"] = description
        if state_id is not None:
            input_data["stateId"] = state_id
        if assignee_id is not None:
            input_data["assigneeId"] = assignee_id
        if priority is not None:
            input_data["priority"] = priority
        
        variables = {"id": issue_id, "input": input_data}
        response = await self._graphql_request(mutation, variables)
        
        if response and "data" in response and "issueUpdate" in response["data"]:
            return response["data"]["issueUpdate"]["issue"]
        
        return None
    
    async def get_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """Get a Linear issue"""
        query = """
        query Issue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                url
                state {
                    id
                    name
                }
                assignee {
                    id
                    name
                }
                team {
                    id
                    name
                }
                priority
                createdAt
                updatedAt
            }
        }
        """
        
        variables = {"id": issue_id}
        response = await self._graphql_request(query, variables)
        
        if response and "data" in response and "issue" in response["data"]:
            return response["data"]["issue"]
        
        return None
    
    async def add_comment(self, issue_id: str, body: str) -> Optional[Dict[str, Any]]:
        """Add a comment to a Linear issue"""
        mutation = """
        mutation CommentCreate($input: CommentCreateInput!) {
            commentCreate(input: $input) {
                success
                comment {
                    id
                    body
                    createdAt
                }
            }
        }
        """
        
        input_data = {
            "issueId": issue_id,
            "body": body
        }
        
        variables = {"input": input_data}
        response = await self._graphql_request(mutation, variables)
        
        if response and "data" in response and "commentCreate" in response["data"]:
            return response["data"]["commentCreate"]["comment"]
        
        return None
    
    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get Linear teams"""
        query = """
        query Teams {
            teams {
                nodes {
                    id
                    name
                    key
                }
            }
        }
        """
        
        response = await self._graphql_request(query)
        
        if response and "data" in response and "teams" in response["data"]:
            return response["data"]["teams"]["nodes"]
        
        return []
    
    async def get_issue_states(self, team_id: str = None) -> List[Dict[str, Any]]:
        """Get issue states for a team"""
        query = """
        query WorkflowStates($teamId: String!) {
            team(id: $teamId) {
                states {
                    nodes {
                        id
                        name
                        type
                        position
                    }
                }
            }
        }
        """
        
        variables = {"teamId": team_id or self.team_id}
        response = await self._graphql_request(query, variables)
        
        if response and "data" in response and "team" in response["data"]:
            return response["data"]["team"]["states"]["nodes"]
        
        return []
    
    async def search_issues(self, query: str, team_id: str = None, 
                           limit: int = 50) -> List[Dict[str, Any]]:
        """Search Linear issues"""
        graphql_query = """
        query SearchIssues($query: String!, $first: Int!) {
            issues(filter: { title: { contains: $query } }, first: $first) {
                nodes {
                    id
                    identifier
                    title
                    description
                    url
                    state {
                        id
                        name
                    }
                    assignee {
                        id
                        name
                    }
                    createdAt
                    updatedAt
                }
            }
        }
        """
        
        variables = {"query": query, "first": limit}
        response = await self._graphql_request(graphql_query, variables)
        
        if response and "data" in response and "issues" in response["data"]:
            return response["data"]["issues"]["nodes"]
        
        return []
    
    async def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """Handle Linear webhook events"""
        try:
            self.logger.info(f"Handling Linear webhook: {event_type}")
            
            # Process common webhook events
            if event_type == "Issue":
                await self._handle_issue_event(payload)
            elif event_type == "Comment":
                await self._handle_comment_event(payload)
            
            # Call registered event handlers
            handlers = self.event_handlers.get(event_type, [])
            for handler in handlers:
                try:
                    await handler(payload)
                except Exception as e:
                    self.logger.error(f"Event handler error: {e}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Webhook handling failed: {e}")
            return False
    
    def register_event_handler(self, event_type: str, handler: callable):
        """Register an event handler for specific Linear events"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    async def _handle_issue_event(self, payload: Dict[str, Any]):
        """Handle issue events"""
        action = payload.get("action")
        data = payload.get("data", {})
        
        self.logger.info(f"Issue {action}: {data.get('identifier')} - {data.get('title')}")
    
    async def _handle_comment_event(self, payload: Dict[str, Any]):
        """Handle comment events"""
        action = payload.get("action")
        data = payload.get("data", {})
        
        self.logger.info(f"Comment {action} on issue: {data.get('issue', {}).get('identifier')}")
    
    async def _graphql_request(self, query: str, variables: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Make a GraphQL request to the Linear API"""
        if not self.api_token:
            self.logger.error("No Linear API token configured")
            return None
        
        import aiohttp
        
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json"
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Check for GraphQL errors
                        if "errors" in result:
                            self.logger.error(f"Linear GraphQL errors: {result['errors']}")
                            return None
                        
                        return result
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Linear API error {response.status}: {error_text}")
                        return None
        
        except Exception as e:
            self.logger.error(f"Linear API request failed: {e}")
            return None


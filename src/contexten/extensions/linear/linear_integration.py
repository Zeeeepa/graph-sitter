#!/usr/bin/env python3
"""
Linear Integration Module
Handles Linear API interactions, issue management, project tracking, and team coordination.
"""

from typing import Dict, List, Any, Optional
import asyncio
import logging
import aiohttp
from datetime import datetime

from ..base.interfaces import BaseExtension

logger = logging.getLogger(__name__)


class LinearIntegration(BaseExtension):
    """Linear integration for issue and project management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.linear_token = self.config.get("linear_token") if self.config else None
        self.base_url = "https://api.linear.app/graphql"
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def _initialize_impl(self) -> None:
        """Initialize Linear integration."""
        self.logger.info("Initializing Linear integration")
        
        if not self.linear_token:
            self.logger.warning("No Linear token provided - some features may be limited")
            
        # Initialize HTTP session
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.linear_token}" if self.linear_token else ""
        }
        
        self.session = aiohttp.ClientSession(headers=headers)
        
    async def _handle_impl(self, payload: Dict[str, Any], request: Any = None) -> Dict[str, Any]:
        """Handle Linear integration requests."""
        action = payload.get("action")
        
        if action == "list_issues":
            return await self.list_issues(
                payload.get("team_id"),
                payload.get("state"),
                payload.get("assignee_id")
            )
        elif action == "get_issue":
            issue_id = payload.get("issue_id")
            if not issue_id:
                return {"error": "issue_id is required", "status": "failed"}
            return await self.get_issue(issue_id)
        elif action == "create_issue":
            return await self.create_issue(payload)
        elif action == "update_issue":
            return await self.update_issue(payload)
        elif action == "list_teams":
            return await self.list_teams()
        elif action == "get_team":
            team_id = payload.get("team_id")
            if not team_id:
                return {"error": "team_id is required", "status": "failed"}
            return await self.get_team(team_id)
        elif action == "list_projects":
            return await self.list_projects(payload.get("team_id"))
        elif action == "get_project":
            project_id = payload.get("project_id")
            if not project_id:
                return {"error": "project_id is required", "status": "failed"}
            return await self.get_project(project_id)
        elif action == "create_project":
            return await self.create_project(payload)
        elif action == "list_users":
            return await self.list_users()
        else:
            return {"error": f"Unknown action: {action}", "status": "failed"}
    
    async def _execute_graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query against Linear API."""
        try:
            payload = {"query": query}
            if variables:
                payload["variables"] = variables
                
            async with self.session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    if "errors" in result:
                        return {"error": result["errors"], "status": "failed"}
                    return {"data": result.get("data"), "status": "success"}
                else:
                    error_text = await response.text()
                    return {"error": f"HTTP {response.status}: {error_text}", "status": "failed"}
                    
        except Exception as e:
            self.logger.error(f"Error executing GraphQL query: {e}")
            return {"error": str(e), "status": "failed"}
    
    async def list_issues(self, team_id: Optional[str] = None, state: Optional[str] = None, 
                         assignee_id: Optional[str] = None) -> Dict[str, Any]:
        """List issues with optional filtering."""
        query = """
        query Issues($filter: IssueFilter) {
            issues(filter: $filter, first: 50) {
                nodes {
                    id
                    identifier
                    title
                    description
                    state {
                        id
                        name
                        type
                    }
                    priority
                    assignee {
                        id
                        name
                        email
                    }
                    team {
                        id
                        name
                        key
                    }
                    project {
                        id
                        name
                    }
                    createdAt
                    updatedAt
                    url
                }
            }
        }
        """
        
        filter_conditions = {}
        if team_id:
            filter_conditions["team"] = {"id": {"eq": team_id}}
        if state:
            filter_conditions["state"] = {"name": {"eq": state}}
        if assignee_id:
            filter_conditions["assignee"] = {"id": {"eq": assignee_id}}
        
        variables = {"filter": filter_conditions} if filter_conditions else None
        
        result = await self._execute_graphql(query, variables)
        if result["status"] == "success":
            issues = result["data"]["issues"]["nodes"]
            return {
                "issues": [
                    {
                        "id": issue["id"],
                        "identifier": issue["identifier"],
                        "title": issue["title"],
                        "description": issue.get("description"),
                        "state": {
                            "id": issue["state"]["id"],
                            "name": issue["state"]["name"],
                            "type": issue["state"]["type"]
                        },
                        "priority": issue.get("priority"),
                        "assignee": {
                            "id": issue["assignee"]["id"],
                            "name": issue["assignee"]["name"],
                            "email": issue["assignee"]["email"]
                        } if issue.get("assignee") else None,
                        "team": {
                            "id": issue["team"]["id"],
                            "name": issue["team"]["name"],
                            "key": issue["team"]["key"]
                        },
                        "project": {
                            "id": issue["project"]["id"],
                            "name": issue["project"]["name"]
                        } if issue.get("project") else None,
                        "created_at": issue["createdAt"],
                        "updated_at": issue["updatedAt"],
                        "url": issue["url"]
                    }
                    for issue in issues
                ],
                "status": "success"
            }
        return result
    
    async def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific issue."""
        query = """
        query Issue($id: String!) {
            issue(id: $id) {
                id
                identifier
                title
                description
                state {
                    id
                    name
                    type
                }
                priority
                assignee {
                    id
                    name
                    email
                }
                team {
                    id
                    name
                    key
                }
                project {
                    id
                    name
                }
                labels {
                    nodes {
                        id
                        name
                        color
                    }
                }
                comments {
                    nodes {
                        id
                        body
                        user {
                            id
                            name
                        }
                        createdAt
                    }
                }
                createdAt
                updatedAt
                url
            }
        }
        """
        
        result = await self._execute_graphql(query, {"id": issue_id})
        if result["status"] == "success":
            issue = result["data"]["issue"]
            if not issue:
                return {"error": "Issue not found", "status": "failed"}
                
            return {
                "issue": {
                    "id": issue["id"],
                    "identifier": issue["identifier"],
                    "title": issue["title"],
                    "description": issue.get("description"),
                    "state": {
                        "id": issue["state"]["id"],
                        "name": issue["state"]["name"],
                        "type": issue["state"]["type"]
                    },
                    "priority": issue.get("priority"),
                    "assignee": {
                        "id": issue["assignee"]["id"],
                        "name": issue["assignee"]["name"],
                        "email": issue["assignee"]["email"]
                    } if issue.get("assignee") else None,
                    "team": {
                        "id": issue["team"]["id"],
                        "name": issue["team"]["name"],
                        "key": issue["team"]["key"]
                    },
                    "project": {
                        "id": issue["project"]["id"],
                        "name": issue["project"]["name"]
                    } if issue.get("project") else None,
                    "labels": [
                        {
                            "id": label["id"],
                            "name": label["name"],
                            "color": label["color"]
                        }
                        for label in issue["labels"]["nodes"]
                    ],
                    "comments": [
                        {
                            "id": comment["id"],
                            "body": comment["body"],
                            "user": {
                                "id": comment["user"]["id"],
                                "name": comment["user"]["name"]
                            },
                            "created_at": comment["createdAt"]
                        }
                        for comment in issue["comments"]["nodes"]
                    ],
                    "created_at": issue["createdAt"],
                    "updated_at": issue["updatedAt"],
                    "url": issue["url"]
                },
                "status": "success"
            }
        return result
    
    async def create_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new issue."""
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
        
        title = payload.get("title")
        team_id = payload.get("team_id")
        
        if not all([title, team_id]):
            return {"error": "title and team_id are required", "status": "failed"}
        
        input_data = {
            "title": title,
            "teamId": team_id
        }
        
        if payload.get("description"):
            input_data["description"] = payload["description"]
        if payload.get("assignee_id"):
            input_data["assigneeId"] = payload["assignee_id"]
        if payload.get("project_id"):
            input_data["projectId"] = payload["project_id"]
        if payload.get("priority"):
            input_data["priority"] = payload["priority"]
        if payload.get("state_id"):
            input_data["stateId"] = payload["state_id"]
        
        result = await self._execute_graphql(mutation, {"input": input_data})
        if result["status"] == "success":
            create_result = result["data"]["issueCreate"]
            if create_result["success"]:
                return {
                    "issue": create_result["issue"],
                    "status": "success"
                }
            else:
                return {"error": "Failed to create issue", "status": "failed"}
        return result
    
    async def update_issue(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing issue."""
        mutation = """
        mutation IssueUpdate($input: IssueUpdateInput!) {
            issueUpdate(input: $input) {
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
        
        issue_id = payload.get("issue_id")
        if not issue_id:
            return {"error": "issue_id is required", "status": "failed"}
        
        input_data = {"id": issue_id}
        
        if payload.get("title"):
            input_data["title"] = payload["title"]
        if payload.get("description"):
            input_data["description"] = payload["description"]
        if payload.get("assignee_id"):
            input_data["assigneeId"] = payload["assignee_id"]
        if payload.get("project_id"):
            input_data["projectId"] = payload["project_id"]
        if payload.get("priority"):
            input_data["priority"] = payload["priority"]
        if payload.get("state_id"):
            input_data["stateId"] = payload["state_id"]
        
        result = await self._execute_graphql(mutation, {"input": input_data})
        if result["status"] == "success":
            update_result = result["data"]["issueUpdate"]
            if update_result["success"]:
                return {
                    "issue": update_result["issue"],
                    "status": "success"
                }
            else:
                return {"error": "Failed to update issue", "status": "failed"}
        return result
    
    async def list_teams(self) -> Dict[str, Any]:
        """List all teams."""
        query = """
        query Teams {
            teams {
                nodes {
                    id
                    name
                    key
                    description
                    private
                    issueCount
                    members {
                        nodes {
                            id
                            name
                            email
                        }
                    }
                }
            }
        }
        """
        
        result = await self._execute_graphql(query)
        if result["status"] == "success":
            teams = result["data"]["teams"]["nodes"]
            return {
                "teams": [
                    {
                        "id": team["id"],
                        "name": team["name"],
                        "key": team["key"],
                        "description": team.get("description"),
                        "private": team["private"],
                        "issue_count": team["issueCount"],
                        "members": [
                            {
                                "id": member["id"],
                                "name": member["name"],
                                "email": member["email"]
                            }
                            for member in team["members"]["nodes"]
                        ]
                    }
                    for team in teams
                ],
                "status": "success"
            }
        return result
    
    async def get_team(self, team_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific team."""
        query = """
        query Team($id: String!) {
            team(id: $id) {
                id
                name
                key
                description
                private
                issueCount
                members {
                    nodes {
                        id
                        name
                        email
                    }
                }
                states {
                    nodes {
                        id
                        name
                        type
                        color
                    }
                }
                labels {
                    nodes {
                        id
                        name
                        color
                    }
                }
            }
        }
        """
        
        result = await self._execute_graphql(query, {"id": team_id})
        if result["status"] == "success":
            team = result["data"]["team"]
            if not team:
                return {"error": "Team not found", "status": "failed"}
                
            return {
                "team": {
                    "id": team["id"],
                    "name": team["name"],
                    "key": team["key"],
                    "description": team.get("description"),
                    "private": team["private"],
                    "issue_count": team["issueCount"],
                    "members": [
                        {
                            "id": member["id"],
                            "name": member["name"],
                            "email": member["email"]
                        }
                        for member in team["members"]["nodes"]
                    ],
                    "states": [
                        {
                            "id": state["id"],
                            "name": state["name"],
                            "type": state["type"],
                            "color": state["color"]
                        }
                        for state in team["states"]["nodes"]
                    ],
                    "labels": [
                        {
                            "id": label["id"],
                            "name": label["name"],
                            "color": label["color"]
                        }
                        for label in team["labels"]["nodes"]
                    ]
                },
                "status": "success"
            }
        return result
    
    async def list_projects(self, team_id: Optional[str] = None) -> Dict[str, Any]:
        """List projects with optional team filtering."""
        query = """
        query Projects($filter: ProjectFilter) {
            projects(filter: $filter, first: 50) {
                nodes {
                    id
                    name
                    description
                    state
                    progress
                    startDate
                    targetDate
                    lead {
                        id
                        name
                        email
                    }
                    teams {
                        nodes {
                            id
                            name
                            key
                        }
                    }
                    issueCount
                    url
                }
            }
        }
        """
        
        variables = None
        if team_id:
            variables = {"filter": {"teams": {"some": {"id": {"eq": team_id}}}}}
        
        result = await self._execute_graphql(query, variables)
        if result["status"] == "success":
            projects = result["data"]["projects"]["nodes"]
            return {
                "projects": [
                    {
                        "id": project["id"],
                        "name": project["name"],
                        "description": project.get("description"),
                        "state": project["state"],
                        "progress": project["progress"],
                        "start_date": project.get("startDate"),
                        "target_date": project.get("targetDate"),
                        "lead": {
                            "id": project["lead"]["id"],
                            "name": project["lead"]["name"],
                            "email": project["lead"]["email"]
                        } if project.get("lead") else None,
                        "teams": [
                            {
                                "id": team["id"],
                                "name": team["name"],
                                "key": team["key"]
                            }
                            for team in project["teams"]["nodes"]
                        ],
                        "issue_count": project["issueCount"],
                        "url": project["url"]
                    }
                    for project in projects
                ],
                "status": "success"
            }
        return result
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific project."""
        query = """
        query Project($id: String!) {
            project(id: $id) {
                id
                name
                description
                state
                progress
                startDate
                targetDate
                lead {
                    id
                    name
                    email
                }
                teams {
                    nodes {
                        id
                        name
                        key
                    }
                }
                issues {
                    nodes {
                        id
                        identifier
                        title
                        state {
                            name
                            type
                        }
                    }
                }
                issueCount
                url
            }
        }
        """
        
        result = await self._execute_graphql(query, {"id": project_id})
        if result["status"] == "success":
            project = result["data"]["project"]
            if not project:
                return {"error": "Project not found", "status": "failed"}
                
            return {
                "project": {
                    "id": project["id"],
                    "name": project["name"],
                    "description": project.get("description"),
                    "state": project["state"],
                    "progress": project["progress"],
                    "start_date": project.get("startDate"),
                    "target_date": project.get("targetDate"),
                    "lead": {
                        "id": project["lead"]["id"],
                        "name": project["lead"]["name"],
                        "email": project["lead"]["email"]
                    } if project.get("lead") else None,
                    "teams": [
                        {
                            "id": team["id"],
                            "name": team["name"],
                            "key": team["key"]
                        }
                        for team in project["teams"]["nodes"]
                    ],
                    "issues": [
                        {
                            "id": issue["id"],
                            "identifier": issue["identifier"],
                            "title": issue["title"],
                            "state": {
                                "name": issue["state"]["name"],
                                "type": issue["state"]["type"]
                            }
                        }
                        for issue in project["issues"]["nodes"]
                    ],
                    "issue_count": project["issueCount"],
                    "url": project["url"]
                },
                "status": "success"
            }
        return result
    
    async def create_project(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project."""
        mutation = """
        mutation ProjectCreate($input: ProjectCreateInput!) {
            projectCreate(input: $input) {
                success
                project {
                    id
                    name
                    url
                }
            }
        }
        """
        
        name = payload.get("name")
        if not name:
            return {"error": "name is required", "status": "failed"}
        
        input_data = {"name": name}
        
        if payload.get("description"):
            input_data["description"] = payload["description"]
        if payload.get("lead_id"):
            input_data["leadId"] = payload["lead_id"]
        if payload.get("team_ids"):
            input_data["teamIds"] = payload["team_ids"]
        if payload.get("start_date"):
            input_data["startDate"] = payload["start_date"]
        if payload.get("target_date"):
            input_data["targetDate"] = payload["target_date"]
        
        result = await self._execute_graphql(mutation, {"input": input_data})
        if result["status"] == "success":
            create_result = result["data"]["projectCreate"]
            if create_result["success"]:
                return {
                    "project": create_result["project"],
                    "status": "success"
                }
            else:
                return {"error": "Failed to create project", "status": "failed"}
        return result
    
    async def list_users(self) -> Dict[str, Any]:
        """List all users in the organization."""
        query = """
        query Users {
            users {
                nodes {
                    id
                    name
                    email
                    displayName
                    active
                    admin
                    avatarUrl
                }
            }
        }
        """
        
        result = await self._execute_graphql(query)
        if result["status"] == "success":
            users = result["data"]["users"]["nodes"]
            return {
                "users": [
                    {
                        "id": user["id"],
                        "name": user["name"],
                        "email": user["email"],
                        "display_name": user.get("displayName"),
                        "active": user["active"],
                        "admin": user["admin"],
                        "avatar_url": user.get("avatarUrl")
                    }
                    for user in users
                ],
                "status": "success"
            }
        return result
    
    async def _cleanup_impl(self) -> None:
        """Cleanup Linear integration resources."""
        if self.session:
            await self.session.close()
            self.session = None
        self.logger.info("Linear integration cleaned up")


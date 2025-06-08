"""Linear Extension for Contexten.

This extension provides comprehensive Linear integration including:
- Issue management
- Project tracking
- Team management
- Workflow automation
- Progress monitoring
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from gql import Client, gql
from gql.transport.httpx import HTTPXTransport

from ...core.extension import EventHandlerExtension, ExtensionMetadata
from ...core.events.bus import Event

logger = logging.getLogger(__name__)

class LinearExtension(EventHandlerExtension):
    """Linear integration extension."""

    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app, config)
        self.linear_client: Optional[Client] = None
        self._teams: Dict[str, Dict[str, Any]] = {}
        self._projects: Dict[str, Dict[str, Any]] = {}
        self._issues: Dict[str, Dict[str, Any]] = {}

    @property
    def metadata(self) -> ExtensionMetadata:
        return ExtensionMetadata(
            name="linear",
            version="1.0.0",
            description="Linear integration for issue and project management",
            author="Contexten",
            dependencies=[],
            required=False,
            config_schema={
                "type": "object",
                "properties": {
                    "api_key": {"type": "string", "description": "Linear API key"},
                    "webhook_secret": {"type": "string", "description": "Webhook secret"},
                },
                "required": ["api_key"]
            },
            tags={"integration", "project-management", "issues"}
        )

    async def initialize(self) -> None:
        """Initialize Linear client and services."""
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError("Linear API key is required")

        # Setup GraphQL client
        transport = HTTPXTransport(
            url="https://api.linear.app/graphql",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        self.linear_client = Client(transport=transport, fetch_schema_from_transport=True)

        # Register event handlers
        self.register_event_handler("linear.webhook", self._handle_webhook)
        self.register_event_handler("project.requirements", self._handle_requirements)
        self.register_event_handler("task.create", self._handle_task_create)

        logger.info("Linear extension initialized")

    async def start(self) -> None:
        """Start Linear extension services."""
        # Verify Linear connection
        try:
            viewer = await self._get_viewer()
            logger.info(f"Connected to Linear as: {viewer['name']}")
        except Exception as e:
            logger.error(f"Failed to connect to Linear: {e}")
            raise

        # Start background tasks
        asyncio.create_task(self._sync_data())

    async def stop(self) -> None:
        """Stop Linear extension services."""
        logger.info("Linear extension stopped")

    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams.
        
        Returns:
            List of team information
        """
        try:
            query = gql("""
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
                            createdAt
                            updatedAt
                        }
                    }
                }
            """)

            result = await self.linear_client.execute_async(query)
            teams = result["teams"]["nodes"]

            # Cache teams
            for team in teams:
                self._teams[team["id"]] = team

            return teams

        except Exception as e:
            logger.error(f"Failed to get teams: {e}")
            raise

    async def get_projects(self, team_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get projects.
        
        Args:
            team_id: Optional team ID to filter by
            
        Returns:
            List of project information
        """
        try:
            if team_id:
                query = gql("""
                    query GetTeamProjects($teamId: String!) {
                        team(id: $teamId) {
                            projects {
                                nodes {
                                    id
                                    name
                                    description
                                    state
                                    progress
                                    startDate
                                    targetDate
                                    createdAt
                                    updatedAt
                                    lead {
                                        id
                                        name
                                        email
                                    }
                                }
                            }
                        }
                    }
                """)
                result = await self.linear_client.execute_async(query, variable_values={"teamId": team_id})
                projects = result["team"]["projects"]["nodes"]
            else:
                query = gql("""
                    query GetProjects {
                        projects {
                            nodes {
                                id
                                name
                                description
                                state
                                progress
                                startDate
                                targetDate
                                createdAt
                                updatedAt
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
                            }
                        }
                    }
                """)
                result = await self.linear_client.execute_async(query)
                projects = result["projects"]["nodes"]

            # Cache projects
            for project in projects:
                self._projects[project["id"]] = project

            return projects

        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            raise

    async def get_issues(
        self,
        team_id: Optional[str] = None,
        project_id: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get issues.
        
        Args:
            team_id: Optional team ID to filter by
            project_id: Optional project ID to filter by
            state: Optional state to filter by
            
        Returns:
            List of issue information
        """
        try:
            filters = []
            if team_id:
                filters.append(f'team: {{id: {{eq: "{team_id}"}}}}')
            if project_id:
                filters.append(f'project: {{id: {{eq: "{project_id}"}}}}')
            if state:
                filters.append(f'state: {{name: {{eq: "{state}"}}}}')

            filter_str = ", ".join(filters) if filters else ""

            query = gql(f"""
                query GetIssues {"{" if filter_str else ""}
                    issues{"(filter: {" + filter_str + "})" if filter_str else ""} {{
                        nodes {{
                            id
                            identifier
                            title
                            description
                            priority
                            estimate
                            createdAt
                            updatedAt
                            dueDate
                            state {{
                                id
                                name
                                type
                                color
                            }}
                            assignee {{
                                id
                                name
                                email
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
                {"}" if filter_str else ""}
            """)

            result = await self.linear_client.execute_async(query)
            issues = result["issues"]["nodes"]

            # Cache issues
            for issue in issues:
                self._issues[issue["id"]] = issue

            return issues

        except Exception as e:
            logger.error(f"Failed to get issues: {e}")
            raise

    async def create_issue(
        self,
        team_id: str,
        title: str,
        description: Optional[str] = None,
        assignee_id: Optional[str] = None,
        project_id: Optional[str] = None,
        priority: Optional[int] = None,
        estimate: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create an issue.
        
        Args:
            team_id: Team ID
            title: Issue title
            description: Optional description
            assignee_id: Optional assignee ID
            project_id: Optional project ID
            priority: Optional priority (1-4)
            estimate: Optional estimate
            
        Returns:
            Created issue information
        """
        try:
            mutation = gql("""
                mutation CreateIssue($input: IssueCreateInput!) {
                    issueCreate(input: $input) {
                        success
                        issue {
                            id
                            identifier
                            title
                            description
                            url
                            state {
                                name
                            }
                        }
                    }
                }
            """)

            input_data = {
                "teamId": team_id,
                "title": title,
            }

            if description:
                input_data["description"] = description
            if assignee_id:
                input_data["assigneeId"] = assignee_id
            if project_id:
                input_data["projectId"] = project_id
            if priority:
                input_data["priority"] = priority
            if estimate:
                input_data["estimate"] = estimate

            result = await self.linear_client.execute_async(
                mutation,
                variable_values={"input": input_data}
            )

            if result["issueCreate"]["success"]:
                issue = result["issueCreate"]["issue"]
                
                # Publish event
                await self.app.event_bus.publish(Event(
                    type="linear.issue.created",
                    source="linear",
                    data={
                        "issue_id": issue["id"],
                        "identifier": issue["identifier"],
                        "title": title,
                        "team_id": team_id,
                    }
                ))

                return issue
            else:
                raise Exception("Failed to create issue")

        except Exception as e:
            logger.error(f"Failed to create issue: {e}")
            raise

    async def update_issue(
        self,
        issue_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        state_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        priority: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update an issue.
        
        Args:
            issue_id: Issue ID
            title: Optional new title
            description: Optional new description
            state_id: Optional new state ID
            assignee_id: Optional new assignee ID
            priority: Optional new priority
            
        Returns:
            Updated issue information
        """
        try:
            mutation = gql("""
                mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
                    issueUpdate(id: $id, input: $input) {
                        success
                        issue {
                            id
                            identifier
                            title
                            description
                            state {
                                name
                            }
                        }
                    }
                }
            """)

            input_data = {}
            if title:
                input_data["title"] = title
            if description:
                input_data["description"] = description
            if state_id:
                input_data["stateId"] = state_id
            if assignee_id:
                input_data["assigneeId"] = assignee_id
            if priority:
                input_data["priority"] = priority

            result = await self.linear_client.execute_async(
                mutation,
                variable_values={"id": issue_id, "input": input_data}
            )

            if result["issueUpdate"]["success"]:
                issue = result["issueUpdate"]["issue"]
                
                # Publish event
                await self.app.event_bus.publish(Event(
                    type="linear.issue.updated",
                    source="linear",
                    data={
                        "issue_id": issue["id"],
                        "identifier": issue["identifier"],
                        "changes": input_data,
                    }
                ))

                return issue
            else:
                raise Exception("Failed to update issue")

        except Exception as e:
            logger.error(f"Failed to update issue: {e}")
            raise

    async def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        team_ids: Optional[List[str]] = None,
        lead_id: Optional[str] = None,
        start_date: Optional[str] = None,
        target_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a project.
        
        Args:
            name: Project name
            description: Optional description
            team_ids: Optional team IDs
            lead_id: Optional lead ID
            start_date: Optional start date (ISO format)
            target_date: Optional target date (ISO format)
            
        Returns:
            Created project information
        """
        try:
            mutation = gql("""
                mutation CreateProject($input: ProjectCreateInput!) {
                    projectCreate(input: $input) {
                        success
                        project {
                            id
                            name
                            description
                            state
                            url
                        }
                    }
                }
            """)

            input_data = {"name": name}
            if description:
                input_data["description"] = description
            if team_ids:
                input_data["teamIds"] = team_ids
            if lead_id:
                input_data["leadId"] = lead_id
            if start_date:
                input_data["startDate"] = start_date
            if target_date:
                input_data["targetDate"] = target_date

            result = await self.linear_client.execute_async(
                mutation,
                variable_values={"input": input_data}
            )

            if result["projectCreate"]["success"]:
                project = result["projectCreate"]["project"]
                
                # Publish event
                await self.app.event_bus.publish(Event(
                    type="linear.project.created",
                    source="linear",
                    data={
                        "project_id": project["id"],
                        "name": name,
                        "team_ids": team_ids or [],
                    }
                ))

                return project
            else:
                raise Exception("Failed to create project")

        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise

    async def _get_viewer(self) -> Dict[str, Any]:
        """Get current user information."""
        query = gql("""
            query GetViewer {
                viewer {
                    id
                    name
                    email
                }
            }
        """)
        result = await self.linear_client.execute_async(query)
        return result["viewer"]

    async def _handle_webhook(self, event_data: Dict[str, Any]) -> None:
        """Handle Linear webhook events."""
        event_type = event_data.get("type")
        data = event_data.get("data", {})

        if event_type == "Issue":
            await self._handle_issue_webhook(data)
        elif event_type == "Project":
            await self._handle_project_webhook(data)

    async def _handle_issue_webhook(self, data: Dict[str, Any]) -> None:
        """Handle issue webhook events."""
        action = data.get("action")
        issue = data.get("issue", {})

        await self.app.event_bus.publish(Event(
            type=f"linear.issue.{action}",
            source="linear",
            data={
                "issue_id": issue.get("id"),
                "identifier": issue.get("identifier"),
                "title": issue.get("title"),
                "state": issue.get("state", {}).get("name"),
            }
        ))

    async def _handle_project_webhook(self, data: Dict[str, Any]) -> None:
        """Handle project webhook events."""
        action = data.get("action")
        project = data.get("project", {})

        await self.app.event_bus.publish(Event(
            type=f"linear.project.{action}",
            source="linear",
            data={
                "project_id": project.get("id"),
                "name": project.get("name"),
                "state": project.get("state"),
            }
        ))

    async def _handle_requirements(self, event_data: Dict[str, Any]) -> None:
        """Handle project requirements."""
        project_name = event_data.get("project_name")
        requirements = event_data.get("requirements")
        
        if project_name and requirements:
            # Create project if it doesn't exist
            projects = await self.get_projects()
            existing_project = next(
                (p for p in projects if p["name"] == project_name),
                None
            )
            
            if not existing_project:
                await self.create_project(
                    name=project_name,
                    description=f"Project created from requirements: {requirements[:100]}..."
                )

    async def _handle_task_create(self, event_data: Dict[str, Any]) -> None:
        """Handle task creation."""
        await self.create_issue(
            team_id=event_data["team_id"],
            title=event_data["title"],
            description=event_data.get("description"),
            project_id=event_data.get("project_id"),
            priority=event_data.get("priority"),
        )

    async def _sync_data(self) -> None:
        """Background task to sync Linear data."""
        while True:
            try:
                await asyncio.sleep(300)  # Sync every 5 minutes
                await self.get_teams()
                await self.get_projects()
            except Exception as e:
                logger.error(f"Linear sync failed: {e}")

    async def health_check(self) -> Dict[str, Any]:
        """Check Linear extension health."""
        try:
            viewer = await self._get_viewer()
            
            return {
                "status": "healthy",
                "user": viewer["name"],
                "cached_teams": len(self._teams),
                "cached_projects": len(self._projects),
                "cached_issues": len(self._issues),
                "timestamp": self.app.current_time.isoformat(),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": str(e),
                "timestamp": self.app.current_time.isoformat(),
            }


"""Linear Extension Adapter for the unified extension system.

This adapter wraps the existing Linear extension to provide the unified
protocol interface without requiring changes to the original extension.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from ..core.extension_base import ExtensionBase, ExtensionMetadata, ExtensionConfig
from ..core.capabilities import ExtensionCapability, CapabilityType, CapabilityMethod, CapabilityParameter
from ..linear.integration_agent import LinearIntegrationAgent
from ..linear.config import LinearIntegrationConfig, get_linear_config

logger = logging.getLogger(__name__)


class LinearExtensionAdapter(ExtensionBase):
    """Adapter for Linear extension to unified protocol."""

    def __init__(self, config: Optional[ExtensionConfig] = None):
        """Initialize Linear adapter.
        
        Args:
            config: Extension configuration
        """
        super().__init__(config)
        self._linear_agent: Optional[LinearIntegrationAgent] = None
        self._linear_config: Optional[LinearIntegrationConfig] = None

    def _create_metadata(self) -> ExtensionMetadata:
        """Create extension metadata."""
        return ExtensionMetadata(
            name="linear",
            version="1.0.0",
            description="Linear issue management and project tracking integration",
            author="Contexten Team",
            capabilities=[
                ExtensionCapability(
                    name="issue_management",
                    type=CapabilityType.ISSUE_TRACKING,
                    description="Create, update, and manage Linear issues",
                    methods=[
                        CapabilityMethod(
                            name="create_issue",
                            description="Create a new Linear issue",
                            parameters=[
                                CapabilityParameter(
                                    name="title",
                                    type="string",
                                    description="Issue title",
                                    required=True
                                ),
                                CapabilityParameter(
                                    name="description",
                                    type="string",
                                    description="Issue description",
                                    required=False
                                ),
                                CapabilityParameter(
                                    name="team_id",
                                    type="string",
                                    description="Team ID",
                                    required=False
                                ),
                                CapabilityParameter(
                                    name="priority",
                                    type="integer",
                                    description="Issue priority (1-4)",
                                    required=False,
                                    default=3
                                ),
                                CapabilityParameter(
                                    name="labels",
                                    type="array",
                                    description="Issue labels",
                                    required=False
                                )
                            ],
                            return_description="Created issue object with ID and details"
                        ),
                        CapabilityMethod(
                            name="update_issue",
                            description="Update an existing Linear issue",
                            parameters=[
                                CapabilityParameter(
                                    name="issue_id",
                                    type="string",
                                    description="Linear issue ID",
                                    required=True
                                ),
                                CapabilityParameter(
                                    name="updates",
                                    type="object",
                                    description="Fields to update",
                                    required=True
                                )
                            ],
                            return_description="Updated issue object"
                        ),
                        CapabilityMethod(
                            name="get_issue",
                            description="Get Linear issue by ID",
                            parameters=[
                                CapabilityParameter(
                                    name="issue_id",
                                    type="string",
                                    description="Linear issue ID",
                                    required=True
                                )
                            ],
                            return_description="Issue object with full details"
                        ),
                        CapabilityMethod(
                            name="search_issues",
                            description="Search Linear issues",
                            parameters=[
                                CapabilityParameter(
                                    name="query",
                                    type="string",
                                    description="Search query",
                                    required=False
                                ),
                                CapabilityParameter(
                                    name="team_id",
                                    type="string",
                                    description="Team ID filter",
                                    required=False
                                ),
                                CapabilityParameter(
                                    name="state",
                                    type="string",
                                    description="Issue state filter",
                                    required=False
                                ),
                                CapabilityParameter(
                                    name="limit",
                                    type="integer",
                                    description="Maximum number of results",
                                    required=False,
                                    default=50
                                )
                            ],
                            return_description="List of matching issues"
                        )
                    ]
                ),
                ExtensionCapability(
                    name="project_management",
                    type=CapabilityType.PROJECT_MANAGEMENT,
                    description="Manage Linear projects and teams",
                    methods=[
                        CapabilityMethod(
                            name="get_teams",
                            description="Get all teams",
                            parameters=[],
                            return_description="List of team objects"
                        ),
                        CapabilityMethod(
                            name="get_projects",
                            description="Get projects for a team",
                            parameters=[
                                CapabilityParameter(
                                    name="team_id",
                                    type="string",
                                    description="Team ID",
                                    required=False
                                )
                            ],
                            return_description="List of project objects"
                        )
                    ]
                ),
                ExtensionCapability(
                    name="workflow_automation",
                    type=CapabilityType.WORKFLOW_AUTOMATION,
                    description="Automate Linear workflows and integrations",
                    methods=[
                        CapabilityMethod(
                            name="auto_assign_issue",
                            description="Automatically assign issue based on rules",
                            parameters=[
                                CapabilityParameter(
                                    name="issue_id",
                                    type="string",
                                    description="Issue ID to assign",
                                    required=True
                                )
                            ],
                            return_description="Assignment result"
                        ),
                        CapabilityMethod(
                            name="process_webhook",
                            description="Process Linear webhook event",
                            parameters=[
                                CapabilityParameter(
                                    name="webhook_data",
                                    type="object",
                                    description="Webhook payload",
                                    required=True
                                )
                            ],
                            return_description="Processing result"
                        )
                    ]
                )
            ],
            dependencies=[]
        )

    async def initialize(self) -> bool:
        """Initialize the Linear adapter."""
        try:
            # Load Linear configuration
            self._linear_config = get_linear_config()
            
            # Validate configuration
            errors = self._linear_config.validate()
            if errors:
                logger.error(f"Linear configuration validation failed: {errors}")
                return False
                
            # Create Linear integration agent
            self._linear_agent = LinearIntegrationAgent(self._linear_config)
            
            logger.info("Linear adapter initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Linear adapter: {e}")
            return False

    async def start(self) -> bool:
        """Start the Linear adapter."""
        try:
            if not self._linear_agent:
                logger.error("Linear agent not initialized")
                return False
                
            # Start the Linear integration agent
            await self._linear_agent.start()
            
            # Set up message handlers
            self.add_message_handler("create_issue", self._handle_create_issue)
            self.add_message_handler("update_issue", self._handle_update_issue)
            self.add_message_handler("get_issue", self._handle_get_issue)
            self.add_message_handler("search_issues", self._handle_search_issues)
            self.add_message_handler("get_teams", self._handle_get_teams)
            self.add_message_handler("get_projects", self._handle_get_projects)
            self.add_message_handler("auto_assign_issue", self._handle_auto_assign_issue)
            self.add_message_handler("process_webhook", self._handle_process_webhook)
            
            logger.info("Linear adapter started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start Linear adapter: {e}")
            return False

    async def stop(self) -> bool:
        """Stop the Linear adapter."""
        try:
            if self._linear_agent:
                await self._linear_agent.stop()
                
            logger.info("Linear adapter stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop Linear adapter: {e}")
            return False

    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            if not self._linear_agent:
                return False
                
            # Check Linear agent health
            health_status = await self._linear_agent.get_health_status()
            return health_status.get("overall_status") == "healthy"
            
        except Exception as e:
            logger.error(f"Linear adapter health check failed: {e}")
            return False

    # Message handlers for unified protocol

    async def _handle_create_issue(self, message) -> Any:
        """Handle create issue request."""
        payload = message.payload
        
        # Extract parameters
        title = payload.get("title")
        description = payload.get("description", "")
        team_id = payload.get("team_id")
        priority = payload.get("priority", 3)
        labels = payload.get("labels", [])
        
        if not title:
            raise ValueError("Title is required")
            
        # Use Linear agent to create issue
        issue_data = {
            "title": title,
            "description": description,
            "priority": priority
        }
        
        if team_id:
            issue_data["teamId"] = team_id
            
        if labels:
            issue_data["labelIds"] = labels
            
        result = await self._linear_agent.linear_client.create_issue(issue_data)
        return result

    async def _handle_update_issue(self, message) -> Any:
        """Handle update issue request."""
        payload = message.payload
        
        issue_id = payload.get("issue_id")
        updates = payload.get("updates", {})
        
        if not issue_id:
            raise ValueError("Issue ID is required")
            
        if not updates:
            raise ValueError("Updates are required")
            
        # Use Linear agent to update issue
        result = await self._linear_agent.linear_client.update_issue(issue_id, updates)
        return result

    async def _handle_get_issue(self, message) -> Any:
        """Handle get issue request."""
        payload = message.payload
        
        issue_id = payload.get("issue_id")
        if not issue_id:
            raise ValueError("Issue ID is required")
            
        # Use Linear agent to get issue
        result = await self._linear_agent.linear_client.get_issue(issue_id)
        return result

    async def _handle_search_issues(self, message) -> Any:
        """Handle search issues request."""
        payload = message.payload
        
        query = payload.get("query")
        team_id = payload.get("team_id")
        state = payload.get("state")
        limit = payload.get("limit", 50)
        
        # Build search parameters
        search_params = {"first": limit}
        
        if query:
            search_params["filter"] = {"title": {"contains": query}}
            
        if team_id:
            search_params["filter"] = search_params.get("filter", {})
            search_params["filter"]["team"] = {"id": {"eq": team_id}}
            
        if state:
            search_params["filter"] = search_params.get("filter", {})
            search_params["filter"]["state"] = {"name": {"eq": state}}
            
        # Use Linear agent to search issues
        result = await self._linear_agent.linear_client.search_issues(search_params)
        return result

    async def _handle_get_teams(self, message) -> Any:
        """Handle get teams request."""
        # Use Linear agent to get teams
        result = await self._linear_agent.linear_client.get_teams()
        return result

    async def _handle_get_projects(self, message) -> Any:
        """Handle get projects request."""
        payload = message.payload
        team_id = payload.get("team_id")
        
        # Use Linear agent to get projects
        if team_id:
            result = await self._linear_agent.linear_client.get_team_projects(team_id)
        else:
            result = await self._linear_agent.linear_client.get_projects()
            
        return result

    async def _handle_auto_assign_issue(self, message) -> Any:
        """Handle auto assign issue request."""
        payload = message.payload
        
        issue_id = payload.get("issue_id")
        if not issue_id:
            raise ValueError("Issue ID is required")
            
        # Use Linear agent's assignment detector
        result = await self._linear_agent.assignment_detector.auto_assign_issue(issue_id)
        return result

    async def _handle_process_webhook(self, message) -> Any:
        """Handle process webhook request."""
        payload = message.payload
        
        webhook_data = payload.get("webhook_data")
        if not webhook_data:
            raise ValueError("Webhook data is required")
            
        # Use Linear agent's webhook processor
        result = await self._linear_agent.webhook_processor.process_webhook(webhook_data)
        return result

    # Public API methods for direct usage

    async def create_issue(
        self,
        title: str,
        description: str = "",
        team_id: Optional[str] = None,
        priority: int = 3,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a Linear issue.
        
        Args:
            title: Issue title
            description: Issue description
            team_id: Team ID
            priority: Issue priority (1-4)
            labels: Issue labels
            
        Returns:
            Created issue data
        """
        if not self._linear_agent:
            raise RuntimeError("Linear adapter not initialized")
            
        issue_data = {
            "title": title,
            "description": description,
            "priority": priority
        }
        
        if team_id:
            issue_data["teamId"] = team_id
            
        if labels:
            issue_data["labelIds"] = labels
            
        return await self._linear_agent.linear_client.create_issue(issue_data)

    async def update_issue(self, issue_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a Linear issue.
        
        Args:
            issue_id: Issue ID
            updates: Fields to update
            
        Returns:
            Updated issue data
        """
        if not self._linear_agent:
            raise RuntimeError("Linear adapter not initialized")
            
        return await self._linear_agent.linear_client.update_issue(issue_id, updates)

    async def get_issue(self, issue_id: str) -> Dict[str, Any]:
        """Get a Linear issue.
        
        Args:
            issue_id: Issue ID
            
        Returns:
            Issue data
        """
        if not self._linear_agent:
            raise RuntimeError("Linear adapter not initialized")
            
        return await self._linear_agent.linear_client.get_issue(issue_id)

    async def search_issues(
        self,
        query: Optional[str] = None,
        team_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search Linear issues.
        
        Args:
            query: Search query
            team_id: Team ID filter
            state: State filter
            limit: Maximum results
            
        Returns:
            List of matching issues
        """
        if not self._linear_agent:
            raise RuntimeError("Linear adapter not initialized")
            
        search_params = {"first": limit}
        
        if query:
            search_params["filter"] = {"title": {"contains": query}}
            
        if team_id:
            search_params["filter"] = search_params.get("filter", {})
            search_params["filter"]["team"] = {"id": {"eq": team_id}}
            
        if state:
            search_params["filter"] = search_params.get("filter", {})
            search_params["filter"]["state"] = {"name": {"eq": state}}
            
        return await self._linear_agent.linear_client.search_issues(search_params)

    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams.
        
        Returns:
            List of teams
        """
        if not self._linear_agent:
            raise RuntimeError("Linear adapter not initialized")
            
        return await self._linear_agent.linear_client.get_teams()

    async def get_projects(self, team_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get projects.
        
        Args:
            team_id: Optional team ID filter
            
        Returns:
            List of projects
        """
        if not self._linear_agent:
            raise RuntimeError("Linear adapter not initialized")
            
        if team_id:
            return await self._linear_agent.linear_client.get_team_projects(team_id)
        else:
            return await self._linear_agent.linear_client.get_projects()

    def get_linear_agent(self) -> Optional[LinearIntegrationAgent]:
        """Get the underlying Linear integration agent.
        
        Returns:
            Linear integration agent instance
        """
        return self._linear_agent


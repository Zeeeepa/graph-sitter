"""
Enhanced Linear Service using Strands Tools Integration

This service wraps the existing Linear integration with strands tools patterns
while preserving all current functionality.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

# Import existing Linear integration (to be preserved)
from contexten.extensions.linear.enhanced_client import LinearClient
from contexten.extensions.linear.types import LinearIssue, LinearProject, LinearTeam
from contexten.extensions.linear.config import LinearIntegrationConfig

# TODO: Import strands tools when available
# from strands_tools.workflow import Workflow, WorkflowStep

logger = logging.getLogger(__name__)


@dataclass
class LinearWorkflowResult:
    """Result from Linear workflow execution"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    workflow_id: Optional[str] = None
    execution_time: Optional[float] = None


class StrandsLinearWorkflow:
    """
    Linear workflow using strands tools patterns
    
    This wraps the existing Linear functionality with proper strands tools
    workflow patterns while preserving all current capabilities.
    """
    
    def __init__(self, config: Optional[LinearIntegrationConfig] = None):
        self.config = config or LinearIntegrationConfig()
        self.linear_client = LinearClient(self.config)
        self.workflow_id = f"linear_workflow_{datetime.now().timestamp()}"
        
    async def execute_issue_workflow(self, workflow_type: str, params: Dict[str, Any]) -> LinearWorkflowResult:
        """Execute Linear issue workflow using strands patterns"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            logger.info(f"🔄 Executing Linear workflow: {workflow_type}")
            
            result = None
            
            if workflow_type == "create_issue":
                result = await self._create_issue_workflow(params)
            elif workflow_type == "update_issue":
                result = await self._update_issue_workflow(params)
            elif workflow_type == "search_issues":
                result = await self._search_issues_workflow(params)
            elif workflow_type == "sync_status":
                result = await self._sync_status_workflow(params)
            else:
                raise ValueError(f"Unknown workflow type: {workflow_type}")
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            logger.info(f"✅ Linear workflow completed: {workflow_type} in {execution_time:.2f}s")
            
            return LinearWorkflowResult(
                success=True,
                data=result,
                workflow_id=self.workflow_id,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            logger.error(f"❌ Linear workflow failed: {workflow_type} - {e}")
            
            return LinearWorkflowResult(
                success=False,
                error=str(e),
                workflow_id=self.workflow_id,
                execution_time=execution_time
            )
    
    async def _create_issue_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create issue workflow step"""
        logger.info("📝 Creating Linear issue")
        
        # Use existing Linear client functionality
        issue = await self.linear_client.create_issue(
            title=params.get("title"),
            description=params.get("description"),
            team_id=params.get("team_id"),
            assignee_id=params.get("assignee_id"),
            priority=params.get("priority"),
            labels=params.get("labels", [])
        )
        
        return {
            "issue": issue.to_dict() if hasattr(issue, 'to_dict') else issue,
            "workflow_step": "create_issue",
            "status": "completed"
        }
    
    async def _update_issue_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update issue workflow step"""
        logger.info(f"✏️ Updating Linear issue: {params.get('issue_id')}")
        
        # Use existing Linear client functionality
        issue = await self.linear_client.update_issue(
            issue_id=params.get("issue_id"),
            title=params.get("title"),
            description=params.get("description"),
            state_id=params.get("state_id"),
            assignee_id=params.get("assignee_id"),
            priority=params.get("priority")
        )
        
        return {
            "issue": issue.to_dict() if hasattr(issue, 'to_dict') else issue,
            "workflow_step": "update_issue",
            "status": "completed"
        }
    
    async def _search_issues_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Search issues workflow step"""
        logger.info(f"🔍 Searching Linear issues: {params.get('query')}")
        
        # Use existing Linear client functionality
        issues = await self.linear_client.search_issues(
            query=params.get("query"),
            team_id=params.get("team_id"),
            state_id=params.get("state_id"),
            assignee_id=params.get("assignee_id"),
            limit=params.get("limit", 50)
        )
        
        return {
            "issues": [issue.to_dict() if hasattr(issue, 'to_dict') else issue for issue in issues],
            "count": len(issues),
            "workflow_step": "search_issues",
            "status": "completed"
        }
    
    async def _sync_status_workflow(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sync status workflow step"""
        logger.info("🔄 Syncing Linear status")
        
        # Use existing Linear client functionality for status sync
        sync_result = await self.linear_client.sync_status(
            issue_id=params.get("issue_id"),
            external_status=params.get("external_status"),
            source=params.get("source", "strands_workflow")
        )
        
        return {
            "sync_result": sync_result,
            "workflow_step": "sync_status",
            "status": "completed"
        }


class LinearService:
    """
    Enhanced Linear service integrating strands tools with existing functionality
    
    This service preserves all existing Linear integration capabilities while
    adding strands tools workflow patterns and modern orchestration.
    """
    
    def __init__(self):
        self.config = LinearIntegrationConfig()
        self.linear_client = LinearClient(self.config)
        self.workflows: Dict[str, StrandsLinearWorkflow] = {}
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """Initialize Linear service with strands tools integration"""
        try:
            logger.info("🚀 Initializing Linear service with strands tools")
            
            # Initialize existing Linear client
            await self.linear_client.initialize()
            
            # TODO: Initialize strands tools components
            # self.strands_workflow = StrandsWorkflow("linear_integration")
            
            self.is_initialized = True
            logger.info("✅ Linear service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Linear service: {e}")
            return False
    
    async def create_workflow(self, workflow_id: str) -> StrandsLinearWorkflow:
        """Create new Linear workflow"""
        workflow = StrandsLinearWorkflow(self.config)
        self.workflows[workflow_id] = workflow
        logger.info(f"🔄 Created Linear workflow: {workflow_id}")
        return workflow
    
    async def execute_workflow(self, workflow_type: str, params: Dict[str, Any]) -> LinearWorkflowResult:
        """Execute Linear workflow"""
        workflow_id = f"workflow_{datetime.now().timestamp()}"
        workflow = await self.create_workflow(workflow_id)
        return await workflow.execute_issue_workflow(workflow_type, params)
    
    # Preserve existing Linear functionality with enhanced patterns
    
    async def get_issues(self, team_id: Optional[str] = None, limit: int = 50) -> List[LinearIssue]:
        """Get Linear issues (preserved functionality)"""
        logger.info(f"📋 Getting Linear issues (team: {team_id}, limit: {limit})")
        return await self.linear_client.get_issues(team_id=team_id, limit=limit)
    
    async def get_issue(self, issue_id: str) -> LinearIssue:
        """Get specific Linear issue (preserved functionality)"""
        logger.info(f"📄 Getting Linear issue: {issue_id}")
        return await self.linear_client.get_issue(issue_id)
    
    async def create_issue(self, title: str, description: Optional[str] = None, **kwargs) -> LinearIssue:
        """Create Linear issue (preserved functionality with workflow enhancement)"""
        logger.info(f"📝 Creating Linear issue: {title}")
        
        # Use workflow for enhanced functionality
        result = await self.execute_workflow("create_issue", {
            "title": title,
            "description": description,
            **kwargs
        })
        
        if not result.success:
            raise Exception(f"Failed to create issue: {result.error}")
        
        return result.data["issue"]
    
    async def update_issue(self, issue_id: str, **kwargs) -> LinearIssue:
        """Update Linear issue (preserved functionality with workflow enhancement)"""
        logger.info(f"✏️ Updating Linear issue: {issue_id}")
        
        # Use workflow for enhanced functionality
        result = await self.execute_workflow("update_issue", {
            "issue_id": issue_id,
            **kwargs
        })
        
        if not result.success:
            raise Exception(f"Failed to update issue: {result.error}")
        
        return result.data["issue"]
    
    async def search_issues(self, query: str, **kwargs) -> List[LinearIssue]:
        """Search Linear issues (preserved functionality with workflow enhancement)"""
        logger.info(f"🔍 Searching Linear issues: {query}")
        
        # Use workflow for enhanced functionality
        result = await self.execute_workflow("search_issues", {
            "query": query,
            **kwargs
        })
        
        if not result.success:
            raise Exception(f"Failed to search issues: {result.error}")
        
        return result.data["issues"]
    
    async def get_teams(self) -> List[LinearTeam]:
        """Get Linear teams (preserved functionality)"""
        logger.info("👥 Getting Linear teams")
        return await self.linear_client.get_teams()
    
    async def get_projects(self) -> List[LinearProject]:
        """Get Linear projects (preserved functionality)"""
        logger.info("📁 Getting Linear projects")
        return await self.linear_client.get_projects()
    
    async def sync_with_external(self, external_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync Linear with external systems using strands workflows"""
        logger.info("🔄 Syncing Linear with external systems")
        
        result = await self.execute_workflow("sync_status", {
            "external_status": external_data.get("status"),
            "source": external_data.get("source"),
            "issue_id": external_data.get("issue_id")
        })
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error
        }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow execution status"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"status": "not_found"}
        
        return {
            "status": "active",
            "workflow_id": workflow_id,
            "created_at": workflow.workflow_id
        }
    
    async def shutdown(self):
        """Shutdown Linear service"""
        if self.is_initialized:
            logger.info("🛑 Shutting down Linear service")
            await self.linear_client.shutdown()
            self.workflows.clear()
            self.is_initialized = False


# Global Linear service instance
linear_service = LinearService()

